# 🚀 UBUNTU 22.04 LTS - MONGODB PERFEKTE INSTALLATION

## 🎯 WARUM UBUNTU 22.04 LTS BESSER IST

✅ **Offizielle MongoDB-Unterstützung**  
✅ **Einfachere Installation ohne Docker**  
✅ **Bessere Community-Unterstützung**  
✅ **Weniger Dependency-Konflikte**  
✅ **Stabilere Docker-Integration**  

## 🖥️ SERVER-EMPFEHLUNG

### **HETZNER CLOUD UBUNTU SETUP:**
```
OS: Ubuntu 22.04 LTS
CPU: 2 vCores (CX21)
RAM: 4GB
Storage: 40GB SSD
Preis: ~8€/Monat
```

## 🔧 MONGODB INSTALLATION (OHNE DOCKER!)

### **METHODE 1: NATIVE MONGODB INSTALLATION**
```bash
# MongoDB GPG Key
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor

# MongoDB Repository
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# Installation
sudo apt update
sudo apt install -y mongodb-org

# Service konfigurieren
sudo systemctl enable mongod
sudo systemctl start mongod

# Status prüfen
sudo systemctl status mongod
```

### **METHODE 2: DOCKER (FALLS BEVORZUGT)**
```bash
# Docker installieren (einfacher auf Ubuntu)
sudo apt update
sudo apt install docker.io docker-compose -y
sudo usermod -aG docker $USER

# MongoDB Docker
mkdir -p ~/canteen-app
cd ~/canteen-app

cat > docker-compose.yml << EOF
version: '3.8'
services:
  mongodb:
    image: mongo:7.0
    container_name: canteen_mongo
    restart: unless-stopped
    ports:
      - "127.0.0.1:27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=SecurePassword123!
    command: mongod --bind_ip 127.0.0.1 --auth

volumes:
  mongodb_data:
EOF

docker-compose up -d
```

## 🛡️ MONGODB SICHERHEITSKONFIGURATION

### **FÜR NATIVE INSTALLATION:**
```bash
# MongoDB Konfiguration bearbeiten
sudo nano /etc/mongod.conf

# Sicherer Inhalt:
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

# Service neu starten
sudo systemctl restart mongod

# Admin-Benutzer erstellen
mongosh --eval "
use admin
db.createUser({
  user: 'admin',
  pwd: 'SecureAdminPassword123!',
  roles: ['root']
})
"

# App-Benutzer erstellen
mongosh -u admin -p SecureAdminPassword123! --authenticationDatabase admin --eval "
use canteen_db
db.createUser({
  user: 'canteen_user',
  pwd: 'CanteenAppPassword123!',
  roles: ['readWrite']
})
"
```

## 🚀 CANTEEN-APP DEPLOYMENT

### **1. SYSTEM-DEPENDENCIES**
```bash
# Python & Node.js
sudo apt update
sudo apt install python3 python3-pip python3-venv nodejs npm -y

# Yarn installieren
sudo npm install -g yarn

# Git installieren
sudo apt install git -y
```

### **2. APP-DIRECTORY ERSTELLEN**
```bash
sudo mkdir -p /var/www/canteen-manager
sudo chown $USER:$USER /var/www/canteen-manager
cd /var/www/canteen-manager
```

### **3. GITHUB CLONE**
```bash
# SSH Key erstellen
ssh-keygen -t ed25519 -C "canteen-ubuntu-server"

# Public Key anzeigen (zu GitHub hinzufügen)
cat ~/.ssh/id_ed25519.pub

# Repository klonen
git clone git@github.com:USER/canteen-manager.git .
```

