#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
בדיקת מחיקת קבוצת Arcserver
"""

import os
import sys
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
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('arcserver_deletion.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def test_arcserver_deletion():
    """בדיקת מחיקת קבוצת Arcserver"""
    logger.info("🚀 מתחיל בדיקת מחיקת קבוצת Arcserver")
    
    # קבוצת Arcserver
    group_id = "120363419914095358@g.us"
    group_name = "CIG's Contabo Server"
    
    try:
        from green_api_client import get_green_api_client
        
        client = get_green_api_client()
        logger.info("✅ Green API client נוצר בהצלחה")
        
        # בדיקת מצב ה-instance
        state = client.get_state_instance()
        logger.info(f"📡 מצב ה-instance: {state}")
        
        if state.get('stateInstance') != 'authorized':
            logger.error("❌ ה-instance לא מורשה")
            return False
        
        # בדיקת פרטי הקבוצה
        logger.info(f"📊 מקבל פרטי קבוצה: {group_name}")
        group_data = client.get_group_data(group_id)
        logger.info(f"📋 פרטי הקבוצה: {json.dumps(group_data, indent=2, ensure_ascii=False)}")
        
        if "error" in group_data:
            logger.error(f"❌ שגיאה בקבלת פרטי קבוצה: {group_data['error']}")
            return False
        
        # בדיקת משתתפים
        participants = group_data.get("participants", [])
        logger.info(f"👥 נמצאו {len(participants)} משתתפים בקבוצה")
        
        # בדיקת אם אני מנהל
        my_phone = "972549990001@c.us"
        my_participant = None
        for participant in participants:
            if participant.get("id") == my_phone:
                my_participant = participant
                break
        
        if my_participant:
            is_admin = my_participant.get("isAdmin", False)
            is_super_admin = my_participant.get("isSuperAdmin", False)
            logger.info(f"👤 סטטוס שלי: Admin={is_admin}, SuperAdmin={is_super_admin}")
        else:
            logger.warning("⚠️ לא נמצא מידע עלי בקבוצה")
        
        # ניסיון מחיקה
        logger.info("🚀 מתחיל תהליך מחיקה...")
        result = client.delete_group_completely(group_id)
        
        logger.info(f"📊 תוצאת המחיקה: {json.dumps(result, indent=2, ensure_ascii=False)}")
        
        if result.get('success'):
            logger.info("🎉 הקבוצה נמחקה בהצלחה!")
            return True
        else:
            logger.error(f"❌ המחיקה נכשלה: {result.get('error')}")
            return False
        
    except Exception as e:
        logger.error(f"❌ שגיאה כללית: {e}")
        return False

if __name__ == "__main__":
    success = test_arcserver_deletion()
    if success:
        print("✅ הבדיקה הושלמה בהצלחה")
    else:
        print("❌ הבדיקה נכשלה")
    sys.exit(0 if success else 1)


