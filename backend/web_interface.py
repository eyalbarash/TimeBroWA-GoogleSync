#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ממשק Web לניהול טבלאות Contacts ו-Groups
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import json
import urllib.parse
import time
import logging
from datetime import datetime
import os
import re
from sync_manager import SyncManager
from credential_manager import GreenAPICredentials
from green_api_client import GreenAPITester
from auth_manager import init_auth_manager, require_auth, get_current_user

# Register REGEXP function for SQLite
def regexp(pattern, string):
    """Custom REGEXP function for SQLite"""
    if string is None:
        return False
    return re.search(pattern, string) is not None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('group_deletion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class DatabaseManager:
    def __init__(self):
        self.contacts_db = "whatsapp_contacts_groups.db"
        self.groups_db = "whatsapp_contacts_groups.db"
        self.calendar_db = "timebro_calendar.db"
    
    def search_contacts(self, search_term="", phone_filter="", date_from="", date_to="", 
                       include_calendar_only=False, israeli_only=False, business_only=False,
                       personal_only=False, page=1, per_page=50):
        """חיפוש אנשי קשר עם פילטרים"""
        try:
            conn = sqlite3.connect(self.contacts_db)
            # Register custom REGEXP function
            conn.create_function("REGEXP", 2, regexp)
            cursor = conn.cursor()
            
            # בניית שאילתה
            where_conditions = []
            params = []
            
            # פילטר בסיסי - הסתרת רשומות ריקות לחלוטין
            # חייב להיות לפחות שם תקין (לא רק מספרים או תווים מיוחדים)
            where_conditions.append("(name IS NOT NULL AND name != '' AND name NOT REGEXP '^[0-9]+$' AND LENGTH(TRIM(name)) > 2 OR push_name IS NOT NULL AND push_name != '')")
            
            if search_term:
                # חיפוש גם לפי שם חברה
                where_conditions.append("(name LIKE ? OR push_name LIKE ? OR phone_number LIKE ? OR company_name LIKE ?)")
                params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
            
            if phone_filter:
                # חיפוש טלפון - עם ובלי קידומת מדינה
                # לדוגמה: 0549990001 ימצא גם 972549990001
                # יצירת תבניות חיפוש: המקור + המקור עם 972 + המקור עם 0
                phone_variations = [
                    f"%{phone_filter}%",  # המקור
                    f"%972{phone_filter}%",  # עם 972
                    f"%0{phone_filter}%",  # עם 0
                ]
                # יצירת תנאי OR לכל הגרסאות
                phone_conditions = " OR ".join(["phone_number LIKE ?" for _ in phone_variations])
                where_conditions.append(f"({phone_conditions})")
                params.extend(phone_variations)
            
            if date_from:
                where_conditions.append("DATE(created_at) >= ?")
                params.append(date_from)
            
            if date_to:
                where_conditions.append("DATE(created_at) <= ?")
                params.append(date_to)
            
            if include_calendar_only:
                # חיפוש גם באנשי קשר וגם בקבוצות
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # הוספת פילטר אנשי קשר אישיים
                if personal_only:
                    # אנשי קשר אישיים = שמורים בוואטסאפ עם שם אמיתי או שיש להם שם ב-Google Contacts
                    # חייב להיות שם אמיתי (לא ריק) ומספר טלפון
                    where_clause += " AND ((is_saved = 1 AND (name IS NOT NULL AND name != '' OR push_name IS NOT NULL AND push_name != '')) OR (google_contact_name IS NOT NULL AND google_contact_name != '')) AND phone_number IS NOT NULL AND phone_number != ''"
                
                # ספירת תוצאות - אנשי קשר
                count_query_contacts = f"SELECT COUNT(*) FROM contacts WHERE {where_clause} AND include_in_timebro = 1 AND type = 'contact'"
                cursor.execute(count_query_contacts, params)
                contacts_count = cursor.fetchone()[0]
                
                # ספירת תוצאות - קבוצות
                count_query_groups = f"SELECT COUNT(*) FROM groups WHERE include_in_timebro = 1"
                if search_term:
                    # חיפוש גם לפי שם חברה בקבוצות
                    count_query_groups += " AND (subject LIKE ? OR description LIKE ? OR company_name LIKE ?)"
                    group_params = [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
                else:
                    group_params = []
                cursor.execute(count_query_groups, group_params)
                groups_count = cursor.fetchone()[0]
                
                total_results = contacts_count + groups_count
                
                # שאילתת נתונים - אנשי קשר
                offset = (page - 1) * per_page
                query_contacts = f"""
                    SELECT contact_id, whatsapp_id, phone_number, 
                           COALESCE(NULLIF(name, ''), NULLIF(push_name, ''), NULLIF(phone_number, ''), whatsapp_id) as name,
                           push_name,
                           is_business, is_saved, type, include_in_timebro, timebro_priority,
                           created_at, updated_at, company_name, google_contact_name, whatsapp_personal_name
                    FROM contacts 
                    WHERE {where_clause} AND include_in_timebro = 1 AND type = 'contact'
                    ORDER BY COALESCE(NULLIF(name, ''), NULLIF(push_name, ''), NULLIF(phone_number, ''), '~')
                """
                
                # שאילתת נתונים - קבוצות
                query_groups = """
                    SELECT group_id as contact_id, whatsapp_group_id as whatsapp_id, '' as phone_number,
                           subject as name, '' as push_name,
                           0 as is_business, 0 as is_saved, 'group' as type, 
                           include_in_timebro, timebro_priority,
                           created_at, updated_at, company_name, '' as google_contact_name, '' as whatsapp_personal_name
                    FROM groups 
                    WHERE include_in_timebro = 1
                """
                # הוספת תנאי חיפוש לקבוצות גם
                if search_term:
                    query_groups += " AND (subject LIKE ? OR description LIKE ? OR company_name LIKE ?)"
                query_groups += " ORDER BY subject"
                
                # ביצוע השאילתות
                cursor.execute(query_contacts, params)
                contacts_results = cursor.fetchall()
                
                # הכנת פרמטרים לקבוצות
                group_params = []
                if search_term:
                    group_params = [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
                
                if search_term:
                    cursor.execute(query_groups, group_params)
                else:
                    cursor.execute(query_groups)
                groups_results = cursor.fetchall()
                
                # שילוב התוצאות
                all_results = contacts_results + groups_results
                
                # pagination ידני
                start_idx = (page - 1) * per_page
                end_idx = start_idx + per_page
                results = all_results[start_idx:end_idx]
            else:
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # הוספת פילטר אנשי קשר אישיים
                if personal_only:
                    # אנשי קשר אישיים = שמורים בוואטסאפ עם שם אמיתי או שיש להם שם ב-Google Contacts
                    # חייב להיות שם אמיתי (לא ריק) ומספר טלפון
                    where_clause += " AND ((is_saved = 1 AND (name IS NOT NULL AND name != '' OR push_name IS NOT NULL AND push_name != '')) OR (google_contact_name IS NOT NULL AND google_contact_name != '')) AND phone_number IS NOT NULL AND phone_number != ''"
                
                # ספירת תוצאות
                count_query = f"SELECT COUNT(*) FROM contacts WHERE {where_clause}"
                cursor.execute(count_query, params)
                total_results = cursor.fetchone()[0]
                
                # שאילתת נתונים עם pagination
                offset = (page - 1) * per_page
                query = f"""
                    SELECT contact_id, whatsapp_id, phone_number, 
                           COALESCE(NULLIF(name, ''), NULLIF(push_name, ''), NULLIF(phone_number, ''), whatsapp_id) as name,
                           push_name,
                           is_business, is_saved, type, include_in_timebro, timebro_priority,
                           created_at, updated_at, company_name, google_contact_name, whatsapp_personal_name
                    FROM contacts 
                    WHERE {where_clause}
                    ORDER BY COALESCE(NULLIF(name, ''), NULLIF(push_name, ''), NULLIF(phone_number, ''), '~')
                    LIMIT ? OFFSET ?
                """
                params.extend([per_page, offset])
                
                cursor.execute(query, params)
                results = cursor.fetchall()
            
            # המרה לרשימת dictionaries
            columns = ['contact_id', 'whatsapp_id', 'phone_number', 'name', 'push_name',
                      'is_business', 'is_saved', 'type', 'include_in_timebro', 'timebro_priority',
                      'created_at', 'updated_at', 'company_name', 'google_contact_name', 'whatsapp_personal_name']
            
            contacts = []
            for row in results:
                contact = dict(zip(columns, row))
                contacts.append(contact)
            
            conn.close()
            
            return {
                'contacts': contacts,
                'total': total_results,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_results + per_page - 1) // per_page
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def search_groups(self, search_term="", date_from="", date_to="", 
                     include_calendar_only=False, page=1, per_page=50):
        """חיפוש קבוצות עם פילטרים"""
        try:
            conn = sqlite3.connect(self.groups_db)
            cursor = conn.cursor()
            
            # בניית שאילתה
            where_conditions = []
            params = []
            
            if search_term:
                where_conditions.append("(subject LIKE ? OR description LIKE ?)")
                params.extend([f"%{search_term}%", f"%{search_term}%"])
            
            if date_from:
                where_conditions.append("DATE(created_at) >= ?")
                params.append(date_from)
            
            if date_to:
                where_conditions.append("DATE(created_at) <= ?")
                params.append(date_to)
            
            if include_calendar_only:
                where_conditions.append("include_in_timebro = 1")
            
            where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
            
            # ספירת תוצאות
            count_query = f"SELECT COUNT(*) FROM groups WHERE {where_clause}"
            cursor.execute(count_query, params)
            total_results = cursor.fetchone()[0]
            
            # שאילתת נתונים עם pagination
            offset = (page - 1) * per_page
            query = f"""
                SELECT group_id, whatsapp_group_id, subject, description, size, owner, created_at,
                       updated_at, include_in_timebro, timebro_priority, company_name
                FROM groups 
                WHERE {where_clause}
                ORDER BY subject
                LIMIT ? OFFSET ?
            """
            params.extend([per_page, offset])
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # המרה לרשימת dictionaries
            columns = ['group_id', 'whatsapp_group_id', 'subject', 'description', 'size', 'owner', 'created_at',
                      'updated_at', 'include_in_timebro', 'timebro_priority', 'company_name']
            
            groups = []
            for row in results:
                group = dict(zip(columns, row))
                groups.append(group)
            
            conn.close()
            
            return {
                'groups': groups,
                'total': total_results,
                'page': page,
                'per_page': per_page,
                'total_pages': (total_results + per_page - 1) // per_page
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def update_contact_calendar_status(self, contact_id, add_to_calendar):
        """עדכון סטטוס include_in_timebro של איש קשר"""
        try:
            conn = sqlite3.connect(self.contacts_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE contacts 
                SET include_in_timebro = ?, updated_at = CURRENT_TIMESTAMP
                WHERE contact_id = ?
            """, (add_to_calendar, contact_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def update_contact_company_name(self, contact_id, company_name):
        """עדכון שם חברה של איש קשר"""
        try:
            conn = sqlite3.connect(self.contacts_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE contacts 
                SET company_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE contact_id = ?
            """, (company_name, contact_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def update_group_calendar_status(self, group_id, add_to_calendar):
        """עדכון סטטוס include_in_timebro של קבוצה"""
        try:
            conn = sqlite3.connect(self.groups_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE groups 
                SET include_in_timebro = ?, updated_at = CURRENT_TIMESTAMP
                WHERE group_id = ?
            """, (add_to_calendar, group_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def update_group_company_name(self, group_id, company_name):
        """עדכון שם חברה של קבוצה"""
        try:
            conn = sqlite3.connect(self.groups_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE groups 
                SET company_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE group_id = ?
            """, (company_name, group_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def update_contact_google_contact_name(self, contact_id, google_contact_name):
        """עדכון שם Google Contact של איש קשר"""
        try:
            conn = sqlite3.connect(self.contacts_db)
            cursor = conn.cursor()
            
            # בדיקה אם השדה קיים, אם לא - נוסיף אותו
            cursor.execute("PRAGMA table_info(contacts)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'google_contact_name' not in columns:
                cursor.execute("ALTER TABLE contacts ADD COLUMN google_contact_name TEXT")
            
            cursor.execute("""
                UPDATE contacts 
                SET google_contact_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE contact_id = ?
            """, (google_contact_name, contact_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def update_contact_whatsapp_name(self, contact_id, whatsapp_name):
        """עדכון שם וואטסאפ של איש קשר"""
        try:
            conn = sqlite3.connect(self.contacts_db)
            cursor = conn.cursor()
            
            # בדיקה אם השדה קיים, אם לא - נוסיף אותו
            cursor.execute("PRAGMA table_info(contacts)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'whatsapp_personal_name' not in columns:
                cursor.execute("ALTER TABLE contacts ADD COLUMN whatsapp_personal_name TEXT")
            
            cursor.execute("""
                UPDATE contacts 
                SET whatsapp_personal_name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE contact_id = ?
            """, (whatsapp_name, contact_id))
            
            conn.commit()
            conn.close()
            
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}
    
    def add_contact_to_google(self, contact_id, name, phone, company, email):
        """הוספת איש קשר ל-Google Contacts"""
        try:
            conn = sqlite3.connect(self.contacts_db)
            cursor = conn.cursor()
            
            # עדכון השדות במסד הנתונים
            cursor.execute("""
                UPDATE contacts 
                SET google_contact_name = ?, 
                    company_name = COALESCE(company_name, ?),
                    updated_at = CURRENT_TIMESTAMP
                WHERE contact_id = ?
            """, (name, company, contact_id))
            
            conn.commit()
            conn.close()
            
            # כאן תהיה אינטגרציה עם Google Contacts API
            # כרגע זה רק סימולציה
            logger.info(f"הוספת איש קשר ל-Google: {name} ({phone})")
            
            return {
                'success': True, 
                'message': f'איש הקשר {name} נוסף ל-Google Contacts בהצלחה',
                'google_contact_id': f'google_{contact_id}_{int(time.time())}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_group(self, group_id):
        """מחיקת קבוצה מהמסד הנתונים"""
        try:
            conn = sqlite3.connect(self.groups_db)
            cursor = conn.cursor()
            
            # בדיקה אם הקבוצה קיימת
            cursor.execute("SELECT name FROM groups WHERE id = ?", (group_id,))
            group = cursor.fetchone()
            
            if not group:
                conn.close()
                return {'success': False, 'error': 'הקבוצה לא נמצאה'}
            
            # מחיקת הקבוצה
            cursor.execute("DELETE FROM groups WHERE id = ?", (group_id,))
            
            conn.commit()
            conn.close()
            
            return {'success': True, 'message': f'הקבוצה "{group[0]}" נמחקה בהצלחה'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_statistics(self):
        """קבלת סטטיסטיקות כלליות"""
        stats = {}
        
        try:
            conn = sqlite3.connect(self.contacts_db)
            cursor = conn.cursor()
            
            # סטטיסטיקות אנשי קשר
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'contact'")
            stats['total_contacts'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'contact' AND include_in_timebro = 1")
            stats['contacts_in_calendar'] = cursor.fetchone()[0]
            
            # סטטיסטיקות קבוצות
            cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'group'")
            stats['total_groups'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM groups WHERE include_in_timebro = 1")
            stats['groups_in_calendar'] = cursor.fetchone()[0]
            
            # בדיקה אם יש שדה is_israeli
            cursor.execute("PRAGMA table_info(contacts)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'is_israeli' in columns:
                cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'contact' AND is_israeli = 1")
                stats['israeli_contacts'] = cursor.fetchone()[0]
            else:
                # חישוב ישראלים לפי קידומת 972
                cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'contact' AND phone_number LIKE '972%'")
                stats['israeli_contacts'] = cursor.fetchone()[0]
            
            conn.close()
        except Exception as e:
            print(f"⚠️ שגיאה בסטטיסטיקות: {e}")
            stats['total_contacts'] = 0
            stats['contacts_in_calendar'] = 0
            stats['total_groups'] = 0
            stats['groups_in_calendar'] = 0
            stats['israeli_contacts'] = 0
        
        # סטטיסטיקות סינכרון
        try:
            calendar_conn = sqlite3.connect(self.calendar_db)
            calendar_cursor = calendar_conn.cursor()
            
            # ספירת אירועים שנוצרו
            calendar_cursor.execute("SELECT COUNT(*) FROM calendar_events")
            stats['total_calendar_events'] = calendar_cursor.fetchone()[0]
            
            # אירועים מהתקופה האחרונה (30 יום)
            from datetime import datetime, timedelta
            thirty_days_ago = datetime.now() - timedelta(days=30)
            calendar_cursor.execute("SELECT COUNT(*) FROM calendar_events WHERE created_at >= ?", (thirty_days_ago,))
            stats['recent_calendar_events'] = calendar_cursor.fetchone()[0]
            
            # אירועים מאוגוסט 2025
            august_2025 = datetime(2025, 8, 1)
            calendar_cursor.execute("SELECT COUNT(*) FROM calendar_events WHERE created_at >= ?", (august_2025,))
            stats['august_2025_events'] = calendar_cursor.fetchone()[0]
            
            # בדיקת סטטוס סינכרון אחרון
            calendar_cursor.execute("SELECT last_sync, messages_count, events_count FROM sync_status ORDER BY last_sync DESC LIMIT 1")
            last_sync = calendar_cursor.fetchone()
            if last_sync:
                stats['last_sync_date'] = last_sync[0]
                stats['last_sync_messages'] = last_sync[1] or 0
                stats['last_sync_events'] = last_sync[2] or 0
            else:
                stats['last_sync_date'] = None
                stats['last_sync_messages'] = 0
                stats['last_sync_events'] = 0
            
            calendar_conn.close()
        except Exception as e:
            print(f"⚠️ שגיאה בסטטיסטיקות יומן: {e}")
            stats['total_calendar_events'] = 0
            stats['recent_calendar_events'] = 0
            stats['august_2025_events'] = 0
            stats['last_sync_date'] = None
            stats['last_sync_messages'] = 0
            stats['last_sync_events'] = 0
        
        return stats

# יצירת מופע של מנהל הנתונים
db_manager = DatabaseManager()

# יצירת מופע של מנהל הסינכרון - רק כשצריך
sync_manager = None

def get_sync_manager():
    """יצירת SyncManager רק כשצריך"""
    global sync_manager
    if sync_manager is None:
        try:
            sync_manager = SyncManager()
        except Exception as e:
            print(f"⚠️ לא ניתן ליצור מנהל סינכרון: {e}")
            return None
    return sync_manager

@app.route('/')
def index():
    """עמוד ראשי"""
    stats = db_manager.get_statistics()
    return render_template('index.html', stats=stats)

@app.route('/contacts')
def contacts():
    """עמוד ניהול אנשי קשר"""
    return render_template('contacts.html')

@app.route('/groups')
def groups():
    """עמוד ניהול קבוצות"""
    return render_template('groups.html')

@app.route('/api/search/contacts')
def api_search_contacts():
    """API לחיפוש אנשי קשר"""
    search_term = urllib.parse.unquote_plus(request.args.get('search', ''))
    phone_filter = request.args.get('phone', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    # תמיכה גם ב-include_calendar_only וגם ב-calendar_only
    include_calendar_only = (request.args.get('include_calendar_only', request.args.get('calendar_only', 'false'))).lower() == 'true'
    israeli_only = request.args.get('israeli_only', 'false').lower() == 'true'
    business_only = request.args.get('business_only', 'false').lower() == 'true'
    personal_only = request.args.get('personal_only', 'false').lower() == 'true'
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    result = db_manager.search_contacts(
        search_term, phone_filter, date_from, date_to, 
        include_calendar_only, israeli_only, business_only, personal_only, page, per_page
    )
    
    return jsonify(result)

@app.route('/api/search/groups')
def api_search_groups():
    """API לחיפוש קבוצות"""
    search_term = urllib.parse.unquote_plus(request.args.get('search', ''))
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    include_calendar_only = request.args.get('calendar_only', 'false').lower() == 'true'
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 50))
    
    result = db_manager.search_groups(
        search_term, date_from, date_to, 
        include_calendar_only, page, per_page
    )
    
    return jsonify(result)

@app.route('/api/update/contact/<contact_id>', methods=['POST'])
def api_update_contact(contact_id):
    """API לעדכון סטטוס איש קשר"""
    data = request.get_json()
    add_to_calendar = data.get('include_in_timebro', False)
    
    result = db_manager.update_contact_calendar_status(contact_id, add_to_calendar)
    return jsonify(result)

@app.route('/api/update/group/<group_id>', methods=['POST'])
def api_update_group(group_id):
    """API לעדכון סטטוס קבוצה"""
    data = request.get_json()
    add_to_calendar = data.get('include_in_timebro', False)
    
    result = db_manager.update_group_calendar_status(group_id, add_to_calendar)
    return jsonify(result)

@app.route('/api/update/contact/<contact_id>/company', methods=['POST'])
def api_update_contact_company(contact_id):
    """API לעדכון שם חברה של איש קשר"""
    data = request.get_json()
    company_name = data.get('company_name', '')
    
    result = db_manager.update_contact_company_name(contact_id, company_name)
    return jsonify(result)

@app.route('/api/update/group/<group_id>/company', methods=['POST'])
def api_update_group_company(group_id):
    """API לעדכון שם חברה של קבוצה"""
    data = request.get_json()
    company_name = data.get('company_name', '')
    
    result = db_manager.update_group_company_name(group_id, company_name)
    return jsonify(result)

@app.route('/api/update/contact/<contact_id>/google_contact', methods=['POST'])
def api_update_contact_google_contact(contact_id):
    """API לעדכון שם Google Contact של איש קשר"""
    data = request.get_json()
    google_contact_name = data.get('google_contact', '')
    
    result = db_manager.update_contact_google_contact_name(contact_id, google_contact_name)
    return jsonify(result)

@app.route('/api/update/contact/<contact_id>/whatsapp_name', methods=['POST'])
def api_update_contact_whatsapp_name(contact_id):
    """API לעדכון שם וואטסאפ של איש קשר"""
    data = request.get_json()
    whatsapp_name = data.get('whatsapp_name', '')
    
    result = db_manager.update_contact_whatsapp_name(contact_id, whatsapp_name)
    return jsonify(result)

@app.route('/api/add-to-google/<contact_id>', methods=['POST'])
def api_add_to_google(contact_id):
    """API להוספת איש קשר ל-Google Contacts"""
    data = request.get_json()
    name = data.get('name', '')
    phone = data.get('phone', '')
    company = data.get('company', '')
    email = data.get('email', '')
    
    try:
        # הוספה ל-Google Contacts (סימולציה)
        # בפועל כאן תהיה אינטגרציה עם Google Contacts API
        result = db_manager.add_contact_to_google(contact_id, name, phone, company, email)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def api_stats():
    """API לקבלת סטטיסטיקות"""
    return jsonify(db_manager.get_statistics())

@app.route('/api/status')
def api_status():
    """API לבדיקת סטטוס השרת"""
    return jsonify({'status': 'ok', 'message': 'Backend is running'})

# Initialize authentication BEFORE defining routes that use @require_auth
auth_manager = init_auth_manager(
    secret_key=os.getenv('SECRET_KEY', 'your-secret-key-change-in-production'),
    admin_email=os.getenv('ADMIN_EMAIL', 'admin@cig.chat'),
    admin_password_hash=os.getenv('ADMIN_PASSWORD_HASH', 'default-hash-change-in-production')
)

# Green API Credential Management
green_api_credentials = GreenAPICredentials()
green_api_tester = GreenAPITester(green_api_credentials.credential_manager)

# Authentication endpoints
@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login endpoint"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        token = auth_manager.authenticate(email, password)
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Invalid credentials'
            }), 401
        
        response = jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': {
                'email': email,
                'role': 'admin'
            }
        })
        
        # Set secure cookie
        response.set_cookie(
            'auth_token',
            token,
            httponly=True,
            secure=True,
            samesite='Strict',
            max_age=86400  # 24 hours
        )
        
        return response
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Login failed: {str(e)}'
        }), 500

@app.route('/admin/logout', methods=['POST'])
@require_auth
def admin_logout():
    """Admin logout endpoint"""
    response = jsonify({
        'success': True,
        'message': 'Logout successful'
    })
    
    # Clear cookie
    response.set_cookie('auth_token', '', expires=0)
    
    return response

@app.route('/admin/me', methods=['GET'])
@require_auth
def admin_profile():
    """Get current admin profile"""
    user = get_current_user()
    return jsonify({
        'success': True,
        'user': {
            'email': user['email'],
            'role': 'admin',
            'expires_at': user['exp']
        }
    })

@app.route('/admin/verify', methods=['GET'])
@require_auth
def verify_auth():
    """Verify authentication status"""
    return jsonify({
        'success': True,
        'authenticated': True,
        'message': 'Token is valid'
    })

@app.route('/api/green-api/credentials', methods=['GET'])
def api_get_green_api_credentials():
    """API לקבלת סטטוס הרשאות Green API"""
    has_creds = green_api_credentials.has_credentials()
    if has_creds:
        creds = green_api_credentials.get_credentials()
        return jsonify({
            'has_credentials': True,
            'instance_id': creds.get('instance_id'),
            'saved_at': creds.get('saved_at'),
            'status': 'configured'
        })
    else:
        return jsonify({
            'has_credentials': False,
            'status': 'not_configured'
        })

@app.route('/api/green-api/credentials', methods=['POST'])
def api_save_green_api_credentials():
    """API לשמירת הרשאות Green API"""
    try:
        data = request.get_json()
        instance_id = data.get('instance_id', '').strip()
        token = data.get('token', '').strip()
        id_instance = data.get('id_instance', '').strip()
        
        if not instance_id or not token:
            return jsonify({
                'success': False,
                'error': 'Instance ID and Token are required'
            }), 400
        
        # Validate credentials format
        credentials = {
            'instance_id': instance_id,
            'token': token,
            'id_instance': id_instance
        }
        
        is_valid, message = green_api_credentials.credential_manager.validate_credentials(credentials)
        if not is_valid:
            return jsonify({
                'success': False,
                'error': message
            }), 400
        
        # Save credentials
        success = green_api_credentials.save_credentials(instance_id, token, id_instance)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Credentials saved successfully',
                'status': 'saved'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to save credentials'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error saving credentials: {str(e)}'
        }), 500

@app.route('/api/green-api/test', methods=['POST'])
def api_test_green_api():
    """API לבדיקת חיבור Green API"""
    try:
        data = request.get_json()
        instance_id = data.get('instance_id', '').strip()
        token = data.get('token', '').strip()
        id_instance = data.get('id_instance', '').strip()
        
        if not instance_id or not token:
            return jsonify({
                'success': False,
                'error': 'Instance ID and Token are required for testing'
            }), 400
        
        # Test credentials
        result = green_api_tester.test_credentials(instance_id, token, id_instance)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error testing credentials: {str(e)}'
        }), 500

@app.route('/api/green-api/help', methods=['GET'])
def api_get_green_api_help():
    """API לקבלת עזרה למציאת הרשאות Green API"""
    try:
        from green_api_client import GreenAPIClient
        client = GreenAPIClient("dummy", "dummy")  # Dummy client just for help
        help_info = client.get_credential_help()
        return jsonify(help_info)
    except Exception as e:
        return jsonify({
            'error': f'Error getting help information: {str(e)}'
        }), 500

@app.route('/api/green-api/credentials', methods=['DELETE'])
def api_delete_green_api_credentials():
    """API למחיקת הרשאות Green API"""
    try:
        success = green_api_credentials.delete_credentials()
        if success:
            return jsonify({
                'success': True,
                'message': 'Credentials deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to delete credentials'
            }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error deleting credentials: {str(e)}'
        }), 500

# API endpoints לסינכרון
@app.route('/api/sync/contact/<contact_id>', methods=['POST'])
def api_sync_contact(contact_id):
    """API לסינכרון איש קשר ספציפי"""
    sm = get_sync_manager()
    if not sm:
        return jsonify({"error": "מנהל סינכרון לא זמין"}), 500
    
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({"error": "נדרשים תאריכי התחלה וסיום"}), 400
    
    try:
        # התחלת סינכרון אסינכרוני
        sync_id = sm.start_async_sync("contact", contact_id, start_date, end_date)
        return jsonify({
            "success": True,
            "sync_id": sync_id,
            "message": "סינכרון הותחל בהצלחה"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync/group/<group_id>', methods=['POST'])
def api_sync_group(group_id):
    """API לסינכרון קבוצה ספציפית"""
    sm = get_sync_manager()
    if not sm:
        return jsonify({"error": "מנהל סינכרון לא זמין"}), 500
    
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({"error": "נדרשים תאריכי התחלה וסיום"}), 400
    
    try:
        # התחלת סינכרון אסינכרוני
        sync_id = sm.start_async_sync("group", group_id, start_date, end_date)
        return jsonify({
            "success": True,
            "sync_id": sync_id,
            "message": "סינכרון הותחל בהצלחה"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync/all', methods=['POST'])
def api_sync_all():
    """API לסינכרון כל המסומנים"""
    sm = get_sync_manager()
    if not sm:
        return jsonify({"error": "מנהל סינכרון לא זמין"}), 500
    
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    if not start_date or not end_date:
        return jsonify({"error": "נדרשים תאריכי התחלה וסיום"}), 400
    
    try:
        # התחלת סינכרון אסינכרוני
        sync_id = sm.start_async_sync("all", "all", start_date, end_date)
        return jsonify({
            "success": True,
            "sync_id": sync_id,
            "message": "סינכרון כללי הותחל בהצלחה"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync/status/<sync_id>')
def api_sync_status(sync_id):
    """API לקבלת סטטוס סינכרון"""
    sm = get_sync_manager()
    if not sm:
        return jsonify({"error": "מנהל סינכרון לא זמין"}), 500
    
    try:
        status = sm.get_sync_progress(sync_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sync/status/item/<item_id>')
def api_item_sync_status(item_id):
    """API לקבלת סטטוס סינכרון של פריט ספציפי"""
    sm = get_sync_manager()
    if not sm:
        return jsonify({"error": "מנהל סינכרון לא זמין"}), 500
    
    try:
        status = sm.get_sync_status(item_id)
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/delete/group/<group_id>', methods=['DELETE'])
def api_delete_group(group_id):
    """מחיקת קבוצה מהוואטסאפ ומהמסד הנתונים"""
    logger.info(f"🗑️ מתחיל תהליך מחיקת קבוצה: {group_id}")
    
    try:
        # קבלת פרטי הקבוצה מהמסד הנתונים
        logger.info(f"📊 מחפש פרטי קבוצה במסד הנתונים: {group_id}")
        conn = sqlite3.connect(db_manager.groups_db)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM groups WHERE id = ?", (group_id,))
        group_info = cursor.fetchone()
        conn.close()
        
        if not group_info:
            logger.error(f"❌ הקבוצה לא נמצאה במסד הנתונים: {group_id}")
            return jsonify({'success': False, 'error': 'הקבוצה לא נמצאה במסד הנתונים'}), 404
        
        whatsapp_group_id, group_name = group_info
        logger.info(f"✅ נמצאה קבוצה: {group_name} (WhatsApp ID: {whatsapp_group_id})")
        
        # מחיקה מהוואטסאפ באמצעות Green API או Evolution API
        whatsapp_result = None
        api_used = None
        
        # נסה קודם עם Green API
        logger.info(f"🟢 מנסה מחיקה באמצעות Green API עבור קבוצה: {whatsapp_group_id}")
        try:
            from green_api_client import get_green_api_client
            green_api = get_green_api_client()
            logger.info("✅ Green API client נוצר בהצלחה")
            
            # מחיקה מלאה של הקבוצה מהוואטסאפ
            logger.info(f"🚀 מתחיל תהליך מחיקה מלא של הקבוצה: {whatsapp_group_id}")
            whatsapp_result = green_api.delete_group_completely(whatsapp_group_id)
            api_used = "green_api"
            
            logger.info(f"📊 תוצאת Green API: {whatsapp_result}")
            
            if not whatsapp_result.get('success', False):
                raise Exception(f"Green API failed: {whatsapp_result.get('error', 'Unknown error')}")
            
            logger.info("✅ Green API הצליח למחוק את הקבוצה")
            
        except Exception as green_error:
            logger.warning(f"⚠️ Green API נכשל: {green_error}")
            
            # נסה עם Evolution API כחלופה
            logger.info(f"🔵 מנסה מחיקה באמצעות Evolution API עבור קבוצה: {whatsapp_group_id}")
            try:
                from evolution_api_client import get_evolution_api_client
                evolution_api = get_evolution_api_client()
                logger.info("✅ Evolution API client נוצר בהצלחה")
                
                # מחיקה מלאה של הקבוצה מהוואטסאפ
                logger.info(f"🚀 מתחיל תהליך מחיקה מלא של הקבוצה באמצעות Evolution API: {whatsapp_group_id}")
                whatsapp_result = evolution_api.delete_group_completely(whatsapp_group_id)
                api_used = "evolution_api"
                
                logger.info(f"📊 תוצאת Evolution API: {whatsapp_result}")
                
                if not whatsapp_result.get('success', False):
                    raise Exception(f"Evolution API failed: {whatsapp_result.get('error', 'Unknown error')}")
                    
                logger.info("✅ Evolution API הצליח למחוק את הקבוצה")
                    
            except Exception as evolution_error:
                logger.error(f"❌ שני ה-APIs נכשלו. Green API: {green_error}, Evolution API: {evolution_error}")
                return jsonify({
                    'success': False, 
                    'error': f'שגיאה במחיקת הקבוצה מהוואטסאפ. Green API: {str(green_error)}, Evolution API: {str(evolution_error)}'
                }), 500
        
        # מחיקה מהמסד הנתונים המקומי
        logger.info(f"🗄️ מוחק קבוצה ממסד הנתונים המקומי: {group_id}")
        result = db_manager.delete_group(group_id)
        logger.info(f"📊 תוצאת מחיקת מסד נתונים: {result}")
        
        if result['success']:
            logger.info("✅ הקבוצה נמחקה בהצלחה מהמסד הנתונים")
            # הוספת מידע על ה-API שבו השתמשנו
            if whatsapp_result:
                whatsapp_result['api_used'] = api_used
            
            logger.info(f"🎉 תהליך המחיקה הושלם בהצלחה עבור קבוצה: {group_name}")
            return jsonify({
                'success': True, 
                'message': f'הקבוצה "{group_name}" נמחקה בהצלחה מהוואטסאפ ומהמסד הנתונים',
                'whatsapp_deletion': whatsapp_result,
                'api_used': api_used
            })
        else:
            logger.error(f"❌ שגיאה במחיקת הקבוצה ממסד הנתונים: {result['error']}")
            return jsonify({
                'success': False, 
                'error': f'הקבוצה נמחקה מהוואטסאפ אך לא מהמסד הנתונים: {result["error"]}',
                'api_used': api_used
            }), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs')
def api_get_logs():
    """קבלת לוגים של המערכת"""
    try:
        import os
        from datetime import datetime, timedelta
        
        # רשימת קבצי לוג לקריאה
        log_files = [
            'group_deletion.log',
            'arcserver_deletion.log',
            'debug_group_deletion.log',
            'simple_timebro.log',
            'sync_manager.log'
        ]
        
        all_logs = []
        
        for log_file in log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                    # קריאת 100 השורות האחרונות מכל קובץ
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    
                    for line in recent_lines:
                        line = line.strip()
                        if line:
                            # ניסיון לפרסר את הלוג
                            log_entry = parse_log_line(line)
                            if log_entry:
                                all_logs.append(log_entry)
                                
                except Exception as e:
                    logger.warning(f"שגיאה בקריאת קובץ לוג {log_file}: {e}")
                    continue
        
        # מיון לפי תאריך (הכי חדש ראשון)
        all_logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # הגבלה ל-200 לוגים אחרונים
        all_logs = all_logs[:200]
        
        return jsonify({
            'success': True,
            'logs': all_logs,
            'total_count': len(all_logs)
        })
        
    except Exception as e:
        logger.error(f"שגיאה בקבלת לוגים: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def parse_log_line(line):
    """פרסור שורת לוג לפורמט JSON"""
    try:
        # פורמט: 2025-09-29 20:24:23,330 - INFO - 🚀 מתחיל בדיקת מחיקת קבוצת Arcserver
        parts = line.split(' - ', 2)
        if len(parts) >= 3:
            timestamp_str = parts[0]
            level = parts[1]
            message = parts[2]
            
            # המרת תאריך
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
            except:
                try:
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                except:
                    timestamp = datetime.now()
            
            return {
                'timestamp': timestamp.isoformat(),
                'level': level,
                'message': message
            }
    except Exception as e:
        logger.debug(f"שגיאה בפרסור שורת לוג: {e}")
        return None

if __name__ == '__main__':
    # יצירת תיקיית templates אם לא קיימת
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("🌐 מפעיל שרת Web...")
    print("📱 ממשק זמין בכתובת: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)
