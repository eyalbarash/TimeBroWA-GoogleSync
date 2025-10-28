#!/usr/bin/env python3
"""
Check Current WhatsApp Events in Calendar
בדיקת אירועי WhatsApp נוכחיים ביומן
"""

import json
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path

class CheckWhatsAppEvents:
    def __init__(self):
        self.calendar_id = "c_mjbk37j51lkl4pl8i9tk31ek3o@group.calendar.google.com"
        self.service = None
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "ℹ️"
        print(f"[{timestamp}] {emoji} {message}")

    def authenticate_google_calendar(self):
        """מתחבר ל-Google Calendar API"""
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

    def check_whatsapp_events(self):
        """בודק את כל אירועי WhatsApp ביומן"""
        self.log("בודק אירועי WhatsApp ביומן...")
        
        try:
            # קבלת כל האירועים
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                maxResults=2500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            whatsapp_events = []
            
            for event in events:
                summary = event.get('summary', '')
                description = event.get('description', '')
                
                # זיהוי אירועי WhatsApp
                is_whatsapp = False
                whatsapp_type = ""
                
                if any(keyword in summary.lower() for keyword in ['שיחה עם', 'whatsapp', 'מייק ביקוב']):
                    is_whatsapp = True
                    whatsapp_type = "summary_match"
                elif any(keyword in description.lower() for keyword in ['whatsapp', 'wa.me', 'קישור לפתיחה']):
                    is_whatsapp = True
                    whatsapp_type = "description_match"
                elif any(keyword in summary.lower() for keyword in ['call to', 'call from']):
                    is_whatsapp = True
                    whatsapp_type = "call_event"
                elif any(keyword in summary.lower() for keyword in ['דיון עבודה', 'איש קשר', 'מפגש']):
                    is_whatsapp = True
                    whatsapp_type = "generic_work"
                
                if is_whatsapp:
                    start_time = event.get('start', {}).get('dateTime', event.get('start', {}).get('date', ''))
                    
                    whatsapp_events.append({
                        'id': event['id'],
                        'summary': summary,
                        'description': description[:100] + "..." if len(description) > 100 else description,
                        'start_time': start_time,
                        'type': whatsapp_type
                    })
            
            self.log(f"נמצאו {len(whatsapp_events)} אירועי WhatsApp", "SUCCESS")
            
            # הצגת האירועים
            if whatsapp_events:
                print("\n📱 אירועי WhatsApp ביומן:")
                print("=" * 80)
                
                for i, event in enumerate(whatsapp_events, 1):
                    print(f"\n{i}. 📅 {event['start_time']}")
                    print(f"   📝 כותרת: {event['summary']}")
                    print(f"   📄 תיאור: {event['description']}")
                    print(f"   🏷️ סוג: {event['type']}")
            else:
                print("\n✅ לא נמצאו אירועי WhatsApp ביומן")
            
            return whatsapp_events
            
        except Exception as e:
            self.log(f"שגיאה בבדיקת אירועים: {str(e)}", "ERROR")
            return []

    def run(self):
        """מריץ את הבדיקה"""
        try:
            self.log("מתחיל בדיקת אירועי WhatsApp ביומן")
            print("=" * 60)
            
            self.authenticate_google_calendar()
            whatsapp_events = self.check_whatsapp_events()
            
            # שמירת דוח
            report = {
                "timestamp": datetime.now().isoformat(),
                "total_whatsapp_events": len(whatsapp_events),
                "events": whatsapp_events
            }
            
            report_file = f"whatsapp_events_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            print(f"\n📄 דוח נשמר ב: {report_file}")
            print(f"📊 סיכום: {len(whatsapp_events)} אירועי WhatsApp ביומן")
            
        except Exception as e:
            self.log(f"שגיאה: {str(e)}", "ERROR")

if __name__ == "__main__":
    checker = CheckWhatsAppEvents()
    checker.run()













