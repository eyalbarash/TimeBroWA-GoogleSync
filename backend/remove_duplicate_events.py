#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Remove Duplicate Events from TimeBro Calendar
Finds and removes exact duplicate calendar events (same title + start + end time)
"""

import os
import sys
import sqlite3
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

class DuplicateEventRemover:
    """Remove duplicate events from TimeBro Google Calendar"""

    def __init__(self, dry_run=True, start_date=None, end_date=None):
        self.dry_run = dry_run
        self.db_calendar = 'timebro_calendar.db'
        self.timebro_calendar_id = None
        self.service = None
        self.start_date = start_date
        self.end_date = end_date

        # Initialize logging
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

    def fetch_all_events(self):
        """Fetch all events from TimeBro calendar"""
        try:
            if self.start_date and self.end_date:
                self.log(f"🔍 קורא אירועים מהיומן ({self.start_date} עד {self.end_date})...")
            else:
                self.log("🔍 קורא אירועים מהיומן...")

            events = []
            page_token = None

            # Build query parameters
            query_params = {
                'calendarId': self.timebro_calendar_id,
                'maxResults': 2500,
                'singleEvents': True,
                'orderBy': 'startTime',
            }

            # Add date range if specified
            if self.start_date:
                query_params['timeMin'] = self.start_date
            if self.end_date:
                query_params['timeMax'] = self.end_date

            while True:
                query_params['pageToken'] = page_token
                events_result = self.service.events().list(**query_params).execute()

                events.extend(events_result.get('items', []))
                page_token = events_result.get('nextPageToken')

                if not page_token:
                    break

            self.log(f"📊 נמצאו {len(events)} אירועים ביומן", "SUCCESS")
            return events

        except Exception as e:
            self.log(f"❌ שגיאה בקריאת אירועים: {e}", "ERROR")
            return []

    def find_duplicates(self, events):
        """
        Find duplicate events - same title, start time, and end time
        Returns: Dict[signature, List[event]]
        """
        self.log("🔍 מחפש כפילויות...")

        # Group events by (title, start, end)
        event_groups = defaultdict(list)

        for event in events:
            # Skip events without required fields
            if 'summary' not in event or 'start' not in event or 'end' not in event:
                continue

            title = event.get('summary', '')

            # Get start/end times
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            # Create unique signature
            signature = (title, start, end)

            # Add event to group
            event_groups[signature].append(event)

        # Filter only groups with duplicates (2+ events)
        duplicates = {sig: events for sig, events in event_groups.items() if len(events) > 1}

        if duplicates:
            total_duplicate_events = sum(len(events) - 1 for events in duplicates.values())
            self.log(f"📊 נמצאו {len(duplicates)} קבוצות כפילויות ({total_duplicate_events} אירועים כפולים)", "SUCCESS")
        else:
            self.log("✅ לא נמצאו כפילויות!", "SUCCESS")

        return duplicates

    def preview_duplicates(self, duplicates):
        """Show preview of duplicate events"""
        if not duplicates:
            self.log("✅ אין כפילויות להצגה", "SUCCESS")
            return

        print("\n" + "="*70)
        print("📋 תצוגה מקדימה של כפילויות")
        print("="*70 + "\n")

        total_to_delete = 0

        for idx, (signature, events) in enumerate(duplicates.items(), 1):
            title, start, end = signature
            duplicate_count = len(events) - 1  # Minus one because we keep the oldest
            total_to_delete += duplicate_count

            print(f"{idx}. 📌 {title}")
            print(f"   🕐 {start} → {end}")
            print(f"   🔢 {len(events)} אירועים (נמחק {duplicate_count})")

            # Show event IDs and creation dates
            for i, event in enumerate(events, 1):
                created = event.get('created', 'Unknown')
                event_id = event.get('id', 'Unknown')[:20]
                marker = "🔒 KEEP" if i == 1 else "🗑️  DELETE"
                print(f"      {marker} - ID: {event_id}... (Created: {created})")

            print()

        print("="*70)
        print(f"📊 סיכום:")
        print(f"   • {len(duplicates)} קבוצות כפילויות")
        print(f"   • {total_to_delete} אירועים יימחקו")
        print(f"   • {len(duplicates)} אירועים ישמרו")
        print("="*70 + "\n")

    def remove_duplicates(self, duplicates):
        """Remove duplicate events (keep oldest by creation date)"""
        if not duplicates:
            return 0, 0

        deleted_count = 0
        failed_count = 0

        for signature, events in duplicates.items():
            title, start, end = signature

            # Sort by creation date (oldest first)
            sorted_events = sorted(events, key=lambda e: e.get('created', ''))

            # Keep the oldest, delete the rest
            events_to_delete = sorted_events[1:]

            self.log(f"🔄 מעבד: {title[:50]}... ({len(events_to_delete)} כפילויות)")

            for event in events_to_delete:
                event_id = event['id']

                if self.dry_run:
                    self.log(f"   🔸 [DRY RUN] היה מוחק: {event_id[:20]}...", "WARNING")
                    deleted_count += 1
                else:
                    try:
                        self.service.events().delete(
                            calendarId=self.timebro_calendar_id,
                            eventId=event_id
                        ).execute()

                        self.log(f"   ✅ נמחק: {event_id[:20]}...", "SUCCESS")
                        deleted_count += 1

                    except Exception as e:
                        self.log(f"   ❌ שגיאה במחיקת {event_id[:20]}...: {e}", "ERROR")
                        failed_count += 1

        return deleted_count, failed_count

    def update_local_database(self, duplicates):
        """Remove duplicate entries from local database"""
        if self.dry_run:
            self.log("🔸 [DRY RUN] לא מעדכן מסד נתונים מקומי", "WARNING")
            return 0

        try:
            conn = sqlite3.connect(self.db_calendar)
            cursor = conn.cursor()

            # Remove duplicates from local DB
            # Keep only one record per (contact_name, start_datetime, end_datetime)
            cursor.execute("""
                DELETE FROM simple_calendar_events
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM simple_calendar_events
                    GROUP BY contact_name, start_datetime, end_datetime
                )
            """)

            removed = cursor.rowcount
            conn.commit()
            conn.close()

            if removed > 0:
                self.log(f"✅ הוסרו {removed} כפילויות ממסד נתונים מקומי", "SUCCESS")
            else:
                self.log("ℹ️  אין כפילויות במסד נתונים מקומי", "INFO")

            return removed

        except Exception as e:
            self.log(f"❌ שגיאה בעדכון מסד נתונים: {e}", "ERROR")
            return 0

    def run(self):
        """Main execution flow"""
        print("\n" + "="*70)
        print("🧹 מסיר כפילויות מיומן TimeBro")
        print("="*70 + "\n")

        if self.dry_run:
            print("⚠️  מצב DRY RUN - לא יבוצעו מחיקות בפועל\n")

        # Step 1: Authenticate
        if not self.authenticate_google():
            return False

        # Step 2: Find TimeBro calendar
        if not self.find_timebro_calendar():
            return False

        # Step 3: Fetch all events
        events = self.fetch_all_events()
        if not events:
            self.log("אין אירועים לעיבוד", "WARNING")
            return True

        # Step 4: Find duplicates
        duplicates = self.find_duplicates(events)

        # Step 5: Preview duplicates
        if duplicates:
            self.preview_duplicates(duplicates)

            # Step 6: Remove duplicates (confirmation already done in main())
            print()
            deleted, failed = self.remove_duplicates(duplicates)

            # Step 8: Update local database
            if not self.dry_run:
                db_removed = self.update_local_database(duplicates)

            # Step 9: Summary
            print("\n" + "="*70)
            print("📊 סיכום")
            print("="*70)
            print(f"✅ אירועים שנמחקו: {deleted}")
            if failed > 0:
                print(f"❌ אירועים שנכשלו: {failed}")
            if not self.dry_run:
                print(f"💾 הוסרו ממסד נתונים: {db_removed}")
            print("="*70 + "\n")

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Remove duplicate events from TimeBro calendar')
    parser.add_argument('--dry-run', action='store_true', default=False,
                       help='Preview duplicates without deleting (default: False)')
    parser.add_argument('--execute', action='store_true', default=False,
                       help='Actually delete duplicates (use with caution!)')
    parser.add_argument('--start-date', type=str, default=None,
                       help='Start date in ISO format (e.g., 2025-08-01T00:00:00+03:00)')
    parser.add_argument('--end-date', type=str, default=None,
                       help='End date in ISO format (e.g., 2025-10-28T23:59:59+03:00)')

    args = parser.parse_args()

    # Default to dry-run unless --execute is specified
    dry_run = not args.execute

    if not dry_run:
        print("\n" + "🚨"*25)
        print("WARNING: You are about to PERMANENTLY DELETE duplicate events!")
        print("🚨"*25 + "\n")
        response = input("Type 'DELETE' to confirm: ")
        if response != 'DELETE':
            print("Cancelled.")
            return

    # Run the remover
    remover = DuplicateEventRemover(
        dry_run=dry_run,
        start_date=args.start_date,
        end_date=args.end_date
    )
    success = remover.run()

    if success:
        print("\n✅ הושלם בהצלחה!")
        if dry_run:
            print("\n💡 Tip: Run with --execute to actually delete duplicates")
    else:
        print("\n❌ הפעולה נכשלה")
        sys.exit(1)


if __name__ == "__main__":
    main()
