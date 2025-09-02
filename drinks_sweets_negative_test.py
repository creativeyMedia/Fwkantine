#!/usr/bin/env python3
"""
🎯 DRINKS AND SWEETS NEGATIVE DISPLAY BUG FIX VERIFICATION

CRITICAL CHANGES TESTED:
1. Modified `/app/backend/server.py` lines 1321-1340: drinks and sweets orders now have `total_price = -total_price` 
2. Modified balance update logic: drinks/sweets use `new_balance = old_balance + total_price` (since total_price is negative)

SPECIFIC TESTING REQUIREMENTS:
1. Create test employees for department fw4abteilung2
2. Create drinks orders (e.g., Kaffee, Cola) - verify orders are stored with NEGATIVE total_price values
3. Create sweets orders (e.g., Schokoriegel, Keks) - verify orders are stored with NEGATIVE total_price values
4. Check employee balance updates are correct (negative balances representing debt)
5. Verify breakfast orders still work normally with POSITIVE total_price values
6. Test GET endpoints that return order data to confirm negative values are returned

EXPECTED RESULTS:
- Drinks orders: total_price should be negative (e.g., -0.80 for 0.80€ drink)
- Sweets orders: total_price should be negative (e.g., -1.50 for 1.50€ sweet)
- Employee drinks_sweets_balance should decrease (become more negative) after orders
- Breakfast orders should remain positive and work as before

Department: fw4abteilung2 (2. Wachabteilung)
Login: admin2/password2
"""

import requests
import json
from datetime import datetime, timedelta
import pytz
import os
from typing import Dict, List, Any

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteenio.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test Configuration - Use Department 2 as specified
DEPARTMENT_ID = "fw4abteilung2"  # Department 2 (2. Wachabteilung)
ADMIN_PASSWORD = "admin2"
DEPARTMENT_NAME = "2. Wachabteilung"

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

class DrinksSweeetsNegativeDisplayTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_employees = {}  # Store test employee IDs
        self.created_orders = {}  # Store created orders for verification
        
    def cleanup_test_data(self) -> bool:
        """Clean up test data to create fresh scenario"""
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/debug-cleanup/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully cleaned up test data: {result}")
                return True
            else:
                print(f"⚠️ Cleanup failed (continuing anyway): {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Cleanup error (continuing anyway): {e}")
            return False
    
    def authenticate_admin(self) -> bool:
        """Authenticate as admin for Department 2"""
        try:
            response = self.session.post(f"{API_BASE}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Admin Authentication Success: {data}")
                return True
            else:
                print(f"❌ Admin Authentication Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Admin Authentication Error: {e}")
            return False
    
    def create_test_employee(self, name: str) -> str:
        """Create a test employee and return employee ID"""
        try:
            response = self.session.post(f"{API_BASE}/employees", json={
                "name": name,
                "department_id": DEPARTMENT_ID
            })
            
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee["id"]
                print(f"✅ Created test employee '{name}': {employee_id}")
                return employee_id
            else:
                print(f"❌ Failed to create employee '{name}': {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating employee '{name}': {e}")
            return None
    
    def get_menu_items(self) -> Dict[str, Any]:
        """Get menu items for drinks and sweets"""
        try:
            # Get drinks menu
            drinks_response = self.session.get(f"{API_BASE}/menu/drinks/{DEPARTMENT_ID}")
            sweets_response = self.session.get(f"{API_BASE}/menu/sweets/{DEPARTMENT_ID}")
            
            drinks_menu = drinks_response.json() if drinks_response.status_code == 200 else []
            sweets_menu = sweets_response.json() if sweets_response.status_code == 200 else []
            
            print(f"📋 Available Drinks: {len(drinks_menu)} items")
            for drink in drinks_menu:
                print(f"  - {drink['name']}: €{drink['price']:.2f} (ID: {drink['id']})")
            
            print(f"📋 Available Sweets: {len(sweets_menu)} items")
            for sweet in sweets_menu:
                print(f"  - {sweet['name']}: €{sweet['price']:.2f} (ID: {sweet['id']})")
            
            return {
                "drinks": drinks_menu,
                "sweets": sweets_menu
            }
            
        except Exception as e:
            print(f"❌ Error getting menu items: {e}")
            return {"drinks": [], "sweets": []}
    
    def create_drinks_order(self, employee_name: str, employee_id: str, menu_items: Dict) -> Dict:
        """Create a drinks order and verify negative total_price"""
        try:
            print(f"\n🥤 CREATING DRINKS ORDER for {employee_name}:")
            print("=" * 60)
            
            drinks_menu = menu_items["drinks"]
            if not drinks_menu:
                print(f"❌ No drinks menu available")
                return None
            
            # Select first two drinks for testing
            selected_drinks = {}
            total_expected_cost = 0.0
            
            for i, drink in enumerate(drinks_menu[:2]):  # Take first 2 drinks
                quantity = 1 if i == 0 else 2  # 1 of first drink, 2 of second
                selected_drinks[drink["id"]] = quantity
                cost = drink["price"] * quantity
                total_expected_cost += cost
                print(f"  - {drink['name']}: {quantity}x €{drink['price']:.2f} = €{cost:.2f}")
            
            print(f"  - TOTAL EXPECTED COST: €{total_expected_cost:.2f}")
            print(f"  - EXPECTED STORED PRICE: €{-total_expected_cost:.2f} (NEGATIVE)")
            
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "drinks",
                "drink_items": selected_drinks
            }
            
            print(f"\n📤 SENDING DRINKS ORDER REQUEST:")
            print(f"Order data: {json.dumps(order_data, indent=2)}")
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                stored_price = order["total_price"]
                
                print(f"\n✅ DRINKS ORDER CREATED SUCCESSFULLY:")
                print(f"  - Order ID: {order['id']}")
                print(f"  - Stored Total Price: €{stored_price:.2f}")
                print(f"  - Expected Negative Price: €{-total_expected_cost:.2f}")
                
                # CRITICAL VERIFICATION: Check if price is stored as negative
                is_negative = stored_price < 0
                correct_amount = abs(abs(stored_price) - total_expected_cost) < 0.01
                
                print(f"\n🎯 CRITICAL VERIFICATION:")
                print(f"  - Price is NEGATIVE: {'✅' if is_negative else '❌'}")
                print(f"  - Correct Amount: {'✅' if correct_amount else '❌'}")
                print(f"  - Expected: €{-total_expected_cost:.2f}, Got: €{stored_price:.2f}")
                
                if is_negative and correct_amount:
                    print(f"  ✅ DRINKS NEGATIVE STORAGE: WORKING CORRECTLY")
                else:
                    print(f"  ❌ DRINKS NEGATIVE STORAGE: BUG DETECTED!")
                
                self.created_orders[f"{employee_name}_drinks"] = {
                    "order": order,
                    "expected_cost": total_expected_cost,
                    "is_negative_correct": is_negative,
                    "amount_correct": correct_amount
                }
                
                return order
            else:
                print(f"❌ Failed to create drinks order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating drinks order: {e}")
            return None
    
    def create_sweets_order(self, employee_name: str, employee_id: str, menu_items: Dict) -> Dict:
        """Create a sweets order and verify negative total_price"""
        try:
            print(f"\n🍫 CREATING SWEETS ORDER for {employee_name}:")
            print("=" * 60)
            
            sweets_menu = menu_items["sweets"]
            if not sweets_menu:
                print(f"❌ No sweets menu available")
                return None
            
            # Select first two sweets for testing
            selected_sweets = {}
            total_expected_cost = 0.0
            
            for i, sweet in enumerate(sweets_menu[:2]):  # Take first 2 sweets
                quantity = 2 if i == 0 else 1  # 2 of first sweet, 1 of second
                selected_sweets[sweet["id"]] = quantity
                cost = sweet["price"] * quantity
                total_expected_cost += cost
                print(f"  - {sweet['name']}: {quantity}x €{sweet['price']:.2f} = €{cost:.2f}")
            
            print(f"  - TOTAL EXPECTED COST: €{total_expected_cost:.2f}")
            print(f"  - EXPECTED STORED PRICE: €{-total_expected_cost:.2f} (NEGATIVE)")
            
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "sweets",
                "sweet_items": selected_sweets
            }
            
            print(f"\n📤 SENDING SWEETS ORDER REQUEST:")
            print(f"Order data: {json.dumps(order_data, indent=2)}")
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                stored_price = order["total_price"]
                
                print(f"\n✅ SWEETS ORDER CREATED SUCCESSFULLY:")
                print(f"  - Order ID: {order['id']}")
                print(f"  - Stored Total Price: €{stored_price:.2f}")
                print(f"  - Expected Negative Price: €{-total_expected_cost:.2f}")
                
                # CRITICAL VERIFICATION: Check if price is stored as negative
                is_negative = stored_price < 0
                correct_amount = abs(abs(stored_price) - total_expected_cost) < 0.01
                
                print(f"\n🎯 CRITICAL VERIFICATION:")
                print(f"  - Price is NEGATIVE: {'✅' if is_negative else '❌'}")
                print(f"  - Correct Amount: {'✅' if correct_amount else '❌'}")
                print(f"  - Expected: €{-total_expected_cost:.2f}, Got: €{stored_price:.2f}")
                
                if is_negative and correct_amount:
                    print(f"  ✅ SWEETS NEGATIVE STORAGE: WORKING CORRECTLY")
                else:
                    print(f"  ❌ SWEETS NEGATIVE STORAGE: BUG DETECTED!")
                
                self.created_orders[f"{employee_name}_sweets"] = {
                    "order": order,
                    "expected_cost": total_expected_cost,
                    "is_negative_correct": is_negative,
                    "amount_correct": correct_amount
                }
                
                return order
            else:
                print(f"❌ Failed to create sweets order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating sweets order: {e}")
            return None
    
    def create_breakfast_order(self, employee_name: str, employee_id: str) -> Dict:
        """Create a breakfast order and verify it remains POSITIVE"""
        try:
            print(f"\n🥐 CREATING BREAKFAST ORDER for {employee_name} (Control Test):")
            print("=" * 60)
            
            # Simple breakfast order
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 1 roll (2 halves)
                    "white_halves": 1,  # €0.50
                    "seeded_halves": 1, # €0.60
                    "toppings": ["butter", "kaese"],
                    "has_lunch": False,
                    "boiled_eggs": 0,
                    "has_coffee": True  # Should add coffee cost
                }]
            }
            
            print(f"📤 SENDING BREAKFAST ORDER REQUEST:")
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                stored_price = order["total_price"]
                
                print(f"\n✅ BREAKFAST ORDER CREATED SUCCESSFULLY:")
                print(f"  - Order ID: {order['id']}")
                print(f"  - Stored Total Price: €{stored_price:.2f}")
                
                # CRITICAL VERIFICATION: Check if price is POSITIVE (breakfast should remain positive)
                is_positive = stored_price > 0
                
                print(f"\n🎯 CRITICAL VERIFICATION:")
                print(f"  - Price is POSITIVE: {'✅' if is_positive else '❌'}")
                print(f"  - Breakfast orders should remain positive: {'✅' if is_positive else '❌'}")
                
                if is_positive:
                    print(f"  ✅ BREAKFAST POSITIVE STORAGE: WORKING CORRECTLY")
                else:
                    print(f"  ❌ BREAKFAST POSITIVE STORAGE: BUG DETECTED!")
                
                self.created_orders[f"{employee_name}_breakfast"] = {
                    "order": order,
                    "is_positive_correct": is_positive
                }
                
                return order
            else:
                print(f"❌ Failed to create breakfast order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating breakfast order: {e}")
            return None
    
    def verify_employee_balance_updates(self, employee_name: str, employee_id: str) -> Dict:
        """Verify that employee balance updates are correct after drinks/sweets orders"""
        try:
            print(f"\n💰 VERIFYING BALANCE UPDATES for {employee_name}:")
            print("=" * 60)
            
            # Get employee profile to check balances
            response = self.session.get(f"{API_BASE}/employees/{employee_id}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                
                breakfast_balance = profile.get("breakfast_balance", 0.0)
                drinks_sweets_balance = profile.get("drinks_sweets_balance", 0.0)
                
                print(f"📊 CURRENT BALANCES:")
                print(f"  - Breakfast Balance: €{breakfast_balance:.2f}")
                print(f"  - Drinks/Sweets Balance: €{drinks_sweets_balance:.2f}")
                
                # Calculate expected drinks/sweets balance
                expected_drinks_sweets_debt = 0.0
                
                # Add drinks order debt
                if f"{employee_name}_drinks" in self.created_orders:
                    drinks_cost = self.created_orders[f"{employee_name}_drinks"]["expected_cost"]
                    expected_drinks_sweets_debt -= drinks_cost  # Negative because it's debt
                    print(f"  - Expected drinks debt: €{-drinks_cost:.2f}")
                
                # Add sweets order debt
                if f"{employee_name}_sweets" in self.created_orders:
                    sweets_cost = self.created_orders[f"{employee_name}_sweets"]["expected_cost"]
                    expected_drinks_sweets_debt -= sweets_cost  # Negative because it's debt
                    print(f"  - Expected sweets debt: €{-sweets_cost:.2f}")
                
                print(f"  - Total Expected Drinks/Sweets Debt: €{expected_drinks_sweets_debt:.2f}")
                
                # Verify balance is correct
                balance_correct = abs(drinks_sweets_balance - expected_drinks_sweets_debt) < 0.01
                balance_is_negative = drinks_sweets_balance < 0
                
                print(f"\n🎯 BALANCE VERIFICATION:")
                print(f"  - Balance is NEGATIVE (debt): {'✅' if balance_is_negative else '❌'}")
                print(f"  - Balance amount CORRECT: {'✅' if balance_correct else '❌'}")
                print(f"  - Expected: €{expected_drinks_sweets_debt:.2f}, Got: €{drinks_sweets_balance:.2f}")
                
                if balance_is_negative and balance_correct:
                    print(f"  ✅ BALANCE UPDATE LOGIC: WORKING CORRECTLY")
                else:
                    print(f"  ❌ BALANCE UPDATE LOGIC: BUG DETECTED!")
                
                return {
                    "balance_correct": balance_correct,
                    "balance_is_negative": balance_is_negative,
                    "expected_balance": expected_drinks_sweets_debt,
                    "actual_balance": drinks_sweets_balance
                }
            else:
                print(f"❌ Failed to get employee profile: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error verifying balance updates: {e}")
            return None
    
    def verify_get_endpoints_return_negative_values(self) -> Dict:
        """Verify that GET endpoints return negative values for drinks/sweets orders"""
        try:
            print(f"\n🔍 VERIFYING GET ENDPOINTS RETURN NEGATIVE VALUES:")
            print("=" * 60)
            
            # Test employee profile endpoint
            results = {"profile_endpoint": False, "orders_endpoint": False}
            
            for employee_name, employee_id in self.test_employees.items():
                print(f"\n📋 Testing GET endpoints for {employee_name}:")
                
                # Test individual employee profile
                response = self.session.get(f"{API_BASE}/employees/{employee_id}/profile")
                
                if response.status_code == 200:
                    profile = response.json()
                    order_history = profile.get("order_history", [])
                    
                    print(f"  - Order history entries: {len(order_history)}")
                    
                    negative_drinks_found = False
                    negative_sweets_found = False
                    
                    for order in order_history:
                        order_type = order.get("order_type", "")
                        total_price = order.get("total_price", 0.0)
                        
                        print(f"    - {order_type} order: €{total_price:.2f}")
                        
                        if order_type == "drinks" and total_price < 0:
                            negative_drinks_found = True
                            print(f"      ✅ Drinks order has negative price")
                        elif order_type == "sweets" and total_price < 0:
                            negative_sweets_found = True
                            print(f"      ✅ Sweets order has negative price")
                        elif order_type == "breakfast" and total_price > 0:
                            print(f"      ✅ Breakfast order has positive price")
                        elif order_type in ["drinks", "sweets"] and total_price >= 0:
                            print(f"      ❌ {order_type} order should be negative but is €{total_price:.2f}")
                    
                    if negative_drinks_found or negative_sweets_found:
                        results["profile_endpoint"] = True
                        print(f"  ✅ Profile endpoint returns negative values correctly")
                    else:
                        print(f"  ❌ Profile endpoint does not return negative values")
                
                break  # Test with first employee only
            
            print(f"\n🎯 GET ENDPOINTS VERIFICATION:")
            print(f"  - Profile endpoint returns negative values: {'✅' if results['profile_endpoint'] else '❌'}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error verifying GET endpoints: {e}")
            return {"profile_endpoint": False, "orders_endpoint": False}
    
    def run_drinks_sweets_negative_test(self):
        """Run the complete drinks and sweets negative display test"""
        print("🎯 DRINKS AND SWEETS NEGATIVE DISPLAY BUG FIX VERIFICATION")
        print("=" * 100)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 2 (fw4abteilung2)")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 2: Clean up existing data for fresh test
        print("\n2️⃣ Cleaning Up Existing Data")
        self.cleanup_test_data()
        
        # Step 3: Get menu items
        print("\n3️⃣ Getting Menu Items")
        menu_items = self.get_menu_items()
        if not menu_items["drinks"] and not menu_items["sweets"]:
            print("❌ CRITICAL FAILURE: No menu items available")
            return False
        
        # Step 4: Create test employees
        print("\n4️⃣ Creating Test Employees")
        test_employee_names = ["TestDrinks", "TestSweets", "TestBoth"]
        
        for name in test_employee_names:
            employee_id = self.create_test_employee(name)
            if not employee_id:
                print(f"❌ CRITICAL FAILURE: Cannot create {name}")
                return False
            self.test_employees[name] = employee_id
        
        # Step 5: Test drinks orders (negative storage)
        print("\n5️⃣ Testing Drinks Orders (Should be NEGATIVE)")
        drinks_success = True
        if menu_items["drinks"]:
            drinks_order = self.create_drinks_order("TestDrinks", self.test_employees["TestDrinks"], menu_items)
            if not drinks_order:
                drinks_success = False
        else:
            print("⚠️ Skipping drinks test - no drinks menu available")
        
        # Step 6: Test sweets orders (negative storage)
        print("\n6️⃣ Testing Sweets Orders (Should be NEGATIVE)")
        sweets_success = True
        if menu_items["sweets"]:
            sweets_order = self.create_sweets_order("TestSweets", self.test_employees["TestSweets"], menu_items)
            if not sweets_order:
                sweets_success = False
        else:
            print("⚠️ Skipping sweets test - no sweets menu available")
        
        # Step 7: Test breakfast orders (positive storage - control test)
        print("\n7️⃣ Testing Breakfast Orders (Should remain POSITIVE)")
        breakfast_order = self.create_breakfast_order("TestBoth", self.test_employees["TestBoth"])
        breakfast_success = breakfast_order is not None
        
        # Step 8: Test combined orders (both drinks and sweets for same employee)
        print("\n8️⃣ Testing Combined Orders (Both Drinks and Sweets)")
        combined_success = True
        if menu_items["drinks"] and menu_items["sweets"]:
            # Create both drinks and sweets orders for TestBoth employee
            drinks_order2 = self.create_drinks_order("TestBoth", self.test_employees["TestBoth"], menu_items)
            sweets_order2 = self.create_sweets_order("TestBoth", self.test_employees["TestBoth"], menu_items)
            if not drinks_order2 or not sweets_order2:
                combined_success = False
        
        # Step 9: Verify employee balance updates
        print("\n9️⃣ Verifying Employee Balance Updates")
        balance_results = {}
        for employee_name, employee_id in self.test_employees.items():
            balance_result = self.verify_employee_balance_updates(employee_name, employee_id)
            balance_results[employee_name] = balance_result
        
        # Step 10: Verify GET endpoints return negative values
        print("\n🔟 Verifying GET Endpoints Return Negative Values")
        get_endpoints_result = self.verify_get_endpoints_return_negative_values()
        
        # Final Results
        print(f"\n🏁 DRINKS AND SWEETS NEGATIVE DISPLAY TEST RESULTS:")
        print("=" * 100)
        
        all_tests_passed = True
        
        # Check drinks orders
        if menu_items["drinks"]:
            drinks_order_key = "TestDrinks_drinks"
            if drinks_order_key in self.created_orders:
                drinks_result = self.created_orders[drinks_order_key]
                drinks_negative_ok = drinks_result["is_negative_correct"]
                drinks_amount_ok = drinks_result["amount_correct"]
                
                print(f"✅ Drinks Orders: {'PASSED' if drinks_negative_ok and drinks_amount_ok else 'FAILED'}")
                print(f"   - Stored as NEGATIVE: {'✅' if drinks_negative_ok else '❌'}")
                print(f"   - Correct Amount: {'✅' if drinks_amount_ok else '❌'}")
                
                if not (drinks_negative_ok and drinks_amount_ok):
                    all_tests_passed = False
            else:
                print(f"❌ Drinks Orders: FAILED - No drinks order created")
                all_tests_passed = False
        
        # Check sweets orders
        if menu_items["sweets"]:
            sweets_order_key = "TestSweets_sweets"
            if sweets_order_key in self.created_orders:
                sweets_result = self.created_orders[sweets_order_key]
                sweets_negative_ok = sweets_result["is_negative_correct"]
                sweets_amount_ok = sweets_result["amount_correct"]
                
                print(f"✅ Sweets Orders: {'PASSED' if sweets_negative_ok and sweets_amount_ok else 'FAILED'}")
                print(f"   - Stored as NEGATIVE: {'✅' if sweets_negative_ok else '❌'}")
                print(f"   - Correct Amount: {'✅' if sweets_amount_ok else '❌'}")
                
                if not (sweets_negative_ok and sweets_amount_ok):
                    all_tests_passed = False
            else:
                print(f"❌ Sweets Orders: FAILED - No sweets order created")
                all_tests_passed = False
        
        # Check breakfast orders (control test)
        breakfast_order_key = "TestBoth_breakfast"
        if breakfast_order_key in self.created_orders:
            breakfast_result = self.created_orders[breakfast_order_key]
            breakfast_positive_ok = breakfast_result["is_positive_correct"]
            
            print(f"✅ Breakfast Orders (Control): {'PASSED' if breakfast_positive_ok else 'FAILED'}")
            print(f"   - Remains POSITIVE: {'✅' if breakfast_positive_ok else '❌'}")
            
            if not breakfast_positive_ok:
                all_tests_passed = False
        else:
            print(f"❌ Breakfast Orders (Control): FAILED - No breakfast order created")
            all_tests_passed = False
        
        # Check balance updates
        balance_all_correct = True
        for employee_name, balance_result in balance_results.items():
            if balance_result:
                balance_correct = balance_result["balance_correct"] and balance_result["balance_is_negative"]
                if not balance_correct:
                    balance_all_correct = False
                    break
        
        print(f"✅ Employee Balance Updates: {'PASSED' if balance_all_correct else 'FAILED'}")
        print(f"   - Balances become NEGATIVE (debt): {'✅' if balance_all_correct else '❌'}")
        print(f"   - Balance amounts CORRECT: {'✅' if balance_all_correct else '❌'}")
        
        if not balance_all_correct:
            all_tests_passed = False
        
        # Check GET endpoints
        get_endpoints_ok = get_endpoints_result["profile_endpoint"]
        print(f"✅ GET Endpoints Return Negative Values: {'PASSED' if get_endpoints_ok else 'FAILED'}")
        print(f"   - Profile endpoint returns negative values: {'✅' if get_endpoints_ok else '❌'}")
        
        if not get_endpoints_ok:
            all_tests_passed = False
        
        print(f"\n🎯 CRITICAL VERIFICATION SUMMARY:")
        print(f"   - Drinks orders stored as NEGATIVE: {'✅' if all_tests_passed else '❌'}")
        print(f"   - Sweets orders stored as NEGATIVE: {'✅' if all_tests_passed else '❌'}")
        print(f"   - Employee balances become negative (debt): {'✅' if all_tests_passed else '❌'}")
        print(f"   - Breakfast orders remain POSITIVE: {'✅' if all_tests_passed else '❌'}")
        print(f"   - GET endpoints return negative values: {'✅' if all_tests_passed else '❌'}")
        
        return all_tests_passed

def main():
    """Main test execution"""
    test = DrinksSweeetsNegativeDisplayTest()
    
    try:
        success = test.run_drinks_sweets_negative_test()
        
        if success:
            print(f"\n✅ DRINKS AND SWEETS NEGATIVE DISPLAY TEST: COMPLETED SUCCESSFULLY")
            print(f"🎯 The backend fix for drinks and sweets negative display is WORKING CORRECTLY!")
            exit(0)
        else:
            print(f"\n❌ DRINKS AND SWEETS NEGATIVE DISPLAY TEST: CRITICAL ISSUES DETECTED")
            print(f"🚨 The backend fix for drinks and sweets negative display has BUGS!")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()