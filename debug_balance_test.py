#!/usr/bin/env python3
"""
Debug Balance Update Test
========================

This test debugs the balance update issue by checking each step of the process.
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

def debug_balance_update():
    """Debug the balance update process step by step"""
    
    log("🔍 DEBUG BALANCE UPDATE PROCESS")
    log("=" * 50)
    
    # Create test employee
    employee_name = f"DebugTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    department_id = "fw4abteilung1"
    
    employee_data = {
        "name": employee_name,
        "department_id": department_id
    }
    
    response = requests.post(f"{API_BASE}/employees", json=employee_data)
    if response.status_code != 200:
        error(f"Failed to create employee: {response.status_code} - {response.text}")
        return False
        
    employee = response.json()
    employee_id = employee["id"]
    success(f"Created test employee: {employee_name} (ID: {employee_id})")
    
    # Check employee data structure
    log(f"Employee data: {json.dumps(employee, indent=2)}")
    
    # Get initial profile
    response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
    if response.status_code != 200:
        error(f"Failed to get employee profile: {response.status_code}")
        return False
        
    profile = response.json()
    log(f"Initial profile breakfast_total: {profile.get('breakfast_total', 'MISSING')}")
    log(f"Initial profile drinks_sweets_total: {profile.get('drinks_sweets_total', 'MISSING')}")
    
    # Create a simple breakfast order
    order_data = {
        "employee_id": employee_id,
        "department_id": department_id,
        "order_type": "breakfast",
        "breakfast_items": [{
            "total_halves": 1,
            "white_halves": 1,
            "seeded_halves": 0,
            "toppings": ["Rührei"],
            "has_lunch": False,
            "boiled_eggs": 0,
            "fried_eggs": 0,
            "has_coffee": False  # Simplify - no coffee
        }]
    }
    
    log("Creating simple breakfast order (1 white roll with Rührei, no coffee)...")
    response = requests.post(f"{API_BASE}/orders", json=order_data)
    if response.status_code != 200:
        error(f"Failed to create order: {response.status_code} - {response.text}")
        return False
        
    order = response.json()
    order_id = order["id"]
    total_price = order["total_price"]
    
    success(f"Created order (ID: {order_id}, Total: €{total_price})")
    log(f"Order data: {json.dumps(order, indent=2)}")
    
    # Check if this is a home department order
    log(f"Employee department: {department_id}")
    log(f"Order department: {department_id}")
    log(f"Is home department: {department_id == department_id}")
    
    # Wait and check balance multiple times
    for attempt in range(5):
        log(f"\n--- Balance check attempt {attempt + 1}/5 ---")
        time.sleep(2)
        
        response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
        if response.status_code != 200:
            error(f"Failed to get updated profile: {response.status_code}")
            continue
            
        updated_profile = response.json()
        breakfast_balance = updated_profile.get("breakfast_total", "MISSING")
        drinks_balance = updated_profile.get("drinks_sweets_total", "MISSING")
        
        log(f"Breakfast balance: {breakfast_balance}")
        log(f"Drinks/Sweets balance: {drinks_balance}")
        
        if isinstance(breakfast_balance, (int, float)) and breakfast_balance != 0:
            expected_balance = -total_price
            if abs(breakfast_balance - expected_balance) < 0.01:
                success(f"✅ Balance updated correctly: €{breakfast_balance} (expected: €{expected_balance})")
                return True
            else:
                error(f"❌ Balance updated incorrectly: €{breakfast_balance} (expected: €{expected_balance})")
                return False
    
    # Check if we can find the order in the breakfast history
    log("\n--- Checking breakfast history ---")
    response = requests.get(f"{API_BASE}/orders/breakfast-history/{department_id}")
    if response.status_code == 200:
        history = response.json()
        if "history" in history and len(history["history"]) > 0:
            recent_day = history["history"][0]
            employee_orders = recent_day.get("employee_orders", {})
            
            # Look for our employee
            found_employee = False
            for emp_key, emp_data in employee_orders.items():
                if employee_name in emp_key:
                    found_employee = True
                    log(f"Found employee in breakfast history: {emp_key}")
                    log(f"Employee data: {json.dumps(emp_data, indent=2)}")
                    break
            
            if not found_employee:
                log("Employee not found in breakfast history")
        else:
            log("No breakfast history found")
    else:
        error(f"Failed to get breakfast history: {response.status_code}")
    
    error("❌ Balance was not updated correctly after multiple attempts")
    return False

def main():
    """Main test execution"""
    print("🧪 Debug Balance Update Test")
    print("=" * 50)
    
    success = debug_balance_update()
    
    if success:
        print("\n🎉 BALANCE UPDATE WORKING!")
    else:
        print("\n❌ BALANCE UPDATE NOT WORKING!")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)