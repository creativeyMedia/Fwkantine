#!/usr/bin/env python3
"""
Gastmitarbeiter-Marker Functionality Test Suite
==============================================

This test suite tests the newly implemented Gastmitarbeiter-Marker functionality 
in the Admin Dashboard's Bestellverlauf (order history) section.

NEW FUNCTIONALITY TESTED:
1. BACKEND DEPARTMENT INFORMATION:
   - breakfast-history API contains employee_department_id and order_department_id
   - System recognizes when employee from another department orders
   - Department information is correctly provided for frontend processing

2. GUEST EMPLOYEE RECOGNITION:
   - System detects when employee_department_id ≠ order_department_id
   - Proper data structure for frontend to display guest markers

3. MARKER DISPLAY LOGIC:
   - Frontend can identify guest employees from other departments
   - Correct marker text: "👥 Gast aus X. WA"

4. TEST SCENARIOS:
   - Regular employee from 1. WA orders in 1. WA → NO marker
   - Guest employee from 2. WA orders in 1. WA → Marker "👥 Gast aus 2. WA"
   - Guest employee from 3. WA orders in 1. WA → Marker "👥 Gast aus 3. WA"

EXPECTED RESULTS:
- ✅ breakfast-history API contains Department-IDs for each employee
- ✅ Guest employees show marker data in Admin Dashboard
- ✅ Regular employees show NO marker in own department
- ✅ Marker data correct for frontend processing
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class GastmitarbeiterMarkerTest:
    def __init__(self):
        self.target_department_id = "fw4abteilung1"  # Target department (1. WA)
        self.guest_department_2_id = "fw4abteilung2"  # Guest from 2. WA
        self.guest_department_3_id = "fw4abteilung3"  # Guest from 3. WA
        
        # Admin credentials for target department
        self.admin_credentials = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        
        # Test employees
        self.regular_employee_id = None
        self.guest_employee_2_id = None
        self.guest_employee_3_id = None
        
        # Test employee names with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.regular_employee_name = f"RegularEmployee_{timestamp}"
        self.guest_employee_2_name = f"GuestEmployee2_{timestamp}"
        self.guest_employee_3_name = f"GuestEmployee3_{timestamp}"
        
        # Test order IDs
        self.regular_order_id = None
        self.guest_order_2_id = None
        self.guest_order_3_id = None
        
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
            
    def test_get_departments(self):
        """Test that all required departments exist"""
        try:
            response = requests.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                departments = response.json()
                dept_ids = [dept['id'] for dept in departments]
                
                required_depts = [self.target_department_id, self.guest_department_2_id, self.guest_department_3_id]
                missing_depts = [dept for dept in required_depts if dept not in dept_ids]
                
                if not missing_depts:
                    self.success(f"All required departments found: {required_depts}")
                    for dept in departments:
                        self.log(f"  - {dept['name']} (ID: {dept['id']})")
                    return True
                else:
                    self.error(f"Missing departments: {missing_depts}")
                    return False
            else:
                self.error(f"Failed to get departments: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception getting departments: {str(e)}")
            return False
            
    def authenticate_admin(self):
        """Authenticate as department admin for target department"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.admin_credentials)
            if response.status_code == 200:
                self.success(f"Admin authentication successful for {self.target_department_id}")
                return True
            else:
                self.error(f"Admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Admin authentication exception: {str(e)}")
            return False
            
    def create_test_employees(self):
        """Create test employees in different departments"""
        try:
            # Create regular employee in target department (1. WA)
            regular_employee_data = {
                "name": self.regular_employee_name,
                "department_id": self.target_department_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=regular_employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.regular_employee_id = employee["id"]
                self.success(f"Created regular employee: {self.regular_employee_name} in {self.target_department_id}")
            else:
                self.error(f"Failed to create regular employee: {response.status_code} - {response.text}")
                return False
                
            # Create guest employee from 2. WA
            guest_employee_2_data = {
                "name": self.guest_employee_2_name,
                "department_id": self.guest_department_2_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=guest_employee_2_data)
            if response.status_code == 200:
                employee = response.json()
                self.guest_employee_2_id = employee["id"]
                self.success(f"Created guest employee: {self.guest_employee_2_name} in {self.guest_department_2_id}")
            else:
                self.error(f"Failed to create guest employee 2: {response.status_code} - {response.text}")
                return False
                
            # Create guest employee from 3. WA
            guest_employee_3_data = {
                "name": self.guest_employee_3_name,
                "department_id": self.guest_department_3_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=guest_employee_3_data)
            if response.status_code == 200:
                employee = response.json()
                self.guest_employee_3_id = employee["id"]
                self.success(f"Created guest employee: {self.guest_employee_3_name} in {self.guest_department_3_id}")
                return True
            else:
                self.error(f"Failed to create guest employee 3: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception creating test employees: {str(e)}")
            return False
            
    def create_test_orders(self):
        """Create test orders to test the marker functionality"""
        try:
            # Create order for regular employee in their home department (1. WA → 1. WA)
            regular_order_data = {
                "employee_id": self.regular_employee_id,
                "department_id": self.target_department_id,  # Same as employee's home department
                "order_type": "breakfast",
                "notes": "Regular employee order - no marker expected",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["Rührei", "Spiegelei"],
                    "has_lunch": False,
                    "boiled_eggs": 0,
                    "fried_eggs": 0,
                    "has_coffee": True
                }]
            }
            
            response = requests.post(f"{API_BASE}/orders", json=regular_order_data)
            if response.status_code == 200:
                order = response.json()
                self.regular_order_id = order["id"]
                self.success(f"Created regular employee order: {self.regular_employee_name} → {self.target_department_id}")
            else:
                self.error(f"Failed to create regular order: {response.status_code} - {response.text}")
                return False
                
            # Create order for guest employee from 2. WA ordering in 1. WA
            guest_order_2_data = {
                "employee_id": self.guest_employee_2_id,
                "department_id": self.target_department_id,  # Different from employee's home department
                "order_type": "breakfast",
                "notes": "Guest from 2. WA - marker expected",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["Rührei", "Spiegelei"],
                    "has_lunch": True,
                    "boiled_eggs": 1,
                    "fried_eggs": 0,
                    "has_coffee": True
                }]
            }
            
            response = requests.post(f"{API_BASE}/orders", json=guest_order_2_data)
            if response.status_code == 200:
                order = response.json()
                self.guest_order_2_id = order["id"]
                self.success(f"Created guest order 2: {self.guest_employee_2_name} ({self.guest_department_2_id}) → {self.target_department_id}")
            else:
                self.error(f"Failed to create guest order 2: {response.status_code} - {response.text}")
                return False
                
            # Create order for guest employee from 3. WA ordering in 1. WA
            guest_order_3_data = {
                "employee_id": self.guest_employee_3_id,
                "department_id": self.target_department_id,  # Different from employee's home department
                "order_type": "breakfast",
                "notes": "Guest from 3. WA - marker expected",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 2,
                    "seeded_halves": 0,
                    "toppings": ["Spiegelei", "Spiegelei"],
                    "has_lunch": False,
                    "boiled_eggs": 0,
                    "fried_eggs": 1,
                    "has_coffee": False
                }]
            }
            
            response = requests.post(f"{API_BASE}/orders", json=guest_order_3_data)
            if response.status_code == 200:
                order = response.json()
                self.guest_order_3_id = order["id"]
                self.success(f"Created guest order 3: {self.guest_employee_3_name} ({self.guest_department_3_id}) → {self.target_department_id}")
                return True
            else:
                self.error(f"Failed to create guest order 3: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception creating test orders: {str(e)}")
            return False
            
    def test_breakfast_history_department_ids(self):
        """Test that breakfast-history API contains employee_department_id and order_department_id"""
        try:
            response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.target_department_id}")
            if response.status_code == 200:
                history_data = response.json()
                self.success("Breakfast history API accessible")
                
                # Check if history contains our test orders
                found_regular = False
                found_guest_2 = False
                found_guest_3 = False
                
                if history_data.get("history"):
                    for day_data in history_data["history"]:
                        employee_orders = day_data.get("employee_orders", {})
                        
                        for employee_key, employee_data in employee_orders.items():
                            # Check for required fields
                            employee_dept_id = employee_data.get("employee_department_id")
                            order_dept_id = employee_data.get("order_department_id")
                            
                            if employee_dept_id is None or order_dept_id is None:
                                self.error(f"Missing department IDs in employee data: {employee_key}")
                                self.error(f"  employee_department_id: {employee_dept_id}")
                                self.error(f"  order_department_id: {order_dept_id}")
                                return False
                            
                            # Check our test employees
                            if self.regular_employee_name in employee_key:
                                found_regular = True
                                if employee_dept_id == self.target_department_id and order_dept_id == self.target_department_id:
                                    self.success(f"Regular employee department IDs correct: {employee_dept_id} = {order_dept_id}")
                                else:
                                    self.error(f"Regular employee department IDs incorrect: {employee_dept_id} ≠ {order_dept_id}")
                                    return False
                                    
                            elif self.guest_employee_2_name in employee_key:
                                found_guest_2 = True
                                if employee_dept_id == self.guest_department_2_id and order_dept_id == self.target_department_id:
                                    self.success(f"Guest employee 2 department IDs correct: {employee_dept_id} ≠ {order_dept_id}")
                                else:
                                    self.error(f"Guest employee 2 department IDs incorrect: {employee_dept_id}, {order_dept_id}")
                                    return False
                                    
                            elif self.guest_employee_3_name in employee_key:
                                found_guest_3 = True
                                if employee_dept_id == self.guest_department_3_id and order_dept_id == self.target_department_id:
                                    self.success(f"Guest employee 3 department IDs correct: {employee_dept_id} ≠ {order_dept_id}")
                                else:
                                    self.error(f"Guest employee 3 department IDs incorrect: {employee_dept_id}, {order_dept_id}")
                                    return False
                
                # Verify all test employees were found
                if found_regular and found_guest_2 and found_guest_3:
                    self.success("All test employees found in breakfast history with correct department IDs")
                    return True
                else:
                    self.error(f"Missing test employees in history: regular={found_regular}, guest2={found_guest_2}, guest3={found_guest_3}")
                    return False
                    
            else:
                self.error(f"Failed to get breakfast history: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception testing breakfast history department IDs: {str(e)}")
            return False
            
    def test_guest_recognition_logic(self):
        """Test that the system can recognize guest employees vs regular employees"""
        try:
            response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.target_department_id}")
            if response.status_code == 200:
                history_data = response.json()
                
                guest_employees_found = 0
                regular_employees_found = 0
                
                if history_data.get("history"):
                    for day_data in history_data["history"]:
                        employee_orders = day_data.get("employee_orders", {})
                        
                        for employee_key, employee_data in employee_orders.items():
                            employee_dept_id = employee_data.get("employee_department_id")
                            order_dept_id = employee_data.get("order_department_id")
                            
                            # Check if this is a guest employee (different departments)
                            if employee_dept_id != order_dept_id:
                                guest_employees_found += 1
                                self.log(f"Guest employee detected: {employee_key} ({employee_dept_id} → {order_dept_id})")
                            else:
                                regular_employees_found += 1
                                self.log(f"Regular employee detected: {employee_key} ({employee_dept_id} = {order_dept_id})")
                
                if guest_employees_found >= 2:  # We created 2 guest employees
                    self.success(f"Guest employee recognition working: {guest_employees_found} guest employees detected")
                else:
                    self.error(f"Guest employee recognition failed: only {guest_employees_found} guest employees detected")
                    return False
                    
                if regular_employees_found >= 1:  # We created 1 regular employee
                    self.success(f"Regular employee recognition working: {regular_employees_found} regular employees detected")
                    return True
                else:
                    self.error(f"Regular employee recognition failed: only {regular_employees_found} regular employees detected")
                    return False
                    
            else:
                self.error(f"Failed to get breakfast history for guest recognition: {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Exception testing guest recognition logic: {str(e)}")
            return False
            
    def test_marker_data_structure(self):
        """Test that the data structure supports frontend marker display"""
        try:
            response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.target_department_id}")
            if response.status_code == 200:
                history_data = response.json()
                
                # Check that we can extract department names for marker display
                departments_response = requests.get(f"{API_BASE}/departments")
                if departments_response.status_code != 200:
                    self.error("Failed to get departments for name mapping")
                    return False
                    
                departments = departments_response.json()
                dept_name_map = {dept['id']: dept['name'] for dept in departments}
                
                marker_data_correct = True
                
                if history_data.get("history"):
                    for day_data in history_data["history"]:
                        employee_orders = day_data.get("employee_orders", {})
                        
                        for employee_key, employee_data in employee_orders.items():
                            employee_dept_id = employee_data.get("employee_department_id")
                            order_dept_id = employee_data.get("order_department_id")
                            
                            # Test marker logic for guest employees
                            if employee_dept_id != order_dept_id:
                                # This should be a guest employee
                                employee_dept_name = dept_name_map.get(employee_dept_id, employee_dept_id)
                                
                                # Extract department number for marker text
                                if "Wachabteilung" in employee_dept_name:
                                    dept_number = employee_dept_name.split(".")[0]
                                    expected_marker = f"👥 Gast aus {dept_number}. WA"
                                    
                                    self.success(f"Marker data available for {employee_key}: {expected_marker}")
                                else:
                                    self.error(f"Cannot extract department number from: {employee_dept_name}")
                                    marker_data_correct = False
                            else:
                                # Regular employee - no marker expected
                                self.log(f"No marker needed for regular employee: {employee_key}")
                
                if marker_data_correct:
                    self.success("Marker data structure supports frontend display")
                    return True
                else:
                    self.error("Marker data structure has issues")
                    return False
                    
            else:
                self.error(f"Failed to get breakfast history for marker data test: {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Exception testing marker data structure: {str(e)}")
            return False
            
    def test_consistency_check(self):
        """Test that marker logic is consistent across all orders"""
        try:
            response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.target_department_id}")
            if response.status_code == 200:
                history_data = response.json()
                
                consistency_issues = []
                total_employees_checked = 0
                
                if history_data.get("history"):
                    for day_data in history_data["history"]:
                        employee_orders = day_data.get("employee_orders", {})
                        
                        for employee_key, employee_data in employee_orders.items():
                            total_employees_checked += 1
                            employee_dept_id = employee_data.get("employee_department_id")
                            order_dept_id = employee_data.get("order_department_id")
                            
                            # Check consistency rules
                            if employee_dept_id is None:
                                consistency_issues.append(f"{employee_key}: missing employee_department_id")
                            elif order_dept_id is None:
                                consistency_issues.append(f"{employee_key}: missing order_department_id")
                            elif order_dept_id != self.target_department_id:
                                consistency_issues.append(f"{employee_key}: order_department_id should be {self.target_department_id}, got {order_dept_id}")
                
                if consistency_issues:
                    self.error(f"Consistency issues found:")
                    for issue in consistency_issues:
                        self.error(f"  - {issue}")
                    return False
                else:
                    self.success(f"Consistency check passed for {total_employees_checked} employees")
                    return True
                    
            else:
                self.error(f"Failed to get breakfast history for consistency check: {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Exception during consistency check: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete Gastmitarbeiter-Marker functionality test"""
        self.log("🎯 STARTING GASTMITARBEITER-MARKER FUNCTIONALITY VERIFICATION")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Get Departments", self.test_get_departments),
            ("Admin Authentication", self.authenticate_admin),
            ("Create Test Employees", self.create_test_employees),
            ("Create Test Orders", self.create_test_orders),
            ("Test Breakfast History Department IDs", self.test_breakfast_history_department_ids),
            ("Test Guest Recognition Logic", self.test_guest_recognition_logic),
            ("Test Marker Data Structure", self.test_marker_data_structure),
            ("Test Consistency Check", self.test_consistency_check)
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
            self.success(f"🎉 GASTMITARBEITER-MARKER FUNCTIONALITY VERIFICATION COMPLETED SUCCESSFULLY!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            self.log("\n🎯 CRITICAL VERIFICATION RESULTS:")
            self.log("✅ breakfast-history API contains employee_department_id and order_department_id")
            self.log("✅ Guest employee recognition working (employee_department_id ≠ order_department_id)")
            self.log("✅ Regular employee recognition working (employee_department_id = order_department_id)")
            self.log("✅ Marker data structure supports frontend display")
            self.log("✅ Consistency check passed for all employees")
            self.log("\n🎯 TEST SCENARIOS VERIFIED:")
            self.log("✅ Regular employee from 1. WA orders in 1. WA → NO marker data")
            self.log("✅ Guest employee from 2. WA orders in 1. WA → Marker data available")
            self.log("✅ Guest employee from 3. WA orders in 1. WA → Marker data available")
            return True
        else:
            self.error(f"❌ GASTMITARBEITER-MARKER FUNCTIONALITY VERIFICATION PARTIALLY FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            return False

def main():
    """Main test execution"""
    print("🧪 Backend Test Suite - Gastmitarbeiter-Marker Functionality")
    print("=" * 70)
    
    # Initialize and run test
    test_suite = GastmitarbeiterMarkerTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - GASTMITARBEITER-MARKER FUNCTIONALITY IS WORKING!")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - GASTMITARBEITER-MARKER FUNCTIONALITY NEEDS ATTENTION!")
        exit(1)

if __name__ == "__main__":
    main()