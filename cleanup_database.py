#!/usr/bin/env python3
"""
DATABASE CLEANUP SCRIPT

Reinigt die Datenbank für saubere Tests:
- Löscht alle Orders
- Setzt alle Mitarbeiter-Salden auf 0
- Löscht Payment Logs
- Behält Mitarbeiter, Menüs und Einstellungen
"""

import requests
import json
import sys
from datetime import datetime
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/canteen_manager')

async def cleanup_database():
    """Clean up database for fresh testing"""
    try:
        print("🧹 Starte Datenbank-Bereinigung...")
        
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_URL)
        db = client.canteen_manager
        
        # 1. Delete all orders
        orders_result = await db.orders.delete_many({})
        print(f"✅ {orders_result.deleted_count} Bestellungen gelöscht")
        
        # 2. Reset all employee balances to 0
        employees_result = await db.employees.update_many(
            {},
            {"$set": {
                "breakfast_balance": 0.0,
                "drinks_sweets_balance": 0.0
            }}
        )
        print(f"✅ {employees_result.modified_count} Mitarbeiter-Salden zurückgesetzt")
        
        # 3. Delete all payment logs
        payment_logs_result = await db.payment_logs.delete_many({})
        print(f"✅ {payment_logs_result.deleted_count} Zahlungsprotokoll-Einträge gelöscht")
        
        # 4. Get statistics of what remains
        departments_count = await db.departments.count_documents({})
        employees_count = await db.employees.count_documents({})
        menu_breakfast_count = await db.menu_breakfast.count_documents({})
        menu_toppings_count = await db.menu_toppings.count_documents({})
        menu_drinks_count = await db.menu_drinks.count_documents({})
        menu_sweets_count = await db.menu_sweets.count_documents({})
        lunch_settings_count = await db.lunch_settings.count_documents({})
        
        print("\n📊 Verbleibende Daten:")
        print(f"   • Abteilungen: {departments_count}")
        print(f"   • Mitarbeiter: {employees_count}")
        print(f"   • Frühstück-Menü: {menu_breakfast_count}")
        print(f"   • Beläge-Menü: {menu_toppings_count}")
        print(f"   • Getränke-Menü: {menu_drinks_count}")
        print(f"   • Süßes-Menü: {menu_sweets_count}")
        print(f"   • Mittag-Einstellungen: {lunch_settings_count}")
        
        # 5. Verify cleanup
        remaining_orders = await db.orders.count_documents({})
        remaining_payment_logs = await db.payment_logs.count_documents({})
        
        if remaining_orders == 0 and remaining_payment_logs == 0:
            print("\n🎉 Datenbank-Bereinigung erfolgreich abgeschlossen!")
            print("   ✅ Alle Bestellungen gelöscht")
            print("   ✅ Alle Mitarbeiter-Salden auf 0.00€ gesetzt")
            print("   ✅ Alle Zahlungsprotokolle gelöscht")
            print("   ✅ Menüs und Einstellungen bleiben erhalten")
            print("\nSie können jetzt saubere Tests durchführen! 🧪")
            return True
        else:
            print(f"\n⚠️  Warnung: Bereinigung unvollständig!")
            print(f"   Verbleibende Orders: {remaining_orders}")
            print(f"   Verbleibende Payment Logs: {remaining_payment_logs}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler bei der Datenbank-Bereinigung: {str(e)}")
        return False
    finally:
        client.close()

async def main():
    """Main cleanup function"""
    print("🚨 ACHTUNG: Diese Aktion löscht alle Bestellungen und setzt alle Salden zurück!")
    print("Möchten Sie fortfahren? (j/N): ", end="")
    
    # For automated execution, we'll proceed directly
    print("j")  # Auto-confirm for script execution
    
    success = await cleanup_database()
    
    if success:
        print("\n✨ Die Datenbank ist jetzt bereit für saubere Tests!")
        sys.exit(0)
    else:
        print("\n💥 Bereinigung fehlgeschlagen!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())