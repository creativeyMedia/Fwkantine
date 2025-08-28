#!/usr/bin/env python3
"""
DATENBANK-MIGRATIONS-SCRIPT für Stornierungsfelder & Masterpasswort

Dieses Script aktualisiert eine bestehende Datenbank mit den neuen Feldern
ohne Datenverlust für Production-Umgebungen.
"""

import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

async def migrate_database():
    """Migriere bestehende Datenbank zu neuer Struktur"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'fw_kantine_production')
    
    print(f"🔄 Connecting to MongoDB: {mongo_url}")
    print(f"🔄 Database: {db_name}")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # 1. Check current database status
        print("\n📊 CURRENT DATABASE STATUS:")
        collections_status = {}
        for collection_name in ['departments', 'employees', 'orders', 'lunch_settings']:
            count = await db[collection_name].count_documents({})
            collections_status[collection_name] = count
            print(f"   {collection_name}: {count} documents")
        
        # 2. Check orders without cancellation fields
        orders_missing_cancelled = await db.orders.count_documents({"is_cancelled": {"$exists": False}})
        print(f"\n🔍 Orders missing 'is_cancelled' field: {orders_missing_cancelled}")
        
        if orders_missing_cancelled == 0:
            print("✅ All orders already have cancellation fields - no migration needed!")
            return
        
        # 3. Add cancellation fields to existing orders
        print(f"\n🔄 Adding 'is_cancelled: false' to {orders_missing_cancelled} orders...")
        
        result = await db.orders.update_many(
            {"is_cancelled": {"$exists": False}},
            {"$set": {"is_cancelled": False}}
        )
        
        print(f"✅ Updated {result.modified_count} orders with cancellation field")
        
        # 4. Verify migration
        orders_still_missing = await db.orders.count_documents({"is_cancelled": {"$exists": False}})
        if orders_still_missing == 0:
            print("✅ Migration successful - all orders now have 'is_cancelled' field")
        else:
            print(f"❌ Migration incomplete - {orders_still_missing} orders still missing field")
            return
        
        # 5. Check environment variables
        print("\n🔧 ENVIRONMENT VARIABLES CHECK:")
        master_password = os.environ.get('MASTER_PASSWORD')
        if master_password:
            print(f"✅ MASTER_PASSWORD is set: {master_password}")
        else:
            print("❌ MASTER_PASSWORD not found in .env file!")
            print("   Add this line to /app/backend/.env:")
            print("   MASTER_PASSWORD=\"master123dev\"")
        
        # 6. Check department passwords
        for i in range(1, 5):
            dept_pass = os.environ.get(f'DEPT_{i}_PASSWORD')
            admin_pass = os.environ.get(f'DEPT_{i}_ADMIN_PASSWORD')
            print(f"   DEPT_{i}_PASSWORD: {'✅' if dept_pass else '❌'}")
            print(f"   DEPT_{i}_ADMIN_PASSWORD: {'✅' if admin_pass else '❌'}")
        
        print("\n🎉 MIGRATION COMPLETED SUCCESSFULLY!")
        print("\nNext steps:")
        print("1. Restart backend: sudo supervisorctl restart backend")
        print("2. Test master password login with 'master123dev'")
        print("3. Test order cancellation functionality")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        return False
    finally:
        client.close()
    
    return True

async def verify_migration():
    """Verify that migration was successful"""
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'fw_kantine_production')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        # Check that all orders have is_cancelled field
        total_orders = await db.orders.count_documents({})
        orders_with_field = await db.orders.count_documents({"is_cancelled": {"$exists": True}})
        
        print(f"\n✅ VERIFICATION RESULTS:")
        print(f"   Total orders: {total_orders}")
        print(f"   Orders with 'is_cancelled' field: {orders_with_field}")
        print(f"   Migration success: {'✅' if total_orders == orders_with_field else '❌'}")
        
        # Show example of migrated order
        sample_order = await db.orders.find_one({"is_cancelled": False})
        if sample_order:
            print(f"   Sample migrated order ID: {sample_order.get('id', 'unknown')}")
            print(f"   Has 'is_cancelled' field: {'✅' if 'is_cancelled' in sample_order else '❌'}")
    
    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--verify":
        print("🔍 VERIFYING MIGRATION...")
        asyncio.run(verify_migration())
    else:
        print("🚀 STARTING DATABASE MIGRATION...")
        success = asyncio.run(migrate_database())
        if success:
            print("\n🔍 Running verification...")
            asyncio.run(verify_migration())