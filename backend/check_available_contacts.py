#!/usr/bin/env python3
"""
Check Available Contacts for Calendar Sync
בדיקת אנשי קשר זמינים לסנכרון יומן
"""

import sqlite3
import json
from datetime import datetime
from contacts_list import CONTACTS_CONFIG, get_contact_company

class CheckAvailableContacts:
    def __init__(self):
        self.mike_db_path = 'whatsapp_messages.db'  # מסד הנתונים עם מייק ביקוב
        self.main_db_path = 'whatsapp_chats.db'     # מסד הנתונים הכללי
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "ℹ️"
        print(f"[{timestamp}] {emoji} {message}")

    def check_mike_database(self):
        """בודק מה יש במסד הנתונים של מייק"""
        self.log("בודק מסד נתונים של מייק ביקוב...")
        
        conn = sqlite3.connect(self.mike_db_path)
        cursor = conn.cursor()
        
        try:
            # בדיקת טבלאות
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            mike_data = {"tables": [table[0] for table in tables]}
            
            # בדיקת הודעות אוגוסט
            if 'august_messages' in mike_data["tables"]:
                cursor.execute("SELECT COUNT(*) FROM august_messages")
                mike_data["august_messages_count"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT DISTINCT sender FROM august_messages")
                mike_data["august_senders"] = [row[0] for row in cursor.fetchall()]
            
            # בדיקת הודעות כלליות
            if 'messages' in mike_data["tables"]:
                cursor.execute("SELECT COUNT(*) FROM messages WHERE content IS NOT NULL")
                mike_data["total_messages_with_content"] = cursor.fetchone()[0]
            
            conn.close()
            return mike_data
            
        except Exception as e:
            self.log(f"שגיאה בבדיקת מסד נתונים של מייק: {str(e)}", "ERROR")
            conn.close()
            return {}

    def check_main_database(self):
        """בודק את מסד הנתונים הכללי"""
        self.log("בודק מסד נתונים כללי...")
        
        conn = sqlite3.connect(self.main_db_path)
        cursor = conn.cursor()
        
        try:
            # קבלת כל אנשי הקשר עם שמות
            cursor.execute("""
                SELECT name, phone_number, is_group 
                FROM contacts 
                WHERE name IS NOT NULL AND name != '' AND name != phone_number
                ORDER BY name
            """)
            
            db_contacts = cursor.fetchall()
            
            # בדיקת הודעות לכל איש קשר
            contacts_with_messages = []
            
            for name, phone, is_group in db_contacts:
                # מציאת contact_id
                cursor.execute("SELECT contact_id FROM contacts WHERE name = ?", (name,))
                contact_result = cursor.fetchone()
                
                if contact_result:
                    contact_id = contact_result[0]
                    
                    # בדיקת הודעות
                    cursor.execute("""
                        SELECT COUNT(*) 
                        FROM messages m
                        JOIN chats c ON m.chat_id = c.chat_id
                        WHERE c.contact_id = ? AND m.content IS NOT NULL AND m.content != ''
                    """, (contact_id,))
                    
                    message_count = cursor.fetchone()[0]
                    
                    if message_count > 0:
                        contacts_with_messages.append({
                            "name": name,
                            "phone": phone,
                            "is_group": bool(is_group),
                            "message_count": message_count
                        })
            
            conn.close()
            return contacts_with_messages
            
        except Exception as e:
            self.log(f"שגיאה בבדיקת מסד נתונים כללי: {str(e)}", "ERROR")
            conn.close()
            return []

    def match_with_contacts_list(self, db_contacts):
        """מתאים אנשי קשר מהמסד לרשימה המבוקשת"""
        self.log("מתאים אנשי קשר לרשימה המבוקשת...")
        
        matched_contacts = []
        
        # בניית רשימת כל אנשי הקשר המבוקשים
        all_requested_contacts = []
        for company, config in CONTACTS_CONFIG.items():
            for contact in config["contacts"]:
                all_requested_contacts.append({
                    "name": contact,
                    "company": company,
                    "color": config["color"]
                })
        
        # התאמה
        for db_contact in db_contacts:
            db_name = db_contact["name"]
            
            for requested in all_requested_contacts:
                requested_name = requested["name"]
                
                # בדיקות התאמה שונות
                is_match = False
                match_type = ""
                
                # התאמה מדויקת
                if db_name == requested_name:
                    is_match = True
                    match_type = "התאמה מדויקת"
                
                # התאמה חלקית
                elif requested_name in db_name or db_name in requested_name:
                    is_match = True
                    match_type = "התאמה חלקית"
                
                # התאמה של שמות מנוקים
                elif self._clean_name(db_name) == self._clean_name(requested_name):
                    is_match = True
                    match_type = "התאמה נקייה"
                
                # התאמה של חלקי שמות
                elif self._compare_name_parts(db_name, requested_name):
                    is_match = True
                    match_type = "התאמת חלקי שמות"
                
                if is_match:
                    matched_contacts.append({
                        "db_name": db_name,
                        "requested_name": requested_name,
                        "company": requested["company"],
                        "color": requested["color"],
                        "phone": db_contact["phone"],
                        "is_group": db_contact["is_group"],
                        "message_count": db_contact["message_count"],
                        "match_type": match_type
                    })
                    break
        
        return matched_contacts

    def _clean_name(self, name):
        """מנקה שם לצורך השוואה"""
        import re
        clean = re.sub(r'[^\w\s]', '', name.lower()).strip()
        clean = re.sub(r'\s+', ' ', clean)
        return clean

    def _compare_name_parts(self, name1, name2):
        """משווה חלקי שמות"""
        parts1 = set(self._clean_name(name1).split())
        parts2 = set(self._clean_name(name2).split())
        
        if len(parts1) > 0 and len(parts2) > 0:
            common = parts1.intersection(parts2)
            return len(common) >= min(len(parts1), len(parts2)) * 0.5
        
        return False

    def generate_availability_report(self, mike_data, main_contacts, matched_contacts):
        """יוצר דוח זמינות אנשי קשר"""
        
        print("\n📊 דוח זמינות אנשי קשר לסנכרון יומן")
        print("=" * 70)
        
        # סיכום מסדי נתונים
        print("\n💾 מסדי נתונים זמינים:")
        print(f"   📱 מסד מייק ביקוב: {mike_data.get('august_messages_count', 0)} הודעות אוגוסט")
        print(f"   🗃️ מסד כללי: {len(main_contacts)} אנשי קשר עם הודעות")
        
        # סיכום התאמות
        print(f"\n🎯 התאמות לרשימה המבוקשת:")
        print(f"   📋 סך הכל ברשימה: {sum(len(config['contacts']) for config in CONTACTS_CONFIG.values())} אנשי קשר")
        print(f"   ✅ נמצאו במסדי נתונים: {len(matched_contacts)} אנשי קשר")
        
        # פירוט אנשי קשר שנמצאו
        if matched_contacts:
            print("\n✅ אנשי קשר זמינים לסנכרון יומן:")
            for i, contact in enumerate(matched_contacts, 1):
                company_color = {
                    "0": "ברירת מחדל", "1": "לבנדר", "2": "מרווה", "3": "ענב",
                    "4": "פלמינגו", "5": "בננה", "6": "טנג'רין", "7": "טווס",
                    "8": "קקאו", "9": "אוכמניות", "10": "בזיליקום", "11": "עגבנייה"
                }.get(contact["color"], "לא מזוהה")
                
                group_text = " (קבוצה)" if contact["is_group"] else ""
                
                print(f"\n   {i}. 👤 {contact['db_name']}")
                print(f"      🎯 מתאים ל: {contact['requested_name']}")
                print(f"      🏢 חברה: {contact['company']} (צבע: {company_color})")
                print(f"      📱 טלפון: {contact['phone']}{group_text}")
                print(f"      💬 הודעות: {contact['message_count']}")
                print(f"      🔗 סוג התאמה: {contact['match_type']}")
        else:
            print("\n❌ לא נמצאו אנשי קשר נוספים זמינים")
        
        # רשימת אנשי קשר שלא נמצאו
        found_names = [contact['requested_name'] for contact in matched_contacts]
        all_requested = []
        for company, config in CONTACTS_CONFIG.items():
            all_requested.extend(config["contacts"])
        
        missing_contacts = [name for name in all_requested if name not in found_names]
        
        if missing_contacts:
            print(f"\n❌ אנשי קשר שלא נמצאו במסדי נתונים ({len(missing_contacts)}):")
            for i, name in enumerate(missing_contacts[:15], 1):
                company, color = get_contact_company(name)
                print(f"   {i}. {name} ({company})")
            
            if len(missing_contacts) > 15:
                print(f"   ... ועוד {len(missing_contacts) - 15} אנשי קשר")
        
        # שמירת דוח
        report = {
            "timestamp": datetime.now().isoformat(),
            "mike_database": mike_data,
            "main_database_contacts": len(main_contacts),
            "matched_contacts": matched_contacts,
            "missing_contacts": missing_contacts,
            "total_requested": len(all_requested),
            "total_found": len(matched_contacts)
        }
        
        report_file = f"available_contacts_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 דוח מלא נשמר ב: {report_file}")
        
        return matched_contacts

    def run(self):
        """מריץ את הבדיקה"""
        try:
            self.log("בודק זמינות אנשי קשר לסנכרון יומן")
            print("=" * 60)
            
            # בדיקת מסד נתונים של מייק
            mike_data = self.check_mike_database()
            
            # בדיקת מסד נתונים כללי
            main_contacts = self.check_main_database()
            
            # התאמה לרשימה המבוקשת
            matched_contacts = self.match_with_contacts_list(main_contacts)
            
            # דוח זמינות
            available = self.generate_availability_report(mike_data, main_contacts, matched_contacts)
            
            print("\n🎯 סיכום:")
            if available:
                print(f"✅ יש {len(available)} אנשי קשר זמינים לסנכרון יומן")
                print("💡 האם תרצה ליצור עבורם אירועי יומן?")
            else:
                print("❌ רק מייק ביקוב זמין כרגע לסנכרון יומן")
                print("💡 נדרש לחפש עוד מקורות נתונים עבור שאר אנשי הקשר")
            
            return available
            
        except Exception as e:
            self.log(f"שגיאה: {str(e)}", "ERROR")
            return []

if __name__ == "__main__":
    checker = CheckAvailableContacts()
    available = checker.run()













