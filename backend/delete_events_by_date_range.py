#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Delete Calendar Events by Date Range
Deletes all events from TimeBro calendar within a specified date range
"""

import os
import sys
import pickle
from datetime import datetime
from typing import List, Dict
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class EventDeleter:
    """Delete events from TimeBro Google Calendar by date range"""

    def __init__(self, start_date: str, end_date: str, dry_run=True):
        self.dry_run = dry_run
        self.start_date = start_date  # Format: YYYY-MM-DD
        self.end_date = end_date      # Format: YYYY-MM-DD
        self.timebro_calendar_id = None
        self.service = None
        self.log_entries = []

    def log(self, message, level="INFO"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_entries.append(log_entry)

        # Console output with colors
        if level == "SUCCESS":
            print(f"✅ {message}")
        elif level == "WARNING":
            print(f"⚠️  {message}")
        elif level == "ERROR":
            print(f"❌ {message}")
        else:
            print(f"ℹ️  {message}")

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
                    self.log("❌ קובץ credentials.json לא נמצא", "ERROR")
                    self.log("אנא הוסף את קובץ credentials.json מ-Google Cloud Console", "ERROR")
                    return False

                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)

            # Save credentials
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        self.service = build('calendar', 'v3', credentials=creds)
        self.log("✅ מחובר ל-Google Calendar", "SUCCESS")
        return True

    def find_timebro_calendar(self):
        """Find TimeBro calendar by name"""
        try:
            calendar_list = self.service.calendarList().list().execute()

            for calendar in calendar_list.get('items', []):
                if 'timebro' in calendar['summary'].lower():
                    self.timebro_calendar_id = calendar['id']
                    self.log(f"📅 נמצא יומן TimeBro: {calendar['summary']}", "SUCCESS")
                    return True

            self.log("❌ לא נמצא יומן TimeBro", "ERROR")
            return False

        except Exception as e:
            self.log(f"❌ שגיאה בחיפוש יומן: {e}", "ERROR")
            return False

    def fetch_events_in_range(self):
        """Fetch all events from TimeBro calendar within date range"""
        try:
            self.log(f"🔍 קורא אירועים מהיומן ({self.start_date} עד {self.end_date})...")

            events = []
            page_token = None

            # Convert dates to RFC3339 format with timezone
            time_min = f"{self.start_date}T00:00:00+03:00"
            time_max = f"{self.end_date}T23:59:59+03:00"

            while True:
                events_result = self.service.events().list(
                    calendarId=self.timebro_calendar_id,
                    timeMin=time_min,
                    timeMax=time_max,
                    maxResults=2500,
                    singleEvents=True,
                    orderBy='startTime',
                    pageToken=page_token
                ).execute()

                events.extend(events_result.get('items', []))
                page_token = events_result.get('nextPageToken')

                if not page_token:
                    break

            self.log(f"📊 נמצאו {len(events)} אירועים ביומן", "SUCCESS")
            return events

        except Exception as e:
            self.log(f"❌ שגיאה בקריאת אירועים: {e}", "ERROR")
            return []

    def preview_events(self, events):
        """Show preview of events to be deleted"""
        if not events:
            self.log("✅ אין אירועים למחיקה", "SUCCESS")
            return

        print("\n" + "="*70)
        print("📋 תצוגה מקדימה של אירועים שיימחקו")
        print("="*70 + "\n")

        for idx, event in enumerate(events[:20], 1):  # Show first 20
            title = event.get('summary', 'ללא כותרת')
            start = event['start'].get('dateTime', event['start'].get('date', 'Unknown'))
            event_id = event.get('id', 'Unknown')[:20]

            print(f"{idx}. 📌 {title}")
            print(f"   🕐 {start}")
            print(f"   🆔 {event_id}...")
            print()

        if len(events) > 20:
            print(f"... ועוד {len(events) - 20} אירועים\n")

        print("="*70)
        print(f"📊 סיכום:")
        print(f"   • {len(events)} אירועים ימחקו")
        print("="*70 + "\n")

    def delete_events(self, events):
        """Delete events from calendar"""
        if not events:
            return 0, 0

        deleted_count = 0
        failed_count = 0

        for idx, event in enumerate(events, 1):
            event_id = event['id']
            title = event.get('summary', 'ללא כותרת')[:30]

            if self.dry_run:
                self.log(f"   🔸 [{idx}/{len(events)}] [DRY RUN] היה מוחק: {title}", "WARNING")
                deleted_count += 1
            else:
                try:
                    self.service.events().delete(
                        calendarId=self.timebro_calendar_id,
                        eventId=event_id
                    ).execute()

                    self.log(f"   ✅ [{idx}/{len(events)}] נמחק: {title}", "SUCCESS")
                    deleted_count += 1

                except Exception as e:
                    self.log(f"   ❌ [{idx}/{len(events)}] שגיאה במחיקת {title}: {e}", "ERROR")
                    failed_count += 1

        return deleted_count, failed_count

    def run(self):
        """Main execution flow"""
        print("\n" + "="*70)
        print("🗑️  מוחק אירועים מיומן TimeBro")
        print("="*70 + "\n")

        if self.dry_run:
            print("⚠️  מצב DRY RUN - לא יבוצעו מחיקות בפועל\n")

        # Step 1: Authenticate
        if not self.authenticate_google():
            return False

        # Step 2: Find TimeBro calendar
        if not self.find_timebro_calendar():
            return False

        # Step 3: Fetch events in range
        events = self.fetch_events_in_range()
        if not events:
            self.log("אין אירועים למחיקה בטווח התאריכים", "WARNING")
            return True

        # Step 4: Preview events
        self.preview_events(events)

        # Step 5: Delete events
        print()
        deleted, failed = self.delete_events(events)

        # Step 6: Summary
        print("\n" + "="*70)
        print("📊 סיכום")
        print("="*70)
        print(f"✅ אירועים שנמחקו: {deleted}")
        if failed > 0:
            print(f"❌ אירועים שנכשלו: {failed}")
        print("="*70 + "\n")

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Delete events from TimeBro calendar by date range')
    parser.add_argument('--start-date', type=str, required=True,
                       help='Start date (YYYY-MM-DD, e.g., 2025-10-10)')
    parser.add_argument('--end-date', type=str, required=True,
                       help='End date (YYYY-MM-DD, e.g., 2025-10-28)')
    parser.add_argument('--dry-run', action='store_true', default=True,
                       help='Preview events without deleting (default: True)')
    parser.add_argument('--execute', action='store_true', default=False,
                       help='Actually delete events (use with caution!)')

    args = parser.parse_args()

    # Default to dry-run unless --execute is specified
    dry_run = not args.execute

    if not dry_run:
        print("\n" + "🚨"*25)
        print("WARNING: You are about to PERMANENTLY DELETE events!")
        print("🚨"*25 + "\n")
        print(f"Date range: {args.start_date} to {args.end_date}")
        print()
        response = input("Type 'DELETE' to confirm: ")
        if response != 'DELETE':
            print("Cancelled.")
            return

    # Run the deleter
    deleter = EventDeleter(
        start_date=args.start_date,
        end_date=args.end_date,
        dry_run=dry_run
    )
    success = deleter.run()

    if success:
        print("\n✅ הושלם בהצלחה!")
        if dry_run:
            print("\n💡 Tip: Run with --execute to actually delete events")
    else:
        print("\n❌ הפעולה נכשלה")
        sys.exit(1)


if __name__ == "__main__":
    main()
