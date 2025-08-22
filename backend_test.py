#!/usr/bin/env python3
"""
Backend Test Suite for German Canteen Management System
Tests all core functionalities including German menu items and Euro pricing
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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteen-hub-1.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class CanteenTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.departments = []
        self.employees = []
        self.menu_items = {
            'breakfast': [],
            'toppings': [],
            'drinks': [],
            'sweets': []
        }
        
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
        
    def test_data_initialization(self):
        """Test the /api/init-data endpoint"""
        print("\n=== Testing Data Initialization ===")
        
        try:
            response = self.session.post(f"{API_BASE}/init-data")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Data Initialization", True, 
                            f"Response: {data.get('message', 'Success')}")
                return True
            else:
                self.log_test("Data Initialization", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Data Initialization", False, f"Exception: {str(e)}")
            return False
    
    def test_get_departments(self):
        """Test getting all departments"""
        print("\n=== Testing Department Retrieval ===")
        
        try:
            response = self.session.get(f"{API_BASE}/departments")
            
            if response.status_code == 200:
                departments = response.json()
                self.departments = departments
                
                # Check if we have 4 German departments
                expected_departments = ["Wachabteilung A", "Wachabteilung B", 
                                      "Wachabteilung C", "Wachabteilung D"]
                
                dept_names = [dept['name'] for dept in departments]
                
                if len(departments) == 4:
                    self.log_test("Department Count", True, f"Found {len(departments)} departments")
                else:
                    self.log_test("Department Count", False, f"Expected 4, found {len(departments)}")
                
                # Check department names
                missing_depts = [name for name in expected_departments if name not in dept_names]
                if not missing_depts:
                    self.log_test("German Department Names", True, 
                                f"All expected departments found: {dept_names}")
                else:
                    self.log_test("German Department Names", False, 
                                f"Missing departments: {missing_depts}")
                
                return len(departments) == 4 and not missing_depts
                
            else:
                self.log_test("Get Departments", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Departments", False, f"Exception: {str(e)}")
            return False
    
    def test_department_authentication(self):
        """Test department login functionality"""
        print("\n=== Testing Department Authentication ===")
        
        if not self.departments:
            self.log_test("Department Authentication", False, "No departments available for testing")
            return False
        
        success_count = 0
        
        # Test correct passwords
        expected_passwords = {
            "Wachabteilung A": "passwordA",
            "Wachabteilung B": "passwordB", 
            "Wachabteilung C": "passwordC",
            "Wachabteilung D": "passwordD"
        }
        
        for dept in self.departments:
            dept_name = dept['name']
            expected_password = expected_passwords.get(dept_name)
            
            if expected_password:
                try:
                    # Test correct login
                    login_data = {
                        "department_name": dept_name,
                        "password": expected_password
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department", 
                                               json=login_data)
                    
                    if response.status_code == 200:
                        login_result = response.json()
                        if login_result.get('department_id') == dept['id']:
                            self.log_test(f"Login {dept_name}", True, 
                                        f"Successful authentication")
                            success_count += 1
                        else:
                            self.log_test(f"Login {dept_name}", False, 
                                        "Department ID mismatch")
                    else:
                        self.log_test(f"Login {dept_name}", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
                    # Test wrong password
                    wrong_login_data = {
                        "department_name": dept_name,
                        "password": "wrongpassword"
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department", 
                                               json=wrong_login_data)
                    
                    if response.status_code == 401:
                        self.log_test(f"Wrong Password {dept_name}", True, 
                                    "Correctly rejected wrong password")
                    else:
                        self.log_test(f"Wrong Password {dept_name}", False, 
                                    f"Should reject wrong password, got {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Login {dept_name}", False, f"Exception: {str(e)}")
        
        return success_count == len(self.departments)
    
    def test_employee_management(self):
        """Test employee creation and retrieval"""
        print("\n=== Testing Employee Management ===")
        
        if not self.departments:
            self.log_test("Employee Management", False, "No departments available")
            return False
        
        success_count = 0
        
        # Create test employees for each department
        for dept in self.departments:
            try:
                # Create employee
                employee_data = {
                    "name": f"Hans Mueller ({dept['name'][-1]})",  # Hans Mueller (A), etc.
                    "department_id": dept['id']
                }
                
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                
                if response.status_code == 200:
                    employee = response.json()
                    self.employees.append(employee)
                    
                    # Verify employee data
                    if (employee['name'] == employee_data['name'] and 
                        employee['department_id'] == dept['id'] and
                        employee['breakfast_balance'] == 0.0 and
                        employee['drinks_sweets_balance'] == 0.0):
                        
                        self.log_test(f"Create Employee {dept['name']}", True, 
                                    f"Created: {employee['name']}")
                        success_count += 1
                    else:
                        self.log_test(f"Create Employee {dept['name']}", False, 
                                    "Employee data validation failed")
                else:
                    self.log_test(f"Create Employee {dept['name']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Create Employee {dept['name']}", False, f"Exception: {str(e)}")
        
        # Test retrieving department employees
        for dept in self.departments:
            try:
                response = self.session.get(f"{API_BASE}/departments/{dept['id']}/employees")
                
                if response.status_code == 200:
                    dept_employees = response.json()
                    dept_employee_count = len([emp for emp in self.employees 
                                             if emp['department_id'] == dept['id']])
                    
                    if len(dept_employees) == dept_employee_count:
                        self.log_test(f"Get Employees {dept['name']}", True, 
                                    f"Found {len(dept_employees)} employees")
                    else:
                        self.log_test(f"Get Employees {dept['name']}", False, 
                                    f"Expected {dept_employee_count}, found {len(dept_employees)}")
                else:
                    self.log_test(f"Get Employees {dept['name']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Get Employees {dept['name']}", False, f"Exception: {str(e)}")
        
        return success_count == len(self.departments)
    
    def test_menu_endpoints(self):
        """Test all menu endpoints for German items and Euro pricing"""
        print("\n=== Testing Menu Endpoints ===")
        
        menu_tests = [
            {
                'endpoint': 'breakfast',
                'expected_items': ['hell', 'dunkel', 'vollkorn'],
                'price_field': 'roll_type'
            },
            {
                'endpoint': 'toppings', 
                'expected_items': ['ruehrei', 'spiegelei', 'eiersalat', 'salami', 'schinken', 'kaese', 'butter'],
                'price_field': 'topping_type'
            },
            {
                'endpoint': 'drinks',
                'expected_items': ['Kaffee', 'Tee', 'Wasser', 'Orangensaft', 'Apfelsaft', 'Cola'],
                'price_field': 'name'
            },
            {
                'endpoint': 'sweets',
                'expected_items': ['Schokoriegel', 'Keks', 'Apfel', 'Banane', 'Kuchen'],
                'price_field': 'name'
            }
        ]
        
        success_count = 0
        
        for menu_test in menu_tests:
            try:
                response = self.session.get(f"{API_BASE}/menu/{menu_test['endpoint']}")
                
                if response.status_code == 200:
                    items = response.json()
                    self.menu_items[menu_test['endpoint']] = items
                    
                    # Check if all expected items are present
                    item_values = [item[menu_test['price_field']] for item in items]
                    missing_items = [item for item in menu_test['expected_items'] 
                                   if item not in item_values]
                    
                    if not missing_items:
                        self.log_test(f"Menu {menu_test['endpoint'].title()}", True, 
                                    f"All German items found: {len(items)} items")
                        
                        # Check Euro pricing (all prices should be > 0 and reasonable)
                        valid_prices = all(0 < item['price'] < 10 for item in items)
                        if valid_prices:
                            self.log_test(f"Pricing {menu_test['endpoint'].title()}", True, 
                                        f"Valid Euro pricing: €{min(item['price'] for item in items):.2f} - €{max(item['price'] for item in items):.2f}")
                            success_count += 1
                        else:
                            self.log_test(f"Pricing {menu_test['endpoint'].title()}", False, 
                                        "Invalid pricing found")
                    else:
                        self.log_test(f"Menu {menu_test['endpoint'].title()}", False, 
                                    f"Missing items: {missing_items}")
                else:
                    self.log_test(f"Menu {menu_test['endpoint'].title()}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Menu {menu_test['endpoint'].title()}", False, f"Exception: {str(e)}")
        
        return success_count == len(menu_tests)
    
    def test_order_processing(self):
        """Test creating different types of orders"""
        print("\n=== Testing Order Processing ===")
        
        if not self.employees or not any(self.menu_items.values()):
            self.log_test("Order Processing", False, "Missing employees or menu items")
            return False
        
        success_count = 0
        test_employee = self.employees[0]  # Use first employee for testing
        
        # Test 1: Breakfast Order
        try:
            breakfast_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "hell",
                        "roll_count": 2,
                        "toppings": ["ruehrei", "kaese"]
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            
            if response.status_code == 200:
                order = response.json()
                if order['total_price'] > 0:
                    self.log_test("Breakfast Order", True, 
                                f"Created order with total: €{order['total_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Breakfast Order", False, "Invalid total price")
            else:
                self.log_test("Breakfast Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Breakfast Order", False, f"Exception: {str(e)}")
        
        # Test 2: Drinks Order
        if self.menu_items['drinks']:
            try:
                drink_item = self.menu_items['drinks'][0]  # Get first drink
                drinks_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "drinks",
                    "drink_items": {
                        drink_item['id']: 3
                    }
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=drinks_order)
                
                if response.status_code == 200:
                    order = response.json()
                    expected_total = drink_item['price'] * 3
                    if abs(order['total_price'] - expected_total) < 0.01:
                        self.log_test("Drinks Order", True, 
                                    f"Created drinks order: €{order['total_price']:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Drinks Order", False, 
                                    f"Price mismatch: expected €{expected_total:.2f}, got €{order['total_price']:.2f}")
                else:
                    self.log_test("Drinks Order", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Drinks Order", False, f"Exception: {str(e)}")
        
        # Test 3: Sweets Order
        if self.menu_items['sweets']:
            try:
                sweet_item = self.menu_items['sweets'][0]  # Get first sweet
                sweets_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "sweets",
                    "sweet_items": {
                        sweet_item['id']: 2
                    }
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=sweets_order)
                
                if response.status_code == 200:
                    order = response.json()
                    expected_total = sweet_item['price'] * 2
                    if abs(order['total_price'] - expected_total) < 0.01:
                        self.log_test("Sweets Order", True, 
                                    f"Created sweets order: €{order['total_price']:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Sweets Order", False, 
                                    f"Price mismatch: expected €{expected_total:.2f}, got €{order['total_price']:.2f}")
                else:
                    self.log_test("Sweets Order", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Sweets Order", False, f"Exception: {str(e)}")
        
        return success_count >= 2  # At least 2 out of 3 order types should work
    
    def test_daily_summary(self):
        """Test daily summary functionality"""
        print("\n=== Testing Daily Summary ===")
        
        if not self.departments:
            self.log_test("Daily Summary", False, "No departments available")
            return False
        
        try:
            test_dept = self.departments[0]
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check if summary has expected structure
                required_fields = ['date', 'breakfast_summary', 'drinks_summary', 'sweets_summary']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Daily Summary Structure", True, 
                                f"Summary for {summary['date']}")
                    
                    # Check if date is today's date
                    today = datetime.now().date().isoformat()
                    if summary['date'] == today:
                        self.log_test("Daily Summary Date", True, f"Correct date: {today}")
                        return True
                    else:
                        self.log_test("Daily Summary Date", False, 
                                    f"Expected {today}, got {summary['date']}")
                        return False
                else:
                    self.log_test("Daily Summary Structure", False, 
                                f"Missing fields: {missing_fields}")
                    return False
            else:
                self.log_test("Daily Summary", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Daily Summary", False, f"Exception: {str(e)}")
            return False
    
    def test_admin_functions(self):
        """Test admin login and order deletion"""
        print("\n=== Testing Admin Functions ===")
        
        success_count = 0
        
        # Test admin login
        try:
            admin_login = {"password": "admin123"}
            response = self.session.post(f"{API_BASE}/login/admin", json=admin_login)
            
            if response.status_code == 200:
                admin_result = response.json()
                if admin_result.get('role') == 'admin':
                    self.log_test("Admin Login", True, "Successful admin authentication")
                    success_count += 1
                else:
                    self.log_test("Admin Login", False, "Invalid admin response")
            else:
                self.log_test("Admin Login", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
            # Test wrong admin password
            wrong_admin_login = {"password": "wrongpassword"}
            response = self.session.post(f"{API_BASE}/login/admin", json=wrong_admin_login)
            
            if response.status_code == 401:
                self.log_test("Admin Wrong Password", True, "Correctly rejected wrong password")
                success_count += 1
            else:
                self.log_test("Admin Wrong Password", False, 
                            f"Should reject wrong password, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
        
        return success_count >= 1
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🧪 Starting German Canteen Management System Backend Tests")
        print(f"🌐 Testing against: {API_BASE}")
        print("=" * 60)
        
        # Run tests in order
        tests = [
            ("Data Initialization", self.test_data_initialization),
            ("Department Retrieval", self.test_get_departments),
            ("Department Authentication", self.test_department_authentication),
            ("Employee Management", self.test_employee_management),
            ("Menu Endpoints", self.test_menu_endpoints),
            ("Order Processing", self.test_order_processing),
            ("Daily Summary", self.test_daily_summary),
            ("Admin Functions", self.test_admin_functions)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)
        
        print(f"✅ Passed: {passed_tests}/{total_tests} test suites")
        print(f"❌ Failed: {total_tests - passed_tests}/{total_tests} test suites")
        
        # Print individual test results
        print(f"\n📊 Detailed Results ({len(self.test_results)} individual tests):")
        passed_individual = sum(1 for result in self.test_results if result['success'])
        failed_individual = len(self.test_results) - passed_individual
        
        print(f"   ✅ Individual tests passed: {passed_individual}")
        print(f"   ❌ Individual tests failed: {failed_individual}")
        
        if failed_individual > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['message']}")
        
        # Overall status
        success_rate = passed_tests / total_tests
        if success_rate >= 0.8:
            print(f"\n🎉 OVERALL STATUS: GOOD ({success_rate:.1%} test suites passed)")
            return True
        elif success_rate >= 0.6:
            print(f"\n⚠️  OVERALL STATUS: PARTIAL ({success_rate:.1%} test suites passed)")
            return False
        else:
            print(f"\n🚨 OVERALL STATUS: CRITICAL ISSUES ({success_rate:.1%} test suites passed)")
            return False

if __name__ == "__main__":
    tester = CanteenTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)