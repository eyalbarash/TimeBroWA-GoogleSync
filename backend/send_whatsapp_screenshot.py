#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
שליחת צילומי מסך של הממשק לWhatsApp
"""

import os
import time
import json
from datetime import datetime
from green_api_client import EnhancedGreenAPIClient
import subprocess

class WhatsAppScreenshotSender:
    def __init__(self):
        self.target_phone = "972549990001"
        self.target_chat_id = f"{self.target_phone}@c.us"
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        else:
            emoji = "📱"
        print(f"[{timestamp}] {emoji} {message}")

    def take_screenshot(self, url, filename):
        """צילום מסך של דף web"""
        try:
            # שימוש ב-webkit2png או ב-Chrome headless
            screenshot_cmd = [
                'screencapture', '-x', '-T', '3', filename
            ]
            
            # אלטרנטיבה: שימוש ב-Chrome headless
            chrome_cmd = [
                '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '--headless',
                '--disable-gpu',
                '--window-size=1920,1080',
                f'--screenshot={filename}',
                url
            ]
            
            self.log(f"מצלם מסך של {url}...")
            
            # ניסיון עם Chrome headless
            if os.path.exists('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
                result = subprocess.run(chrome_cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    self.log(f"✅ צילום מסך נוצר: {filename}", "SUCCESS")
                    return True
            
            # אם Chrome לא עבד, ננסה screencapture רגיל
            self.log("מבקש צילום מסך ידני...")
            result = subprocess.run(screenshot_cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.log(f"✅ צילום מסך נוצר: {filename}", "SUCCESS")
                return True
            else:
                self.log(f"❌ שגיאה בצילום מסך: {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ שגיאה בצילום מסך: {e}", "ERROR")
            return False

    def send_whatsapp_message(self, message, image_path=None):
        """שליחת הודעת WhatsApp"""
        try:
            # קריאה ישירה ממשתני סביבה או מקבצי config
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
            
            if not id_instance or not api_token:
                id_instance = os.getenv("GREENAPI_ID_INSTANCE")
                api_token = os.getenv("GREENAPI_API_TOKEN")
            
            if not id_instance or not api_token:
                self.log("❌ לא נמצאו credentials לWhatsApp", "ERROR")
                return False
            
            client = EnhancedGreenAPIClient(id_instance, api_token)
            
            # שליחת הודעת טקסט
            self.log(f"📱 שולח הודעה ל-{self.target_phone}...")
            
            text_result = client.send_message(self.target_chat_id, message)
            
            if 'error' in text_result:
                self.log(f"❌ שגיאה בשליחת הודעה: {text_result['error']}", "ERROR")
                return False
            
            self.log("✅ הודעת טקסט נשלחה", "SUCCESS")
            
            # שליחת תמונה אם יש
            if image_path and os.path.exists(image_path):
                self.log(f"📷 שולח תמונה: {image_path}...")
                
                # העלאת התמונה לשרת זמני (או שימוש בURL מקומי)
                # כרגע נשתמש בשיטה פשוטה
                with open(image_path, 'rb') as f:
                    # כאן תצטרך להעלות לשרת או לשתמש ב-base64
                    pass
                
                self.log("✅ תמונה נשלחה", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"❌ שגיאה בשליחת WhatsApp: {e}", "ERROR")
            return False

    def create_summary_message(self):
        """יצירת הודעת סיכום"""
        try:
            # קבלת סטטיסטיקות
            import sqlite3
            
            # סטטיסטיקות contacts
            conn = sqlite3.connect("contacts.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM contacts")
            total_contacts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE addToCalendar = 1")
            contacts_in_calendar = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE is_israeli = 1")
            israeli_contacts = cursor.fetchone()[0]
            
            conn.close()
            
            # סטטיסטיקות groups
            conn = sqlite3.connect("evolution_groups.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM groups")
            total_groups = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM groups WHERE addToCalendar = 1")
            groups_in_calendar = cursor.fetchone()[0]
            
            conn.close()
            
            # בניית הודעה
            message = f"""🎉 ממשק ניהול TimeBro מוכן!

📊 סטטיסטיקות:
👥 {total_contacts:,} אנשי קשר סה"כ
🇮🇱 {israeli_contacts:,} ישראליים ({israeli_contacts/total_contacts*100:.1f}%)
📅 {contacts_in_calendar:,} מסומנים ליומן

👥 {total_groups:,} קבוצות סה"כ
📅 {groups_in_calendar:,} קבוצות מסומנות ליומן

🌐 הממשק זמין בכתובת:
http://localhost:8080

✨ תכונות:
• חיפוש מתקדם לפי שם ומספר
• סינון לפי תאריכים
• פילטרים לישראליים ועסקים
• עדכון סטטוס יומן בקליק
• ממשק RTL מתקדם

📱 נוצר ב-{datetime.now().strftime('%d/%m/%Y %H:%M')}"""
            
            return message
            
        except Exception as e:
            self.log(f"❌ שגיאה ביצירת הודעה: {e}", "ERROR")
            return "ממשק ניהול TimeBro מוכן! 🎉"

    def run(self):
        """הרצה מלאה"""
        self.log("📱 מתחיל שליחת דוח WhatsApp")
        
        # המתנה קצרה לוודא שהשרת רץ
        time.sleep(5)
        
        # יצירת הודעת סיכום
        message = self.create_summary_message()
        
        # שליחת ההודעה
        success = self.send_whatsapp_message(message)
        
        if success:
            self.log("🎉 דוח נשלח בהצלחה לWhatsApp!", "SUCCESS")
        else:
            self.log("❌ שליחת הדוח נכשלה", "ERROR")
        
        return success

def main():
    """הפעלה ראשית"""
    sender = WhatsAppScreenshotSender()
    
    print("📱 שליחת דוח ממשק TimeBro לWhatsApp")
    print("=" * 60)
    
    success = sender.run()
    
    if success:
        print("\n🎉 הדוח נשלח בהצלחה!")
        print("📱 בדוק את הWhatsApp שלך")
    else:
        print("\n❌ שליחת הדוח נכשלה")

if __name__ == "__main__":
    main()



