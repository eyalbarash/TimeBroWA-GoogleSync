#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת תצוגת סנכרון אחרון
"""

import sqlite3
from datetime import datetime

def test_last_sync_display():
    """בדיקת תצוגת סנכרון אחרון"""
    try:
        print("🔧 בודק תצוגת סנכרון אחרון...")
        
        # בדיקת טבלת sync_status
        conn = sqlite3.connect("timebro_calendar.db")
        cursor = conn.cursor()
        
        # בדיקה אם יש נתונים
        cursor.execute("SELECT COUNT(*) FROM sync_status")
        count = cursor.fetchone()[0]
        print(f"📊 רשומות בטבלת sync_status: {count}")
        
        if count > 0:
            # הצגת דוגמאות
            cursor.execute("""
                SELECT item_id, item_type, last_sync, success, messages_count, events_count
                FROM sync_status 
                ORDER BY last_sync DESC 
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            print("\n📋 דוגמאות לסנכרון אחרון:")
            for row in results:
                item_id, item_type, last_sync, success, messages_count, events_count = row
                status_icon = "✅" if success else "❌"
                print(f"  {status_icon} {item_type}: {item_id}")
                print(f"    זמן: {last_sync}")
                print(f"    הודעות: {messages_count}, אירועים: {events_count}")
                print()
        else:
            print("ℹ️ אין נתוני סינכרון בטבלה")
        
        conn.close()
        
        # בדיקת אנשי קשר מסומנים
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE addToCalendar = 1")
        marked_contacts = cursor.fetchone()[0]
        conn.close()
        
        print(f"👥 אנשי קשר מסומנים ליומן: {marked_contacts}")
        
        print("✅ בדיקה הושלמה")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקה: {e}")
        return False

if __name__ == "__main__":
    test_last_sync_display()

