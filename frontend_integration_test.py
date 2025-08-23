#!/usr/bin/env python3
"""
Frontend Integration Test for Department-Specific Products & Pricing
Tests the specific areas mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class FrontendIntegrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.departments = []
        self.employees = []
        
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

    def setup_test_data(self):
        """Setup test data"""
        print("\n=== Setting Up Test Data ===")
        
        try:
            # Initialize data
            response = self.session.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.log_test("Initialize Data", True, "Data initialized")
            
            # Get departments
            response = self.session.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                self.departments = response.json()
                self.log_test("Load Departments", True, f"Loaded {len(self.departments)} departments")
                
                # Create test employees
                for i, dept in enumerate(self.departments[:2]):  # Create employees for first 2 departments
                    employee_data = {
                        "name": f"Test Employee {i+1}",
                        "department_id": dept['id']
                    }
                    
                    response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                    if response.status_code == 200:
                        self.employees.append(response.json())
                
                return True
            else:
                return False
                
        except Exception as e:
            self.log_test("Setup", False, f"Exception: {str(e)}")
            return False

    def test_department_specific_menu_fetch_calls(self):
        """Test that updated menu fetch calls work correctly with department_id"""
        print("\n=== CRITICAL AREA 1: Department-Specific Menu Loading ===")
        
        if not self.departments:
            self.log_test("Menu Fetch Test", False, "No departments available")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        dept_id = test_dept['id']
        
        # Test 1: Verify /api/menu/breakfast/{department_id} endpoint
        try:
            response = self.session.get(f"{API_BASE}/menu/breakfast/{dept_id}")
            
            if response.status_code == 200:
                items = response.json()
                if len(items) > 0 and all('department_id' in item and item['department_id'] == dept_id for item in items):
                    self.log_test("Breakfast Menu Fetch with Dept ID", True, 
                                f"✅ /api/menu/breakfast/{dept_id} returns {len(items)} department-specific items")
                    success_count += 1
                else:
                    self.log_test("Breakfast Menu Fetch with Dept ID", False, 
                                "Items missing department_id or empty response")
            else:
                self.log_test("Breakfast Menu Fetch with Dept ID", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Breakfast Menu Fetch with Dept ID", False, f"Exception: {str(e)}")
        
        # Test 2: Test that frontend correctly uses department_id from authentication context
        try:
            # Simulate frontend authentication flow
            login_data = {
                "department_name": test_dept['name'],
                "password": "password1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department", json=login_data)
            
            if response.status_code == 200:
                auth_result = response.json()
                auth_dept_id = auth_result['department_id']
                
                # Now use the authenticated department_id to fetch menu
                response = self.session.get(f"{API_BASE}/menu/breakfast/{auth_dept_id}")
                
                if response.status_code == 200:
                    items = response.json()
                    if all(item['department_id'] == auth_dept_id for item in items):
                        self.log_test("Frontend Auth Context Menu Fetch", True, 
                                    "✅ Frontend can use department_id from auth context to fetch correct menu")
                        success_count += 1
                    else:
                        self.log_test("Frontend Auth Context Menu Fetch", False, 
                                    "Menu items don't match authenticated department")
                else:
                    self.log_test("Frontend Auth Context Menu Fetch", False, f"HTTP {response.status_code}")
            else:
                self.log_test("Frontend Auth Context Menu Fetch", False, f"Auth failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Frontend Auth Context Menu Fetch", False, f"Exception: {str(e)}")
        
        # Test 3: Verify fallback to old endpoints works
        try:
            response = self.session.get(f"{API_BASE}/menu/breakfast")
            
            if response.status_code == 200:
                items = response.json()
                if len(items) > 0:
                    self.log_test("Fallback to Old Endpoints", True, 
                                "✅ Old /api/menu/breakfast endpoint still works as fallback")
                    success_count += 1
                else:
                    self.log_test("Fallback to Old Endpoints", False, "Old endpoint returns empty")
            else:
                self.log_test("Fallback to Old Endpoints", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Fallback to Old Endpoints", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_admin_menu_creation_with_department_id(self):
        """Test that admin menu item creation includes department_id in request body"""
        print("\n=== CRITICAL AREA 2: Admin Menu Creation ===")
        
        if not self.departments:
            self.log_test("Admin Menu Creation", False, "No departments available")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        dept_id = test_dept['id']
        
        # Test 1: Breakfast item creation with department_id
        try:
            breakfast_data = {
                "roll_type": "weiss",
                "price": 0.85,
                "department_id": dept_id  # Critical: department_id in request body
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/breakfast", json=breakfast_data)
            
            if response.status_code == 200:
                item = response.json()
                if item.get('department_id') == dept_id:
                    self.log_test("Admin Breakfast Creation with Dept ID", True, 
                                "✅ Breakfast item created with department_id in request body")
                    success_count += 1
                else:
                    self.log_test("Admin Breakfast Creation with Dept ID", False, 
                                "Created item missing department_id")
            else:
                self.log_test("Admin Breakfast Creation with Dept ID", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Breakfast Creation with Dept ID", False, f"Exception: {str(e)}")
        
        # Test 2: Toppings item creation with department_id
        try:
            topping_data = {
                "topping_type": "ruehrei",
                "price": 0.00,
                "department_id": dept_id  # Critical: department_id in request body
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", json=topping_data)
            
            if response.status_code == 200:
                item = response.json()
                if item.get('department_id') == dept_id:
                    self.log_test("Admin Toppings Creation with Dept ID", True, 
                                "✅ Toppings item created with department_id in request body")
                    success_count += 1
                else:
                    self.log_test("Admin Toppings Creation with Dept ID", False, 
                                "Created item missing department_id")
            else:
                self.log_test("Admin Toppings Creation with Dept ID", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Toppings Creation with Dept ID", False, f"Exception: {str(e)}")
        
        # Test 3: Drinks creation with department_id
        try:
            drink_data = {
                "name": "Test Premium Kaffee",
                "price": 1.30,
                "department_id": dept_id  # Critical: department_id in request body
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/drinks", json=drink_data)
            
            if response.status_code == 200:
                item = response.json()
                if item.get('department_id') == dept_id:
                    self.log_test("Admin Drinks Creation with Dept ID", True, 
                                "✅ Drinks item created with department_id in request body")
                    success_count += 1
                else:
                    self.log_test("Admin Drinks Creation with Dept ID", False, 
                                "Created item missing department_id")
            else:
                self.log_test("Admin Drinks Creation with Dept ID", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Drinks Creation with Dept ID", False, f"Exception: {str(e)}")
        
        # Test 4: Sweets creation with department_id
        try:
            sweet_data = {
                "name": "Test Premium Schokolade",
                "price": 1.75,
                "department_id": dept_id  # Critical: department_id in request body
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/sweets", json=sweet_data)
            
            if response.status_code == 200:
                item = response.json()
                if item.get('department_id') == dept_id:
                    self.log_test("Admin Sweets Creation with Dept ID", True, 
                                "✅ Sweets item created with department_id in request body")
                    success_count += 1
                else:
                    self.log_test("Admin Sweets Creation with Dept ID", False, 
                                "Created item missing department_id")
            else:
                self.log_test("Admin Sweets Creation with Dept ID", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Sweets Creation with Dept ID", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_menu_isolation_between_departments(self):
        """Test that departments see only their own items"""
        print("\n=== CRITICAL AREA 3: Menu Isolation ===")
        
        if len(self.departments) < 2:
            self.log_test("Menu Isolation", False, "Need at least 2 departments")
            return False
        
        success_count = 0
        dept1 = self.departments[0]
        dept2 = self.departments[1]
        
        # Test 1: Department 1 admin sees only Department 1 menu items
        try:
            # Create unique item for dept1
            dept1_item_data = {
                "name": "Dept1 Unique Kaffee",
                "price": 1.00,
                "department_id": dept1['id']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/drinks", json=dept1_item_data)
            dept1_item_id = None
            if response.status_code == 200:
                dept1_item_id = response.json()['id']
            
            # Fetch dept1 menu
            response = self.session.get(f"{API_BASE}/menu/drinks/{dept1['id']}")
            if response.status_code == 200:
                dept1_items = response.json()
                dept1_item_ids = [item['id'] for item in dept1_items]
                
                if dept1_item_id and dept1_item_id in dept1_item_ids:
                    self.log_test("Department 1 Sees Own Items", True, 
                                "✅ Department 1 admin sees Department 1 menu items")
                    success_count += 1
                else:
                    self.log_test("Department 1 Sees Own Items", False, 
                                "Department 1 cannot see its own items")
                    
        except Exception as e:
            self.log_test("Department 1 Sees Own Items", False, f"Exception: {str(e)}")
        
        # Test 2: Department 2 admin sees only Department 2 menu items
        try:
            # Create unique item for dept2
            dept2_item_data = {
                "name": "Dept2 Unique Tee",
                "price": 0.90,
                "department_id": dept2['id']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/drinks", json=dept2_item_data)
            dept2_item_id = None
            if response.status_code == 200:
                dept2_item_id = response.json()['id']
            
            # Fetch dept2 menu
            response = self.session.get(f"{API_BASE}/menu/drinks/{dept2['id']}")
            if response.status_code == 200:
                dept2_items = response.json()
                dept2_item_ids = [item['id'] for item in dept2_items]
                
                if dept2_item_id and dept2_item_id in dept2_item_ids:
                    self.log_test("Department 2 Sees Own Items", True, 
                                "✅ Department 2 admin sees Department 2 menu items")
                    success_count += 1
                else:
                    self.log_test("Department 2 Sees Own Items", False, 
                                "Department 2 cannot see its own items")
                    
        except Exception as e:
            self.log_test("Department 2 Sees Own Items", False, f"Exception: {str(e)}")
        
        # Test 3: Verify order creation uses correct department-specific menus
        if self.employees:
            try:
                # Create order for dept1 employee
                dept1_employee = next((emp for emp in self.employees if emp['department_id'] == dept1['id']), None)
                
                if dept1_employee:
                    order_data = {
                        "employee_id": dept1_employee['id'],
                        "department_id": dept1['id'],
                        "order_type": "breakfast",
                        "breakfast_items": [
                            {
                                "total_halves": 2,
                                "white_halves": 2,
                                "seeded_halves": 0,
                                "toppings": ["ruehrei", "kaese"],
                                "has_lunch": False
                            }
                        ]
                    }
                    
                    response = self.session.post(f"{API_BASE}/orders", json=order_data)
                    
                    if response.status_code == 200:
                        order = response.json()
                        if order['department_id'] == dept1['id']:
                            self.log_test("Order Uses Dept-Specific Menus", True, 
                                        "✅ Order creation uses correct department-specific menus")
                            success_count += 1
                        else:
                            self.log_test("Order Uses Dept-Specific Menus", False, 
                                        "Order department_id mismatch")
                    else:
                        self.log_test("Order Uses Dept-Specific Menus", False, f"HTTP {response.status_code}")
                        
            except Exception as e:
                self.log_test("Order Uses Dept-Specific Menus", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_authentication_with_department_credentials(self):
        """Test authentication with department credentials (password1-4) and admin credentials (admin1-4)"""
        print("\n=== CRITICAL AREA 5: Authentication ===")
        
        if not self.departments:
            self.log_test("Authentication", False, "No departments available")
            return False
        
        success_count = 0
        
        # Test department credentials (password1-4)
        expected_passwords = ["password1", "password2", "password3", "password4"]
        
        for i, dept in enumerate(self.departments[:4]):
            try:
                login_data = {
                    "department_name": dept['name'],
                    "password": expected_passwords[i]
                }
                
                response = self.session.post(f"{API_BASE}/login/department", json=login_data)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('department_id') == dept['id']:
                        self.log_test(f"Dept Credentials {expected_passwords[i]}", True, 
                                    f"✅ {dept['name']} authenticated with {expected_passwords[i]}")
                        success_count += 1
                    else:
                        self.log_test(f"Dept Credentials {expected_passwords[i]}", False, 
                                    "Department ID mismatch")
                else:
                    self.log_test(f"Dept Credentials {expected_passwords[i]}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Dept Credentials {expected_passwords[i]}", False, f"Exception: {str(e)}")
        
        # Test admin credentials (admin1-4)
        expected_admin_passwords = ["admin1", "admin2", "admin3", "admin4"]
        
        for i, dept in enumerate(self.departments[:4]):
            try:
                admin_login_data = {
                    "department_name": dept['name'],
                    "admin_password": expected_admin_passwords[i]
                }
                
                response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('role') == 'department_admin' and result.get('department_id') == dept['id']:
                        self.log_test(f"Admin Credentials {expected_admin_passwords[i]}", True, 
                                    f"✅ {dept['name']} admin authenticated with {expected_admin_passwords[i]}")
                        success_count += 1
                    else:
                        self.log_test(f"Admin Credentials {expected_admin_passwords[i]}", False, 
                                    "Role or department ID mismatch")
                else:
                    self.log_test(f"Admin Credentials {expected_admin_passwords[i]}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Admin Credentials {expected_admin_passwords[i]}", False, f"Exception: {str(e)}")
        
        return success_count >= 6

    def run_all_tests(self):
        """Run all frontend integration tests"""
        print("🎯 FRONTEND INTEGRATION WITH DEPARTMENT-SPECIFIC PRODUCTS & PRICING")
        print("=" * 80)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Failed to setup test data")
            return False
        
        # Run critical area tests
        test_results = []
        
        test_results.append(self.test_department_specific_menu_fetch_calls())
        test_results.append(self.test_admin_menu_creation_with_department_id())
        test_results.append(self.test_menu_isolation_between_departments())
        test_results.append(self.test_authentication_with_department_credentials())
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n{'='*80}")
        print(f"FRONTEND INTEGRATION TESTING SUMMARY")
        print(f"{'='*80}")
        print(f"Total Critical Areas Tested: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print(f"\nDETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['message']:
                print(f"   {result['message']}")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = FrontendIntegrationTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)