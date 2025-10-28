#!/usr/bin/env python3
"""
Test calendar event creation from existing messages
This bypasses Green API and works directly with database messages
"""

import sys
from datetime import datetime, timedelta
from simple_timebro_calendar import SimpleTimeBroCalendar

def main():
    print("=" * 60)
    print("📅 Testing Calendar Event Creation from Existing Messages")
    print("=" * 60)

    # Get date range from arguments or use defaults
    if len(sys.argv) == 3:
        start_date_str = sys.argv[1]  # Format: YYYY-MM-DD
        end_date_str = sys.argv[2]    # Format: YYYY-MM-DD
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    else:
        # Default: last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)

    print(f"\n📅 Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"🕐 This will process messages from existing database")
    print(f"✅ No Green API connection needed\n")

    # Initialize calendar system
    calendar = SimpleTimeBroCalendar()

    print("📊 Getting messages from database...")
    messages = calendar.get_messages_for_date_range(start_date, end_date)

    if not messages:
        print("\n❌ No messages found in database for this date range")
        print("💡 Try a different date range or check if messages exist:")
        print("   sqlite3 whatsapp_messages_webjs.db 'SELECT COUNT(*) FROM messages;'")
        return

    print(f"✅ Found {len(messages)} messages from approved contacts")

    # Group messages
    print("\n🔄 Grouping messages by contact and time...")
    conversations = calendar.group_messages_by_contact_and_time(messages)
    print(f"✅ Grouped into {len(conversations)} conversation sessions")

    # Authenticate with Google Calendar
    print("\n🔐 Connecting to Google Calendar...")
    service = calendar.authenticate_google_calendar()

    if not service:
        print("❌ Failed to connect to Google Calendar")
        print("💡 Check your credentials.json and token.json files")
        return

    print("✅ Connected to Google Calendar")

    # Create events
    print(f"\n📝 Creating calendar events...")
    events_created = 0
    events_skipped = 0

    for conv_key, conversation in conversations.items():
        contact_name = conversation['contact_name']
        print(f"\n👤 Processing: {contact_name}")
        print(f"   Messages: {len(conversation['messages'])}")
        print(f"   Time: {conversation['start_time'].strftime('%Y-%m-%d %H:%M')} - {conversation['end_time'].strftime('%H:%M')}")

        success = calendar.create_calendar_event(contact_name, conversation, service)

        if success:
            events_created += 1
            print(f"   ✅ Event created")
        else:
            events_skipped += 1
            print(f"   ⚠️  Event skipped (duplicate or error)")

    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"   ✅ Events created: {events_created}")
    print(f"   ⚠️  Events skipped: {events_skipped}")
    print(f"   📅 Total conversations: {len(conversations)}")
    print("=" * 60)

    if events_created > 0:
        print(f"\n🎉 Success! Check your TimeBro calendar:")
        print(f"   https://calendar.google.com")
        print(f"\n💡 Calendar ID: {calendar.timebro_calendar_id}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        print("Usage: python3 test_calendar_creation.py [start_date] [end_date]")
        print("\nExamples:")
        print("  python3 test_calendar_creation.py                    # Last 7 days")
        print("  python3 test_calendar_creation.py 2025-10-01 2025-10-27  # Specific range")
        sys.exit(0)

    main()
