#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
יצירת וטעינת טבלת Contacts מנתוני Green API
"""

import json
import sqlite3
import os
from datetime import datetime
from green_api_client import EnhancedGreenAPIClient

class ContactsTableManager:
    def __init__(self, db_file="contacts.db"):
        self.db_file = db_file
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        else:
            emoji = "📊"
        print(f"[{timestamp}] {emoji} {message}")

    def create_contacts_table(self):
        """יצירת טבלת Contacts"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # מחיקת טבלה קיימת אם יש
            cursor.execute("DROP TABLE IF EXISTS contacts")
            
            # יצירת טבלה חדשה
            cursor.execute("""
                CREATE TABLE contacts (
                    id TEXT PRIMARY KEY,
                    whatsapp_id TEXT UNIQUE NOT NULL,
                    phone_number TEXT,
                    name TEXT,
                    contact_name TEXT,
                    display_name TEXT,
                    type TEXT,
                    is_business BOOLEAN DEFAULT 0,
                    is_group BOOLEAN DEFAULT 0,
                    country_code TEXT,
                    is_israeli BOOLEAN DEFAULT 0,
                    has_profile_picture BOOLEAN DEFAULT 0,
                    last_seen DATETIME,
                    status_message TEXT,
                    is_approved BOOLEAN DEFAULT 0,
                    approval_reason TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # יצירת אינדקסים לחיפוש מהיר
            cursor.execute("CREATE INDEX idx_contacts_phone ON contacts(phone_number)")
            cursor.execute("CREATE INDEX idx_contacts_name ON contacts(name)")
            cursor.execute("CREATE INDEX idx_contacts_display_name ON contacts(display_name)")
            cursor.execute("CREATE INDEX idx_contacts_is_israeli ON contacts(is_israeli)")
            cursor.execute("CREATE INDEX idx_contacts_is_approved ON contacts(is_approved)")
            cursor.execute("CREATE INDEX idx_contacts_country_code ON contacts(country_code)")
            
            conn.commit()
            conn.close()
            
            self.log("✅ טבלת contacts נוצרה בהצלחה", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ שגיאה ביצירת טבלה: {e}", "ERROR")
            return False

    def extract_phone_from_whatsapp_id(self, whatsapp_id):
        """חילוץ מספר טלפון מ-WhatsApp ID"""
        if whatsapp_id.endswith("@c.us"):
            return whatsapp_id.replace("@c.us", "")
        elif whatsapp_id.endswith("@g.us"):
            return whatsapp_id.replace("@g.us", "")
        return whatsapp_id

    def analyze_phone_number(self, phone):
        """ניתוח מספר טלפון לקוד מדינה"""
        if not phone or not phone.isdigit():
            return None, False
        
        # בדיקת קוד מדינה ישראלי
        if phone.startswith("972"):
            return "972", True
        elif phone.startswith("1"):  # USA/Canada
            return "1", False
        elif phone.startswith("44"):  # UK
            return "44", False
        elif phone.startswith("49"):  # Germany
            return "49", False
        elif phone.startswith("33"):  # France
            return "33", False
        elif phone.startswith("39"):  # Italy
            return "39", False
        elif phone.startswith("34"):  # Spain
            return "34", False
        elif phone.startswith("31"):  # Netherlands
            return "31", False
        elif phone.startswith("32"):  # Belgium
            return "32", False
        elif len(phone) >= 10:
            # ניחוש לפי אורך
            if len(phone) == 10:
                return "972", True  # כנראה ישראלי ללא קידומת
            else:
                return phone[:2], False
        
        return None, False

    def get_display_name(self, contact):
        """קביעת השם המוצג"""
        name = contact.get('name', '').strip()
        contact_name = contact.get('contactName', '').strip()
        
        # אם יש שם בפנקס הכתובות, השתמש בו
        if contact_name:
            return contact_name
        # אחרת השתמש בשם המוצג
        elif name:
            return name
        # אחרת השתמש במספר הטלפון
        else:
            phone = self.extract_phone_from_whatsapp_id(contact.get('id', ''))
            return phone or 'Unknown'

    def fetch_and_store_contacts(self):
        """קבלת אנשי קשר מ-Green API ושמירה בטבלה"""
        try:
            # קריאה ישירה ממשתני סביבה או מקבצי config
            self.log("📡 מתחבר לGreen API...")
            
            # ניסיון לקרוא מקובץ .env אם קיים
            env_file = ".env"
            id_instance = None
            api_token = None
            
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.startswith('GREENAPI_ID_INSTANCE='):
                            id_instance = line.split('=', 1)[1].strip()
                        elif line.startswith('GREENAPI_API_TOKEN='):
                            api_token = line.split('=', 1)[1].strip()
            
            # אם לא נמצא, ננסה משתני סביבה
            if not id_instance:
                id_instance = os.getenv("GREENAPI_ID_INSTANCE")
            if not api_token:
                api_token = os.getenv("GREENAPI_API_TOKEN")
            
            if not id_instance or not api_token:
                self.log("❌ לא נמצאו credentials", "ERROR")
                return False
            
            # יצירת client וקבלת אנשי קשר
            client = EnhancedGreenAPIClient(id_instance, api_token)
            self.log("📞 מקבל אנשי קשר...")
            
            contacts = client.get_contacts()
            
            if not isinstance(contacts, list):
                self.log(f"❌ פורמט תגובה לא צפוי: {type(contacts)}", "ERROR")
                return False
            
            self.log(f"📊 התקבלו {len(contacts)} אנשי קשר")
            
            # שמירה במסד נתונים
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            saved_count = 0
            israeli_count = 0
            business_count = 0
            
            for i, contact in enumerate(contacts, 1):
                try:
                    whatsapp_id = contact.get('id', '')
                    phone = self.extract_phone_from_whatsapp_id(whatsapp_id)
                    country_code, is_israeli = self.analyze_phone_number(phone)
                    
                    # קביעת השם המוצג
                    display_name = self.get_display_name(contact)
                    
                    # זיהוי אם זה עסק (לפי השם או סוג)
                    is_business = (
                        'business' in contact.get('type', '').lower() or
                        any(word in display_name.lower() for word in ['ltd', 'בע"מ', 'חברת', 'company', 'corp'])
                    )
                    
                    # זיהוי אם זה קבוצה
                    is_group = whatsapp_id.endswith('@g.us')
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO contacts 
                        (id, whatsapp_id, phone_number, name, contact_name, display_name, 
                         type, is_business, is_group, country_code, is_israeli, 
                         updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        whatsapp_id,  # id = whatsapp_id
                        whatsapp_id,
                        phone,
                        contact.get('name', ''),
                        contact.get('contactName', ''),
                        display_name,
                        contact.get('type', ''),
                        is_business,
                        is_group,
                        country_code,
                        is_israeli
                    ))
                    
                    saved_count += 1
                    if is_israeli:
                        israeli_count += 1
                    if is_business:
                        business_count += 1
                    
                    # הצגת התקדמות כל 1000 אנשי קשר
                    if i % 1000 == 0:
                        self.log(f"  💾 נשמרו {i}/{len(contacts)} אנשי קשר...")
                    
                except Exception as e:
                    self.log(f"שגיאה בשמירת איש קשר {contact.get('id', 'unknown')}: {e}")
                    continue
            
            conn.commit()
            conn.close()
            
            # סיכום
            self.log(f"✅ נשמרו {saved_count} אנשי קשר", "SUCCESS")
            self.log(f"📊 מתוכם: {israeli_count} ישראליים, {business_count} עסקים")
            
            return True
            
        except Exception as e:
            self.log(f"❌ שגיאה כללית: {e}", "ERROR")
            return False

    def show_contacts_summary(self):
        """הצגת סיכום הטבלה"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # סטטיסטיקות כלליות
            cursor.execute("SELECT COUNT(*) FROM contacts")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE is_israeli = 1")
            israeli = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE is_business = 1")
            business = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE is_group = 1")
            groups = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT country_code) FROM contacts WHERE country_code IS NOT NULL")
            countries = cursor.fetchone()[0]
            
            self.log("📊 סיכום טבלת Contacts:")
            self.log(f"   👥 סה\"כ אנשי קשר: {total:,}")
            self.log(f"   🇮🇱 ישראליים: {israeli:,} ({israeli/total*100:.1f}%)")
            self.log(f"   🏢 עסקים: {business:,} ({business/total*100:.1f}%)")
            self.log(f"   👥 קבוצות: {groups:,} ({groups/total*100:.1f}%)")
            self.log(f"   🌍 מדינות: {countries}")
            
            # קודי מדינות מובילים
            cursor.execute("""
                SELECT country_code, COUNT(*) as count 
                FROM contacts 
                WHERE country_code IS NOT NULL 
                GROUP BY country_code 
                ORDER BY count DESC 
                LIMIT 5
            """)
            
            top_countries = cursor.fetchall()
            if top_countries:
                self.log("🌍 קודי מדינות מובילים:")
                for code, count in top_countries:
                    percentage = count/total*100
                    country_name = {
                        '972': 'ישראל',
                        '1': 'USA/Canada',
                        '44': 'UK',
                        '49': 'Germany',
                        '33': 'France'
                    }.get(code, f'קוד {code}')
                    self.log(f"   {country_name}: {count:,} ({percentage:.1f}%)")
            
            # דוגמאות לאנשי קשר
            cursor.execute("""
                SELECT display_name, phone_number, country_code, is_business 
                FROM contacts 
                WHERE is_israeli = 1 
                ORDER BY display_name 
                LIMIT 5
            """)
            
            israeli_samples = cursor.fetchall()
            if israeli_samples:
                self.log("🇮🇱 דוגמאות לאנשי קשר ישראליים:")
                for name, phone, code, is_biz in israeli_samples:
                    biz_mark = " 🏢" if is_biz else ""
                    self.log(f"   📞 {name} ({phone}){biz_mark}")
            
            conn.close()
            
        except Exception as e:
            self.log(f"❌ שגיאה בהצגת סיכום: {e}", "ERROR")

    def run(self):
        """הרצה מלאה"""
        self.log("🚀 מתחיל יצירת טבלת Contacts")
        
        # יצירת טבלה
        if not self.create_contacts_table():
            return False
        
        # טעינת נתונים
        if not self.fetch_and_store_contacts():
            return False
        
        # הצגת סיכום
        self.show_contacts_summary()
        
        self.log("✅ טבלת Contacts מוכנה לשימוש!", "SUCCESS")
        return True

def main():
    """הפעלה ראשית"""
    manager = ContactsTableManager()
    
    print("📊 יצירת טבלת Contacts מנתוני Green API")
    print("=" * 60)
    
    success = manager.run()
    
    if success:
        print(f"\n🎉 הושלם בהצלחה!")
        print(f"📊 בדוק את המסד נתונים: {manager.db_file}")
        print(f"📋 הטבלה מכילה את כל אנשי הקשר עם מידע מפורט")
    else:
        print(f"\n❌ התהליך נכשל")
        print(f"📋 בדוק את השגיאות למעלה")

if __name__ == "__main__":
    main()




