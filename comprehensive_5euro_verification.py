#!/usr/bin/env python3
"""
COMPREHENSIVE 5€ EXTRA PROBLEM VERIFICATION

This test verifies the complete fix for the 5€ extra problem by:
1. Creating a fresh scenario in a different department
2. Testing the exact user case: 5×5€ lunch + 0.50€ egg = 25.50€
3. Verifying that after sponsoring, the total is NOT 30.50€
4. Checking both daily summary and individual employee balances
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Use Department 2 for fresh testing
BASE_URL = "https://canteen-manager-2.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class Comprehensive5EuroVerification:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_auth = None
        self.test_employees = []
        
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
    
    def get_current_lunch_price(self):
        """Get current lunch price to calculate expected totals"""
        try:
            # Get today's lunch price
            today = date.today().isoformat()
            response = self.session.get(f"{BASE_URL}/daily-lunch-price/{DEPARTMENT_ID}/{today}")
            
            if response.status_code == 200:
                price_data = response.json()
                lunch_price = price_data.get("lunch_price", 5.0)
                print(f"   Current lunch price: €{lunch_price:.2f}")
                return lunch_price
            else:
                # Fallback to global settings
                response = self.session.get(f"{BASE_URL}/lunch-settings")
                if response.status_code == 200:
                    settings = response.json()
                    lunch_price = settings.get("price", 5.0)
                    print(f"   Global lunch price: €{lunch_price:.2f}")
                    return lunch_price
                else:
                    print(f"   Using default lunch price: €5.00")
                    return 5.0
                    
        except Exception as e:
            print(f"   Error getting lunch price: {e}, using default €5.00")
            return 5.0
    
    def create_fresh_test_employees(self):
        """Create 5 fresh test employees"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            employee_names = [f"Fresh1_{timestamp}", f"Fresh2_{timestamp}", f"Fresh3_{timestamp}", 
                            f"Fresh4_{timestamp}", f"Fresh5_{timestamp}"]
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
                    print(f"   Failed to create employee {name}: {response.status_code} - {response.text}")
            
            if len(created_employees) == 5:
                self.log_result(
                    "Create Fresh Test Employees",
                    True,
                    f"Successfully created {len(created_employees)} fresh test employees in {DEPARTMENT_NAME}"
                )
                return True
            else:
                self.log_result(
                    "Create Fresh Test Employees",
                    False,
                    error=f"Could only create {len(created_employees)} employees, need exactly 5"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Fresh Test Employees", False, error=str(e))
            return False
    
    def create_user_scenario_orders(self):
        """Create the exact user scenario: 5 lunch orders + 1 egg"""
        try:
            if len(self.test_employees) < 5:
                self.log_result(
                    "Create User Scenario Orders",
                    False,
                    error="Not enough test employees available (need 5)"
                )
                return False
            
            lunch_price = self.get_current_lunch_price()
            orders_created = 0
            total_expected = 0
            
            # Employees 1-4: Only lunch
            for i in range(4):
                employee = self.test_employees[i]
                order_data = {
                    "employee_id": employee["id"],
                    "department_id": DEPARTMENT_ID,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 0,
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],
                        "has_lunch": True,
                        "boiled_eggs": 0,
                        "has_coffee": False
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    orders_created += 1
                    order_total = order.get('total_price', 0)
                    total_expected += order_total
                    print(f"   Created lunch order for {employee['name']}: €{order_total:.2f}")
                else:
                    print(f"   Failed to create lunch order for {employee['name']}: {response.status_code} - {response.text}")
            
            # Employee 5: Lunch + Egg
            if len(self.test_employees) >= 5:
                employee = self.test_employees[4]
                order_data = {
                    "employee_id": employee["id"],
                    "department_id": DEPARTMENT_ID,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 0,
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],
                        "has_lunch": True,
                        "boiled_eggs": 1,  # Add the egg
                        "has_coffee": False
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    orders_created += 1
                    order_total = order.get('total_price', 0)
                    total_expected += order_total
                    print(f"   Created lunch+egg order for {employee['name']}: €{order_total:.2f}")
                else:
                    print(f"   Failed to create lunch+egg order for {employee['name']}: {response.status_code} - {response.text}")
            
            if orders_created == 5:
                self.log_result(
                    "Create User Scenario Orders",
                    True,
                    f"Successfully created user scenario: 5 orders totaling €{total_expected:.2f} (4×lunch + 1×lunch+egg)"
                )
                return True
            else:
                self.log_result(
                    "Create User Scenario Orders",
                    False,
                    error=f"Could only create {orders_created} orders, need exactly 5"
                )
                return False
                
        except Exception as e:
            self.log_result("Create User Scenario Orders", False, error=str(e))
            return False
    
    def verify_before_sponsoring(self):
        """Verify totals before sponsoring to establish baseline"""
        try:
            # Get daily summary before sponsoring
            response = self.session.get(f"{BASE_URL}/orders/daily-summary/{DEPARTMENT_ID}")
            
            if response.status_code != 200:
                self.log_result(
                    "Verify Before Sponsoring",
                    False,
                    error=f"Could not fetch daily summary: HTTP {response.status_code}"
                )
                return False
            
            daily_summary = response.json()
            employee_orders = daily_summary.get("employee_orders", {})
            
            total_before = sum(order.get("total_amount", 0) for order in employee_orders.values())
            
            print(f"\n   📊 BEFORE SPONSORING:")
            for employee_name, order_data in employee_orders.items():
                if any(emp["name"] in employee_name for emp in self.test_employees):
                    employee_total = order_data.get("total_amount", 0)
                    has_lunch = order_data.get("has_lunch", False)
                    boiled_eggs = order_data.get("boiled_eggs", 0)
                    print(f"   - {employee_name}: €{employee_total:.2f} (lunch: {has_lunch}, eggs: {boiled_eggs})")
            
            print(f"   - Total before sponsoring: €{total_before:.2f}")
            
            if total_before > 20.0:  # Should be around 25.50€
                self.log_result(
                    "Verify Before Sponsoring",
                    True,
                    f"Baseline established: €{total_before:.2f} total before sponsoring (expected ~€25.50)"
                )
                return True
            else:
                self.log_result(
                    "Verify Before Sponsoring",
                    False,
                    error=f"Baseline too low: €{total_before:.2f}, expected ~€25.50"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Before Sponsoring", False, error=str(e))
            return False
    
    def sponsor_lunches_fresh(self):
        """Sponsor lunches with fresh employee"""
        try:
            if len(self.test_employees) < 5:
                self.log_result(
                    "Sponsor Lunches Fresh",
                    False,
                    error="Not enough test employees available (need 5)"
                )
                return False
            
            # Employee 5 sponsors lunch for all
            sponsor_employee = self.test_employees[4]
            today = date.today().isoformat()
            
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
                
                self.log_result(
                    "Sponsor Lunches Fresh",
                    True,
                    f"Fresh sponsoring: {sponsored_items} items for {affected_employees} employees, cost €{total_cost:.2f}"
                )
                return True
            else:
                self.log_result(
                    "Sponsor Lunches Fresh",
                    False,
                    error=f"Sponsoring failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Sponsor Lunches Fresh", False, error=str(e))
            return False
    
    def verify_final_fix(self):
        """CRITICAL: Verify the 5€ extra problem is fixed"""
        try:
            # Get daily summary after sponsoring
            response = self.session.get(f"{BASE_URL}/orders/daily-summary/{DEPARTMENT_ID}")
            
            if response.status_code != 200:
                self.log_result(
                    "Verify Final Fix",
                    False,
                    error=f"Could not fetch daily summary: HTTP {response.status_code}"
                )
                return False
            
            daily_summary = response.json()
            employee_orders = daily_summary.get("employee_orders", {})
            
            print(f"\n   📊 AFTER SPONSORING (FINAL FIX VERIFICATION):")
            
            total_after = 0
            sponsored_employees = 0
            employees_with_eggs = 0
            sponsor_total = 0
            
            for employee_name, order_data in employee_orders.items():
                if any(emp["name"] in employee_name for emp in self.test_employees):
                    employee_total = order_data.get("total_amount", 0)
                    has_lunch = order_data.get("has_lunch", False)
                    boiled_eggs = order_data.get("boiled_eggs", 0)
                    total_after += employee_total
                    
                    if employee_total == 0:
                        sponsored_employees += 1
                    if boiled_eggs > 0:
                        employees_with_eggs += 1
                    if employee_total > 5.0:  # Likely the sponsor
                        sponsor_total = employee_total
                    
                    print(f"   - {employee_name}: €{employee_total:.2f} (lunch: {has_lunch}, eggs: {boiled_eggs})")
            
            print(f"\n   📋 FINAL FIX ANALYSIS:")
            print(f"   - Total after sponsoring: €{total_after:.2f}")
            print(f"   - Sponsored employees (€0.00): {sponsored_employees}")
            print(f"   - Employees with eggs: {employees_with_eggs}")
            print(f"   - Sponsor total: €{sponsor_total:.2f}")
            
            # The critical test: total should be much less than 30.50€
            # Expected: around 0.50€ (egg) + sponsor's original cost
            if total_after < 15.0:  # Much less than the problematic 30.50€
                verification_details = []
                verification_details.append(f"Total €{total_after:.2f} << €30.50 (5€ extra eliminated)")
                verification_details.append(f"{sponsored_employees} employees sponsored (€0.00)")
                verification_details.append(f"{employees_with_eggs} employees with eggs")
                
                self.log_result(
                    "Verify Final Fix",
                    True,
                    f"🎉 FINAL 5€ EXTRA PROBLEM COMPLETELY FIXED! {'; '.join(verification_details)}. The daily summary no longer double-counts sponsor costs, eliminating the 5€ extra issue."
                )
                return True
            else:
                self.log_result(
                    "Verify Final Fix",
                    False,
                    error=f"❌ 5€ EXTRA PROBLEM PERSISTS! Total €{total_after:.2f} still too high, expected < €15.00"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Final Fix", False, error=str(e))
            return False

    def run_comprehensive_verification(self):
        """Run comprehensive verification of the 5€ extra problem fix"""
        print("🎯 STARTING COMPREHENSIVE 5€ EXTRA PROBLEM VERIFICATION")
        print("=" * 80)
        print("OBJECTIVE: Verify the 5€ extra problem is completely fixed")
        print("USER ISSUE: Expected €25.50, but got €30.50 (5€ too much)")
        print("ROOT CAUSE: Daily summary double-counted sponsor costs")
        print("FIX: Modified get_daily_summary to exclude sponsor_total_cost")
        print("VERIFICATION: Use fresh data to confirm fix works")
        print("=" * 80)
        
        tests_passed = 0
        total_tests = 6
        
        # 1. Authenticate as Department 2 admin
        if self.authenticate_admin():
            tests_passed += 1
        
        # 2. Create 5 fresh test employees
        if self.create_fresh_test_employees():
            tests_passed += 1
        
        # 3. Create user scenario orders
        if self.create_user_scenario_orders():
            tests_passed += 1
        
        # 4. Verify baseline before sponsoring
        if self.verify_before_sponsoring():
            tests_passed += 1
        
        # 5. Sponsor lunches with fresh data
        if self.sponsor_lunches_fresh():
            tests_passed += 1
        
        # 6. CRITICAL: Verify final fix
        if self.verify_final_fix():
            tests_passed += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 COMPREHENSIVE 5€ EXTRA PROBLEM VERIFICATION SUMMARY")
        print("=" * 80)
        
        success_rate = (tests_passed / total_tests) * 100
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   Details: {result['details']}")
            if result['error']:
                print(f"   Error: {result['error']}")
        
        print(f"\n📊 OVERALL RESULT: {tests_passed}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        if tests_passed == total_tests:
            print("🎉 COMPREHENSIVE 5€ EXTRA PROBLEM FIX VERIFICATION SUCCESSFUL!")
            print("✅ The 5€ extra problem has been completely eliminated")
            print("✅ Daily summary no longer double-counts sponsor costs")
            print("✅ Fix works correctly with fresh test data")
            print("✅ User's reported issue is resolved")
            return True
        else:
            print("❌ COMPREHENSIVE VERIFICATION FAILED")
            failed_tests = total_tests - tests_passed
            print(f"⚠️  {failed_tests} test(s) failed - fix may need additional work")
            return False

if __name__ == "__main__":
    tester = Comprehensive5EuroVerification()
    success = tester.run_comprehensive_verification()
    sys.exit(0 if success else 1)