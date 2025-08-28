#!/usr/bin/env python3
"""
FRESH SPONSOR SALDO CONSERVATION TEST

This test creates completely new employees to test the full sponsor flow from scratch.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Configuration - Use Department 3 as specified in review request
BASE_URL = "https://canteen-manager-2.preview.emergentagent.com/api"
DEPARTMENT_NAME = "3. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung3"
ADMIN_PASSWORD = "admin3"

class FreshSponsorTest:
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
    
    def create_fresh_employees(self):
        """Create 4 completely fresh employees"""
        try:
            # Use unique timestamp to avoid conflicts
            timestamp = datetime.now().strftime("%H%M%S%f")[:8]  # Include microseconds
            employee_names = [f"Fresh1_{timestamp}", f"Fresh2_{timestamp}", 
                            f"Fresh3_{timestamp}", f"Fresh4_{timestamp}"]
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
            
            if len(created_employees) == 4:
                self.log_result(
                    "Create Fresh Employees",
                    True,
                    f"Successfully created 4 fresh employees with unique names"
                )
                return True
            else:
                self.log_result(
                    "Create Fresh Employees",
                    False,
                    error=f"Created {len(created_employees)} employees, need exactly 4"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Fresh Employees", False, error=str(e))
            return False
    
    def create_lunch_orders(self):
        """Create 4 identical lunch orders for 5€ each"""
        try:
            orders_created = 0
            total_order_value = 0.0
            
            for i, employee in enumerate(self.test_employees):
                # Order: Simple lunch order to get exactly 5€
                order_data = {
                    "employee_id": employee["id"],
                    "department_id": DEPARTMENT_ID,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 0,  # No rolls
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],  # No toppings
                        "has_lunch": True,  # Only lunch (should be 5€)
                        "boiled_eggs": 0,
                        "has_coffee": False  # No coffee
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    self.test_orders.append(order)
                    orders_created += 1
                    order_price = order.get('total_price', 0)
                    total_order_value += order_price
                    print(f"   Created lunch order for {employee['name']}: €{order_price:.2f}")
                else:
                    print(f"   Failed to create order for {employee['name']}: {response.status_code} - {response.text}")
            
            if orders_created == 4:
                self.log_result(
                    "Create Fresh Lunch Orders",
                    True,
                    f"Successfully created 4 fresh lunch orders, total value: €{total_order_value:.2f}"
                )
                return True
            else:
                self.log_result(
                    "Create Fresh Lunch Orders",
                    False,
                    error=f"Could only create {orders_created} orders, need exactly 4"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Fresh Lunch Orders", False, error=str(e))
            return False
    
    def get_employee_balances(self):
        """Get current balances for all test employees"""
        try:
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            
            if response.status_code != 200:
                return None
            
            employees = response.json()
            balances = {}
            
            for test_emp in self.test_employees:
                for emp in employees:
                    if emp["id"] == test_emp["id"]:
                        balances[test_emp["name"]] = emp.get("breakfast_balance", 0.0)
                        break
            
            return balances
                
        except Exception as e:
            print(f"Error getting balances: {e}")
            return None
    
    def sponsor_lunch_fresh(self):
        """Employee 4 sponsors lunch for all 4 employees (fresh sponsoring)"""
        try:
            # Get initial balances
            initial_balances = self.get_employee_balances()
            if not initial_balances:
                self.log_result(
                    "Sponsor Lunch Fresh",
                    False,
                    error="Could not get initial employee balances"
                )
                return False
            
            print(f"\n   💰 INITIAL BALANCES:")
            total_initial = 0.0
            for name, balance in initial_balances.items():
                print(f"   - {name}: €{balance:.2f}")
                total_initial += balance
            print(f"   - TOTAL INITIAL: €{total_initial:.2f}")
            
            # Employee 4 (index 3) sponsors lunch for everyone
            sponsor_employee = self.test_employees[3]
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
                sponsored_items = sponsor_result.get("sponsored_items", "")
                total_cost = sponsor_result.get("total_cost", 0)
                affected_employees = sponsor_result.get("affected_employees", 0)
                sponsor_name = sponsor_result.get("sponsor", "")
                
                print(f"\n   🎁 FRESH LUNCH SPONSORING RESULT:")
                print(f"   - Sponsor: {sponsor_name}")
                print(f"   - Sponsored items: {sponsored_items}")
                print(f"   - Total cost: €{total_cost:.2f}")
                print(f"   - Affected employees: {affected_employees}")
                
                # Get final balances
                final_balances = self.get_employee_balances()
                if not final_balances:
                    self.log_result(
                        "Sponsor Lunch Fresh",
                        False,
                        error="Could not get final employee balances"
                    )
                    return False
                
                print(f"\n   💰 FINAL BALANCES:")
                total_final = 0.0
                for name, balance in final_balances.items():
                    print(f"   - {name}: €{balance:.2f}")
                    total_final += balance
                print(f"   - TOTAL FINAL: €{total_final:.2f}")
                
                # Verify saldo conservation
                saldo_diff = abs(total_final - total_initial)
                print(f"\n   🔍 SALDO CONSERVATION CHECK:")
                print(f"   - Initial total: €{total_initial:.2f}")
                print(f"   - Final total: €{total_final:.2f}")
                print(f"   - Difference: €{saldo_diff:.2f}")
                
                # Verify sponsor payment logic
                sponsor_initial = initial_balances.get(sponsor_employee["name"], 0.0)
                sponsor_final = final_balances.get(sponsor_employee["name"], 0.0)
                sponsor_payment = sponsor_final - sponsor_initial
                
                print(f"\n   🎯 SPONSOR PAYMENT ANALYSIS:")
                print(f"   - Sponsor initial balance: €{sponsor_initial:.2f}")
                print(f"   - Sponsor final balance: €{sponsor_final:.2f}")
                print(f"   - Sponsor net payment: €{sponsor_payment:.2f}")
                print(f"   - Expected net payment: €15.00 (3 others × €5.00)")
                
                # Check if sponsor paid the correct amount (15€ for 3 others, not 20€ for all 4)
                expected_net_payment = 15.0  # 3 others × 5€ each
                payment_diff = abs(sponsor_payment - expected_net_payment)
                
                if saldo_diff < 0.01 and payment_diff < 0.01:
                    self.log_result(
                        "Sponsor Lunch Fresh",
                        True,
                        f"✅ FRESH SPONSORING SUCCESS! Saldo conserved (diff: €{saldo_diff:.2f}), sponsor paid correct net amount (€{sponsor_payment:.2f} vs expected €{expected_net_payment:.2f})"
                    )
                    return True
                else:
                    self.log_result(
                        "Sponsor Lunch Fresh",
                        False,
                        error=f"❌ FRESH SPONSORING FAILED! Saldo diff: €{saldo_diff:.2f}, sponsor payment diff: €{payment_diff:.2f}"
                    )
                    return False
            else:
                self.log_result(
                    "Sponsor Lunch Fresh",
                    False,
                    error=f"Sponsoring failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Sponsor Lunch Fresh", False, error=str(e))
            return False

    def run_fresh_test(self):
        """Run fresh sponsor test with new employees"""
        print("🎯 STARTING FRESH SPONSOR SALDO CONSERVATION TEST")
        print("=" * 80)
        print("FOCUS: Test complete sponsor flow with fresh employees")
        print("CRITICAL: Verify saldo conservation and correct sponsor payment")
        print("SCENARIO: 4 fresh employees, Employee 4 sponsors lunch for all")
        print("EXPECTED: Sponsor pays 15€ net (for 3 others), total saldo conserved")
        print("=" * 80)
        
        tests_passed = 0
        total_tests = 4
        
        # 1. Authenticate as Department 3 admin
        if self.authenticate_admin():
            tests_passed += 1
        
        # 2. Create 4 fresh employees
        if self.create_fresh_employees():
            tests_passed += 1
        
        # 3. Create 4 fresh lunch orders
        if self.create_lunch_orders():
            tests_passed += 1
        
        # 4. Test fresh sponsoring with complete verification
        if self.sponsor_lunch_fresh():
            tests_passed += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 FRESH SPONSOR TEST SUMMARY")
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
            print("🎉 FRESH SPONSOR SALDO CONSERVATION FIX VERIFIED!")
            print("✅ Total saldo conserved with fresh employees")
            print("✅ Sponsor pays correct net amount (for others only)")
            print("✅ No double-counting bug present")
            return True
        else:
            print("❌ FRESH SPONSOR TEST ISSUES DETECTED")
            return False

if __name__ == "__main__":
    tester = FreshSponsorTest()
    success = tester.run_fresh_test()
    sys.exit(0 if success else 1)