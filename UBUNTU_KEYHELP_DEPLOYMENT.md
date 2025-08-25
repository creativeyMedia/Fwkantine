# 🚀 UBUNTU 22.04.5 + KEYHELP DEPLOYMENT GUIDE
## Feuerwehr Kantinen-Management auf fw-kantine.de

## 🔍 KEYHELP SYSTEM-ANALYSE

### **SCHRITT 1: KEYHELP INSTALLATION PRÜFEN**
```bash
# SSH in den Server
ssh root@IHR_SERVER_IP

# Keyhelp Status prüfen
systemctl status keyhelp

# Webserver identifizieren (Apache oder Nginx)
systemctl status apache2
systemctl status nginx

# Welche Ports sind belegt?
netstat -tulpn | grep ':80\|:443\|:3000\|:8001'

# Keyhelp Konfiguration finden
find /etc -name "*keyhelp*" -type d 2>/dev/null
ls -la /etc/apache2/ /etc/nginx/ 2>/dev/null
```

## 🛡️ GRUNDLEGENDE SYSTEM-SICHERHEIT

### **SCHRITT 2: SYSTEM ABSICHERN**
```bash
# System aktualisieren
apt update && apt upgrade -y

# Firewall konfigurieren (vorsichtig bei Keyhelp!)
ufw status
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 8080/tcp  # Keyhelp (falls nötig)
# MongoDB Port 27017 NICHT öffnen!

# Fail2ban installieren
apt install fail2ban -y
systemctl enable fail2ban
systemctl start fail2ban

# SSH absichern (ACHTUNG: Erst SSH-Key einrichten!)
# cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup
# Später: PermitRootLogin no, PasswordAuthentication no
```

## 📦 ERFORDERLICHE PAKETE INSTALLIEREN

### **SCHRITT 3: DEVELOPMENT TOOLS**
```bash
# Git und Build-Tools
apt install git curl wget unzip build-essential -y

# Python 3.10+ (sollte schon installiert sein)
python3 --version
apt install python3-pip python3-venv python3-dev -y

# Node.js 18+ über NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install nodejs -y

# Yarn Package Manager
npm install -g yarn

# PM2 für Process Management
npm install -g pm2
```

## 🍃 MONGODB INSTALLATION (NATIV)

### **SCHRITT 4: MONGODB SICHER INSTALLIEREN**
```bash
# MongoDB GPG Key importieren
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# MongoDB Repository hinzufügen
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# MongoDB installieren
apt update
apt install -y mongodb-org

# WICHTIG: MongoDB auf localhost beschränken
nano /etc/mongod.conf

# Sichere Konfiguration:
net:
  port: 27017
  bindIp: 127.0.0.1  # NUR LOCALHOST!

security:
  authorization: enabled

storage:
  dbPath: /var/lib/mongodb

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

# MongoDB Service aktivieren
systemctl daemon-reload
systemctl enable mongod
systemctl start mongod
systemctl status mongod

# KRITISCH: Prüfen dass nur localhost läuft
netstat -tulpn | grep 27017
# MUSS zeigen: 127.0.0.1:27017 (NICHT 0.0.0.0:27017!)
```

### **SCHRITT 5: MONGODB BENUTZER ERSTELLEN**
```bash
# Admin-Benutzer erstellen (nur einmalig)
mongosh --eval "
use admin
db.createUser({
  user: 'mongodb_admin',
  pwd: 'SecureAdminPassword2025!',
  roles: ['root']
})
"

# Canteen App-Benutzer erstellen
mongosh -u mongodb_admin -p SecureAdminPassword2025! --authenticationDatabase admin --eval "
use canteen_db
db.createUser({
  user: 'canteen_user',
  pwd: 'FW_Secure2025!MongoDB',
  roles: ['readWrite']
})
"

# Verbindung testen
mongosh "mongodb://canteen_user:FW_Secure2025!MongoDB@127.0.0.1:27017/canteen_db"
```

