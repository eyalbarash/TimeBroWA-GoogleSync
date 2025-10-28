#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מנהל סינכרון ממוקד של WhatsApp ליומן Google
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from green_api_client import GreenAPIClient
from simple_timebro_calendar import SimpleTimeBroCalendar
from credential_manager import GreenAPICredentials
import threading
import time

class SyncManager:
    def __init__(self):
        self.contacts_db = "whatsapp_contacts_groups.db"
        self.groups_db = "whatsapp_contacts_groups.db"
        self.messages_db = "whatsapp_messages_webjs.db"
        self.calendar_db = "timebro_calendar.db"
        
        # Green API credentials - try multiple sources
        self.id_instance = os.getenv("GREENAPI_ID_INSTANCE")
        self.api_token = os.getenv("GREENAPI_API_TOKEN")
        
        # אם לא נמצאו במשתני סביבה, ננסה לקרוא מקובץ .env
        if not self.id_instance or not self.api_token:
            try:
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('GREENAPI_ID_INSTANCE='):
                            self.id_instance = line.split('=', 1)[1].strip()
                        elif line.startswith('GREENAPI_API_TOKEN='):
                            self.api_token = line.split('=', 1)[1].strip()
            except FileNotFoundError:
                pass
        
        # אם עדיין לא נמצאו, נסה לקרוא מ-credential_manager
        if not self.id_instance or not self.api_token:
            try:
                creds = GreenAPICredentials()
                credentials = creds.get_credentials()
                if credentials:
                    self.id_instance = credentials.get('instance_id')
                    self.api_token = credentials.get('token')
                    self.log(f"✅ נטענו הרשאות Green API מ-credential_manager", "SUCCESS")
            except Exception as e:
                self.log(f"⚠️ שגיאה בטעינת הרשאות מ-credential_manager: {e}", "WARNING")
        
        if not self.id_instance or not self.api_token:
            raise ValueError("Green API credentials not found")
        
        self.green_api_client = GreenAPIClient(self.id_instance, self.api_token)
        self.calendar_system = SimpleTimeBroCalendar()
        
        # סטטוס סינכרון פעיל
        self.active_syncs = {}
        
    def log(self, message, level="INFO"):
        """לוגים"""
        import logging
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        elif level == "WARNING":
            emoji = "⚠️"
        else:
            emoji = "📱"
        
        log_message = f"[{timestamp}] {emoji} {message}"
        print(log_message)
        
        # כתיבה לקובץ לוג
        try:
            with open('sync_manager.log', 'a', encoding='utf-8') as f:
                f.write(f"{timestamp} - {level} - {message}\n")
        except Exception as e:
            print(f"שגיאה בכתיבת לוג: {e}")
        
        # גם ל-logging של Python
        logger = logging.getLogger(__name__)
        if level == "ERROR":
            logger.error(message)
        elif level == "WARNING":
            logger.warning(message)
        elif level == "SUCCESS":
            logger.info(f"✅ {message}")
        else:
            logger.info(message)

    def sync_contact_messages(self, contact_id: str, start_date: str, end_date: str) -> Dict:
        """סינכרון הודעות של איש קשר ספציפי - עם בדיקה חכמה למניעת API מיותר"""
        try:
            self.log(f"🔄 מתחיל סינכרון איש קשר: {contact_id}")
            self.log(f"📅 תקופה: {start_date} - {end_date}")

            # המרת תאריכים
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            else:
                start_dt = start_date

            if isinstance(end_date, str):
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                end_dt = end_date

            # קבלת whatsapp_id מהמסד נתונים
            whatsapp_id = self._get_whatsapp_id_for_contact(contact_id)
            if not whatsapp_id:
                return {
                    "success": False,
                    "error": f"לא נמצא whatsapp_id עבור איש קשר {contact_id}",
                    "messages_found": 0,
                    "events_created": 0
                }

            # בדיקה חכמה: האם כבר יש הודעות במסד הנתונים לטווח הזמן?
            conn = sqlite3.connect(self.messages_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM messages
                WHERE chat_id = ?
                AND timestamp BETWEEN ? AND ?
            """, (whatsapp_id, int(start_dt.timestamp() * 1000), int(end_dt.timestamp() * 1000)))
            existing_messages_count = cursor.fetchone()[0]
            conn.close()

            messages_fetched = 0
            saved_count = 0

            if existing_messages_count > 0:
                self.log(f"✅ נמצאו {existing_messages_count} הודעות קיימות במסד הנתונים - מדלג על API")
                self.log(f"💡 חוסך קריאת API מיותרת ל-Green API")
                messages_fetched = existing_messages_count
                # No need to call Green API - messages already in database
            else:
                # אין הודעות במסד הנתונים - צריך לקרוא מ-API
                self.log(f"📡 לא נמצאו הודעות במסד הנתונים - מקבל מ-Green API...")

                # בדיקת בריאות Green API
                self.log("🏥 בודק בריאות Green API...")
                success, state = self.green_api_client.get_state_instance()
                if not success or state.get("stateInstance") != "authorized":
                    self.log(f"❌ Green API לא זמין: {state.get('error', 'לא ידוע')}", "ERROR")
                    return {
                        "success": False,
                        "error": f"Green API לא זמין: {state.get('error', 'לא ידוע')}",
                        "messages_found": 0,
                        "events_created": 0
                    }

                # קבלת הודעות מ-Green API
                self.log(f"📡 מקבל הודעות מ-Green API עבור {whatsapp_id}...")
                self.log(f"📅 טווח תאריכים: {start_dt.strftime('%d/%m/%Y')} - {end_dt.strftime('%d/%m/%Y')}")

                # Delay קצר לפני כל קריאה ל-API
                import time
                time.sleep(2.0)  # Increased delay for better rate limiting

                messages = self.green_api_client.get_chat_history_by_date_range(whatsapp_id, start_dt, end_dt)

                if isinstance(messages, dict) and "error" in messages:
                    self.log(f"❌ שגיאה בקבלת הודעות: {messages['error']}", "ERROR")
                else:
                    self.log(f"📊 התקבלו {len(messages)} הודעות מ-Green API", "SUCCESS")

                if not messages or (isinstance(messages, dict) and "error" in messages):
                    return {
                        "success": False,
                        "error": f"שגיאה בקבלת הודעות: {messages.get('error', 'לא ידוע') if isinstance(messages, dict) else 'לא ידוע'}",
                        "messages_found": 0,
                        "events_created": 0
                    }

                # שמירת הודעות למסד הנתונים
                self.log(f"💾 שומר {len(messages)} הודעות למסד הנתונים...")
                saved_count = self._save_messages_to_db(messages, whatsapp_id)
                self.log(f"✅ נשמרו {saved_count} הודעות חדשות למסד הנתונים")
                messages_fetched = len(messages)

            # יצירת אירועי יומן (תמיד - גם אם ההודעות כבר היו במסד)
            self.log("📅 יוצר אירועי יומן...")
            # Pass both contact_id and whatsapp_id to calendar creation
            events_created = self._create_calendar_events(contact_id, start_dt, end_dt, whatsapp_id)
            self.log(f"📅 נוצרו {events_created} אירועי יומן")

            # עדכון סטטוס "כלול ביומן"
            self._mark_for_calendar(contact_id, is_contact=True)

            # עדכון סטטוס סינכרון
            self._update_sync_status(contact_id, "contact", True, saved_count, events_created)

            result = {
                "success": True,
                "messages_found": messages_fetched,
                "messages_saved": saved_count,
                "messages_existing": existing_messages_count,
                "events_created": events_created,
                "contact_id": contact_id,
                "sync_date": datetime.now().isoformat(),
                "api_called": existing_messages_count == 0
            }

            self.log(f"✅ סינכרון הושלם: {messages_fetched} הודעות, {events_created} אירועים", "SUCCESS")
            return result

        except Exception as e:
            self.log(f"❌ שגיאה בסינכרון איש קשר: {e}", "ERROR")
            return {
                "success": False,
                "error": str(e),
                "messages_found": 0,
                "events_created": 0
            }

    def sync_group_messages(self, group_id: str, start_date: str, end_date: str) -> Dict:
        """סינכרון הודעות של קבוצה ספציפית"""
        try:
            self.log(f"🔄 מתחיל סינכרון קבוצה: {group_id}")
            self.log(f"📅 תקופה: {start_date} עד {end_date}")
            
            # המרת תאריכים
            if isinstance(start_date, str):
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            else:
                start_dt = start_date
                
            if isinstance(end_date, str):
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            else:
                end_dt = end_date
            self.log(f"📊 תאריכים מומרים: {start_dt} - {end_dt}")
            
            # בדיקת חיבור ל-Green API
            self.log("🔍 בודק חיבור ל-Green API...")
            
            # Delay קצר לפני כל קריאה ל-API
            import time
            time.sleep(0.5)
            
            state = self.green_api_client.get_state_instance()
            self.log(f"📡 מצב Green API: {state}")
            
            if state.get('stateInstance') != 'authorized':
                self.log("❌ Green API לא מורשה", "ERROR")
                return {
                    "success": False,
                    "error": "Green API לא מורשה",
                    "messages_found": 0,
                    "events_created": 0
                }
            
            # קבלת הודעות מ-Green API
            self.log("📡 מקבל הודעות מ-Green API...")
            messages = self.green_api_client.get_chat_history_by_date_range(group_id, start_dt, end_dt)
            self.log(f"📊 קיבלתי {len(messages) if messages else 0} הודעות מ-Green API")
            
            if not messages or (isinstance(messages, dict) and "error" in messages):
                return {
                    "success": False,
                    "error": f"שגיאה בקבלת הודעות: {messages.get('error', 'לא ידוע') if isinstance(messages, dict) else 'לא ידוע'}",
                    "messages_found": 0,
                    "events_created": 0
                }
            
            # שמירת הודעות למסד הנתונים
            self.log(f"💾 שומר {len(messages)} הודעות למסד הנתונים...")
            saved_count = self._save_messages_to_db(messages, group_id)
            self.log(f"✅ נשמרו {saved_count} הודעות למסד הנתונים")
            
            # יצירת אירועי יומן
            self.log("📅 יוצר אירועי יומן...")
            events_created = self._create_calendar_events(group_id, start_dt, end_dt)
            self.log(f"✅ נוצרו {events_created} אירועי יומן")
            
            # עדכון סטטוס "כלול ביומן"
            self.log("🏷️ מעדכן סטטוס 'כלול ביומן'...")
            self._mark_for_calendar(group_id, is_contact=False)
            
            # עדכון סטטוס סינכרון
            self.log("📊 מעדכן סטטוס סינכרון...")
            self._update_sync_status(group_id, "group", True, saved_count, events_created)
            
            result = {
                "success": True,
                "messages_found": len(messages),
                "messages_saved": saved_count,
                "events_created": events_created,
                "group_id": group_id,
                "sync_date": datetime.now().isoformat()
            }
            
            self.log(f"✅ סינכרון הושלם: {saved_count} הודעות, {events_created} אירועים", "SUCCESS")
            return result
            
        except Exception as e:
            self.log(f"❌ שגיאה בסינכרון קבוצה: {e}", "ERROR")
            return {
                "success": False,
                "error": str(e),
                "messages_found": 0,
                "events_created": 0
            }

    def sync_all_marked(self, start_date: str, end_date: str) -> Dict:
        """סינכרון כל המסומנים ליומן"""
        try:
            self.log("🔄 מתחיל סינכרון כל המסומנים ליומן")
            
            # קבלת כל המסומנים
            marked_contacts = self._get_marked_contacts()
            marked_groups = self._get_marked_groups()
            
            total_contacts = len(marked_contacts)
            total_groups = len(marked_groups)
            
            self.log(f"📊 נמצאו {total_contacts} אנשי קשר ו-{total_groups} קבוצות מסומנים")
            
            results = {
                "success": True,
                "total_contacts": total_contacts,
                "total_groups": total_groups,
                "contacts_results": [],
                "groups_results": [],
                "total_messages": 0,
                "total_events": 0
            }
            
            # סינכרון אנשי קשר
            for i, contact_id in enumerate(marked_contacts):
                self.log(f"👤 מסנכרן איש קשר: {contact_id} ({i+1}/{len(marked_contacts)})")
                contact_result = self.sync_contact_messages(contact_id, start_date, end_date)
                results["contacts_results"].append(contact_result)
                if contact_result["success"]:
                    results["total_messages"] += contact_result["messages_saved"]
                    results["total_events"] += contact_result["events_created"]
                    self.log(f"✅ איש קשר {contact_id} סונכרן בהצלחה: {contact_result['messages_saved']} הודעות, {contact_result['events_created']} אירועים")
                else:
                    self.log(f"❌ שגיאה בסינכרון איש קשר {contact_id}: {contact_result.get('error', 'לא ידוע')}")
                
                # Delay בין סינכרונים של אנשי קשר שונים (חוץ מהאחרון)
                if i < len(marked_contacts) - 1:
                    import time
                    self.log(f"⏳ ממתין 2 שניות לפני הסינכרון הבא... ({len(marked_contacts) - i - 1} נותרו)")
                    time.sleep(2.0)  # 2 שניות delay בין אנשי קשר
            
            # סינכרון קבוצות
            for i, group_id in enumerate(marked_groups):
                self.log(f"👥 מסנכרן קבוצה: {group_id} ({i+1}/{len(marked_groups)})")
                group_result = self.sync_group_messages(group_id, start_date, end_date)
                results["groups_results"].append(group_result)
                if group_result["success"]:
                    results["total_messages"] += group_result["messages_saved"]
                    results["total_events"] += group_result["events_created"]
                    self.log(f"✅ קבוצה {group_id} סונכרנה בהצלחה: {group_result['messages_saved']} הודעות, {group_result['events_created']} אירועים")
                else:
                    self.log(f"❌ שגיאה בסינכרון קבוצה {group_id}: {group_result.get('error', 'לא ידוע')}")
                
                # Delay בין סינכרונים של קבוצות שונות (חוץ מהאחרונה)
                if i < len(marked_groups) - 1:
                    import time
                    self.log(f"⏳ ממתין 2 שניות לפני הסינכרון הבא... ({len(marked_groups) - i - 1} נותרו)")
                    time.sleep(2.0)  # 2 שניות delay בין קבוצות
            
            self.log(f"✅ סינכרון כללי הושלם: {results['total_messages']} הודעות, {results['total_events']} אירועים", "SUCCESS")
            return results
            
        except Exception as e:
            self.log(f"❌ שגיאה בסינכרון כללי: {e}", "ERROR")
            return {
                "success": False,
                "error": str(e),
                "total_messages": 0,
                "total_events": 0
            }

    def _save_messages_to_db(self, messages: List[Dict], chat_id: str) -> int:
        """שמירת הודעות למסד הנתונים"""
        try:
            conn = sqlite3.connect(self.messages_db)
            cursor = conn.cursor()
            
            saved_count = 0
            for message in messages:
                try:
                    # בדיקה אם ההודעה כבר קיימת
                    message_id = message.get('id') or message.get('messageId')
                    cursor.execute("""
                        SELECT id FROM messages 
                        WHERE id = ? AND chat_id = ?
                    """, (message_id, chat_id))
                    
                    if cursor.fetchone():
                        continue  # הודעה כבר קיימת
                    
                    # קבלת שם איש הקשר מ-contacts.db
                    contact_name = self._get_contact_name(chat_id)
                    
                    # שמירת הודעה חדשה
                    cursor.execute("""
                        INSERT INTO messages 
                        (id, chat_id, contact_number, contact_name, message_body, 
                         message_type, timestamp, is_from_me, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        message_id,
                        chat_id,
                        chat_id,  # contact_number
                        contact_name,  # contact_name
                        message.get('textMessage') or message.get('body') or message.get('text') or message.get('message'),
                        message.get('typeMessage') or message.get('type') or 'text',
                        int((message.get('timestamp') or message.get('time') or 0) * 1000),
                        message.get('type') == 'outgoing',  # fromMe
                        datetime.now().isoformat()
                    ))
                    saved_count += 1
                    
                except Exception as e:
                    self.log(f"⚠️ שגיאה בשמירת הודעה: {e}", "WARNING")
                    continue
            
            conn.commit()
            conn.close()
            
            return saved_count
            
        except Exception as e:
            self.log(f"❌ שגיאה בשמירת הודעות למסד: {e}", "ERROR")
            return 0
    
    def _get_whatsapp_id_for_contact(self, contact_id: str) -> str:
        """קבלת whatsapp_id לפי contact_id"""
        try:
            conn = sqlite3.connect(self.contacts_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT whatsapp_id FROM contacts 
                WHERE contact_id = ?
                LIMIT 1
            """, (contact_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            else:
                return None
                
        except Exception as e:
            self.log(f"שגיאה בקבלת whatsapp_id: {e}", "ERROR")
            return None

    def _get_contact_name(self, chat_id):
        """קבלת שם איש הקשר מ-contacts.db"""
        try:
            conn = sqlite3.connect(self.contacts_db)
            cursor = conn.cursor()
            
            # חיפוש לפי מספר טלפון
            cursor.execute("""
                SELECT name FROM contacts 
                WHERE whatsapp_id = ? OR phone_number = ?
                LIMIT 1
            """, (chat_id, chat_id))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            else:
                # אם לא נמצא, נסה לחלץ שם מהמספר
                if '@c.us' in chat_id:
                    phone = chat_id.replace('@c.us', '')
                    return f"איש קשר {phone}"
                else:
                    return "איש קשר לא ידוע"
                    
        except Exception as e:
            self.log(f"⚠️ שגיאה בקבלת שם איש קשר: {e}", "WARNING")
            return "איש קשר לא ידוע"

    def _create_calendar_events(self, contact_id: str, start_dt: datetime, end_dt: datetime, whatsapp_id: str = None) -> int:
        """יצירת אירועי יומן עבור contact_id"""
        try:
            self.log(f"📅 מתחיל יצירת אירועי יומן עבור {contact_id}")
            self.log(f"📅 תקופה: {start_dt.strftime('%d/%m/%Y')} - {end_dt.strftime('%d/%m/%Y')}")

            # אם לא סופק whatsapp_id, נקבל אותו מהמסד נתונים
            if not whatsapp_id:
                whatsapp_id = self._get_whatsapp_id_for_contact(contact_id)
                if not whatsapp_id:
                    self.log(f"❌ לא נמצא whatsapp_id עבור {contact_id}")
                    return 0

            self.log(f"📱 משתמש ב-whatsapp_id: {whatsapp_id}")

            # בדיקה אם יש הודעות במסד הנתונים (משתמש ב-whatsapp_id!)
            conn = sqlite3.connect(self.messages_db)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT COUNT(*) FROM messages
                WHERE chat_id = ?
                AND timestamp BETWEEN ? AND ?
            """, (whatsapp_id, int(start_dt.timestamp() * 1000), int(end_dt.timestamp() * 1000)))

            messages_count = cursor.fetchone()[0]
            conn.close()

            self.log(f"📊 נמצאו {messages_count} הודעות במסד הנתונים עבור {contact_id} (whatsapp_id: {whatsapp_id})")

            if messages_count == 0:
                self.log("⚠️ אין הודעות במסד הנתונים - לא נוצרים אירועי יומן")
                return 0

            # שימוש במערכת TimeBro הקיימת (מעביר contact_id, לא whatsapp_id!)
            events_created = self.calendar_system.sync_calendar_for_contact(
                contact_id, start_dt, end_dt
            )
            self.log(f"📅 נוצרו {events_created} אירועי יומן")

            return events_created

        except Exception as e:
            self.log(f"❌ שגיאה ביצירת אירועי יומן: {e}", "ERROR")
            return 0

    def _mark_for_calendar(self, item_id: str, is_contact: bool = True):
        """סימון איש קשר/קבוצה לכלול ביומן"""
        try:
            if is_contact:
                conn = sqlite3.connect(self.contacts_db)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE contacts 
                    SET include_in_timebro = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE whatsapp_id = ?
                """, (item_id,))
            else:
                conn = sqlite3.connect(self.groups_db)
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE groups 
                    SET include_in_timebro = 1, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (item_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log(f"⚠️ שגיאה בסימון ליומן: {e}", "WARNING")

    def _update_sync_status(self, item_id: str, item_type: str, success: bool, messages_count: int = 0, events_count: int = 0):
        """עדכון סטטוס סינכרון"""
        try:
            # יצירת טבלת סטטוס סינכרון אם לא קיימת
            conn = sqlite3.connect(self.calendar_db)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sync_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_id TEXT NOT NULL,
                    item_type TEXT NOT NULL,
                    last_sync DATETIME,
                    success BOOLEAN,
                    messages_count INTEGER,
                    events_count INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # עדכון/הוספת סטטוס
            cursor.execute("""
                INSERT OR REPLACE INTO sync_status 
                (item_id, item_type, last_sync, success, messages_count, events_count, created_at)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (item_id, item_type, success, messages_count, events_count))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log(f"⚠️ שגיאה בעדכון סטטוס סינכרון: {e}", "WARNING")

    def _get_marked_contacts(self) -> List[str]:
        """קבלת רשימת אנשי קשר מסומנים ליומן"""
        try:
            conn = sqlite3.connect(self.contacts_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT contact_id FROM contacts 
                WHERE include_in_timebro = 1
            """)
            contacts = [row[0] for row in cursor.fetchall()]
            conn.close()
            return contacts
        except Exception as e:
            self.log(f"❌ שגיאה בקבלת אנשי קשר מסומנים: {e}", "ERROR")
            return []

    def _get_marked_groups(self) -> List[str]:
        """קבלת רשימת קבוצות מסומנות ליומן"""
        try:
            conn = sqlite3.connect(self.groups_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT group_id FROM groups 
                WHERE include_in_timebro = 1
            """)
            groups = [row[0] for row in cursor.fetchall()]
            conn.close()
            return groups
        except Exception as e:
            self.log(f"❌ שגיאה בקבלת קבוצות מסומנות: {e}", "ERROR")
            return []

    def get_sync_status(self, item_id: str) -> Dict:
        """קבלת סטטוס סינכרון של פריט"""
        try:
            conn = sqlite3.connect(self.calendar_db)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT last_sync, success, messages_count, events_count
                FROM sync_status 
                WHERE item_id = ?
                ORDER BY last_sync DESC
                LIMIT 1
            """, (item_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    "last_sync": result[0],
                    "success": bool(result[1]),
                    "messages_count": result[2] or 0,
                    "events_count": result[3] or 0
                }
            else:
                return {
                    "last_sync": None,
                    "success": False,
                    "messages_count": 0,
                    "events_count": 0
                }
                
        except Exception as e:
            self.log(f"❌ שגיאה בקבלת סטטוס סינכרון: {e}", "ERROR")
            return {
                "last_sync": None,
                "success": False,
                "messages_count": 0,
                "events_count": 0
            }

    def start_async_sync(self, sync_type: str, item_id: str, start_date: str, end_date: str) -> str:
        """התחלת סינכרון אסינכרוני"""
        sync_id = f"{sync_type}_{item_id}_{int(time.time())}"
        
        def sync_worker():
            try:
                if sync_type == "contact":
                    result = self.sync_contact_messages(item_id, start_date, end_date)
                elif sync_type == "group":
                    result = self.sync_group_messages(item_id, start_date, end_date)
                elif sync_type == "all":
                    result = self.sync_all_marked(start_date, end_date)
                else:
                    result = {"success": False, "error": "סוג סינכרון לא ידוע"}
                
                self.active_syncs[sync_id] = {
                    "status": "completed",
                    "result": result,
                    "completed_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                self.active_syncs[sync_id] = {
                    "status": "error",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }
        
        # התחלת הסינכרון ברקע
        thread = threading.Thread(target=sync_worker)
        thread.daemon = True
        thread.start()
        
        self.active_syncs[sync_id] = {
            "status": "running",
            "started_at": datetime.now().isoformat(),
            "sync_type": sync_type,
            "item_id": item_id,
            "start_date": start_date,
            "end_date": end_date
        }
        
        return sync_id

    def get_sync_progress(self, sync_id: str) -> Dict:
        """קבלת התקדמות סינכרון"""
        return self.active_syncs.get(sync_id, {"status": "not_found"})
