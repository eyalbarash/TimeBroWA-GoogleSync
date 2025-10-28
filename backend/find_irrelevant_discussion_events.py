#!/usr/bin/env python3
"""
Find Irrelevant Discussion Events
מציאת אירועי דיון לא רלוונטיים שאינם קשורים לרשימת אנשי הקשר
"""

import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
from contacts_list import CONTACTS_CONFIG

class FindIrrelevantEvents:
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

    def find_discussion_events(self):
        """מוצא אירועי דיון שאינם קשורים לרשימת אנשי הקשר"""
        self.log("מחפש אירועי דיון לא רלוונטיים...")
        
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
            call_events = []           # אירועי שיחות טלפון - לא נוגעים!
            whatsapp_relevant = []     # אירועי WhatsApp רלוונטיים
            whatsapp_irrelevant = []   # אירועי WhatsApp/דיון לא רלוונטיים
            other_events = []          # אירועים אחרים
            
            for event in events:
                summary = event.get('summary', '')
                description = event.get('description', '')
                
                # אירועי שיחות טלפון - לא נוגעים!
                if summary.startswith('Call to ') or summary.startswith('Call from '):
                    call_events.append(event)
                    continue
                
                # בדיקה אם זה אירוע WhatsApp או דיון
                is_whatsapp_or_discussion = (
                    any(keyword in summary.lower() for keyword in ['שיחה עם', 'דיון', 'מפגש', 'aiש קשר', 'whatsapp']) or
                    any(keyword in description.lower() for keyword in ['whatsapp', 'wa.me', 'קישור לפתיחה', 'השיחה המלאה', 'דיון'])
                )
                
                if is_whatsapp_or_discussion:
                    # בדיקה אם זה רלוונטי לרשימת אנשי הקשר
                    full_text = f"{summary} {description}".lower()
                    is_relevant = False
                    matched_contact = None
                    
                    for contact_name in self.relevant_contact_names:
                        if contact_name.lower() in full_text:
                            is_relevant = True
                            matched_contact = contact_name
                            break
                    
                    if is_relevant:
                        whatsapp_relevant.append({
                            'event': event,
                            'matched_contact': matched_contact
                        })
                    else:
                        whatsapp_irrelevant.append(event)
                else:
                    other_events.append(event)
            
            return {
                'call_events': call_events,
                'whatsapp_relevant': whatsapp_relevant,
                'whatsapp_irrelevant': whatsapp_irrelevant,
                'other_events': other_events,
                'total_events': len(events)
            }
            
        except Exception as e:
            self.log(f"שגיאה בחיפוש אירועים: {str(e)}", "ERROR")
            return None

    def display_findings(self, categorization):
        """מציג את הממצאים בצורה ברורה"""
        
        print("\n📊 סיכום אירועים ביומן TimeBro:")
        print("=" * 70)
        print(f"📅 סך הכל אירועים: {categorization['total_events']}")
        print(f"📞 אירועי שיחות טלפון (לא נוגעים): {len(categorization['call_events'])}")
        print(f"✅ אירועי WhatsApp רלוונטיים (נשמרים): {len(categorization['whatsapp_relevant'])}")
        print(f"❌ אירועי WhatsApp/דיון לא רלוונטיים (למחיקה): {len(categorization['whatsapp_irrelevant'])}")
        print(f"🔒 אירועים אחרים (לא נוגעים): {len(categorization['other_events'])}")
        
        # הצגת אירועים רלוונטיים שיישמרו
        if categorization['whatsapp_relevant']:
            print("\n✅ אירועי WhatsApp רלוונטיים שיישמרו:")
            for i, item in enumerate(categorization['whatsapp_relevant'][:10], 1):
                event = item['event']
                contact = item['matched_contact']
                summary = event.get('summary', 'ללא כותרת')[:60]
                start_time = event.get('start', {}).get('dateTime', '')[:10]
                print(f"   {i}. [{start_time}] {summary}... (התאמה: {contact})")
            
            if len(categorization['whatsapp_relevant']) > 10:
                print(f"   ... ועוד {len(categorization['whatsapp_relevant']) - 10} אירועים")
        
        # הצגת אירועים לא רלוונטיים למחיקה
        if categorization['whatsapp_irrelevant']:
            print("\n❌ אירועי WhatsApp/דיון לא רלוונטיים שיימחקו:")
            for i, event in enumerate(categorization['whatsapp_irrelevant'][:15], 1):
                summary = event.get('summary', 'ללא כותרת')[:60]
                start_time = event.get('start', {}).get('dateTime', '')[:10]
                description = event.get('description', '')[:50]
                print(f"   {i}. [{start_time}] {summary}...")
                if description:
                    print(f"      תיאור: {description}...")
            
            if len(categorization['whatsapp_irrelevant']) > 15:
                print(f"   ... ועוד {len(categorization['whatsapp_irrelevant']) - 15} אירועים")
        
        return categorization

    def save_report(self, categorization):
        """שומר דוח מפורט"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_events": categorization['total_events'],
                "call_events_count": len(categorization['call_events']),
                "whatsapp_relevant_count": len(categorization['whatsapp_relevant']),
                "whatsapp_irrelevant_count": len(categorization['whatsapp_irrelevant']),
                "other_events_count": len(categorization['other_events'])
            },
            "relevant_contact_names": self.relevant_contact_names,
            "whatsapp_irrelevant_events": [
                {
                    "id": event['id'],
                    "summary": event.get('summary', ''),
                    "start_time": event.get('start', {}).get('dateTime', ''),
                    "description": event.get('description', '')[:200]
                }
                for event in categorization['whatsapp_irrelevant']
            ]
        }
        
        report_file = f"irrelevant_events_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 דוח מפורט נשמר ב: {report_file}")
        return report_file

    def run(self):
        """מריץ את הבדיקה"""
        try:
            self.log("מתחיל חיפוש אירועי דיון לא רלוונטיים")
            print("=" * 70)
            
            # התחברות ל-Google Calendar
            self.authenticate_google_calendar()
            
            # חיפוש וסיווג האירועים
            categorization = self.find_discussion_events()
            
            if not categorization:
                self.log("נכשל בחיפוש האירועים", "ERROR")
                return
            
            # הצגת הממצאים
            self.display_findings(categorization)
            
            # שמירת דוח
            self.save_report(categorization)
            
            print("\n🔍 הבדיקה הושלמה!")
            print("📞 אירועי שיחות הטלפון שלך בטוחים ולא יימחקו")
            if categorization['whatsapp_irrelevant']:
                print(f"❌ נמצאו {len(categorization['whatsapp_irrelevant'])} אירועי דיון לא רלוונטיים למחיקה")
            else:
                print("✅ לא נמצאו אירועי דיון לא רלוונטיים למחיקה")
            
        except Exception as e:
            self.log(f"שגיאה: {str(e)}", "ERROR")
            raise

if __name__ == "__main__":
    finder = FindIrrelevantEvents()
    finder.run()