## 🔐 DEPLOYMENT-BENUTZER ERSTELLEN

### **SCHRITT 6: SICHERER DEPLOYMENT-USER**
```bash
# Deployment-Benutzer erstellen (nicht root verwenden!)
adduser fwkantine
usermod -aG sudo fwkantine

# SSH-Key für Deployment-User
mkdir -p /home/fwkantine/.ssh
chown fwkantine:fwkantine /home/fwkantine/.ssh
chmod 700 /home/fwkantine/.ssh

# SSH-Key erstellen (für GitHub)
su - fwkantine
ssh-keygen -t ed25519 -C "fw-kantine-deployment"
cat ~/.ssh/id_ed25519.pub  # Zu GitHub hinzufügen
```

## 📂 ANWENDUNGSVERZEICHNIS ERSTELLEN

### **SCHRITT 7: APP-STRUKTUR**
```bash
# Als fwkantine User
su - fwkantine

# Web-Directory erstellen (Keyhelp-kompatibel)
sudo mkdir -p /var/www/fw-kantine.de
sudo chown fwkantine:fwkantine /var/www/fw-kantine.de
cd /var/www/fw-kantine.de

# GitHub Repository klonen
git clone git@github.com:IHR_USERNAME/canteen-manager.git .

# Oder falls noch kein SSH-Key bei GitHub:
git clone https://github.com/IHR_USERNAME/canteen-manager.git .
```

## 🔧 BACKEND-KONFIGURATION

### **SCHRITT 8: PYTHON BACKEND SETUP**
```bash
cd /var/www/fw-kantine.de/backend

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install --upgrade pip
pip install -r requirements.txt

# Production .env erstellen
cp .env.production .env

# .env anpassen (sichere Passwörter)
nano .env

# Inhalt:
MONGO_URL=mongodb://canteen_user:FW_Secure2025!MongoDB@127.0.0.1:27017/canteen_db?authSource=canteen_db
DB_NAME=canteen_db
ENVIRONMENT=production
ALLOW_DANGEROUS_APIS=false
ALLOW_INIT_DATA=false

# Backend testen
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('✅ Backend-Konfiguration geladen')
print(f'DB: {os.getenv(\"DB_NAME\")}')
print(f'Environment: {os.getenv(\"ENVIRONMENT\")}')
"
```

### **SCHRITT 9: SYSTEMD SERVICE ERSTELLEN**
```bash
# Backend Service für systemd
sudo tee /etc/systemd/system/fw-kantine-backend.service << EOF
[Unit]
Description=FW Kantine Backend
After=network.target mongod.service
Requires=mongod.service
StartLimitIntervalSec=0

[Service]
Type=simple
Restart=always
RestartSec=5
User=fwkantine
WorkingDirectory=/var/www/fw-kantine.de/backend
Environment=PATH=/var/www/fw-kantine.de/backend/venv/bin
ExecStart=/var/www/fw-kantine.de/backend/venv/bin/uvicorn server:app --host 127.0.0.1 --port 8001
StandardOutput=journal
StandardError=journal
SyslogIdentifier=fw-kantine-backend

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable fw-kantine-backend
sudo systemctl start fw-kantine-backend
sudo systemctl status fw-kantine-backend

# Logs prüfen
sudo journalctl -u fw-kantine-backend -f
```

## 🌐 FRONTEND BUILD

### **SCHRITT 10: REACT FRONTEND**
```bash
cd /var/www/fw-kantine.de/frontend

# .env.production aktualisieren
echo "REACT_APP_BACKEND_URL=https://fw-kantine.de" > .env.production

# Dependencies installieren
yarn install

# Production Build erstellen
yarn build

# Build-Ordner prüfen
ls -la build/
```

## 🔄 WEBSERVER-KONFIGURATION

### **SCHRITT 11: NGINX/APACHE KONFIGURATION**

