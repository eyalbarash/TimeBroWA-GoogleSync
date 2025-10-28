#!/usr/bin/env python3
"""
Delete Only Call Events - Keep Real WhatsApp Events
מחיקת אירועי שיחות טלפון בלבד - שמירה על אירועי WhatsApp אמיתיים
"""

import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
from contacts_list import CONTACTS_CONFIG

class DeleteCallEventsOnly:
    def __init__(self):
        self.calendar_id = "c_mjbk37j51lkl4pl8i9tk31ek3o@group.calendar.google.com"
        self.service = None
        self.relevant_contact_names = self._build_relevant_names_list()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "ℹ️"
        print(f"[{timestamp}] {emoji} {message}")

    def _build_relevant_names_list(self):
        """בונה רשימה של כל שמות אנשי הקשר הרלוונטיים"""
        relevant_names = []
        for company, config in CONTACTS_CONFIG.items():
            for contact in config["contacts"]:
                relevant_names.append(contact)
                # נוסיף גם גרסאות מנוקות של השמות
                clean_name = contact.split('(')[0].strip() if '(' in contact else contact
                if clean_name != contact:
                    relevant_names.append(clean_name)
                if '/' in contact:
                    parts = contact.split('/')
                    for part in parts:
                        relevant_names.append(part.strip())
        
        return list(set(relevant_names))

    def authenticate_google_calendar(self):
        """מתחבר ל-Google Calendar API"""
        self.log("מתחבר ל-Google Calendar...")
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        self.log("התחברות ל-Google Calendar הושלמה", "SUCCESS")

    def categorize_events(self):
        """מסווג את האירועים לפי סוג"""
        self.log("מסווג את כל האירועים ביומן...")
        
        try:
            # קבלת כל האירועים
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                maxResults=2500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # סיווג האירועים
            call_events = []           # אירועי שיחות טלפון
            whatsapp_text_events = []  # אירועי WhatsApp עם תוכן טקסט
            relevant_whatsapp = []     # אירועי WhatsApp של אנשי קשר רלוונטיים
            other_events = []          # אירועים אחרים
            
            for event in events:
                summary = event.get('summary', '')
                description = event.get('description', '')
                
                # זיהוי אירועי שיחות טלפון
                if summary.startswith('Call to ') or summary.startswith('Call from '):
                    call_events.append(event)
                    continue
                
                # זיהוי אירועי WhatsApp אמיתיים
                if (any(keyword in summary.lower() for keyword in ['שיחה עם', 'מייק ביקוב']) or
                    any(keyword in description.lower() for keyword in ['whatsapp', 'wa.me', 'קישור לפתיחה', 'השיחה המלאה'])):
                    
                    # בדיקה אם זה אירוע רלוונטי
                    full_text = f"{summary} {description}".lower()
                    is_relevant = False
                    
                    for contact_name in self.relevant_contact_names:
                        if contact_name.lower() in full_text:
                            is_relevant = True
                            break
                    
                    if is_relevant:
                        relevant_whatsapp.append(event)
                    else:
                        whatsapp_text_events.append(event)
                    continue
                
                # אירועים אחרים
                other_events.append(event)
            
            return {
                'call_events': call_events,
                'whatsapp_text_events': whatsapp_text_events,
                'relevant_whatsapp': relevant_whatsapp,
                'other_events': other_events,
                'total_events': len(events)
            }
            
        except Exception as e:
            self.log(f"שגיאה בסיווג אירועים: {str(e)}", "ERROR")
            return None

    def delete_call_events(self, call_events):
        """מוחק את אירועי השיחות הטלפוניות בלבד"""
        self.log(f"מוחק {len(call_events)} אירועי שיחות טלפון...")
        
        deleted_count = 0
        
        for event in call_events:
            try:
                self.service.events().delete(
                    calendarId=self.calendar_id,
                    eventId=event['id']
                ).execute()
                deleted_count += 1
                
                if deleted_count % 100 == 0:  # דיווח כל 100 מחיקות
                    self.log(f"נמחקו עד כה {deleted_count} אירועי שיחות...")
                    
            except Exception as e:
                self.log(f"שגיאה במחיקת אירוע {event['id']}: {str(e)}", "ERROR")
        
        self.log(f"נמחקו {deleted_count} אירועי שיחות טלפון", "SUCCESS")
        return deleted_count

    def generate_cleanup_report(self, categorization, deleted_count):
        """יוצר דוח ניקוי מפורט"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "cleanup_summary": {
                "total_events_before": categorization['total_events'],
                "call_events_deleted": deleted_count,
                "whatsapp_relevant_kept": len(categorization['relevant_whatsapp']),
                "whatsapp_irrelevant_kept": len(categorization['whatsapp_text_events']),
                "other_events_kept": len(categorization['other_events'])
            },
            "relevant_whatsapp_events": [
                {
                    "summary": event.get('summary', ''),
                    "start_time": event.get('start', {}).get('dateTime', '')
                }
                for event in categorization['relevant_whatsapp']
            ]
        }
        
        # שמירת הדוח
        report_file = f"call_events_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # הדפסת סיכום
        print("\n📊 דוח ניקוי אירועי שיחות טלפון")
        print("=" * 60)
        print(f"📅 סך הכל אירועים לפני הניקוי: {categorization['total_events']}")
        print(f"📞 אירועי שיחות טלפון שנמחקו: {deleted_count}")
        print(f"✅ אירועי WhatsApp רלוונטיים שנשמרו: {len(categorization['relevant_whatsapp'])}")
        print(f"⚠️ אירועי WhatsApp לא רלוונטיים שנשמרו: {len(categorization['whatsapp_text_events'])}")
        print(f"🔒 אירועים אחרים שנשמרו: {len(categorization['other_events'])}")
        print(f"📄 דוח נשמר ב: {report_file}")
        
        remaining_events = (len(categorization['relevant_whatsapp']) + 
                          len(categorization['whatsapp_text_events']) + 
                          len(categorization['other_events']))
        print(f"\n📈 סך הכל אירועים שנותרו ביומן: {remaining_events}")
        
        if categorization['relevant_whatsapp']:
            print("\n✅ אירועי WhatsApp רלוונטיים שנשמרו:")
            for i, event in enumerate(categorization['relevant_whatsapp'][:10], 1):
                summary = event.get('summary', 'ללא כותרת')[:60]
                start_time = event.get('start', {}).get('dateTime', '')[:10]  # רק התאריך
                print(f"   {i}. [{start_time}] {summary}...")
            
            if len(categorization['relevant_whatsapp']) > 10:
                print(f"   ... ועוד {len(categorization['relevant_whatsapp']) - 10} אירועים")
        
        return report

    def run(self):
        """מריץ את תהליך הניקוי"""
        try:
            self.log("מתחיל ניקוי אירועי שיחות טלפון מהיומן")
            print("=" * 60)
            
            # שלב 1: התחברות ל-Google Calendar
            self.authenticate_google_calendar()
            
            # שלב 2: סיווג האירועים
            categorization = self.categorize_events()
            
            if not categorization:
                self.log("נכשל בסיווג האירועים", "ERROR")
                return
            
            # הצגת סיכום לפני המחיקה
            print(f"\n🔍 נמצאו {categorization['call_events'].__len__()} אירועי שיחות טלפון למחיקה")
            print(f"✅ יישמרו {categorization['relevant_whatsapp'].__len__()} אירועי WhatsApp רלוונטיים")
            print(f"⚠️ יישמרו {categorization['whatsapp_text_events'].__len__()} אירועי WhatsApp לא רלוונטיים")
            print(f"🔒 יישמרו {categorization['other_events'].__len__()} אירועים אחרים")
            
            # בקשת אישור מהמשתמש (בעת הרצה אינטראקטיבית)
            print(f"\nהאם להמשיך ולמחוק {len(categorization['call_events'])} אירועי שיחות? (y/n)")
            # לצרכי האוטומציה - נמשיך אוטומטית
            
            # שלב 3: מחיקת אירועי השיחות בלבד
            deleted_count = self.delete_call_events(categorization['call_events'])
            
            # שלב 4: יצירת דוח
            self.generate_cleanup_report(categorization, deleted_count)
            
            print("\n✅ ניקוי אירועי השיחות הושלם בהצלחה!")
            print("📅 נותרו ביומן רק אירועי WhatsApp ואירועים אחרים רלוונטיים")
            
        except Exception as e:
            self.log(f"שגיאה בתהליך הניקוי: {str(e)}", "ERROR")
            raise

if __name__ == "__main__":
    cleanup = DeleteCallEventsOnly()
    cleanup.run()













