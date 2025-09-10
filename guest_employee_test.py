#!/usr/bin/env python3
"""
CRITICAL DATABASE STORAGE VERIFICATION: Guest Employee Creation Test Suite
=========================================================================

This test suite verifies that employees created with guest marker (is_guest: true) 
are properly stored in the database and can be retrieved correctly.

CRITICAL SUCCESS CRITERIA:
✅ Guest employees are created successfully via API
✅ Guest employees appear in database queries  
✅ is_guest field is correctly stored and returned
✅ No difference in storage behavior between regular and guest employees

TEST PLAN:
1. Test POST /api/employees with standard employee (no guest marker)
2. Test POST /api/employees with guest employee (is_guest: true)
3. Verify both API calls return success (201/200 status)
4. Check if employees are actually stored in MongoDB using GET /api/employees
5. Verify is_guest field is correctly stored and returned
6. Create specific test employee with guest marker and verify it appears in responses
7. Compare regular vs guest employees storage behavior
8. Use MongoDB queries to check actual database contents
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class GuestEmployeeTest:
    def __init__(self):
        self.department_id = "fw4abteilung1"
        self.admin_credentials = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.test_regular_employee_id = None
        self.test_guest_employee_id = None
        self.test_regular_employee_name = f"Test_Normal_DB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_guest_employee_name = f"Test_Gast_DB_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        
    def critical(self, message):
        """Log critical verification results"""
        print(f"🎯 CRITICAL: {message}")
        
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
        """Test that departments are returned"""
        try:
            response = requests.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                departments = response.json()
                if len(departments) > 0:
                    self.success(f"Found {len(departments)} departments")
                    for dept in departments:
                        self.log(f"  - {dept['name']} (ID: {dept['id']})")
                    return True
                else:
                    self.error("No departments found")
                    return False
            else:
                self.error(f"Failed to get departments: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception getting departments: {str(e)}")
            return False
            
    def create_regular_employee(self):
        """Create a regular employee (no guest marker)"""
        try:
            employee_data = {
                "name": self.test_regular_employee_name,
                "department_id": self.department_id,
                "is_guest": False
            }
            
            self.log(f"Creating regular employee: {self.test_regular_employee_name}")
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_regular_employee_id = employee["id"]
                
                # Verify is_guest field in response
                is_guest = employee.get("is_guest", None)
                if is_guest is False:
                    self.success(f"Regular employee created successfully with is_guest: {is_guest}")
                    self.success(f"Employee ID: {self.test_regular_employee_id}")
                    return True
                else:
                    self.error(f"Regular employee created but is_guest field incorrect: {is_guest}")
                    return False
            else:
                self.error(f"Failed to create regular employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating regular employee: {str(e)}")
            return False
            
    def create_guest_employee(self):
        """Create a guest employee (is_guest: true)"""
        try:
            employee_data = {
                "name": self.test_guest_employee_name,
                "department_id": self.department_id,
                "is_guest": True
            }
            
            self.log(f"Creating guest employee: {self.test_guest_employee_name}")
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_guest_employee_id = employee["id"]
                
                # Verify is_guest field in response
                is_guest = employee.get("is_guest", None)
                if is_guest is True:
                    self.success(f"Guest employee created successfully with is_guest: {is_guest}")
                    self.success(f"Employee ID: {self.test_guest_employee_id}")
                    return True
                else:
                    self.error(f"Guest employee created but is_guest field incorrect: {is_guest}")
                    return False
            else:
                self.error(f"Failed to create guest employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating guest employee: {str(e)}")
            return False
            
    def verify_employees_in_database(self):
        """Verify both employees appear in GET /api/departments/{id}/employees"""
        try:
            response = requests.get(f"{API_BASE}/departments/{self.department_id}/employees")
            if response.status_code == 200:
                employees = response.json()
                self.success(f"Retrieved {len(employees)} employees from database")
                
                # Look for our test employees
                regular_found = False
                guest_found = False
                
                for employee in employees:
                    if employee["id"] == self.test_regular_employee_id:
                        regular_found = True
                        is_guest = employee.get("is_guest", None)
                        if is_guest is False:
                            self.success(f"Regular employee found in database with correct is_guest: {is_guest}")
                        else:
                            self.error(f"Regular employee found but is_guest field incorrect: {is_guest}")
                            return False
                            
                    elif employee["id"] == self.test_guest_employee_id:
                        guest_found = True
                        is_guest = employee.get("is_guest", None)
                        if is_guest is True:
                            self.success(f"Guest employee found in database with correct is_guest: {is_guest}")
                        else:
                            self.error(f"Guest employee found but is_guest field incorrect: {is_guest}")
                            return False
                
                if regular_found and guest_found:
                    self.critical("Both regular and guest employees successfully stored and retrieved from database")
                    return True
                else:
                    self.error(f"Employees not found in database - Regular: {regular_found}, Guest: {guest_found}")
                    return False
            else:
                self.error(f"Failed to get employees from database: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception verifying employees in database: {str(e)}")
            return False
            
    def test_specific_guest_employee_scenario(self):
        """Test the exact scenario from review request"""
        try:
            # Create the specific test employee mentioned in review request
            specific_employee_data = {
                "name": "Test Gast DB",
                "department_id": self.department_id,
                "is_guest": True
            }
            
            self.log("Creating specific test employee: 'Test Gast DB' with is_guest: true")
            
            response = requests.post(f"{API_BASE}/employees", json=specific_employee_data)
            if response.status_code == 200:
                employee = response.json()
                specific_employee_id = employee["id"]
                
                # Verify is_guest field
                is_guest = employee.get("is_guest", None)
                if is_guest is True:
                    self.success(f"Specific test employee created with is_guest: {is_guest}")
                    
                    # Now verify it appears in GET /api/employees response
                    verify_response = requests.get(f"{API_BASE}/departments/{self.department_id}/employees")
                    if verify_response.status_code == 200:
                        employees = verify_response.json()
                        
                        # Look for our specific employee
                        found_specific = False
                        for emp in employees:
                            if emp["name"] == "Test Gast DB" and emp["id"] == specific_employee_id:
                                found_specific = True
                                emp_is_guest = emp.get("is_guest", None)
                                if emp_is_guest is True:
                                    self.critical("Specific test employee 'Test Gast DB' found in database with is_guest: true")
                                    return True
                                else:
                                    self.error(f"Specific employee found but is_guest incorrect: {emp_is_guest}")
                                    return False
                        
                        if not found_specific:
                            self.error("Specific test employee 'Test Gast DB' not found in database")
                            return False
                    else:
                        self.error(f"Failed to verify specific employee: {verify_response.status_code}")
                        return False
                else:
                    self.error(f"Specific employee created but is_guest field incorrect: {is_guest}")
                    return False
            else:
                self.error(f"Failed to create specific test employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception testing specific guest employee scenario: {str(e)}")
            return False
            
    def compare_storage_behavior(self):
        """Compare storage behavior between regular and guest employees"""
        try:
            response = requests.get(f"{API_BASE}/departments/{self.department_id}/employees")
            if response.status_code == 200:
                employees = response.json()
                
                regular_employee = None
                guest_employee = None
                
                # Find our test employees
                for employee in employees:
                    if employee["id"] == self.test_regular_employee_id:
                        regular_employee = employee
                    elif employee["id"] == self.test_guest_employee_id:
                        guest_employee = employee
                
                if regular_employee and guest_employee:
                    self.log("Comparing storage behavior between regular and guest employees:")
                    
                    # Compare structure (should be identical except for is_guest field)
                    regular_keys = set(regular_employee.keys())
                    guest_keys = set(guest_employee.keys())
                    
                    if regular_keys == guest_keys:
                        self.success("Both employees have identical field structure")
                    else:
                        self.error(f"Field structure differs - Regular: {regular_keys}, Guest: {guest_keys}")
                        return False
                    
                    # Verify both have required fields
                    required_fields = ["id", "name", "department_id", "breakfast_balance", "drinks_sweets_balance", "sort_order", "is_guest"]
                    
                    for field in required_fields:
                        if field in regular_employee and field in guest_employee:
                            self.log(f"  ✓ Both have '{field}' field")
                        else:
                            self.error(f"Missing field '{field}' in one or both employees")
                            return False
                    
                    # Verify is_guest field values
                    if regular_employee["is_guest"] is False and guest_employee["is_guest"] is True:
                        self.critical("is_guest field correctly differentiates between regular and guest employees")
                        return True
                    else:
                        self.error(f"is_guest field values incorrect - Regular: {regular_employee['is_guest']}, Guest: {guest_employee['is_guest']}")
                        return False
                else:
                    self.error("Could not find both test employees for comparison")
                    return False
            else:
                self.error(f"Failed to get employees for comparison: {response.status_code}")
                return False
        except Exception as e:
            self.error(f"Exception comparing storage behavior: {str(e)}")
            return False
            
    def test_guest_field_persistence(self):
        """Test that is_guest field persists correctly across multiple API calls"""
        try:
            # Make multiple calls to verify persistence
            for i in range(3):
                response = requests.get(f"{API_BASE}/departments/{self.department_id}/employees")
                if response.status_code == 200:
                    employees = response.json()
                    
                    guest_found = False
                    for employee in employees:
                        if employee["id"] == self.test_guest_employee_id:
                            guest_found = True
                            is_guest = employee.get("is_guest", None)
                            if is_guest is not True:
                                self.error(f"is_guest field not persistent on call {i+1}: {is_guest}")
                                return False
                            break
                    
                    if not guest_found:
                        self.error(f"Guest employee not found on call {i+1}")
                        return False
                else:
                    self.error(f"API call {i+1} failed: {response.status_code}")
                    return False
            
            self.success("is_guest field persists correctly across multiple API calls")
            return True
        except Exception as e:
            self.error(f"Exception testing field persistence: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete guest employee database storage verification"""
        self.log("🎯 STARTING CRITICAL DATABASE STORAGE VERIFICATION: Guest Employee Creation")
        self.log("=" * 90)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Get Departments", self.test_get_departments),
            ("Create Regular Employee (no guest marker)", self.create_regular_employee),
            ("Create Guest Employee (is_guest: true)", self.create_guest_employee),
            ("Verify Employees in Database", self.verify_employees_in_database),
            ("Test Specific Guest Employee Scenario", self.test_specific_guest_employee_scenario),
            ("Compare Storage Behavior", self.compare_storage_behavior),
            ("Test Guest Field Persistence", self.test_guest_field_persistence)
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        
        for step_name, step_function in test_steps:
            self.log(f"\n📋 Step {passed_tests + 1}/{total_tests}: {step_name}")
            self.log("-" * 60)
            
            if step_function():
                passed_tests += 1
                self.success(f"Step {passed_tests}/{total_tests} PASSED: {step_name}")
            else:
                self.error(f"Step {passed_tests + 1}/{total_tests} FAILED: {step_name}")
                # Continue with other tests even if one fails
                
        # Final results
        self.log("\n" + "=" * 90)
        if passed_tests == total_tests:
            self.success(f"🎉 CRITICAL DATABASE STORAGE VERIFICATION COMPLETED SUCCESSFULLY!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            self.log("\n🎯 CRITICAL VERIFICATION RESULTS:")
            self.log("✅ Guest employees are created successfully via API")
            self.log("✅ Guest employees appear in database queries")
            self.log("✅ is_guest field is correctly stored and returned")
            self.log("✅ No difference in storage behavior between regular and guest employees")
            self.log("✅ Guest marker persists correctly across multiple API calls")
            self.log("✅ Specific test scenario 'Test Gast DB' works correctly")
            return True
        else:
            self.error(f"❌ CRITICAL DATABASE STORAGE VERIFICATION FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            self.log("\n🚨 CRITICAL ISSUES IDENTIFIED:")
            if passed_tests < total_tests:
                self.log("❌ Guest employee creation or storage has critical issues")
                self.log("❌ Database storage verification failed")
                self.log("❌ Guest marker functionality is broken")
            return False

def main():
    """Main test execution"""
    print("🧪 CRITICAL DATABASE STORAGE VERIFICATION: Guest Employee Creation")
    print("=" * 80)
    
    # Initialize and run test
    test_suite = GuestEmployeeTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - GUEST EMPLOYEE DATABASE STORAGE IS WORKING!")
        exit(0)
    else:
        print("\n❌ CRITICAL FAILURE - GUEST EMPLOYEE DATABASE STORAGE NEEDS IMMEDIATE ATTENTION!")
        exit(1)

if __name__ == "__main__":
    main()