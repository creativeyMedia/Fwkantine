#!/usr/bin/env python3
"""
Detailed Bug Fixes Test - Focus on Balance Update Logic
======================================================

This test specifically focuses on verifying the balance update logic for Bug 1.
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

def test_bug_1_detailed():
    """Detailed test for Bug 1 - Double Balance Deduction"""
    
    log("🎯 DETAILED BUG 1 TEST: Double Balance Deduction for Stammwachabteilung Breakfast")
    log("=" * 80)
    
    # Create test employee
    employee_name = f"DetailedTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
    
    # Get initial balance
    response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
    if response.status_code != 200:
        error(f"Failed to get employee profile: {response.status_code}")
        return False
        
    profile = response.json()
    initial_breakfast_balance = profile.get("breakfast_balance", 0.0)
    initial_drinks_balance = profile.get("drinks_sweets_balance", 0.0)
    
    log(f"Initial balances - Breakfast: €{initial_breakfast_balance}, Drinks/Sweets: €{initial_drinks_balance}")
    
    # Create breakfast order
    order_data = {
        "employee_id": employee_id,
        "department_id": department_id,
        "order_type": "breakfast",
        "breakfast_items": [{
            "total_halves": 2,
            "white_halves": 1,      # €0.50
            "seeded_halves": 1,     # €0.60
            "toppings": ["Rührei", "Spiegelei"],  # Free toppings
            "has_lunch": False,
            "boiled_eggs": 0,
            "fried_eggs": 0,
            "has_coffee": True      # Coffee price varies by department
        }]
    }
    
    log("Creating breakfast order...")
    response = requests.post(f"{API_BASE}/orders", json=order_data)
    if response.status_code != 200:
        error(f"Failed to create order: {response.status_code} - {response.text}")
        return False
        
    order = response.json()
    order_id = order["id"]
    total_price = order["total_price"]
    
    success(f"Created order (ID: {order_id}, Total: €{total_price})")
    
    # Wait for balance update
    log("Waiting for balance update...")
    time.sleep(3)
    
    # Check balance multiple times to ensure consistency
    for attempt in range(3):
        log(f"Balance check attempt {attempt + 1}/3...")
        
        response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
        if response.status_code != 200:
            error(f"Failed to get updated profile: {response.status_code}")
            continue
            
        updated_profile = response.json()
        final_breakfast_balance = updated_profile.get("breakfast_balance", 0.0)
        final_drinks_balance = updated_profile.get("drinks_sweets_balance", 0.0)
        
        log(f"Attempt {attempt + 1} - Breakfast: €{final_breakfast_balance}, Drinks/Sweets: €{final_drinks_balance}")
        
        # Calculate balance change
        balance_change = final_breakfast_balance - initial_breakfast_balance
        expected_change = -total_price  # Should be negative (debt)
        
        log(f"Balance change: €{balance_change} (expected: €{expected_change})")
        
        if abs(balance_change - expected_change) < 0.01:
            success(f"✅ BUG 1 FIX VERIFIED: Balance correctly deducted once (€{balance_change})")
            success(f"   Order total: €{total_price}, Balance change: €{balance_change}")
            return True
        elif abs(balance_change - (2 * expected_change)) < 0.01:
            error(f"❌ BUG 1 STILL EXISTS: Balance deducted twice! Expected: €{expected_change}, Got: €{balance_change}")
            return False
        elif balance_change == 0:
            log(f"⚠️  Balance not updated yet, waiting...")
            time.sleep(2)
            continue
        else:
            error(f"❌ BUG 1 UNEXPECTED: Balance change doesn't match expected pattern. Expected: €{expected_change}, Got: €{balance_change}")
            return False
    
    error("❌ Balance was not updated after multiple attempts")
    return False

def test_order_verification():
    """Verify that orders are being created and stored correctly"""
    
    log("🔍 ORDER VERIFICATION TEST")
    log("=" * 50)
    
    # Get recent orders to verify they're being stored
    response = requests.get(f"{API_BASE}/orders/breakfast-history/fw4abteilung1")
    if response.status_code != 200:
        error(f"Failed to get breakfast history: {response.status_code}")
        return False
        
    history = response.json()
    log(f"Breakfast history retrieved successfully")
    
    if "history" in history and len(history["history"]) > 0:
        recent_day = history["history"][0]
        employee_orders = recent_day.get("employee_orders", {})
        log(f"Found {len(employee_orders)} employee orders for most recent day")
        
        # Look for our test employees
        test_employees = [emp_key for emp_key in employee_orders.keys() if "Test" in emp_key]
        log(f"Found {len(test_employees)} test employees in recent orders")
        
        for emp_key in test_employees[:3]:  # Show first 3 test employees
            emp_data = employee_orders[emp_key]
            total_amount = emp_data.get("total_amount", 0)
            log(f"  {emp_key}: Total amount €{total_amount}")
            
        return True
    else:
        log("No recent breakfast history found")
        return True

def main():
    """Main test execution"""
    print("🧪 Detailed Bug Fixes Test - Balance Update Logic")
    print("=" * 70)
    
    # Run tests
    tests = [
        ("Order Verification", test_order_verification),
        ("Bug 1 Detailed Test", test_bug_1_detailed)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 50)
        
        if test_func():
            passed += 1
            success(f"PASSED: {test_name}")
        else:
            error(f"FAILED: {test_name}")
    
    print(f"\n🎯 RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)