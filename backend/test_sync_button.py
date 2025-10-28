#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת כפתור סנכרון הכל עכשיו
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

def test_sync_manager():
    """בדיקת SyncManager"""
    print("🧪 בודק SyncManager...")
    
    try:
        from sync_manager import SyncManager
        
        # יצירת SyncManager
        sync_manager = SyncManager()
        print("✅ SyncManager נוצר בהצלחה")
        
        # בדיקת חיבור ל-Green API
        print("🔍 בודק חיבור ל-Green API...")
        state = sync_manager.green_api_client.get_state_instance()
        print(f"📡 מצב Green API: {state}")
        
        if state.get('stateInstance') != 'authorized':
            print("❌ Green API לא מורשה")
            return False
        
        print("✅ Green API מורשה")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה ב-SyncManager: {e}")
        return False

def test_sync_api():
    """בדיקת API של הסנכרון"""
    print("🧪 בודק API של הסנכרון...")
    
    try:
        from web_interface import app
        
        with app.test_client() as client:
            # בדיקת API endpoint
            print("📡 בודק API endpoint...")
            
            # נתונים לבדיקה
            test_data = {
                "start_date": "2024-09-01",
                "end_date": "2024-09-30"
            }
            
            # בדיקת קבוצות זמינות
            print("🔍 בודק קבוצות זמינות...")
            response = client.get('/api/search/groups')
            if response.status_code == 200:
                groups_data = response.get_json()
                if groups_data and 'groups' in groups_data and groups_data['groups']:
                    first_group = groups_data['groups'][0]
                    group_id = first_group['id']
                    print(f"✅ נמצאה קבוצה לבדיקה: {group_id}")
                    
                    # בדיקת API סנכרון
                    print(f"🔄 בודק סנכרון קבוצה: {group_id}")
                    response = client.post(f'/api/sync/group/{group_id}', 
                                        json=test_data,
                                        content_type='application/json')
                    
                    if response.status_code == 200:
                        result = response.get_json()
                        print(f"✅ API סנכרון עובד: {result}")
                        return True
                    else:
                        print(f"❌ API סנכרון נכשל: {response.status_code} - {response.get_data()}")
                        return False
                else:
                    print("⚠️ לא נמצאו קבוצות לבדיקה")
                    return False
            else:
                print(f"❌ שגיאה בקבלת קבוצות: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ שגיאה בבדיקת API: {e}")
        return False

def test_logs():
    """בדיקת לוגים"""
    print("🧪 בודק לוגים...")
    
    try:
        # בדיקת קובץ לוג של SyncManager
        log_file = 'sync_manager.log'
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            print(f"✅ קובץ לוג SyncManager קיים: {len(lines)} שורות")
            
            # הצגת 5 השורות האחרונות
            print("📋 5 השורות האחרונות:")
            for line in lines[-5:]:
                print(f"  {line.strip()}")
        else:
            print("⚠️ קובץ לוג SyncManager לא קיים")
        
        # בדיקת API לוגים
        from web_interface import app
        with app.test_client() as client:
            response = client.get('/api/logs')
            if response.status_code == 200:
                logs_data = response.get_json()
                if logs_data and 'success' in logs_data and logs_data['success']:
                    logs = logs_data.get('logs', [])
                    print(f"✅ API לוגים עובד: {len(logs)} לוגים")
                    
                    # הצגת 3 לוגים אחרונים
                    print("📋 3 לוגים אחרונים:")
                    for log in logs[:3]:
                        print(f"  [{log.get('level', 'N/A')}] {log.get('message', 'N/A')}")
                else:
                    print("❌ API לוגים נכשל")
                    return False
            else:
                print(f"❌ שגיאה ב-API לוגים: {response.status_code}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקת לוגים: {e}")
        return False

def main():
    """הרצת כל הבדיקות"""
    print("🚀 מתחיל בדיקת כפתור סנכרון הכל עכשיו")
    print("=" * 60)
    
    results = []
    
    # בדיקת SyncManager
    results.append(("SyncManager", test_sync_manager()))
    
    # בדיקת API
    results.append(("API סנכרון", test_sync_api()))
    
    # בדיקת לוגים
    results.append(("לוגים", test_logs()))
    
    print("\n" + "=" * 60)
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
        print("🎉 כל הבדיקות עברו בהצלחה! כפתור הסנכרון מוכן לשימוש.")
    else:
        print("⚠️ יש בעיות שצריך לפתור לפני השימוש.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
