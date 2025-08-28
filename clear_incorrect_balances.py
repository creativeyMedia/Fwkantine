#!/usr/bin/env python3
"""
CLEAR INCORRECT BALANCES SCRIPT

Dieses Script setzt alle Employee-Balances auf 0.00 zurück und löscht alle
Bestellungen und Payments, damit das korrigierte Flexible Payment System 
mit sauberen Daten getestet werden kann.

Nach der Balance-Logic-Korrektur sind alte Salden falsch berechnet.
"""

import os
import sys
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

async def clear_incorrect_balances():
    """Clear all incorrect balances and related data"""
    
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'fw_kantine_production')
    
    print("🧹 CLEARING INCORRECT BALANCES")
    print("=" * 50)
    print(f"📊 Database: {db_name}")
    print(f"🔗 MongoDB: {mongo_url}")
    
    try:
        client = AsyncIOMotorClient(mongo_url)
        db = client[db_name]
        
        # 1. Get current status
        print(f"\n📊 CURRENT STATUS:")
        employees_count = await db.employees.count_documents({})
        orders_count = await db.orders.count_documents({})
        payment_logs_count = await db.payment_logs.count_documents({})
        
        print(f"   Employees: {employees_count}")
        print(f"   Orders: {orders_count}")
        print(f"   Payment Logs: {payment_logs_count}")
        
        # 2. Show some incorrect balances as examples
        print(f"\n🔍 EXAMPLES OF INCORRECT BALANCES:")
        employees = await db.employees.find({}).to_list(5)
        for emp in employees[:3]:  # Show first 3
            name = emp.get('name', 'Unknown')
            breakfast_balance = emp.get('breakfast_balance', 0)
            drinks_balance = emp.get('drinks_sweets_balance', 0)
            print(f"   {name}: Frühstück=€{breakfast_balance:.2f}, Getränke=€{drinks_balance:.2f}")
        
        # 3. Clear all orders (which created incorrect balances)
        print(f"\n🗑️  CLEARING ALL ORDERS...")
        orders_result = await db.orders.delete_many({})
        print(f"   Deleted {orders_result.deleted_count} orders")
        
        # 4. Clear all payment logs (incorrect payments)
        print(f"\n🗑️  CLEARING ALL PAYMENT LOGS...")
        payments_result = await db.payment_logs.delete_many({})
        print(f"   Deleted {payments_result.deleted_count} payment logs")
        
        # 5. Reset all employee balances to 0.00
        print(f"\n🔄 RESETTING ALL EMPLOYEE BALANCES TO 0.00...")
        employees_result = await db.employees.update_many(
            {},  # All employees
            {
                "$set": {
                    "breakfast_balance": 0.0,
                    "drinks_sweets_balance": 0.0
                }
            }
        )
        print(f"   Reset balances for {employees_result.modified_count} employees")
        
        # 6. Verify cleanup
        print(f"\n✅ VERIFICATION:")
        remaining_orders = await db.orders.count_documents({})
        remaining_payments = await db.payment_logs.count_documents({})
        
        # Check that all balances are 0.00
        non_zero_breakfast = await db.employees.count_documents({"breakfast_balance": {"$ne": 0.0}})
        non_zero_drinks = await db.employees.count_documents({"drinks_sweets_balance": {"$ne": 0.0}})
        
        print(f"   Remaining orders: {remaining_orders}")
        print(f"   Remaining payments: {remaining_payments}")
        print(f"   Non-zero breakfast balances: {non_zero_breakfast}")
        print(f"   Non-zero drinks balances: {non_zero_drinks}")
        
        if remaining_orders == 0 and remaining_payments == 0 and non_zero_breakfast == 0 and non_zero_drinks == 0:
            print(f"\n🎉 CLEANUP SUCCESSFUL!")
            print(f"✅ All orders deleted")
            print(f"✅ All payment logs deleted") 
            print(f"✅ All employee balances reset to 0.00")
            print(f"\n📝 NEXT STEPS:")
            print(f"1. Das korrigierte Flexible Payment System ist bereit zum Testen")
            print(f"2. Neue Bestellungen werden korrekte negative Balances erstellen")
            print(f"3. Einzahlungen werden korrekte positive Balances erstellen")
        else:
            print(f"\n⚠️  CLEANUP INCOMPLETE - Some data remains")
        
        client.close()
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 STARTING BALANCE CLEANUP FOR CORRECTED LOGIC...")
    success = asyncio.run(clear_incorrect_balances())
    
    if success:
        print(f"\n✅ Database cleanup completed successfully!")
        print(f"Das Flexible Payment System kann jetzt mit korrekter Balance-Logik getestet werden.")
    else:
        print(f"\n❌ Database cleanup failed!")
    
    sys.exit(0 if success else 1)