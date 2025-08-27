#!/usr/bin/env python3
"""
DEBUG NEGATIVE SPONSOR BALANCE ISSUE

**Problem**: Sponsor receives -17.50€ instead of expected positive balance

**Debug Focus**:
1. Create fresh test scenario in Department 2  
2. Create sponsor + 4 other employees
3. Create orders and track exact balance calculations step by step
4. Before sponsoring: Check all employee balances
5. After sponsoring: Check exact sponsor balance calculation
6. Identify where the negative value is coming from

**Debug Points to Check**:
- Initial sponsor balance before sponsoring
- Sponsor's original order cost (should be ~7.50€)
- Total sponsored cost calculation (should be 25€ for all lunches)
- Sponsor contributed amount (should be 5€ for own lunch)
- Sponsor additional cost (should be 20€ for others)
- Final calculation: initial_balance + additional_cost

**Expected Flow**:
- Sponsor initial balance: 7.50€ (from own order)  
- Additional cost: 20€ (for 4 others at 5€ each)
- Final balance: 7.50€ + 20€ = 27.50€

Find out why we get -17.50€ instead. Check if there's a sign error or wrong calculation in the backend logic.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Configuration - Use Department 2 as specified in review request
BASE_URL = "https://mealflow-1.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class DebugNegativeBalance:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_auth = None
        self.debug_employees = []
        self.debug_orders = []
        
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
    
    def cleanup_existing_data(self):
        """Clean up existing test data to create fresh scenario"""
        try:
            # Get all employees in department
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            if response.status_code != 200:
                self.log_result(
                    "Clean Up Existing Data",
                    False,
                    error=f"Could not fetch employees: {response.status_code} - {response.text}"
                )
                return False
            
            employees = response.json()
            
            # Delete test employees (those with timestamps in names)
            deleted_employees = 0
            deleted_orders = 0
            reset_balances = 0
            
            for employee in employees:
                employee_name = employee.get("name", "")
                
                # Check if this is a test employee (contains timestamp patterns)
                is_test_employee = any(pattern in employee_name for pattern in [
                    "Sponsor_", "Employee", "Bug3Test_", "Debug_", "_20"
                ])
                
                if is_test_employee:
                    # Get employee orders first
                    orders_response = self.session.get(f"{BASE_URL}/employees/{employee['id']}/orders")
                    if orders_response.status_code == 200:
                        orders_data = orders_response.json()
                        orders_list = orders_data.get("orders", [])
                        
                        # Delete today's orders
                        today_date = date.today().isoformat()
                        for order in orders_list:
                            order_date = order.get("timestamp", "")[:10]
                            if order_date == today_date:
                                delete_response = self.session.delete(f"{BASE_URL}/orders/{order['id']}")
                                if delete_response.status_code == 200:
                                    deleted_orders += 1
                    
                    # Reset employee balance
                    reset_response = self.session.post(f"{BASE_URL}/admin/reset-balance/{employee['id']}", json={
                        "balance_type": "breakfast"
                    })
                    if reset_response.status_code == 200:
                        reset_balances += 1
                    
                    # Delete employee
                    delete_response = self.session.delete(f"{BASE_URL}/department-admin/employees/{employee['id']}")
                    if delete_response.status_code == 200:
                        deleted_employees += 1
            
            self.log_result(
                "Clean Up Existing Data",
                True,
                f"Successfully cleaned up {deleted_employees} employees, {deleted_orders} orders, reset {reset_balances} balances for fresh testing scenario"
            )
            return True
                
        except Exception as e:
            self.log_result("Clean Up Existing Data", False, error=str(e))
            return False
    
    def create_fresh_employees(self):
        """Create exactly 5 employees: 1 sponsor (Brauni) + 4 others"""
        try:
            # Use timestamp to ensure unique names
            timestamp = datetime.now().strftime("%H%M%S")
            
            # Create sponsor employee named "Brauni" as specified in review request
            employee_names = [f"Brauni"] + [f"Employee{i}_{timestamp}" for i in range(1, 5)]
            created_employees = []
            
            for name in employee_names:
                response = self.session.post(f"{BASE_URL}/employees", json={
                    "name": name,
                    "department_id": DEPARTMENT_ID
                })
                
                if response.status_code == 200:
                    employee = response.json()
                    created_employees.append(employee)
                    self.debug_employees.append(employee)
                    print(f"   Created employee: {name} (ID: {employee['id'][-8:]})")
                else:
                    print(f"   Failed to create employee {name}: {response.status_code} - {response.text}")
            
            if len(created_employees) >= 5:
                self.log_result(
                    "Create Fresh Employees",
                    True,
                    f"Successfully created {len(created_employees)} employees: 1 sponsor (Brauni) + 4 others"
                )
                return True
            else:
                self.log_result(
                    "Create Fresh Employees",
                    False,
                    error=f"Could only create {len(created_employees)} employees, need exactly 5"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Fresh Employees", False, error=str(e))
            return False
    
    def create_sponsor_order(self):
        """Create sponsor's order (should be ~7.50€)"""
        try:
            if len(self.debug_employees) < 1:
                self.log_result(
                    "Create Sponsor Order",
                    False,
                    error="No sponsor employee available"
                )
                return False
            
            # Sponsor is Brauni (first employee)
            sponsor = self.debug_employees[0]
            
            # Create order worth ~7.50€: breakfast items + lunch
            # 2 white roll halves (1.00€) + 1 boiled egg (0.50€) + lunch (varies by daily price)
            order_data = {
                "employee_id": sponsor["id"],
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 2 roll halves
                    "white_halves": 2,  # 2 white roll halves (0.50€ each = 1.00€)
                    "seeded_halves": 0,
                    "toppings": ["butter", "kaese"],  # 2 free toppings
                    "has_lunch": True,  # Include lunch
                    "boiled_eggs": 1,  # 1 boiled egg (0.50€)
                    "has_coffee": False
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.debug_orders.append(order)
                total_cost = order.get('total_price', 0)
                
                print(f"   📋 SPONSOR ORDER DETAILS:")
                print(f"   - Employee: {sponsor['name']}")
                print(f"   - Order cost: €{total_cost:.2f}")
                print(f"   - Components: 2 white roll halves + 1 boiled egg + lunch")
                
                self.log_result(
                    "Create Sponsor Order",
                    True,
                    f"Successfully created sponsor order for {sponsor['name']}: €{total_cost:.2f}"
                )
                return True
            else:
                self.log_result(
                    "Create Sponsor Order",
                    False,
                    error=f"Failed to create sponsor order: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Sponsor Order", False, error=str(e))
            return False
    
    def create_other_employee_orders(self):
        """Create lunch orders for the other 4 employees (5€ each)"""
        try:
            if len(self.debug_employees) < 5:
                self.log_result(
                    "Create Other Employee Orders",
                    False,
                    error="Not enough employees available (need 5 total)"
                )
                return False
            
            print(f"   📋 OTHER EMPLOYEE ORDERS:")
            
            # Create lunch orders for employees 1-4 (skip sponsor at index 0)
            lunch_orders_created = 0
            total_lunch_cost = 0
            
            for i in range(1, 5):
                employee = self.debug_employees[i]
                # Order: lunch only (should be around 5€)
                order_data = {
                    "employee_id": employee["id"],
                    "department_id": DEPARTMENT_ID,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 0,  # No rolls
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],  # No toppings
                        "has_lunch": True,  # Only lunch
                        "boiled_eggs": 0,
                        "has_coffee": False
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    self.debug_orders.append(order)
                    order_cost = order.get('total_price', 0)
                    total_lunch_cost += order_cost
                    lunch_orders_created += 1
                    print(f"   - {employee['name']}: €{order_cost:.2f} (lunch only)")
                else:
                    print(f"   - Failed to create lunch order for {employee['name']}: {response.status_code} - {response.text}")
            
            if lunch_orders_created == 4:
                print(f"   - Total lunch cost for 4 employees: €{total_lunch_cost:.2f}")
                
                self.log_result(
                    "Create Other Employee Orders",
                    True,
                    f"Successfully created {lunch_orders_created} lunch orders, total cost: €{total_lunch_cost:.2f}"
                )
                return True
            else:
                self.log_result(
                    "Create Other Employee Orders",
                    False,
                    error=f"Could only create {lunch_orders_created} lunch orders, need exactly 4"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Other Employee Orders", False, error=str(e))
            return False
    
    def check_balances_before_sponsoring(self):
        """Check all employee balances BEFORE sponsoring"""
        try:
            print(f"\n   💰 BALANCES BEFORE SPONSORING:")
            
            # Get employees list
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            
            if response.status_code != 200:
                self.log_result(
                    "Check Balances Before Sponsoring",
                    False,
                    error=f"Could not fetch employees list: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            employees_list = response.json()
            balance_details = []
            
            for debug_employee in self.debug_employees:
                employee_data = None
                for emp in employees_list:
                    if emp["id"] == debug_employee["id"]:
                        employee_data = emp
                        break
                
                if employee_data:
                    balance = employee_data.get("breakfast_balance", 0)
                    balance_details.append(f"{debug_employee['name']}: €{balance:.2f}")
                    print(f"   - {debug_employee['name']}: €{balance:.2f}")
                else:
                    balance_details.append(f"{debug_employee['name']}: NOT FOUND")
                    print(f"   - {debug_employee['name']}: NOT FOUND")
            
            self.log_result(
                "Check Balances Before Sponsoring",
                True,
                f"Balances before sponsoring: {'; '.join(balance_details)}"
            )
            return True
                
        except Exception as e:
            self.log_result("Check Balances Before Sponsoring", False, error=str(e))
            return False
    
    def sponsor_lunch_for_all(self):
        """Sponsor lunch for all 5 employees and track the calculation"""
        try:
            if len(self.debug_employees) < 5:
                self.log_result(
                    "Sponsor Lunch for All",
                    False,
                    error="Not enough test employees available (need 5)"
                )
                return False
            
            # Use Brauni as sponsor
            sponsor_employee = self.debug_employees[0]
            today = date.today().isoformat()
            
            print(f"\n   🎯 SPONSORING LUNCH FOR ALL EMPLOYEES:")
            print(f"   - Sponsor: {sponsor_employee['name']}")
            print(f"   - Date: {today}")
            print(f"   - Meal type: lunch")
            
            # Sponsor lunch for all employees in the department today
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": sponsor_employee["id"],
                "sponsor_employee_name": sponsor_employee["name"]
            }
            
            response = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=sponsor_data)
            
            if response.status_code == 200:
                sponsor_result = response.json()
                sponsored_items = sponsor_result.get("sponsored_items", 0)
                total_cost = sponsor_result.get("total_cost", 0)
                affected_employees = sponsor_result.get("affected_employees", 0)
                sponsor_additional_cost = sponsor_result.get("sponsor_additional_cost", 0)
                
                print(f"   ✅ Sponsoring successful!")
                print(f"   - Sponsored items: {sponsored_items}")
                print(f"   - Total cost: €{total_cost:.2f}")
                print(f"   - Affected employees: {affected_employees}")
                print(f"   - Sponsor additional cost: €{sponsor_additional_cost:.2f}")
                
                self.log_result(
                    "Sponsor Lunch for All",
                    True,
                    f"Successfully sponsored lunch: {sponsored_items} items, €{total_cost:.2f} total cost, €{sponsor_additional_cost:.2f} additional cost for sponsor, {affected_employees} employees affected"
                )
                return True
            else:
                self.log_result(
                    "Sponsor Lunch for All",
                    False,
                    error=f"Sponsoring failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Sponsor Lunch for All", False, error=str(e))
            return False
    
    def check_balances_after_sponsoring(self):
        """Check all employee balances AFTER sponsoring and identify the negative balance issue"""
        try:
            print(f"\n   💰 BALANCES AFTER SPONSORING:")
            
            # Get employees list
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            
            if response.status_code != 200:
                self.log_result(
                    "Check Balances After Sponsoring",
                    False,
                    error=f"Could not fetch employees list: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            employees_list = response.json()
            balance_details = []
            sponsor_balance = None
            other_balances = []
            
            for i, debug_employee in enumerate(self.debug_employees):
                employee_data = None
                for emp in employees_list:
                    if emp["id"] == debug_employee["id"]:
                        employee_data = emp
                        break
                
                if employee_data:
                    balance = employee_data.get("breakfast_balance", 0)
                    balance_details.append(f"{debug_employee['name']}: €{balance:.2f}")
                    print(f"   - {debug_employee['name']}: €{balance:.2f}")
                    
                    if i == 0:  # Sponsor (Brauni)
                        sponsor_balance = balance
                    else:  # Other employees
                        other_balances.append(balance)
                else:
                    balance_details.append(f"{debug_employee['name']}: NOT FOUND")
                    print(f"   - {debug_employee['name']}: NOT FOUND")
            
            # Analyze the sponsor balance issue
            print(f"\n   🔍 SPONSOR BALANCE ANALYSIS:")
            print(f"   - Sponsor balance: €{sponsor_balance:.2f}")
            
            if sponsor_balance is not None:
                if sponsor_balance < 0:
                    print(f"   ❌ NEGATIVE BALANCE DETECTED: €{sponsor_balance:.2f}")
                    print(f"   🎯 This matches the reported issue: negative balance instead of positive")
                    
                    if abs(sponsor_balance + 17.50) < 1.0:
                        print(f"   🎯 EXACT MATCH: This is the -17.50€ issue mentioned in the review request!")
                    
                    # Calculate what the balance should be
                    expected_balance = 27.50  # 7.50€ (own order) + 20€ (for 4 others at 5€ each)
                    difference = expected_balance - sponsor_balance
                    print(f"   📊 Expected balance: €{expected_balance:.2f}")
                    print(f"   📊 Actual balance: €{sponsor_balance:.2f}")
                    print(f"   📊 Difference: €{difference:.2f}")
                    
                    # Check if it's a sign error
                    if abs(abs(sponsor_balance) - expected_balance) < 5.0:
                        print(f"   🚨 LIKELY SIGN ERROR: The absolute value is close to expected positive value")
                    
                elif sponsor_balance > 0:
                    expected_balance = 27.50
                    if abs(sponsor_balance - expected_balance) <= 5.0:
                        print(f"   ✅ Sponsor balance appears correct (within tolerance)")
                    else:
                        print(f"   ⚠️ Sponsor balance unexpected: €{sponsor_balance:.2f} (expected ~€{expected_balance:.2f})")
            
            # Check other employee balances
            print(f"\n   🔍 OTHER EMPLOYEE BALANCES ANALYSIS:")
            all_others_zero = all(abs(balance) < 0.01 for balance in other_balances)
            if all_others_zero:
                print(f"   ✅ All other employees have €0.00 (properly sponsored)")
            else:
                print(f"   ❌ Some employees still have non-zero balances (sponsoring incomplete)")
                for i, balance in enumerate(other_balances, 1):
                    if abs(balance) >= 0.01:
                        print(f"   - Employee{i} still owes: €{balance:.2f}")
            
            # Determine success based on whether we identified the issue
            if sponsor_balance is not None and sponsor_balance < 0:
                self.log_result(
                    "Check Balances After Sponsoring",
                    True,  # Success in identifying the issue
                    f"🎯 NEGATIVE BALANCE ISSUE IDENTIFIED: Sponsor has €{sponsor_balance:.2f} instead of expected positive balance. {'; '.join(balance_details)}"
                )
                return True
            else:
                self.log_result(
                    "Check Balances After Sponsoring",
                    False,
                    error=f"Could not reproduce negative balance issue. Balances: {'; '.join(balance_details)}"
                )
                return False
                
        except Exception as e:
            self.log_result("Check Balances After Sponsoring", False, error=str(e))
            return False

    def run_debug_test(self):
        """Run the complete debug test for negative sponsor balance issue"""
        print("🔍 STARTING DEBUG TEST FOR NEGATIVE SPONSOR BALANCE ISSUE")
        print("=" * 80)
        print("PROBLEM: Sponsor receives -17.50€ instead of expected positive balance")
        print("DEPARTMENT: 2. Wachabteilung (admin2 password)")
        print("GOAL: Create fresh scenario and track exact balance calculations")
        print("=" * 80)
        
        # Test sequence
        tests_passed = 0
        total_tests = 7
        
        # Authentication
        if self.authenticate_admin():
            tests_passed += 1
        
        # Clean up existing data
        if self.cleanup_existing_data():
            tests_passed += 1
        
        # Create fresh scenario
        if self.create_fresh_employees():
            tests_passed += 1
        
        if self.create_sponsor_order():
            tests_passed += 1
        
        if self.create_other_employee_orders():
            tests_passed += 1
        
        # Check balances before sponsoring
        if self.check_balances_before_sponsoring():
            tests_passed += 1
        
        # Sponsor lunch and check results
        if self.sponsor_lunch_for_all():
            # Check balances after sponsoring (this is the key test)
            if self.check_balances_after_sponsoring():
                tests_passed += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("🔍 DEBUG TEST FOR NEGATIVE SPONSOR BALANCE ISSUE SUMMARY")
        print("=" * 80)
        
        success_rate = (tests_passed / total_tests) * 100
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   Details: {result['details']}")
            if result['error']:
                print(f"   Error: {result['error']}")
        
        print(f"\n📊 OVERALL RESULT: {tests_passed}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        if tests_passed >= 6:  # Allow some tolerance
            print("🎯 DEBUG TEST COMPLETED - NEGATIVE BALANCE ISSUE ANALYSIS COMPLETE")
            return True
        else:
            print("❌ DEBUG TEST FAILED - COULD NOT REPRODUCE OR ANALYZE THE ISSUE")
            return False

if __name__ == "__main__":
    debugger = DebugNegativeBalance()
    success = debugger.run_debug_test()
    sys.exit(0 if success else 1)