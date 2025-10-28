#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת מחיקת קבוצה - דיבוג מפורט
"""

import os
import sys
import sqlite3
import json
import logging
from datetime import datetime

# Load environment variables from .env file
def load_env_file():
    """Load environment variables from .env file"""
    env_file = ".env"
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load environment variables
load_env_file()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_group_deletion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def check_group_in_database():
    """בדיקת קבוצה במסד הנתונים"""
    logger.info("🔍 בודק קבוצות במסד הנתונים...")
    
    try:
        conn = sqlite3.connect("evolution_groups.db")
        cursor = conn.cursor()
        
        # חיפוש קבוצות עם "arc" או "server"
        cursor.execute("""
            SELECT id, name FROM groups 
            WHERE name LIKE '%arc%' OR name LIKE '%server%' OR name LIKE '%ARC%' OR name LIKE '%SERVER%'
            OR name LIKE '%Arc%' OR name LIKE '%Server%'
        """)
        groups = cursor.fetchall()
        
        logger.info(f"📊 נמצאו {len(groups)} קבוצות רלוונטיות:")
        for group_id, name in groups:
            logger.info(f"  - {group_id}: {name}")
        
        conn.close()
        return groups
        
    except Exception as e:
        logger.error(f"❌ שגיאה בבדיקת מסד הנתונים: {e}")
        return []

def check_group_in_whatsapp(group_id):
    """בדיקת קבוצה בוואטסאפ"""
    logger.info(f"📱 בודק קבוצה בוואטסאפ: {group_id}")
    
    try:
        from green_api_client import get_green_api_client
        
        client = get_green_api_client()
        
        # בדיקת מצב ה-instance
        state = client.get_state_instance()
        logger.info(f"📡 מצב ה-instance: {state}")
        
        if state.get('stateInstance') != 'authorized':
            logger.error("❌ ה-instance לא מורשה")
            return False
        
        # בדיקת פרטי הקבוצה
        group_data = client.get_group_data(group_id)
        logger.info(f"📋 פרטי הקבוצה: {json.dumps(group_data, indent=2, ensure_ascii=False)}")
        
        if "error" in group_data:
            logger.error(f"❌ שגיאה בקבלת פרטי קבוצה: {group_data['error']}")
            return False
        
        # בדיקת משתתפים
        participants = group_data.get("participants", [])
        logger.info(f"👥 נמצאו {len(participants)} משתתפים בקבוצה")
        
        # בדיקת אם אני בקבוצה
        my_participant = None
        my_phone = "972549990001@c.us"  # המספר שלך
        
        for participant in participants:
            participant_id = participant.get("id", "")
            if participant_id == my_phone or participant.get("isMe", False):
                my_participant = participant
                break
        
        if my_participant:
            logger.info(f"✅ אני נמצא בקבוצה: {my_participant}")
        else:
            logger.warning("⚠️ אני לא נמצא בקבוצה")
            logger.info(f"🔍 מחפש את המספר שלי: {my_phone}")
            for participant in participants:
                logger.info(f"  - משתתף: {participant.get('id')}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ שגיאה בבדיקת וואטסאפ: {e}")
        return False

def test_group_deletion(group_id, group_name):
    """בדיקת מחיקת קבוצה"""
    logger.info(f"🧪 בודק מחיקת קבוצה: {group_name} ({group_id})")
    
    try:
        from green_api_client import get_green_api_client
        
        client = get_green_api_client()
        
        # בדיקת פרטי הקבוצה לפני המחיקה
        logger.info("📊 פרטי הקבוצה לפני המחיקה:")
        group_data = client.get_group_data(group_id)
        logger.info(f"  - שם: {group_data.get('subject', 'לא ידוע')}")
        logger.info(f" - משתתפים: {len(group_data.get('participants', []))}")
        
        # בדיקת אם אני מנהל הקבוצה
        participants = group_data.get("participants", [])
        my_participant = None
        for participant in participants:
            if participant.get("isMe", False):
                my_participant = participant
                break
        
        if my_participant:
            is_admin = my_participant.get("isAdmin", False)
            is_super_admin = my_participant.get("isSuperAdmin", False)
            logger.info(f"👤 סטטוס שלי בקבוצה: Admin={is_admin}, SuperAdmin={is_super_admin}")
            
            if not is_admin and not is_super_admin:
                logger.warning("⚠️ אני לא מנהל הקבוצה - לא אוכל להסיר משתתפים")
        else:
            logger.warning("⚠️ לא נמצא מידע עלי בקבוצה")
        
        # ניסיון מחיקה
        logger.info("🚀 מתחיל תהליך מחיקה...")
        result = client.delete_group_completely(group_id)
        logger.info(f"📊 תוצאת המחיקה: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ שגיאה במחיקת קבוצה: {e}")
        return {"success": False, "error": str(e)}

def main():
    """הרצת בדיקות דיבוג"""
    logger.info("🚀 מתחיל בדיקת דיבוג מחיקת קבוצות")
    logger.info("=" * 60)
    
    # בדיקת קבוצות במסד הנתונים
    groups = check_group_in_database()
    
    if not groups:
        logger.info("❌ לא נמצאו קבוצות רלוונטיות במסד הנתונים")
        return
    
    # בדיקת כל קבוצה
    for group_id, group_name in groups:
        logger.info(f"\n🔍 בודק קבוצה: {group_name} ({group_id})")
        logger.info("-" * 40)
        
        # בדיקת קיום בוואטסאפ
        exists_in_whatsapp = check_group_in_whatsapp(group_id)
        
        if exists_in_whatsapp:
            logger.info("✅ הקבוצה קיימת בוואטסאפ")
            
            # שאלת המשתמש אם למחוק
            response = input(f"\nהאם למחוק את הקבוצה '{group_name}'? (y/n): ")
            if response.lower() == 'y':
                result = test_group_deletion(group_id, group_name)
                if result.get('success'):
                    logger.info("🎉 הקבוצה נמחקה בהצלחה!")
                else:
                    logger.error(f"❌ המחיקה נכשלה: {result.get('error')}")
            else:
                logger.info("⏭️ דילוג על מחיקת הקבוצה")
        else:
            logger.info("❌ הקבוצה לא קיימת בוואטסאפ")

if __name__ == "__main__":
    main()
