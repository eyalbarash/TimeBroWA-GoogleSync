#!/usr/bin/env python3
"""
שחזור 57 אנשי הקשר המסומנים ליומן
"""

import json
import sqlite3
from datetime import datetime

def restore_contacts():
    # קריאת הקובץ
    with open('timebro_verified_final_list.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    contacts = data['contacts']
    print(f"מצאתי {len(contacts)} אנשי קשר לשחזור")
    
    # חיבור למסד הנתונים
    conn = sqlite3.connect('whatsapp_contacts_groups.db')
    cursor = conn.cursor()
    
    restored_count = 0
    
    for contact in contacts:
        name = contact['name']
        phone = contact.get('phone', '')
        
        # חיפוש איש הקשר במסד
        cursor.execute('''
            SELECT contact_id, whatsapp_id FROM contacts 
            WHERE (name = ? OR push_name = ? OR phone_number = ?) 
            AND phone_number = ?
        ''', (name, name, phone, phone))
        
        result = cursor.fetchone()
        
        if result:
            contact_id, whatsapp_id = result
            # עדכון לסימון ליומן
            cursor.execute('''
                UPDATE contacts 
                SET include_in_timebro = 1, 
                    timebro_priority = 6,
                    updated_at = ?
                WHERE contact_id = ?
            ''', (datetime.now().isoformat(), contact_id))
            
            restored_count += 1
            print(f"✅ שוחזר: {name} - {phone}")
        else:
            print(f"❌ לא נמצא: {name} - {phone}")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 שוחזרו {restored_count} אנשי קשר!")
    return restored_count

if __name__ == "__main__":
    restore_contacts()










