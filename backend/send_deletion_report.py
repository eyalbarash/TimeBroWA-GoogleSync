#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
שליחת דוח מחיקת אירועים בוואטסאפ
"""

import os
import sys
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

def send_whatsapp_message(message):
    """שליחת הודעת WhatsApp"""
    try:
        from green_api_client import get_green_api_client
        
        # יצירת Green API client
        green_api = get_green_api_client()
        
        # מספר היעד
        target_number = "972549990001@c.us"
        
        # שליחת ההודעה
        result = green_api.send_message(target_number, message)
        
        if result.get('success'):
            print(f"✅ הודעת WhatsApp נשלחה בהצלחה: {message}")
            return True
        else:
            print(f"❌ שגיאה בשליחת הודעת WhatsApp: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ שגיאה בשליחת הודעת WhatsApp: {e}")
        return False

def main():
    """הפעלה ראשית"""
    print("📱 שולח דוח מחיקת אירועים בוואטסאפ")
    print("=" * 50)
    
    # הודעת הדוח
    message = """🗑️ דוח מחיקת אירועים - TimeBro

✅ הושלמה מחיקת כל האירועים בלוח שנה TimeBro

📊 סיכום:
• 250 אירועים נמחקו מ-Google Calendar
• 46 רשומות נמחקו מהמסד המקומי
• סה"כ: 296 אירועים

🕐 זמן: {time}

המערכת מוכנה לסנכרון חדש עם פורמט מעודכן.""".format(
        time=datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    )
    
    # שליחת ההודעה
    success = send_whatsapp_message(message)
    
    if success:
        print("\n✅ הדוח נשלח בהצלחה!")
    else:
        print("\n❌ שליחת הדוח נכשלה")

if __name__ == "__main__":
    main()


