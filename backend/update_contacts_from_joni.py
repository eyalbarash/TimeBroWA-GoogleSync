#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
עדכון מסד הנתונים עם אנשי הקשר מקובץ JONI_Contacts.csv
מעדכן 2,712 אנשי קשר חדשים במערכת
"""

import sqlite3
import csv
import json
from datetime import datetime
import os

class JONIContactsUpdater:
    def __init__(self):
        self.user_phone = '972549990001'
        self.db_path = 'whatsapp_contacts.db'
        self.csv_path = 'JONI_Contacts.csv'
        self.stats = {
            'total_contacts': 0,
            'new_contacts': 0,
            'updated_contacts': 0,
            'errors': 0,
            'israeli_numbers': 0,
            'international_numbers': 0
        }
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "📱" if level == "INFO" else "✅" if level == "SUCCESS" else "❌"
        print(f"[{timestamp}] {emoji} {message}")
        
    def create_contacts_table(self):
        """יצירת טבלת אנשי קשר משודרגת"""
        self.log("יוצר טבלת אנשי קשר משודרגת...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # יצירת טבלה עם כל השדות הנדרשים
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                full_name TEXT,
                country_code TEXT,
                is_israeli BOOLEAN DEFAULT 0,
                is_business BOOLEAN DEFAULT 0,
                category TEXT,
                last_seen DATE,
                message_count INTEGER DEFAULT 0,
                has_chat BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # אינדקסים לחיפוש מהיר
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_phone ON contacts(phone_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_name ON contacts(name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_country ON contacts(country_code)')
        
        conn.commit()
        conn.close()
        self.log("טבלת אנשי קשר נוצרה בהצלחה", "SUCCESS")
        
    def parse_phone_number(self, phone):
        """ניתוח מספר טלפון וזיהוי ארץ"""
        phone = str(phone).strip()
        
        # זיהוי ישראל
        if phone.startswith('972'):
            return {
                'country_code': '972',
                'is_israeli': True,
                'formatted': phone
            }
        
        # זיהוי ארצות אחרות
        country_codes = {
            '1': 'US/Canada',
            '33': 'France', 
            '49': 'Germany',
            '44': 'UK',
            '39': 'Italy',
            '66': 'Thailand',
            '86': 'China',
            '201': 'Egypt',
            '91': 'India'
        }
        
        for code, country in country_codes.items():
            if phone.startswith(code):
                return {
                    'country_code': code,
                    'is_israeli': False,
                    'formatted': phone,
                    'country': country
                }
        
        return {
            'country_code': 'Unknown',
            'is_israeli': False,
            'formatted': phone
        }
        
    def categorize_contact(self, name, full_name):
        """קטגוריזציה אוטומטית של אנשי קשר"""
        name_lower = name.lower()
        full_name_lower = full_name.lower() if full_name else ""
        
        business_keywords = [
            'דר', 'ד״ר', 'מוסך', 'טכנאי', 'מסגר', 'רופא', 'שיפוצים',
            'משרד', 'חברה', 'קופות', 'שירותים', 'מונית', 'שליח',
            'מכירות', 'חשמלאי', 'סולרי', 'ביטוח', 'בנק', 'מרפאה'
        ]
        
        for keyword in business_keywords:
            if keyword in name_lower or keyword in full_name_lower:
                return 'business'
                
        return 'personal'
        
    def load_and_process_contacts(self):
        """טעינה ועיבוד אנשי הקשר מהקובץ"""
        self.log(f"טוען אנשי קשר מקובץ {self.csv_path}...")
        
        if not os.path.exists(self.csv_path):
            self.log(f"קובץ {self.csv_path} לא נמצא!", "ERROR")
            return False
            
        contacts = []
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8-sig') as file:  # utf-8-sig מסיר BOM
                reader = csv.DictReader(file)
                
                for row in reader:
                    if not row.get('Mobile') or not row.get('Name'):
                        continue
                        
                    phone_info = self.parse_phone_number(row['Mobile'])
                    category = self.categorize_contact(row['Name'], row.get('Full Name', ''))
                    
                    contact = {
                        'phone_number': phone_info['formatted'],
                        'name': row['Name'].strip(),
                        'full_name': row.get('Full Name', '').strip(),
                        'country_code': phone_info['country_code'],
                        'is_israeli': phone_info['is_israeli'],
                        'is_business': category == 'business',
                        'category': category
                    }
                    
                    contacts.append(contact)
                    self.stats['total_contacts'] += 1
                    
                    if phone_info['is_israeli']:
                        self.stats['israeli_numbers'] += 1
                    else:
                        self.stats['international_numbers'] += 1
                        
        except Exception as e:
            self.log(f"שגיאה בקריאת הקובץ: {str(e)}", "ERROR")
            return False
            
        self.log(f"נטענו {len(contacts)} אנשי קשר מהקובץ", "SUCCESS")
        return contacts
        
    def update_database(self, contacts):
        """עדכון מסד הנתונים עם אנשי הקשר"""
        self.log("מעדכן מסד נתונים...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for contact in contacts:
            try:
                # בדיקה אם איש הקשר כבר קיים
                cursor.execute('SELECT id FROM contacts WHERE phone_number = ?', 
                             (contact['phone_number'],))
                
                if cursor.fetchone():
                    # עדכון איש קשר קיים
                    cursor.execute('''
                        UPDATE contacts SET 
                            name = ?, full_name = ?, country_code = ?,
                            is_israeli = ?, is_business = ?, category = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE phone_number = ?
                    ''', (
                        contact['name'], contact['full_name'], contact['country_code'],
                        contact['is_israeli'], contact['is_business'], contact['category'],
                        contact['phone_number']
                    ))
                    self.stats['updated_contacts'] += 1
                else:
                    # הוספת איש קשר חדש
                    cursor.execute('''
                        INSERT INTO contacts 
                        (phone_number, name, full_name, country_code, is_israeli, is_business, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        contact['phone_number'], contact['name'], contact['full_name'],
                        contact['country_code'], contact['is_israeli'], contact['is_business'],
                        contact['category']
                    ))
                    self.stats['new_contacts'] += 1
                    
            except Exception as e:
                self.log(f"שגיאה בעדכון איש קשר {contact['name']}: {str(e)}", "ERROR")
                self.stats['errors'] += 1
                continue
                
        conn.commit()
        conn.close()
        
    def generate_report(self):
        """יצירת דוח סיכום"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'source_file': self.csv_path,
            'database_path': self.db_path,
            'user_phone': self.user_phone,
            'statistics': self.stats,
            'summary': {
                'success_rate': round((self.stats['total_contacts'] - self.stats['errors']) / self.stats['total_contacts'] * 100, 2),
                'israeli_percentage': round(self.stats['israeli_numbers'] / self.stats['total_contacts'] * 100, 2),
                'new_vs_updated': f"{self.stats['new_contacts']} חדשים, {self.stats['updated_contacts']} מעודכנים"
            }
        }
        
        report_file = f"contacts_update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
            
        return report, report_file
        
    def print_summary(self, report):
        """הדפסת סיכום מפורט"""
        print("\n" + "="*60)
        print("🎉 סיכום עדכון אנשי הקשר")
        print("="*60)
        print(f"📱 סה\"כ אנשי קשר: {self.stats['total_contacts']:,}")
        print(f"✅ חדשים: {self.stats['new_contacts']:,}")
        print(f"🔄 מעודכנים: {self.stats['updated_contacts']:,}")
        print(f"❌ שגיאות: {self.stats['errors']:,}")
        print(f"🇮🇱 מספרים ישראליים: {self.stats['israeli_numbers']:,} ({report['summary']['israeli_percentage']}%)")
        print(f"🌍 מספרים בינלאומיים: {self.stats['international_numbers']:,}")
        print(f"📊 אחוז הצלחה: {report['summary']['success_rate']}%")
        print("="*60)
        
    def run(self):
        """הרצת התהליך המלא"""
        self.log("🚀 התחלת עדכון אנשי קשר מקובץ JONI")
        
        # יצירת טבלה
        self.create_contacts_table()
        
        # טעינת אנשי קשר
        contacts = self.load_and_process_contacts()
        if not contacts:
            return False
            
        # עדכון מסד נתונים
        self.update_database(contacts)
        
        # יצירת דוח
        report, report_file = self.generate_report()
        
        # הדפסת סיכום
        self.print_summary(report)
        
        self.log(f"📄 דוח נשמר ב: {report_file}", "SUCCESS")
        self.log("✅ עדכון אנשי הקשר הושלם בהצלחה!", "SUCCESS")
        
        return True

if __name__ == "__main__":
    updater = JONIContactsUpdater()
    updater.run()
