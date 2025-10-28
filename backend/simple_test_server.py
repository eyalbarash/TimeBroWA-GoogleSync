#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
שרת בדיקה פשוט לממשק TimeBro
"""

from flask import Flask, render_template_string
import sqlite3
import json

app = Flask(__name__)

# HTML פשוט לבדיקה
SIMPLE_HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ממשק TimeBro - בדיקה</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; direction: rtl; }
        .success { color: #28a745; font-size: 24px; text-align: center; }
        .info { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; }
        .button { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 5px; display: inline-block; }
    </style>
</head>
<body>
    <h1>🎉 ממשק TimeBro עובד!</h1>
    
    <div class="success">✅ השרת פועל בהצלחה</div>
    
    <div class="info">
        <h3>📊 נתונים זמינים:</h3>
        <ul>
            <li>👥 {{ total_contacts }} אנשי קשר</li>
            <li>🇮🇱 {{ israeli_contacts }} ישראליים</li>
            <li>👥 {{ total_groups }} קבוצות</li>
            <li>📅 {{ contacts_in_calendar }} מסומנים ליומן</li>
        </ul>
    </div>
    
    <div class="info">
        <h3>🌐 דפים זמינים:</h3>
        <a href="/" class="button">דף הבית</a>
        <a href="/contacts" class="button">אנשי קשר</a>
        <a href="/groups" class="button">קבוצות</a>
    </div>
    
    <div class="info">
        <h3>🔧 אם הממשק לא נטען:</h3>
        <ol>
            <li>רענן את הדפדפן (Cmd+R)</li>
            <li>נקה את ה-cache (Cmd+Shift+R)</li>
            <li>נסה דפדפן אחר</li>
        </ol>
    </div>
    
    <p style="text-align: center; color: #666;">
        נוצר ב-29 בספטמבר 2025
    </p>
</body>
</html>
"""

def get_stats():
    """קבלת סטטיסטיקות"""
    try:
        # סטטיסטיקות contacts
        conn = sqlite3.connect("contacts.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM contacts")
        total_contacts = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE addToCalendar = 1")
        contacts_in_calendar = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM contacts WHERE is_israeli = 1")
        israeli_contacts = cursor.fetchone()[0]
        conn.close()
        
        # סטטיסטיקות groups
        conn = sqlite3.connect("evolution_groups.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM groups")
        total_groups = cursor.fetchone()[0]
        conn.close()
        
        return {
            'total_contacts': total_contacts,
            'israeli_contacts': israeli_contacts,
            'total_groups': total_groups,
            'contacts_in_calendar': contacts_in_calendar
        }
    except Exception as e:
        return {
            'total_contacts': 0,
            'israeli_contacts': 0,
            'total_groups': 0,
            'contacts_in_calendar': 0
        }

@app.route('/')
def index():
    """דף ראשי פשוט"""
    stats = get_stats()
    return render_template_string(SIMPLE_HTML, **stats)

@app.route('/contacts')
def contacts():
    """דף אנשי קשר פשוט"""
    return f"""
    <html dir="rtl">
    <head><title>אנשי קשר</title></head>
    <body>
        <h1>👥 אנשי קשר</h1>
        <p>דף אנשי קשר - תכונה זו זמינה בממשק המלא</p>
        <a href="/">← חזרה לדף הבית</a>
    </body>
    </html>
    """

@app.route('/groups')
def groups():
    """דף קבוצות פשוט"""
    return f"""
    <html dir="rtl">
    <head><title>קבוצות</title></head>
    <body>
        <h1>👥 קבוצות</h1>
        <p>דף קבוצות - תכונה זו זמינה בממשק המלא</p>
        <a href="/">← חזרה לדף הבית</a>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("🌐 מפעיל שרת בדיקה פשוט...")
    print("📱 זמין בכתובת: http://localhost:8081")
    app.run(debug=True, host='0.0.0.0', port=8081)

