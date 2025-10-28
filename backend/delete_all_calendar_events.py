#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מחיקת כל האירועים בלוח שנה TimeBro
"""

import sqlite3
import os
from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class AllCalendarEventsCleaner:
    def __init__(self):
        self.timebro_calendar_id = 'c_mjbk37j51lkl4pl8i9tk31ek3o@group.calendar.google.com'
        self.db_calendar = 'timebro_calendar.db'
        
        # Google Calendar API
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.credentials_file = 'credentials.json'
        self.token_file = 'token.json'

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        else:
            emoji = "🗑️"
        print(f"[{timestamp}] {emoji} {message}")

    def authenticate_google_calendar(self):
        """אימות Google Calendar API"""
        creds = None
        
        if os.path.exists(self.token_file):
            creds = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                self.log("❌ קובץ credentials.json לא נמצא", "ERROR")
                return None
            
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        try:
            service = build('calendar', 'v3', credentials=creds)
            self.log("✅ חיבור לGoogle Calendar הצליח", "SUCCESS")
            return service
        except Exception as e:
            self.log(f"❌ שגיאה בחיבור לGoogle Calendar: {e}", "ERROR")
            return None

    def get_all_events_from_google(self, service):
        """קבלת כל האירועים מ-Google Calendar"""
        try:
            self.log("📡 מקבל כל האירועים מ-Google Calendar...")
            
            events_result = service.events().list(
                calendarId=self.timebro_calendar_id,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            self.log(f"📊 נמצאו {len(events)} אירועים ב-Google Calendar")
            return events
            
        except Exception as e:
            self.log(f"❌ שגיאה בקבלת אירועים מ-Google Calendar: {e}", "ERROR")
            return []

    def delete_all_google_events(self, service, events):
        """מחיקת כל האירועים מ-Google Calendar"""
        deleted_count = 0
        failed_count = 0
        
        self.log(f"🗑️ מוחק {len(events)} אירועים מ-Google Calendar...")
        
        for i, event in enumerate(events):
            try:
                event_id = event['id']
                event_title = event.get('summary', 'ללא כותרת')
                
                # מחיקה מ-Google Calendar
                service.events().delete(
                    calendarId=self.timebro_calendar_id,
                    eventId=event_id
                ).execute()
                
                self.log(f"✅ נמחק: {event_title} ({i+1}/{len(events)})")
                deleted_count += 1
                
            except Exception as e:
                self.log(f"❌ שגיאה במחיקת {event_title}: {e}", "ERROR")
                failed_count += 1
        
        return deleted_count, failed_count

    def delete_all_local_events(self):
        """מחיקת כל האירועים מהמסד המקומי"""
        try:
            if not os.path.exists(self.db_calendar):
                self.log("⚠️ מסד נתונים לא נמצא - מדלג על מחיקה מקומית")
                return 0
            
            conn = sqlite3.connect(self.db_calendar)
            cursor = conn.cursor()
            
            # קבלת מספר האירועים לפני מחיקה
            cursor.execute("SELECT COUNT(*) FROM simple_calendar_events")
            count_before = cursor.fetchone()[0]
            
            # מחיקה של כל האירועים
            cursor.execute("DELETE FROM simple_calendar_events")
            
            deleted_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.log(f"✅ נמחקו {deleted_rows} רשומות מהמסד המקומי")
            return deleted_rows
            
        except Exception as e:
            self.log(f"❌ שגיאה במחיקה מהמסד המקומי: {e}", "ERROR")
            return 0

    def clean_all_events(self):
        """מחיקת כל האירועים"""
        self.log("🗑️ מתחיל מחיקת כל האירועים בלוח שנה TimeBro")
        
        # אימות Google Calendar
        service = self.authenticate_google_calendar()
        if not service:
            return False, 0
        
        # קבלת כל האירועים
        events = self.get_all_events_from_google(service)
        
        if not events:
            self.log("✅ אין אירועים למחיקה ב-Google Calendar")
            # עדיין נמחק מהמסד המקומי
            local_deleted = self.delete_all_local_events()
            return True, local_deleted
        
        # מחיקה מ-Google Calendar
        google_deleted, google_failed = self.delete_all_google_events(service, events)
        
        # מחיקה מהמסד המקומי
        local_deleted = self.delete_all_local_events()
        
        # סיכום
        total_deleted = google_deleted + local_deleted
        self.log(f"✅ סיכום: {google_deleted} אירועים נמחקו מ-Google Calendar, {local_deleted} מהמסד המקומי")
        
        if google_failed > 0:
            self.log(f"⚠️ {google_failed} אירועים נכשלו במחיקה מ-Google Calendar", "ERROR")
        
        return google_failed == 0, total_deleted

def main():
    """הפעלה ראשית"""
    cleaner = AllCalendarEventsCleaner()
    
    print("🗑️ מחיקת כל האירועים בלוח שנה TimeBro")
    print("=" * 60)
    
    # מחיקת כל האירועים
    success, total_deleted = cleaner.clean_all_events()
    
    if success:
        print(f"\n✅ מחיקה הושלמה בהצלחה!")
        print(f"📊 סה\"כ נמחקו {total_deleted} אירועים")
        return total_deleted
    else:
        print("\n❌ מחיקה נכשלה חלקית")
        print("📋 בדוק את השגיאות למעלה")
        return 0

if __name__ == "__main__":
    deleted_count = main()
    print(f"\n🎯 מספר האירועים שנמחקו: {deleted_count}")


