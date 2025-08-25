# 🚨 NOTFALL-FIX: item_cost FELD MANUELL ENTFERNEN

## PROBLEM
Frontend sendet weiterhin 'item_cost' Feld → HTTP 422 Fehler

## SOFORT-LÖSUNG: MANUELLE CODE-BEARBEITUNG

### SSH in Server:
```bash
ssh fwkantine@IHR_SERVER_IP
cd /var/www/fw-kantine.de
```

### SCHRITT 1: GIT STATUS PRÜFEN
```bash
git status
git log --oneline -5
# Prüfen ob die neuesten Commits da sind
```

### SCHRITT 2: FRONTEND-CODE MANUELL BEARBEITEN
```bash
cd frontend/src
nano App.js
```

### FINDE DIESE ZEILEN UND ÄNDERE SIE:

**SUCHE NACH (ca. Zeile 826):**
```javascript
item_cost: totalCost  // ❌ DIESE ZEILE LÖSCHEN
```

**ERSETZE MIT:**
```javascript
boiled_eggs: 0,
has_coffee: false
```

**SUCHE NACH (ca. Zeile 1189):**
```javascript
item_cost: totalCost  // ❌ DIESE ZEILE LÖSCHEN  
```

**ERSETZE MIT:**
```javascript
// item_cost entfernt - verursacht HTTP 422
```

### SCHRITT 3: DATEI SPEICHERN
```
Ctrl + X → Y → Enter
```

### SCHRITT 4: NEUEN BUILD ERSTELLEN
```bash
cd /var/www/fw-kantine.de/frontend
yarn build --verbose
```

### SCHRITT 5: WEBSERVER NEU LADEN
```bash
sudo systemctl reload nginx
```

### SCHRITT 6: BROWSER-CACHE KOMPLETT LEEREN
1. Browser öffnen
2. F12 (Developer Tools)
3. Rechtsklick auf Reload-Button
4. "Empty Cache and Hard Reload"

## ALTERNATIVE: SCHNELLER WORKAROUND

### Falls Code-Bearbeitung zu kompliziert:
```bash
cd /var/www/fw-kantine.de
git reset --hard HEAD
git pull origin main --force
cd frontend
rm -rf node_modules build
yarn install
yarn build
sudo systemctl reload nginx
```

## VERIFIKATION

### Nach dem Fix:
1. **Öffnen Sie:** https://fw-kantine.de
2. **F12 → Network Tab öffnen**
3. **Frühstück bestellen**
4. **POST Request anklicken**
5. **Request Payload prüfen:**
   - ✅ SOLLTE NICHT enthalten: `item_cost`
   - ✅ SOLLTE enthalten: `total_halves`, `white_halves`, etc.

## ERFOLG WENN:
- ✅ Kein `item_cost` im Network Request
- ✅ HTTP 200 statt HTTP 422
- ✅ "Bestellung erfolgreich" statt Fehlermeldung
- ✅ Bestellung erscheint im Verlauf

🎯 **DAS SOLLTE DEN BUG ENDGÜLTIG BEHEBEN!**