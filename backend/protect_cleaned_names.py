#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הגנה על שמות מנוקים בייבוא הבא
רק עדכון שמות שהם ריקים או לא מובנים
"""

import sqlite3
import re

class NameProtector:
    def __init__(self, db_path="whatsapp_contacts_groups.db"):
        self.db_path = db_path
    
    def is_name_clean(self, text):
        """בדיקה אם שם נקי (ללא אמוג'ים, רווחים מיותרים וכו')"""
        if not text or text == 'None':
            return False
        
        # אם יש רווחים מיותרים
        if '  ' in text or text.strip() != text:
            return False
        
        # אם יש אמוג'ים
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            u"\U0001F900-\U0001F9FF"
            "]+", flags=re.UNICODE)
        if emoji_pattern.search(text):
            return False
        
        # אם יש פסיקים מיותרים
        if ',' in text:
            return False
        
        # אם יש סימני פיסוק מיותרים בקצה (חוץ מנקודה אמצעית)
        if text.endswith(('.', '!', '?', ':', ';')):
            return False
        
        return True
    
    def should_update_name(self, new_name, existing_name):
        """החלטה אם לעדכן שם קיים"""
        # אם אין שם קיים - עדכן
        if not existing_name or existing_name == 'None':
            return True, "לא קיים שם"
        
        # אם השם הקיים נקי - לא לעדכן
        if self.is_name_clean(existing_name):
            return False, "השם הקיים נקי"
        
        # אם השם החדש נקי והקיים לא - עדכן
        if self.is_name_clean(new_name):
            return True, "השם החדש נקי יותר"
        
        # אחרת - לא לעדכן
        return False, "אין שינוי משמעותי"
    
    def protect_existing_names(self):
        """מגן על שמות קיימים"""
        print("🛡️ מבדק הגנה על שמות מנוקים...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # סימון שמות נקיים
        try:
            cursor.execute("ALTER TABLE contacts ADD COLUMN name_cleaned BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # עמודה כבר קיימת
        
        try:
            cursor.execute("ALTER TABLE groups ADD COLUMN subject_cleaned BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass  # עמודה כבר קיימת
        
        # ספירת שמות נקיים
        cursor.execute("""
            UPDATE contacts 
            SET name_cleaned = 1 
            WHERE (name IS NOT NULL AND name != '' AND name != 'None')
        """)
        
        cursor.execute("""
            UPDATE groups 
            SET subject_cleaned = 1 
            WHERE (subject IS NOT NULL AND subject != '' AND subject != 'None')
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ הוגנו שמות מנוקים")
        print("💡 בייבוא הבא - רק שמות ריקים יועדכנו")

if __name__ == "__main__":
    protector = NameProtector()
    protector.protect_existing_names()
