#!/usr/bin/env python3
"""
Final Cleanup with Rate Limiting
ניקוי סופי עם המתנה בין בקשות למניעת Rate Limit
"""

import json
import time
import re
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
from contacts_list import CONTACTS_CONFIG

class FinalCleanupWithDelays:
    def __init__(self):
        self.calendar_id = "c_mjbk37j51lkl4pl8i9tk31ek3o@group.calendar.google.com"
        self.service = None
        self.relevant_contact_names = self._build_relevant_names_list()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "ℹ️"
        print(f"[{timestamp}] {emoji} {message}")

    def _build_relevant_names_list(self):
        """בונה רשימה של כל שמות אנשי הקשר הרלוונטיים"""
        relevant_names = []
        for company, config in CONTACTS_CONFIG.items():
            for contact in config["contacts"]:
                relevant_names.append(contact)
                # גרסאות מנוקות
                clean_name = contact.split('(')[0].strip() if '(' in contact else contact
                if clean_name != contact:
                    relevant_names.append(clean_name)
                if '/' in contact:
                    parts = contact.split('/')
                    for part in parts:
                        relevant_names.append(part.strip())
        
        return list(set(relevant_names))

    def authenticate_google_calendar(self):
        """מתחבר ל-Google Calendar API"""
        self.log("מתחבר ל-Google Calendar...")
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        self.log("התחברות ל-Google Calendar הושלמה", "SUCCESS")

    def find_generic_discussion_events(self):
        """מוצא אירועי דיון גנריים עם מספרי איש קשר"""
        self.log("מחפש אירועי דיון גנריים עם מספרי איש קשר...")
        
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                maxResults=2500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # מוצא אירועים עם פטרנים גנריים
            generic_events = []
            relevant_events = []
            
            for event in events:
                summary = event.get('summary', '')
                description = event.get('description', '')
                
                # זיהוי אירועים גנריים
                is_generic = (
                    re.search(r'דיון עבודה.*איש קשר \d+', summary) or
                    re.search(r'דיון מורחב.*איש קשר \d+', summary) or
                    re.search(r'שיחה עם איש קשר \d+', summary) or
                    re.search(r'מפגש \d+', summary) or
                    ('איש קשר' in summary and any(char.isdigit() for char in summary))
                )
                
                if is_generic:
                    # בדיקה אם האירוע הגנרי קשור לאיש קשר מהרשימה
                    full_text = f"{summary} {description}".lower()
                    is_relevant = False
                    
                    for contact_name in self.relevant_contact_names:
                        if contact_name.lower() in full_text:
                            is_relevant = True
                            break
                    
                    if not is_relevant:
                        generic_events.append(event)
                    else:
                        relevant_events.append(event)
            
            self.log(f"נמצאו {len(generic_events)} אירועי דיון גנריים למחיקה")
            self.log(f"נמצאו {len(relevant_events)} אירועי דיון רלוונטיים לשמירה")
            
            return generic_events, relevant_events
            
        except Exception as e:
            self.log(f"שגיאה בחיפוש: {str(e)}", "ERROR")
            return [], []

    def delete_events_with_delays(self, events_to_delete):
        """מוחק אירועים עם השהיות למניעת Rate Limit"""
        self.log(f"מוחק {len(events_to_delete)} אירועים עם השהיות...")
        
        deleted_count = 0
        failed_count = 0
        
        for i, event in enumerate(events_to_delete, 1):
            try:
                # המתנה בין בקשות
                if i > 1:
                    time.sleep(1)  # המתנה של שנייה בין מחיקות
                
                self.service.events().delete(
                    calendarId=self.calendar_id,
                    eventId=event['id']
                ).execute()
                
                deleted_count += 1
                summary = event.get('summary', 'ללא כותרת')[:50]
                
                if deleted_count % 10 == 0:
                    self.log(f"נמחקו {deleted_count}/{len(events_to_delete)}: {summary}...")
                
                # המתנה ארוכה יותר כל 50 מחיקות
                if deleted_count % 50 == 0:
                    self.log("המתנה ארוכה למניעת Rate Limit...")
                    time.sleep(5)
                    
            except Exception as e:
                failed_count += 1
                if "Rate Limit" in str(e):
                    self.log(f"Rate Limit - מחכה 10 שניות...")
                    time.sleep(10)
                    # ניסיון נוסף
                    try:
                        self.service.events().delete(
                            calendarId=self.calendar_id,
                            eventId=event['id']
                        ).execute()
                        deleted_count += 1
                    except:
                        self.log(f"נכשל גם בניסיון שני עבור {event['id']}", "ERROR")
                else:
                    self.log(f"שגיאה במחיקת {event['id']}: {str(e)}", "ERROR")
        
        self.log(f"הושלמה מחיקה: {deleted_count} הצליחו, {failed_count} נכשלו", "SUCCESS")
        return deleted_count, failed_count

    def display_events_for_deletion(self, events_to_delete):
        """מציג את האירועים שיימחקו"""
        print("\n❌ אירועים שיימחקו (דיון גנרי עם מספרי איש קשר):")
        print("=" * 70)
        
        for i, event in enumerate(events_to_delete[:20], 1):
            summary = event.get('summary', 'ללא כותרת')
            start_time = event.get('start', {}).get('dateTime', '')[:10]
            description = event.get('description', '')[:50]
            print(f"   {i}. [{start_time}] {summary}")
            if description and description.strip():
                print(f"      📄 {description}...")
        
        if len(events_to_delete) > 20:
            print(f"   ... ועוד {len(events_to_delete) - 20} אירועים דומים")
        
        print(f"\n📊 סך הכל אירועים למחיקה: {len(events_to_delete)}")

    def run(self):
        """מריץ את תהליך הניקוי הסופי"""
        try:
            self.log("מתחיל ניקוי סופי של אירועי דיון גנריים")
            print("=" * 70)
            
            # התחברות
            self.authenticate_google_calendar()
            
            # חיפוש אירועים גנריים
            events_to_delete, relevant_events = self.find_generic_discussion_events()
            
            if not events_to_delete:
                self.log("לא נמצאו אירועי דיון גנריים למחיקה", "SUCCESS")
                print("✅ היומן כבר נקי מאירועי דיון לא רלוונטיים!")
                return
            
            # הצגת האירועים למחיקה
            self.display_events_for_deletion(events_to_delete)
            
            # מחיקה עם השהיות
            deleted_count, failed_count = self.delete_events_with_delays(events_to_delete)
            
            # דוח סיכום
            print("\n📊 דוח ניקוי סופי")
            print("=" * 50)
            print(f"🗑️ אירועים גנריים שנמחקו: {deleted_count}")
            print(f"❌ אירועים שנכשלו במחיקה: {failed_count}")
            print(f"✅ אירועי WhatsApp רלוונטיים שנשמרו: {len(relevant_events)}")
            
            if failed_count > 0:
                print(f"\n⚠️ {failed_count} אירועים נכשלו - ניתן לנסות שוב מאוחר יותר")
            else:
                print("\n✅ כל האירועים הגנריים נמחקו בהצלחה!")
                print("📅 היומן עכשיו מכיל רק אירועים רלוונטיים מהרשימה שלך")
            
        except Exception as e:
            self.log(f"שגיאה: {str(e)}", "ERROR")
            raise

if __name__ == "__main__":
    cleanup = FinalCleanupWithDelays()
    cleanup.run()













