#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת סינכרון משופר עם לוגים
"""

from datetime import datetime, timedelta
from sync_manager import SyncManager
import os

def test_improved_sync():
    """בדיקת סינכרון משופר"""
    try:
        print("🔧 בודק סינכרון משופר...")
        
        # יצירת מנהל סינכרון
        sync_manager = SyncManager()
        
        # בדיקת איש קשר לדוגמה
        test_contact = "972503070829@c.us"  # חלי פאר
        
        print(f"📞 בודק איש קשר: {test_contact}")
        
        # טווח תאריכים קטן לבדיקה
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)  # רק שבוע
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        print(f"📅 טווח: {start_date_str} - {end_date_str}")
        
        # סינכרון
        print("🔄 מתחיל סינכרון...")
        result = sync_manager.sync_contact_messages(test_contact, start_date_str, end_date_str)
        
        print(f"✅ תוצאות סינכרון:")
        print(f"   הצלחה: {result.get('success', False)}")
        print(f"   הודעות שנמצאו: {result.get('messages_found', 0)}")
        print(f"   הודעות שנשמרו: {result.get('messages_saved', 0)}")
        print(f"   אירועים שנוצרו: {result.get('events_created', 0)}")
        
        if not result.get('success', False):
            print(f"❌ שגיאה: {result.get('error', 'לא ידוע')}")
        
        print("✅ בדיקה הושלמה")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקה: {e}")
        return False

if __name__ == "__main__":
    test_improved_sync()

