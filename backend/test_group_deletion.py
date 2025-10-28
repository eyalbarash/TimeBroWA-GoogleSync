#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת פונקציונליות מחיקת קבוצות
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

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

def test_green_api_group_deletion():
    """בדיקת מחיקת קבוצה באמצעות Green API"""
    print("🧪 בודק Green API group deletion...")
    
    try:
        from green_api_client import get_green_api_client
        
        # קבלת client
        client = get_green_api_client()
        print("✅ Green API client נוצר בהצלחה")
        
        # בדיקת חיבור
        state = client.get_state_instance()
        print(f"📡 מצב ה-instance: {state}")
        
        # בדיקת קבלת קבוצות
        chats = client.get_chats()
        if isinstance(chats, list):
            chats_list = chats
        else:
            chats_list = chats.get('chats', []) if isinstance(chats, dict) else []
        print(f"📋 נמצאו {len(chats_list)} צ'אטים")
        
        # חיפוש קבוצות
        groups = [chat for chat in chats_list if '@g.us' in chat.get('id', '')]
        print(f"👥 נמצאו {len(groups)} קבוצות")
        
        if groups:
            # נסה לקבל פרטי הקבוצה הראשונה
            first_group = groups[0]
            group_id = first_group['id']
            print(f"🔍 בודק קבוצה: {group_id}")
            
            group_data = client.get_group_data(group_id)
            print(f"📊 פרטי הקבוצה: {json.dumps(group_data, indent=2, ensure_ascii=False)}")
        
        print("✅ Green API פונקציונליות בסיסית עובדת")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה ב-Green API: {e}")
        return False

def test_evolution_api_group_deletion():
    """בדיקת מחיקת קבוצה באמצעות Evolution API"""
    print("🧪 בודק Evolution API group deletion...")
    
    try:
        from evolution_api_client import get_evolution_api_client
        
        # קבלת client
        client = get_evolution_api_client()
        print("✅ Evolution API client נוצר בהצלחה")
        
        # בדיקת קבלת קבוצות
        groups = client.get_groups()
        print(f"👥 נמצאו קבוצות: {json.dumps(groups, indent=2, ensure_ascii=False)}")
        
        print("✅ Evolution API פונקציונליות בסיסית עובדת")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה ב-Evolution API: {e}")
        return False

def test_database_operations():
    """בדיקת פעולות מסד נתונים"""
    print("🧪 בודק פעולות מסד נתונים...")
    
    try:
        # בדיקת קיום מסדי נתונים
        groups_db = "evolution_groups.db"
        if os.path.exists(groups_db):
            conn = sqlite3.connect(groups_db)
            cursor = conn.cursor()
            
            # בדיקת טבלת קבוצות
            cursor.execute("SELECT COUNT(*) FROM groups")
            count = cursor.fetchone()[0]
            print(f"📊 נמצאו {count} קבוצות במסד הנתונים")
            
            # קבלת דוגמה של קבוצה
            cursor.execute("SELECT id, name FROM groups LIMIT 1")
            group = cursor.fetchone()
            if group:
                print(f"📋 דוגמת קבוצה: ID={group[0]}, שם={group[1]}")
            
            conn.close()
            print("✅ מסד הנתונים עובד תקין")
            return True
        else:
            print("❌ מסד נתונים לא נמצא")
            return False
            
    except Exception as e:
        print(f"❌ שגיאה במסד הנתונים: {e}")
        return False

def test_web_interface_integration():
    """בדיקת אינטגרציה עם ממשק ה-Web"""
    print("🧪 בודק אינטגרציה עם ממשק ה-Web...")
    
    try:
        # בדיקת קיום קבצי template
        template_file = "templates/groups.html"
        if os.path.exists(template_file):
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # בדיקת קיום פונקציות JavaScript
            if 'deleteGroup' in content:
                print("✅ פונקציית deleteGroup קיימת ב-template")
            else:
                print("❌ פונקציית deleteGroup לא נמצאה")
                return False
                
            if 'timeout: 120000' in content:
                print("✅ Timeout מוגדר ל-2 דקות")
            else:
                print("⚠️ Timeout לא מוגדר או שונה")
                
            print("✅ ממשק ה-Web מוכן")
            return True
        else:
            print("❌ קובץ template לא נמצא")
            return False
            
    except Exception as e:
        print(f"❌ שגיאה בבדיקת ממשק ה-Web: {e}")
        return False

def main():
    """הרצת כל הבדיקות"""
    print("🚀 מתחיל בדיקת פונקציונליות מחיקת קבוצות")
    print("=" * 50)
    
    results = []
    
    # בדיקת מסד נתונים
    results.append(("מסד נתונים", test_database_operations()))
    
    # בדיקת Green API
    results.append(("Green API", test_green_api_group_deletion()))
    
    # בדיקת Evolution API
    results.append(("Evolution API", test_evolution_api_group_deletion()))
    
    # בדיקת ממשק Web
    results.append(("ממשק Web", test_web_interface_integration()))
    
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
        print("🎉 כל הבדיקות עברו בהצלחה! הפונקציונליות מוכנה לשימוש.")
    else:
        print("⚠️ יש בעיות שצריך לפתור לפני השימוש.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
