#!/usr/bin/env python3
"""
Debug the initialize_default_data function to see what's happening
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def debug_init_data():
    session = requests.Session()
    
    print("🔍 DEBUGGING INITIALIZE_DEFAULT_DATA FUNCTION")
    print("=" * 60)
    
    # Step 1: Get current state
    print("\n1. Current department state:")
    response = session.get(f"{API_BASE}/departments")
    if response.status_code == 200:
        departments = response.json()
        for dept in departments:
            print(f"   {dept['name']}: employee={dept.get('password_hash')}, admin={dept.get('admin_password_hash')}")
    else:
        print(f"❌ Failed to get departments: {response.status_code}")
        return
    
    # Step 2: Find a working department and change its password
    working_dept = None
    for i, dept in enumerate(departments, 1):
        admin_login = {
            "department_name": dept['name'],
            "admin_password": f"admin{i}"
        }
        
        response = session.post(f"{API_BASE}/login/department-admin", json=admin_login)
        if response.status_code == 200:
            working_dept = dept
            break
    
    if not working_dept:
        print("❌ No working department found")
        return
    
    print(f"\n2. Using department: {working_dept['name']}")
    
    # Step 3: Change password
    new_password = "debug_test_password"
    print(f"\n3. Changing admin password to: {new_password}")
    
    response = session.put(
        f"{API_BASE}/department-admin/change-admin-password/{working_dept['id']}", 
        params={"new_password": new_password}
    )
    
    if response.status_code == 200:
        print("✅ Password change successful")
    else:
        print(f"❌ Password change failed: {response.status_code}")
        return
    
    # Step 4: Check state after password change
    print(f"\n4. Department state after password change:")
    response = session.get(f"{API_BASE}/departments")
    if response.status_code == 200:
        departments = response.json()
        for dept in departments:
            if dept['id'] == working_dept['id']:
                print(f"   {dept['name']}: employee={dept.get('password_hash')}, admin={dept.get('admin_password_hash')}")
                break
    
    # Step 5: Call init-data and see what happens
    print(f"\n5. Calling /api/init-data...")
    
    response = session.post(f"{API_BASE}/init-data")
    if response.status_code == 200:
        print(f"✅ Init-data successful: {response.json()}")
    else:
        print(f"❌ Init-data failed: {response.status_code}")
        return
    
    # Step 6: Check state after init-data
    print(f"\n6. Department state after init-data:")
    response = session.get(f"{API_BASE}/departments")
    if response.status_code == 200:
        departments = response.json()
        for dept in departments:
            if dept['id'] == working_dept['id']:
                current_admin_pass = dept.get('admin_password_hash')
                print(f"   {dept['name']}: employee={dept.get('password_hash')}, admin={current_admin_pass}")
                
                if current_admin_pass == new_password:
                    print("✅ PASSWORD PRESERVED - Fix is working!")
                else:
                    print(f"❌ PASSWORD RESET - Fix is NOT working! (was {new_password}, now {current_admin_pass})")
                break
    
    # Step 7: Test authentication
    print(f"\n7. Testing authentication with changed password...")
    
    new_admin_login = {
        "department_name": working_dept['name'],
        "admin_password": new_password
    }
    
    response = session.post(f"{API_BASE}/login/department-admin", json=new_admin_login)
    if response.status_code == 200:
        print("✅ Authentication with changed password successful")
    else:
        print(f"❌ Authentication with changed password failed: {response.status_code}")

if __name__ == "__main__":
    debug_init_data()