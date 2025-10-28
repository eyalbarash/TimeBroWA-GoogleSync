#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
תיקון בעיות יומן TimeBro - מחיקת אירועים שגויים ויצירת מערכת נכונה
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from contacts_list import CONTACTS_CONFIG, list_all_contacts, get_contact_company

# Google Calendar API
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class CalendarFixer:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.token_file = 'token.json'
        
        # רשימת אנשי הקשר הנכונה מהקובץ
        self.all_contacts = list_all_contacts()
        self.valid_contact_names = [contact['name'] for contact in self.all_contacts]
        
        # תקופת עבודה: מ-25 באוגוסט עד היום
        self.start_date = datetime(2025, 8, 25)
        self.end_date = datetime.now()

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        elif level == "WARNING":
            emoji = "⚠️"
        else:
            emoji = "🔧"
        print(f"[{timestamp}] {emoji} {message}")

    def get_calendar_service(self):
        """חיבור לGoogle Calendar API"""
        try:
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:
            self.log(f"שגיאה בחיבור לGoogle Calendar: {e}", "ERROR")
            return None

    def find_timebro_calendar_id(self, service):
        """מציאת ID של יומן timebro"""
        try:
            calendars_result = service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            for cal in calendars:
                if cal['summary'].lower() == 'timebro':
                    self.log(f"נמצא יומן timebro: {cal['id']}")
                    return cal['id']
            
            # אם לא קיים - יוצר חדש
            self.log("יומן timebro לא קיים - יוצר חדש...")
            calendar = {
                'summary': 'timebro',
                'description': 'יומן אוטומטי מהשיחות בוואטסאפ - נכון ומסודר',
                'timeZone': 'Asia/Jerusalem'
            }
            
            created_calendar = service.calendars().insert(body=calendar).execute()
            timebro_id = created_calendar['id']
            self.log(f"✅ יומן timebro נוצר: {timebro_id}", "SUCCESS")
            return timebro_id
            
        except Exception as e:
            self.log(f"שגיאה במציאת יומן timebro: {e}", "ERROR")
            return None

    def delete_wrong_events_from_google(self, service):
        """מחיקת אירועים שגויים מGoogle Calendar"""
        self.log("מחפש ומוחק אירועים שגויים...")
        
        try:
            # בדיקת יומן ראשי (Eyal Barash)
            events_result = service.events().list(
                calendarId='primary',
                timeMin=self.start_date.isoformat() + 'Z',
                timeMax=self.end_date.isoformat() + 'Z',
                maxResults=500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            self.log(f"נמצאו {len(events)} אירועים ביומן הראשי")
            
            deleted_count = 0
            wrong_sources = ['שיתופים😏', 'חדשות בזמן', 'חדשות מהרגע', 'קהילת']
            
            for event in events:
                title = event.get('summary', '')
                description = event.get('description', '')
                
                # בדיקה אם זה אירוע שגוי
                is_wrong = False
                
                # בדיקה 1: אירועים מקבוצות לא רלוונטיות
                if any(wrong_source in title for wrong_source in wrong_sources):
                    is_wrong = True
                    reason = "קבוצה לא רלוונטית"
                
                # בדיקה 2: אירועים שלא מהרשימה הנכונה
                elif '[TimeBro]' in title and not any(contact in title for contact in self.valid_contact_names):
                    is_wrong = True
                    reason = "לא מרשימת אנשי הקשר"
                
                # בדיקה 3: כפילויות
                elif title.count('מייק ביקוב') > 1:
                    is_wrong = True
                    reason = "כפילות בשם"
                
                if is_wrong:
                    try:
                        service.events().delete(
                            calendarId='primary',
                            eventId=event['id']
                        ).execute()
                        
                        deleted_count += 1
                        self.log(f"   🗑️ נמחק: {title[:50]}... ({reason})")
                        
                    except Exception as e:
                        self.log(f"   ❌ שגיאה במחיקת {title[:30]}: {e}", "ERROR")
            
            self.log(f"✅ נמחקו {deleted_count} אירועים שגויים", "SUCCESS")
            return deleted_count
            
        except Exception as e:
            self.log(f"שגיאה במחיקת אירועים: {e}", "ERROR")
            return 0

    def clean_local_database(self):
        """ניקוי מסד הנתונים המקומי"""
        self.log("מנקה מסד נתונים מקומי...")
        
        try:
            conn = sqlite3.connect('timebro_calendar.db')
            cursor = conn.cursor()
            
            # מחיקת אירועים שגויים
            wrong_sources = ['שיתופים😏', 'חדשות בזמן', 'חדשות מהרגע', 'קהילת']
            
            for source in wrong_sources:
                cursor.execute("""
                    DELETE FROM calendar_events 
                    WHERE source_contact LIKE ?
                """, (f'%{source}%',))
                
                deleted = cursor.rowcount
                if deleted > 0:
                    self.log(f"   🗑️ נמחקו {deleted} אירועים מ-{source}")
            
            # מחיקת כפילויות
            cursor.execute("""
                DELETE FROM calendar_events 
                WHERE id NOT IN (
                    SELECT MIN(id) 
                    FROM calendar_events 
                    GROUP BY title, start_datetime
                )
            """)
            
            duplicates_deleted = cursor.rowcount
            if duplicates_deleted > 0:
                self.log(f"   🗑️ נמחקו {duplicates_deleted} כפילויות")
            
            conn.commit()
            conn.close()
            
            self.log("✅ מסד נתונים מקומי נוקה", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"שגיאה בניקוי מסד מקומי: {e}", "ERROR")
            return False

    def create_correct_events(self, service, timebro_calendar_id):
        """יצירת אירועים נכונים רק מאנשי הקשר ברשימה"""
        self.log("יוצר אירועים נכונים מרשימת אנשי הקשר...")
        
        # חיפוש הודעות מאנשי הקשר ברשימה בלבד
        valid_messages = self.get_messages_from_valid_contacts()
        
        if not valid_messages:
            self.log("לא נמצאו הודעות מאנשי הקשר ברשימה")
            return 0
        
        events_created = 0
        
        for contact, messages in valid_messages.items():
            try:
                company, color = get_contact_company(contact)
                self.log(f"מעבד {contact} ({company}) - {len(messages)} הודעות")
                
                # סינון הודעות עם פוטנציאל יומן אמיתי
                calendar_messages = []
                for msg in messages:
                    content = msg.get('content', '')
                    
                    # מילות מפתח חזקות לאירועי יומן
                    strong_keywords = [
                        'פגישה', 'מפגש', 'נפגש', 'בואו נקבע',
                        'דדליין', 'עד יום', 'תאריך יעד',
                        'תזכיר לי', 'תזכורת', 'לזכור',
                        'בשעה', 'מחר ב', 'היום ב'
                    ]
                    
                    if any(keyword in content for keyword in strong_keywords) and len(content) > 30:
                        calendar_messages.append(msg)
                
                # יצירת אירועים איכותיים
                for msg in calendar_messages:
                    event_data = self.create_quality_event(msg, contact, company)
                    
                    if event_data:
                        success = self.create_calendar_event_correctly(
                            event_data, service, timebro_calendar_id, color
                        )
                        
                        if success:
                            events_created += 1
                            self.log(f"   ✅ אירוע איכותי: {event_data['title'][:40]}...")
                
            except Exception as e:
                self.log(f"שגיאה בעיבוד {contact}: {e}", "ERROR")
        
        return events_created

    def get_messages_from_valid_contacts(self):
        """קבלת הודעות רק מאנשי הקשר ברשימה הנכונה"""
        valid_messages = {}
        
        try:
            # בדיקה בכל המסדים
            databases = [
                ('whatsapp_messages.db', 'august_messages'),
                ('whatsapp_messages_webjs.db', 'messages')
            ]
            
            for db_path, table_name in databases:
                if not os.path.exists(db_path):
                    continue
                    
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                for contact_name in self.valid_contact_names:
                    if table_name == 'august_messages':
                        cursor.execute("""
                            SELECT id, datetime_str, sender, content
                            FROM august_messages
                            WHERE (sender LIKE ? OR sender LIKE ?)
                            AND datetime_str >= ?
                            ORDER BY timestamp ASC
                        """, (f'%{contact_name}%', f'%{contact_name.split()[0]}%', 
                              self.start_date.strftime('%Y-%m-%d')))
                    else:
                        start_timestamp = int(self.start_date.timestamp())
                        cursor.execute("""
                            SELECT id, contact_name, message_body, timestamp
                            FROM messages
                            WHERE (contact_name LIKE ? OR contact_name LIKE ?)
                            AND timestamp >= ?
                            ORDER BY timestamp ASC
                        """, (f'%{contact_name}%', f'%{contact_name.split()[0]}%', start_timestamp))
                    
                    rows = cursor.fetchall()
                    if rows:
                        if contact_name not in valid_messages:
                            valid_messages[contact_name] = []
                        
                        for row in rows:
                            if table_name == 'august_messages':
                                valid_messages[contact_name].append({
                                    'content': row[3] or '',
                                    'datetime': row[1] or '',
                                    'sender': row[2] or ''
                                })
                            else:
                                dt = datetime.fromtimestamp(row[3])
                                valid_messages[contact_name].append({
                                    'content': row[2] or '',
                                    'datetime': dt.isoformat(),
                                    'sender': row[1] or ''
                                })
                
                conn.close()
            
            self.log(f"נמצאו הודעות מ-{len(valid_messages)} אנשי קשר מהרשימה")
            return valid_messages
            
        except Exception as e:
            self.log(f"שגיאה בקבלת הודעות: {e}", "ERROR")
            return {}

    def create_quality_event(self, message, contact, company):
        """יצירת אירוע איכותי מהודעה"""
        content = message.get('content', '')
        
        # בדיקה שזה באמת ראוי לאירוע יומן
        quality_indicators = [
            'פגישה', 'נפגש', 'בואו נקבע',
            'דדליין', 'עד יום', 
            'תזכיר לי', 'תזכורת',
            'בשעה', 'מחר ב-', 'היום ב-'
        ]
        
        if not any(indicator in content for indicator in quality_indicators):
            return None
        
        if len(content) < 30:  # הודעות קצרות מדי
            return None
        
        # יצירת כותרת ותיאור איכותיים
        if 'פגישה' in content or 'נפגש' in content:
            title = f"פגישה עם {contact}"
            category = 'meeting'
            duration = 60
        elif 'דדליין' in content or 'עד יום' in content:
            title = f"דדליין - {contact}"
            category = 'deadline'
            duration = 30
        elif 'תזכיר' in content or 'תזכורת' in content:
            title = f"תזכורת - {contact}"
            category = 'reminder'
            duration = 15
        else:
            # חילוץ נושא מהתוכן
            words = content.split()[:8]
            clean_words = [w for w in words if len(w) > 2 and w not in ['את', 'של', 'עם', 'על']][:4]
            subject = ' '.join(clean_words) if clean_words else 'משימה'
            title = f"{contact} - {subject}"
            category = 'task'
            duration = 45
        
        # הכנת תיאור מפורט
        description = f"""📞 איש קשר: {contact} ({company})
📅 תאריך מקורי: {message.get('datetime', '')[:10]}
🏢 חברה: {company}

💬 תוכן ההודעה:
{content[:300]}{'...' if len(content) > 300 else ''}

🤖 נוצר אוטומטית ע"י TimeBro Calendar
⏰ נוצר: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""

        return {
            'title': title,
            'description': description,
            'date': self.extract_date_from_message(message),
            'time': self.extract_time_from_message(message, category),
            'duration_minutes': duration,
            'category': category,
            'contact': contact,
            'company': company
        }

    def extract_date_from_message(self, message):
        """חילוץ תאריך מההודעה"""
        msg_datetime = message.get('datetime', '')
        
        if msg_datetime and msg_datetime.startswith('2025-'):
            return msg_datetime[:10]
        
        return datetime.now().strftime('%Y-%m-%d')

    def extract_time_from_message(self, message, category):
        """חילוץ שעה מההודעה"""
        content = message.get('content', '')
        
        # חיפוש זמן בהודעה
        import re
        time_match = re.search(r'(\d{1,2}):(\d{2})', content)
        if time_match:
            hour, minute = time_match.groups()
            if 0 <= int(hour) <= 23:
                return f"{hour.zfill(2)}:{minute}"
        
        # זמן לפי קטגוריה
        default_times = {
            'meeting': '10:00',
            'deadline': '17:00',
            'reminder': '09:00',
            'task': '14:00'
        }
        
        return default_times.get(category, '10:00')

    def create_calendar_event_correctly(self, event_data, service, calendar_id, color):
        """יצירת אירוע נכון ביומן timebro"""
        try:
            start_datetime = f"{event_data['date']}T{event_data['time']}:00"
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = start_dt + timedelta(minutes=event_data['duration_minutes'])
            
            calendar_event = {
                'summary': event_data['title'],
                'description': event_data['description'],
                'start': {
                    'dateTime': start_dt.replace(tzinfo=None).isoformat() + '+02:00',
                    'timeZone': 'Asia/Jerusalem'
                },
                'end': {
                    'dateTime': end_dt.replace(tzinfo=None).isoformat() + '+02:00',
                    'timeZone': 'Asia/Jerusalem'
                },
                'colorId': color,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15}
                    ]
                }
            }
            
            # יצירה ביומן timebro הנכון
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=calendar_event
            ).execute()
            
            # שמירה במסד המקומי
            self.save_to_local_db(event_data, created_event.get('id'))
            
            return True
            
        except Exception as e:
            self.log(f"שגיאה ביצירת אירוע: {e}", "ERROR")
            return False

    def save_to_local_db(self, event_data, google_event_id):
        """שמירה נכונה במסד המקומי"""
        try:
            conn = sqlite3.connect('timebro_calendar.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO calendar_events 
                (title, description, start_datetime, end_datetime, 
                 source_contact, category, google_event_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data['title'],
                event_data['description'],
                f"{event_data['date']}T{event_data['time']}:00",
                f"{event_data['date']}T{event_data['time']}:00",
                event_data['contact'],
                event_data['category'],
                google_event_id,
                'active'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log(f"שגיאה בשמירה למסד: {e}", "ERROR")

    def run_complete_fix(self):
        """הרצת תיקון מלא"""
        print('\n' + '='*80)
        print('🔧 תיקון מערכת TimeBro Calendar - ניקוי ויצירה נכונה')
        print('='*80)
        
        try:
            # 1. חיבור לGoogle Calendar
            service = self.get_calendar_service()
            if not service:
                self.log("לא ניתן להתחבר לGoogle Calendar", "ERROR")
                return
            
            # 2. מציאת/יצירת יומן timebro
            timebro_id = self.find_timebro_calendar_id(service)
            if not timebro_id:
                self.log("לא ניתן ליצור יומן timebro", "ERROR")
                return
            
            # 3. מחיקת אירועים שגויים
            deleted_count = self.delete_wrong_events_from_google(service)
            
            # 4. ניקוי מסד נתונים מקומי
            self.clean_local_database()
            
            # 5. יצירת אירועים נכונים
            created_count = self.create_correct_events(service, timebro_id)
            
            # 6. סיכום
            print(f'\n📊 סיכום תיקון:')
            print(f'   🗑️ אירועים שגויים נמחקו: {deleted_count}')
            print(f'   ✅ אירועים נכונים נוצרו: {created_count}')
            print(f'   📅 יומן יעד: timebro')
            print(f'   👥 רק מרשימת אנשי הקשר: {len(self.valid_contact_names)} אנשים')
            
            print(f'\n🎉 תיקון הושלם! יומן timebro נקי ונכון')
            
        except Exception as e:
            self.log(f"שגיאה בתיקון: {e}", "ERROR")

def main():
    fixer = CalendarFixer()
    fixer.run_complete_fix()

if __name__ == "__main__":
    main()













