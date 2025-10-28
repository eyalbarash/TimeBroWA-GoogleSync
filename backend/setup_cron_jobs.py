#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הגדרת Cron Jobs למערכת TimeBro Calendar
- סינכרון שעתי של WhatsApp (כל השיחות)
- עיבוד יומן שבועי במוצאי שבת
"""

import os
import subprocess
from datetime import datetime

class CronJobsSetup:
    def __init__(self):
        self.project_path = os.getcwd()
        self.python_path = subprocess.check_output(['which', 'python3']).decode().strip()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emoji = "⚙️" if level == "INFO" else "✅" if level == "SUCCESS" else "❌"
        print(f"[{timestamp}] {emoji} {message}")

    def create_cron_scripts(self):
        """יצירת סקריפטים לcron jobs"""
        
        # סקריפט סינכרון שעתי
        hourly_script = f"""#!/bin/bash
# TimeBro - Hourly WhatsApp Sync
# רץ כל שעה לסינכרון כל השיחות בוואטסאפ

cd "{self.project_path}"

# לוג התחלה
echo "[$(date)] 🔄 Starting hourly WhatsApp sync..." >> timebro_cron.log

# הפעלת סינכרון WhatsApp
{self.python_path} -c "
import sys
sys.path.append('{self.project_path}')
from timebro_calendar_system import TimeBroCalendarSystem
system = TimeBroCalendarSystem()
system.sync_whatsapp_messages()
" >> timebro_cron.log 2>&1

# לוג סיום
echo "[$(date)] ✅ Hourly sync completed" >> timebro_cron.log
"""

        # סקריפט עיבוד יומן שבועי
        weekly_script = f"""#!/bin/bash
# TimeBro - Weekly Calendar Processing
# רץ כל מוצאי שבת לעיבוד אירועי יומן

cd "{self.project_path}"

# לוג התחלה
echo "[$(date)] 📅 Starting weekly calendar processing..." >> timebro_cron.log

# הפעלת עיבוד יומן שבועי
{self.python_path} -c "
import sys
sys.path.append('{self.project_path}')
from timebro_calendar_system import TimeBroCalendarSystem
system = TimeBroCalendarSystem()
system.weekly_calendar_process()
" >> timebro_cron.log 2>&1

# לוג סיום
echo "[$(date)] ✅ Weekly calendar processing completed" >> timebro_cron.log
"""

        # שמירת הסקריפטים
        with open('timebro_hourly_sync.sh', 'w') as f:
            f.write(hourly_script)
        
        with open('timebro_weekly_calendar.sh', 'w') as f:
            f.write(weekly_script)
        
        # הפיכה לניתנים להרצה
        os.chmod('timebro_hourly_sync.sh', 0o755)
        os.chmod('timebro_weekly_calendar.sh', 0o755)
        
        self.log("✅ סקריפטי cron נוצרו", "SUCCESS")

    def setup_cron_jobs(self):
        """הגדרת cron jobs במערכת"""
        
        cron_entries = f"""
# TimeBro Calendar System - Automated Jobs
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Hourly WhatsApp sync (all conversations)
# רץ כל שעה ב-7 דקות (למניעת עומס בתחילת השעה)
7 * * * * {self.project_path}/timebro_hourly_sync.sh

# Weekly calendar processing (Saturday night)
# רץ כל מוצאי שבת בשעה 21:00
0 21 * * 6 {self.project_path}/timebro_weekly_calendar.sh

# System health check (daily at 8 AM)
# בדיקת בריאות המערכת כל יום בשעה 8 בבוקר
0 8 * * * {self.python_path} {self.project_path}/timebro_calendar_system.py >> {self.project_path}/timebro_health.log 2>&1

"""
        
        # שמירת crontab החדש
        cron_file = 'timebro_crontab.txt'
        with open(cron_file, 'w') as f:
            f.write(cron_entries.strip())
        
        self.log(f"✅ קובץ crontab נוצר: {cron_file}")
        
        return cron_file

    def install_cron_jobs(self):
        """התקנת cron jobs במערכת"""
        try:
            # יצירת הסקריפטים
            self.create_cron_scripts()
            
            # הגדרת cron jobs
            cron_file = self.setup_cron_jobs()
            
            # קריאת crontab נוכחי
            try:
                current_cron = subprocess.check_output(['crontab', '-l'], 
                                                     stderr=subprocess.DEVNULL).decode()
            except subprocess.CalledProcessError:
                current_cron = ""
            
            # הוספת הjobs החדשים
            with open(cron_file, 'r') as f:
                new_cron_entries = f.read()
            
            # בדיקה אם כבר קיימים
            if 'TimeBro Calendar System' in current_cron:
                self.log("⚠️ Cron jobs של TimeBro כבר קיימים")
                print("\n🔧 כדי לעדכן, הרץ:")
                print(f"crontab -e")
                print("והחלף את הרשומות הקיימות עם:")
                print(new_cron_entries)
            else:
                # הוספה לcrontab
                full_cron = current_cron + "\n" + new_cron_entries
                
                # כתיבה לקובץ זמני
                temp_cron = 'temp_crontab.txt'
                with open(temp_cron, 'w') as f:
                    f.write(full_cron)
                
                # התקנה
                subprocess.run(['crontab', temp_cron], check=True)
                os.remove(temp_cron)
                
                self.log("✅ Cron jobs הותקנו בהצלחה!", "SUCCESS")
            
            # יצירת הוראות שימוש
            self.create_usage_instructions()
            
        except Exception as e:
            self.log(f"שגיאה בהתקנת cron jobs: {e}", "ERROR")
            print(f"\n🔧 התקנה ידנית:")
            print(f"1. crontab -e")
            print(f"2. הוסף את התוכן מקובץ: {cron_file}")

    def create_usage_instructions(self):
        """יצירת הוראות שימוש"""
        instructions = f"""
