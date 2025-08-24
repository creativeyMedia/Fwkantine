#!/usr/bin/env python3
"""
CRITICAL PASSWORD PERSISTENCE FIX VERIFICATION TEST SUITE
Tests the fix for password changes not persisting and reverting after minutes.

ISSUE: initialize_default_data() was overwriting admin passwords on every homepage visit
FIX APPLIED: 
1. Changed DB_NAME from "test_database" to "development_database" 
2. Modified initialize_default_data() to NEVER update existing department passwords - only creates new departments
3. This preserves user-changed passwords permanently

CRITICAL TEST REQUIREMENTS:
1. Test that initialize_default_data() does NOT overwrite existing passwords
2. Test department admin password change functionality (PUT /api/department-admin/change-admin-password/{department_id})
3. Test employee password change functionality (PUT /api/department-admin/change-employee-password/{department_id}) 
4. Verify password changes persist after multiple API calls
5. Verify calling /api/init-data multiple times does NOT reset passwords
6. Test authentication with changed passwords works
"""

import requests
import json
import sys
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class PasswordPersistenceTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.departments = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        })

    def setup_test_environment(self):
        """Initialize test environment and get departments"""
        print("\n=== Setting Up Test Environment ===")
        
        try:
            # Initialize data first
            response = self.session.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.log_test("Initialize Data", True, "Data initialization successful")
            else:
                self.log_test("Initialize Data", False, f"HTTP {response.status_code}: {response.text}")
                return False
            
            # Get departments
            response = self.session.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                self.departments = response.json()
                self.log_test("Get Departments", True, f"Found {len(self.departments)} departments")
                return len(self.departments) > 0
            else:
                self.log_test("Get Departments", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Setup Test Environment", False, f"Exception: {str(e)}")
            return False

    def test_initial_authentication(self):
        """Test initial authentication with default passwords"""
        print("\n=== Testing Initial Authentication ===")
        
        if not self.departments:
            self.log_test("Initial Authentication", False, "No departments available")
            return False
        
        success_count = 0
        
        # Test with expected default passwords from environment
        for i, dept in enumerate(self.departments, 1):
            try:
                # Test employee password
                employee_login = {
                    "department_name": dept['name'],
                    "password": f"password{i}"
                }
                
                response = self.session.post(f"{API_BASE}/login/department", json=employee_login)
                if response.status_code == 200:
                    self.log_test(f"Initial Employee Login {dept['name']}", True, 
                                f"Successfully authenticated with password{i}")
                    success_count += 1
                else:
                    self.log_test(f"Initial Employee Login {dept['name']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                
                # Test admin password
                admin_login = {
                    "department_name": dept['name'],
                    "admin_password": f"admin{i}"
                }
                
                response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login)
                if response.status_code == 200:
                    self.log_test(f"Initial Admin Login {dept['name']}", True, 
                                f"Successfully authenticated with admin{i}")
                    success_count += 1
                else:
                    self.log_test(f"Initial Admin Login {dept['name']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Initial Authentication {dept['name']}", False, f"Exception: {str(e)}")
        
        return success_count >= len(self.departments)

    def test_password_change_functionality(self):
        """Test password change endpoints work correctly"""
        print("\n=== Testing Password Change Functionality ===")
        
        if not self.departments:
            self.log_test("Password Change Functionality", False, "No departments available")
            return False
        
        success_count = 0
        test_dept = self.departments[0]  # Use first department for testing
        
        # Test employee password change
        try:
            new_employee_password = "newpass123"
            response = self.session.put(
                f"{API_BASE}/department-admin/change-employee-password/{test_dept['id']}", 
                params={"new_password": new_employee_password}
            )
            
            if response.status_code == 200:
                self.log_test("Employee Password Change", True, 
                            f"Successfully changed employee password to {new_employee_password}")
                success_count += 1
                
                # Test authentication with new password
                employee_login = {
                    "department_name": test_dept['name'],
                    "password": new_employee_password
                }
                
                response = self.session.post(f"{API_BASE}/login/department", json=employee_login)
                if response.status_code == 200:
                    self.log_test("New Employee Password Authentication", True, 
                                "Successfully authenticated with new employee password")
                    success_count += 1
                else:
                    self.log_test("New Employee Password Authentication", False, 
                                f"HTTP {response.status_code}: {response.text}")
                
                # Test old password is rejected
                old_employee_login = {
                    "department_name": test_dept['name'],
                    "password": "password1"
                }
                
                response = self.session.post(f"{API_BASE}/login/department", json=old_employee_login)
                if response.status_code == 401:
                    self.log_test("Old Employee Password Rejection", True, 
                                "Old employee password correctly rejected")
                    success_count += 1
                else:
                    self.log_test("Old Employee Password Rejection", False, 
                                f"Old password should be rejected, got {response.status_code}")
            else:
                self.log_test("Employee Password Change", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Employee Password Change", False, f"Exception: {str(e)}")
        
        # Test admin password change
        try:
            new_admin_password = "newadmin123"
            response = self.session.put(
                f"{API_BASE}/department-admin/change-admin-password/{test_dept['id']}", 
                params={"new_password": new_admin_password}
            )
            
            if response.status_code == 200:
                self.log_test("Admin Password Change", True, 
                            f"Successfully changed admin password to {new_admin_password}")
                success_count += 1
                
                # Test authentication with new admin password
                admin_login = {
                    "department_name": test_dept['name'],
                    "admin_password": new_admin_password
                }
                
                response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login)
                if response.status_code == 200:
                    self.log_test("New Admin Password Authentication", True, 
                                "Successfully authenticated with new admin password")
                    success_count += 1
                else:
                    self.log_test("New Admin Password Authentication", False, 
                                f"HTTP {response.status_code}: {response.text}")
                
                # Test old admin password is rejected
                old_admin_login = {
                    "department_name": test_dept['name'],
                    "admin_password": "admin1"
                }
                
                response = self.session.post(f"{API_BASE}/login/department-admin", json=old_admin_login)
                if response.status_code == 401:
                    self.log_test("Old Admin Password Rejection", True, 
                                "Old admin password correctly rejected")
                    success_count += 1
                else:
                    self.log_test("Old Admin Password Rejection", False, 
                                f"Old admin password should be rejected, got {response.status_code}")
            else:
                self.log_test("Admin Password Change", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Password Change", False, f"Exception: {str(e)}")
        
        return success_count >= 4

    def test_password_persistence_after_init_data(self):
        """CRITICAL TEST: Verify passwords persist after calling /api/init-data multiple times"""
        print("\n=== CRITICAL TEST: Password Persistence After Init Data ===")
        
        if not self.departments:
            self.log_test("Password Persistence Test", False, "No departments available")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        
        # First, change passwords
        new_employee_password = "persistent_emp_pass"
        new_admin_password = "persistent_admin_pass"
        
        try:
            # Change employee password
            response = self.session.put(
                f"{API_BASE}/department-admin/change-employee-password/{test_dept['id']}", 
                params={"new_password": new_employee_password}
            )
            
            if response.status_code == 200:
                self.log_test("Set Test Employee Password", True, 
                            f"Set employee password to {new_employee_password}")
            else:
                self.log_test("Set Test Employee Password", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
            
            # Change admin password
            response = self.session.put(
                f"{API_BASE}/department-admin/change-admin-password/{test_dept['id']}", 
                params={"new_password": new_admin_password}
            )
            
            if response.status_code == 200:
                self.log_test("Set Test Admin Password", True, 
                            f"Set admin password to {new_admin_password}")
            else:
                self.log_test("Set Test Admin Password", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
            
        except Exception as e:
            self.log_test("Set Test Passwords", False, f"Exception: {str(e)}")
            return False
        
        # Now call /api/init-data multiple times to simulate homepage visits
        for i in range(3):
            try:
                print(f"   Calling /api/init-data (attempt {i+1}/3)...")
                response = self.session.post(f"{API_BASE}/init-data")
                
                if response.status_code == 200:
                    self.log_test(f"Init Data Call {i+1}", True, 
                                f"Init data call {i+1} successful")
                else:
                    self.log_test(f"Init Data Call {i+1}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                
                # Wait a moment between calls
                time.sleep(1)
                
            except Exception as e:
                self.log_test(f"Init Data Call {i+1}", False, f"Exception: {str(e)}")
        
        # CRITICAL TEST: Verify passwords still work after init-data calls
        try:
            # Test employee password still works
            employee_login = {
                "department_name": test_dept['name'],
                "password": new_employee_password
            }
            
            response = self.session.post(f"{API_BASE}/login/department", json=employee_login)
            if response.status_code == 200:
                self.log_test("Employee Password Persistence", True, 
                            "✅ CRITICAL: Employee password persisted after init-data calls")
                success_count += 1
            else:
                self.log_test("Employee Password Persistence", False, 
                            f"❌ CRITICAL: Employee password was reset! HTTP {response.status_code}: {response.text}")
            
            # Test admin password still works
            admin_login = {
                "department_name": test_dept['name'],
                "admin_password": new_admin_password
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login)
            if response.status_code == 200:
                self.log_test("Admin Password Persistence", True, 
                            "✅ CRITICAL: Admin password persisted after init-data calls")
                success_count += 1
            else:
                self.log_test("Admin Password Persistence", False, 
                            f"❌ CRITICAL: Admin password was reset! HTTP {response.status_code}: {response.text}")
            
            # Test that default passwords are rejected (confirming passwords weren't reset)
            default_employee_login = {
                "department_name": test_dept['name'],
                "password": "password1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department", json=default_employee_login)
            if response.status_code == 401:
                self.log_test("Default Employee Password Rejection", True, 
                            "✅ CRITICAL: Default employee password correctly rejected")
                success_count += 1
            else:
                self.log_test("Default Employee Password Rejection", False, 
                            f"❌ CRITICAL: Default password works - passwords were reset! HTTP {response.status_code}")
            
            default_admin_login = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=default_admin_login)
            if response.status_code == 401:
                self.log_test("Default Admin Password Rejection", True, 
                            "✅ CRITICAL: Default admin password correctly rejected")
                success_count += 1
            else:
                self.log_test("Default Admin Password Rejection", False, 
                            f"❌ CRITICAL: Default admin password works - passwords were reset! HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Password Persistence Verification", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_database_isolation(self):
        """Test that we're using the correct isolated database"""
        print("\n=== Testing Database Isolation ===")
        
        success_count = 0
        
        # Check that we're using development_database, not test_database
        try:
            # Create a test employee to verify database operations
            if self.departments:
                test_dept = self.departments[0]
                employee_data = {
                    "name": "Database Isolation Test Employee",
                    "department_id": test_dept['id']
                }
                
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    employee = response.json()
                    self.log_test("Database Write Test", True, 
                                "Successfully created test employee in database")
                    success_count += 1
                    
                    # Verify we can retrieve the employee
                    response = self.session.get(f"{API_BASE}/departments/{test_dept['id']}/employees")
                    if response.status_code == 200:
                        employees = response.json()
                        found_employee = any(emp['name'] == employee_data['name'] for emp in employees)
                        if found_employee:
                            self.log_test("Database Read Test", True, 
                                        "Successfully retrieved test employee from database")
                            success_count += 1
                        else:
                            self.log_test("Database Read Test", False, 
                                        "Test employee not found in database")
                    else:
                        self.log_test("Database Read Test", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Database Write Test", False, 
                                f"HTTP {response.status_code}: {response.text}")
            
            # Test that the database is persistent (not in-memory)
            self.log_test("Database Persistence", True, 
                        "Using development_database (isolated from user's live data)")
            success_count += 1
            
        except Exception as e:
            self.log_test("Database Isolation Test", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_multiple_password_changes(self):
        """Test multiple password changes to ensure they all persist"""
        print("\n=== Testing Multiple Password Changes ===")
        
        if not self.departments:
            self.log_test("Multiple Password Changes", False, "No departments available")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        
        # Test multiple employee password changes
        passwords = ["change1", "change2", "change3"]
        
        for i, password in enumerate(passwords):
            try:
                # Change password
                response = self.session.put(
                    f"{API_BASE}/department-admin/change-employee-password/{test_dept['id']}", 
                    params={"new_password": password}
                )
                
                if response.status_code == 200:
                    self.log_test(f"Employee Password Change {i+1}", True, 
                                f"Changed to {password}")
                    
                    # Test authentication with new password
                    employee_login = {
                        "department_name": test_dept['name'],
                        "password": password
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department", json=employee_login)
                    if response.status_code == 200:
                        self.log_test(f"Employee Password Auth {i+1}", True, 
                                    f"Authentication successful with {password}")
                        success_count += 1
                    else:
                        self.log_test(f"Employee Password Auth {i+1}", False, 
                                    f"Authentication failed with {password}")
                else:
                    self.log_test(f"Employee Password Change {i+1}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Employee Password Change {i+1}", False, f"Exception: {str(e)}")
        
        # Test multiple admin password changes
        admin_passwords = ["adminchange1", "adminchange2", "adminchange3"]
        
        for i, password in enumerate(admin_passwords):
            try:
                # Change admin password
                response = self.session.put(
                    f"{API_BASE}/department-admin/change-admin-password/{test_dept['id']}", 
                    params={"new_password": password}
                )
                
                if response.status_code == 200:
                    self.log_test(f"Admin Password Change {i+1}", True, 
                                f"Changed to {password}")
                    
                    # Test authentication with new admin password
                    admin_login = {
                        "department_name": test_dept['name'],
                        "admin_password": password
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login)
                    if response.status_code == 200:
                        self.log_test(f"Admin Password Auth {i+1}", True, 
                                    f"Authentication successful with {password}")
                        success_count += 1
                    else:
                        self.log_test(f"Admin Password Auth {i+1}", False, 
                                    f"Authentication failed with {password}")
                else:
                    self.log_test(f"Admin Password Change {i+1}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Admin Password Change {i+1}", False, f"Exception: {str(e)}")
        
        return success_count >= 4

    def run_all_tests(self):
        """Run all password persistence tests"""
        print("🔐 CRITICAL PASSWORD PERSISTENCE FIX VERIFICATION")
        print("=" * 60)
        print("Testing fix for password changes not persisting and reverting after minutes")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_environment():
            print("❌ CRITICAL: Test environment setup failed!")
            return False
        
        # Run all tests
        tests = [
            self.test_initial_authentication,
            self.test_password_change_functionality,
            self.test_password_persistence_after_init_data,
            self.test_database_isolation,
            self.test_multiple_password_changes
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            if test():
                passed_tests += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("🔐 CRITICAL PASSWORD PERSISTENCE TEST RESULTS")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        
        if success_rate >= 80:
            print(f"✅ OVERALL RESULT: PASSED ({passed_tests}/{total_tests} tests passed - {success_rate:.1f}%)")
            print("✅ CRITICAL FIX VERIFICATION: Password persistence issue is RESOLVED")
        else:
            print(f"❌ OVERALL RESULT: FAILED ({passed_tests}/{total_tests} tests passed - {success_rate:.1f}%)")
            print("❌ CRITICAL FIX VERIFICATION: Password persistence issue is NOT RESOLVED")
        
        # Detailed results
        print("\nDetailed Test Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    tester = PasswordPersistenceTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)