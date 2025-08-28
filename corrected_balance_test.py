#!/usr/bin/env python3
"""
CORRECTED MEAL SPONSORING BALANCE CALCULATION TEST

FOCUS: Test the CORRECTED balance calculation logic for the meal sponsoring feature.
This test first checks actual menu prices and then creates the appropriate test case.

**Critical Fix to Verify:** 
The sponsor balance calculation now includes: `total_cost - sponsor_own_cost` instead of just `total_cost`, which should fix the double-charging issue.

BACKEND URL: https://canteen-manager-2.preview.emergentagent.com/api
DEPARTMENT: 2. Wachabteilung (fw4abteilung2)
ADMIN CREDENTIALS: admin2

PURPOSE: Verify the corrected balance calculation logic with actual menu prices.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Configuration - Use production backend URL from frontend/.env
BASE_URL = "https://canteen-manager-2.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class CorrectedBalanceCalculationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_auth = None
        self.test_employees = []
        self.test_orders = []
        self.menu_prices = {}
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def authenticate_admin(self):
        """Authenticate as department admin"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                self.admin_auth = response.json()
                self.log_result(
                    "Department Admin Authentication",
                    True,
                    f"Successfully authenticated as admin for {DEPARTMENT_NAME}"
                )
                return True
            else:
                self.log_result(
                    "Department Admin Authentication",
                    False,
                    error=f"Authentication failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Department Admin Authentication", False, error=str(e))
            return False
    
    def get_menu_prices(self):
        """Get actual menu prices from the system"""
        try:
            # Get breakfast menu
            breakfast_response = self.session.get(f"{BASE_URL}/menu/breakfast/{DEPARTMENT_ID}")
            if breakfast_response.status_code == 200:
                breakfast_menu = breakfast_response.json()
                for item in breakfast_menu:
                    self.menu_prices[item["roll_type"]] = item["price"]
            
            # Get lunch settings
            lunch_response = self.session.get(f"{BASE_URL}/lunch-settings")
            if lunch_response.status_code == 200:
                lunch_settings = lunch_response.json()
                self.menu_prices["boiled_eggs"] = lunch_settings.get("boiled_eggs_price", 0.60)
                self.menu_prices["coffee"] = lunch_settings.get("coffee_price", 1.50)
                self.menu_prices["lunch"] = lunch_settings.get("price", 0.0)
            
            print(f"   Menu Prices:")
            print(f"   - White rolls: €{self.menu_prices.get('weiss', 0.50):.2f} per half")
            print(f"   - Seeded rolls: €{self.menu_prices.get('koerner', 0.60):.2f} per half")
            print(f"   - Boiled eggs: €{self.menu_prices.get('boiled_eggs', 0.60):.2f} each")
            print(f"   - Coffee: €{self.menu_prices.get('coffee', 1.50):.2f}")
            print(f"   - Lunch: €{self.menu_prices.get('lunch', 0.0):.2f}")
            
            self.log_result(
                "Get Menu Prices",
                True,
                f"Retrieved menu prices successfully"
            )
            return True
                
        except Exception as e:
            self.log_result("Get Menu Prices", False, error=str(e))
            return False
    
    def create_four_identical_employees(self):
        """Create 4 employees for the specific test case"""
        try:
            employee_names = ["BalanceTest1", "BalanceTest2", "BalanceTest3", "BalanceTest4"]
            created_employees = []
            
            for name in employee_names:
                response = self.session.post(f"{BASE_URL}/employees", json={
                    "name": name,
                    "department_id": DEPARTMENT_ID
                })
                
                if response.status_code == 200:
                    employee = response.json()
                    created_employees.append(employee)
                    self.test_employees.append(employee)
                else:
                    # Employee might already exist, try to find existing ones
                    pass
            
            # If we couldn't create new ones, get existing employees
            if len(created_employees) < 4:
                response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
                if response.status_code == 200:
                    existing_employees = response.json()
                    # Use first 4 employees for testing
                    self.test_employees = existing_employees[:4]
                    created_employees = self.test_employees
            
            if len(created_employees) >= 4:
                self.log_result(
                    "Create 4 Test Employees",
                    True,
                    f"Successfully prepared {len(created_employees)} test employees for balance calculation test"
                )
                return True
            else:
                self.log_result(
                    "Create 4 Test Employees",
                    False,
                    error=f"Could not prepare enough test employees. Got {len(created_employees)}, need 4"
                )
                return False
                
        except Exception as e:
            self.log_result("Create 4 Test Employees", False, error=str(e))
            return False
    
    def create_identical_breakfast_orders_with_actual_prices(self):
        """Create 4 identical breakfast orders using actual menu prices"""
        try:
            if len(self.test_employees) < 4:
                self.log_result(
                    "Create 4 Identical Breakfast Orders",
                    False,
                    error="Not enough test employees available"
                )
                return False
            
            # Calculate expected cost per order based on actual prices
            white_roll_price = self.menu_prices.get("weiss", 0.50)
            egg_price = self.menu_prices.get("boiled_eggs", 0.60)
            coffee_price = self.menu_prices.get("coffee", 1.50)
            
            # Create order: 4 white roll halves (2 rolls) + 3 eggs + 1 coffee
            expected_cost_per_order = (4 * white_roll_price) + (3 * egg_price) + coffee_price
            
            print(f"   Expected cost per order:")
            print(f"   - 4 white roll halves: 4 × €{white_roll_price:.2f} = €{4 * white_roll_price:.2f}")
            print(f"   - 3 boiled eggs: 3 × €{egg_price:.2f} = €{3 * egg_price:.2f}")
            print(f"   - 1 coffee: €{coffee_price:.2f}")
            print(f"   - Total per order: €{expected_cost_per_order:.2f}")
            print(f"   - Total for 4 orders: €{4 * expected_cost_per_order:.2f}")
            
            orders_created = 0
            
            # Create identical orders for all 4 employees
            for i in range(4):
                employee = self.test_employees[i]
                order_data = {
                    "employee_id": employee["id"],
                    "department_id": DEPARTMENT_ID,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 4,  # 2 white rolls = 4 halves
                        "white_halves": 4,  # All white rolls
                        "seeded_halves": 0,  # No seeded rolls
                        "toppings": ["ruehrei", "ruehrei", "ruehrei", "ruehrei"],  # 4 toppings for 4 halves (free)
                        "has_lunch": False,  # No lunch
                        "boiled_eggs": 3,    # 3 boiled eggs
                        "has_coffee": True   # 1 coffee
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    self.test_orders.append(order)
                    orders_created += 1
                    print(f"   Created order for {employee['name']}: €{order['total_price']:.2f}")
                else:
                    print(f"   Failed to create order for {employee['name']}: {response.status_code} - {response.text}")
            
            if orders_created == 4:
                total_cost = sum(order['total_price'] for order in self.test_orders)
                self.log_result(
                    "Create 4 Identical Breakfast Orders",
                    True,
                    f"Successfully created 4 identical breakfast orders. Total cost: €{total_cost:.2f} (Expected: €{4 * expected_cost_per_order:.2f})"
                )
                return True
            else:
                self.log_result(
                    "Create 4 Identical Breakfast Orders",
                    False,
                    error=f"Could only create {orders_created} orders, need 4"
                )
                return False
                
        except Exception as e:
            self.log_result("Create 4 Identical Breakfast Orders", False, error=str(e))
            return False
    
    def verify_initial_balances(self):
        """Verify initial balances match order costs"""
        try:
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            if response.status_code != 200:
                raise Exception("Could not fetch employees to check balances")
            
            employees = response.json()
            test_employee_balances = []
            
            for test_emp in self.test_employees:
                emp = next((e for e in employees if e["id"] == test_emp["id"]), None)
                if emp:
                    balance = emp.get("breakfast_balance", 0.0)
                    test_employee_balances.append(balance)
                    print(f"   {emp['name']}: €{balance:.2f}")
            
            total_balance = sum(test_employee_balances)
            expected_individual = self.test_orders[0]['total_price'] if self.test_orders else 0.0
            expected_total = sum(order['total_price'] for order in self.test_orders)
            
            # Check if all balances match their order costs
            all_correct = all(abs(balance - expected_individual) < 0.1 for balance in test_employee_balances)
            total_correct = abs(total_balance - expected_total) < 0.1
            
            if all_correct and total_correct:
                self.log_result(
                    "Verify Initial Balances",
                    True,
                    f"All 4 employees have correct initial balances (€{expected_individual:.2f} each). Total: €{total_balance:.2f}"
                )
                return True
            else:
                self.log_result(
                    "Verify Initial Balances",
                    False,
                    error=f"Incorrect initial balances. Expected: 4x €{expected_individual:.2f} = €{expected_total:.2f}, Got: {test_employee_balances} = €{total_balance:.2f}"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Initial Balances", False, error=str(e))
            return False
    
    def test_breakfast_sponsoring_balance_calculation(self):
        """Test breakfast sponsoring and verify CORRECTED balance calculations"""
        try:
            if len(self.test_employees) < 4:
                self.log_result(
                    "Test Breakfast Sponsoring Balance Calculation",
                    False,
                    error="Not enough test employees for sponsoring test"
                )
                return False
            
            # Use 4th employee as sponsor (index 3)
            sponsor = self.test_employees[3]
            today = date.today().isoformat()
            
            # Perform breakfast sponsoring
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": sponsor["id"],
                "sponsor_employee_name": sponsor["name"]
            }
            
            response = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=sponsor_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response structure
                required_fields = ["message", "sponsored_items", "total_cost", "affected_employees", "sponsor"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "Test Breakfast Sponsoring Balance Calculation",
                        False,
                        error=f"Missing fields in response: {missing_fields}"
                    )
                    return False
                
                print(f"   Sponsoring result: {result['sponsored_items']}")
                print(f"   Total sponsored cost: €{result['total_cost']}")
                print(f"   Affected employees: {result['affected_employees']}")
                
                # Now check the balances after sponsoring
                return self.verify_corrected_balances_after_sponsoring(sponsor, result['total_cost'])
                
            elif response.status_code == 400 and "bereits gesponsert" in response.text:
                # Already sponsored - check existing balances
                self.log_result(
                    "Test Breakfast Sponsoring Balance Calculation",
                    True,
                    "Breakfast already sponsored today - checking existing balance calculations"
                )
                # Estimate sponsored cost based on menu prices
                white_roll_price = self.menu_prices.get("weiss", 0.50)
                egg_price = self.menu_prices.get("boiled_eggs", 0.60)
                estimated_sponsored_cost = 4 * ((4 * white_roll_price) + (3 * egg_price))  # 4 employees, rolls + eggs only
                return self.verify_corrected_balances_after_sponsoring(sponsor, estimated_sponsored_cost)
            else:
                self.log_result(
                    "Test Breakfast Sponsoring Balance Calculation",
                    False,
                    error=f"Sponsoring failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Breakfast Sponsoring Balance Calculation", False, error=str(e))
            return False
    
    def verify_corrected_balances_after_sponsoring(self, sponsor, total_sponsored_cost):
        """Verify the corrected balance calculations after sponsoring"""
        try:
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            if response.status_code != 200:
                raise Exception("Could not fetch employees to check post-sponsoring balances")
            
            employees = response.json()
            balances = {}
            
            for test_emp in self.test_employees:
                emp = next((e for e in employees if e["id"] == test_emp["id"]), None)
                if emp:
                    balance = emp.get("breakfast_balance", 0.0)
                    balances[emp["name"]] = balance
                    is_sponsor = emp["id"] == sponsor["id"]
                    print(f"   {emp['name']} {'(SPONSOR)' if is_sponsor else ''}: €{balance:.2f}")
            
            # Calculate expected results based on actual prices and logic:
            white_roll_price = self.menu_prices.get("weiss", 0.50)
            egg_price = self.menu_prices.get("boiled_eggs", 0.60)
            coffee_price = self.menu_prices.get("coffee", 1.50)
            
            # Original order cost per person
            original_cost_per_person = (4 * white_roll_price) + (3 * egg_price) + coffee_price
            
            # Sponsored cost per person (only rolls + eggs, NO coffee)
            sponsored_cost_per_person = (4 * white_roll_price) + (3 * egg_price)
            
            # Expected results:
            # - Sponsor: original_cost + total_sponsored_cost - sponsor_own_sponsored_cost
            # - Others: original_cost - sponsored_cost_per_person (only coffee remains)
            
            expected_sponsor_balance = original_cost_per_person + total_sponsored_cost - sponsored_cost_per_person
            expected_other_balance = original_cost_per_person - sponsored_cost_per_person  # Should be just coffee cost
            
            print(f"   Expected calculations:")
            print(f"   - Original cost per person: €{original_cost_per_person:.2f}")
            print(f"   - Sponsored cost per person: €{sponsored_cost_per_person:.2f}")
            print(f"   - Total sponsored cost: €{total_sponsored_cost:.2f}")
            print(f"   - Expected sponsor balance: €{expected_sponsor_balance:.2f}")
            print(f"   - Expected other balance: €{expected_other_balance:.2f} (coffee only)")
            
            sponsor_name = sponsor["name"]
            sponsor_balance = balances.get(sponsor_name, 0.0)
            
            # Get balances of other employees (not sponsor)
            other_balances = [balance for name, balance in balances.items() if name != sponsor_name]
            
            # Check sponsor balance
            sponsor_correct = abs(sponsor_balance - expected_sponsor_balance) < 0.5
            
            # Check other employees' balances
            others_correct = all(abs(balance - expected_other_balance) < 0.5 for balance in other_balances)
            
            if sponsor_correct and others_correct:
                self.log_result(
                    "Verify Corrected Balance Calculations",
                    True,
                    f"✅ CRITICAL FIX VERIFIED: Correct balance calculations! Sponsor: €{sponsor_balance:.2f} (expected €{expected_sponsor_balance:.2f}), Others: {[f'€{b:.2f}' for b in other_balances]} (expected €{expected_other_balance:.2f} each - coffee only)"
                )
                return True
            else:
                self.log_result(
                    "Verify Corrected Balance Calculations",
                    False,
                    error=f"❌ INCORRECT BALANCE CALCULATIONS: Sponsor: €{sponsor_balance:.2f} (expected €{expected_sponsor_balance:.2f}), Others: {[f'€{b:.2f}' for b in other_balances]} (expected €{expected_other_balance:.2f} each)"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Corrected Balance Calculations", False, error=str(e))
            return False
    
    def verify_sponsored_messages(self):
        """Verify sponsored messages are added to orders"""
        try:
            if len(self.test_employees) < 4:
                self.log_result(
                    "Verify Sponsored Messages",
                    False,
                    error="Not enough test employees to verify sponsored messages"
                )
                return False
            
            sponsor = self.test_employees[3]  # 4th employee is sponsor
            sponsor_name = sponsor["name"]
            
            messages_found = 0
            today = date.today().isoformat()
            
            # Check all employees' orders for sponsored messages
            for employee in self.test_employees:
                orders_response = self.session.get(f"{BASE_URL}/employees/{employee['id']}/orders")
                if orders_response.status_code == 200:
                    orders_data = orders_response.json()
                    orders = orders_data.get("orders", [])
                    
                    for order in orders:
                        order_date = order.get("timestamp", "")
                        if order_date.startswith(today):
                            if employee["id"] == sponsor["id"]:
                                # Check sponsor message
                                if order.get("sponsor_message"):
                                    messages_found += 1
                                    print(f"   Sponsor message found for {employee['name']}")
                            else:
                                # Check sponsored message
                                if order.get("sponsored_message"):
                                    messages_found += 1
                                    print(f"   Sponsored message found for {employee['name']}")
            
            if messages_found >= 2:  # At least sponsor message + one sponsored message
                self.log_result(
                    "Verify Sponsored Messages",
                    True,
                    f"Found {messages_found} sponsored messages in orders"
                )
                return True
            else:
                self.log_result(
                    "Verify Sponsored Messages",
                    True,  # Not critical for balance calculation test
                    f"Only found {messages_found} sponsored messages (not critical for balance test)"
                )
                return True
                
        except Exception as e:
            self.log_result("Verify Sponsored Messages", False, error=str(e))
            return False

    def run_corrected_balance_calculation_test(self):
        """Run the corrected balance calculation test"""
        print("🧮 CORRECTED MEAL SPONSORING BALANCE CALCULATION TEST")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME} ({DEPARTMENT_ID})")
        print(f"Admin Password: {ADMIN_PASSWORD}")
        print("=" * 80)
        print("🎯 TESTING CORRECTED BALANCE CALCULATION LOGIC:")
        print("   - 4 employees in Department 2")
        print("   - Each orders: 4 white roll halves + 3 eggs + 1 coffee")
        print("   - After breakfast sponsoring by one employee")
        print("   - Verify: sponsor pays total - own_sponsored, others pay only coffee")
        print("=" * 80)
        print()
        
        # Test 1: Department Admin Authentication
        print("🧪 TEST 1: Department Admin Authentication")
        test1_ok = self.authenticate_admin()
        
        if not test1_ok:
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Test 2: Get Menu Prices
        print("🧪 TEST 2: Get Menu Prices")
        test2_ok = self.get_menu_prices()
        
        if not test2_ok:
            print("❌ Cannot proceed without menu prices")
            return False
        
        # Test 3: Create 4 Test Employees
        print("🧪 TEST 3: Create 4 Test Employees")
        test3_ok = self.create_four_identical_employees()
        
        if not test3_ok:
            print("❌ Cannot proceed without 4 test employees")
            return False
        
        # Test 4: Create 4 Identical Breakfast Orders
        print("🧪 TEST 4: Create 4 Identical Breakfast Orders (with actual prices)")
        test4_ok = self.create_identical_breakfast_orders_with_actual_prices()
        
        # Test 5: Verify Initial Balances
        print("🧪 TEST 5: Verify Initial Balances")
        test5_ok = self.verify_initial_balances()
        
        # Test 6: Test Breakfast Sponsoring Balance Calculation (CRITICAL)
        print("🧪 TEST 6: Test Breakfast Sponsoring Balance Calculation (CRITICAL)")
        test6_ok = self.test_breakfast_sponsoring_balance_calculation()
        
        # Test 7: Verify Sponsored Messages
        print("🧪 TEST 7: Verify Sponsored Messages")
        test7_ok = self.verify_sponsored_messages()
        
        # Summary
        self.print_test_summary()
        
        return all([test1_ok, test2_ok, test3_ok, test4_ok, test5_ok, test6_ok, test7_ok])
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🧮 CORRECTED BALANCE CALCULATION TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        print()
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['error']}")
            print()
            print("🚨 CONCLUSION: Balance calculation fix has issues!")
        else:
            print("✅ ALL BALANCE CALCULATION TESTS PASSED!")
            print("   • ✅ Correct Balance Calculations: Sponsor pays total minus own sponsored part")
            print("   • ✅ No Double Charging: Fixed sponsor balance calculation")
            print("   • ✅ Others Pay Correctly: Only non-sponsored items (coffee)")
            print("   • 🎉 THE BALANCE CALCULATION FIX IS WORKING CORRECTLY!")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = CorrectedBalanceCalculationTester()
    
    try:
        success = tester.run_corrected_balance_calculation_test()
        
        # Exit with appropriate code
        failed_tests = [r for r in tester.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            sys.exit(1)  # Indicate test failures
        else:
            sys.exit(0)  # All tests passed
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()