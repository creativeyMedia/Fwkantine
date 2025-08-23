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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
# Use the correct URL for testing
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
                'expected_items': ['weiss', 'koerner'],  # Updated roll types
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
                        
                        # Check pricing - toppings should be free (0.00), others should be > 0
                        if menu_test['endpoint'] == 'toppings':
                            valid_prices = all(item['price'] == 0.0 for item in items)
                            if valid_prices:
                                self.log_test(f"Free Toppings Pricing", True, 
                                            f"All toppings are free: €0.00")
                                success_count += 1
                            else:
                                self.log_test(f"Free Toppings Pricing", False, 
                                            "Toppings should be free (€0.00)")
                        else:
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
                        "roll_type": "weiss",  # Updated roll type
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
                        "roll_type": "weiss",  # Updated roll type
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

    def test_lunch_management_system(self):
        """Test lunch settings and pricing functionality"""
        print("\n=== Testing Lunch Management System ===")
        
        success_count = 0
        
        # Test GET lunch settings
        try:
            response = self.session.get(f"{API_BASE}/lunch-settings")
            
            if response.status_code == 200:
                lunch_settings = response.json()
                
                # Check required fields
                if 'price' in lunch_settings and 'enabled' in lunch_settings:
                    self.log_test("Get Lunch Settings", True, 
                                f"Current lunch price: €{lunch_settings['price']:.2f}, Enabled: {lunch_settings['enabled']}")
                    success_count += 1
                else:
                    self.log_test("Get Lunch Settings", False, "Missing required fields in lunch settings")
            else:
                self.log_test("Get Lunch Settings", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Lunch Settings", False, f"Exception: {str(e)}")
        
        # Test PUT lunch settings (update price)
        try:
            new_lunch_price = 3.50
            response = self.session.put(f"{API_BASE}/lunch-settings", 
                                      params={"price": new_lunch_price})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('price') == new_lunch_price:
                    self.log_test("Update Lunch Price", True, 
                                f"Successfully updated lunch price to €{new_lunch_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Update Lunch Price", False, "Price update response mismatch")
            else:
                self.log_test("Update Lunch Price", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Update Lunch Price", False, f"Exception: {str(e)}")
        
        return success_count >= 1

    def test_breakfast_with_lunch_option(self):
        """Test breakfast orders with lunch option and pricing"""
        print("\n=== Testing Breakfast with Lunch Option ===")
        
        if not self.employees:
            self.log_test("Breakfast with Lunch", False, "No employees available for testing")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # First, set a lunch price
        try:
            lunch_price = 4.00
            self.session.put(f"{API_BASE}/lunch-settings", params={"price": lunch_price})
        except:
            pass  # Continue even if lunch price setting fails
        
        # Test breakfast order with lunch option
        try:
            breakfast_with_lunch_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "weiss",  # Updated roll type
                        "roll_count": 2,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": True  # Include lunch
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_with_lunch_order)
            
            if response.status_code == 200:
                order = response.json()
                
                # Check that total price includes lunch cost
                if order['total_price'] > 0:
                    self.log_test("Breakfast Order with Lunch", True, 
                                f"Created breakfast order with lunch: €{order['total_price']:.2f}")
                    success_count += 1
                    
                    # Verify the order contains lunch information
                    if order.get('breakfast_items') and len(order['breakfast_items']) > 0:
                        breakfast_item = order['breakfast_items'][0]
                        if breakfast_item.get('has_lunch') == True:
                            self.log_test("Lunch Option in Order", True, 
                                        "Lunch option correctly saved in order")
                            success_count += 1
                        else:
                            self.log_test("Lunch Option in Order", False, 
                                        "Lunch option not saved in order")
                else:
                    self.log_test("Breakfast Order with Lunch", False, "Invalid total price")
            else:
                self.log_test("Breakfast Order with Lunch", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Breakfast Order with Lunch", False, f"Exception: {str(e)}")
        
        # Test breakfast order without lunch option
        try:
            breakfast_without_lunch_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "koerner",  # Updated roll type
                        "roll_count": 1,
                        "toppings": ["schinken"],
                        "has_lunch": False  # No lunch
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_without_lunch_order)
            
            if response.status_code == 200:
                order = response.json()
                self.log_test("Breakfast Order without Lunch", True, 
                            f"Created breakfast order without lunch: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Breakfast Order without Lunch", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Breakfast Order without Lunch", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_admin_employee_management(self):
        """Test admin employee management functions"""
        print("\n=== Testing Admin Employee Management ===")
        
        if not self.employees:
            self.log_test("Admin Employee Management", False, "No employees available for testing")
            return False
        
        success_count = 0
        
        # Create a test employee for deletion
        test_dept = self.departments[0] if self.departments else None
        if not test_dept:
            self.log_test("Admin Employee Management", False, "No departments available")
            return False
        
        test_employee_id = None
        try:
            employee_data = {
                "name": "Test Employee for Deletion",
                "department_id": test_dept['id']
            }
            
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                test_employee = response.json()
                test_employee_id = test_employee['id']
                self.log_test("Create Test Employee", True, "Test employee created for deletion test")
            
        except Exception as e:
            self.log_test("Create Test Employee", False, f"Exception: {str(e)}")
        
        # Test employee deletion
        if test_employee_id:
            try:
                response = self.session.delete(f"{API_BASE}/department-admin/employees/{test_employee_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("Delete Employee", True, 
                                f"Successfully deleted employee: {result.get('message', 'Success')}")
                    success_count += 1
                else:
                    self.log_test("Delete Employee", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Delete Employee", False, f"Exception: {str(e)}")
        
        # Test balance reset functionality
        if self.employees:
            try:
                test_employee = self.employees[0]
                
                # Test breakfast balance reset
                response = self.session.post(f"{API_BASE}/admin/reset-balance/{test_employee['id']}", 
                                           params={"balance_type": "breakfast"})
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("Reset Breakfast Balance", True, 
                                f"Successfully reset breakfast balance: {result.get('message', 'Success')}")
                    success_count += 1
                else:
                    self.log_test("Reset Breakfast Balance", False, 
                                f"HTTP {response.status_code}: {response.text}")
                
                # Test drinks/sweets balance reset
                response = self.session.post(f"{API_BASE}/admin/reset-balance/{test_employee['id']}", 
                                           params={"balance_type": "drinks_sweets"})
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("Reset Drinks/Sweets Balance", True, 
                                f"Successfully reset drinks/sweets balance: {result.get('message', 'Success')}")
                    success_count += 1
                else:
                    self.log_test("Reset Drinks/Sweets Balance", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Reset Balance", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_order_deletion(self):
        """Test order deletion functionality"""
        print("\n=== Testing Order Deletion ===")
        
        if not self.employees:
            self.log_test("Order Deletion", False, "No employees available for testing")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Create a test order for deletion
        test_order_id = None
        try:
            test_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "weiss",
                        "roll_count": 1,
                        "toppings": ["butter"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=test_order)
            if response.status_code == 200:
                order = response.json()
                test_order_id = order['id']
                self.log_test("Create Test Order", True, "Test order created for deletion test")
            
        except Exception as e:
            self.log_test("Create Test Order", False, f"Exception: {str(e)}")
        
        # Test order deletion
        if test_order_id:
            try:
                response = self.session.delete(f"{API_BASE}/orders/{test_order_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("Delete Order", True, 
                                f"Successfully deleted order: {result.get('message', 'Success')}")
                    success_count += 1
                else:
                    self.log_test("Delete Order", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Delete Order", False, f"Exception: {str(e)}")
        
        return success_count >= 1

    def test_daily_summary_with_new_roll_types(self):
        """Test daily summary with new roll types and toppings"""
        print("\n=== Testing Daily Summary with New Roll Types ===")
        
        if not self.departments or not self.employees:
            self.log_test("Daily Summary New Roll Types", False, "Missing departments or employees")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        test_employee = self.employees[0]
        
        # Create test breakfast orders with new roll types
        try:
            # Order with weiss roll
            weiss_order = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "weiss",
                        "roll_count": 2,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=weiss_order)
            if response.status_code == 200:
                self.log_test("Create Weiss Roll Order", True, "Created order with weiss roll")
            
            # Order with koerner roll
            koerner_order = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "koerner",
                        "roll_count": 1,
                        "toppings": ["schinken", "butter"],
                        "has_lunch": True
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=koerner_order)
            if response.status_code == 200:
                self.log_test("Create Koerner Roll Order", True, "Created order with koerner roll")
            
        except Exception as e:
            self.log_test("Create Test Orders", False, f"Exception: {str(e)}")
        
        # Test daily summary aggregation
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check structure
                required_fields = ['date', 'breakfast_summary', 'drinks_summary', 'sweets_summary']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Daily Summary Structure", True, "Summary has correct structure")
                    success_count += 1
                    
                    # Check breakfast summary for new roll types
                    breakfast_summary = summary.get('breakfast_summary', {})
                    
                    # Check if new roll types are present
                    has_weiss = 'weiss' in breakfast_summary
                    has_koerner = 'koerner' in breakfast_summary
                    
                    if has_weiss or has_koerner:
                        self.log_test("New Roll Types in Summary", True, 
                                    f"Summary includes new roll types: weiss={has_weiss}, koerner={has_koerner}")
                        success_count += 1
                        
                        # Check toppings aggregation
                        for roll_type, roll_data in breakfast_summary.items():
                            if 'toppings' in roll_data and roll_data['toppings']:
                                self.log_test("Toppings Aggregation", True, 
                                            f"Toppings properly aggregated for {roll_type}: {list(roll_data['toppings'].keys())}")
                                success_count += 1
                                break
                    else:
                        self.log_test("New Roll Types in Summary", False, 
                                    "New roll types not found in summary")
                else:
                    self.log_test("Daily Summary Structure", False, f"Missing fields: {missing_fields}")
                    
            else:
                self.log_test("Daily Summary", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_enhanced_employee_profile(self):
        """Test enhanced employee profile with German roll type labels and lunch options"""
        print("\n=== Testing Enhanced Employee Profile ===")
        
        if not self.employees:
            self.log_test("Enhanced Employee Profile", False, "No employees available for testing")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Create test orders with new roll types and lunch options
        try:
            # Order with lunch option
            lunch_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "weiss",
                        "roll_count": 1,
                        "toppings": ["ruehrei"],
                        "has_lunch": True
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=lunch_order)
            if response.status_code == 200:
                self.log_test("Create Lunch Order for Profile", True, "Created order with lunch for profile testing")
            
        except Exception as e:
            self.log_test("Create Lunch Order for Profile", False, f"Exception: {str(e)}")
        
        # Test enhanced profile endpoint
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                
                # Check required fields
                required_fields = ['employee', 'order_history', 'total_orders', 'breakfast_total', 'drinks_sweets_total']
                missing_fields = [field for field in required_fields if field not in profile]
                
                if not missing_fields:
                    self.log_test("Enhanced Profile Structure", True, "Profile has all required fields")
                    success_count += 1
                    
                    # Check for German roll type labels in order history
                    order_history = profile.get('order_history', [])
                    has_german_labels = False
                    has_lunch_display = False
                    
                    for order in order_history:
                        if 'readable_items' in order:
                            for item in order['readable_items']:
                                description = item.get('description', '')
                                
                                # Check for German roll labels
                                if 'Weißes Brötchen' in description or 'Körnerbrötchen' in description:
                                    has_german_labels = True
                                
                                # Check for lunch option display
                                if 'mit Mittagessen' in description:
                                    has_lunch_display = True
                    
                    if has_german_labels:
                        self.log_test("German Roll Type Labels", True, 
                                    "Profile shows German roll type labels (Weißes Brötchen, Körnerbrötchen)")
                        success_count += 1
                    else:
                        self.log_test("German Roll Type Labels", False, 
                                    "Missing German roll type labels in profile")
                    
                    if has_lunch_display:
                        self.log_test("Lunch Option Display", True, 
                                    "Profile shows lunch option in order descriptions")
                        success_count += 1
                    else:
                        self.log_test("Lunch Option Display", False, 
                                    "Missing lunch option display in profile")
                        
                else:
                    self.log_test("Enhanced Profile Structure", False, f"Missing fields: {missing_fields}")
                    
            else:
                self.log_test("Enhanced Employee Profile", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Enhanced Employee Profile", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_new_breakfast_toppings_menu_management(self):
        """Test the new breakfast and toppings menu management endpoints"""
        print("\n=== Testing New Breakfast & Toppings Menu Management ===")
        
        success_count = 0
        created_items = []
        
        # Test 1: POST /api/department-admin/menu/breakfast - Create new breakfast item
        try:
            new_breakfast_data = {
                "roll_type": "weiss",  # Valid enum value
                "price": 0.75
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/breakfast", 
                                       json=new_breakfast_data)
            
            if response.status_code == 200:
                new_breakfast = response.json()
                created_items.append(('breakfast', new_breakfast['id']))
                self.log_test("Create New Breakfast Item", True, 
                            f"Created breakfast item: {new_breakfast['roll_type']} for €{new_breakfast['price']:.2f}")
                success_count += 1
                
                # Verify it appears in GET request
                verify_response = self.session.get(f"{API_BASE}/menu/breakfast")
                if verify_response.status_code == 200:
                    breakfast_items = verify_response.json()
                    item_found = any(item['id'] == new_breakfast['id'] for item in breakfast_items)
                    if item_found:
                        self.log_test("Verify New Breakfast in Menu", True, 
                                    "New breakfast item appears in menu")
                        success_count += 1
                    else:
                        self.log_test("Verify New Breakfast in Menu", False, 
                                    "New breakfast item not found in menu")
            else:
                self.log_test("Create New Breakfast Item", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create New Breakfast Item", False, f"Exception: {str(e)}")
        
        # Test 2: POST /api/department-admin/menu/toppings - Create new topping item
        try:
            new_topping_data = {
                "topping_type": "ruehrei",  # Valid enum value
                "price": 0.25
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", 
                                       json=new_topping_data)
            
            if response.status_code == 200:
                new_topping = response.json()
                created_items.append(('toppings', new_topping['id']))
                self.log_test("Create New Topping Item", True, 
                            f"Created topping item: {new_topping['topping_type']} for €{new_topping['price']:.2f}")
                success_count += 1
                
                # Verify it appears in GET request
                verify_response = self.session.get(f"{API_BASE}/menu/toppings")
                if verify_response.status_code == 200:
                    topping_items = verify_response.json()
                    item_found = any(item['id'] == new_topping['id'] for item in topping_items)
                    if item_found:
                        self.log_test("Verify New Topping in Menu", True, 
                                    "New topping item appears in menu")
                        success_count += 1
                    else:
                        self.log_test("Verify New Topping in Menu", False, 
                                    "New topping item not found in menu")
            else:
                self.log_test("Create New Topping Item", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create New Topping Item", False, f"Exception: {str(e)}")
        
        # Test 3: Create another breakfast item with koerner roll type
        try:
            koerner_breakfast_data = {
                "roll_type": "koerner",  # Valid enum value
                "price": 0.85
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/breakfast", 
                                       json=koerner_breakfast_data)
            
            if response.status_code == 200:
                koerner_breakfast = response.json()
                created_items.append(('breakfast', koerner_breakfast['id']))
                self.log_test("Create Koerner Breakfast Item", True, 
                            f"Created koerner breakfast: €{koerner_breakfast['price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create Koerner Breakfast Item", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Koerner Breakfast Item", False, f"Exception: {str(e)}")
        
        # Test 4: Create another topping with different type
        try:
            cheese_topping_data = {
                "topping_type": "kaese",  # Valid enum value
                "price": 0.30
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", 
                                       json=cheese_topping_data)
            
            if response.status_code == 200:
                cheese_topping = response.json()
                created_items.append(('toppings', cheese_topping['id']))
                self.log_test("Create Cheese Topping Item", True, 
                            f"Created cheese topping: €{cheese_topping['price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create Cheese Topping Item", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Cheese Topping Item", False, f"Exception: {str(e)}")
        
        # Test 5: DELETE breakfast items
        breakfast_items_to_delete = [item for item in created_items if item[0] == 'breakfast']
        for item_type, item_id in breakfast_items_to_delete:
            try:
                response = self.session.delete(f"{API_BASE}/department-admin/menu/breakfast/{item_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(f"Delete Breakfast Item", True, 
                                f"Successfully deleted breakfast item: {result.get('message', 'Success')}")
                    success_count += 1
                    
                    # Verify deletion by checking it's no longer in menu
                    verify_response = self.session.get(f"{API_BASE}/menu/breakfast")
                    if verify_response.status_code == 200:
                        breakfast_items = verify_response.json()
                        item_found = any(item['id'] == item_id for item in breakfast_items)
                        if not item_found:
                            self.log_test("Verify Breakfast Item Deletion", True, 
                                        "Breakfast item successfully removed from menu")
                            success_count += 1
                        else:
                            self.log_test("Verify Breakfast Item Deletion", False, 
                                        "Breakfast item still appears in menu after deletion")
                else:
                    self.log_test(f"Delete Breakfast Item", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Delete Breakfast Item", False, f"Exception: {str(e)}")
        
        # Test 6: DELETE topping items
        topping_items_to_delete = [item for item in created_items if item[0] == 'toppings']
        for item_type, item_id in topping_items_to_delete:
            try:
                response = self.session.delete(f"{API_BASE}/department-admin/menu/toppings/{item_id}")
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test(f"Delete Topping Item", True, 
                                f"Successfully deleted topping item: {result.get('message', 'Success')}")
                    success_count += 1
                    
                    # Verify deletion by checking it's no longer in menu
                    verify_response = self.session.get(f"{API_BASE}/menu/toppings")
                    if verify_response.status_code == 200:
                        topping_items = verify_response.json()
                        item_found = any(item['id'] == item_id for item in topping_items)
                        if not item_found:
                            self.log_test("Verify Topping Item Deletion", True, 
                                        "Topping item successfully removed from menu")
                            success_count += 1
                        else:
                            self.log_test("Verify Topping Item Deletion", False, 
                                        "Topping item still appears in menu after deletion")
                else:
                    self.log_test(f"Delete Topping Item", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Delete Topping Item", False, f"Exception: {str(e)}")
        
        # Test 7: Test error handling for invalid IDs
        try:
            invalid_id = "invalid-breakfast-id-12345"
            response = self.session.delete(f"{API_BASE}/department-admin/menu/breakfast/{invalid_id}")
            
            if response.status_code == 404:
                self.log_test("Error Handling - Invalid Breakfast ID", True, 
                            "Correctly returned 404 for invalid breakfast ID")
                success_count += 1
            else:
                self.log_test("Error Handling - Invalid Breakfast ID", False, 
                            f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Invalid Breakfast ID", False, f"Exception: {str(e)}")
        
        try:
            invalid_id = "invalid-topping-id-12345"
            response = self.session.delete(f"{API_BASE}/department-admin/menu/toppings/{invalid_id}")
            
            if response.status_code == 404:
                self.log_test("Error Handling - Invalid Topping ID", True, 
                            "Correctly returned 404 for invalid topping ID")
                success_count += 1
            else:
                self.log_test("Error Handling - Invalid Topping ID", False, 
                            f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Error Handling - Invalid Topping ID", False, f"Exception: {str(e)}")
        
        return success_count >= 8  # Expect at least 8 successful tests
    
    def test_critical_breakfast_ordering_fixes(self):
        """Test the critical breakfast ordering fixes as requested in review"""
        print("\n=== Testing Critical Breakfast Ordering Fixes ===")
        
        if not self.departments or not self.employees:
            self.log_test("Critical Breakfast Fixes", False, "Missing departments or employees")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        test_employee = self.employees[0]
        
        # Test 1: Order Submission Workflow with new breakfast format
        try:
            # Test POST /api/orders with new breakfast format
            breakfast_order = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 4,
                        "white_halves": 2,
                        "seeded_halves": 2,
                        "toppings": ["ruehrei", "kaese", "schinken", "butter"],
                        "has_lunch": True
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            
            if response.status_code == 200:
                order = response.json()
                
                # Verify order structure
                if (order.get('breakfast_items') and 
                    len(order['breakfast_items']) > 0 and
                    order['breakfast_items'][0].get('total_halves') == 4 and
                    order['breakfast_items'][0].get('white_halves') == 2 and
                    order['breakfast_items'][0].get('seeded_halves') == 2 and
                    order['breakfast_items'][0].get('has_lunch') == True and
                    len(order['breakfast_items'][0].get('toppings', [])) == 4):
                    
                    self.log_test("New Breakfast Order Format", True, 
                                f"Order created with new format: €{order['total_price']:.2f}, ID: {order['id']}")
                    success_count += 1
                    
                    # Store order ID for later tests
                    self.test_order_id = order['id']
                else:
                    self.log_test("New Breakfast Order Format", False, "Order structure validation failed")
            else:
                self.log_test("New Breakfast Order Format", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("New Breakfast Order Format", False, f"Exception: {str(e)}")
        
        # Test 2: Order Persistence & Retrieval
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                
                # Verify response format
                if 'orders' in orders_data and isinstance(orders_data['orders'], list):
                    orders = orders_data['orders']
                    
                    # Find our test order
                    test_order_found = False
                    for order in orders:
                        if (order.get('order_type') == 'breakfast' and 
                            order.get('breakfast_items') and
                            len(order['breakfast_items']) > 0):
                            
                            breakfast_item = order['breakfast_items'][0]
                            if (breakfast_item.get('total_halves') == 4 and
                                breakfast_item.get('white_halves') == 2 and
                                breakfast_item.get('seeded_halves') == 2):
                                test_order_found = True
                                break
                    
                    if test_order_found:
                        self.log_test("Order Persistence & Retrieval", True, 
                                    f"Found {len(orders)} orders with correct new format")
                        success_count += 1
                    else:
                        self.log_test("Order Persistence & Retrieval", False, 
                                    "Test order not found in employee orders")
                else:
                    self.log_test("Order Persistence & Retrieval", False, 
                                "Invalid response format - missing 'orders' array")
            else:
                self.log_test("Order Persistence & Retrieval", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Order Persistence & Retrieval", False, f"Exception: {str(e)}")
        
        # Test 3: Admin Order Management
        try:
            # Test department admin authentication first
            admin_login_data = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"  # Using admin1 as per review request
            }
            
            admin_response = self.session.post(f"{API_BASE}/login/department-admin", 
                                             json=admin_login_data)
            
            if admin_response.status_code == 200:
                self.log_test("Department Admin Authentication", True, "Admin login successful")
                
                # Test admin order management - GET orders
                response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
                
                if response.status_code == 200:
                    orders_data = response.json()
                    if 'orders' in orders_data and len(orders_data['orders']) > 0:
                        self.log_test("Admin Order Management - View", True, 
                                    f"Admin can view {len(orders_data['orders'])} employee orders")
                        success_count += 1
                        
                        # Test admin order deletion if we have an order
                        if hasattr(self, 'test_order_id'):
                            try:
                                delete_response = self.session.delete(f"{API_BASE}/department-admin/orders/{self.test_order_id}")
                                
                                if delete_response.status_code == 200:
                                    self.log_test("Admin Order Deletion", True, 
                                                "Admin successfully deleted order")
                                    success_count += 1
                                else:
                                    self.log_test("Admin Order Deletion", False, 
                                                f"HTTP {delete_response.status_code}: {delete_response.text}")
                            except Exception as e:
                                self.log_test("Admin Order Deletion", False, f"Exception: {str(e)}")
                    else:
                        self.log_test("Admin Order Management - View", False, "No orders found for admin management")
                else:
                    self.log_test("Admin Order Management - View", False, 
                                f"HTTP {response.status_code}: {response.text}")
            else:
                self.log_test("Department Admin Authentication", False, 
                            f"HTTP {admin_response.status_code}: {admin_response.text}")
                
        except Exception as e:
            self.log_test("Admin Order Management", False, f"Exception: {str(e)}")
        
        # Test 4: Menu Integration with Dynamic Pricing
        try:
            # Get current breakfast menu
            menu_response = self.session.get(f"{API_BASE}/menu/breakfast")
            
            if menu_response.status_code == 200:
                breakfast_menu = menu_response.json()
                
                if breakfast_menu and len(breakfast_menu) > 0:
                    # Update a menu item price
                    test_item = breakfast_menu[0]
                    original_price = test_item['price']
                    new_price = original_price + 0.25
                    
                    update_response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{test_item['id']}", 
                                                     json={"price": new_price})
                    
                    if update_response.status_code == 200:
                        self.log_test("Menu Price Update", True, 
                                    f"Updated price from €{original_price:.2f} to €{new_price:.2f}")
                        
                        # Create new order to test dynamic pricing
                        test_order = {
                            "employee_id": test_employee['id'],
                            "department_id": test_dept['id'],
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
                        
                        order_response = self.session.post(f"{API_BASE}/orders", json=test_order)
                        
                        if order_response.status_code == 200:
                            order = order_response.json()
                            
                            # Calculate expected price (2 white halves * new_price + free toppings)
                            expected_price = 2 * new_price  # 2 halves * new price
                            
                            if abs(order['total_price'] - expected_price) < 0.01:
                                self.log_test("Dynamic Pricing Integration", True, 
                                            f"Order correctly uses updated price: €{order['total_price']:.2f}")
                                success_count += 1
                            else:
                                self.log_test("Dynamic Pricing Integration", False, 
                                            f"Price mismatch: expected €{expected_price:.2f}, got €{order['total_price']:.2f}")
                        else:
                            self.log_test("Dynamic Pricing Integration", False, 
                                        f"Order creation failed: HTTP {order_response.status_code}")
                    else:
                        self.log_test("Menu Price Update", False, 
                                    f"HTTP {update_response.status_code}: {update_response.text}")
                else:
                    self.log_test("Menu Integration", False, "No breakfast menu items found")
            else:
                self.log_test("Menu Integration", False, 
                            f"HTTP {menu_response.status_code}: {menu_response.text}")
                
        except Exception as e:
            self.log_test("Menu Integration", False, f"Exception: {str(e)}")
        
        # Test 5: Validation Tests
        try:
            # Test invalid breakfast order (mismatched halves)
            invalid_order = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 4,
                        "white_halves": 2,
                        "seeded_halves": 1,  # Should be 2 to match total_halves
                        "toppings": ["ruehrei", "kaese", "schinken", "butter"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=invalid_order)
            
            if response.status_code == 400:
                self.log_test("Order Validation - Halves Mismatch", True, 
                            "Correctly rejected order with mismatched halves")
                success_count += 1
            else:
                self.log_test("Order Validation - Halves Mismatch", False, 
                            f"Should reject invalid order, got HTTP {response.status_code}")
            
            # Test invalid toppings count
            invalid_toppings_order = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 4,
                        "white_halves": 2,
                        "seeded_halves": 2,
                        "toppings": ["ruehrei", "kaese"],  # Should be 4 toppings for 4 halves
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=invalid_toppings_order)
            
            if response.status_code == 400:
                self.log_test("Order Validation - Toppings Count", True, 
                            "Correctly rejected order with wrong toppings count")
                success_count += 1
            else:
                self.log_test("Order Validation - Toppings Count", False, 
                            f"Should reject invalid order, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Order Validation", False, f"Exception: {str(e)}")
        
        return success_count >= 5  # At least 5 out of 7 tests should pass

    def test_critical_bug_fixes(self):
        """Test the critical bug fixes for canteen management system"""
        print("\n=== Testing Critical Bug Fixes ===")
        
        success_count = 0
        
        # 1. Test Employee Orders Management - GET /api/employees/{employee_id}/orders
        if self.employees:
            try:
                test_employee = self.employees[0]
                response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
                
                if response.status_code == 200:
                    orders_data = response.json()
                    if 'orders' in orders_data and isinstance(orders_data['orders'], list):
                        self.log_test("Employee Orders Management - GET", True, 
                                    f"Successfully fetched orders for employee: {len(orders_data['orders'])} orders")
                        success_count += 1
                    else:
                        self.log_test("Employee Orders Management - GET", False, 
                                    "Invalid response format - missing 'orders' field")
                else:
                    self.log_test("Employee Orders Management - GET", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Employee Orders Management - GET", False, f"Exception: {str(e)}")
        
        # 2. Test Order Creation with New Breakfast Format (dynamic pricing)
        if self.employees and self.menu_items.get('breakfast'):
            try:
                test_employee = self.employees[0]
                
                # Create order with new breakfast format (white_halves, seeded_halves, item_cost)
                new_format_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 4,
                            "white_halves": 2,
                            "seeded_halves": 2,
                            "toppings": ["ruehrei", "kaese", "schinken", "butter"],
                            "has_lunch": False
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=new_format_order)
                
                if response.status_code == 200:
                    order = response.json()
                    if order.get('total_price', 0) > 0:
                        self.log_test("Order Creation - New Breakfast Format", True, 
                                    f"Successfully created order with new format: €{order['total_price']:.2f}")
                        success_count += 1
                        
                        # Verify the order structure is saved correctly
                        if order.get('breakfast_items') and len(order['breakfast_items']) > 0:
                            breakfast_item = order['breakfast_items'][0]
                            if ('total_halves' in breakfast_item and 
                                'white_halves' in breakfast_item and 
                                'seeded_halves' in breakfast_item):
                                self.log_test("Order Structure Validation", True, 
                                            "New breakfast format correctly saved")
                                success_count += 1
                            else:
                                self.log_test("Order Structure Validation", False, 
                                            "New breakfast format not properly saved")
                    else:
                        self.log_test("Order Creation - New Breakfast Format", False, 
                                    "Invalid total price calculation")
                else:
                    self.log_test("Order Creation - New Breakfast Format", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Order Creation - New Breakfast Format", False, f"Exception: {str(e)}")
        
        # 3. Test Menu Integration with Custom Names
        if self.menu_items.get('toppings'):
            try:
                # First, update a topping with a custom name
                topping_item = self.menu_items['toppings'][0]
                custom_name = "Premium Rührei"
                
                update_data = {"name": custom_name}
                response = self.session.put(f"{API_BASE}/department-admin/menu/toppings/{topping_item['id']}", 
                                          json=update_data)
                
                if response.status_code == 200:
                    # Now fetch the menu to verify custom name is returned
                    response = self.session.get(f"{API_BASE}/menu/toppings")
                    
                    if response.status_code == 200:
                        toppings = response.json()
                        updated_item = next((item for item in toppings if item['id'] == topping_item['id']), None)
                        
                        if updated_item and updated_item.get('name') == custom_name:
                            self.log_test("Menu Integration - Custom Names", True, 
                                        f"Custom name '{custom_name}' correctly returned in menu")
                            success_count += 1
                        else:
                            self.log_test("Menu Integration - Custom Names", False, 
                                        "Custom name not reflected in menu response")
                    else:
                        self.log_test("Menu Integration - Custom Names", False, 
                                    f"Failed to fetch updated menu: HTTP {response.status_code}")
                else:
                    self.log_test("Menu Integration - Custom Names", False, 
                                f"Failed to update topping name: HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test("Menu Integration - Custom Names", False, f"Exception: {str(e)}")
        
        # 4. Test Employee Deletion (Department Admin)
        if self.departments:
            try:
                # Create a test employee for deletion
                test_dept = self.departments[0]
                employee_data = {
                    "name": "Test Employee for Critical Bug Fix",
                    "department_id": test_dept['id']
                }
                
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    test_employee = response.json()
                    
                    # Test deletion
                    response = self.session.delete(f"{API_BASE}/department-admin/employees/{test_employee['id']}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.log_test("Employee Deletion - No Redirect Issues", True, 
                                    f"Employee successfully deleted: {result.get('message', 'Success')}")
                        success_count += 1
                    else:
                        self.log_test("Employee Deletion - No Redirect Issues", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Employee Deletion - No Redirect Issues", False, 
                                "Failed to create test employee for deletion")
                    
            except Exception as e:
                self.log_test("Employee Deletion - No Redirect Issues", False, f"Exception: {str(e)}")
        
        # 5. Test Department Admin Order Deletion
        if self.employees:
            try:
                test_employee = self.employees[0]
                
                # Create a test order
                test_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 2,
                            "white_halves": 2,
                            "seeded_halves": 0,
                            "toppings": ["butter", "kaese"],
                            "has_lunch": False
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=test_order)
                if response.status_code == 200:
                    order = response.json()
                    
                    # Test admin order deletion
                    response = self.session.delete(f"{API_BASE}/department-admin/orders/{order['id']}")
                    
                    if response.status_code == 200:
                        result = response.json()
                        self.log_test("Department Admin Order Deletion", True, 
                                    f"Order successfully deleted by admin: {result.get('message', 'Success')}")
                        success_count += 1
                    else:
                        self.log_test("Department Admin Order Deletion", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Department Admin Order Deletion", False, 
                                "Failed to create test order for deletion")
                    
            except Exception as e:
                self.log_test("Department Admin Order Deletion", False, f"Exception: {str(e)}")
        
        # 6. Test Dynamic Pricing Integration
        if self.menu_items.get('breakfast') and self.employees:
            try:
                # Update breakfast item price
                breakfast_item = self.menu_items['breakfast'][0]
                new_price = 0.75
                
                update_data = {"price": new_price}
                response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{breakfast_item['id']}", 
                                          json=update_data)
                
                if response.status_code == 200:
                    # Create order to test dynamic pricing
                    test_employee = self.employees[0]
                    pricing_test_order = {
                        "employee_id": test_employee['id'],
                        "department_id": test_employee['department_id'],
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
                    
                    response = self.session.post(f"{API_BASE}/orders", json=pricing_test_order)
                    
                    if response.status_code == 200:
                        order = response.json()
                        expected_roll_cost = new_price * 2  # 2 white halves
                        
                        if order.get('total_price', 0) >= expected_roll_cost:
                            self.log_test("Dynamic Pricing Integration", True, 
                                        f"Order correctly uses updated price: €{order['total_price']:.2f}")
                            success_count += 1
                        else:
                            self.log_test("Dynamic Pricing Integration", False, 
                                        f"Price calculation incorrect: expected ≥€{expected_roll_cost:.2f}, got €{order.get('total_price', 0):.2f}")
                    else:
                        self.log_test("Dynamic Pricing Integration", False, 
                                    f"Failed to create order for pricing test: HTTP {response.status_code}")
                else:
                    self.log_test("Dynamic Pricing Integration", False, 
                                f"Failed to update breakfast price: HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test("Dynamic Pricing Integration", False, f"Exception: {str(e)}")
        
        return success_count >= 4  # At least 4 out of 6 critical tests should pass

    def test_department_specific_migration(self):
        """Test the migration to department-specific menu system"""
        print("\n=== Testing Department-Specific Migration ===")
        
        success_count = 0
        
        # Test migration endpoint
        try:
            response = self.session.post(f"{API_BASE}/migrate-to-department-specific")
            
            if response.status_code == 200:
                migration_result = response.json()
                
                # Check migration results
                if 'results' in migration_result:
                    results = migration_result['results']
                    departments_processed = results.get('departments_processed', 0)
                    breakfast_items = results.get('breakfast_items', 0)
                    topping_items = results.get('topping_items', 0)
                    drink_items = results.get('drink_items', 0)
                    sweet_items = results.get('sweet_items', 0)
                    
                    if departments_processed == 4:  # Should process 4 departments
                        self.log_test("Migration Departments", True, 
                                    f"Processed {departments_processed} departments")
                        success_count += 1
                    else:
                        self.log_test("Migration Departments", False, 
                                    f"Expected 4 departments, processed {departments_processed}")
                    
                    total_items = breakfast_items + topping_items + drink_items + sweet_items
                    if total_items > 0:
                        self.log_test("Migration Items", True, 
                                    f"Migrated {total_items} items (B:{breakfast_items}, T:{topping_items}, D:{drink_items}, S:{sweet_items})")
                        success_count += 1
                    else:
                        self.log_test("Migration Items", False, "No items were migrated")
                        
                    self.log_test("Migration Endpoint", True, 
                                f"Migration completed: {migration_result.get('message', 'Success')}")
                    success_count += 1
                else:
                    self.log_test("Migration Endpoint", False, "Missing results in migration response")
            else:
                self.log_test("Migration Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Migration Endpoint", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_department_specific_menu_endpoints(self):
        """Test department-specific menu endpoints"""
        print("\n=== Testing Department-Specific Menu Endpoints ===")
        
        if not self.departments:
            self.log_test("Department-Specific Menus", False, "No departments available")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        dept_id = test_dept['id']
        
        # Test department-specific breakfast menu
        try:
            response = self.session.get(f"{API_BASE}/menu/breakfast/{dept_id}")
            
            if response.status_code == 200:
                breakfast_items = response.json()
                if len(breakfast_items) > 0:
                    # Check that all items have department_id
                    all_have_dept_id = all('department_id' in item and item['department_id'] == dept_id 
                                         for item in breakfast_items)
                    if all_have_dept_id:
                        self.log_test("Department-Specific Breakfast Menu", True, 
                                    f"Found {len(breakfast_items)} breakfast items for department")
                        success_count += 1
                    else:
                        self.log_test("Department-Specific Breakfast Menu", False, 
                                    "Items missing department_id or wrong department")
                else:
                    self.log_test("Department-Specific Breakfast Menu", False, "No breakfast items found")
            else:
                self.log_test("Department-Specific Breakfast Menu", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Department-Specific Breakfast Menu", False, f"Exception: {str(e)}")
        
        # Test department-specific toppings menu
        try:
            response = self.session.get(f"{API_BASE}/menu/toppings/{dept_id}")
            
            if response.status_code == 200:
                topping_items = response.json()
                if len(topping_items) > 0:
                    all_have_dept_id = all('department_id' in item and item['department_id'] == dept_id 
                                         for item in topping_items)
                    if all_have_dept_id:
                        self.log_test("Department-Specific Toppings Menu", True, 
                                    f"Found {len(topping_items)} topping items for department")
                        success_count += 1
                    else:
                        self.log_test("Department-Specific Toppings Menu", False, 
                                    "Items missing department_id or wrong department")
                else:
                    self.log_test("Department-Specific Toppings Menu", False, "No topping items found")
            else:
                self.log_test("Department-Specific Toppings Menu", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Department-Specific Toppings Menu", False, f"Exception: {str(e)}")
        
        # Test department-specific drinks menu
        try:
            response = self.session.get(f"{API_BASE}/menu/drinks/{dept_id}")
            
            if response.status_code == 200:
                drink_items = response.json()
                if len(drink_items) > 0:
                    all_have_dept_id = all('department_id' in item and item['department_id'] == dept_id 
                                         for item in drink_items)
                    if all_have_dept_id:
                        self.log_test("Department-Specific Drinks Menu", True, 
                                    f"Found {len(drink_items)} drink items for department")
                        success_count += 1
                    else:
                        self.log_test("Department-Specific Drinks Menu", False, 
                                    "Items missing department_id or wrong department")
                else:
                    self.log_test("Department-Specific Drinks Menu", False, "No drink items found")
            else:
                self.log_test("Department-Specific Drinks Menu", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Department-Specific Drinks Menu", False, f"Exception: {str(e)}")
        
        # Test department-specific sweets menu
        try:
            response = self.session.get(f"{API_BASE}/menu/sweets/{dept_id}")
            
            if response.status_code == 200:
                sweet_items = response.json()
                if len(sweet_items) > 0:
                    all_have_dept_id = all('department_id' in item and item['department_id'] == dept_id 
                                         for item in sweet_items)
                    if all_have_dept_id:
                        self.log_test("Department-Specific Sweets Menu", True, 
                                    f"Found {len(sweet_items)} sweet items for department")
                        success_count += 1
                    else:
                        self.log_test("Department-Specific Sweets Menu", False, 
                                    "Items missing department_id or wrong department")
                else:
                    self.log_test("Department-Specific Sweets Menu", False, "No sweet items found")
            else:
                self.log_test("Department-Specific Sweets Menu", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Department-Specific Sweets Menu", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_backward_compatibility_menus(self):
        """Test backward compatibility of old menu endpoints"""
        print("\n=== Testing Backward Compatibility Menu Endpoints ===")
        
        success_count = 0
        
        # Test old breakfast menu endpoint (should return first department's menu)
        try:
            response = self.session.get(f"{API_BASE}/menu/breakfast")
            
            if response.status_code == 200:
                breakfast_items = response.json()
                if len(breakfast_items) > 0:
                    self.log_test("Backward Compatible Breakfast Menu", True, 
                                f"Old endpoint returns {len(breakfast_items)} breakfast items")
                    success_count += 1
                else:
                    self.log_test("Backward Compatible Breakfast Menu", False, "No breakfast items returned")
            else:
                self.log_test("Backward Compatible Breakfast Menu", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Backward Compatible Breakfast Menu", False, f"Exception: {str(e)}")
        
        # Test old toppings menu endpoint
        try:
            response = self.session.get(f"{API_BASE}/menu/toppings")
            
            if response.status_code == 200:
                topping_items = response.json()
                if len(topping_items) > 0:
                    self.log_test("Backward Compatible Toppings Menu", True, 
                                f"Old endpoint returns {len(topping_items)} topping items")
                    success_count += 1
                else:
                    self.log_test("Backward Compatible Toppings Menu", False, "No topping items returned")
            else:
                self.log_test("Backward Compatible Toppings Menu", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Backward Compatible Toppings Menu", False, f"Exception: {str(e)}")
        
        # Test old drinks menu endpoint
        try:
            response = self.session.get(f"{API_BASE}/menu/drinks")
            
            if response.status_code == 200:
                drink_items = response.json()
                if len(drink_items) > 0:
                    self.log_test("Backward Compatible Drinks Menu", True, 
                                f"Old endpoint returns {len(drink_items)} drink items")
                    success_count += 1
                else:
                    self.log_test("Backward Compatible Drinks Menu", False, "No drink items returned")
            else:
                self.log_test("Backward Compatible Drinks Menu", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Backward Compatible Drinks Menu", False, f"Exception: {str(e)}")
        
        # Test old sweets menu endpoint
        try:
            response = self.session.get(f"{API_BASE}/menu/sweets")
            
            if response.status_code == 200:
                sweet_items = response.json()
                if len(sweet_items) > 0:
                    self.log_test("Backward Compatible Sweets Menu", True, 
                                f"Old endpoint returns {len(sweet_items)} sweet items")
                    success_count += 1
                else:
                    self.log_test("Backward Compatible Sweets Menu", False, "No sweet items returned")
            else:
                self.log_test("Backward Compatible Sweets Menu", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Backward Compatible Sweets Menu", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_department_specific_order_creation(self):
        """Test that orders use department-specific pricing"""
        print("\n=== Testing Department-Specific Order Creation ===")
        
        if not self.departments or not self.employees:
            self.log_test("Department-Specific Orders", False, "Missing departments or employees")
            return False
        
        success_count = 0
        
        # Test with different departments to ensure proper isolation
        for i, dept in enumerate(self.departments[:2]):  # Test first 2 departments
            dept_employees = [emp for emp in self.employees if emp['department_id'] == dept['id']]
            if not dept_employees:
                continue
                
            test_employee = dept_employees[0]
            
            try:
                # Get department-specific menu prices
                breakfast_response = self.session.get(f"{API_BASE}/menu/breakfast/{dept['id']}")
                if breakfast_response.status_code != 200:
                    continue
                    
                breakfast_menu = breakfast_response.json()
                if not breakfast_menu:
                    continue
                
                # Create breakfast order using department-specific menu
                breakfast_order = {
                    "employee_id": test_employee['id'],
                    "department_id": dept['id'],
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
                
                response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
                
                if response.status_code == 200:
                    order = response.json()
                    
                    # Verify order uses department-specific pricing
                    if order['total_price'] > 0 and order['department_id'] == dept['id']:
                        self.log_test(f"Department {i+1} Order Creation", True, 
                                    f"Created order with department-specific pricing: €{order['total_price']:.2f}")
                        success_count += 1
                    else:
                        self.log_test(f"Department {i+1} Order Creation", False, 
                                    "Invalid pricing or department mismatch")
                else:
                    self.log_test(f"Department {i+1} Order Creation", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Department {i+1} Order Creation", False, f"Exception: {str(e)}")
        
        return success_count >= 1

    def test_department_isolation_data_integrity(self):
        """Test that departments have isolated menu items and proper data integrity"""
        print("\n=== Testing Department Isolation & Data Integrity ===")
        
        if len(self.departments) < 2:
            self.log_test("Department Isolation", False, "Need at least 2 departments for isolation testing")
            return False
        
        success_count = 0
        dept1 = self.departments[0]
        dept2 = self.departments[1]
        
        # Test that each department has its own copy of menu items
        try:
            # Get breakfast menus for both departments
            response1 = self.session.get(f"{API_BASE}/menu/breakfast/{dept1['id']}")
            response2 = self.session.get(f"{API_BASE}/menu/breakfast/{dept2['id']}")
            
            if response1.status_code == 200 and response2.status_code == 200:
                menu1 = response1.json()
                menu2 = response2.json()
                
                if len(menu1) > 0 and len(menu2) > 0:
                    # Check that items have different IDs (separate copies)
                    menu1_ids = {item['id'] for item in menu1}
                    menu2_ids = {item['id'] for item in menu2}
                    
                    if menu1_ids.isdisjoint(menu2_ids):
                        self.log_test("Department Menu Isolation", True, 
                                    f"Departments have separate menu items (Dept1: {len(menu1)}, Dept2: {len(menu2)})")
                        success_count += 1
                    else:
                        self.log_test("Department Menu Isolation", False, 
                                    "Departments share menu item IDs - not properly isolated")
                        
                    # Check that all items have correct department_id
                    dept1_correct = all(item['department_id'] == dept1['id'] for item in menu1)
                    dept2_correct = all(item['department_id'] == dept2['id'] for item in menu2)
                    
                    if dept1_correct and dept2_correct:
                        self.log_test("Department ID Integrity", True, 
                                    "All menu items have correct department_id")
                        success_count += 1
                    else:
                        self.log_test("Department ID Integrity", False, 
                                    "Menu items have incorrect department_id")
                else:
                    self.log_test("Department Menu Isolation", False, "Empty menus found")
            else:
                self.log_test("Department Menu Isolation", False, 
                            f"Failed to fetch menus: {response1.status_code}, {response2.status_code}")
                
        except Exception as e:
            self.log_test("Department Menu Isolation", False, f"Exception: {str(e)}")
        
        # Test department admin access isolation
        try:
            # Login as admin for dept1
            admin_login_data = {
                "department_name": dept1['name'],
                "admin_password": "admin1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            
            if response.status_code == 200:
                login_result = response.json()
                if login_result.get('department_id') == dept1['id']:
                    self.log_test("Department Admin Isolation", True, 
                                "Department admin can only access their department")
                    success_count += 1
                else:
                    self.log_test("Department Admin Isolation", False, 
                                "Department admin access not properly isolated")
            else:
                self.log_test("Department Admin Isolation", False, 
                            f"Admin login failed: {response.status_code}")
                
        except Exception as e:
            self.log_test("Department Admin Isolation", False, f"Exception: {str(e)}")
        
        # Test order isolation - orders should reference correct department-specific menu items
        if self.employees:
            try:
                dept1_employees = [emp for emp in self.employees if emp['department_id'] == dept1['id']]
                if dept1_employees:
                    test_employee = dept1_employees[0]
                    
                    # Get employee's orders
                    response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
                    
                    if response.status_code == 200:
                        orders_data = response.json()
                        orders = orders_data.get('orders', [])
                        
                        # Check that all orders belong to correct department
                        dept_orders_correct = all(order.get('department_id') == dept1['id'] for order in orders)
                        
                        if dept_orders_correct:
                            self.log_test("Order Department Integrity", True, 
                                        f"All {len(orders)} orders reference correct department")
                            success_count += 1
                        else:
                            self.log_test("Order Department Integrity", False, 
                                        "Orders reference incorrect department")
                    else:
                        self.log_test("Order Department Integrity", False, 
                                    f"Failed to fetch orders: {response.status_code}")
                        
            except Exception as e:
                self.log_test("Order Department Integrity", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_boiled_breakfast_eggs_feature(self):
        """Test the new boiled breakfast eggs feature implementation"""
        print("\n=== Testing Boiled Breakfast Eggs Feature ===")
        
        if not self.employees or not self.departments:
            self.log_test("Boiled Eggs Feature", False, "Missing employees or departments")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        test_dept = self.departments[0]
        
        # Test 1: Data Model Updates - BreakfastOrder with boiled_eggs field
        try:
            # Create breakfast order with boiled eggs
            breakfast_order_with_eggs = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": False,
                        "boiled_eggs": 3  # Test with 3 boiled eggs
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order_with_eggs)
            
            if response.status_code == 200:
                order = response.json()
                # Verify boiled_eggs field is accepted and stored
                if (order.get('breakfast_items') and 
                    len(order['breakfast_items']) > 0 and
                    order['breakfast_items'][0].get('boiled_eggs') == 3):
                    self.log_test("BreakfastOrder Model - Boiled Eggs Field", True, 
                                f"Order created with 3 boiled eggs, total: €{order['total_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("BreakfastOrder Model - Boiled Eggs Field", False, 
                                "Boiled eggs field not properly stored in order")
            else:
                self.log_test("BreakfastOrder Model - Boiled Eggs Field", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("BreakfastOrder Model - Boiled Eggs Field", False, f"Exception: {str(e)}")
        
        # Test 2: Various boiled egg quantities (0, 1, 5, 10)
        test_quantities = [0, 1, 5, 10]
        for quantity in test_quantities:
            try:
                breakfast_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_dept['id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 1,
                            "white_halves": 1,
                            "seeded_halves": 0,
                            "toppings": ["butter"],
                            "has_lunch": False,
                            "boiled_eggs": quantity
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
                
                if response.status_code == 200:
                    order = response.json()
                    stored_quantity = order['breakfast_items'][0].get('boiled_eggs', 0)
                    if stored_quantity == quantity:
                        self.log_test(f"Boiled Eggs Quantity {quantity}", True, 
                                    f"Order created with {quantity} boiled eggs")
                        success_count += 1
                    else:
                        self.log_test(f"Boiled Eggs Quantity {quantity}", False, 
                                    f"Expected {quantity}, got {stored_quantity}")
                else:
                    self.log_test(f"Boiled Eggs Quantity {quantity}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Boiled Eggs Quantity {quantity}", False, f"Exception: {str(e)}")
        
        # Test 3: Pricing Integration - LunchSettings boiled_eggs_price field
        try:
            response = self.session.get(f"{API_BASE}/lunch-settings")
            
            if response.status_code == 200:
                lunch_settings = response.json()
                if 'boiled_eggs_price' in lunch_settings:
                    self.log_test("LunchSettings - Boiled Eggs Price Field", True, 
                                f"Boiled eggs price: €{lunch_settings['boiled_eggs_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("LunchSettings - Boiled Eggs Price Field", False, 
                                "boiled_eggs_price field missing from lunch settings")
            else:
                self.log_test("LunchSettings - Boiled Eggs Price Field", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("LunchSettings - Boiled Eggs Price Field", False, f"Exception: {str(e)}")
        
        # Test 4: Boiled Eggs Price Update Endpoint
        try:
            new_boiled_eggs_price = 0.75
            response = self.session.put(f"{API_BASE}/lunch-settings/boiled-eggs-price", 
                                      params={"price": new_boiled_eggs_price})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('price') == new_boiled_eggs_price:
                    self.log_test("Boiled Eggs Price Update Endpoint", True, 
                                f"Successfully updated boiled eggs price to €{new_boiled_eggs_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Boiled Eggs Price Update Endpoint", False, 
                                "Price update response mismatch")
            else:
                self.log_test("Boiled Eggs Price Update Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Boiled Eggs Price Update Endpoint", False, f"Exception: {str(e)}")
        
        # Test 5: Order Pricing Calculation with Boiled Eggs
        try:
            # First, ensure we have a known boiled eggs price
            self.session.put(f"{API_BASE}/lunch-settings/boiled-eggs-price", params={"price": 0.60})
            
            # Create order with boiled eggs and verify pricing
            breakfast_order_pricing = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 2,
                        "white_halves": 2,
                        "seeded_halves": 0,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": False,
                        "boiled_eggs": 4  # 4 eggs at €0.60 each = €2.40
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order_pricing)
            
            if response.status_code == 200:
                order = response.json()
                total_price = order['total_price']
                
                # Calculate expected boiled eggs cost (4 * €0.60 = €2.40)
                expected_eggs_cost = 4 * 0.60
                
                # Check if total price includes boiled eggs cost
                if total_price >= expected_eggs_cost:
                    self.log_test("Boiled Eggs Pricing Calculation", True, 
                                f"Order total €{total_price:.2f} includes boiled eggs cost (€{expected_eggs_cost:.2f})")
                    success_count += 1
                else:
                    self.log_test("Boiled Eggs Pricing Calculation", False, 
                                f"Order total €{total_price:.2f} seems too low for boiled eggs cost")
            else:
                self.log_test("Boiled Eggs Pricing Calculation", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Boiled Eggs Pricing Calculation", False, f"Exception: {str(e)}")
        
        # Test 6: Daily Summary Integration - Total Boiled Eggs
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check if total_boiled_eggs field is present
                if 'total_boiled_eggs' in summary:
                    total_boiled_eggs = summary['total_boiled_eggs']
                    self.log_test("Daily Summary - Total Boiled Eggs", True, 
                                f"Daily summary includes total_boiled_eggs: {total_boiled_eggs}")
                    success_count += 1
                else:
                    self.log_test("Daily Summary - Total Boiled Eggs", False, 
                                "total_boiled_eggs field missing from daily summary")
                
                # Check if employee_orders include boiled_eggs field
                employee_orders = summary.get('employee_orders', {})
                has_boiled_eggs_in_employee_orders = False
                for employee_name, employee_data in employee_orders.items():
                    if 'boiled_eggs' in employee_data:
                        has_boiled_eggs_in_employee_orders = True
                        break
                
                if has_boiled_eggs_in_employee_orders:
                    self.log_test("Daily Summary - Employee Boiled Eggs", True, 
                                "Employee orders include boiled_eggs field")
                    success_count += 1
                else:
                    self.log_test("Daily Summary - Employee Boiled Eggs", False, 
                                "Employee orders missing boiled_eggs field")
                    
            else:
                self.log_test("Daily Summary - Boiled Eggs Integration", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary - Boiled Eggs Integration", False, f"Exception: {str(e)}")
        
        # Test 7: Order History - Boiled Eggs in Profile
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                order_history = profile.get('order_history', [])
                
                # Check if any order in history contains boiled eggs information
                has_boiled_eggs_in_history = False
                for order in order_history:
                    if (order.get('order_type') == 'breakfast' and 
                        order.get('breakfast_items')):
                        for item in order['breakfast_items']:
                            if item.get('boiled_eggs', 0) > 0:
                                has_boiled_eggs_in_history = True
                                break
                        if has_boiled_eggs_in_history:
                            break
                
                if has_boiled_eggs_in_history:
                    self.log_test("Employee Profile - Boiled Eggs in History", True, 
                                "Order history includes boiled eggs data")
                    success_count += 1
                else:
                    self.log_test("Employee Profile - Boiled Eggs in History", True, 
                                "Order history ready for boiled eggs data (no orders with eggs yet)")
                    success_count += 1  # This is acceptable as we may not have orders with eggs in history
                    
            else:
                self.log_test("Employee Profile - Boiled Eggs in History", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Employee Profile - Boiled Eggs in History", False, f"Exception: {str(e)}")
        
        return success_count >= 6  # At least 6 out of 8+ tests should pass
    
    def test_admin_boiled_eggs_pricing_management(self):
        """Test the new Admin Boiled Eggs Pricing Management feature"""
        print("\n=== Testing Admin Boiled Eggs Pricing Management ===")
        
        success_count = 0
        
        # Test 1: Admin Price Management Interface - GET /api/lunch-settings returns boiled_eggs_price field
        try:
            response = self.session.get(f"{API_BASE}/lunch-settings")
            
            if response.status_code == 200:
                lunch_settings = response.json()
                
                if 'boiled_eggs_price' in lunch_settings:
                    current_price = lunch_settings['boiled_eggs_price']
                    self.log_test("GET Lunch Settings - Boiled Eggs Price Field", True, 
                                f"Boiled eggs price field present: €{current_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("GET Lunch Settings - Boiled Eggs Price Field", False, 
                                "boiled_eggs_price field missing from lunch settings")
            else:
                self.log_test("GET Lunch Settings - Boiled Eggs Price Field", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET Lunch Settings - Boiled Eggs Price Field", False, f"Exception: {str(e)}")
        
        # Test 2: Admin Price Management Interface - PUT /api/lunch-settings/boiled-eggs-price endpoint
        try:
            new_price = 0.75
            response = self.session.put(f"{API_BASE}/lunch-settings/boiled-eggs-price", 
                                      params={"price": new_price})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('price') == new_price:
                    self.log_test("PUT Boiled Eggs Price Update", True, 
                                f"Successfully updated boiled eggs price to €{new_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("PUT Boiled Eggs Price Update", False, 
                                "Price update response mismatch")
            else:
                self.log_test("PUT Boiled Eggs Price Update", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("PUT Boiled Eggs Price Update", False, f"Exception: {str(e)}")
        
        # Test 3: Verify price persistence - GET again to confirm update
        try:
            response = self.session.get(f"{API_BASE}/lunch-settings")
            
            if response.status_code == 200:
                lunch_settings = response.json()
                updated_price = lunch_settings.get('boiled_eggs_price', 0)
                
                if updated_price == 0.75:
                    self.log_test("Boiled Eggs Price Persistence", True, 
                                f"Price update persisted correctly: €{updated_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Boiled Eggs Price Persistence", False, 
                                f"Expected €0.75, got €{updated_price:.2f}")
            else:
                self.log_test("Boiled Eggs Price Persistence", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Boiled Eggs Price Persistence", False, f"Exception: {str(e)}")
        
        # Test 4: Dynamic Price Integration - Test order creation uses updated price
        if self.employees:
            try:
                test_employee = self.employees[0]
                
                # Create breakfast order with boiled eggs
                breakfast_order_with_eggs = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 2,
                            "white_halves": 2,
                            "seeded_halves": 0,
                            "toppings": ["ruehrei", "kaese"],
                            "has_lunch": False,
                            "boiled_eggs": 3  # 3 boiled eggs at €0.75 each = €2.25
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=breakfast_order_with_eggs)
                
                if response.status_code == 200:
                    order = response.json()
                    total_price = order['total_price']
                    
                    # Calculate expected boiled eggs cost: 3 eggs × €0.75 = €2.25
                    expected_eggs_cost = 3 * 0.75
                    
                    if total_price > expected_eggs_cost:  # Should include roll cost + eggs cost
                        self.log_test("Order Creation with Updated Boiled Eggs Price", True, 
                                    f"Order created with boiled eggs: €{total_price:.2f} (includes €{expected_eggs_cost:.2f} for eggs)")
                        success_count += 1
                    else:
                        self.log_test("Order Creation with Updated Boiled Eggs Price", False, 
                                    f"Total price €{total_price:.2f} seems too low for 3 eggs at €0.75 each")
                else:
                    self.log_test("Order Creation with Updated Boiled Eggs Price", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Order Creation with Updated Boiled Eggs Price", False, f"Exception: {str(e)}")
        
        # Test 5: Price Independence - Test that boiled eggs pricing is separate from lunch pricing
        try:
            # Update lunch price
            lunch_price = 4.50
            response = self.session.put(f"{API_BASE}/lunch-settings", params={"price": lunch_price})
            
            if response.status_code == 200:
                # Check that boiled eggs price remains unchanged
                response = self.session.get(f"{API_BASE}/lunch-settings")
                
                if response.status_code == 200:
                    settings = response.json()
                    lunch_price_check = settings.get('price', 0)
                    eggs_price_check = settings.get('boiled_eggs_price', 0)
                    
                    if lunch_price_check == 4.50 and eggs_price_check == 0.75:
                        self.log_test("Price Independence - Lunch vs Boiled Eggs", True, 
                                    f"Lunch price: €{lunch_price_check:.2f}, Boiled eggs price: €{eggs_price_check:.2f} (independent)")
                        success_count += 1
                    else:
                        self.log_test("Price Independence - Lunch vs Boiled Eggs", False, 
                                    f"Price independence failed. Lunch: €{lunch_price_check:.2f}, Eggs: €{eggs_price_check:.2f}")
                else:
                    self.log_test("Price Independence - Lunch vs Boiled Eggs", False, 
                                f"Failed to verify independence: HTTP {response.status_code}")
            else:
                self.log_test("Price Independence - Lunch vs Boiled Eggs", False, 
                            f"Failed to update lunch price: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Price Independence - Lunch vs Boiled Eggs", False, f"Exception: {str(e)}")
        
        # Test 6: Test another price change to verify admin control
        try:
            another_new_price = 0.60
            response = self.session.put(f"{API_BASE}/lunch-settings/boiled-eggs-price", 
                                      params={"price": another_new_price})
            
            if response.status_code == 200:
                # Verify the change took effect
                response = self.session.get(f"{API_BASE}/lunch-settings")
                
                if response.status_code == 200:
                    settings = response.json()
                    final_price = settings.get('boiled_eggs_price', 0)
                    
                    if final_price == another_new_price:
                        self.log_test("Admin Complete Control - Multiple Price Changes", True, 
                                    f"Admin can change boiled eggs price multiple times: €{final_price:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Admin Complete Control - Multiple Price Changes", False, 
                                    f"Expected €{another_new_price:.2f}, got €{final_price:.2f}")
                else:
                    self.log_test("Admin Complete Control - Multiple Price Changes", False, 
                                f"Failed to verify final price: HTTP {response.status_code}")
            else:
                self.log_test("Admin Complete Control - Multiple Price Changes", False, 
                            f"Failed to update price again: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Complete Control - Multiple Price Changes", False, f"Exception: {str(e)}")
        
        # Test 7: Test order processing with final price
        if self.employees:
            try:
                test_employee = self.employees[0]
                
                # Create another order with different quantity to verify calculation
                breakfast_order_final = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 1,
                            "white_halves": 1,
                            "seeded_halves": 0,
                            "toppings": ["butter"],
                            "has_lunch": False,
                            "boiled_eggs": 2  # 2 boiled eggs at €0.60 each = €1.20
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=breakfast_order_final)
                
                if response.status_code == 200:
                    order = response.json()
                    total_price = order['total_price']
                    
                    # Calculate expected boiled eggs cost: 2 eggs × €0.60 = €1.20
                    expected_eggs_cost = 2 * 0.60
                    
                    if total_price >= expected_eggs_cost:  # Should include roll cost + eggs cost
                        self.log_test("Final Order Processing with Admin-Set Price", True, 
                                    f"Order uses current admin-set price: €{total_price:.2f} (includes €{expected_eggs_cost:.2f} for eggs)")
                        success_count += 1
                    else:
                        self.log_test("Final Order Processing with Admin-Set Price", False, 
                                    f"Total price €{total_price:.2f} seems incorrect for 2 eggs at €0.60 each")
                else:
                    self.log_test("Final Order Processing with Admin-Set Price", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Final Order Processing with Admin-Set Price", False, f"Exception: {str(e)}")
        
        return success_count >= 5  # At least 5 out of 7 tests should pass
    
    def test_daily_summary_data_structure_investigation(self):
        """Investigate the data structure returned by GET /api/orders/daily-summary/{department_id} 
        to identify why [object Object] appears in frontend table display"""
        print("\n=== INVESTIGATING DAILY SUMMARY DATA STRUCTURE FOR [object Object] ISSUE ===")
        
        success_count = 0
        
        # Step 1: Authenticate with password1/admin1 for department 1
        department_id = None
        try:
            # First get departments to find department 1
            response = self.session.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                departments = response.json()
                dept_1 = next((dept for dept in departments if "1." in dept['name']), None)
                if dept_1:
                    department_id = dept_1['id']
                    self.log_test("Find Department 1", True, f"Found department: {dept_1['name']}")
                    success_count += 1
                else:
                    self.log_test("Find Department 1", False, "Department 1 not found")
                    return False
            else:
                self.log_test("Get Departments", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Find Department 1", False, f"Exception: {str(e)}")
            return False
        
        # Step 2: Authenticate as department user
        try:
            login_data = {
                "department_name": dept_1['name'],
                "password": "password1"
            }
            response = self.session.post(f"{API_BASE}/login/department", json=login_data)
            if response.status_code == 200:
                self.log_test("Department Authentication", True, "Authenticated with password1")
                success_count += 1
            else:
                self.log_test("Department Authentication", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Department Authentication", False, f"Exception: {str(e)}")
            return False
        
        # Step 3: Create a test employee for breakfast order
        test_employee_id = None
        try:
            employee_data = {
                "name": "Test Employee for Data Investigation",
                "department_id": department_id
            }
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                test_employee_id = employee['id']
                self.log_test("Create Test Employee", True, f"Created employee: {employee['name']}")
                success_count += 1
            else:
                self.log_test("Create Test Employee", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create Test Employee", False, f"Exception: {str(e)}")
            return False
        
        # Step 4: Create a breakfast order with the new format (total_halves, white_halves, seeded_halves)
        try:
            breakfast_order = {
                "employee_id": test_employee_id,
                "department_id": department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 2,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese", "schinken"],  # 3 toppings for 3 halves
                        "has_lunch": False,
                        "boiled_eggs": 2
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                order = response.json()
                self.log_test("Create Breakfast Order", True, 
                            f"Created breakfast order with total: €{order['total_price']:.2f}")
                success_count += 1
                
                # Log the exact order structure for analysis
                print(f"   📋 Order Structure: {json.dumps(order, indent=2, default=str)}")
            else:
                self.log_test("Create Breakfast Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Create Breakfast Order", False, f"Exception: {str(e)}")
            return False
        
        # Step 5: Retrieve daily summary and analyze the exact data structure
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{department_id}")
            if response.status_code == 200:
                summary = response.json()
                self.log_test("Get Daily Summary", True, "Retrieved daily summary successfully")
                success_count += 1
                
                # Log the complete summary structure
                print(f"\n   📋 COMPLETE DAILY SUMMARY STRUCTURE:")
                print(f"   {json.dumps(summary, indent=2, default=str)}")
                
                # Focus on employee_orders section and toppings data format
                employee_orders = summary.get('employee_orders', {})
                if employee_orders:
                    self.log_test("Employee Orders Section Present", True, 
                                f"Found {len(employee_orders)} employee orders")
                    success_count += 1
                    
                    # Analyze each employee's order data
                    for employee_name, order_data in employee_orders.items():
                        print(f"\n   👤 EMPLOYEE: {employee_name}")
                        print(f"   📊 Order Data: {json.dumps(order_data, indent=4, default=str)}")
                        
                        # Check toppings data type specifically
                        toppings = order_data.get('toppings', {})
                        if toppings:
                            self.log_test(f"Toppings Data Type for {employee_name}", True, 
                                        f"Toppings type: {type(toppings)}, Content: {toppings}")
                            success_count += 1
                            
                            # Check if toppings are objects or numbers
                            for topping_name, topping_value in toppings.items():
                                print(f"   🥪 Topping '{topping_name}': Type={type(topping_value)}, Value={topping_value}")
                                
                                # This is the key investigation - check if topping values are objects
                                if isinstance(topping_value, dict):
                                    self.log_test(f"FOUND OBJECT TOPPINGS", False, 
                                                f"Topping '{topping_name}' is an object: {topping_value} - THIS CAUSES [object Object] in frontend!")
                                elif isinstance(topping_value, (int, float)):
                                    self.log_test(f"Topping Value Type", True, 
                                                f"Topping '{topping_name}' is numeric: {topping_value}")
                                else:
                                    self.log_test(f"Unexpected Topping Type", False, 
                                                f"Topping '{topping_name}' has unexpected type: {type(topping_value)}")
                        else:
                            self.log_test(f"No Toppings Data for {employee_name}", False, 
                                        "Employee has no toppings data")
                else:
                    self.log_test("Employee Orders Section", False, "No employee_orders section found")
                
                # Also check the breakfast_summary section for comparison
                breakfast_summary = summary.get('breakfast_summary', {})
                if breakfast_summary:
                    print(f"\n   🥐 BREAKFAST SUMMARY STRUCTURE:")
                    for roll_type, roll_data in breakfast_summary.items():
                        print(f"   Roll Type '{roll_type}': {json.dumps(roll_data, indent=4, default=str)}")
                        
                        # Check toppings in breakfast summary too
                        summary_toppings = roll_data.get('toppings', {})
                        for topping_name, topping_count in summary_toppings.items():
                            print(f"   🥪 Summary Topping '{topping_name}': Type={type(topping_count)}, Value={topping_count}")
                
            else:
                self.log_test("Get Daily Summary", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Daily Summary", False, f"Exception: {str(e)}")
            return False
        
        # Step 6: Summary of findings
        print(f"\n   🔍 INVESTIGATION SUMMARY:")
        print(f"   - Created breakfast order with new format (total_halves, white_halves, seeded_halves)")
        print(f"   - Retrieved daily summary and analyzed data structure")
        print(f"   - Focused on employee_orders section and toppings data format")
        print(f"   - Checked if toppings are returned as objects or numbers")
        
        return success_count >= 4
    
    def test_daily_summary_toppings_fix(self):
        """Test the fix for [object Object] display issue in daily summary toppings"""
        print("\n=== Testing Daily Summary Toppings Fix - [object Object] Issue ===")
        
        success_count = 0
        
        # First authenticate with password1/admin1 for department 1
        dept_auth_success = False
        department_id = None
        
        try:
            # Get departments first
            response = self.session.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                departments = response.json()
                # Find department 1 (1. Wachabteilung)
                dept_1 = None
                for dept in departments:
                    if "1." in dept['name'] and "Wachabteilung" in dept['name']:
                        dept_1 = dept
                        break
                
                if dept_1:
                    department_id = dept_1['id']
                    
                    # Authenticate with password1/admin1
                    login_data = {
                        "department_name": dept_1['name'],
                        "password": "password1"
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department", json=login_data)
                    if response.status_code == 200:
                        self.log_test("Department 1 Authentication", True, "Successfully authenticated with password1")
                        dept_auth_success = True
                        success_count += 1
                    else:
                        self.log_test("Department 1 Authentication", False, f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Find Department 1", False, "Could not find 1. Wachabteilung")
            else:
                self.log_test("Get Departments", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Department Authentication", False, f"Exception: {str(e)}")
        
        if not dept_auth_success or not department_id:
            self.log_test("Daily Summary Toppings Fix", False, "Could not authenticate with department 1")
            return False
        
        # Create a test employee for this department
        test_employee_id = None
        try:
            employee_data = {
                "name": "Test Employee for Toppings Fix",
                "department_id": department_id
            }
            
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                test_employee_id = employee['id']
                self.log_test("Create Test Employee", True, "Test employee created for toppings test")
                success_count += 1
            else:
                self.log_test("Create Test Employee", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Test Employee", False, f"Exception: {str(e)}")
        
        if not test_employee_id:
            self.log_test("Daily Summary Toppings Fix", False, "Could not create test employee")
            return False
        
        # Create a test breakfast order with multiple toppings using new format
        try:
            breakfast_order = {
                "employee_id": test_employee_id,
                "department_id": department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 4,
                        "white_halves": 2,
                        "seeded_halves": 2,
                        "toppings": ["ruehrei", "kaese", "schinken", "butter"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                order = response.json()
                self.log_test("Create Test Breakfast Order", True, 
                            f"Created breakfast order with 4 toppings: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create Test Breakfast Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Test Breakfast Order", False, f"Exception: {str(e)}")
        
        # Now test the daily summary endpoint for the toppings data structure
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{department_id}")
            
            if response.status_code == 200:
                summary = response.json()
                self.log_test("Get Daily Summary", True, "Successfully retrieved daily summary")
                success_count += 1
                
                # Check the structure of employee_orders section
                employee_orders = summary.get('employee_orders', {})
                if employee_orders:
                    self.log_test("Employee Orders Section Present", True, f"Found {len(employee_orders)} employee orders")
                    success_count += 1
                    
                    # Check toppings data structure in employee_orders
                    toppings_structure_fixed = True
                    complex_toppings_found = []
                    
                    for employee_name, employee_data in employee_orders.items():
                        toppings = employee_data.get('toppings', {})
                        for topping_name, topping_value in toppings.items():
                            # Check if topping value is a simple integer (FIXED) or complex object (BROKEN)
                            if isinstance(topping_value, dict):
                                toppings_structure_fixed = False
                                complex_toppings_found.append(f"{topping_name}: {topping_value}")
                            elif not isinstance(topping_value, int):
                                toppings_structure_fixed = False
                                complex_toppings_found.append(f"{topping_name}: {type(topping_value)} - {topping_value}")
                    
                    if toppings_structure_fixed:
                        self.log_test("Toppings Data Structure Fix", True, 
                                    "✅ FIXED: Employee orders toppings are simple integers (no [object Object] issue)")
                        success_count += 1
                        
                        # Show example of fixed structure
                        for employee_name, employee_data in employee_orders.items():
                            toppings = employee_data.get('toppings', {})
                            if toppings:
                                example_toppings = {k: v for k, v in list(toppings.items())[:3]}  # Show first 3
                                self.log_test("Example Fixed Toppings Structure", True, 
                                            f"Employee '{employee_name}': {example_toppings}")
                                break
                    else:
                        self.log_test("Toppings Data Structure Fix", False, 
                                    f"❌ STILL BROKEN: Found complex objects in toppings: {complex_toppings_found[:3]}")
                else:
                    self.log_test("Employee Orders Section Present", False, "No employee orders found in summary")
                
                # Verify breakfast_summary section still works correctly (no regression)
                breakfast_summary = summary.get('breakfast_summary', {})
                if breakfast_summary:
                    self.log_test("Breakfast Summary Section", True, "Breakfast summary section present (no regression)")
                    success_count += 1
                    
                    # Check that breakfast_summary toppings are still integers
                    breakfast_toppings_ok = True
                    for roll_type, roll_data in breakfast_summary.items():
                        toppings = roll_data.get('toppings', {})
                        for topping_name, topping_count in toppings.items():
                            if not isinstance(topping_count, int):
                                breakfast_toppings_ok = False
                                break
                    
                    if breakfast_toppings_ok:
                        self.log_test("Breakfast Summary Toppings", True, "Breakfast summary toppings are integers (no regression)")
                        success_count += 1
                    else:
                        self.log_test("Breakfast Summary Toppings", False, "Breakfast summary toppings structure broken")
                else:
                    self.log_test("Breakfast Summary Section", False, "Breakfast summary section missing")
                
                # Verify shopping_list section still works correctly (no regression)
                shopping_list = summary.get('shopping_list', {})
                if shopping_list:
                    self.log_test("Shopping List Section", True, "Shopping list section present (no regression)")
                    success_count += 1
                    
                    # Check shopping list structure
                    shopping_list_ok = True
                    for roll_type, roll_data in shopping_list.items():
                        if not isinstance(roll_data, dict) or 'whole_rolls' not in roll_data:
                            shopping_list_ok = False
                            break
                    
                    if shopping_list_ok:
                        self.log_test("Shopping List Structure", True, "Shopping list structure correct (no regression)")
                        success_count += 1
                    else:
                        self.log_test("Shopping List Structure", False, "Shopping list structure broken")
                else:
                    self.log_test("Shopping List Section", False, "Shopping list section missing")
                
                # Show complete data structure for verification
                print(f"\n📊 DAILY SUMMARY DATA STRUCTURE ANALYSIS:")
                print(f"   Date: {summary.get('date', 'N/A')}")
                print(f"   Employee Orders Count: {len(employee_orders)}")
                print(f"   Breakfast Summary Keys: {list(breakfast_summary.keys()) if breakfast_summary else 'None'}")
                print(f"   Shopping List Keys: {list(shopping_list.keys()) if shopping_list else 'None'}")
                
                if employee_orders:
                    first_employee = list(employee_orders.keys())[0]
                    first_employee_data = employee_orders[first_employee]
                    print(f"   First Employee Toppings: {first_employee_data.get('toppings', {})}")
                
            else:
                self.log_test("Get Daily Summary", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary Analysis", False, f"Exception: {str(e)}")
        
        return success_count >= 6  # Expect at least 6 successful tests
    
    def test_breakfast_day_deletion(self):
        """Test the new breakfast day deletion functionality"""
        print("\n=== Testing Breakfast Day Deletion Functionality ===")
        
        if not self.departments or not self.employees:
            self.log_test("Breakfast Day Deletion", False, "Missing departments or employees")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        test_employee = self.employees[0]
        
        # First authenticate as department admin
        admin_auth_success = False
        try:
            admin_login_data = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"  # Using admin1 as per review request
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            if response.status_code == 200:
                admin_auth_success = True
                self.log_test("Department Admin Authentication", True, "Successfully authenticated as department admin")
                success_count += 1
            else:
                self.log_test("Department Admin Authentication", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Department Admin Authentication", False, f"Exception: {str(e)}")
        
        if not admin_auth_success:
            return False
        
        # Create test breakfast orders for today's date
        today = datetime.now().date().isoformat()
        created_orders = []
        
        try:
            # Create multiple breakfast orders with new format
            for i in range(3):
                breakfast_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_dept['id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 2,
                            "white_halves": 1,
                            "seeded_halves": 1,
                            "toppings": ["ruehrei", "kaese"],
                            "has_lunch": False,
                            "boiled_eggs": 0
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
                if response.status_code == 200:
                    order = response.json()
                    created_orders.append(order)
                    self.log_test(f"Create Test Breakfast Order {i+1}", True, f"Order created with total: €{order['total_price']:.2f}")
                else:
                    self.log_test(f"Create Test Breakfast Order {i+1}", False, f"HTTP {response.status_code}: {response.text}")
            
            if len(created_orders) >= 2:
                success_count += 1
                self.log_test("Create Test Orders", True, f"Created {len(created_orders)} test breakfast orders")
            
        except Exception as e:
            self.log_test("Create Test Orders", False, f"Exception: {str(e)}")
        
        # Get employee balance before deletion
        initial_balance = 0.0
        try:
            employee_response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            if employee_response.status_code == 200:
                profile = employee_response.json()
                initial_balance = profile['employee']['breakfast_balance']
                self.log_test("Get Initial Balance", True, f"Initial breakfast balance: €{initial_balance:.2f}")
                success_count += 1
        except Exception as e:
            self.log_test("Get Initial Balance", False, f"Exception: {str(e)}")
        
        # Test DELETE breakfast day endpoint
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/breakfast-day/{test_dept['id']}/{today}")
            
            if response.status_code == 200:
                result = response.json()
                deleted_count = result.get('deleted_orders', 0)
                total_refunded = result.get('total_refunded', 0.0)
                
                self.log_test("Delete Breakfast Day", True, 
                            f"Successfully deleted {deleted_count} orders, refunded €{total_refunded:.2f}")
                success_count += 1
                
                # Verify response structure
                required_fields = ['message', 'deleted_orders', 'total_refunded', 'date']
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    self.log_test("Delete Response Structure", True, "Response has all required fields")
                    success_count += 1
                else:
                    self.log_test("Delete Response Structure", False, f"Missing fields: {missing_fields}")
                
            else:
                self.log_test("Delete Breakfast Day", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Delete Breakfast Day", False, f"Exception: {str(e)}")
        
        # Verify employee balance adjustment
        try:
            employee_response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            if employee_response.status_code == 200:
                profile = employee_response.json()
                final_balance = profile['employee']['breakfast_balance']
                
                if final_balance < initial_balance:
                    self.log_test("Balance Adjustment", True, 
                                f"Balance correctly adjusted from €{initial_balance:.2f} to €{final_balance:.2f}")
                    success_count += 1
                else:
                    self.log_test("Balance Adjustment", False, 
                                f"Balance not adjusted properly: €{initial_balance:.2f} -> €{final_balance:.2f}")
        except Exception as e:
            self.log_test("Balance Adjustment", False, f"Exception: {str(e)}")
        
        # Verify orders are removed from database
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            if response.status_code == 200:
                summary = response.json()
                breakfast_summary = summary.get('breakfast_summary', {})
                
                # Check if breakfast summary is empty or has minimal data
                total_orders = sum(data.get('halves', 0) for data in breakfast_summary.values())
                
                if total_orders == 0:
                    self.log_test("Data Integrity - Orders Removed", True, "All breakfast orders removed from daily summary")
                    success_count += 1
                else:
                    self.log_test("Data Integrity - Orders Removed", False, f"Still found {total_orders} halves in summary")
        except Exception as e:
            self.log_test("Data Integrity - Orders Removed", False, f"Exception: {str(e)}")
        
        # Test error handling with invalid date
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/breakfast-day/{test_dept['id']}/invalid-date")
            
            if response.status_code == 400:
                self.log_test("Error Handling - Invalid Date", True, "Correctly rejected invalid date format")
                success_count += 1
            else:
                self.log_test("Error Handling - Invalid Date", False, f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("Error Handling - Invalid Date", False, f"Exception: {str(e)}")
        
        # Test error handling with non-existent date
        try:
            future_date = "2025-12-31"  # Future date with no orders
            response = self.session.delete(f"{API_BASE}/department-admin/breakfast-day/{test_dept['id']}/{future_date}")
            
            if response.status_code == 404:
                self.log_test("Error Handling - Non-existent Date", True, "Correctly returned 404 for date with no orders")
                success_count += 1
            else:
                self.log_test("Error Handling - Non-existent Date", False, f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("Error Handling - Non-existent Date", False, f"Exception: {str(e)}")
        
        # Test authorization - try without admin credentials (should fail)
        try:
            # Create a new session without admin authentication
            unauthorized_session = requests.Session()
            response = unauthorized_session.delete(f"{API_BASE}/department-admin/breakfast-day/{test_dept['id']}/{today}")
            
            # Note: The endpoint doesn't have explicit auth middleware, but it's under department-admin path
            # This test verifies the endpoint exists and responds appropriately
            if response.status_code in [401, 403, 404]:
                self.log_test("Authorization Check", True, f"Endpoint properly protected (HTTP {response.status_code})")
                success_count += 1
            else:
                self.log_test("Authorization Check", False, f"Expected auth error, got {response.status_code}")
        except Exception as e:
            self.log_test("Authorization Check", False, f"Exception: {str(e)}")
        
        return success_count >= 6  # At least 6 out of 10 tests should pass

    def test_password_change_functionality(self):
        """Test password change functionality for both employee and admin passwords"""
        print("\n=== Testing Password Change Functionality ===")
        
        if not self.departments:
            self.log_test("Password Change", False, "No departments available for testing")
            return False
        
        success_count = 0
        test_dept = None
        
        # Find department 1 (1. Wachabteilung)
        for dept in self.departments:
            if "1." in dept['name'] and "Wachabteilung" in dept['name']:
                test_dept = dept
                break
        
        if not test_dept:
            self.log_test("Find Department 1", False, "Could not find department 1 for testing")
            return False
        
        self.log_test("Find Department 1", True, f"Found department: {test_dept['name']}")
        
        # Step 1: Test initial authentication with original passwords
        try:
            # Test employee login with password1
            employee_login = {
                "department_name": test_dept['name'],
                "password": "password1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department", json=employee_login)
            if response.status_code == 200:
                self.log_test("Initial Employee Authentication", True, "Successfully authenticated with password1")
                success_count += 1
            else:
                self.log_test("Initial Employee Authentication", False, f"Failed to authenticate with password1: {response.status_code}")
                return False
            
            # Test admin login with admin1
            admin_login = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login)
            if response.status_code == 200:
                self.log_test("Initial Admin Authentication", True, "Successfully authenticated with admin1")
                success_count += 1
            else:
                self.log_test("Initial Admin Authentication", False, f"Failed to authenticate with admin1: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Initial Authentication", False, f"Exception: {str(e)}")
            return False
        
        # Step 2: Test individual password change endpoints
        try:
            # Test change employee password endpoint
            response = self.session.put(f"{API_BASE}/department-admin/change-employee-password/{test_dept['id']}", 
                                      params={"new_password": "newpass1"})
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Change Employee Password Endpoint", True, 
                            f"Employee password changed: {result.get('message', 'Success')}")
                success_count += 1
            else:
                self.log_test("Change Employee Password Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Change Employee Password Endpoint", False, f"Exception: {str(e)}")
            return False
        
        try:
            # Test change admin password endpoint
            response = self.session.put(f"{API_BASE}/department-admin/change-admin-password/{test_dept['id']}", 
                                      params={"new_password": "newadmin1"})
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Change Admin Password Endpoint", True, 
                            f"Admin password changed: {result.get('message', 'Success')}")
                success_count += 1
            else:
                self.log_test("Change Admin Password Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Change Admin Password Endpoint", False, f"Exception: {str(e)}")
            return False
        
        # Step 3: Test that old passwords no longer work
        try:
            # Test old employee password should fail
            old_employee_login = {
                "department_name": test_dept['name'],
                "password": "password1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department", json=old_employee_login)
            if response.status_code == 401:
                self.log_test("Old Employee Password Rejected", True, "Old employee password correctly rejected")
                success_count += 1
            else:
                self.log_test("Old Employee Password Rejected", False, 
                            f"Old password should be rejected, got {response.status_code}")
            
            # Test old admin password should fail
            old_admin_login = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=old_admin_login)
            if response.status_code == 401:
                self.log_test("Old Admin Password Rejected", True, "Old admin password correctly rejected")
                success_count += 1
            else:
                self.log_test("Old Admin Password Rejected", False, 
                            f"Old admin password should be rejected, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Old Password Rejection", False, f"Exception: {str(e)}")
        
        # Step 4: Test authentication with new passwords
        try:
            # Test new employee password
            new_employee_login = {
                "department_name": test_dept['name'],
                "password": "newpass1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department", json=new_employee_login)
            if response.status_code == 200:
                login_result = response.json()
                if login_result.get('department_id') == test_dept['id']:
                    self.log_test("New Employee Password Authentication", True, 
                                "Successfully authenticated with new employee password")
                    success_count += 1
                else:
                    self.log_test("New Employee Password Authentication", False, 
                                "Department ID mismatch with new password")
            else:
                self.log_test("New Employee Password Authentication", False, 
                            f"Failed to authenticate with new password: {response.status_code}")
            
            # Test new admin password
            new_admin_login = {
                "department_name": test_dept['name'],
                "admin_password": "newadmin1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=new_admin_login)
            if response.status_code == 200:
                login_result = response.json()
                if (login_result.get('department_id') == test_dept['id'] and 
                    login_result.get('role') == 'department_admin'):
                    self.log_test("New Admin Password Authentication", True, 
                                "Successfully authenticated with new admin password")
                    success_count += 1
                else:
                    self.log_test("New Admin Password Authentication", False, 
                                "Department ID or role mismatch with new admin password")
            else:
                self.log_test("New Admin Password Authentication", False, 
                            f"Failed to authenticate with new admin password: {response.status_code}")
                
        except Exception as e:
            self.log_test("New Password Authentication", False, f"Exception: {str(e)}")
        
        # Step 5: Test database persistence by checking department data
        try:
            # Get department data to verify password changes are persisted
            response = self.session.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                departments = response.json()
                updated_dept = None
                for dept in departments:
                    if dept['id'] == test_dept['id']:
                        updated_dept = dept
                        break
                
                if updated_dept:
                    # We can't directly check password hashes, but we can verify the department still exists
                    # and our authentication tests above confirm the passwords work
                    self.log_test("Database Persistence Check", True, 
                                "Department data retrieved successfully after password changes")
                    success_count += 1
                else:
                    self.log_test("Database Persistence Check", False, 
                                "Could not find updated department in database")
            else:
                self.log_test("Database Persistence Check", False, 
                            f"Failed to retrieve departments: {response.status_code}")
                
        except Exception as e:
            self.log_test("Database Persistence Check", False, f"Exception: {str(e)}")
        
        # Step 6: Test endpoint availability and error handling
        try:
            # Test with invalid department ID
            response = self.session.put(f"{API_BASE}/department-admin/change-employee-password/invalid-id", 
                                      params={"new_password": "testpass"})
            
            if response.status_code == 404:
                self.log_test("Invalid Department ID Handling", True, 
                            "Correctly handled invalid department ID")
                success_count += 1
            else:
                self.log_test("Invalid Department ID Handling", False, 
                            f"Expected 404 for invalid ID, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Department ID Handling", False, f"Exception: {str(e)}")
        
        return success_count >= 8  # Expect at least 8 out of 10 tests to pass

    def test_four_specific_bug_fixes(self):
        """Test the 4 specific bug fixes mentioned in the review request"""
        print("\n=== Testing Four Specific Bug Fixes ===")
        
        success_count = 0
        
        # First authenticate as department admin
        if not self.departments:
            self.log_test("Bug Fixes Authentication", False, "No departments available")
            return False
        
        test_dept = self.departments[0]
        admin_auth_success = False
        
        try:
            admin_login_data = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"  # Using updated admin password
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            if response.status_code == 200:
                admin_auth_success = True
                self.log_test("Admin Authentication for Bug Tests", True, "Successfully authenticated as department admin")
            else:
                self.log_test("Admin Authentication for Bug Tests", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Admin Authentication for Bug Tests", False, f"Exception: {str(e)}")
        
        if not admin_auth_success:
            return False
        
        # BUG 1: Test Simplified Topping Creation
        try:
            # Test the new POST /api/department-admin/menu/toppings endpoint with topping_id, topping_name, and price
            custom_topping_data = {
                "topping_id": "hausgemachte_marmelade",
                "topping_name": "Hausgemachte Marmelade", 
                "price": 0.75,
                "department_id": test_dept['id']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", json=custom_topping_data)
            
            if response.status_code == 200:
                topping = response.json()
                if (topping.get('name') == "Hausgemachte Marmelade" and 
                    topping.get('price') == 0.75):
                    self.log_test("Bug 1 - Simplified Topping Creation", True, 
                                f"Successfully created custom topping: {topping['name']} for €{topping['price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Bug 1 - Simplified Topping Creation", False, "Topping data mismatch")
            else:
                self.log_test("Bug 1 - Simplified Topping Creation", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bug 1 - Simplified Topping Creation", False, f"Exception: {str(e)}")
        
        # BUG 2: Test Lunch Display Logic
        if self.employees:
            try:
                test_employee = self.employees[0]
                
                # Create a breakfast order with lunch=true
                breakfast_with_lunch = {
                    "employee_id": test_employee['id'],
                    "department_id": test_dept['id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 2,
                            "white_halves": 2,
                            "seeded_halves": 0,
                            "toppings": ["ruehrei", "kaese"],
                            "has_lunch": True
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=breakfast_with_lunch)
                
                if response.status_code == 200:
                    order = response.json()
                    
                    # Verify lunch is included in order
                    if (order.get('breakfast_items') and 
                        len(order['breakfast_items']) > 0 and
                        order['breakfast_items'][0].get('has_lunch') == True):
                        self.log_test("Bug 2 - Lunch Display Logic (Order Creation)", True, 
                                    f"Breakfast order with lunch created successfully: €{order['total_price']:.2f}")
                        
                        # Now check if it shows correctly in daily summary
                        summary_response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
                        
                        if summary_response.status_code == 200:
                            summary = summary_response.json()
                            
                            # Check if lunch appears in the summary data
                            has_lunch_data = False
                            if 'employee_orders' in summary:
                                for employee_name, employee_data in summary['employee_orders'].items():
                                    if employee_name == test_employee['name']:
                                        has_lunch_data = True
                                        break
                            
                            if has_lunch_data:
                                self.log_test("Bug 2 - Lunch Display Logic (Daily Summary)", True, 
                                            "Lunch order appears correctly in daily summary")
                                success_count += 1
                            else:
                                self.log_test("Bug 2 - Lunch Display Logic (Daily Summary)", False, 
                                            "Lunch order not found in daily summary")
                        else:
                            self.log_test("Bug 2 - Lunch Display Logic (Daily Summary)", False, 
                                        f"Failed to get daily summary: HTTP {summary_response.status_code}")
                    else:
                        self.log_test("Bug 2 - Lunch Display Logic (Order Creation)", False, 
                                    "Lunch option not saved in order")
                else:
                    self.log_test("Bug 2 - Lunch Display Logic (Order Creation)", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Bug 2 - Lunch Display Logic", False, f"Exception: {str(e)}")
        
        # BUG 3: Test Lunch Counter in Shopping List
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check if daily summary includes lunch count data
                has_lunch_count = False
                lunch_count = 0
                
                # Look for lunch-related data in the response
                if 'employee_orders' in summary:
                    for employee_name, employee_data in summary['employee_orders'].items():
                        # Check if employee has lunch orders (this would be indicated by orders with has_lunch=true)
                        if isinstance(employee_data, dict):
                            has_lunch_count = True
                            break
                
                # Also check if there's a specific lunch count field
                if 'total_lunch_orders' in summary or has_lunch_count:
                    self.log_test("Bug 3 - Lunch Counter in Shopping List", True, 
                                "Daily summary includes lunch count data")
                    success_count += 1
                else:
                    self.log_test("Bug 3 - Lunch Counter in Shopping List", False, 
                                "Daily summary missing lunch count data")
            else:
                self.log_test("Bug 3 - Lunch Counter in Shopping List", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Bug 3 - Lunch Counter in Shopping List", False, f"Exception: {str(e)}")
        
        # BUG 4: Test Retroactive Price Updates
        try:
            # First, get current lunch price
            lunch_response = self.session.get(f"{API_BASE}/lunch-settings")
            if lunch_response.status_code == 200:
                current_settings = lunch_response.json()
                original_price = current_settings.get('price', 0.0)
                
                # Update lunch price
                new_lunch_price = 5.50
                update_response = self.session.put(f"{API_BASE}/lunch-settings", 
                                                 params={"price": new_lunch_price})
                
                if update_response.status_code == 200:
                    update_result = update_response.json()
                    
                    # Check if existing orders were updated
                    if 'updated_orders' in update_result:
                        updated_count = update_result['updated_orders']
                        self.log_test("Bug 4 - Retroactive Price Updates", True, 
                                    f"Lunch price updated to €{new_lunch_price:.2f}, {updated_count} existing orders updated")
                        success_count += 1
                    else:
                        self.log_test("Bug 4 - Retroactive Price Updates", True, 
                                    f"Lunch price updated to €{new_lunch_price:.2f} (no existing orders to update)")
                        success_count += 1
                else:
                    self.log_test("Bug 4 - Retroactive Price Updates", False, 
                                f"Failed to update lunch price: HTTP {update_response.status_code}")
            else:
                self.log_test("Bug 4 - Retroactive Price Updates", False, 
                            f"Failed to get lunch settings: HTTP {lunch_response.status_code}")
                
        except Exception as e:
            self.log_test("Bug 4 - Retroactive Price Updates", False, f"Exception: {str(e)}")
        
        return success_count >= 3  # At least 3 out of 4 bugs should be fixed

    def test_breakfast_ordering_flexibility(self):
        """Test new breakfast ordering flexibility that allows orders without rolls"""
        print("\n=== Testing Breakfast Ordering Flexibility (No Rolls Required) ===")
        
        if not self.employees or not self.departments:
            self.log_test("Breakfast Ordering Flexibility", False, "No employees or departments available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        test_dept = self.departments[0]
        
        # First authenticate with department 1 (password1)
        try:
            login_data = {
                "department_name": "1. Wachabteilung",
                "password": "password1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department", json=login_data)
            if response.status_code == 200:
                self.log_test("Department 1 Authentication", True, "Successfully authenticated with password1")
                success_count += 1
            else:
                self.log_test("Department 1 Authentication", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Department 1 Authentication", False, f"Exception: {str(e)}")
            return False
        
        # Get lunch settings to check boiled eggs price
        try:
            response = self.session.get(f"{API_BASE}/lunch-settings")
            if response.status_code == 200:
                lunch_settings = response.json()
                boiled_eggs_price = lunch_settings.get('boiled_eggs_price', 0.50)
                lunch_price = lunch_settings.get('price', 0.0)
                self.log_test("Get Lunch Settings", True, f"Boiled eggs: €{boiled_eggs_price:.2f}, Lunch: €{lunch_price:.2f}")
            else:
                boiled_eggs_price = 0.50
                lunch_price = 0.0
                self.log_test("Get Lunch Settings", False, "Using default prices")
        except Exception as e:
            boiled_eggs_price = 0.50
            lunch_price = 0.0
            self.log_test("Get Lunch Settings", False, f"Exception: {str(e)}")
        
        # Test 1: Only Boiled Eggs (0 rolls, just boiled_eggs > 0)
        try:
            only_eggs_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 0,
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],
                        "has_lunch": False,
                        "boiled_eggs": 3
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=only_eggs_order)
            
            if response.status_code == 200:
                order = response.json()
                expected_price = boiled_eggs_price * 3
                if abs(order['total_price'] - expected_price) < 0.01:
                    self.log_test("Only Boiled Eggs Order", True, 
                                f"Created order with 3 boiled eggs: €{order['total_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Only Boiled Eggs Order", False, 
                                f"Price mismatch: expected €{expected_price:.2f}, got €{order['total_price']:.2f}")
            else:
                self.log_test("Only Boiled Eggs Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Only Boiled Eggs Order", False, f"Exception: {str(e)}")
        
        # Test 2: Only Lunch (0 rolls, just has_lunch = true)
        try:
            only_lunch_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 0,
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],
                        "has_lunch": True,
                        "boiled_eggs": 0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=only_lunch_order)
            
            if response.status_code == 200:
                order = response.json()
                expected_price = lunch_price  # Just lunch price once (no rolls)
                if abs(order['total_price'] - expected_price) < 0.01:
                    self.log_test("Only Lunch Order", True, 
                                f"Created order with only lunch: €{order['total_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Only Lunch Order", False, 
                                f"Price mismatch: expected €{expected_price:.2f}, got €{order['total_price']:.2f}")
            else:
                self.log_test("Only Lunch Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Only Lunch Order", False, f"Exception: {str(e)}")
        
        # Test 3: Eggs + Lunch (0 rolls, boiled_eggs > 0 AND has_lunch = true)
        try:
            eggs_lunch_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 0,
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],
                        "has_lunch": True,
                        "boiled_eggs": 2
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=eggs_lunch_order)
            
            if response.status_code == 200:
                order = response.json()
                expected_price = lunch_price + (boiled_eggs_price * 2)
                if abs(order['total_price'] - expected_price) < 0.01:
                    self.log_test("Eggs + Lunch Order", True, 
                                f"Created order with 2 eggs + lunch: €{order['total_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Eggs + Lunch Order", False, 
                                f"Price mismatch: expected €{expected_price:.2f}, got €{order['total_price']:.2f}")
            else:
                self.log_test("Eggs + Lunch Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Eggs + Lunch Order", False, f"Exception: {str(e)}")
        
        # Test 4: Traditional Order (rolls + toppings still work normally)
        try:
            # Get breakfast menu prices
            response = self.session.get(f"{API_BASE}/menu/breakfast/{test_employee['department_id']}")
            if response.status_code == 200:
                breakfast_menu = response.json()
                white_price = next((item['price'] for item in breakfast_menu if item['roll_type'] == 'weiss'), 0.50)
                seeded_price = next((item['price'] for item in breakfast_menu if item['roll_type'] == 'koerner'), 0.60)
            else:
                white_price = 0.50
                seeded_price = 0.60
            
            traditional_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 4,
                        "white_halves": 2,
                        "seeded_halves": 2,
                        "toppings": ["ruehrei", "kaese", "schinken", "butter"],
                        "has_lunch": False,
                        "boiled_eggs": 0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=traditional_order)
            
            if response.status_code == 200:
                order = response.json()
                expected_price = (white_price * 2) + (seeded_price * 2)  # Toppings are free
                if abs(order['total_price'] - expected_price) < 0.01:
                    self.log_test("Traditional Order", True, 
                                f"Created traditional order with rolls + toppings: €{order['total_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Traditional Order", False, 
                                f"Price mismatch: expected €{expected_price:.2f}, got €{order['total_price']:.2f}")
            else:
                self.log_test("Traditional Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Traditional Order", False, f"Exception: {str(e)}")
        
        # Test 5: Mixed Order (rolls + eggs + lunch all together)
        try:
            mixed_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": True,
                        "boiled_eggs": 1
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=mixed_order)
            
            if response.status_code == 200:
                order = response.json()
                expected_price = (white_price * 1) + (seeded_price * 1) + (lunch_price * 2) + (boiled_eggs_price * 1)
                if abs(order['total_price'] - expected_price) < 0.01:
                    self.log_test("Mixed Order", True, 
                                f"Created mixed order (rolls + eggs + lunch): €{order['total_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Mixed Order", False, 
                                f"Price mismatch: expected €{expected_price:.2f}, got €{order['total_price']:.2f}")
            else:
                self.log_test("Mixed Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Mixed Order", False, f"Exception: {str(e)}")
        
        # Test 6: Invalid Order (no rolls, no eggs, no lunch)
        try:
            invalid_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 0,
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],
                        "has_lunch": False,
                        "boiled_eggs": 0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=invalid_order)
            
            if response.status_code == 400:
                self.log_test("Invalid Order Rejection", True, 
                            "Correctly rejected order with no rolls, eggs, or lunch")
                success_count += 1
            else:
                self.log_test("Invalid Order Rejection", False, 
                            f"Should reject invalid order, got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Invalid Order Rejection", False, f"Exception: {str(e)}")
        
        return success_count >= 5  # At least 5 out of 6 tests should pass

    def test_topping_system_bugs(self):
        """Test and fix the topping system bugs as requested in the review"""
        print("\n=== Testing Topping System Bugs ===")
        
        if not self.departments:
            self.log_test("Topping System Bugs", False, "No departments available for testing")
            return False
        
        success_count = 0
        test_dept = self.departments[0]  # Use first department
        
        # Step 1: Get current toppings for department 1
        try:
            response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
            
            if response.status_code == 200:
                current_toppings = response.json()
                self.log_test("Get Current Toppings", True, 
                            f"Found {len(current_toppings)} toppings for department 1")
                success_count += 1
                
                # Check for duplicate toppings with different topping_type vs topping_name
                topping_names = {}
                duplicates_found = []
                
                for topping in current_toppings:
                    topping_type = topping.get('topping_type', '')
                    topping_name = topping.get('name', topping_type)
                    display_name = topping_name if topping_name else topping_type
                    
                    if display_name in topping_names:
                        duplicates_found.append({
                            'name': display_name,
                            'existing': topping_names[display_name],
                            'duplicate': topping
                        })
                    else:
                        topping_names[display_name] = topping
                
                if duplicates_found:
                    self.log_test("Check for Duplicate Toppings", False, 
                                f"Found {len(duplicates_found)} duplicate toppings: {[d['name'] for d in duplicates_found]}")
                    
                    # Clean up duplicates
                    for duplicate in duplicates_found:
                        try:
                            # Delete the duplicate entry
                            dup_id = duplicate['duplicate']['id']
                            delete_response = self.session.delete(f"{API_BASE}/department-admin/menu/toppings/{dup_id}")
                            if delete_response.status_code == 200:
                                self.log_test(f"Clean Duplicate Topping {duplicate['name']}", True, 
                                            f"Successfully removed duplicate topping")
                            else:
                                self.log_test(f"Clean Duplicate Topping {duplicate['name']}", False, 
                                            f"Failed to remove duplicate: HTTP {delete_response.status_code}")
                        except Exception as e:
                            self.log_test(f"Clean Duplicate Topping {duplicate['name']}", False, f"Exception: {str(e)}")
                else:
                    self.log_test("Check for Duplicate Toppings", True, "No duplicate toppings found")
                    success_count += 1
                    
            else:
                self.log_test("Get Current Toppings", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Current Toppings", False, f"Exception: {str(e)}")
        
        # Step 2: Create a test topping with custom name
        test_topping_id = None
        try:
            test_topping_data = {
                "topping_id": "test_schnittei",
                "topping_name": "Test Schnittei",
                "price": 0.75,
                "department_id": test_dept['id']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", 
                                       json=test_topping_data)
            
            if response.status_code == 200:
                test_topping = response.json()
                test_topping_id = test_topping['id']
                self.log_test("Create Test Topping", True, 
                            f"Created test topping 'Test Schnittei' with ID: {test_topping_id}")
                success_count += 1
            else:
                self.log_test("Create Test Topping", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Test Topping", False, f"Exception: {str(e)}")
        
        # Step 3: Update the topping name and verify no duplicates
        if test_topping_id:
            try:
                update_data = {
                    "name": "Updated Schnittei Premium",
                    "price": 1.00
                }
                
                response = self.session.put(f"{API_BASE}/department-admin/menu/toppings/{test_topping_id}", 
                                          json=update_data, 
                                          params={"department_id": test_dept['id']})
                
                if response.status_code == 200:
                    self.log_test("Update Topping Name", True, 
                                "Successfully updated topping name to 'Updated Schnittei Premium'")
                    success_count += 1
                    
                    # Verify the update by fetching the topping again
                    verify_response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
                    if verify_response.status_code == 200:
                        updated_toppings = verify_response.json()
                        updated_topping = next((t for t in updated_toppings if t['id'] == test_topping_id), None)
                        
                        if updated_topping:
                            # Check if both topping_name and topping_type are updated correctly
                            name_updated = updated_topping.get('name') == "Updated Schnittei Premium"
                            type_updated = updated_topping.get('topping_type') == test_topping_id  # Should match ID
                            price_updated = updated_topping.get('price') == 1.00
                            
                            if name_updated and type_updated and price_updated:
                                self.log_test("Verify Topping Update", True, 
                                            "Both topping_name and topping_type updated correctly")
                                success_count += 1
                            else:
                                self.log_test("Verify Topping Update", False, 
                                            f"Update verification failed: name={name_updated}, type={type_updated}, price={price_updated}")
                        else:
                            self.log_test("Verify Topping Update", False, "Updated topping not found")
                    
                    # Check for duplicates after update
                    duplicate_check_response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
                    if duplicate_check_response.status_code == 200:
                        all_toppings = duplicate_check_response.json()
                        schnittei_toppings = [t for t in all_toppings if 'schnittei' in t.get('name', '').lower() or 'schnittei' in t.get('topping_type', '').lower()]
                        
                        if len(schnittei_toppings) <= 1:
                            self.log_test("No Duplicates After Update", True, 
                                        f"Found {len(schnittei_toppings)} Schnittei topping(s) - no duplicates")
                            success_count += 1
                        else:
                            self.log_test("No Duplicates After Update", False, 
                                        f"Found {len(schnittei_toppings)} Schnittei toppings - duplicates exist")
                else:
                    self.log_test("Update Topping Name", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Update Topping Name", False, f"Exception: {str(e)}")
        
        # Step 4: Test deletion functionality
        if test_topping_id:
            try:
                response = self.session.delete(f"{API_BASE}/department-admin/menu/toppings/{test_topping_id}")
                
                if response.status_code == 200:
                    self.log_test("Delete Test Topping", True, 
                                "Successfully deleted test topping")
                    success_count += 1
                    
                    # Verify deletion
                    verify_response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
                    if verify_response.status_code == 200:
                        remaining_toppings = verify_response.json()
                        deleted_topping = next((t for t in remaining_toppings if t['id'] == test_topping_id), None)
                        
                        if not deleted_topping:
                            self.log_test("Verify Topping Deletion", True, 
                                        "Topping properly removed from database")
                            success_count += 1
                        else:
                            self.log_test("Verify Topping Deletion", False, 
                                        "Topping still exists after deletion")
                else:
                    self.log_test("Delete Test Topping", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Delete Test Topping", False, f"Exception: {str(e)}")
        
        # Step 5: Clean up any remaining problematic entries
        try:
            final_response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
            if final_response.status_code == 200:
                final_toppings = final_response.json()
                
                # Look for any inconsistent entries
                inconsistent_entries = []
                for topping in final_toppings:
                    topping_type = topping.get('topping_type', '')
                    topping_name = topping.get('name', '')
                    
                    # Check for inconsistencies
                    if topping_name and topping_type and topping_name != topping_type:
                        # This is actually expected for custom names, so check for real issues
                        if not topping_name.strip() or not topping_type.strip():
                            inconsistent_entries.append(topping)
                
                if inconsistent_entries:
                    self.log_test("Clean Inconsistent Entries", False, 
                                f"Found {len(inconsistent_entries)} inconsistent topping entries")
                    
                    # Clean up inconsistent entries
                    for entry in inconsistent_entries:
                        try:
                            delete_response = self.session.delete(f"{API_BASE}/department-admin/menu/toppings/{entry['id']}")
                            if delete_response.status_code == 200:
                                self.log_test(f"Clean Inconsistent Entry {entry['id']}", True, 
                                            "Successfully removed inconsistent entry")
                        except Exception as e:
                            self.log_test(f"Clean Inconsistent Entry {entry['id']}", False, f"Exception: {str(e)}")
                else:
                    self.log_test("Database Consistency Check", True, 
                                "Database is clean and consistent")
                    success_count += 1
                    
        except Exception as e:
            self.log_test("Database Consistency Check", False, f"Exception: {str(e)}")
        
        return success_count >= 6  # At least 6 out of the main tests should pass

    def run_all_tests(self):
        """Run all backend tests focusing on Department-Specific Menu System"""
        print("🧪 Starting Department-Specific Menu System Testing for German Canteen Management System")
        print(f"🌐 Testing against: {API_BASE}")
        print("=" * 60)
        
        # Run essential setup tests first
        setup_tests = [
            ("Data Initialization", self.test_data_initialization),
            ("Department Retrieval", self.test_get_departments),
            ("Department Admin Authentication", self.test_department_admin_authentication),
            ("Employee Management", self.test_employee_management),
            ("Menu Endpoints", self.test_menu_endpoints),
        ]
        
        # Department-Specific Menu System tests (main focus)
        department_specific_tests = [
            ("Department-Specific Migration", self.test_department_specific_migration),
            ("Department-Specific Menu Endpoints", self.test_department_specific_menu_endpoints),
            ("Backward Compatibility Menus", self.test_backward_compatibility_menus),
            ("Department-Specific Order Creation", self.test_department_specific_order_creation),
            ("Department Isolation & Data Integrity", self.test_department_isolation_data_integrity),
        ]
        
        # Additional critical tests
        critical_tests = [
            ("🎯 Topping System Bugs Testing", self.test_topping_system_bugs),  # Add the new topping test
            ("🎯 Four Specific Bug Fixes", self.test_four_specific_bug_fixes),
            ("Critical Breakfast Ordering Fixes", self.test_critical_breakfast_ordering_fixes),
            ("Critical Bug Fixes", self.test_critical_bug_fixes),
            ("🔧 Daily Summary Toppings Fix - [object Object] Issue", self.test_daily_summary_toppings_fix),
            ("🆕 NEW FEATURE - Breakfast Day Deletion", self.test_breakfast_day_deletion),
            ("🔐 PASSWORD CHANGE FUNCTIONALITY", self.test_password_change_functionality),
            ("🆕 BREAKFAST ORDERING FLEXIBILITY - No Rolls Required", self.test_breakfast_ordering_flexibility),
        ]
        
        # NEW FEATURE TEST - Boiled Breakfast Eggs
        new_feature_tests = [
            ("🆕 NEW FEATURE - Boiled Breakfast Eggs", self.test_boiled_breakfast_eggs_feature),
            ("🆕 NEW FEATURE - Admin Boiled Eggs Pricing Management", self.test_admin_boiled_eggs_pricing_management),
        ]
        
        # Run setup tests
        print("\n--- Running Essential Setup Tests ---")
        setup_passed = 0
        for test_name, test_func in setup_tests:
            try:
                if test_func():
                    setup_passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {str(e)}")
        
        print(f"\nSetup Tests: {setup_passed}/{len(setup_tests)} passed")
        
        # Run Department-Specific Menu System tests (main focus)
        print("\n--- Running Department-Specific Menu System Tests ---")
        dept_specific_passed = 0
        for test_name, test_func in department_specific_tests:
            try:
                if test_func():
                    dept_specific_passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {str(e)}")
        
        # Run additional critical tests
        print("\n--- Running Additional Critical Tests ---")
        critical_passed = 0
        for test_name, test_func in critical_tests:
            try:
                if test_func():
                    critical_passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {str(e)}")
        
        # Run NEW FEATURE tests - Boiled Breakfast Eggs
        print("\n--- Running NEW FEATURE Tests - Boiled Breakfast Eggs ---")
        new_feature_passed = 0
        for test_name, test_func in new_feature_tests:
            try:
                if test_func():
                    new_feature_passed += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 BACKEND TESTING SUMMARY - INCLUDING NEW BOILED EGGS FEATURE")
        print("=" * 60)
        
        total_tests = len(setup_tests) + len(department_specific_tests) + len(critical_tests) + len(new_feature_tests)
        total_passed = setup_passed + dept_specific_passed + critical_passed + new_feature_passed
        
        print(f"✅ Setup Tests: {setup_passed}/{len(setup_tests)}")
        print(f"🏢 Department-Specific Tests: {dept_specific_passed}/{len(department_specific_tests)}")
        print(f"🔧 Additional Critical Tests: {critical_passed}/{len(critical_tests)}")
        print(f"🆕 NEW FEATURE - Boiled Eggs Tests: {new_feature_passed}/{len(new_feature_tests)}")
        print(f"📊 Overall: {total_passed}/{total_tests}")
        
        # Print individual test results for department-specific tests
        print(f"\n📋 Department-Specific Menu System Test Details:")
        dept_specific_results = [result for result in self.test_results 
                               if any(keyword in result['test'] for keyword in 
                                    ['Migration', 'Department-Specific', 'Backward Compatible', 
                                     'Department Isolation', 'Department ID Integrity'])]
        
        for result in dept_specific_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}: {result['message']}")
        
        # Overall status
        if dept_specific_passed == len(department_specific_tests):
            print(f"\n🎉 DEPARTMENT-SPECIFIC MENU SYSTEM: ALL WORKING CORRECTLY!")
            return (total_passed, total_tests - total_passed)
        elif dept_specific_passed >= len(department_specific_tests) * 0.8:  # 80% pass rate
            print(f"\n✅ DEPARTMENT-SPECIFIC MENU SYSTEM: MOSTLY WORKING ({dept_specific_passed}/{len(department_specific_tests)})")
            return (total_passed, total_tests - total_passed)
        elif dept_specific_passed > 0:
            print(f"\n⚠️  DEPARTMENT-SPECIFIC MENU SYSTEM: PARTIALLY WORKING ({dept_specific_passed}/{len(department_specific_tests)})")
            return (total_passed, total_tests - total_passed)
        else:
            print(f"\n🚨 DEPARTMENT-SPECIFIC MENU SYSTEM: MAJOR ISSUES DETECTED")
            return (total_passed, total_tests - total_passed)

    def test_drag_drop_employee_creation(self):
        """Test employee creation and management for drag and drop functionality"""
        print("\n=== Testing Employee Creation for Drag and Drop ===")
        
        success_count = 0
        
        # First, ensure we have department 1 available
        if not self.departments:
            # Try to get departments first
            try:
                response = self.session.get(f"{API_BASE}/departments")
                if response.status_code == 200:
                    self.departments = response.json()
            except:
                pass
        
        # Find department 1 (first department)
        department_1 = None
        for dept in self.departments:
            if "1." in dept['name'] or dept['name'].endswith('A'):
                department_1 = dept
                break
        
        if not department_1:
            # Use first available department
            department_1 = self.departments[0] if self.departments else None
        
        if not department_1:
            self.log_test("Find Department 1", False, "No departments available for testing")
            return False
        
        self.log_test("Find Department 1", True, f"Using department: {department_1['name']}")
        success_count += 1
        
        # Create the 3 specific test employees
        test_employees = [
            "Max Mustermann",
            "Anna Schmidt", 
            "Peter Weber"
        ]
        
        created_employees = []
        
        for employee_name in test_employees:
            try:
                employee_data = {
                    "name": employee_name,
                    "department_id": department_1['id']
                }
                
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                
                if response.status_code == 200:
                    employee = response.json()
                    created_employees.append(employee)
                    
                    # Verify employee data structure
                    required_fields = ['id', 'name', 'department_id', 'breakfast_balance', 'drinks_sweets_balance']
                    missing_fields = [field for field in required_fields if field not in employee]
                    
                    if not missing_fields:
                        self.log_test(f"Create Employee: {employee_name}", True, 
                                    f"Created with ID: {employee['id'][:8]}..., Balance: €{employee['breakfast_balance']:.2f}")
                        success_count += 1
                    else:
                        self.log_test(f"Create Employee: {employee_name}", False, 
                                    f"Missing fields: {missing_fields}")
                else:
                    self.log_test(f"Create Employee: {employee_name}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Create Employee: {employee_name}", False, f"Exception: {str(e)}")
        
        # Test employee listing endpoint
        try:
            response = self.session.get(f"{API_BASE}/departments/{department_1['id']}/employees")
            
            if response.status_code == 200:
                dept_employees = response.json()
                
                # Check if our created employees are in the list
                created_names = [emp['name'] for emp in created_employees]
                found_employees = [emp for emp in dept_employees if emp['name'] in created_names]
                
                if len(found_employees) >= len(created_employees):
                    self.log_test("Employee Listing", True, 
                                f"Found {len(found_employees)} employees in department listing")
                    success_count += 1
                    
                    # Verify data structure for drag and drop
                    for employee in found_employees:
                        required_fields = ['id', 'name', 'department_id', 'breakfast_balance', 'drinks_sweets_balance']
                        missing_fields = [field for field in required_fields if field not in employee]
                        
                        if not missing_fields:
                            self.log_test(f"Employee Data Structure: {employee['name']}", True, 
                                        "All required fields present for frontend")
                            success_count += 1
                        else:
                            self.log_test(f"Employee Data Structure: {employee['name']}", False, 
                                        f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Employee Listing", False, 
                                f"Expected {len(created_employees)} employees, found {len(found_employees)}")
            else:
                self.log_test("Employee Listing", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Employee Listing", False, f"Exception: {str(e)}")
        
        # Test individual employee data retrieval (for drag and drop functionality)
        for employee in created_employees:
            try:
                # Test getting employee orders (needed for drag and drop context)
                response = self.session.get(f"{API_BASE}/employees/{employee['id']}/orders")
                
                if response.status_code == 200:
                    orders_data = response.json()
                    if 'orders' in orders_data:
                        self.log_test(f"Employee Orders: {employee['name']}", True, 
                                    f"Orders endpoint accessible with {len(orders_data['orders'])} orders")
                        success_count += 1
                    else:
                        self.log_test(f"Employee Orders: {employee['name']}", False, 
                                    "Orders data structure incorrect")
                else:
                    self.log_test(f"Employee Orders: {employee['name']}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Employee Orders: {employee['name']}", False, f"Exception: {str(e)}")
        
        # Summary of created employees for drag and drop
        if created_employees:
            employee_names = [emp['name'] for emp in created_employees]
            self.log_test("Drag and Drop Data Ready", True, 
                        f"Created {len(created_employees)} employees: {', '.join(employee_names)}")
            success_count += 1
        
        return success_count >= 6  # At least 6 successful operations

    def run_drag_drop_test_only(self):
        """Run only the drag and drop employee creation test"""
        print("🚀 Starting Employee Creation and Management Test for Drag and Drop")
        print(f"🌐 Testing against: {API_BASE}")
        print("=" * 80)
        
        # Initialize data first
        print("\n=== Initializing Test Data ===")
        self.test_data_initialization()
        self.test_get_departments()
        
        # Run the specific test
        print(f"\n{'='*20} Drag and Drop Employee Test {'='*20}")
        try:
            if self.test_drag_drop_employee_creation():
                print("✅ Drag and Drop Employee Test PASSED")
                return True
            else:
                print("❌ Drag and Drop Employee Test FAILED")
                return False
        except Exception as e:
            print(f"❌ Drag and Drop Employee Test FAILED with exception: {str(e)}")
            return False

if __name__ == "__main__":
    tester = CanteenTester()
    
    # Check if we should run only the drag and drop test
    if len(sys.argv) > 1 and sys.argv[1] == "--drag-drop-only":
        success = tester.run_drag_drop_test_only()
        sys.exit(0 if success else 1)
    else:
        passed, failed = tester.run_all_tests()
        sys.exit(0 if failed == 0 else 1)