# 📅 TimeBro Calendar System - הוראות שימוש

## 🚀 מה הותקן:

### 1. סינכרון שעתי (כל השיחות בוואטסאפ)
- **מתי**: כל שעה ב-7 דקות
- **מה**: סינכרון כל השיחות והקבוצות מוואטסאפ
- **סקריפט**: timebro_hourly_sync.sh

### 2. עיבוד יומן שבועי
- **מתי**: כל מוצאי שבת בשעה 21:00
- **מה**: חילוץ אירועי יומן מהשבוע שחלף ושליחה לClaude
- **סקריפט**: timebro_weekly_calendar.sh

### 3. בדיקת בריאות יומית
- **מתי**: כל יום בשעה 8:00
- **מה**: בדיקת מצב המערכת וסטטיסטיקות

## 🔧 פקודות שימושיות:

### הצגת cron jobs פעילים:
```bash
crontab -l
```

### הפעלה ידנית של סינכרון:
```bash
cd "{self.project_path}"
./timebro_hourly_sync.sh
```

### הפעלה ידנית של עיבוד יומן:
```bash
cd "{self.project_path}"
./timebro_weekly_calendar.sh
```

### צפייה בלוגים:
```bash
tail -f {self.project_path}/timebro_cron.log
tail -f {self.project_path}/timebro_health.log
```

### הפעלה ידנית של המערכת:
```bash
cd "{self.project_path}"
python3 timebro_calendar_system.py
```

## 📋 תהליך שבועי:

1. **אוטומטי כל מוצאי שבת**:
   - המערכת מחלצת הודעות מהשבוע שחלף
   - יוצרת קובץ נתונים לClaude
   - שומרת בקובץ: weekly_claude_data_YYYYMMDD_HHMMSS.json

2. **פעולה ידנית נדרשת**:
   - שלח את הקובץ ל-Claude עם הפרומפט
   - שמור את תגובת Claude בקובץ JSON
   - הרץ: python3 -c "from timebro_calendar_system import TimeBroCalendarSystem; TimeBroCalendarSystem().process_claude_response('claude_response.json')"

## 🎯 יומן timebro:
- כל האירועים נכנסים ליומן **timebro** בלבד
- אינטגרציה אוטומטית עם Google Calendar
- תזכורות אוטומטיות: 15 דקות (popup) + 60 דקות (email)

## 🔍 פתרון בעיות:

### אם הסינכרון לא עובד:
```bash
# בדיקה אם WhatsApp Client רץ
pgrep -f whatsapp_web_js_client.js

# הפעלה ידנית
node whatsapp_web_js_client.js
```

### אם יש שגיאות בcron:
```bash
# צפייה בלוג המערכת
sudo tail -f /var/log/system.log | grep cron
```

### עדכון הגדרות:
```bash
# עריכת cron jobs
crontab -e

# הפעלה מחדש של המערכת
cd "{self.project_path}"
python3 setup_cron_jobs.py
```

📞 **תמיכה**: כל הלוגים נשמרים ב-{self.project_path}/timebro_cron.log
"""

        with open('TIMEBRO_USAGE_GUIDE.md', 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        self.log("✅ מדריך שימוש נוצר: TIMEBRO_USAGE_GUIDE.md", "SUCCESS")

    def check_system_status(self):
        """בדיקת מצב המערכת"""
        print('\n' + '='*70)
        print('📊 TimeBro Calendar System - מצב המערכת')
        print('='*70)
        
        # בדיקת cron jobs
        try:
            cron_output = subprocess.check_output(['crontab', '-l']).decode()
            if 'TimeBro' in cron_output:
                print('✅ Cron jobs פעילים')
            else:
                print('❌ Cron jobs לא מותקנים')
        except:
            print('❌ שגיאה בבדיקת cron jobs')
        
        # בדיקת קבצים
        required_files = [
            'timebro_calendar_system.py',
            'timebro_hourly_sync.sh',
            'timebro_weekly_calendar.sh',
            'whatsapp_web_js_client.js'
        ]
        
        for file in required_files:
            if os.path.exists(file):
                print(f'✅ {file}')
            else:
                print(f'❌ {file} חסר')
        
        # בדיקת WhatsApp Client
        try:
            result = subprocess.run(['pgrep', '-f', 'whatsapp_web_js_client.js'], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                print('✅ WhatsApp Client רץ')
            else:
                print('⚠️ WhatsApp Client לא רץ')
        except:
            print('❌ שגיאה בבדיקת WhatsApp Client')
        
        print('='*70)

def main():
    setup = CronJobsSetup()
    
    print("🚀 מתקין מערכת TimeBro Calendar עם Cron Jobs")
    print("="*60)
    
    # התקנת cron jobs
    setup.install_cron_jobs()
    
    # בדיקת מצב
    setup.check_system_status()
    
    print(f"\n🎉 התקנה הושלמה!")
    print(f"📋 עיין במדריך: TIMEBRO_USAGE_GUIDE.md")
    print(f"📊 צפה בלוגים: tail -f timebro_cron.log")

if __name__ == "__main__":
    main()