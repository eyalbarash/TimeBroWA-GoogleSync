#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הפעלה ידנית של עדכון יומן TimeBro
לשימוש כאשר אייל רוצה להפעיל את התהליך מיד
"""

import os
import json
from datetime import datetime
from timebro_calendar_system import TimeBroCalendarSystem

class ManualCalendarUpdate:
    def __init__(self):
        self.system = TimeBroCalendarSystem()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "🔧" if level == "INFO" else "✅" if level == "SUCCESS" else "❌"
        print(f"[{timestamp}] {emoji} {message}")

    def manual_full_process(self):
        """תהליך מלא ידני - מחילוץ ועד יבוא ליומן"""
        print('\n' + '='*70)
        print('🔧 הפעלה ידנית של מערכת TimeBro Calendar')
        print('='*70)
        
        try:
            # 1. אתחול מסדי נתונים
            self.system.init_databases()
            
            # 2. חילוץ נתוני השבוע
            self.log("מחלץ נתוני השבוע לעיבוד יומן...")
            weekly_data = self.system.extract_weekly_calendar_data()
            
            if not weekly_data or len(weekly_data.get('messages_with_calendar_potential', [])) == 0:
                self.log("⚠️ לא נמצאו הודעות עם פוטנציאל יומן השבוע")
                print("\n💡 ייתכן שצריך:")
                print("1. לחכות עוד זמן לאיסוף הודעות")
                print("2. לבדוק שהWhatsApp Client רץ")
                print("3. לבצע סינכרון ידני: python3 -c \"from timebro_calendar_system import TimeBroCalendarSystem; TimeBroCalendarSystem().sync_whatsapp_messages()\"")
                return
            
            # 3. יצירת קבצים לClaude
            data_file, prompt_file = self.system.send_to_claude_and_process(weekly_data)
            
            print(f"\n📄 קבצים נוצרו לClaude:")
            print(f"   נתונים: {data_file}")
            print(f"   פרומפט: {prompt_file}")
            
            # 4. הוראות למשתמש
            print(f"\n🚀 השלבים הבאים:")
            print(f"1. שלח ל-Claude את הפרומפט מהקובץ: {prompt_file}")
            print(f"2. צרף את קובץ הנתונים: {data_file}")
            print(f"3. שמור את תגובת Claude כ-: claude_response.json")
            print(f"4. הרץ: python3 manual_calendar_update.py --process-claude claude_response.json")
            
            print(f"\n💡 או הרץ:")
            print(f"python3 -c \"from manual_calendar_update import ManualCalendarUpdate; ManualCalendarUpdate().process_claude_response('claude_response.json')\"")
            
        except Exception as e:
            self.log(f"שגיאה בתהליך: {e}", "ERROR")

    def process_claude_response(self, response_file):
        """עיבוד תגובת Claude והכנסה ליומן"""
        if not os.path.exists(response_file):
            self.log(f"קובץ {response_file} לא נמצא", "ERROR")
            return
        
        print(f"\n📅 מעבד תגובת Claude: {response_file}")
        
        try:
            # עיבוד התגובה
            events_created = self.system.process_claude_response(response_file)
            
            if events_created > 0:
                print(f"\n🎉 הצלחה! נוצרו {events_created} אירועים ביומן timebro")
                print(f"📅 בדוק את היומן שלך ב-Google Calendar")
            else:
                print(f"\n⚠️ לא נוצרו אירועים חדשים")
                print(f"💡 ייתכן שכל האירועים כבר קיימים או שהיו שגיאות בנתונים")
                
        except Exception as e:
            self.log(f"שגיאה בעיבוד תגובת Claude: {e}", "ERROR")

    def quick_sync(self):
        """סינכרון מהיר של WhatsApp"""
        print(f"\n🔄 מבצע סינכרון מהיר של WhatsApp...")
        
        try:
            self.system.sync_whatsapp_messages()
            self.log("✅ סינכרון הושלם", "SUCCESS")
        except Exception as e:
            self.log(f"שגיאה בסינכרון: {e}", "ERROR")

    def status_check(self):
        """בדיקת מצב המערכת"""
        print(f"\n📊 בדיקת מצב מערכת TimeBro Calendar")
        print("="*50)
        
        # בדיקת קבצים חיוניים
        required_files = [
            'timebro_calendar_system.py',
            'whatsapp_web_js_client.js',
            'whatsapp_messages_webjs.db',
            'whatsapp_contacts.db'
        ]
        
        for file in required_files:
            if os.path.exists(file):
                print(f"✅ {file}")
            else:
                print(f"❌ {file} חסר")
        
        # בדיקת WhatsApp Client
        import subprocess
        try:
            result = subprocess.run(['pgrep', '-f', 'whatsapp_web_js_client.js'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print(f"✅ WhatsApp Client רץ (PID: {result.stdout.strip()})")
            else:
                print(f"❌ WhatsApp Client לא רץ")
                print(f"💡 הפעל: node whatsapp_web_js_client.js")
        except:
            print(f"❌ שגיאה בבדיקת WhatsApp Client")
        
        # בדיקת מסדי נתונים
        try:
            import sqlite3
            conn = sqlite3.connect(self.system.db_main)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages")
            message_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"📊 {message_count:,} הודעות במסד הנתונים")
            
        except Exception as e:
            print(f"❌ שגיאה בבדיקת מסד הנתונים: {e}")
        
        print("="*50)

def main():
    import sys
    
    updater = ManualCalendarUpdate()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--process-claude' and len(sys.argv) > 2:
            # עיבוד תגובת Claude
            updater.process_claude_response(sys.argv[2])
        elif sys.argv[1] == '--sync':
            # סינכרון מהיר
            updater.quick_sync()
        elif sys.argv[1] == '--status':
            # בדיקת מצב
            updater.status_check()
        else:
            print("❌ פרמטר לא ידוע")
            print("שימוש:")
            print("  python3 manual_calendar_update.py                    # תהליך מלא")
            print("  python3 manual_calendar_update.py --process-claude <file>  # עיבוד תגובת Claude")
            print("  python3 manual_calendar_update.py --sync             # סינכרון מהיר")
            print("  python3 manual_calendar_update.py --status           # בדיקת מצב")
    else:
        # תהליך מלא
        updater.manual_full_process()

if __name__ == "__main__":
    main()













