#!/usr/bin/env python3
"""
Example: How to Add More Contacts to the System
דוגמה: איך להוסיף אנשי קשר נוספים למערכת
"""

import sqlite3
from datetime import datetime
from quick_multi_contact_demo import QuickMultiContactDemo

class ExtendedContactAnalyzer(QuickMultiContactDemo):
    def __init__(self):
        super().__init__()
        
        # הרחבת רשימת אנשי הקשר - הוסף כאן מספרים נוספים שזיהית
        self.known_contacts.update({
            # דוגמאות לאנשי קשר נוספים - החלף במספרים אמיתיים
            
            # "972XXXXXXXX": {
            #     'name': "מוטי בראל",
            #     'company': "כפרי דרייב",
            #     'color': "10"  # בזיליקום - ירוק
            # },
            
            # "972XXXXXXXX": {
            #     'name': "עדי גץ פניאל", 
            #     'company': "MLY",
            #     'color': "9"  # אוכמניות - כחול
            # },
            
            # "972XXXXXXXX": {
            #     'name': "ערן זלטקין",
            #     'company': "סולומון גרופ", 
            #     'color': "11"  # עגבנייה - אדום
            # },
            
            # "972XXXXXXXX": {
            #     'name': "שחר זכאי",
            #     'company': "fundit",
            #     'color': "5"  # בננה - צהוב  
            # }
        })
    
    def find_high_activity_numbers(self, min_messages=500):
        """מחפש מספרי טלפון עם פעילות גבוהה"""
        self.log(f"מחפש מספרים עם יותר מ-{min_messages} הודעות...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    c.phone_number,
                    c.name,
                    COUNT(m.message_id) as message_count,
                    MAX(m.timestamp) as last_message
                FROM contacts c
                LEFT JOIN chats ch ON c.contact_id = ch.contact_id
                LEFT JOIN messages m ON ch.chat_id = m.chat_id
                GROUP BY c.contact_id
                HAVING message_count >= ?
                ORDER BY message_count DESC
                LIMIT 20
            ''', (min_messages,))
            
            results = cursor.fetchall()
            conn.close()
            
            print(f"\n📊 נמצאו {len(results)} מספרים עם פעילות גבוהה:")
            print("=" * 60)
            
            for phone, name, msg_count, last_msg in results:
                # בדוק אם כבר מזוהה
                if phone in self.known_contacts:
                    status = f"✅ מזוהה: {self.known_contacts[phone]['name']}"
                else:
                    status = "❌ לא מזוהה"
                
                print(f"📞 {phone}")
                print(f"   📝 שם בבסיס: {name}")
                print(f"   💬 {msg_count} הודעות")
                print(f"   📊 סטטוס: {status}")
                print()
                
            return results
            
        except sqlite3.Error as e:
            self.log(f"שגיאה בחיפוש מספרים: {str(e)}", "ERROR")
            return []
    
    def preview_contact_messages(self, phone_number, limit=10):
        """מציג דוגמת הודעות עבור מספר טלפון"""
        self.log(f"מציג דוגמת הודעות עבור {phone_number}...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # מצא את chat_id
            cursor.execute('''
                SELECT ch.chat_id 
                FROM contacts c
                JOIN chats ch ON c.contact_id = ch.contact_id
                WHERE c.phone_number = ?
            ''', (phone_number,))
            
            result = cursor.fetchone()
            if not result:
                print(f"❌ לא נמצא מספר {phone_number}")
                return
                
            chat_id = result[0]
            
            # קבל דוגמת הודעות
            cursor.execute('''
                SELECT content, message_type, timestamp
                FROM messages
                WHERE chat_id = ? AND content IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (chat_id, limit))
            
            messages = cursor.fetchall()
            conn.close()
            
            print(f"\n💬 דוגמת הודעות עבור {phone_number}:")
            print("-" * 40)
            
            for content, msg_type, timestamp_str in messages:
                if content and len(content.strip()) > 0:
                    # נקה את ההודעה
                    clean_content = content.strip()[:100]
                    try:
                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d %H:%M')
                    except:
                        date_str = "תאריך לא ידוע"
                    
                    print(f"[{date_str}] {msg_type}: {clean_content}")
                    
        except sqlite3.Error as e:
            self.log(f"שגיאה בקבלת הודעות: {str(e)}", "ERROR")
    
    def suggest_contact_mapping(self, phone_number):
        """מציע התאמה לאיש קשר מהרשימה"""
        messages = self.get_contact_messages(phone_number)
        
        if not messages:
            print(f"❌ לא נמצאו הודעות עבור {phone_number}")
            return
            
        # נתח תוכן להתרמה
        all_content = []
        for msg in messages[:50]:  # רק 50 הראשונות
            if msg['content'] and msg['type'] == 'text':
                all_content.append(msg['content'].lower())
                
        full_text = ' '.join(all_content)
        
        # חיפוש שמות מהרשימה בתוכן
        from contacts_list import CONTACTS_CONFIG
        
        # בנה רשימת כל אנשי הקשר
        all_contacts = []
        for company, config in CONTACTS_CONFIG.items():
            all_contacts.extend(config["contacts"])
        
        suggestions = []
        for contact_name in all_contacts:
            score = 0
            words = contact_name.split()
            
            for word in words:
                if len(word) > 2 and word.lower() in full_text:
                    score += 1
                    
            if score > 0:
                suggestions.append((contact_name, score))
                
        if suggestions:
            print(f"\n🎯 הצעות התאמה עבור {phone_number}:")
            suggestions.sort(key=lambda x: x[1], reverse=True)
            
            for contact, score in suggestions[:5]:
                from contacts_list import get_contact_company
                company, color = get_contact_company(contact)
                print(f"   • {contact} ({company}) - ציון: {score}")
        else:
            print(f"❌ לא נמצאו הצעות התאמה עבור {phone_number}")

