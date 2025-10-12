# Saldo-Migration bei Mitarbeiter-Verschiebung

## Überblick
Das Developer Dashboard ermöglicht das Verschieben von Mitarbeitern zwischen Wachabteilungen mit korrekter Saldo-Migration.

## Funktionsweise

### Vor der Verschiebung
```
Mitarbeiter: Max Mustermann
Stamm-WA: 1. Wachabteilung
Hauptsaldo: €10 (Frühstück), €5 (Getränke)
Subkonten: 2. WA: €0, 3. WA: €2 (Getränke)
```

### Nach Verschiebung zu 2. Wachabteilung
```
Mitarbeiter: Max Mustermann  
Stamm-WA: 2. Wachabteilung (NEU)
Hauptsaldo: €0 (wird neues Hauptkonto)
Subkonten: 
- 1. WA: €10 (Frühstück), €5 (Getränke) [MIGRATED]
- 3. WA: €2 (Getränke) [UNVERÄNDERT]
```

## Saldo-Migration Regeln

1. **Hauptsaldo → Subkonto**: Aktueller Hauptsaldo wird zu Subkonto der alten Abteilung
2. **Subkonto → Hauptsaldo**: Falls bereits Subkonto für neue Abteilung existiert, wird es zum neuen Hauptsaldo
3. **Geld-Erhaltung**: Gesamtsaldo bleibt immer konstant (kein Geld verloren/erstellt)
4. **Mehrfache Verschiebungen**: Alle vorherigen Abteilungs-Salden bleiben als Subkonten erhalten

## API Endpoint
```
PUT /api/developer/move-employee/{employee_id}
Body: {"new_department_id": "fw4abteilung2"}
```

## Sicherheitshinweise
- ⚠️ Verschiebungen sind **nicht rückgängig machbar** (außer durch erneute Verschiebung)
- ✅ Alle Saldo-Änderungen werden in der Response dokumentiert
- ✅ Mathematische Konsistenz wird gewährleistet

## Beispiel API Response
```json
{
  "message": "Mitarbeiter erfolgreich von 1. Wachabteilung nach 2. Wachabteilung verschoben",
  "balance_migration": {
    "old_main_balances_moved_to_subaccount": {
      "department": "1. Wachabteilung",
      "breakfast": 10.0,
      "drinks": 5.0
    },
    "new_main_balances_from_subaccount": {
      "department": "2. Wachabteilung",
      "breakfast": 0.0,
      "drinks": 0.0
    }
  }
}
```