#!/usr/bin/env python3
"""
Authentication Test for Department-Specific System
Tests authentication with password1-4 and admin1-4 credentials
"""

import requests
import json
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class AuthTester:
    def __init__(self):
        self.session = requests.Session()
        self.departments = []
        
    def log_test(self, test_name, success, message=""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")

    def get_departments(self):
        """Get all departments"""
        try:
            response = self.session.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                self.departments = response.json()
                return True
            return False
        except:
            return False

    def test_department_credentials(self):
        """Test department credentials password1-4"""
        print("\n=== TESTING DEPARTMENT CREDENTIALS (password1-4) ===")
        
        if not self.get_departments():
            print("❌ Failed to get departments")
            return False
        
        success_count = 0
        expected_passwords = ["password1", "password2", "password3", "password4"]
        
        for i, dept in enumerate(self.departments):
            if i < len(expected_passwords):
                password = expected_passwords[i]
                
                try:
                    login_data = {
                        "department_name": dept['name'],
                        "password": password
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department", json=login_data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('department_id') == dept['id']:
                            self.log_test(f"Department {dept['name']}", True, 
                                        f"Successfully authenticated with {password}")
                            success_count += 1
                        else:
                            self.log_test(f"Department {dept['name']}", False, 
                                        "Department ID mismatch")
                    else:
                        self.log_test(f"Department {dept['name']}", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
                except Exception as e:
                    self.log_test(f"Department {dept['name']}", False, f"Exception: {str(e)}")
        
        return success_count == len(self.departments)

    def test_admin_credentials(self):
        """Test admin credentials admin1-4"""
        print("\n=== TESTING ADMIN CREDENTIALS (admin1-4) ===")
        
        if not self.departments:
            print("❌ No departments available")
            return False
        
        success_count = 0
        expected_admin_passwords = ["admin1", "admin2", "admin3", "admin4"]
        
        for i, dept in enumerate(self.departments):
            if i < len(expected_admin_passwords):
                admin_password = expected_admin_passwords[i]
                
                try:
                    admin_login_data = {
                        "department_name": dept['name'],
                        "admin_password": admin_password
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if (result.get('department_id') == dept['id'] and 
                            result.get('role') == 'department_admin'):
                            self.log_test(f"Admin {dept['name']}", True, 
                                        f"Successfully authenticated with {admin_password}")
                            success_count += 1
                        else:
                            self.log_test(f"Admin {dept['name']}", False, 
                                        "Department ID or role mismatch")
                    else:
                        self.log_test(f"Admin {dept['name']}", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
                except Exception as e:
                    self.log_test(f"Admin {dept['name']}", False, f"Exception: {str(e)}")
        
        return success_count == len(self.departments)

    def test_wrong_credentials(self):
        """Test that wrong credentials are rejected"""
        print("\n=== TESTING WRONG CREDENTIALS REJECTION ===")
        
        if not self.departments:
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        
        # Test wrong department password
        try:
            wrong_login_data = {
                "department_name": test_dept['name'],
                "password": "wrongpassword"
            }
            
            response = self.session.post(f"{API_BASE}/login/department", json=wrong_login_data)
            
            if response.status_code == 401:
                self.log_test("Wrong Department Password", True, 
                            "Correctly rejected wrong password")
                success_count += 1
            else:
                self.log_test("Wrong Department Password", False, 
                            f"Should reject wrong password, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Wrong Department Password", False, f"Exception: {str(e)}")
        
        # Test wrong admin password
        try:
            wrong_admin_login_data = {
                "department_name": test_dept['name'],
                "admin_password": "wrongadminpassword"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=wrong_admin_login_data)
            
            if response.status_code == 401:
                self.log_test("Wrong Admin Password", True, 
                            "Correctly rejected wrong admin password")
                success_count += 1
            else:
                self.log_test("Wrong Admin Password", False, 
                            f"Should reject wrong admin password, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Wrong Admin Password", False, f"Exception: {str(e)}")
        
        return success_count == 2

    def run_all_tests(self):
        """Run all authentication tests"""
        print("🔐 TESTING DEPARTMENT-SPECIFIC AUTHENTICATION")
        print("=" * 60)
        
        test_results = []
        test_results.append(("Department Credentials", self.test_department_credentials()))
        test_results.append(("Admin Credentials", self.test_admin_credentials()))
        test_results.append(("Wrong Credentials Rejection", self.test_wrong_credentials()))
        
        print("\n" + "=" * 60)
        print("🎯 AUTHENTICATION TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\n📊 RESULT: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = AuthTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)