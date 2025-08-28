# Datenbank-Migration Guide für Stornierung & Masterpasswort

## Problem-Diagnose
Ihr Server nutzt eine alte Datenbankstruktur ohne die neuen Felder:
- `is_cancelled`, `cancelled_by`, `cancelled_at`, `cancelled_by_name` (Stornierungsfelder)
- Möglicherweise fehlt `MASTER_PASSWORD` in der .env

## OPTION 1: Sichere Neu-Initialisierung (Empfohlen für Test-/Development-Server)

### Schritt 1: Backup erstellen
```bash
# MongoDB Backup (falls wichtige Daten vorhanden)
mongodump --host localhost:27017 --db fw_kantine_production --out /backup/$(date +%Y%m%d)
```

### Schritt 2: Datenbank leeren
```bash
# Verbinden zur MongoDB
mongo fw_kantine_production

# Alle Collections löschen
db.departments.deleteMany({})
db.employees.deleteMany({})
db.orders.deleteMany({})
db.lunch_settings.deleteMany({})
db.menu_breakfast.deleteMany({})
db.menu_toppings.deleteMany({})
db.menu_drinks.deleteMany({})
db.menu_sweets.deleteMany({})
```

### Schritt 3: .env Datei aktualisieren
Stellen Sie sicher, dass Ihre `/app/backend/.env` enthält:
```env
MASTER_PASSWORD="master123dev"
DEPT_1_PASSWORD="password1"
DEPT_1_ADMIN_PASSWORD="admin1"
DEPT_2_PASSWORD="password2"
DEPT_2_ADMIN_PASSWORD="admin2"
DEPT_3_PASSWORD="password3"
DEPT_3_ADMIN_PASSWORD="admin3"
DEPT_4_PASSWORD="password4"
DEPT_4_ADMIN_PASSWORD="admin4"
```

### Schritt 4: Sichere Reinitialisierung
```bash
# Backend neu starten
sudo supervisorctl restart backend

# Dann API aufrufen:
curl -X POST "http://localhost:8001/api/safe-init-empty-database"
```

## OPTION 2: In-Place Migration (Für Production mit wichtigen Daten)

### Schritt 1: .env aktualisieren (wie oben)

### Schritt 2: Backend neu starten
```bash
sudo supervisorctl restart backend
```

### Schritt 3: Migration Script ausführen
```bash
# In MongoDB Shell
mongo fw_kantine_production

# Alle bestehenden Orders mit Stornierungsfeldern erweitern (falls sie fehlen)
db.orders.updateMany(
    { "is_cancelled": { $exists: false } },
    { 
        $set: { 
            "is_cancelled": false
        } 
    }
)

# Verifikation
db.orders.find({"is_cancelled": {$exists: false}}).count()  // Sollte 0 sein
```

## Verifikation nach Migration

### 1. Masterpasswort testen
```bash
curl -X POST "http://localhost:8001/api/login/department" \
-H "Content-Type: application/json" \
-d '{"department_name": "1. Wachabteilung", "password": "master123dev"}'

# Erwartete Antwort:
# {"department_id": "fw4abteilung1", "role": "master_admin", "access_level": "master"}
```

### 2. Stornierungsfelder testen
```bash
# Eine Bestellung erstellen und stornieren, dann prüfen:
mongo fw_kantine_production
db.orders.findOne({"is_cancelled": true})

# Sollte Felder enthalten: is_cancelled, cancelled_at, cancelled_by, cancelled_by_name
```

## Häufige Probleme

### Problem: "MASTER_PASSWORD not found"
**Lösung**: `.env` Datei prüfen und Backend neu starten

### Problem: "is_cancelled field missing" 
**Lösung**: MongoDB Migration (Option 2, Schritt 3) ausführen

### Problem: "Orders still appear in daily summary"
**Lösung**: Backend-Code verwendet bereits Legacy-kompatible Queries - sollte automatisch funktionieren

## Nach erfolgreicher Migration

Beide Funktionen sollten dann funktionieren:
✅ Masterpasswort "master123dev" für alle Dashboards
✅ Stornierte Bestellungen als rote Felder mit "Storniert von..." Meldungen