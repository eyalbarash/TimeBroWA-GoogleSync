#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
יצירת רשימה מעודכנת לאנשי קשר בעדיפות timebro
עם מספרי טלפון ומזהים ייחודיים
"""

import sqlite3
import json
from datetime import datetime

def get_timebro_priority_contacts():
    """קבלת רשימת אנשי קשר בעדיפות עם פרטים מלאים"""
    
    db_path = "whatsapp_contacts_groups.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # שאילתה לאנשי קשר בעדיפות גבוהה בלבד
    cursor.execute('''
        SELECT name, phone_number, remote_jid, whatsapp_id, timebro_priority
        FROM contacts 
        WHERE include_in_timebro = 1 AND timebro_priority >= 5
        ORDER BY timebro_priority DESC, name
    ''')
    
    high_priority_contacts = cursor.fetchall()
    
    # שאילתה לקבוצות בעדיפות
    cursor.execute('''
        SELECT subject, whatsapp_group_id, timebro_priority
        FROM groups 
        WHERE include_in_timebro = 1
        ORDER BY timebro_priority DESC, subject
    ''')
    
    priority_groups = cursor.fetchall()
    
    conn.close()
    
    print("🎯 רשימה מעודכנת ליומן timebro")
    print("=" * 60)
    print(f"⏰ עודכן: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("")
    
    print("👥 אנשי קשר בעדיפות גבוהה (5-10):")
    print("-" * 40)
    
    for contact in high_priority_contacts:
        name, phone, remote_jid, whatsapp_id, priority = contact
        
        # איתור מזהה ייחודי עיקרי
        unique_id = phone if phone else (remote_jid if remote_jid else whatsapp_id)
        
        print(f"• {name}")
        if phone:
            print(f"  📞 {phone}")
        if remote_jid and remote_jid != phone:
            print(f"  🆔 {remote_jid}")
        print(f"  ⭐ עדיפות: {priority}")
        print("")
    
    print(f"📊 סה\"כ: {len(high_priority_contacts)} אנשי קשר בעדיפות גבוהה")
    print("")
    
    if priority_groups:
        print("🏠 קבוצות בעדיפות:")
        print("-" * 40)
        
        for group in priority_groups:
            subject, group_id, priority = group
            print(f"• {subject}")
            print(f"  🆔 {group_id}")
            print(f"  ⭐ עדיפות: {priority}")
            print("")
        
        print(f"📊 סה\"כ: {len(priority_groups)} קבוצות בעדיפות")
    
    # יצירת רשימה לייצוא JSON
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'high_priority_contacts': [
            {
                'name': contact[0],
                'phone': contact[1],
                'remote_jid': contact[2],
                'whatsapp_id': contact[3],
                'priority': contact[4],
                'unique_identifier': contact[1] if contact[1] else (contact[2] if contact[2] else contact[3])
            }
            for contact in high_priority_contacts
        ],
        'priority_groups': [
            {
                'name': group[0],
                'group_id': group[1],
                'priority': group[2]
            }
            for group in priority_groups
        ]
    }
    
    # שמירת קובץ JSON
    with open('timebro_priority_list.json', 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 רשימה נשמרה בקובץ: timebro_priority_list.json")
    
    return export_data

def show_exact_matches():
    """הצגת התאמות מדויקות לרשימה המקורית"""
    
    original_list = [
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
    
    db_path = "whatsapp_contacts_groups.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n🔍 התאמות מדויקות לרשימה המקורית:")
    print("=" * 60)
    
    found_matches = []
    not_found = []
    
    for target_name in original_list:
        # חיפוש בכמה דרכים
        variations = [
            target_name,
            target_name.split('/')[0].strip(),
            target_name.split('|')[0].strip()
        ]
        
        found = False
        for variation in variations:
            cursor.execute('''
                SELECT name, phone_number, remote_jid, timebro_priority
                FROM contacts
                WHERE name LIKE ? OR name LIKE ?
                ORDER BY timebro_priority DESC
                LIMIT 1
            ''', (f'%{variation}%', f'{variation}%'))
            
            result = cursor.fetchone()
            if result:
                name, phone, remote_jid, priority = result
                unique_id = phone if phone else remote_jid
                
                print(f"✅ {target_name}")
                print(f"   → נמצא: {name}")
                print(f"   📞 {unique_id}")
                print(f"   ⭐ עדיפות: {priority}")
                print("")
                
                found_matches.append({
                    'original': target_name,
                    'found': name,
                    'identifier': unique_id,
                    'priority': priority
                })
                found = True
                break
        
        if not found:
            not_found.append(target_name)
    
    if not_found:
        print("\n❌ לא נמצאו:")
        print("-" * 20)
        for name in not_found:
            print(f"   • {name}")
    
    print(f"\n📊 סיכום התאמות:")
    print(f"   ✅ נמצאו: {len(found_matches)}")
    print(f"   ❌ לא נמצאו: {len(not_found)}")
    print(f"   📈 אחוז הצלחה: {len(found_matches)/len(original_list)*100:.1f}%")
    
    conn.close()
    
    return found_matches, not_found

if __name__ == "__main__":
    # קבלת רשימה מלאה
    data = get_timebro_priority_contacts()
    
    # הצגת התאמות מדויקות
    matches, not_found = show_exact_matches()













