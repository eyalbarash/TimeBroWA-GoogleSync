#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת כפתור סנכרון הכל עכשיו בעמוד הראשי
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment variables
load_env_file()

def test_sync_all_api():
    """בדיקת API של סנכרון כללי"""
    print("🧪 בודק API של סנכרון כללי...")
    
    try:
        from web_interface import app
        
        with app.test_client() as client:
            # נתונים לבדיקה
            test_data = {
                "start_date": "2024-09-01",
                "end_date": "2024-09-30"
            }
            
            print("🔄 בודק API סנכרון כללי...")
            response = client.post('/api/sync/all', 
                                json=test_data,
                                content_type='application/json')
            
            print(f"📊 סטטוס תגובה: {response.status_code}")
            print(f"📋 תוכן תגובה: {response.get_data()}")
            
            if response.status_code == 200:
                result = response.get_json()
                print(f"✅ API סנכרון כללי עובד: {result}")
                return True
            else:
                print(f"❌ API סנכרון כללי נכשל: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ שגיאה בבדיקת API: {e}")
        return False

def test_sync_manager_all():
    """בדיקת SyncManager ישירות"""
    print("🧪 בודק SyncManager ישירות...")
    
    try:
        from sync_manager import SyncManager
        
        # יצירת SyncManager
        sync_manager = SyncManager()
        print("✅ SyncManager נוצר בהצלחה")
        
        # בדיקת פונקציות עזר
        print("🔍 בודק פונקציות עזר...")
        marked_contacts = sync_manager._get_marked_contacts()
        marked_groups = sync_manager._get_marked_groups()
        
        print(f"📊 אנשי קשר מסומנים: {len(marked_contacts)}")
        print(f"📊 קבוצות מסומנות: {len(marked_groups)}")
        
        if len(marked_contacts) == 0 and len(marked_groups) == 0:
            print("⚠️ אין אנשי קשר או קבוצות מסומנים ליומן")
            return False
        
        # בדיקת סנכרון כללי
        print("🔄 בודק סנכרון כללי...")
        result = sync_manager.sync_all_marked("2024-09-01", "2024-09-30")
        
        print(f"📊 תוצאת סנכרון כללי: {result}")
        
        if result.get("success"):
            print("✅ סנכרון כללי עובד")
            return True
        else:
            print(f"❌ סנכרון כללי נכשל: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"❌ שגיאה ב-SyncManager: {e}")
        return False

def test_database_tables():
    """בדיקת טבלאות מסד הנתונים"""
    print("🧪 בודק טבלאות מסד הנתונים...")
    
    try:
        import sqlite3
        
        # בדיקת טבלת אנשי קשר
        print("🔍 בודק טבלת אנשי קשר...")
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE addToCalendar = 1")
        contacts_count = cursor.fetchone()[0]
        print(f"📊 אנשי קשר מסומנים: {contacts_count}")
        conn.close()
        
        # בדיקת טבלת קבוצות
        print("🔍 בודק טבלת קבוצות...")
        conn = sqlite3.connect("evolution_groups.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM groups WHERE addToCalendar = 1")
        groups_count = cursor.fetchone()[0]
        print(f"📊 קבוצות מסומנות: {groups_count}")
        conn.close()
        
        if contacts_count == 0 and groups_count == 0:
            print("⚠️ אין פריטים מסומנים ליומן")
            return False
        
        print("✅ יש פריטים מסומנים ליומן")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקת מסד נתונים: {e}")
        return False

def main():
    """הרצת כל הבדיקות"""
    print("🚀 מתחיל בדיקת כפתור סנכרון הכל עכשיו בעמוד הראשי")
    print("=" * 70)
    
    results = []
    
    # בדיקת מסד נתונים
    results.append(("מסד נתונים", test_database_tables()))
    
    # בדיקת SyncManager
    results.append(("SyncManager", test_sync_manager_all()))
    
    # בדיקת API
    results.append(("API סנכרון כללי", test_sync_all_api()))
    
    print("\n" + "=" * 70)
    print("📊 תוצאות הבדיקות:")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ עבר" if result else "❌ נכשל"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 סיכום: {passed}/{total} בדיקות עברו")
    
    if passed == total:
        print("🎉 כל הבדיקות עברו בהצלחה! כפתור הסנכרון הכללי מוכן לשימוש.")
    else:
        print("⚠️ יש בעיות שצריך לפתור לפני השימוש.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


