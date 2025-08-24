#!/usr/bin/env python3
"""
Comprehensive Password Persistence Test - Clean State
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

def comprehensive_password_test():
    session = requests.Session()
    
    print("🔐 COMPREHENSIVE PASSWORD PERSISTENCE TEST")
    print("=" * 60)
    
    # Step 1: Clean up and initialize
    print("\n1. Cleaning up and initializing departments...")
    response = session.post(f"{API_BASE}/cleanup-departments-final")
    if response.status_code == 200:
        print("✅ Departments cleaned up")
    else:
        print(f"❌ Cleanup failed: {response.status_code}")
    
    response = session.post(f"{API_BASE}/init-data")
    if response.status_code == 200:
        print("✅ Data initialized")
    else:
        print(f"❌ Init failed: {response.status_code}")
        return False
    
    # Step 2: Get departments
    response = session.get(f"{API_BASE}/departments")
    if response.status_code != 200:
        print(f"❌ Failed to get departments: {response.status_code}")
        return False
    
    departments = response.json()
    if not departments:
        print("❌ No departments found")
        return False
    
    test_dept = departments[0]
    print(f"✅ Testing with: {test_dept['name']} (ID: {test_dept['id']})")
    
    # Step 3: Test initial authentication
    print(f"\n2. Testing initial authentication...")
    
    # Test employee login
    employee_login = {
        "department_name": test_dept['name'],
        "password": "password1"
    }
    
    response = session.post(f"{API_BASE}/login/department", json=employee_login)
    if response.status_code == 200:
        print("✅ Initial employee authentication successful")
    else:
        print(f"❌ Initial employee authentication failed: {response.status_code}")
    
    # Test admin login
    admin_login = {
        "department_name": test_dept['name'],
        "admin_password": "admin1"
    }
    
    response = session.post(f"{API_BASE}/login/department-admin", json=admin_login)
    if response.status_code == 200:
        print("✅ Initial admin authentication successful")
    else:
        print(f"❌ Initial admin authentication failed: {response.status_code}")
        return False
    
    # Step 4: Change passwords
    print(f"\n3. Changing passwords...")
    
    new_employee_password = "test_emp_pass_123"
    new_admin_password = "test_admin_pass_123"
    
    # Change employee password
    response = session.put(
        f"{API_BASE}/department-admin/change-employee-password/{test_dept['id']}", 
        params={"new_password": new_employee_password}
    )
    
    if response.status_code == 200:
        print(f"✅ Employee password changed to: {new_employee_password}")
    else:
        print(f"❌ Employee password change failed: {response.status_code}")
        return False
    
    # Change admin password
    response = session.put(
        f"{API_BASE}/department-admin/change-admin-password/{test_dept['id']}", 
        params={"new_password": new_admin_password}
    )
    
    if response.status_code == 200:
        print(f"✅ Admin password changed to: {new_admin_password}")
    else:
        print(f"❌ Admin password change failed: {response.status_code}")
        return False
    
    # Step 5: Test authentication with new passwords
    print(f"\n4. Testing authentication with new passwords...")
    
    # Test new employee password
    new_employee_login = {
        "department_name": test_dept['name'],
        "password": new_employee_password
    }
    
    response = session.post(f"{API_BASE}/login/department", json=new_employee_login)
    if response.status_code == 200:
        print("✅ New employee password authentication successful")
    else:
        print(f"❌ New employee password authentication failed: {response.status_code}")
        return False
    
    # Test new admin password
    new_admin_login = {
        "department_name": test_dept['name'],
        "admin_password": new_admin_password
    }
    
    response = session.post(f"{API_BASE}/login/department-admin", json=new_admin_login)
    if response.status_code == 200:
        print("✅ New admin password authentication successful")
    else:
        print(f"❌ New admin password authentication failed: {response.status_code}")
        return False
    
    # Step 6: Call init-data multiple times
    print(f"\n5. Calling /api/init-data multiple times to test persistence...")
    
    for i in range(3):
        response = session.post(f"{API_BASE}/init-data")
        if response.status_code == 200:
            print(f"✅ Init-data call {i+1} successful")
        else:
            print(f"❌ Init-data call {i+1} failed: {response.status_code}")
    
    # Step 7: CRITICAL TEST - Check if passwords still work
    print(f"\n6. CRITICAL TEST: Checking if passwords persist after init-data calls...")
    
    # Test employee password persistence
    response = session.post(f"{API_BASE}/login/department", json=new_employee_login)
    if response.status_code == 200:
        print("✅ CRITICAL SUCCESS: Employee password persisted after init-data calls")
        employee_persistent = True
    else:
        print(f"❌ CRITICAL FAILURE: Employee password was reset! {response.status_code}")
        employee_persistent = False
    
    # Test admin password persistence
    response = session.post(f"{API_BASE}/login/department-admin", json=new_admin_login)
    if response.status_code == 200:
        print("✅ CRITICAL SUCCESS: Admin password persisted after init-data calls")
        admin_persistent = True
    else:
        print(f"❌ CRITICAL FAILURE: Admin password was reset! {response.status_code}")
        admin_persistent = False
    
    # Step 8: Test that old passwords are rejected
    print(f"\n7. Testing that old passwords are rejected...")
    
    # Test old employee password
    response = session.post(f"{API_BASE}/login/department", json=employee_login)
    if response.status_code == 401:
        print("✅ Old employee password correctly rejected")
        old_employee_rejected = True
    else:
        print(f"❌ Old employee password still works! {response.status_code}")
        old_employee_rejected = False
    
    # Test old admin password
    response = session.post(f"{API_BASE}/login/department-admin", json=admin_login)
    if response.status_code == 401:
        print("✅ Old admin password correctly rejected")
        old_admin_rejected = True
    else:
        print(f"❌ Old admin password still works! {response.status_code}")
        old_admin_rejected = False
    
    # Final assessment
    print(f"\n" + "=" * 60)
    print("🔐 FINAL ASSESSMENT")
    print("=" * 60)
    
    if employee_persistent and admin_persistent and old_employee_rejected and old_admin_rejected:
        print("✅ OVERALL RESULT: PASSWORD PERSISTENCE FIX IS WORKING CORRECTLY")
        print("✅ User-changed passwords are preserved after init-data calls")
        print("✅ Old passwords are properly rejected")
        return True
    else:
        print("❌ OVERALL RESULT: PASSWORD PERSISTENCE ISSUE STILL EXISTS")
        if not employee_persistent:
            print("❌ Employee passwords are being reset")
        if not admin_persistent:
            print("❌ Admin passwords are being reset")
        if not old_employee_rejected:
            print("❌ Old employee passwords still work")
        if not old_admin_rejected:
            print("❌ Old admin passwords still work")
        return False

if __name__ == "__main__":
    success = comprehensive_password_test()
    exit(0 if success else 1)