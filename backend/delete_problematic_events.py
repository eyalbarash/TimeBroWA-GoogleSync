#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מחיקת אירועים בעייתיים עם הכותרת "שיחה עם איש קשר לא ידוע"
"""

from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

def delete_problematic_events():
    # הגדרות Google Calendar
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    credentials_file = 'credentials.json'
    token_file = 'token.json'
    timebro_calendar_id = 'c_mjbk37j51lkl4pl8i9tk31ek3o@group.calendar.google.com'

    # אימות
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print('❌ לא ניתן להתחבר ל-Google Calendar')
            return

    service = build('calendar', 'v3', credentials=creds)

    # קבלת כל האירועים
    print('🔍 בודק אירועים קיימים בלוח השנה...')
    events_result = service.events().list(
        calendarId=timebro_calendar_id,
        timeMin=datetime(2000, 1, 1).isoformat() + 'Z',
        maxResults=2500,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    print(f'📊 נמצאו {len(events)} אירועים בלוח השנה')

    # חיפוש אירועים עם הכותרת הבעייתית
    problematic_events = []
    for event in events:
        summary = event.get('summary', '')
        if 'שיחה עם איש קשר לא ידוע' in summary:
            problematic_events.append(event)

    print(f'❌ נמצאו {len(problematic_events)} אירועים עם הכותרת "שיחה עם איש קשר לא ידוע"')
    
    if not problematic_events:
        print('✅ אין אירועים בעייתיים למחיקה')
        return

    # מחיקת האירועים הבעייתיים
    deleted_count = 0
    for i, event in enumerate(problematic_events):
        try:
            event_id = event.get('id')
            event_title = event.get('summary', 'ללא כותרת')
            
            service.events().delete(
                calendarId=timebro_calendar_id,
                eventId=event_id
            ).execute()
            
            deleted_count += 1
            print(f'✅ נמחק: {event_title} ({i+1}/{len(problematic_events)})')
            
        except Exception as e:
            print(f'❌ שגיאה במחיקת אירוע {event_title}: {e}')

    print(f'\\n🎉 הושלמה מחיקת {deleted_count} אירועים בעייתיים')

if __name__ == "__main__":
    delete_problematic_events()


