#!/usr/bin/env python3
"""
Focused Critical Bugs Test for German Canteen Management System
Specifically testing the 4 critical bugs mentioned in the review request
"""

import requests
import json
import sys
from datetime import datetime
import os

# Use the backend URL directly
BACKEND_URL = "https://stable-canteen.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

class FocusedBugsTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.departments = []
        self.employees = []
        self.menu_items = {}
        
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
        """Setup basic test data"""
        print("\n=== Setting Up Test Data ===")
        
        # Get departments
        try:
            response = self.session.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                self.departments = response.json()
                print(f"Found {len(self.departments)} departments")
            else:
                print(f"Failed to get departments: {response.status_code}")
                return False
        except Exception as e:
            print(f"Exception getting departments: {e}")
            return False

        # Get employees for first department
        if self.departments:
            try:
                dept_id = self.departments[0]['id']
                response = self.session.get(f"{API_BASE}/departments/{dept_id}/employees")
                if response.status_code == 200:
                    self.employees = response.json()
                    print(f"Found {len(self.employees)} employees")
                    
                    # Create a test employee if none exist
                    if not self.employees:
                        employee_data = {
                            "name": "Test Employee",
                            "department_id": dept_id
                        }
                        response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                        if response.status_code == 200:
                            self.employees = [response.json()]
                            print("Created test employee")
            except Exception as e:
                print(f"Exception with employees: {e}")

        # Get menu items
        if self.departments:
            dept_id = self.departments[0]['id']
            for menu_type in ['breakfast', 'toppings', 'drinks', 'sweets']:
                try:
                    response = self.session.get(f"{API_BASE}/menu/{menu_type}/{dept_id}")
                    if response.status_code == 200:
                        self.menu_items[menu_type] = response.json()
                        print(f"Found {len(self.menu_items[menu_type])} {menu_type} items")
                except:
                    self.menu_items[menu_type] = []

        return len(self.departments) > 0

    def test_breakfast_price_error_bug(self):
        """Test the breakfast ordering price error specifically for seeded rolls"""
        print("\n=== Testing Breakfast Price Error Bug ===")
        
        success_count = 0
        
        # Check seeded roll pricing in menu
        seeded_rolls = [item for item in self.menu_items.get('breakfast', []) 
                       if item.get('roll_type') == 'koerner']
        
        if seeded_rolls:
            seeded_roll = seeded_rolls[0]
            price = seeded_roll['price']
            
            if price == 999.0:
                self.log_test("Seeded Roll 999€ Bug", False, 
                            f"CRITICAL: Seeded roll shows 999€ price bug!")
            elif price > 50.0:
                self.log_test("Seeded Roll Excessive Price", False, 
                            f"CRITICAL: Seeded roll shows excessive price: €{price:.2f}")
            else:
                self.log_test("Seeded Roll Price Check", True, 
                            f"Seeded roll price is reasonable: €{price:.2f}")
                success_count += 1
        else:
            self.log_test("Seeded Roll Availability", False, "No seeded rolls found in menu")

        # Test actual order creation with seeded rolls
        if self.employees and seeded_rolls:
            try:
                test_employee = self.employees[0]
                
                # Test with new breakfast format
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
                    
                    if total_price > 100:
                        self.log_test("Order Price Bug", False, 
                                    f"CRITICAL: Order shows excessive price: €{total_price:.2f}")
                    else:
                        self.log_test("Order Price Reasonable", True, 
                                    f"Order price is reasonable: €{total_price:.2f}")
                        success_count += 1
                else:
                    self.log_test("Order Creation", False, 
                                f"Failed to create order: {response.status_code} - {response.text}")
                    
            except Exception as e:
                self.log_test("Order Creation", False, f"Exception: {str(e)}")

        return success_count >= 1

    def test_toppings_display_bug(self):
        """Test the breakfast overview toppings display issue"""
        print("\n=== Testing Toppings Display Bug ===")
        
        success_count = 0
        
        if not self.departments:
            self.log_test("Toppings Display Test", False, "No departments available")
            return False

        dept_id = self.departments[0]['id']
        
        # Test daily summary endpoint
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{dept_id}")
            
            if response.status_code == 200:
                summary = response.json()
                self.log_test("Daily Summary Response", True, "Got daily summary")
                
                # Check breakfast_summary structure
                breakfast_summary = summary.get('breakfast_summary', {})
                
                # Look for object-instead-of-string issues in toppings
                toppings_issues = []
                for roll_type, roll_data in breakfast_summary.items():
                    if 'toppings' in roll_data:
                        toppings = roll_data['toppings']
                        for topping_name, topping_value in toppings.items():
                            if isinstance(topping_value, dict):
                                toppings_issues.append(f"Topping '{topping_name}' is object: {topping_value}")
                            elif isinstance(topping_value, str) and topping_value.startswith('[object'):
                                toppings_issues.append(f"Topping '{topping_name}' shows '[object Object]': {topping_value}")

                if toppings_issues:
                    self.log_test("Toppings Object Bug", False, 
                                f"CRITICAL: Found object-instead-of-string issues: {toppings_issues}")
                else:
                    self.log_test("Toppings Structure OK", True, 
                                "Toppings data structure is correct")
                    success_count += 1

                # Check employee_orders for similar issues
                employee_orders = summary.get('employee_orders', {})
                employee_toppings_issues = []
                
                for employee_name, employee_data in employee_orders.items():
                    if 'toppings' in employee_data:
                        toppings = employee_data['toppings']
                        for topping_name, topping_data in toppings.items():
                            if not isinstance(topping_data, dict):
                                employee_toppings_issues.append(f"Employee {employee_name} topping '{topping_name}' should be object with white/seeded counts")
                            elif 'white' not in topping_data or 'seeded' not in topping_data:
                                employee_toppings_issues.append(f"Employee {employee_name} topping '{topping_name}' missing white/seeded structure")

                if employee_toppings_issues:
                    self.log_test("Employee Toppings Structure", False, 
                                f"Employee toppings issues: {employee_toppings_issues}")
                else:
                    self.log_test("Employee Toppings Structure OK", True, 
                                "Employee toppings structure is correct")
                    success_count += 1
                    
            else:
                self.log_test("Daily Summary Response", False, 
                            f"Failed to get daily summary: {response.status_code}")
                
        except Exception as e:
            self.log_test("Daily Summary Test", False, f"Exception: {str(e)}")

        return success_count >= 1

    def test_admin_dashboard_display_bug(self):
        """Test the admin dashboard order management display issue"""
        print("\n=== Testing Admin Dashboard Display Bug ===")
        
        success_count = 0
        
        if not self.employees:
            self.log_test("Admin Dashboard Test", False, "No employees available")
            return False

        test_employee = self.employees[0]
        
        # Test employee orders endpoint
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get('orders', [])
                
                self.log_test("Employee Orders Response", True, f"Found {len(orders)} orders")
                
                # Check for ID vs name issues in drink_items and sweet_items
                id_vs_name_issues = []
                
                for order in orders:
                    if order.get('order_type') == 'drinks' and order.get('drink_items'):
                        drink_items = order['drink_items']
                        for item_key, quantity in drink_items.items():
                            # Check if item_key looks like a name instead of ID
                            if len(item_key) < 20 and ' ' in item_key:  # Likely a name
                                id_vs_name_issues.append(f"Drink item key '{item_key}' appears to be name instead of ID")
                    
                    if order.get('order_type') == 'sweets' and order.get('sweet_items'):
                        sweet_items = order['sweet_items']
                        for item_key, quantity in sweet_items.items():
                            # Check if item_key looks like a name instead of ID
                            if len(item_key) < 20 and ' ' in item_key:  # Likely a name
                                id_vs_name_issues.append(f"Sweet item key '{item_key}' appears to be name instead of ID")

                if id_vs_name_issues:
                    self.log_test("ID vs Name Issues", False, 
                                f"CRITICAL: Found ID vs name issues: {id_vs_name_issues}")
                else:
                    self.log_test("Order Items Structure OK", True, 
                                "Order items use proper IDs")
                    success_count += 1
                    
            else:
                self.log_test("Employee Orders Response", False, 
                            f"Failed to get employee orders: {response.status_code}")
                
        except Exception as e:
            self.log_test("Employee Orders Test", False, f"Exception: {str(e)}")

        # Test employee profile endpoint for readable display
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                order_history = profile.get('order_history', [])
                
                self.log_test("Employee Profile Response", True, f"Found {len(order_history)} orders in profile")
                
                # Check readable_items for proper display
                display_issues = []
                for order in order_history:
                    if order.get('order_type') in ['drinks', 'sweets'] and 'readable_items' in order:
                        readable_items = order['readable_items']
                        for item in readable_items:
                            description = item.get('description', '')
                            # Check for long numeric strings (IDs instead of names)
                            if len(description) > 30 and description.replace('-', '').replace(' ', '').isalnum():
                                display_issues.append(f"Description appears to be ID: {description[:30]}...")

                if display_issues:
                    self.log_test("Display Issues", False, 
                                f"CRITICAL: Found display issues: {display_issues}")
                else:
                    self.log_test("Profile Display OK", True, 
                                "Profile displays proper names, not IDs")
                    success_count += 1
                    
            else:
                self.log_test("Employee Profile Response", False, 
                            f"Failed to get employee profile: {response.status_code}")
                
        except Exception as e:
            self.log_test("Employee Profile Test", False, f"Exception: {str(e)}")

        return success_count >= 1

    def test_data_structure_bug(self):
        """Test general data structure issues"""
        print("\n=== Testing Data Structure Bug ===")
        
        success_count = 0
        
        if not self.departments:
            self.log_test("Data Structure Test", False, "No departments available")
            return False

        dept_id = self.departments[0]['id']
        
        # Test menu endpoints for proper structure
        menu_types = ['breakfast', 'toppings', 'drinks', 'sweets']
        
        for menu_type in menu_types:
            try:
                response = self.session.get(f"{API_BASE}/menu/{menu_type}/{dept_id}")
                
                if response.status_code == 200:
                    menu_items = response.json()
                    
                    if menu_items:
                        # Check for required fields
                        structure_issues = []
                        for item in menu_items:
                            if 'id' not in item:
                                structure_issues.append(f"{menu_type} item missing 'id' field")
                            if 'price' not in item:
                                structure_issues.append(f"{menu_type} item missing 'price' field")
                            if 'department_id' not in item:
                                structure_issues.append(f"{menu_type} item missing 'department_id' field")
                            
                            # Check price is numeric
                            if 'price' in item and not isinstance(item['price'], (int, float)):
                                structure_issues.append(f"{menu_type} item price is not numeric: {type(item['price'])}")

                        if structure_issues:
                            self.log_test(f"{menu_type.title()} Structure Issues", False, 
                                        f"CRITICAL: {structure_issues}")
                        else:
                            self.log_test(f"{menu_type.title()} Structure OK", True, 
                                        f"{menu_type.title()} menu structure is correct")
                            success_count += 1
                    else:
                        self.log_test(f"{menu_type.title()} Empty", False, 
                                    f"No {menu_type} items found")
                else:
                    self.log_test(f"{menu_type.title()} Response", False, 
                                f"Failed to get {menu_type}: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"{menu_type.title()} Test", False, f"Exception: {str(e)}")

        # Special test for toppings dropdown structure
        try:
            response = self.session.get(f"{API_BASE}/menu/toppings/{dept_id}")
            
            if response.status_code == 200:
                toppings = response.json()
                
                dropdown_issues = []
                for topping in toppings:
                    # Check if topping has proper display name
                    display_name = topping.get('name') or topping.get('topping_type', '')
                    if not display_name:
                        dropdown_issues.append(f"Topping {topping.get('id', 'unknown')} has no display name")
                    
                    # Check topping_type enum
                    valid_types = ['ruehrei', 'spiegelei', 'eiersalat', 'salami', 'schinken', 'kaese', 'butter']
                    if topping.get('topping_type') not in valid_types:
                        dropdown_issues.append(f"Invalid topping_type: {topping.get('topping_type')}")

                if dropdown_issues:
                    self.log_test("Toppings Dropdown Issues", False, 
                                f"CRITICAL: {dropdown_issues}")
                else:
                    self.log_test("Toppings Dropdown OK", True, 
                                "Toppings dropdown structure is correct")
                    success_count += 1
                    
        except Exception as e:
            self.log_test("Toppings Dropdown Test", False, f"Exception: {str(e)}")

        return success_count >= 3

    def run_focused_tests(self):
        """Run focused tests for the 4 critical bugs"""
        print("🚨 FOCUSED CRITICAL BUGS TESTING 🚨")
        print("Testing specific issues mentioned in review request")
        
        if not self.setup_test_data():
            print("❌ Failed to setup test data")
            return False
        
        # Run focused bug tests
        bug_results = []
        bug_results.append(self.test_breakfast_price_error_bug())
        bug_results.append(self.test_toppings_display_bug())
        bug_results.append(self.test_admin_dashboard_display_bug())
        bug_results.append(self.test_data_structure_bug())
        
        # Print summary
        print("\n" + "="*60)
        print("🚨 FOCUSED BUGS TEST SUMMARY 🚨")
        print("="*60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nCRITICAL BUGS STATUS:")
        bug_names = [
            "1. Breakfast Ordering Price Error (999€ bug)",
            "2. Breakfast Overview Toppings Display ([object Object])",
            "3. Admin Dashboard Order Management Display (IDs vs Names)",
            "4. Data Structure Issues (Menu format problems)"
        ]
        
        for i, (bug_name, bug_result) in enumerate(zip(bug_names, bug_results)):
            status = "✅ NO ISSUES FOUND" if bug_result else "❌ CRITICAL ISSUES DETECTED"
            print(f"{status}: {bug_name}")
        
        # Print critical issues
        critical_issues = [result for result in self.test_results if not result['success']]
        if critical_issues:
            print("\n🔍 CRITICAL ISSUES FOUND:")
            for test in critical_issues:
                print(f"❌ {test['test']}: {test['message']}")
        else:
            print("\n✅ NO CRITICAL ISSUES FOUND - All systems working correctly!")
        
        return len(critical_issues) == 0

if __name__ == "__main__":
    tester = FocusedBugsTester()
    success = tester.run_focused_tests()
    sys.exit(0 if success else 1)