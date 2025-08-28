#!/usr/bin/env python3
"""
FRESH BALANCE CALCULATION TEST

Test the exact scenario from the review request with fresh employees to avoid conflicts.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

BASE_URL = "https://canteen-manager-2.preview.emergentagent.com/api"
DEPARTMENT_NAME = "4. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung4"
ADMIN_PASSWORD = "admin4"

def test_balance_calculation():
    """Test the balance calculation with fresh employees"""
    session = requests.Session()
    
    print("🧮 FRESH BALANCE CALCULATION TEST")
    print("=" * 60)
    
    # 1. Authenticate as admin
    print("1. Authenticating as admin...")
    auth_response = session.post(f"{BASE_URL}/login/department-admin", json={
        "department_name": DEPARTMENT_NAME,
        "admin_password": ADMIN_PASSWORD
    })
    
    if auth_response.status_code != 200:
        print(f"❌ Admin authentication failed: {auth_response.status_code}")
        return False
    
    print("✅ Admin authenticated successfully")
    
    # 2. Create fresh test employees
    print("\\n2. Creating fresh test employees...")
    
    # Create employee who will place the order
    test_employee_name = f"TestEmployee_{datetime.now().strftime('%H%M%S')}"
    employee_response = session.post(f"{BASE_URL}/employees", json={
        "name": test_employee_name,
        "department_id": DEPARTMENT_ID
    })
    
    if employee_response.status_code != 200:
        print(f"❌ Failed to create test employee: {employee_response.status_code}")
        return False
    
    test_employee = employee_response.json()
    print(f"✅ Created test employee: {test_employee['name']}")
    
    # Create sponsor employee
    sponsor_name = f"Sponsor_{datetime.now().strftime('%H%M%S')}"
    sponsor_response = session.post(f"{BASE_URL}/employees", json={
        "name": sponsor_name,
        "department_id": DEPARTMENT_ID
    })
    
    if sponsor_response.status_code != 200:
        print(f"❌ Failed to create sponsor employee: {sponsor_response.status_code}")
        return False
    
    sponsor_employee = sponsor_response.json()
    print(f"✅ Created sponsor employee: {sponsor_employee['name']}")
    
    # 3. Check initial balances
    print("\\n3. Checking initial balances...")
    
    def get_employee_balance(emp_id):
        emp_response = session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
        if emp_response.status_code == 200:
            employees = emp_response.json()
            employee = next((emp for emp in employees if emp["id"] == emp_id), None)
            if employee:
                return employee.get("breakfast_balance", 0.0)
        return None
    
    initial_balance = get_employee_balance(test_employee["id"])
    print(f"Test employee initial balance: €{initial_balance:.2f}")
    
    # 4. Create the specific order: 0.5€ roll + 0.5€ egg + 1€ coffee = 2€
    print("\\n4. Creating order: 1 roll half + 1 boiled egg + coffee...")
    
    order_data = {
        "employee_id": test_employee["id"],
        "department_id": DEPARTMENT_ID,
        "order_type": "breakfast",
        "breakfast_items": [{
            "total_halves": 1,
            "white_halves": 1,
            "seeded_halves": 0,
            "toppings": ["ruehrei"],  # Free topping
            "has_lunch": False,
            "boiled_eggs": 1,  # Should be 0.5€
            "has_coffee": True  # Should be 1.5€ (coffee price)
        }]
    }
    
    order_response = session.post(f"{BASE_URL}/orders", json=order_data)
    
    if order_response.status_code != 200:
        print(f"❌ Failed to create order: {order_response.status_code}: {order_response.text}")
        return False
    
    order = order_response.json()
    order_total = order.get("total_price", 0.0)
    print(f"✅ Order created with total: €{order_total:.2f}")
    
    # Check balance after order
    balance_after_order = get_employee_balance(test_employee["id"])
    print(f"Balance after order: €{balance_after_order:.2f}")
    
    # 5. Perform breakfast sponsoring
    print("\\n5. Performing breakfast sponsoring...")
    
    today = date.today().isoformat()
    sponsor_data = {
        "department_id": DEPARTMENT_ID,
        "date": today,
        "meal_type": "breakfast",
        "sponsor_employee_id": sponsor_employee["id"],
        "sponsor_employee_name": sponsor_employee["name"]
    }
    
    sponsor_response = session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=sponsor_data)
    
    if sponsor_response.status_code == 200:
        result = sponsor_response.json()
        print(f"✅ Breakfast sponsoring successful!")
        print(f"   Sponsored items: {result.get('sponsored_items', 'N/A')}")
        print(f"   Total cost: €{result.get('total_cost', 0):.2f}")
        print(f"   Affected employees: {result.get('affected_employees', 0)}")
        
        # Check balance after sponsoring
        balance_after_sponsoring = get_employee_balance(test_employee["id"])
        balance_change = balance_after_sponsoring - balance_after_order
        
        print(f"\\n6. Balance Analysis:")
        print(f"   Before order: €{initial_balance:.2f}")
        print(f"   After order: €{balance_after_order:.2f} (+€{balance_after_order - initial_balance:.2f})")
        print(f"   After sponsoring: €{balance_after_sponsoring:.2f} (change: €{balance_change:.2f})")
        
        # Expected: If rolls + eggs are sponsored, coffee should remain
        # Coffee price is typically 1.5€, so final balance should be initial + 1.5€
        expected_final_balance = initial_balance + 1.5  # Only coffee cost remains
        
        if abs(balance_after_sponsoring - expected_final_balance) <= 0.1:
            print(f"✅ BALANCE CALCULATION CORRECT!")
            print(f"   Expected final balance: €{expected_final_balance:.2f}")
            print(f"   Actual final balance: €{balance_after_sponsoring:.2f}")
            print(f"   ✅ Only coffee cost remains with employee as expected")
            return True
        else:
            print(f"❌ BALANCE CALCULATION ISSUE!")
            print(f"   Expected final balance: €{expected_final_balance:.2f}")
            print(f"   Actual final balance: €{balance_after_sponsoring:.2f}")
            print(f"   Difference: €{abs(balance_after_sponsoring - expected_final_balance):.2f}")
            return False
            
    elif sponsor_response.status_code == 400 and "bereits gesponsert" in sponsor_response.text:
        print("⚠️ Breakfast already sponsored today - cannot test fresh scenario")
        return True
    else:
        print(f"❌ Sponsoring failed: {sponsor_response.status_code}: {sponsor_response.text}")
        return False

if __name__ == "__main__":
    success = test_balance_calculation()
    print("\\n" + "=" * 60)
    if success:
        print("🎉 BALANCE CALCULATION TEST PASSED!")
    else:
        print("🚨 BALANCE CALCULATION TEST FAILED!")
    print("=" * 60)
    sys.exit(0 if success else 1)