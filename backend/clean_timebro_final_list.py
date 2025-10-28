#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
רשימה סופית נקייה ליומן timebro
עם התאמות מדויקות בלבד
"""

import sqlite3
import json
from datetime import datetime

def get_clean_timebro_list():
    """קבלת רשימה נקייה עם ההתאמות המדויקות מהרשימה המקורית"""
    
    # רשימת אנשי הקשר שנמצאו בפועל עם מספרי הטלפון הנכונים
    verified_contacts = [
        # עדיפות עליונה
        {'name': 'מייק ביקוב / LBS', 'phone': '972546687813', 'priority': 10, 'company': 'LBS'},
        {'name': 'סשה דיבקה', 'phone': '972526059554', 'priority': 8, 'company': ''},
        {'name': 'אלימלך בינשטוק / היתקשרות', 'phone': '972542237700', 'priority': 7, 'company': 'היתקשרות'},
        
        # כפרי דרייב
        {'name': 'מוטי בראל (עבודה) / כפרי דרייב', 'phone': '972547999883', 'priority': 9, 'company': 'כפרי דרייב'},
        {'name': 'מוטי בראל / כפרי דרייב', 'phone': '972524643240', 'priority': 9, 'company': 'כפרי דרייב'},
        {'name': 'איריס מנהלת משרד כפרי דרייב', 'phone': '972508882582', 'priority': 9, 'company': 'כפרי דרייב'},
        {'name': 'סיון דווידוביץ׳ כפרי דרייב', 'phone': '972505588956', 'priority': 9, 'company': 'כפרי דרייב'},
        {'name': 'עוז סושיאל כפרי', 'phone': '972542609496', 'priority': 9, 'company': 'כפרי דרייב'},
        {'name': 'אביעד כפרי דרייב', 'phone': '972506551126', 'priority': 9, 'company': 'כפרי דרייב'},
        {'name': 'צחי כפרי / כפרי דרייב', 'phone': '972547999884', 'priority': 9, 'company': 'כפרי דרייב'},
        {'name': 'גלעד אטיאס / כפרי דרייב', 'phone': '972528105754', 'priority': 9, 'company': 'כפרי דרייב'},
        
        # MLY
        {'name': 'עדי גץ פניאל / MLY', 'phone': '972523000348', 'priority': 7, 'company': 'MLY'},
        {'name': 'אושר חיים זדה / MLY', 'phone': '972542550772', 'priority': 7, 'company': 'MLY'},
        {'name': 'קרן בן דוד ברנדס / MLY', 'phone': '972546668744', 'priority': 7, 'company': 'MLY'},
        {'name': 'גיל שרון / MLY', 'phone': '972528113415', 'priority': 7, 'company': 'MLY'},
        
        # חשובים אחרים
        {'name': 'אופיר אריה', 'phone': '972528105362', 'priority': 6, 'company': ''},
        {'name': 'ריקי רוזנברג', 'phone': '972544440651', 'priority': 6, 'company': 'Salesflow'},
        {'name': 'צליל נויימן', 'phone': '972547406064', 'priority': 6, 'company': ''},
        {'name': 'מיכל קולינגר / כפרי דרייב', 'phone': '972543231222', 'priority': 6, 'company': 'כפרי דרייב'},
        {'name': 'ישי גביאן', 'phone': '972549166679', 'priority': 6, 'company': ''},
        {'name': 'שחר זכאי / fundit', 'phone': '972522241682', 'priority': 6, 'company': 'Fundit'},
        {'name': 'ג׳וליה סקסס קולג׳', 'phone': '972542272546', 'priority': 6, 'company': ''},
        {'name': 'ענת שרייבר כוכבא / fundit', 'phone': '972544395050', 'priority': 6, 'company': 'Fundit'},
        {'name': 'עמי ברעם / התרשרות', 'phone': '972535274770', 'priority': 6, 'company': 'התרשרות'},
        {'name': 'ערן זלטקין / סולומון גרופ', 'phone': '972528085971', 'priority': 6, 'company': 'סולומון גרופ'},
        {'name': 'מיקה חברת מדיה סולומון / סולמון גרופ', 'phone': '972778040922', 'priority': 6, 'company': 'סולומון גרופ'},
        {'name': 'עדי הירש / טודו דזיין', 'phone': '972526696302', 'priority': 6, 'company': 'טודו דזיין'},
        {'name': 'איילת הירש / טודו דזיין', 'phone': '972545667717', 'priority': 6, 'company': 'טודו דזיין'},
        {'name': 'fital / טל מועלם', 'phone': '972523616914', 'priority': 5, 'company': ''},
        {'name': 'ד״ר גיא נחמני', 'phone': '972527360422', 'priority': 6, 'company': ''},
        {'name': 'דניאל דיקובסקי / xwear', 'phone': '972545243725', 'priority': 6, 'company': 'XWear'},
        {'name': 'רנית גרנות / ד״ר גיא נחמני', 'phone': '972526820421', 'priority': 6, 'company': ''},
        {'name': 'חלי אוטומציות / אניגמה', 'phone': '972503070829', 'priority': 6, 'company': 'אניגמה'},
        {'name': 'דובי פורת', 'phone': '972502688222', 'priority': 6, 'company': ''},
        {'name': 'דויד פורת / ריקי רוזנברג', 'phone': '972539823922', 'priority': 6, 'company': 'Salesflow'},
        {'name': 'גדעון להב / אופיר אריה', 'phone': '972549905992', 'priority': 6, 'company': ''},
        {'name': 'עומר דהאן / סשה דידקה', 'phone': '972545661640', 'priority': 6, 'company': ''},
        {'name': 'אלעד דניאלי / שטורעם', 'phone': '972545755862', 'priority': 6, 'company': 'שטורעם'},
        {'name': 'יהונתן לוי / אניגמה', 'phone': '972523136454', 'priority': 6, 'company': 'אניגמה'},
        {'name': 'לי עמר / משה עמר', 'phone': '972525080115', 'priority': 7, 'company': ''},
        {'name': 'משה עמר', 'phone': '972509913244', 'priority': 7, 'company': ''},
        {'name': 'יהודה גולדמן', 'phone': '972544704448', 'priority': 6, 'company': ''},
        {'name': 'מעיין פרץ / סולומון גרופ', 'phone': '972535764531', 'priority': 6, 'company': 'סולומון גרופ'},
        {'name': 'אבי ואלס / שרון רייכטר', 'phone': '972509289281', 'priority': 5, 'company': ''},
        {'name': 'אורי קובץ / ישי גביאן', 'phone': '972546321606', 'priority': 5, 'company': ''},
        {'name': 'איה סושיאל / ד״ר גיא נחמני', 'phone': '972526820422', 'priority': 5, 'company': ''},
        {'name': 'אתי כהן / trichome', 'phone': '972544969704', 'priority': 5, 'company': 'Trichome'},
        {'name': 'גד טמיר', 'phone': '972548088154', 'priority': 5, 'company': ''},
        {'name': 'יאיר אסולין / סולומון גרופ', 'phone': '972527722504', 'priority': 6, 'company': 'סולומון גרופ'},
        {'name': 'תומר טרייכום / trichome', 'phone': '972526911118', 'priority': 5, 'company': 'Trichome'},
        {'name': 'רותם סקסס קולג׳', 'phone': '972524169739', 'priority': 5, 'company': ''},
        {'name': 'עידן טרייכום / trichome', 'phone': '972543012075', 'priority': 5, 'company': 'Trichome'},
        {'name': 'נטע שלי / שתלתם', 'phone': '972546734324', 'priority': 6, 'company': 'שתלתם'},
        {'name': 'תמיכה טרייכום / trichome', 'phone': '972546263032', 'priority': 5, 'company': 'Trichome'},
        {'name': 'אורלי / לצאת לאור', 'phone': '972525288085', 'priority': 6, 'company': 'לצאת לאור'},
        {'name': 'איריס יוגב / לצאת לאור', 'phone': '972523883600', 'priority': 6, 'company': 'לצאת לאור'},
        {'name': 'אוטומציות LBS+אייל', 'phone': '120363041310911227@g.us', 'priority': 7, 'company': 'LBS'}
    ]
    
    print("🎯 רשימה סופית נקייה ומעודכנת ליומן timebro")
    print("="*70)
    print(f"⏰ {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📊 {len(verified_contacts)} אנשי קשר מאומתים")
    print("")
    
    # קיבוץ לפי עדיפות
    by_priority = {}
    for contact in verified_contacts:
        priority = contact['priority']
        if priority not in by_priority:
            by_priority[priority] = []
        by_priority[priority].append(contact)
    
    # הצגה לפי עדיפות
    for priority in sorted(by_priority.keys(), reverse=True):
        contacts = by_priority[priority]
        
        print(f"⭐ עדיפות {priority} ({len(contacts)} אנשי קשר):")
        print("-" * 50)
        
        for contact in sorted(contacts, key=lambda x: x['name']):
            print(f"• {contact['name']}")
            print(f"  📞 {contact['phone']}")
            if contact['company']:
                print(f"  🏢 {contact['company']}")
            print("")
    
    # שמירת רשימה סופית
    final_data = {
        'timestamp': datetime.now().isoformat(),
        'total_contacts': len(verified_contacts),
        'contacts_by_priority': by_priority,
        'contacts': verified_contacts
    }
    
    with open('timebro_verified_final_list.json', 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    # רשימה פשוטה לטקסט
    with open('timebro_verified_contacts.txt', 'w', encoding='utf-8') as f:
        f.write("רשימה סופית מאומתת ליומן timebro\n")
        f.write("="*50 + "\n")
        f.write(f"עודכן: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        f.write(f"סה\"כ: {len(verified_contacts)} אנשי קשר\n\n")
        
        for priority in sorted(by_priority.keys(), reverse=True):
            contacts = by_priority[priority]
            f.write(f"עדיפות {priority}:\n")
            
            for contact in sorted(contacts, key=lambda x: x['name']):
                f.write(f"  • {contact['name']}\n")
                f.write(f"    📞 {contact['phone']}\n")
                if contact['company']:
                    f.write(f"    🏢 {contact['company']}\n")
                f.write("\n")
    
    print(f"💾 רשימה נשמרה בקבצים:")
    print(f"   • timebro_verified_final_list.json")
    print(f"   • timebro_verified_contacts.txt")
    
    return final_data

if __name__ == "__main__":
    final_data = get_clean_timebro_list()













