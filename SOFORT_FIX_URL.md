# 🚨 SOFORTIGER FIX: Frontend URL-Konfiguration

## PROBLEM
Frontend sendet API-Calls an falsche URL → Bestellungen schlagen fehl

## LÖSUNG: SSH in Ihren Server

### SCHRITT 1: Frontend .env korrigieren
```bash
# SSH in den Server
ssh fwkantine@IHR_SERVER_IP

# Zum Frontend-Verzeichnis
cd /var/www/fw-kantine.de/frontend

# Aktuelle .env prüfen
cat .env

# .env korrigieren
nano .env

# Inhalt ändern zu:
REACT_APP_BACKEND_URL=https://fw-kantine.de

# Speichern: Ctrl+X, Y, Enter
```

### SCHRITT 2: Frontend neu bauen
```bash
# Im frontend-Verzeichnis:
yarn build

# Prüfen dass Build erfolgreich
ls -la build/
```

### SCHRITT 3: Webserver neu laden
```bash
# Nginx neu laden
sudo systemctl reload nginx

# ODER Apache neu laden (falls Sie Apache nutzen)
sudo systemctl reload apache2
```

### SCHRITT 4: Browser-Cache leeren
- **Wichtig:** Besucher müssen Browser-Cache leeren
- **Oder:** Hard-Refresh mit Ctrl+F5

## VERIFIKATION

### Test 1: API-Endpoint direkt
```bash
curl -s "https://fw-kantine.de/api/departments" | head -20
# Sollte Department-Daten zeigen
```

### Test 2: Frontend testen  
1. Website neu laden: https://fw-kantine.de
2. Frühstücks-Bestellung versuchen
3. Sollte jetzt funktionieren!

## URSACHE DES PROBLEMS
Nach dem Deployment wurde die alte Development-URL nicht aktualisiert, 
wodurch das Frontend API-Calls an den falschen Server sendet.

✅ **Nach diesem Fix sollten alle Bestellungen wieder funktionieren!**