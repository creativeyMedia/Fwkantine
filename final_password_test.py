#!/usr/bin/env python3
"""
Final Password Persistence Test - Focus on the core issue
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

def final_password_test():
    session = requests.Session()
    
    print("🔐 FINAL PASSWORD PERSISTENCE TEST")
    print("=" * 60)
    print("Testing the CORE issue: Do password changes persist after init-data calls?")
    print("=" * 60)
    
    # Step 1: Initialize data
    print("\n1. Initializing data...")
    response = session.post(f"{API_BASE}/init-data")
    if response.status_code == 200:
        print("✅ Data initialized")
    else:
        print(f"❌ Init failed: {response.status_code}")
        return False
    
    # Step 2: Get departments and find one that works
    response = session.get(f"{API_BASE}/departments")
    if response.status_code != 200:
        print(f"❌ Failed to get departments: {response.status_code}")
        return False
    
    departments = response.json()
    if not departments:
        print("❌ No departments found")
        return False
    
    # Find a department that has working authentication
    working_dept = None
    for i, dept in enumerate(departments, 1):
        admin_login = {
            "department_name": dept['name'],
            "admin_password": f"admin{i}"
        }
        
        response = session.post(f"{API_BASE}/login/department-admin", json=admin_login)
        if response.status_code == 200:
            working_dept = dept
            working_admin_pass = f"admin{i}"
            print(f"✅ Found working department: {dept['name']} with admin password: {working_admin_pass}")
            break
    
    if not working_dept:
        print("❌ No working department found - trying with different passwords")
        # Try some variations
        for dept in departments:
            for test_pass in ["admin1a", "admin2", "admin3", "admin4"]:
                admin_login = {
                    "department_name": dept['name'],
                    "admin_password": test_pass
                }
                
                response = session.post(f"{API_BASE}/login/department-admin", json=admin_login)
                if response.status_code == 200:
                    working_dept = dept
                    working_admin_pass = test_pass
                    print(f"✅ Found working department: {dept['name']} with admin password: {test_pass}")
                    break
            if working_dept:
                break
    
    if not working_dept:
        print("❌ No working department found at all")
        return False
    
    # Step 3: Change the admin password
    print(f"\n2. Changing admin password...")
    
    new_admin_password = "persistence_test_admin_123"
    
    response = session.put(
        f"{API_BASE}/department-admin/change-admin-password/{working_dept['id']}", 
        params={"new_password": new_admin_password}
    )
    
    if response.status_code == 200:
        print(f"✅ Admin password changed to: {new_admin_password}")
    else:
        print(f"❌ Admin password change failed: {response.status_code} - {response.text}")
        return False
    
    # Step 4: Verify the password change worked
    print(f"\n3. Verifying password change...")
    
    new_admin_login = {
        "department_name": working_dept['name'],
        "admin_password": new_admin_password
    }
    
    response = session.post(f"{API_BASE}/login/department-admin", json=new_admin_login)
    if response.status_code == 200:
        print("✅ New admin password authentication successful")
    else:
        print(f"❌ New admin password authentication failed: {response.status_code}")
        return False
    
    # Step 5: Call init-data to test persistence
    print(f"\n4. Calling /api/init-data to test persistence...")
    
    response = session.post(f"{API_BASE}/init-data")
    if response.status_code == 200:
        print(f"✅ Init-data call successful: {response.json()}")
    else:
        print(f"❌ Init-data call failed: {response.status_code}")
        return False
    
    # Step 6: CRITICAL TEST - Check if password still works
    print(f"\n5. CRITICAL TEST: Checking if password persists...")
    
    response = session.post(f"{API_BASE}/login/department-admin", json=new_admin_login)
    if response.status_code == 200:
        print("✅ CRITICAL SUCCESS: Admin password persisted after init-data call!")
        print("✅ THE PASSWORD PERSISTENCE FIX IS WORKING CORRECTLY")
        return True
    else:
        print(f"❌ CRITICAL FAILURE: Admin password was reset after init-data call!")
        print(f"   Response: {response.status_code} - {response.text}")
        
        # Check if old password works again
        old_admin_login = {
            "department_name": working_dept['name'],
            "admin_password": working_admin_pass
        }
        
        response = session.post(f"{API_BASE}/login/department-admin", json=old_admin_login)
        if response.status_code == 200:
            print("❌ CONFIRMED: Password was reset to original value")
            print("❌ THE PASSWORD PERSISTENCE FIX IS NOT WORKING")
        else:
            print("❓ Password was not reset to original - something else is wrong")
        
        return False

if __name__ == "__main__":
    success = final_password_test()
    print("\n" + "=" * 60)
    if success:
        print("🎉 FINAL RESULT: PASSWORD PERSISTENCE FIX IS WORKING!")
    else:
        print("💥 FINAL RESULT: PASSWORD PERSISTENCE ISSUE STILL EXISTS!")
    print("=" * 60)
    exit(0 if success else 1)