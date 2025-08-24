#!/usr/bin/env python3
"""
Additional Lunch Pricing Tests
Tests all the additional scenarios mentioned in the review request
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

def run_additional_lunch_tests():
    """Run additional lunch pricing tests"""
    print("🧪 ADDITIONAL LUNCH PRICING TESTS")
    print("=" * 50)
    print(f"Testing against: {API_BASE}")
    print("=" * 50)
    
    session = requests.Session()
    
    # Initialize and authenticate
    session.post(f"{API_BASE}/init-data")
    departments = session.get(f"{API_BASE}/departments").json()
    test_dept = departments[0]
    
    # Master authentication
    session.post(f"{API_BASE}/login/master", 
                params={"department_name": test_dept['name'], "master_password": "master123dev"})
    
    # Create test employee
    employee_data = {"name": "Additional Test User", "department_id": test_dept['id']}
    test_employee = session.post(f"{API_BASE}/employees", json=employee_data).json()
    
    # Set prices
    session.put(f"{API_BASE}/lunch-settings", params={"price": 3.00})
    session.put(f"{API_BASE}/lunch-settings/boiled-eggs-price", params={"price": 0.50})
    
    # Update roll prices
    breakfast_menu = session.get(f"{API_BASE}/menu/breakfast/{test_dept['id']}").json()
    white_roll = next((item for item in breakfast_menu if item['roll_type'] == 'weiss'), None)
    seeded_roll = next((item for item in breakfast_menu if item['roll_type'] == 'koerner'), None)
    
    if white_roll:
        session.put(f"{API_BASE}/department-admin/menu/breakfast/{white_roll['id']}", 
                   json={"price": 0.50}, params={"department_id": test_dept['id']})
    if seeded_roll:
        session.put(f"{API_BASE}/department-admin/menu/breakfast/{seeded_roll['id']}", 
                   json={"price": 0.60}, params={"department_id": test_dept['id']})
    
    test_results = []
    
    # Test 1: Lunch-only order (should be 3.00€)
    print("\n1️⃣ Testing lunch-only order...")
    try:
        lunch_only_order = {
            "employee_id": test_employee['id'],
            "department_id": test_dept['id'],
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 0,
                "white_halves": 0,
                "seeded_halves": 0,
                "toppings": [],
                "boiled_eggs": 0,
                "has_lunch": True
            }]
        }
        
        response = session.post(f"{API_BASE}/orders", json=lunch_only_order)
        if response.status_code == 200:
            order = response.json()
            actual = order['total_price']
            expected = 3.00
            
            if abs(actual - expected) < 0.01:
                print(f"✅ Lunch-only: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(True)
            else:
                print(f"❌ Lunch-only: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(False)
        else:
            print(f"❌ Lunch-only order failed: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ Lunch-only test error: {str(e)}")
        test_results.append(False)
    
    # Test 2: Rolls+lunch (2 halves + lunch): should be 1.10€ + 3.00€ = 4.10€
    print("\n2️⃣ Testing rolls+lunch order...")
    try:
        rolls_lunch_order = {
            "employee_id": test_employee['id'],
            "department_id": test_dept['id'],
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 2,
                "white_halves": 1,  # 0.50€
                "seeded_halves": 1,  # 0.60€
                "toppings": ["butter", "butter"],
                "boiled_eggs": 0,
                "has_lunch": True  # 3.00€
            }]
        }
        
        response = session.post(f"{API_BASE}/orders", json=rolls_lunch_order)
        if response.status_code == 200:
            order = response.json()
            actual = order['total_price']
            expected = 4.10  # 0.50 + 0.60 + 3.00
            
            if abs(actual - expected) < 0.01:
                print(f"✅ Rolls+lunch: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(True)
            else:
                print(f"❌ Rolls+lunch: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(False)
        else:
            print(f"❌ Rolls+lunch order failed: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ Rolls+lunch test error: {str(e)}")
        test_results.append(False)
    
    # Test 3: Eggs+lunch (no rolls): should be 0.50€ + 3.00€ = 3.50€
    print("\n3️⃣ Testing eggs+lunch order...")
    try:
        eggs_lunch_order = {
            "employee_id": test_employee['id'],
            "department_id": test_dept['id'],
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 0,
                "white_halves": 0,
                "seeded_halves": 0,
                "toppings": [],
                "boiled_eggs": 1,  # 0.50€
                "has_lunch": True  # 3.00€
            }]
        }
        
        response = session.post(f"{API_BASE}/orders", json=eggs_lunch_order)
        if response.status_code == 200:
            order = response.json()
            actual = order['total_price']
            expected = 3.50  # 0.50 + 3.00
            
            if abs(actual - expected) < 0.01:
                print(f"✅ Eggs+lunch: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(True)
            else:
                print(f"❌ Eggs+lunch: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(False)
        else:
            print(f"❌ Eggs+lunch order failed: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ Eggs+lunch test error: {str(e)}")
        test_results.append(False)
    
    # Test 4: Multiple eggs + lunch
    print("\n4️⃣ Testing multiple eggs+lunch order...")
    try:
        multi_eggs_lunch_order = {
            "employee_id": test_employee['id'],
            "department_id": test_dept['id'],
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 0,
                "white_halves": 0,
                "seeded_halves": 0,
                "toppings": [],
                "boiled_eggs": 3,  # 3 × 0.50€ = 1.50€
                "has_lunch": True  # 3.00€
            }]
        }
        
        response = session.post(f"{API_BASE}/orders", json=multi_eggs_lunch_order)
        if response.status_code == 200:
            order = response.json()
            actual = order['total_price']
            expected = 4.50  # 1.50 + 3.00
            
            if abs(actual - expected) < 0.01:
                print(f"✅ Multiple eggs+lunch: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(True)
            else:
                print(f"❌ Multiple eggs+lunch: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(False)
        else:
            print(f"❌ Multiple eggs+lunch order failed: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ Multiple eggs+lunch test error: {str(e)}")
        test_results.append(False)
    
    # Test 5: Complex order (rolls + eggs + lunch)
    print("\n5️⃣ Testing complex order (rolls + eggs + lunch)...")
    try:
        complex_order = {
            "employee_id": test_employee['id'],
            "department_id": test_dept['id'],
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 3,
                "white_halves": 2,  # 2 × 0.50€ = 1.00€
                "seeded_halves": 1,  # 1 × 0.60€ = 0.60€
                "toppings": ["butter", "butter", "butter"],
                "boiled_eggs": 2,  # 2 × 0.50€ = 1.00€
                "has_lunch": True  # 3.00€
            }]
        }
        
        response = session.post(f"{API_BASE}/orders", json=complex_order)
        if response.status_code == 200:
            order = response.json()
            actual = order['total_price']
            expected = 5.60  # 1.00 + 0.60 + 1.00 + 3.00
            
            if abs(actual - expected) < 0.01:
                print(f"✅ Complex order: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(True)
            else:
                print(f"❌ Complex order: €{actual:.2f} (expected €{expected:.2f})")
                test_results.append(False)
        else:
            print(f"❌ Complex order failed: {response.status_code}")
            test_results.append(False)
    except Exception as e:
        print(f"❌ Complex order test error: {str(e)}")
        test_results.append(False)
    
    # Summary
    passed = sum(test_results)
    total = len(test_results)
    
    print(f"\n🎯 ADDITIONAL TESTS SUMMARY:")
    print(f"Passed: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 ALL ADDITIONAL LUNCH PRICING TESTS PASSED!")
        return True
    else:
        print("🚨 SOME ADDITIONAL TESTS FAILED!")
        return False

if __name__ == "__main__":
    success = run_additional_lunch_tests()
    if success:
        exit(0)
    else:
        exit(1)