#!/usr/bin/env python3
"""
Check departments in database to debug password issue
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

def check_departments():
    session = requests.Session()
    
    print("=== CHECKING DEPARTMENTS IN DATABASE ===")
    
    # Get all departments
    response = session.get(f"{API_BASE}/departments")
    if response.status_code != 200:
        print(f"Failed to get departments: {response.status_code}")
        return
    
    departments = response.json()
    print(f"Found {len(departments)} departments:")
    
    for i, dept in enumerate(departments):
        print(f"\nDepartment {i+1}:")
        print(f"  ID: {dept['id']}")
        print(f"  Name: {dept['name']}")
        print(f"  Employee Password: {dept.get('password_hash', 'NOT FOUND')}")
        print(f"  Admin Password: {dept.get('admin_password_hash', 'NOT FOUND')}")
    
    # Check for duplicates
    names = [dept['name'] for dept in departments]
    duplicates = [name for name in set(names) if names.count(name) > 1]
    
    if duplicates:
        print(f"\n❌ DUPLICATE DEPARTMENT NAMES FOUND: {duplicates}")
        print("This could cause password update issues!")
    else:
        print(f"\n✅ No duplicate department names found")

if __name__ == "__main__":
    check_departments()