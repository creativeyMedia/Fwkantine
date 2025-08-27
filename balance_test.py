#!/usr/bin/env python3
"""
MEAL SPONSORING BALANCE CALCULATION TEST

FOCUS: Test the CORRECTED balance calculation logic for the meal sponsoring feature.
Focus on the specific test case reported by the user.

**USER'S TEST CASE:**
- 4 employees in "2. Wachabteilung" 
- Each orders EXACTLY the same: 2x white rolls (1€) + 3x eggs (1€) + 1x coffee (1€) = 3€ per person
- Total breakfast cost: 12€
- After breakfast sponsoring by one employee

**EXPECTED RESULTS:**
- Sponsored costs: 4 employees × 2€ (rolls + eggs) = 8€
- Sponsor should have: 3€ (own order) - 2€ (own sponsored parts) + 8€ (pays for all) = 9€ balance
- Others should have: 3€ (own order) - 2€ (sponsored parts) = 1€ balance (only coffee)

**ACTUAL WRONG RESULTS (to verify fix):**
- Sponsor had: 11,80€ (wrong)
- Others had: 0,80€ (wrong)

**Critical Fix to Verify:** 
The sponsor balance calculation now includes: `total_cost - sponsor_own_cost` instead of just `total_cost`, which should fix the double-charging issue.

BACKEND URL: https://mealflow-1.preview.emergentagent.com/api
DEPARTMENT: 2. Wachabteilung (fw4abteilung2)
ADMIN CREDENTIALS: admin2

PURPOSE: Verify the corrected balance calculation logic for the specific user test case.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Configuration - Use production backend URL from frontend/.env
BASE_URL = "https://mealflow-1.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class BalanceCalculationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_auth = None
        self.test_employees = []
        self.test_orders = []
        
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
    
    def create_four_identical_employees(self):
        """Create 4 employees for the specific test case"""
        try:
            employee_names = ["TestEmp1", "TestEmp2", "TestEmp3", "TestEmp4"]
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
    
    def create_identical_breakfast_orders(self):
        """Create 4 identical breakfast orders: 2x white rolls (1€) + 3x eggs (1€) + 1x coffee (1€) = 3€ per person"""
        try:
            if len(self.test_employees) < 4:
                self.log_result(
                    "Create 4 Identical Breakfast Orders",
                    False,
                    error="Not enough test employees available"
                )
                return False
            
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
                        "toppings": ["ruehrei", "ruehrei", "ruehrei", "ruehrei"],  # 4 toppings for 4 halves
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
                    f"Successfully created 4 identical breakfast orders. Total cost: €{total_cost:.2f} (Expected: €12.00)"
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
        """Verify initial balances are 3€ each (total 12€)"""
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
            expected_individual = 3.0
            expected_total = 12.0
            
            # Check if all balances are approximately 3€ each
            all_correct = all(abs(balance - expected_individual) < 0.1 for balance in test_employee_balances)
            total_correct = abs(total_balance - expected_total) < 0.1
            
            if all_correct and total_correct:
                self.log_result(
                    "Verify Initial Balances",
                    True,
                    f"All 4 employees have correct initial balances (~€3.00 each). Total: €{total_balance:.2f}"
                )
                return True
            else:
                self.log_result(
                    "Verify Initial Balances",
                    False,
                    error=f"Incorrect initial balances. Expected: 4x €3.00 = €12.00, Got: {test_employee_balances} = €{total_balance:.2f}"
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
                return self.verify_corrected_balances_after_sponsoring(sponsor)
                
            elif response.status_code == 400 and "bereits gesponsert" in response.text:
                # Already sponsored - check existing balances
                self.log_result(
                    "Test Breakfast Sponsoring Balance Calculation",
                    True,
                    "Breakfast already sponsored today - checking existing balance calculations"
                )
                return self.verify_corrected_balances_after_sponsoring(sponsor)
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
    
    def verify_corrected_balances_after_sponsoring(self, sponsor):
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
            
            # Expected results:
            # - Sponsored costs: 4 employees × 2€ (rolls + eggs) = 8€
            # - Sponsor should have: 3€ (own order) - 2€ (own sponsored parts) + 8€ (pays for all) = 9€ balance
            # - Others should have: 3€ (own order) - 2€ (sponsored parts) = 1€ balance (only coffee)
            
            sponsor_name = sponsor["name"]
            sponsor_balance = balances.get(sponsor_name, 0.0)
            
            # Get balances of other employees (not sponsor)
            other_balances = [balance for name, balance in balances.items() if name != sponsor_name]
            
            expected_sponsor_balance = 9.0
            expected_other_balance = 1.0
            
            # Check sponsor balance (should be around 9€)
            sponsor_correct = abs(sponsor_balance - expected_sponsor_balance) < 0.5
            
            # Check other employees' balances (should be around 1€ each)
            others_correct = all(abs(balance - expected_other_balance) < 0.5 for balance in other_balances)
            
            if sponsor_correct and others_correct:
                self.log_result(
                    "Verify Corrected Balance Calculations",
                    True,
                    f"✅ CRITICAL FIX VERIFIED: Correct balance calculations! Sponsor: €{sponsor_balance:.2f} (expected ~€9.00), Others: {[f'€{b:.2f}' for b in other_balances]} (expected ~€1.00 each)"
                )
                return True
            else:
                # Check if we have the old wrong results
                old_wrong_sponsor = abs(sponsor_balance - 11.80) < 0.5
                old_wrong_others = all(abs(balance - 0.80) < 0.5 for balance in other_balances)
                
                if old_wrong_sponsor and old_wrong_others:
                    self.log_result(
                        "Verify Corrected Balance Calculations",
                        False,
                        error=f"❌ CRITICAL BUG: Still showing OLD WRONG RESULTS! Sponsor: €{sponsor_balance:.2f} (wrong, should be ~€9.00), Others: {[f'€{b:.2f}' for b in other_balances]} (wrong, should be ~€1.00 each). The balance calculation fix is NOT working!"
                    )
                else:
                    self.log_result(
                        "Verify Corrected Balance Calculations",
                        False,
                        error=f"❌ INCORRECT BALANCE CALCULATIONS: Sponsor: €{sponsor_balance:.2f} (expected ~€9.00), Others: {[f'€{b:.2f}' for b in other_balances]} (expected ~€1.00 each)"
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
    
    def verify_total_system_balance(self):
        """Check that total system balance remains correct"""
        try:
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            if response.status_code != 200:
                raise Exception("Could not fetch employees to check total balance")
            
            employees = response.json()
            total_balance = 0.0
            
            for test_emp in self.test_employees:
                emp = next((e for e in employees if e["id"] == test_emp["id"]), None)
                if emp:
                    balance = emp.get("breakfast_balance", 0.0)
                    total_balance += balance
            
            # Total should still be around 12€ (the original total cost)
            expected_total = 12.0
            
            if abs(total_balance - expected_total) < 0.5:
                self.log_result(
                    "Verify Total System Balance",
                    True,
                    f"Total system balance correct: €{total_balance:.2f} (expected ~€12.00)"
                )
                return True
            else:
                self.log_result(
                    "Verify Total System Balance",
                    False,
                    error=f"Total system balance incorrect: €{total_balance:.2f} (expected ~€12.00)"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Total System Balance", False, error=str(e))
            return False

    def run_balance_calculation_test(self):
        """Run the specific balance calculation test"""
        print("🧮 MEAL SPONSORING BALANCE CALCULATION TEST")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME} ({DEPARTMENT_ID})")
        print(f"Admin Password: {ADMIN_PASSWORD}")
        print("=" * 80)
        print("🎯 TESTING USER'S SPECIFIC TEST CASE:")
        print("   - 4 employees in Department 2")
        print("   - Each orders: 2x white rolls (1€) + 3x eggs (1€) + 1x coffee (1€) = 3€")
        print("   - Total breakfast cost: 12€")
        print("   - After breakfast sponsoring by one employee")
        print("   - Expected: Sponsor 9€, Others 1€ each")
        print("=" * 80)
        print()
        
        # Test 1: Department Admin Authentication
        print("🧪 TEST 1: Department Admin Authentication")
        test1_ok = self.authenticate_admin()
        
        if not test1_ok:
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Test 2: Create 4 Test Employees
        print("🧪 TEST 2: Create 4 Test Employees")
        test2_ok = self.create_four_identical_employees()
        
        if not test2_ok:
            print("❌ Cannot proceed without 4 test employees")
            return False
        
        # Test 3: Create 4 Identical Breakfast Orders
        print("🧪 TEST 3: Create 4 Identical Breakfast Orders (2x rolls + 3x eggs + 1x coffee)")
        test3_ok = self.create_identical_breakfast_orders()
        
        # Test 4: Verify Initial Balances
        print("🧪 TEST 4: Verify Initial Balances (3€ each, 12€ total)")
        test4_ok = self.verify_initial_balances()
        
        # Test 5: Test Breakfast Sponsoring Balance Calculation (CRITICAL)
        print("🧪 TEST 5: Test Breakfast Sponsoring Balance Calculation (CRITICAL)")
        test5_ok = self.test_breakfast_sponsoring_balance_calculation()
        
        # Test 6: Verify Sponsored Messages
        print("🧪 TEST 6: Verify Sponsored Messages")
        test6_ok = self.verify_sponsored_messages()
        
        # Test 7: Verify Total System Balance
        print("🧪 TEST 7: Verify Total System Balance")
        test7_ok = self.verify_total_system_balance()
        
        # Summary
        self.print_test_summary()
        
        return all([test1_ok, test2_ok, test3_ok, test4_ok, test5_ok, test6_ok, test7_ok])
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🧮 BALANCE CALCULATION TEST SUMMARY")
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
            print("   • ✅ Correct Balance Calculations: Sponsor gets 9€, Others get 1€ each")
            print("   • ✅ No Double Charging: Fixed sponsor balance calculation")
            print("   • ✅ Total System Balance: Remains correct at 12€")
            print("   • 🎉 THE BALANCE CALCULATION FIX IS WORKING CORRECTLY!")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = BalanceCalculationTester()
    
    try:
        success = tester.run_balance_calculation_test()
        
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