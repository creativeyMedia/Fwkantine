#!/usr/bin/env python3
"""
Retroactive Lunch Price Adjustment Bug Test for Guest Employees
==============================================================

This test suite specifically tests the user-reported bug:
"Das rückwirkende Mittagessen preisanpassen funktioniert noch immer nicht korrekt."

PROBLEM ANALYSIS:
- For regular employees (Stammmitarbeiter): Works correctly
- For guest employees (Gastmitarbeiter): Total is changed, but subaccount balance is not updated
- Suspicion: Lunch price adjustment goes to main account instead of subaccount

TEST SCENARIO:
1. Create guest employee order:
   - Guest employee from fw4abteilung2
   - Add temporarily to fw4abteilung1
   - Create breakfast order with lunch (e.g. 6.00€)
   - Check initial subaccount balance

2. Test retroactive lunch price change:
   - Set lunch price for fw4abteilung1 from 6.00€ to 5.00€
   - Check order: total_price should be reduced by -1.00€
   - Check guest employee subaccount: breakfast balance should improve by +1.00€
   - Check guest employee main account: SHOULD REMAIN UNCHANGED

3. Compare with regular employee:
   - Create regular employee order
   - Test same lunch price change
   - Document the difference
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class RetroactiveLunchPriceTest:
    def __init__(self):
        self.dept1_id = "fw4abteilung1"  # Target department for guest orders
        self.dept2_id = "fw4abteilung2"  # Home department for guest employee
        self.dept1_admin = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.dept2_admin = {"department_name": "2. Wachabteilung", "admin_password": "admin2"}
        
        # Test employees
        self.guest_employee_id = None
        self.guest_employee_name = f"GastTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.regular_employee_id = None
        self.regular_employee_name = f"StammTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Test orders
        self.guest_order_id = None
        self.regular_order_id = None
        
        # Test data tracking
        self.initial_lunch_price = 6.00
        self.new_lunch_price = 5.00
        self.expected_difference = -1.00  # Price reduction
        
        # Track actual order prices
        self.guest_order_initial_total = None
        self.regular_order_initial_total = None
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        
    def debug(self, message):
        """Log debug information"""
        print(f"🔍 DEBUG: {message}")
        
    def test_init_data(self):
        """Initialize data to ensure departments exist"""
        try:
            response = requests.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.success("Data initialization successful")
                return True
            else:
                self.log(f"Init data response: {response.status_code} - {response.text}")
                return True  # May fail if data exists, which is OK
        except Exception as e:
            self.error(f"Exception during data initialization: {str(e)}")
            return False
            
    def authenticate_dept1_admin(self):
        """Authenticate as department 1 admin"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.dept1_admin)
            if response.status_code == 200:
                self.success(f"Department 1 admin authentication successful")
                return True
            else:
                self.error(f"Department 1 admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Department 1 admin authentication exception: {str(e)}")
            return False
            
    def authenticate_dept2_admin(self):
        """Authenticate as department 2 admin"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.dept2_admin)
            if response.status_code == 200:
                self.success(f"Department 2 admin authentication successful")
                return True
            else:
                self.error(f"Department 2 admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Department 2 admin authentication exception: {str(e)}")
            return False
            
    def create_guest_employee(self):
        """Create guest employee in fw4abteilung2 (home department)"""
        try:
            employee_data = {
                "name": self.guest_employee_name,
                "department_id": self.dept2_id,  # Home department
                "is_guest": False  # Regular employee in home dept
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.guest_employee_id = employee["id"]
                self.success(f"Created guest employee: {self.guest_employee_name} (ID: {self.guest_employee_id}) in {self.dept2_id}")
                return True
            else:
                self.error(f"Failed to create guest employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating guest employee: {str(e)}")
            return False
            
    def create_regular_employee(self):
        """Create regular employee in fw4abteilung1"""
        try:
            employee_data = {
                "name": self.regular_employee_name,
                "department_id": self.dept1_id,  # Home department
                "is_guest": False
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.regular_employee_id = employee["id"]
                self.success(f"Created regular employee: {self.regular_employee_name} (ID: {self.regular_employee_id}) in {self.dept1_id}")
                return True
            else:
                self.error(f"Failed to create regular employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating regular employee: {str(e)}")
            return False
            
    def add_guest_employee_temporarily(self):
        """Add guest employee temporarily to fw4abteilung1"""
        try:
            assignment_data = {
                "employee_id": self.guest_employee_id
            }
            
            response = requests.post(f"{API_BASE}/departments/{self.dept1_id}/temporary-employees", json=assignment_data)
            if response.status_code == 200:
                result = response.json()
                self.success(f"Added guest employee temporarily to {self.dept1_id}: {result.get('message')}")
                return True
            else:
                self.error(f"Failed to add guest employee temporarily: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception adding guest employee temporarily: {str(e)}")
            return False
            
    def set_initial_lunch_price(self):
        """Set initial lunch price to 6.00€ globally (affects all departments)"""
        try:
            # First check current lunch price
            response = requests.get(f"{API_BASE}/lunch-settings")
            if response.status_code == 200:
                current_settings = response.json()
                current_price = current_settings.get("price", 0.0)
                self.debug(f"Current global lunch price: €{current_price}")
            
            # Set new lunch price globally
            response = requests.put(f"{API_BASE}/lunch-settings?price={self.initial_lunch_price}")
            if response.status_code == 200:
                result = response.json()
                updated_orders = result.get("updated_orders", 0)
                self.success(f"Set initial lunch price to €{self.initial_lunch_price} globally")
                self.debug(f"Updated {updated_orders} existing orders")
                return True
            else:
                self.error(f"Failed to set initial lunch price: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception setting initial lunch price: {str(e)}")
            return False
            
    def create_guest_employee_order(self):
        """Create breakfast order with lunch for guest employee in fw4abteilung1"""
        try:
            order_data = {
                "employee_id": self.guest_employee_id,
                "department_id": self.dept1_id,  # Guest order in dept1
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["Rührei", "Spiegelei"],
                    "has_lunch": True,  # CRITICAL: Include lunch
                    "boiled_eggs": 0,
                    "fried_eggs": 0,
                    "has_coffee": False
                }]
            }
            
            self.log(f"Creating guest employee order with lunch in {self.dept1_id}")
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.guest_order_id = order["id"]
                total_price = order["total_price"]
                self.guest_order_initial_total = total_price
                
                self.success(f"Created guest employee order (ID: {order['id']}, Total: €{total_price})")
                self.debug(f"Guest order details: {json.dumps(order, indent=2)}")
                return True
            else:
                self.error(f"Failed to create guest employee order: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating guest employee order: {str(e)}")
            return False
            
    def create_regular_employee_order(self):
        """Create breakfast order with lunch for regular employee in fw4abteilung1"""
        try:
            order_data = {
                "employee_id": self.regular_employee_id,
                "department_id": self.dept1_id,  # Regular order in home dept
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["Rührei", "Spiegelei"],
                    "has_lunch": True,  # CRITICAL: Include lunch
                    "boiled_eggs": 0,
                    "fried_eggs": 0,
                    "has_coffee": False
                }]
            }
            
            self.log(f"Creating regular employee order with lunch in {self.dept1_id}")
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.regular_order_id = order["id"]
                total_price = order["total_price"]
                self.regular_order_initial_total = total_price
                
                self.success(f"Created regular employee order (ID: {order['id']}, Total: €{total_price})")
                self.debug(f"Regular order details: {json.dumps(order, indent=2)}")
                return True
            else:
                self.error(f"Failed to create regular employee order: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating regular employee order: {str(e)}")
            return False
            
    def get_employee_balances_before(self):
        """Get employee balances before price change"""
        try:
            # Get guest employee balances
            response = requests.get(f"{API_BASE}/employees/{self.guest_employee_id}/all-balances")
            if response.status_code == 200:
                guest_balances = response.json()
                self.guest_balances_before = guest_balances
                
                self.debug(f"Guest employee balances BEFORE price change:")
                self.debug(f"  Main account ({self.dept2_id}): Breakfast: €{guest_balances['main_balances']['breakfast']}")
                self.debug(f"  Subaccount ({self.dept1_id}): Breakfast: €{guest_balances['subaccount_balances'].get(self.dept1_id, {}).get('breakfast', 0.0)}")
            else:
                self.error(f"Failed to get guest employee balances: {response.status_code}")
                return False
                
            # Get regular employee balances
            response = requests.get(f"{API_BASE}/employees/{self.regular_employee_id}/all-balances")
            if response.status_code == 200:
                regular_balances = response.json()
                self.regular_balances_before = regular_balances
                
                self.debug(f"Regular employee balances BEFORE price change:")
                self.debug(f"  Main account ({self.dept1_id}): Breakfast: €{regular_balances['main_balances']['breakfast']}")
            else:
                self.error(f"Failed to get regular employee balances: {response.status_code}")
                return False
                
            return True
        except Exception as e:
            self.error(f"Exception getting employee balances before: {str(e)}")
            return False
            
    def apply_retroactive_lunch_price_change(self):
        """Apply retroactive lunch price change from 6.00€ to 5.00€"""
        try:
            self.log(f"Applying retroactive lunch price change: €{self.initial_lunch_price} → €{self.new_lunch_price}")
            
            response = requests.put(f"{API_BASE}/lunch-settings?price={self.new_lunch_price}&department_id={self.dept1_id}")
            if response.status_code == 200:
                result = response.json()
                updated_orders = result.get("updated_orders", 0)
                
                self.success(f"Applied retroactive lunch price change: €{self.new_lunch_price}")
                self.success(f"Updated {updated_orders} orders retroactively")
                return True
            else:
                self.error(f"Failed to apply retroactive lunch price change: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception applying retroactive lunch price change: {str(e)}")
            return False
            
    def verify_order_price_changes(self):
        """Verify that order total_price was updated correctly"""
        try:
            # Check guest employee order
            response = requests.get(f"{API_BASE}/employees/{self.guest_employee_id}/profile")
            if response.status_code == 200:
                profile = response.json()
                orders = profile.get("orders", [])
                
                guest_order = None
                for order in orders:
                    if order["id"] == self.guest_order_id:
                        guest_order = order
                        break
                        
                if guest_order:
                    new_total = guest_order["total_price"]
                    self.debug(f"Guest order new total_price: €{new_total}")
                    self.guest_order_new_total = new_total
                else:
                    self.error("Guest order not found in profile")
                    return False
            else:
                self.error(f"Failed to get guest employee profile: {response.status_code}")
                return False
                
            # Check regular employee order
            response = requests.get(f"{API_BASE}/employees/{self.regular_employee_id}/profile")
            if response.status_code == 200:
                profile = response.json()
                orders = profile.get("orders", [])
                
                regular_order = None
                for order in orders:
                    if order["id"] == self.regular_order_id:
                        regular_order = order
                        break
                        
                if regular_order:
                    new_total = regular_order["total_price"]
                    self.debug(f"Regular order new total_price: €{new_total}")
                    self.regular_order_new_total = new_total
                else:
                    self.error("Regular order not found in profile")
                    return False
            else:
                self.error(f"Failed to get regular employee profile: {response.status_code}")
                return False
                
            return True
        except Exception as e:
            self.error(f"Exception verifying order price changes: {str(e)}")
            return False
            
    def get_employee_balances_after(self):
        """Get employee balances after price change"""
        try:
            # Get guest employee balances
            response = requests.get(f"{API_BASE}/employees/{self.guest_employee_id}/all-balances")
            if response.status_code == 200:
                guest_balances = response.json()
                self.guest_balances_after = guest_balances
                
                self.debug(f"Guest employee balances AFTER price change:")
                self.debug(f"  Main account ({self.dept2_id}): Breakfast: €{guest_balances['main_balances']['breakfast']}")
                self.debug(f"  Subaccount ({self.dept1_id}): Breakfast: €{guest_balances['subaccount_balances'].get(self.dept1_id, {}).get('breakfast', 0.0)}")
            else:
                self.error(f"Failed to get guest employee balances after: {response.status_code}")
                return False
                
            # Get regular employee balances
            response = requests.get(f"{API_BASE}/employees/{self.regular_employee_id}/all-balances")
            if response.status_code == 200:
                regular_balances = response.json()
                self.regular_balances_after = regular_balances
                
                self.debug(f"Regular employee balances AFTER price change:")
                self.debug(f"  Main account ({self.dept1_id}): Breakfast: €{regular_balances['main_balances']['breakfast']}")
            else:
                self.error(f"Failed to get regular employee balances after: {response.status_code}")
                return False
                
            return True
        except Exception as e:
            self.error(f"Exception getting employee balances after: {str(e)}")
            return False
            
    def analyze_balance_changes(self):
        """Analyze and verify balance changes"""
        try:
            self.log("\n🔍 ANALYZING BALANCE CHANGES:")
            self.log("=" * 50)
            
            # Guest employee analysis
            guest_main_before = self.guest_balances_before['main_balances']['breakfast']
            guest_main_after = self.guest_balances_after['main_balances']['breakfast']
            guest_main_change = guest_main_after - guest_main_before
            
            guest_sub_before = self.guest_balances_before['subaccount_balances'].get(self.dept1_id, {}).get('breakfast', 0.0)
            guest_sub_after = self.guest_balances_after['subaccount_balances'].get(self.dept1_id, {}).get('breakfast', 0.0)
            guest_sub_change = guest_sub_after - guest_sub_before
            
            self.log(f"GUEST EMPLOYEE ({self.guest_employee_name}):")
            self.log(f"  Main account change: €{guest_main_before} → €{guest_main_after} (Δ€{guest_main_change})")
            self.log(f"  Subaccount change: €{guest_sub_before} → €{guest_sub_after} (Δ€{guest_sub_change})")
            
            # Regular employee analysis
            regular_main_before = self.regular_balances_before['main_balances']['breakfast']
            regular_main_after = self.regular_balances_after['main_balances']['breakfast']
            regular_main_change = regular_main_after - regular_main_before
            
            self.log(f"REGULAR EMPLOYEE ({self.regular_employee_name}):")
            self.log(f"  Main account change: €{regular_main_before} → €{regular_main_after} (Δ€{regular_main_change})")
            
            # Verification
            success = True
            
            # Expected: Guest employee subaccount should improve by +1.00€
            if abs(guest_sub_change - 1.00) < 0.01:
                self.success(f"✅ CORRECT: Guest subaccount improved by €{guest_sub_change}")
            else:
                self.error(f"❌ BUG: Guest subaccount change €{guest_sub_change}, expected €1.00")
                success = False
                
            # Expected: Guest employee main account should remain unchanged
            if abs(guest_main_change) < 0.01:
                self.success(f"✅ CORRECT: Guest main account unchanged (€{guest_main_change})")
            else:
                self.error(f"❌ BUG: Guest main account changed by €{guest_main_change}, expected €0.00")
                success = False
                
            # Expected: Regular employee main account should improve by +1.00€
            if abs(regular_main_change - 1.00) < 0.01:
                self.success(f"✅ CORRECT: Regular main account improved by €{regular_main_change}")
            else:
                self.error(f"❌ BUG: Regular main account change €{regular_main_change}, expected €1.00")
                success = False
                
            return success
        except Exception as e:
            self.error(f"Exception analyzing balance changes: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete retroactive lunch price adjustment test"""
        self.log("🎯 STARTING RETROACTIVE LUNCH PRICE ADJUSTMENT BUG TEST")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Authenticate Department 1 Admin", self.authenticate_dept1_admin),
            ("Authenticate Department 2 Admin", self.authenticate_dept2_admin),
            ("Create Guest Employee (fw4abteilung2)", self.create_guest_employee),
            ("Create Regular Employee (fw4abteilung1)", self.create_regular_employee),
            ("Add Guest Employee Temporarily to fw4abteilung1", self.add_guest_employee_temporarily),
            ("Set Initial Lunch Price (€6.00)", self.set_initial_lunch_price),
            ("Create Guest Employee Order with Lunch", self.create_guest_employee_order),
            ("Create Regular Employee Order with Lunch", self.create_regular_employee_order),
            ("Get Employee Balances Before Price Change", self.get_employee_balances_before),
            ("Apply Retroactive Lunch Price Change (€6.00 → €5.00)", self.apply_retroactive_lunch_price_change),
            ("Verify Order Price Changes", self.verify_order_price_changes),
            ("Get Employee Balances After Price Change", self.get_employee_balances_after),
            ("Analyze Balance Changes", self.analyze_balance_changes)
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
            self.success(f"🎉 RETROACTIVE LUNCH PRICE ADJUSTMENT TEST COMPLETED!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            return True
        else:
            self.error(f"❌ RETROACTIVE LUNCH PRICE ADJUSTMENT TEST FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            return False

def main():
    """Main test execution"""
    print("🧪 Retroactive Lunch Price Adjustment Bug Test for Guest Employees")
    print("=" * 70)
    
    # Initialize and run test
    test_suite = RetroactiveLunchPriceTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - RETROACTIVE LUNCH PRICE ADJUSTMENT IS WORKING!")
        exit(0)
    else:
        print("\n❌ TESTS FAILED - RETROACTIVE LUNCH PRICE ADJUSTMENT BUG CONFIRMED!")
        exit(1)

if __name__ == "__main__":
    main()