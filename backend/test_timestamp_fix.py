#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת תיקון timestamp
"""

from datetime import datetime, timedelta
from green_api_client import EnhancedGreenAPIClient
import os

def test_timestamp_fix():
    """בדיקת תיקון timestamp"""
    try:
        print("🔧 בודק תיקון timestamp...")
        
        # קריאת credentials
        id_instance = None
        api_token = None
        
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('GREENAPI_ID_INSTANCE='):
                    id_instance = line.split('=', 1)[1].strip()
                elif line.startswith('GREENAPI_API_TOKEN='):
                    api_token = line.split('=', 1)[1].strip()
        
        if not id_instance or not api_token:
            print("❌ לא נמצאו credentials")
            return False
        
        # יצירת client
        client = EnhancedGreenAPIClient(id_instance, api_token)
        
        # בדיקת איש קשר לדוגמה
        test_contact = "972503070829@c.us"  # חלי פאר
        
        print(f"📞 בודק איש קשר: {test_contact}")
        
        # טווח תאריכים קטן לבדיקה
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        print(f"📅 טווח: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
        
        # קבלת הודעות
        print("📡 מקבל הודעות...")
        messages = client.get_chat_history_by_date_range(test_contact, start_date, end_date)
        
        print(f"✅ התקבלו {len(messages)} הודעות")
        
        if messages:
            print("📋 דוגמאות להודעות:")
            for i, msg in enumerate(messages[:3]):
                print(f"  {i+1}. {msg.get('body', 'No body')[:50]}...")
        
        print("✅ בדיקה הושלמה")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקה: {e}")
        return False

if __name__ == "__main__":
    test_timestamp_fix()

