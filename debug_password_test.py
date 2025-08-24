#!/usr/bin/env python3
"""
Debug test to investigate the admin password persistence issue
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

def debug_password_issue():
    session = requests.Session()
    
    print("=== DEBUG: Password Persistence Issue ===")
    
    # Get departments
    response = session.get(f"{API_BASE}/departments")
    if response.status_code != 200:
        print(f"Failed to get departments: {response.status_code}")
        return
    
    departments = response.json()
    test_dept = departments[0]
    print(f"Testing with department: {test_dept['name']} (ID: {test_dept['id']})")
    
    # Step 1: Change admin password
    new_admin_password = "debug_admin_pass"
    print(f"\n1. Changing admin password to: {new_admin_password}")
    
    response = session.put(
        f"{API_BASE}/department-admin/change-admin-password/{test_dept['id']}", 
        params={"new_password": new_admin_password}
    )
    
    if response.status_code == 200:
        print("✅ Admin password change successful")
    else:
        print(f"❌ Admin password change failed: {response.status_code} - {response.text}")
        return
    
    # Step 2: Test authentication with new password
    print(f"\n2. Testing authentication with new password: {new_admin_password}")
    
    admin_login = {
        "department_name": test_dept['name'],
        "admin_password": new_admin_password
    }
    
    response = session.post(f"{API_BASE}/login/department-admin", json=admin_login)
    if response.status_code == 200:
        print("✅ Authentication with new password successful")
    else:
        print(f"❌ Authentication with new password failed: {response.status_code} - {response.text}")
        return
    
    # Step 3: Call init-data
    print(f"\n3. Calling /api/init-data")
    
    response = session.post(f"{API_BASE}/init-data")
    if response.status_code == 200:
        print(f"✅ Init-data successful: {response.json()}")
    else:
        print(f"❌ Init-data failed: {response.status_code} - {response.text}")
        return
    
    # Step 4: Test authentication again
    print(f"\n4. Testing authentication after init-data with: {new_admin_password}")
    
    response = session.post(f"{API_BASE}/login/department-admin", json=admin_login)
    if response.status_code == 200:
        print("✅ Authentication after init-data successful - PASSWORD PERSISTED!")
    else:
        print(f"❌ Authentication after init-data failed - PASSWORD WAS RESET! {response.status_code} - {response.text}")
        
        # Try with default password
        print(f"\n5. Testing with default admin password: admin1")
        default_admin_login = {
            "department_name": test_dept['name'],
            "admin_password": "admin1"
        }
        
        response = session.post(f"{API_BASE}/login/department-admin", json=default_admin_login)
        if response.status_code == 200:
            print("❌ CRITICAL: Default password works - passwords were reset by init-data!")
        else:
            print("✅ Default password rejected - something else is wrong")
    
    # Step 5: Check what's in the database by getting departments again
    print(f"\n6. Checking department data after init-data")
    response = session.get(f"{API_BASE}/departments")
    if response.status_code == 200:
        updated_departments = response.json()
        updated_dept = next((d for d in updated_departments if d['id'] == test_dept['id']), None)
        if updated_dept:
            print(f"Department found: {updated_dept['name']}")
            print(f"Admin password hash: {updated_dept.get('admin_password_hash', 'NOT FOUND')}")
        else:
            print("❌ Department not found after init-data!")
    else:
        print(f"❌ Failed to get departments: {response.status_code}")

if __name__ == "__main__":
    debug_password_issue()