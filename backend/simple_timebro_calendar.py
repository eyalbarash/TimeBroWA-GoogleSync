#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מערכת TimeBro פשוטה ללא AI
מעדכנת ביומן כל שיחה עם אנשי קשר מסומנים
הודעות במרחק של עד 10 דקות נחשבות כאירוע אחד
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from contacts_list import CONTACTS_CONFIG, get_contact_company
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class SimpleTimeBroCalendar:
    def __init__(self):
        self.timebro_calendar_id = 'c_mjbk37j51lkl4pl8i9tk31ek3o@group.calendar.google.com'
        self.db_main = 'whatsapp_messages_webjs.db'
        self.db_calendar = 'timebro_calendar.db'
        
        # Google Calendar API
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.credentials_file = 'credentials.json'
        self.token_file = 'token.json'
        
        # רשימת אנשי הקשר המאושרים - רק אלה שביקשת
        self.approved_contacts = set()
        self._load_approved_contacts()
        
        # מרחק זמן לקיבוץ הודעות (60 דקות - שעה)
        self.message_grouping_minutes = 60

    def _load_approved_contacts(self):
        """טעינת אנשי הקשר המאושרים מהמסד הנתונים"""
        try:
            import sqlite3
            
            # טעינת אנשי קשר מסומנים לסינכרון
            conn = sqlite3.connect('whatsapp_contacts_groups.db')
            cursor = conn.cursor()
            
            # אנשי קשר
            cursor.execute('SELECT name FROM contacts WHERE include_in_timebro = 1')
            contacts = cursor.fetchall()
            for contact in contacts:
                self.approved_contacts.add(contact[0])
            
            # קבוצות
            cursor.execute('SELECT subject FROM groups WHERE include_in_timebro = 1')
            groups = cursor.fetchall()
            for group in groups:
                self.approved_contacts.add(group[0])
            
            conn.close()
            
            self.log(f"✅ נטענו {len(self.approved_contacts)} אנשי קשר וקבוצות מאושרים מהמסד")
            return self.approved_contacts
        except Exception as e:
            self.log(f"❌ שגיאה בטעינת אנשי קשר מהמסד: {e}", "ERROR")
            return set()

    def is_approved_contact(self, contact_name):
        """בדיקה חכמה יותר אם איש קשר מאושר"""
        if not contact_name or len(contact_name.strip()) < 2:
            return False
        
        contact_clean = contact_name.strip().lower()
        
        # בדיקה מדויקת ראשונה
        for approved in self.approved_contacts:
            approved_clean = approved.strip().lower()
            if contact_clean == approved_clean:
                return True
        
        # בדיקה חלקית - אם השם מכיל או מוכל באישור
        for approved in self.approved_contacts:
            approved_clean = approved.strip().lower()
            # אם השם מכיל את השם המאושר או להפך
            if approved_clean in contact_clean or contact_clean in approved_clean:
                # וודא שהשם ארוך מספיק כדי למנוע false positives
                min_len = min(len(approved_clean), len(contact_clean))
                if min_len >= 4:  # שמות של לפחות 4 תווים
                    return True
        
        # בדיקה לפי מילים נפרדות (שם פרטי או משפחה)
        contact_words = contact_clean.split()
        for approved in self.approved_contacts:
            approved_words = approved.strip().lower().split()
            
            # אם יש התאמה של לפחות מילה אחת ארוכה
            for contact_word in contact_words:
                for approved_word in approved_words:
                    if len(contact_word) >= 3 and len(approved_word) >= 3:
                        if contact_word == approved_word:
                            return True
        
        return False
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emoji = "📅" if level == "INFO" else "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "🔄"
        log_entry = f"[{timestamp}] {emoji} {message}"
        print(log_entry)
        
        # שמירה בלוג
        with open('simple_timebro.log', 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")

    def init_database(self):
        """אתחול מסד נתונים"""
        conn = sqlite3.connect(self.db_calendar)
        cursor = conn.cursor()
        
        # טבלת אירועים פשוטה
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simple_calendar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_name TEXT NOT NULL,
                company TEXT,
                start_datetime TEXT NOT NULL,
                end_datetime TEXT NOT NULL,
                total_messages INTEGER,
                my_messages INTEGER,
                their_messages INTEGER,
                event_content TEXT,
                google_event_id TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        self.log("✅ מסד נתונים אותחל", "SUCCESS")

    def authenticate_google_calendar(self):
        """אימות Google Calendar API"""
        creds = None
        
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_file):
                    self.log("❌ קובץ credentials.json לא נמצא", "ERROR")
                    return None
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            self.log("✅ חיבור לGoogle Calendar הצליח", "SUCCESS")
            return service
        except Exception as e:
            self.log(f"❌ שגיאה בחיבור לGoogle Calendar: {e}", "ERROR")
            return None

    def get_messages_for_date_range(self, start_date, end_date):
        """קבלת הודעות מטווח תאריכים מאנשי קשר מאושרים בלבד"""
        try:
            conn = sqlite3.connect(self.db_main)
            cursor = conn.cursor()
            
            # חישוב timestamps
            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)
            
            # שאילתה להודעות מכל אנשי הקשר
            cursor.execute("""
                SELECT 
                    contact_name,
                    contact_number,
                    message_body,
                    timestamp,
                    is_from_me,
                    created_at
                FROM messages
                WHERE 
                    timestamp >= ? AND timestamp <= ?
                    AND contact_name IS NOT NULL
                    AND message_body IS NOT NULL
                    AND LENGTH(TRIM(message_body)) > 0
                ORDER BY contact_name, timestamp ASC
            """, (start_timestamp, end_timestamp))
            
            all_messages = cursor.fetchall()
            conn.close()
            
            # סינון לאנשי קשר מאושרים בלבד
            approved_messages = []
            for msg in all_messages:
                contact_name = msg[0]
                if self.is_approved_contact(contact_name):
                    approved_messages.append(msg)
            
            self.log(f"נמצאו {len(approved_messages)} הודעות מאנשי קשר מאושרים (מתוך {len(all_messages)} סה\"כ)")
            
            # רשימת אנשי קשר שיש להם הודעות
            contacts_with_messages = set()
            for msg in approved_messages:
                contacts_with_messages.add(msg[0])
            
            self.log(f"📊 אנשי קשר עם הודעות בתקופה: {len(contacts_with_messages)}")
            return approved_messages
            
        except Exception as e:
            self.log(f"❌ שגיאה בקבלת הודעות: {e}", "ERROR")
            return []

    def group_messages_by_contact_and_time(self, messages):
        """קיבוץ הודעות לפי איש קשר ולאחר מכן לפי פערי זמן של שעה"""
        # שלב 1: קיבוץ לפי איש קשר
        messages_by_contact = {}
        
        for msg in messages:
            contact_name = msg[0]
            timestamp = msg[3]
            message_datetime = datetime.fromtimestamp(timestamp / 1000)
            
            if contact_name not in messages_by_contact:
                messages_by_contact[contact_name] = []
            
            messages_by_contact[contact_name].append({
                'content': msg[2],
                'timestamp': timestamp,
                'datetime': message_datetime,
                'is_from_me': bool(msg[4]),
                'contact_name': contact_name
            })
        
        # שלב 2: קיבוץ כל איש קשר למספר מקבצים לפי פערי זמן של שעה
        all_conversations = {}
        
        for contact_name, contact_messages in messages_by_contact.items():
            # מיון הודעות לפי זמן
            contact_messages.sort(key=lambda x: x['timestamp'])
            
            # יצירת מקבצים לפי פערי זמן
            conversation_groups = []
            current_group = [contact_messages[0]]
            last_time = contact_messages[0]['datetime']
            
            for msg in contact_messages[1:]:
                time_diff_minutes = (msg['datetime'] - last_time).total_seconds() / 60
                
                if time_diff_minutes <= 60:  # פחות משעה - אותו מקבץ
                    current_group.append(msg)
                    last_time = msg['datetime']  # עדכון last_time גם כאן!
                else:  # יותר משעה - מקבץ חדש
                    conversation_groups.append(current_group)
                    current_group = [msg]
                    last_time = msg['datetime']
            
            # הוספת המקבץ האחרון
            conversation_groups.append(current_group)
            
            # יצירת שם ייחודי לכל מקבץ
            for i, group in enumerate(conversation_groups):
                unique_key = f"{contact_name}_{i+1}" if len(conversation_groups) > 1 else contact_name
                all_conversations[unique_key] = {
                    'contact_name': contact_name,
                    'start_time': group[0]['datetime'],
                    'end_time': group[-1]['datetime'],
                    'messages': group
                }
        
        return all_conversations

    def format_conversation_content(self, conversation):
        """עיצוב תוכן השיחה בפורמט עם RTL ויישור"""
        messages = conversation['messages']
        formatted_lines = []
        
        # הודעות
        my_count = 0
        their_count = 0
        
        for msg in messages:
            time_str = msg['datetime'].strftime('%H:%M')
            content = (msg.get('content') or msg.get('message_body') or '').strip()
            
            # דילוג על הודעות ריקות
            if not content:
                continue
            
            if msg['is_from_me']:
                # הודעה שלי - RTL מיושר ימין
                formatted_lines.append(f"‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎‏‏‎ ‎[{time_str}] [אייל]: {content}")
                my_count += 1
            else:
                # הודעת הלקוח - RTL מיושר שמאל
                contact_name = msg.get('contact_name', 'לא ידוע')
                formatted_lines.append(f"[{time_str}] [{contact_name}]: {content}")
                their_count += 1
        
        return '\n'.join(formatted_lines), my_count, their_count

    def create_calendar_event(self, contact_name, conversation, service):
        """יצירת אירוע ביומן"""
        try:
            # קבלת שם החברה מהמסד
            company_name = self._get_company_name(contact_name)
            company, color = get_contact_company(contact_name)
            
            # הכנת תוכן האירוע
            content, my_messages, their_messages = self.format_conversation_content(conversation)
            
            # כותרת האירוע - שם החברה (או שם איש הקשר אם אין) עם אימוג'י צ'ט
            start_time = conversation['start_time']
            title = f"💬 {company_name if company_name else contact_name}"
            
            # זמני האירוע
            # אם השיחה קצרה מ-5 דקות, נעשה אותה 5 דקות (מינימום)
            duration = conversation['end_time'] - conversation['start_time']
            if duration < timedelta(minutes=5):
                end_time = conversation['start_time'] + timedelta(minutes=5)
            else:
                end_time = conversation['end_time']
            
            # בדיקה אם אירוע דומה כבר קיים (למניעת כפילויות)
            if self._event_exists(service, title, start_time, end_time):
                self.log(f"⚠️ אירוע דומה כבר קיים: {title[:50]}...", "WARNING")
                return False
            
            # מבנה אירוע Google Calendar
            calendar_event = {
                'summary': title,
                'description': content,
                'start': {
                    'dateTime': conversation['start_time'].replace(microsecond=0).isoformat(),
                    'timeZone': 'Asia/Jerusalem'
                },
                'end': {
                    'dateTime': end_time.replace(microsecond=0).isoformat(),
                    'timeZone': 'Asia/Jerusalem'
                },
                'colorId': color,
                'reminders': {
                    'useDefault': False,
                    'overrides': []
                }
            }
            
            # יצירת האירוע
            created_event = service.events().insert(
                calendarId=self.timebro_calendar_id,
                body=calendar_event
            ).execute()
            
            # שמירה במסד הנתונים המקומי
            self.save_event_to_db(
                contact_name=contact_name,
                company=company,
                start_datetime=conversation['start_time'],
                end_datetime=end_time,
                total_messages=len(conversation['messages']),
                my_messages=my_messages,
                their_messages=their_messages,
                event_content=content,
                google_event_id=created_event.get('id')
            )
            
            self.log(f"✅ נוצר אירוע: {title[:50]}...", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ שגיאה ביצירת אירוע: {e}", "ERROR")
            return False

    def save_event_to_db(self, **kwargs):
        """שמירת אירוע במסד הנתונים המקומי"""
        try:
            conn = sqlite3.connect(self.db_calendar)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO simple_calendar_events 
                (contact_name, company, start_datetime, end_datetime, 
                 total_messages, my_messages, their_messages, 
                 event_content, google_event_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                kwargs['contact_name'],
                kwargs['company'],
                kwargs['start_datetime'].isoformat(),
                kwargs['end_datetime'].isoformat(),
                kwargs['total_messages'],
                kwargs['my_messages'],
                kwargs['their_messages'],
                kwargs['event_content'],
                kwargs['google_event_id']
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log(f"❌ שגיאה בשמירת אירוע במסד: {e}", "ERROR")

    def _get_company_name(self, contact_name):
        """קבלת שם החברה מהמסד"""
        try:
            conn = sqlite3.connect('whatsapp_contacts_groups.db')
            cursor = conn.cursor()
            
            # חיפוש לפי שם
            cursor.execute("""
                SELECT company_name FROM contacts 
                WHERE name = ? OR push_name = ?
                LIMIT 1
            """, (contact_name, contact_name))
            
            result = cursor.fetchone()
            conn.close()
            
            if result and result[0]:
                return result[0]
            
            # אם לא נמצא באנשי קשר, נסה בקבוצות
            conn = sqlite3.connect('whatsapp_contacts_groups.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT company_name FROM groups 
                WHERE subject = ?
                LIMIT 1
            """, (contact_name,))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result and result[0] else None
            
        except Exception as e:
            self.log(f"⚠️ שגיאה בקבלת שם חברה: {e}", "WARNING")
            return None
    
    def _event_exists(self, service, title, start_time, end_time):
        """בדיקה אם אירוע דומה כבר קיים"""
        try:
            # חיפוש אירועים עם אותה כותרת באותו יום
            start_of_day = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = start_time.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            events_result = service.events().list(
                calendarId=self.timebro_calendar_id,
                timeMin=start_of_day.isoformat() + '+03:00',
                timeMax=end_of_day.isoformat() + '+03:00',
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            for event in events:
                if event.get('summary') == title:
                    # בדיקה אם הזמנים חופפים - המרה ל-timezone aware
                    event_start_str = event['start']['dateTime']
                    event_end_str = event['end']['dateTime']
                    
                    # המרה ל-datetime objects עם timezone
                    if event_start_str.endswith('Z'):
                        event_start = datetime.fromisoformat(event_start_str.replace('Z', '+00:00'))
                    else:
                        event_start = datetime.fromisoformat(event_start_str)
                    
                    if event_end_str.endswith('Z'):
                        event_end = datetime.fromisoformat(event_end_str.replace('Z', '+00:00'))
                    else:
                        event_end = datetime.fromisoformat(event_end_str)
                    
                    # המרת הזמנים המקומיים ל-timezone aware
                    from datetime import timezone
                    start_time_aware = start_time.replace(tzinfo=timezone.utc)
                    end_time_aware = end_time.replace(tzinfo=timezone.utc)
                    
                    # אם יש חפיפה בזמנים
                    if (start_time_aware < event_end and end_time_aware > event_start):
                        return True
            
            return False
            
        except Exception as e:
            self.log(f"❌ שגיאה בבדיקת קיום אירוע: {e}", "ERROR")
            return False

    def debug_contact_matching(self, start_date, end_date):
        """בדיקת אנשי קשר זמינים לדיבוג"""
        try:
            conn = sqlite3.connect(self.db_main)
            cursor = conn.cursor()
            
            # קבלת כל השמות הייחודיים
            start_timestamp = int(start_date.timestamp() * 1000)
            end_timestamp = int(end_date.timestamp() * 1000)
            
            cursor.execute("""
                SELECT DISTINCT contact_name, COUNT(*) as msg_count
                FROM messages
                WHERE 
                    timestamp >= ? AND timestamp <= ?
                    AND contact_name IS NOT NULL
                    AND contact_name != ''
                    AND LENGTH(TRIM(contact_name)) > 2
                GROUP BY contact_name
                ORDER BY msg_count DESC
            """, (start_timestamp, end_timestamp))
            
            all_contacts = cursor.fetchall()
            conn.close()
            
            self.log(f"🔍 נמצאו {len(all_contacts)} אנשי קשר עם הודעות בתקופה")
            
            # הצגת 10 אנשי הקשר הראשונים
            if all_contacts:
                self.log("📊 אנשי הקשר עם הכי הרבה הודעות:")
                for contact_name, msg_count in all_contacts[:10]:
                    self.log(f"  - {contact_name} ({msg_count} הודעות)")
            
            return all_contacts, []
            
        except Exception as e:
            self.log(f"❌ שגיאה בבדיקת אנשי קשר: {e}", "ERROR")
            return [], []

    def sync_calendar_for_contact(self, contact_id, start_date, end_date):
        """סינכרון יומן עבור איש קשר ספציפי"""
        try:
            # קבלת whatsapp_id עבור contact_id
            conn = sqlite3.connect('whatsapp_contacts_groups.db')
            cursor = conn.cursor()
            cursor.execute('SELECT whatsapp_id FROM contacts WHERE contact_id = ?', (contact_id,))
            result = cursor.fetchone()
            conn.close()
            
            if not result:
                self.log(f"❌ לא נמצא whatsapp_id עבור contact_id {contact_id}")
                return 0
            
            whatsapp_id = result[0]
            self.log(f"📱 משתמש ב-whatsapp_id: {whatsapp_id}")
            
            # קבלת הודעות עבור איש הקשר
            conn = sqlite3.connect(self.db_main)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM messages 
                WHERE chat_id = ? 
                AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp
            """, (whatsapp_id, int(start_date.timestamp() * 1000), int(end_date.timestamp() * 1000)))
            
            messages = cursor.fetchall()
            conn.close()
            
            if not messages:
                return 0
            
            # קיבוץ הודעות לאירועים
            events = self._group_messages_into_events(messages)
            
            # יצירת אירועי יומן
            events_created = 0
            for event in events:
                if self._create_calendar_event(event):
                    events_created += 1
            
            return events_created
            
        except Exception as e:
            self.log(f"❌ שגיאה בסינכרון איש קשר: {e}", "ERROR")
            return 0
    
    def _group_messages_into_events(self, messages):
        """קיבוץ הודעות לאירועים לפי זמן"""
        if not messages:
            return []
        
        events = []
        current_event = []
        last_timestamp = None
        
        for message in messages:
            # המרת timestamp
            timestamp = datetime.fromtimestamp(message[6] / 1000)  # timestamp הוא במילישניות
            
            if last_timestamp is None:
                # הודעה ראשונה
                current_event = [message]
                last_timestamp = timestamp
            else:
                # בדיקה אם ההודעה קרובה להודעה הקודמת (בתוך שעה אחת)
                time_diff = timestamp - last_timestamp
                if time_diff.total_seconds() <= self.message_grouping_minutes * 60:
                    # הודעה באותו אירוע
                    current_event.append(message)
                else:
                    # הודעה חדשה - שמירת האירוע הקודם
                    if current_event:
                        events.append(current_event)
                    current_event = [message]
                
                last_timestamp = timestamp
        
        # הוספת האירוע האחרון
        if current_event:
            events.append(current_event)
        
        return events
    
    def _create_calendar_event(self, event_messages):
        """יצירת אירוע יומן מקבוצת הודעות"""
        try:
            if not event_messages:
                return False
            
            # קבלת פרטי האירוע
            first_message = event_messages[0]
            last_message = event_messages[-1]
            
            # זמני התחלה וסיום
            start_time = datetime.fromtimestamp(first_message[6] / 1000)
            end_time = datetime.fromtimestamp(last_message[6] / 1000)

            # מינימום 5 דקות לאירוע
            if (end_time - start_time).total_seconds() < 300:  # 5 minutes
                end_time = start_time + timedelta(minutes=5)
            
            # שם האירוע - רק השם עם אימוג'י צ'ט
            contact_name = first_message[3] or "איש קשר לא ידוע"
            event_title = f"💬 {contact_name}"
            
            # תוכן האירוע - הודעות עם RTL
            event_description = self._format_messages_for_calendar(event_messages)
            
            # יצירת האירוע
            service = self.authenticate_google_calendar()
            if not service:
                return False
            
            # הכנת conversation object
            conversation = {
                'start_time': start_time,
                'end_time': end_time,
                'content': event_description,
                'messages': self._convert_messages_to_dict(event_messages)  # המרת הודעות
            }
            
            return self.create_calendar_event(
                contact_name=contact_name,
                conversation=conversation,
                service=service
            )
            
        except Exception as e:
            self.log(f"❌ שגיאה ביצירת אירוע יומן: {e}", "ERROR")
            return False
    
    def _format_messages_for_calendar(self, messages):
        """עיצוב הודעות לתצוגה ביומן עם RTL"""
        try:
            formatted_messages = []
            
            for message in messages:
                # פרטי ההודעה
                message_id = message[0]
                contact_name = message[3] or "לא ידוע"
                message_body = message[4] or ""
                timestamp = datetime.fromtimestamp(message[6] / 1000)
                is_from_me = message[7]
                
                # עיצוב RTL
                if is_from_me:
                    # הודעה שלי - מיושרת לימין
                    formatted = f"<div dir='rtl' style='text-align: right; margin: 5px 0;'>"
                    formatted += f"<strong>אני ({timestamp.strftime('%H:%M')}):</strong><br>"
                    formatted += f"{message_body}"
                    formatted += "</div>"
                else:
                    # הודעה של הלקוח - מיושרת לשמאל
                    formatted = f"<div dir='rtl' style='text-align: left; margin: 5px 0;'>"
                    formatted += f"<strong>{contact_name} ({timestamp.strftime('%H:%M')}):</strong><br>"
                    formatted += f"{message_body}"
                    formatted += "</div>"
                
                formatted_messages.append(formatted)
            
            return "<br>".join(formatted_messages)
            
        except Exception as e:
            self.log(f"❌ שגיאה בעיצוב הודעות: {e}", "ERROR")
            return "שגיאה בעיצוב הודעות"
    
    def _convert_messages_to_dict(self, messages):
        """המרת הודעות מ-tuple ל-dictionary"""
        try:
            converted_messages = []
            
            for message in messages:
                # פרטי ההודעה
                message_dict = {
                    'id': message[0],
                    'chat_id': message[1],
                    'contact_number': message[2],
                    'contact_name': message[3] or "לא ידוע",
                    'message_body': message[4] or "",
                    'content': message[4] or "",  # הוספת content
                    'message_type': message[5] or "text",
                    'timestamp': message[6],
                    'datetime': datetime.fromtimestamp(message[6] / 1000),  # הוספת datetime object
                    'is_from_me': message[7],
                    'created_at': message[8] if len(message) > 8 else None
                }
                converted_messages.append(message_dict)
            
            return converted_messages
            
        except Exception as e:
            self.log(f"❌ שגיאה בהמרת הודעות: {e}", "ERROR")
            return []

    def sync_calendar_for_period(self, start_date, end_date):
        """סינכרון יומן לתקופה מסוימת"""
        self.log(f"🔄 מתחיל סינכרון יומן מ-{start_date.strftime('%d/%m/%Y')} עד {end_date.strftime('%d/%m/%Y')}")
        
        # בדיקת התאמות לדיבוג
        matched, unmatched = self.debug_contact_matching(start_date, end_date)
        
        # אתחול
        self.init_database()
        
        # אימות Google Calendar
        service = self.authenticate_google_calendar()
        if not service:
            return False
        
        # קבלת הודעות
        messages = self.get_messages_for_date_range(start_date, end_date)
        if not messages:
            self.log("❌ לא נמצאו הודעות לעיבוד", "ERROR")
            return False
        
        # קיבוץ הודעות
        grouped = self.group_messages_by_contact_and_time(messages)
        
        # יצירת אירועים - מספר אירועים לכל איש קשר לפי מקבצי זמן
        total_events = 0
        successful_events = 0
        
        for unique_key, conversation in grouped.items():
            # יצירת אירוע לכל מקבץ
            contact_name = conversation['contact_name']
            total_events += 1
            if self.create_calendar_event(contact_name, conversation, service):
                successful_events += 1
        
        # סיכום
        self.log(f"✅ הושלם: {successful_events}/{total_events} אירועים נוצרו", "SUCCESS")
        return successful_events > 0

def main():
    """הפעלה ראשית"""
    calendar_system = SimpleTimeBroCalendar()
    
    print("📅 מערכת TimeBro פשוטה - ללא AI")
    print("=" * 60)
    
    # בדיקת הטווח הזמין במסד הנתונים
    try:
        conn = sqlite3.connect(calendar_system.db_main)
        cursor = conn.cursor()
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages WHERE timestamp > 0")
        min_ts, max_ts = cursor.fetchone()
        conn.close()
        
        if min_ts and max_ts:
            db_start = datetime.fromtimestamp(min_ts / 1000)
            db_end = datetime.fromtimestamp(max_ts / 1000)
            print(f"🗄️ נתונים זמינים במסד: {db_start.strftime('%d/%m/%Y')} - {db_end.strftime('%d/%m/%Y')}")
            
            # השתמש בטווח הזמין במסד הנתונים
            start_date = db_start
            end_date = db_end
        else:
            # אם אין נתונים, השתמש בטווח הברירת מחדל
            start_date = datetime(2025, 8, 1)
            end_date = datetime.now()
            print("⚠️ לא נמצאו נתונים במסד, משתמש בטווח ברירת מחדל")
    except Exception as e:
        print(f"⚠️ שגיאה בבדיקת המסד: {e}")
        start_date = datetime(2025, 8, 1)
        end_date = datetime.now()
    
    print(f"תקופת סינכרון: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
    print(f"כמות אנשי קשר מאושרים: {len(calendar_system.approved_contacts)}")
    print()
    
    # הרצת הסינכרון
    success = calendar_system.sync_calendar_for_period(start_date, end_date)
    
    if success:
        print("\n🎉 סינכרון הושלם בהצלחה!")
        print("📅 בדוק את יומן timebro ב-Google Calendar")
    else:
        print("\n❌ סינכרון נכשל")
        print("📋 בדוק לוגים: simple_timebro.log")

if __name__ == "__main__":
    main()
