#!/usr/bin/env python3
"""
Delete Irrelevant Events and Update Relevant Titles
מחיקת אירועים לא רלוונטיים ועדכון כותרות אירועים רלוונטיים
"""

import json
import re
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os.path
from contacts_list import CONTACTS_CONFIG, get_contact_company

class DeleteAndUpdateEvents:
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
                # נוסיף גם גרסאות מנוקות של השמות
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

    def categorize_events(self):
        """מסווג את האירועים"""
        self.log("מסווג אירועים ביומן...")
        
        try:
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                maxResults=2500,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            whatsapp_relevant = []
            whatsapp_irrelevant = []
            call_events = []
            other_events = []
            
            for event in events:
                summary = event.get('summary', '')
                description = event.get('description', '')
                
                # אירועי שיחות טלפון - לא נוגעים!
                if summary.startswith('Call to ') or summary.startswith('Call from '):
                    call_events.append(event)
                    continue
                
                # אירועי WhatsApp/דיון
                is_whatsapp_or_discussion = (
                    any(keyword in summary.lower() for keyword in ['שיחה עם', 'דיון', 'מפגש', 'איש קשר', 'whatsapp']) or
                    any(keyword in description.lower() for keyword in ['whatsapp', 'wa.me', 'קישור לפתיחה', 'השיחה המלאה', 'דיון'])
                )
                
                if is_whatsapp_or_discussion:
                    # בדיקה אם רלוונטי
                    full_text = f"{summary} {description}".lower()
                    is_relevant = False
                    matched_contact = None
                    
                    for contact_name in self.relevant_contact_names:
                        if contact_name.lower() in full_text:
                            is_relevant = True
                            matched_contact = contact_name
                            break
                    
                    if is_relevant:
                        whatsapp_relevant.append({
                            'event': event,
                            'matched_contact': matched_contact
                        })
                    else:
                        whatsapp_irrelevant.append(event)
                else:
                    other_events.append(event)
            
            return {
                'whatsapp_relevant': whatsapp_relevant,
                'whatsapp_irrelevant': whatsapp_irrelevant,
                'call_events': call_events,
                'other_events': other_events
            }
            
        except Exception as e:
            self.log(f"שגיאה בסיווג: {str(e)}", "ERROR")
            return None

    def delete_irrelevant_events(self, irrelevant_events):
        """מוחק אירועים לא רלוונטיים"""
        self.log(f"מוחק {len(irrelevant_events)} אירועים לא רלוונטיים...")
        
        deleted_count = 0
        for event in irrelevant_events:
            try:
                self.service.events().delete(
                    calendarId=self.calendar_id,
                    eventId=event['id']
                ).execute()
                
                deleted_count += 1
                if deleted_count % 20 == 0:
                    self.log(f"נמחקו {deleted_count} אירועים...")
                    
            except Exception as e:
                self.log(f"שגיאה במחיקת {event['id']}: {str(e)}", "ERROR")
        
        self.log(f"נמחקו {deleted_count} אירועים לא רלוונטיים", "SUCCESS")
        return deleted_count

    def extract_topic_from_content(self, description):
        """מחלץ נושא מתוכן השיחה"""
        if not description:
            return "דיון כללי"
        
        content_lower = description.lower()
        
        # חיפוש מילות מפתח
        if any(word in content_lower for word in ['פרויקט', 'עבודה', 'משימה', 'טכני', 'פיתוח']):
            return "עבודה טכנית"
        elif any(word in content_lower for word in ['פגישה', 'זמן', 'תזמון', 'תאריך']):
            return "תיאום פגישה"
        elif any(word in content_lower for word in ['בעיה', 'תקלה', 'לא עובד', 'שגיאה']):
            return "פתרון בעיות"
        elif any(word in content_lower for word in ['תודה', 'אחלה', 'מעולה', 'כל הכבוד']):
            return "מעקב ותודות"
        elif any(word in content_lower for word in ['powerlink', 'טמפלט', 'עדכון']):
            return "עדכון טמפלט"
        elif any(word in content_lower for word in ['אוטומציה', 'מערכת', 'הגדרה']):
            return "הגדרת מערכת"
        else:
            return "דיון כללי"

    def update_relevant_event_titles(self, relevant_events):
        """עדכון כותרות האירועים הרלוונטיים"""
        self.log(f"מעדכן כותרות של {len(relevant_events)} אירועים רלוונטיים...")
        
        updated_count = 0
        
        for item in relevant_events:
            try:
                event = item['event']
                matched_contact = item['matched_contact']
                
                # מציאת החברה והצבע
                company, color = get_contact_company(matched_contact)
                
                # חילוץ נושא מהתיאור
                description = event.get('description', '')
                topic = self.extract_topic_from_content(description)
                
                # יצירת כותרת חדשה
                date_str = event.get('start', {}).get('dateTime', '')[:10]  # YYYY-MM-DD
                if date_str:
                    formatted_date = datetime.strptime(date_str, '%Y-%m-%d').strftime('%d/%m')
                else:
                    formatted_date = "תאריך לא ידוע"
                
                new_title = f"{matched_contact} | {company} - {topic} ({formatted_date})"
                
                # עדכון האירוע
                event['summary'] = new_title
                if color != "0":
                    event['colorId'] = color
                
                updated_event = self.service.events().update(
                    calendarId=self.calendar_id,
                    eventId=event['id'],
                    body=event
                ).execute()
                
                updated_count += 1
                self.log(f"עודכן: {new_title}")
                
            except Exception as e:
                self.log(f"שגיאה בעדכון אירוע: {str(e)}", "ERROR")
        
        self.log(f"עודכנו {updated_count} כותרות אירועים", "SUCCESS")
        return updated_count

    def generate_final_report(self, deleted_count, updated_count, categorization):
        """יוצר דוח סיכום"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "action_summary": {
                "deleted_irrelevant_events": deleted_count,
                "updated_relevant_titles": updated_count,
                "preserved_call_events": len(categorization['call_events']),
                "preserved_other_events": len(categorization['other_events'])
            },
            "relevant_contacts_with_events": [
                {
                    "contact": item['matched_contact'],
                    "company": get_contact_company(item['matched_contact'])[0],
                    "event_title": item['event'].get('summary', ''),
                    "date": item['event'].get('start', {}).get('dateTime', '')[:10]
                }
                for item in categorization['whatsapp_relevant']
            ]
        }
        
        report_file = f"calendar_cleanup_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("\n📊 דוח סיכום פעולות יומן")
        print("=" * 60)
        print(f"🗑️ אירועים לא רלוונטיים שנמחקו: {deleted_count}")
        print(f"✏️ כותרות אירועים שעודכנו: {updated_count}")
        print(f"📞 אירועי שיחות שנשמרו (לא נגעו): {len(categorization['call_events'])}")
        print(f"🔒 אירועים אחרים שנשמרו: {len(categorization['other_events'])}")
        print(f"📄 דוח נשמר ב: {report_file}")
        
        if categorization['whatsapp_relevant']:
            print("\n✅ אירועים רלוונטיים עם כותרות מעודכנות:")
            for i, item in enumerate(categorization['whatsapp_relevant'][:10], 1):
                contact = item['matched_contact']
                company = get_contact_company(contact)[0]
                event_date = item['event'].get('start', {}).get('dateTime', '')[:10]
                print(f"   {i}. [{event_date}] {contact} | {company}")
            
            if len(categorization['whatsapp_relevant']) > 10:
                print(f"   ... ועוד {len(categorization['whatsapp_relevant']) - 10} אירועים")
        
        return report

    def run(self):
        """מריץ את כל התהליך"""
        try:
            self.log("מתחיל מחיקה ועדכון אירועי יומן")
            print("=" * 60)
            
            # התחברות
            self.authenticate_google_calendar()
            
            # סיווג אירועים
            categorization = self.categorize_events()
            if not categorization:
                return
            
            # מחיקת אירועים לא רלוונטיים
            deleted_count = self.delete_irrelevant_events(categorization['whatsapp_irrelevant'])
            
            # עדכון כותרות אירועים רלוונטיים
            updated_count = self.update_relevant_event_titles(categorization['whatsapp_relevant'])
            
            # דוח סיכום
            self.generate_final_report(deleted_count, updated_count, categorization)
            
            print("\n✅ תהליך ניקוי ועדכון יומן הושלם בהצלחה!")
            print("📅 היומן עכשיו מכיל רק אירועים רלוונטיים עם כותרות מעודכנות")
            print("📞 כל אירועי השיחות שלך נשמרו בלי לגעת בהם")
            
        except Exception as e:
            self.log(f"שגיאה: {str(e)}", "ERROR")
            raise

if __name__ == "__main__":
    processor = DeleteAndUpdateEvents()
    processor.run()













