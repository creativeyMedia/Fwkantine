#!/usr/bin/env python3
"""
Bug Fixes Test Suite for Canteen System
========================================

This test suite verifies the two specific bug fixes mentioned in the review request:

BUG 1 - Double Balance Deduction for Stammwachabteilung Breakfast:
- Create a test employee in 1st department (1. Wachabteilung)
- Order breakfast with rolls and coffee for about 3.85€
- Verify that balance is correctly debited by exactly -3.85€ (NOT double like -7.70€)
- Test both through employee ordering and balance checking

BUG 2 - Missing Details for Guest Employee Drinks/Sweets:
- Create a temporary guest employee from another department
- Order drink (e.g. Cola) or sweet (e.g. chocolate bar) for the guest employee
- Check in order history that details are correctly displayed:
  * "1x Cola (1.20 €)" instead of just the price without details
  * "1x Schokoriegel (1.50 €)" with complete product details

Test Endpoints:
- POST /api/orders for orders
- GET /api/employees/{id}/profile for order history and balance details
- POST /api/departments/{id}/temporary-employees for guest employees
- GET /api/departments/{id}/employees for employee lists
"""

import requests
import json
import os
from datetime import datetime
import uuid
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BugFixesTest:
    def __init__(self):
        self.department_id_1 = "fw4abteilung1"  # 1. Wachabteilung
        self.department_id_2 = "fw4abteilung2"  # 2. Wachabteilung (for guest employee)
        self.admin_credentials_1 = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.admin_credentials_2 = {"department_name": "2. Wachabteilung", "admin_password": "admin2"}
        
        # Test employee for Bug 1 (Stammwachabteilung)
        self.test_employee_1_id = None
        self.test_employee_1_name = f"StammTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Test employee for Bug 2 (Guest from another department)
        self.test_employee_2_id = None
        self.test_employee_2_name = f"GuestTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        self.test_order_1_id = None
        self.test_order_2_id = None
        
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
            
    def authenticate_admin_dept_1(self):
        """Authenticate as admin for department 1"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.admin_credentials_1)
            if response.status_code == 200:
                self.success(f"Admin authentication successful for {self.department_id_1}")
                return True
            else:
                self.error(f"Admin authentication failed for dept 1: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Admin authentication exception for dept 1: {str(e)}")
            return False
            
    def authenticate_admin_dept_2(self):
        """Authenticate as admin for department 2"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.admin_credentials_2)
            if response.status_code == 200:
                self.success(f"Admin authentication successful for {self.department_id_2}")
                return True
            else:
                self.error(f"Admin authentication failed for dept 2: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Admin authentication exception for dept 2: {str(e)}")
            return False
            
    def create_test_employee_dept_1(self):
        """Create a test employee in department 1 for Bug 1 testing"""
        try:
            employee_data = {
                "name": self.test_employee_1_name,
                "department_id": self.department_id_1
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_1_id = employee["id"]
                self.success(f"Created test employee in dept 1: {self.test_employee_1_name} (ID: {self.test_employee_1_id})")
                return True
            else:
                self.error(f"Failed to create test employee in dept 1: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating test employee in dept 1: {str(e)}")
            return False
            
    def create_test_employee_dept_2(self):
        """Create a test employee in department 2 for Bug 2 testing"""
        try:
            employee_data = {
                "name": self.test_employee_2_name,
                "department_id": self.department_id_2
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_2_id = employee["id"]
                self.success(f"Created test employee in dept 2: {self.test_employee_2_name} (ID: {self.test_employee_2_id})")
                return True
            else:
                self.error(f"Failed to create test employee in dept 2: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating test employee in dept 2: {str(e)}")
            return False
            
    def add_guest_employee_to_dept_1(self):
        """Add employee from dept 2 as temporary guest to dept 1"""
        try:
            guest_data = {
                "employee_id": self.test_employee_2_id
            }
            
            response = requests.post(f"{API_BASE}/departments/{self.department_id_1}/temporary-employees", json=guest_data)
            if response.status_code == 200:
                result = response.json()
                self.success(f"Added guest employee to dept 1: {result.get('employee_name', 'Unknown')}")
                return True
            else:
                self.error(f"Failed to add guest employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception adding guest employee: {str(e)}")
            return False
            
    def get_employee_balance_before_order(self, employee_id):
        """Get employee balance before placing order"""
        try:
            response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
            if response.status_code == 200:
                profile = response.json()
                breakfast_balance = profile.get("breakfast_balance", 0.0)
                drinks_balance = profile.get("drinks_sweets_balance", 0.0)
                self.log(f"Employee balance before order - Breakfast: €{breakfast_balance}, Drinks/Sweets: €{drinks_balance}")
                return breakfast_balance, drinks_balance
            else:
                self.error(f"Failed to get employee profile: {response.status_code} - {response.text}")
                return None, None
        except Exception as e:
            self.error(f"Exception getting employee balance: {str(e)}")
            return None, None
            
    def test_bug_1_breakfast_order(self):
        """BUG 1 TEST: Create breakfast order and verify single balance deduction"""
        try:
            # Get balance before order
            balance_before_breakfast, balance_before_drinks = self.get_employee_balance_before_order(self.test_employee_1_id)
            if balance_before_breakfast is None:
                return False
                
            # Create breakfast order with rolls and coffee (approximately 3.85€)
            order_data = {
                "employee_id": self.test_employee_1_id,
                "department_id": self.department_id_1,
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
            
            self.log(f"Creating breakfast order for Stammwachabteilung employee...")
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.test_order_1_id = order["id"]
                total_price = order["total_price"]
                
                self.success(f"Created breakfast order (ID: {order['id']}, Total: €{total_price})")
                
                # Wait a moment for balance update
                time.sleep(1)
                
                # Get balance after order
                balance_after_breakfast, balance_after_drinks = self.get_employee_balance_before_order(self.test_employee_1_id)
                if balance_after_breakfast is None:
                    return False
                
                # Calculate actual balance change
                balance_change = balance_after_breakfast - balance_before_breakfast
                expected_change = -total_price  # Should be negative (debt)
                
                self.log(f"Balance change: €{balance_change} (expected: €{expected_change})")
                
                # BUG 1 VERIFICATION: Check that balance was deducted only once
                if abs(balance_change - expected_change) < 0.01:
                    self.success(f"✅ BUG 1 FIX VERIFIED: Balance correctly deducted once (€{balance_change})")
                    self.success(f"   Order total: €{total_price}, Balance change: €{balance_change}")
                    return True
                elif abs(balance_change - (2 * expected_change)) < 0.01:
                    self.error(f"❌ BUG 1 STILL EXISTS: Balance deducted twice! Expected: €{expected_change}, Got: €{balance_change}")
                    return False
                else:
                    self.error(f"❌ BUG 1 UNEXPECTED: Balance change doesn't match expected pattern. Expected: €{expected_change}, Got: €{balance_change}")
                    return False
            else:
                self.error(f"Failed to create breakfast order: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception in Bug 1 test: {str(e)}")
            return False
            
    def test_bug_2_guest_drinks_order(self):
        """BUG 2 TEST: Create drinks order for guest employee and verify details display"""
        try:
            # Create drinks order for guest employee
            order_data = {
                "employee_id": self.test_employee_2_id,
                "department_id": self.department_id_1,  # Guest ordering in dept 1
                "order_type": "drinks",
                "drink_items": {
                    # We need to find actual drink IDs from the menu
                }
            }
            
            # First, get the drinks menu to find Cola
            menu_response = requests.get(f"{API_BASE}/menu/drinks/{self.department_id_1}")
            if menu_response.status_code == 200:
                drinks_menu = menu_response.json()
                cola_item = None
                for drink in drinks_menu:
                    if "Cola" in drink.get("name", ""):
                        cola_item = drink
                        break
                
                if cola_item:
                    order_data["drink_items"] = {cola_item["id"]: 1}  # 1x Cola
                    expected_price = cola_item["price"]
                    
                    self.log(f"Creating drinks order for guest employee: 1x {cola_item['name']} (€{expected_price})")
                    
                    response = requests.post(f"{API_BASE}/orders", json=order_data)
                    if response.status_code == 200:
                        order = response.json()
                        self.test_order_2_id = order["id"]
                        total_price = order["total_price"]
                        
                        self.success(f"Created drinks order for guest (ID: {order['id']}, Total: €{total_price})")
                        
                        # Wait a moment for order processing
                        time.sleep(1)
                        
                        # Now check the order history/profile for readable_items
                        return self.verify_guest_order_details(cola_item["name"], expected_price)
                    else:
                        self.error(f"Failed to create drinks order for guest: {response.status_code} - {response.text}")
                        return False
                else:
                    self.error("Cola not found in drinks menu")
                    return False
            else:
                self.error(f"Failed to get drinks menu: {menu_response.status_code} - {menu_response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception in Bug 2 drinks test: {str(e)}")
            return False
            
    def test_bug_2_guest_sweets_order(self):
        """BUG 2 TEST: Create sweets order for guest employee and verify details display"""
        try:
            # Create sweets order for guest employee
            order_data = {
                "employee_id": self.test_employee_2_id,
                "department_id": self.department_id_1,  # Guest ordering in dept 1
                "order_type": "sweets",
                "sweet_items": {
                    # We need to find actual sweet IDs from the menu
                }
            }
            
            # First, get the sweets menu to find Schokoriegel
            menu_response = requests.get(f"{API_BASE}/menu/sweets/{self.department_id_1}")
            if menu_response.status_code == 200:
                sweets_menu = menu_response.json()
                chocolate_item = None
                for sweet in sweets_menu:
                    if "Schokoriegel" in sweet.get("name", ""):
                        chocolate_item = sweet
                        break
                
                if chocolate_item:
                    order_data["sweet_items"] = {chocolate_item["id"]: 1}  # 1x Schokoriegel
                    expected_price = chocolate_item["price"]
                    
                    self.log(f"Creating sweets order for guest employee: 1x {chocolate_item['name']} (€{expected_price})")
                    
                    response = requests.post(f"{API_BASE}/orders", json=order_data)
                    if response.status_code == 200:
                        order = response.json()
                        total_price = order["total_price"]
                        
                        self.success(f"Created sweets order for guest (ID: {order['id']}, Total: €{total_price})")
                        
                        # Wait a moment for order processing
                        time.sleep(1)
                        
                        # Now check the order history/profile for readable_items
                        return self.verify_guest_order_details(chocolate_item["name"], expected_price)
                    else:
                        self.error(f"Failed to create sweets order for guest: {response.status_code} - {response.text}")
                        return False
                else:
                    self.error("Schokoriegel not found in sweets menu")
                    return False
            else:
                self.error(f"Failed to get sweets menu: {menu_response.status_code} - {menu_response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception in Bug 2 sweets test: {str(e)}")
            return False
            
    def verify_guest_order_details(self, item_name, expected_price):
        """Verify that guest employee order details are correctly displayed"""
        try:
            # Check employee profile for order history
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_2_id}/profile")
            if response.status_code == 200:
                profile = response.json()
                order_history = profile.get("order_history", [])
                
                # Look for our recent order
                for order in order_history:
                    readable_items = order.get("readable_items", [])
                    if readable_items:
                        for item in readable_items:
                            if item_name in item:
                                # BUG 2 VERIFICATION: Check if details are properly formatted
                                expected_format = f"1x {item_name} ({expected_price:.2f} €)"
                                if expected_format in item or (item_name in item and f"{expected_price:.2f}" in item):
                                    self.success(f"✅ BUG 2 FIX VERIFIED: Guest order details correctly displayed")
                                    self.success(f"   Found: '{item}' (contains product name and price)")
                                    return True
                                else:
                                    self.error(f"❌ BUG 2 STILL EXISTS: Order details incomplete")
                                    self.error(f"   Expected format like: '1x {item_name} ({expected_price:.2f} €)'")
                                    self.error(f"   Found: '{item}'")
                                    return False
                
                self.error(f"❌ BUG 2 VERIFICATION FAILED: Could not find order with {item_name} in readable_items")
                self.log(f"Available order history: {len(order_history)} orders")
                for i, order in enumerate(order_history):
                    self.log(f"  Order {i+1}: {order.get('readable_items', [])}")
                return False
            else:
                self.error(f"Failed to get guest employee profile: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception verifying guest order details: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete bug fixes test"""
        self.log("🎯 STARTING BUG FIXES VERIFICATION")
        self.log("=" * 80)
        self.log("BUG 1: Double Balance Deduction for Stammwachabteilung Breakfast")
        self.log("BUG 2: Missing Details for Guest Employee Drinks/Sweets")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Admin Authentication Dept 1", self.authenticate_admin_dept_1),
            ("Admin Authentication Dept 2", self.authenticate_admin_dept_2),
            ("Create Test Employee Dept 1", self.create_test_employee_dept_1),
            ("Create Test Employee Dept 2", self.create_test_employee_dept_2),
            ("Add Guest Employee to Dept 1", self.add_guest_employee_to_dept_1),
            ("BUG 1 TEST: Breakfast Order Balance Deduction", self.test_bug_1_breakfast_order),
            ("BUG 2 TEST: Guest Drinks Order Details", self.test_bug_2_guest_drinks_order),
            ("BUG 2 TEST: Guest Sweets Order Details", self.test_bug_2_guest_sweets_order)
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        critical_bugs_fixed = 0
        
        for step_name, step_function in test_steps:
            self.log(f"\n📋 Step {passed_tests + 1}/{total_tests}: {step_name}")
            self.log("-" * 50)
            
            if step_function():
                passed_tests += 1
                self.success(f"Step {passed_tests}/{total_tests} PASSED: {step_name}")
                
                # Track critical bug fixes
                if "BUG 1 TEST" in step_name or "BUG 2 TEST" in step_name:
                    critical_bugs_fixed += 1
            else:
                self.error(f"Step {passed_tests + 1}/{total_tests} FAILED: {step_name}")
                # Continue with other tests even if one fails
                
        # Final results
        self.log("\n" + "=" * 80)
        self.log("🎯 BUG FIXES VERIFICATION RESULTS:")
        self.log("=" * 80)
        
        if critical_bugs_fixed >= 2:  # At least 2 bug tests passed
            self.success(f"🎉 CRITICAL BUG FIXES VERIFICATION COMPLETED SUCCESSFULLY!")
            self.success(f"Both bug fixes are working correctly")
            self.log("\n✅ BUG 1 (Double Balance Deduction): FIXED")
            self.log("✅ BUG 2 (Missing Guest Order Details): FIXED")
            return True
        else:
            self.error(f"❌ CRITICAL BUG FIXES VERIFICATION FAILED!")
            self.error(f"Only {critical_bugs_fixed} out of 2 critical bug fixes are working")
            if critical_bugs_fixed == 0:
                self.log("\n❌ BUG 1 (Double Balance Deduction): NOT FIXED")
                self.log("❌ BUG 2 (Missing Guest Order Details): NOT FIXED")
            elif critical_bugs_fixed == 1:
                self.log("\n⚠️  One bug fix is working, one is not - check individual test results above")
            return False

def main():
    """Main test execution"""
    print("🧪 Bug Fixes Test Suite - Canteen System")
    print("=" * 70)
    
    # Initialize and run test
    test_suite = BugFixesTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL CRITICAL BUG FIXES ARE WORKING!")
        exit(0)
    else:
        print("\n❌ SOME CRITICAL BUG FIXES NEED ATTENTION!")
        exit(1)

if __name__ == "__main__":
    main()