#!/usr/bin/env python3
"""
Critical Bugs Test Suite for German Canteen Management System
Tests the four new critical bugs reported in the system
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

class CriticalBugsTester:
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
        self.admin_auth = None
        
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
        """Initialize test data and authenticate"""
        print("\n=== Setting Up Test Data ===")
        
        # Initialize data
        try:
            response = self.session.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.log_test("Data Initialization", True, "Test data initialized")
            else:
                self.log_test("Data Initialization", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Data Initialization", False, f"Exception: {str(e)}")
            return False

        # Get departments
        try:
            response = self.session.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                self.departments = response.json()
                self.log_test("Get Departments", True, f"Found {len(self.departments)} departments")
            else:
                return False
        except Exception as e:
            return False

        # Create test employees
        for i, dept in enumerate(self.departments[:2]):  # Use first 2 departments
            try:
                employee_data = {
                    "name": f"Test Employee {i+1}",
                    "department_id": dept['id']
                }
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    self.employees.append(response.json())
            except:
                pass

        # Get menu items for first department
        if self.departments:
            dept_id = self.departments[0]['id']
            for menu_type in ['breakfast', 'toppings', 'drinks', 'sweets']:
                try:
                    response = self.session.get(f"{API_BASE}/menu/{menu_type}/{dept_id}")
                    if response.status_code == 200:
                        self.menu_items[menu_type] = response.json()
                except:
                    # Try backward compatibility endpoint
                    try:
                        response = self.session.get(f"{API_BASE}/menu/{menu_type}")
                        if response.status_code == 200:
                            self.menu_items[menu_type] = response.json()
                    except:
                        pass

        # Authenticate as department admin
        if self.departments:
            try:
                admin_login_data = {
                    "department_name": self.departments[0]['name'],
                    "admin_password": "admin1"
                }
                response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
                if response.status_code == 200:
                    self.admin_auth = response.json()
                    self.log_test("Admin Authentication", True, "Admin authenticated successfully")
            except:
                pass

        return len(self.departments) > 0 and len(self.employees) > 0

    def test_bug_1_breakfast_ordering_price_error(self):
        """
        BUG 1: Breakfast Ordering Price Error
        Test breakfast order creation with seeded rolls (Körner Brötchen)
        Verify menu prices from admin panel vs actual order pricing
        Check if seeded rolls show 999€ or other incorrect pricing
        """
        print("\n=== Testing BUG 1: Breakfast Ordering Price Error ===")
        
        if not self.employees or not self.menu_items['breakfast']:
            self.log_test("Bug 1 Setup", False, "Missing test data")
            return False

        success_count = 0
        test_employee = self.employees[0]
        
        # Test 1.1: Check menu prices for seeded rolls
        try:
            seeded_roll_item = None
            for item in self.menu_items['breakfast']:
                if item.get('roll_type') == 'koerner':  # Seeded roll
                    seeded_roll_item = item
                    break
            
            if seeded_roll_item:
                price = seeded_roll_item['price']
                if price == 999.0 or price > 50.0:  # Check for 999€ bug or unreasonable pricing
                    self.log_test("Seeded Roll Price Check", False, 
                                f"CRITICAL: Seeded roll shows incorrect price: €{price:.2f}")
                elif 0.1 <= price <= 5.0:  # Reasonable price range
                    self.log_test("Seeded Roll Price Check", True, 
                                f"Seeded roll price is reasonable: €{price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Seeded Roll Price Check", False, 
                                f"Seeded roll price seems unusual: €{price:.2f}")
            else:
                self.log_test("Seeded Roll Price Check", False, "No seeded roll found in menu")
                
        except Exception as e:
            self.log_test("Seeded Roll Price Check", False, f"Exception: {str(e)}")

        # Test 1.2: Create breakfast order with seeded rolls and verify pricing
        try:
            if seeded_roll_item:
                breakfast_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 2,
                            "white_halves": 0,
                            "seeded_halves": 2,
                            "toppings": ["ruehrei", "kaese"],
                            "has_lunch": False
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
                
                if response.status_code == 200:
                    order = response.json()
                    total_price = order['total_price']
                    
                    # Calculate expected price (2 seeded halves * price)
                    expected_price = seeded_roll_item['price'] * 2
                    
                    if abs(total_price - expected_price) < 0.01:
                        self.log_test("Seeded Roll Order Pricing", True, 
                                    f"Order pricing correct: €{total_price:.2f} (expected: €{expected_price:.2f})")
                        success_count += 1
                    elif total_price > 100:  # Check for 999€ bug in orders
                        self.log_test("Seeded Roll Order Pricing", False, 
                                    f"CRITICAL: Order shows excessive price: €{total_price:.2f}")
                    else:
                        self.log_test("Seeded Roll Order Pricing", False, 
                                    f"Price mismatch: got €{total_price:.2f}, expected €{expected_price:.2f}")
                else:
                    self.log_test("Seeded Roll Order Creation", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            self.log_test("Seeded Roll Order Pricing", False, f"Exception: {str(e)}")

        # Test 1.3: Test department-specific menu pricing consistency
        try:
            for dept in self.departments[:2]:  # Test first 2 departments
                response = self.session.get(f"{API_BASE}/menu/breakfast/{dept['id']}")
                if response.status_code == 200:
                    dept_breakfast_menu = response.json()
                    for item in dept_breakfast_menu:
                        if item.get('roll_type') == 'koerner':
                            price = item['price']
                            if price == 999.0 or price > 50.0:
                                self.log_test(f"Dept {dept['name']} Seeded Roll Price", False, 
                                            f"CRITICAL: Department shows incorrect price: €{price:.2f}")
                            else:
                                self.log_test(f"Dept {dept['name']} Seeded Roll Price", True, 
                                            f"Department price OK: €{price:.2f}")
                                success_count += 1
                            break
                            
        except Exception as e:
            self.log_test("Department-Specific Pricing", False, f"Exception: {str(e)}")

        return success_count >= 2

    def test_bug_2_breakfast_overview_toppings_display(self):
        """
        BUG 2: Breakfast Overview Toppings Display Issue
        Test GET /api/orders/daily-summary/{department_id} response structure
        Check if toppings data contains objects instead of strings
        Verify data structure in breakfast summaries and employee details
        """
        print("\n=== Testing BUG 2: Breakfast Overview Toppings Display Issue ===")
        
        if not self.employees or not self.departments:
            self.log_test("Bug 2 Setup", False, "Missing test data")
            return False

        success_count = 0
        test_employee = self.employees[0]
        test_dept = self.departments[0]

        # Create test breakfast orders with toppings
        try:
            breakfast_order = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 2,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese", "schinken"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                self.log_test("Create Test Order for Summary", True, "Test order created")
            else:
                self.log_test("Create Test Order for Summary", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Create Test Order for Summary", False, f"Exception: {str(e)}")

        # Test 2.1: Check daily summary structure
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                self.log_test("Daily Summary Response", True, "Got daily summary response")
                
                # Check breakfast_summary structure
                breakfast_summary = summary.get('breakfast_summary', {})
                if breakfast_summary:
                    self.log_test("Breakfast Summary Present", True, "Breakfast summary found")
                    success_count += 1
                    
                    # Check toppings data structure
                    toppings_issues = []
                    for roll_type, roll_data in breakfast_summary.items():
                        if 'toppings' in roll_data:
                            toppings = roll_data['toppings']
                            if isinstance(toppings, dict):
                                # Check if toppings values are proper (should be integers, not objects)
                                for topping_name, topping_count in toppings.items():
                                    if isinstance(topping_count, dict):
                                        toppings_issues.append(f"Topping '{topping_name}' contains object: {topping_count}")
                                    elif not isinstance(topping_count, (int, float)):
                                        toppings_issues.append(f"Topping '{topping_name}' has invalid count type: {type(topping_count)}")
                            else:
                                toppings_issues.append(f"Toppings for {roll_type} is not a dict: {type(toppings)}")
                    
                    if toppings_issues:
                        self.log_test("Toppings Data Structure", False, 
                                    f"CRITICAL: Toppings contain objects/invalid data: {toppings_issues}")
                    else:
                        self.log_test("Toppings Data Structure", True, 
                                    "Toppings data structure is correct (no objects)")
                        success_count += 1
                else:
                    self.log_test("Breakfast Summary Present", False, "No breakfast summary found")
                    
            else:
                self.log_test("Daily Summary Response", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary Response", False, f"Exception: {str(e)}")

        # Test 2.2: Check employee_orders structure in daily summary
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                employee_orders = summary.get('employee_orders', {})
                
                if employee_orders:
                    self.log_test("Employee Orders Present", True, "Employee orders found in summary")
                    
                    # Check employee toppings structure
                    employee_toppings_issues = []
                    for employee_name, employee_data in employee_orders.items():
                        if 'toppings' in employee_data:
                            toppings = employee_data['toppings']
                            if isinstance(toppings, dict):
                                for topping_name, topping_data in toppings.items():
                                    # Check if topping data is object with white/seeded counts
                                    if isinstance(topping_data, dict):
                                        if 'white' not in topping_data or 'seeded' not in topping_data:
                                            employee_toppings_issues.append(f"Employee {employee_name} topping '{topping_name}' missing white/seeded structure")
                                        elif not isinstance(topping_data['white'], (int, float)) or not isinstance(topping_data['seeded'], (int, float)):
                                            employee_toppings_issues.append(f"Employee {employee_name} topping '{topping_name}' has invalid count types")
                                    else:
                                        employee_toppings_issues.append(f"Employee {employee_name} topping '{topping_name}' should be object with white/seeded counts")
                    
                    if employee_toppings_issues:
                        self.log_test("Employee Toppings Structure", False, 
                                    f"Employee toppings structure issues: {employee_toppings_issues}")
                    else:
                        self.log_test("Employee Toppings Structure", True, 
                                    "Employee toppings structure is correct")
                        success_count += 1
                else:
                    self.log_test("Employee Orders Present", False, "No employee orders found")
                    
        except Exception as e:
            self.log_test("Employee Orders Structure", False, f"Exception: {str(e)}")

        # Test 2.3: Check total_toppings structure
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                total_toppings = summary.get('total_toppings', {})
                
                if total_toppings:
                    self.log_test("Total Toppings Present", True, "Total toppings found in summary")
                    
                    # Check total toppings structure
                    total_toppings_issues = []
                    for topping_name, topping_count in total_toppings.items():
                        if not isinstance(topping_count, (int, float)):
                            total_toppings_issues.append(f"Total topping '{topping_name}' has invalid count type: {type(topping_count)}")
                        elif isinstance(topping_count, dict):
                            total_toppings_issues.append(f"Total topping '{topping_name}' contains object: {topping_count}")
                    
                    if total_toppings_issues:
                        self.log_test("Total Toppings Structure", False, 
                                    f"CRITICAL: Total toppings contain objects: {total_toppings_issues}")
                    else:
                        self.log_test("Total Toppings Structure", True, 
                                    "Total toppings structure is correct")
                        success_count += 1
                        
        except Exception as e:
            self.log_test("Total Toppings Structure", False, f"Exception: {str(e)}")

        return success_count >= 2

    def test_bug_3_admin_dashboard_order_management_display(self):
        """
        BUG 3: Admin Dashboard Order Management Display
        Test GET /api/employees/{employee_id}/orders endpoint
        Check if drink_items and sweet_items contain IDs vs names
        Verify data structure for order details display in admin panel
        """
        print("\n=== Testing BUG 3: Admin Dashboard Order Management Display ===")
        
        if not self.employees or not self.menu_items['drinks'] or not self.menu_items['sweets']:
            self.log_test("Bug 3 Setup", False, "Missing test data")
            return False

        success_count = 0
        test_employee = self.employees[0]

        # Create test orders with drinks and sweets
        try:
            # Create drinks order
            drink_item = self.menu_items['drinks'][0]
            drinks_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "drinks",
                "drink_items": {drink_item['id']: 2}
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=drinks_order)
            if response.status_code == 200:
                self.log_test("Create Test Drinks Order", True, "Drinks order created")
            
            # Create sweets order
            sweet_item = self.menu_items['sweets'][0]
            sweets_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "sweets",
                "sweet_items": {sweet_item['id']: 1}
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=sweets_order)
            if response.status_code == 200:
                self.log_test("Create Test Sweets Order", True, "Sweets order created")
                
        except Exception as e:
            self.log_test("Create Test Orders", False, f"Exception: {str(e)}")

        # Test 3.1: Check employee orders endpoint structure
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get('orders', [])
                
                if orders:
                    self.log_test("Employee Orders Response", True, f"Found {len(orders)} orders")
                    success_count += 1
                    
                    # Check drink_items structure
                    drink_order_issues = []
                    sweet_order_issues = []
                    
                    for order in orders:
                        if order.get('order_type') == 'drinks' and order.get('drink_items'):
                            drink_items = order['drink_items']
                            if isinstance(drink_items, dict):
                                for item_key, quantity in drink_items.items():
                                    # Check if item_key is an ID (UUID-like) or a name
                                    if len(item_key) < 10:  # Short string, likely a name
                                        drink_order_issues.append(f"Drink item key '{item_key}' appears to be a name, not ID")
                                    elif not isinstance(quantity, (int, float)):
                                        drink_order_issues.append(f"Drink item '{item_key}' has invalid quantity type: {type(quantity)}")
                            else:
                                drink_order_issues.append(f"drink_items is not a dict: {type(drink_items)}")
                        
                        if order.get('order_type') == 'sweets' and order.get('sweet_items'):
                            sweet_items = order['sweet_items']
                            if isinstance(sweet_items, dict):
                                for item_key, quantity in sweet_items.items():
                                    # Check if item_key is an ID (UUID-like) or a name
                                    if len(item_key) < 10:  # Short string, likely a name
                                        sweet_order_issues.append(f"Sweet item key '{item_key}' appears to be a name, not ID")
                                    elif not isinstance(quantity, (int, float)):
                                        sweet_order_issues.append(f"Sweet item '{item_key}' has invalid quantity type: {type(quantity)}")
                            else:
                                sweet_order_issues.append(f"sweet_items is not a dict: {type(sweet_items)}")
                    
                    if drink_order_issues:
                        self.log_test("Drink Items Structure", False, 
                                    f"CRITICAL: Drink items structure issues: {drink_order_issues}")
                    else:
                        self.log_test("Drink Items Structure", True, 
                                    "Drink items contain proper IDs")
                        success_count += 1
                    
                    if sweet_order_issues:
                        self.log_test("Sweet Items Structure", False, 
                                    f"CRITICAL: Sweet items structure issues: {sweet_order_issues}")
                    else:
                        self.log_test("Sweet Items Structure", True, 
                                    "Sweet items contain proper IDs")
                        success_count += 1
                        
                else:
                    self.log_test("Employee Orders Response", False, "No orders found")
                    
            else:
                self.log_test("Employee Orders Response", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Employee Orders Response", False, f"Exception: {str(e)}")

        # Test 3.2: Check employee profile endpoint for order display
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                order_history = profile.get('order_history', [])
                
                if order_history:
                    self.log_test("Employee Profile Orders", True, f"Found {len(order_history)} orders in profile")
                    
                    # Check readable_items for drinks and sweets
                    readable_items_issues = []
                    for order in order_history:
                        if order.get('order_type') in ['drinks', 'sweets'] and 'readable_items' in order:
                            readable_items = order['readable_items']
                            if isinstance(readable_items, list):
                                for item in readable_items:
                                    if 'description' not in item:
                                        readable_items_issues.append(f"Readable item missing description: {item}")
                                    elif len(item['description']) > 100:  # Very long description might indicate ID instead of name
                                        readable_items_issues.append(f"Readable item description too long (possible ID): {item['description'][:50]}...")
                            else:
                                readable_items_issues.append(f"readable_items is not a list: {type(readable_items)}")
                    
                    if readable_items_issues:
                        self.log_test("Readable Items Structure", False, 
                                    f"Readable items issues: {readable_items_issues}")
                    else:
                        self.log_test("Readable Items Structure", True, 
                                    "Readable items structure is correct")
                        success_count += 1
                        
        except Exception as e:
            self.log_test("Employee Profile Orders", False, f"Exception: {str(e)}")

        return success_count >= 2

    def test_bug_4_data_structure_issues(self):
        """
        BUG 4: Data Structure Issues
        Test department-specific menu endpoints to ensure proper data format
        Verify that menu items have correct structure (id, name, price, etc.)
        Check topping menu data structure for dropdown population
        """
        print("\n=== Testing BUG 4: Data Structure Issues ===")
        
        if not self.departments:
            self.log_test("Bug 4 Setup", False, "Missing departments")
            return False

        success_count = 0
        test_dept = self.departments[0]

        # Test 4.1: Department-specific menu endpoints structure
        menu_types = ['breakfast', 'toppings', 'drinks', 'sweets']
        
        for menu_type in menu_types:
            try:
                response = self.session.get(f"{API_BASE}/menu/{menu_type}/{test_dept['id']}")
                
                if response.status_code == 200:
                    menu_items = response.json()
                    
                    if menu_items:
                        self.log_test(f"{menu_type.title()} Menu Response", True, 
                                    f"Found {len(menu_items)} {menu_type} items")
                        
                        # Check required fields for each item
                        structure_issues = []
                        for item in menu_items:
                            required_fields = ['id', 'price', 'department_id']
                            
                            # Add type-specific required fields
                            if menu_type == 'breakfast':
                                required_fields.append('roll_type')
                            elif menu_type == 'toppings':
                                required_fields.append('topping_type')
                            else:
                                required_fields.append('name')
                            
                            missing_fields = [field for field in required_fields if field not in item]
                            if missing_fields:
                                structure_issues.append(f"Item {item.get('id', 'unknown')} missing fields: {missing_fields}")
                            
                            # Check data types
                            if 'price' in item and not isinstance(item['price'], (int, float)):
                                structure_issues.append(f"Item {item.get('id', 'unknown')} price is not numeric: {type(item['price'])}")
                            
                            if 'department_id' in item and not isinstance(item['department_id'], str):
                                structure_issues.append(f"Item {item.get('id', 'unknown')} department_id is not string: {type(item['department_id'])}")
                        
                        if structure_issues:
                            self.log_test(f"{menu_type.title()} Menu Structure", False, 
                                        f"CRITICAL: Structure issues: {structure_issues}")
                        else:
                            self.log_test(f"{menu_type.title()} Menu Structure", True, 
                                        f"{menu_type.title()} menu structure is correct")
                            success_count += 1
                    else:
                        self.log_test(f"{menu_type.title()} Menu Response", False, 
                                    f"No {menu_type} items found")
                else:
                    self.log_test(f"{menu_type.title()} Menu Response", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"{menu_type.title()} Menu Response", False, f"Exception: {str(e)}")

        # Test 4.2: Topping menu data structure for dropdown population
        try:
            response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
            
            if response.status_code == 200:
                toppings = response.json()
                
                if toppings:
                    self.log_test("Toppings for Dropdown", True, f"Found {len(toppings)} toppings")
                    
                    # Check if toppings have proper structure for dropdown
                    dropdown_issues = []
                    for topping in toppings:
                        # Check if topping has display name (either custom name or default from topping_type)
                        display_name = topping.get('name') or topping.get('topping_type', '')
                        if not display_name:
                            dropdown_issues.append(f"Topping {topping.get('id', 'unknown')} has no display name")
                        
                        # Check if topping_type is valid enum value
                        valid_topping_types = ['ruehrei', 'spiegelei', 'eiersalat', 'salami', 'schinken', 'kaese', 'butter']
                        if topping.get('topping_type') not in valid_topping_types:
                            dropdown_issues.append(f"Topping {topping.get('id', 'unknown')} has invalid topping_type: {topping.get('topping_type')}")
                    
                    if dropdown_issues:
                        self.log_test("Toppings Dropdown Structure", False, 
                                    f"CRITICAL: Dropdown issues: {dropdown_issues}")
                    else:
                        self.log_test("Toppings Dropdown Structure", True, 
                                    "Toppings have proper structure for dropdown")
                        success_count += 1
                        
        except Exception as e:
            self.log_test("Toppings Dropdown Structure", False, f"Exception: {str(e)}")

        # Test 4.3: Check backward compatibility endpoints
        try:
            for menu_type in menu_types:
                response = self.session.get(f"{API_BASE}/menu/{menu_type}")
                
                if response.status_code == 200:
                    menu_items = response.json()
                    if menu_items:
                        self.log_test(f"Backward Compatibility {menu_type.title()}", True, 
                                    f"Backward compatibility endpoint works: {len(menu_items)} items")
                        success_count += 1
                    else:
                        self.log_test(f"Backward Compatibility {menu_type.title()}", False, 
                                    "No items returned from backward compatibility endpoint")
                else:
                    self.log_test(f"Backward Compatibility {menu_type.title()}", False, 
                                f"HTTP {response.status_code}")
                    
        except Exception as e:
            self.log_test("Backward Compatibility", False, f"Exception: {str(e)}")

        # Test 4.4: Check menu item custom names vs default names
        try:
            # Test breakfast items
            response = self.session.get(f"{API_BASE}/menu/breakfast/{test_dept['id']}")
            if response.status_code == 200:
                breakfast_items = response.json()
                name_issues = []
                
                for item in breakfast_items:
                    roll_type = item.get('roll_type')
                    custom_name = item.get('name')
                    
                    # Check if custom name is set and different from roll_type
                    if custom_name and custom_name != roll_type:
                        # Custom name is set
                        pass
                    elif not custom_name:
                        # Should fall back to default roll_type name
                        if roll_type not in ['weiss', 'koerner']:
                            name_issues.append(f"Breakfast item has invalid roll_type: {roll_type}")
                    
                if name_issues:
                    self.log_test("Breakfast Item Names", False, f"Name issues: {name_issues}")
                else:
                    self.log_test("Breakfast Item Names", True, "Breakfast item names are correct")
                    success_count += 1
                    
        except Exception as e:
            self.log_test("Breakfast Item Names", False, f"Exception: {str(e)}")

        return success_count >= 4

    def run_all_tests(self):
        """Run all critical bug tests"""
        print("🚨 CRITICAL BUGS TESTING STARTED 🚨")
        print("Testing 4 new critical bugs in German canteen management system")
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return False
        
        # Run all bug tests
        bug_results = []
        bug_results.append(self.test_bug_1_breakfast_ordering_price_error())
        bug_results.append(self.test_bug_2_breakfast_overview_toppings_display())
        bug_results.append(self.test_bug_3_admin_dashboard_order_management_display())
        bug_results.append(self.test_bug_4_data_structure_issues())
        
        # Print summary
        print("\n" + "="*60)
        print("🚨 CRITICAL BUGS TEST SUMMARY 🚨")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nBUG STATUS:")
        bug_names = [
            "BUG 1: Breakfast Ordering Price Error",
            "BUG 2: Breakfast Overview Toppings Display", 
            "BUG 3: Admin Dashboard Order Management Display",
            "BUG 4: Data Structure Issues"
        ]
        
        for i, (bug_name, bug_result) in enumerate(zip(bug_names, bug_results)):
            status = "✅ RESOLVED" if bug_result else "❌ CRITICAL ISSUE"
            print(f"{status}: {bug_name}")
        
        # Print failed tests details
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n🔍 FAILED TESTS DETAILS:")
            for test in failed_tests:
                print(f"❌ {test['test']}: {test['message']}")
                if test['details']:
                    print(f"   Details: {test['details']}")
        
        return sum(bug_results) >= 2  # At least 2 bugs should be resolved

if __name__ == "__main__":
    tester = CriticalBugsTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)