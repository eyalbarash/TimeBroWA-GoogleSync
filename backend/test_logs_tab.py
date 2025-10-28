#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת טאב הלוגים
"""

import os
import sys
import json
from datetime import datetime

def test_logs_api():
    """בדיקת API של הלוגים"""
    print("🧪 בודק API של הלוגים...")
    
    try:
        # יצירת קובץ לוג לדוגמה
        test_log_file = "test_logs.log"
        with open(test_log_file, 'w', encoding='utf-8') as f:
            f.write("2025-09-29 20:30:00,000 - INFO - 🚀 מתחיל בדיקת טאב הלוגים\n")
            f.write("2025-09-29 20:30:01,000 - WARNING - ⚠️ זהו לוג אזהרה\n")
            f.write("2025-09-29 20:30:02,000 - ERROR - ❌ זהו לוג שגיאה\n")
            f.write("2025-09-29 20:30:03,000 - DEBUG - 🔍 זהו לוג דיבוג\n")
        
        print(f"✅ נוצר קובץ לוג לדוגמה: {test_log_file}")
        
        # בדיקת פונקציית פרסור הלוגים
        from web_interface import parse_log_line
        
        test_line = "2025-09-29 20:30:00,000 - INFO - 🚀 מתחיל בדיקת טאב הלוגים"
        parsed = parse_log_line(test_line)
        
        if parsed:
            print(f"✅ פרסור לוג עובד: {parsed}")
        else:
            print("❌ פרסור לוג נכשל")
            return False
        
        # בדיקת API endpoint
        print("📡 בודק API endpoint...")
        
        # יצירת Flask app לבדיקה
        from web_interface import app
        with app.test_client() as client:
            response = client.get('/api/logs')
            data = response.get_json()
            
            if data and data.get('success'):
                logs = data.get('logs', [])
                print(f"✅ API מחזיר {len(logs)} לוגים")
                
                # הצגת הלוגים
                for i, log in enumerate(logs[:5]):  # 5 לוגים ראשונים
                    print(f"  {i+1}. [{log.get('level', 'N/A')}] {log.get('message', 'N/A')}")
                
                return True
            else:
                print(f"❌ API נכשל: {data}")
                return False
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקת API: {e}")
        return False
    finally:
        # ניקוי קובץ הלוג לדוגמה
        if os.path.exists(test_log_file):
            os.remove(test_log_file)
            print(f"🧹 נוקה קובץ הלוג לדוגמה: {test_log_file}")

def test_log_files_exist():
    """בדיקת קיום קבצי לוג"""
    print("🔍 בודק קיום קבצי לוג...")
    
    log_files = [
        'group_deletion.log',
        'arcserver_deletion.log', 
        'debug_group_deletion.log',
        'simple_timebro.log'
    ]
    
    existing_files = []
    for log_file in log_files:
        if os.path.exists(log_file):
            size = os.path.getsize(log_file)
            existing_files.append(f"{log_file} ({size} bytes)")
            print(f"✅ {log_file} - {size} bytes")
        else:
            print(f"⚠️ {log_file} - לא קיים")
    
    print(f"📊 נמצאו {len(existing_files)} קבצי לוג")
    return len(existing_files) > 0

def main():
    """הרצת כל הבדיקות"""
    print("🚀 מתחיל בדיקת טאב הלוגים")
    print("=" * 50)
    
    results = []
    
    # בדיקת קבצי לוג
    results.append(("קבצי לוג", test_log_files_exist()))
    
    # בדיקת API
    results.append(("API לוגים", test_logs_api()))
    
    print("\n" + "=" * 50)
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
        print("🎉 כל הבדיקות עברו בהצלחה! טאב הלוגים מוכן לשימוש.")
    else:
        print("⚠️ יש בעיות שצריך לפתור לפני השימוש.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)


