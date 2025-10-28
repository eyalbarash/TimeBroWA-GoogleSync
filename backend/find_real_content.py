#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
חיפוש הודעות עם תוכן אמיתי בכל מסדי הנתונים
"""

import sqlite3
import os
from datetime import datetime

def check_database_for_content(db_path):
    """בדיקת תוכן הודעות במסד נתונים"""
    if not os.path.exists(db_path):
        print(f"❌ {db_path} לא קיים")
        return
    
    print(f"\n🔍 בודק תוכן הודעות ב-{db_path}")
    print("="*50)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # רשימת טבלאות
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        for table in tables:
            if 'message' in table.lower():
                print(f"\n📋 טבלה: {table}")
                
                # מבנה הטבלה
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # חיפוש עמודות תוכן
                content_columns = [col for col in columns if any(keyword in col.lower() 
                                                               for keyword in ['content', 'body', 'text', 'message'])]
                
                if content_columns:
                    print(f"   עמודות תוכן: {content_columns}")
                    
                    for col in content_columns:
                        try:
                            # ספירת הודעות עם תוכן
                            cursor.execute(f"""
                                SELECT COUNT(*) 
                                FROM {table} 
                                WHERE {col} IS NOT NULL 
                                AND LENGTH(TRIM({col})) > 0
                            """)
                            count_with_content = cursor.fetchone()[0]
                            
                            # ספירת כל ההודעות
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            total_count = cursor.fetchone()[0]
                            
                            print(f"   📊 {col}: {count_with_content:,} עם תוכן מתוך {total_count:,}")
                            
                            # דוגמאות תוכן
                            if count_with_content > 0:
                                cursor.execute(f"""
                                    SELECT {col}, rowid 
                                    FROM {table} 
                                    WHERE {col} IS NOT NULL 
                                    AND LENGTH(TRIM({col})) > 0
                                    LIMIT 5
                                """)
                                samples = cursor.fetchall()
                                
                                print(f"   🔍 דוגמאות:")
                                for i, (content, rowid) in enumerate(samples, 1):
                                    preview = content[:80] + "..." if len(content) > 80 else content
                                    print(f"      {i}. (ID:{rowid}) {preview}")
                        
                        except Exception as e:
                            print(f"   ❌ שגיאה בעמודה {col}: {e}")
                else:
                    print("   ❌ לא נמצאו עמודות תוכן")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ שגיאה ב-{db_path}: {e}")

def search_mike_with_content():
    """חיפוש הודעות של מייק עם תוכן בכל מקום"""
    databases = [
        'whatsapp_messages.db',
        'whatsapp_messages_webjs.db', 
        'whatsapp_selenium_extraction.db',
        'whatsapp_chats.db',
        'whatsapp_current_structure.db'
    ]
    
    print("🔍 חיפוש הודעות עם תוכן אמיתי")
    print("="*60)
    
    for db in databases:
        check_database_for_content(db)
    
    # בדיקה ספציפית לקבצי August שמצאנו קודם
    print(f"\n🗓️ בדיקת קבצי אוגוסט...")
    if os.path.exists('whatsapp_messages.db'):
        try:
            conn = sqlite3.connect('whatsapp_messages.db')
            cursor = conn.cursor()
            
            # בדיקת טבלת august_messages
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='august_messages'")
            if cursor.fetchone():
                print("✅ נמצאה טבלת august_messages")
                
                cursor.execute("PRAGMA table_info(august_messages)")
                columns = [col[1] for col in cursor.fetchall()]
                print(f"   עמודות: {columns}")
                
                cursor.execute("SELECT COUNT(*) FROM august_messages")
                count = cursor.fetchone()[0]
                print(f"   📊 {count:,} רשומות")
                
                # חיפוש תוכן
                content_cols = [col for col in columns if 'content' in col.lower() or 'message' in col.lower()]
                for col in content_cols:
                    try:
                        cursor.execute(f"""
                            SELECT COUNT(*) 
                            FROM august_messages 
                            WHERE {col} IS NOT NULL 
                            AND LENGTH(TRIM({col})) > 0
                        """)
                        content_count = cursor.fetchone()[0]
                        print(f"   📝 {col}: {content_count:,} עם תוכן")
                        
                        if content_count > 0:
                            cursor.execute(f"SELECT {col} FROM august_messages WHERE LENGTH(TRIM({col})) > 0 LIMIT 3")
                            samples = cursor.fetchall()
                            for i, (content,) in enumerate(samples, 1):
                                preview = content[:60] + "..." if len(content) > 60 else content
                                print(f"      {i}. {preview}")
                    except Exception as e:
                        print(f"   ❌ שגיאה ב-{col}: {e}")
            
            conn.close()
            
        except Exception as e:
            print(f"❌ שגיאה: {e}")

def create_demo_data():
    """יצירת נתוני דמו למייק לדוגמה"""
    print(f"\n💡 יצירת נתוני דמו של מייק לדוגמה...")
    
    demo_conversations = [
        {
            "date": "2025-09-24",
            "conversation_id": 1,
            "messages": [
                {"sender": "מייק", "content": "שלום אייל, איך אתה?", "time": "09:00"},
                {"sender": "אני", "content": "שלום מייק! הכל בסדר, תודה. מה שלומך?", "time": "09:02"},
                {"sender": "מייק", "content": "אני רוצה לדבר איתך על הפרויקט החדש שאנחנו עובדים עליו", "time": "09:05"},
                {"sender": "אני", "content": "בטח, מה יש? יש לך עדכונים?", "time": "09:07"},
                {"sender": "מייק", "content": "כן, יש לי כמה רעיונות איך לשפר את הביצועים", "time": "09:10"},
            ]
        },
        {
            "date": "2025-09-24",
            "conversation_id": 2,
            "messages": [
                {"sender": "אני", "content": "מייק, ראיתי את הדוח ששלחת. מעניין מאוד!", "time": "14:30"},
                {"sender": "מייק", "content": "תודה! עבדתי על זה השבוע. מה אתה חושב על ההמלצות?", "time": "14:35"},
                {"sender": "אני", "content": "אני חושב שזה כיוון נכון. בואו נקבע פגישה לדון בפרטים", "time": "14:40"},
                {"sender": "מייק", "content": "מצוין, אני פנוי מחר בבוקר", "time": "14:45"},
            ]
        }
    ]
    
    # שמירת נתוני הדמו בקובץ JSON
    demo_filename = f"mike_demo_conversations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    demo_data = {
        "metadata": {
            "contact": "מייק ביקוב (דמו)",
            "period": "דמו - ספטמבר 2025",
            "extracted_at": datetime.now().isoformat(),
            "total_messages": sum(len(conv["messages"]) for conv in demo_conversations),
            "total_conversations": len(demo_conversations),
            "note": "זהו קובץ דמו שנוצר להדגמת הפורמט המבוקש לניתוח עם Claude"
        },
        "conversations": demo_conversations,
        "analysis_prompt": "נתח את השיחות הבאות עם מייק ביקוב. זהה את הנושאים העיקריים, סגנון התקשורת של כל צד, ותן המלצות לשיפור היעילות של השיחות העתידיות."
    }
    
    import json
    with open(demo_filename, 'w', encoding='utf-8') as f:
        json.dump(demo_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ נוצר קובץ דמו: {demo_filename}")
    print(f"📄 קובץ זה מכיל דוגמה של הפורמט שאתה מחפש לניתוח עם Claude")
    
    return demo_filename

def main():
    search_mike_with_content()
    demo_file = create_demo_data()
    
    print(f"\n" + "="*70)
    print("📋 סיכום:")
    print(f"• נראה שההודעות האמיתיות במסדי הנתונים הקיימים ריקות מתוכן")
    print(f"• יתכן שהתוכן נמצא במקום אחר או שהוא לא נשמר כמו שצריך")
    print(f"• יצרתי קובץ דמו: {demo_file}")
    print(f"• קובץ הדמו מדגים את הפורמט המבוקש לניתוח עם Claude")
    print("="*70)

if __name__ == "__main__":
    main()













