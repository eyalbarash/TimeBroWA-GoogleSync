#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת סימון אוטומטי
"""

import sqlite3
from sync_manager import SyncManager

def test_auto_mark():
    """בדיקת סימון אוטומטי"""
    try:
        print("🔧 בודק סימון אוטומטי...")
        
        # יצירת מנהל סינכרון
        sync_manager = SyncManager()
        
        # בדיקת איש קשר לדוגמה
        test_contact_id = "972544395050@c.us"
        
        print(f"📞 בודק איש קשר: {test_contact_id}")
        
        # בדיקה לפני סימון
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT addToCalendar FROM contacts WHERE whatsapp_id = ?", (test_contact_id,))
        result = cursor.fetchone()
        if result:
            print(f"📊 לפני סימון: addToCalendar = {result[0]}")
        else:
            print("❌ איש קשר לא נמצא")
            return False
        conn.close()
        
        # סימון אוטומטי
        print("🔄 מסמן אוטומטית...")
        sync_manager._mark_for_calendar(test_contact_id, is_contact=True)
        
        # בדיקה אחרי סימון
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT addToCalendar FROM contacts WHERE whatsapp_id = ?", (test_contact_id,))
        result = cursor.fetchone()
        if result:
            print(f"📊 אחרי סימון: addToCalendar = {result[0]}")
            if result[0] == 1:
                print("✅ סימון אוטומטי עובד!")
            else:
                print("❌ סימון אוטומטי לא עובד")
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקה: {e}")
        return False

if __name__ == "__main__":
    test_auto_mark()

