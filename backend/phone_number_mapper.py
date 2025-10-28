#!/usr/bin/env python3
"""
Phone Number to Contact Name Mapper
מערכת התאמת מספרי טלפון לשמות אנשי קשר מהרשימה
"""

import sqlite3
import re
from contacts_list import CONTACTS_CONFIG, get_contact_company

# מיפוי ידני של מספרי טלפון לשמות (נתחיל עם המספרים שאנו יודעים)
PHONE_TO_NAME_MAPPING = {
    # מייק ביקוב - כבר מזוהה
    "972546687813": "מייק ביקוב",
    "972546887813": "מייק ביקוב",
    
    # נמשיך להוסיף מספרים נוספים כאן לפי הצורך
    # ניתן להוסיף מספרים באופן ידני אם ידועים מקורות חיצוניים
}

# רשימת כל אנשי הקשר מהתצורה
ALL_CONTACTS_FROM_CONFIG = []
for company, config in CONTACTS_CONFIG.items():
    for contact in config["contacts"]:
        ALL_CONTACTS_FROM_CONFIG.append(contact)

class PhoneNumberMapper:
    def __init__(self):
        self.db_path = "whatsapp_chats.db"
        self.mapped_contacts = {}
        self.unmapped_phones = []
        
    def log(self, message, level="INFO"):
        timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "🔍" if level == "ANALYZE" else "ℹ️"
        print(f"[{timestamp}] {emoji} {message}")
        
    def get_phone_with_messages(self):
        """מחזיר רשימת מספרי טלפון עם מספר ההודעות"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    c.phone_number,
                    c.name,
                    COUNT(m.message_id) as message_count
                FROM contacts c
                LEFT JOIN chats ch ON c.contact_id = ch.contact_id
                LEFT JOIN messages m ON ch.chat_id = m.chat_id
                GROUP BY c.contact_id
                HAVING message_count > 10
                ORDER BY message_count DESC
            ''')
            
            results = cursor.fetchall()
            conn.close()
            
            return results
            
        except sqlite3.Error as e:
            self.log(f"שגיאה בקבלת מספרי טלפון: {str(e)}", "ERROR")
            return []
            
    def create_phone_contact_mapping(self):
        """יוצר מיפוי בין מספרי טלפון לשמות אנשי קשר"""
        self.log("יוצר מיפוי מספרי טלפון לאנשי קשר...")
        
        # קבלת כל המספרים עם הודעות
        phone_data = self.get_phone_with_messages()
        
        self.log(f"נמצאו {len(phone_data)} מספרי טלפון עם הודעות")
        
        mapped_count = 0
        
        for phone, name, msg_count in phone_data:
            # בדיקה אם יש מיפוי ידני
            if phone in PHONE_TO_NAME_MAPPING:
                contact_name = PHONE_TO_NAME_MAPPING[phone]
                company, color = get_contact_company(contact_name)
                
                self.mapped_contacts[phone] = {
                    'name': contact_name,
                    'company': company,
                    'color': color,
                    'message_count': msg_count,
                    'db_name': name,
                    'source': 'manual_mapping'
                }
                mapped_count += 1
                self.log(f"✅ {phone} → {contact_name} ({company})")
                
            # בדיקה אם השם בבסיס נתונים תואם לרשימה
            elif name and name != phone:
                matched_contact = self.find_matching_contact(name)
                if matched_contact:
                    company, color = get_contact_company(matched_contact)
                    
                    self.mapped_contacts[phone] = {
                        'name': matched_contact,
                        'company': company,
                        'color': color,
                        'message_count': msg_count,
                        'db_name': name,
                        'source': 'name_matching'
                    }
                    mapped_count += 1
                    self.log(f"✅ {phone} → {matched_contact} ({company}) [התאמת שם]")
                else:
                    self.unmapped_phones.append({
                        'phone': phone,
                        'db_name': name,
                        'message_count': msg_count
                    })
            else:
                self.unmapped_phones.append({
                    'phone': phone,
                    'db_name': name,
                    'message_count': msg_count
                })
                
        self.log(f"✅ הושלם המיפוי: {mapped_count} מספרים מופו, {len(self.unmapped_phones)} לא מופו")
        return self.mapped_contacts, self.unmapped_phones
        
    def find_matching_contact(self, db_name):
        """מחפש התאמה בין שם בבסיס הנתונים לרשימת אנשי הקשר"""
        if not db_name or db_name.isdigit():
            return None
            
        # בדיקה ישירה
        for contact in ALL_CONTACTS_FROM_CONFIG:
            if db_name.strip() == contact.strip():
                return contact
                
        # בדיקה חלקית
        for contact in ALL_CONTACTS_FROM_CONFIG:
            # בדיקה אם השם מכיל מילים מהאיש קשר
            contact_words = contact.split()
            db_words = db_name.split()
            
            # אם יש התאמה של לפחות מילה אחת משמעותית
            meaningful_matches = 0
            for word in contact_words:
                if len(word) > 2 and word in db_name:
                    meaningful_matches += 1
                    
            if meaningful_matches > 0:
                return contact
                
        return None
        
    def generate_mapping_report(self):
        """יוצר דוח מיפוי מפורט"""
        mapped, unmapped = self.create_phone_contact_mapping()
        
        print("\n" + "="*70)
        print("📊 דוח מיפוי מספרי טלפון לאנשי קשר")
        print("="*70)
        
        # Mapped contacts by company
        if mapped:
            print(f"✅ אנשי קשר מופו ({len(mapped)}):")
            
            company_groups = {}
            for phone, data in mapped.items():
                company = data['company']
                if company not in company_groups:
                    company_groups[company] = []
                company_groups[company].append((phone, data))
                
            for company, contacts in company_groups.items():
                color_name = {
                    "1": "לבנדר", "2": "מרווה", "3": "ענב", "4": "פלמינגו",
                    "5": "בננה", "6": "טנג'רין", "7": "טווס", "8": "קקאו",
                    "9": "אוכמניות", "10": "בזיליקום", "11": "עגבנייה", "0": "ברירת מחדל"
                }.get(contacts[0][1]['color'], "לא מזוהה")
                
                print(f"\n🏢 {company} (צבע: {color_name}):")
                for phone, data in sorted(contacts, key=lambda x: x[1]['message_count'], reverse=True):
                    print(f"   📞 {data['name']}")
                    print(f"      📱 {phone}")
                    print(f"      💬 {data['message_count']} הודעות")
                    print(f"      🔍 מקור: {data['source']}")
        
        # Unmapped phones
        if unmapped:
            print(f"\n❌ מספרים לא מופו ({len(unmapped)}):")
            print("   (מספרים אלה ידרשו מיפוי ידני)")
            
            # Show top unmapped by message count
            top_unmapped = sorted(unmapped, key=lambda x: x['message_count'], reverse=True)[:15]
            for phone_data in top_unmapped:
                print(f"   📞 {phone_data['phone']} ({phone_data['db_name']}) - {phone_data['message_count']} הודעות")
                
        # Statistics
        total_messages = sum(data['message_count'] for data in mapped.values())
        print(f"\n📈 סיכום:")
        print(f"   ✅ {len(mapped)} אנשי קשר מופו")
        print(f"   ❌ {len(unmapped)} מספרים לא מופו")
        print(f"   💬 {total_messages} הודעות כוללות באנשי קשר מופו")
        
        return mapped, unmapped
        
    def suggest_manual_mappings(self, unmapped_data):
        """מציע מיפויים ידניים פוטנציאליים"""
        print(f"\n🎯 הצעות למיפוי ידני:")
        print("="*50)
        
        for phone_data in unmapped_data[:10]:  # Top 10
            phone = phone_data['phone']
            db_name = phone_data['db_name']
            msg_count = phone_data['message_count']
            
            print(f"\n📞 {phone} ({msg_count} הודעות)")
            print(f"   🏷️ שם בבסיס נתונים: {db_name}")
            
            # חיפוש התאמות חלקיות
            potential_matches = []
            if db_name and not db_name.isdigit():
                for contact in ALL_CONTACTS_FROM_CONFIG:
                    similarity = self.calculate_name_similarity(db_name, contact)
                    if similarity > 0.3:  # threshold for potential match
                        potential_matches.append((contact, similarity))
                        
            if potential_matches:
                print("   🎯 התאמות פוטנציאליות:")
                for contact, similarity in sorted(potential_matches, key=lambda x: x[1], reverse=True)[:3]:
                    company, _ = get_contact_company(contact)
                    print(f"      • {contact} ({company}) - דמיון: {similarity:.2f}")
            else:
                print("   ⚠️ לא נמצאו התאמות אוטומטיות")
                
    def calculate_name_similarity(self, name1, name2):
        """מחשב דמיון בין שני שמות"""
        if not name1 or not name2:
            return 0
            
        # Simple word overlap similarity
        words1 = set(name1.lower().split())
        words2 = set(name2.lower().split())
        
        if not words1 or not words2:
            return 0
            
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0

def main():
    """הפעלת מערכת המיפוי"""
    print("🗂️ מערכת מיפוי מספרי טלפון לאנשי קשר")
    print("="*50)
    
    mapper = PhoneNumberMapper()
    mapped, unmapped = mapper.generate_mapping_report()
    
    if unmapped:
        mapper.suggest_manual_mappings(unmapped)
        
        print(f"\n💡 להמשך העבודה:")
        print(f"   1. הוסף מיפויים ידניים לקובץ phone_number_mapper.py")
        print(f"   2. עדכן את המילון PHONE_TO_NAME_MAPPING")
        print(f"   3. הרץ שוב את המערכת")

if __name__ == "__main__":
    main()













