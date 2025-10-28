#!/usr/bin/env python3
"""
גיבוי אנשי קשר וקבוצות מסומנים ליומן
"""

import sqlite3
import json
from datetime import datetime

def backup_contacts_and_groups():
    """גיבוי כל אנשי הקשר והקבוצות המסומנים ליומן"""
    
    conn = sqlite3.connect('whatsapp_contacts_groups.db')
    cursor = conn.cursor()
    
    # גיבוי אנשי קשר
    cursor.execute('''
        SELECT contact_id, whatsapp_id, name, push_name, phone_number, 
               include_in_timebro, timebro_priority, company_name, created_at, updated_at
        FROM contacts 
        WHERE include_in_timebro = 1
    ''')
    
    contacts = []
    for row in cursor.fetchall():
        contacts.append({
            'contact_id': row[0],
            'whatsapp_id': row[1],
            'name': row[2],
            'push_name': row[3],
            'phone_number': row[4],
            'include_in_timebro': row[5],
            'timebro_priority': row[6],
            'company_name': row[7],
            'created_at': row[8],
            'updated_at': row[9]
        })
    
    # גיבוי קבוצות
    cursor.execute('''
        SELECT group_id, whatsapp_group_id, subject, description, 
               include_in_timebro, timebro_priority, company_name, created_at, updated_at
        FROM groups 
        WHERE include_in_timebro = 1
    ''')
    
    groups = []
    for row in cursor.fetchall():
        groups.append({
            'group_id': row[0],
            'whatsapp_group_id': row[1],
            'subject': row[2],
            'description': row[3],
            'include_in_timebro': row[4],
            'timebro_priority': row[5],
            'company_name': row[6],
            'created_at': row[7],
            'updated_at': row[8]
        })
    
    conn.close()
    
    # שמירת הגיבוי
    backup_data = {
        'timestamp': datetime.now().isoformat(),
        'total_contacts': len(contacts),
        'total_groups': len(groups),
        'contacts': contacts,
        'groups': groups
    }
    
    backup_filename = f"backup_contacts_groups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(backup_filename, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ גיבוי נוצר: {backup_filename}")
    print(f"📊 {len(contacts)} אנשי קשר, {len(groups)} קבוצות")
    
    return backup_filename

if __name__ == "__main__":
    backup_contacts_and_groups()
