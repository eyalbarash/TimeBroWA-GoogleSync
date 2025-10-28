#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
פרוצדורות עדכון מסד נתונים WhatsApp
סקריפט נח לשימוש יומיומי לעדכון אנשי קשר וקבוצות
"""

import requests
import json
import os
import sys
from datetime import datetime
from whatsapp_contacts_groups_database import WhatsAppContactsGroupsDatabase

class WhatsAppDatabaseUpdater:
    def __init__(self):
        self.db_manager = WhatsAppContactsGroupsDatabase()
        self.api_base = "https://evolution.cigcrm.com"
        self.api_key = "A6401FCD5870-4CDB-87C4-6A22F06745CD"
        self.instance_id = "ebs"

    def log(self, message: str, level: str = "INFO"):
        """רישום לוג עם חותמת זמן"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = {"SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(level, "🔄")
        print(f"[{timestamp}] {emoji} {message}")

    def update_contacts_from_api(self):
        """עדכון אנשי קשר מ-API"""
        self.log("מבצע בקשת API לעדכון אנשי קשר...")
        
        try:
            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/json'
            }
            
            data = {"where": {}}
            
            response = requests.post(
                f"{self.api_base}/chat/findContacts/{self.instance_id}",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                contacts_data = response.json()
                
                # שמירת קובץ גיבוי
                with open('findContactsResults.json', 'w', encoding='utf-8') as f:
                    json.dump(contacts_data, f, ensure_ascii=False, indent=2)
                
                # עיבוד לתוך המסד
                contacts_count, priority_count = self.db_manager.process_api_contacts(contacts_data)
                
                self.log(f"עודכנו {contacts_count:,} אנשי קשר ({priority_count} בעדיפות)", "SUCCESS")
                return contacts_count, priority_count
                
            else:
                self.log(f"שגיאה בבקשת API: {response.status_code} - {response.text}", "ERROR")
                return 0, 0
                
        except Exception as e:
            self.log(f"שגיאה בעדכון אנשי קשר: {e}", "ERROR")
            return 0, 0

    def update_groups_from_api(self):
        """עדכון קבוצות מ-API"""
        self.log("מבצע בקשת API לעדכון קבוצות...")
        
        try:
            headers = {
                'apikey': self.api_key
            }
            
            response = requests.get(
                f"{self.api_base}/group/fetchAllGroups/{self.instance_id}",
                headers=headers,
                timeout=60
            )
            
            if response.status_code == 200:
                groups_data = response.json()
                
                # שמירת קובץ גיבוי
                with open('fetchAppGroupsResults.json', 'w', encoding='utf-8') as f:
                    json.dump(groups_data, f, ensure_ascii=False, indent=2)
                
                # עיבוד לתוך המסד
                groups_count, priority_count = self.db_manager.process_api_groups(groups_data)
                
                self.log(f"עודכנו {groups_count:,} קבוצות ({priority_count} בעדיפות)", "SUCCESS")
                return groups_count, priority_count
                
            else:
                self.log(f"שגיאה בבקשת API קבוצות: {response.status_code} - {response.text}", "ERROR")
                return 0, 0
                
        except Exception as e:
            self.log(f"שגיאה בעדכון קבוצות: {e}", "ERROR")
            return 0, 0

    def run_full_update(self):
        """עדכון מלא מ-API"""
        self.log("🚀 מתחיל עדכון מלא מ-API...")
        
        # עדכון אנשי קשר
        contacts_count, contacts_priority = self.update_contacts_from_api()
        
        # עדכון קבוצות
        groups_count, groups_priority = self.update_groups_from_api()
        
        # קבלת רשימת עדיפויות
        priority_list = self.db_manager.get_timebro_priority_list()
        
        # יצירת דוח
        report = self.db_manager.generate_report()
        
        self.log("🎉 עדכון מלא הושלם!", "SUCCESS")
        
        return {
            'contacts': {'total': contacts_count, 'priority': contacts_priority},
            'groups': {'total': groups_count, 'priority': groups_priority},
            'priority_list': priority_list,
            'report': report
        }

    def run_quick_update(self):
        """עדכון מהיר מקבצים קיימים"""
        self.log("🔄 מבצע עדכון מהיר מקבצים קיימים...")
        
        results = self.db_manager.update_from_json_files()
        priority_list = self.db_manager.get_timebro_priority_list()
        report = self.db_manager.generate_report()
        
        return {
            'results': results,
            'priority_list': priority_list,
            'report': report
        }

    def show_timebro_contacts_only(self):
        """הצגת רק אנשי קשר בעדיפות timebro"""
        priority_list = self.db_manager.get_timebro_priority_list()
        
        print("\n" + "="*60)
        print("🎯 אנשי קשר בעדיפות timebro בלבד")
        print("="*60)
        
        for contact in priority_list['contacts']:
            if contact['priority'] >= 5:  # רק עדיפות גבוהה
                print(f"   • {contact['name']} (עדיפות: {contact['priority']})")
                if contact['phone']:
                    print(f"     📞 {contact['phone']}")
        
        print(f"\n📊 סה\"כ: {len([c for c in priority_list['contacts'] if c['priority'] >= 5])} אנשי קשר בעדיפות גבוהה")

if __name__ == "__main__":
    updater = WhatsAppDatabaseUpdater()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "full":
            results = updater.run_full_update()
            print("\n" + results['report'])
            
        elif command == "quick":
            results = updater.run_quick_update()
            print("\n" + results['report'])
            
        elif command == "contacts":
            contacts_count, priority_count = updater.update_contacts_from_api()
            print(f"\n✅ עודכנו {contacts_count:,} אנשי קשר ({priority_count} בעדיפות)")
            
        elif command == "groups":
            groups_count, priority_count = updater.update_groups_from_api()
            print(f"\n✅ עודכנו {groups_count:,} קבוצות ({priority_count} בעדיפות)")
            
        elif command == "timebro":
            updater.show_timebro_contacts_only()
            
        else:
            print("שימוש:")
            print("  python3 update_whatsapp_database.py full      - עדכון מלא מ-API")
            print("  python3 update_whatsapp_database.py quick     - עדכון מהיר מקבצים")
            print("  python3 update_whatsapp_database.py contacts  - עדכון אנשי קשר בלבד")
            print("  python3 update_whatsapp_database.py groups    - עדכון קבוצות בלבד")
            print("  python3 update_whatsapp_database.py timebro   - הצגת רשימת timebro")
    else:
        # ברירת מחדל - עדכון מהיר
        results = updater.run_quick_update()
        print("\n" + results['report'])













