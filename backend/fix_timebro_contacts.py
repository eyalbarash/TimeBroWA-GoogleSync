#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
תיקון רשימת timebro - עדכון חלי פאר והסרת אנשי קשר שלא נמצאו
"""

import sqlite3
import json
from datetime import datetime

class TimeBroContactsFixer:
    def __init__(self):
        self.db_path = "whatsapp_contacts_groups.db"
        
    def log(self, message: str, level: str = "INFO"):
        """רישום לוג עם חותמת זמן"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = {"SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "FIX": "🔧"}.get(level, "📊")
        print(f"[{timestamp}] {emoji} {message}")

    def fix_chali_automation(self):
        """תיקון חלי פאר = חלי אוטומציות / אניגמה"""
        self.log("מתקן: חלי פאר = חלי אוטומציות / אניגמה", "FIX")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # חיפוש חלי פאר במסד
        cursor.execute('''
            SELECT name, phone_number, remote_jid, whatsapp_id
            FROM contacts
            WHERE LOWER(name) LIKE '%חלי%' AND LOWER(name) LIKE '%פאר%'
        ''')
        
        chali_contacts = cursor.fetchall()
        
        if chali_contacts:
            for contact in chali_contacts:
                name, phone, remote_jid, whatsapp_id = contact
                
                # עדכון לעדיפות גבוהה עם תיאור נכון
                cursor.execute('''
                    UPDATE contacts 
                    SET include_in_timebro = 1,
                        timebro_priority = 6,
                        company = 'אניגמה',
                        notes = 'חלי אוטומציות / אניגמה',
                        updated_at = ?
                    WHERE name = ?
                ''', (datetime.now().isoformat(), name))
                
                self.log(f"עודכן: {name} - {phone or remote_jid} (אניגמה)", "SUCCESS")
        else:
            # חיפוש רחב יותר
            cursor.execute('''
                SELECT name, phone_number, remote_jid, whatsapp_id
                FROM contacts
                WHERE LOWER(name) LIKE '%חלי%'
                ORDER BY timebro_priority DESC
            ''')
            
            all_chali = cursor.fetchall()
            self.log(f"נמצאו {len(all_chali)} אנשי קשר עם השם חלי:", "INFO")
            
            for contact in all_chali:
                name, phone, remote_jid, whatsapp_id = contact
                print(f"   • {name} - {phone or remote_jid}")
        
        conn.commit()
        conn.close()

    def remove_contacts_not_found(self):
        """הסרת אנשי קשר שלא נמצאו מהרשימת העדיפות"""
        self.log("מסיר אנשי קשר שלא נמצאו מרשימת timebro", "FIX")
        
        # אנשי קשר להסרה
        contacts_to_remove = [
            'שרון רייכטר - טיפול טכני ב crm',
            'ישי גבנאן | יזם ומומחה למסחר באטסי',
            'אלדד וואטסאפ טריכום / trichome',
            'נדיה טרייכום / trichome'
        ]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        removed_count = 0
        
        for contact_name in contacts_to_remove:
            # חיפוש והסרה מרשימת timebro (לא מחיקה מהמסד)
            keywords = contact_name.lower().split()
            main_keywords = [word for word in keywords if len(word) > 2 and word not in ['/', 'של', 'ב']]
            
            if main_keywords:
                search_pattern = '%' + '%'.join(main_keywords[:2]) + '%'
                
                cursor.execute('''
                    UPDATE contacts 
                    SET include_in_timebro = 0,
                        timebro_priority = 0,
                        notes = 'הוסר מרשימת timebro לפי בקשת המשתמש',
                        updated_at = ?
                    WHERE LOWER(name) LIKE ? AND include_in_timebro = 1
                ''', (datetime.now().isoformat(), search_pattern))
                
                if cursor.rowcount > 0:
                    removed_count += cursor.rowcount
                    self.log(f"הוסר מtimebro: {contact_name}", "SUCCESS")
        
        conn.commit()
        conn.close()
        
        self.log(f"הוסרו {removed_count} אנשי קשר מרשימת timebro", "SUCCESS")
        return removed_count

    def generate_clean_final_list(self):
        """יצירת רשימה סופית נקייה"""
        self.log("יוצר רשימה סופית נקייה ומעודכנת", "FIX")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # רשימת אנשי קשר בעדיפות גבוהה בלבד
        cursor.execute('''
            SELECT name, phone_number, remote_jid, timebro_priority, company, notes
            FROM contacts
            WHERE include_in_timebro = 1 AND timebro_priority >= 4
            ORDER BY timebro_priority DESC, name
        ''')
        
        high_priority_contacts = cursor.fetchall()
        
        # רשימת קבוצות בעדיפות
        cursor.execute('''
            SELECT subject, whatsapp_group_id, timebro_priority
            FROM groups 
            WHERE include_in_timebro = 1
            ORDER BY timebro_priority DESC, subject
        ''')
        
        priority_groups = cursor.fetchall()
        
        conn.close()
        
        print("\n" + "="*80)
        print("🎯 רשימה סופית נקייה ליומן timebro")
        print("="*80)
        print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print(f"📊 {len(high_priority_contacts)} אנשי קשר בעדיפות גבוהה (4+)")
        print("")
        
        # קיבוץ לפי עדיפות
        by_priority = {}
        for contact in high_priority_contacts:
            priority = contact[3]
            if priority not in by_priority:
                by_priority[priority] = []
            by_priority[priority].append(contact)
        
        # הצגה לפי עדיפות
        for priority in sorted(by_priority.keys(), reverse=True):
            contacts = by_priority[priority]
            
            print(f"⭐ עדיפות {priority} ({len(contacts)} אנשי קשר):")
            print("-" * 50)
            
            for contact in sorted(contacts, key=lambda x: x[0]):
                name, phone, remote_jid, prio, company, notes = contact
                identifier = phone if phone else remote_jid
                
                print(f"• {name}")
                print(f"  📞 {identifier}")
                if company:
                    print(f"  🏢 {company}")
                if notes and 'אניגמה' in notes:
                    print(f"  📝 {notes}")
                print("")
        
        # קבוצות
        if priority_groups:
            print(f"🏠 קבוצות בעדיפות ({len(priority_groups)}):")
            print("-" * 40)
            
            for group in priority_groups:
                subject, group_id, priority = group
                print(f"• {subject} (עדיפות: {priority})")
                print(f"  🆔 {group_id}")
                print("")
        
        # שמירת רשימה סופית לקובץ
        final_list = {
            'timestamp': datetime.now().isoformat(),
            'contacts_count': len(high_priority_contacts),
            'groups_count': len(priority_groups),
            'contacts': [
                {
                    'name': contact[0],
                    'identifier': contact[1] if contact[1] else contact[2],
                    'phone': contact[1],
                    'remote_jid': contact[2],
                    'priority': contact[3],
                    'company': contact[4],
                    'notes': contact[5]
                } for contact in high_priority_contacts
            ],
            'groups': [
                {
                    'name': group[0],
                    'group_id': group[1],
                    'priority': group[2]
                } for group in priority_groups
            ]
        }
        
        with open('timebro_clean_final_list.json', 'w', encoding='utf-8') as f:
            json.dump(final_list, f, ensure_ascii=False, indent=2)
        
        # רשימה פשוטה לטקסט
        with open('timebro_clean_contacts.txt', 'w', encoding='utf-8') as f:
            f.write("רשימה סופית נקייה ליומן timebro\n")
            f.write("="*50 + "\n")
            f.write(f"עודכן: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
            
            for priority in sorted(by_priority.keys(), reverse=True):
                contacts = by_priority[priority]
                f.write(f"עדיפות {priority}:\n")
                
                for contact in sorted(contacts, key=lambda x: x[0]):
                    name, phone, remote_jid, prio, company, notes = contact
                    identifier = phone if phone else remote_jid
                    f.write(f"  • {name} - {identifier}\n")
                f.write("\n")
        
        self.log("רשימה סופית נשמרה בקבצים: timebro_clean_final_list.json, timebro_clean_contacts.txt", "SUCCESS")
        
        return final_list

if __name__ == "__main__":
    fixer = TimeBroContactsFixer()
    
    # תיקון חלי פאר
    fixer.fix_chali_automation()
    
    # הסרת אנשי קשר שלא נמצאו
    removed_count = fixer.remove_contacts_not_found()
    
    # יצירת רשימה סופית נקייה
    final_list = fixer.generate_clean_final_list()
    
    print(f"\n🎉 תיקונים הושלמו!")
    print(f"📊 רשימה סופית עם {final_list['contacts_count']} אנשי קשר")













