#!/usr/bin/env python3
"""
Fix lunch settings ObjectId issue
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid

# Load environment variables
ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

async def fix_lunch_settings():
    # MongoDB connection
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    print("🔧 Fixing lunch settings...")
    
    # Clear existing lunch settings
    result = await db.lunch_settings.delete_many({})
    print(f"Deleted {result.deleted_count} old lunch settings")
    
    # Create new lunch settings with proper UUID
    new_lunch_settings = {
        "id": str(uuid.uuid4()),
        "price": 0.0,
        "enabled": True
    }
    
    await db.lunch_settings.insert_one(new_lunch_settings)
    print("Created new lunch settings")
    
    # Verify
    settings = await db.lunch_settings.find_one()
    print(f"Lunch settings: price=€{settings['price']:.2f}, enabled={settings['enabled']}")
    
    client.close()
    print("🎉 Lunch settings fixed!")

if __name__ == "__main__":
    asyncio.run(fix_lunch_settings())