#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
עדכון אנשי קשר מ-Google Contacts CSV
"""

import sqlite3
import csv
from datetime import datetime

class GoogleContactsUpdater:
    def __init__(self, csv_path="/Users/eyalbarash/Downloads/contacts.csv", db_path="whatsapp_contacts_groups.db"):
        self.csv_path = csv_path
        self.db_path = db_path
        self.updates_made = {
            'names': 0,
            'company_names': 0,
            'phones_matched': 0
        }
    
    def normalize_phone(self, phone):
        """נירמול מספר טלפון"""
        if not phone:
            return None
        
        # הסרת כל סימנים מלבד ספרות
        phone = ''.join(filter(str.isdigit, phone))
        
        # אם מתחיל ב-972, הסר 0 בתחילה של המספר
        if phone.startswith('972'):
            number_part = phone[3:]  # החלק אחרי 972
            if len(number_part) > 0 and number_part[0] == '0':
                phone = '972' + number_part[1:]
        elif phone.startswith('0'):
            # אם מתחיל ב-0, הוסף 972
            phone = '972' + phone[1:]
        elif len(phone) == 9:
            # מספר ישראלי ללא קידומת
            phone = '972' + phone
        
        return phone
    
    def read_google_contacts(self):
        """קריאת אנשי קשר מ-Google Contacts CSV"""
        contacts = {}
        
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # בניית שם מלא
                    first = row.get('First Name', '').strip()
                    middle = row.get('Middle Name', '').strip()
                    last = row.get('Last Name', '').strip()
                    
                    name_parts = [first, middle, last]
                    name = ' '.join([p for p in name_parts if p])
                    
                    # שם חברה
                    company = row.get('Organization Name', '').strip()
                    
                    # טלפון
                    phone = row.get('Phone 1 - Value', '').strip()
                    
                    if name:
                        normalized_phone = self.normalize_phone(phone)
                        
                        # שמירה לפי טלפון ראשון
                        if normalized_phone and normalized_phone not in contacts:
                            contacts[normalized_phone] = {
                                'name': name,
                                'company': company
                            }
                        elif not normalized_phone:
                            # שמירה לפי שם בלבד
                            if name not in contacts:
                                contacts[name] = {
                                    'name': name,
                                    'company': company,
                                    'phone': None
                                }
        except Exception as e:
            print(f"❌ שגיאה בקריאת CSV: {e}")
            import traceback
            traceback.print_exc()
            return {}
        
        return contacts
    
    def update_database(self, google_contacts):
        """עדכון מסד הנתונים"""
        print(f"📊 עדכון מסד נתונים מ-{len(google_contacts)} אנשי קשר ב-Google Contacts...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # קבלת כל אנשי הקשר מהמסד
        cursor.execute("SELECT contact_id, name, phone_number, company_name FROM contacts WHERE type = 'contact'")
        db_contacts = cursor.fetchall()
        
        for contact_id, db_name, db_phone, db_company in db_contacts:
            db_phone_normalized = self.normalize_phone(db_phone) if db_phone else None
            
            # חיפוש התאמה ב-Google Contacts
            if db_phone_normalized and db_phone_normalized in google_contacts:
                google_contact = google_contacts[db_phone_normalized]
                
                # עדכון שם אם Google טוב יותר
                if google_contact['name'] and google_contact['name'] != db_name:
                    cursor.execute("""
                        UPDATE contacts 
                        SET name = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE contact_id = ?
                    """, (google_contact['name'], contact_id))
                    self.updates_made['names'] += 1
                    print(f"📝 שם: '{db_name}' -> '{google_contact['name']}' ({db_phone_normalized})")
                
                # עדכון חברה אם Google טוב יותר
                if google_contact['company'] and google_contact['company'] != db_company:
                    cursor.execute("""
                        UPDATE contacts 
                        SET company_name = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE contact_id = ?
                    """, (google_contact['company'], contact_id))
                    self.updates_made['company_names'] += 1
                    print(f"🏢 חברה: '{db_company}' -> '{google_contact['company']}' ({db_phone_normalized})")
                
                self.updates_made['phones_matched'] += 1
        
        conn.commit()
        conn.close()
        
        print(f"\n✅ סיימתי עדכון:")
        print(f"   - {self.updates_made['phones_matched']} התאמות טלפון")
        print(f"   - {self.updates_made['names']} שמות עודכנו")
        print(f"   - {self.updates_made['company_names']} שמות חברות עודכנו")
    
    def run_update(self):
        """הרצת כל העדכון"""
        print("🚀 מתחיל עדכון מ-Google Contacts...")
        print("=" * 60)
        
        google_contacts = self.read_google_contacts()
        print(f"📖 נטענו {len(google_contacts)} אנשי קשר מ-Google Contacts")
        
        if google_contacts:
            self.update_database(google_contacts)
        else:
            print("❌ לא נמצאו אנשי קשר לעדכון")
        
        print("=" * 60)

if __name__ == "__main__":
    updater = GoogleContactsUpdater()
    updater.run_update()

