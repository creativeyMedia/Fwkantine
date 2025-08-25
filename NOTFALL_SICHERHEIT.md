# 🚨 NOTFALL: MONGODB SICHERHEITSLÜCKE SCHLIESSEN

## SOFORTIGE MASSNAHMEN (AUF IHREM LIVE-SERVER):

### SCHRITT 1: DOCKER CONTAINER STOPPEN UND SICHERN
```bash
# Container stoppen
docker stop mongodb2

# Sichere Docker-Konfiguration erstellen
cd /var/www/canteen-manager
```

### SCHRITT 2: DOCKER-COMPOSE MIT SICHERHEIT ERSTELLEN
```yaml
# docker-compose.yml
version: '3.8'
services:
  mongodb:
    image: mongo:6.0
    container_name: mongodb_secure
    restart: unless-stopped
    ports:
      - "127.0.0.1:27017:27017"  # NUR LOCALHOST!
    volumes:
      - mongodb_data:/data/db
      - ./mongod.conf:/etc/mongo/mongod.conf
    environment:
      - MONGO_INITDB_ROOT_USERNAME=admin
      - MONGO_INITDB_ROOT_PASSWORD=IHR_SICHERES_PASSWORT_HIER
    command: mongod --config /etc/mongo/mongod.conf --auth

volumes:
  mongodb_data:
```

### SCHRITT 3: SICHERE MONGODB KONFIGURATION
```yaml
# mongod.conf
net:
  port: 27017
  bindIp: 127.0.0.1  # NUR LOCALHOST!

security:
  authorization: enabled

storage:
  dbPath: /data/db
```

### SCHRITT 4: FIREWALL ABSICHERN
```bash
# MongoDB Port von außen blockieren
sudo ufw deny 27017
sudo iptables -A INPUT -p tcp --dport 27017 -s 127.0.0.1 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 27017 -j DROP
```

### SCHRITT 5: BACKEND .ENV ANPASSEN
```bash
# .env Datei anpassen für authentifizierte Verbindung
MONGO_URL=mongodb://admin:IHR_SICHERES_PASSWORT_HIER@127.0.0.1:27017/canteen_db?authSource=admin
```

### SCHRITT 6: NEUSTART MIT SICHERHEIT
```bash
# Neuen sicheren Container starten
docker-compose up -d

# Backend neu starten
sudo systemctl restart canteen-backend
```

## VERIFIKATION:
```bash
# Prüfen dass nur localhost erreichbar
ss -tlnp | grep 27017
# Sollte zeigen: 127.0.0.1:27017 (NICHT 0.0.0.0:27017!)
```