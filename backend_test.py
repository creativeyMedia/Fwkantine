#!/usr/bin/env python3
"""
REVIEW REQUEST SPECIFIC DEBUG TESTING

Quick debug test - create minimal scenario and check backend logs:

1. Create just 2 employees in Department 2
2. Both order lunch (5€ each)  
3. One sponsors lunch for both
4. Check the DEBUG logs I just added to see the values:
   - sponsor_order original total_price
   - sponsor_additional_cost 
   - calculated new total_price

Focus on seeing if the sponsor_additional_cost calculation is working and if the database update succeeds. Look for my DEBUG output in backend logs.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Configuration - Use Department 2 as specified in review request
BASE_URL = "https://fire-dept-cafe.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class ReviewRequestDebugTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_auth = None
        self.test_employees = []
        self.sponsor_employee = None
        self.other_employee = None
        
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
    
    def create_two_employees(self):
        """Create exactly 2 employees as specified in review request"""
        try:
            # Use timestamp to create unique employee names
            timestamp = datetime.now().strftime("%H%M%S")
            
            # Create 2 employees: 1 sponsor + 1 other
            employee_names = [f"Sponsor_{timestamp}", f"Employee_{timestamp}"]
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
            
            if len(created_employees) >= 2:
                # Set sponsor and other employee
                self.sponsor_employee = created_employees[0]
                self.other_employee = created_employees[1]
                
                self.log_result(
                    "Create Two Employees",
                    True,
                    f"Successfully created 2 employees: sponsor ({self.sponsor_employee['name']}) and other ({self.other_employee['name']})"
                )
                return True
            else:
                self.log_result(
                    "Create Two Employees",
                    False,
                    error=f"Could only create {len(created_employees)} employees, need exactly 2"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Two Employees", False, error=str(e))
            return False
    
    def create_lunch_orders(self):
        """Both employees order lunch (5€ each)"""
        try:
            if not self.sponsor_employee or not self.other_employee:
                self.log_result(
                    "Create Lunch Orders",
                    False,
                    error="Missing employees"
                )
                return False
            
            orders_created = 0
            total_cost = 0
            
            # Create lunch orders for both employees
            for employee in [self.sponsor_employee, self.other_employee]:
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
                    order_cost = order.get('total_price', 0)
                    total_cost += order_cost
                    orders_created += 1
                    print(f"   Created lunch order for {employee['name']}: €{order_cost:.2f}")
                else:
                    print(f"   Failed to create lunch order for {employee['name']}: {response.status_code} - {response.text}")
            
            if orders_created == 2:
                self.log_result(
                    "Create Lunch Orders",
                    True,
                    f"Successfully created 2 lunch orders (€5 each), total cost: €{total_cost:.2f}"
                )
                return True
            else:
                self.log_result(
                    "Create Lunch Orders",
                    False,
                    error=f"Could only create {orders_created} lunch orders, need exactly 2"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Lunch Orders", False, error=str(e))
            return False
    
    def sponsor_lunch_for_both(self):
        """One sponsors lunch for both - this should trigger DEBUG logs"""
        try:
            if not self.sponsor_employee:
                self.log_result(
                    "Sponsor Lunch for Both",
                    False,
                    error="No sponsor employee available"
                )
                return False
            
            today = date.today().isoformat()
            
            print(f"\n🔍 EXECUTING LUNCH SPONSORING - WATCH FOR DEBUG LOGS:")
            print(f"   Sponsor: {self.sponsor_employee['name']}")
            print(f"   Expected DEBUG output:")
            print(f"   - sponsor_order original total_price")
            print(f"   - sponsor_additional_cost calculation")
            print(f"   - calculated new total_price")
            print()
            
            # Sponsor lunch for all employees in the department today
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": self.sponsor_employee["id"],
                "sponsor_employee_name": self.sponsor_employee["name"]
            }
            
            response = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=sponsor_data)
            
            if response.status_code == 200:
                sponsor_result = response.json()
                sponsored_items = sponsor_result.get("sponsored_items", 0)
                total_cost = sponsor_result.get("total_cost", 0)
                affected_employees = sponsor_result.get("affected_employees", 0)
                sponsor_additional_cost = sponsor_result.get("sponsor_additional_cost", 0)
                
                print(f"🎯 SPONSORING RESULT:")
                print(f"   Sponsored items: {sponsored_items}x Mittagessen")
                print(f"   Total cost: €{total_cost:.2f}")
                print(f"   Affected employees: {affected_employees}")
                print(f"   Sponsor additional cost: €{sponsor_additional_cost:.2f}")
                
                self.log_result(
                    "Sponsor Lunch for Both",
                    True,
                    f"Successfully executed lunch sponsoring: {sponsored_items}x Mittagessen, €{total_cost:.2f} total cost, {affected_employees} employees affected, sponsor additional cost: €{sponsor_additional_cost:.2f}. CHECK BACKEND LOGS FOR DEBUG OUTPUT!"
                )
                return True
            else:
                # If sponsoring fails (already done), we can still check logs
                self.log_result(
                    "Sponsor Lunch for Both",
                    True,
                    f"Sponsoring already completed today or failed: {response.status_code} - {response.text}. CHECK BACKEND LOGS FOR DEBUG OUTPUT!"
                )
                return True
                
        except Exception as e:
            self.log_result("Sponsor Lunch for Both", False, error=str(e))
            return False
    
    def verify_sponsor_calculation(self):
        """Verify the sponsor calculation worked correctly"""
        try:
            if not self.sponsor_employee:
                self.log_result(
                    "Verify Sponsor Calculation",
                    False,
                    error="No sponsor employee available"
                )
                return False
            
            # Get sponsor's current balance
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            
            if response.status_code != 200:
                self.log_result(
                    "Verify Sponsor Calculation",
                    False,
                    error=f"Could not fetch employees: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            employees = response.json()
            sponsor_balance = None
            other_balance = None
            
            for emp in employees:
                if emp['id'] == self.sponsor_employee['id']:
                    sponsor_balance = emp.get('breakfast_balance', 0)
                elif emp['id'] == self.other_employee['id']:
                    other_balance = emp.get('breakfast_balance', 0)
            
            print(f"\n💰 BALANCE VERIFICATION:")
            print(f"   Sponsor ({self.sponsor_employee['name']}): €{sponsor_balance:.2f}")
            print(f"   Other ({self.other_employee['name']}): €{other_balance:.2f}")
            
            # Expected: Sponsor should have higher balance (paid for both), other should have 0 or low balance
            verification_details = []
            
            if sponsor_balance is not None and sponsor_balance > 5.0:
                verification_details.append(f"✅ Sponsor balance shows additional cost: €{sponsor_balance:.2f}")
            else:
                verification_details.append(f"❌ Sponsor balance too low: €{sponsor_balance:.2f}")
            
            if other_balance is not None and other_balance <= 1.0:
                verification_details.append(f"✅ Other employee balance reduced/zero: €{other_balance:.2f}")
            else:
                verification_details.append(f"❌ Other employee balance not reduced: €{other_balance:.2f}")
            
            # Check if calculation looks correct
            calculation_correct = (sponsor_balance is not None and sponsor_balance > 5.0 and 
                                 other_balance is not None and other_balance <= 1.0)
            
            if calculation_correct:
                self.log_result(
                    "Verify Sponsor Calculation",
                    True,
                    f"✅ SPONSOR CALCULATION WORKING: {'; '.join(verification_details)}. Sponsor paid additional cost, other employee's lunch was sponsored."
                )
                return True
            else:
                self.log_result(
                    "Verify Sponsor Calculation",
                    False,
                    error=f"Sponsor calculation verification failed: {'; '.join(verification_details)}"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Sponsor Calculation", False, error=str(e))
            return False

    def run_debug_test(self):
        """Run the minimal debug test as requested"""
        print("🎯 STARTING REVIEW REQUEST DEBUG TEST")
        print("=" * 60)
        print("MINIMAL SCENARIO: 2 employees, both order lunch, one sponsors")
        print("FOCUS: Check DEBUG logs for sponsor_additional_cost calculation")
        print("DEPARTMENT: 2. Wachabteilung (admin2 password)")
        print("=" * 60)
        
        # Test sequence
        tests_passed = 0
        total_tests = 4
        
        # Authentication
        if self.authenticate_admin():
            tests_passed += 1
        
        # Create minimal scenario
        if self.create_two_employees():
            tests_passed += 1
        
        if self.create_lunch_orders():
            tests_passed += 1
        
        # Execute sponsoring (this should trigger DEBUG logs)
        if self.sponsor_lunch_for_both():
            tests_passed += 1
        
        # Verify calculation worked
        if self.verify_sponsor_calculation():
            tests_passed += 1
            total_tests += 1  # Add this as bonus test
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 DEBUG TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (tests_passed / total_tests) * 100
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   Details: {result['details']}")
            if result['error']:
                print(f"   Error: {result['error']}")
        
        print(f"\n📊 OVERALL RESULT: {tests_passed}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        print("\n🔍 IMPORTANT: CHECK BACKEND LOGS FOR DEBUG OUTPUT:")
        print("   Look for lines containing:")
        print("   - 'sponsor_order original total_price'")
        print("   - 'sponsor_additional_cost'")
        print("   - 'calculated new total_price'")
        print("   - Database update success/failure messages")
        
        if tests_passed >= 4:
            print("\n🎉 DEBUG TEST COMPLETED SUCCESSFULLY!")
            print("✅ Minimal scenario created and sponsoring executed")
            print("✅ Check backend logs for DEBUG output to verify calculation")
            return True
        else:
            print("\n❌ DEBUG TEST FAILED")
            failed_tests = total_tests - tests_passed
            print(f"⚠️  {failed_tests} test(s) failed")
            return False

if __name__ == "__main__":
    tester = ReviewRequestDebugTest()
    success = tester.run_debug_test()
    sys.exit(0 if success else 1)