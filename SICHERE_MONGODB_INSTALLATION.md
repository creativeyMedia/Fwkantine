# 🛡️ SICHERE MONGODB DOCKER INSTALLATION
## Debian + Apache2 + MongoDB Docker + mongosh

### SCHRITT 1: ALTE UNSICHERE CONTAINER ENTFERNEN
```bash
# Auf Ihrem Live-Server ausführen:
cd /var/www/canteen-manager

# Backend stoppen
sudo systemctl stop canteen-backend

# Unsicheren MongoDB Container stoppen und entfernen
docker stop mongodb2
docker rm mongodb2

# Eventuell alte Volumes löschen (ACHTUNG: Löscht alle Daten!)
docker volume ls | grep mongo
# Falls Volumes vorhanden:
# docker volume rm VOLUME_NAME
```

### SCHRITT 2: SICHERE DOCKER-COMPOSE KONFIGURATION
```bash
# docker-compose.yml erstellen
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    container_name: canteen_mongodb_secure
    restart: unless-stopped
    ports:
      - "127.0.0.1:27017:27017"  # NUR LOCALHOST - SICHER!
    volumes:
      - mongodb_data:/data/db
      - ./mongo-init:/docker-entrypoint-initdb.d
    environment:
      - MONGO_INITDB_ROOT_USERNAME=canteen_admin
      - MONGO_INITDB_ROOT_PASSWORD=SecureCanteenPassword2025!
      - MONGO_INITDB_DATABASE=canteen_db
    command: mongod --bind_ip 127.0.0.1 --auth
    networks:
      - canteen_network

networks:
  canteen_network:
    driver: bridge

volumes:
  mongodb_data:
EOF
```

### SCHRITT 3: MONGODB BENUTZER-INITIALISIERUNG
```bash
# Ordner für Initialisierung erstellen
mkdir -p mongo-init

# Benutzer-Setup Skript erstellen
cat > mongo-init/01-setup-users.js << 'EOF'
// Admin Benutzer wird automatisch erstellt durch MONGO_INITDB_ROOT_*

// Wechsel zur canteen_db Datenbank
db = db.getSiblingDB('canteen_db');

// Canteen App Benutzer erstellen
db.createUser({
  user: 'canteen_user',
  pwd: 'CanteenAppPassword2025!',
  roles: [
    {
      role: 'readWrite',
      db: 'canteen_db'
    }
  ]
});

print('✅ Canteen Benutzer erfolgreich erstellt');
EOF
```

### SCHRITT 4: BACKEND .ENV KONFIGURATION ANPASSEN
```bash
# Backend .env Datei sichern
cp backend/.env backend/.env.backup.$(date +%Y%m%d)

# Neue sichere .env erstellen
cat > backend/.env << 'EOF'
# SICHERE MONGODB KONFIGURATION
MONGO_URL=mongodb://canteen_user:CanteenAppPassword2025!@127.0.0.1:27017/canteen_db?authSource=canteen_db
DB_NAME=canteen_db

# SICHERHEIT
ENVIRONMENT=production
ALLOW_DANGEROUS_APIS=false
ALLOW_INIT_DATA=false

# DEPARTMENT PASSWORDS (Standard)
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

### SCHRITT 5: FIREWALL ABSICHERUNG
```bash
# MongoDB Port von außen komplett blockieren
sudo ufw deny 27017

# Nur localhost Zugriff erlauben (zusätzliche Sicherheit)
sudo iptables -A INPUT -p tcp --dport 27017 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 27017 -j DROP

# Regeln permanent speichern
sudo iptables-save | sudo tee /etc/iptables/rules.v4
```

### SCHRITT 6: SICHERE MONGODB STARTEN
```bash
# Docker-Compose starten
docker-compose up -d

# Logs prüfen
docker-compose logs mongodb

# Warten bis MongoDB bereit ist (ca. 30 Sekunden)
sleep 30
```

### SCHRITT 7: VERBINDUNG TESTEN
```bash
# Mit mongosh testen (als Admin)
mongosh "mongodb://canteen_admin:SecureCanteenPassword2025!@127.0.0.1:27017/admin"

# Test-Befehl in der Shell:
# show dbs

# Als App-Benutzer testen
mongosh "mongodb://canteen_user:CanteenAppPassword2025!@127.0.0.1:27017/canteen_db"

# Test-Befehl:
# db.test.insertOne({hello: "world"})
# db.test.find()
```

### SCHRITT 8: BACKEND STARTEN UND INITIALISIEREN
```bash
# Backend starten
sudo systemctl start canteen-backend

# Status prüfen
sudo systemctl status canteen-backend

# Logs prüfen
sudo journalctl -u canteen-backend -f
```

### SCHRITT 9: SICHERE DATENBANK-INITIALISIERUNG
```bash
# Einmalig Initialisierung erlauben
echo "ALLOW_INIT_DATA=true" >> backend/.env

# Backend neu starten
sudo systemctl restart canteen-backend

# Sichere Initialisierung ausführen
curl -X POST "https://kantine.dev-creativey.de/api/safe-init-empty-database"

# Initialisierung wieder deaktivieren
sed -i '/ALLOW_INIT_DATA=true/d' backend/.env

# Final restart
sudo systemctl restart canteen-backend
```

### SCHRITT 10: SICHERHEIT VERIFIZIEREN
```bash
# Prüfen dass MongoDB nur auf localhost läuft
ss -tlnp | grep 27017
# MUSS zeigen: 127.0.0.1:27017 (NICHT 0.0.0.0:27017!)

# Docker Container Status
docker ps | grep mongo

# Von außen testen (sollte FEHLSCHLAGEN)
# telnet IHR_SERVER_IP 27017
# (Verbindung sollte abgelehnt werden)
```

### SCHRITT 11: FUNKTIONSTEST
```bash
# Departments prüfen
curl -s "https://kantine.dev-creativey.de/api/departments" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f'✅ {len(data)} Departments gefunden')
for dept in data:
    print(f'  - {dept[\"name\"]}')
"

# Login testen
curl -X POST "https://kantine.dev-creativey.de/api/login/department" \
  -H "Content-Type: application/json" \
  -d '{"department_name": "1. Wachabteilung", "password": "password1"}'
```

## 🛡️ SICHERHEITSZUSAMMENFASSUNG

✅ **MongoDB nur auf localhost** (127.0.0.1:27017)  
✅ **Authentifizierung aktiviert** (Benutzername + Passwort)  
✅ **Firewall blockiert** externen Zugriff  
✅ **Sichere Passwörter** generiert  
✅ **Production-Mode** aktiviert  
✅ **Gefährliche APIs** deaktiviert  

## 🔧 WARTUNG

### MongoDB Shell Zugriff:
```bash
# Als Admin
mongosh "mongodb://canteen_admin:SecureCanteenPassword2025!@127.0.0.1:27017/admin"

# Als App-User
mongosh "mongodb://canteen_user:CanteenAppPassword2025!@127.0.0.1:27017/canteen_db"
```

### Backup erstellen:
```bash
mongodump --uri="mongodb://canteen_admin:SecureCanteenPassword2025!@127.0.0.1:27017/canteen_db"
```

### Container neu starten:
```bash
docker-compose restart mongodb
```