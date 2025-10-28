#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ניקוי וסידור פרויקט TimeBro Calendar
מחיקת קבצים לא נחוצים, ארגון מחדש
"""

import os
import shutil
import json
from datetime import datetime

class ProjectCleanup:
    def __init__(self):
        self.project_path = "/Users/eyalbarash/Local Development/GreenAPI_MCP_972549990001"
        
        # קבצים חיוניים שצריך לשמור
        self.essential_files = {
            # Core system files
            'whatsapp_web_js_client.js',
            'timebro_calendar_system.py',
            'contacts_list.py',
            
            # Main databases
            'whatsapp_messages_webjs.db',
            'whatsapp_contacts.db',
            'timebro_calendar.db',
            'whatsapp_messages.db',  # יש נתוני אוגוסט חשובים
            
            # Automation scripts
            'fully_automated_timebro.py',
            'daily_timebro_updater.py',
            'fix_calendar_issues.py',
            
            # Cron jobs
            'timebro_hourly_sync.sh',
            'timebro_weekly_calendar.sh',
            'timebro_daily_update.sh',
            'setup_cron_jobs.py',
            
            # Configuration and credentials
            'token.json',
            'credentials.json',
            'package.json',
            'package-lock.json',
            
            # Documentation
            'TIMEBRO_USAGE_GUIDE.md',
            'AUTOMATION_COMPLETE_SUMMARY.md',
            'contacts_list.py',
            
            # Session data
            'whatsapp_session_webjs',
            '.wwebjs_auth',
            '.wwebjs_cache'
        }
        
        # קבצים לארכיון (לא למחיקה)
        self.archive_patterns = [
            'mike_august_*',
            'automation_report_*',
            'JONI_Contacts.*'
        ]

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        elif level == "WARNING":
            emoji = "⚠️"
        else:
            emoji = "🧹"
        print(f"[{timestamp}] {emoji} {message}")

    def identify_files_to_remove(self):
        """זיהוי קבצים למחיקה"""
        files_to_remove = []
        files_to_archive = []
        
        for root, dirs, files in os.walk(self.project_path):
            # דילוג על תיקיות מיוחדות
            dirs[:] = [d for d in dirs if d not in ['node_modules', '.git', '__pycache__', 'venv']]
            
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, self.project_path)
                
                # בדיקה אם קובץ חיוני
                if any(essential in relative_path for essential in self.essential_files):
                    continue
                
                # בדיקה אם לארכיון
                should_archive = any(
                    file.startswith(pattern.replace('*', '')) 
                    for pattern in self.archive_patterns
                )
                
                if should_archive:
                    files_to_archive.append(relative_path)
                elif self.should_remove_file(file, relative_path):
                    files_to_remove.append(relative_path)
        
        return files_to_remove, files_to_archive

    def should_remove_file(self, filename, relative_path):
        """קביעה אם קובץ צריך להימחק"""
        # קבצי temp ו-debug
        temp_patterns = [
            'debug_', 'temp_', 'test_', 'quick_', 'simple_',
            '_temp', '_debug', '_test', '_old',
            'extraction_plan_', 'claude_prompt_', 'claude_usage_',
            'weekly_claude_', 'claude_calendar_extraction'
        ]
        
        # קבצי דוחות ישנים
        old_reports = [
            'extract_', 'found_contacts_', 'comprehensive_',
            'regular_chrome_', 'selenium_extraction',
            'whatsapp_structure_', 'calendar_cleanup_',
            'calendar_sync_report_', 'call_events_cleanup'
        ]
        
        # קבצי JavaScript לא נחוצים
        unused_js = [
            'advanced_whatsapp_', 'connect_', 'direct_',
            'improved_whatsapp_', 'final_whatsapp_',
            'whatsapp_august_', 'continue_august_',
            'final_august_', 'use_existing_'
        ]
        
        # בדיקות
        if any(pattern in filename for pattern in temp_patterns + old_reports + unused_js):
            return True
        
        # קבצי JSON זמניים (לא mike_august או automation_report)
        if (filename.endswith('.json') and 
            not filename.startswith('mike_august') and 
            not filename.startswith('automation_report') and
            not filename.startswith('JONI_Contacts')):
            return True
        
        # קבצי CSV זמניים
        if filename.endswith('.csv') and not filename.startswith('JONI_Contacts'):
            return True
        
        # קבצי txt זמניים
        if filename.endswith('.txt') and filename not in ['requirements.txt', 'env_template.txt']:
            return True
        
        return False

    def create_archive_folder(self, files_to_archive):
        """יצירת תיקיית ארכיון"""
        if not files_to_archive:
            return
        
        archive_folder = 'archive_backup'
        if not os.path.exists(archive_folder):
            os.makedirs(archive_folder)
        
        for file_path in files_to_archive:
            try:
                src = file_path
                dst = os.path.join(archive_folder, os.path.basename(file_path))
                shutil.move(src, dst)
                self.log(f"📦 הועבר לארכיון: {file_path}")
            except Exception as e:
                self.log(f"שגיאה בהעברה לארכיון {file_path}: {e}", "ERROR")

    def remove_unnecessary_files(self, files_to_remove):
        """מחיקת קבצים לא נחוצים"""
        removed_count = 0
        
        for file_path in files_to_remove:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    removed_count += 1
                    if removed_count <= 10:  # הצגת 10 ראשונים
                        self.log(f"🗑️ נמחק: {file_path}")
            except Exception as e:
                self.log(f"שגיאה במחיקת {file_path}: {e}", "ERROR")
        
        if removed_count > 10:
            self.log(f"🗑️ ... ועוד {removed_count - 10} קבצים נמחקו")
        
        return removed_count

    def create_project_structure(self):
        """יצירת מבנה פרויקט מסודר"""
        folders_to_create = [
            'logs',
            'config', 
            'scripts',
            'archive_backup'
        ]
        
        for folder in folders_to_create:
            if not os.path.exists(folder):
                os.makedirs(folder)
                self.log(f"📁 נוצרה תיקייה: {folder}")

    def run_cleanup(self):
        """הרצת ניקוי מלא"""
        print('\n' + '='*80)
        print('🧹 ניקוי וסידור פרויקט TimeBro Calendar')
        print('='*80)
        
        try:
            # 1. זיהוי קבצים
            self.log("זיהוי קבצים למחיקה וארכיון...")
            files_to_remove, files_to_archive = self.identify_files_to_remove()
            
            self.log(f"נמצאו {len(files_to_remove)} קבצים למחיקה")
            self.log(f"נמצאו {len(files_to_archive)} קבצים לארכיון")
            
            # 2. יצירת מבנה תיקיות
            self.create_project_structure()
            
            # 3. העברה לארכיון
            self.create_archive_folder(files_to_archive)
            
            # 4. מחיקת קבצים לא נחוצים
            removed_count = self.remove_unnecessary_files(files_to_remove)
            
            # 5. סיכום
            print(f'\n📊 סיכום ניקוי:')
            print(f'   🗑️ קבצים נמחקו: {removed_count}')
            print(f'   📦 קבצים בארכיון: {len(files_to_archive)}')
            print(f'   📁 תיקיות נוצרו: 4')
            print(f'   ✅ פרויקט מסודר ונקי')
            
        except Exception as e:
            self.log(f"שגיאה בניקוי: {e}", "ERROR")

def main():
    cleanup = ProjectCleanup()
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()













