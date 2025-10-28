#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקה ואימות יומן timebro ויומן Eyal Barash
מחיקת אירועים שגויים ווידוא תקינות
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import json

class CalendarVerifier:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.token_file = 'token.json'
        
        # אנשי קשר תקפים מהרשימה
        from contacts_list import list_all_contacts
        self.valid_contacts = [contact['name'] for contact in list_all_contacts()]

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        elif level == "WARNING":
            emoji = "⚠️"
        else:
            emoji = "🔍"
        print(f"[{timestamp}] {emoji} {message}")

    def get_calendar_service(self):
        """חיבור לGoogle Calendar"""
        try:
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            service = build('calendar', 'v3', credentials=creds)
            return service
        except Exception as e:
            self.log(f"שגיאה בחיבור: {e}", "ERROR")
            return None

    def check_all_calendars_for_wrong_events(self):
        """בדיקת כל היומנים לאירועים שגויים"""
        self.log("בודק כל היומנים לאירועים שגויים...")
        
        service = self.get_calendar_service()
        if not service:
            return
        
        try:
            # קבלת כל היומנים
            calendars_result = service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            today = datetime.now()
            time_min = (today - timedelta(days=3)).isoformat() + 'Z'
            time_max = (today + timedelta(days=1)).isoformat() + 'Z'
            
            total_wrong_events = 0
            timebro_events = 0
            
            for calendar in calendars:
                calendar_id = calendar['id']
                calendar_name = calendar['summary']
                
                try:
                    events_result = service.events().list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        maxResults=100,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    events = events_result.get('items', [])
                    
                    if events:
                        self.log(f"יומן {calendar_name}: {len(events)} אירועים")
                        
                        # בדיקת אירועים
                        wrong_events = []
                        correct_events = []
                        
                        for event in events:
                            title = event.get('summary', '')
                            description = event.get('description', '')
                            
                            # זיהוי אירועים שיצרתי
                            is_my_event = (
                                'TimeBro' in title or 
                                'TimeBro Calendar' in description or
                                any(contact in title for contact in self.valid_contacts) or
                                any(wrong in title for wrong in ['שיתופים😏', 'חדשות'])
                            )
                            
                            if is_my_event:
                                # בדיקה אם הוא נכון או שגוי
                                is_wrong = (
                                    calendar_name.lower() != 'timebro' or  # לא ביומן הנכון
                                    any(wrong in title for wrong in ['שיתופים😏', 'חדשות בזמן', 'חדשות מהרגע']) or  # מקבוצות
                                    title.count('מייק') > 1  # כפילויות
                                )
                                
                                if is_wrong:
                                    wrong_events.append(event)
                                else:
                                    correct_events.append(event)
                                    if calendar_name.lower() == 'timebro':
                                        timebro_events += 1
                        
                        # מחיקת אירועים שגויים
                        for event in wrong_events:
                            try:
                                service.events().delete(
                                    calendarId=calendar_id,
                                    eventId=event['id']
                                ).execute()
                                
                                total_wrong_events += 1
                                self.log(f"   🗑️ נמחק מ-{calendar_name}: {event['summary'][:40]}...")
                                
                            except Exception as e:
                                self.log(f"   ❌ שגיאה במחיקה: {e}", "ERROR")
                        
                        # הצגת אירועים נכונים
                        for event in correct_events:
                            self.log(f"   ✅ נכון ב-{calendar_name}: {event['summary'][:40]}...")
                
                except Exception as e:
                    self.log(f"שגיאה ביומן {calendar_name}: {e}", "ERROR")
            
            print(f'\n📊 תוצאות בדיקה:')
            print(f'   🗑️ אירועים שגויים נמחקו: {total_wrong_events}')
            print(f'   ✅ אירועים נכונים ביומן timebro: {timebro_events}')
            
        except Exception as e:
            self.log(f"שגיאה בבדיקה: {e}", "ERROR")

def main():
    verifier = CalendarVerifier()
    verifier.check_all_calendars_for_wrong_events()

if __name__ == '__main__':
    main()
"













