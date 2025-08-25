# 🖥️ NEUER SERVER: KOMPLETTES SETUP

## 🎯 SERVERBESTELLUNG

### **EMPFOHLENE KONFIGURATION:**
```
Provider: Hetzner Cloud CX21 (oder ähnlich)
CPU: 2 vCores
RAM: 4GB
Storage: 40GB SSD
OS: Debian 12 (Bookworm)
Rechenzentrum: Deutschland (Nürnberg/Falkenstein)
```

## 🔧 INITIAL-SETUP NACH SERVERERHALT

### **1. ERSTE ANMELDUNG & SICHERHEIT**
```bash
# SSH Key erstellen (auf Ihrem lokalen Computer)
ssh-keygen -t ed25519 -C "canteen-server-key"

# Key zum Server hinzufügen (beim Provider oder manuell)
# Dann anmelden:
ssh root@IHR_SERVER_IP

# System aktualisieren
apt update && apt upgrade -y

# Non-root Benutzer erstellen
adduser canteen
usermod -aG sudo canteen

# SSH Keys für neuen Benutzer
mkdir -p /home/canteen/.ssh
cp ~/.ssh/authorized_keys /home/canteen/.ssh/
chown -R canteen:canteen /home/canteen/.ssh
chmod 700 /home/canteen/.ssh
chmod 600 /home/canteen/.ssh/authorized_keys
```

### **2. SICHERHEIT KONFIGURIEREN**
```bash
# SSH absichern
nano /etc/ssh/sshd_config
# Ändern:
# PermitRootLogin no
# PasswordAuthentication no
# Port 2222 (optional, anderer Port)

systemctl restart sshd

# Firewall konfigurieren
ufw default deny incoming
ufw default allow outgoing
ufw allow 2222/tcp  # SSH (oder 22 wenn Standard-Port)
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable

# Fail2ban installieren
apt install fail2ban -y
systemctl enable fail2ban
```

### **3. DOCKER INSTALLIEREN**
```bash
# Als canteen User anmelden
su - canteen

# Docker GPG Key
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Docker Repository
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Docker installieren
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y

# User zu docker Gruppe
sudo usermod -aG docker canteen
newgrp docker

# Docker testen
docker run hello-world
```

### **4. NGINX INSTALLIEREN**
```bash
sudo apt install nginx -y
sudo systemctl enable nginx
sudo systemctl start nginx

# Nginx Konfiguration für Ihre Domain
sudo nano /etc/nginx/sites-available/kantine
```

### **5. SSL ZERTIFIKAT (Let's Encrypt)**
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d kantine.dev-creativey.de
```

### **6. PYTHON & NODE.JS**
```bash
# Python 3.11+
sudo apt install python3 python3-pip python3-venv -y

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Yarn installieren
npm install -g yarn
```

### **7. ANWENDUNGSORDNER ERSTELLEN**
```bash
sudo mkdir -p /var/www/canteen-manager
sudo chown canteen:canteen /var/www/canteen-manager
cd /var/www/canteen-manager
```

## 🚀 DEPLOYMENT VORBEREITUNG

### **GITHUB DEPLOYMENT KEYS**
```bash
# SSH Key für GitHub
ssh-keygen -t ed25519 -C "canteen-deployment-key"

# Public Key zu GitHub Repository hinzufügen
cat ~/.ssh/id_ed25519.pub
```

### **SYSTEMD SERVICE SETUP**
```bash
# Backend Service erstellen
sudo nano /etc/systemd/system/canteen-backend.service

[Unit]
Description=Canteen Management Backend
After=network.target

[Service]
Type=simple
User=canteen
WorkingDirectory=/var/www/canteen-manager/backend
Environment=PATH=/var/www/canteen-manager/backend/venv/bin
ExecStart=/var/www/canteen-manager/backend/venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always

[Install]
WantedBy=multi-user.target
```

### **MONGODB DOCKER SETUP**
```bash
cd /var/www/canteen-manager

# Sichere docker-compose.yml erstellen
nano docker-compose.yml
# (Inhalt aus vorheriger Anleitung)

# MongoDB starten
docker compose up -d
```

## 🔍 MONITORING & WARTUNG

### **LOG-MONITORING**
```bash
# Systemd Journal für Backend
journalctl -u canteen-backend -f

# Docker Logs
docker compose logs -f mongodb

# Nginx Logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### **BACKUP-STRATEGIE**
```bash
# MongoDB Backup Skript
nano backup-db.sh

#!/bin/bash
DATE=$(date '+%Y%m%d_%H%M%S')
mongodump --uri="mongodb://canteen_admin:PASSWORD@127.0.0.1:27017/canteen_db" --out="/home/canteen/backups/mongodb_$DATE"
tar -czf "/home/canteen/backups/canteen_backup_$DATE.tar.gz" "/home/canteen/backups/mongodb_$DATE"
rm -rf "/home/canteen/backups/mongodb_$DATE"

# Alte Backups löschen (älter als 7 Tage)
find /home/canteen/backups -name "canteen_backup_*.tar.gz" -mtime +7 -delete

chmod +x backup-db.sh

# Cron Job für tägliche Backups
crontab -e
# Hinzufügen:
# 0 2 * * * /home/canteen/backup-db.sh
```

## ✅ DEPLOYMENT-BEREIT CHECKLISTE

```
✅ Server mit Debian 12 aufgesetzt
✅ SSH Key-Authentifizierung aktiviert
✅ Root-Login deaktiviert
✅ Firewall konfiguriert (UFW)
✅ Fail2ban installiert
✅ Docker + Docker Compose installiert
✅ Nginx installiert und konfiguriert
✅ SSL Zertifikat installiert
✅ Python 3.11+ + venv verfügbar
✅ Node.js 18+ + Yarn installiert
✅ MongoDB Docker Container bereit
✅ Systemd Service konfiguriert
✅ Backup-Skript eingerichtet
✅ Domain DNS konfiguriert
```

## 🎯 FINALE SCHRITTE

Nach diesem Setup können Sie:
1. **GitHub Repository klonen**
2. **Dependencies installieren**
3. **Sichere .env Konfiguration**
4. **Services starten**
5. **Datenbank initialisieren**

Ihr neuer Server ist dann **100% sicher** und **production-ready**!