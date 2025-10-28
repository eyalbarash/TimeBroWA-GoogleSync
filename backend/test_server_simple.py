#!/usr/bin/env python3
"""
בדיקה פשוטה של השרת ללא SyncManager
"""

from flask import Flask, jsonify
import sqlite3

app = Flask(__name__)

def get_statistics_simple():
    """קבלת סטטיסטיקות כלליות"""
    stats = {}
    
    try:
        conn = sqlite3.connect('whatsapp_contacts_groups.db')
        cursor = conn.cursor()
        
        # סטטיסטיקות אנשי קשר
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'contact'")
        stats['total_contacts'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'contact' AND include_in_timebro = 1")
        stats['contacts_in_calendar'] = cursor.fetchone()[0]
        
        # סטטיסטיקות קבוצות
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'group'")
        stats['total_groups'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM groups WHERE include_in_timebro = 1")
        stats['groups_in_calendar'] = cursor.fetchone()[0]
        
        # חישוב ישראלים לפי קידומת 972
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE type = 'contact' AND phone_number LIKE '972%'")
        stats['israeli_contacts'] = cursor.fetchone()[0]
        
        conn.close()
    except Exception as e:
        print(f"⚠️ שגיאה בסטטיסטיקות: {e}")
        stats['total_contacts'] = 0
        stats['contacts_in_calendar'] = 0
        stats['total_groups'] = 0
        stats['groups_in_calendar'] = 0
        stats['israeli_contacts'] = 0
    
    return stats

@app.route('/api/stats')
def api_stats():
    """API לקבלת סטטיסטיקות"""
    return jsonify(get_statistics_simple())

@app.route('/')
def index():
    return "Server OK"

if __name__ == '__main__':
    print("🌐 מפעיל שרת בדיקה על http://localhost:8081")
    app.run(host='0.0.0.0', port=8081, debug=False)










