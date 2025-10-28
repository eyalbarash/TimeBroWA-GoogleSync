#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
רשימה סופית מעודכנת לאנשי קשר בעדיפות timebro
על בסיס הצלבת נתונים מ-WhatsApp Export ומסד הנתונים
"""

import json
from datetime import datetime

def show_final_timebro_list():
    """הצגת הרשימה הסופית המעודכנת"""
    
    # קריאת הדוח המלא
    with open('timebro_cross_reference_report.json', 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    print("🎯 רשימה סופית מעודכנת ליומן timebro")
    print("=" * 80)
    print(f"⏰ עודכן: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"📊 בהתבסס על הצלבת {report['summary']['updated_flags']:,} אנשי קשר")
    print("")
    
    # התאמות מדויקות שנמצאו
    exact_matches = report['exact_matches']
    
    print(f"✅ נמצאו {len(exact_matches)} התאמות מדויקות:")
    print("="*60)
    
    # קיבוץ לפי דרגת עדיפות
    by_priority = {}
    for match in exact_matches:
        priority = match['priority']
        if priority not in by_priority:
            by_priority[priority] = []
        by_priority[priority].append(match)
    
    # הצגה לפי עדיפות
    for priority in sorted(by_priority.keys(), reverse=True):
        matches = by_priority[priority]
        
        print(f"\n⭐ עדיפות {priority} ({len(matches)} אנשי קשר):")
        print("-" * 40)
        
        for match in sorted(matches, key=lambda x: x['csv_name']):
            print(f"• {match['csv_full_name']}")
            print(f"  📞 {match['phone']}")
            print(f"  🆔 {match['remote_jid']}")
            if match.get('company'):
                print(f"  🏢 {match['company']}")
            print("")
    
    # רשימה מסוכמת לקובץ טקסט
    with open('timebro_final_contacts_list.txt', 'w', encoding='utf-8') as f:
        f.write("רשימה סופית מעודכנת ליומן timebro\n")
        f.write("="*50 + "\n")
        f.write(f"עודכן: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n")
        
        for priority in sorted(by_priority.keys(), reverse=True):
            matches = by_priority[priority]
            f.write(f"עדיפות {priority}:\n")
            
            for match in sorted(matches, key=lambda x: x['csv_name']):
                f.write(f"  • {match['csv_full_name']} - {match['phone']}\n")
            f.write("\n")
    
    print(f"\n💾 רשימה נשמרה גם בקובץ: timebro_final_contacts_list.txt")
    
    # החסרים
    if report['no_matches']:
        print(f"\n❌ לא נמצאו ({len(report['no_matches'])}):")
        print("-" * 30)
        for name in report['no_matches']:
            print(f"   • {name}")
    
    print(f"\n📈 סיכום ביצועים:")
    print(f"   ✅ התאמות מדויקות: {len(exact_matches)}")
    print(f"   ❓ התאמות חלקיות: {len(report['partial_matches'])}")
    print(f"   ❌ לא נמצאו: {len(report['no_matches'])}")
    print(f"   📊 אחוז הצלחה: {len(exact_matches)/(len(exact_matches)+len(report['no_matches']))*100:.1f}%")

def show_top_priority_only():
    """הצגת רק אנשי הקשר בעדיפות הגבוהה ביותר"""
    
    with open('timebro_cross_reference_report.json', 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    print("\n🌟 אנשי קשר בעדיפות עליונה בלבד (8-10):")
    print("="*60)
    
    top_contacts = []
    for match in report['exact_matches']:
        if match['priority'] >= 8:
            top_contacts.append(match)
    
    for match in sorted(top_contacts, key=lambda x: (-x['priority'], x['csv_name'])):
        print(f"⭐ {match['priority']} | {match['csv_full_name']}")
        print(f"    📞 {match['phone']}")
        print(f"    🆔 {match['remote_jid']}")
        print("")
    
    print(f"📊 סה\"כ: {len(top_contacts)} אנשי קשר בעדיפות עליונה")

if __name__ == "__main__":
    show_final_timebro_list()
    show_top_priority_only()













