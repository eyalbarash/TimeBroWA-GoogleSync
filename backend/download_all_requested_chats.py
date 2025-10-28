#!/usr/bin/env python3
"""
Download All Requested Chats from August 2025 to Today
הורדת כל השיחות המבוקשות מאוגוסט 2025 עד היום
"""

import sqlite3
import json
import time
import re
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from contacts_list import CONTACTS_CONFIG

class DownloadAllRequestedChats:
    def __init__(self):
        self.driver = None
        self.db_path = 'whatsapp_all_requested_chats.db'
        self.db = None
        
        # בניית רשימה מלאה של כל 67 אנשי הקשר
        self.all_requested_contacts = []
        for company, config in CONTACTS_CONFIG.items():
            for contact in config["contacts"]:
                self.all_requested_contacts.append({
                    "name": contact,
                    "company": company,
                    "color": config["color"]
                })
        
        # סטטיסטיקות מפורטות
        self.stats = {
            "total_contacts": len(self.all_requested_contacts),
            "contacts_found": 0,
            "contacts_processed": 0,
            "total_messages_extracted": 0,
            "chats_with_messages": 0,
            "empty_chats": 0,
            "errors": 0,
            "start_time": datetime.now()
        }
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "ℹ️" if level == "INFO" else "🔄"
        print(f"[{timestamp}] {emoji} {message}")

    def detailed_log(self, category, message, progress=None):
        """לוגים מפורטים עם קטגוריה והתקדמות"""
        if progress:
            self.log(f"[{category}] {message} - {progress}", "🔄")
        else:
            self.log(f"[{category}] {message}")

    def initialize_comprehensive_database(self):
        """יצירת מסד נתונים מקיף לכל השיחות"""
        self.detailed_log("DATABASE", "יוצר מסד נתונים מקיף...")
        
        try:
            self.db = sqlite3.connect(self.db_path)
            cursor = self.db.cursor()
            
            schema = """
                -- טבלת אנשי קשר מבוקשים
                CREATE TABLE IF NOT EXISTS requested_contacts (
                    contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    company TEXT,
                    color_id TEXT,
                    found_in_whatsapp BOOLEAN DEFAULT FALSE,
                    messages_extracted BOOLEAN DEFAULT FALSE,
                    message_count INTEGER DEFAULT 0,
                    last_message_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- טבלת הודעות מאוגוסט 2025
                CREATE TABLE IF NOT EXISTS messages_since_august_2025 (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_name TEXT,
                    content TEXT,
                    timestamp_raw TEXT,
                    timestamp_parsed TIMESTAMP,
                    is_from_me BOOLEAN DEFAULT FALSE,
                    message_type TEXT DEFAULT 'text',
                    date_extracted TEXT,
                    month_year TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contact_name) REFERENCES requested_contacts(name)
                );
                
                -- טבלת סטטיסטיקות חילוץ
                CREATE TABLE IF NOT EXISTS extraction_stats (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    extraction_date TEXT,
                    contacts_processed INTEGER,
                    messages_extracted INTEGER,
                    time_taken_minutes INTEGER,
                    browser_port TEXT,
                    extraction_notes TEXT
                );
                
                -- אינדקסים לביצועים
                CREATE INDEX IF NOT EXISTS idx_messages_contact ON messages_since_august_2025(contact_name);
                CREATE INDEX IF NOT EXISTS idx_messages_date ON messages_since_august_2025(timestamp_parsed);
                CREATE INDEX IF NOT EXISTS idx_contacts_company ON requested_contacts(company);
            """
            
            cursor.executescript(schema)
            self.db.commit()
            
            # הכנסת כל אנשי הקשר המבוקשים
            for contact in self.all_requested_contacts:
                cursor.execute("""
                    INSERT OR IGNORE INTO requested_contacts (name, company, color_id)
                    VALUES (?, ?, ?)
                """, (contact["name"], contact["company"], contact["color"]))
            
            self.db.commit()
            self.detailed_log("DATABASE", f"מסד נתונים נוצר עם {len(self.all_requested_contacts)} אנשי קשר", "✅")
            return True
            
        except Exception as e:
            self.log(f"שגיאה ביצירת מסד נתונים: {str(e)}", "ERROR")
            self.stats["errors"] += 1
            return False

    def connect_to_whatsapp_web(self):
        """התחברות ל-WhatsApp Web הקיים"""
        self.detailed_log("BROWSER", "מתחבר לדפדפן WhatsApp הקיים...")
        
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.detailed_log("BROWSER", "חיבור לדפדפן הושלם", "1/3")
            
            # מציאת טאב WhatsApp
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if "web.whatsapp.com" in self.driver.current_url:
                    self.detailed_log("BROWSER", f"נמצא טאב WhatsApp: {self.driver.title}", "2/3")
                    break
            else:
                raise Exception("לא נמצא טאב WhatsApp Web")
            
            # וידוא שהטאב מוכן
            wait = WebDriverWait(self.driver, 20)
            wait.until(lambda driver: "WhatsApp" in driver.title and len(driver.page_source) > 1000)
            self.detailed_log("BROWSER", "WhatsApp Web מוכן לחילוץ", "3/3")
            
            return True
            
        except Exception as e:
            self.log(f"שגיאה בחיבור ל-WhatsApp: {str(e)}", "ERROR")
            self.stats["errors"] += 1
            return False

    def search_and_extract_chat(self, contact_name, contact_index, total_contacts):
        """חיפוש וחילוץ שיחה ספציפית"""
        self.detailed_log("EXTRACT", f"מחלץ שיחה: {contact_name}", f"{contact_index}/{total_contacts}")
        
        try:
            # בדיקה אם כבר עובד
            cursor = self.db.cursor()
            cursor.execute("SELECT messages_extracted FROM requested_contacts WHERE name = ?", (contact_name,))
            result = cursor.fetchone()
            
            if result and result[0]:
                self.detailed_log("SKIP", f"{contact_name} כבר חולץ - מדלג")
                return 0
            
            # חיפוש בתיבת החיפוש
            self.detailed_log("SEARCH", f"מחפש את {contact_name}...", "1/6")
            
            # ניקוי חיפוש קודם
            try:
                # לחיצה על X לניקוי חיפוש
                clear_search = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="search-input-clear"]')
                if clear_search:
                    clear_search[0].click()
                    time.sleep(0.5)
            except:
                pass
            
            # מציאת תיבת החיפוש
            search_selectors = [
                '[data-testid="chat-list-search"]',
                'div[contenteditable="true"][data-tab="3"]',
                'div[role="textbox"]'
            ]
            
            search_box = None
            for selector in search_selectors:
                try:
                    search_box = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not search_box:
                # ניסיון לקליק על אייקון החיפוש
                try:
                    search_icon = self.driver.find_element(By.CSS_SELECTOR, '[data-testid="search"]')
                    search_icon.click()
                    time.sleep(1)
                    
                    search_box = self.driver.find_element(By.CSS_SELECTOR, 'div[contenteditable="true"]')
                except:
                    pass
            
            if search_box:
                # ביצוע החיפוש
                search_box.clear()
                search_box.send_keys(contact_name)
                time.sleep(2)
                self.detailed_log("SEARCH", f"חיפש: {contact_name}", "2/6")
                
                # חיפוש התוצאה בתוצאות החיפוש
                search_results = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="cell-frame-container"]')
                
                chat_found = False
                for result in search_results:
                    try:
                        name_element = result.find_element(By.CSS_SELECTOR, '[data-testid="cell-frame-title"] span')
                        result_name = name_element.text.strip()
                        
                        # בדיקת התאמה
                        if self._is_name_match(result_name, contact_name):
                            result.click()
                            chat_found = True
                            self.detailed_log("SEARCH", f"נמצא וקליק: {result_name}", "3/6")
                            break
                    except:
                        continue
                
                if not chat_found:
                    self.detailed_log("SEARCH", f"{contact_name} לא נמצא", "3/6")
                    return 0
            else:
                self.detailed_log("SEARCH", "לא נמצאה תיבת חיפוש", "ERROR")
                return 0
            
            # המתנה לטעינת השיחה
            time.sleep(3)
            self.detailed_log("LOAD", "ממתין לטעינת השיחה", "4/6")
            
            # גלילה לטעינת היסטוריה מאוגוסט 2025
            messages_count = self._scroll_and_extract_messages(contact_name)
            self.detailed_log("EXTRACT", f"חולצו {messages_count} הודעות", "5/6")
            
            # עדכון סטטוס במסד
            cursor.execute("""
                UPDATE requested_contacts 
                SET found_in_whatsapp = TRUE, messages_extracted = TRUE, message_count = ?
                WHERE name = ?
            """, (messages_count, contact_name))
            self.db.commit()
            
            self.detailed_log("SAVE", f"סטטוס עודכן במסד נתונים", "6/6")
            
            self.stats["contacts_found"] += 1
            self.stats["contacts_processed"] += 1
            if messages_count > 0:
                self.stats["chats_with_messages"] += 1
            else:
                self.stats["empty_chats"] += 1
            
            return messages_count
            
        except Exception as e:
            self.log(f"שגיאה בחילוץ {contact_name}: {str(e)}", "ERROR")
            self.stats["errors"] += 1
            return 0

    def _is_name_match(self, found_name, requested_name):
        """בדיקת התאמה בין שמות"""
        if not found_name or not requested_name:
            return False
        
        # ניקוי שמות
        clean_found = re.sub(r'[^\u05d0-\u05ea\w\s]', '', found_name.lower()).strip()
        clean_requested = re.sub(r'[^\u05d0-\u05ea\w\s]', '', requested_name.lower()).strip()
        
        # התאמה מדויקת
        if clean_found == clean_requested:
            return True
        
        # התאמה חלקית חזקה
        if clean_found in clean_requested or clean_requested in clean_found:
            return True
        
        # התאמת מילים עיקריות
        words_found = [w for w in clean_found.split() if len(w) > 1]
        words_requested = [w for w in clean_requested.split() if len(w) > 1]
        
        if words_found and words_requested:
            common = [w1 for w1 in words_found if any(w1 in w2 or w2 in w1 for w2 in words_requested)]
            return len(common) >= min(len(words_found), len(words_requested)) * 0.7
        
        return False

    def _scroll_and_extract_messages(self, contact_name):
        """גלילה וחילוץ הודעות מאוגוסט 2025"""
        self.detailed_log("SCROLL", f"טוען היסטוריה של {contact_name} מאוגוסט 2025...")
        
        messages_extracted = 0
        
        try:
            # מציאת מיכל ההודעות
            message_container = None
            container_selectors = [
                '[data-testid="conversation-panel-messages"]',
                'div[role="log"]',
                'div[data-testid="msg-container"]',
                'div.copyable-text'
            ]
            
            for selector in container_selectors:
                try:
                    message_container = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except:
                    continue
            
            if not message_container:
                self.detailed_log("SCROLL", "לא נמצא מיכל הודעות", "ERROR")
                return 0
            
            # גלילה אגרסיבית למעלה לטעינת היסטוריה
            self.detailed_log("SCROLL", "גולל לטעינת היסטוריה...")
            
            for scroll_round in range(1, 21):  # 20 סיבובי גלילה
                # גלילה למעלה
                self.driver.execute_script("arguments[0].scrollTop = 0;", message_container)
                time.sleep(1.5)
                
                # בדיקה אם הגענו לאוגוסט 2025
                if scroll_round % 5 == 0:
                    self.detailed_log("SCROLL", f"סיבוב גלילה {scroll_round}/20", "🔄")
                    
                    # בדיקה אם יש הודעות מאוגוסט 2025
                    if self._check_for_august_2025_messages():
                        self.detailed_log("SCROLL", "הגענו לאוגוסט 2025!", "✅")
                        break
            
            # חילוץ כל ההודעות הנראות
            self.detailed_log("EXTRACT", "מחלץ את כל ההודעות הנראות...")
            
            # מציאת כל אלמנטי ההודעות
            message_selectors = [
                'div[data-testid="msg-container"]',
                'div.copyable-text',
                'span[data-testid="conversation-info-header"]',
                'div.selectable-text'
            ]
            
            all_message_elements = []
            for selector in message_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    all_message_elements.extend(elements)
                except:
                    continue
            
            self.detailed_log("EXTRACT", f"נמצאו {len(all_message_elements)} אלמנטי הודעות")
            
            # עיבוד ההודעות
            for i, element in enumerate(all_message_elements):
                try:
                    message_text = element.text.strip()
                    
                    if not message_text or len(message_text) < 2:
                        continue
                    
                    # ניסיון לחלץ זמן
                    timestamp_raw = ""
                    try:
                        # חיפוש אלמנט זמן
                        time_element = element.find_element(By.CSS_SELECTOR, 'span[data-testid="msg-time"]')
                        timestamp_raw = time_element.get_attribute("title") or time_element.text
                    except:
                        # ניסיון אלטרנטיבי לזמן
                        try:
                            parent = element.find_element(By.XPATH, "..")
                            time_element = parent.find_element(By.CSS_SELECTOR, 'span[title*=":"]')
                            timestamp_raw = time_element.get_attribute("title")
                        except:
                            timestamp_raw = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # זיהוי כיוון ההודעה
                    is_from_me = False
                    try:
                        classes = element.get_attribute("class") or ""
                        is_from_me = "message-out" in classes or "msg-from-me" in classes
                    except:
                        pass
                    
                    # שמירת ההודעה
                    self._save_message_to_db(contact_name, message_text, timestamp_raw, is_from_me)
                    messages_extracted += 1
                    
                    # דיווח התקדמות
                    if messages_extracted % 50 == 0:
                        self.detailed_log("EXTRACT", f"חולצו {messages_extracted} הודעות")
                
                except Exception as e:
                    continue
            
            self.detailed_log("EXTRACT", f"סיום חילוץ: {messages_extracted} הודעות", "✅")
            self.stats["total_messages_extracted"] += messages_extracted
            
            return messages_extracted
            
        except Exception as e:
            self.log(f"שגיאה בגלילה וחילוץ עבור {contact_name}: {str(e)}", "ERROR")
            self.stats["errors"] += 1
            return 0

    def _check_for_august_2025_messages(self):
        """בדיקה אם יש הודעות מאוגוסט 2025"""
        try:
            # חיפוש תאריכים בדף
            page_text = self.driver.page_source
            august_patterns = ['08/2025', '8/2025', 'אוגוסט 2025', 'August 2025']
            
            for pattern in august_patterns:
                if pattern in page_text:
                    return True
            
            return False
            
        except:
            return False

    def _save_message_to_db(self, contact_name, content, timestamp_raw, is_from_me):
        """שמירת הודעה במסד הנתונים"""
        try:
            cursor = self.db.cursor()
            
            # ניסיון לפרסר תאריך
            timestamp_parsed = None
            try:
                # ניסיונות פרסור שונים
                if "/" in timestamp_raw and ":" in timestamp_raw:
                    # פורמט DD/MM/YYYY, HH:MM:SS
                    timestamp_parsed = datetime.strptime(timestamp_raw, "%d/%m/%Y, %H:%M:%S").isoformat()
                elif timestamp_raw:
                    # השארת הטקסט כמו שהוא
                    timestamp_parsed = timestamp_raw
                else:
                    timestamp_parsed = datetime.now().isoformat()
            except:
                timestamp_parsed = datetime.now().isoformat()
            
            # חילוץ חודש-שנה לקיבוץ
            month_year = ""
            try:
                dt = datetime.fromisoformat(timestamp_parsed.replace('Z', '+00:00'))
                month_year = dt.strftime("%Y-%m")
            except:
                month_year = datetime.now().strftime("%Y-%m")
            
            cursor.execute("""
                INSERT INTO messages_since_august_2025 
                (contact_name, content, timestamp_raw, timestamp_parsed, is_from_me, 
                 date_extracted, month_year)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                contact_name,
                content,
                timestamp_raw,
                timestamp_parsed,
                is_from_me,
                datetime.now().strftime("%Y-%m-%d"),
                month_year
            ))
            
            self.db.commit()
            
        except Exception as e:
            # שמירת בסיסית גם אם הפרסור נכשל
            try:
                cursor.execute("""
                    INSERT INTO messages_since_august_2025 
                    (contact_name, content, timestamp_raw, is_from_me, date_extracted)
                    VALUES (?, ?, ?, ?, ?)
                """, (contact_name, content, timestamp_raw, is_from_me, datetime.now().strftime("%Y-%m-%d")))
                self.db.commit()
            except:
                pass

    def generate_progress_report(self):
        """יצירת דוח התקדמות"""
        elapsed = datetime.now() - self.stats["start_time"]
        elapsed_minutes = elapsed.total_seconds() / 60
        
        print(f"\n📊 דוח התקדמות - {elapsed_minutes:.1f} דקות")
        print("=" * 50)
        print(f"📋 סך הכל אנשי קשר: {self.stats['total_contacts']}")
        print(f"🔍 נמצאו ב-WhatsApp: {self.stats['contacts_found']}")
        print(f"✅ עובדו: {self.stats['contacts_processed']}")
        print(f"💬 שיחות עם הודעות: {self.stats['chats_with_messages']}")
        print(f"📝 סך הודעות: {self.stats['total_messages_extracted']}")
        print(f"❌ שגיאות: {self.stats['errors']}")
        
        # חישוב קצב
        if self.stats['contacts_processed'] > 0:
            rate = elapsed_minutes / self.stats['contacts_processed']
            remaining = self.stats['total_contacts'] - self.stats['contacts_processed']
            eta_minutes = remaining * rate
            print(f"⏱️ זמן משוער לסיום: {eta_minutes:.1f} דקות")

    def process_all_contacts(self):
        """עיבוד כל 67 אנשי הקשר"""
        self.detailed_log("PROCESS", f"מתחיל עיבוד {len(self.all_requested_contacts)} אנשי קשר...")
        
        for i, contact in enumerate(self.all_requested_contacts, 1):
            contact_name = contact["name"]
            company = contact["company"]
            
            try:
                self.detailed_log("CONTACT", f"מתחיל: {contact_name} ({company})", f"{i}/{len(self.all_requested_contacts)}")
                
                # חילוץ השיחה
                messages_count = self.search_and_extract_chat(contact_name, i, len(self.all_requested_contacts))
                
                if messages_count > 0:
                    self.detailed_log("SUCCESS", f"{contact_name}: {messages_count} הודעות", "✅")
                else:
                    self.detailed_log("EMPTY", f"{contact_name}: אין הודעות", "⚪")
                
                # דיווח התקדמות כל 10 אנשי קשר
                if i % 10 == 0:
                    self.generate_progress_report()
                
                # השהיה בין אנשי קשר למניעת עומס
                time.sleep(2)
                
            except Exception as e:
                self.log(f"שגיאה בעיבוד {contact_name}: {str(e)}", "ERROR")
                self.stats["errors"] += 1
        
        self.detailed_log("PROCESS", "עיבוד כל אנשי הקשר הושלם", "✅")

    def generate_final_comprehensive_report(self):
        """יצירת דוח סיכום מקיף"""
        self.detailed_log("REPORT", "יוצר דוח סיכום מקיף...")
        
        try:
            cursor = self.db.cursor()
            
            # סטטיסטיקות מסד נתונים
            cursor.execute("SELECT COUNT(*) FROM messages_since_august_2025")
            total_messages = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM requested_contacts WHERE found_in_whatsapp = TRUE")
            found_contacts = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM requested_contacts WHERE message_count > 0")
            contacts_with_messages = cursor.fetchone()[0]
            
            # פירוט לפי חברות
            cursor.execute("""
                SELECT company, COUNT(*) as count, SUM(message_count) as total_messages
                FROM requested_contacts 
                WHERE found_in_whatsapp = TRUE
                GROUP BY company
                ORDER BY total_messages DESC
            """)
            company_stats = cursor.fetchall()
            
            # שמירת סטטיסטיקות סשן
            elapsed_minutes = (datetime.now() - self.stats["start_time"]).total_seconds() / 60
            cursor.execute("""
                INSERT INTO extraction_stats 
                (extraction_date, contacts_processed, messages_extracted, time_taken_minutes, browser_port, extraction_notes)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.stats["contacts_processed"],
                self.stats["total_messages_extracted"],
                int(elapsed_minutes),
                "9222",
                f"Full extraction of {len(self.all_requested_contacts)} requested contacts"
            ))
            
            self.db.commit()
            
            # יצירת דוח JSON
            report = {
                "timestamp": datetime.now().isoformat(),
                "extraction_period": "August 2025 to today",
                "total_requested_contacts": len(self.all_requested_contacts),
                "session_stats": self.stats,
                "database_stats": {
                    "total_messages_extracted": total_messages,
                    "contacts_found_in_whatsapp": found_contacts,
                    "contacts_with_messages": contacts_with_messages
                },
                "company_breakdown": [
                    {"company": comp, "contacts_found": count, "total_messages": msgs}
                    for comp, count, msgs in company_stats
                ],
                "database_file": self.db_path
            }
            
            # שמירת דוח
            report_file = f"all_chats_extraction_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # הצגת סיכום מפורט
            print("\n📊 דוח סיכום מקיף - הורדת כל השיחות המבוקשות")
            print("=" * 80)
            print(f"📅 תקופה: אוגוסט 2025 עד היום")
            print(f"📋 סך הכל אנשי קשר מבוקשים: {len(self.all_requested_contacts)}")
            print(f"🔍 נמצאו ב-WhatsApp: {found_contacts}")
            print(f"💬 עם הודעות: {contacts_with_messages}")
            print(f"📝 סך הודעות שחולצו: {total_messages}")
            print(f"⏱️ זמן חילוץ: {elapsed_minutes:.1f} דקות")
            print(f"💾 מסד נתונים: {self.db_path}")
            print(f"📄 דוח: {report_file}")
            
            if company_stats:
                print("\n🏢 פירוט לפי חברות:")
                for company, count, messages in company_stats:
                    print(f"   📂 {company}: {count} אנשי קשר, {messages} הודעות")
            
            print(f"\n📈 ביצועים:")
            print(f"   ✅ הצלחה: {self.stats['contacts_found']}/{self.stats['total_contacts']}")
            print(f"   ❌ שגיאות: {self.stats['errors']}")
            
            return report
            
        except Exception as e:
            self.log(f"שגיאה ביצירת דוח: {str(e)}", "ERROR")
            return {}

    def cleanup(self):
        """ניקוי משאבים"""
        self.detailed_log("CLEANUP", "מסיים ושומר משאבים...")
        
        if self.db:
            self.db.close()
        
        # דפדפן נשאר פתוח!
        self.log("🔗 דפדפן WhatsApp נשאר פתוח - ללא צורך ב-QR בעתיד", "SUCCESS")

    def run(self):
        """הרצת התהליך המלא"""
        try:
            self.log("🚀 מתחיל הורדת כל 67 השיחות המבוקשות מאוגוסט 2025")
            print("=" * 80)
            
            # אתחול מסד נתונים
            if not self.initialize_comprehensive_database():
                raise Exception("נכשל ביצירת מסד נתונים")
            
            # התחברות ל-WhatsApp
            if not self.connect_to_whatsapp_web():
                raise Exception("נכשל בחיבור ל-WhatsApp Web")
            
            # עיבוד כל אנשי הקשר
            self.process_all_contacts()
            
            # דוח סיכום
            report = self.generate_final_comprehensive_report()
            
            self.log("🎉 הורדת כל השיחות הושלמה בהצלחה!", "SUCCESS")
            
            return report
            
        except Exception as e:
            self.log(f"שגיאה בתהליך הורדת השיחות: {str(e)}", "ERROR")
            return None
            
        finally:
            self.cleanup()

if __name__ == "__main__":
    downloader = DownloadAllRequestedChats()
    
    print("📋 רשימת 67 אנשי הקשר שיורדו:")
    print("=" * 50)
    
    for i, contact in enumerate(downloader.all_requested_contacts, 1):
        print(f"{i:2d}. {contact['name']} ({contact['company']})")
    
    print(f"\n🎯 מתחיל הורדה של כל {len(downloader.all_requested_contacts)} השיחות...")
    
    try:
        report = downloader.run()
        
        if report:
            print("\n🎉 הורדת כל השיחות הושלמה!")
            print("💾 כל ההודעות מאוגוסט 2025 עד היום נשמרו במסד הנתונים")
            print("🔗 החיבור ל-WhatsApp נשמר ללא צורך ב-QR")
        else:
            print("❌ הורדת השיחות נכשלה")
            
    except Exception as error:
        print(f"❌ שגיאה כללית: {str(error)}")
        print("💡 דפדפן WhatsApp נשאר פתוח")













