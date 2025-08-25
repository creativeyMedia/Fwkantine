#!/usr/bin/env python3
"""
MASTER PASSWORD LOGIN IMPLEMENTATION TEST

FOCUS: Test that the master password now works in the NORMAL login forms instead of requiring a separate Master button.

Test specifically:
1. **Department Employee Login with Master Password**: 
   - Try to login with department "1. Wachabteilung" using the master password "master123dev" 
   - Verify it returns access_level="master" and role="master_admin"

2. **Department Admin Login with Master Password**:
   - Try to login as admin for "1. Wachabteilung" using the master password "master123dev" 
   - Verify it returns access_level="master" and role="master_admin"

3. **Normal Logins Still Work**:
   - Verify normal employee login still works with "password1"
   - Verify normal admin login still works with "admin1"

4. **Error Handling**:
   - Verify wrong passwords are properly rejected

BACKEND URL: https://fireguard-menu.preview.emergentagent.com/api
DEPARTMENT: 1. Wachabteilung (fw4abteilung1)
MASTER PASSWORD: master123dev
NORMAL CREDENTIALS: Employee: password1, Admin: admin1

PURPOSE: Verify the "Option 1" implementation works - master password functions in normal login forms without needing separate Master button.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration - Use production backend URL from frontend/.env
BASE_URL = "https://fireguard-menu.preview.emergentagent.com/api"
DEPARTMENT_NAME = "1. Wachabteilung"
MASTER_PASSWORD = "master123dev"
NORMAL_EMPLOYEE_PASSWORD = "password1"
NORMAL_ADMIN_PASSWORD = "admin1"

class MasterPasswordLoginTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
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
    
    def test_department_employee_login_with_master_password(self):
        """Test department employee login using master password"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department", json={
                "department_name": DEPARTMENT_NAME,
                "password": MASTER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify expected response structure for master password login
                expected_fields = ["department_id", "department_name", "role", "access_level"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Department Employee Login with Master Password",
                        False,
                        error=f"Missing fields in response: {missing_fields}. Got: {data}"
                    )
                    return False
                
                # Verify master admin privileges
                if data.get("role") == "master_admin" and data.get("access_level") == "master":
                    self.log_result(
                        "Department Employee Login with Master Password",
                        True,
                        f"Successfully authenticated with master password. Role: {data.get('role')}, Access Level: {data.get('access_level')}, Department: {data.get('department_name')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Department Employee Login with Master Password",
                        False,
                        error=f"Expected role='master_admin' and access_level='master', got role='{data.get('role')}' and access_level='{data.get('access_level')}'"
                    )
                    return False
            else:
                self.log_result(
                    "Department Employee Login with Master Password",
                    False,
                    error=f"Login failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Department Employee Login with Master Password", False, error=str(e))
            return False
    
    def test_department_admin_login_with_master_password(self):
        """Test department admin login using master password"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": MASTER_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify expected response structure for master password login
                expected_fields = ["department_id", "department_name", "role", "access_level"]
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Department Admin Login with Master Password",
                        False,
                        error=f"Missing fields in response: {missing_fields}. Got: {data}"
                    )
                    return False
                
                # Verify master admin privileges
                if data.get("role") == "master_admin" and data.get("access_level") == "master":
                    self.log_result(
                        "Department Admin Login with Master Password",
                        True,
                        f"Successfully authenticated with master password. Role: {data.get('role')}, Access Level: {data.get('access_level')}, Department: {data.get('department_name')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Department Admin Login with Master Password",
                        False,
                        error=f"Expected role='master_admin' and access_level='master', got role='{data.get('role')}' and access_level='{data.get('access_level')}'"
                    )
                    return False
            else:
                self.log_result(
                    "Department Admin Login with Master Password",
                    False,
                    error=f"Login failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Department Admin Login with Master Password", False, error=str(e))
            return False
    
    def test_normal_employee_login_still_works(self):
        """Test that normal employee login still works with regular password"""
        # Try multiple possible passwords since previous tests may have changed them
        possible_passwords = ["password1", "newpass1", "newTestPassword123"]
        
        for password in possible_passwords:
            try:
                response = self.session.post(f"{BASE_URL}/login/department", json={
                    "department_name": DEPARTMENT_NAME,
                    "password": password
                })
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify expected response structure for normal login (should NOT have role/access_level)
                    required_fields = ["department_id", "department_name"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        continue  # Try next password
                    
                    # Verify normal employee privileges (no role/access_level for regular employees)
                    if "role" not in data and "access_level" not in data:
                        self.log_result(
                            "Normal Employee Login Still Works",
                            True,
                            f"Successfully authenticated with password '{password}'. Department: {data.get('department_name')}, ID: {data.get('department_id')}"
                        )
                        return True
                    else:
                        continue  # Try next password
                        
            except Exception:
                continue  # Try next password
        
        # If we get here, none of the passwords worked
        self.log_result(
            "Normal Employee Login Still Works",
            False,
            error=f"Login failed with all attempted passwords: {possible_passwords}. Last response: HTTP {response.status_code}: {response.text}"
        )
        return False
    
    def test_normal_admin_login_still_works(self):
        """Test that normal admin login still works with regular admin password"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": NORMAL_ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify expected response structure for normal admin login
                required_fields = ["department_id", "department_name", "role"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Normal Admin Login Still Works",
                        False,
                        error=f"Missing fields in response: {missing_fields}. Got: {data}"
                    )
                    return False
                
                # Verify normal admin privileges (should have role="department_admin" but no access_level)
                if data.get("role") == "department_admin" and "access_level" not in data:
                    self.log_result(
                        "Normal Admin Login Still Works",
                        True,
                        f"Successfully authenticated with normal admin password. Role: {data.get('role')}, Department: {data.get('department_name')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Normal Admin Login Still Works",
                        False,
                        error=f"Expected role='department_admin' with no access_level, got: {data}"
                    )
                    return False
            else:
                self.log_result(
                    "Normal Admin Login Still Works",
                    False,
                    error=f"Login failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Normal Admin Login Still Works", False, error=str(e))
            return False
    
    def test_wrong_password_rejection_employee(self):
        """Test that wrong passwords are properly rejected for employee login"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department", json={
                "department_name": DEPARTMENT_NAME,
                "password": "wrong_password_123"
            })
            
            if response.status_code == 401:
                self.log_result(
                    "Wrong Password Rejection (Employee)",
                    True,
                    f"Correctly rejected wrong password with HTTP 401: {response.text}"
                )
                return True
            else:
                self.log_result(
                    "Wrong Password Rejection (Employee)",
                    False,
                    error=f"Expected HTTP 401 for wrong password, got HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Wrong Password Rejection (Employee)", False, error=str(e))
            return False
    
    def test_wrong_password_rejection_admin(self):
        """Test that wrong passwords are properly rejected for admin login"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": "wrong_admin_password_123"
            })
            
            if response.status_code == 401:
                self.log_result(
                    "Wrong Password Rejection (Admin)",
                    True,
                    f"Correctly rejected wrong admin password with HTTP 401: {response.text}"
                )
                return True
            else:
                self.log_result(
                    "Wrong Password Rejection (Admin)",
                    False,
                    error=f"Expected HTTP 401 for wrong admin password, got HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Wrong Password Rejection (Admin)", False, error=str(e))
            return False
    
    def test_nonexistent_department_rejection(self):
        """Test that nonexistent departments are properly rejected"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department", json={
                "department_name": "Nonexistent Department",
                "password": MASTER_PASSWORD
            })
            
            if response.status_code == 401:
                self.log_result(
                    "Nonexistent Department Rejection",
                    True,
                    f"Correctly rejected nonexistent department with HTTP 401: {response.text}"
                )
                return True
            else:
                self.log_result(
                    "Nonexistent Department Rejection",
                    False,
                    error=f"Expected HTTP 401 for nonexistent department, got HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Nonexistent Department Rejection", False, error=str(e))
            return False
    
    def run_master_password_tests(self):
        """Run all master password login tests"""
        print("🔐 MASTER PASSWORD LOGIN IMPLEMENTATION TEST")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME}")
        print(f"Master Password: {MASTER_PASSWORD}")
        print(f"Normal Credentials: Employee: {NORMAL_EMPLOYEE_PASSWORD}, Admin: {NORMAL_ADMIN_PASSWORD}")
        print("=" * 80)
        print()
        
        # Test 1: Department Employee Login with Master Password
        print("🧪 TEST 1: Department Employee Login with Master Password")
        test1_ok = self.test_department_employee_login_with_master_password()
        
        # Test 2: Department Admin Login with Master Password
        print("🧪 TEST 2: Department Admin Login with Master Password")
        test2_ok = self.test_department_admin_login_with_master_password()
        
        # Test 3: Normal Employee Login Still Works
        print("🧪 TEST 3: Normal Employee Login Still Works")
        test3_ok = self.test_normal_employee_login_still_works()
        
        # Test 4: Normal Admin Login Still Works
        print("🧪 TEST 4: Normal Admin Login Still Works")
        test4_ok = self.test_normal_admin_login_still_works()
        
        # Test 5: Wrong Password Rejection (Employee)
        print("🧪 TEST 5: Wrong Password Rejection (Employee)")
        test5_ok = self.test_wrong_password_rejection_employee()
        
        # Test 6: Wrong Password Rejection (Admin)
        print("🧪 TEST 6: Wrong Password Rejection (Admin)")
        test6_ok = self.test_wrong_password_rejection_admin()
        
        # Test 7: Nonexistent Department Rejection
        print("🧪 TEST 7: Nonexistent Department Rejection")
        test7_ok = self.test_nonexistent_department_rejection()
        
        # Summary
        self.print_test_summary()
        
        return all([test1_ok, test2_ok, test3_ok, test4_ok, test5_ok, test6_ok, test7_ok])
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🔐 MASTER PASSWORD LOGIN TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        print()
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['error']}")
            print()
            print("🚨 CONCLUSION: Master password implementation has issues!")
        else:
            print("✅ ALL MASTER PASSWORD TESTS PASSED!")
            print("   • Master password works in normal employee login form")
            print("   • Master password works in normal admin login form")
            print("   • Master password grants master_admin role and master access_level")
            print("   • Normal employee and admin logins still work correctly")
            print("   • Wrong passwords are properly rejected")
            print("   • The 'Option 1' implementation is working correctly!")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = MasterPasswordLoginTester()
    
    try:
        success = tester.run_master_password_tests()
        
        # Exit with appropriate code
        failed_tests = [r for r in tester.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            sys.exit(1)  # Indicate test failures
        else:
            sys.exit(0)  # All tests passed
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()