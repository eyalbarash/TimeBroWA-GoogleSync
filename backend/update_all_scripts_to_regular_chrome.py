#!/usr/bin/env python3
"""
Update All Scripts to Use Regular Chrome
עדכון כל הסקריפטים לשימוש ב-Chrome רגיל
"""

import os
import re
from datetime import datetime

class UpdateAllScriptsToRegularChrome:
    def __init__(self):
        self.project_dir = "/Users/eyalbarash/Local Development/GreenAPI_MCP_972549990001"
        self.updated_files = []
        self.errors = []
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "ℹ️"
        print(f"[{timestamp}] {emoji} {message}")

    def find_files_to_update(self):
        """מציאת קבצים שצריכים עדכון"""
        files_to_update = []
        
        # קבצי Python
        python_files = [
            "whatsapp_web_scraper_selenium.py",
            "comprehensive_chat_updater.py",
            "check_actual_whatsapp_list.py",
            "extract_found_contacts_messages.py",
            "download_all_requested_chats.py"
        ]
        
        # קבצי JavaScript
        js_files = [
            "direct_devtools_extractor.js",
            "simple_tab_reader.js",
            "extract_from_specific_tab.js",
            "connect_existing_whatsapp.js"
        ]
        
        all_files = python_files + js_files
        
        for filename in all_files:
            filepath = os.path.join(self.project_dir, filename)
            if os.path.exists(filepath):
                files_to_update.append(filepath)
        
        self.log(f"נמצאו {len(files_to_update)} קבצים לעדכון")
        return files_to_update

    def update_python_file(self, filepath):
        """עדכון קובץ Python"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # עדכון פורט מ-9223 ל-9222
            content = content.replace('9223', '9222')
            content = content.replace('localhost:9223', 'localhost:9222')
            
            # עדכון הערות ותיאורים
            content = content.replace('Chrome for Testing', 'Chrome רגיל')
            content = content.replace('chrome for testing', 'chrome רגיל')
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.updated_files.append(filepath)
                self.log(f"עודכן: {os.path.basename(filepath)}")
                return True
            else:
                self.log(f"לא נדרש עדכון: {os.path.basename(filepath)}")
                return False
                
        except Exception as e:
            self.log(f"שגיאה בעדכון {filepath}: {str(e)}", "ERROR")
            self.errors.append(f"{filepath}: {str(e)}")
            return False

    def update_javascript_file(self, filepath):
        """עדכון קובץ JavaScript"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # עדכון פורט מ-9223 ל-9222
            content = content.replace('9223', '9222')
            content = content.replace('localhost:9223', 'localhost:9222')
            
            # עדכון הערות
            content = content.replace('Chrome for Testing', 'Chrome רגיל')
            content = content.replace('chrome for testing', 'chrome רגיל')
            
            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.updated_files.append(filepath)
                self.log(f"עודכן: {os.path.basename(filepath)}")
                return True
            else:
                self.log(f"לא נדרש עדכון: {os.path.basename(filepath)}")
                return False
                
        except Exception as e:
            self.log(f"שגיאה בעדכון {filepath}: {str(e)}", "ERROR")
            self.errors.append(f"{filepath}: {str(e)}")
            return False

    def update_all_files(self):
        """עדכון כל הקבצים"""
        self.log("מתחיל עדכון כל הקבצים ל-Chrome רגיל...")
        
        files_to_update = self.find_files_to_update()
        
        for filepath in files_to_update:
            filename = os.path.basename(filepath)
            
            if filename.endswith('.py'):
                self.update_python_file(filepath)
            elif filename.endswith('.js'):
                self.update_javascript_file(filepath)
        
        self.log(f"עדכון הושלם: {len(self.updated_files)} קבצים עודכנו", "SUCCESS")
        
        if self.errors:
            self.log(f"שגיאות: {len(self.errors)} קבצים", "ERROR")
            for error in self.errors:
                print(f"   ❌ {error}")

    def update_memory_reference(self):
        """עדכון הפניות בזכרון המערכת"""
        self.log("מעדכן הפניות בזכרון המערכת...")
        
        memory_updates = {
            "browser_port": "9222",
            "chrome_type": "regular_chrome",
            "whatsapp_tab_id": "424925248DE7A7B18A19DA5F5F2D4B40",
            "debugging_address": "localhost:9222",
            "browser_path": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        }
        
        # שמירת הגדרות חדשות
        config_file = os.path.join(self.project_dir, "chrome_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(memory_updates, f, ensure_ascii=False, indent=2)
        
        self.log("הגדרות Chrome רגיל נשמרו", "SUCCESS")

    def generate_update_report(self):
        """יצירת דוח עדכון"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "update_type": "chrome_migration",
            "from_port": "9223 (Chrome for Testing)",
            "to_port": "9222 (Regular Chrome)",
            "files_updated": [os.path.basename(f) for f in self.updated_files],
            "errors": self.errors,
            "whatsapp_status": "ready_on_regular_chrome"
        }
        
        report_file = f"chrome_update_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print("\n📊 דוח עדכון ל-Chrome רגיל")
        print("=" * 50)
        print(f"🔄 עדכון: Chrome for Testing → Chrome רגיל")
        print(f"🌐 פורט: 9223 → 9222")
        print(f"📝 קבצים עודכנו: {len(self.updated_files)}")
        print(f"❌ שגיאות: {len(self.errors)}")
        print(f"📄 דוח: {report_file}")
        
        if self.updated_files:
            print("\n✅ קבצים שעודכנו:")
            for file in self.updated_files:
                print(f"   - {os.path.basename(file)}")
        
        return report

    def run(self):
        """הרצת כל התהליך"""
        try:
            self.log("🔄 מתחיל עדכון לChrome רגיל")
            print("=" * 60)
            
            # עדכון כל הקבצים
            self.update_all_files()
            
            # עדכון זכרון מערכת
            self.update_memory_reference()
            
            # דוח סיכום
            self.generate_update_report()
            
            self.log("🎉 עדכון ל-Chrome רגיל הושלם!", "SUCCESS")
            
        except Exception as e:
            self.log(f"שגיאה בעדכון: {str(e)}", "ERROR")

if __name__ == "__main__":
    updater = UpdateAllScriptsToRegularChrome()
    updater.run()
    
    print("\n🎯 המערכת עודכנה לעבוד עם Chrome רגיל!")
    print("🔗 כל הסקריפטים עכשיו מתחברים לפורט 9222")
    print("💡 לא נדרש QR scanning - החיבור נשמר")













