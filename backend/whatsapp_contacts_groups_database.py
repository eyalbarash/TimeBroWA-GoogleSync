#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
מערכת מסד נתונים מתקדמת לאנשי קשר וקבוצות WhatsApp
כולל פרוצדורות עדכון אוטומטיות ודגלי timebro
"""

import sqlite3
import json
import requests
import os
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

class WhatsAppContactsGroupsDatabase:
    def __init__(self, db_path: str = "whatsapp_contacts_groups.db"):
        self.db_path = db_path
        self.api_base = "https://evolution.cigcrm.com"
        self.api_key = "A6401FCD5870-4CDB-87C4-6A22F06745CD"
        self.instance_id = "ebs"
        
        # רשימת אנשי הקשר בעדיפות למערכת timebro
        self.timebro_priority_contacts = [
            'מייק ביקוב / LBS',
            'סשה דיבקה', 
            'אלימלך בינשטוק / היתקשרות',
            'מוטי בראל (עבודה) / כפרי דרייב',
            'מוטי בראל / כפרי דרייב',
            'עדי גץ פניאל / MLY',
            'אופיר אריה',
            'מחלקת הטמעה Salesflow / ריקי רוזנברג',
            'שרון רייכטר - טיפול טכני ב crm',
            'צליל נויימן',
            'מיכל קולינגר / כפרי דרייב',
            'ישי גבנאן | יזם ומומחה למסחר באטסי',
            'ישי גביאן',
            'סיון דווידוביץ׳ כפרי דרייב',
            'שחר זכאי / fundit',
            'ג׳וליה סקסס קולג׳',
            'ענת שרייבר כוכבא / fundit',
            'איריס מנהלת משרד כפרי דרייב',
            'עמי ברעם / התרשרות',
            'ערן זלטקין / סולומון גרופ',
            'ספירת לידים סולומון / סולומון גרופ',
            'עדי הירש / טודו דזיין',
            'איילת הירש / טודו דזיין',
            'fital / טל מועלם',
            'ד״ר גיא נחמני',
            'אביעד כפרי דרייב',
            'מנדי מנהל קמפיינים של שביר פיננסיים',
            'עוז סושיאל כפרי',
            'דניאל דיקובסקי / xwear',
            'רנית גרנות / ד״ר גיא נחמני',
            'צחי כפרי / כפרי דרייב',
            'סיון דווידוביץ׳ פרטי / כפרי דרייב',
            'מכירות שרון / שרון רייכטר',
            'אושר חיים זדה / MLY',
            'קרן בן דוד ברנדס / MLY',
            'גיל שרון / MLY',
            'אורלי / לצאת לאור',
            'איריס יוגב / לצאת לאור',
            'גלעד אטיאס / כפרי דרייב',
            'מעבר חברה MINDCRM / סולומון גרופ',
            'דולב סוכן דרום / trichome',
            'נטע שלי / שתלתם',
            'דויד פורת / ריקי רוזנברג',
            'גדעון להב / אופיר אריה',
            'עומר דהאן / סשה דידקה',
            'אלעד דניאלי / שטורעם',
            'חלי אוטומציות / אניגמה',
            'דובי פורת',
            'אלדד וואטסאפ טריכום / trichome',
            'יהונתן לוי / אניגמה',
            'לי עמר / משה עמר',
            'משה עמר',
            'יהודה גולדמן',
            'מעיין פרץ / סולומון גרופ',
            'אבי ואלס / שרון רייכטר',
            'אורי קובץ / ישי גביאן',
            'איה סושיאל / ד״ר גיא נחמני',
            'אתי כהן / trichome',
            'גד טמיר',
            'יאיר אסולין / סולומון גרופ',
            'תומר טרייכום / trichome',
            'מיקה חברת מדיה סולומון / סולמון גרופ',
            'רותם סקסס קולג׳',
            'נדיה טרייכום / trichome',
            'עידן טרייכום / trichome',
            'אוטומציות LBS+אייל',
            'תמיכה טרייכום / trichome'
        ]
        
        self.init_database()

    def log(self, message: str, level: str = "INFO"):
        """רישום לוג עם חותמת זמן"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = {"SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}.get(level, "📊")
        print(f"[{timestamp}] {emoji} {message}")

    def init_database(self):
        """יצירת מסד הנתונים עם הטבלאות הדרושות"""
        self.log("יוצר מסד נתונים עם טבלאות מתקדמות...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # טבלת אנשי קשר מתקדמת
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                contact_id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number VARCHAR(20),
                whatsapp_id VARCHAR(100) UNIQUE,
                remote_jid VARCHAR(100) UNIQUE,
                name VARCHAR(255),
                push_name VARCHAR(255),
                profile_picture_url TEXT,
                is_business BOOLEAN DEFAULT FALSE,
                is_saved BOOLEAN DEFAULT FALSE,
                type VARCHAR(50),
                include_in_timebro BOOLEAN DEFAULT FALSE,
                timebro_priority INTEGER DEFAULT 0,
                company VARCHAR(255),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # טבלת קבוצות מתקדמת  
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY AUTOINCREMENT,
                whatsapp_group_id VARCHAR(100) UNIQUE NOT NULL,
                subject VARCHAR(255),
                description TEXT,
                picture_url TEXT,
                size INTEGER DEFAULT 0,
                creation BIGINT,
                subject_time BIGINT,
                subject_owner VARCHAR(100),
                owner VARCHAR(100),
                is_community BOOLEAN DEFAULT FALSE,
                is_community_announce BOOLEAN DEFAULT FALSE,
                restrict BOOLEAN DEFAULT FALSE,
                announce BOOLEAN DEFAULT FALSE,
                linked_parent VARCHAR(100),
                include_in_timebro BOOLEAN DEFAULT FALSE,
                timebro_priority INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # טבלת מיפוי אנשי קשר לקבוצות
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                contact_id INTEGER NOT NULL,
                role VARCHAR(20) DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (group_id) REFERENCES groups(group_id),
                FOREIGN KEY (contact_id) REFERENCES contacts(contact_id),
                UNIQUE(group_id, contact_id)
            )
        ''')
        
        # טבלת הגדרות timebro
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS timebro_settings (
                setting_id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                group_id INTEGER,
                setting_name VARCHAR(100),
                setting_value TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (contact_id) REFERENCES contacts(contact_id),
                FOREIGN KEY (group_id) REFERENCES groups(group_id)
            )
        ''')
        
        # יצירת אינדקסים
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_phone ON contacts(phone_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_whatsapp_id ON contacts(whatsapp_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_contacts_timebro ON contacts(include_in_timebro)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_groups_whatsapp_id ON groups(whatsapp_group_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_groups_timebro ON groups(include_in_timebro)')
        
        conn.commit()
        conn.close()
        
        self.log("מסד הנתונים נוצר בהצלחה", "SUCCESS")

    def normalize_phone_number(self, phone: str) -> str:
        """נורמליזציה של מספר טלפון"""
        if not phone:
            return ""
        
        # הסרת תווים לא רלוונטיים
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # הוספת קוד ישראל אם חסר
        if clean_phone.startswith('0'):
            clean_phone = '972' + clean_phone[1:]
        elif not clean_phone.startswith('972') and not clean_phone.startswith('+972'):
            if len(clean_phone) == 9:
                clean_phone = '972' + clean_phone
                
        # הסרת + אם קיים
        clean_phone = clean_phone.replace('+', '')
        
        return clean_phone

    def extract_phone_from_remote_jid(self, remote_jid: str) -> str:
        """חילוץ מספר טלפון מ-remote JID"""
        if not remote_jid:
            return ""
        
        # עבור אנשי קשר רגילים
        if '@s.whatsapp.net' in remote_jid:
            return remote_jid.split('@')[0]
        
        # עבור LinkedIn ID או ID אחרים
        if '@lid' in remote_jid:
            return ""  # אין מספר טלפון זמין
            
        return ""

    def load_contacts_from_json(self, file_path: str):
        """טעינת אנשי קשר מקובץ JSON"""
        self.log(f"טוען אנשי קשר מ-{file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                contacts_data = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            processed_count = 0
            
            for contact in contacts_data:
                try:
                    phone_number = self.extract_phone_from_remote_jid(contact.get('remoteJid', ''))
                    
                    # בדיקה אם זה איש קשר בעדיפות
                    name = contact.get('pushName', '') or ''
                    include_in_timebro = 0  # לא מסומן אוטומטית
                    priority = 0  # לא מסומן אוטומטית
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO contacts (
                            whatsapp_id, remote_jid, phone_number, name, push_name,
                            profile_picture_url, is_saved, type, include_in_timebro,
                            timebro_priority, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        contact.get('id', ''),
                        contact.get('remoteJid', ''),
                        phone_number,
                        name,
                        contact.get('pushName', ''),
                        contact.get('profilePicUrl', ''),
                        contact.get('isSaved', False),
                        contact.get('type', 'contact'),
                        include_in_timebro,
                        priority,
                        datetime.now().isoformat()
                    ))
                    
                    processed_count += 1
                    
                except Exception as e:
                    self.log(f"שגיאה בעיבוד איש קשר {contact.get('pushName', 'לא ידוע')}: {e}", "ERROR")
                    continue
            
            conn.commit()
            conn.close()
            
            self.log(f"עובדו {processed_count} אנשי קשר בהצלחה", "SUCCESS")
            return processed_count
            
        except Exception as e:
            self.log(f"שגיאה בטעינת אנשי קשר: {e}", "ERROR")
            return 0

    def load_groups_from_json(self, file_path: str):
        """טעינת קבוצות מקובץ JSON"""
        self.log(f"טוען קבוצות מ-{file_path}...")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                groups_data = json.load(f)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            processed_count = 0
            
            for group in groups_data:
                try:
                    subject = group.get('subject', '')
                    include_in_timebro = self.is_priority_group(subject)
                    priority = self.get_group_priority(subject)
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO groups (
                            whatsapp_group_id, subject, description, picture_url,
                            size, creation, subject_time, subject_owner, owner,
                            is_community, is_community_announce, restrict, announce,
                            linked_parent, include_in_timebro, timebro_priority,
                            updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        group.get('id', ''),
                        subject,
                        group.get('desc', ''),
                        group.get('pictureUrl', ''),
                        group.get('size', 0),
                        group.get('creation', 0),
                        group.get('subjectTime', 0),
                        group.get('subjectOwner', ''),
                        group.get('owner', ''),
                        group.get('isCommunity', False),
                        group.get('isCommunityAnnounce', False),
                        group.get('restrict', False),
                        group.get('announce', False),
                        group.get('linkedParent', ''),
                        include_in_timebro,
                        priority,
                        datetime.now().isoformat()
                    ))
                    
                    processed_count += 1
                    
                except Exception as e:
                    self.log(f"שגיאה בעיבוד קבוצה {group.get('subject', 'לא ידועה')}: {e}", "ERROR")
                    continue
            
            conn.commit()
            conn.close()
            
            self.log(f"עובדו {processed_count} קבוצות בהצלחה", "SUCCESS")
            return processed_count
            
        except Exception as e:
            self.log(f"שגיאה בטעינת קבוצות: {e}", "ERROR")
            return 0

    def is_priority_contact(self, name: str) -> bool:
        """בדיקה אם איש קשר נמצא ברשימת העדיפויות"""
        if not name:
            return False
            
        name_lower = name.lower()
        
        # בדיקה ישירה בשמות
        for priority_name in self.timebro_priority_contacts:
            if priority_name.lower() in name_lower or name_lower in priority_name.lower():
                return True
        
        # בדיקה במילות מפתח
        priority_keywords = [
            'מייק', 'mike', 'ביקוב', 'lbs',
            'סשה', 'דיבקה',
            'כפרי', 'דרייב', 'צחי',
            'עמר', 'משה', 'לי',
            'שתלתם', 'נטע', 'שלי',
            'fital', 'טל', 'מועלם',
            'אופיר', 'אריה',
            'סולומון', 'גרופ',
            'mly', 'גץ',
            'trichome', 'טריכום'
        ]
        
        for keyword in priority_keywords:
            if keyword in name_lower:
                return True
                
        return False

    def get_contact_priority(self, name: str) -> int:
        """מתן דרגת עדיפות לאיש קשר (1-10)"""
        if not name:
            return 0
            
        name_lower = name.lower()
        
        # עדיפות גבוהה
        if any(keyword in name_lower for keyword in ['מייק', 'mike', 'ביקוב']):
            return 10
        elif any(keyword in name_lower for keyword in ['צחי', 'כפרי']):
            return 9  
        elif any(keyword in name_lower for keyword in ['סשה', 'דיבקה']):
            return 8
        elif any(keyword in name_lower for keyword in ['עמר', 'משה', 'לי']):
            return 7
        elif any(keyword in name_lower for keyword in ['שתלתם', 'נטע']):
            return 6
        elif any(keyword in name_lower for keyword in ['fital', 'טל']):
            return 5
        
        # עדיפות בינונית
        elif any(keyword in name_lower for keyword in ['סולומון', 'mly', 'אופיר']):
            return 4
        elif any(keyword in name_lower for keyword in ['trichome', 'טריכום']):
            return 3
        elif any(keyword in name_lower for keyword in ['lbs', 'אוטומציות']):
            return 2
        
        return 1 if self.is_priority_contact(name) else 0

    def is_priority_group(self, subject: str) -> bool:
        """בדיקה אם קבוצה חשובה לtimebro"""
        if not subject:
            return False
            
        subject_lower = subject.lower()
        
        # קבוצות עבודה חשובות
        work_keywords = [
            'כפרי', 'דרייב', 'lbs', 'mly', 'סולומון',
            'אוטומציות', 'crm', 'מינדקרם', 'trichome',
            'fundit', 'salesflow', 'אניגמה'
        ]
        
        for keyword in work_keywords:
            if keyword in subject_lower:
                return True
                
        return False

    def get_group_priority(self, subject: str) -> int:
        """מתן דרגת עדיפות לקבוצה (1-5)"""
        if not subject:
            return 0
            
        subject_lower = subject.lower()
        
        # עדיפות גבוהה - קבוצות עבודה ישירות
        if any(keyword in subject_lower for keyword in ['כפרי', 'דרייב']):
            return 5
        elif any(keyword in subject_lower for keyword in ['lbs', 'אוטומציות']):
            return 4
        elif any(keyword in subject_lower for keyword in ['mly', 'סולומון']):
            return 3
        elif any(keyword in subject_lower for keyword in ['trichome', 'crm']):
            return 2
        
        return 1 if self.is_priority_group(subject) else 0

    def fetch_contacts_from_api(self) -> Dict:
        """שליפת אנשי קשר מ-API"""
        self.log("שולף אנשי קשר מ-Evolution API...")
        
        try:
            headers = {
                'apikey': self.api_key,
                'Content-Type': 'application/json'
            }
            
            data = {
                "where": {}
            }
            
            response = requests.post(
                f"{self.api_base}/chat/findContacts/{self.instance_id}",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"התקבלו {len(result)} אנשי קשר מ-API", "SUCCESS")
                return result
            else:
                self.log(f"שגיאה בשליפת אנשי קשר: {response.status_code}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"שגיאה בשליפת אנשי קשר מ-API: {e}", "ERROR")
            return []

    def fetch_groups_from_api(self) -> Dict:
        """שליפת קבוצות מ-API"""
        self.log("שולף קבוצות מ-Evolution API...")
        
        try:
            headers = {
                'apikey': self.api_key
            }
            
            response = requests.get(
                f"{self.api_base}/group/fetchAllGroups/{self.instance_id}",
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"התקבלו {len(result)} קבוצות מ-API", "SUCCESS")
                return result
            else:
                self.log(f"שגיאה בשליפת קבוצות: {response.status_code}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"שגיאה בשליפת קבוצות מ-API: {e}", "ERROR")
            return []

    def process_api_contacts(self, api_contacts: List[Dict]):
        """עיבוד אנשי קשר מ-API לתוך המסד"""
        self.log("מעבד אנשי קשר מ-API...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        processed_count = 0
        priority_count = 0
        
        for contact in api_contacts:
            try:
                phone_number = self.extract_phone_from_remote_jid(contact.get('remoteJid', ''))
                name = contact.get('pushName', '') or ''
                
                # ⚠️ לא מסמנים אוטומטית! סימון רק דרך ממשק Web
                include_in_timebro = 0  # תמיד 0 - סימון ידני בלבד
                priority = 0  # תמיד 0 - ללא עדיפות אוטומטית
                
                if include_in_timebro:
                    priority_count += 1
                
                # בדיקה אם הרשומה כבר קיימת
                cursor.execute('SELECT company_name FROM contacts WHERE whatsapp_id = ?', 
                              (contact.get('id', ''),))
                existing = cursor.fetchone()
                
                # קביעת company_name - אם כבר קיים ושונה, נשמור אותו
                if existing and existing[0] and existing[0] != name:
                    # כבר יש שם חברה מותאם אישית - נשמור אותו
                    new_company_name = existing[0]
                else:
                    # אין או זהה לשם - נעדכן לשם החדש
                    new_company_name = name if name else contact.get('pushName', '')
                
                # בדיקה אם הרשומה כבר קיימת לפי whatsapp_id
                cursor.execute('SELECT contact_id, company_name FROM contacts WHERE whatsapp_id = ?', 
                              (contact.get('id', ''),))
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # עדכון רשומה קיימת - שמירה על company_name אם שונה
                    existing_company_name = existing_record[1]
                    if existing_company_name and existing_company_name != name:
                        # יש שם חברה מותאם אישית - נשמור אותו
                        final_company_name = existing_company_name
                    else:
                        # עדכון לשם החדש
                        final_company_name = new_company_name
                    
                    cursor.execute('''
                        UPDATE contacts SET
                            remote_jid = ?, phone_number = ?, name = ?, push_name = ?,
                            profile_picture_url = ?, is_saved = ?, type = ?,
                            include_in_timebro = ?, timebro_priority = ?, company_name = ?, updated_at = ?
                        WHERE whatsapp_id = ?
                    ''', (
                        contact.get('remoteJid', ''),
                        phone_number,
                        name,
                        contact.get('pushName', ''),
                        contact.get('profilePicUrl', ''),
                        contact.get('isSaved', False),
                        contact.get('type', 'contact'),
                        include_in_timebro,
                        priority,
                        final_company_name,
                        datetime.now().isoformat(),
                        contact.get('id', '')
                    ))
                else:
                    # הוספת רשומה חדשה
                    cursor.execute('''
                        INSERT INTO contacts (
                            whatsapp_id, remote_jid, phone_number, name, push_name,
                            profile_picture_url, is_saved, type, include_in_timebro,
                            timebro_priority, company_name, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        contact.get('id', ''),
                        contact.get('remoteJid', ''),
                        phone_number,
                        name,
                        contact.get('pushName', ''),
                        contact.get('profilePicUrl', ''),
                        contact.get('isSaved', False),
                        contact.get('type', 'contact'),
                        include_in_timebro,
                        priority,
                        new_company_name,
                        datetime.now().isoformat()
                    ))
                
                processed_count += 1
                
            except Exception as e:
                self.log(f"שגיאה בעיבוד איש קשר {contact.get('pushName', 'לא ידוע')}: {e}", "ERROR")
                continue
        
        conn.commit()
        conn.close()
        
        self.log(f"עובדו {processed_count} אנשי קשר, {priority_count} בעדיפות timebro", "SUCCESS")
        return processed_count, priority_count

    def process_api_groups(self, api_groups: List[Dict]):
        """עיבוד קבוצות מ-API לתוך המסד"""
        self.log("מעבד קבוצות מ-API...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        processed_count = 0
        priority_count = 0
        
        for group in api_groups:
            try:
                subject = group.get('subject', '')
                
                # ⚠️ לא מסמנים אוטומטית! סימון רק דרך ממשק Web
                include_in_timebro = 0  # תמיד 0 - סימון ידני בלבד
                priority = 0  # תמיד 0 - ללא עדיפות אוטומטית
                
                if include_in_timebro:
                    priority_count += 1
                
                # בדיקה אם הרשומה כבר קיימת
                cursor.execute('SELECT company_name FROM groups WHERE whatsapp_group_id = ?', 
                              (group.get('id', ''),))
                existing = cursor.fetchone()
                
                # קביעת company_name - אם כבר קיים ושונה, נשמור אותו
                if existing and existing[0] and existing[0] != subject:
                    # כבר יש שם חברה מותאם אישית - נשמור אותו
                    new_company_name = existing[0]
                else:
                    # אין או זהה לשם - נעדכן לשם החדש
                    new_company_name = subject
                
                cursor.execute('''
                    INSERT OR REPLACE INTO groups (
                        whatsapp_group_id, subject, description, picture_url,
                        size, creation, subject_time, subject_owner, owner,
                        is_community, is_community_announce, restrict, announce,
                        linked_parent, include_in_timebro, timebro_priority,
                        company_name, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    group.get('id', ''),
                    subject,
                    group.get('desc', ''),
                    group.get('pictureUrl', ''),
                    group.get('size', 0),
                    group.get('creation', 0),
                    group.get('subjectTime', 0),
                    group.get('subjectOwner', ''),
                    group.get('owner', ''),
                    group.get('isCommunity', False),
                    group.get('isCommunityAnnounce', False),
                    group.get('restrict', False),
                    group.get('announce', False),
                    group.get('linkedParent', ''),
                    include_in_timebro,
                    priority,
                    new_company_name,
                    datetime.now().isoformat()
                ))
                
                processed_count += 1
                
            except Exception as e:
                self.log(f"שגיאה בעיבוד קבוצה {group.get('subject', 'לא ידועה')}: {e}", "ERROR")
                continue
        
        conn.commit()
        conn.close()
        
        self.log(f"עובדו {processed_count} קבוצות, {priority_count} בעדיפות timebro", "SUCCESS")
        return processed_count, priority_count

    def update_from_json_files(self):
        """עדכון מקבצי JSON קיימים"""
        self.log("מעדכן מסד נתונים מקבצי JSON קיימים...")
        
        # עדכון אנשי קשר
        contacts_file = "findContactsResults.json"
        if os.path.exists(contacts_file):
            contacts_count, contacts_priority = self.process_api_contacts(
                json.load(open(contacts_file, 'r', encoding='utf-8'))
            )
        else:
            self.log(f"קובץ {contacts_file} לא נמצא", "WARNING")
            contacts_count, contacts_priority = 0, 0
        
        # עדכון קבוצות
        groups_file = "fetchAppGroupsResults.json"
        if os.path.exists(groups_file):
            groups_count, groups_priority = self.process_api_groups(
                json.load(open(groups_file, 'r', encoding='utf-8'))
            )
        else:
            self.log(f"קובץ {groups_file} לא נמצא", "WARNING")
            groups_count, groups_priority = 0, 0
        
        return {
            'contacts_processed': contacts_count,
            'contacts_priority': contacts_priority,
            'groups_processed': groups_count,
            'groups_priority': groups_priority
        }

    def update_from_api(self):
        """עדכון חי מ-API"""
        self.log("מעדכן מסד נתונים מ-API...")
        
        # שליפת נתונים חדשים
        api_contacts = self.fetch_contacts_from_api()
        api_groups = self.fetch_groups_from_api()
        
        # שמירת קבצי גיבוי עדכניים
        if api_contacts:
            with open('findContactsResults.json', 'w', encoding='utf-8') as f:
                json.dump(api_contacts, f, ensure_ascii=False, indent=2)
        
        if api_groups:
            with open('fetchAppGroupsResults.json', 'w', encoding='utf-8') as f:
                json.dump(api_groups, f, ensure_ascii=False, indent=2)
        
        # עיבוד לתוך המסד
        contacts_count, contacts_priority = self.process_api_contacts(api_contacts)
        groups_count, groups_priority = self.process_api_groups(api_groups)
        
        return {
            'contacts_processed': contacts_count,
            'contacts_priority': contacts_priority,
            'groups_processed': groups_count,
            'groups_priority': groups_priority
        }

    def get_timebro_priority_list(self) -> Dict:
        """קבלת רשימה מעודכנת של אנשי קשר וקבוצות בעדיפות"""
        self.log("יוצר רשימה מעודכנת לtimebro...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # אנשי קשר בעדיפות
        cursor.execute('''
            SELECT name, phone_number, remote_jid, timebro_priority
            FROM contacts 
            WHERE include_in_timebro = 1
            ORDER BY timebro_priority DESC, name
        ''')
        priority_contacts = cursor.fetchall()
        
        # קבוצות בעדיפות
        cursor.execute('''
            SELECT subject, whatsapp_group_id, timebro_priority
            FROM groups 
            WHERE include_in_timebro = 1
            ORDER BY timebro_priority DESC, subject
        ''')
        priority_groups = cursor.fetchall()
        
        conn.close()
        
        # יצירת רשימה מעוצבת
        result = {
            'contacts': [
                {
                    'name': row[0],
                    'phone': row[1],
                    'whatsapp_id': row[2],
                    'priority': row[3]
                } for row in priority_contacts
            ],
            'groups': [
                {
                    'name': row[0],
                    'group_id': row[1],
                    'priority': row[2]
                } for row in priority_groups
            ],
            'timestamp': datetime.now().isoformat(),
            'total_contacts': len(priority_contacts),
            'total_groups': len(priority_groups)
        }
        
        self.log(f"נמצאו {len(priority_contacts)} אנשי קשר ו-{len(priority_groups)} קבוצות בעדיפות", "SUCCESS")
        
        return result

    def generate_report(self) -> str:
        """יצירת דוח מקיף על מסד הנתונים"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # סטטיסטיקות כלליות
        cursor.execute('SELECT COUNT(*) FROM contacts')
        total_contacts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM contacts WHERE include_in_timebro = 1')
        timebro_contacts = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM groups')
        total_groups = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM groups WHERE include_in_timebro = 1')
        timebro_groups = cursor.fetchone()[0]
        
        conn.close()
        
        report = f"""
📊 דוח מסד נתונים WhatsApp
═══════════════════════════════

👥 אנשי קשר:
   • סה"כ: {total_contacts:,}
   • בעדיפות timebro: {timebro_contacts}
   • אחוז עדיפות: {(timebro_contacts/total_contacts*100):.1f}%

🏠 קבוצות:
   • סה"כ: {total_groups:,}  
   • בעדיפות timebro: {timebro_groups}
   • אחוז עדיפות: {(timebro_groups/total_groups*100):.1f}%

⏰ עודכן: {datetime.now().strftime('%d/%m/%Y %H:%M')}
        """
        
        return report.strip()

    def run_full_update(self):
        """הרצת עדכון מלא מ-API וקבצים קיימים"""
        self.log("🚀 מתחיל עדכון מלא של מסד הנתונים...")
        
        # עדכון מקבצים קיימים
        json_results = self.update_from_json_files()
        
        # עדכון מ-API
        try:
            api_results = self.update_from_api()
        except Exception as e:
            self.log(f"שגיאה בעדכון מ-API: {e}", "ERROR")
            api_results = {'contacts_processed': 0, 'contacts_priority': 0, 'groups_processed': 0, 'groups_priority': 0}
        
        # קבלת רשימת עדיפויות מעודכנת
        priority_list = self.get_timebro_priority_list()
        
        # יצירת דוח
        report = self.generate_report()
        
        self.log("🎉 עדכון מלא הושלם בהצלחה!", "SUCCESS")
        
        return {
            'json_results': json_results,
            'api_results': api_results,
            'priority_list': priority_list,
            'report': report
        }

if __name__ == "__main__":
    db_manager = WhatsAppContactsGroupsDatabase()
    results = db_manager.run_full_update()
    
    print("\n" + "="*50)
    print(results['report'])
    print("\n" + "="*50)
    
    # הדפסת רשימת עדיפויות
    priority = results['priority_list']
    print(f"\n🎯 רשימת עדיפות timebro מעודכנת:")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    print(f"\n👥 אנשי קשר בעדיפות ({len(priority['contacts'])}):")
    for contact in priority['contacts']:
        print(f"   • {contact['name']} (עדיפות: {contact['priority']})")
        if contact['phone']:
            print(f"     📞 {contact['phone']}")
    
    print(f"\n🏠 קבוצות בעדיפות ({len(priority['groups'])}):")
    for group in priority['groups']:
        print(f"   • {group['name']} (עדיפות: {group['priority']})")







