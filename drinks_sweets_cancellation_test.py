#!/usr/bin/env python3
"""
Critical Drinks/Sweets Cancellation Logic Bug Test
==================================================

This test suite specifically tests the critical bug fix for drinks and sweets cancellation logic.

BUG SCENARIO TESTED:
1. Order a drink for €1.20 → balance should be -€1.20
2. Cancel this order → balance should go back to €0 (NOT -€2.40)
3. Same test for sweets (e.g., Schokoriegel €1.50)

FIX VERIFICATION:
- Lines ~2327 and ~3069: Use subtraction instead of addition for drinks/sweets cancellation
- Reason: drinks/sweets total_price is already stored as negative amounts

TESTING TASKS:
1. Create a test employee
2. Order 1 drink (Cola €1.20) → verify balance = -€1.20
3. Cancel via Employee-Delete-Endpoint → verify balance = €0 (NOT -€2.40)
4. Order 1 sweet (Schokoriegel €1.50) → verify balance = -€1.50
5. Cancel via Admin-Delete-Endpoint → verify balance = €0 (NOT -€3.00)
6. Verify breakfast orders still work correctly
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class DrinksSweetsCancellationTest:
    def __init__(self):
        self.department_id = "fw4abteilung1"
        self.admin_credentials = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.test_employee_id = None
        self.test_employee_name = f"CancelTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.drink_order_id = None
        self.sweet_order_id = None
        self.cola_item_id = None
        self.schokoriegel_item_id = None
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        
    def test_init_data(self):
        """Initialize data to ensure departments exist"""
        try:
            response = requests.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.success("Data initialization successful")
                return True
            else:
                self.log(f"Init data response: {response.status_code} - {response.text}")
                # This might fail if data already exists, which is OK
                return True
        except Exception as e:
            self.error(f"Exception during data initialization: {str(e)}")
            return False
            
    def authenticate_admin(self):
        """Authenticate as department admin"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.admin_credentials)
            if response.status_code == 200:
                self.success(f"Admin authentication successful for {self.department_id}")
                return True
            else:
                self.error(f"Admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Admin authentication exception: {str(e)}")
            return False
            
    def create_test_employee(self):
        """Create a test employee for the cancellation test"""
        try:
            employee_data = {
                "name": self.test_employee_name,
                "department_id": self.department_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_id = employee["id"]
                self.success(f"Created test employee: {self.test_employee_name} (ID: {self.test_employee_id})")
                return True
            else:
                self.error(f"Failed to create test employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating test employee: {str(e)}")
            return False
            
    def get_menu_items(self):
        """Get drink and sweet menu items to find Cola and Schokoriegel"""
        try:
            # Get drinks menu
            drinks_response = requests.get(f"{API_BASE}/menu/drinks/{self.department_id}")
            if drinks_response.status_code == 200:
                drinks = drinks_response.json()
                for drink in drinks:
                    if "Cola" in drink["name"]:
                        self.cola_item_id = drink["id"]
                        self.success(f"Found Cola item: {drink['name']} (€{drink['price']}) - ID: {drink['id']}")
                        break
                
                if not self.cola_item_id:
                    self.error("Cola not found in drinks menu")
                    return False
            else:
                self.error(f"Failed to get drinks menu: {drinks_response.status_code}")
                return False
                
            # Get sweets menu
            sweets_response = requests.get(f"{API_BASE}/menu/sweets/{self.department_id}")
            if sweets_response.status_code == 200:
                sweets = sweets_response.json()
                for sweet in sweets:
                    if "Schokoriegel" in sweet["name"]:
                        self.schokoriegel_item_id = sweet["id"]
                        self.success(f"Found Schokoriegel item: {sweet['name']} (€{sweet['price']}) - ID: {sweet['id']}")
                        break
                
                if not self.schokoriegel_item_id:
                    self.error("Schokoriegel not found in sweets menu")
                    return False
            else:
                self.error(f"Failed to get sweets menu: {sweets_response.status_code}")
                return False
                
            return True
        except Exception as e:
            self.error(f"Exception getting menu items: {str(e)}")
            return False
            
    def get_employee_balance(self):
        """Get current employee balance"""
        try:
            response = requests.get(f"{API_BASE}/departments/{self.department_id}/employees")
            if response.status_code == 200:
                employees = response.json()
                for employee in employees:
                    if employee["id"] == self.test_employee_id:
                        return {
                            "breakfast_balance": employee["breakfast_balance"],
                            "drinks_sweets_balance": employee["drinks_sweets_balance"]
                        }
                self.error("Test employee not found in department employees")
                return None
            else:
                self.error(f"Failed to get employees: {response.status_code}")
                return None
        except Exception as e:
            self.error(f"Exception getting employee balance: {str(e)}")
            return None
            
    def test_drink_order_and_cancellation(self):
        """Test drink order creation and employee cancellation"""
        try:
            # Step 1: Check initial balance
            initial_balance = self.get_employee_balance()
            if initial_balance is None:
                return False
                
            self.log(f"Initial drinks/sweets balance: €{initial_balance['drinks_sweets_balance']}")
            
            # Step 2: Create drink order (Cola)
            order_data = {
                "employee_id": self.test_employee_id,
                "department_id": self.department_id,
                "order_type": "drinks",
                "drink_items": {
                    self.cola_item_id: 1  # 1 Cola
                }
            }
            
            self.log("Creating drink order (1x Cola)...")
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.drink_order_id = order["id"]
                total_price = order["total_price"]
                self.success(f"Created drink order (ID: {order['id']}, Total: €{total_price})")
                
                # Verify total_price is negative (drinks are stored as negative)
                if total_price < 0:
                    self.success(f"Drink order total_price is negative as expected: €{total_price}")
                else:
                    self.error(f"Drink order total_price should be negative, got: €{total_price}")
                    return False
            else:
                self.error(f"Failed to create drink order: {response.status_code} - {response.text}")
                return False
                
            # Step 3: Check balance after order
            after_order_balance = self.get_employee_balance()
            if after_order_balance is None:
                return False
                
            expected_balance = initial_balance["drinks_sweets_balance"] + total_price  # total_price is negative
            actual_balance = after_order_balance["drinks_sweets_balance"]
            
            self.log(f"Balance after drink order: €{actual_balance} (expected: €{expected_balance})")
            
            if abs(actual_balance - expected_balance) < 0.01:
                self.success(f"✅ STEP 1 VERIFIED: Drink order correctly updated balance to €{actual_balance}")
            else:
                self.error(f"Balance after drink order incorrect: expected €{expected_balance}, got €{actual_balance}")
                return False
                
            # Step 4: Cancel the drink order via employee endpoint
            self.log("Cancelling drink order via employee endpoint...")
            cancel_response = requests.delete(f"{API_BASE}/employee/{self.test_employee_id}/orders/{self.drink_order_id}")
            if cancel_response.status_code == 200:
                self.success("Drink order cancelled successfully")
            else:
                self.error(f"Failed to cancel drink order: {cancel_response.status_code} - {cancel_response.text}")
                return False
                
            # Step 5: Check balance after cancellation
            after_cancel_balance = self.get_employee_balance()
            if after_cancel_balance is None:
                return False
                
            final_balance = after_cancel_balance["drinks_sweets_balance"]
            expected_final = initial_balance["drinks_sweets_balance"]  # Should be back to initial
            
            self.log(f"Balance after drink cancellation: €{final_balance} (expected: €{expected_final})")
            
            if abs(final_balance - expected_final) < 0.01:
                self.success(f"🎯 CRITICAL SUCCESS: Drink cancellation correctly restored balance to €{final_balance}")
                self.success(f"✅ BUG FIX VERIFIED: Balance did NOT become -€{abs(total_price * 2)} (double negative)")
                return True
            else:
                self.error(f"🚨 CRITICAL BUG: Balance after cancellation incorrect!")
                self.error(f"Expected: €{expected_final}, Got: €{final_balance}")
                if abs(final_balance - (expected_final + total_price * 2)) < 0.01:
                    self.error(f"🚨 This looks like the OLD BUG: double negative effect!")
                return False
                
        except Exception as e:
            self.error(f"Exception in drink order and cancellation test: {str(e)}")
            return False
            
    def test_sweet_order_and_admin_cancellation(self):
        """Test sweet order creation and admin cancellation"""
        try:
            # Step 1: Check initial balance
            initial_balance = self.get_employee_balance()
            if initial_balance is None:
                return False
                
            self.log(f"Initial drinks/sweets balance: €{initial_balance['drinks_sweets_balance']}")
            
            # Step 2: Create sweet order (Schokoriegel)
            order_data = {
                "employee_id": self.test_employee_id,
                "department_id": self.department_id,
                "order_type": "sweets",
                "sweet_items": {
                    self.schokoriegel_item_id: 1  # 1 Schokoriegel
                }
            }
            
            self.log("Creating sweet order (1x Schokoriegel)...")
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.sweet_order_id = order["id"]
                total_price = order["total_price"]
                self.success(f"Created sweet order (ID: {order['id']}, Total: €{total_price})")
                
                # Verify total_price is negative (sweets are stored as negative)
                if total_price < 0:
                    self.success(f"Sweet order total_price is negative as expected: €{total_price}")
                else:
                    self.error(f"Sweet order total_price should be negative, got: €{total_price}")
                    return False
            else:
                self.error(f"Failed to create sweet order: {response.status_code} - {response.text}")
                return False
                
            # Step 3: Check balance after order
            after_order_balance = self.get_employee_balance()
            if after_order_balance is None:
                return False
                
            expected_balance = initial_balance["drinks_sweets_balance"] + total_price  # total_price is negative
            actual_balance = after_order_balance["drinks_sweets_balance"]
            
            self.log(f"Balance after sweet order: €{actual_balance} (expected: €{expected_balance})")
            
            if abs(actual_balance - expected_balance) < 0.01:
                self.success(f"✅ STEP 2 VERIFIED: Sweet order correctly updated balance to €{actual_balance}")
            else:
                self.error(f"Balance after sweet order incorrect: expected €{expected_balance}, got €{actual_balance}")
                return False
                
            # Step 4: Cancel the sweet order via admin endpoint
            self.log("Cancelling sweet order via admin endpoint...")
            cancel_response = requests.delete(f"{API_BASE}/department-admin/orders/{self.sweet_order_id}?admin_user=TestAdmin")
            if cancel_response.status_code == 200:
                self.success("Sweet order cancelled successfully by admin")
            else:
                self.error(f"Failed to cancel sweet order: {cancel_response.status_code} - {cancel_response.text}")
                return False
                
            # Step 5: Check balance after cancellation
            after_cancel_balance = self.get_employee_balance()
            if after_cancel_balance is None:
                return False
                
            final_balance = after_cancel_balance["drinks_sweets_balance"]
            expected_final = initial_balance["drinks_sweets_balance"]  # Should be back to initial
            
            self.log(f"Balance after sweet cancellation: €{final_balance} (expected: €{expected_final})")
            
            if abs(final_balance - expected_final) < 0.01:
                self.success(f"🎯 CRITICAL SUCCESS: Sweet admin cancellation correctly restored balance to €{final_balance}")
                self.success(f"✅ BUG FIX VERIFIED: Balance did NOT become -€{abs(total_price * 2)} (double negative)")
                return True
            else:
                self.error(f"🚨 CRITICAL BUG: Balance after admin cancellation incorrect!")
                self.error(f"Expected: €{expected_final}, Got: €{final_balance}")
                if abs(final_balance - (expected_final + total_price * 2)) < 0.01:
                    self.error(f"🚨 This looks like the OLD BUG: double negative effect!")
                return False
                
        except Exception as e:
            self.error(f"Exception in sweet order and admin cancellation test: {str(e)}")
            return False
            
    def test_breakfast_order_still_works(self):
        """Verify breakfast orders still work correctly (regression test)"""
        try:
            # Check initial balance
            initial_balance = self.get_employee_balance()
            if initial_balance is None:
                return False
                
            self.log(f"Initial breakfast balance: €{initial_balance['breakfast_balance']}")
            
            # Create a simple breakfast order
            order_data = {
                "employee_id": self.test_employee_id,
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["Rührei", "Spiegelei"],
                    "has_lunch": False,
                    "boiled_eggs": 0,
                    "fried_eggs": 0,
                    "has_coffee": False
                }]
            }
            
            self.log("Creating breakfast order for regression test...")
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                breakfast_order_id = order["id"]
                total_price = order["total_price"]
                self.success(f"Created breakfast order (ID: {order['id']}, Total: €{total_price})")
                
                # Verify total_price is positive (breakfast orders are positive)
                if total_price > 0:
                    self.success(f"Breakfast order total_price is positive as expected: €{total_price}")
                else:
                    self.error(f"Breakfast order total_price should be positive, got: €{total_price}")
                    return False
                    
                # Check balance after breakfast order
                after_order_balance = self.get_employee_balance()
                if after_order_balance is None:
                    return False
                    
                expected_balance = initial_balance["breakfast_balance"] - total_price  # Breakfast decreases balance
                actual_balance = after_order_balance["breakfast_balance"]
                
                if abs(actual_balance - expected_balance) < 0.01:
                    self.success(f"✅ REGRESSION TEST PASSED: Breakfast orders still work correctly (€{actual_balance})")
                    return True
                else:
                    self.error(f"Breakfast order balance incorrect: expected €{expected_balance}, got €{actual_balance}")
                    return False
            else:
                self.error(f"Failed to create breakfast order: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception in breakfast regression test: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete drinks/sweets cancellation bug test"""
        self.log("🎯 STARTING CRITICAL DRINKS/SWEETS CANCELLATION BUG VERIFICATION")
        self.log("=" * 80)
        self.log("BUG SCENARIO: Order drink €1.20 → balance -€1.20, cancel → should be €0 (NOT -€2.40)")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Admin Authentication", self.authenticate_admin),
            ("Create Test Employee", self.create_test_employee),
            ("Get Menu Items (Cola & Schokoriegel)", self.get_menu_items),
            ("Test Drink Order & Employee Cancellation", self.test_drink_order_and_cancellation),
            ("Test Sweet Order & Admin Cancellation", self.test_sweet_order_and_admin_cancellation),
            ("Test Breakfast Orders Still Work (Regression)", self.test_breakfast_order_still_works)
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        
        for step_name, step_function in test_steps:
            self.log(f"\n📋 Step {passed_tests + 1}/{total_tests}: {step_name}")
            self.log("-" * 50)
            
            if step_function():
                passed_tests += 1
                self.success(f"Step {passed_tests}/{total_tests} PASSED: {step_name}")
            else:
                self.error(f"Step {passed_tests + 1}/{total_tests} FAILED: {step_name}")
                # Continue with other tests even if one fails
                
        # Final results
        self.log("\n" + "=" * 80)
        if passed_tests == total_tests:
            self.success(f"🎉 CRITICAL DRINKS/SWEETS CANCELLATION BUG FIX VERIFICATION COMPLETED SUCCESSFULLY!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            self.log("\n🎯 CRITICAL VERIFICATION RESULTS:")
            self.log("✅ Drink order: balance correctly goes to negative")
            self.log("✅ Drink cancellation: balance correctly returns to zero (NOT double negative)")
            self.log("✅ Sweet order: balance correctly goes to negative")
            self.log("✅ Sweet admin cancellation: balance correctly returns to zero (NOT double negative)")
            self.log("✅ Breakfast orders: still work correctly (regression test passed)")
            self.log("✅ Lines ~2327 and ~3069 fix: subtraction instead of addition for drinks/sweets")
            return True
        else:
            self.error(f"❌ CRITICAL DRINKS/SWEETS CANCELLATION BUG FIX VERIFICATION FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            return False

def main():
    """Main test execution"""
    print("🧪 Critical Drinks/Sweets Cancellation Logic Bug Test")
    print("=" * 60)
    
    # Initialize and run test
    test_suite = DrinksSweetsCancellationTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - DRINKS/SWEETS CANCELLATION BUG IS FIXED!")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - DRINKS/SWEETS CANCELLATION BUG NEEDS ATTENTION!")
        exit(1)

if __name__ == "__main__":
    main()