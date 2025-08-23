#!/usr/bin/env python3
"""
Focused test for specific bug fix areas
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

def test_department_admin_auth():
    """Test department admin authentication with admin1, admin2, etc."""
    print("\n=== Testing Department Admin Authentication ===")
    
    session = requests.Session()
    
    # Initialize data first
    session.post(f"{API_BASE}/init-data")
    
    # Get departments
    response = session.get(f"{API_BASE}/departments")
    if response.status_code != 200:
        print("❌ Failed to get departments")
        return False
        
    departments = response.json()
    
    # Test admin authentication for each department
    admin_passwords = ["admin1", "admin2", "admin3", "admin4"]
    success_count = 0
    
    for i, dept in enumerate(departments[:4]):
        admin_password = admin_passwords[i]
        
        try:
            login_data = {
                "department_name": dept['name'],
                "admin_password": admin_password
            }
            
            response = session.post(f"{API_BASE}/login/department-admin", json=login_data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('role') == 'department_admin':
                    print(f"✅ {dept['name']} admin login with {admin_password}: SUCCESS")
                    success_count += 1
                else:
                    print(f"❌ {dept['name']} admin login: Wrong role")
            else:
                print(f"❌ {dept['name']} admin login: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {dept['name']} admin login: Exception {str(e)}")
    
    return success_count == len(departments)

def test_payment_processing():
    """Test payment processing endpoint"""
    print("\n=== Testing Payment Processing ===")
    
    session = requests.Session()
    
    # Initialize data
    session.post(f"{API_BASE}/init-data")
    
    # Get departments and create employee
    response = session.get(f"{API_BASE}/departments")
    departments = response.json()
    dept = departments[0]
    
    # Create employee
    employee_data = {"name": "Payment Test Employee", "department_id": dept['id']}
    response = session.post(f"{API_BASE}/employees", json=employee_data)
    employee = response.json()
    
    # Create an order to generate balance
    order_data = {
        "employee_id": employee['id'],
        "department_id": dept['id'],
        "order_type": "breakfast",
        "breakfast_items": [
            {
                "total_halves": 2,
                "white_halves": 2,
                "seeded_halves": 0,
                "toppings": ["ruehrei", "kaese"],
                "has_lunch": False
            }
        ]
    }
    
    response = session.post(f"{API_BASE}/orders", json=order_data)
    if response.status_code == 200:
        order = response.json()
        print(f"✅ Created order with balance: €{order['total_price']:.2f}")
        
        # Test payment processing
        payment_data = {
            "payment_type": "breakfast",
            "amount": order['total_price'],
            "admin_department": dept['name']
        }
        
        response = session.post(f"{API_BASE}/department-admin/payment/{employee['id']}", 
                               params=payment_data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Payment processed: {result.get('message', 'Success')}")
            
            # Check payment logs
            response = session.get(f"{API_BASE}/department-admin/payment-logs/{employee['id']}")
            if response.status_code == 200:
                logs = response.json()
                print(f"✅ Payment logs retrieved: {len(logs)} entries")
                return True
            else:
                print(f"❌ Payment logs failed: HTTP {response.status_code}")
        else:
            print(f"❌ Payment processing failed: HTTP {response.status_code}")
    else:
        print(f"❌ Order creation failed: HTTP {response.status_code}")
    
    return False

def test_employee_profile_issue():
    """Test the employee profile issue specifically"""
    print("\n=== Testing Employee Profile Issue ===")
    
    session = requests.Session()
    
    # Initialize data
    session.post(f"{API_BASE}/init-data")
    
    # Get departments and create employee
    response = session.get(f"{API_BASE}/departments")
    departments = response.json()
    dept = departments[0]
    
    # Create employee
    employee_data = {"name": "Profile Test Employee", "department_id": dept['id']}
    response = session.post(f"{API_BASE}/employees", json=employee_data)
    employee = response.json()
    
    # Create an order with new format
    order_data = {
        "employee_id": employee['id'],
        "department_id": dept['id'],
        "order_type": "breakfast",
        "breakfast_items": [
            {
                "total_halves": 2,
                "white_halves": 1,
                "seeded_halves": 1,
                "toppings": ["ruehrei", "kaese"],
                "has_lunch": True
            }
        ]
    }
    
    response = session.post(f"{API_BASE}/orders", json=order_data)
    if response.status_code == 200:
        print("✅ Created order with new format")
        
        # Test profile endpoint
        response = session.get(f"{API_BASE}/employees/{employee['id']}/profile")
        if response.status_code == 200:
            profile = response.json()
            print("✅ Employee profile retrieved successfully")
            print(f"   Orders in history: {len(profile.get('order_history', []))}")
            return True
        else:
            print(f"❌ Employee profile failed: HTTP {response.status_code}")
            if response.status_code == 500:
                print("   This is the KeyError: 'roll_type' issue we identified")
    else:
        print(f"❌ Order creation failed: HTTP {response.status_code}")
    
    return False

if __name__ == "__main__":
    print("🧪 Running Focused Bug Fix Tests")
    print("=" * 50)
    
    results = []
    results.append(("Department Admin Auth", test_department_admin_auth()))
    results.append(("Payment Processing", test_payment_processing()))
    results.append(("Employee Profile Issue", test_employee_profile_issue()))
    
    print("\n" + "=" * 50)
    print("📊 FOCUSED TEST RESULTS")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\nOverall: {passed}/{total} tests passed")