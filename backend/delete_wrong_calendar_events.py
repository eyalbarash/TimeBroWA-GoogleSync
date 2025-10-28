#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מחיקת כל האירועים השגויים שיצרתי ביומנים
"""

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from datetime import datetime, timedelta
import sqlite3
import json

class WrongEventsDeleter:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.token_file = 'token.json'
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        else:
            emoji = "🗑️"
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
            self.log(f"שגיאה בחיבור: {e}", "ERROR")
            return None

    def delete_all_wrong_events(self):
        """מחיקת כל האירועים השגויים"""
        self.log("מתחיל מחיקת כל האירועים השגויים...")
        
        service = self.get_calendar_service()
        if not service:
            return False
        
        try:
            # קבלת כל היומנים
            calendars_result = service.calendarList().list().execute()
            calendars = calendars_result.get('items', [])
            
            total_deleted = 0
            
            for calendar in calendars:
                calendar_id = calendar['id']
                calendar_name = calendar['summary']
                
                self.log(f"בודק יומן: {calendar_name}")
                
                # קבלת אירועים מהיום
                today = datetime.now()
                time_min = (today - timedelta(days=2)).isoformat() + 'Z'
                time_max = (today + timedelta(days=1)).isoformat() + 'Z'
                
                try:
                    events_result = service.events().list(
                        calendarId=calendar_id,
                        timeMin=time_min,
                        timeMax=time_max,
                        maxResults=500,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    
                    events = events_result.get('items', [])
                    self.log(f"   נמצאו {len(events)} אירועים")
                    
                    # מחיקת אירועים שנוצרו ע"י TimeBro
                    deleted_in_calendar = 0
                    for event in events:
                        title = event.get('summary', '')
                        description = event.get('description', '')
                        
                        # זיהוי אירועים שיצרתי
                        is_my_event = (
                            '[TimeBro]' in title or 
                            'TimeBro Calendar' in description or
                            'נוצר אוטומטית ע"י TimeBro' in description or
                            any(wrong_source in title for wrong_source in [
                                'שיתופים😏', 'חדשות בזמן', 'חדשות מהרגע'
                            ])
                        )
                        
                        if is_my_event:
                            try:
                                service.events().delete(
                                    calendarId=calendar_id,
                                    eventId=event['id']
                                ).execute()
                                
                                deleted_in_calendar += 1
                                total_deleted += 1
                                
                                if deleted_in_calendar <= 5:  # הצגת 5 ראשונים לכל יומן
                                    self.log(f"   🗑️ נמחק: {title[:50]}...")
                                
                            except Exception as e:
                                self.log(f"   ❌ שגיאה במחיקת {title[:30]}: {e}", "ERROR")
                    
                    if deleted_in_calendar > 5:
                        self.log(f"   🗑️ ... ועוד {deleted_in_calendar - 5} אירועים נמחקו")
                    
                    if deleted_in_calendar > 0:
                        self.log(f"   ✅ נמחקו {deleted_in_calendar} אירועים מיומן {calendar_name}", "SUCCESS")
                    
                except Exception as e:
                    self.log(f"   ❌ שגיאה ביומן {calendar_name}: {e}", "ERROR")
            
            self.log(f"✅ סה\"כ נמחקו {total_deleted} אירועים שגויים", "SUCCESS")
            
            # ניקוי מסד הנתונים המקומי
            self.clean_local_database()
            
            return True
            
        except Exception as e:
            self.log(f"שגיאה במחיקה: {e}", "ERROR")
            return False

    def clean_local_database(self):
        """ניקוי מסד הנתונים המקומי"""
        self.log("מנקה מסד נתונים מקומי...")
        
        try:
            conn = sqlite3.connect('timebro_calendar.db')
            cursor = conn.cursor()
            
            # מחיקת כל האירועים (התחלה מחדש)
            cursor.execute("DELETE FROM calendar_events")
            deleted_local = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.log(f"✅ נמחקו {deleted_local} אירועים ממסד מקומי", "SUCCESS")
            
        except Exception as e:
            self.log(f"שגיאה בניקוי מסד מקומי: {e}", "ERROR")

def main():
    deleter = WrongEventsDeleter()
    
    print('\n' + '='*70)
    print('🗑️ מחיקת כל האירועים השגויים שיצרתי')
    print('='*70)
    
    success = deleter.delete_all_wrong_events()
    
    if success:
        print('\n✅ כל האירועים השגויים נמחקו!')
        print('📅 היומנים נקיים ומוכנים להתחלה נכונה')
    else:
        print('\n❌ שגיאה במחיקה')

if __name__ == "__main__":
    main()













