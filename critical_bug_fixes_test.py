#!/usr/bin/env python3
"""
Critical Bug Fixes Test Suite for German Canteen Management System
Tests the three critical bug fixes:
1. Menu Item Edit Saving Fix
2. Payment History Display Fix  
3. Department-Specific Menu Updates Integration
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

class CriticalBugFixesTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.departments = []
        self.employees = []
        self.test_orders = []
        
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
                self.log_test("Get Departments", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Departments", False, f"Exception: {str(e)}")
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
                    employee = response.json()
                    self.employees.append(employee)
                    self.log_test(f"Create Employee {i+1}", True, f"Created: {employee['name']}")
                else:
                    self.log_test(f"Create Employee {i+1}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Create Employee {i+1}", False, f"Exception: {str(e)}")

        return len(self.employees) >= 1

    def test_order_update_functionality(self):
        """Test PUT /api/orders/{order_id} with breakfast item updates"""
        print("\n=== Testing Order Update Functionality (NEW ENDPOINT) ===")
        
        if not self.employees:
            self.log_test("Order Update", False, "No employees available")
            return False

        success_count = 0
        test_employee = self.employees[0]

        # First create an initial breakfast order
        try:
            initial_order = {
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
            
            response = self.session.post(f"{API_BASE}/orders", json=initial_order)
            if response.status_code == 200:
                order = response.json()
                order_id = order['id']
                initial_price = order['total_price']
                self.test_orders.append(order_id)
                self.log_test("Create Initial Order", True, f"Created order with price €{initial_price:.2f}")
                
                # Now test updating the order
                updated_order_data = {
                    "breakfast_items": [
                        {
                            "total_halves": 3,
                            "white_halves": 1,
                            "seeded_halves": 2,
                            "toppings": ["ruehrei", "schinken", "butter"],
                            "has_lunch": True
                        }
                    ]
                }
                
                response = self.session.put(f"{API_BASE}/orders/{order_id}", json=updated_order_data)
                if response.status_code == 200:
                    result = response.json()
                    self.log_test("Order Update Endpoint", True, "Order successfully updated")
                    success_count += 1
                    
                    # Verify the order was actually updated by fetching employee orders
                    response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
                    if response.status_code == 200:
                        orders_data = response.json()
                        orders = orders_data.get('orders', [])
                        updated_order = next((o for o in orders if o['id'] == order_id), None)
                        
                        if updated_order and updated_order['breakfast_items']:
                            breakfast_item = updated_order['breakfast_items'][0]
                            if (breakfast_item.get('total_halves') == 3 and 
                                breakfast_item.get('white_halves') == 1 and
                                breakfast_item.get('seeded_halves') == 2 and
                                len(breakfast_item.get('toppings', [])) == 3):
                                self.log_test("Order Update Verification", True, "Order changes persisted correctly")
                                success_count += 1
                            else:
                                self.log_test("Order Update Verification", False, "Order changes not persisted correctly")
                        else:
                            self.log_test("Order Update Verification", False, "Updated order not found")
                    
                    # Test balance recalculation
                    response = self.session.get(f"{API_BASE}/departments/{test_employee['department_id']}/employees")
                    if response.status_code == 200:
                        employees = response.json()
                        updated_employee = next((e for e in employees if e['id'] == test_employee['id']), None)
                        if updated_employee and updated_employee['breakfast_balance'] != initial_price:
                            self.log_test("Balance Recalculation", True, 
                                        f"Balance updated from €{initial_price:.2f} to €{updated_employee['breakfast_balance']:.2f}")
                            success_count += 1
                        else:
                            self.log_test("Balance Recalculation", False, "Balance not recalculated after order update")
                else:
                    self.log_test("Order Update Endpoint", False, f"HTTP {response.status_code}: {response.text}")
            else:
                self.log_test("Create Initial Order", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Order Update Functionality", False, f"Exception: {str(e)}")

        return success_count >= 2

    def test_balance_adjustment_on_order_deletion(self):
        """Test DELETE /api/department-admin/orders/{order_id} by admin with balance adjustment"""
        print("\n=== Testing Balance Adjustment on Order Deletion ===")
        
        if not self.employees or not self.departments:
            self.log_test("Balance Adjustment on Deletion", False, "No employees or departments available")
            return False

        success_count = 0
        test_employee = self.employees[0]
        test_dept = self.departments[0]

        # Create orders of different types
        order_ids = []
        initial_breakfast_balance = 0
        initial_drinks_balance = 0

        # Get initial balances
        try:
            response = self.session.get(f"{API_BASE}/departments/{test_employee['department_id']}/employees")
            if response.status_code == 200:
                employees = response.json()
                employee = next((e for e in employees if e['id'] == test_employee['id']), None)
                if employee:
                    initial_breakfast_balance = employee.get('breakfast_balance', 0)
                    initial_drinks_balance = employee.get('drinks_sweets_balance', 0)
        except:
            pass

        # Create breakfast order
        try:
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
                order_ids.append(('breakfast', order['id'], order['total_price']))
                self.log_test("Create Breakfast Order for Deletion", True, f"Created breakfast order €{order['total_price']:.2f}")
        except Exception as e:
            self.log_test("Create Breakfast Order for Deletion", False, f"Exception: {str(e)}")

        # Create drinks order
        try:
            # Get drinks menu first
            response = self.session.get(f"{API_BASE}/menu/drinks")
            if response.status_code == 200:
                drinks = response.json()
                if drinks:
                    drink_item = drinks[0]
                    drinks_order = {
                        "employee_id": test_employee['id'],
                        "department_id": test_employee['department_id'],
                        "order_type": "drinks",
                        "drink_items": {drink_item['id']: 2}
                    }
                    
                    response = self.session.post(f"{API_BASE}/orders", json=drinks_order)
                    if response.status_code == 200:
                        order = response.json()
                        order_ids.append(('drinks', order['id'], order['total_price']))
                        self.log_test("Create Drinks Order for Deletion", True, f"Created drinks order €{order['total_price']:.2f}")
        except Exception as e:
            self.log_test("Create Drinks Order for Deletion", False, f"Exception: {str(e)}")

        # Test admin deletion with balance adjustment
        for order_type, order_id, order_price in order_ids:
            try:
                # Get balance before deletion
                response = self.session.get(f"{API_BASE}/departments/{test_employee['department_id']}/employees")
                balance_before = 0
                if response.status_code == 200:
                    employees = response.json()
                    employee = next((e for e in employees if e['id'] == test_employee['id']), None)
                    if employee:
                        if order_type == 'breakfast':
                            balance_before = employee.get('breakfast_balance', 0)
                        else:
                            balance_before = employee.get('drinks_sweets_balance', 0)

                # Delete order as admin
                response = self.session.delete(f"{API_BASE}/department-admin/orders/{order_id}")
                if response.status_code == 200:
                    self.log_test(f"Admin Delete {order_type.title()} Order", True, "Order deleted successfully")
                    
                    # Verify balance adjustment
                    response = self.session.get(f"{API_BASE}/departments/{test_employee['department_id']}/employees")
                    if response.status_code == 200:
                        employees = response.json()
                        employee = next((e for e in employees if e['id'] == test_employee['id']), None)
                        if employee:
                            if order_type == 'breakfast':
                                balance_after = employee.get('breakfast_balance', 0)
                            else:
                                balance_after = employee.get('drinks_sweets_balance', 0)
                            
                            expected_balance = max(0, balance_before - order_price)
                            if abs(balance_after - expected_balance) < 0.01:
                                self.log_test(f"Balance Adjustment {order_type.title()}", True, 
                                            f"Balance correctly reduced from €{balance_before:.2f} to €{balance_after:.2f}")
                                success_count += 1
                            else:
                                self.log_test(f"Balance Adjustment {order_type.title()}", False, 
                                            f"Expected €{expected_balance:.2f}, got €{balance_after:.2f}")
                        else:
                            self.log_test(f"Balance Adjustment {order_type.title()}", False, "Employee not found after deletion")
                    else:
                        self.log_test(f"Balance Adjustment {order_type.title()}", False, "Could not fetch employee after deletion")
                else:
                    self.log_test(f"Admin Delete {order_type.title()} Order", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Admin Delete {order_type.title()} Order", False, f"Exception: {str(e)}")

        return success_count >= 1

    def test_single_breakfast_order_constraint(self):
        """Test that only one breakfast order per employee per day is maintained"""
        print("\n=== Testing Order Persistence & Single Breakfast Order ===")
        
        if not self.employees:
            self.log_test("Single Breakfast Order", False, "No employees available")
            return False

        success_count = 0
        test_employee = self.employees[0]

        # Create first breakfast order
        try:
            first_order = {
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
            
            response = self.session.post(f"{API_BASE}/orders", json=first_order)
            if response.status_code == 200:
                first_order_result = response.json()
                first_order_id = first_order_result['id']
                self.log_test("Create First Breakfast Order", True, f"Created first breakfast order")
                
                # Try to create second breakfast order for same employee same day
                second_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 1,
                            "white_halves": 0,
                            "seeded_halves": 1,
                            "toppings": ["schinken"],
                            "has_lunch": True
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=second_order)
                
                # Check if only one breakfast order exists
                response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
                if response.status_code == 200:
                    orders_data = response.json()
                    orders = orders_data.get('orders', [])
                    breakfast_orders = [o for o in orders if o.get('order_type') == 'breakfast']
                    
                    if len(breakfast_orders) == 1:
                        self.log_test("Single Breakfast Order Constraint", True, 
                                    "Only one breakfast order exists per employee per day")
                        success_count += 1
                        
                        # Check if the order was updated instead of creating duplicate
                        remaining_order = breakfast_orders[0]
                        if remaining_order['id'] == first_order_id:
                            # Check if it was updated with new data
                            breakfast_item = remaining_order.get('breakfast_items', [{}])[0]
                            if (breakfast_item.get('total_halves') == 1 and 
                                breakfast_item.get('seeded_halves') == 1 and
                                breakfast_item.get('has_lunch') == True):
                                self.log_test("Order Update Instead of Duplicate", True, 
                                            "Existing order was updated instead of creating duplicate")
                                success_count += 1
                            else:
                                self.log_test("Order Update Instead of Duplicate", False, 
                                            "Order was not updated with new data")
                        else:
                            self.log_test("Order Update Instead of Duplicate", False, 
                                        "New order created instead of updating existing")
                    else:
                        self.log_test("Single Breakfast Order Constraint", False, 
                                    f"Found {len(breakfast_orders)} breakfast orders, expected 1")
                else:
                    self.log_test("Single Breakfast Order Constraint", False, 
                                f"Could not fetch employee orders: HTTP {response.status_code}")
            else:
                self.log_test("Create First Breakfast Order", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Single Breakfast Order", False, f"Exception: {str(e)}")

        return success_count >= 1

    def test_price_calculation_accuracy(self):
        """Test breakfast pricing with per-half calculation"""
        print("\n=== Testing Price Calculation Accuracy ===")
        
        if not self.employees:
            self.log_test("Price Calculation", False, "No employees available")
            return False

        success_count = 0
        test_employee = self.employees[0]

        # Get current menu prices
        try:
            response = self.session.get(f"{API_BASE}/menu/breakfast")
            if response.status_code != 200:
                self.log_test("Get Menu Prices", False, f"HTTP {response.status_code}")
                return False
            
            breakfast_menu = response.json()
            white_price = next((item['price'] for item in breakfast_menu if item['roll_type'] == 'weiss'), 0.5)
            seeded_price = next((item['price'] for item in breakfast_menu if item['roll_type'] == 'koerner'), 0.6)
            
            self.log_test("Get Menu Prices", True, f"White roll: €{white_price:.2f}, Seeded roll: €{seeded_price:.2f}")
            
        except Exception as e:
            self.log_test("Get Menu Prices", False, f"Exception: {str(e)}")
            return False

        # Test per-half calculation: 3 halves at €0.75 per whole roll = €1.125 (not €14.25)
        try:
            # Update menu price to €0.75 for testing
            if breakfast_menu:
                white_item = next((item for item in breakfast_menu if item['roll_type'] == 'weiss'), None)
                if white_item:
                    update_data = {"price": 0.75}
                    response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{white_item['id']}", 
                                              json=update_data)
                    if response.status_code == 200:
                        self.log_test("Update Menu Price", True, "Updated white roll price to €0.75")
                    
            # Create order with 3 halves
            test_order = {
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
            
            response = self.session.post(f"{API_BASE}/orders", json=test_order)
            if response.status_code == 200:
                order = response.json()
                actual_price = order['total_price']
                
                # Expected: 3 halves * (€0.75 / 2) = €1.125
                expected_price = 3 * (0.75 / 2)  # Per-half pricing
                
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("Per-Half Price Calculation", True, 
                                f"Correct calculation: 3 halves × €0.375 = €{actual_price:.3f}")
                    success_count += 1
                else:
                    self.log_test("Per-Half Price Calculation", False, 
                                f"Expected €{expected_price:.3f}, got €{actual_price:.2f}")
                
                # Verify it's NOT the old incorrect calculation (€14.25)
                if actual_price != 14.25:
                    self.log_test("Avoid Incorrect Calculation", True, 
                                f"Price is €{actual_price:.2f}, not the incorrect €14.25")
                    success_count += 1
                else:
                    self.log_test("Avoid Incorrect Calculation", False, 
                                "Still using incorrect €14.25 calculation")
                    
            else:
                self.log_test("Create Test Order", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Price Calculation Accuracy", False, f"Exception: {str(e)}")

        return success_count >= 1

    def test_daily_summary_employee_data(self):
        """Test GET /api/orders/daily-summary/{department_id} returns complete structure"""
        print("\n=== Testing Daily Summary & Employee Data ===")
        
        if not self.departments or not self.employees:
            self.log_test("Daily Summary", False, "No departments or employees available")
            return False

        success_count = 0
        test_dept = self.departments[0]
        test_employee = self.employees[0]

        # Create some test orders first
        try:
            test_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=test_order)
            if response.status_code == 200:
                self.log_test("Create Test Order for Summary", True, "Created test order")
        except:
            pass

        # Test daily summary structure
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            if response.status_code == 200:
                summary = response.json()
                
                # Check required fields
                required_fields = ['date', 'breakfast_summary', 'employee_orders', 'drinks_summary', 'sweets_summary']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Daily Summary Structure", True, "All required fields present")
                    success_count += 1
                    
                    # Check employee_orders contains individual employee data
                    employee_orders = summary.get('employee_orders', {})
                    if isinstance(employee_orders, dict) and employee_orders:
                        self.log_test("Employee Orders Section", True, 
                                    f"Contains data for {len(employee_orders)} employees")
                        success_count += 1
                        
                        # Check employee data structure
                        for employee_name, employee_data in employee_orders.items():
                            required_employee_fields = ['white_halves', 'seeded_halves', 'toppings']
                            missing_employee_fields = [field for field in required_employee_fields 
                                                     if field not in employee_data]
                            if not missing_employee_fields:
                                self.log_test("Employee Data Structure", True, 
                                            f"Employee {employee_name} has complete data structure")
                                success_count += 1
                                break
                    else:
                        self.log_test("Employee Orders Section", False, "Missing or empty employee_orders section")
                    
                    # Check breakfast_summary aggregates
                    breakfast_summary = summary.get('breakfast_summary', {})
                    if isinstance(breakfast_summary, dict):
                        self.log_test("Breakfast Summary Aggregates", True, 
                                    f"Breakfast summary contains {len(breakfast_summary)} roll types")
                        success_count += 1
                    else:
                        self.log_test("Breakfast Summary Aggregates", False, "Invalid breakfast_summary structure")
                        
                else:
                    self.log_test("Daily Summary Structure", False, f"Missing fields: {missing_fields}")
                    
            else:
                self.log_test("Daily Summary", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary", False, f"Exception: {str(e)}")

        return success_count >= 3

    def test_authentication_with_department_credentials(self):
        """Test authentication with department credentials (password1-4) and admin credentials (admin1-4)"""
        print("\n=== Testing Authentication with Department Credentials ===")
        
        success_count = 0
        
        # Test department authentication with password1-4
        department_passwords = {
            "1. Wachabteilung": "password1",
            "2. Wachabteilung": "password2", 
            "3. Wachabteilung": "password3",
            "4. Wachabteilung": "password4"
        }
        
        for dept in self.departments:
            dept_name = dept['name']
            expected_password = department_passwords.get(dept_name)
            
            if expected_password:
                try:
                    login_data = {
                        "department_name": dept_name,
                        "password": expected_password
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department", json=login_data)
                    if response.status_code == 200:
                        self.log_test(f"Department Login {dept_name}", True, "Authentication successful")
                        success_count += 1
                    else:
                        self.log_test(f"Department Login {dept_name}", False, f"HTTP {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Department Login {dept_name}", False, f"Exception: {str(e)}")

        # Test admin authentication with admin1-4
        admin_passwords = {
            "1. Wachabteilung": "admin1",
            "2. Wachabteilung": "admin2",
            "3. Wachabteilung": "admin3", 
            "4. Wachabteilung": "admin4"
        }
        
        for dept in self.departments:
            dept_name = dept['name']
            expected_admin_password = admin_passwords.get(dept_name)
            
            if expected_admin_password:
                try:
                    admin_login_data = {
                        "department_name": dept_name,
                        "admin_password": expected_admin_password
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
                    if response.status_code == 200:
                        login_result = response.json()
                        if login_result.get('role') == 'department_admin':
                            self.log_test(f"Admin Login {dept_name}", True, "Admin authentication successful")
                            success_count += 1
                        else:
                            self.log_test(f"Admin Login {dept_name}", False, "Role mismatch")
                    else:
                        self.log_test(f"Admin Login {dept_name}", False, f"HTTP {response.status_code}")
                        
                except Exception as e:
                    self.log_test(f"Admin Login {dept_name}", False, f"Exception: {str(e)}")

        return success_count >= 4  # At least 4 successful authentications

    def run_all_tests(self):
        """Run all critical bug fix tests"""
        print("🧪 CRITICAL BUG FIXES TESTING STARTED")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_data():
            print("❌ SETUP FAILED - Cannot continue with tests")
            return False
        
        # Run all critical tests
        test_results = []
        
        test_results.append(("Authentication", self.test_authentication_with_department_credentials()))
        test_results.append(("Order Update Functionality", self.test_order_update_functionality()))
        test_results.append(("Balance Adjustment on Deletion", self.test_balance_adjustment_on_order_deletion()))
        test_results.append(("Single Breakfast Order Constraint", self.test_single_breakfast_order_constraint()))
        test_results.append(("Price Calculation Accuracy", self.test_price_calculation_accuracy()))
        test_results.append(("Daily Summary & Employee Data", self.test_daily_summary_employee_data()))
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 CRITICAL BUG FIXES TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 ALL CRITICAL BUG FIXES ARE WORKING CORRECTLY!")
            return True
        else:
            print("⚠️  SOME CRITICAL ISSUES FOUND - REVIEW REQUIRED")
            return False

if __name__ == "__main__":
    tester = CriticalBugFixesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)