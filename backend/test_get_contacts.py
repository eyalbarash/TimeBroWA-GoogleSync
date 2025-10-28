#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת getContacts method של Green API
"""

import json
import os
from green_api_client import EnhancedGreenAPIClient

def test_get_contacts():
    """בדיקת קבלת אנשי קשר מ-Green API"""
    
    try:
        # קריאה ישירה ממשתני סביבה או מקבצי config
        print("📡 מחפש credentials...")
        
        # ניסיון לקרוא מקובץ .env אם קיים
        env_file = ".env"
        id_instance = None
        api_token = None
        
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('GREENAPI_ID_INSTANCE='):
                        id_instance = line.split('=', 1)[1].strip()
                    elif line.startswith('GREENAPI_API_TOKEN='):
                        api_token = line.split('=', 1)[1].strip()
        
        # אם לא נמצא, ננסה משתני סביבה
        if not id_instance:
            id_instance = os.getenv("GREENAPI_ID_INSTANCE")
        if not api_token:
            api_token = os.getenv("GREENAPI_API_TOKEN")
        
        if not id_instance or not api_token:
            print("❌ לא נמצאו credentials.")
            print("   אפשרויות:")
            print("   1. צור קובץ .env עם GREENAPI_ID_INSTANCE ו-GREENAPI_API_TOKEN")
            print("   2. הגדר משתני סביבה")
            print("   3. בדוק אם יש קבצי config אחרים")
            return
        
        print(f"✅ נמצאו credentials: Instance={id_instance[:10]}...")
        
        # יצירת client
        client = EnhancedGreenAPIClient(id_instance, api_token)
        
        print("📞 קורא ל-getContacts...")
        
        # קבלת אנשי קשר
        contacts = client.get_contacts()
        
        print(f"📊 סוג התגובה: {type(contacts)}")
        
        if isinstance(contacts, dict) and 'error' in contacts:
            print(f"❌ שגיאה: {contacts['error']}")
            return
        
        if isinstance(contacts, list):
            print(f"✅ התקבלו {len(contacts)} אנשי קשר")
            
            # הצגת 5 ראשונים
            print("\n📋 דוגמאות לאנשי קשר:")
            for i, contact in enumerate(contacts[:5], 1):
                print(f"\n{i}. {json.dumps(contact, indent=2, ensure_ascii=False)}")
            
            if len(contacts) > 5:
                print(f"\n... ועוד {len(contacts) - 5} אנשי קשר")
                
            # הצגת המבנה של איש קשר ראשון
            if contacts:
                print("\n🔍 מפתחות זמינים באיש קשר:")
                for key in contacts[0].keys():
                    print(f"  - {key}")
        
        elif isinstance(contacts, dict):
            print("📄 התגובה היא אובייקט:")
            print(json.dumps(contacts, indent=2, ensure_ascii=False))
        
        else:
            print(f"❓ פורמט לא צפוי: {contacts}")
            
    except Exception as e:
        print(f"❌ שגיאה: {e}")

if __name__ == "__main__":
    test_get_contacts()
