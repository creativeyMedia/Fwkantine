#!/usr/bin/env python3
"""
Focused test for retroactive lunch price change (BUG 2)
"""

import requests
import json
import os
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log(message):
    print(f"🧪 {message}")

def error(message):
    print(f"❌ ERROR: {message}")

def success(message):
    print(f"✅ SUCCESS: {message}")

def test_retroactive_lunch_price():
    """Test retroactive lunch price change"""
    department_id = "fw4abteilung1"
    admin_credentials = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
    
    # Step 1: Authenticate
    response = requests.post(f"{API_BASE}/login/department-admin", json=admin_credentials)
    if response.status_code != 200:
        error(f"Authentication failed: {response.status_code}")
        return False
    success("Authenticated successfully")
    
    # Step 2: Set lunch price to 6.00€ FIRST
    log("Setting lunch price to €6.00")
    response = requests.put(f"{API_BASE}/lunch-settings?price=6.0&department_id={department_id}")
    if response.status_code != 200:
        error(f"Failed to set lunch price to 6.00: {response.status_code}")
        return False
    success("Set lunch price to €6.00")
    
    # Step 3: Create test employee
    employee_name = f"RetroTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    employee_data = {
        "name": employee_name,
        "department_id": department_id
    }
    
    response = requests.post(f"{API_BASE}/employees", json=employee_data)
    if response.status_code != 200:
        error(f"Failed to create employee: {response.status_code}")
        return False
    
    employee = response.json()
    employee_id = employee["id"]
    success(f"Created employee: {employee_name} (ID: {employee_id})")
    
    # Step 4: Create order with lunch at 6.00€
    order_data = {
        "employee_id": employee_id,
        "department_id": department_id,
        "order_type": "breakfast",
        "breakfast_items": [{
            "total_halves": 2,
            "white_halves": 1,
            "seeded_halves": 1,
            "toppings": ["Rührei", "Spiegelei"],
            "has_lunch": True,
            "boiled_eggs": 0,
            "fried_eggs": 0,
            "has_coffee": False
        }]
    }
    
    response = requests.post(f"{API_BASE}/orders", json=order_data)
    if response.status_code != 200:
        error(f"Failed to create order: {response.status_code}")
        return False
    
    order = response.json()
    order_id = order["id"]
    initial_total = order["total_price"]
    success(f"Created order with lunch at €6.00 (ID: {order_id}, Total: €{initial_total})")
    
    # Step 5: Get initial balance
    response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
    if response.status_code != 200:
        error(f"Failed to get initial balance: {response.status_code}")
        return False
    
    initial_profile = response.json()
    initial_balance = initial_profile["employee"]["breakfast_balance"]
    log(f"Initial balance after €6.00 lunch order: €{initial_balance}")
    
    # Step 6: Change lunch price to 5.00€ (retroactive)
    log("Changing lunch price to €5.00 (retroactive)")
    response = requests.put(f"{API_BASE}/lunch-settings?price=5.0&department_id={department_id}")
    if response.status_code != 200:
        error(f"Failed to change lunch price: {response.status_code}")
        return False
    
    result = response.json()
    updated_orders = result.get("updated_orders", 0)
    success(f"Changed lunch price to €5.00 (retroactive) - Updated {updated_orders} orders")
    
    # Step 7: Wait and check updated balance
    time.sleep(2)
    response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
    if response.status_code != 200:
        error(f"Failed to get updated balance: {response.status_code}")
        return False
    
    updated_profile = response.json()
    updated_balance = updated_profile["employee"]["breakfast_balance"]
    log(f"Updated balance after €5.00 lunch price change: €{updated_balance}")
    
    # Step 8: Check the order was updated
    updated_order = updated_profile["order_history"][0]
    updated_total = updated_order["total_price"]
    lunch_price_in_order = updated_order.get("lunch_price")
    
    log(f"Order details after retroactive update:")
    log(f"  - Order total_price: €{updated_total}")
    log(f"  - Order lunch_price: €{lunch_price_in_order}")
    
    # Step 9: Verify the changes
    balance_difference = updated_balance - initial_balance
    total_difference = updated_total - initial_total
    expected_difference = 1.0  # Should be €1.00 improvement
    
    log(f"Analysis:")
    log(f"  - Balance difference: €{balance_difference} (expected: €{expected_difference})")
    log(f"  - Order total difference: €{total_difference} (expected: €-1.0)")
    
    if abs(balance_difference - expected_difference) < 0.01:
        success("🎯 BUG 2 FIX VERIFIED: Retroactive lunch price change updated balance correctly!")
        return True
    else:
        error(f"BUG 2 NOT FIXED: Balance difference incorrect - Expected: €{expected_difference}, Got: €{balance_difference}")
        return False

if __name__ == "__main__":
    print("🧪 Focused Test - Retroactive Lunch Price Change (BUG 2)")
    print("=" * 60)
    
    success = test_retroactive_lunch_price()
    
    if success:
        print("\n🎉 BUG 2 FIX VERIFIED!")
    else:
        print("\n❌ BUG 2 NOT FIXED!")