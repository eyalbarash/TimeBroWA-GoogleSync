#!/usr/bin/env python3
"""
Targeted Calendar Sync - רק אנשי הקשר הרלוונטיים
סינכרון יומן ממוקד לאנשי הקשר שצוינו בקובץ contacts_list.py
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta
from collections import defaultdict
from timebro_calendar import TimeBroCalendar
from contacts_list import CONTACTS_CONFIG

class TargetedCalendarSync:
    def __init__(self):
        self.db_path = "whatsapp_chats.db"
        self.calendar = TimeBroCalendar()
        
        # בניית מיפוי מספרי טלפון לאנשי קשר ידועים
        self.phone_mappings = {
            "972546687813": {"name": "מייק ביקוב", "company": "LBS", "color": "1"},
            # נוסיף עוד כשנמצא אותם בבסיס הנתונים
        }
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "🔍" if level == "ANALYZE" else "ℹ️"
        print(f"[{timestamp}] {emoji} {message}")
        
    def find_contact_phone_numbers(self):
        """מוצא מספרי טלפון של אנשי הקשר הרלוונטיים בבסיס הנתונים"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # קבל את כל השמות מהרשימה
            all_target_names = []
            for company, config in CONTACTS_CONFIG.items():
                all_target_names.extend(config["contacts"])
            
            found_mappings = {}
            
            # חפש בבסיס הנתונים לפי שמות
            for target_name in all_target_names:
                # ניקוי השם לחיפוש טוב יותר
                clean_name = target_name.split('/')[0].strip()
                clean_name = re.sub(r'\s*\(.*\)', '', clean_name).strip()
                
                # חיפוש גמיש בבסיס הנתונים
                cursor.execute('''
                    SELECT DISTINCT c.phone_number, c.name, 
                           COUNT(m.message_id) as message_count
                    FROM contacts c
                    JOIN chats ch ON c.contact_id = ch.contact_id
                    JOIN messages m ON ch.chat_id = m.chat_id
                    WHERE (LOWER(c.name) LIKE ? OR LOWER(c.name) LIKE ? OR LOWER(c.name) LIKE ?)
                    AND DATE(m.timestamp) BETWEEN '2025-08-01' AND '2025-09-24'
                    GROUP BY c.phone_number, c.name
                    HAVING message_count > 50
                    ORDER BY message_count DESC
                ''', (
                    f'%{clean_name.lower()}%',
                    f'%{clean_name.lower().replace(" ", "%")}%',
                    f'%{target_name.lower()}%'
                ))
                
                results = cursor.fetchall()
                
                for phone, db_name, msg_count in results:
                    # מצא את החברה והצבע
                    company, color = self.get_contact_info(target_name)
                    
                    found_mappings[phone] = {
                        "name": target_name,
                        "db_name": db_name,
                        "company": company,
                        "color": color,
                        "message_count": msg_count
                    }
                    
                    self.log(f"מצא: {target_name} → {phone} ({msg_count} הודעות)")
                    break  # קח רק את התוצאה הראשונה (הכי פעילה)
            
            conn.close()
            return found_mappings
            
        except sqlite3.Error as e:
            self.log(f"שגיאה בחיפוש אנשי קשר: {str(e)}", "ERROR")
            return {}
            
    def get_contact_info(self, contact_name):
        """מחזיר מידע על איש קשר מהרשימה"""
        for company, config in CONTACTS_CONFIG.items():
            if contact_name in config["contacts"]:
                return company, config["color"]
        return "לא מזוהה", "0"
        
    def get_contact_messages_for_period(self, phone_number, start_date="2025-08-01", end_date="2025-09-24"):
        """קבלת הודעות איש קשר לתקופה מסוימת"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # מצא את contact_id ו-chat_id
            cursor.execute('''
                SELECT c.contact_id, ch.chat_id 
                FROM contacts c
                JOIN chats ch ON c.contact_id = ch.contact_id
                WHERE c.phone_number = ?
            ''', (phone_number,))
            
            result = cursor.fetchone()
            if not result:
                return []
                
            contact_id, chat_id = result
            
            # קבל הודעות לתקופה
            cursor.execute('''
                SELECT 
                    timestamp,
                    sender_contact_id,
                    content,
                    message_type,
                    local_media_path
                FROM messages
                WHERE chat_id = ? 
                AND DATE(timestamp) BETWEEN ? AND ?
                ORDER BY timestamp
            ''', (chat_id, start_date, end_date))
            
            messages = cursor.fetchall()
            conn.close()
            
            # המר לפורמט מובנה
            structured_messages = []
            for msg in messages:
                timestamp_str, sender_id, content, msg_type, media_path = msg
                
                try:
                    if isinstance(timestamp_str, str):
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        timestamp = dt.timestamp()
                    else:
                        timestamp = float(timestamp_str)
                        dt = datetime.fromtimestamp(timestamp)
                except (ValueError, TypeError):
                    continue
                
                from_contact = sender_id == contact_id
                
                structured_messages.append({
                    'timestamp': timestamp,
                    'datetime': dt,
                    'sender_id': sender_id,
                    'content': content or f"[{msg_type}]",
                    'type': msg_type,
                    'media_path': media_path,
                    'from_contact': from_contact,
                    'to_contact': not from_contact
                })
                
            return structured_messages
            
        except sqlite3.Error as e:
            self.log(f"שגיאה בקבלת הודעות עבור {phone_number}: {str(e)}", "ERROR")
            return []
            
    def extract_conversation_topic(self, messages, contact_name):
        """חילוץ נושא השיחה"""
        if not messages:
            return f"שיחה עם {contact_name}"
            
        # ניתוח תוכן (אם יש)
        all_content = []
        for msg in messages[:30]:  # רק 30 הראשונות לניתוח
            if msg['content'] and msg['type'] == 'text' and len(msg['content']) > 5:
                content = str(msg['content'])
                if content and not any(skip in content.lower() for skip in ['[', 'deleted', 'null', 'none']):
                    all_content.append(content)
        
        # מילות מפתח מתקדמות
        key_phrases = {
            'פגישה': 4, 'meeting': 4, 'נפגש': 4, 'לפגוש': 4,
            'פרוייקט': 4, 'project': 4, 'לקוח': 4, 'client': 4,
            'CRM': 5, 'crm': 5, 'מערכת': 3, 'system': 3,
            'דחוף': 5, 'urgent': 5, 'חשוב': 4, 'important': 4,
            'PowerLink': 5, 'powerlink': 5, 'טמפלט': 4, 'template': 4,
            'באג': 4, 'bug': 4, 'שגיאה': 3, 'error': 3, 'בעיה': 3,
            'לידים': 5, 'leads': 5, 'קמפיין': 4, 'campaign': 4,
            'אוטומציה': 4, 'automation': 4, 'API': 4, 'api': 4,
            'הזמנה': 4, 'order': 4, 'מכירה': 4, 'sale': 4,
            'תמיכה': 3, 'support': 3, 'עזרה': 3, 'help': 3,
            'הדרכה': 4, 'training': 4, 'הסבר': 3, 'explanation': 3
        }
        
        if all_content:
            full_text = ' '.join(all_content).lower()
            
            phrase_scores = {}
            for phrase, score in key_phrases.items():
                if phrase.lower() in full_text:
                    phrase_scores[phrase] = score
                    
            if phrase_scores:
                top_phrase = max(phrase_scores.items(), key=lambda x: x[1])[0]
                
                if 'powerlink' in top_phrase.lower():
                    return f"עדכון PowerLink - {contact_name}"
                elif top_phrase.lower() in ['crm', 'מערכת']:
                    return f"עבודה על CRM - {contact_name}"
                elif top_phrase.lower() in ['לידים', 'leads']:
                    return f"ניהול לידים - {contact_name}"
                elif top_phrase.lower() in ['פגישה', 'meeting', 'נפגש', 'לפגוש']:
                    return f"תיאום פגישה - {contact_name}"
                elif top_phrase.lower() in ['דחוף', 'urgent']:
                    return f"נושא דחוף - {contact_name}"
                elif top_phrase.lower() in ['פרוייקט', 'project']:
                    return f"דיון פרוייקט - {contact_name}"
                elif top_phrase.lower() in ['הזמנה', 'order', 'מכירה', 'sale']:
                    return f"דיון מכירות - {contact_name}"
                elif top_phrase.lower() in ['תמיכה', 'support', 'עזרה', 'help']:
                    return f"מתן תמיכה - {contact_name}"
                elif top_phrase.lower() in ['הדרכה', 'training', 'הסבר']:
                    return f"הדרכה והסבר - {contact_name}"
                elif top_phrase.lower() in ['באג', 'bug', 'שגיאה', 'error', 'בעיה']:
                    return f"פתרון בעיות - {contact_name}"
        
        # נפילה בהתאם למספר הודעות ותאריך
        msg_count = len(messages)
        if msg_count > 100:
            return f"דיון מורחב - {contact_name}"
        elif msg_count > 30:
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
                
                # הפסקה של 4 שעות תתחיל מפגש חדש
                if time_gap > timedelta(hours=4):
                    if current_session:
                        sessions.append(current_session)
                        current_session = [msg]
                else:
                    current_session.append(msg)
                    
        if current_session:
            sessions.append(current_session)
            
        return sessions
        
    def format_full_conversation(self, messages):
        """יצירת תוכן השיחה המלא"""
        if not messages:
            return "אין הודעות זמינות"
            
        conversation_lines = []
        current_date = None
        
        for msg in messages:
            # הוספת תאריך אם השתנה
            msg_date = msg['datetime'].strftime('%d/%m/%Y')
            if current_date != msg_date:
                current_date = msg_date
                conversation_lines.append(f"\n📅 {msg_date}")
                conversation_lines.append("-" * 30)
            
            # פורמט ההודעה
            time_str = msg['datetime'].strftime('%H:%M')
            sender = "אתה" if not msg['from_contact'] else "הוא"
            
            if msg['type'] == 'text' and msg['content']:
                conversation_lines.append(f"[{time_str}] {sender}: {msg['content']}")
            else:
                conversation_lines.append(f"[{time_str}] {sender}: [{msg['type']}]")
        
        return "\n".join(conversation_lines)
        
    def create_enhanced_calendar_event(self, session, contact_info, session_num=1):
        """יצירת אירוע יומן מתקדם עם תוכן מלא"""
        if not session:
            return None
            
        contact_name = contact_info.get('name', 'איש קשר לא מזוהה')
        company = contact_info.get('company', 'לא מזוהה')
        color = contact_info.get('color', '0')
        phone = contact_info.get('phone', '')
        
        start_time = session[0]['datetime']
        end_time = session[-1]['datetime']
        
        # זמן מינימלי של 15 דקות
        if (end_time - start_time).total_seconds() < 900:
            end_time = start_time + timedelta(minutes=15)
            
        # כותרת לפי הפורמט הנדרש
        topic = self.extract_conversation_topic(session, contact_name)
        if session_num > 1:
            title = f"{topic} (המשך {session_num})"
        else:
            title = topic
            
        # תוכן השיחה המלא
        full_conversation = self.format_full_conversation(session)
        
        # סיכום השיחה
        duration = end_time - start_time
        summary_parts = [
            f"💬 {len(session)} הודעות",
            f"⏱️ משך: {duration}",
            f"📅 {start_time.strftime('%d/%m/%Y')}",
            f"⏰ {start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}"
        ]
        conversation_summary = " | ".join(summary_parts)
        
        # קישור WhatsApp
        whatsapp_link = f"whatsapp://send?phone={phone.replace('+', '')}" if phone else ""
        
        # תיאור מקיף
        description_parts = [
            f"💬 שיחת WhatsApp עם {contact_name}",
            f"🏢 חברה: {company}",
            f"📱 טלפון: {phone}",
            "",
            f"📊 סיכום השיחה:",
            conversation_summary,
            "",
            f"📱 פתח ב-WhatsApp: {whatsapp_link}" if whatsapp_link else "",
            "",
            "=" * 50,
            "📝 תוכן השיחה המלא:",
            "=" * 50,
            full_conversation,
            "",
            "🤖 נוצר אוטומטית על ידי מערכת ניתוח WhatsApp מתקדמת"
        ]
        
        description = "\n".join(filter(None, description_parts))
        
        # יצירת האירוע
        try:
            event = self.calendar.create_event(
                title=title,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                description=description,
                timezone="Asia/Jerusalem"
            )
            
            if event:
                # הגדרת צבע
                try:
                    self.calendar.service.events().patch(
                        calendarId=self.calendar.calendar_id,
                        eventId=event['id'],
                        body={'colorId': color}
                    ).execute()
                except:
                    pass
                    
                self.log(f"נוצר אירוע: {title} (צבע {color})", "SUCCESS")
                return {
                    'event': event,
                    'title': title,
                    'contact': contact_name,
                    'company': company,
                    'color': color,
                    'start_time': start_time,
                    'end_time': end_time,
                    'message_count': len(session),
                    'date': start_time.strftime('%Y-%m-%d')
                }
                
        except Exception as e:
            self.log(f"שגיאה ביצירת אירוע עבור {contact_name}: {str(e)}", "ERROR")
            
        return None
        
    def clear_existing_whatsapp_events(self, start_date="2025-08-01", end_date="2025-09-24"):
        """מחיקת אירועי WhatsApp קיימים בתקופה"""
        self.log(f"מוחק אירועי WhatsApp קיימים מ-{start_date} עד {end_date}...")
        
        try:
            time_min = f'{start_date}T00:00:00Z'
            time_max = f'{end_date}T23:59:59Z'
            
            events_result = self.calendar.service.events().list(
                calendarId=self.calendar.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            whatsapp_events = [e for e in events if any(keyword in e.get('summary', '').lower() 
                                                      for keyword in ['whatsapp', 'שיחה', 'דיון', 'מייק', 'עם', 'איש קשר'])]
            
            self.log(f"נמצאו {len(whatsapp_events)} אירועי WhatsApp למחיקה")
            
            deleted_count = 0
            for event in whatsapp_events:
                try:
                    self.calendar.service.events().delete(
                        calendarId=self.calendar.calendar_id,
                        eventId=event['id']
                    ).execute()
                    deleted_count += 1
                except Exception as e:
                    self.log(f"שגיאה במחיקת אירוע {event['id']}: {str(e)}", "ERROR")
                    
            self.log(f"נמחקו {deleted_count} אירועים קיימים", "SUCCESS")
            return deleted_count
            
        except Exception as e:
            self.log(f"שגיאה במחיקת אירועים: {str(e)}", "ERROR")
            return 0
            
    def sync_targeted_calendar(self):
        """סינכרון יומן ממוקד לאנשי הקשר הרלוונטיים בלבד"""
        self.log("מתחיל סינכרון יומן ממוקד לאנשי הקשר הרלוונטיים")
        
        # אימות יומן
        if not self.calendar.authenticate():
            self.log("אימות יומן נכשל", "ERROR")
            return []
            
        # מחיקת אירועים קיימים
        deleted_count = self.clear_existing_whatsapp_events()
        
        # מציאת מספרי טלפון של אנשי הקשר הרלוונטיים
        phone_mappings = self.find_contact_phone_numbers()
        
        # הוספת המיפויים הידועים
        phone_mappings.update(self.phone_mappings)
        
        self.log(f"נמצאו {len(phone_mappings)} אנשי קשר רלוונטיים")
        
        created_events = []
        
        # עיבוד כל איש קשר רלוונטי
        for i, (phone, contact_info) in enumerate(phone_mappings.items(), 1):
            contact_name = contact_info.get('name', 'איש קשר לא מזוהה')
            company = contact_info.get('company', 'לא מזוהה')
            
            self.log(f"[{i}/{len(phone_mappings)}] מעבד: {contact_name} מ-{company}")
            
            # קבלת הודעות לתקופה
            messages = self.get_contact_messages_for_period(phone)
            
            if not messages:
                self.log(f"לא נמצאו הודעות עבור {contact_name}")
                continue
                
            # זיהוי מפגשים
            sessions = self.identify_conversation_sessions(messages)
            self.log(f"זוהו {len(sessions)} מפגשים עבור {contact_name}")
            
            # יצירת אירועים לכל מפגש
            contact_info_with_phone = contact_info.copy()
            contact_info_with_phone['phone'] = phone
            
            for j, session in enumerate(sessions, 1):
                if len(session) >= 3:  # רק מפגשים עם לפחות 3 הודעות
                    event_data = self.create_enhanced_calendar_event(
                        session, contact_info_with_phone, j
                    )
                    if event_data:
                        created_events.append(event_data)
                        
        return created_events
        
    def generate_targeted_report(self, events):
        """יצירת דוח ממוקד"""
        self.log("\n" + "="*70)
        self.log("📊 דוח סינכרון יומן ממוקד - אנשי קשר רלוונטיים בלבד")
        self.log("="*70)
        
        if not events:
            self.log("לא נוצרו אירועים")
            return
            
        # סטטיסטיקות כלליות
        total_events = len(events)
        total_messages = sum(event['message_count'] for event in events)
        unique_contacts = len(set(event['contact'] for event in events))
        
        # פירוט לפי חודש
        august_events = [e for e in events if e['date'].startswith('2025-08')]
        september_events = [e for e in events if e['date'].startswith('2025-09')]
        
        # פירוט לפי חברה
        company_stats = defaultdict(lambda: {'events': 0, 'contacts': set(), 'messages': 0})
        for event in events:
            company = event['company']
            company_stats[company]['events'] += 1
            company_stats[company]['contacts'].add(event['contact'])
            company_stats[company]['messages'] += event['message_count']
        
        self.log(f"📈 סיכום כללי:")
        self.log(f"   📅 סך הכל אירועים: {total_events}")
        self.log(f"   📊 אוגוסט 2025: {len(august_events)} אירועים")
        self.log(f"   📊 ספטמבר 2025: {len(september_events)} אירועים")
        self.log(f"   👥 אנשי קשר ייחודיים: {unique_contacts}")
        self.log(f"   💬 סך הכל הודעות: {total_messages}")
        
        self.log(f"\n🏢 פירוט לפי חברות:")
        for company, stats in sorted(company_stats.items(), key=lambda x: x[1]['events'], reverse=True):
            if stats['events'] > 0:
                self.log(f"   🎯 {company}:")
                self.log(f"      📅 {stats['events']} אירועים")
                self.log(f"      👥 {len(stats['contacts'])} אנשי קשר")
                self.log(f"      💬 {stats['messages']} הודעות")
        
        # השיחות הגדולות ביותר
        self.log(f"\n🏆 השיחות הגדולות ביותר:")
        top_events = sorted(events, key=lambda x: x['message_count'], reverse=True)[:10]
        for i, event in enumerate(top_events, 1):
            duration = event['end_time'] - event['start_time']
            self.log(f"   {i}. {event['title']}")
            self.log(f"      👤 {event['contact']} ({event['company']})")
            self.log(f"      📅 {event['date']} | 💬 {event['message_count']} הודעות | ⏱️ {duration}")

def main():
    """הפעלת הסינכרון הממוקד"""
    print("🎯 סינכרון יומן ממוקד - אנשי קשר רלוונטיים בלבד")
    print("✨ יצירת אירועים עם תוכן מלא לאנשי הקשר מהרשימה")
    print("="*70)
    
    sync = TargetedCalendarSync()
    
    # ביצוע הסינכרון
    events = sync.sync_targeted_calendar()
    
    # יצירת דוח
    sync.generate_targeted_report(events)
    
    if events:
        print(f"\n🎉 הושלם בהצלחה! נוצרו {len(events)} אירועי יומן ממוקדים")
        print("📅 בדוק את TimeBro Calendar לראות את האירועים החדשים")
        print("🎨 כל חברה בצבע שונה לזיהוי מיידי")
        print("📝 כל אירוע כולל את תוכן השיחה המלא!")
    else:
        print("\n⚠️ לא נוצרו אירועים. בדוק את הלוגים למעלה")

if __name__ == "__main__":
    main()













