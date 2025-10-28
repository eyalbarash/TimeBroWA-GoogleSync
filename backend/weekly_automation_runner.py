#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
רץ אוטומטית כל מוצאי שבת - מעבד את השבוע שחלף ומכניס ליומן timebro
"""

import os
import json
from datetime import datetime, timedelta
from full_automation_timebro import FullTimeBroAutomation
from timebro_calendar_system import TimeBroCalendarSystem

class WeeklyAutomationRunner:
    def __init__(self):
        self.system = TimeBroCalendarSystem()
        self.automation = FullTimeBroAutomation()
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        emoji = "📅" if level == "INFO" else "✅" if level == "SUCCESS" else "❌"
        log_entry = f"[{timestamp}] {emoji} {message}"
        print(log_entry)
        
        # שמירה בלוג מוצאי שבת
        with open('weekly_automation.log', 'a', encoding='utf-8') as f:
            f.write(f"{log_entry}\n")

    def run_weekly_process(self):
        """תהליך מוצאי שבת מלא"""
        print('\n' + '='*80)
        print('🌟 TimeBro Calendar - תהליך מוצאי שבת אוטומטי')
        print('='*80)
        
        try:
            # 1. חילוץ נתוני השבוע שחלף
            self.log("שלב 1: חילוץ נתוני השבוע שחלף...")
            weekly_data = self.system.extract_weekly_calendar_data()
            
            if not weekly_data:
                self.log("אין נתונים לעיבוד השבוע", "ERROR")
                return
            
            # 2. שמירת הנתונים
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            weekly_file = f"weekly_calendar_data_{timestamp}.json"
            
            with open(weekly_file, 'w', encoding='utf-8') as f:
                json.dump(weekly_data, f, ensure_ascii=False, indent=2)
            
            self.log(f"✅ נתוני השבוע נשמרו: {weekly_file}")
            
            # 3. הפעלת אוטומציה על הנתונים
            self.log("שלב 2: הפעלת אוטומציה על נתוני השבוע...")
            events, csv_file = self.automation.run_full_automation(weekly_file)
            
            if events and csv_file:
                # 4. רישום הצלחה
                self.log(f"✅ נוצרו {len(events)} אירועים מהשבוע שחלף", "SUCCESS")
                
                # 5. עדכון מעקב במסד
                self.system.update_sync_tracking('weekly_automation', 'completed', 
                                               events_created=len(events))
                
                # 6. יצירת סיכום שבועי
                self.create_weekly_summary(events, csv_file, weekly_file)
                
            else:
                self.log("לא נוצרו אירועים השבוע", "ERROR")
                
        except Exception as e:
            self.log(f"שגיאה בתהליך שבועי: {e}", "ERROR")

    def create_weekly_summary(self, events, csv_file, data_file):
        """יצירת סיכום שבועי"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = f"weekly_summary_{timestamp}.json"
        
        # חישוב תאריכי השבוע
        today = datetime.now()
        last_saturday = today - timedelta(days=(today.weekday() + 1) % 7 + 1)
        week_start = last_saturday - timedelta(days=6)
        
        summary = {
            'week_period': {
                'start': week_start.strftime('%Y-%m-%d'),
                'end': last_saturday.strftime('%Y-%m-%d'),
                'processed_at': datetime.now().isoformat()
            },
            'automation_results': {
                'total_events_created': len(events),
                'events_by_priority': {},
                'events_by_category': {},
                'main_contacts': {}
            },
            'files_created': {
                'data_file': data_file,
                'csv_file': csv_file,
                'summary_file': summary_file
            },
            'next_run': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d 21:00')
        }
        
        # סטטיסטיקות
        for event in events:
            # לפי עדיפות
            priority = event['priority']
            summary['automation_results']['events_by_priority'][priority] = \
                summary['automation_results']['events_by_priority'].get(priority, 0) + 1
            
            # לפי קטגוריה
            category = event['category']
            summary['automation_results']['events_by_category'][category] = \
                summary['automation_results']['events_by_category'].get(category, 0) + 1
            
            # לפי איש קשר
            contact = event['contact_source']
            summary['automation_results']['main_contacts'][contact] = \
                summary['automation_results']['main_contacts'].get(contact, 0) + 1
        
        # שמירת הסיכום
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        self.log(f"✅ סיכום שבועי נוצר: {summary_file}")
        
        return summary_file

def main():
    """הפעלה שבועית אוטומטית"""
    runner = WeeklyAutomationRunner()
    runner.run_weekly_process()

if __name__ == "__main__":
    main()













