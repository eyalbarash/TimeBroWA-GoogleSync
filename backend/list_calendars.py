#!/usr/bin/env python3
"""
List all accessible calendars to find the correct TimeBro calendar ID
"""

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def list_calendars():
    """List all calendars accessible to the authenticated user"""
    
    # Load existing credentials
    if not os.path.exists('token.json'):
        print("❌ No authentication token found. Please run timebro_calendar.py first.")
        return
        
    creds = Credentials.from_authorized_user_file('token.json')
    
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        print("📅 Listing all accessible calendars...")
        print("="*60)
        
        # Get calendar list
        calendar_list = service.calendarList().list().execute()
        calendars = calendar_list.get('items', [])
        
        if not calendars:
            print("❌ No calendars found")
            return
            
        print(f"Found {len(calendars)} calendars:\n")
        
        for i, calendar in enumerate(calendars, 1):
            calendar_id = calendar['id']
            summary = calendar.get('summary', 'No name')
            access_role = calendar.get('accessRole', 'Unknown')
            primary = calendar.get('primary', False)
            
            print(f"{i}. 📊 {summary}")
            print(f"   🆔 ID: {calendar_id}")
            print(f"   🔑 Access: {access_role}")
            if primary:
                print("   ⭐ Primary calendar")
            print()
            
            # Check if this looks like TimeBro calendar
            if 'timebro' in summary.lower() or 'tkbk37j51lkl4pl8i9tk31ek3o' in calendar_id:
                print(f"   🎯 THIS MIGHT BE YOUR TIMEBRO CALENDAR!")
                print()
        
        # Show the original calendar ID we were trying to use
        original_id = "c_tkbk37j51lkl4pl8i9tk31ek3o@group.calendar.google.com"
        print(f"🔍 Original TimeBro calendar ID we tried:")
        print(f"   {original_id}")
        print()
        
        # Check if any calendar ID matches or contains the pattern
        matching_calendars = []
        for calendar in calendars:
            if 'tkbk37j51lkl4pl8i9tk31ek3o' in calendar['id']:
                matching_calendars.append(calendar)
                
        if matching_calendars:
            print("✅ Found matching TimeBro calendar(s):")
            for cal in matching_calendars:
                print(f"   🎯 {cal['summary']}: {cal['id']}")
        else:
            print("⚠️ No calendars found matching the TimeBro pattern")
            print("💡 The TimeBro calendar might need to be shared with your Google account")
            
    except HttpError as error:
        print(f"❌ Error accessing calendars: {error}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    list_calendars()














