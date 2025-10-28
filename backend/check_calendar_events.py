#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת אירועים בלוח השנה
"""

from datetime import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os

def check_calendar_events():
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

    print(f'❌ נמצאו {len(problematic_events)} אירועים עם הכותרת "שיחה עם איש קשר לא ידוע":')
    for i, event in enumerate(problematic_events):
        summary = event.get('summary', 'ללא כותרת')
        event_id = event.get('id', 'ללא ID')
        print(f'  {i+1}. {summary} - ID: {event_id}')

    # חיפוש אירועים עם אימוג'י צ'ט (החדשים)
    chat_events = []
    for event in events:
        summary = event.get('summary', '')
        if '💬' in summary:
            chat_events.append(event)

    print(f'\n💬 נמצאו {len(chat_events)} אירועים עם אימוגי צ\'ט (החדשים):')
    for i, event in enumerate(chat_events[:10]):  # מציג 10 ראשונים
        summary = event.get('summary', 'ללא כותרת')
        print(f'  {i+1}. {summary}')

    if len(chat_events) > 10:
        print(f'  ... ועוד {len(chat_events) - 10} אירועים')

    # חיפוש אירועי שיחות טלפון
    call_events = []
    for event in events:
        summary = event.get('summary', '')
        if 'Call from' in summary or 'Call to' in summary:
            call_events.append(event)

    print(f'\n📞 נמצאו {len(call_events)} אירועי שיחות טלפון (לא נגענו בהם):')
    for i, event in enumerate(call_events[:5]):  # מציג 5 ראשונים
        summary = event.get('summary', 'ללא כותרת')
        print(f'  {i+1}. {summary}')

    if len(call_events) > 5:
        print(f'  ... ועוד {len(call_events) - 5} אירועי שיחות')

    return problematic_events, chat_events, call_events

if __name__ == "__main__":
    check_calendar_events()
