#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
חיפוש הודעות מייק ביקוב בכל מסדי הנתונים
לראות מה יש ומתי
"""

import sqlite3
import os
from datetime import datetime

def check_database_structure(db_path):
    """בדיקת מבנה מסד הנתונים"""
    if not os.path.exists(db_path):
        print(f"❌ {db_path} לא קיים")
        return
    
    print(f"\n🔍 בודק מסד נתונים: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # רשימת טבלאות
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 טבלאות: {', '.join(tables)}")
        
        if 'messages' in tables:
            # מבנה הטבלה
            cursor.execute("PRAGMA table_info(messages)")
            columns = [f"{row[1]} ({row[2]})" for row in cursor.fetchall()]
            print(f"📊 עמודות: {', '.join(columns)}")
            
            # ספירת הודעות כללית
            cursor.execute("SELECT COUNT(*) FROM messages")
            total = cursor.fetchone()[0]
            print(f"💬 סה\"כ הודעות: {total:,}")
            
            # חיפוש הודעות של מייק
            mike_queries = [
                "SELECT COUNT(*) FROM messages WHERE contact_name LIKE '%מייק%'",
                "SELECT COUNT(*) FROM messages WHERE contact_name LIKE '%Mike%'", 
                "SELECT COUNT(*) FROM messages WHERE sender_name LIKE '%מייק%'",
                "SELECT COUNT(*) FROM messages WHERE sender_name LIKE '%Mike%'"
            ]
            
            mike_count = 0
            for query in mike_queries:
                try:
                    cursor.execute(query)
                    count = cursor.fetchone()[0]
                    if count > 0:
                        mike_count = max(mike_count, count)
                        print(f"✅ נמצאו {count} הודעות של מייק")
                except:
                    continue
            
            if mike_count == 0:
                # חיפוש כללי באנשי קשר
                try:
                    cursor.execute("SELECT DISTINCT contact_name FROM messages WHERE contact_name IS NOT NULL LIMIT 10")
                    contacts = [row[0] for row in cursor.fetchall()]
                    print(f"👥 דוגמאות אנשי קשר: {contacts}")
                except:
                    try:
                        cursor.execute("SELECT DISTINCT sender_name FROM messages WHERE sender_name IS NOT NULL LIMIT 10")
                        contacts = [row[0] for row in cursor.fetchall()]
                        print(f"👥 דוגמאות שולחים: {contacts}")
                    except:
                        pass
            
            # טווח תאריכים
            try:
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM messages WHERE timestamp > 0")
                min_ts, max_ts = cursor.fetchone()
                if min_ts and max_ts:
                    min_date = datetime.fromtimestamp(min_ts).strftime('%Y-%m-%d %H:%M')
                    max_date = datetime.fromtimestamp(max_ts).strftime('%Y-%m-%d %H:%M')
                    print(f"📅 טווח תאריכים: {min_date} עד {max_date}")
            except Exception as e:
                print(f"❌ שגיאה בטווח תאריכים: {e}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ שגיאה: {e}")

def search_mike_everywhere():
    """חיפוש מייק בכל מקום אפשרי"""
    databases = [
        'whatsapp_messages.db',
        'whatsapp_messages_webjs.db', 
        'whatsapp_selenium_extraction.db',
        'whatsapp_chats.db',
        'whatsapp_current_structure.db',
        'whatsapp_contacts.db'
    ]
    
    print("🔍 מחפש הודעות של מייק ביקוב בכל מסדי הנתונים")
    print("="*60)
    
    for db in databases:
        check_database_structure(db)
    
    # בדיקה נוספת במסד אנשי הקשר
    print(f"\n📱 בודק באנשי קשר...")
    if os.path.exists('whatsapp_contacts.db'):
        try:
            conn = sqlite3.connect('whatsapp_contacts.db')
            cursor = conn.cursor()
            
            cursor.execute("SELECT name, phone_number, full_name FROM contacts WHERE name LIKE '%מייק%' OR full_name LIKE '%Mike%'")
            mike_contacts = cursor.fetchall()
            
            if mike_contacts:
                print("✅ נמצא מייק באנשי קשר:")
                for contact in mike_contacts:
                    print(f"   📞 {contact[0]} - {contact[1]} ({contact[2]})")
            else:
                print("❌ מייק לא נמצא באנשי קשר")
            
            conn.close()
        except Exception as e:
            print(f"❌ שגיאה בבדיקת אנשי קשר: {e}")

if __name__ == "__main__":
    search_mike_everywhere()













