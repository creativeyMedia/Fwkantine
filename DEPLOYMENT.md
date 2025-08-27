# 🚀 Feuerwehr Kantine - Multi-Tenant Deployment Guide

## 📋 Übersicht
Diese Anleitung zeigt, wie Sie die Feuerwehr Kantine App auf einer neuen Domain/Subdomain deployen. Das System unterstützt Multi-Tenant Architektur für mehrere Feuerwachen.

## 🎯 Deployment Beispiel
- **Hauptdomain**: `fw-kantine.de` (Port 8001)
- **Neue Instanz**: `4600.fw-kantine.de` (Port 8002)
- **Zukünftige**: `4601.fw-kantine.de` (Port 8003), etc.

---

## 📁 Server Vorbereitung

### 1. Verzeichnisse erstellen
```bash
# Hauptverzeichnis für neue Instanz
sudo mkdir -p /var/www/4600.fw-kantine.de
sudo chown -R www-data:www-data /var/www/4600.fw-kantine.de

# Unterverzeichnisse
sudo mkdir -p /var/www/4600.fw-kantine.de/backend
sudo mkdir -p /var/www/4600.fw-kantine.de/frontend
```

### 2. MongoDB Datenbank einrichten
```bash
# MongoDB User und Datenbank erstellen
mongosh
use kantine_4600
db.createUser({
  user: "kantine_4600_admin",
  pwd: "IHR_SICHERES_PASSWORD",
  roles: [{ role: "readWrite", db: "kantine_4600" }]
})
```

---

## 🔧 Code Deployment

### 1. Repository clonen/kopieren
```bash
cd /var/www/4600.fw-kantine.de
# Kopieren Sie die Dateien von GitHub oder bestehendem Deployment
```

### 2. Backend Konfiguration

**Datei**: `/var/www/4600.fw-kantine.de/backend/.env`
```bash
MONGO_URL=mongodb://kantine_4600_admin:IHR_PASSWORD@127.0.0.1:27017/kantine_4600?authSource=kantine_4600
DB_NAME=kantine_4600
CORS_ORIGINS="https://4600.fw-kantine.de,http://4600.fw-kantine.de"

# 🔒 SICHERHEITSEINSTELLUNGEN
ENVIRONMENT="production"
ALLOW_DANGEROUS_APIS="false"

# Password Configuration - ÄNDERN SIE DIESE!
DEPARTMENT_PASSWORD_DEFAULT="neues_password1"
ADMIN_PASSWORD_DEFAULT="neues_admin1"
MASTER_PASSWORD="neues_master123"
CENTRAL_ADMIN_PASSWORD="neues_admin123"

# Department-specific passwords (für jede Feuerwache unterschiedlich!)
DEPT_1_PASSWORD="fw4600_dept1"
DEPT_1_ADMIN_PASSWORD="fw4600_admin1"
DEPT_2_PASSWORD="fw4600_dept2"
DEPT_2_ADMIN_PASSWORD="fw4600_admin2"
DEPT_3_PASSWORD="fw4600_dept3"
DEPT_3_ADMIN_PASSWORD="fw4600_admin3"
DEPT_4_PASSWORD="fw4600_dept4"
DEPT_4_ADMIN_PASSWORD="fw4600_admin4"
```

### 3. Frontend Konfiguration

**Datei**: `/var/www/4600.fw-kantine.de/frontend/.env`
```bash
REACT_APP_BACKEND_URL=https://4600.fw-kantine.de
WDS_SOCKET_PORT=443
```

### 4. Python Virtual Environment
```bash
cd /var/www/4600.fw-kantine.de/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Frontend Build erstellen
```bash
cd /var/www/4600.fw-kantine.de/frontend
npm install
npm run build
# Build Files werden in /frontend/build/ erstellt
```

---

## ⚙️ Apache2 Konfiguration

### 1. Virtual Host erstellen

**Datei**: `/etc/apache2/sites-available/4600.fw-kantine.de.conf`
```apache
<VirtualHost *:80>
    ServerName 4600.fw-kantine.de
    DocumentRoot /var/www/4600.fw-kantine.de/frontend/build
    Redirect permanent / https://4600.fw-kantine.de/
</VirtualHost>

<VirtualHost *:443>
    ServerName 4600.fw-kantine.de
    DocumentRoot /var/www/4600.fw-kantine.de/frontend/build
    
    # SSL Configuration
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/4600.fw-kantine.de/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/4600.fw-kantine.de/privkey.pem
    
    # Frontend Directory
    <Directory "/var/www/4600.fw-kantine.de/frontend/build">
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
        DirectoryIndex index.html
        
        RewriteEngine On
        RewriteBase /
        RewriteRule ^index\.html$ - [L]
        RewriteCond %{REQUEST_FILENAME} !-f
        RewriteCond %{REQUEST_FILENAME} !-d
        RewriteRule . /index.html [L]
    </Directory>
    
    # Backend API Proxy - ACHTUNG: Port muss unique sein!
    ProxyRequests Off
    ProxyPreserveHost On
    ProxyPass /api http://127.0.0.1:8002/api
    ProxyPassReverse /api http://127.0.0.1:8002/api
    
    # CORS Headers
    <LocationMatch "^/api">
        Header always set Access-Control-Allow-Origin "https://4600.fw-kantine.de"
        Header always set Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS"
        Header always set Access-Control-Allow-Headers "Content-Type, Authorization, X-Requested-With"
        Header always set Access-Control-Allow-Credentials "true"
        
        # Handle OPTIONS requests
        RewriteEngine On
        RewriteCond %{REQUEST_METHOD} OPTIONS
        RewriteRule ^(.*)$ $1 [R=200,L]
    </LocationMatch>
    
    ErrorLog ${APACHE_LOG_DIR}/4600.fw-kantine.de_error.log
    CustomLog ${APACHE_LOG_DIR}/4600.fw-kantine.de_access.log combined
