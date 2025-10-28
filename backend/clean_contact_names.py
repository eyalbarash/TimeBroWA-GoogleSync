#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ניקוי ושיפור שמות אנשי קשר ושמות חברות
"""

import sqlite3
import re
from datetime import datetime

class ContactNameCleaner:
    def __init__(self, db_path="whatsapp_contacts_groups.db"):
        self.db_path = db_path
        self.changes_made = {
            'names': 0,
            'company_names': 0,
            'groups': 0
        }
    
    def clean_name(self, text):
        """ניקוי שם ממיותר"""
        if not text:
            return ''
        
        # הסרת רווחים מיותרים
        text = ' '.join(text.split())
        
        # אם השם כולו מספר - השאר ריק
        if re.match(r'^\d+$', text):
            return ''
        
        # אם השם מכיל רק תווים מיוחדים או נקודות/קווים
        cleaned_for_check = re.sub(r'[\s\.\_\-]', '', text)
        if not cleaned_for_check or len(cleaned_for_check) <= 1:
            return ''
        
        # הסרת אמוג'ים ותווים מיוחדים מוזרים
        # שומר רק: אותיות, מספרים, רווחים, אותיות עברית/אנגלית, - (מקף), ' (גרש)
        text = re.sub(r'[^\w\s\-\.\'א-תa-zA-Z0-9]', '', text)
        
        # אם אחרי הסרת תווים מיוחדים נשאר רק מספר או תו אחד - ריק
        cleaned_check = re.sub(r'[\s\-\.]', '', text)
        if re.match(r'^\d+$', cleaned_check) or len(cleaned_check) <= 1:
            return ''
        
        # הסרת נקודות מיותרות בקצה
        text = text.rstrip('.')
        
        # תיקון גרש תלוי
        text = text.replace('׳', "'")
        
        # הסרת פסיקים
        text = text.replace(',', '')
        
        # הסרת נקודות מיותרות
        text = text.replace('..', '.')
        
        # הסרת קו תחתי
        text = text.replace('_', ' ')
        
        # אם השם רק תו אחד או שניים - ריק
        if len(text.strip()) <= 1:
            return ''
        
        return text.strip()
    
    def clean_contact_names(self):
        """ניקוי שמות אנשי קשר"""
        print("🧹 מנקה שמות אנשי קשר...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # קבלת כל אנשי הקשר
        cursor.execute("SELECT contact_id, name, company_name FROM contacts WHERE type = 'contact'")
        contacts = cursor.fetchall()
        
        for contact_id, name, company_name in contacts:
            cleaned_name = self.clean_name(name) if name else None
            cleaned_company = self.clean_name(company_name) if company_name else None
            
            # עדכון רק אם היו שינויים וגם השם החדש לא ריק
            if cleaned_name != name and cleaned_name:
                cursor.execute("UPDATE contacts SET name = ?, name_cleaned = 1 WHERE contact_id = ?", (cleaned_name, contact_id))
                self.changes_made['names'] += 1
                print(f"📝 שם: '{name}' -> '{cleaned_name}'")
            elif cleaned_name and not cleaned_name.strip():
                # אם השם הריק - סימון כנוקה כדי לא לדרוס
                cursor.execute("UPDATE contacts SET name_cleaned = 1 WHERE contact_id = ?", (contact_id,))
                print(f"🗑️ שם ריק נשמר: '{name}'")
            
            if cleaned_company != company_name and cleaned_company:
                cursor.execute("UPDATE contacts SET company_name = ?, name_cleaned = 1 WHERE contact_id = ?", (cleaned_company, contact_id))
                self.changes_made['company_names'] += 1
                print(f"🏢 חברה: '{company_name}' -> '{cleaned_company}'")
        
        conn.commit()
        conn.close()
        
        print(f"✅ {self.changes_made['names']} שמות נוקו")
        print(f"✅ {self.changes_made['company_names']} שמות חברות נוקו")
    
    def clean_group_names(self):
        """ניקוי שמות קבוצות"""
        print("\n🧹 מנקה שמות קבוצות...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # קבלת כל הקבוצות
        cursor.execute("SELECT group_id, subject, company_name FROM groups")
        groups = cursor.fetchall()
        
        for group_id, subject, company_name in groups:
            cleaned_subject = self.clean_name(subject) if subject else None
            cleaned_company = self.clean_name(company_name) if company_name else None
            
            if cleaned_subject != subject:
                cursor.execute("UPDATE groups SET subject = ? WHERE group_id = ?", (cleaned_subject, group_id))
                self.changes_made['groups'] += 1
                print(f"📝 קבוצה: '{subject}' -> '{cleaned_subject}'")
            
            if cleaned_company != company_name:
                cursor.execute("UPDATE groups SET company_name = ? WHERE group_id = ?", (cleaned_company, group_id))
                self.changes_made['company_names'] += 1
                print(f"🏢 חברה: '{company_name}' -> '{cleaned_company}'")
        
        conn.commit()
        conn.close()
        
        print(f"✅ {self.changes_made['groups']} קבוצות נוקו")
    
    def run_cleanup(self):
        """הרצת כל הניקוי"""
        print("🚀 מתחיל ניקוי שמות...")
        print("=" * 60)
        
        self.clean_contact_names()
        self.clean_group_names()
        
        print("=" * 60)
        print(f"✅ סיימתי! סה\"כ שינויים:")
        print(f"   - {self.changes_made['names']} שמות אנשי קשר")
        print(f"   - {self.changes_made['company_names']} שמות חברות")
        print(f"   - {self.changes_made['groups']} קבוצות")

if __name__ == "__main__":
    cleaner = ContactNameCleaner()
    cleaner.run_cleanup()
