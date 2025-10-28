#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify Event Times in TimeBro Calendar
Check that events have correct start/end times based on message timestamps
"""

import os
import sys
import pickle
import sqlite3
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class EventTimeVerifier:
    """Verify event times match message timestamps"""

    def __init__(self):
        self.timebro_calendar_id = None
        self.service = None
        self.messages_db = 'messages.db'

    def authenticate_google(self):
        """Authenticate with Google Calendar API"""
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None

        # Load credentials
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)

        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    print("❌ קובץ credentials.json לא נמצא")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)
        print("✅ מחובר ל-Google Calendar")
        return True

    def find_timebro_calendar(self):
        """Find TimeBro calendar by name"""
        try:
            calendar_list = self.service.calendarList().list().execute()

            for calendar in calendar_list.get('items', []):
                if 'timebro' in calendar['summary'].lower():
                    self.timebro_calendar_id = calendar['id']
                    print(f"📅 נמצא יומן TimeBro: {calendar['summary']}")
                    return True

            print("❌ לא נמצא יומן TimeBro")
            return False

        except Exception as e:
            print(f"❌ שגיאה בחיפוש יומן: {e}")
            return False

    def fetch_recent_events(self, limit=10):
        """Fetch recent events from TimeBro calendar"""
        try:
            print(f"\n🔍 מביא {limit} אירועים אחרונים...")

            # Get events from October 10, 2025
            time_min = f"2025-10-10T00:00:00+03:00"
            time_max = f"2025-10-28T23:59:59+03:00"

            events_result = self.service.events().list(
                calendarId=self.timebro_calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=limit,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])
            print(f"📊 נמצאו {len(events)} אירועים")
            return events

        except Exception as e:
            print(f"❌ שגיאה בקריאת אירועים: {e}")
            return []

    def get_messages_for_contact(self, whatsapp_id, start_dt, end_dt):
        """Get messages for a contact within date range"""
        try:
            conn = sqlite3.connect(self.messages_db)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, chat_id, type, body, timestamp, type_message, timestamp
                FROM messages
                WHERE chat_id = ?
                AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp ASC
            """, (whatsapp_id, int(start_dt.timestamp() * 1000), int(end_dt.timestamp() * 1000)))

            messages = cursor.fetchall()
            conn.close()

            return messages

        except Exception as e:
            print(f"❌ שגיאה בקריאת הודעות: {e}")
            return []

    def verify_events(self, events):
        """Verify that event times match message timestamps"""
        print("\n" + "="*70)
        print("📋 בדיקת זמני אירועים")
        print("="*70 + "\n")

        verified = 0
        issues = 0

        for idx, event in enumerate(events, 1):
            title = event.get('summary', 'ללא כותרת')
            start_str = event['start'].get('dateTime', event['start'].get('date'))
            end_str = event['end'].get('dateTime', event['end'].get('date'))

            # Parse datetime
            start_dt = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_str.replace('Z', '+00:00'))

            duration = (end_dt - start_dt).total_seconds() / 60

            print(f"{idx}. 📌 {title}")
            print(f"   🕐 התחלה: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   🕐 סיום: {end_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   ⏱️  משך: {duration:.1f} דקות")

            # Check minimum duration
            if duration < 5:
                print(f"   ⚠️  WARNING: משך פחות מ-5 דקות!")
                issues += 1
            else:
                print(f"   ✅ משך תקין (מינימום 5 דקות)")
                verified += 1

            print()

        print("="*70)
        print(f"📊 סיכום:")
        print(f"   ✅ אירועים תקינים: {verified}")
        print(f"   ⚠️  אירועים עם בעיות: {issues}")
        print("="*70 + "\n")

        return verified, issues

    def run(self):
        """Main execution flow"""
        print("\n" + "="*70)
        print("🔍 בודק זמני אירועים ביומן TimeBro")
        print("="*70 + "\n")

        # Step 1: Authenticate
        if not self.authenticate_google():
            return False

        # Step 2: Find TimeBro calendar
        if not self.find_timebro_calendar():
            return False

        # Step 3: Fetch recent events
        events = self.fetch_recent_events(limit=20)
        if not events:
            print("⚠️  אין אירועים לבדיקה")
            return True

        # Step 4: Verify event times
        verified, issues = self.verify_events(events)

        return issues == 0


def main():
    """Main entry point"""
    verifier = EventTimeVerifier()
    success = verifier.run()

    if success:
        print("\n✅ כל האירועים תקינים!")
    else:
        print("\n⚠️  נמצאו בעיות באירועים")
        sys.exit(1)


if __name__ == "__main__":
    main()
