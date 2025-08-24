#!/usr/bin/env python3
"""
Test the EXACT user scenario: 
1. User changes admin password
2. User visits homepage (triggers init-data)  
3. Password should NOT revert
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('frontend/.env')

BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def test_user_scenario():
    session = requests.Session()
    
    print("🔥 TESTING USER SCENARIO: Password Persistence")
    print("=" * 60)
    
    # Step 1: Initialize (like first app start)
    print("1. Initialize data (like first app start)...")
    response = session.post(f"{API_BASE}/init-data")
    print(f"   Init response: {response.status_code}")
    
    # Get departments
    response = session.get(f"{API_BASE}/departments")
    departments = response.json()
    test_dept = departments[0]
    print(f"   Testing dept: {test_dept['name']}")
    
    # Step 2: Login as admin with default password
    print(f"\n2. Login as admin with DEFAULT password...")
    admin_login = {
        "department_name": test_dept['name'],
        "admin_password": "admin1"  # Default password
    }
    response = session.post(f"{API_BASE}/login/department-admin", json=admin_login)
    print(f"   Default login result: {response.status_code}")
    
    # Step 3: Change admin password
    print(f"\n3. Change admin password...")
    NEW_PASSWORD = "my_custom_admin_password_123"
    response = session.put(
        f"{API_BASE}/department-admin/change-admin-password/{test_dept['id']}", 
        params={"new_password": NEW_PASSWORD}
    )
    print(f"   Password change result: {response.status_code}")
    
    # Step 4: Verify new password works
    print(f"\n4. Test login with NEW password...")
    new_admin_login = {
        "department_name": test_dept['name'],
        "admin_password": NEW_PASSWORD
    }
    response = session.post(f"{API_BASE}/login/department-admin", json=new_admin_login)
    print(f"   New password login: {response.status_code} {'✅ WORKS' if response.status_code == 200 else '❌ FAILED'}")
    
    # Step 5: CRITICAL - Simulate homepage visit (triggers init-data)
    print(f"\n5. 🚨 CRITICAL - Simulate homepage visit (triggers init-data)...")
    response = session.post(f"{API_BASE}/init-data")
    print(f"   Homepage init-data call: {response.status_code}")
    
    # Step 6: Test if password still works after init-data
    print(f"\n6. 🎯 TEST - Does the new password STILL work?...")
    response = session.post(f"{API_BASE}/login/department-admin", json=new_admin_login)
    if response.status_code == 200:
        print(f"   ✅ SUCCESS! Password persisted after init-data call!")
        return True
    else:
        print(f"   ❌ FAILURE! Password was reset by init-data call!")
        
        # Test if default password works again
        print(f"   Testing if default password works again...")
        response = session.post(f"{API_BASE}/login/department-admin", json=admin_login)
        if response.status_code == 200:
            print(f"   ❌ CONFIRMED: Password was reset to default!")
        else:
            print(f"   ❓ Neither new nor old password works!")
        
        return False

if __name__ == "__main__":
    test_user_scenario()
