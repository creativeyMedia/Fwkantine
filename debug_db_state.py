#!/usr/bin/env python3
"""
Direct MongoDB debugging - track exactly what happens
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

async def debug_complete_scenario():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    print("=" * 60)
    print("🔍 COMPLETE DEBUG SCENARIO")
    print("=" * 60)
    
    # Step 1: Clean slate
    print("\n1. Starting with clean slate...")
    await db.departments.delete_many({})
    count = await db.departments.count_documents({})
    print(f"   Departments after cleanup: {count}")
    
    # Step 2: Create departments manually (simulating first init-data)
    print("\n2. Creating departments manually (like init-data)...")
    
    from pydantic import BaseModel, Field
    import uuid
    
    class Department(BaseModel):
        id: str = Field(default_factory=lambda: str(uuid.uuid4()))
        name: str
        password_hash: str
        admin_password_hash: str
    
    for i in range(1, 5):
        dept = Department(
            name=f"{i}. Wachabteilung",
            password_hash=f"password{i}",
            admin_password_hash=f"admin{i}"
        )
        result = await db.departments.insert_one(dept.dict())
        print(f"   Created: {dept.name} with ID: {result.inserted_id}")
    
    # Step 3: Verify departments
    print("\n3. Verifying created departments...")
    depts = await db.departments.find().to_list(100)
    for dept in depts:
        print(f"   {dept['name']}: emp={dept['password_hash']}, admin={dept['admin_password_hash']}")
    
    # Step 4: Simulate password change
    print(f"\n4. Simulating admin password change for 1st department...")
    test_dept = depts[0]
    NEW_ADMIN_PASSWORD = "changed_admin_password_123"
    
    result = await db.departments.update_one(
        {"id": test_dept["id"]},
        {"$set": {"admin_password_hash": NEW_ADMIN_PASSWORD}}
    )
    print(f"   Password change result: matched={result.matched_count}, modified={result.modified_count}")
    
    # Step 5: Verify password change
    print(f"\n5. Verifying password change...")
    updated_dept = await db.departments.find_one({"id": test_dept["id"]})
    print(f"   Updated dept admin password: {updated_dept['admin_password_hash']}")
    
    # Step 6: Simulate what init-data does
    print(f"\n6. Simulating init-data logic...")
    
    for i in range(1, 5):
        dept_name = f"{i}. Wachabteilung"
        existing_dept = await db.departments.find_one({"name": dept_name})
        
        if existing_dept:
            print(f"   Found existing dept: {dept_name} - should preserve passwords")
            print(f"      Current admin password: {existing_dept['admin_password_hash']}")
        else:
            print(f"   No existing dept found for: {dept_name} - would create new")
    
    # Step 7: Final verification
    print(f"\n7. Final verification...")
    final_depts = await db.departments.find().to_list(100)
    for dept in final_depts:
        print(f"   FINAL: {dept['name']} - admin_pass: {dept['admin_password_hash']}")

asyncio.run(debug_complete_scenario())
