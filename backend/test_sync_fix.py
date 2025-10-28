#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת תיקון הסינכרון
"""

import sqlite3
from sync_manager import SyncManager

def test_sync_fix():
    """בדיקת תיקון הסינכרון"""
    try:
        print("🔧 בודק תיקון הסינכרון...")
        
        # יצירת מנהל סינכרון
        sync_manager = SyncManager()
        
        # בדיקת טבלת sync_status
        conn = sqlite3.connect("timebro_calendar.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_status'")
        if cursor.fetchone():
            print("✅ טבלת sync_status קיימת")
        else:
            print("❌ טבלת sync_status לא קיימת")
        conn.close()
        
        # בדיקת אנשי קשר מסומנים
        marked_contacts = sync_manager._get_marked_contacts()
        print(f"📊 אנשי קשר מסומנים: {len(marked_contacts)}")
        
        # בדיקת קבוצות מסומנות
        marked_groups = sync_manager._get_marked_groups()
        print(f"📊 קבוצות מסומנות: {len(marked_groups)}")
        
        print("✅ בדיקה הושלמה")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקה: {e}")
        return False

if __name__ == "__main__":
    test_sync_fix()

