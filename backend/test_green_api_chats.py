#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת getChats method של Green API לקבלת קבוצות
"""

import json
import os
from green_api_client import EnhancedGreenAPIClient

def test_get_chats():
    """בדיקת קבלת chats (כולל קבוצות) מ-Green API"""
    
    try:
        # קריאה ישירה ממשתני סביבה או מקבצי config
        print("📡 מתחבר לGreen API...")
        
        # ניסיון לקרוא מקובץ .env אם קיים
        env_file = ".env"
        id_instance = None
        api_token = None
        
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('GREENAPI_ID_INSTANCE='):
                        id_instance = line.split('=', 1)[1].strip()
                    elif line.startswith('GREENAPI_API_TOKEN='):
                        api_token = line.split('=', 1)[1].strip()
        
        # אם לא נמצא, ננסה משתני סביבה
        if not id_instance:
            id_instance = os.getenv("GREENAPI_ID_INSTANCE")
        if not api_token:
            api_token = os.getenv("GREENAPI_API_TOKEN")
        
        if not id_instance or not api_token:
            print("❌ לא נמצאו credentials.")
            return
        
        print(f"✅ נמצאו credentials: Instance={id_instance[:10]}...")
        
        # יצירת client
        client = EnhancedGreenAPIClient(id_instance, api_token)
        
        print("💬 קורא ל-getChats...")
        
        # קבלת chats
        chats = client.get_chats()
        
        print(f"📊 סוג התגובה: {type(chats)}")
        
        if isinstance(chats, dict) and 'error' in chats:
            print(f"❌ שגיאה: {chats['error']}")
            return
        
        if isinstance(chats, list):
            print(f"✅ התקבלו {len(chats)} chats")
            
            # הפרדה בין private chats וקבוצות
            private_chats = []
            group_chats = []
            
            for chat in chats:
                chat_id = chat.get('id', '')
                if chat_id.endswith('@c.us'):
                    private_chats.append(chat)
                elif chat_id.endswith('@g.us'):
                    group_chats.append(chat)
            
            print(f"📱 Private chats: {len(private_chats)}")
            print(f"👥 Group chats: {len(group_chats)}")
            
            # הצגת דוגמאות לקבוצות
            if group_chats:
                print(f"\n🔍 דוגמאות לקבוצות (5 ראשונות):")
                for i, group in enumerate(group_chats[:5], 1):
                    print(f"\n{i}. {json.dumps(group, indent=2, ensure_ascii=False)}")
                
                if len(group_chats) > 5:
                    print(f"\n... ועוד {len(group_chats) - 5} קבוצות")
                
                # הצגת המפתחות הזמינים בקבוצה
                if group_chats:
                    print(f"\n🔍 מפתחות זמינים בקבוצה:")
                    for key in group_chats[0].keys():
                        print(f"  - {key}")
            
            # השוואה עם מה שיש ב-Evolution API
            print(f"\n📊 השוואה:")
            print(f"  Green API Groups: {len(group_chats)}")
            
            # בדיקה אם יש קובץ Evolution groups
            if os.path.exists('evolution_groups.db'):
                import sqlite3
                conn = sqlite3.connect('evolution_groups.db')
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM groups")
                evolution_count = cursor.fetchone()[0]
                conn.close()
                print(f"  Evolution API Groups: {evolution_count}")
                
                if len(group_chats) != evolution_count:
                    print(f"  ⚠️ יש הבדל של {abs(len(group_chats) - evolution_count)} קבוצות!")
                else:
                    print(f"  ✅ אותה כמות קבוצות")
            
        elif isinstance(chats, dict):
            print("📄 התגובה היא אובייקט:")
            print(json.dumps(chats, indent=2, ensure_ascii=False))
        
        else:
            print(f"❓ פורמט לא צפוי: {chats}")
            
    except Exception as e:
        print(f"❌ שגיאה: {e}")

if __name__ == "__main__":
    test_get_chats()




