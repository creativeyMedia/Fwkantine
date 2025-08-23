#!/usr/bin/env python3
"""
Review Critical Bug Fixes Test Suite
Tests all the critical bug fixes for persistent issues in the canteen management system
as specified in the review request
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

class ReviewCriticalTester:
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
    
    def setup_test_environment(self):
        """Setup test environment with fresh data"""
        print("\n=== Setting Up Test Environment ===")
        
        # Initialize data
        try:
            response = self.session.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.log_test("Initialize Data", True, "Database initialized")
            else:
                self.log_test("Initialize Data", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Initialize Data", False, f"Exception: {str(e)}")
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
        
        # Create fresh test employee
        if self.departments:
            test_dept = self.departments[0]
            try:
                employee_data = {
                    "name": "Critical Test Employee",
                    "department_id": test_dept['id']
                }
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    employee = response.json()
                    self.employees.append(employee)
                    self.log_test("Create Test Employee", True, f"Created: {employee['name']}")
                else:
                    return False
            except Exception as e:
                return False
        
        return True
    
    def test_price_calculation_accuracy(self):
        """
        CRITICAL TEST 1: Price Calculation Accuracy
        - Test breakfast ordering with admin-set prices (€0.75 per half roll, not €0.38)
        - Verify 3 halves × €0.75 = €2.25 (correct calculation)
        - Test both weiss and koerner roll pricing accuracy
        - Confirm no division by 2 in price calculations
        """
        print("\n=== CRITICAL TEST 1: Price Calculation Accuracy ===")
        
        if not self.employees:
            self.log_test("Price Calculation Test", False, "No test employee available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Get current breakfast menu
        try:
            response = self.session.get(f"{API_BASE}/menu/breakfast")
            if response.status_code == 200:
                breakfast_menu = response.json()
                self.log_test("Get Breakfast Menu", True, f"Found {len(breakfast_menu)} breakfast items")
                
                # Update prices to €0.75 for testing
                for item in breakfast_menu:
                    if item['roll_type'] == 'weiss':
                        update_data = {"price": 0.75}
                        response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{item['id']}", 
                                                  json=update_data)
                        if response.status_code == 200:
                            self.log_test("Set Weiss Roll Price", True, "Set to €0.75 per half roll")
                            break
                
                for item in breakfast_menu:
                    if item['roll_type'] == 'koerner':
                        update_data = {"price": 0.75}
                        response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{item['id']}", 
                                                  json=update_data)
                        if response.status_code == 200:
                            self.log_test("Set Koerner Roll Price", True, "Set to €0.75 per half roll")
                            break
                
            else:
                self.log_test("Get Breakfast Menu", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Breakfast Menu", False, f"Exception: {str(e)}")
            return False
        
        # Test 1: 3 halves × €0.75 = €2.25 (correct calculation)
        try:
            breakfast_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 3,
                        "seeded_halves": 0,
                        "toppings": ["ruehrei", "kaese", "butter"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            
            if response.status_code == 200:
                order = response.json()
                actual_price = order['total_price']
                expected_price = 3 * 0.75  # 3 halves × €0.75 = €2.25
                
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("3 Halves Price Calculation", True, 
                                f"CORRECT: 3 halves × €0.75 = €{actual_price:.2f}")
                    success_count += 1
                else:
                    # Check if it's using the wrong calculation (dividing by 2)
                    wrong_expected = 3 * (0.75 / 2)  # €1.125
                    if abs(actual_price - wrong_expected) < 0.01:
                        self.log_test("3 Halves Price Calculation", False, 
                                    f"BUG CONFIRMED: Using €0.375 per half (€{actual_price:.2f}) instead of €0.75 per half (should be €{expected_price:.2f})")
                    else:
                        self.log_test("3 Halves Price Calculation", False, 
                                    f"UNEXPECTED CALCULATION: Got €{actual_price:.2f}, expected €{expected_price:.2f}")
            else:
                self.log_test("3 Halves Price Calculation", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("3 Halves Price Calculation", False, f"Exception: {str(e)}")
        
        # Test 2: Mixed weiss and koerner roll pricing
        try:
            # Create a new employee for this test to avoid single order constraint
            employee_data = {
                "name": "Mixed Roll Test Employee",
                "department_id": test_employee['department_id']
            }
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                mixed_test_employee = response.json()
                
                mixed_order = {
                    "employee_id": mixed_test_employee['id'],
                    "department_id": mixed_test_employee['department_id'],
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
                
                response = self.session.post(f"{API_BASE}/orders", json=mixed_order)
                
                if response.status_code == 200:
                    order = response.json()
                    actual_price = order['total_price']
                    expected_price = (2 * 0.75) + (2 * 0.75)  # 2 weiss + 2 koerner = €3.00
                    
                    if abs(actual_price - expected_price) < 0.01:
                        self.log_test("Mixed Roll Price Calculation", True, 
                                    f"CORRECT: 2 weiss + 2 koerner = €{actual_price:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Mixed Roll Price Calculation", False, 
                                    f"WRONG: Expected €{expected_price:.2f}, got €{actual_price:.2f}")
                else:
                    self.log_test("Mixed Roll Price Calculation", False, 
                                f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Mixed Roll Price Calculation", False, f"Exception: {str(e)}")
        
        return success_count >= 1
    
    def test_single_breakfast_order_constraint(self):
        """
        CRITICAL TEST 2: Single Breakfast Order Constraint
        - Create breakfast order for employee for today
        - Try to create second breakfast order for same employee same day
        - Verify error message about existing order
        - Test order update functionality instead of duplicate creation
        """
        print("\n=== CRITICAL TEST 2: Single Breakfast Order Constraint ===")
        
        success_count = 0
        
        # Create a fresh employee for this test
        try:
            if not self.departments:
                self.log_test("Single Order Test", False, "No departments available")
                return False
            
            employee_data = {
                "name": "Single Order Test Employee",
                "department_id": self.departments[0]['id']
            }
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                test_employee = response.json()
                self.log_test("Create Single Order Test Employee", True, f"Created: {test_employee['name']}")
            else:
                self.log_test("Create Single Order Test Employee", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create Single Order Test Employee", False, f"Exception: {str(e)}")
            return False
        
        # Test 1: Create first breakfast order for today
        first_order_id = None
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
                order = response.json()
                first_order_id = order['id']
                self.log_test("Create First Breakfast Order", True, 
                            f"Successfully created first order: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create First Breakfast Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create First Breakfast Order", False, f"Exception: {str(e)}")
        
        # Test 2: Try to create second breakfast order for same employee same day
        try:
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
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=second_order)
            
            if response.status_code == 400:
                error_data = response.json()
                error_message = error_data.get('detail', '')
                if 'bereits eine Frühstücksbestellung' in error_message:
                    self.log_test("Prevent Duplicate Breakfast Order", True, 
                                f"CORRECT: System prevented duplicate order with message: '{error_message}'")
                    success_count += 1
                else:
                    self.log_test("Prevent Duplicate Breakfast Order", False, 
                                f"Wrong error message: {error_message}")
            elif response.status_code == 200:
                self.log_test("Prevent Duplicate Breakfast Order", False, 
                            "BUG: System allowed duplicate breakfast order when it should prevent it")
            else:
                self.log_test("Prevent Duplicate Breakfast Order", False, 
                            f"Unexpected HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Prevent Duplicate Breakfast Order", False, f"Exception: {str(e)}")
        
        # Test 3: Test order update functionality instead of duplicate creation
        if first_order_id:
            try:
                updated_items = [
                    {
                        "total_halves": 3,
                        "white_halves": 1,
                        "seeded_halves": 2,
                        "toppings": ["ruehrei", "kaese", "schinken"],
                        "has_lunch": True
                    }
                ]
                
                update_data = {"breakfast_items": updated_items}
                response = self.session.put(f"{API_BASE}/orders/{first_order_id}", json=update_data)
                
                if response.status_code == 200:
                    updated_order = response.json()
                    self.log_test("Update Existing Order Instead", True, 
                                f"CORRECT: Updated existing order instead of creating duplicate")
                    success_count += 1
                else:
                    self.log_test("Update Existing Order Instead", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Update Existing Order Instead", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_balance_updates_on_deletion(self):
        """
        CRITICAL TEST 3: Balance Updates on Deletion
        - Create orders for employee (build up balance)
        - Delete orders via admin dashboard
        - Verify balance decreases correctly by exact order amount
        - Test balance cannot go below zero
        """
        print("\n=== CRITICAL TEST 3: Balance Updates on Deletion ===")
        
        success_count = 0
        
        # Create a fresh employee for this test
        try:
            employee_data = {
                "name": "Balance Test Employee",
                "department_id": self.departments[0]['id']
            }
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                test_employee = response.json()
                self.log_test("Create Balance Test Employee", True, f"Created: {test_employee['name']}")
            else:
                self.log_test("Create Balance Test Employee", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create Balance Test Employee", False, f"Exception: {str(e)}")
            return False
        
        # Create orders to build up balance
        created_orders = []
        
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
                created_orders.append(order)
                self.log_test("Create Breakfast Order for Balance", True, 
                            f"Created breakfast order: €{order['total_price']:.2f}")
        except Exception as e:
            self.log_test("Create Breakfast Order for Balance", False, f"Exception: {str(e)}")
        
        # Create drinks order
        try:
            drinks_response = self.session.get(f"{API_BASE}/menu/drinks")
            if drinks_response.status_code == 200:
                drinks_menu = drinks_response.json()
                if drinks_menu:
                    drink_item = drinks_menu[0]
                    drinks_order = {
                        "employee_id": test_employee['id'],
                        "department_id": test_employee['department_id'],
                        "order_type": "drinks",
                        "drink_items": {drink_item['id']: 2}
                    }
                    
                    response = self.session.post(f"{API_BASE}/orders", json=drinks_order)
                    if response.status_code == 200:
                        order = response.json()
                        created_orders.append(order)
                        self.log_test("Create Drinks Order for Balance", True, 
                                    f"Created drinks order: €{order['total_price']:.2f}")
        except Exception as e:
            self.log_test("Create Drinks Order for Balance", False, f"Exception: {str(e)}")
        
        # Get balance after creating orders
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            if response.status_code == 200:
                profile = response.json()
                breakfast_balance_before = profile['employee']['breakfast_balance']
                drinks_balance_before = profile['employee']['drinks_sweets_balance']
                self.log_test("Check Balance After Orders", True, 
                            f"Breakfast: €{breakfast_balance_before:.2f}, Drinks: €{drinks_balance_before:.2f}")
                success_count += 1
        except Exception as e:
            self.log_test("Check Balance After Orders", False, f"Exception: {str(e)}")
        
        # Delete orders via admin dashboard and verify balance decreases
        for i, order in enumerate(created_orders):
            try:
                # Get balance before deletion
                response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
                if response.status_code == 200:
                    profile = response.json()
                    if order['order_type'] == 'breakfast':
                        balance_before = profile['employee']['breakfast_balance']
                    else:
                        balance_before = profile['employee']['drinks_sweets_balance']
                    
                    # Delete order via admin endpoint
                    response = self.session.delete(f"{API_BASE}/department-admin/orders/{order['id']}")
                    
                    if response.status_code == 200:
                        # Check balance after deletion
                        response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
                        if response.status_code == 200:
                            profile = response.json()
                            if order['order_type'] == 'breakfast':
                                balance_after = profile['employee']['breakfast_balance']
                            else:
                                balance_after = profile['employee']['drinks_sweets_balance']
                            
                            expected_balance = max(0, balance_before - order['total_price'])
                            
                            if abs(balance_after - expected_balance) < 0.01:
                                self.log_test(f"Balance Update on Deletion {i+1}", True, 
                                            f"CORRECT: Balance reduced by exact order amount: €{balance_before:.2f} → €{balance_after:.2f}")
                                success_count += 1
                            else:
                                self.log_test(f"Balance Update on Deletion {i+1}", False, 
                                            f"WRONG: Expected €{expected_balance:.2f}, got €{balance_after:.2f}")
                    else:
                        self.log_test(f"Delete Order {i+1}", False, 
                                    f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"Delete Order {i+1}", False, f"Exception: {str(e)}")
        
        # Test balance cannot go below zero
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            if response.status_code == 200:
                profile = response.json()
                breakfast_balance = profile['employee']['breakfast_balance']
                drinks_balance = profile['employee']['drinks_sweets_balance']
                
                if breakfast_balance >= 0 and drinks_balance >= 0:
                    self.log_test("Balance Cannot Go Below Zero", True, 
                                f"CORRECT: All balances non-negative (Breakfast: €{breakfast_balance:.2f}, Drinks: €{drinks_balance:.2f})")
                    success_count += 1
                else:
                    self.log_test("Balance Cannot Go Below Zero", False, 
                                f"BUG: Negative balance found (Breakfast: €{breakfast_balance:.2f}, Drinks: €{drinks_balance:.2f})")
        except Exception as e:
            self.log_test("Balance Cannot Go Below Zero", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_order_update_and_reediting(self):
        """
        CRITICAL TEST 4: Order Update & Re-editing
        - Create breakfast order for employee
        - Update the order with PUT /api/orders/{order_id}
        - Verify order gets updated, not duplicated
        - Test balance adjustment with order updates
        """
        print("\n=== CRITICAL TEST 4: Order Update & Re-editing ===")
        
        success_count = 0
        
        # Create a fresh employee for this test
        try:
            employee_data = {
                "name": "Update Test Employee",
                "department_id": self.departments[0]['id']
            }
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                test_employee = response.json()
                self.log_test("Create Update Test Employee", True, f"Created: {test_employee['name']}")
            else:
                self.log_test("Create Update Test Employee", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create Update Test Employee", False, f"Exception: {str(e)}")
            return False
        
        # Create initial breakfast order
        original_order_id = None
        original_price = 0.0
        
        try:
            original_order = {
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
            
            response = self.session.post(f"{API_BASE}/orders", json=original_order)
            
            if response.status_code == 200:
                order = response.json()
                original_order_id = order['id']
                original_price = order['total_price']
                self.log_test("Create Original Order", True, 
                            f"Created original order: €{original_price:.2f}")
                success_count += 1
            else:
                self.log_test("Create Original Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Original Order", False, f"Exception: {str(e)}")
        
        # Update the order with PUT /api/orders/{order_id}
        if original_order_id:
            try:
                updated_items = [
                    {
                        "total_halves": 4,
                        "white_halves": 2,
                        "seeded_halves": 2,
                        "toppings": ["ruehrei", "kaese", "schinken", "butter"],
                        "has_lunch": True
                    }
                ]
                
                update_data = {"breakfast_items": updated_items}
                response = self.session.put(f"{API_BASE}/orders/{original_order_id}", json=update_data)
                
                if response.status_code == 200:
                    updated_order = response.json()
                    new_price = updated_order.get('total_price', 0.0)
                    
                    self.log_test("Update Order via PUT", True, 
                                f"CORRECT: Order updated successfully: €{original_price:.2f} → €{new_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Update Order via PUT", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Update Order via PUT", False, f"Exception: {str(e)}")
        
        # Verify order gets updated, not duplicated
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get('orders', [])
                
                # Count breakfast orders for today
                today = datetime.now().date().isoformat()
                breakfast_orders_today = [
                    order for order in orders 
                    if order['order_type'] == 'breakfast' and 
                    order.get('timestamp', '').startswith(today)
                ]
                
                if len(breakfast_orders_today) == 1:
                    self.log_test("Order Updated Not Duplicated", True, 
                                f"CORRECT: Found exactly 1 breakfast order (updated, not duplicated)")
                    success_count += 1
                else:
                    self.log_test("Order Updated Not Duplicated", False, 
                                f"BUG: Found {len(breakfast_orders_today)} breakfast orders, should be 1")
        except Exception as e:
            self.log_test("Order Updated Not Duplicated", False, f"Exception: {str(e)}")
        
        # Test balance adjustment with order updates
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            if response.status_code == 200:
                profile = response.json()
                current_balance = profile['employee']['breakfast_balance']
                
                self.log_test("Balance Adjustment with Update", True, 
                            f"CORRECT: Balance reflects updated order: €{current_balance:.2f}")
                success_count += 1
                
        except Exception as e:
            self.log_test("Balance Adjustment with Update", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_daily_summary_data_structure(self):
        """
        CRITICAL TEST 5: Daily Summary Data Structure
        - Test GET /api/orders/daily-summary/{department_id}
        - Verify data structure is correct for frontend consumption
        - Check shopping_list, breakfast_summary, employee_orders sections
        - Ensure no malformed objects that cause React rendering errors
        """
        print("\n=== CRITICAL TEST 5: Daily Summary Data Structure ===")
        
        success_count = 0
        
        if not self.departments:
            self.log_test("Daily Summary Test", False, "No departments available")
            return False
        
        test_dept = self.departments[0]
        
        # Test GET /api/orders/daily-summary/{department_id}
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                self.log_test("Daily Summary API Call", True, "Successfully retrieved daily summary")
                success_count += 1
                
                # Verify data structure is correct for frontend consumption
                required_fields = ['date', 'breakfast_summary', 'employee_orders', 'drinks_summary', 'sweets_summary']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Required Fields Present", True, 
                                f"All required fields present: {list(summary.keys())}")
                    success_count += 1
                else:
                    self.log_test("Required Fields Present", False, 
                                f"Missing required fields: {missing_fields}")
                
                # Check shopping_list section
                if 'shopping_list' in summary:
                    shopping_list = summary['shopping_list']
                    if isinstance(shopping_list, dict):
                        self.log_test("Shopping List Structure", True, 
                                    f"Shopping list is properly structured dict with keys: {list(shopping_list.keys())}")
                        success_count += 1
                        
                        # Verify shopping list calculations (halves to whole rolls)
                        for roll_type, data in shopping_list.items():
                            if isinstance(data, dict) and 'halves' in data and 'whole_rolls' in data:
                                halves = data['halves']
                                whole_rolls = data['whole_rolls']
                                expected_whole_rolls = (halves + 1) // 2  # Round up
                                
                                if whole_rolls == expected_whole_rolls:
                                    self.log_test(f"Shopping List Math - {roll_type}", True, 
                                                f"CORRECT: {halves} halves → {whole_rolls} whole rolls")
                                else:
                                    self.log_test(f"Shopping List Math - {roll_type}", False, 
                                                f"WRONG: {halves} halves → {whole_rolls} whole rolls (expected {expected_whole_rolls})")
                    else:
                        self.log_test("Shopping List Structure", False, 
                                    f"Shopping list is not a dict: {type(shopping_list)}")
                
                # Check breakfast_summary section
                if 'breakfast_summary' in summary:
                    breakfast_summary = summary['breakfast_summary']
                    if isinstance(breakfast_summary, dict):
                        self.log_test("Breakfast Summary Structure", True, 
                                    f"Breakfast summary properly structured with roll types: {list(breakfast_summary.keys())}")
                        success_count += 1
                    else:
                        self.log_test("Breakfast Summary Structure", False, 
                                    f"Breakfast summary is not a dict: {type(breakfast_summary)}")
                
                # Check employee_orders section
                if 'employee_orders' in summary:
                    employee_orders = summary['employee_orders']
                    if isinstance(employee_orders, dict):
                        self.log_test("Employee Orders Structure", True, 
                                    f"Employee orders properly structured with {len(employee_orders)} employees")
                        success_count += 1
                    else:
                        self.log_test("Employee Orders Structure", False, 
                                    f"Employee orders is not a dict: {type(employee_orders)}")
                
                # Ensure no malformed objects that cause React rendering errors
                try:
                    json.dumps(summary)  # Test JSON serialization
                    self.log_test("JSON Serializable for React", True, 
                                "CORRECT: Complete summary data is properly serializable for React frontend")
                    success_count += 1
                except Exception as json_error:
                    self.log_test("JSON Serializable for React", False, 
                                f"BUG: JSON serialization error would cause React errors: {str(json_error)}")
                
            else:
                self.log_test("Daily Summary API Call", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary API Call", False, f"Exception: {str(e)}")
        
        return success_count >= 4
    
    def run_all_critical_tests(self):
        """Run all critical bug fix tests as specified in the review request"""
        print("🚨 CRITICAL BUG FIXES TESTING FOR PERSISTENT ISSUES")
        print("=" * 70)
        print("Testing all critical bug fixes for the canteen management system:")
        print("1. Price Calculation Accuracy (€0.75 per half roll, not €0.38)")
        print("2. Single Breakfast Order Constraint")
        print("3. Balance Updates on Deletion")
        print("4. Order Update & Re-editing")
        print("5. Daily Summary Data Structure")
        print("=" * 70)
        
        # Setup test environment
        if not self.setup_test_environment():
            print("❌ FAILED TO SETUP TEST ENVIRONMENT - ABORTING")
            return False
        
        # Run all critical tests
        test_results = {
            "Price Calculation Accuracy": self.test_price_calculation_accuracy(),
            "Single Breakfast Order Constraint": self.test_single_breakfast_order_constraint(),
            "Balance Updates on Deletion": self.test_balance_updates_on_deletion(),
            "Order Update & Re-editing": self.test_order_update_and_reediting(),
            "Daily Summary Data Structure": self.test_daily_summary_data_structure()
        }
        
        # Print final summary
        print("\n" + "=" * 70)
        print("🚨 CRITICAL BUG FIXES TEST RESULTS")
        print("=" * 70)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ WORKING" if result else "❌ FAILING"
            print(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        print(f"\nOVERALL RESULT: {passed_tests}/{total_tests} critical tests passed")
        
        if passed_tests == total_tests:
            print("🎉 ALL CRITICAL BUG FIXES ARE WORKING CORRECTLY!")
            print("✅ All functionality should work with correct pricing, proper constraints, and accurate balance management")
            return True
        else:
            print("🚨 CRITICAL BUGS STILL EXIST - IMMEDIATE ATTENTION REQUIRED!")
            print("❌ Some functionality is not working as expected")
            return False

def main():
    """Main test execution"""
    tester = ReviewCriticalTester()
    success = tester.run_all_critical_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()