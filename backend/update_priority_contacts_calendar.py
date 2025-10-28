#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
עדכון יומן timebro עבור אנשי הקשר ברשימת הפריוריטי
מ-25 באוגוסט 2025 עד היום
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
import re
from fully_automated_timebro import FullyAutomatedTimeBro

class PriorityContactsCalendarUpdater:
    def __init__(self):
        self.automation = FullyAutomatedTimeBro()
        
        # רשימת אנשי הקשר העדיפות שלך (מהזיכרון)
        self.priority_contacts = [
            'מייק ביקוב', 'מייק', 'Mike',
            'צחי כפרי', 'צחי', 'כפרי דרייב',
            'לי עמר', 'עילי ברש', 'משה עמר',
            'סשה דיבקה', 'סשה',
            'שתלתם', 'נטה שלי', 'נטע שלי',
            'fital', 'טל מועלם'
        ]
        
        # תאריכי החיפוש
        self.start_date = datetime(2025, 8, 25)  # 25 באוגוסט
        self.end_date = datetime.now()  # עד היום
        
        self.stats = {
            'contacts_found': 0,
            'messages_processed': 0,
            'events_created': 0,
            'period_days': (self.end_date - self.start_date).days
        }

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        else:
            emoji = "🎯"
        print(f"[{timestamp}] {emoji} {message}")

    def extract_priority_contacts_messages(self):
        """חילוץ הודעות של אנשי הקשר העדיפות מ-25/8 עד היום"""
        self.log(f"מחלץ הודעות אנשי קשר עדיפות מ-{self.start_date.strftime('%d/%m')} עד היום...")
        
        databases = [
            ('whatsapp_messages.db', 'august_messages'),
            ('whatsapp_messages_webjs.db', 'messages'),
            ('whatsapp_chats.db', 'messages')
        ]
        
        all_messages = []
        
        for db_path, table_name in databases:
            if not os.path.exists(db_path):
                continue
                
            try:
                self.log(f"בודק במסד: {db_path} -> {table_name}")
                messages = self.extract_from_database(db_path, table_name)
                all_messages.extend(messages)
                
            except Exception as e:
                self.log(f"שגיאה ב-{db_path}: {e}", "ERROR")
        
        self.log(f"נמצאו {len(all_messages)} הודעות מאנשי הקשר העדיפות")
        return all_messages

    def extract_from_database(self, db_path, table_name):
        """חילוץ מהמסד הספציפי"""
        messages = []
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # חילוץ לפי סוג המסד
            if table_name == 'august_messages':
                # טבלת אוגוסט - נתונים אמיתיים
                cursor.execute("""
                    SELECT id, timestamp, datetime_str, sender, content, message_type
                    FROM august_messages
                    WHERE datetime_str >= ? 
                    ORDER BY timestamp ASC
                """, (self.start_date.strftime('%Y-%m-%d'),))
                
                for row in cursor.fetchall():
                    sender = row[3] or ''
                    if self.is_priority_contact(sender):
                        messages.append({
                            'id': row[0],
                            'datetime': row[2] or '',
                            'sender': sender,
                            'content': row[4] or '',
                            'source': 'august_real_data'
                        })
            
            elif 'webjs' in db_path:
                # WhatsApp Web.js - נתונים חדשים
                start_timestamp = int(self.start_date.timestamp())
                
                cursor.execute("""
                    SELECT id, contact_name, message_body, timestamp, is_from_me
                    FROM messages
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                """, (start_timestamp,))
                
                for row in cursor.fetchall():
                    sender = row[1] or ''
                    if self.is_priority_contact(sender):
                        dt = datetime.fromtimestamp(row[3])
                        messages.append({
                            'id': row[0],
                            'datetime': dt.isoformat(),
                            'sender': sender,
                            'content': row[2] or '',
                            'is_from_me': bool(row[4]),
                            'source': 'webjs_current'
                        })
            
            conn.close()
            
        except Exception as e:
            self.log(f"שגיאה בחילוץ מ-{db_path}: {e}", "ERROR")
        
        return messages

    def is_priority_contact(self, sender):
        """בדיקה אם זה איש קשר עדיפות"""
        if not sender:
            return False
            
        sender_lower = sender.lower()
        
        return any(contact.lower() in sender_lower for contact in self.priority_contacts)

    def group_messages_by_contact(self, messages):
        """קיבוץ הודעות לפי איש קשר"""
        by_contact = {}
        
        for msg in messages:
            sender = msg['sender']
            if sender not in by_contact:
                by_contact[sender] = []
            by_contact[sender].append(msg)
        
        self.log(f"נמצאו הודעות מ-{len(by_contact)} אנשי קשר עדיפות")
        
        # הצגת סיכום
        for contact, contact_messages in by_contact.items():
            self.log(f"   👤 {contact}: {len(contact_messages)} הודעות")
        
        return by_contact

    def process_contact_messages_for_calendar(self, contact, messages):
        """עיבוד הודעות של איש קשר ספציפי לאירועי יומן"""
        self.log(f"מעבד הודעות של {contact} לאירועי יומן...")
        
        calendar_candidates = []
        
        # סינון הודעות עם פוטנציאל יומן
        for msg in messages:
            content = msg.get('content', '')
            
            # בדיקה אם יש מילות מפתח ליומן
            calendar_keywords = [
                'פגישה', 'מפגש', 'נפגש', 'בואו נקבע',
                'דדליין', 'עד ה', 'תאריך יעד', 'לסיים עד',
                'תזכיר', 'תזכורת', 'לזכור',
                'מחר', 'היום', 'בשבוע', 'בשעה', 'ב-',
                'משימה', 'לעשות', 'לבדוק', 'לעדכן'
            ]
            
            if any(keyword in content for keyword in calendar_keywords) and len(content) > 20:
                calendar_candidates.append(msg)
        
        self.log(f"   📅 {len(calendar_candidates)} מועמדי יומן עבור {contact}")
        
        # יצירת אירועים
        events_created = 0
        for candidate in calendar_candidates:
            try:
                # ניתוח המועמד
                analyzed = self.automation.analyze_candidate_for_calendar(candidate)
                
                if analyzed and analyzed['should_create_event']:
                    # יצירת האירוע
                    event_data = analyzed['event_data']
                    event_data['title'] = f"{contact}: {event_data['title']}"  # הוספת שם איש הקשר
                    
                    # יצירה דרך Google Calendar API
                    service = self.automation.setup_google_calendar_api()
                    if service:
                        event_id = self.automation.create_calendar_event_api(event_data, service)
                        if event_id:
                            # שמירה במסד המקומי
                            self.automation.save_event_to_local_db(event_data, event_id)
                            events_created += 1
                            
                            self.log(f"   ✅ אירוע נוצר: {event_data['title'][:50]}...")
            
            except Exception as e:
                self.log(f"   ❌ שגיאה באירוע: {e}", "ERROR")
        
        return events_created

    def run_priority_update(self):
        """הפעלת עדכון מלא לאנשי הקשר העדיפות"""
        print('\n' + '='*80)
        print('🎯 עדכון יומן TimeBro - אנשי קשר עדיפות')
        print(f'📅 תקופה: {self.start_date.strftime("%d/%m/%Y")} - {self.end_date.strftime("%d/%m/%Y")}')
        print('='*80)
        
        try:
            # 1. חילוץ הודעות
            all_messages = self.extract_priority_contacts_messages()
            self.stats['messages_processed'] = len(all_messages)
            
            if not all_messages:
                self.log("לא נמצאו הודעות מאנשי הקשר העדיפות בתקופה זו")
                return
            
            # 2. קיבוץ לפי איש קשר
            by_contact = self.group_messages_by_contact(all_messages)
            self.stats['contacts_found'] = len(by_contact)
            
            # 3. עיבוד כל איש קשר
            total_events = 0
            for contact, contact_messages in by_contact.items():
                events_count = self.process_contact_messages_for_calendar(contact, contact_messages)
                total_events += events_count
            
            self.stats['events_created'] = total_events
            
            # 4. סיכום
            self.print_update_summary()
            
        except Exception as e:
            self.log(f"שגיאה בעדכון: {e}", "ERROR")

    def print_update_summary(self):
        """הדפסת סיכום העדכון"""
        print('\n' + '='*80)
        print('📊 סיכום עדכון יומן אנשי קשר עדיפות')
        print('='*80)
        
        print(f'📅 תקופה: {self.stats["period_days"]} ימים')
        print(f'👥 אנשי קשר נמצאו: {self.stats["contacts_found"]}')
        print(f'💬 הודעות עובדו: {self.stats["messages_processed"]}')
        print(f'✅ אירועים נוצרו: {self.stats["events_created"]}')
        
        # בדיקת מסד הנתונים
        try:
            conn = sqlite3.connect('timebro_calendar.db')
            cursor = conn.cursor()
            
            # אירועים מהתקופה
            cursor.execute("""
                SELECT COUNT(*) FROM calendar_events 
                WHERE start_datetime >= ? AND start_datetime <= ?
            """, (
                self.start_date.strftime('%Y-%m-%d'),
                self.end_date.strftime('%Y-%m-%d')
            ))
            
            period_events = cursor.fetchone()[0]
            
            # אירועים מהיום
            cursor.execute("""
                SELECT COUNT(*) FROM calendar_events 
                WHERE DATE(start_datetime) = DATE('now')
            """)
            
            today_events = cursor.fetchone()[0]
            
            conn.close()
            
            print(f'📅 אירועים בתקופה: {period_events}')
            print(f'📅 אירועים שנוצרו היום: {today_events}')
            
        except Exception as e:
            self.log(f"שגיאה בבדיקת מסד: {e}", "ERROR")
        
        print('='*80)
        print(f'✅ עדכון הושלם! בדוק את יומן timebro ב-Google Calendar')
        print('='*80)

def main():
    updater = PriorityContactsCalendarUpdater()
    updater.run_priority_update()

if __name__ == "__main__":
    main()
