# 🚨 SOFORTIGER FIX: Fehlende Menü-Items erstellen

## PROBLEM
Frühstücks- und Beläge-Menü-Tabellen sind nach DB-Cleanup LEER

## LÖSUNG 1: Via Admin-Interface (EMPFOHLEN)

### SCHRITT 1: Als Admin anmelden
1. https://fw-kantine.de → 2. Wachabteilung
2. Passwort: lenny (Admin-Login)

### SCHRITT 2: Frühstücks-Items erstellen
**Gehe zu "Menü & Preise" → "Frühstück verwalten" → "Hinzufügen"**

Erstelle diese Items:
```
1. Brötchen-Art: "weiss" (Weißes Brötchen)
   Preis: 0.50€

2. Brötchen-Art: "koerner" (Körnerbrötchen) 
   Preis: 0.60€
```

### SCHRITT 3: Beläge erstellen
**Gehe zu "Menü & Preise" → "Beläge verwalten" → "Hinzufügen"**

Erstelle diese Beläge:
```
1. ruehrei (Rührei) - 0.00€
2. spiegelei (Spiegelei) - 0.00€
3. eiersalat (Eiersalat) - 0.00€
4. salami (Salami) - 0.00€
5. schinken (Schinken) - 0.00€  
6. kaese (Käse) - 0.00€
7. butter (Butter) - 0.00€
```

## LÖSUNG 2: Via API (FALLBACK)

Falls Admin-Interface nicht funktioniert:

### Admin-Login via API:
```bash
curl -X POST "https://fw-kantine.de/api/login/department-admin" \
  -H "Content-Type: application/json" \
  -d '{"department_name": "2. Wachabteilung", "admin_password": "lenny"}'
```

### Brötchen erstellen:
```bash
# Weißes Brötchen
curl -X POST "https://fw-kantine.de/api/department-admin/menu/breakfast" \
  -H "Content-Type: application/json" \
  -d '{"roll_type": "weiss", "price": 0.50}'

# Körnerbrötchen  
curl -X POST "https://fw-kantine.de/api/department-admin/menu/breakfast" \
  -H "Content-Type: application/json" \
  -d '{"roll_type": "koerner", "price": 0.60}'
```

### Beläge erstellen:
```bash
# Rührei
curl -X POST "https://fw-kantine.de/api/department-admin/menu/toppings" \
  -H "Content-Type: application/json" \
  -d '{"topping_type": "ruehrei", "price": 0.00}'

# Spiegelei
curl -X POST "https://fw-kantine.de/api/department-admin/menu/toppings" \
  -H "Content-Type: application/json" \
  -d '{"topping_type": "spiegelei", "price": 0.00}'

# Eiersalat
curl -X POST "https://fw-kantine.de/api/department-admin/menu/toppings" \
  -H "Content-Type: application/json" \
  -d '{"topping_type": "eiersalat", "price": 0.00}'

# Salami
curl -X POST "https://fw-kantine.de/api/department-admin/menu/toppings" \
  -H "Content-Type: application/json" \
  -d '{"topping_type": "salami", "price": 0.00}'

# Schinken
curl -X POST "https://fw-kantine.de/api/department-admin/menu/toppings" \
  -H "Content-Type: application/json" \
  -d '{"topping_type": "schinken", "price": 0.00}'

# Käse
curl -X POST "https://fw-kantine.de/api/department-admin/menu/toppings" \
  -H "Content-Type: application/json" \
  -d '{"topping_type": "kaese", "price": 0.00}'

# Butter
curl -X POST "https://fw-kantine.de/api/department-admin/menu/toppings" \
  -H "Content-Type: application/json" \
  -d '{"topping_type": "butter", "price": 0.00}'
```

## VERIFIKATION

### Prüfen ob Items erstellt wurden:
```bash
# Frühstücks-Items prüfen
curl -s "https://fw-kantine.de/api/menu/breakfast/fw4abteilung2"

# Beläge prüfen  
curl -s "https://fw-kantine.de/api/menu/toppings/fw4abteilung2"
```

### Frühstücks-Bestellung testen:
1. Gehe zu https://fw-kantine.de
2. Wähle "2. Wachabteilung" (Passwort: costa)
3. Wähle Jonas Parlow
4. Versuche Frühstücks-Bestellung (2x weisse Brötchen)
5. **SOLLTE JETZT FUNKTIONIEREN!** ✅

## WICHTIG
- Alle anderen Departments (1, 3, 4) haben vermutlich das GLEICHE Problem
- Wiederholen Sie den Prozess für alle Departments
- Oder verwenden Sie die API mit entsprechenden department_ids

✅ **Nach diesem Fix sollten alle Frühstücks-Bestellungen wieder funktionieren!**