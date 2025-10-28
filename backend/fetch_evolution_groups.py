#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
קבלת כל הקבוצות מ-Evolution API ושמירה במסד נתונים
"""

import requests
import json
import sqlite3
import os
from datetime import datetime

class EvolutionGroupsFetcher:
    def __init__(self):
        # הגדרות API
        self.api_base_url = "https://evolution.cigcrm.com"
        self.api_key = "A6401FCD5870-4CDB-87C4-6A22F06745CD"
        self.instance = None  # יש להגדיר את ה-instance
        
        # מסד נתונים
        self.db_file = "evolution_groups.db"
        
        self.headers = {
            'apikey': self.api_key,
            'Content-Type': 'application/json'
        }

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if level == "SUCCESS":
            emoji = "✅"
        elif level == "ERROR":
            emoji = "❌"
        else:
            emoji = "📡"
        print(f"[{timestamp}] {emoji} {message}")

    def init_database(self):
        """יצירת טבלת קבוצות במסד הנתונים"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # יצירת טבלת קבוצות
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    participants_count INTEGER,
                    owner TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    raw_data TEXT,
                    fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # אינדקסים לחיפוש מהיר
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_groups_name ON groups(name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_groups_owner ON groups(owner)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_groups_fetched_at ON groups(fetched_at)")
            
            conn.commit()
            conn.close()
            
            self.log("✅ טבלת קבוצות נוצרה במסד הנתונים", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ שגיאה ביצירת מסד נתונים: {e}", "ERROR")
            return False

    def get_instance_name(self):
        """קבלת שם ה-instance (יש להגדיר ידנית או לקרוא מקובץ)"""
        # אפשרות 1: קריאה מקובץ הגדרות
        config_file = "evolution_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    return config.get('instance')
            except Exception as e:
                self.log(f"שגיאה בקריאת קובץ הגדרות: {e}")
        
        # אפשרות 2: שאלת המשתמש
        instance = input("אנא הכנס את שם ה-instance: ").strip()
        if instance:
            # שמירה בקובץ הגדרות לפעם הבאה
            try:
                config = {"instance": instance, "created_at": datetime.now().isoformat()}
                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                self.log(f"שם ה-instance נשמר: {instance}")
            except Exception as e:
                self.log(f"שגיאה בשמירת הגדרות: {e}")
        
        return instance

    def fetch_groups_from_api(self):
        """קבלת קבוצות מ-Evolution API"""
        if not self.instance:
            self.instance = self.get_instance_name()
            
        if not self.instance:
            self.log("❌ לא הוגדר instance", "ERROR")
            return None
        
        # בניית URL (תיקון הכפל https)
        clean_base_url = self.api_base_url.replace("https://https//", "https://")
        url = f"{clean_base_url}/group/fetchAllGroups/{self.instance}"
        
        # הוספת פרמטר getParticipants שנדרש על ידי ה-API
        # נתחיל עם false כדי לקבל רק מידע בסיסי על הקבוצות
        params = {
            'getParticipants': 'false'
        }
        
        self.log(f"📡 שולח בקשה ל-API: {url}")
        self.log(f"📡 עם פרמטרים: {params}")
        
        try:
            # timeout ארוך מאוד כי יש המון קבוצות
            self.log("⏳ מחכה לתגובה מהשרת... זה יכול לקחת כמה דקות")
            response = requests.get(url, headers=self.headers, params=params, timeout=300)
            
            self.log(f"📡 קוד תגובה: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ התקבלו נתונים מה-API", "SUCCESS")
                return data
            else:
                self.log(f"❌ שגיאה ב-API: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except requests.exceptions.Timeout:
            self.log("❌ תם הזמן הקצוב לבקשה", "ERROR")
            return None
        except requests.exceptions.RequestException as e:
            self.log(f"❌ שגיאה בבקשת API: {e}", "ERROR")
            return None
        except json.JSONDecodeError as e:
            self.log(f"❌ שגיאה בפענוח JSON: {e}", "ERROR")
            return None

    def save_groups_to_db(self, groups_data):
        """שמירת נתוני קבוצות במסד הנתונים"""
        if not groups_data:
            self.log("❌ אין נתונים לשמירה", "ERROR")
            return 0
        
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # ניקוי נתונים ישנים
            cursor.execute("DELETE FROM groups")
            
            saved_count = 0
            
            # אם הנתונים הם רשימה
            if isinstance(groups_data, list):
                groups_list = groups_data
            # אם הנתונים הם אובייקט עם מפתח של רשימה
            elif isinstance(groups_data, dict):
                # חיפוש המפתח המכיל את הרשימה
                groups_list = None
                for key, value in groups_data.items():
                    if isinstance(value, list) and len(value) > 0:
                        groups_list = value
                        break
                
                if not groups_list:
                    self.log("❌ לא נמצאה רשימת קבוצות בנתונים", "ERROR")
                    return 0
            else:
                self.log("❌ פורמט נתונים לא מזוהה", "ERROR")
                return 0
            
            # שמירת כל קבוצה
            for group in groups_list:
                try:
                    # חילוץ נתונים מהקבוצה
                    group_id = group.get('id', str(group.get('groupId', '')))
                    name = group.get('name', group.get('subject', 'Unknown'))
                    description = group.get('description', group.get('desc', ''))
                    participants_count = len(group.get('participants', []))
                    owner = group.get('owner', group.get('groupOwner', ''))
                    created_at = group.get('createdAt', group.get('creation', ''))
                    
                    cursor.execute("""
                        INSERT OR REPLACE INTO groups 
                        (id, name, description, participants_count, owner, created_at, 
                         updated_at, raw_data, fetched_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        group_id,
                        name,
                        description,
                        participants_count,
                        owner,
                        created_at,
                        datetime.now().isoformat(),
                        json.dumps(group, ensure_ascii=False)
                    ))
                    
                    saved_count += 1
                    
                    if saved_count <= 5:  # הצגת 5 ראשונים
                        self.log(f"  💾 נשמר: {name} ({participants_count} משתתפים)")
                    
                except Exception as e:
                    self.log(f"❌ שגיאה בשמירת קבוצה: {e}", "ERROR")
                    continue
            
            conn.commit()
            conn.close()
            
            self.log(f"✅ נשמרו {saved_count} קבוצות במסד הנתונים", "SUCCESS")
            return saved_count
            
        except Exception as e:
            self.log(f"❌ שגיאה בשמירת נתונים: {e}", "ERROR")
            return 0

    def show_groups_summary(self):
        """הצגת סיכום הקבוצות שנשמרו"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # סיכום כללי
            cursor.execute("SELECT COUNT(*) FROM groups")
            total_groups = cursor.fetchone()[0]
            
            cursor.execute("SELECT SUM(participants_count) FROM groups")
            total_participants = cursor.fetchone()[0] or 0
            
            cursor.execute("SELECT AVG(participants_count) FROM groups")
            avg_participants = cursor.fetchone()[0] or 0
            
            self.log(f"📊 סיכום קבוצות:")
            self.log(f"   📁 סך הכל קבוצות: {total_groups}")
            self.log(f"   👥 סך הכל משתתפים: {total_participants}")
            self.log(f"   📈 ממוצע משתתפים לקבוצה: {avg_participants:.1f}")
            
            # קבוצות הגדולות ביותר
            cursor.execute("""
                SELECT name, participants_count 
                FROM groups 
                ORDER BY participants_count DESC 
                LIMIT 5
            """)
            
            top_groups = cursor.fetchall()
            if top_groups:
                self.log(f"🔝 הקבוצות הגדולות ביותר:")
                for i, (name, count) in enumerate(top_groups, 1):
                    self.log(f"   {i}. {name} ({count} משתתפים)")
            
            conn.close()
            
        except Exception as e:
            self.log(f"❌ שגיאה בהצגת סיכום: {e}", "ERROR")

    def run(self):
        """הרצה ראשית"""
        self.log("📡 מתחיל קבלת קבוצות מ-Evolution API")
        
        # אתחול מסד נתונים
        if not self.init_database():
            return False
        
        # קבלת נתונים מ-API
        groups_data = self.fetch_groups_from_api()
        if not groups_data:
            return False
        
        # שמירת הנתונים הגולמיים לקובץ
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        raw_file = f"evolution_groups_raw_{timestamp}.json"
        try:
            with open(raw_file, 'w', encoding='utf-8') as f:
                json.dump(groups_data, f, ensure_ascii=False, indent=2)
            self.log(f"💾 נתונים גולמיים נשמרו: {raw_file}")
        except Exception as e:
            self.log(f"שגיאה בשמירת נתונים גולמיים: {e}")
        
        # שמירה במסד נתונים
        saved_count = self.save_groups_to_db(groups_data)
        
        if saved_count > 0:
            # הצגת סיכום
            self.show_groups_summary()
            self.log("✅ קבלת קבוצות הושלמה בהצלחה", "SUCCESS")
            return True
        else:
            self.log("❌ לא נשמרו קבוצות", "ERROR")
            return False

def main():
    """הפעלה ראשית"""
    import sys
    
    # אם הועבר instance כפרמטר
    if len(sys.argv) > 1:
        instance_name = sys.argv[1]
    else:
        instance_name = None
    
    fetcher = EvolutionGroupsFetcher()
    if instance_name:
        fetcher.instance = instance_name
        print(f"📡 Evolution API - קבלת כל הקבוצות (Instance: {instance_name})")
    else:
        print("📡 Evolution API - קבלת כל הקבוצות")
    
    print("=" * 60)
    
    success = fetcher.run()
    
    if success:
        print("\n🎉 הקבלה הושלמה בהצלחה!")
        print("📊 בדוק את המסד נתונים: evolution_groups.db")
    else:
        print("\n❌ הקבלה נכשלה")
        print("📋 בדוק את השגיאות למעלה")

if __name__ == "__main__":
    main()
