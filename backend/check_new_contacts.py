#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקה ועדכון אנשי קשר חדשים מוואטסאפ
חלק ממערכת TimeBro Calendar
"""

import os
import json
from datetime import datetime
from timebro_calendar_system import TimeBroCalendarSystem

class NewContactsChecker:
    def __init__(self):
        self.system = TimeBroCalendarSystem()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "👥" if level == "INFO" else "✅" if level == "SUCCESS" else "❌"
        print(f"[{timestamp}] {emoji} {message}")

    def manual_contacts_sync(self):
        """סינכרון ידני של אנשי קשר"""
        print('\n' + '='*60)
        print('👥 בדיקת אנשי קשר חדשים - TimeBro Calendar')
        print('='*60)
        
        try:
            # הפעלת סינכרון אנשי קשר
            new_contacts_count = self.system.sync_new_contacts()
            
            if new_contacts_count > 0:
                print(f"\n🎉 נמצאו ונוספו {new_contacts_count} אנשי קשר חדשים!")
                
                # הצגת סטטיסטיקות מעודכנות
                self.show_contacts_statistics()
                
                # הצעה לסינכרון הודעות
                print(f"\n💡 כדי לסנכרן את ההודעות של אנשי הקשר החדשים:")
                print(f"python3 manual_calendar_update.py --sync")
                
            else:
                print(f"\n✅ המערכת מעודכנת - אין אנשי קשר חדשים")
                self.show_contacts_statistics()
                
        except Exception as e:
            self.log(f"שגיאה בסינכרון: {e}", "ERROR")

    def show_contacts_statistics(self):
        """הצגת סטטיסטיקות אנשי קשר"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.system.contacts_db)
            cursor = conn.cursor()
            
            # סטטיסטיקות כלליות
            cursor.execute("SELECT COUNT(*) FROM contacts")
            total_contacts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE is_israeli = 1")
            israeli_contacts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE is_business = 1")
            business_contacts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE category = 'group'")
            group_contacts = cursor.fetchone()[0]
            
            # אנשי קשר שנוספו היום
            cursor.execute("""
                SELECT COUNT(*) FROM contacts 
                WHERE DATE(created_at) = DATE('now')
            """)
            today_contacts = cursor.fetchone()[0]
            
            # אנשי קשר חדשים (שבוע אחרון)
            cursor.execute("""
                SELECT name, phone_number, created_at 
                FROM contacts 
                WHERE created_at >= datetime('now', '-7 days')
                ORDER BY created_at DESC
                LIMIT 10
            """)
            recent_contacts = cursor.fetchall()
            
            conn.close()
            
            print(f"\n📊 סטטיסטיקות אנשי קשר:")
            print(f"   📱 סה\"כ אנשי קשר: {total_contacts:,}")
            print(f"   🇮🇱 ישראליים: {israeli_contacts:,}")
            print(f"   🏢 עסקיים: {business_contacts:,}")
            print(f"   👥 קבוצות: {group_contacts:,}")
            print(f"   📅 נוספו היום: {today_contacts}")
            
            if recent_contacts:
                print(f"\n🆕 אנשי קשר חדשים (שבוע אחרון):")
                for i, (name, phone, created) in enumerate(recent_contacts, 1):
                    created_dt = datetime.fromisoformat(created)
                    print(f"   {i}. {name} ({phone}) - {created_dt.strftime('%d/%m %H:%M')}")
            
        except Exception as e:
            self.log(f"שגיאה בהצגת סטטיסטיקות: {e}", "ERROR")

    def export_new_contacts_report(self):
        """ייצוא דוח אנשי קשר חדשים"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(self.system.contacts_db)
            cursor = conn.cursor()
            
            # אנשי קשר שנוספו בשבוע האחרון
            cursor.execute("""
                SELECT name, phone_number, country_code, is_israeli, 
                       is_business, category, created_at
                FROM contacts 
                WHERE created_at >= datetime('now', '-7 days')
                ORDER BY created_at DESC
            """)
            
            recent_contacts = cursor.fetchall()
            conn.close()
            
            if recent_contacts:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_file = f"new_contacts_report_{timestamp}.csv"
                
                import csv
                with open(report_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['שם', 'מספר טלפון', 'קוד מדינה', 'ישראלי', 'עסקי', 'קטגוריה', 'נוסף בתאריך'])
                    
                    for contact in recent_contacts:
                        writer.writerow([
                            contact[0],  # name
                            contact[1],  # phone
                            contact[2],  # country_code
                            'כן' if contact[3] else 'לא',  # is_israeli
                            'כן' if contact[4] else 'לא',  # is_business
                            contact[5],  # category
                            datetime.fromisoformat(contact[6]).strftime('%d/%m/%Y %H:%M')  # created_at
                        ])
                
                self.log(f"✅ דוח נוצר: {report_file}", "SUCCESS")
                return report_file
            else:
                self.log("אין אנשי קשר חדשים לדיווח")
                return None
                
        except Exception as e:
            self.log(f"שגיאה ביצירת דוח: {e}", "ERROR")
            return None

def main():
    import sys
    
    checker = NewContactsChecker()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--report':
            # יצירת דוח
            checker.export_new_contacts_report()
        elif sys.argv[1] == '--stats':
            # הצגת סטטיסטיקות בלבד
            checker.show_contacts_statistics()
        else:
            print("שימוש:")
            print("  python3 check_new_contacts.py           # בדיקה וסינכרון")
            print("  python3 check_new_contacts.py --stats   # סטטיסטיקות בלבד") 
            print("  python3 check_new_contacts.py --report  # יצירת דוח CSV")
    else:
        # בדיקה וסינכרון מלא
        checker.manual_contacts_sync()

if __name__ == "__main__":
    main()













