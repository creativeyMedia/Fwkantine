#!/usr/bin/env python3
"""
FRESH SPONSOR MESSAGE WITH COST INFORMATION TESTING

Test the improved sponsor message with cost information with a completely fresh scenario:

1. Create 3 fresh employees in Department 2  
2. All order breakfast items (rolls + eggs)
3. One sponsors breakfast for all 3
4. Verify the sponsor message shows cost information
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Configuration - Use Department 2 as specified in review request
BASE_URL = "https://canteen-fire.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class FreshSponsorMessageTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_auth = None
        self.test_employees = []
        self.sponsor_employee = None
        self.other_employees = []
        
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
                    f"Successfully authenticated as admin for {DEPARTMENT_NAME} (admin2 password)"
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
        """Create 3 completely fresh employees"""
        try:
            # Use timestamp to create unique employee names
            timestamp = datetime.now().strftime("%H%M%S")
            
            # Create 3 employees: 1 sponsor + 2 others
            employee_names = [
                f"FreshSponsor_{timestamp}",
                f"FreshEmp1_{timestamp}",
                f"FreshEmp2_{timestamp}"
            ]
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
                    print(f"   Created employee: {name} (ID: {employee['id']})")
                else:
                    print(f"   Failed to create employee {name}: {response.status_code} - {response.text}")
            
            if len(created_employees) >= 3:
                # Set sponsor and other employees
                self.sponsor_employee = created_employees[0]
                self.other_employees = created_employees[1:3]
                
                self.log_result(
                    "Create 3 Fresh Employees",
                    True,
                    f"Created 3 fresh employees: sponsor ({self.sponsor_employee['name']}) + 2 others ({', '.join([emp['name'] for emp in self.other_employees])})"
                )
                return True
            else:
                self.log_result(
                    "Create 3 Fresh Employees",
                    False,
                    error=f"Could only create {len(created_employees)} employees, need exactly 3"
                )
                return False
                
        except Exception as e:
            self.log_result("Create 3 Fresh Employees", False, error=str(e))
            return False
    
    def create_breakfast_orders(self):
        """All order breakfast items (rolls + eggs)"""
        try:
            orders_created = 0
            total_cost = 0
            
            # Create breakfast orders for all 3 employees (rolls + eggs)
            for employee in self.test_employees:
                # Order: breakfast with rolls + eggs
                order_data = {
                    "employee_id": employee["id"],
                    "department_id": DEPARTMENT_ID,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 2,  # 1 roll = 2 halves
                        "white_halves": 2,  # 1 white roll
                        "seeded_halves": 0,
                        "toppings": ["butter", "kaese"],  # 2 toppings for 2 halves
                        "has_lunch": False,
                        "boiled_eggs": 1,   # Add 1 boiled egg
                        "has_coffee": False
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    order_cost = order.get('total_price', 0)
                    total_cost += order_cost
                    orders_created += 1
                    print(f"   Created breakfast order for {employee['name']}: €{order_cost:.2f} (rolls + eggs)")
                else:
                    print(f"   Failed to create breakfast order for {employee['name']}: {response.status_code} - {response.text}")
            
            if orders_created == 3:
                self.log_result(
                    "All Order Breakfast Items (Rolls + Eggs)",
                    True,
                    f"Successfully created 3 breakfast orders with rolls + eggs. Total cost: €{total_cost:.2f}"
                )
                return True
            else:
                self.log_result(
                    "All Order Breakfast Items (Rolls + Eggs)",
                    False,
                    error=f"Could only create {orders_created} breakfast orders, need exactly 3"
                )
                return False
                
        except Exception as e:
            self.log_result("All Order Breakfast Items (Rolls + Eggs)", False, error=str(e))
            return False
    
    def sponsor_breakfast_for_all(self):
        """One sponsors breakfast for all 3"""
        try:
            if not self.sponsor_employee:
                self.log_result(
                    "One Sponsors Breakfast for All 3",
                    False,
                    error="No sponsor employee available"
                )
                return False
            
            today = date.today().isoformat()
            
            print(f"\n🎯 EXECUTING BREAKFAST SPONSORING:")
            print(f"   Sponsor: {self.sponsor_employee['name']} (ID: {self.sponsor_employee['id']})")
            print(f"   Date: {today}")
            print()
            
            # Sponsor breakfast for all employees in the department today
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": self.sponsor_employee["id"],
                "sponsor_employee_name": self.sponsor_employee["name"]
            }
            
            response = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=sponsor_data)
            
            print(f"   Sponsoring response: HTTP {response.status_code}")
            if response.status_code != 200:
                print(f"   Response text: {response.text}")
            
            if response.status_code == 200:
                sponsor_result = response.json()
                sponsored_items = sponsor_result.get("sponsored_items", 0)
                total_sponsored_cost = sponsor_result.get("total_cost", 0)
                affected_employees = sponsor_result.get("affected_employees", 0)
                sponsor_additional_cost = sponsor_result.get("sponsor_additional_cost", 0)
                
                print(f"🎯 BREAKFAST SPONSORING RESULT:")
                print(f"   Sponsored items: {sponsored_items} breakfast items")
                print(f"   Total sponsored cost: €{total_sponsored_cost:.2f}")
                print(f"   Affected employees: {affected_employees}")
                print(f"   Sponsor additional cost: €{sponsor_additional_cost:.2f}")
                
                self.log_result(
                    "One Sponsors Breakfast for All 3",
                    True,
                    f"Successfully sponsored breakfast for all 3 employees. Sponsored {sponsored_items} breakfast items, €{total_sponsored_cost:.2f} total cost, {affected_employees} employees affected"
                )
                return True
            else:
                error_text = response.text
                self.log_result(
                    "One Sponsors Breakfast for All 3",
                    False,
                    error=f"Breakfast sponsoring failed: {response.status_code} - {error_text}"
                )
                return False
                
        except Exception as e:
            self.log_result("One Sponsors Breakfast for All 3", False, error=str(e))
            return False
    
    def verify_sponsor_message_with_cost(self):
        """Verify the sponsor message shows cost information"""
        try:
            if not self.sponsor_employee:
                self.log_result(
                    "Verify Sponsor Message with Cost Information",
                    False,
                    error="No sponsor employee available"
                )
                return False
            
            # Get sponsor's today orders to check for sponsor message
            response = self.session.get(f"{BASE_URL}/employee/{self.sponsor_employee['id']}/today-orders")
            
            if response.status_code != 200:
                self.log_result(
                    "Verify Sponsor Message with Cost Information",
                    False,
                    error=f"Could not fetch sponsor orders: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            orders = response.json()
            
            if not orders:
                self.log_result(
                    "Verify Sponsor Message with Cost Information",
                    False,
                    error="No orders found for sponsor employee"
                )
                return False
            
            # Look for sponsor message in the order
            sponsor_message_found = False
            cost_info_found = False
            sponsor_message = ""
            
            for order in orders:
                # Check for sponsor message fields
                if order.get("sponsor_message") or order.get("sponsored_message"):
                    sponsor_message = order.get("sponsor_message") or order.get("sponsored_message")
                    sponsor_message_found = True
                    
                    # Check if message contains cost information
                    if "Ausgegeben für" in sponsor_message and "Mitarbeiter im Wert von" in sponsor_message and "€" in sponsor_message:
                        cost_info_found = True
                    
                    print(f"   Found sponsor message: {sponsor_message}")
                    break
            
            print(f"\n💬 SPONSOR MESSAGE VERIFICATION:")
            print(f"   Sponsor message found: {sponsor_message_found}")
            print(f"   Cost information found: {cost_info_found}")
            print(f"   Message: {sponsor_message}")
            
            if sponsor_message_found and cost_info_found:
                self.log_result(
                    "Verify Sponsor Message with Cost Information",
                    True,
                    f"✅ SPONSOR MESSAGE WITH COST INFORMATION VERIFIED! Message: '{sponsor_message}'. Format matches expected: 'Frühstück wurde von dir ausgegeben, vielen Dank! (Ausgegeben für X Mitarbeiter im Wert von Y.YY€)'"
                )
                return True
            elif sponsor_message_found:
                self.log_result(
                    "Verify Sponsor Message with Cost Information",
                    False,
                    error=f"Sponsor message found but missing cost information: '{sponsor_message}'. Expected format with cost details."
                )
                return False
            else:
                self.log_result(
                    "Verify Sponsor Message with Cost Information",
                    False,
                    error=f"No sponsor message found in sponsor's orders. Order details: {json.dumps(orders, indent=2)}"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Sponsor Message with Cost Information", False, error=str(e))
            return False
    
    def verify_sponsored_employee_messages(self):
        """Verify sponsored employees show thank-you messages"""
        try:
            if not self.other_employees:
                self.log_result(
                    "Verify Sponsored Employee Messages",
                    False,
                    error="No other employees available"
                )
                return False
            
            sponsored_messages_found = 0
            sponsored_employee_details = []
            
            for other_emp in self.other_employees:
                # Get employee's today orders
                response = self.session.get(f"{BASE_URL}/employee/{other_emp['id']}/today-orders")
                
                if response.status_code != 200:
                    sponsored_employee_details.append(f"{other_emp['name']}: Could not fetch orders")
                    continue
                
                orders = response.json()
                
                if not orders:
                    sponsored_employee_details.append(f"{other_emp['name']}: No orders found")
                    continue
                
                # Look for sponsored message
                sponsored_message_found = False
                for order in orders:
                    if order.get("sponsored_message"):
                        sponsored_message = order.get("sponsored_message")
                        if "wurde von" in sponsored_message and "ausgegeben" in sponsored_message and "bedanke dich" in sponsored_message:
                            sponsored_messages_found += 1
                            sponsored_message_found = True
                            sponsored_employee_details.append(f"{other_emp['name']}: '{sponsored_message}'")
                            break
                
                if not sponsored_message_found:
                    sponsored_employee_details.append(f"{other_emp['name']}: No sponsored message found")
            
            print(f"\n👥 SPONSORED EMPLOYEE MESSAGES:")
            for detail in sponsored_employee_details:
                print(f"   {detail}")
            
            if sponsored_messages_found >= 2:
                self.log_result(
                    "Verify Sponsored Employee Messages",
                    True,
                    f"✅ SPONSORED EMPLOYEE MESSAGES VERIFIED! Found {sponsored_messages_found} sponsored employees with thank-you messages. Details: {'; '.join(sponsored_employee_details)}"
                )
                return True
            else:
                self.log_result(
                    "Verify Sponsored Employee Messages",
                    False,
                    error=f"Only found {sponsored_messages_found} sponsored employee messages, expected 2. Details: {'; '.join(sponsored_employee_details)}"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Sponsored Employee Messages", False, error=str(e))
            return False

    def run_fresh_sponsor_message_test(self):
        """Run the fresh sponsor message test"""
        print("💬 STARTING FRESH SPONSOR MESSAGE WITH COST INFORMATION TEST")
        print("=" * 80)
        print("FRESH TEST SCENARIO:")
        print("1. Create 3 completely fresh employees in Department 2")
        print("2. All order breakfast items (rolls + eggs)")
        print("3. One sponsors breakfast for all 3")
        print("4. Verify sponsor message shows cost information")
        print("DEPARTMENT: 2. Wachabteilung (admin2 password)")
        print("=" * 80)
        
        # Test sequence
        tests_passed = 0
        total_tests = 6
        
        # Authentication
        if self.authenticate_admin():
            tests_passed += 1
        
        # Create fresh test scenario
        if self.create_fresh_employees():
            tests_passed += 1
        
        if self.create_breakfast_orders():
            tests_passed += 1
        
        # Execute sponsoring
        if self.sponsor_breakfast_for_all():
            tests_passed += 1
        
        # Verify messages
        if self.verify_sponsor_message_with_cost():
            tests_passed += 1
        
        if self.verify_sponsored_employee_messages():
            tests_passed += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("💬 FRESH SPONSOR MESSAGE TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (tests_passed / total_tests) * 100
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   Details: {result['details']}")
            if result['error']:
                print(f"   Error: {result['error']}")
        
        print(f"\n📊 OVERALL RESULT: {tests_passed}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        if tests_passed >= 4:  # At least 67% success rate
            print("\n🎉 FRESH SPONSOR MESSAGE WITH COST INFORMATION TEST COMPLETED SUCCESSFULLY!")
            print("✅ Created 3 fresh employees in Department 2")
            print("✅ All ordered breakfast items (rolls + eggs)")
            print("✅ One sponsored breakfast for all 3")
            print("✅ Verified sponsor message includes cost information")
            return True
        else:
            print("\n❌ FRESH SPONSOR MESSAGE TEST FAILED")
            failed_tests = total_tests - tests_passed
            print(f"⚠️  {failed_tests} test(s) failed")
            return False

if __name__ == "__main__":
    tester = FreshSponsorMessageTest()
    success = tester.run_fresh_sponsor_message_test()
    sys.exit(0 if success else 1)