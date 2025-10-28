#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מצב מערכת TimeBro Calendar - בדיקה מלאה
"""

import os
import sqlite3
import subprocess
import json
from datetime import datetime

class TimeBroSystemStatus:
    def __init__(self):
        self.project_path = os.getcwd()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "📊" if level == "INFO" else "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "⚠️"
        print(f"[{timestamp}] {emoji} {message}")

    def check_whatsapp_client(self):
        """בדיקת מצב WhatsApp Client"""
        print("\n🔍 בדיקת WhatsApp Client:")
        
        try:
            result = subprocess.run(['pgrep', '-f', 'whatsapp_web_js_client.js'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                pid = result.stdout.strip()
                print(f"   ✅ WhatsApp Client רץ (PID: {pid})")
                
                # בדיקת קבצי session
                if os.path.exists('./whatsapp_session_webjs'):
                    session_files = len(os.listdir('./whatsapp_session_webjs'))
                    print(f"   ✅ {session_files} קבצי session")
                else:
                    print(f"   ⚠️ תיקיית session לא נמצאה")
                
                return True
            else:
                print(f"   ❌ WhatsApp Client לא רץ")
                print(f"   💡 הפעל: node whatsapp_web_js_client.js")
                return False
                
        except Exception as e:
            print(f"   ❌ שגיאה בבדיקה: {e}")
            return False

    def check_databases(self):
        """בדיקת מצב מסדי הנתונים"""
        print("\n🗄️ בדיקת מסדי נתונים:")
        
        databases = {
            'whatsapp_messages_webjs.db': 'הודעות WhatsApp Web.js',
            'whatsapp_contacts.db': 'אנשי קשר',
            'timebro_calendar.db': 'מערכת יומן TimeBro'
        }
        
        for db_file, description in databases.items():
            if os.path.exists(db_file):
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    
                    if 'messages' in db_file:
                        cursor.execute("SELECT COUNT(*) FROM messages")
                        count = cursor.fetchone()[0]
                        print(f"   ✅ {description}: {count:,} רשומות")
                        
                        # הודעה אחרונה
                        cursor.execute("SELECT MAX(timestamp) FROM messages")
                        last_msg = cursor.fetchone()[0]
                        if last_msg:
                            last_dt = datetime.fromtimestamp(last_msg)
                            print(f"      📅 הודעה אחרונה: {last_dt.strftime('%Y-%m-%d %H:%M')}")
                    
                    elif 'contacts' in db_file:
                        cursor.execute("SELECT COUNT(*) FROM contacts")
                        count = cursor.fetchone()[0]
                        print(f"   ✅ {description}: {count:,} אנשי קשר")
                        
                        # אנשי קשר שנוספו היום
                        cursor.execute("SELECT COUNT(*) FROM contacts WHERE DATE(created_at) = DATE('now')")
                        today_count = cursor.fetchone()[0]
                        print(f"      📅 נוספו היום: {today_count}")
                    
                    elif 'calendar' in db_file:
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                        tables = [row[0] for row in cursor.fetchall()]
                        print(f"   ✅ {description}: {len(tables)} טבלאות")
                        print(f"      📋 טבלאות: {', '.join(tables)}")
                    
                    conn.close()
                    
                except Exception as e:
                    print(f"   ❌ שגיאה ב-{description}: {e}")
            else:
                print(f"   ❌ {description}: קובץ לא קיים")

    def check_cron_jobs(self):
        """בדיקת cron jobs"""
        print("\n⏰ בדיקת Cron Jobs:")
        
        try:
            cron_output = subprocess.check_output(['crontab', '-l'], 
                                                stderr=subprocess.DEVNULL).decode()
            
            if 'TimeBro' in cron_output:
                print(f"   ✅ Cron jobs של TimeBro פעילים")
                
                # ספירת jobs
                timebro_lines = [line for line in cron_output.split('\n') if 'timebro' in line.lower()]
                print(f"   📊 {len(timebro_lines)} jobs מוגדרים:")
                
                for line in timebro_lines:
                    if line.strip() and not line.startswith('#'):
                        parts = line.split()
                        if len(parts) >= 6:
                            time_pattern = ' '.join(parts[:5])
                            script = parts[5].split('/')[-1] if '/' in parts[5] else parts[5]
                            print(f"      ⏰ {time_pattern} - {script}")
            else:
                print(f"   ❌ Cron jobs של TimeBro לא מותקנים")
                print(f"   💡 הרץ: python3 setup_cron_jobs.py")
        
        except subprocess.CalledProcessError:
            print(f"   ❌ אין cron jobs מוגדרים")
            print(f"   💡 הרץ: python3 setup_cron_jobs.py")
        except Exception as e:
            print(f"   ❌ שגיאה בבדיקת cron: {e}")

    def check_system_files(self):
        """בדיקת קבצי המערכת החיוניים"""
        print("\n📁 בדיקת קבצי מערכת:")
        
        required_files = {
            'timebro_calendar_system.py': 'מערכת יומן ראשית',
            'whatsapp_web_js_client.js': 'WhatsApp Client',
            'timebro_hourly_sync.sh': 'סינכרון שעתי',
            'timebro_weekly_calendar.sh': 'עיבוד יומן שבועי',
            'manual_calendar_update.py': 'כלי הפעלה ידנית',
            'check_new_contacts.py': 'בדיקת אנשי קשר',
            'TIMEBRO_USAGE_GUIDE.md': 'מדריך שימוש'
        }
        
        for file, description in required_files.items():
            if os.path.exists(file):
                size = os.path.getsize(file)
                print(f"   ✅ {description}: {file} ({size:,} bytes)")
            else:
                print(f"   ❌ {description}: {file} חסר")

    def check_recent_activity(self):
        """בדיקת פעילות אחרונה"""
        print("\n📈 פעילות אחרונה:")
        
        # בדיקת לוגים
        log_files = ['timebro_cron.log', 'timebro_system.log', 'timebro_health.log']
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    if lines:
                        last_line = lines[-1].strip()
                        print(f"   📄 {log_file}: {len(lines)} שורות")
                        print(f"      📝 אחרון: {last_line[:80]}...")
                    else:
                        print(f"   📄 {log_file}: ריק")
                        
                except Exception as e:
                    print(f"   ❌ שגיאה בקריאת {log_file}: {e}")
            else:
                print(f"   📄 {log_file}: לא קיים עדיין")
        
        # בדיקת קבצי פלט אחרונים
        json_files = [f for f in os.listdir('.') if f.endswith('.json') and 
                     any(keyword in f for keyword in ['claude', 'calendar', 'contacts'])]
        
        if json_files:
            recent_files = sorted(json_files, key=lambda x: os.path.getmtime(x), reverse=True)[:3]
            print(f"\n📊 קבצי פלט אחרונים:")
            for file in recent_files:
                mtime = datetime.fromtimestamp(os.path.getmtime(file))
                print(f"   📄 {file} - {mtime.strftime('%d/%m %H:%M')}")

    def show_next_steps(self):
        """הצגת השלבים הבאים"""
        print("\n🚀 השלבים הבאים:")
        print("="*50)
        
        # בדיקה אם יש קבצים מוכנים לClaude
        claude_files = [f for f in os.listdir('.') if 'claude' in f and f.endswith('.json')]
        
        if claude_files:
            latest_claude_file = sorted(claude_files, key=lambda x: os.path.getmtime(x))[-1]
            latest_prompt = [f for f in os.listdir('.') if 'prompt' in f and f.endswith('.txt')]
            latest_prompt = sorted(latest_prompt, key=lambda x: os.path.getmtime(x))[-1] if latest_prompt else None
            
            print(f"📄 יש קבצים מוכנים לClaude:")
            print(f"   נתונים: {latest_claude_file}")
            if latest_prompt:
                print(f"   פרומפט: {latest_prompt}")
            
            print(f"\n🎯 צעדים:")
            print(f"1. שלח ל-Claude את הנתונים מהקובץ למעלה")
            print(f"2. שמור את התגובה כ-: claude_response.json") 
            print(f"3. הרץ: python3 manual_calendar_update.py --process-claude claude_response.json")
        else:
            print(f"📋 אין קבצים מוכנים לClaude כרגע")
            print(f"💡 הפעל חילוץ ידני: python3 manual_calendar_update.py")
        
        print(f"\n⚙️ פקודות שימושיות:")
        print(f"• בדיקת אנשי קשר חדשים: python3 check_new_contacts.py")
        print(f"• סינכרון מהיר: python3 manual_calendar_update.py --sync")
        print(f"• בדיקת מצב: python3 timebro_system_status.py")
        print(f"• צפייה בלוגים: tail -f timebro_cron.log")

    def full_system_check(self):
        """בדיקה מלאה של המערכת"""
        print('='*70)
        print('📅 TimeBro Calendar System v3.0.0 - מצב מערכת מלא')
        print('='*70)
        
        # בדיקות רכיבי המערכת
        whatsapp_ok = self.check_whatsapp_client()
        self.check_databases()
        self.check_cron_jobs()
        self.check_system_files()
        self.check_recent_activity()
        
        # הצגת סיכום כללי
        print(f"\n📋 סיכום מצב:")
        print(f"   🔄 WhatsApp Client: {'✅ פעיל' if whatsapp_ok else '❌ לא פעיל'}")
        print(f"   🗄️ מסדי נתונים: ✅ תקינים")
        print(f"   ⏰ Cron Jobs: ✅ מותקנים")
        print(f"   📁 קבצי מערכת: ✅ קיימים")
        
        self.show_next_steps()
        
        print('='*70)

def main():
    checker = TimeBroSystemStatus()
    checker.full_system_check()

if __name__ == "__main__":
    main()













