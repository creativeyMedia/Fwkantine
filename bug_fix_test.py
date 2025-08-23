#!/usr/bin/env python3
"""
Bug Fix Test Suite for German Canteen Management System
Tests specific bug fixes and improvements as requested in the review
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

class BugFixTester:
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

        # Get menu items
        for menu_type in ['breakfast', 'toppings', 'drinks', 'sweets']:
            try:
                response = self.session.get(f"{API_BASE}/menu/{menu_type}")
                if response.status_code == 200:
                    self.menu_items[menu_type] = response.json()
            except:
                pass

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

        return len(self.departments) > 0 and len(self.employees) > 0

    def test_price_calculation_fix(self):
        """Test 1: Price Calculation Fix - Dynamic prices from menu instead of hardcoded values"""
        print("\n=== Testing Price Calculation Fix ===")
        
        if not self.employees or not self.menu_items['breakfast']:
            self.log_test("Price Calculation Fix", False, "Missing test data")
            return False

        success_count = 0
        test_employee = self.employees[0]

        # Get current menu prices
        breakfast_menu = self.menu_items['breakfast']
        toppings_menu = self.menu_items['toppings']
        
        # Find weiss and koerner roll prices
        weiss_price = None
        koerner_price = None
        for item in breakfast_menu:
            if item['roll_type'] == 'weiss':
                weiss_price = item['price']
            elif item['roll_type'] == 'koerner':
                koerner_price = item['price']

        if weiss_price is None or koerner_price is None:
            self.log_test("Menu Price Retrieval", False, "Could not find roll prices")
            return False

        self.log_test("Menu Price Retrieval", True, f"Weiss: €{weiss_price:.2f}, Koerner: €{koerner_price:.2f}")
        success_count += 1

        # Test breakfast order with new roll halves system
        try:
            breakfast_order = {
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

            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            
            if response.status_code == 200:
                order = response.json()
                
                # Calculate expected price: 2 * weiss_price + 2 * koerner_price + topping prices (should be 0)
                expected_price = (2 * weiss_price) + (2 * koerner_price)
                actual_price = order['total_price']
                
                # Allow small floating point differences
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("Dynamic Price Calculation", True, 
                                f"Expected: €{expected_price:.2f}, Actual: €{actual_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Dynamic Price Calculation", False, 
                                f"Expected: €{expected_price:.2f}, Actual: €{actual_price:.2f}")
                    
            else:
                self.log_test("Breakfast Order Creation", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Dynamic Price Calculation", False, f"Exception: {str(e)}")

        # Test different roll combinations
        try:
            # Test with only weiss rolls
            weiss_only_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 3,
                        "seeded_halves": 0,
                        "toppings": ["ruehrei", "kaese", "schinken"],
                        "has_lunch": False
                    }
                ]
            }

            response = self.session.post(f"{API_BASE}/orders", json=weiss_only_order)
            
            if response.status_code == 200:
                order = response.json()
                expected_price = 3 * weiss_price
                actual_price = order['total_price']
                
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("Weiss Only Price Calculation", True, 
                                f"3 weiss halves: €{actual_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Weiss Only Price Calculation", False, 
                                f"Expected: €{expected_price:.2f}, Actual: €{actual_price:.2f}")
                    
        except Exception as e:
            self.log_test("Weiss Only Price Calculation", False, f"Exception: {str(e)}")

        return success_count >= 2

    def test_employee_deletion(self):
        """Test 2: Employee Deletion - DELETE /api/department-admin/employees/{employee_id}"""
        print("\n=== Testing Employee Deletion ===")
        
        if not self.departments:
            self.log_test("Employee Deletion", False, "No departments available")
            return False

        success_count = 0
        test_dept = self.departments[0]

        # Create a test employee for deletion
        test_employee_id = None
        try:
            employee_data = {
                "name": "Employee To Delete",
                "department_id": test_dept['id']
            }
            
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                test_employee = response.json()
                test_employee_id = test_employee['id']
                self.log_test("Create Test Employee", True, f"Created employee: {test_employee['name']}")
                success_count += 1
            else:
                self.log_test("Create Test Employee", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create Test Employee", False, f"Exception: {str(e)}")
            return False

        # Create some orders for the employee
        try:
            order_data = {
                "employee_id": test_employee_id,
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
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                self.log_test("Create Test Order", True, "Created order for employee")
                
        except Exception as e:
            self.log_test("Create Test Order", False, f"Exception: {str(e)}")

        # Test employee deletion
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/employees/{test_employee_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Delete Employee", True, f"Response: {result.get('message', 'Success')}")
                success_count += 1
                
                # Verify employee is deleted by trying to get their profile
                profile_response = self.session.get(f"{API_BASE}/employees/{test_employee_id}/profile")
                if profile_response.status_code == 404:
                    self.log_test("Verify Employee Deleted", True, "Employee profile no longer accessible")
                    success_count += 1
                else:
                    self.log_test("Verify Employee Deleted", False, "Employee still exists after deletion")
                    
            else:
                self.log_test("Delete Employee", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Delete Employee", False, f"Exception: {str(e)}")

        # Test deletion with invalid employee ID
        try:
            invalid_id = "invalid-employee-id"
            response = self.session.delete(f"{API_BASE}/department-admin/employees/{invalid_id}")
            
            if response.status_code == 404:
                self.log_test("Delete Invalid Employee", True, "Correctly returned 404 for invalid ID")
                success_count += 1
            else:
                self.log_test("Delete Invalid Employee", False, f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Delete Invalid Employee", False, f"Exception: {str(e)}")

        return success_count >= 3

    def test_employee_profile_history(self):
        """Test 3: Employee Profile/History - GET /api/employees/{employee_id}/profile"""
        print("\n=== Testing Employee Profile/History ===")
        
        if not self.employees:
            self.log_test("Employee Profile", False, "No employees available")
            return False

        success_count = 0
        test_employee = self.employees[0]

        # Create some test orders for the employee
        try:
            # Breakfast order
            breakfast_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": True
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                self.log_test("Create Breakfast Order", True, "Created breakfast order for profile test")

            # Drinks order
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
                    self.log_test("Create Drinks Order", True, "Created drinks order for profile test")
                    
        except Exception as e:
            self.log_test("Create Test Orders", False, f"Exception: {str(e)}")

        # Test employee profile endpoint
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
                else:
                    self.log_test("Profile Structure", False, f"Missing fields: {missing_fields}")

                # Check employee data
                employee_data = profile.get('employee', {})
                if (employee_data.get('id') == test_employee['id'] and 
                    employee_data.get('name') == test_employee['name']):
                    self.log_test("Employee Data", True, "Employee details correct")
                    success_count += 1
                else:
                    self.log_test("Employee Data", False, "Employee details mismatch")

                # Check order history
                order_history = profile.get('order_history', [])
                if isinstance(order_history, list) and len(order_history) > 0:
                    self.log_test("Order History", True, f"Found {len(order_history)} orders in history")
                    success_count += 1
                    
                    # Check for German descriptions
                    has_german_descriptions = False
                    for order in order_history:
                        if 'readable_items' in order:
                            for item in order['readable_items']:
                                description = item.get('description', '')
                                if any(word in description for word in ['Brötchen', 'Hälften', 'Mittagessen']):
                                    has_german_descriptions = True
                                    break
                    
                    if has_german_descriptions:
                        self.log_test("German Descriptions", True, "Order history contains German descriptions")
                        success_count += 1
                    else:
                        self.log_test("German Descriptions", False, "Missing German descriptions")
                        
                else:
                    self.log_test("Order History", False, "No order history found")

                # Check balance totals
                if (isinstance(profile.get('total_orders'), int) and 
                    isinstance(profile.get('breakfast_total'), (int, float)) and
                    isinstance(profile.get('drinks_sweets_total'), (int, float))):
                    self.log_test("Balance Totals", True, 
                                f"Orders: {profile['total_orders']}, Breakfast: €{profile['breakfast_total']:.2f}, Drinks/Sweets: €{profile['drinks_sweets_total']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Balance Totals", False, "Invalid balance data")
                    
            else:
                self.log_test("Employee Profile", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Employee Profile", False, f"Exception: {str(e)}")

        # Test with non-existent employee
        try:
            invalid_id = "non-existent-employee-id"
            response = self.session.get(f"{API_BASE}/employees/{invalid_id}/profile")
            
            if response.status_code == 404:
                self.log_test("Non-existent Employee", True, "Correctly returned 404 for invalid employee")
                success_count += 1
            else:
                self.log_test("Non-existent Employee", False, f"Expected 404, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Non-existent Employee", False, f"Exception: {str(e)}")

        return success_count >= 4

    def test_payment_processing(self):
        """Test 4: Payment Processing - POST /api/department-admin/payment/{employee_id}"""
        print("\n=== Testing Payment Processing ===")
        
        if not self.employees or not self.departments:
            self.log_test("Payment Processing", False, "Missing test data")
            return False

        success_count = 0
        test_employee = self.employees[0]
        test_dept = self.departments[0]

        # First create some orders to generate balances
        try:
            # Create breakfast order
            breakfast_order = {
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
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                order = response.json()
                breakfast_amount = order['total_price']
                self.log_test("Create Breakfast for Payment", True, f"Created breakfast order: €{breakfast_amount:.2f}")

            # Create drinks order
            if self.menu_items['drinks']:
                drink_item = self.menu_items['drinks'][0]
                drinks_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "drinks",
                    "drink_items": {drink_item['id']: 3}
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=drinks_order)
                if response.status_code == 200:
                    order = response.json()
                    drinks_amount = order['total_price']
                    self.log_test("Create Drinks for Payment", True, f"Created drinks order: €{drinks_amount:.2f}")
                    
        except Exception as e:
            self.log_test("Create Orders for Payment", False, f"Exception: {str(e)}")

        # Get current employee balance
        current_breakfast_balance = 0
        current_drinks_balance = 0
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            if response.status_code == 200:
                profile = response.json()
                current_breakfast_balance = profile.get('breakfast_total', 0)
                current_drinks_balance = profile.get('drinks_sweets_total', 0)
                self.log_test("Get Current Balances", True, 
                            f"Breakfast: €{current_breakfast_balance:.2f}, Drinks/Sweets: €{current_drinks_balance:.2f}")
                success_count += 1
        except Exception as e:
            self.log_test("Get Current Balances", False, f"Exception: {str(e)}")

        # Test breakfast payment processing
        if current_breakfast_balance > 0:
            try:
                payment_data = {
                    "payment_type": "breakfast",
                    "amount": current_breakfast_balance,
                    "admin_department": test_dept['name']
                }
                
                response = self.session.post(f"{API_BASE}/department-admin/payment/{test_employee['id']}", 
                                           params=payment_data)
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("Breakfast Payment", True, f"Response: {result.get('message', 'Success')}")
                    success_count += 1
                    
                    # Verify balance is reset
                    profile_response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
                    if profile_response.status_code == 200:
                        profile = profile_response.json()
                        new_breakfast_balance = profile.get('breakfast_total', 0)
                        if new_breakfast_balance == 0:
                            self.log_test("Breakfast Balance Reset", True, "Balance reset to €0.00")
                            success_count += 1
                        else:
                            self.log_test("Breakfast Balance Reset", False, f"Balance not reset: €{new_breakfast_balance:.2f}")
                            
                else:
                    self.log_test("Breakfast Payment", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Breakfast Payment", False, f"Exception: {str(e)}")

        # Test drinks/sweets payment processing
        if current_drinks_balance > 0:
            try:
                payment_data = {
                    "payment_type": "drinks_sweets",
                    "amount": current_drinks_balance,
                    "admin_department": test_dept['name']
                }
                
                response = self.session.post(f"{API_BASE}/department-admin/payment/{test_employee['id']}", 
                                           params=payment_data)
                
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("Drinks/Sweets Payment", True, f"Response: {result.get('message', 'Success')}")
                    success_count += 1
                    
                    # Verify balance is reset
                    profile_response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
                    if profile_response.status_code == 200:
                        profile = profile_response.json()
                        new_drinks_balance = profile.get('drinks_sweets_total', 0)
                        if new_drinks_balance == 0:
                            self.log_test("Drinks/Sweets Balance Reset", True, "Balance reset to €0.00")
                            success_count += 1
                        else:
                            self.log_test("Drinks/Sweets Balance Reset", False, f"Balance not reset: €{new_drinks_balance:.2f}")
                            
                else:
                    self.log_test("Drinks/Sweets Payment", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Drinks/Sweets Payment", False, f"Exception: {str(e)}")

        # Test payment logs
        try:
            response = self.session.get(f"{API_BASE}/department-admin/payment-logs/{test_employee['id']}")
            
            if response.status_code == 200:
                logs = response.json()
                if isinstance(logs, list) and len(logs) > 0:
                    self.log_test("Payment Logs", True, f"Found {len(logs)} payment log entries")
                    success_count += 1
                else:
                    self.log_test("Payment Logs", False, "No payment logs found")
            else:
                self.log_test("Payment Logs", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Payment Logs", False, f"Exception: {str(e)}")

        return success_count >= 3

    def test_menu_price_integration(self):
        """Test 5: Menu Price Integration - Verify menu prices affect order calculations"""
        print("\n=== Testing Menu Price Integration ===")
        
        if not self.employees or not self.menu_items['breakfast']:
            self.log_test("Menu Price Integration", False, "Missing test data")
            return False

        success_count = 0
        test_employee = self.employees[0]

        # Get current breakfast menu
        try:
            response = self.session.get(f"{API_BASE}/menu/breakfast")
            if response.status_code == 200:
                breakfast_menu = response.json()
                self.log_test("Get Breakfast Menu", True, f"Retrieved {len(breakfast_menu)} breakfast items")
                success_count += 1
                
                # Verify menu has current prices
                for item in breakfast_menu:
                    if 'price' in item and item['price'] >= 0:
                        self.log_test(f"Menu Price {item['roll_type']}", True, f"€{item['price']:.2f}")
                    else:
                        self.log_test(f"Menu Price {item['roll_type']}", False, "Invalid price")
                        
            else:
                self.log_test("Get Breakfast Menu", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Get Breakfast Menu", False, f"Exception: {str(e)}")
            return False

        # Test that menu price updates affect order calculations
        if breakfast_menu:
            try:
                # Find a breakfast item to update
                test_item = breakfast_menu[0]
                original_price = test_item['price']
                new_price = original_price + 0.25
                
                # Update the menu item price
                update_data = {"price": new_price}
                response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{test_item['id']}", 
                                          json=update_data)
                
                if response.status_code == 200:
                    self.log_test("Update Menu Price", True, f"Updated {test_item['roll_type']} from €{original_price:.2f} to €{new_price:.2f}")
                    success_count += 1
                    
                    # Create an order with the updated item
                    order_data = {
                        "employee_id": test_employee['id'],
                        "department_id": test_employee['department_id'],
                        "order_type": "breakfast",
                        "breakfast_items": [
                            {
                                "total_halves": 2,
                                "white_halves": 2 if test_item['roll_type'] == 'weiss' else 0,
                                "seeded_halves": 2 if test_item['roll_type'] == 'koerner' else 0,
                                "toppings": ["ruehrei", "kaese"],
                                "has_lunch": False
                            }
                        ]
                    }
                    
                    response = self.session.post(f"{API_BASE}/orders", json=order_data)
                    
                    if response.status_code == 200:
                        order = response.json()
                        expected_price = 2 * new_price  # 2 halves * new price + free toppings
                        actual_price = order['total_price']
                        
                        if abs(actual_price - expected_price) < 0.01:
                            self.log_test("Updated Price in Order", True, 
                                        f"Order uses updated price: €{actual_price:.2f}")
                            success_count += 1
                        else:
                            self.log_test("Updated Price in Order", False, 
                                        f"Expected: €{expected_price:.2f}, Actual: €{actual_price:.2f}")
                    else:
                        self.log_test("Create Order with Updated Price", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
                else:
                    self.log_test("Update Menu Price", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Menu Price Update Test", False, f"Exception: {str(e)}")

        # Test toppings are free
        try:
            response = self.session.get(f"{API_BASE}/menu/toppings")
            if response.status_code == 200:
                toppings_menu = response.json()
                all_free = all(item['price'] == 0.0 for item in toppings_menu)
                
                if all_free:
                    self.log_test("Free Toppings Verification", True, "All toppings are free (€0.00)")
                    success_count += 1
                else:
                    paid_toppings = [item for item in toppings_menu if item['price'] > 0]
                    self.log_test("Free Toppings Verification", False, 
                                f"Found {len(paid_toppings)} paid toppings")
                    
        except Exception as e:
            self.log_test("Free Toppings Verification", False, f"Exception: {str(e)}")

        return success_count >= 3

    def run_all_tests(self):
        """Run all bug fix tests"""
        print("🧪 Starting Bug Fix Test Suite for German Canteen Management System")
        print("=" * 80)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Exiting.")
            return False

        # Run all tests
        test_methods = [
            self.test_price_calculation_fix,
            self.test_employee_deletion,
            self.test_employee_profile_history,
            self.test_payment_processing,
            self.test_menu_price_integration
        ]

        passed_tests = 0
        total_tests = len(test_methods)

        for test_method in test_methods:
            try:
                if test_method():
                    passed_tests += 1
            except Exception as e:
                print(f"❌ Test {test_method.__name__} failed with exception: {str(e)}")

        # Print summary
        print("\n" + "=" * 80)
        print("🎯 BUG FIX TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print individual test results
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")

        print("=" * 80)
        
        return passed_tests >= (total_tests * 0.8)  # 80% pass rate required

if __name__ == "__main__":
    tester = BugFixTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)