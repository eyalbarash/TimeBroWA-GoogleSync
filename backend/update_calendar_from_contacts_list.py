#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
עדכון יומן TimeBro על בסיס רשימת אנשי הקשר המאורגנת מcontacts_list.py
מ-25 באוגוסט עד היום - אוטומטי מלא עם Google Calendar API
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from contacts_list import CONTACTS_CONFIG, list_all_contacts, get_contact_company
from fully_automated_timebro import FullyAutomatedTimeBro

class ContactsListCalendarUpdater:
    def __init__(self):
        self.automation = FullyAutomatedTimeBro()
        
        # קבלת כל אנשי הקשר מהרשימה המאורגנת
        self.all_contacts = list_all_contacts()
        self.contact_names = [contact['name'] for contact in self.all_contacts]
        
        # תקופת החיפוש - מ-25 באוגוסט עד היום
        self.start_date = datetime(2025, 8, 25)
        self.end_date = datetime.now()
        
        self.stats = {
            'total_contacts_in_list': len(self.contact_names),
            'contacts_found_with_messages': 0,
            'messages_processed': 0,
            'events_created': 0,
            'companies_processed': len(CONTACTS_CONFIG)
        }

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        else:
            emoji = "📋"
        print(f"[{timestamp}] {emoji} {message}")

    def find_contacts_in_databases(self):
        """חיפוש אנשי הקשר מהרשימה בכל מסדי הנתונים"""
        self.log(f"מחפש {len(self.contact_names)} אנשי קשר מהרשימה המאורגנת...")
        
        databases = [
            ('whatsapp_messages.db', 'august_messages'),
            ('whatsapp_messages_webjs.db', 'messages'),
            ('whatsapp_chats.db', 'messages')
        ]
        
        found_contacts = {}
        
        for db_path, table_name in databases:
            if not os.path.exists(db_path):
                continue
                
            self.log(f"בודק במסד: {db_path}")
            contacts_in_db = self.search_contacts_in_database(db_path, table_name)
            
            # מיזוג התוצאות
            for contact, messages in contacts_in_db.items():
                if contact not in found_contacts:
                    found_contacts[contact] = []
                found_contacts[contact].extend(messages)
        
        self.stats['contacts_found_with_messages'] = len(found_contacts)
        
        # הצגת סיכום
        self.log(f"נמצאו {len(found_contacts)} אנשי קשר עם הודעות:")
        for contact, messages in found_contacts.items():
            company, color = get_contact_company(contact)
            self.log(f"   👤 {contact} ({company}): {len(messages)} הודעות")
        
        return found_contacts

    def search_contacts_in_database(self, db_path, table_name):
        """חיפוש אנשי קשר במסד נתונים ספציפי"""
        contacts_found = {}
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if table_name == 'august_messages':
                # חיפוש בטבלת אוגוסט
                for contact_name in self.contact_names:
                    cursor.execute("""
                        SELECT id, timestamp, datetime_str, sender, content, message_type
                        FROM august_messages
                        WHERE (sender LIKE ? OR sender LIKE ?)
                        AND datetime_str >= ?
                        ORDER BY timestamp ASC
                    """, (f'%{contact_name}%', f'%{contact_name.split()[0]}%', 
                          self.start_date.strftime('%Y-%m-%d')))
                    
                    rows = cursor.fetchall()
                    if rows:
                        contacts_found[contact_name] = []
                        for row in rows:
                            contacts_found[contact_name].append({
                                'id': row[0],
                                'datetime': row[2] or '',
                                'sender': row[3] or '',
                                'content': row[4] or '',
                                'source': 'august_data'
                            })
            
            elif 'webjs' in db_path:
                # חיפוש ב-WhatsApp Web.js
                start_timestamp = int(self.start_date.timestamp())
                
                for contact_name in self.contact_names:
                    cursor.execute("""
                        SELECT id, contact_name, message_body, timestamp, is_from_me
                        FROM messages
                        WHERE (contact_name LIKE ? OR contact_name LIKE ?)
                        AND timestamp >= ?
                        ORDER BY timestamp ASC
                    """, (f'%{contact_name}%', f'%{contact_name.split()[0]}%', start_timestamp))
                    
                    rows = cursor.fetchall()
                    if rows:
                        contacts_found[contact_name] = []
                        for row in rows:
                            dt = datetime.fromtimestamp(row[3])
                            contacts_found[contact_name].append({
                                'id': row[0],
                                'datetime': dt.isoformat(),
                                'sender': row[1] or '',
                                'content': row[2] or '',
                                'is_from_me': bool(row[4]),
                                'source': 'webjs_current'
                            })
            
            conn.close()
            
        except Exception as e:
            self.log(f"שגיאה בחיפוש ב-{db_path}: {e}", "ERROR")
        
        return contacts_found

    def process_contacts_for_calendar(self, found_contacts):
        """עיבוד אנשי קשר שנמצאו לאירועי יומן"""
        self.log("מתחיל עיבוד אנשי קשר לאירועי יומן...")
        
        # הגדרת Google Calendar API
        service = self.automation.setup_google_calendar_api()
        if not service:
            self.log("לא ניתן להתחבר ל-Google Calendar", "ERROR")
            return 0
        
        total_events_created = 0
        
        for contact, messages in found_contacts.items():
            try:
                company, color = get_contact_company(contact)
                self.log(f"מעבד {contact} ({company}) - {len(messages)} הודעות")
                
                # סינון הודעות עם פוטנציאל יומן
                calendar_candidates = []
                for msg in messages:
                    content = msg.get('content', '')
                    
                    # בדיקת מילות מפתח ליומן
                    calendar_keywords = [
                        'פגישה', 'מפגש', 'נפגש', 'בואו נקבע',
                        'דדליין', 'עד ה', 'תאריך יעד', 'לסיים עד',
                        'תזכיר', 'תזכורת', 'לזכור', 'להזכיר',
                        'מחר', 'היום', 'בשבוע', 'בשעה', 'ב-',
                        'משימה', 'לעשות', 'לבדוק', 'לעדכן',
                        'כנס', 'סדנה', 'הרצאה', 'אירוע'
                    ]
                    
                    if any(keyword in content for keyword in calendar_keywords) and len(content) > 15:
                        msg['contact_company'] = company
                        msg['company_color'] = color
                        calendar_candidates.append(msg)
                
                # יצירת אירועים
                events_created = 0
                for candidate in calendar_candidates:
                    try:
                        # ניתוח המועמד
                        analyzed = self.automation.analyze_candidate_for_calendar(candidate)
                        
                        if analyzed and analyzed['should_create_event']:
                            event_data = analyzed['event_data']
                            
                            # הוספת מידע על החברה
                            event_data['title'] = f"[{company}] {contact}: {event_data['title']}"
                            event_data['company'] = company
                            event_data['company_color'] = color
                            
                            # בדיקה שהאירוע לא קיים
                            if not self.event_exists(event_data):
                                # יצירת האירוע עם צבע החברה
                                event_id = self.create_calendar_event_with_company_color(
                                    event_data, service, color
                                )
                                
                                if event_id:
                                    # שמירה במסד המקומי
                                    self.automation.save_event_to_local_db(event_data, event_id)
                                    events_created += 1
                                    total_events_created += 1
                                    
                                    self.log(f"   ✅ אירוע נוצר: {event_data['title'][:50]}...")
                    
                    except Exception as e:
                        self.log(f"   ❌ שגיאה באירוע: {e}", "ERROR")
                
                if events_created > 0:
                    self.log(f"✅ {contact}: {events_created} אירועים נוצרו", "SUCCESS")
                
            except Exception as e:
                self.log(f"שגיאה בעיבוד {contact}: {e}", "ERROR")
        
        self.stats['events_created'] = total_events_created
        return total_events_created

    def create_calendar_event_with_company_color(self, event_data, service, color_id):
        """יצירת אירוע עם צבע החברה"""
        try:
            # הכנת זמני האירוע
            start_datetime = f"{event_data['date']}T{event_data['time']}:00"
            start_dt = datetime.fromisoformat(start_datetime)
            end_dt = start_dt + timedelta(minutes=event_data.get('duration_minutes', 60))
            
            # בניית אירוע Google Calendar
            calendar_event = {
                'summary': event_data['title'],
                'description': event_data.get('description', ''),
                'start': {
                    'dateTime': start_dt.replace(tzinfo=None).isoformat() + '+02:00',
                    'timeZone': 'Asia/Jerusalem'
                },
                'end': {
                    'dateTime': end_dt.replace(tzinfo=None).isoformat() + '+02:00',
                    'timeZone': 'Asia/Jerusalem'
                },
                'colorId': color_id,  # צבע החברה
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 15}
                    ]
                }
            }
            
            # יצירת האירוע ביומן timebro
            created_event = service.events().insert(
                calendarId='primary',  # יומן ראשי
                body=calendar_event
            ).execute()
            
            return created_event.get('id')
            
        except Exception as e:
            self.log(f"שגיאה ביצירת אירוע: {e}", "ERROR")
            return None

    def event_exists(self, event_data):
        """בדיקה אם האירוע כבר קיים"""
        try:
            conn = sqlite3.connect('timebro_calendar.db')
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM calendar_events 
                WHERE title = ? AND start_datetime = ?
            """, (
                event_data['title'],
                f"{event_data['date']}T{event_data['time']}:00"
            ))
            
            exists = cursor.fetchone()[0] > 0
            conn.close()
            return exists
            
        except Exception as e:
            return False

    def run_contacts_list_update(self):
        """הפעלת עדכון מלא על בסיס רשימת אנשי הקשר"""
        print('\n' + '='*80)
        print('📋 TimeBro Calendar - עדכון על בסיס רשימת אנשי הקשר')
        print(f'📅 תקופה: {self.start_date.strftime("%d/%m/%Y")} - {self.end_date.strftime("%d/%m/%Y")}')
        print(f'👥 בודק {len(self.contact_names)} אנשי קשר מ-{len(CONTACTS_CONFIG)} חברות')
        print('='*80)
        
        try:
            # 1. חיפוש אנשי קשר בכל המסדים
            found_contacts = self.find_contacts_in_databases()
            
            if not found_contacts:
                self.log("לא נמצאו הודעות מאנשי הקשר ברשימה בתקופה זו")
                return
            
            # 2. עיבוד לאירועי יומן
            events_created = self.process_contacts_for_calendar(found_contacts)
            
            # 3. סיכום
            self.print_final_summary()
            
        except Exception as e:
            self.log(f"שגיאה בעדכון: {e}", "ERROR")

    def print_final_summary(self):
        """הדפסת סיכום סופי"""
        print('\n' + '='*80)
        print('📊 סיכום עדכון יומן מרשימת אנשי הקשר')
        print('='*80)
        
        print(f'👥 סה\"כ אנשי קשר ברשימה: {self.stats["total_contacts_in_list"]}')
        print(f'🔍 נמצאו עם הודעות: {self.stats["contacts_found_with_messages"]}')
        print(f'💬 הודעות עובדו: {self.stats["messages_processed"]}')
        print(f'✅ אירועים נוצרו: {self.stats["events_created"]}')
        print(f'🏢 חברות עובדו: {self.stats["companies_processed"]}')
        
        # הצגת פילוג לפי חברות
        print(f'\n🏢 פילוג לפי חברות:')
        for company, config in CONTACTS_CONFIG.items():
            company_contacts = config['contacts']
            print(f'   📂 {company}: {len(company_contacts)} אנשי קשר')
        
        print('='*80)
        print(f'✅ עדכון הושלם! בדוק את יומן timebro ב-Google Calendar')
        print(f'🎨 אירועים מצובעים לפי חברות')
        print('='*80)

def main():
    updater = ContactsListCalendarUpdater()
    updater.run_contacts_list_update()

if __name__ == "__main__":
    main()