</VirtualHost>
```

### 2. Apache Module aktivieren
```bash
sudo a2enmod ssl
sudo a2enmod rewrite
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod headers
```

### 3. Site aktivieren
```bash
sudo a2ensite 4600.fw-kantine.de.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

---

## 🔄 Systemd Service für Backend

### 1. Service Datei erstellen

**Datei**: `/etc/systemd/system/4600.fw-kantine-backend.service`
```ini
[Unit]
Description=Kantine 4600 Backend Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/4600.fw-kantine.de/backend
Environment=PATH=/var/www/4600.fw-kantine.de/backend/venv/bin
ExecStart=/var/www/4600.fw-kantine.de/backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8002
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 2. Service starten
```bash
sudo systemctl daemon-reload
sudo systemctl enable 4600.fw-kantine-backend.service
sudo systemctl start 4600.fw-kantine-backend.service
sudo systemctl status 4600.fw-kantine-backend.service
```

---

## 🌐 SSL Zertifikat (Let's Encrypt)

```bash
# Zertifikat erstellen
sudo certbot --apache -d 4600.fw-kantine.de

# Auto-Renewal prüfen
sudo certbot renew --dry-run
```

---

## 🔍 Testing & Troubleshooting

### 1. Backend direkt testen
```bash
curl -v http://localhost:8002/api/departments
# Sollte 200 OK mit JSON Response zeigen
```

### 2. Frontend über Apache testen  
```bash
curl -I https://4600.fw-kantine.de/
# Sollte 200 OK zeigen
```

### 3. API über Apache testen
```bash
curl -v https://4600.fw-kantine.de/api/departments
# Sollte 200 OK mit JSON Response zeigen
```

### 4. Logs prüfen
```bash
# Backend Service Logs
sudo journalctl -u 4600.fw-kantine-backend.service -f

# Apache Logs
sudo tail -f /var/log/apache2/4600.fw-kantine.de_error.log
sudo tail -f /var/log/apache2/4600.fw-kantine.de_access.log
```

---

## 🚨 Häufige Probleme & Lösungen

### Problem: 403 Forbidden
**Ursache**: Frontend Build Files fehlen oder falsche Berechtigungen
```bash
# Lösung:
sudo chown -R www-data:www-data /var/www/4600.fw-kantine.de
sudo chmod -R 755 /var/www/4600.fw-kantine.de
ls -la /var/www/4600.fw-kantine.de/frontend/build/index.html
```

### Problem: CORS Errors
**Ursache**: Falsche Domain in CORS_ORIGINS oder Backend nicht erreichbar
```bash
# Lösung: .env prüfen
grep CORS_ORIGINS /var/www/4600.fw-kantine.de/backend/.env
# Sollte Ihre Domain enthalten
```

### Problem: Backend nicht erreichbar
**Ursache**: Port bereits belegt oder Service nicht gestartet
```bash
# Prüfen:
sudo netstat -tulpn | grep :8002
sudo systemctl status 4600.fw-kantine-backend.service

# Anderen Port verwenden falls nötig (8003, 8004, etc.)
```

### Problem: React App lädt nicht
**Ursache**: Build Files nicht im richtigen Verzeichnis
```bash
# Lösung: DocumentRoot in Apache Config prüfen
# Muss auf /frontend/build/ zeigen oder Build Files ins Hauptverzeichnis kopieren
```

---

## 📋 Port-Schema für Multi-Tenant

| Domain | Port | Service |
|--------|------|---------|
| fw-kantine.de | 8001 | Original |
| 4600.fw-kantine.de | 8002 | Feuerwehr 4600 |
| 4601.fw-kantine.de | 8003 | Feuerwehr 4601 |
| 4602.fw-kantine.de | 8004 | Feuerwehr 4602 |

---

## ✅ Final Checklist

- [ ] Domain zeigt auf Server
- [ ] MongoDB Datenbank erstellt
- [ ] .env Files konfiguriert (Backend + Frontend)
- [ ] Requirements installiert
- [ ] Frontend Build erstellt
- [ ] Apache Virtual Host konfiguriert
- [ ] SSL Zertifikat installiert
- [ ] Backend Service läuft
- [ ] Apache2 neu gestartet
- [ ] Tests erfolgreich

---

## 🔒 Sicherheits-Empfehlungen

1. **Passwörter ändern**: Alle Default-Passwörter in .env anpassen
2. **MongoDB User**: Separate User pro Instanz verwenden
3. **SSL**: Immer HTTPS verwenden
4. **Firewall**: Nur notwendige Ports öffnen
5. **Backups**: Regelmäßige Datenbank-Backups
6. **Updates**: System und Dependencies aktuell halten

---

## 📞 Support

Bei Problemen:
1. Logs prüfen (siehe Testing Sektion)
2. Konfiguration mit Vorlage vergleichen
3. Port-Konflikte prüfen
4. Berechtigungen überprüfen

**Das Deployment-System ist getestet und produktionsbereit!** 🎉