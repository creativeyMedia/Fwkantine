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
    
    def test_department_admin_authentication(self):
        """Test department admin login functionality with new admin passwords"""
        print("\n=== Testing Department Admin Authentication ===")
        
        if not self.departments:
            self.log_test("Department Admin Authentication", False, "No departments available for testing")
            return False
        
        success_count = 0
        
        # Test correct admin passwords
        expected_admin_passwords = {
            "Wachabteilung A": "adminA",
            "Wachabteilung B": "adminB", 
            "Wachabteilung C": "adminC",
            "Wachabteilung D": "adminD"
        }
        
        for dept in self.departments:
            dept_name = dept['name']
            expected_admin_password = expected_admin_passwords.get(dept_name)
            
            if expected_admin_password:
                try:
                    # Test correct admin login
                    admin_login_data = {
                        "department_name": dept_name,
                        "admin_password": expected_admin_password
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department-admin", 
                                               json=admin_login_data)
                    
                    if response.status_code == 200:
                        login_result = response.json()
                        if (login_result.get('department_id') == dept['id'] and 
                            login_result.get('role') == 'department_admin'):
                            self.log_test(f"Admin Login {dept_name}", True, 
                                        f"Successful admin authentication with role assignment")
                            success_count += 1
                        else:
                            self.log_test(f"Admin Login {dept_name}", False, 
                                        "Department ID or role mismatch")
                    else:
                        self.log_test(f"Admin Login {dept_name}", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
                    # Test wrong admin password
                    wrong_admin_login_data = {
                        "department_name": dept_name,
                        "admin_password": "wrongadminpassword"
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department-admin", 
                                               json=wrong_admin_login_data)
                    
                    if response.status_code == 401:
                        self.log_test(f"Wrong Admin Password {dept_name}", True, 
                                    "Correctly rejected wrong admin password")
                    else:
                        self.log_test(f"Wrong Admin Password {dept_name}", False, 
                                    f"Should reject wrong admin password, got {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Admin Login {dept_name}", False, f"Exception: {str(e)}")
        
        return success_count == len(self.departments)

    def test_employee_profile_endpoint(self):
        """Test the enhanced employee profile endpoint with order history"""
        print("\n=== Testing Employee Profile Endpoint ===")
        
        if not self.employees:
            self.log_test("Employee Profile", False, "No employees available for testing")
            return False
        
        test_employee = self.employees[0]
        success_count = 0
        
        # First create some test orders for the employee
        try:
            # Create breakfast order
            breakfast_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "hell",
                        "roll_count": 1,
                        "toppings": ["ruehrei", "kaese"]
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                self.log_test("Create Test Breakfast Order", True, "Order created for profile testing")
            
            # Create drinks order if drinks available
            if self.menu_items['drinks']:
                drink_item = self.menu_items['drinks'][0]
                drinks_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "drinks",
                    "drink_items": {drink_item['id']: 2}
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=drinks_order)
                if response.status_code == 200:
                    self.log_test("Create Test Drinks Order", True, "Drinks order created for profile testing")
            
            # Create sweets order if sweets available
            if self.menu_items['sweets']:
                sweet_item = self.menu_items['sweets'][0]
                sweets_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "sweets",
                    "sweet_items": {sweet_item['id']: 1}
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=sweets_order)
                if response.status_code == 200:
                    self.log_test("Create Test Sweets Order", True, "Sweets order created for profile testing")
            
        except Exception as e:
            self.log_test("Create Test Orders", False, f"Exception: {str(e)}")
        
        # Now test the profile endpoint
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                
                # Check required fields
                required_fields = ['employee', 'order_history', 'total_orders', 'breakfast_total', 'drinks_sweets_total']
                missing_fields = [field for field in required_fields if field not in profile]
                
                if not missing_fields:
                    self.log_test("Profile Structure", True, "All required fields present")
                    success_count += 1
                    
                    # Check employee details
                    employee_data = profile['employee']
                    if (employee_data['id'] == test_employee['id'] and 
                        employee_data['name'] == test_employee['name']):
                        self.log_test("Profile Employee Data", True, "Employee details correct")
                        success_count += 1
                    else:
                        self.log_test("Profile Employee Data", False, "Employee details mismatch")
                    
                    # Check order history with German descriptions
                    order_history = profile['order_history']
                    if isinstance(order_history, list) and len(order_history) > 0:
                        self.log_test("Profile Order History", True, f"Found {len(order_history)} orders")
                        success_count += 1
                        
                        # Check for readable German descriptions
                        has_readable_items = any('readable_items' in order for order in order_history)
                        if has_readable_items:
                            self.log_test("Profile German Descriptions", True, "Orders have German readable descriptions")
                            success_count += 1
                        else:
                            self.log_test("Profile German Descriptions", False, "Missing German readable descriptions")
                    else:
                        self.log_test("Profile Order History", False, "No order history found")
                    
                    # Check balance summaries
                    if (isinstance(profile['total_orders'], int) and 
                        isinstance(profile['breakfast_total'], (int, float)) and
                        isinstance(profile['drinks_sweets_total'], (int, float))):
                        self.log_test("Profile Balance Summaries", True, 
                                    f"Total orders: {profile['total_orders']}, Breakfast: €{profile['breakfast_total']:.2f}, Drinks/Sweets: €{profile['drinks_sweets_total']:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Profile Balance Summaries", False, "Invalid balance data types")
                        
                else:
                    self.log_test("Profile Structure", False, f"Missing fields: {missing_fields}")
                    
            else:
                self.log_test("Employee Profile", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Employee Profile", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_department_admin_menu_management(self):
        """Test department admin menu management functionality"""
        print("\n=== Testing Department Admin Menu Management ===")
        
        if not self.menu_items or not any(self.menu_items.values()):
            self.log_test("Menu Management", False, "No menu items available for testing")
            return False
        
        success_count = 0
        
        # Test breakfast price updates
        if self.menu_items['breakfast']:
            try:
                breakfast_item = self.menu_items['breakfast'][0]
                original_price = breakfast_item['price']
                new_price = original_price + 0.10
                
                update_data = {"price": new_price}
                response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{breakfast_item['id']}", 
                                          json=update_data)
                
                if response.status_code == 200:
                    self.log_test("Update Breakfast Price", True, 
                                f"Updated price from €{original_price:.2f} to €{new_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Update Breakfast Price", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Update Breakfast Price", False, f"Exception: {str(e)}")
        
        # Test toppings price updates
        if self.menu_items['toppings']:
            try:
                topping_item = self.menu_items['toppings'][0]
                original_price = topping_item['price']
                new_price = original_price + 0.05
                
                update_data = {"price": new_price}
                response = self.session.put(f"{API_BASE}/department-admin/menu/toppings/{topping_item['id']}", 
                                          json=update_data)
                
                if response.status_code == 200:
                    self.log_test("Update Toppings Price", True, 
                                f"Updated topping price from €{original_price:.2f} to €{new_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Update Toppings Price", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Update Toppings Price", False, f"Exception: {str(e)}")
        
        # Test drinks price and name updates
        if self.menu_items['drinks']:
            try:
                drink_item = self.menu_items['drinks'][0]
                original_price = drink_item['price']
                original_name = drink_item['name']
                new_price = original_price + 0.15
                new_name = f"{original_name} Premium"
                
                update_data = {"price": new_price, "name": new_name}
                response = self.session.put(f"{API_BASE}/department-admin/menu/drinks/{drink_item['id']}", 
                                          json=update_data)
                
                if response.status_code == 200:
                    self.log_test("Update Drinks Price/Name", True, 
                                f"Updated '{original_name}' to '{new_name}' with price €{new_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Update Drinks Price/Name", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Update Drinks Price/Name", False, f"Exception: {str(e)}")
        
        # Test sweets price and name updates
        if self.menu_items['sweets']:
            try:
                sweet_item = self.menu_items['sweets'][0]
                original_price = sweet_item['price']
                original_name = sweet_item['name']
                new_price = original_price + 0.20
                new_name = f"{original_name} Deluxe"
                
                update_data = {"price": new_price, "name": new_name}
                response = self.session.put(f"{API_BASE}/department-admin/menu/sweets/{sweet_item['id']}", 
                                          json=update_data)
                
                if response.status_code == 200:
                    self.log_test("Update Sweets Price/Name", True, 
                                f"Updated '{original_name}' to '{new_name}' with price €{new_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Update Sweets Price/Name", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Update Sweets Price/Name", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_menu_item_creation_deletion(self):
        """Test creating and deleting menu items"""
        print("\n=== Testing Menu Item Creation & Deletion ===")
        
        success_count = 0
        created_items = []
        
        # Test creating new drink item
        try:
            new_drink_data = {"name": "Heisse Schokolade", "price": 1.80}
            response = self.session.post(f"{API_BASE}/department-admin/menu/drinks", 
                                       json=new_drink_data)
            
            if response.status_code == 200:
                new_drink = response.json()
                created_items.append(('drinks', new_drink['id']))
                self.log_test("Create New Drink", True, 
                            f"Created '{new_drink['name']}' for €{new_drink['price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create New Drink", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create New Drink", False, f"Exception: {str(e)}")
        
        # Test creating new sweet item
        try:
            new_sweet_data = {"name": "Lebkuchen", "price": 1.25}
            response = self.session.post(f"{API_BASE}/department-admin/menu/sweets", 
                                       json=new_sweet_data)
            
            if response.status_code == 200:
                new_sweet = response.json()
                created_items.append(('sweets', new_sweet['id']))
                self.log_test("Create New Sweet", True, 
                            f"Created '{new_sweet['name']}' for €{new_sweet['price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create New Sweet", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create New Sweet", False, f"Exception: {str(e)}")
        
        # Test deleting created items
        for item_type, item_id in created_items:
            try:
                response = self.session.delete(f"{API_BASE}/department-admin/menu/{item_type}/{item_id}")
                
                if response.status_code == 200:
                    self.log_test(f"Delete {item_type.title()} Item", True, 
                                f"Successfully deleted item {item_id}")
                    success_count += 1
                else:
                    self.log_test(f"Delete {item_type.title()} Item", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Delete {item_type.title()} Item", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_data_integrity(self):
        """Test data integrity after menu updates and operations"""
        print("\n=== Testing Data Integrity ===")
        
        success_count = 0
        
        # Test that menu fetches reflect updates
        try:
            # Fetch updated menus
            response = self.session.get(f"{API_BASE}/menu/drinks")
            if response.status_code == 200:
                drinks = response.json()
                self.log_test("Menu Fetch After Updates", True, 
                            f"Successfully fetched {len(drinks)} drinks after updates")
                success_count += 1
            else:
                self.log_test("Menu Fetch After Updates", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Menu Fetch After Updates", False, f"Exception: {str(e)}")
        
        # Test employee profile shows German translations
        if self.employees:
            try:
                test_employee = self.employees[0]
                response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
                
                if response.status_code == 200:
                    profile = response.json()
                    order_history = profile.get('order_history', [])
                    
                    # Check for German translations in order descriptions
                    has_german_translations = False
                    for order in order_history:
                        if 'readable_items' in order:
                            for item in order['readable_items']:
                                description = item.get('description', '')
                                # Check for German words
                                german_words = ['Brötchen', 'Rührei', 'Spiegelei', 'Käse', 'Schinken']
                                if any(word in description for word in german_words):
                                    has_german_translations = True
                                    break
                    
                    if has_german_translations:
                        self.log_test("German Translation Integrity", True, 
                                    "Employee profile shows proper German order descriptions")
                        success_count += 1
                    else:
                        self.log_test("German Translation Integrity", False, 
                                    "Missing German translations in order descriptions")
                else:
                    self.log_test("Profile Data Integrity", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Profile Data Integrity", False, f"Exception: {str(e)}")
        
        # Test Euro pricing consistency
        try:
            all_menus = ['breakfast', 'toppings', 'drinks', 'sweets']
            euro_pricing_valid = True
            
            for menu_type in all_menus:
                response = self.session.get(f"{API_BASE}/menu/{menu_type}")
                if response.status_code == 200:
                    items = response.json()
                    for item in items:
                        if not (0 < item['price'] < 20):  # Reasonable Euro price range
                            euro_pricing_valid = False
                            break
            
            if euro_pricing_valid:
                self.log_test("Euro Pricing Integrity", True, 
                            "All menu items have valid Euro pricing")
                success_count += 1
            else:
                self.log_test("Euro Pricing Integrity", False, 
                            "Invalid Euro pricing found in menu items")
                
        except Exception as e:
            self.log_test("Euro Pricing Integrity", False, f"Exception: {str(e)}")
        
        return success_count >= 2

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
            ("Department Admin Authentication", self.test_department_admin_authentication),
            ("Employee Management", self.test_employee_management),
            ("Menu Endpoints", self.test_menu_endpoints),
            ("Order Processing", self.test_order_processing),
            ("Employee Profile Endpoint", self.test_employee_profile_endpoint),
            ("Department Admin Menu Management", self.test_department_admin_menu_management),
            ("Menu Item Creation & Deletion", self.test_menu_item_creation_deletion),
            ("Data Integrity", self.test_data_integrity),
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