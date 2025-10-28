#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
הצלבת אנשי קשר מ-WhatsApp Export עם מסד הנתונים
לקבלת התאמות מדויקות יותר לרשימת timebro
"""

import sqlite3
import csv
import json
import re
from datetime import datetime

class ContactsCrossReference:
    def __init__(self):
        self.db_path = "whatsapp_contacts_groups.db"
        self.csv_file = "WhatsAppContactsExport.csv"
        
        # רשימת אנשי הקשר המבוקשים לtimebro
        self.target_contacts = [
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
        
        self.csv_contacts = {}
        self.load_csv_contacts()

    def log(self, message: str, level: str = "INFO"):
        """רישום לוג עם חותמת זמן"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        emoji = {"SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️", "MATCH": "🎯"}.get(level, "📊")
        print(f"[{timestamp}] {emoji} {message}")

    def load_csv_contacts(self):
        """טעינת אנשי קשר מקובץ CSV"""
        self.log("טוען אנשי קשר מקובץ WhatsApp Export...")
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    mobile = row['Mobile'].strip()
                    name = row['Name'].strip()
                    full_name = row['Full Name'].strip()
                    
                    # יצירת מילון לחיפוש מהיר
                    self.csv_contacts[mobile] = {
                        'name': name,
                        'full_name': full_name,
                        'mobile': mobile
                    }
                    
                    # גם לפי שם לחיפוש
                    if name:
                        self.csv_contacts[name.lower()] = {
                            'name': name,
                            'full_name': full_name,
                            'mobile': mobile
                        }
            
            self.log(f"נטענו {len(self.csv_contacts)//2} אנשי קשר מ-CSV", "SUCCESS")
            
        except Exception as e:
            self.log(f"שגיאה בטעינת קובץ CSV: {e}", "ERROR")

    def normalize_phone(self, phone: str) -> str:
        """נורמליזציה של מספר טלפון"""
        if not phone:
            return ""
        
        # הסרת תווים מיותרים
        clean = re.sub(r'[^\d]', '', phone)
        
        # הוספת קוד מדינה אם חסר
        if clean.startswith('0'):
            clean = '972' + clean[1:]
        elif len(clean) == 9 and not clean.startswith('972'):
            clean = '972' + clean
            
        return clean

    def find_best_match(self, target_name: str) -> dict:
        """חיפוש ההתאמה הטובה ביותר לאיש קשר מבוקש"""
        
        # שלב 1: חיפוש ישיר בשם מקובץ CSV
        target_lower = target_name.lower()
        
        # מילות מפתח לחיפוש
        keywords = []
        if '/' in target_name:
            main_name = target_name.split('/')[0].strip()
            company = target_name.split('/')[1].strip()
            keywords.extend([main_name.lower(), company.lower()])
        else:
            keywords.append(target_lower)
        
        # שלב 2: חיפוש בקובץ CSV
        csv_matches = []
        for contact in self.csv_contacts.values():
            if 'mobile' not in contact:
                continue
                
            name = contact['name'].lower()
            full_name = contact['full_name'].lower()
            
            for keyword in keywords:
                if keyword in name or keyword in full_name:
                    csv_matches.append(contact)
                    break
        
        # שלב 3: חיפוש במסד הנתונים
        db_matches = []
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for keyword in keywords:
            cursor.execute('''
                SELECT name, phone_number, remote_jid, whatsapp_id, timebro_priority
                FROM contacts
                WHERE LOWER(name) LIKE ? OR LOWER(push_name) LIKE ?
                ORDER BY timebro_priority DESC, name
            ''', (f'%{keyword}%', f'%{keyword}%'))
            
            results = cursor.fetchall()
            for result in results:
                db_matches.append({
                    'name': result[0],
                    'phone': result[1],
                    'remote_jid': result[2],
                    'whatsapp_id': result[3],
                    'priority': result[4]
                })
        
        conn.close()
        
        return {
            'target': target_name,
            'csv_matches': csv_matches,
            'db_matches': db_matches
        }

    def find_exact_matches(self):
        """מציאת התאמות מדויקות עם מספרי טלפון"""
        self.log("מחפש התאמות מדויקות עם הצלבת נתונים...")
        
        exact_matches = []
        partial_matches = []
        no_matches = []
        
        for target_name in self.target_contacts:
            match_result = self.find_best_match(target_name)
            
            # בדיקה אם יש התאמה מדויקת עם מספר טלפון
            found_exact = False
            
            for csv_contact in match_result['csv_matches']:
                phone = self.normalize_phone(csv_contact['mobile'])
                
                # חיפוש במסד הנתונים לפי מספר טלפון
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT name, phone_number, remote_jid, timebro_priority
                    FROM contacts
                    WHERE phone_number = ? OR remote_jid LIKE ?
                ''', (phone, f'{phone}%'))
                
                db_result = cursor.fetchone()
                conn.close()
                
                if db_result:
                    exact_match = {
                        'target': target_name,
                        'csv_name': csv_contact['name'],
                        'csv_full_name': csv_contact['full_name'],
                        'phone': phone,
                        'db_name': db_result[0],
                        'db_phone': db_result[1],
                        'remote_jid': db_result[2],
                        'priority': db_result[3],
                        'unique_id': phone
                    }
                    exact_matches.append(exact_match)
                    found_exact = True
                    break
            
            if not found_exact:
                # אם לא נמצאה התאמה מדויקת, נסה חיפוש חלקי
                if match_result['csv_matches'] or match_result['db_matches']:
                    partial_matches.append(match_result)
                else:
                    no_matches.append(target_name)
        
        return exact_matches, partial_matches, no_matches

    def update_timebro_flags_from_csv(self):
        """עדכון דגלי timebro במסד הנתונים על בסיס הצלבת נתונים"""
        self.log("מעדכן דגלי timebro על בסיס הצלבת נתונים...")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updated_count = 0
        
        # עבור כל איש קשר בקובץ CSV
        for contact in self.csv_contacts.values():
            if 'mobile' not in contact:
                continue
                
            phone = self.normalize_phone(contact['mobile'])
            name = contact['name']
            full_name = contact['full_name']
            
            # בדיקה אם זה איש קשר בעדיפות
            is_priority = self.is_target_contact(name, full_name)
            priority_level = self.calculate_priority(name, full_name) if is_priority else 0
            
            if is_priority:
                # עדכון במסד הנתונים
                cursor.execute('''
                    UPDATE contacts 
                    SET include_in_timebro = 1, 
                        timebro_priority = ?,
                        company = ?,
                        updated_at = ?
                    WHERE phone_number = ? OR remote_jid LIKE ?
                ''', (
                    priority_level,
                    self.extract_company(full_name),
                    datetime.now().isoformat(),
                    phone,
                    f'{phone}%'
                ))
                
                if cursor.rowcount > 0:
                    updated_count += 1
                    self.log(f"עודכן: {name} - {phone}", "MATCH")
        
        conn.commit()
        conn.close()
        
        self.log(f"עודכנו {updated_count} אנשי קשר נוספים בדגלי timebro", "SUCCESS")
        return updated_count

    def is_target_contact(self, name: str, full_name: str) -> bool:
        """בדיקה אם איש קשר נמצא ברשימת היעד"""
        search_text = f"{name} {full_name}".lower()
        
        # בדיקה ישירה לפי רשימת היעד
        for target in self.target_contacts:
            target_words = target.lower().split()
            
            # בדיקה אם כל המילים המרכזיות קיימות
            main_words = [word for word in target_words if len(word) > 2 and word not in ['/', 'של', 'בע״מ']]
            
            if len(main_words) > 0:
                matches = sum(1 for word in main_words if word in search_text)
                if matches >= max(1, len(main_words) // 2):  # לפחות מחצית מהמילות
                    return True
        
        # בדיקת מילות מפתח חשובות
        priority_keywords = [
            'מייק', 'mike', 'ביקוב',
            'סשה', 'דיבקה',
            'אלימלך', 'בינשטוק',
            'מוטי', 'בראל', 'כפרי', 'דרייב',
            'עדי', 'גץ', 'פניאל', 'mly',
            'אופיר', 'אריה',
            'salesflow', 'ריקי', 'רוזנברג',
            'שרון', 'רייכטר', 'crm',
            'צליל', 'נויימן',
            'מיכל', 'קולינגר',
            'ישי', 'גביאן', 'גבנאן',
            'סיון', 'דווידוביץ',
            'שחר', 'זכאי', 'fundit',
            'ג׳וליה', 'סקסס',
            'ענת', 'שרייבר', 'כוכבא',
            'איריס', 'מנהלת', 'משרד',
            'עמי', 'ברעם',
            'ערן', 'זלטקין', 'סולומון',
            'ספירת', 'לידים',
            'עדי', 'איילת', 'הירש', 'טודו',
            'fital', 'טל', 'מועלם',
            'גיא', 'נחמני',
            'אביעד',
            'מנדי', 'קמפיינים',
            'עוז', 'סושיאל',
            'דניאל', 'דיקובסקי', 'xwear',
            'רנית', 'גרנות',
            'צחי',
            'מכירות',
            'אושר', 'חיים', 'זדה',
            'קרן', 'בן', 'דוד', 'ברנדס',
            'גיל', 'שרון',
            'אורלי', 'לצאת', 'לאור',
            'איריס', 'יוגב',
            'גלעד', 'אטיאס',
            'mindcrm', 'מעבר', 'חברה',
            'דולב', 'סוכן', 'דרום', 'trichome',
            'נטע', 'שלי', 'שתלתם',
            'דויד', 'פורת',
            'גדעון', 'להב',
            'עומר', 'דהאן',
            'אלעד', 'דניאלי', 'שטורעם',
            'חלי', 'אוטומציות', 'אניגמה',
            'דובי',
            'אלדד', 'טריכום',
            'יהונתן', 'לוי',
            'לי', 'עמר', 'משה',
            'יהודה', 'גולדמן',
            'מעיין', 'פרץ',
            'אבי', 'ואלס',
            'אורי', 'קובץ',
            'איה',
            'אתי', 'כהן',
            'גד', 'טמיר',
            'יאיר', 'אסולין',
            'תומר',
            'מיקה', 'מדיה',
            'רותם',
            'נדיה',
            'עידן',
            'lbs', 'אוטומציות',
            'תמיכה'
        ]
        
        for keyword in priority_keywords:
            if keyword in search_text:
                return True
                
        return False

    def calculate_priority(self, name: str, full_name: str) -> int:
        """חישוב דרגת עדיפות על בסיס השם"""
        search_text = f"{name} {full_name}".lower()
        
        # עדיפות עליונה
        if any(word in search_text for word in ['מייק', 'mike', 'ביקוב']):
            return 10
        elif any(word in search_text for word in ['צחי', 'כפרי']):
            return 9
        elif any(word in search_text for word in ['סשה', 'דיבקה']):
            return 8
        elif any(word in search_text for word in ['עמר', 'משה', 'לי']):
            return 7
        elif any(word in search_text for word in ['שתלתם', 'נטע', 'שלי']):
            return 6
        elif any(word in search_text for word in ['fital', 'טל', 'מועלם']):
            return 5
        
        # עדיפות בינונית
        elif any(word in search_text for word in ['אופיר', 'אריה', 'סולומון', 'mly']):
            return 4
        elif any(word in search_text for word in ['trichome', 'טריכום', 'אניגמה']):
            return 3
        elif any(word in search_text for word in ['lbs', 'אוטומציות', 'crm']):
            return 2
        
        return 1

    def extract_company(self, full_name: str) -> str:
        """חילוץ שם חברה מהשם המלא"""
        if not full_name:
            return ""
        
        # חיפוש דפוסים של חברות
        companies = {
            'כפרי': 'כפרי דרייב',
            'דרייב': 'כפרי דרייב',
            'lbs': 'LBS',
            'mly': 'MLY',
            'סולומון': 'סולומון גרופ',
            'trichome': 'Trichome',
            'טריכום': 'Trichome',
            'fundit': 'Fundit',
            'salesflow': 'Salesflow',
            'crm': 'CRM',
            'mindcrm': 'MindCRM',
            'אניגמה': 'אניגמה',
            'טודו': 'טודו דזיין',
            'אוטומציות': 'אוטומציות',
            'שתלתם': 'שתלתם'
        }
        
        full_lower = full_name.lower()
        for keyword, company in companies.items():
            if keyword in full_lower:
                return company
                
        return ""

    def generate_comprehensive_report(self):
        """יצירת דוח מקיף עם כל ההתאמות"""
        self.log("יוצר דוח מקיף עם הצלבת נתונים...")
        
        # עדכון דגלי timebro
        updated_count = self.update_timebro_flags_from_csv()
        
        # חיפוש התאמות
        exact_matches, partial_matches, no_matches = self.find_exact_matches()
        
        print("\n" + "="*80)
        print("🎯 דוח מקיף - הצלבת אנשי קשר WhatsApp עם רשימת timebro")
        print("="*80)
        print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        print("")
        
        print(f"📊 סיכום:")
        print(f"   • התאמות מדויקות: {len(exact_matches)}")
        print(f"   • התאמות חלקיות: {len(partial_matches)}")  
        print(f"   • לא נמצאו: {len(no_matches)}")
        print(f"   • עודכנו דגלי timebro: {updated_count}")
        print("")
        
        if exact_matches:
            print("✅ התאמות מדויקות:")
            print("-" * 50)
            
            for match in exact_matches:
                print(f"🎯 {match['target']}")
                print(f"   CSV: {match['csv_name']} ({match['csv_full_name']})")
                print(f"   DB:  {match['db_name']}")
                print(f"   📞  {match['phone']}")
                print(f"   🆔  {match['remote_jid']}")
                print(f"   ⭐  עדיפות: {match['priority']}")
                print("")
        
        if partial_matches:
            print("\n🔍 התאמות חלקיות (דורשות בדיקה ידנית):")
            print("-" * 50)
            
            for match in partial_matches[:10]:  # רק 10 הראשונות
                print(f"❓ {match['target']}")
                if match['csv_matches']:
                    print(f"   CSV: {match['csv_matches'][0]['name']} - {match['csv_matches'][0]['mobile']}")
                if match['db_matches']:
                    print(f"   DB:  {match['db_matches'][0]['name']} - עדיפות {match['db_matches'][0]['priority']}")
                print("")
        
        if no_matches:
            print(f"\n❌ לא נמצאו ({len(no_matches)}):")
            print("-" * 30)
            for name in no_matches:
                print(f"   • {name}")
        
        # יצירת רשימה מעודכנת סופית
        priority_list = self.get_final_priority_list()
        
        print(f"\n📋 רשימה סופית מעודכנת לtimebro:")
        print("=" * 50)
        
        for contact in priority_list:
            print(f"• {contact['name']}")
            print(f"  📞 {contact['identifier']}")
            print(f"  🏢 {contact['company']}")
            print(f"  ⭐ עדיפות: {contact['priority']}")
            print("")
        
        # שמירת דוח לקובץ JSON
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'exact_matches': len(exact_matches),
                'partial_matches': len(partial_matches),
                'no_matches': len(no_matches),
                'updated_flags': updated_count
            },
            'exact_matches': exact_matches,
            'partial_matches': partial_matches,
            'no_matches': no_matches,
            'final_priority_list': priority_list
        }
        
        with open('timebro_cross_reference_report.json', 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        self.log("דוח נשמר בקובץ: timebro_cross_reference_report.json", "SUCCESS")
        
        return report_data

    def get_final_priority_list(self):
        """קבלת רשימה סופית מעודכנת לtimebro"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, phone_number, remote_jid, timebro_priority, company
            FROM contacts
            WHERE include_in_timebro = 1 AND timebro_priority >= 5
            ORDER BY timebro_priority DESC, name
        ''')
        
        contacts = cursor.fetchall()
        conn.close()
        
        priority_list = []
        for contact in contacts:
            name, phone, remote_jid, priority, company = contact
            
            # מזהה ייחודי
            identifier = phone if phone else remote_jid
            
            priority_list.append({
                'name': name,
                'identifier': identifier,
                'phone': phone,
                'remote_jid': remote_jid,
                'priority': priority,
                'company': company or self.extract_company(name)
            })
        
        return priority_list

if __name__ == "__main__":
    cross_ref = ContactsCrossReference()
    report = cross_ref.generate_comprehensive_report()
    
    print(f"\n🎉 הצלבת נתונים הושלמה!")
    print(f"📊 סה\"כ: {report['summary']['exact_matches']} התאמות מדויקות")













