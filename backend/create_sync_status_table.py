#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
יצירת טבלת sync_status
"""

import sqlite3
import os

def create_sync_status_table():
    """יצירת טבלת sync_status"""
    try:
        # יצירת טבלת sync_status
        conn = sqlite3.connect("timebro_calendar.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id TEXT NOT NULL,
                item_type TEXT NOT NULL,
                last_sync DATETIME,
                success BOOLEAN,
                messages_count INTEGER,
                events_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ טבלת sync_status נוצרה בהצלחה")
        return True
        
    except Exception as e:
        print(f"❌ שגיאה ביצירת טבלת sync_status: {e}")
        return False

if __name__ == "__main__":
    print("🔧 יוצר טבלת sync_status...")
    if create_sync_status_table():
        print("🎉 הושלם בהצלחה!")
    else:
        print("❌ נכשל!")