def main():
    """הפעלת דוגמת הרחבה"""
    print("🔧 דוגמה: הוספת אנשי קשר נוספים למערכת")
    print("=" * 60)
    
    analyzer = ExtendedContactAnalyzer()
    
    # שלב 1: מצא מספרים עם פעילות גבוהה
    print("🔍 שלב 1: חיפוש מספרים עם פעילות גבוהה")
    high_activity = analyzer.find_high_activity_numbers(min_messages=1000)
    
    if not high_activity:
        print("❌ לא נמצאו מספרים עם פעילות גבוהה")
        return
    
    # שלב 2: בחר מספר לדוגמה (הראשון שלא מזוהה)
    target_phone = None
    for phone, name, msg_count, last_msg in high_activity:
        if phone not in analyzer.known_contacts:
            target_phone = phone
            break
            
    if not target_phone:
        print("✅ כל המספרים עם פעילות גבוהה כבר מזוהים!")
        return
        
    print(f"\n🎯 דוגמה: ניתוח מספר {target_phone}")
    print("=" * 50)
    
    # שלב 3: הצג דוגמת הודעות
    print("📝 שלב 2: דוגמת הודעות")
    analyzer.preview_contact_messages(target_phone, limit=15)
    
    # שלב 4: הצע התאמה
    print(f"\n🤖 שלב 3: הצעות התאמה אוטומטיות")
    analyzer.suggest_contact_mapping(target_phone)
    
    # שלב 5: הוראות המשך
    print(f"\n📋 שלב 4: איך להמשיך")
    print("-" * 30)
    print(f"1. זהה את האיש קשר המתאים עבור {target_phone}")
    print(f"2. הוסף אותו לקובץ quick_multi_contact_demo.py:")
    print(f'   "{target_phone}": {{')
    print(f'       "name": "שם האיש קשר",')
    print(f'       "company": "שם החברה",') 
    print(f'       "color": "מספר צבע"')
    print(f'   }}')
    print(f"3. הרץ שוב: python3 quick_multi_contact_demo.py")
    
    print(f"\n💡 טיפ: השתמש ב-CONTACT_MANAGEMENT_GUIDE.md למידע נוסף")

if __name__ == "__main__":
    main()
