#!/usr/bin/env python3
"""
CRITICAL LUNCH PRICING CALCULATION TEST
Tests the exact user-reported bug where lunch pricing calculation was incorrect
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

def test_critical_lunch_pricing_bug():
    """Test the exact lunch pricing calculation bug reported by user"""
    print("🚨 CRITICAL LUNCH PRICING CALCULATION TEST")
    print("=" * 60)
    print(f"Testing against: {API_BASE}")
    print("User reported: Expected €4.60, system showed €7.60")
    print("=" * 60)
    
    session = requests.Session()
    
    # Step 1: Initialize data and get departments
    print("\n1️⃣ Initializing data...")
    try:
        response = session.post(f"{API_BASE}/init-data")
        if response.status_code == 200:
            print("✅ Data initialized successfully")
        else:
            print(f"❌ Data initialization failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Data initialization error: {str(e)}")
        return False
    
    # Get departments
    try:
        response = session.get(f"{API_BASE}/departments")
        if response.status_code == 200:
            departments = response.json()
            if departments:
                test_dept = departments[0]
                print(f"✅ Using department: {test_dept['name']}")
            else:
                print("❌ No departments found")
                return False
        else:
            print(f"❌ Failed to get departments: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Department retrieval error: {str(e)}")
        return False
    
    # Step 2: Authenticate with department credentials
    print("\n2️⃣ Authenticating with department credentials...")
    try:
        login_data = {
            "department_name": test_dept['name'],
            "password": "password1"
        }
        response = session.post(f"{API_BASE}/login/department", json=login_data)
        if response.status_code == 200:
            print("✅ Department authentication successful")
        else:
            print(f"❌ Department authentication failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication error: {str(e)}")
        return False
    
    # Step 3: Create a test employee
    print("\n3️⃣ Creating test employee...")
    try:
        employee_data = {
            "name": "Test User for Lunch Pricing",
            "department_id": test_dept['id']
        }
        response = session.post(f"{API_BASE}/employees", json=employee_data)
        if response.status_code == 200:
            test_employee = response.json()
            print(f"✅ Created test employee: {test_employee['name']}")
        else:
            print(f"❌ Employee creation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Employee creation error: {str(e)}")
        return False
    
    # Step 4: Set lunch price to 3.00€
    print("\n4️⃣ Setting lunch price to €3.00...")
    try:
        response = session.put(f"{API_BASE}/lunch-settings", params={"price": 3.00})
        if response.status_code == 200:
            print("✅ Lunch price set to €3.00")
        else:
            print(f"❌ Failed to set lunch price: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Lunch price setting error: {str(e)}")
        return False
    
    # Step 5: Set boiled eggs price to 0.50€
    print("\n5️⃣ Setting boiled eggs price to €0.50...")
    try:
        response = session.put(f"{API_BASE}/lunch-settings/boiled-eggs-price", params={"price": 0.50})
        if response.status_code == 200:
            print("✅ Boiled eggs price set to €0.50")
        else:
            print(f"❌ Failed to set boiled eggs price: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Boiled eggs price setting error: {str(e)}")
        return False
    
    # Step 6: Update roll prices (weiss=0.50€, koerner=0.60€)
    print("\n6️⃣ Setting roll prices (weiss=€0.50, koerner=€0.60)...")
    try:
        # Get breakfast menu
        response = session.get(f"{API_BASE}/menu/breakfast/{test_dept['id']}")
        if response.status_code == 200:
            breakfast_menu = response.json()
            
            # Update white roll price
            white_roll = next((item for item in breakfast_menu if item['roll_type'] == 'weiss'), None)
            if white_roll:
                response = session.put(f"{API_BASE}/department-admin/menu/breakfast/{white_roll['id']}", 
                                     json={"price": 0.50}, params={"department_id": test_dept['id']})
                if response.status_code == 200:
                    print("✅ White roll price set to €0.50")
                else:
                    print(f"❌ Failed to update white roll price: {response.status_code}")
            
            # Update seeded roll price
            seeded_roll = next((item for item in breakfast_menu if item['roll_type'] == 'koerner'), None)
            if seeded_roll:
                response = session.put(f"{API_BASE}/department-admin/menu/breakfast/{seeded_roll['id']}", 
                                     json={"price": 0.60}, params={"department_id": test_dept['id']})
                if response.status_code == 200:
                    print("✅ Seeded roll price set to €0.60")
                else:
                    print(f"❌ Failed to update seeded roll price: {response.status_code}")
        else:
            print(f"❌ Failed to get breakfast menu: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Roll price setting error: {str(e)}")
        return False
    
    # Step 7: Create the EXACT order from user's test case
    print("\n7️⃣ Creating the EXACT order from user's test case...")
    print("Order: 1x white roll (€0.50) + 1x seeded roll (€0.60) + 1x boiled egg (€0.50) + lunch (€3.00)")
    print("Expected total: €4.60")
    
    try:
        critical_test_order = {
            "employee_id": test_employee['id'],
            "department_id": test_dept['id'],
            "order_type": "breakfast",
            "breakfast_items": [
                {
                    "total_halves": 2,
                    "white_halves": 1,  # 1x white roll half (€0.50)
                    "seeded_halves": 1,  # 1x seeded roll half (€0.60)
                    "toppings": ["butter", "butter"],  # 2 toppings for 2 roll halves
                    "boiled_eggs": 1,  # 1x boiled egg (€0.50)
                    "has_lunch": True  # 1x lunch (€3.00)
                }
            ]
        }
        
        response = session.post(f"{API_BASE}/orders", json=critical_test_order)
        
        if response.status_code == 200:
            order = response.json()
            actual_total = order['total_price']
            expected_total = 4.60  # 0.50 + 0.60 + 0.50 + 3.00 = 4.60€
            
            print(f"\n🎯 CRITICAL TEST RESULT:")
            print(f"Expected total: €{expected_total:.2f}")
            print(f"Actual total:   €{actual_total:.2f}")
            print(f"Difference:     €{actual_total - expected_total:.2f}")
            
            if abs(actual_total - expected_total) < 0.01:  # Allow for floating point precision
                print("✅ SUCCESS! Lunch pricing calculation is CORRECT!")
                print("🎉 The bug has been FIXED!")
                return True
            else:
                print("❌ FAILURE! Lunch pricing calculation is still WRONG!")
                print("🚨 The bug still EXISTS!")
                
                # Detailed breakdown
                print(f"\n🔍 DETAILED BREAKDOWN:")
                print(f"- White roll half: €0.50")
                print(f"- Seeded roll half: €0.60")
                print(f"- Boiled egg: €0.50")
                print(f"- Lunch: €3.00")
                print(f"- Expected total: €4.60")
                print(f"- Actual total: €{actual_total:.2f}")
                
                if actual_total > expected_total:
                    print(f"- System is overcharging by €{actual_total - expected_total:.2f}")
                else:
                    print(f"- System is undercharging by €{expected_total - actual_total:.2f}")
                
                return False
        else:
            print(f"❌ Order creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Order creation error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_critical_lunch_pricing_bug()
    if success:
        print("\n🎉 CRITICAL LUNCH PRICING TEST PASSED!")
        exit(0)
    else:
        print("\n🚨 CRITICAL LUNCH PRICING TEST FAILED!")
        exit(1)