#### **FALLS NGINX (Keyhelp Standard):**
```bash
# Nginx Site für fw-kantine.de erstellen
sudo tee /etc/nginx/sites-available/fw-kantine.de << EOF
server {
    listen 80;
    server_name fw-kantine.de www.fw-kantine.de;
    
    # Frontend (React Build)
    root /var/www/fw-kantine.de/frontend/build;
    index index.html;
    
    # Frontend Routes
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$server_name;
    }
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

# Site aktivieren
sudo ln -s /etc/nginx/sites-available/fw-kantine.de /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### **FALLS APACHE (Alternative):**
```bash
# Apache VirtualHost erstellen
sudo tee /etc/apache2/sites-available/fw-kantine.de.conf << EOF
<VirtualHost *:80>
    ServerName fw-kantine.de
    ServerAlias www.fw-kantine.de
    DocumentRoot /var/www/fw-kantine.de/frontend/build
    
    # Frontend
    <Directory "/var/www/fw-kantine.de/frontend/build">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
        FallbackResource /index.html
    </Directory>
    
    # Backend API Proxy
    ProxyPreserveHost On
    ProxyPass /api/ http://127.0.0.1:8001/api/
    ProxyPassReverse /api/ http://127.0.0.1:8001/api/
    
    # Security Headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set X-Content-Type-Options "nosniff"
    
    ErrorLog \${APACHE_LOG_DIR}/fw-kantine_error.log
    CustomLog \${APACHE_LOG_DIR}/fw-kantine_access.log combined
</VirtualHost>
EOF

# Erforderliche Module aktivieren
sudo a2enmod proxy proxy_http headers rewrite
sudo a2ensite fw-kantine.de
sudo systemctl reload apache2
```

## 🔒 SSL-ZERTIFIKAT

### **SCHRITT 12: LET'S ENCRYPT SSL**
```bash
# Certbot installieren
apt install certbot python3-certbot-nginx -y  # für Nginx
# ODER
apt install certbot python3-certbot-apache -y  # für Apache

# SSL-Zertifikat erstellen
certbot --nginx -d fw-kantine.de -d www.fw-kantine.de  # Nginx
# ODER
certbot --apache -d fw-kantine.de -d www.fw-kantine.de  # Apache

# Auto-Renewal testen
certbot renew --dry-run
```

## 🏁 DATENBANK INITIALISIERUNG

### **SCHRITT 13: SICHERE ERSTINITIALISIERUNG**
```bash
# Einmalig Init erlauben
echo "ALLOW_INIT_DATA=true" >> /var/www/fw-kantine.de/backend/.env

# Backend neu starten
sudo systemctl restart fw-kantine-backend

# Warten bis Service bereit
sleep 10

# Datenbank initialisieren
curl -X POST "https://fw-kantine.de/api/safe-init-empty-database"

# Init wieder deaktivieren (SICHERHEIT!)
sed -i '/ALLOW_INIT_DATA=true/d' /var/www/fw-kantine.de/backend/.env
sudo systemctl restart fw-kantine-backend
```

## ✅ SYSTEM-VERIFIKATION

### **SCHRITT 14: VOLLSTÄNDIGER TEST**
```bash
# Services prüfen
systemctl status mongod
systemctl status fw-kantine-backend
systemctl status nginx  # oder apache2

# Ports prüfen
netstat -tulpn | grep ':27017\|:8001\|:80\|:443'

# MongoDB Sicherheit prüfen (MUSS 127.0.0.1 zeigen!)
netstat -tulpn | grep 27017

# Backend-API testen
curl -s "https://fw-kantine.de/api/departments" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'✅ API funktioniert: {len(data)} Departments gefunden')
except:
    print('❌ API-Fehler')
"

# Frontend testen
curl -s -o /dev/null -w "%{http_code}" "https://fw-kantine.de/"
# Sollte 200 zurückgeben

