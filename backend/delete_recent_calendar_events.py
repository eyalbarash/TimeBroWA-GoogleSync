#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מחיקת אירועי יומן שנוצרו לאחרונה
"""

import sqlite3
import os
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

class CalendarEventsCleaner:
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

    def get_events_to_delete(self, since_date):
        """קבלת אירועים למחיקה מהמסד המקומי"""
        try:
            if not os.path.exists(self.db_calendar):
                self.log("❌ מסד נתונים לא נמצא")
                return []
            
            conn = sqlite3.connect(self.db_calendar)
            cursor = conn.cursor()
            
            # קבלת אירועים שנוצרו מתאריך מסוים
            cursor.execute("""
                SELECT google_event_id, contact_name, start_datetime, created_at
                FROM simple_calendar_events
                WHERE created_at >= ? AND google_event_id IS NOT NULL
                ORDER BY created_at DESC
            """, (since_date.isoformat(),))
            
            events = cursor.fetchall()
            conn.close()
            
            self.log(f"נמצאו {len(events)} אירועים למחיקה")
            return events
            
        except Exception as e:
            self.log(f"❌ שגיאה בקבלת אירועים: {e}", "ERROR")
            return []

    def delete_calendar_events(self, events, service):
        """מחיקת אירועים מ-Google Calendar"""
        deleted_count = 0
        failed_count = 0
        
        for event_id, contact_name, start_time, created_at in events:
            try:
                # מחיקה מ-Google Calendar
                service.events().delete(
                    calendarId=self.timebro_calendar_id,
                    eventId=event_id
                ).execute()
                
                self.log(f"✅ נמחק: {contact_name} ({start_time})")
                deleted_count += 1
                
            except Exception as e:
                self.log(f"❌ שגיאה במחיקת {contact_name}: {e}", "ERROR")
                failed_count += 1
        
        return deleted_count, failed_count

    def delete_from_local_db(self, since_date):
        """מחיקת אירועים מהמסד המקומי"""
        try:
            conn = sqlite3.connect(self.db_calendar)
            cursor = conn.cursor()
            
            # מחיקה מהמסד המקומי
            cursor.execute("""
                DELETE FROM simple_calendar_events
                WHERE created_at >= ?
            """, (since_date.isoformat(),))
            
            deleted_rows = cursor.rowcount
            conn.commit()
            conn.close()
            
            self.log(f"✅ נמחקו {deleted_rows} רשומות מהמסד המקומי")
            return deleted_rows
            
        except Exception as e:
            self.log(f"❌ שגיאה במחיקה מהמסד המקומי: {e}", "ERROR")
            return 0

    def clean_recent_events(self, hours_back=24):
        """מחיקת אירועים מהשעות האחרונות"""
        since_date = datetime.now() - timedelta(hours=hours_back)
        
        self.log(f"🗑️ מוחק אירועים שנוצרו מ-{since_date.strftime('%d/%m/%Y %H:%M')}")
        
        # קבלת אירועים למחיקה
        events = self.get_events_to_delete(since_date)
        
        if not events:
            self.log("✅ אין אירועים למחיקה")
            return True
        
        # אימות Google Calendar
        service = self.authenticate_google_calendar()
        if not service:
            return False
        
        # מחיקה מ-Google Calendar
        deleted, failed = self.delete_calendar_events(events, service)
        
        # מחיקה מהמסד המקומי
        local_deleted = self.delete_from_local_db(since_date)
        
        # סיכום
        self.log(f"✅ סיכום: {deleted} אירועים נמחקו, {failed} נכשלו")
        
        return failed == 0

def main():
    """הפעלה ראשית"""
    cleaner = CalendarEventsCleaner()
    
    print("🗑️ מחיקת אירועי יומן מאמש")
    print("=" * 50)
    
    # מחיקת אירועים מה-24 שעות האחרונות
    success = cleaner.clean_recent_events(hours_back=24)
    
    if success:
        print("\n✅ מחיקה הושלמה בהצלחה!")
        print("📅 היומן נוקה מאירועים שנוצרו אמש")
    else:
        print("\n❌ מחיקה נכשלה")
        print("📋 בדוק את השגיאות למעלה")

if __name__ == "__main__":
    main()
