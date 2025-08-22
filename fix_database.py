#!/usr/bin/env python3
"""
Fix database issues with roll types and toppings pricing
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

async def fix_database():
    # MongoDB connection
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔧 Fixing database issues...")
    
    # 1. Clear existing breakfast menu items with old roll types
    print("Clearing old breakfast menu items...")
    result = await db.menu_breakfast.delete_many({})
    print(f"Deleted {result.deleted_count} old breakfast items")
    
    # 2. Create new breakfast items with correct roll types
    print("Creating new breakfast items with updated roll types...")
    new_breakfast_items = [
        {"id": "breakfast_weiss", "roll_type": "weiss", "price": 0.50},
        {"id": "breakfast_koerner", "roll_type": "koerner", "price": 0.60}
    ]
    
    for item in new_breakfast_items:
        await db.menu_breakfast.insert_one(item)
    print(f"Created {len(new_breakfast_items)} new breakfast items")
    
    # 3. Update all toppings to be free (price = 0.00)
    print("Updating toppings to be free...")
    result = await db.menu_toppings.update_many({}, {"$set": {"price": 0.0}})
    print(f"Updated {result.modified_count} toppings to be free")
    
    # 4. Verify the changes
    print("\n✅ Verification:")
    
    # Check breakfast items
    breakfast_items = await db.menu_breakfast.find().to_list(100)
    print(f"Breakfast items: {len(breakfast_items)}")
    for item in breakfast_items:
        print(f"  - {item['roll_type']}: €{item['price']:.2f}")
    
    # Check toppings
    toppings = await db.menu_toppings.find().to_list(100)
    print(f"Toppings: {len(toppings)}")
    free_toppings = [t for t in toppings if t['price'] == 0.0]
    print(f"  - Free toppings: {len(free_toppings)}/{len(toppings)}")
    
    client.close()
    print("\n🎉 Database fixes completed!")

if __name__ == "__main__":
    asyncio.run(fix_database())