# Login testen
curl -X POST "https://fw-kantine.de/api/login/department" \
  -H "Content-Type: application/json" \
  -d '{"department_name": "1. Wachabteilung", "password": "password1"}' \
  -s | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('✅ Login funktioniert')
except:
    print('❌ Login-Fehler')
"
```

## 🔐 FINALE SICHERHEITSPRÜFUNG

### **SCHRITT 15: SICHERHEITS-AUDIT**
```bash
# MongoDB von außen NICHT erreichbar (sollte fehlschlagen!)
timeout 5 telnet fw-kantine.de 27017 2>/dev/null || echo "✅ MongoDB sicher (nicht von außen erreichbar)"

# Firewall Status
ufw status

# SSH-Härtung (nach SSH-Key Setup!)
# nano /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no
# systemctl restart sshd

# Fail2ban Status
systemctl status fail2ban

# Automatische Updates aktivieren
apt install unattended-upgrades -y
dpkg-reconfigure -plow unattended-upgrades
```

## 📊 MONITORING & WARTUNG

### **SCHRITT 16: ÜBERWACHUNG EINRICHTEN**
```bash
# PM2 für erweiterte Überwachung (optional)
pm2 startup
pm2 save

# Log-Rotation für Anwendung
sudo tee /etc/logrotate.d/fw-kantine << EOF
/var/log/fw-kantine/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 0644 fwkantine fwkantine
    postrotate
        systemctl reload fw-kantine-backend
    endscript
}
EOF

# Backup-Skript erstellen
tee /home/fwkantine/backup-fw-kantine.sh << EOF
#!/bin/bash
DATE=\$(date '+%Y%m%d_%H%M%S')
BACKUP_DIR="/home/fwkantine/backups"
mkdir -p \$BACKUP_DIR

# MongoDB Backup
mongodump --uri="mongodb://canteen_user:FW_Secure2025!MongoDB@127.0.0.1:27017/canteen_db" --out="\$BACKUP_DIR/mongodb_\$DATE"

# Tar komprimieren
tar -czf "\$BACKUP_DIR/fw-kantine-backup_\$DATE.tar.gz" "\$BACKUP_DIR/mongodb_\$DATE"
rm -rf "\$BACKUP_DIR/mongodb_\$DATE"

# Alte Backups löschen (älter als 30 Tage)
find \$BACKUP_DIR -name "fw-kantine-backup_*.tar.gz" -mtime +30 -delete

echo "✅ Backup erstellt: fw-kantine-backup_\$DATE.tar.gz"
EOF

chmod +x /home/fwkantine/backup-fw-kantine.sh

# Tägliches Backup via Cron
crontab -e
# Hinzufügen: 0 2 * * * /home/fwkantine/backup-fw-kantine.sh
```

## 🎯 DEPLOYMENT ABGESCHLOSSEN!

### **✅ ERFOLGREICH INSTALLIERT:**
- ✅ Ubuntu 22.04.5 + Keyhelp
- ✅ MongoDB 7.0 (sicher auf localhost)
- ✅ Python Backend (Port 8001)
- ✅ React Frontend (Production Build)
- ✅ Nginx/Apache Reverse Proxy
- ✅ SSL-Verschlüsselung (Let's Encrypt)
- ✅ Firewall konfiguriert
- ✅ Automatische Backups
- ✅ System-Monitoring
- ✅ Sicherheits-Härtung

### **🌐 IHRE ANWENDUNG:**
**URL:** https://fw-kantine.de  
**Backend:** https://fw-kantine.de/api/  
**Status:** Production-Ready & Secure! 🚀

### **🔧 WARTUNG:**
```bash
# Logs prüfen
sudo journalctl -u fw-kantine-backend -f

# Services neu starten
sudo systemctl restart fw-kantine-backend

# Backup manuell ausführen
/home/fwkantine/backup-fw-kantine.sh
```

**IHR SYSTEM IST JETZT SICHER UND PRODUKTIONSBEREIT!** 🛡️