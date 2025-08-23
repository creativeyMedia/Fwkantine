#!/usr/bin/env python3
"""
Backend Test Suite for Updated German Canteen Management System
Tests all new features including roll halves, retroactive lunch pricing, payment logging, and shopping list
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
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteen-manager.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class UpdatedCanteenTester:
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

    def test_new_department_structure(self):
        """Test new department names and authentication credentials"""
        print("\n=== Testing New Department Structure ===")
        
        # Initialize data first
        try:
            response = self.session.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.log_test("Data Initialization", True, "System initialized successfully")
            else:
                self.log_test("Data Initialization", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Data Initialization", False, f"Exception: {str(e)}")
        
        success_count = 0
        
        # Test getting departments with new names
        try:
            response = self.session.get(f"{API_BASE}/departments")
            
            if response.status_code == 200:
                departments = response.json()
                self.departments = departments
                
                # Check for new department names
                expected_departments = ["1. Schichtabteilung", "2. Schichtabteilung", 
                                      "3. Schichtabteilung", "4. Schichtabteilung"]
                
                dept_names = [dept['name'] for dept in departments]
                
                if len(departments) == 4:
                    self.log_test("Department Count", True, f"Found {len(departments)} departments")
                    success_count += 1
                else:
                    self.log_test("Department Count", False, f"Expected 4, found {len(departments)}")
                
                # Check new department names
                missing_depts = [name for name in expected_departments if name not in dept_names]
                if not missing_depts:
                    self.log_test("New Department Names", True, 
                                f"All new departments found: {dept_names}")
                    success_count += 1
                else:
                    self.log_test("New Department Names", False, 
                                f"Missing departments: {missing_depts}")
                
            else:
                self.log_test("Get Departments", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Departments", False, f"Exception: {str(e)}")
        
        # Test new authentication credentials
        expected_credentials = {
            "1. Schichtabteilung": {"password": "password1", "admin": "admin1"},
            "2. Schichtabteilung": {"password": "password2", "admin": "admin2"},
            "3. Schichtabteilung": {"password": "password3", "admin": "admin3"},
            "4. Schichtabteilung": {"password": "password4", "admin": "admin4"}
        }
        
        for dept in self.departments:
            dept_name = dept['name']
            if dept_name in expected_credentials:
                creds = expected_credentials[dept_name]
                
                # Test department login
                try:
                    login_data = {
                        "department_name": dept_name,
                        "password": creds["password"]
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department", json=login_data)
                    
                    if response.status_code == 200:
                        self.log_test(f"Department Login {dept_name}", True, 
                                    f"Successfully authenticated with {creds['password']}")
                        success_count += 1
                    else:
                        self.log_test(f"Department Login {dept_name}", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
                except Exception as e:
                    self.log_test(f"Department Login {dept_name}", False, f"Exception: {str(e)}")
                
                # Test department admin login
                try:
                    admin_login_data = {
                        "department_name": dept_name,
                        "admin_password": creds["admin"]
                    }
                    
                    response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
                    
                    if response.status_code == 200:
                        login_result = response.json()
                        if login_result.get('role') == 'department_admin':
                            self.log_test(f"Admin Login {dept_name}", True, 
                                        f"Successfully authenticated admin with {creds['admin']}")
                            success_count += 1
                        else:
                            self.log_test(f"Admin Login {dept_name}", False, "Role mismatch")
                    else:
                        self.log_test(f"Admin Login {dept_name}", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
                except Exception as e:
                    self.log_test(f"Admin Login {dept_name}", False, f"Exception: {str(e)}")
        
        # Test that central admin (admin123) still works
        try:
            admin_login = {"password": "admin123"}
            response = self.session.post(f"{API_BASE}/login/admin", json=admin_login)
            
            if response.status_code == 200:
                admin_result = response.json()
                if admin_result.get('role') == 'admin':
                    self.log_test("Central Admin Access", True, "Central admin (admin123) still accessible")
                    success_count += 1
                else:
                    self.log_test("Central Admin Access", False, "Invalid admin response")
            else:
                self.log_test("Central Admin Access", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Central Admin Access", False, f"Exception: {str(e)}")
        
        return success_count >= 6  # At least 6 successful tests

    def test_roll_halves_breakfast_logic(self):
        """Test new breakfast logic with roll halves instead of roll count"""
        print("\n=== Testing Roll Halves Breakfast Logic ===")
        
        # Get menu items first
        try:
            response = self.session.get(f"{API_BASE}/menu/breakfast")
            if response.status_code == 200:
                self.menu_items['breakfast'] = response.json()
            
            response = self.session.get(f"{API_BASE}/menu/toppings")
            if response.status_code == 200:
                self.menu_items['toppings'] = response.json()
        except:
            pass
        
        # Create test employee if needed
        if not self.employees and self.departments:
            try:
                employee_data = {
                    "name": "Max Mustermann",
                    "department_id": self.departments[0]['id']
                }
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    self.employees.append(response.json())
            except:
                pass
        
        if not self.employees:
            self.log_test("Roll Halves Logic", False, "No employees available for testing")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Test 1: Valid order with matching toppings and roll halves
        try:
            valid_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "weiss",
                        "roll_halves": 3,  # 3 halves
                        "toppings": ["ruehrei", "kaese", "schinken"],  # 3 toppings (matches halves)
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=valid_order)
            
            if response.status_code == 200:
                order = response.json()
                self.log_test("Valid Roll Halves Order", True, 
                            f"Created order with 3 roll halves and 3 toppings: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Valid Roll Halves Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Valid Roll Halves Order", False, f"Exception: {str(e)}")
        
        # Test 2: Invalid order with mismatched toppings and roll halves
        try:
            invalid_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "koerner",
                        "roll_halves": 2,  # 2 halves
                        "toppings": ["ruehrei", "kaese", "schinken"],  # 3 toppings (doesn't match)
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=invalid_order)
            
            if response.status_code == 400:
                error_data = response.json()
                if "Anzahl der Beläge" in error_data.get('detail', ''):
                    self.log_test("Topping Validation", True, 
                                "Correctly rejected order with mismatched toppings and halves")
                    success_count += 1
                else:
                    self.log_test("Topping Validation", False, "Wrong error message")
            else:
                self.log_test("Topping Validation", False, 
                            f"Should reject invalid order, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Topping Validation", False, f"Exception: {str(e)}")
        
        # Test 3: Pricing calculation with roll halves
        try:
            pricing_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "weiss",
                        "roll_halves": 5,  # 5 halves
                        "toppings": ["ruehrei", "kaese", "schinken", "salami", "butter"],  # 5 toppings
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=pricing_order)
            
            if response.status_code == 200:
                order = response.json()
                # Calculate expected price (5 halves * roll price + 5 toppings * topping price)
                if self.menu_items['breakfast']:
                    roll_price = next((item['price'] for item in self.menu_items['breakfast'] 
                                     if item['roll_type'] == 'weiss'), 0.5)
                    expected_roll_cost = roll_price * 5
                    # Toppings are free, so total should be just roll cost
                    if abs(order['total_price'] - expected_roll_cost) < 0.01:
                        self.log_test("Roll Halves Pricing", True, 
                                    f"Correct pricing: 5 halves × €{roll_price:.2f} = €{order['total_price']:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Roll Halves Pricing", False, 
                                    f"Expected €{expected_roll_cost:.2f}, got €{order['total_price']:.2f}")
                else:
                    self.log_test("Roll Halves Pricing", True, 
                                f"Order created with pricing: €{order['total_price']:.2f}")
                    success_count += 1
            else:
                self.log_test("Roll Halves Pricing", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Roll Halves Pricing", False, f"Exception: {str(e)}")
        
        # Test 4: Lunch option integration with roll halves
        try:
            lunch_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "koerner",
                        "roll_halves": 2,  # 2 halves
                        "toppings": ["ruehrei", "kaese"],  # 2 toppings
                        "has_lunch": True  # With lunch
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=lunch_order)
            
            if response.status_code == 200:
                order = response.json()
                # Should include lunch cost for 2 halves
                self.log_test("Lunch Option with Roll Halves", True, 
                            f"Created lunch order with 2 halves: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Lunch Option with Roll Halves", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Lunch Option with Roll Halves", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_retroactive_lunch_pricing(self):
        """Test retroactive lunch pricing updates"""
        print("\n=== Testing Retroactive Lunch Pricing ===")
        
        if not self.employees:
            self.log_test("Retroactive Lunch Pricing", False, "No employees available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Step 1: Set initial lunch price
        try:
            initial_price = 2.50
            response = self.session.put(f"{API_BASE}/lunch-settings", params={"price": initial_price})
            if response.status_code == 200:
                self.log_test("Set Initial Lunch Price", True, f"Set lunch price to €{initial_price:.2f}")
                success_count += 1
            else:
                self.log_test("Set Initial Lunch Price", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Set Initial Lunch Price", False, f"Exception: {str(e)}")
        
        # Step 2: Create breakfast orders with lunch option
        created_orders = []
        try:
            for i in range(2):
                lunch_order = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "roll_type": "weiss",
                            "roll_halves": 2,
                            "toppings": ["ruehrei", "kaese"],
                            "has_lunch": True
                        }
                    ]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=lunch_order)
                if response.status_code == 200:
                    order = response.json()
                    created_orders.append(order)
                    
            if len(created_orders) == 2:
                self.log_test("Create Lunch Orders", True, 
                            f"Created {len(created_orders)} breakfast orders with lunch")
                success_count += 1
            else:
                self.log_test("Create Lunch Orders", False, "Failed to create test orders")
                
        except Exception as e:
            self.log_test("Create Lunch Orders", False, f"Exception: {str(e)}")
        
        # Step 3: Get employee balance before price update
        old_balance = 0.0
        try:
            response = self.session.get(f"{API_BASE}/departments/{test_employee['department_id']}/employees")
            if response.status_code == 200:
                employees = response.json()
                for emp in employees:
                    if emp['id'] == test_employee['id']:
                        old_balance = emp['breakfast_balance']
                        break
                self.log_test("Get Balance Before Update", True, f"Balance before: €{old_balance:.2f}")
        except Exception as e:
            self.log_test("Get Balance Before Update", False, f"Exception: {str(e)}")
        
        # Step 4: Update lunch price (should trigger retroactive update)
        try:
            new_price = 4.00
            response = self.session.put(f"{API_BASE}/lunch-settings", params={"price": new_price})
            
            if response.status_code == 200:
                result = response.json()
                updated_orders = result.get('updated_orders', 0)
                if updated_orders > 0:
                    self.log_test("Retroactive Price Update", True, 
                                f"Updated lunch price to €{new_price:.2f}, affected {updated_orders} orders")
                    success_count += 1
                else:
                    self.log_test("Retroactive Price Update", False, "No orders were updated")
            else:
                self.log_test("Retroactive Price Update", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Retroactive Price Update", False, f"Exception: {str(e)}")
        
        # Step 5: Verify employee balance was adjusted
        try:
            response = self.session.get(f"{API_BASE}/departments/{test_employee['department_id']}/employees")
            if response.status_code == 200:
                employees = response.json()
                for emp in employees:
                    if emp['id'] == test_employee['id']:
                        new_balance = emp['breakfast_balance']
                        balance_diff = new_balance - old_balance
                        expected_diff = (4.00 - 2.50) * 2 * 2  # price diff * orders * halves per order
                        
                        if abs(balance_diff - expected_diff) < 0.01:
                            self.log_test("Balance Adjustment", True, 
                                        f"Balance correctly adjusted by €{balance_diff:.2f}")
                            success_count += 1
                        else:
                            self.log_test("Balance Adjustment", False, 
                                        f"Expected adjustment €{expected_diff:.2f}, got €{balance_diff:.2f}")
                        break
        except Exception as e:
            self.log_test("Balance Adjustment", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_payment_logging_system(self):
        """Test payment logging and balance reset functionality"""
        print("\n=== Testing Payment Logging System ===")
        
        if not self.employees or not self.departments:
            self.log_test("Payment Logging", False, "No employees or departments available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        test_dept = self.departments[0]
        
        # Step 1: Create some orders to build up balance
        try:
            order_data = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "weiss",
                        "roll_halves": 2,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                self.log_test("Create Order for Payment Test", True, "Created order to build balance")
        except Exception as e:
            self.log_test("Create Order for Payment Test", False, f"Exception: {str(e)}")
        
        # Step 2: Get current balance
        current_balance = 0.0
        try:
            response = self.session.get(f"{API_BASE}/departments/{test_employee['department_id']}/employees")
            if response.status_code == 200:
                employees = response.json()
                for emp in employees:
                    if emp['id'] == test_employee['id']:
                        current_balance = emp['breakfast_balance']
                        break
                self.log_test("Get Current Balance", True, f"Current balance: €{current_balance:.2f}")
        except Exception as e:
            self.log_test("Get Current Balance", False, f"Exception: {str(e)}")
        
        # Step 3: Mark payment
        try:
            payment_data = {
                "payment_type": "breakfast",
                "amount": current_balance,
                "admin_department": test_dept['name']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/payment/{test_employee['id']}", 
                                       params=payment_data)
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Mark Payment", True, 
                            f"Payment marked successfully: {result.get('message', 'Success')}")
                success_count += 1
            else:
                self.log_test("Mark Payment", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Mark Payment", False, f"Exception: {str(e)}")
        
        # Step 4: Verify balance was reset
        try:
            response = self.session.get(f"{API_BASE}/departments/{test_employee['department_id']}/employees")
            if response.status_code == 200:
                employees = response.json()
                for emp in employees:
                    if emp['id'] == test_employee['id']:
                        new_balance = emp['breakfast_balance']
                        if abs(new_balance) < 0.01:  # Should be 0.0
                            self.log_test("Balance Reset", True, 
                                        f"Balance correctly reset to €{new_balance:.2f}")
                            success_count += 1
                        else:
                            self.log_test("Balance Reset", False, 
                                        f"Balance not reset, still €{new_balance:.2f}")
                        break
        except Exception as e:
            self.log_test("Balance Reset", False, f"Exception: {str(e)}")
        
        # Step 5: Retrieve payment logs
        try:
            response = self.session.get(f"{API_BASE}/department-admin/payment-logs/{test_employee['id']}")
            
            if response.status_code == 200:
                logs = response.json()
                if isinstance(logs, list) and len(logs) > 0:
                    latest_log = logs[0]  # Should be most recent
                    if (latest_log.get('action') == 'payment' and 
                        latest_log.get('payment_type') == 'breakfast' and
                        latest_log.get('admin_user') == test_dept['name']):
                        self.log_test("Payment Log Retrieval", True, 
                                    f"Payment log created: €{latest_log.get('amount', 0):.2f} by {latest_log.get('admin_user')}")
                        success_count += 1
                    else:
                        self.log_test("Payment Log Retrieval", False, "Invalid log data")
                else:
                    self.log_test("Payment Log Retrieval", False, "No payment logs found")
            else:
                self.log_test("Payment Log Retrieval", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Payment Log Retrieval", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_enhanced_daily_summary_shopping_list(self):
        """Test enhanced daily summary with shopping list calculation"""
        print("\n=== Testing Enhanced Daily Summary with Shopping List ===")
        
        if not self.employees or not self.departments:
            self.log_test("Enhanced Daily Summary", False, "No employees or departments available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        test_dept = self.departments[0]
        
        # Create multiple breakfast orders with different roll types and halves
        test_orders = [
            {
                "roll_type": "weiss",
                "roll_halves": 5,  # 5 white halves
                "toppings": ["ruehrei", "kaese", "schinken", "salami", "butter"]
            },
            {
                "roll_type": "weiss", 
                "roll_halves": 6,  # 6 more white halves (total 11)
                "toppings": ["ruehrei", "ruehrei", "kaese", "kaese", "schinken", "salami"]
            },
            {
                "roll_type": "koerner",
                "roll_halves": 3,  # 3 seeded halves
                "toppings": ["ruehrei", "kaese", "butter"]
            }
        ]
        
        # Create the test orders
        try:
            for i, order_spec in enumerate(test_orders):
                order_data = {
                    "employee_id": test_employee['id'],
                    "department_id": test_employee['department_id'],
                    "order_type": "breakfast",
                    "breakfast_items": [order_spec]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=order_data)
                if response.status_code == 200:
                    self.log_test(f"Create Test Order {i+1}", True, 
                                f"Created order with {order_spec['roll_halves']} {order_spec['roll_type']} halves")
                else:
                    self.log_test(f"Create Test Order {i+1}", False, 
                                f"HTTP {response.status_code}")
                    
        except Exception as e:
            self.log_test("Create Test Orders", False, f"Exception: {str(e)}")
        
        # Test daily summary with shopping list
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check for required fields including shopping_list
                required_fields = ['date', 'breakfast_summary', 'shopping_list', 'total_toppings']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Daily Summary Structure", True, 
                                "Summary includes shopping_list and total_toppings")
                    success_count += 1
                else:
                    self.log_test("Daily Summary Structure", False, 
                                f"Missing fields: {missing_fields}")
                
                # Test shopping list calculation
                shopping_list = summary.get('shopping_list', {})
                if shopping_list:
                    # Check white rolls: 11 halves should become 6 whole rolls (rounded up)
                    if 'weiss' in shopping_list:
                        weiss_data = shopping_list['weiss']
                        halves = weiss_data.get('halves', 0)
                        whole_rolls = weiss_data.get('whole_rolls', 0)
                        expected_whole = (halves + 1) // 2  # Round up
                        
                        if halves == 11 and whole_rolls == 6:
                            self.log_test("Shopping List Calculation", True, 
                                        f"Correct: 11 white halves → 6 whole rolls")
                            success_count += 1
                        else:
                            self.log_test("Shopping List Calculation", False, 
                                        f"Expected 11 halves → 6 whole, got {halves} → {whole_rolls}")
                    
                    # Check seeded rolls: 3 halves should become 2 whole rolls
                    if 'koerner' in shopping_list:
                        koerner_data = shopping_list['koerner']
                        halves = koerner_data.get('halves', 0)
                        whole_rolls = koerner_data.get('whole_rolls', 0)
                        
                        if halves == 3 and whole_rolls == 2:
                            self.log_test("Seeded Rolls Calculation", True, 
                                        f"Correct: 3 seeded halves → 2 whole rolls")
                            success_count += 1
                        else:
                            self.log_test("Seeded Rolls Calculation", False, 
                                        f"Expected 3 halves → 2 whole, got {halves} → {whole_rolls}")
                
                # Test total toppings aggregation
                total_toppings = summary.get('total_toppings', {})
                if total_toppings:
                    # Should have aggregated all toppings across all orders
                    expected_toppings = ['ruehrei', 'kaese', 'schinken', 'salami', 'butter']
                    found_toppings = list(total_toppings.keys())
                    
                    if all(topping in found_toppings for topping in expected_toppings):
                        self.log_test("Total Toppings Aggregation", True, 
                                    f"All toppings aggregated: {found_toppings}")
                        success_count += 1
                    else:
                        self.log_test("Total Toppings Aggregation", False, 
                                    f"Missing toppings. Found: {found_toppings}")
                
            else:
                self.log_test("Daily Summary", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_employee_profile_roll_halves_display(self):
        """Test employee profile with roll halves display and German descriptions"""
        print("\n=== Testing Employee Profile with Roll Halves Display ===")
        
        if not self.employees:
            self.log_test("Employee Profile Roll Halves", False, "No employees available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Create test order with roll halves and lunch option
        try:
            profile_test_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "roll_type": "weiss",
                        "roll_halves": 3,
                        "toppings": ["ruehrei", "kaese", "schinken"],
                        "has_lunch": True
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=profile_test_order)
            if response.status_code == 200:
                self.log_test("Create Profile Test Order", True, 
                            "Created order with 3 roll halves and lunch option")
        except Exception as e:
            self.log_test("Create Profile Test Order", False, f"Exception: {str(e)}")
        
        # Test enhanced profile endpoint
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                
                # Check required fields
                required_fields = ['employee', 'order_history', 'total_orders', 'breakfast_total', 'drinks_sweets_total']
                missing_fields = [field for field in required_fields if field not in required_fields]
                
                if not missing_fields:
                    self.log_test("Profile Structure", True, "Profile has all required fields")
                    success_count += 1
                
                # Check for German descriptions showing "Brötchenhälften"
                order_history = profile.get('order_history', [])
                has_german_halves = False
                has_lunch_display = False
                
                for order in order_history:
                    if 'readable_items' in order:
                        for item in order['readable_items']:
                            description = item.get('description', '')
                            # Look for German roll descriptions
                            if any(word in description for word in ['Weißes Brötchen', 'Körnerbrötchen']):
                                has_german_halves = True
                            # Look for lunch option display
                            if 'mit Mittagessen' in description:
                                has_lunch_display = True
                
                if has_german_halves:
                    self.log_test("German Roll Descriptions", True, 
                                "Profile shows German roll type descriptions")
                    success_count += 1
                else:
                    self.log_test("German Roll Descriptions", False, 
                                "Missing German roll descriptions")
                
                if has_lunch_display:
                    self.log_test("Lunch Option Display", True, 
                                "Profile shows lunch option in German ('mit Mittagessen')")
                    success_count += 1
                else:
                    self.log_test("Lunch Option Display", False, 
                                "Missing lunch option display")
                
                # Check balance summaries
                if (isinstance(profile.get('total_orders'), int) and 
                    isinstance(profile.get('breakfast_total'), (int, float)) and
                    isinstance(profile.get('drinks_sweets_total'), (int, float))):
                    self.log_test("Profile Balance Data", True, 
                                f"Valid balance data: {profile['total_orders']} orders, €{profile['breakfast_total']:.2f} breakfast")
                    success_count += 1
                else:
                    self.log_test("Profile Balance Data", False, "Invalid balance data types")
                
            else:
                self.log_test("Employee Profile", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Employee Profile", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def run_all_tests(self):
        """Run all updated feature tests"""
        print("🧪 STARTING COMPREHENSIVE UPDATED CANTEEN SYSTEM TESTS")
        print("=" * 80)
        
        all_tests = [
            ("New Department Structure", self.test_new_department_structure),
            ("Roll Halves Breakfast Logic", self.test_roll_halves_breakfast_logic),
            ("Retroactive Lunch Pricing", self.test_retroactive_lunch_pricing),
            ("Payment Logging System", self.test_payment_logging_system),
            ("Enhanced Daily Summary with Shopping List", self.test_enhanced_daily_summary_shopping_list),
            ("Employee Profile Roll Halves Display", self.test_employee_profile_roll_halves_display)
        ]
        
        passed_tests = 0
        total_tests = len(all_tests)
        
        for test_name, test_func in all_tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"💥 {test_name}: EXCEPTION - {str(e)}")
        
        # Print final summary
        print("\n" + "=" * 80)
        print("🎯 FINAL TEST SUMMARY")
        print("=" * 80)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 EXCELLENT: Updated canteen system is working well!")
        elif success_rate >= 60:
            print("⚠️  GOOD: Most features working, some issues need attention")
        else:
            print("🚨 NEEDS WORK: Multiple critical issues found")
        
        # Print detailed results
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return success_rate >= 80

if __name__ == "__main__":
    print("🚀 Starting Updated German Canteen Management System Tests...")
    print(f"🌐 Testing against: {API_BASE}")
    
    tester = UpdatedCanteenTester()
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)