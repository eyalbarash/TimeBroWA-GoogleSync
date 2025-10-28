#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הגדרת Google Calendar API אוטומטית
"""

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class GoogleCalendarSetup:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.credentials_file = 'credentials.json'
        self.token_file = 'token.json'
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "📅" if level == "INFO" else "✅" if level == "SUCCESS" else "❌"
        print(f"[{timestamp}] {emoji} {message}")

    def create_sample_credentials(self):
        """יצירת קובץ credentials לדוגמה"""
        if not os.path.exists(self.credentials_file):
            sample_creds = {
                "web": {
                    "client_id": "YOUR_CLIENT_ID.googleusercontent.com",
                    "project_id": "timebro-calendar",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "client_secret": "YOUR_CLIENT_SECRET",
                    "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
                }
            }
            
            with open(self.credentials_file, 'w') as f:
                json.dump(sample_creds, f, indent=2)
            
            print(f"⚠️ נוצר קובץ credentials לדוגמה: {self.credentials_file}")
            print(f"📋 יש להחליף עם הפרטים האמיתיים מ-Google Cloud Console")
            return False
        
        return True

    def get_calendar_service(self):
        """קבלת שירות Google Calendar"""
        try:
            creds = None
            
            # טעינת token קיים
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            
            # בדיקת תקפות
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    print("✅ Google Calendar token התחדש")
                else:
                    if not os.path.exists(self.credentials_file):
                        self.create_sample_credentials()
                        return None
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES)
                    creds = flow.run_local_server(port=8080)
                    print("✅ אימות Google Calendar הושלם")
                
                # שמירת token
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
            
            service = build('calendar', 'v3', credentials=creds)
            print("✅ חיבור לGoogle Calendar API הצליח")
            return service
            
        except Exception as e:
            print(f"❌ שגיאה בחיבור לGoogle Calendar: {e}")
            return None

    def test_calendar_access(self):
        """בדיקת גישה ליומן"""
        service = self.get_calendar_service()
        
        if not service:
            return False
        
        try:
            # קבלת רשימת יומנים
            calendars_result = service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            print(f"📅 נמצאו {len(calendars)} יומנים:")
            for cal in calendars:
                print(f"   📋 {cal['summary']} (ID: {cal['id']})")
            
            # חיפוש יומן timebro או יצירתו
            timebro_calendar = None
            for cal in calendars:
                if cal['summary'].lower() == 'timebro':
                    timebro_calendar = cal
                    break
            
            if not timebro_calendar:
                print("📅 יומן timebro לא קיים - יוצר חדש...")
                timebro_calendar = self.create_timebro_calendar(service)
            
            if timebro_calendar:
                print(f"✅ יומן timebro מוכן: {timebro_calendar['id']}")
                return timebro_calendar['id']
            
            return None
            
        except Exception as e:
            print(f"❌ שגיאה בבדיקת גישה: {e}")
            return None

    def create_timebro_calendar(self, service):
        """יצירת יומן timebro חדש"""
        try:
            calendar = {
                'summary': 'timebro',
                'description': 'יומן אוטומטי מהשיחות בוואטסאפ - TimeBro Calendar System',
                'timeZone': 'Asia/Jerusalem'
            }
            
            created_calendar = service.calendars().insert(body=calendar).execute()
            print(f"✅ יומן timebro נוצר: {created_calendar['id']}")
            return created_calendar
            
        except Exception as e:
            print(f"❌ שגיאה ביצירת יומן: {e}")
            return None

def main():
    setup = GoogleCalendarSetup()
    
    print("📅 מגדיר Google Calendar API לTimeBro...")
    
    # בדיקת גישה
    calendar_id = setup.test_calendar_access()
    
    if calendar_id:
        print(f"\n🎉 הגדרה הושלמה בהצלחה!")
        print(f"📅 יומן timebro מוכן: {calendar_id}")
        
        # שמירת הגדרות
        config = {
            'timebro_calendar_id': calendar_id,
            'setup_completed': True,
            'setup_time': datetime.now().isoformat()
        }
        
        with open('timebro_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"⚙️ הגדרות נשמרו: timebro_config.json")
    else:
        print(f"\n❌ הגדרה נכשלה")
        print(f"📋 ודא שיש לך קובץ credentials.json תקין")

if __name__ == "__main__":
    from datetime import datetime
    main()













