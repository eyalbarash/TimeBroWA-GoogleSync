#!/usr/bin/env python3
"""
Cleanup Irrelevant Calendar Events
מחיקת אירועים לא רלוונטיים ביומן בלבד
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
from contacts_list import CONTACTS_CONFIG

class CleanupIrrelevantEvents:
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
                # נוסיף גם גרסאות מנוקות של השמות
                relevant_names.append(contact)
                # נוסיף גם את השם ללא סוגריים
                clean_name = re.sub(r'\s*\([^)]*\)', '', contact).strip()
                if clean_name != contact:
                    relevant_names.append(clean_name)
                # נוסיף גם חלקי שמות
                if '/' in contact:
                    parts = contact.split('/')
                    for part in parts:
                        relevant_names.append(part.strip())
        
        return list(set(relevant_names))  # הסרת כפילויות

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

    def is_event_relevant(self, event):
        """בודק אם אירוע רלוונטי לרשימת אנשי הקשר"""
        summary = event.get('summary', '')
        description = event.get('description', '')
        
        # אירועים שאינם של WhatsApp - לא נוגעים בהם
        if not any(keyword in summary.lower() for keyword in ['שיחה עם', 'whatsapp', 'wa.me']) and \
           not any(keyword in description.lower() for keyword in ['whatsapp', 'wa.me', 'קישור לפתיחה']):
            return "not_whatsapp"  # לא אירוע WhatsApp - לא נוגעים
        
        # בדיקה אם האירוע מכיל שם של איש קשר מהרשימה
        full_text = f"{summary} {description}".lower()
        
        for contact_name in self.relevant_contact_names:
            # בדיקה של השם במלואו
            if contact_name.lower() in full_text:
                return "relevant"
            
            # בדיקה של חלקי השם
            name_parts = contact_name.split()
            if len(name_parts) >= 2:
                # אם לפחות שתי המילים הראשונות מופיעות
                if all(part.lower() in full_text for part in name_parts[:2]):
                    return "relevant"
        
        # בדיקה מיוחדת לאירועים כמו "דיון עבודה - איש קשר 5127"
        if re.search(r'(דיון עבודה|איש קשר \d+|מפגש \d+)', summary):
            return "irrelevant"  # אירועים גנריים לא רלוונטיים
        
        # אם זה אירוע WhatsApp אבל לא מכיל שמות מהרשימה
        return "irrelevant"

    def scan_and_cleanup_calendar(self):
        """סורק את היומן ומוחק אירועים לא רלוונטיים"""
        self.log("סורק את כל האירועים ביומן TimeBro...")
        
        try:
            # קבלת כל האירועים
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                maxResults=2500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            self.log(f"נמצאו {len(events)} אירועים ביומן")
            
            # סיווג האירועים
            relevant_events = []
            irrelevant_events = []
            non_whatsapp_events = []
            
            for event in events:
                relevance = self.is_event_relevant(event)
                
                if relevance == "relevant":
                    relevant_events.append(event)
                elif relevance == "irrelevant":
                    irrelevant_events.append(event)
                else:  # not_whatsapp
                    non_whatsapp_events.append(event)
            
            # דוח ראשוני
            print("\n📊 סיכום סריקת האירועים:")
            print("=" * 50)
            print(f"📅 סך הכל אירועים: {len(events)}")
            print(f"✅ אירועי WhatsApp רלוונטיים: {len(relevant_events)}")
            print(f"❌ אירועי WhatsApp לא רלוונטיים: {len(irrelevant_events)}")
            print(f"🔒 אירועים אחרים (לא נוגעים): {len(non_whatsapp_events)}")
            
            # הצגת דוגמאות לאירועים לא רלוונטיים
            if irrelevant_events:
                print("\n❌ אירועים לא רלוונטיים שימחקו:")
                for i, event in enumerate(irrelevant_events[:10], 1):
                    summary = event.get('summary', 'ללא כותרת')[:60]
                    print(f"   {i}. {summary}...")
                
                if len(irrelevant_events) > 10:
                    print(f"   ... ועוד {len(irrelevant_events) - 10} אירועים")
            
            # הצגת אירועים רלוונטיים שנשארים
            if relevant_events:
                print("\n✅ אירועים רלוונטיים שיישארו:")
                for i, event in enumerate(relevant_events[:10], 1):
                    summary = event.get('summary', 'ללא כותרת')[:60]
                    print(f"   {i}. {summary}...")
                
                if len(relevant_events) > 10:
                    print(f"   ... ועוד {len(relevant_events) - 10} אירועים")
            
            # מחיקת האירועים הלא רלוונטיים
            deleted_count = 0
            
            if irrelevant_events:
                self.log(f"מוחק {len(irrelevant_events)} אירועים לא רלוונטיים...")
                
                for event in irrelevant_events:
                    try:
                        self.service.events().delete(
                            calendarId=self.calendar_id,
                            eventId=event['id']
                        ).execute()
                        deleted_count += 1
                        summary = event.get('summary', '')[:50]
                        self.log(f"נמחק: {summary}...")
                    except Exception as e:
                        self.log(f"שגיאה במחיקת {event['id']}: {str(e)}", "ERROR")
            
            return {
                "total_events": len(events),
                "relevant_events": len(relevant_events),
                "irrelevant_events": len(irrelevant_events),
                "non_whatsapp_events": len(non_whatsapp_events),
                "deleted_count": deleted_count
            }
            
        except Exception as e:
            self.log(f"שגיאה בסריקת היומן: {str(e)}", "ERROR")
            return None

    def generate_cleanup_report(self, results):
        """יוצר דוח ניקוי"""
        if not results:
            return
            
        report = {
            "timestamp": datetime.now().isoformat(),
            "cleanup_results": results,
            "relevant_contacts_list": self.relevant_contact_names[:20],  # רק 20 הראשונים
            "total_relevant_contacts": len(self.relevant_contact_names)
        }
        
        # שמירת הדוח
        report_file = f"calendar_cleanup_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # הדפסת סיכום
        print("\n📊 דוח ניקוי יומן")
        print("=" * 50)
        print(f"🗑️ אירועים שנמחקו: {results['deleted_count']}")
        print(f"✅ אירועים רלוונטיים שנותרו: {results['relevant_events']}")
        print(f"🔒 אירועים אחרים (לא נגעו): {results['non_whatsapp_events']}")
        print(f"📋 סך הכל אנשי קשר ברשימה: {len(self.relevant_contact_names)}")
        print(f"📄 דוח נשמר ב: {report_file}")
        
        return report

    def run(self):
        """מריץ את תהליך הניקוי"""
        try:
            self.log("מתחיל תהליך ניקוי אירועים לא רלוונטיים")
            print("=" * 60)
            
            # שלב 1: התחברות ל-Google Calendar
            self.authenticate_google_calendar()
            
            # שלב 2: סריקה וניקוי
            results = self.scan_and_cleanup_calendar()
            
            if results:
                # שלב 3: יצירת דוח
                self.generate_cleanup_report(results)
                
                print("\n✅ תהליך ניקוי יומן הושלם בהצלחה!")
                print("📅 נותרו ביומן רק אירועים רלוונטיים מהרשימה שלך")
                print("🔒 אירועים שאינם של WhatsApp לא נפגעו")
            else:
                self.log("תהליך הניקוי נכשל", "ERROR")
            
        except Exception as e:
            self.log(f"שגיאה בתהליך הניקוי: {str(e)}", "ERROR")
            raise

if __name__ == "__main__":
    cleanup = CleanupIrrelevantEvents()
    cleanup.run()













