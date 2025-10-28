#!/usr/bin/env python3
"""
Update Database with All Chat Names and IDs
עדכון מסד הנתונים עם שמות ומזהי כל השיחות
"""

import sqlite3
import json
import time
import re
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from contacts_list import CONTACTS_CONFIG

class UpdateDatabaseWithAllChats:
    def __init__(self):
        self.driver = None
        self.db_path = 'whatsapp_master_database.db'
        self.db = None
        
        # רשימת אנשי הקשר המבוקשים
        self.requested_contacts = []
        for company, config in CONTACTS_CONFIG.items():
            for contact in config["contacts"]:
                self.requested_contacts.append({
                    "name": contact,
                    "company": company,
                    "color": config["color"]
                })
        
        # סטטיסטיקות
        self.stats = {
            "total_chats_found": 0,
            "requested_contacts_matched": 0,
            "contacts_not_found": 0,
            "chats_scanned": 0,
            "messages_potential": 0
        }

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if level == "SUCCESS" else "❌" if level == "ERROR" else "ℹ️" if level == "INFO" else "🔄"
        print(f"[{timestamp}] {emoji} {message}")

    def detailed_log(self, category, message, progress=None):
        if progress:
            self.log(f"[{category}] {message} - {progress}", "🔄")
        else:
            self.log(f"[{category}] {message}")

    def create_master_database(self):
        """יצירת מסד נתונים מאסטר"""
        self.detailed_log("DATABASE", "יוצר מסד נתונים מאסטר...")
        
        try:
            self.db = sqlite3.connect(self.db_path)
            cursor = self.db.cursor()
            
            schema = """
                -- טבלת כל השיחות ב-WhatsApp
                CREATE TABLE IF NOT EXISTS whatsapp_all_chats (
                    chat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    whatsapp_display_name TEXT UNIQUE,
                    last_message_preview TEXT,
                    last_activity_time TEXT,
                    unread_count INTEGER DEFAULT 0,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    is_group BOOLEAN DEFAULT FALSE,
                    is_phone_number BOOLEAN DEFAULT FALSE,
                    chat_position_index INTEGER,
                    found_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                -- טבלת התאמות לרשימה המבוקשת
                CREATE TABLE IF NOT EXISTS requested_contacts_mapping (
                    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requested_name TEXT,
                    company TEXT,
                    color_id TEXT,
                    whatsapp_display_name TEXT,
                    is_matched BOOLEAN DEFAULT FALSE,
                    match_confidence REAL DEFAULT 0.0,
                    messages_extracted BOOLEAN DEFAULT FALSE,
                    last_extraction_date TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (whatsapp_display_name) REFERENCES whatsapp_all_chats(whatsapp_display_name)
                );
                
                -- טבלת סטטוס חילוץ
                CREATE TABLE IF NOT EXISTS extraction_status (
                    status_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contact_name TEXT,
                    whatsapp_name TEXT,
                    extraction_attempted BOOLEAN DEFAULT FALSE,
                    extraction_successful BOOLEAN DEFAULT FALSE,
                    messages_found INTEGER DEFAULT 0,
                    august_2025_messages INTEGER DEFAULT 0,
                    september_2025_messages INTEGER DEFAULT 0,
                    last_attempt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT,
                    next_attempt_needed BOOLEAN DEFAULT TRUE
                );
                
                -- אינדקסים
                CREATE INDEX IF NOT EXISTS idx_chats_name ON whatsapp_all_chats(whatsapp_display_name);
                CREATE INDEX IF NOT EXISTS idx_mapping_requested ON requested_contacts_mapping(requested_name);
                CREATE INDEX IF NOT EXISTS idx_status_contact ON extraction_status(contact_name);
            """
            
            cursor.executescript(schema)
            self.db.commit()
            
            # הכנסת כל אנשי הקשר המבוקשים
            for contact in self.requested_contacts:
                cursor.execute("""
                    INSERT OR IGNORE INTO requested_contacts_mapping 
                    (requested_name, company, color_id)
                    VALUES (?, ?, ?)
                """, (contact["name"], contact["company"], contact["color"]))
            
            self.db.commit()
            self.detailed_log("DATABASE", f"מסד מאסטר נוצר עם {len(self.requested_contacts)} אנשי קשר", "✅")
            
            return True
            
        except Exception as e:
            self.log(f"שגיאה ביצירת מסד נתונים: {str(e)}", "ERROR")
            return False

    def connect_to_chrome_regular(self):
        """התחברות ל-Chrome רגיל"""
        self.detailed_log("BROWSER", "מתחבר ל-Chrome רגיל על פורט 9222...")
        
        try:
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            
            # מעבר לטאב WhatsApp
            for handle in self.driver.window_handles:
                self.driver.switch_to.window(handle)
                if "web.whatsapp.com" in self.driver.current_url and "WhatsApp" in self.driver.title:
                    self.detailed_log("BROWSER", f"טאב WhatsApp מוכן: {self.driver.title}", "✅")
                    return True
            
            raise Exception("לא נמצא טאב WhatsApp ב-Chrome רגיל")
            
        except Exception as e:
            self.log(f"שגיאה בחיבור ל-Chrome: {str(e)}", "ERROR")
            return False

    def scan_and_catalog_all_chats(self):
        """סריקה וקטלוג של כל השיחות"""
        self.detailed_log("CATALOG", "סורק וקוטלג את כל השיחות...")
        
        try:
            # גלילה אגרסיבית לטעינת כל השיחות
            self.detailed_log("SCROLL", "טוען את כל השיחות הקיימות...")
            
            for scroll_round in range(1, 21):  # 20 סיבובי גלילה
                # גלילה למטה
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # גלילה חזרה למעלה כדי לוודא שהכל נטען
                if scroll_round % 5 == 0:
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(1)
                    self.detailed_log("SCROLL", f"גלילה {scroll_round}/20", "🔄")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(1)
            
            # חילוץ כל השיחות
            self.detailed_log("EXTRACT", "מחלץ פרטי כל השיחות...")
            
            chat_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="cell-frame-container"]')
            self.detailed_log("EXTRACT", f"נמצאו {len(chat_elements)} שיחות")
            
            all_chats = []
            
            for i, element in enumerate(chat_elements):
                try:
                    # שם השיחה
                    name_element = element.find_element(By.CSS_SELECTOR, '[data-testid="cell-frame-title"] span')
                    chat_name = name_element.text.strip()
                    
                    if not chat_name:
                        continue
                    
                    # הודעה אחרונה
                    last_message = ""
                    try:
                        msg_element = element.find_element(By.CSS_SELECTOR, '[data-testid="cell-frame-secondary"] span[dir="ltr"]')
                        last_message = msg_element.text.strip()
                    except:
                        pass
                    
                    # זמן פעילות
                    last_time = ""
                    try:
                        time_element = element.find_element(By.CSS_SELECTOR, '[data-testid="cell-frame-secondary"] div div div')
                        last_time = time_element.text.strip()
                    except:
                        pass
                    
                    # מספר הודעות לא נקראו
                    unread_count = 0
                    try:
                        unread_element = element.find_element(By.CSS_SELECTOR, '[data-testid="icon-unread-count"]')
                        unread_count = int(unread_element.text.strip())
                    except:
                        pass
                    
                    # זיהוי קבוצה
                    is_group = False
                    try:
                        element.find_element(By.CSS_SELECTOR, '[data-testid="default-group"]')
                        is_group = True
                    except:
                        pass
                    
                    # זיהוי מספר טלפון
                    phone_pattern = r'^(\+?972|0)[5-9]\d{8}$'
                    is_phone_number = bool(re.match(phone_pattern, chat_name.replace('[ \-\(\)]', '')))
                    
                    # זיהוי נעוץ
                    is_pinned = False
                    try:
                        element.find_element(By.CSS_SELECTOR, '[data-testid="pinned"]')
                        is_pinned = True
                    except:
                        pass
                    
                    chat_info = {
                        "name": chat_name,
                        "last_message": last_message,
                        "last_time": last_time,
                        "unread_count": unread_count,
                        "is_group": is_group,
                        "is_phone_number": is_phone_number,
                        "is_pinned": is_pinned,
                        "position": i
                    }
                    
                    all_chats.append(chat_info)
                    
                    # דיווח התקדמות
                    if (i + 1) % 20 == 0:
                        self.detailed_log("EXTRACT", f"עובד על שיחה {i+1}/{len(chat_elements)}")
                
                except Exception as e:
                    continue
            
            self.stats["total_chats_found"] = len(all_chats)
            self.stats["chats_scanned"] = len(chat_elements)
            
            self.detailed_log("CATALOG", f"קוטלגו {len(all_chats)} שיחות", "✅")
            
            return all_chats
            
        except Exception as e:
            self.log(f"שגיאה בסריקת שיחות: {str(e)}", "ERROR")
            return []

    def save_all_chats_to_database(self, all_chats):
        """שמירת כל השיחות במסד הנתונים"""
        self.detailed_log("SAVE", "שומר את כל השיחות במסד הנתונים...")
        
        try:
            cursor = self.db.cursor()
            
            saved_count = 0
            for chat in all_chats:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO whatsapp_all_chats 
                        (whatsapp_display_name, last_message_preview, last_activity_time, 
                         unread_count, is_pinned, is_group, is_phone_number, chat_position_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        chat["name"],
                        chat["last_message"],
                        chat["last_time"],
                        chat["unread_count"],
                        chat["is_pinned"],
                        chat["is_group"],
                        chat["is_phone_number"],
                        chat["position"]
                    ))
                    
                    saved_count += 1
                    
                    if saved_count % 20 == 0:
                        self.detailed_log("SAVE", f"נשמרו {saved_count}/{len(all_chats)} שיחות")
                
                except Exception as e:
                    self.log(f"שגיאה בשמירת שיחה {chat['name']}: {str(e)}", "ERROR")
                    continue
            
            self.db.commit()
            self.detailed_log("SAVE", f"נשמרו {saved_count} שיחות במסד הנתונים", "✅")
            
            return saved_count
            
        except Exception as e:
            self.log(f"שגיאה בשמירת שיחות: {str(e)}", "ERROR")
            return 0

    def match_chats_to_requested_contacts(self, all_chats):
        """התאמת שיחות לאנשי הקשר המבוקשים"""
        self.detailed_log("MATCH", "מתאים שיחות לרשימה המבוקשת...")
        
        matches_found = []
        
        for chat in all_chats:
            chat_name = chat["name"]
            best_match = None
            best_confidence = 0.0
            
            for requested in self.requested_contacts:
                requested_name = requested["name"]
                confidence = self._calculate_match_confidence(chat_name, requested_name)
                
                if confidence > best_confidence and confidence >= 0.6:  # סף התאמה
                    best_match = requested
                    best_confidence = confidence
            
            if best_match:
                match_info = {
                    "whatsapp_name": chat_name,
                    "requested_name": best_match["name"],
                    "company": best_match["company"],
                    "color": best_match["color"],
                    "confidence": best_confidence,
                    "chat_details": chat
                }
                
                matches_found.append(match_info)
                
                self.detailed_log("MATCH", f"התאמה: {chat_name} ← {best_match['name']} (ביטחון: {best_confidence:.2f})")
                
                # שמירת ההתאמה במסד נתונים
                self._save_match_to_database(match_info)
        
        self.stats["requested_contacts_matched"] = len(matches_found)
        self.stats["contacts_not_found"] = len(self.requested_contacts) - len(matches_found)
        
        self.detailed_log("MATCH", f"נמצאו {len(matches_found)} התאמות מתוך {len(self.requested_contacts)}", "✅")
        
        return matches_found

    def _calculate_match_confidence(self, whatsapp_name, requested_name):
        """חישוב רמת ביטחון בהתאמה"""
        if not whatsapp_name or not requested_name:
            return 0.0
        
        # ניקוי שמות
        clean_wa = re.sub(r'[^\u05d0-\u05ea\w\s]', '', whatsapp_name.lower()).strip()
        clean_req = re.sub(r'[^\u05d0-\u05ea\w\s]', '', requested_name.lower()).strip()
        
        # התאמה מדויקת
        if clean_wa == clean_req:
            return 1.0
        
        # התאמה חלקית חזקה
        if clean_wa in clean_req or clean_req in clean_wa:
            return 0.9
        
        # התאמת מילים
        words_wa = [w for w in clean_wa.split() if len(w) > 1]
        words_req = [w for w in clean_req.split() if len(w) > 1]
        
        if not words_wa or not words_req:
            return 0.0
        
        # חישוב אחוז מילים משותפות
        common_words = 0
        for w1 in words_wa:
            for w2 in words_req:
                if w1 in w2 or w2 in w1 or w1 == w2:
                    common_words += 1
                    break
        
        word_match_ratio = common_words / min(len(words_wa), len(words_req))
        
        # בונוס לשמות קצרים עם התאמה טובה
        if len(words_req) <= 2 and word_match_ratio >= 0.5:
            word_match_ratio += 0.2
        
        return min(word_match_ratio, 1.0)

    def _save_match_to_database(self, match_info):
        """שמירת התאמה במסד הנתונים"""
        try:
            cursor = self.db.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO requested_contacts_mapping 
                (requested_name, company, color_id, whatsapp_display_name, 
                 is_matched, match_confidence)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                match_info["requested_name"],
                match_info["company"],
                match_info["color"],
                match_info["whatsapp_name"],
                True,
                match_info["confidence"]
            ))
            
            # יצירת רשומת סטטוס חילוץ
            cursor.execute("""
                INSERT OR REPLACE INTO extraction_status 
                (contact_name, whatsapp_name, next_attempt_needed)
                VALUES (?, ?, ?)
            """, (
                match_info["requested_name"],
                match_info["whatsapp_name"],
                True  # צריך לנסות לחלץ
            ))
            
            self.db.commit()
            
        except Exception as e:
            self.log(f"שגיאה בשמירת התאמה: {str(e)}", "ERROR")

    def identify_unmatched_contacts(self):
        """זיהוי אנשי קשר שלא נמצאו"""
        self.detailed_log("ANALYSIS", "מזהה אנשי קשר שלא נמצאו...")
        
        try:
            cursor = self.db.cursor()
            
            # אנשי קשר שלא נמצאו
            cursor.execute("""
                SELECT requested_name, company 
                FROM requested_contacts_mapping 
                WHERE is_matched = FALSE OR whatsapp_display_name IS NULL
                ORDER BY company, requested_name
            """)
            
            unmatched = cursor.fetchall()
            
            # קיבוץ לפי חברות
            unmatched_by_company = {}
            for name, company in unmatched:
                if company not in unmatched_by_company:
                    unmatched_by_company[company] = []
                unmatched_by_company[company].append(name)
            
            return unmatched_by_company
            
        except Exception as e:
            self.log(f"שגיאה בזיהוי לא נמצאו: {str(e)}", "ERROR")
            return {}

    def generate_comprehensive_mapping_report(self, all_chats, matches, unmatched_by_company):
        """יצירת דוח מיפוי מקיף"""
        self.detailed_log("REPORT", "יוצר דוח מיפוי מקיף...")
        
        try:
            # קיבוץ התאמות לפי חברות
            matches_by_company = {}
            for match in matches:
                company = match["company"]
                if company not in matches_by_company:
                    matches_by_company[company] = []
                matches_by_company[company].append(match)
            
            report = {
                "timestamp": datetime.now().isoformat(),
                "chrome_connection": "regular_chrome_port_9222",
                "database_file": self.db_path,
                "scan_results": {
                    "total_chats_in_whatsapp": len(all_chats),
                    "requested_contacts_total": len(self.requested_contacts),
                    "matches_found": len(matches),
                    "contacts_not_found": len(self.requested_contacts) - len(matches)
                },
                "matches_by_company": matches_by_company,
                "unmatched_by_company": unmatched_by_company,
                "next_extraction_needed": [match["requested_name"] for match in matches]
            }
            
            # שמירת דוח
            report_file = f"master_chat_mapping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # הצגת דוח מפורט
            print("\n📊 דוח מיפוי מאסטר - כל השיחות במסד הנתונים")
            print("=" * 80)
            print(f"🌐 Chrome: רגיל על פורט 9222")
            print(f"📱 סך שיחות ב-WhatsApp: {len(all_chats)}")
            print(f"📋 אנשי קשר מבוקשים: {len(self.requested_contacts)}")
            print(f"✅ התאמות שנמצאו: {len(matches)}")
            print(f"❌ לא נמצאו: {len(self.requested_contacts) - len(matches)}")
            print(f"💾 מסד נתונים: {self.db_path}")
            print(f"📄 דוח: {report_file}")
            
            if matches_by_company:
                print("\n✅ התאמות לפי חברות:")
                for company, company_matches in matches_by_company.items():
                    print(f"\n   🏢 {company} ({len(company_matches)} אנשי קשר):")
                    for match in company_matches:
                        confidence_text = f"({match['confidence']:.2f})" if match['confidence'] < 1.0 else ""
                        indicators = []
                        if match['chat_details']['unread_count'] > 0:
                            indicators.append(f"🔴{match['chat_details']['unread_count']}")
                        if match['chat_details']['is_pinned']:
                            indicators.append("📌")
                        if match['chat_details']['is_group']:
                            indicators.append("👥")
                        
                        indicator_text = ' '.join(indicators)
                        
                        print(f"      ✅ {match['requested_name']} {confidence_text}")
                        print(f"         📱 ב-WhatsApp: {match['whatsapp_name']} {indicator_text}")
                        if match['chat_details']['last_time']:
                            print(f"         🕐 פעילות: {match['chat_details']['last_time']}")
            
            if unmatched_by_company:
                print(f"\n❌ אנשי קשר שלא נמצאו ({sum(len(contacts) for contacts in unmatched_by_company.values())}):")
                for company, contacts in unmatched_by_company.items():
                    if contacts:
                        print(f"\n   🏢 {company} ({len(contacts)} אנשי קשר):")
                        for contact in contacts[:5]:  # מוגבל ל-5 ראשונים
                            print(f"      ❌ {contact}")
                        if len(contacts) > 5:
                            print(f"      ... ועוד {len(contacts) - 5} אנשי קשר")
            
            print(f"\n🎯 הערכת חילוץ:")
            total_potential_messages = sum(chat['unread_count'] for chat in all_chats if chat['unread_count'] > 0)
            print(f"   💬 הודעות פוטנציאליות לחילוץ: {total_potential_messages}")
            print(f"   📅 אנשי קשר מוכנים לאירועי יומן: {len(matches)}")
            
            return report
            
        except Exception as e:
            self.log(f"שגיאה ביצירת דוח: {str(e)}", "ERROR")
            return {}

    def create_extraction_plan(self, matches):
        """יצירת תוכנית חילוץ"""
        self.detailed_log("PLAN", "יוצר תוכנית חילוץ...")
        
        try:
            cursor = self.db.cursor()
            
            # עדכון כל ההתאמות שצריכות חילוץ
            for match in matches:
                cursor.execute("""
                    UPDATE extraction_status 
                    SET next_attempt_needed = TRUE,
                        last_attempt_date = datetime('now')
                    WHERE contact_name = ?
                """, (match["requested_name"],))
            
            self.db.commit()
            
            print(f"\n📋 תוכנית חילוץ:")
            print(f"   📝 {len(matches)} אנשי קשר מוכנים לחילוץ הודעות")
            print(f"   📅 {len(matches)} אנשי קשר מוכנים לאירועי יומן")
            print(f"   ⏳ הערכת זמן: {len(matches) * 2} דקות")
            
            return True
            
        except Exception as e:
            self.log(f"שגיאה ביצירת תוכנית: {str(e)}", "ERROR")
            return False

    def cleanup(self):
        """ניקוי משאבים"""
        self.detailed_log("CLEANUP", "מסיים ושומר חיבור Chrome רגיל...")
        
        if self.db:
            self.db.close()
        
        self.log("🔗 Chrome רגיל נשאר פתוח עם WhatsApp Web", "SUCCESS")

    def run(self):
        """הרצת כל התהליך"""
        try:
            self.log("🚀 מתחיל עדכון מסד נתונים עם כל השיחות")
            print("=" * 70)
            
            # יצירת מסד נתונים מאסטר
            if not self.create_master_database():
                raise Exception("נכשל ביצירת מסד נתונים")
            
            # התחברות ל-Chrome רגיל
            if not self.connect_to_chrome_regular():
                raise Exception("נכשל בחיבור ל-Chrome")
            
            # סריקה וקטלוג של כל השיחות
            all_chats = self.scan_and_catalog_all_chats()
            
            if not all_chats:
                raise Exception("לא נמצאו שיחות")
            
            # שמירת כל השיחות
            saved_count = self.save_all_chats_to_database(all_chats)
            
            # התאמה לאנשי קשר מבוקשים
            matches = self.match_chats_to_requested_contacts(all_chats)
            
            # זיהוי לא נמצאו
            unmatched = self.identify_unmatched_contacts()
            
            # יצירת דוח מקיף
            report = self.generate_comprehensive_mapping_report(all_chats, matches, unmatched)
            
            # תוכנית חילוץ
            self.create_extraction_plan(matches)
            
            self.log("🎉 עדכון מסד הנתונים הושלם בהצלחה!", "SUCCESS")
            
            return {
                "all_chats": all_chats,
                "matches": matches,
                "unmatched": unmatched,
                "report": report
            }
            
        except Exception as e:
            self.log(f"שגיאה בעדכון מסד נתונים: {str(e)}", "ERROR")
            return None
            
        finally:
            self.cleanup()

if __name__ == "__main__":
    updater = UpdateDatabaseWithAllChats()
    
    try:
        results = updater.run()
        
        if results:
            print("\n🎉 מסד הנתונים עודכן בהצלחה!")
            print("📊 כל השיחות קוטלגו ונשמרו")
            print("🎯 התאמות זוהו וסומנו")
            print("📋 תוכנית חילוץ מוכנה")
            print("🔗 Chrome רגיל נשאר מחובר")
        else:
            print("❌ עדכון מסד הנתונים נכשל")
            
    except Exception as error:
        print(f"❌ שגיאה: {str(error)}")
        print("💡 Chrome רגיל נשאר פתוח")













