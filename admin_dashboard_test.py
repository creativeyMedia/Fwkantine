#!/usr/bin/env python3
"""
Admin Dashboard Order Management Test Suite
Tests admin dashboard order management functionality for the German Canteen Management System
Focus on: Employee Orders Retrieval, Order Deletion by Admin, Payment History Integration
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

class AdminDashboardTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.departments = []
        self.employees = []
        self.test_orders = []
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
    
    def setup_test_environment(self):
        """Setup test environment with departments, employees, and orders"""
        print("\n=== Setting Up Test Environment ===")
        
        # Initialize data
        try:
            response = self.session.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.log_test("Data Initialization", True, "Test environment initialized")
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
        if self.departments:
            test_dept = self.departments[0]  # Use first department
            for i in range(3):  # Create 3 test employees
                try:
                    employee_data = {
                        "name": f"Test Employee {i+1}",
                        "department_id": test_dept['id']
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
        
        # Authenticate as department admin (using password1/admin1 as specified)
        if self.departments:
            try:
                admin_login_data = {
                    "department_name": self.departments[0]['name'],
                    "admin_password": "admin1"
                }
                response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
                if response.status_code == 200:
                    self.admin_auth = response.json()
                    self.log_test("Admin Authentication", True, f"Authenticated as admin for {self.admin_auth['department_name']}")
                else:
                    self.log_test("Admin Authentication", False, f"HTTP {response.status_code}: {response.text}")
                    return False
            except Exception as e:
                self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
                return False
        
        return len(self.departments) > 0 and len(self.employees) > 0 and self.admin_auth is not None
    
    def create_test_orders(self):
        """Create test orders of different types (breakfast, drinks, sweets)"""
        print("\n=== Creating Test Orders ===")
        
        if not self.employees:
            self.log_test("Create Test Orders", False, "No employees available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Get menu items first
        breakfast_menu = []
        drinks_menu = []
        sweets_menu = []
        
        try:
            # Get breakfast menu
            response = self.session.get(f"{API_BASE}/menu/breakfast/{test_employee['department_id']}")
            if response.status_code == 200:
                breakfast_menu = response.json()
            
            # Get drinks menu
            response = self.session.get(f"{API_BASE}/menu/drinks/{test_employee['department_id']}")
            if response.status_code == 200:
                drinks_menu = response.json()
            
            # Get sweets menu
            response = self.session.get(f"{API_BASE}/menu/sweets/{test_employee['department_id']}")
            if response.status_code == 200:
                sweets_menu = response.json()
                
        except Exception as e:
            self.log_test("Get Menu Items", False, f"Exception: {str(e)}")
            return False
        
        # Create breakfast order with new format
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
                        "has_lunch": True,
                        "boiled_eggs": 2
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                order = response.json()
                self.test_orders.append(order)
                self.log_test("Create Breakfast Order", True, f"Created breakfast order: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create Breakfast Order", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Breakfast Order", False, f"Exception: {str(e)}")
        
        # Create drinks order
        if drinks_menu:
            try:
                drink_item = drinks_menu[0]
                drinks_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "drinks",
                    "drink_items": {drink_item['id']: 3}
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=drinks_order)
                if response.status_code == 200:
                    order = response.json()
                    self.test_orders.append(order)
                    self.log_test("Create Drinks Order", True, f"Created drinks order: €{order['total_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Create Drinks Order", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Create Drinks Order", False, f"Exception: {str(e)}")
        
        # Create sweets order
        if sweets_menu:
            try:
                sweet_item = sweets_menu[0]
                sweets_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "sweets",
                    "sweet_items": {sweet_item['id']: 2}
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=sweets_order)
                if response.status_code == 200:
                    order = response.json()
                    self.test_orders.append(order)
                    self.log_test("Create Sweets Order", True, f"Created sweets order: €{order['total_price']:.2f}")
                    success_count += 1
                else:
                    self.log_test("Create Sweets Order", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Create Sweets Order", False, f"Exception: {str(e)}")
        
        return success_count >= 2  # At least 2 orders created
    
    def test_employee_orders_retrieval(self):
        """Test GET /api/employees/{employee_id}/orders endpoint"""
        print("\n=== Testing Employee Orders Retrieval ===")
        
        if not self.employees:
            self.log_test("Employee Orders Retrieval", False, "No employees available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                
                # Check response structure
                if 'orders' in orders_data and isinstance(orders_data['orders'], list):
                    orders = orders_data['orders']
                    self.log_test("Orders Response Structure", True, f"Correct structure with {len(orders)} orders")
                    success_count += 1
                    
                    # Check if all order types are present
                    order_types = set(order.get('order_type') for order in orders)
                    expected_types = {'breakfast', 'drinks', 'sweets'}
                    found_types = order_types.intersection(expected_types)
                    
                    if len(found_types) >= 2:  # At least 2 order types
                        self.log_test("All Order Types Present", True, f"Found order types: {list(found_types)}")
                        success_count += 1
                    else:
                        self.log_test("All Order Types Present", False, f"Only found: {list(found_types)}")
                    
                    # Check data structure for each order type
                    for order in orders:
                        order_type = order.get('order_type')
                        
                        if order_type == 'breakfast':
                            if 'breakfast_items' in order and order['breakfast_items']:
                                breakfast_item = order['breakfast_items'][0]
                                required_fields = ['total_halves', 'white_halves', 'seeded_halves', 'toppings']
                                if all(field in breakfast_item for field in required_fields):
                                    self.log_test("Breakfast Order Structure", True, "Proper breakfast order structure")
                                    success_count += 1
                                    break
                        
                        elif order_type == 'drinks':
                            if 'drink_items' in order and order['drink_items']:
                                self.log_test("Drinks Order Structure", True, "Proper drinks order structure")
                                success_count += 1
                                break
                        
                        elif order_type == 'sweets':
                            if 'sweet_items' in order and order['sweet_items']:
                                self.log_test("Sweets Order Structure", True, "Proper sweets order structure")
                                success_count += 1
                                break
                    
                    # Check timestamp and pricing
                    valid_orders = 0
                    for order in orders:
                        if ('timestamp' in order and 'total_price' in order and 
                            isinstance(order['total_price'], (int, float)) and order['total_price'] >= 0):
                            valid_orders += 1
                    
                    if valid_orders == len(orders):
                        self.log_test("Order Data Integrity", True, f"All {len(orders)} orders have valid timestamps and pricing")
                        success_count += 1
                    else:
                        self.log_test("Order Data Integrity", False, f"Only {valid_orders}/{len(orders)} orders have valid data")
                        
                else:
                    self.log_test("Orders Response Structure", False, "Invalid response structure")
                    
            else:
                self.log_test("Employee Orders Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Employee Orders Retrieval", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_admin_order_deletion(self):
        """Test DELETE /api/department-admin/orders/{order_id} endpoint"""
        print("\n=== Testing Admin Order Deletion ===")
        
        if not self.test_orders or not self.admin_auth:
            self.log_test("Admin Order Deletion", False, "No test orders or admin auth available")
            return False
        
        success_count = 0
        test_order = self.test_orders[0]  # Use first test order
        
        # Get employee balance before deletion
        employee_id = test_order['employee_id']
        original_balance = None
        
        try:
            response = self.session.get(f"{API_BASE}/employees/{employee_id}/profile")
            if response.status_code == 200:
                profile = response.json()
                if test_order['order_type'] == 'breakfast':
                    original_balance = profile['breakfast_total']
                else:
                    original_balance = profile['drinks_sweets_total']
                self.log_test("Get Original Balance", True, f"Original balance: €{original_balance:.2f}")
        except Exception as e:
            self.log_test("Get Original Balance", False, f"Exception: {str(e)}")
        
        # Test order deletion by admin
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/orders/{test_order['id']}")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Admin Delete Order", True, f"Successfully deleted order: {result.get('message', 'Success')}")
                success_count += 1
                
                # Verify order is actually deleted
                try:
                    response = self.session.get(f"{API_BASE}/employees/{employee_id}/orders")
                    if response.status_code == 200:
                        orders_data = response.json()
                        remaining_orders = orders_data.get('orders', [])
                        
                        # Check if deleted order is no longer in the list
                        deleted_order_found = any(order['id'] == test_order['id'] for order in remaining_orders)
                        
                        if not deleted_order_found:
                            self.log_test("Order Deletion Verification", True, "Order successfully removed from employee orders")
                            success_count += 1
                        else:
                            self.log_test("Order Deletion Verification", False, "Order still exists in employee orders")
                            
                except Exception as e:
                    self.log_test("Order Deletion Verification", False, f"Exception: {str(e)}")
                
                # Verify balance adjustment
                if original_balance is not None:
                    try:
                        response = self.session.get(f"{API_BASE}/employees/{employee_id}/profile")
                        if response.status_code == 200:
                            profile = response.json()
                            if test_order['order_type'] == 'breakfast':
                                new_balance = profile['breakfast_total']
                            else:
                                new_balance = profile['drinks_sweets_total']
                            
                            expected_balance = max(0, original_balance - test_order['total_price'])
                            if abs(new_balance - expected_balance) < 0.01:
                                self.log_test("Balance Adjustment", True, f"Balance correctly adjusted: €{original_balance:.2f} → €{new_balance:.2f}")
                                success_count += 1
                            else:
                                self.log_test("Balance Adjustment", False, f"Balance mismatch: expected €{expected_balance:.2f}, got €{new_balance:.2f}")
                                
                    except Exception as e:
                        self.log_test("Balance Adjustment", False, f"Exception: {str(e)}")
                        
            else:
                self.log_test("Admin Delete Order", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Delete Order", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_payment_history_integration(self):
        """Test POST /api/department-admin/payment/{employee_id} endpoint"""
        print("\n=== Testing Payment History Integration ===")
        
        if not self.employees or not self.admin_auth:
            self.log_test("Payment History Integration", False, "No employees or admin auth available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Get employee balance before payment
        original_breakfast_balance = None
        original_drinks_balance = None
        
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            if response.status_code == 200:
                profile = response.json()
                original_breakfast_balance = profile['breakfast_total']
                original_drinks_balance = profile['drinks_sweets_total']
                self.log_test("Get Pre-Payment Balances", True, 
                            f"Breakfast: €{original_breakfast_balance:.2f}, Drinks/Sweets: €{original_drinks_balance:.2f}")
        except Exception as e:
            self.log_test("Get Pre-Payment Balances", False, f"Exception: {str(e)}")
        
        # Test marking breakfast payment as paid
        try:
            # Get current breakfast balance to use as payment amount
            payment_amount = original_breakfast_balance if original_breakfast_balance else 0.0
            
            params = {
                "payment_type": "breakfast",
                "amount": payment_amount,
                "admin_department": self.admin_auth['department_name']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/payment/{test_employee['id']}", 
                                       params=params)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Mark Breakfast Payment", True, f"Payment marked: {result.get('message', 'Success')}")
                success_count += 1
                
                # Verify payment log creation
                try:
                    response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
                    if response.status_code == 200:
                        profile = response.json()
                        
                        # Check if payment history exists and has our payment
                        payment_history = profile.get('payment_history', [])
                        if payment_history:
                            latest_payment = payment_history[0]  # Should be most recent
                            
                            if (latest_payment.get('payment_type') == 'breakfast' and
                                latest_payment.get('action') == 'payment' and
                                latest_payment.get('admin_user') == self.admin_auth['department_name']):
                                
                                self.log_test("Payment Log Creation", True, 
                                            f"Payment log created: €{latest_payment.get('amount', 0):.2f} for {latest_payment.get('payment_type')}")
                                success_count += 1
                            else:
                                self.log_test("Payment Log Creation", False, "Payment log data mismatch")
                        else:
                            self.log_test("Payment Log Creation", False, "No payment history found")
                        
                        # Check balance reset
                        new_breakfast_balance = profile['breakfast_total']
                        if new_breakfast_balance == 0.0:
                            self.log_test("Balance Reset After Payment", True, "Breakfast balance reset to €0.00")
                            success_count += 1
                        else:
                            self.log_test("Balance Reset After Payment", False, f"Balance not reset: €{new_breakfast_balance:.2f}")
                            
                except Exception as e:
                    self.log_test("Payment Verification", False, f"Exception: {str(e)}")
                    
            else:
                self.log_test("Mark Breakfast Payment", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Mark Breakfast Payment", False, f"Exception: {str(e)}")
        
        # Test marking drinks/sweets payment as paid
        try:
            # Get current drinks balance to use as payment amount
            payment_amount = original_drinks_balance if original_drinks_balance else 0.0
            
            params = {
                "payment_type": "drinks_sweets",
                "amount": payment_amount,
                "admin_department": self.admin_auth['department_name']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/payment/{test_employee['id']}", 
                                       params=params)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Mark Drinks/Sweets Payment", True, f"Payment marked: {result.get('message', 'Success')}")
                success_count += 1
                
                # Verify drinks/sweets balance reset
                try:
                    response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
                    if response.status_code == 200:
                        profile = response.json()
                        new_drinks_balance = profile['drinks_sweets_total']
                        
                        if new_drinks_balance == 0.0:
                            self.log_test("Drinks Balance Reset", True, "Drinks/sweets balance reset to €0.00")
                            success_count += 1
                        else:
                            self.log_test("Drinks Balance Reset", False, f"Balance not reset: €{new_drinks_balance:.2f}")
                            
                except Exception as e:
                    self.log_test("Drinks Balance Verification", False, f"Exception: {str(e)}")
                    
            else:
                self.log_test("Mark Drinks/Sweets Payment", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Mark Drinks/Sweets Payment", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_payment_history_retrieval(self):
        """Test GET /api/employees/{employee_id}/profile for payment history"""
        print("\n=== Testing Payment History Retrieval ===")
        
        if not self.employees:
            self.log_test("Payment History Retrieval", False, "No employees available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                
                # Check if payment_history field exists
                if 'payment_history' in profile:
                    payment_history = profile['payment_history']
                    self.log_test("Payment History Field Present", True, f"Found payment_history with {len(payment_history)} entries")
                    success_count += 1
                    
                    if payment_history:
                        # Check structure of payment history entries
                        valid_entries = 0
                        for entry in payment_history:
                            required_fields = ['amount', 'payment_type', 'action', 'admin_user', 'timestamp']
                            if all(field in entry for field in required_fields):
                                valid_entries += 1
                        
                        if valid_entries == len(payment_history):
                            self.log_test("Payment History Structure", True, f"All {len(payment_history)} entries have correct structure")
                            success_count += 1
                        else:
                            self.log_test("Payment History Structure", False, f"Only {valid_entries}/{len(payment_history)} entries valid")
                        
                        # Check for both payment types
                        payment_types = set(entry.get('payment_type') for entry in payment_history)
                        expected_types = {'breakfast', 'drinks_sweets'}
                        found_types = payment_types.intersection(expected_types)
                        
                        if len(found_types) >= 1:  # At least one payment type
                            self.log_test("Payment Types Coverage", True, f"Found payment types: {list(found_types)}")
                            success_count += 1
                        else:
                            self.log_test("Payment Types Coverage", False, f"No expected payment types found: {list(payment_types)}")
                        
                        # Check timestamp format and admin user
                        recent_entry = payment_history[0]  # Most recent
                        if ('timestamp' in recent_entry and 
                            'admin_user' in recent_entry and 
                            recent_entry['admin_user'] == self.admin_auth['department_name']):
                            self.log_test("Payment History Details", True, 
                                        f"Recent payment by {recent_entry['admin_user']} at {recent_entry.get('timestamp', 'N/A')}")
                            success_count += 1
                        else:
                            self.log_test("Payment History Details", False, "Invalid payment history details")
                    else:
                        self.log_test("Payment History Content", False, "Payment history is empty")
                else:
                    self.log_test("Payment History Field Present", False, "payment_history field missing from profile")
                    
            else:
                self.log_test("Employee Profile Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Payment History Retrieval", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_frontend_display_readiness(self):
        """Test that data structures support frontend display requirements"""
        print("\n=== Testing Frontend Display Readiness ===")
        
        if not self.employees:
            self.log_test("Frontend Display Readiness", False, "No employees available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Test employee profile data structure for frontend
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                
                # Check all required fields for frontend display
                required_fields = ['employee', 'order_history', 'payment_history', 'total_orders', 'breakfast_total', 'drinks_sweets_total']
                missing_fields = [field for field in required_fields if field not in profile]
                
                if not missing_fields:
                    self.log_test("Profile Display Structure", True, "All required fields present for frontend display")
                    success_count += 1
                else:
                    self.log_test("Profile Display Structure", False, f"Missing fields: {missing_fields}")
                
                # Check order history has readable format
                order_history = profile.get('order_history', [])
                if order_history:
                    readable_orders = 0
                    for order in order_history:
                        if 'readable_items' in order:
                            readable_orders += 1
                    
                    if readable_orders > 0:
                        self.log_test("Order Display Format", True, f"{readable_orders}/{len(order_history)} orders have readable format")
                        success_count += 1
                    else:
                        self.log_test("Order Display Format", False, "No orders have readable format")
                
                # Check employee data completeness
                employee_data = profile.get('employee', {})
                if all(field in employee_data for field in ['id', 'name', 'department_id']):
                    self.log_test("Employee Data Completeness", True, "Employee data complete for display")
                    success_count += 1
                else:
                    self.log_test("Employee Data Completeness", False, "Employee data incomplete")
                    
            else:
                self.log_test("Profile Data Retrieval", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Frontend Display Readiness", False, f"Exception: {str(e)}")
        
        # Test orders endpoint data structure
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get('orders', [])
                
                if orders:
                    # Check if orders have all necessary fields for frontend display
                    complete_orders = 0
                    for order in orders:
                        required_order_fields = ['id', 'order_type', 'total_price', 'timestamp']
                        if all(field in order for field in required_order_fields):
                            complete_orders += 1
                    
                    if complete_orders == len(orders):
                        self.log_test("Orders Display Structure", True, f"All {len(orders)} orders have complete structure")
                        success_count += 1
                    else:
                        self.log_test("Orders Display Structure", False, f"Only {complete_orders}/{len(orders)} orders complete")
                        
            else:
                self.log_test("Orders Data Structure", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Orders Data Structure", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def run_all_tests(self):
        """Run all admin dashboard tests"""
        print("🎯 ADMIN DASHBOARD ORDER MANAGEMENT TESTING")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_environment():
            print("\n❌ SETUP FAILED - Cannot proceed with tests")
            return False
        
        # Create test data
        if not self.create_test_orders():
            print("\n❌ TEST DATA CREATION FAILED - Cannot proceed with tests")
            return False
        
        # Run core tests
        test_results = []
        
        test_results.append(self.test_employee_orders_retrieval())
        test_results.append(self.test_admin_order_deletion())
        test_results.append(self.test_payment_history_integration())
        test_results.append(self.test_payment_history_retrieval())
        test_results.append(self.test_frontend_display_readiness())
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 ADMIN DASHBOARD TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['message']:
                print(f"   {result['message']}")
        
        return all(test_results)

def main():
    """Main test execution"""
    tester = AdminDashboardTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL ADMIN DASHBOARD TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SOME ADMIN DASHBOARD TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()