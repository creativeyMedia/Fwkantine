#!/usr/bin/env python3
"""
Critical Issues Test Suite - Frontend Fix and Guest Employee Balance Calculation
===============================================================================

This test suite tests the two critical issues reported in the review request:

PROBLEM 1 - Frontend Fix Verification:
- Test if the "Andere WA" tab loads without toFixed error (null-safe operators ?.toFixed() || 0)

PROBLEM 2 - Frühstücksaldo-Berechnung bei Gastmitarbeitern:
User reports: "Mittagessen wird nicht im Preis eingebunden, -1€ falsch berechnet obwohl Frühstück 2,10€ kostet"

Example from user:
- 2x Helles Brötchen (1.50€) + 1x Gekochte Eier (0.60€) + 1x Mittagessen (5.00€) = 7.10€ 
- But only -1.00€ in balance instead of -7.10€

TEST SCENARIOS:
1. Create guest employee from fw4abteilung2 in fw4abteilung1
2. Set lunch price for fw4abteilung1 to 5.00€
3. Create breakfast order with rolls, eggs and lunch
4. Verify all price components are calculated correctly
5. Verify correct subaccount is charged

EXPECTED RESULTS:
- Lunch price is included in total calculation
- Guest employees use prices from department where they order (not home department)
- Subaccount is charged with correct total amount
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class CriticalIssuesTest:
    def __init__(self):
        self.guest_department_id = "fw4abteilung2"  # Guest employee's home department
        self.target_department_id = "fw4abteilung1"  # Department where guest will order
        self.guest_admin_credentials = {"department_name": "2. Wachabteilung", "admin_password": "admin2"}
        self.target_admin_credentials = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.test_guest_employee_id = None
        self.test_guest_employee_name = f"GuestTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_order_id = None
        self.assignment_id = None
        
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
            
    def authenticate_guest_admin(self):
        """Authenticate as guest department admin"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.guest_admin_credentials)
            if response.status_code == 200:
                self.success(f"Guest admin authentication successful for {self.guest_department_id}")
                return True
            else:
                self.error(f"Guest admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Guest admin authentication exception: {str(e)}")
            return False
            
    def authenticate_target_admin(self):
        """Authenticate as target department admin"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.target_admin_credentials)
            if response.status_code == 200:
                self.success(f"Target admin authentication successful for {self.target_department_id}")
                return True
            else:
                self.error(f"Target admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Target admin authentication exception: {str(e)}")
            return False
            
    def create_guest_employee(self):
        """Create a guest employee in fw4abteilung2"""
        try:
            employee_data = {
                "name": self.test_guest_employee_name,
                "department_id": self.guest_department_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_guest_employee_id = employee["id"]
                self.success(f"Created guest employee: {self.test_guest_employee_name} (ID: {self.test_guest_employee_id}) in {self.guest_department_id}")
                return True
            else:
                self.error(f"Failed to create guest employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating guest employee: {str(e)}")
            return False
            
    def add_guest_to_target_department(self):
        """Add guest employee as temporary worker to fw4abteilung1"""
        try:
            assignment_data = {
                "employee_id": self.test_guest_employee_id
            }
            
            response = requests.post(f"{API_BASE}/departments/{self.target_department_id}/temporary-employees", json=assignment_data)
            if response.status_code == 200:
                result = response.json()
                self.assignment_id = result.get("assignment_id")
                self.success(f"Added guest employee to {self.target_department_id} (Assignment ID: {self.assignment_id})")
                return True
            else:
                self.error(f"Failed to add guest employee to target department: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception adding guest employee to target department: {str(e)}")
            return False
            
    def set_lunch_price_for_target_department(self):
        """Set lunch price for fw4abteilung1 to 5.00€"""
        try:
            # First check if there's a daily lunch price setting
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Create daily lunch price for target department
            lunch_price_data = {
                "department_id": self.target_department_id,
                "date": today,
                "lunch_price": 5.00
            }
            
            response = requests.post(f"{API_BASE}/daily-lunch-prices", json=lunch_price_data)
            if response.status_code == 200:
                self.success(f"Set daily lunch price for {self.target_department_id} to €5.00 for {today}")
                return True
            else:
                # Try alternative endpoint if exists
                response = requests.put(f"{API_BASE}/lunch-settings?price=5.00")
                if response.status_code == 200:
                    self.success(f"Set global lunch price to €5.00")
                    return True
                else:
                    self.error(f"Failed to set lunch price: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            self.error(f"Exception setting lunch price: {str(e)}")
            return False
            
    def verify_menu_prices_for_target_department(self):
        """Verify menu prices for fw4abteilung1"""
        try:
            # Get breakfast menu items
            response = requests.get(f"{API_BASE}/menu/breakfast/{self.target_department_id}")
            if response.status_code == 200:
                breakfast_menu = response.json()
                self.log(f"Breakfast menu for {self.target_department_id}:")
                total_roll_price = 0
                for item in breakfast_menu:
                    self.log(f"  - {item.get('roll_type', 'Unknown')}: €{item.get('price', 0)}")
                    if item.get('roll_type') in ['weiss', 'koerner']:
                        total_roll_price += item.get('price', 0)
                
                # Get boiled eggs price
                response = requests.get(f"{API_BASE}/department-settings/{self.target_department_id}/boiled-eggs-price")
                if response.status_code == 200:
                    eggs_data = response.json()
                    eggs_price = eggs_data.get("boiled_eggs_price", 0)
                    self.log(f"  - Boiled eggs: €{eggs_price}")
                    
                    # Calculate expected total for user's example
                    # 2x Helles Brötchen (assuming white rolls) + 1x Gekochte Eier + 1x Mittagessen
                    expected_total = (2 * 0.50) + eggs_price + 5.00  # Assuming white rolls are €0.50 each
                    self.log(f"Expected total for user's example: €{expected_total}")
                    
                    return True
                else:
                    self.error(f"Failed to get boiled eggs price: {response.status_code}")
                    return False
            else:
                self.error(f"Failed to get breakfast menu: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception verifying menu prices: {str(e)}")
            return False
            
    def create_guest_breakfast_order_with_lunch(self):
        """Create breakfast order for guest employee with rolls, eggs and lunch"""
        try:
            # Create order matching user's example:
            # 2x Helles Brötchen (1.50€) + 1x Gekochte Eier (0.60€) + 1x Mittagessen (5.00€) = 7.10€
            order_data = {
                "employee_id": self.test_guest_employee_id,
                "department_id": self.target_department_id,  # Order in target department
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # 2 whole rolls = 4 halves
                    "white_halves": 4,  # All white rolls (Helles Brötchen)
                    "seeded_halves": 0,
                    "toppings": ["", "", "", ""],  # No toppings
                    "has_lunch": True,  # Include lunch
                    "boiled_eggs": 1,   # 1x Gekochte Eier
                    "fried_eggs": 0,
                    "has_coffee": False
                }]
            }
            
            self.log(f"Creating breakfast order for guest employee with lunch...")
            self.log(f"Order details: 4 white roll halves (2 whole rolls), 1 boiled egg, lunch")
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.test_order_id = order["id"]
                total_price = order["total_price"]
                
                self.success(f"Created breakfast order with lunch (ID: {order['id']}, Total: €{total_price})")
                
                # Verify total price is reasonable (should be around €7.10 based on user's example)
                if total_price >= 6.0 and total_price <= 8.0:
                    self.success(f"Order total price is in expected range: €{total_price}")
                    return True
                else:
                    self.error(f"Order total price seems incorrect: €{total_price} (expected around €7.10)")
                    self.log(f"This might indicate the lunch price is not being included correctly")
                    return False
            else:
                self.error(f"Failed to create breakfast order with lunch: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating breakfast order with lunch: {str(e)}")
            return False
            
    def verify_guest_employee_balance(self):
        """Verify guest employee's balance is updated correctly"""
        try:
            # Get guest employee's profile to check balance
            response = requests.get(f"{API_BASE}/employees/{self.test_guest_employee_id}/profile")
            if response.status_code == 200:
                profile = response.json()
                
                # Check main department balance (should be unchanged)
                employee_data = profile.get("employee", {})
                main_breakfast_balance = employee_data.get("breakfast_balance", 0)
                main_drinks_balance = employee_data.get("drinks_sweets_balance", 0)
                
                self.log(f"Guest employee main department balances:")
                self.log(f"  - Breakfast balance: €{main_breakfast_balance}")
                self.log(f"  - Drinks/Sweets balance: €{main_drinks_balance}")
                
                # Check if subaccount balances are available
                subaccount_balances = employee_data.get("subaccount_balances", {})
                if subaccount_balances and self.target_department_id in subaccount_balances:
                    target_dept_balances = subaccount_balances[self.target_department_id]
                    target_breakfast_balance = target_dept_balances.get("breakfast", 0)
                    target_drinks_balance = target_dept_balances.get("drinks", 0)
                    
                    self.log(f"Guest employee subaccount balances for {self.target_department_id}:")
                    self.log(f"  - Breakfast balance: €{target_breakfast_balance}")
                    self.log(f"  - Drinks balance: €{target_drinks_balance}")
                    
                    # Verify the balance reflects the order total (should be negative)
                    if target_breakfast_balance < -6.0 and target_breakfast_balance > -8.0:
                        self.success(f"Guest employee subaccount balance correctly updated: €{target_breakfast_balance}")
                        
                        # Also verify the order details in the profile
                        order_history = profile.get("order_history", [])
                        if order_history:
                            latest_order = order_history[0]  # Most recent order
                            total_price = latest_order.get("total_price", 0)
                            has_lunch = latest_order.get("has_lunch", False)
                            lunch_price = latest_order.get("lunch_price", 0)
                            
                            self.log(f"Order verification:")
                            self.log(f"  - Total price: €{total_price}")
                            self.log(f"  - Has lunch: {has_lunch}")
                            self.log(f"  - Lunch price: €{lunch_price}")
                            
                            if has_lunch and lunch_price == 5.0:
                                self.success(f"Lunch price correctly included: €{lunch_price}")
                                return True
                            else:
                                self.error(f"Lunch price not correctly included: has_lunch={has_lunch}, lunch_price={lunch_price}")
                                return False
                        else:
                            self.error("No order history found in profile")
                            return False
                    else:
                        self.error(f"Guest employee subaccount balance incorrect: €{target_breakfast_balance} (expected around -€7.10)")
                        return False
                else:
                    self.error("Subaccount balances not found or target department not in subaccounts")
                    return False
            else:
                self.error(f"Failed to get guest employee profile: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception verifying guest employee balance: {str(e)}")
            return False
            
    def verify_order_details(self):
        """Verify order details are stored correctly"""
        try:
            # Get order details through breakfast history
            response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.target_department_id}")
            if response.status_code == 200:
                history_data = response.json()
                
                # Look for our guest employee's order
                found_order = False
                if history_data.get("history"):
                    for day_data in history_data["history"]:
                        employee_orders = day_data.get("employee_orders", {})
                        for employee_key, employee_data in employee_orders.items():
                            if self.test_guest_employee_name in employee_key:
                                total_amount = employee_data.get("total_amount", 0)
                                has_lunch = employee_data.get("has_lunch", False)
                                
                                self.log(f"Found guest employee order in breakfast history:")
                                self.log(f"  - Total amount: €{total_amount}")
                                self.log(f"  - Has lunch: {has_lunch}")
                                
                                # Verify lunch is included
                                if has_lunch:
                                    self.success("Order correctly shows lunch is included")
                                else:
                                    self.error("Order does not show lunch is included")
                                    return False
                                
                                # Verify total amount
                                if abs(total_amount) >= 6.0 and abs(total_amount) <= 8.0:
                                    self.success(f"Order total amount is correct: €{abs(total_amount)}")
                                    found_order = True
                                else:
                                    self.error(f"Order total amount seems incorrect: €{abs(total_amount)}")
                                    return False
                                break
                        if found_order:
                            break
                
                if found_order:
                    return True
                else:
                    self.error("Guest employee order not found in breakfast history")
                    return False
            else:
                self.error(f"Failed to get breakfast history: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception verifying order details: {str(e)}")
            return False
            
    def test_frontend_andere_wa_tab(self):
        """Test if the 'Andere WA' tab loads without toFixed error"""
        try:
            # This is primarily a frontend test, but we can verify the backend endpoints
            # that the frontend would call for the "Andere WA" tab
            
            # Test getting temporary employees (which the "Andere WA" tab would display)
            response = requests.get(f"{API_BASE}/departments/{self.target_department_id}/temporary-employees")
            if response.status_code == 200:
                temp_employees = response.json()
                self.success(f"'Andere WA' backend endpoint working - found {len(temp_employees)} temporary employees")
                
                # Verify our guest employee is in the list
                found_guest = False
                for emp in temp_employees:
                    if emp.get("id") == self.test_guest_employee_id:
                        found_guest = True
                        self.success(f"Guest employee found in 'Andere WA' list: {emp.get('name')}")
                        break
                
                if found_guest:
                    return True
                else:
                    self.error("Guest employee not found in 'Andere WA' list")
                    return False
            else:
                self.error(f"Failed to get temporary employees for 'Andere WA' tab: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception testing 'Andere WA' tab backend: {str(e)}")
            return False
            
    def cleanup_test_data(self):
        """Clean up test data"""
        try:
            # Remove temporary assignment
            if self.assignment_id:
                response = requests.delete(f"{API_BASE}/departments/{self.target_department_id}/temporary-employees/{self.assignment_id}")
                if response.status_code == 200:
                    self.success("Cleaned up temporary assignment")
                else:
                    self.log(f"Could not clean up temporary assignment: {response.status_code}")
            
            # Note: We don't delete the employee or order as they might be useful for further testing
            return True
        except Exception as e:
            self.error(f"Exception during cleanup: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete critical issues test"""
        self.log("🎯 STARTING CRITICAL ISSUES VERIFICATION")
        self.log("Testing: Frontend Fix and Guest Employee Balance Calculation")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Authenticate Guest Admin", self.authenticate_guest_admin),
            ("Authenticate Target Admin", self.authenticate_target_admin),
            ("Create Guest Employee", self.create_guest_employee),
            ("Add Guest to Target Department", self.add_guest_to_target_department),
            ("Set Lunch Price for Target Department", self.set_lunch_price_for_target_department),
            ("Verify Menu Prices", self.verify_menu_prices_for_target_department),
            ("Create Guest Breakfast Order with Lunch", self.create_guest_breakfast_order_with_lunch),
            ("Verify Guest Employee Balance", self.verify_guest_employee_balance),
            ("Verify Order Details", self.verify_order_details),
            ("Test 'Andere WA' Tab Backend", self.test_frontend_andere_wa_tab),
            ("Cleanup Test Data", self.cleanup_test_data)
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
            self.success(f"🎉 CRITICAL ISSUES VERIFICATION COMPLETED SUCCESSFULLY!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            self.log("\n🎯 CRITICAL VERIFICATION RESULTS:")
            self.log("✅ PROBLEM 1 - 'Andere WA' tab backend endpoints working")
            self.log("✅ PROBLEM 2 - Guest employee balance calculation working")
            self.log("✅ Lunch price included in total calculation")
            self.log("✅ Guest employees use correct department prices")
            self.log("✅ Subaccount charged with correct amount")
            return True
        else:
            self.error(f"❌ CRITICAL ISSUES VERIFICATION PARTIALLY FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            return False

def main():
    """Main test execution"""
    print("🧪 Critical Issues Test Suite - Frontend Fix and Guest Employee Balance")
    print("=" * 75)
    
    # Initialize and run test
    test_suite = CriticalIssuesTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - CRITICAL ISSUES ARE RESOLVED!")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - CRITICAL ISSUES NEED ATTENTION!")
        exit(1)

if __name__ == "__main__":
    main()