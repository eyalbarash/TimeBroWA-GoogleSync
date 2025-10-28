# 🚀 הוראות התקנה מפורטות - WAMems

## שלב 1: העלאת הקבצים לשרת

### אופציה A: העלאה אוטומטית
```bash
# הרץ את סקריפט ההעלאה
./upload-to-server.sh
```

### אופציה B: העלאה ידנית
```bash
# העתק את כל הקבצים מהתיקייה deployment
scp -r deployment/* root@45.159.220.65:/root/wamems/
```

## שלב 2: התחברות לשרת והתקנה

```bash
# התחבר לשרת
ssh root@45.159.220.65

# עבור לתיקיית האפליקציה
cd /root/wamems

# הרץ את סקריפט ההתקנה המלא
chmod +x install-wamems.sh
./install-wamems.sh
```

## שלב 3: הגדרת סיסמת Admin

```bash
# עבור לתיקיית האפליקציה
cd /opt/wamems

# צור סיסמת admin (החלף YOUR_PASSWORD)
sudo -u wamems python3 -c "
from backend.auth_manager import AuthManager
auth = AuthManager('temp', 'admin@cig.chat', 'temp')
password = input('Enter admin password: ')
hash_value = auth.hash_password(password)
print('ADMIN_PASSWORD_HASH=' + hash_value)
"

# עדכן את קובץ ה-environment
nano .env.production
# החלף את ADMIN_PASSWORD_HASH=CHANGE_THIS_PASSWORD_HASH
# בערך שקיבלת מהפקודה הקודמת

# הפעל מחדש את השירותים
sudo -u wamems docker-compose restart
```

## שלב 4: בדיקת ההתקנה

```bash
# בדוק שהשירותים רצים
sudo -u wamems docker-compose ps

# בדוק את הלוגים
sudo -u wamems docker-compose logs -f

# בדוק את האתר
curl https://evolution.cig.chat/health
```

## שלב 5: הגדרת Green API

1. פתח את הדפדפן וגש ל: https://evolution.cig.chat
2. התחבר עם admin@cig.chat והסיסמה שיצרת
3. לחץ על "Setup" ליד Green API
4. הזן את ה-credentials מ-Green API Console
5. לחץ על "Test & Save"

## 🔧 פקודות ניהול

```bash
# צפייה בלוגים
cd /opt/wamems && sudo -u wamems docker-compose logs -f

# הפעלה מחדש
systemctl restart wamems

# עצירה
systemctl stop wamems

# סטטוס
systemctl status wamems

# עדכון
cd /opt/wamems
git pull  # אם יש git repository
sudo -u wamems docker-compose up -d --build
```

## 🆘 פתרון בעיות

### בעיה: השירותים לא רצים
```bash
# בדוק את הלוגים
sudo -u wamems docker-compose logs

# בדוק מקום פנוי
df -h

# בדוק זיכרון
free -h
```

### בעיה: SSL לא עובד
```bash
# בדוק את התעודה
certbot certificates

# צור תעודה חדשה
certbot certonly --webroot -w /var/www/certbot -d evolution.cig.chat
```

### בעיה: לא ניתן להתחבר לאתר
```bash
# בדוק firewall
ufw status

# בדוק שירותים
systemctl status wamems
```

## 📞 תמיכה

אם יש בעיות:
1. בדוק את הלוגים
2. ודא שה-DNS מוגדר נכון
3. ודא שה-firewall פתוח
4. בדוק שהשירותים רצים
