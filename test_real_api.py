#!/usr/bin/env python3
"""
Test the real API endpoint vs direct database access
"""

import requests
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv('backend/.env')
mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

BACKEND_URL = 'http://localhost:8001'
API_BASE = f"{BACKEND_URL}/api"

async def check_db_state(step_name):
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    depts = await db.departments.find().to_list(100)
    print(f"\n📊 DB STATE - {step_name}:")
    print(f"   Count: {len(depts)}")
    for dept in depts:
        print(f"   {dept['name']}: admin={dept.get('admin_password_hash', 'MISSING')}")

async def test_real_api_behavior():
    session = requests.Session()
    
    print("🔬 TESTING REAL API vs DATABASE")
    print("=" * 60)
    
    # Step 1: Start clean
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    await db.departments.delete_many({})
    
    await check_db_state("After cleanup")
    
    # Step 2: Call real API init-data
    print(f"\n🔥 Calling REAL /api/init-data endpoint...")
    response = session.post(f"{API_BASE}/init-data")
    print(f"   Response: {response.status_code} - {response.text}")
    
    await check_db_state("After /api/init-data")
    
    # Step 3: Get departments via API
    response = session.get(f"{API_BASE}/departments")
    if response.status_code == 200:
        api_depts = response.json()
        print(f"\n📡 API departments response:")
        for dept in api_depts:
            print(f"   {dept['name']}: admin={dept.get('admin_password_hash', 'MISSING')}")
    else:
        print(f"\n❌ Failed to get departments via API: {response.status_code}")
        return
    
    # Step 4: Change password via API  
    if api_depts:
        test_dept = api_depts[0]
        print(f"\n🔧 Changing admin password for: {test_dept['name']}")
        
        response = session.put(
            f"{API_BASE}/department-admin/change-admin-password/{test_dept['id']}", 
            params={"new_password": "api_changed_password"}
        )
        print(f"   Password change response: {response.status_code}")
        
        await check_db_state("After password change")
        
        # Step 5: Call init-data again
        print(f"\n🔥 Calling /api/init-data AGAIN...")
        response = session.post(f"{API_BASE}/init-data")
        print(f"   Response: {response.status_code} - {response.text}")
        
        await check_db_state("After second /api/init-data")
        
        # Step 6: Test login with changed password
        print(f"\n🔐 Testing login with changed password...")
        login_data = {
            "department_name": test_dept['name'],
            "admin_password": "api_changed_password"
        }
        response = session.post(f"{API_BASE}/login/department-admin", json=login_data)
        print(f"   Login result: {response.status_code} {'✅ SUCCESS' if response.status_code == 200 else '❌ FAILED'}")
        
        if response.status_code != 200:
            print(f"   Trying default password...")
            login_data["admin_password"] = "admin1"
            response = session.post(f"{API_BASE}/login/department-admin", json=login_data)
            print(f"   Default password result: {response.status_code} {'✅ WORKS' if response.status_code == 200 else '❌ FAILED'}")

asyncio.run(test_real_api_behavior())
