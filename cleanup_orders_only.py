#!/usr/bin/env python3
"""
ORDERS & BALANCES CLEANUP SCRIPT

Löscht nur Orders und setzt Balances zurück, behält alles andere.
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os

# Database connection
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/canteen_manager')

async def cleanup_orders_and_balances():
    """Clean up only orders and balances"""
    try:
        print("🧹 Starte Bereinigung von Bestellungen und Salden...")
        
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
        
        # 4. Get current statistics
        departments_count = await db.departments.count_documents({})
        employees_count = await db.employees.count_documents({})
        remaining_orders = await db.orders.count_documents({})
        
        print(f"\n📊 Status nach Bereinigung:")
        print(f"   • Abteilungen: {departments_count}")
        print(f"   • Mitarbeiter: {employees_count}")
        print(f"   • Verbleibende Bestellungen: {remaining_orders}")
        
        # 5. Show employee balances to verify
        employees = await db.employees.find({}).to_list(length=None)
        print(f"\n👥 Mitarbeiter-Salden:")
        for emp in employees[:5]:  # Show first 5
            print(f"   • {emp.get('name', 'Unknown')}: Frühstück {emp.get('breakfast_balance', 0):.2f}€, Getränke {emp.get('drinks_sweets_balance', 0):.2f}€")
        if len(employees) > 5:
            print(f"   ... und {len(employees) - 5} weitere")
        
        print("\n🎉 Bereinigung abgeschlossen! Ready für saubere Tests!")
        return True
            
    except Exception as e:
        print(f"❌ Fehler bei der Bereinigung: {str(e)}")
        return False
    finally:
        client.close()

async def main():
    success = await cleanup_orders_and_balances()
    return success

if __name__ == "__main__":
    asyncio.run(main())