#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הוספת נתונים חיים מהמערכת הפעילה + יצירת בקשה כוללת לClaude
"""

import sqlite3
import json
import csv
from datetime import datetime, timedelta
import os

class LiveDataEnhancer:
    def __init__(self):
        self.live_db = 'whatsapp_messages_webjs.db'
        self.contacts_db = 'whatsapp_contacts.db'
        
        # רשימת האנשים והקבוצות שראינו במערכת החיה
        self.live_contacts_seen = [
            'שירלי קנטור', 'ג\'זייה סבטאן', 'הקקטוסנית זהבית אתגר',
            'מוניפיה עוזרת בית', 'אליס מרקו', 'Ann', 'הדר לנדוליני', 
            'Gaby', 'משפ\' ברש 🐶', 'קהילת בית לחם', 'אקרמן בריכה ועוד',
            'חדשות מהרגע 506', 'הודעות קהילת בית לחם', 'קהילת האימייל מרקטינג',
            'Netflix', 'זהר גרומן', 'איילת יונג', 'פזית אנקר'
        ]
        
        # מילות מפתח מורחבות לאירועי יומן
        self.calendar_keywords = [
            # זמנים
            'מחר', 'היום', 'אתמול', 'בשבוע', 'בחודש', 'בשנה',
            'יום ראשון', 'יום שני', 'יום שלישי', 'יום רביעי', 'יום חמישי', 'יום שישי', 'שבת',
            'בוקר', 'צהריים', 'אחר הצהריים', 'ערב', 'לילה',
            'בשעה', 'ב-', 'עד', 'מ-', 'לשעה',
            
            # פגישות ואירועים
            'פגישה', 'מפגש', 'נפגש', 'ניפגש', 'להיפגש',
            'כנס', 'סדנה', 'הרצאה', 'אירוע', 'מסיבה',
            'ישיבה', 'דיון', 'התייעצות', 'הצגה',
            
            # משימות ודדליינים
            'דדליין', 'תאריך יעד', 'עד ה', 'לסיים עד',
            'משימה', 'למסור', 'לשלוח', 'להגיש',
            'תזכיר', 'תזכורת', 'לזכור', 'להזכיר',
            
            # פעולות עם זמן
            'לקבוע', 'לתאם', 'לסגור', 'להחליט',
            'לבדוק', 'לעקוב', 'למלא', 'לחתום',
            
            # ביטויי זמן
            'השבוע', 'החודש', 'השנה', 'הקרוב',
            'הבא', 'הזה', 'הנוכחי', 'האחרון'
        ]

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "📊" if level == "INFO" else "✅" if level == "SUCCESS" else "❌"
        print(f"[{timestamp}] {emoji} {message}")

    def get_live_messages_september(self):
        """חילוץ הודעות חיות מספטמבר"""
        self.log("חילוץ הודעות חיות מספטמבר...")
        
        try:
            conn = sqlite3.connect(self.live_db)
            cursor = conn.cursor()
            
            # הודעות מספטמבר עד היום
            cursor.execute("""
                SELECT id, chat_id, contact_name, contact_number, 
                       message_body, message_type, timestamp, is_from_me,
                       has_media, media_type, created_at
                FROM messages
                WHERE datetime(timestamp, 'unixepoch') >= '2025-09-01'
                ORDER BY timestamp ASC
            """)
            
            messages = cursor.fetchall()
            conn.close()
            
            self.log(f"נמצאו {len(messages)} הודעות חיות מספטמבר")
            
            processed_messages = []
            for msg in messages:
                processed = self.process_live_message(msg)
                if processed:
                    processed_messages.append(processed)
            
            return processed_messages
            
        except Exception as e:
            self.log(f"שגיאה בחילוץ הודעות חיות: {e}", "ERROR")
            return []

    def process_live_message(self, msg_data):
        """עיבוד הודעה חיה"""
        try:
            content = (msg_data[4] or '').strip()
            sender = msg_data[2] or 'לא ידוע'
            
            # דילוג על הודעות ריקות
            if not content or len(content) < 3:
                return None
            
            # זיהוי פוטנציאל יומן
            has_calendar_potential = any(keyword in content for keyword in self.calendar_keywords)
            
            # זמן
            try:
                dt = datetime.fromtimestamp(msg_data[6])
            except:
                dt = datetime.now()
            
            return {
                'id': msg_data[0],
                'sender': sender,
                'content': content,
                'datetime': dt.isoformat(),
                'date': dt.strftime('%Y-%m-%d'),
                'time': dt.strftime('%H:%M:%S'),
                'has_calendar_potential': has_calendar_potential,
                'is_from_me': bool(msg_data[7]),
                'has_media': bool(msg_data[8]),
                'is_live_contact': sender in self.live_contacts_seen,
                'source': 'live_september'
            }
            
        except Exception as e:
            self.log(f"שגיאה בעיבוד הודעה חיה: {e}", "ERROR")
            return None

    def enhance_existing_extraction(self):
        """הוספת נתונים חיים לחילוץ הקיים"""
        self.log("משפר את החילוץ הקיים עם נתונים חיים...")
        
        # טעינת הקובץ הקיים
        existing_files = [f for f in os.listdir('.') if f.startswith('claude_calendar_extraction_') and f.endswith('.json')]
        
        if not existing_files:
            self.log("לא נמצא קובץ חילוץ קיים", "ERROR")
            return None
        
        latest_file = sorted(existing_files)[-1]
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except Exception as e:
            self.log(f"שגיאה בקריאת קובץ קיים: {e}", "ERROR")
            return None
        
        # הוספת נתונים חיים
        live_messages = self.get_live_messages_september()
        
        # עדכון הנתונים
        enhanced_data = existing_data.copy()
        enhanced_data['live_september_data'] = {
            'total_messages': len(live_messages),
            'calendar_candidates': [msg for msg in live_messages if msg['has_calendar_potential']],
            'live_contacts': [msg for msg in live_messages if msg['is_live_contact']],
            'all_messages': live_messages
        }
        
        # עדכון מטאדטה
        enhanced_data['metadata']['live_data_added'] = True
        enhanced_data['metadata']['live_messages_count'] = len(live_messages)
        enhanced_data['metadata']['live_calendar_candidates'] = len([msg for msg in live_messages if msg['has_calendar_potential']])
        enhanced_data['metadata']['enhancement_time'] = datetime.now().isoformat()
        
        return enhanced_data, live_messages

    def create_final_claude_request(self):
        """יצירת בקשה סופית לClaude עם כל הנתונים"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # שיפור הנתונים הקיימים
        enhanced_data, live_messages = self.enhance_existing_extraction()
        
        if not enhanced_data:
            self.log("לא ניתן ליצור בקשה סופית", "ERROR")
            return None
        
        # שמירת הקובץ המשופר
        enhanced_file = f"final_calendar_extraction_{timestamp}.json"
        with open(enhanced_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
        
        # יצירת פרומפט סופי מותאם
        total_messages = enhanced_data['metadata'].get('total_messages', 0) + len(live_messages)
        calendar_candidates = enhanced_data['metadata'].get('calendar_candidates_found', 0) + enhanced_data['metadata'].get('live_calendar_candidates', 0)
        
        final_prompt = f"""🎯 **בקשה סופית לחילוץ אירועי יומן מכל השיחות**

**תקציר הנתונים:**
- תקופה: אוגוסט - ספטמבר 2025 (עד היום)
- סה"כ הודעות: {total_messages:,}
- מועמדי אירועי יומן: {calendar_candidates:,}
- כולל נתונים חיים מהמערכת הפעילה

**אנשי קשר עדיפות (תן להם דגש מיוחד):**
• מייק ביקוב - השותף העסקי העיקרי
• צחי כפרי - חברת כפרי דרייב  
• לי עמר/עילי ברש/משה עמר - צוות משה עמר
• סשה דיבקה - עצמאיים
• שתלתם/נטע שלי - עצמאיים
• fital/טל מועלם - עצמאיים

**קבוצות וערוצים פעילים:**
• קהילת בית לחם - קהילה מקומית
• קהילת האימייל מרקטינג - עסקי
• משפ' ברש 🐶 - משפחה
• חדשות מהרגע 506 - חדשות

**פורמט פלט נדרש:**
```json
{{
  "calendar_events": [
    {{
      "title": "כותרת האירוע",
      "date": "YYYY-MM-DD", 
      "time": "HH:MM",
      "end_time": "HH:MM",
      "duration_minutes": 60,
      "description": "תיאור מפורט של האירוע/משימה",
      "location": "מיקום (אם נמצא)",
      "participants": ["רשימת משתתפים"],
      "priority": "high/medium/low",
      "category": "meeting/task/deadline/follow_up/reminder/event",
      "contact_source": "מאיזה איש קשר/קבוצה חולץ",
      "extracted_from": "ציטוט ההודעה המקורית",
      "confidence": "high/medium/low",
      "status": "completed/pending/cancelled",
      "month": "august/september"
    }}
  ],
  "summary": {{
    "total_events_found": 0,
    "by_month": {{"august": 0, "september": 0}},
    "by_priority": {{"high": 0, "medium": 0, "low": 0}},
    "by_category": {{}},
    "by_contact": {{}}
  }}
}}
```

**הוראות מיוחדות:**
1. **חפש בעמק** - כל אזכור של זמן, תאריך, מועד, פגישה
2. **הסק מההקשר** - אם התאריך לא מפורש, נסה להבין מתוך ההקשר
3. **כלול הכל** - גם אירועים שכבר עברו (חשוב לארכיון)
4. **סמן סטטוס** - אם אתה יכול להסיק אם האירוע בוצע או לא
5. **תן ציון ביטחון** - כמה בטוח אתה בחילוץ
6. **קבץ דומים** - אם יש אירועים דומים, אפשר לקבץ אותם

**דוגמאות למה לחפש:**
• "נפגש מחר בשעה 10"
• "הדדליין עד יום חמישי"  
• "תזכיר לי לבדוק בשבוע הבא"
• "יש לי פגישה ב-15:00"
• "נסגור את זה עד סוף השבוע"
• "כנס ביום רביעי"
• "יש לי הרצאה ב..."

אנא נתח את הקובץ המצורף וחלץ את כל האירועים האפשריים. תן דגש מיוחד לאנשי הקשר החשובים ולהודעות עם פוטנציאל יומן גבוה."""

        prompt_file = f"final_claude_prompt_{timestamp}.txt"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(final_prompt)
        
        # יצירת סיכום להוראות שימוש
        summary = f"""
✨ **הכל מוכן לשליחה לClaude!**

📊 **סיכום הנתונים:**
• סה"כ הודעות: {total_messages:,}
• מועמדי יומן: {calendar_candidates:,}
• אנשי קשר חשובים: {len(enhanced_data.get('priority_contacts', {}))}
• נתונים חיים מספטמבר נוספו ✅

📄 **קבצים לשליחה:**
1. פרומפט: {prompt_file}
2. נתונים: {enhanced_file}

🚀 **צעדי השימוש:**
1. פתח שיחה חדשה עם Claude
2. העתק את הפרומפט מהקובץ: {prompt_file}
3. צרף את קובץ הנתונים: {enhanced_file}  
4. שלח את הבקשה
5. Claude יחזיר JSON מלא עם כל אירועי היומן!

📅 **מה Claude יחזיר:**
• רשימת JSON עם כל האירועים
• סיכום לפי חודשים, קטגוריות ואנשי קשר
• המלצות על עדיפויות
• אירועים מוכנים ליבוא לGoogle Calendar

💡 **טיפ:** שמור את תוצאת Claude לקובץ JSON נפרד לשימוש עתידי!
"""
        
        instructions_file = f"final_usage_instructions_{timestamp}.txt"
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        self.log("✅ בקשה סופית נוצרה בהצלחה!", "SUCCESS")
        print(summary)
        
        return enhanced_file, prompt_file, instructions_file

def main():
    enhancer = LiveDataEnhancer()
    
    # יצירת בקשה סופית
    files = enhancer.create_final_claude_request()
    
    if files:
        enhanced_file, prompt_file, instructions_file = files
        print(f"\n🎉 **המשימה הושלמה!**")
        print(f"📋 הוראות מפורטות: {instructions_file}")
        print(f"🚀 כל מה שנשאר זה לשלוח לClaude!")

if __name__ == "__main__":
    main()













