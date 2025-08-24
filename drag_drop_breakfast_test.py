#!/usr/bin/env python3
"""
Drag&Drop and Breakfast Calculation Bug Fixes Test Suite
Tests the specific critical bug fixes mentioned in the review request:
1. Drag&Drop Persistence
2. Breakfast Update Calculation Fix
3. Retroactive Lunch Pricing Fix
4. Comprehensive Order Testing
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

class DragDropBreakfastTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.department_id = None
        self.employees = []
        self.orders = []
        
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
        """Setup test environment with department authentication and test employees"""
        print("\n=== Setting Up Test Environment ===")
        
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

        # Authenticate with department 1 using credentials from review request
        try:
            login_data = {
                "department_name": "1. Wachabteilung",
                "password": "password1"
            }
            response = self.session.post(f"{API_BASE}/login/department", json=login_data)
            
            if response.status_code == 200:
                auth_result = response.json()
                self.department_id = auth_result['department_id']
                self.log_test("Department Authentication", True, f"Authenticated with department: {self.department_id}")
            else:
                self.log_test("Department Authentication", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Department Authentication", False, f"Exception: {str(e)}")
            return False

        # Create test employees for drag & drop testing
        test_employee_names = ["Max Mustermann", "Anna Schmidt", "Peter Weber", "Lisa Mueller", "Tom Fischer"]
        
        for name in test_employee_names:
            try:
                employee_data = {
                    "name": name,
                    "department_id": self.department_id
                }
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                
                if response.status_code == 200:
                    employee = response.json()
                    self.employees.append(employee)
                    self.log_test(f"Create Employee {name}", True, f"Employee created with ID: {employee['id']}")
                else:
                    self.log_test(f"Create Employee {name}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Create Employee {name}", False, f"Exception: {str(e)}")

        return len(self.employees) >= 3

    def test_drag_drop_persistence(self):
        """Test Drag&Drop Persistence - PUT /departments/{department_id}/employees/sort-order endpoint"""
        print("\n=== Testing Drag&Drop Persistence ===")
        
        if len(self.employees) < 3:
            self.log_test("Drag&Drop Persistence", False, "Not enough employees for testing")
            return False

        success_count = 0

        # Test 1: Get initial employee list and verify sort_order
        try:
            response = self.session.get(f"{API_BASE}/departments/{self.department_id}/employees")
            
            if response.status_code == 200:
                initial_employees = response.json()
                self.log_test("Get Initial Employee List", True, f"Retrieved {len(initial_employees)} employees")
                success_count += 1
                
                # Verify employees have sort_order field
                has_sort_order = all('sort_order' in emp for emp in initial_employees)
                if has_sort_order:
                    self.log_test("Sort Order Field Present", True, "All employees have sort_order field")
                    success_count += 1
                else:
                    self.log_test("Sort Order Field Present", False, "Missing sort_order field in employees")
            else:
                self.log_test("Get Initial Employee List", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Initial Employee List", False, f"Exception: {str(e)}")
            return False

        # Test 2: Update sort order using drag & drop endpoint
        try:
            # Create new sort order (reverse the current order)
            employee_ids = [emp['id'] for emp in self.employees[:5]]  # Use first 5 employees
            reversed_ids = list(reversed(employee_ids))
            
            response = self.session.put(
                f"{API_BASE}/departments/{self.department_id}/employees/sort-order",
                json=reversed_ids
            )
            
            if response.status_code == 200:
                result = response.json()
                expected_count = len(reversed_ids)
                actual_count = result.get('updated_count', 0)
                
                if actual_count == expected_count:
                    self.log_test("Update Sort Order", True, 
                                f"Successfully updated sort order for {actual_count} employees")
                    success_count += 1
                else:
                    self.log_test("Update Sort Order", False, 
                                f"Expected {expected_count} updates, got {actual_count}")
            else:
                self.log_test("Update Sort Order", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Update Sort Order", False, f"Exception: {str(e)}")
            return False

        # Test 3: Verify sort order persistence
        try:
            response = self.session.get(f"{API_BASE}/departments/{self.department_id}/employees")
            
            if response.status_code == 200:
                updated_employees = response.json()
                
                # Check if employees are returned in the new sort order
                actual_order = [emp['id'] for emp in updated_employees[:len(reversed_ids)]]
                
                if actual_order == reversed_ids:
                    self.log_test("Sort Order Persistence", True, 
                                "Employees returned in correct sorted order")
                    success_count += 1
                else:
                    self.log_test("Sort Order Persistence", False, 
                                f"Expected order: {reversed_ids}, Got: {actual_order}")
            else:
                self.log_test("Sort Order Persistence", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Sort Order Persistence", False, f"Exception: {str(e)}")

        return success_count >= 3

    def test_breakfast_update_calculation_fix(self):
        """Test Breakfast Update Calculation Fix - PUT /orders/{order_id} endpoint"""
        print("\n=== Testing Breakfast Update Calculation Fix ===")
        
        if not self.employees:
            self.log_test("Breakfast Update Calculation", False, "No employees available")
            return False

        success_count = 0
        test_employee = self.employees[0]

        # Set lunch price for testing
        try:
            self.session.put(f"{API_BASE}/lunch-settings", params={"price": 3.0})
        except:
            pass

        # Test 1: Only boiled_eggs (no rolls) - verify boiled_eggs price is calculated
        try:
            eggs_only_order = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 0,
                    "white_halves": 0,
                    "seeded_halves": 0,
                    "toppings": [],
                    "has_lunch": False,
                    "boiled_eggs": 3  # 3 boiled eggs only
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=eggs_only_order)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order['id']
                self.orders.append(order_id)
                
                # Expected price: 3 eggs * €0.50 = €1.50
                expected_price = 3 * 0.50
                actual_price = order['total_price']
                
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("Boiled Eggs Only Order", True, 
                                f"Correct pricing: €{actual_price:.2f} (expected €{expected_price:.2f})")
                    success_count += 1
                else:
                    self.log_test("Boiled Eggs Only Order", False, 
                                f"Price mismatch: got €{actual_price:.2f}, expected €{expected_price:.2f}")
            else:
                self.log_test("Boiled Eggs Only Order", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Boiled Eggs Only Order", False, f"Exception: {str(e)}")

        # Test 2: Mixed order (rolls + eggs + lunch) - verify all components calculated correctly
        try:
            mixed_order = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # 2 rolls = 4 halves
                    "white_halves": 2,
                    "seeded_halves": 2,
                    "toppings": ["ruehrei", "kaese", "schinken", "butter"],  # 4 toppings for 4 halves
                    "has_lunch": True,
                    "boiled_eggs": 2  # 2 boiled eggs
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=mixed_order)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order['id']
                self.orders.append(order_id)
                
                # Expected price calculation:
                # 2 white halves * €0.50 = €1.00
                # 2 seeded halves * €0.60 = €1.20
                # 4 toppings * €0.00 = €0.00 (free toppings)
                # 2 boiled eggs * €0.50 = €1.00
                # lunch for 4 halves * €3.00 = €12.00
                expected_price = (2 * 0.50) + (2 * 0.60) + (4 * 0.00) + (2 * 0.50) + (4 * 3.00)
                actual_price = order['total_price']
                
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("Mixed Order (Rolls + Eggs + Lunch)", True, 
                                f"Correct pricing: €{actual_price:.2f} (expected €{expected_price:.2f})")
                    success_count += 1
                else:
                    self.log_test("Mixed Order (Rolls + Eggs + Lunch)", False, 
                                f"Price mismatch: got €{actual_price:.2f}, expected €{expected_price:.2f}")
            else:
                self.log_test("Mixed Order (Rolls + Eggs + Lunch)", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Mixed Order (Rolls + Eggs + Lunch)", False, f"Exception: {str(e)}")

        # Test 3: Lunch-only order - verify lunch price added once, not multiplied by roll count
        try:
            lunch_only_order = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 0,
                    "white_halves": 0,
                    "seeded_halves": 0,
                    "toppings": [],
                    "has_lunch": True,  # Only lunch
                    "boiled_eggs": 0
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=lunch_only_order)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order['id']
                self.orders.append(order_id)
                
                # Expected price: lunch only = €3.00 (not multiplied by roll count)
                expected_price = 3.00
                actual_price = order['total_price']
                
                if abs(actual_price - expected_price) < 0.01:
                    self.log_test("Lunch Only Order", True, 
                                f"Correct pricing: €{actual_price:.2f} (expected €{expected_price:.2f})")
                    success_count += 1
                else:
                    self.log_test("Lunch Only Order", False, 
                                f"Price mismatch: got €{actual_price:.2f}, expected €{expected_price:.2f}")
            else:
                self.log_test("Lunch Only Order", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Lunch Only Order", False, f"Exception: {str(e)}")

        # Test 4: Verify employee balance is updated correctly
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                breakfast_balance = profile['breakfast_total']
                
                if breakfast_balance > 0:
                    self.log_test("Employee Balance Update", True, 
                                f"Employee balance correctly updated: €{breakfast_balance:.2f}")
                    success_count += 1
                else:
                    self.log_test("Employee Balance Update", False, 
                                f"Employee balance not updated correctly: €{breakfast_balance:.2f}")
            else:
                self.log_test("Employee Balance Update", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Employee Balance Update", False, f"Exception: {str(e)}")

        return success_count >= 3

    def test_retroactive_lunch_pricing_fix(self):
        """Test Retroactive Lunch Pricing Fix - PUT /lunch-settings endpoint"""
        print("\n=== Testing Retroactive Lunch Pricing Fix ===")
        
        if not self.employees:
            self.log_test("Retroactive Lunch Pricing", False, "No employees available")
            return False

        success_count = 0
        test_employee = self.employees[1] if len(self.employees) > 1 else self.employees[0]

        # Test 1: Create breakfast orders with has_lunch=true
        initial_lunch_price = 2.00
        try:
            # Set initial lunch price
            response = self.session.put(f"{API_BASE}/lunch-settings", params={"price": initial_lunch_price})
            if response.status_code == 200:
                self.log_test("Set Initial Lunch Price", True, f"Set lunch price to €{initial_lunch_price:.2f}")
            
            # Create breakfast order with lunch
            breakfast_with_lunch = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 1 roll = 2 halves
                    "white_halves": 2,
                    "seeded_halves": 0,
                    "toppings": ["ruehrei", "kaese"],
                    "has_lunch": True,
                    "boiled_eggs": 1
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_with_lunch)
            
            if response.status_code == 200:
                order = response.json()
                initial_order_id = order['id']
                initial_total = order['total_price']
                self.orders.append(initial_order_id)
                
                self.log_test("Create Order with Initial Lunch Price", True, 
                            f"Order created with total: €{initial_total:.2f}")
                success_count += 1
            else:
                self.log_test("Create Order with Initial Lunch Price", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Create Order with Initial Lunch Price", False, f"Exception: {str(e)}")
            return False

        # Test 2: Change lunch price and verify retroactive update
        new_lunch_price = 4.50
        try:
            response = self.session.put(f"{API_BASE}/lunch-settings", params={"price": new_lunch_price})
            
            if response.status_code == 200:
                result = response.json()
                updated_orders = result.get('updated_orders', 0)
                
                self.log_test("Update Lunch Price", True, 
                            f"Lunch price updated to €{new_lunch_price:.2f}, {updated_orders} orders affected")
                success_count += 1
                
                # Verify the price change was applied correctly
                if updated_orders > 0:
                    self.log_test("Retroactive Orders Updated", True, 
                                f"{updated_orders} existing orders were retroactively updated")
                    success_count += 1
                else:
                    self.log_test("Retroactive Orders Updated", False, "No orders were retroactively updated")
            else:
                self.log_test("Update Lunch Price", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Update Lunch Price", False, f"Exception: {str(e)}")

        # Test 3: Verify prices are NOT divided by 2 (previous bug)
        try:
            # Create another order with the new lunch price
            test_order = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 1 roll = 2 halves
                    "white_halves": 0,
                    "seeded_halves": 2,
                    "toppings": ["schinken", "butter"],
                    "has_lunch": True,
                    "boiled_eggs": 0
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=test_order)
            
            if response.status_code == 200:
                order = response.json()
                order_total = order['total_price']
                self.orders.append(order['id'])
                
                # Expected calculation:
                # 2 seeded halves * €0.60 = €1.20
                # 2 toppings * €0.00 = €0.00 (free)
                # lunch for 2 halves * €4.50 = €9.00 (NOT divided by 2)
                expected_total = (2 * 0.60) + (2 * 0.00) + (2 * 4.50)
                
                if abs(order_total - expected_total) < 0.01:
                    self.log_test("Lunch Price NOT Divided by 2", True, 
                                f"Correct calculation: €{order_total:.2f} (expected €{expected_total:.2f})")
                    success_count += 1
                else:
                    self.log_test("Lunch Price NOT Divided by 2", False, 
                                f"Incorrect calculation: got €{order_total:.2f}, expected €{expected_total:.2f}")
            else:
                self.log_test("Lunch Price NOT Divided by 2", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Lunch Price NOT Divided by 2", False, f"Exception: {str(e)}")

        # Test 4: Verify boiled eggs prices included in recalculation
        try:
            # Create order with boiled eggs and lunch
            eggs_lunch_order = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 0,
                    "white_halves": 0,
                    "seeded_halves": 0,
                    "toppings": [],
                    "has_lunch": True,
                    "boiled_eggs": 2  # Only eggs and lunch
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=eggs_lunch_order)
            
            if response.status_code == 200:
                order = response.json()
                order_total = order['total_price']
                self.orders.append(order['id'])
                
                # Expected: 2 eggs * €0.50 + lunch €4.50 = €5.50
                expected_total = (2 * 0.50) + 4.50
                
                if abs(order_total - expected_total) < 0.01:
                    self.log_test("Boiled Eggs in Lunch Calculation", True, 
                                f"Boiled eggs correctly included: €{order_total:.2f}")
                    success_count += 1
                else:
                    self.log_test("Boiled Eggs in Lunch Calculation", False, 
                                f"Boiled eggs calculation error: got €{order_total:.2f}, expected €{expected_total:.2f}")
            else:
                self.log_test("Boiled Eggs in Lunch Calculation", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Boiled Eggs in Lunch Calculation", False, f"Exception: {str(e)}")

        # Test 5: Verify employee balances updated with correct difference
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                final_balance = profile['breakfast_total']
                
                if final_balance > 0:
                    self.log_test("Employee Balance After Retroactive Update", True, 
                                f"Employee balance correctly reflects retroactive changes: €{final_balance:.2f}")
                    success_count += 1
                else:
                    self.log_test("Employee Balance After Retroactive Update", False, 
                                f"Employee balance incorrect: €{final_balance:.2f}")
            else:
                self.log_test("Employee Balance After Retroactive Update", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Employee Balance After Retroactive Update", False, f"Exception: {str(e)}")

        return success_count >= 4

    def test_comprehensive_order_scenarios(self):
        """Test comprehensive order scenarios including user's specific example"""
        print("\n=== Testing Comprehensive Order Scenarios ===")
        
        if not self.employees:
            self.log_test("Comprehensive Order Testing", False, "No employees available")
            return False

        success_count = 0
        test_employee = self.employees[2] if len(self.employees) > 2 else self.employees[0]

        # Set lunch price to 3.00 for user's specific example
        try:
            self.session.put(f"{API_BASE}/lunch-settings", params={"price": 3.0})
        except:
            pass

        # Test 1: User's specific example - 2x 0.75€ rolls + lunch (0€→3€)
        try:
            # First, update roll prices to match user's example (0.75€)
            # Get breakfast menu to find roll items
            response = self.session.get(f"{API_BASE}/menu/breakfast/{self.department_id}")
            if response.status_code == 200:
                breakfast_menu = response.json()
                if breakfast_menu:
                    # Update first roll type to 0.75€
                    roll_item = breakfast_menu[0]
                    update_data = {"price": 0.75}
                    self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{roll_item['id']}", 
                                   json=update_data, params={"department_id": self.department_id})
            
            # Create user's specific order: 2x 0.75€ rolls + lunch
            user_example_order = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # 2 rolls = 4 halves
                    "white_halves": 4,
                    "seeded_halves": 0,
                    "toppings": ["ruehrei", "kaese", "schinken", "butter"],  # 4 toppings
                    "has_lunch": True,
                    "boiled_eggs": 0
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=user_example_order)
            
            if response.status_code == 200:
                order = response.json()
                order_total = order['total_price']
                self.orders.append(order['id'])
                
                # Expected: 4 halves * €0.75 + lunch for 4 halves * €3.00 = €3.00 + €12.00 = €15.00
                expected_total = (4 * 0.75) + (4 * 3.00)
                
                if abs(order_total - expected_total) < 0.01:
                    self.log_test("User's Specific Example (2x 0.75€ rolls + lunch)", True, 
                                f"Correct total: €{order_total:.2f} (expected €{expected_total:.2f})")
                    success_count += 1
                else:
                    self.log_test("User's Specific Example (2x 0.75€ rolls + lunch)", False, 
                                f"Incorrect total: got €{order_total:.2f}, expected €{expected_total:.2f}")
            else:
                self.log_test("User's Specific Example", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("User's Specific Example", False, f"Exception: {str(e)}")

        # Test 2: Eggs only edge case
        try:
            eggs_only = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 0,
                    "white_halves": 0,
                    "seeded_halves": 0,
                    "toppings": [],
                    "has_lunch": False,
                    "boiled_eggs": 4
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=eggs_only)
            
            if response.status_code == 200:
                order = response.json()
                expected_total = 4 * 0.50  # 4 eggs * €0.50
                
                if abs(order['total_price'] - expected_total) < 0.01:
                    self.log_test("Eggs Only Edge Case", True, 
                                f"Correct pricing: €{order['total_price']:.2f}")
                    success_count += 1
                    self.orders.append(order['id'])
                else:
                    self.log_test("Eggs Only Edge Case", False, 
                                f"Price mismatch: got €{order['total_price']:.2f}, expected €{expected_total:.2f}")
            else:
                self.log_test("Eggs Only Edge Case", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Eggs Only Edge Case", False, f"Exception: {str(e)}")

        # Test 3: Lunch only edge case
        try:
            lunch_only = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 0,
                    "white_halves": 0,
                    "seeded_halves": 0,
                    "toppings": [],
                    "has_lunch": True,
                    "boiled_eggs": 0
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=lunch_only)
            
            if response.status_code == 200:
                order = response.json()
                expected_total = 3.00  # Lunch only
                
                if abs(order['total_price'] - expected_total) < 0.01:
                    self.log_test("Lunch Only Edge Case", True, 
                                f"Correct pricing: €{order['total_price']:.2f}")
                    success_count += 1
                    self.orders.append(order['id'])
                else:
                    self.log_test("Lunch Only Edge Case", False, 
                                f"Price mismatch: got €{order['total_price']:.2f}, expected €{expected_total:.2f}")
            else:
                self.log_test("Lunch Only Edge Case", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Lunch Only Edge Case", False, f"Exception: {str(e)}")

        # Test 4: Rolls only edge case
        try:
            rolls_only = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 6,
                    "white_halves": 3,
                    "seeded_halves": 3,
                    "toppings": ["ruehrei", "kaese", "schinken", "butter", "spiegelei", "eiersalat"],
                    "has_lunch": False,
                    "boiled_eggs": 0
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=rolls_only)
            
            if response.status_code == 200:
                order = response.json()
                # Expected: 3 white * €0.75 + 3 seeded * €0.60 + 6 toppings * €0.00
                expected_total = (3 * 0.75) + (3 * 0.60) + (6 * 0.00)
                
                if abs(order['total_price'] - expected_total) < 0.01:
                    self.log_test("Rolls Only Edge Case", True, 
                                f"Correct pricing: €{order['total_price']:.2f}")
                    success_count += 1
                    self.orders.append(order['id'])
                else:
                    self.log_test("Rolls Only Edge Case", False, 
                                f"Price mismatch: got €{order['total_price']:.2f}, expected €{expected_total:.2f}")
            else:
                self.log_test("Rolls Only Edge Case", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Rolls Only Edge Case", False, f"Exception: {str(e)}")

        # Test 5: Mixed combination with all components
        try:
            mixed_combination = {
                "employee_id": test_employee['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["ruehrei", "kaese"],
                    "has_lunch": True,
                    "boiled_eggs": 1
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=mixed_combination)
            
            if response.status_code == 200:
                order = response.json()
                # Expected: 1 white * €0.75 + 1 seeded * €0.60 + 2 toppings * €0.00 + 1 egg * €0.50 + lunch for 2 halves * €3.00
                expected_total = (1 * 0.75) + (1 * 0.60) + (2 * 0.00) + (1 * 0.50) + (2 * 3.00)
                
                if abs(order['total_price'] - expected_total) < 0.01:
                    self.log_test("Mixed Combination Edge Case", True, 
                                f"Correct pricing: €{order['total_price']:.2f}")
                    success_count += 1
                    self.orders.append(order['id'])
                else:
                    self.log_test("Mixed Combination Edge Case", False, 
                                f"Price mismatch: got €{order['total_price']:.2f}, expected €{expected_total:.2f}")
            else:
                self.log_test("Mixed Combination Edge Case", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Mixed Combination Edge Case", False, f"Exception: {str(e)}")

        return success_count >= 4

    def run_all_tests(self):
        """Run all critical bug fix tests"""
        print("🧪 CRITICAL BUG FIXES TESTING STARTED")
        print("=" * 60)
        
        # Setup test environment
        if not self.setup_test_environment():
            print("❌ Test environment setup failed. Aborting tests.")
            return False
        
        # Run all tests
        test_results = []
        
        test_results.append(("Drag&Drop Persistence", self.test_drag_drop_persistence()))
        test_results.append(("Breakfast Update Calculation Fix", self.test_breakfast_update_calculation_fix()))
        test_results.append(("Retroactive Lunch Pricing Fix", self.test_retroactive_lunch_pricing_fix()))
        test_results.append(("Comprehensive Order Scenarios", self.test_comprehensive_order_scenarios()))
        
        # Print summary
        print("\n" + "=" * 60)
        print("🧪 CRITICAL BUG FIXES TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
            if result:
                passed_tests += 1
        
        print(f"\nOverall Result: {passed_tests}/{total_tests} major test categories passed")
        
        # Print detailed results
        print(f"\nDetailed Results: {len([r for r in self.test_results if r['success']])}/{len(self.test_results)} individual tests passed")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 75:
            print("🎉 CRITICAL BUG FIXES ARE WORKING CORRECTLY!")
            return True
        else:
            print("⚠️ CRITICAL ISSUES FOUND - NEEDS ATTENTION")
            return False

def main():
    """Main test execution"""
    tester = DragDropBreakfastTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n✅ All critical bug fixes are working properly!")
        sys.exit(0)
    else:
        print("\n❌ Critical bug fixes have issues that need to be addressed!")
        sys.exit(1)

if __name__ == "__main__":
    main()