### **4. BACKEND SETUP**
```bash
cd backend

# Virtual Environment
python3 -m venv venv
source venv/bin/activate

# Dependencies
pip install -r requirements.txt

# Sichere .env erstellen
cat > .env << EOF
# SICHERE MONGODB (NATIVE)
MONGO_URL=mongodb://canteen_user:CanteenAppPassword123!@127.0.0.1:27017/canteen_db?authSource=canteen_db
DB_NAME=canteen_db

# PRODUCTION SETTINGS
ENVIRONMENT=production
ALLOW_DANGEROUS_APIS=false
ALLOW_INIT_DATA=false

# DEPARTMENT PASSWORDS
DEPT_1_PASSWORD=password1
DEPT_1_ADMIN_PASSWORD=admin1
DEPT_2_PASSWORD=password2
DEPT_2_ADMIN_PASSWORD=admin2
DEPT_3_PASSWORD=password3
DEPT_3_ADMIN_PASSWORD=admin3
DEPT_4_PASSWORD=password4
DEPT_4_ADMIN_PASSWORD=admin4
EOF
```

### **5. FRONTEND SETUP**
```bash
cd ../frontend

# Dependencies installieren
yarn install

# Production Build
yarn build
```

### **6. SYSTEMD SERVICE**
```bash
# Backend Service
sudo tee /etc/systemd/system/canteen-backend.service << EOF
[Unit]
Description=Canteen Management Backend
After=network.target mongod.service
Requires=mongod.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/var/www/canteen-manager/backend
Environment=PATH=/var/www/canteen-manager/backend/venv/bin
ExecStart=/var/www/canteen-manager/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Service aktivieren
sudo systemctl daemon-reload
sudo systemctl enable canteen-backend
sudo systemctl start canteen-backend
```

### **7. NGINX REVERSE PROXY**
```bash
# Nginx installieren
sudo apt install nginx -y

# Site-Konfiguration
sudo tee /etc/nginx/sites-available/canteen << EOF
server {
    listen 80;
    server_name kantine.dev-creativey.de;

    # Frontend (React Build)
    location / {
        root /var/www/canteen-manager/frontend/build;
        try_files \$uri \$uri/ /index.html;
        index index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Site aktivieren
sudo ln -s /etc/nginx/sites-available/canteen /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### **8. SSL ZERTIFIKAT**
```bash
# Certbot installieren
sudo apt install certbot python3-certbot-nginx -y

# SSL Zertifikat erstellen
sudo certbot --nginx -d kantine.dev-creativey.de
```

### **9. DATENBANK INITIALISIEREN**
```bash
# Einmalig erlauben
echo "ALLOW_INIT_DATA=true" >> /var/www/canteen-manager/backend/.env

# Backend neu starten
sudo systemctl restart canteen-backend

# Datenbank initialisieren
curl -X POST "https://kantine.dev-creativey.de/api/safe-init-empty-database"

# Wieder deaktivieren
sed -i '/ALLOW_INIT_DATA=true/d' /var/www/canteen-manager/backend/.env
sudo systemctl restart canteen-backend
```

## ✅ VORTEILE UBUNTU vs DEBIAN

### **MONGODB:**
```
Ubuntu: ✅ Offizielle Pakete verfügbar
Debian: ❌ Dependency-Konflikte

Ubuntu: ✅ Einfache Installation
Debian: ❌ Nur Docker funktioniert zuverlässig

Ubuntu: ✅ Bessere Systemd-Integration  
Debian: ❌ Mehr manuelle Konfiguration nötig
```

### **COMMUNITY:**
```
Ubuntu: ✅ 10x mehr Tutorials
Ubuntu: ✅ Schnellere Hilfe bei Problemen  
Ubuntu: ✅ Bessere Docker-Dokumentation
```

### **WARTUNG:**
```
Ubuntu: ✅ Automatische Updates einfacher
Ubuntu: ✅ Weniger Breaking Changes
Ubuntu: ✅ Bessere Hardware-Unterstützung
```

## 🎯 FAZIT

**FÜR IHRE ANWENDUNG IST UBUNTU 22.04 LTS DIE BESSERE WAHL:**
- Weniger MongoDB-Probleme
- Einfachere Installation
- Stabilere Docker-Integration  
- Mehr Community-Support
- Weniger Debugging-Zeit

**Sie sparen sich wahrscheinlich Stunden an Troubleshooting!**