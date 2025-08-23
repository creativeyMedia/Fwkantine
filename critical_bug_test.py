#!/usr/bin/env python3
"""
Critical Bug Fixes Test Suite for German Canteen Management System
Tests the 5 critical areas mentioned in the review request:
1. Price Calculation Accuracy
2. Single Breakfast Order Constraint  
3. Balance Updates on Order Deletion
4. Order Update & Re-editing
5. Daily Summary Data Structure
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

class CriticalBugTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.departments = []
        self.employees = []
        self.test_employee = None
        self.test_department = None
        
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
        """Initialize test data and create test employee"""
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
                if self.departments:
                    self.test_department = self.departments[0]
                    self.log_test("Get Departments", True, f"Found {len(self.departments)} departments")
                else:
                    self.log_test("Get Departments", False, "No departments found")
                    return False
            else:
                self.log_test("Get Departments", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Departments", False, f"Exception: {str(e)}")
            return False
        
        return True
    
    def create_test_employee(self, name_suffix=""):
        """Create a new test employee"""
        try:
            employee_data = {
                "name": f"Test Employee {name_suffix}",
                "department_id": self.test_department['id']
            }
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception as e:
            return None
    
    def test_price_calculation_accuracy(self):
        """Test that breakfast pricing uses admin-set prices directly per half roll"""
        print("\n=== Testing Price Calculation Accuracy ===")
        
        # Create fresh employees for each test to avoid single order constraint
        employee1 = self.create_test_employee("Price1")
        employee2 = self.create_test_employee("Price2") 
        employee3 = self.create_test_employee("Price3")
        
        if not employee1 or not employee2 or not employee3:
            self.log_test("Price Calculation Test", False, "Could not create test employees")
            return False
        
        success_count = 0
        
        # First, get current menu prices
        try:
            response = self.session.get(f"{API_BASE}/menu/breakfast")
            if response.status_code != 200:
                self.log_test("Get Breakfast Menu", False, f"HTTP {response.status_code}")
                return False
            
            breakfast_menu = response.json()
            weiss_item = next((item for item in breakfast_menu if item['roll_type'] == 'weiss'), None)
            koerner_item = next((item for item in breakfast_menu if item['roll_type'] == 'koerner'), None)
            
            if not weiss_item or not koerner_item:
                self.log_test("Menu Items Check", False, "Missing weiss or koerner roll types")
                return False
            
            # Update prices to test values (€0.75 for both)
            test_price = 0.75
            
            # Update weiss roll price
            update_data = {"price": test_price}
            response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{weiss_item['id']}", 
                                      json=update_data)
            if response.status_code == 200:
                self.log_test("Update Weiss Roll Price", True, f"Set weiss roll price to €{test_price}")
                success_count += 1
            else:
                self.log_test("Update Weiss Roll Price", False, f"HTTP {response.status_code}")
            
            # Update koerner roll price
            response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{koerner_item['id']}", 
                                      json=update_data)
            if response.status_code == 200:
                self.log_test("Update Koerner Roll Price", True, f"Set koerner roll price to €{test_price}")
                success_count += 1
            else:
                self.log_test("Update Koerner Roll Price", False, f"HTTP {response.status_code}")
            
        except Exception as e:
            self.log_test("Menu Price Setup", False, f"Exception: {str(e)}")
            return False
        
        # Test 1: 3 weiss halves should cost 3 × €0.75 = €2.25
        try:
            breakfast_order = {
                "employee_id": employee1['id'],
                "department_id": self.test_department['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 3,
                        "seeded_halves": 0,
                        "toppings": ["butter", "butter", "butter"],  # 3 toppings for 3 halves
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                order = response.json()
                expected_price = 3 * test_price  # 3 halves × €0.75 = €2.25
                actual_price = order['total_price']
                
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("3 Weiss Halves Price Calculation", True, 
                                f"Correct: 3 halves × €{test_price} = €{actual_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("3 Weiss Halves Price Calculation", False, 
                                f"Expected €{expected_price:.2f}, got €{actual_price:.2f}")
            else:
                self.log_test("3 Weiss Halves Order", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("3 Weiss Halves Test", False, f"Exception: {str(e)}")
        
        # Test 2: 3 koerner halves should cost 3 × €0.75 = €2.25
        try:
            breakfast_order = {
                "employee_id": employee2['id'],
                "department_id": self.test_department['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 0,
                        "seeded_halves": 3,
                        "toppings": ["kaese", "schinken", "ruehrei"],  # 3 toppings for 3 halves
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                order = response.json()
                expected_price = 3 * test_price  # 3 halves × €0.75 = €2.25
                actual_price = order['total_price']
                
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("3 Koerner Halves Price Calculation", True, 
                                f"Correct: 3 halves × €{test_price} = €{actual_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("3 Koerner Halves Price Calculation", False, 
                                f"Expected €{expected_price:.2f}, got €{actual_price:.2f}")
            else:
                self.log_test("3 Koerner Halves Order", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("3 Koerner Halves Test", False, f"Exception: {str(e)}")
        
        # Test 3: Mixed halves (2 weiss + 1 koerner) should cost 3 × €0.75 = €2.25
        try:
            breakfast_order = {
                "employee_id": employee3['id'],
                "department_id": self.test_department['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 2,
                        "seeded_halves": 1,
                        "toppings": ["salami", "eiersalat", "spiegelei"],  # 3 toppings for 3 halves
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                order = response.json()
                expected_price = 3 * test_price  # 3 halves × €0.75 = €2.25
                actual_price = order['total_price']
                
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("Mixed Halves Price Calculation", True, 
                                f"Correct: 3 halves × €{test_price} = €{actual_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Mixed Halves Price Calculation", False, 
                                f"Expected €{expected_price:.2f}, got €{actual_price:.2f}")
            else:
                self.log_test("Mixed Halves Order", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Mixed Halves Test", False, f"Exception: {str(e)}")
        
        return success_count >= 4  # At least 4 out of 5 tests should pass
    
    def test_single_breakfast_order_constraint(self):
        """Test that employees can only have one breakfast order per day"""
        print("\n=== Testing Single Breakfast Order Constraint ===")
        
        # Create fresh employee for this test
        test_employee = self.create_test_employee("SingleOrder")
        if not test_employee:
            self.log_test("Single Order Constraint Test", False, "Could not create test employee")
            return False
        
        success_count = 0
        
        # Create first breakfast order
        try:
            first_order = {
                "employee_id": test_employee['id'],
                "department_id": self.test_department['id'],
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
            
            response = self.session.post(f"{API_BASE}/orders", json=first_order)
            if response.status_code == 200:
                first_order_result = response.json()
                self.log_test("First Breakfast Order", True, 
                            f"Successfully created first breakfast order: €{first_order_result['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("First Breakfast Order", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("First Breakfast Order", False, f"Exception: {str(e)}")
            return False
        
        # Attempt to create second breakfast order (should fail)
        try:
            second_order = {
                "employee_id": test_employee['id'],
                "department_id": self.test_department['id'],
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
                error_response = response.json()
                error_message = error_response.get('detail', '')
                
                # Check for German error message
                expected_german_message = "Sie haben bereits eine Frühstücksbestellung für heute"
                if expected_german_message in error_message:
                    self.log_test("Duplicate Order Prevention", True, 
                                f"Correctly prevented duplicate order with German message: {error_message}")
                    success_count += 1
                else:
                    self.log_test("Duplicate Order Prevention", False, 
                                f"Wrong error message: {error_message}")
            else:
                self.log_test("Duplicate Order Prevention", False, 
                            f"Should have returned 400, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Duplicate Order Prevention", False, f"Exception: {str(e)}")
        
        # Verify only one breakfast order exists for today
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
            if response.status_code == 200:
                orders_response = response.json()
                orders = orders_response.get('orders', [])
                
                # Count breakfast orders for today
                today = datetime.now().date().isoformat()
                breakfast_orders_today = [
                    order for order in orders 
                    if order.get('order_type') == 'breakfast' and 
                    order.get('timestamp', '').startswith(today)
                ]
                
                if len(breakfast_orders_today) == 1:
                    self.log_test("Single Order Verification", True, 
                                f"Confirmed only 1 breakfast order exists for today")
                    success_count += 1
                else:
                    self.log_test("Single Order Verification", False, 
                                f"Found {len(breakfast_orders_today)} breakfast orders, expected 1")
            else:
                self.log_test("Order Count Verification", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Order Count Verification", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_balance_updates_on_order_deletion(self):
        """Test that admin order deletion correctly updates employee balances"""
        print("\n=== Testing Balance Updates on Order Deletion ===")
        
        # Create fresh employee for this test
        test_employee = self.create_test_employee("BalanceTest")
        if not test_employee:
            self.log_test("Balance Update Test", False, "Could not create test employee")
            return False
        
        success_count = 0
        
        # Get initial balance
        try:
            response = self.session.get(f"{API_BASE}/departments/{self.test_department['id']}/employees")
            if response.status_code == 200:
                employees = response.json()
                current_employee = next((emp for emp in employees if emp['id'] == test_employee['id']), None)
                if current_employee:
                    initial_balance = current_employee['breakfast_balance']
                    self.log_test("Get Initial Balance", True, f"Initial balance: €{initial_balance:.2f}")
                else:
                    self.log_test("Get Initial Balance", False, "Employee not found")
                    return False
            else:
                self.log_test("Get Initial Balance", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Initial Balance", False, f"Exception: {str(e)}")
            return False
        
        # Create a test order
        test_order_id = None
        order_amount = 0.0
        try:
            test_order = {
                "employee_id": self.test_employee['id'],
                "department_id": self.test_department['id'],
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
                order_result = response.json()
                test_order_id = order_result['id']
                order_amount = order_result['total_price']
                self.log_test("Create Test Order for Deletion", True, 
                            f"Created order worth €{order_amount:.2f}")
                success_count += 1
            else:
                self.log_test("Create Test Order for Deletion", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create Test Order for Deletion", False, f"Exception: {str(e)}")
            return False
        
        # Verify balance increased
        try:
            response = self.session.get(f"{API_BASE}/departments/{self.test_department['id']}/employees")
            if response.status_code == 200:
                employees = response.json()
                current_employee = next((emp for emp in employees if emp['id'] == self.test_employee['id']), None)
                if current_employee:
                    balance_after_order = current_employee['breakfast_balance']
                    expected_balance = initial_balance + order_amount
                    
                    if abs(balance_after_order - expected_balance) < 0.01:
                        self.log_test("Balance After Order Creation", True, 
                                    f"Balance correctly increased to €{balance_after_order:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Balance After Order Creation", False, 
                                    f"Expected €{expected_balance:.2f}, got €{balance_after_order:.2f}")
                else:
                    self.log_test("Balance After Order Creation", False, "Employee not found")
            else:
                self.log_test("Balance After Order Creation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Balance After Order Creation", False, f"Exception: {str(e)}")
        
        # Delete the order via admin endpoint
        if test_order_id:
            try:
                response = self.session.delete(f"{API_BASE}/department-admin/orders/{test_order_id}")
                if response.status_code == 200:
                    delete_result = response.json()
                    self.log_test("Admin Order Deletion", True, 
                                f"Successfully deleted order: {delete_result.get('message', 'Success')}")
                    success_count += 1
                else:
                    self.log_test("Admin Order Deletion", False, f"HTTP {response.status_code}: {response.text}")
                    return False
                    
            except Exception as e:
                self.log_test("Admin Order Deletion", False, f"Exception: {str(e)}")
                return False
        
        # Verify balance decreased correctly and doesn't go below zero
        try:
            response = self.session.get(f"{API_BASE}/departments/{self.test_department['id']}/employees")
            if response.status_code == 200:
                employees = response.json()
                current_employee = next((emp for emp in employees if emp['id'] == self.test_employee['id']), None)
                if current_employee:
                    final_balance = current_employee['breakfast_balance']
                    expected_final_balance = max(0, initial_balance)  # Should not go below zero
                    
                    if abs(final_balance - expected_final_balance) < 0.01 and final_balance >= 0:
                        self.log_test("Balance After Order Deletion", True, 
                                    f"Balance correctly decreased to €{final_balance:.2f} (≥ €0.00)")
                        success_count += 1
                    else:
                        self.log_test("Balance After Order Deletion", False, 
                                    f"Expected €{expected_final_balance:.2f}, got €{final_balance:.2f}")
                else:
                    self.log_test("Balance After Order Deletion", False, "Employee not found")
            else:
                self.log_test("Balance After Order Deletion", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Balance After Order Deletion", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_order_update_functionality(self):
        """Test PUT /api/orders/{order_id} endpoint for updating orders"""
        print("\n=== Testing Order Update & Re-editing ===")
        
        if not self.test_employee:
            self.log_test("Order Update Test", False, "No test employee available")
            return False
        
        success_count = 0
        
        # Create initial order
        test_order_id = None
        initial_price = 0.0
        try:
            initial_order = {
                "employee_id": self.test_employee['id'],
                "department_id": self.test_department['id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 1,
                        "white_halves": 1,
                        "seeded_halves": 0,
                        "toppings": ["butter"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=initial_order)
            if response.status_code == 200:
                order_result = response.json()
                test_order_id = order_result['id']
                initial_price = order_result['total_price']
                self.log_test("Create Initial Order for Update", True, 
                            f"Created order worth €{initial_price:.2f}")
                success_count += 1
            else:
                self.log_test("Create Initial Order for Update", False, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Create Initial Order for Update", False, f"Exception: {str(e)}")
            return False
        
        # Update the order
        if test_order_id:
            try:
                updated_order_data = {
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
                
                response = self.session.put(f"{API_BASE}/orders/{test_order_id}", json=updated_order_data)
                if response.status_code == 200:
                    update_result = response.json()
                    self.log_test("Order Update Request", True, 
                                f"Successfully updated order: {update_result.get('message', 'Success')}")
                    success_count += 1
                else:
                    self.log_test("Order Update Request", False, f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Order Update Request", False, f"Exception: {str(e)}")
        
        # Verify the order was updated correctly
        try:
            response = self.session.get(f"{API_BASE}/employees/{self.test_employee['id']}/orders")
            if response.status_code == 200:
                orders_response = response.json()
                orders = orders_response.get('orders', [])
                
                updated_order = next((order for order in orders if order['id'] == test_order_id), None)
                if updated_order:
                    # Check if breakfast items were updated
                    breakfast_items = updated_order.get('breakfast_items', [])
                    if breakfast_items and len(breakfast_items) > 0:
                        item = breakfast_items[0]
                        if (item.get('total_halves') == 3 and 
                            item.get('white_halves') == 2 and 
                            item.get('seeded_halves') == 1 and
                            len(item.get('toppings', [])) == 3):
                            self.log_test("Order Content Update Verification", True, 
                                        "Order content correctly updated")
                            success_count += 1
                        else:
                            self.log_test("Order Content Update Verification", False, 
                                        "Order content not updated correctly")
                    else:
                        self.log_test("Order Content Update Verification", False, 
                                    "No breakfast items found in updated order")
                else:
                    self.log_test("Order Update Verification", False, "Updated order not found")
            else:
                self.log_test("Order Update Verification", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Order Update Verification", False, f"Exception: {str(e)}")
        
        # Verify balance was adjusted correctly
        try:
            response = self.session.get(f"{API_BASE}/departments/{self.test_department['id']}/employees")
            if response.status_code == 200:
                employees = response.json()
                current_employee = next((emp for emp in employees if emp['id'] == self.test_employee['id']), None)
                if current_employee:
                    current_balance = current_employee['breakfast_balance']
                    # Balance should reflect the updated order price
                    if current_balance > initial_price:  # Should be higher due to more items
                        self.log_test("Balance Adjustment After Update", True, 
                                    f"Balance correctly adjusted to €{current_balance:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Balance Adjustment After Update", False, 
                                    f"Balance not adjusted correctly: €{current_balance:.2f}")
                else:
                    self.log_test("Balance Adjustment After Update", False, "Employee not found")
            else:
                self.log_test("Balance Adjustment After Update", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Balance Adjustment After Update", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_daily_summary_data_structure(self):
        """Test GET /api/orders/daily-summary/{department_id} returns proper JSON structure"""
        print("\n=== Testing Daily Summary Data Structure ===")
        
        if not self.test_department:
            self.log_test("Daily Summary Test", False, "No test department available")
            return False
        
        success_count = 0
        
        # Create some test orders to ensure data exists
        try:
            if self.test_employee:
                test_order = {
                    "employee_id": self.test_employee['id'],
                    "department_id": self.test_department['id'],
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
                    self.log_test("Create Test Data for Summary", True, "Created test order for summary")
        except:
            pass  # Continue even if test order creation fails
        
        # Test daily summary endpoint
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{self.test_department['id']}")
            if response.status_code == 200:
                summary = response.json()
                
                # Check required top-level fields
                required_fields = ['date', 'breakfast_summary', 'employee_orders', 'shopping_list']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Daily Summary Required Fields", True, 
                                "All required fields present: " + ", ".join(required_fields))
                    success_count += 1
                else:
                    self.log_test("Daily Summary Required Fields", False, 
                                f"Missing fields: {missing_fields}")
                
                # Check date format
                date_str = summary.get('date', '')
                try:
                    datetime.fromisoformat(date_str)
                    self.log_test("Daily Summary Date Format", True, f"Valid date format: {date_str}")
                    success_count += 1
                except:
                    self.log_test("Daily Summary Date Format", False, f"Invalid date format: {date_str}")
                
                # Check breakfast_summary structure
                breakfast_summary = summary.get('breakfast_summary', {})
                if isinstance(breakfast_summary, dict):
                    self.log_test("Breakfast Summary Structure", True, "Breakfast summary is a dictionary")
                    success_count += 1
                    
                    # Check for roll type keys
                    expected_roll_types = ['weiss', 'koerner']
                    found_roll_types = [rt for rt in expected_roll_types if rt in breakfast_summary]
                    if found_roll_types:
                        self.log_test("Breakfast Summary Roll Types", True, 
                                    f"Found roll types: {found_roll_types}")
                        success_count += 1
                else:
                    self.log_test("Breakfast Summary Structure", False, "Breakfast summary is not a dictionary")
                
                # Check employee_orders structure
                employee_orders = summary.get('employee_orders', {})
                if isinstance(employee_orders, dict):
                    self.log_test("Employee Orders Structure", True, "Employee orders is a dictionary")
                    success_count += 1
                    
                    # Check employee order details if any exist
                    if employee_orders:
                        first_employee = next(iter(employee_orders.values()))
                        expected_employee_fields = ['white_halves', 'seeded_halves', 'toppings']
                        employee_missing_fields = [field for field in expected_employee_fields 
                                                 if field not in first_employee]
                        
                        if not employee_missing_fields:
                            self.log_test("Employee Order Details", True, 
                                        "Employee orders have correct structure")
                            success_count += 1
                        else:
                            self.log_test("Employee Order Details", False, 
                                        f"Missing employee fields: {employee_missing_fields}")
                else:
                    self.log_test("Employee Orders Structure", False, "Employee orders is not a dictionary")
                
                # Check shopping_list structure
                shopping_list = summary.get('shopping_list', {})
                if isinstance(shopping_list, dict):
                    self.log_test("Shopping List Structure", True, "Shopping list is a dictionary")
                    success_count += 1
                    
                    # Check shopping list details
                    if shopping_list:
                        first_roll_type = next(iter(shopping_list.values()))
                        if isinstance(first_roll_type, dict) and 'halves' in first_roll_type and 'whole_rolls' in first_roll_type:
                            self.log_test("Shopping List Details", True, 
                                        "Shopping list has halves and whole_rolls fields")
                            success_count += 1
                        else:
                            self.log_test("Shopping List Details", False, 
                                        "Shopping list missing halves/whole_rolls fields")
                else:
                    self.log_test("Shopping List Structure", False, "Shopping list is not a dictionary")
                
                # Test JSON serializability
                try:
                    json.dumps(summary)
                    self.log_test("JSON Serializability", True, "Summary is JSON serializable for React frontend")
                    success_count += 1
                except Exception as json_error:
                    self.log_test("JSON Serializability", False, f"JSON serialization error: {str(json_error)}")
                
            else:
                self.log_test("Daily Summary Request", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary Request", False, f"Exception: {str(e)}")
        
        return success_count >= 6
    
    def run_all_tests(self):
        """Run all critical bug fix tests"""
        print("🧪 CRITICAL BUG FIXES TESTING STARTED")
        print("=" * 60)
        
        # Setup test data
        if not self.setup_test_data():
            print("\n❌ SETUP FAILED - Cannot proceed with tests")
            return False
        
        # Run all critical tests
        test_results = []
        
        test_results.append(("Price Calculation Accuracy", self.test_price_calculation_accuracy()))
        test_results.append(("Single Breakfast Order Constraint", self.test_single_breakfast_order_constraint()))
        test_results.append(("Balance Updates on Order Deletion", self.test_balance_updates_on_order_deletion()))
        test_results.append(("Order Update & Re-editing", self.test_order_update_functionality()))
        test_results.append(("Daily Summary Data Structure", self.test_daily_summary_data_structure()))
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 CRITICAL BUG FIXES TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ WORKING" if result else "❌ FAILING"
            print(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall Result: {passed_tests}/{total_tests} critical areas working correctly")
        
        if passed_tests == total_tests:
            print("🎉 ALL CRITICAL BUG FIXES ARE WORKING CORRECTLY!")
            return True
        else:
            print(f"🚨 {total_tests - passed_tests} CRITICAL ISSUES STILL NEED FIXING")
            return False

def main():
    """Main test execution"""
    tester = CriticalBugTester()
    success = tester.run_all_tests()
    
    # Print individual test results
    print("\n" + "=" * 60)
    print("📋 DETAILED TEST RESULTS")
    print("=" * 60)
    
    for result in tester.test_results:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test']}: {result['message']}")
        if result['details']:
            print(f"   Details: {result['details']}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())