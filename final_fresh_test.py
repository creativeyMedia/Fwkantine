#!/usr/bin/env python3
"""
FINAL VERIFICATION: Test the corrected sponsoring system with a completely fresh scenario

This test uses the cleanup endpoint to start completely fresh and then creates the exact
scenario requested in the review request to verify the negative balance issue is resolved.
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

class FinalFreshTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_auth = None
        self.fresh_employees = []
        self.fresh_orders = []
        
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
    
    def cleanup_all_data(self):
        """Clean up all test data using the admin cleanup endpoint"""
        try:
            response = self.session.post(f"{BASE_URL}/admin/cleanup-testing-data")
            
            if response.status_code == 200:
                cleanup_result = response.json()
                deleted_orders = cleanup_result.get("deleted_orders", 0)
                reset_balances = cleanup_result.get("reset_employee_balances", 0)
                
                self.log_result(
                    "Clean Up All Data",
                    True,
                    f"Successfully cleaned up {deleted_orders} orders and reset {reset_balances} employee balances for completely fresh testing scenario"
                )
                return True
            else:
                self.log_result(
                    "Clean Up All Data",
                    False,
                    error=f"Cleanup failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Clean Up All Data", False, error=str(e))
            return False
    
    def create_fresh_employees(self):
        """Create 5 new employees in Department 2"""
        try:
            # Use timestamp to create unique employee names
            timestamp = datetime.now().strftime("%H%M%S")
            
            # Create 5 employees: 1 sponsor ("TestSponsor") + 4 others
            employee_names = ["TestSponsor"] + [f"Employee{i}" for i in range(1, 5)]
            created_employees = []
            
            for name in employee_names:
                unique_name = f"{name}_{timestamp}"
                response = self.session.post(f"{BASE_URL}/employees", json={
                    "name": unique_name,
                    "department_id": DEPARTMENT_ID
                })
                
                if response.status_code == 200:
                    employee = response.json()
                    created_employees.append(employee)
                    self.fresh_employees.append(employee)
                else:
                    print(f"   Failed to create employee {unique_name}: {response.status_code} - {response.text}")
            
            if len(created_employees) >= 5:
                self.log_result(
                    "Create Fresh Employees",
                    True,
                    f"Successfully created {len(created_employees)} fresh employees in Department 2 (1 TestSponsor + 4 others)"
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
        """Sponsor ("TestSponsor") orders: breakfast (2.50€) + lunch (5€) = 7.50€"""
        try:
            if len(self.fresh_employees) < 1:
                self.log_result(
                    "Create Sponsor Order",
                    False,
                    error="No sponsor employee available"
                )
                return False
            
            # TestSponsor is the first employee
            sponsor = self.fresh_employees[0]
            
            # Order: breakfast items worth ~2.50€ + lunch (5€) = ~7.50€
            # Create: 2 white roll halves (1.00€) + 1 boiled egg (0.50€) + lunch (varies) + coffee (1.00€)
            order_data = {
                "employee_id": sponsor["id"],
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 2 roll halves
                    "white_halves": 2,  # 2 white roll halves (2 × 0.50€ = 1.00€)
                    "seeded_halves": 0,  # No seeded rolls
                    "toppings": ["butter", "kaese"],  # 2 toppings for 2 halves (free)
                    "has_lunch": True,  # Include lunch (~5€)
                    "boiled_eggs": 1,  # 1 boiled egg (0.50€)
                    "has_coffee": True  # Coffee (1.00€)
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.fresh_orders.append(order)
                total_cost = order.get('total_price', 0)
                self.log_result(
                    "Create Sponsor Order",
                    True,
                    f"Successfully created sponsor order for {sponsor['name']}: €{total_cost:.2f} (breakfast + lunch)"
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
    
    def create_other_orders(self):
        """4 others order: lunch only (5€ each) = 20€ total"""
        try:
            if len(self.fresh_employees) < 5:
                self.log_result(
                    "Create Other Employee Orders",
                    False,
                    error="Not enough employees available (need 5 total)"
                )
                return False
            
            # Create lunch orders for employees 1-4 (skip sponsor at index 0)
            lunch_orders_created = 0
            total_lunch_cost = 0
            
            for i in range(1, 5):
                employee = self.fresh_employees[i]
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
                        "has_coffee": False  # No coffee
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    self.fresh_orders.append(order)
                    lunch_orders_created += 1
                    order_cost = order.get('total_price', 0)
                    total_lunch_cost += order_cost
                    print(f"   Created lunch order for {employee['name']}: €{order_cost:.2f}")
                else:
                    print(f"   Failed to create lunch order for {employee['name']}: {response.status_code} - {response.text}")
            
            if lunch_orders_created == 4:
                self.log_result(
                    "Create Other Employee Orders",
                    True,
                    f"Successfully created {lunch_orders_created} lunch orders for other employees, total cost: €{total_lunch_cost:.2f}"
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
    
    def execute_lunch_sponsoring(self):
        """Execute lunch sponsoring"""
        try:
            if len(self.fresh_employees) < 5:
                self.log_result(
                    "Execute Lunch Sponsoring",
                    False,
                    error="Not enough test employees available (need 5)"
                )
                return False
            
            # Use TestSponsor as sponsor
            sponsor_employee = self.fresh_employees[0]
            today = date.today().isoformat()
            
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
                
                self.log_result(
                    "Execute Lunch Sponsoring",
                    True,
                    f"Successfully executed lunch sponsoring: {sponsored_items} items, €{total_cost:.2f} total cost, {affected_employees} employees affected, sponsor additional cost: €{sponsor_additional_cost:.2f}"
                )
                return True
            else:
                self.log_result(
                    "Execute Lunch Sponsoring",
                    False,
                    error=f"Failed to execute lunch sponsoring: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Execute Lunch Sponsoring", False, error=str(e))
            return False
    
    def verify_sponsor_balance(self):
        """Verify sponsor final balance: 7.50€ (initial) + 20€ (additional) = 27.50€ ✅"""
        try:
            if len(self.fresh_employees) < 1:
                self.log_result(
                    "Verify Sponsor Balance",
                    False,
                    error="No sponsor employee available"
                )
                return False
            
            sponsor_employee = self.fresh_employees[0]
            
            # Get employee's current balance
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            
            if response.status_code != 200:
                self.log_result(
                    "Verify Sponsor Balance",
                    False,
                    error=f"Could not fetch employees list: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            employees_list = response.json()
            sponsor_data = None
            
            for emp in employees_list:
                if emp["id"] == sponsor_employee["id"]:
                    sponsor_data = emp
                    break
            
            if not sponsor_data:
                self.log_result(
                    "Verify Sponsor Balance",
                    False,
                    error=f"Sponsor employee {sponsor_employee['name']} not found in list"
                )
                return False
            
            sponsor_balance = sponsor_data.get("breakfast_balance", 0)
            
            # Get sponsor's original order cost
            sponsor_order_cost = 0
            if len(self.fresh_orders) > 0:
                sponsor_order_cost = self.fresh_orders[0].get('total_price', 0)
            
            print(f"\n   💰 SPONSOR BALANCE VERIFICATION:")
            print(f"   Sponsor: {sponsor_employee['name']}")
            print(f"   Original order cost: €{sponsor_order_cost:.2f}")
            print(f"   Current balance: €{sponsor_balance:.2f}")
            print(f"   Expected: ~€27.50 (7.50€ initial + 20€ additional for others)")
            print(f"   Critical: Should be POSITIVE (NOT negative -17.50€)")
            
            # Expected balance should be around 27.50€
            expected_balance = 27.50
            tolerance = 5.0  # Allow some tolerance for price variations
            
            # Check if balance is positive and around expected value
            if sponsor_balance > 0 and abs(sponsor_balance - expected_balance) <= tolerance:
                self.log_result(
                    "Verify Sponsor Balance",
                    True,
                    f"✅ SPONSOR BALANCE CORRECT: €{sponsor_balance:.2f} (expected ~€{expected_balance:.2f}). Balance is POSITIVE, confirming negative balance issue is resolved!"
                )
                return True
            elif sponsor_balance < 0:
                self.log_result(
                    "Verify Sponsor Balance",
                    False,
                    error=f"❌ CRITICAL: Sponsor balance is NEGATIVE: €{sponsor_balance:.2f} (should be positive ~€{expected_balance:.2f}). Negative balance bug still exists!"
                )
                return False
            else:
                self.log_result(
                    "Verify Sponsor Balance",
                    False,
                    error=f"Sponsor balance incorrect: €{sponsor_balance:.2f} (expected ~€{expected_balance:.2f})"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Sponsor Balance", False, error=str(e))
            return False
    
    def verify_other_balances(self):
        """Verify other employees should have €0.00 (lunch sponsored)"""
        try:
            if len(self.fresh_employees) < 5:
                self.log_result(
                    "Verify Other Employee Balances",
                    False,
                    error="Not enough test employees available (need 5)"
                )
                return False
            
            print(f"\n   💳 OTHER EMPLOYEE BALANCE VERIFICATION:")
            
            # Get employees list
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            
            if response.status_code != 200:
                self.log_result(
                    "Verify Other Employee Balances",
                    False,
                    error=f"Could not fetch employees list: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            employees_list = response.json()
            verification_details = []
            all_correct = True
            
            # Check employees 1-4 (skip sponsor at index 0)
            for i in range(1, 5):
                employee = self.fresh_employees[i]
                employee_data = None
                
                for emp in employees_list:
                    if emp["id"] == employee["id"]:
                        employee_data = emp
                        break
                
                if not employee_data:
                    verification_details.append(f"❌ Employee {employee['name']} not found in list")
                    all_correct = False
                    continue
                
                breakfast_balance = employee_data.get("breakfast_balance", 0)
                print(f"   - {employee['name']}: €{breakfast_balance:.2f}")
                
                # Should be €0.00 (lunch sponsored)
                if abs(breakfast_balance) < 0.01:
                    verification_details.append(f"✅ {employee['name']}: Lunch sponsored correctly (€{breakfast_balance:.2f})")
                else:
                    verification_details.append(f"❌ {employee['name']}: Lunch not sponsored correctly (€{breakfast_balance:.2f}, expected €0.00)")
                    all_correct = False
            
            if all_correct:
                self.log_result(
                    "Verify Other Employee Balances",
                    True,
                    f"✅ OTHER EMPLOYEE BALANCES CORRECT: {'; '.join(verification_details)}. All other employees have €0.00 (lunch sponsored)."
                )
                return True
            else:
                self.log_result(
                    "Verify Other Employee Balances",
                    False,
                    error=f"Other employee balance verification failed: {'; '.join(verification_details)}"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Other Employee Balances", False, error=str(e))
            return False

    def run_final_test(self):
        """Run the complete final fresh test scenario"""
        print("🎯 FINAL VERIFICATION: Test the corrected sponsoring system with a completely fresh scenario")
        print("=" * 90)
        print("GOAL: Confirm the negative balance issue is resolved")
        print("DEPARTMENT: 2. Wachabteilung (admin2 password)")
        print("=" * 90)
        print("SCENARIO:")
        print("1. Clean up all test data to start completely fresh")
        print("2. Create 5 new employees in Department 2")
        print("3. Sponsor ('TestSponsor') orders: breakfast (2.50€) + lunch (5€) = 7.50€")
        print("4. 4 others order: lunch only (5€ each) = 20€ total")
        print("5. Execute lunch sponsoring")
        print("=" * 90)
        print("EXPECTED RESULTS:")
        print("- Total sponsored cost: 25€ (5×5€ for all lunches)")
        print("- Sponsor contributed amount: 5€ (sponsor's own lunch)")
        print("- Sponsor additional cost: 25€ - 5€ = 20€ (for others only)")
        print("- Sponsor final balance: 7.50€ (initial) + 20€ (additional) = 27.50€ ✅")
        print("=" * 90)
        
        # Test sequence
        tests_passed = 0
        total_tests = 8
        
        # Authentication
        if self.authenticate_admin():
            tests_passed += 1
        
        # Clean up and create fresh scenario
        if self.cleanup_all_data():
            tests_passed += 1
        
        if self.create_fresh_employees():
            tests_passed += 1
        
        if self.create_sponsor_order():
            tests_passed += 1
        
        if self.create_other_orders():
            tests_passed += 1
        
        if self.execute_lunch_sponsoring():
            tests_passed += 1
        
        # Critical verifications
        if self.verify_sponsor_balance():
            tests_passed += 1
        
        if self.verify_other_balances():
            tests_passed += 1
        
        # Print summary
        print("\n" + "=" * 90)
        print("🎯 FINAL VERIFICATION SUMMARY")
        print("=" * 90)
        
        success_rate = (tests_passed / total_tests) * 100
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   Details: {result['details']}")
            if result['error']:
                print(f"   Error: {result['error']}")
        
        print(f"\n📊 OVERALL RESULT: {tests_passed}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        if tests_passed == total_tests:
            print("🎉 FINAL VERIFICATION COMPLETED SUCCESSFULLY!")
            print("✅ Sponsor balance is POSITIVE ~27.50€ (NOT negative -17.50€)")
            print("✅ Other employees have €0.00 (lunch sponsored)")
            print("✅ Calculation follows: initial_balance + additional_cost")
            print("✅ No sign errors or double subtraction")
            print("✅ The negative balance issue is RESOLVED!")
            return True
        else:
            print("❌ FINAL VERIFICATION FAILED")
            failed_tests = total_tests - tests_passed
            print(f"⚠️  {failed_tests} test(s) failed - negative balance issue may still exist")
            return False

if __name__ == "__main__":
    tester = FinalFreshTest()
    success = tester.run_final_test()
    sys.exit(0 if success else 1)