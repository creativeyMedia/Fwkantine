# 🚀 GITHUB UPDATE & DEPLOYMENT FÜR FIX

## SCHRITT 1: AKTUELLE ÄNDERUNGEN VON GITHUB HOLEN

### SSH in Ihren Server:
```bash
ssh fwkantine@IHR_SERVER_IP
# oder
ssh root@IHR_SERVER_IP
```

### Zum App-Verzeichnis:
```bash
cd /var/www/fw-kantine.de
```

### GitHub Pull (neueste Änderungen holen):
```bash
git pull origin main
# oder falls main Branch anders heißt:
git pull origin master
```

## SCHRITT 2: FRONTEND NEU BAUEN

### Zum Frontend-Verzeichnis:
```bash
cd frontend
```

### Dependencies prüfen (falls nötig):
```bash
yarn install
```

### NEUES PRODUCTION BUILD:
```bash
yarn build
```

### Build-Erfolg prüfen:
```bash
ls -la build/
# Sollte neue Dateien mit aktuellem Timestamp zeigen
```

## SCHRITT 3: WEBSERVER NEU LADEN

### Nginx neu laden:
```bash
sudo systemctl reload nginx
```

### ODER Apache (falls Sie Apache nutzen):
```bash
sudo systemctl reload apache2
```

## SCHRITT 4: BACKEND NEU STARTEN (SICHERHEIT)

```bash
sudo systemctl restart fw-kantine-backend
```

## SCHRITT 5: BROWSER-CACHE LEEREN

### WICHTIG für Tests:
1. **Gehen Sie zu:** https://fw-kantine.de
2. **Drücken Sie:** `Ctrl + F5` (Hard-Refresh)
3. **Oder:** Browser-Cache komplett leeren

## SCHRITT 6: TESTEN

### Frühstück bestellen:
1. **Login:** 2. Wachabteilung (costa)
2. **Mitarbeiter wählen:** Jonas Parlow
3. **Frühstück bestellen:** 2x weisse Brötchen + Rührei
4. **✅ SOLLTE JETZT FUNKTIONIEREN!**

## TROUBLESHOOTING

### Falls git pull Probleme macht:
```bash
# Lokale Änderungen verwerfen (VORSICHT!)
git reset --hard HEAD
git pull origin main
```

### Falls Build fehlschlägt:
```bash
# Node modules neu installieren
rm -rf node_modules
yarn install
yarn build
```

### Logs prüfen:
```bash
# Backend-Logs prüfen
sudo journalctl -u fw-kantine-backend -f

# Nginx-Logs prüfen
sudo tail -f /var/log/nginx/error.log
```

## VERIFIKATION

### Erfolgreiche Aktualisierung wenn:
- ✅ Git pull zeigt neue Commits
- ✅ Frontend build läuft ohne Fehler durch
- ✅ Browser zeigt aktualisierte Seite (nach Cache-Clear)
- ✅ Frühstücks-Bestellung funktioniert ohne HTTP 422 Fehler
- ✅ Console zeigt keine "Fehler beim Speichern der Bestellung" mehr

🎉 **Nach diesen Schritten sollte der HTTP 422 Bug komplett behoben sein!**