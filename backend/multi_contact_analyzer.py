#!/usr/bin/env python3
"""
Multi-Contact Conversation Analyzer
מערכת ניתוח שיחות מתקדמת לכל אנשי הקשר עם צבעים לפי חברות
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict
from timebro_calendar import TimeBroCalendar
from contacts_list import CONTACTS_CONFIG, get_contact_company, get_company_color

class MultiContactAnalyzer:
    def __init__(self):
        self.db_path = "whatsapp_chats.db"  # Database with all contacts
        self.calendar = TimeBroCalendar()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "🔍" if level == "ANALYZE" else "ℹ️"
        print(f"[{timestamp}] {emoji} {message}")
        
    def check_database_contacts(self):
        """בדיקה אילו אנשי קשר קיימים בבסיס הנתונים"""
        self.log("בודק אילו אנשי קשר קיימים בבסיס הנתונים...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all contacts from the database
            cursor.execute("SELECT DISTINCT contact_name FROM chats ORDER BY contact_name")
            db_contacts = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            # Match with our contact list
            matched_contacts = []
            unmatched_contacts = []
            
            # Get all contacts from config
            config_contacts = []
            for company, config in CONTACTS_CONFIG.items():
                for contact in config["contacts"]:
                    config_contacts.append(contact)
            
            self.log(f"נמצאו {len(db_contacts)} אנשי קשר בבסיס הנתונים")
            self.log(f"יש {len(config_contacts)} אנשי קשר ברשימת התצורה")
            
            # Check matches
            for config_contact in config_contacts:
                found = False
                for db_contact in db_contacts:
                    # Check various matching patterns
                    if (config_contact.lower() in db_contact.lower() or 
                        db_contact.lower() in config_contact.lower() or
                        self.fuzzy_match(config_contact, db_contact)):
                        
                        company, color = get_contact_company(config_contact)
                        matched_contacts.append({
                            'config_name': config_contact,
                            'db_name': db_contact,
                            'company': company,
                            'color': color
                        })
                        found = True
                        break
                        
                if not found:
                    unmatched_contacts.append(config_contact)
            
            return matched_contacts, unmatched_contacts, db_contacts
            
        except sqlite3.Error as e:
            self.log(f"שגיאה בבדיקת בסיס הנתונים: {str(e)}", "ERROR")
            return [], [], []
            
    def fuzzy_match(self, name1, name2):
        """התאמה רכה בין שמות"""
        # Remove common words and compare core names
        ignore_words = ['(עבודה)', '/', '-', 'מנהלת', 'משרד', 'מנהל', 'ד״ר', 'טיפול', 'טכני', 'ב']
        
        clean1 = name1
        clean2 = name2
        
        for word in ignore_words:
            clean1 = clean1.replace(word, ' ')
            clean2 = clean2.replace(word, ' ')
            
        # Split to words and check overlap
        words1 = set(clean1.split())
        words2 = set(clean2.split())
        
        # If there's significant word overlap
        if len(words1 & words2) >= min(len(words1), len(words2)) * 0.5:
            return True
            
        return False
        
    def get_contact_conversations(self, contact_db_name):
        """מחזיר את כל השיחות של איש קשר מסוים"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    timestamp,
                    sender,
                    message_text,
                    message_type,
                    media_path
                FROM messages 
                WHERE chat_id = (
                    SELECT chat_id FROM chats WHERE contact_name = ?
                )
                ORDER BY timestamp
            """, (contact_db_name,))
            
            messages = cursor.fetchall()
            conn.close()
            
            # Convert to structured format
            structured_messages = []
            for msg in messages:
                timestamp, sender, text, msg_type, media_path = msg
                
                # Determine if message is from contact or to contact
                from_contact = sender != "972549990001"  # Your number
                
                structured_messages.append({
                    'timestamp': timestamp,
                    'datetime': datetime.fromtimestamp(timestamp),
                    'sender': sender,
                    'content': text or f"[{msg_type}]",
                    'type': msg_type,
                    'media_path': media_path,
                    'from_contact': from_contact,
                    'to_contact': not from_contact
                })
                
            return structured_messages
            
        except sqlite3.Error as e:
            self.log(f"שגיאה בקבלת שיחות עבור {contact_db_name}: {str(e)}", "ERROR")
            return []
            
    def extract_conversation_essence(self, messages, contact_name):
        """חילוץ תמצית השיחה לפי תוכן"""
        if not messages:
            return f"שיחה עם {contact_name}"
            
        # Combine text content
        all_content = []
        for msg in messages:
            if msg['type'] == 'text' and len(msg['content']) > 5:
                content = msg['content']
                if not any(skip in content for skip in ['[', 'deleted', 'https://']):
                    all_content.append(content)
        
        if not all_content:
            return f"שיחה עם {contact_name}"
            
        full_text = ' '.join(all_content[:10])  # First 10 messages for analysis
        
        # Company-specific keywords
        company, _ = get_contact_company(contact_name)
        
        # Enhanced keyword detection
        key_phrases = {
            # Business keywords
            'פגישה': 3, 'meeting': 3, 'נפגש': 3, 'להיפגש': 3,
            'פרוייקט': 3, 'project': 3, 'עבודה': 2, 'work': 2,
            'לקוח': 3, 'client': 3, 'customer': 3,
            'הצעה': 3, 'proposal': 3, 'מחיר': 3, 'price': 3,
            'הסכם': 3, 'contract': 3, 'חוזה': 3,
            
            # Technical keywords
            'CRM': 4, 'crm': 4, 'מערכת': 2, 'system': 2,
            'API': 3, 'api': 3, 'טכני': 2, 'technical': 2,
            'באג': 3, 'bug': 3, 'שגיאה': 2, 'error': 2,
            'תיקון': 2, 'fix': 2, 'בעיה': 2, 'problem': 2,
            
            # Marketing keywords
            'לידים': 4, 'leads': 4, 'lead': 3,
            'קמפיין': 3, 'campaign': 3, 'פרסום': 2, 'marketing': 2,
            'אוטומציה': 3, 'automation': 3, 'אוטומציות': 3,
            
            # Urgency keywords
            'דחוף': 4, 'urgent': 4, 'מיידי': 4, 'immediate': 4,
            'חשוב': 3, 'important': 3, 'בזריזות': 3,
            
            # Company-specific
            'PowerLink': 4, 'powerlink': 4, 'פאוורלינק': 4,
            'Salesflow': 3, 'salesflow': 3,
            'fundit': 3, 'Fundit': 3,
            'trichome': 3, 'Trichome': 3,
            'כפרי': 2, 'kafri': 2
        }
        
        # Score phrases
        phrase_scores = {}
        for phrase, score in key_phrases.items():
            if phrase.lower() in full_text.lower():
                phrase_scores[phrase] = score
                
        # Create smart title
        if phrase_scores:
            top_phrase = max(phrase_scores.items(), key=lambda x: x[1])[0]
            
            # Create contextual titles
            if top_phrase.lower() in ['פגישה', 'meeting', 'נפגש', 'להיפגש']:
                return f"פגישה עם {contact_name}"
            elif top_phrase.lower() in ['crm', 'מערכת', 'system']:
                return f"דיון מערכת CRM - {contact_name}"
            elif top_phrase.lower() in ['לידים', 'leads', 'lead']:
                return f"ניהול לידים - {contact_name}"
            elif top_phrase.lower() in ['פרוייקט', 'project', 'עבודה']:
                return f"דיון פרוייקט - {contact_name}"
            elif top_phrase.lower() in ['באג', 'bug', 'שגיאה', 'בעיה']:
                return f"פתרון בעיות - {contact_name}"
            elif top_phrase.lower() in ['דחוף', 'urgent', 'מיידי']:
                return f"נושא דחוף - {contact_name}"
            elif top_phrase.lower() in ['הצעה', 'proposal', 'מחיר']:
                return f"הצעת מחיר - {contact_name}"
            elif 'powerlink' in top_phrase.lower():
                return f"עדכון PowerLink - {contact_name}"
            elif 'automation' in top_phrase.lower() or 'אוטומציה' in top_phrase.lower():
                return f"אוטומציות - {contact_name}"
        
        # Fallback based on message count and company
        if len(messages) > 50:
            return f"דיון מורחב - {contact_name}"
        elif len(messages) > 20:
            return f"דיון עבודה - {contact_name}"
        else:
            return f"שיחה עם {contact_name}"
            
    def identify_conversation_sessions(self, messages):
        """זיהוי מפגשי שיחה לפי הפסקות זמן"""
        if not messages:
            return []
            
        sessions = []
        current_session = []
        
        sorted_messages = sorted(messages, key=lambda x: x['timestamp'])
        
        for msg in sorted_messages:
            if not current_session:
                current_session = [msg]
            else:
                last_time = current_session[-1]['datetime']
                current_time = msg['datetime']
                time_gap = current_time - last_time
                
                # If gap > 4 hours, start new session (longer gap for multi-contact)
                if time_gap > timedelta(hours=4):
                    if current_session:
                        sessions.append(current_session)
                        current_session = [msg]
                else:
                    current_session.append(msg)
                    
        if current_session:
            sessions.append(current_session)
            
        return sessions
        
    def create_whatsapp_link(self, contact_phone=None):
        """יצירת קישור WhatsApp"""
        if contact_phone:
            clean_phone = contact_phone.replace('+', '').replace('-', '').replace(' ', '')
            return f"whatsapp://send?phone={clean_phone}"
        return "whatsapp://send"
        
    def format_full_conversation(self, messages, contact_name):
        """עיצוב השיחה המלאה"""
        conversation_lines = []
        
        for msg in messages:
            time_str = msg['datetime'].strftime("%H:%M")
            sender = contact_name if msg['from_contact'] else "אייל ברש"
            
            # Format content
            if msg['type'] == 'text':
                content = msg['content']
            elif msg['media_path']:
                if any(ext in msg['media_path'] for ext in ['.jpg', '.png', '.jpeg']):
                    content = f"📷 תמונה: {msg['media_path']}"
                elif any(ext in msg['media_path'] for ext in ['.mp3', '.opus', '.wav']):
                    content = f"🎵 הודעה קולית"
                elif '.pdf' in msg['media_path']:
                    content = f"📄 PDF: {msg['media_path']}"
                else:
                    content = f"📎 קובץ: {msg['media_path']}"
            else:
                content = f"[{msg['type']}]"
                
            conversation_lines.append(f"[{time_str}] {sender}: {content}")
            
        return '\n'.join(conversation_lines)
        
    def create_calendar_event(self, session, contact_name, company, color, session_num=1):
        """יצירת אירוע יומן עם צבע לפי חברה"""
        if not session:
            return None
            
        start_time = session[0]['datetime']
        end_time = session[-1]['datetime']
        
        # Minimum 15 minutes
        if (end_time - start_time).total_seconds() < 900:
            end_time = start_time + timedelta(minutes=15)
            
        # Create title
        essence = self.extract_conversation_essence(session, contact_name)
        if session_num > 1:
            title = f"{essence} (מפגש {session_num})"
        else:
            title = essence
            
        # WhatsApp link
        whatsapp_link = self.create_whatsapp_link()
        
        # Full conversation
        full_conversation = self.format_full_conversation(session, contact_name)
        
        # Description
        description_parts = [
            f"💬 שיחת WhatsApp עם {contact_name}",
            f"🏢 חברה: {company}",
            f"📅 תאריך: {start_time.strftime('%Y-%m-%d')}",
            f"⏰ שעות: {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}",
            f"💬 {len(session)} הודעות",
            f"⏱️ משך: {end_time - start_time}",
            "",
            f"📱 פתח ב-WhatsApp: {whatsapp_link}",
            "",
            "📝 תוכן השיחה המלא:",
            "=" * 50,
            full_conversation,
            "",
            "=" * 50,
            "",
            "🤖 נוצר אוטומטית על ידי מערכת ניתוח WhatsApp מתקדמת"
        ]
        
        description = "\n".join(description_parts)
        
        # Create event with color
        try:
            event = self.calendar.create_event(
                title=title,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                description=description,
                timezone="Asia/Jerusalem"
            )
            
            if event:
                # Set color if supported
                try:
                    self.calendar.service.events().patch(
                        calendarId=self.calendar.calendar_id,
                        eventId=event['id'],
                        body={'colorId': color}
                    ).execute()
                    self.log(f"צבע {color} הוגדר לאירוע {title}", "SUCCESS")
                except:
                    pass  # Color setting is optional
                    
                self.log(f"נוצר אירוע: {title} (צבע {color})", "SUCCESS")
                return {
                    'event': event,
                    'title': title,
                    'contact': contact_name,
                    'company': company,
                    'color': color,
                    'start_time': start_time,
                    'end_time': end_time,
                    'message_count': len(session)
                }
                
        except Exception as e:
            self.log(f"שגיאה ביצירת אירוע עבור {contact_name}: {str(e)}", "ERROR")
            
        return None
        
    def analyze_all_contacts(self):
        """ניתוח כל אנשי הקשר ויצירת אירועי יומן"""
        self.log("מתחיל ניתוח מקיף של כל אנשי הקשר...")
        
        # Authenticate calendar
        if not self.calendar.authenticate():
            self.log("אימות יומן נכשל", "ERROR")
            return []
            
        # Check which contacts exist in database
        matched_contacts, unmatched, all_db_contacts = self.check_database_contacts()
        
        self.log(f"נמצאו {len(matched_contacts)} אנשי קשר תואמים")
        if unmatched:
            self.log(f"לא נמצאו בבסיס הנתונים: {len(unmatched)} אנשי קשר")
            
        created_events = []
        
        # Process each matched contact
        for contact_info in matched_contacts:
            contact_name = contact_info['config_name']
            db_name = contact_info['db_name']
            company = contact_info['company']
            color = contact_info['color']
            
            self.log(f"\n🔍 מעבד: {contact_name} ({company})")
            
            # Get conversations
            messages = self.get_contact_conversations(db_name)
            
            if not messages:
                self.log(f"לא נמצאו הודעות עבור {contact_name}")
                continue
                
            self.log(f"נמצאו {len(messages)} הודעות")
            
            # Identify sessions
            sessions = self.identify_conversation_sessions(messages)
            self.log(f"זוהו {len(sessions)} מפגשי שיחה")
            
            # Create events for each session
            for i, session in enumerate(sessions, 1):
                event_data = self.create_calendar_event(
                    session, contact_name, company, color, i
                )
                if event_data:
                    created_events.append(event_data)
                    
        return created_events
        
    def generate_summary_report(self, events):
        """יצירת דוח סיכום מקיף"""
        self.log("\n" + "="*70)
        self.log("📊 דוח סיכום ניתוח מקיף - כל אנשי הקשר")
        self.log("="*70)
        
        if not events:
            self.log("לא נוצרו אירועים")
            return
            
        # Statistics by company
        company_stats = defaultdict(lambda: {'events': 0, 'contacts': set(), 'messages': 0})
        
        for event in events:
            company = event['company']
            company_stats[company]['events'] += 1
            company_stats[company]['contacts'].add(event['contact'])
            company_stats[company]['messages'] += event['message_count']
            
        total_events = len(events)
        total_messages = sum(event['message_count'] for event in events)
        total_contacts = len(set(event['contact'] for event in events))
        
        self.log(f"📈 סיכום כללי:")
        self.log(f"   📅 סך הכל אירועים: {total_events}")
        self.log(f"   👥 אנשי קשר שעובדו: {total_contacts}")
        self.log(f"   💬 סך הכל הודעות: {total_messages}")
        
        self.log(f"\n🏢 פירוט לפי חברות:")
        for company, stats in sorted(company_stats.items()):
            color_name = {
                "1": "לבנדר", "2": "מרווה", "3": "ענב", "4": "פלמינגו",
                "5": "בננה", "6": "טנג'רין", "7": "טווס", "8": "קקאו",
                "9": "אוכמניות", "10": "בזיליקום", "11": "עגבנייה", "0": "ברירת מחדל"
            }.get(get_company_color(company), "לא מזוהה")
            
            self.log(f"   🎨 {company} (צבע: {color_name})")
            self.log(f"      📅 {stats['events']} אירועים")
            self.log(f"      👥 {len(stats['contacts'])} אנשי קשר")
            self.log(f"      💬 {stats['messages']} הודעות")
            
        # Top conversations
        self.log(f"\n🏆 השיחות הגדולות ביותר:")
        top_events = sorted(events, key=lambda x: x['message_count'], reverse=True)[:5]
        for i, event in enumerate(top_events, 1):
            duration = event['end_time'] - event['start_time']
            self.log(f"   {i}. {event['title']}")
            self.log(f"      👤 {event['contact']} ({event['company']})")
            self.log(f"      💬 {event['message_count']} הודעות, {duration}")

def main():
    """הפעלת המערכת המלאה"""
    print("🧠 מערכת ניתוח שיחות מתקדמת - כל אנשי הקשר")
    print("✨ יצירת אירועי יומן עם צבעים לפי חברות")
    print("="*70)
    
    analyzer = MultiContactAnalyzer()
    
    # Run full analysis
    events = analyzer.analyze_all_contacts()
    
    # Generate report
    analyzer.generate_summary_report(events)
    
    if events:
        print(f"\n🎉 הושלם בהצלחה! נוצרו {len(events)} אירועי יומן")
        print("📅 בדוק את TimeBro Calendar - כל האירועים עם צבעים לפי חברות!")
        print("💬 כל אירוע מכיל את השיחה המלאה עם קישורי WhatsApp")
    else:
        print("\n⚠️ לא נוצרו אירועים. בדוק את הלוגים למעלה")

if __name__ == "__main__":
    main()













