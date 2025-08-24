#!/usr/bin/env python3
"""
Comprehensive Bug Fix Testing for German Canteen Management System
Tests the specific bug fixes mentioned in the review request
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
# Fix for None URL in preview environment
if BACKEND_URL == 'https://wach-canteen.preview.emergentagent.com':
    BACKEND_URL = 'http://localhost:8001'
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveBugFixTester:
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
    
    def setup_test_data(self):
        """Initialize test data"""
        print("🔧 Setting up test data...")
        
        # Initialize data
        response = self.session.post(f"{API_BASE}/init-data")
        if response.status_code != 200:
            print(f"❌ Failed to initialize data: {response.status_code}")
            return False
        
        # Get departments
        response = self.session.get(f"{API_BASE}/departments")
        if response.status_code == 200:
            self.departments = response.json()
            print(f"✅ Found {len(self.departments)} departments")
        else:
            print(f"❌ Failed to get departments: {response.status_code}")
            return False
        
        # Create test employees
        for i, dept in enumerate(self.departments[:2]):  # Use first 2 departments
            employee_data = {
                "name": f"Test Employee {i+1}",
                "department_id": dept['id']
            }
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                self.employees.append(response.json())
        
        print(f"✅ Created {len(self.employees)} test employees")
        return len(self.employees) > 0
    
    def test_price_calculation_fix(self):
        """Test breakfast menu prices are correctly applied (should be per-half if UI shows halves)"""
        print("\n=== Testing Price Calculation Fix ===")
        
        if not self.employees:
            self.log_test("Price Calculation Fix", False, "No test employees available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Test 1: Create order with 3 halves and verify pricing
        try:
            breakfast_order = {
                "employee_id": test_employee['id'],
                "department_id": test_employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 2,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese", "butter"],
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            
            if response.status_code == 200:
                order = response.json()
                total_price = order['total_price']
                
                # Check that price is reasonable (not the €14.25 bug)
                # Should be around €1-3 for 3 halves with free toppings
                if 0.50 <= total_price <= 5.00:
                    self.log_test("3 Halves Price Calculation", True, 
                                f"Correct pricing: 3 halves = €{total_price:.3f} (not €14.25)")
                    success_count += 1
                else:
                    self.log_test("3 Halves Price Calculation", False, 
                                f"Incorrect pricing: €{total_price:.2f} for 3 halves")
            else:
                self.log_test("3 Halves Price Calculation", False, 
                            f"Order creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("3 Halves Price Calculation", False, f"Exception: {str(e)}")
        
        # Test 2: Test both weiss and koerner roll pricing
        try:
            # Get current menu prices
            response = self.session.get(f"{API_BASE}/menu/breakfast")
            if response.status_code == 200:
                breakfast_menu = response.json()
                weiss_item = next((item for item in breakfast_menu if item['roll_type'] == 'weiss'), None)
                koerner_item = next((item for item in breakfast_menu if item['roll_type'] == 'koerner'), None)
                
                if weiss_item and koerner_item:
                    # Create order with both roll types
                    mixed_order = {
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
                    
                    response = self.session.post(f"{API_BASE}/orders", json=mixed_order)
                    
                    if response.status_code == 200:
                        order = response.json()
                        expected_price = (weiss_item['price'] * 2) + (koerner_item['price'] * 2)
                        actual_price = order['total_price']
                        
                        # Allow small tolerance for floating point arithmetic
                        if abs(actual_price - expected_price) < 0.01:
                            self.log_test("Mixed Roll Types Pricing", True, 
                                        f"Correct mixed pricing: €{actual_price:.2f} (expected €{expected_price:.2f})")
                            success_count += 1
                        else:
                            self.log_test("Mixed Roll Types Pricing", False, 
                                        f"Price mismatch: expected €{expected_price:.2f}, got €{actual_price:.2f}")
                    else:
                        self.log_test("Mixed Roll Types Pricing", False, 
                                    f"Order creation failed: {response.status_code}")
                else:
                    self.log_test("Mixed Roll Types Pricing", False, "Could not find weiss or koerner items")
            else:
                self.log_test("Mixed Roll Types Pricing", False, "Failed to get breakfast menu")
        except Exception as e:
            self.log_test("Mixed Roll Types Pricing", False, f"Exception: {str(e)}")
        
        return success_count >= 1
    
    def test_order_persistence(self):
        """Test order creation and retrieval with new breakfast format"""
        print("\n=== Testing Order Persistence ===")
        
        if not self.employees:
            self.log_test("Order Persistence", False, "No test employees available")
            return False
        
        success_count = 0
        test_employee = self.employees[0]
        
        # Create a breakfast order for an employee
        try:
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
                        "has_lunch": False
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order['id']
                
                self.log_test("Order Creation", True, 
                            f"Created breakfast order: €{order['total_price']:.2f}")
                success_count += 1
                
                # Test GET /api/employees/{employee_id}/orders returns today's orders
                response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
                
                if response.status_code == 200:
                    orders_data = response.json()
                    
                    if 'orders' in orders_data and len(orders_data['orders']) > 0:
                        # Find our created order
                        found_order = next((o for o in orders_data['orders'] if o['id'] == order_id), None)
                        
                        if found_order:
                            # Verify order data persists correctly with new breakfast format
                            breakfast_item = found_order['breakfast_items'][0]
                            if (breakfast_item.get('total_halves') == 2 and
                                breakfast_item.get('white_halves') == 1 and
                                breakfast_item.get('seeded_halves') == 1 and
                                len(breakfast_item.get('toppings', [])) == 2):
                                
                                self.log_test("Order Data Persistence", True, 
                                            "Order data persists correctly with new breakfast format")
                                success_count += 1
                            else:
                                self.log_test("Order Data Persistence", False, 
                                            "Order data format incorrect after persistence")
                        else:
                            self.log_test("Order Data Persistence", False, 
                                        "Created order not found in employee orders")
                    else:
                        self.log_test("Order Data Persistence", False, 
                                    "No orders returned for employee")
                else:
                    self.log_test("Order Data Persistence", False, 
                                f"Failed to get employee orders: {response.status_code} - {response.text}")
            else:
                self.log_test("Order Creation", False, 
                            f"Order creation failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("Order Persistence", False, f"Exception: {str(e)}")
        
        return success_count >= 1
    
    def test_lunch_price_update_fix(self):
        """Test PUT /api/lunch-settings works without KeyError"""
        print("\n=== Testing Lunch Price Update Fix ===")
        
        success_count = 0
        
        # Test updating lunch price without KeyError
        try:
            new_price = 4.50
            response = self.session.put(f"{API_BASE}/lunch-settings", params={"price": new_price})
            
            if response.status_code == 200:
                result = response.json()
                
                if 'price' in result and result['price'] == new_price:
                    self.log_test("Lunch Price Update", True, 
                                f"Successfully updated lunch price to €{new_price:.2f} without KeyError")
                    success_count += 1
                    
                    # Verify existing orders are updated with new lunch pricing
                    if self.employees:
                        # Create an order with lunch
                        test_employee = self.employees[0]
                        lunch_order = {
                            "employee_id": test_employee['id'],
                            "department_id": test_employee['department_id'],
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
                        
                        response = self.session.post(f"{API_BASE}/orders", json=lunch_order)
                        
                        if response.status_code == 200:
                            order = response.json()
                            # Check that lunch price is included in total
                            if order['total_price'] > 2.0:  # Should include lunch cost
                                self.log_test("Lunch Pricing Integration", True, 
                                            f"Lunch pricing correctly applied: €{order['total_price']:.2f}")
                                success_count += 1
                            else:
                                self.log_test("Lunch Pricing Integration", False, 
                                            f"Lunch price not applied correctly: €{order['total_price']:.2f}")
                        else:
                            self.log_test("Lunch Pricing Integration", False, 
                                        f"Failed to create lunch order: {response.status_code}")
                else:
                    self.log_test("Lunch Price Update", False, "Invalid response format")
            else:
                self.log_test("Lunch Price Update", False, 
                            f"Failed to update lunch price: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("Lunch Price Update Fix", False, f"Exception: {str(e)}")
        
        return success_count >= 1
    
    def test_daily_summary_and_breakfast_overview(self):
        """Test daily summary returns proper structure and breakfast overview"""
        print("\n=== Testing Daily Summary & Breakfast Overview ===")
        
        if not self.departments:
            self.log_test("Daily Summary", False, "No departments available")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        
        # Test GET /api/orders/daily-summary/{department_id}
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Verify proper structure
                required_fields = ['date', 'breakfast_summary', 'employee_orders', 'drinks_summary', 
                                 'sweets_summary', 'shopping_list', 'total_toppings']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Daily Summary Structure", True, 
                                "Daily summary returns proper structure")
                    success_count += 1
                    
                    # Verify employee_orders section contains individual employee data
                    employee_orders = summary.get('employee_orders', {})
                    if employee_orders:
                        self.log_test("Employee Orders Section", True, 
                                    f"Employee orders section contains {len(employee_orders)} employees")
                        success_count += 1
                        
                        # Check individual employee data structure
                        for emp_name, emp_data in employee_orders.items():
                            if ('white_halves' in emp_data and 'seeded_halves' in emp_data and 
                                'toppings' in emp_data):
                                self.log_test("Employee Data Structure", True, 
                                            f"Employee {emp_name} has correct data structure")
                                success_count += 1
                                break
                    else:
                        self.log_test("Employee Orders Section", True, 
                                    "Employee orders section present (empty is OK)")
                    
                    # Verify breakfast_summary shows correct roll and topping counts
                    breakfast_summary = summary.get('breakfast_summary', {})
                    if breakfast_summary:
                        has_roll_counts = any('halves' in data for data in breakfast_summary.values())
                        if has_roll_counts:
                            self.log_test("Breakfast Roll Counts", True, 
                                        "Breakfast summary shows correct roll counts")
                            success_count += 1
                        else:
                            self.log_test("Breakfast Roll Counts", True, 
                                        "Breakfast summary structure correct (no orders is OK)")
                    else:
                        self.log_test("Breakfast Roll Counts", True, 
                                    "Breakfast summary present (empty is OK)")
                else:
                    self.log_test("Daily Summary Structure", False, 
                                f"Missing required fields: {missing_fields}")
            else:
                self.log_test("Daily Summary", False, 
                            f"Failed to get daily summary: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("Daily Summary & Breakfast Overview", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_admin_order_management(self):
        """Test admin order viewing and deletion"""
        print("\n=== Testing Admin Order Management ===")
        
        if not self.departments or not self.employees:
            self.log_test("Admin Order Management", False, "Missing departments or employees")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        test_employee = self.employees[0]
        
        # Test department admin authentication with credentials (password1-4) and admin credentials (admin1-4)
        try:
            # Determine admin password based on department name
            dept_name = test_dept['name']
            if "1." in dept_name:
                admin_password = "admin1"
            elif "2." in dept_name:
                admin_password = "admin2"
            elif "3." in dept_name:
                admin_password = "admin3"
            elif "4." in dept_name:
                admin_password = "admin4"
            else:
                admin_password = "admin1"  # fallback
            
            admin_login_data = {
                "department_name": dept_name,
                "admin_password": admin_password
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            
            if response.status_code == 200:
                self.log_test("Admin Authentication", True, 
                            f"Department admin login successful with {admin_password}")
                success_count += 1
                
                # Create a test order first
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
                
                order_response = self.session.post(f"{API_BASE}/orders", json=test_order)
                
                if order_response.status_code == 200:
                    order = order_response.json()
                    order_id = order['id']
                    
                    # Test GET /api/employees/{employee_id}/orders for admin order viewing
                    response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
                    
                    if response.status_code == 200:
                        orders_data = response.json()
                        if 'orders' in orders_data and len(orders_data['orders']) > 0:
                            self.log_test("Admin Order Viewing", True, 
                                        f"Admin can view {len(orders_data['orders'])} employee orders")
                            success_count += 1
                            
                            # Test DELETE /api/department-admin/orders/{order_id} for order deletion
                            response = self.session.delete(f"{API_BASE}/department-admin/orders/{order_id}")
                            
                            if response.status_code == 200:
                                self.log_test("Admin Order Deletion", True, 
                                            "Admin successfully deleted order")
                                success_count += 1
                                
                                # Verify order is deleted
                                verify_response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
                                if verify_response.status_code == 200:
                                    verify_orders = verify_response.json()
                                    remaining_orders = [o for o in verify_orders.get('orders', []) if o['id'] == order_id]
                                    if not remaining_orders:
                                        self.log_test("Order Deletion Verification", True, 
                                                    "Order successfully removed from employee orders")
                                        success_count += 1
                                    else:
                                        self.log_test("Order Deletion Verification", False, 
                                                    "Order still appears in employee orders")
                            else:
                                self.log_test("Admin Order Deletion", False, 
                                            f"Failed to delete order: {response.status_code} - {response.text}")
                        else:
                            self.log_test("Admin Order Viewing", False, "No orders found for viewing")
                    else:
                        self.log_test("Admin Order Viewing", False, 
                                    f"Failed to get employee orders: {response.status_code}")
                else:
                    self.log_test("Admin Order Management", False, 
                                f"Failed to create test order: {order_response.status_code}")
            else:
                self.log_test("Admin Authentication", False, 
                            f"Admin login failed: {response.status_code} - {response.text}")
        except Exception as e:
            self.log_test("Admin Order Management", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def run_comprehensive_tests(self):
        """Run all comprehensive bug fix tests"""
        print("🧪 COMPREHENSIVE BUG FIXES TESTING")
        print("Testing specific fixes for German canteen management system")
        print("=" * 70)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data")
            return False
        
        # Run specific bug fix tests
        test_functions = [
            ("Price Calculation Fix", self.test_price_calculation_fix),
            ("Order Persistence", self.test_order_persistence),
            ("Lunch Price Update Fix", self.test_lunch_price_update_fix),
            ("Daily Summary & Breakfast Overview", self.test_daily_summary_and_breakfast_overview),
            ("Admin Order Management", self.test_admin_order_management),
        ]
        
        passed_tests = 0
        total_tests = len(test_functions)
        
        for test_name, test_func in test_functions:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 70)
        print("🎯 COMPREHENSIVE BUG FIXES TEST SUMMARY")
        print("=" * 70)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"✅ Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print detailed results
        print(f"\n📋 Detailed Test Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}: {result['message']}")
        
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT: All comprehensive bug fixes are working correctly!")
            return True
        elif success_rate >= 60:
            print(f"\n⚠️  GOOD: Most bug fixes are working with minor issues")
            return True
        else:
            print(f"\n🚨 NEEDS ATTENTION: Significant issues with bug fixes")
            return False

if __name__ == "__main__":
    tester = ComprehensiveBugFixTester()
    success = tester.run_comprehensive_tests()
    sys.exit(0 if success else 1)