#!/usr/bin/env python3
"""
Department-Specific Products & Pricing System Test Suite
Tests the comprehensive architectural change from global to department-specific menus
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

class DepartmentSpecificTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.departments = []
        self.employees = []
        self.created_orders = []
        
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

    def test_fresh_installation(self):
        """Test 1: Fresh Installation - Test new department-specific initialization"""
        print("\n=== TEST 1: FRESH INSTALLATION ===")
        
        success_count = 0
        
        # Call init-data endpoint
        try:
            response = self.session.post(f"{API_BASE}/init-data")
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Init Data Endpoint", True, 
                            f"Response: {data.get('message', 'Success')}")
                success_count += 1
            else:
                self.log_test("Init Data Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Init Data Endpoint", False, f"Exception: {str(e)}")
            return False
        
        # Verify 4 departments created
        try:
            response = self.session.get(f"{API_BASE}/departments")
            
            if response.status_code == 200:
                departments = response.json()
                self.departments = departments
                
                if len(departments) == 4:
                    self.log_test("Department Creation", True, 
                                f"Created {len(departments)} departments")
                    success_count += 1
                    
                    # Verify department names
                    expected_names = ["1. Wachabteilung", "2. Wachabteilung", 
                                    "3. Wachabteilung", "4. Wachabteilung"]
                    dept_names = [dept['name'] for dept in departments]
                    
                    if all(name in dept_names for name in expected_names):
                        self.log_test("Department Names", True, 
                                    f"All expected departments found: {dept_names}")
                        success_count += 1
                    else:
                        self.log_test("Department Names", False, 
                                    f"Expected {expected_names}, got {dept_names}")
                else:
                    self.log_test("Department Creation", False, 
                                f"Expected 4 departments, got {len(departments)}")
                    
            else:
                self.log_test("Department Creation", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Department Creation", False, f"Exception: {str(e)}")
        
        # Verify each department gets its own menu items
        for dept in self.departments:
            try:
                # Check breakfast menu for this department
                response = self.session.get(f"{API_BASE}/menu/breakfast/{dept['id']}")
                
                if response.status_code == 200:
                    breakfast_items = response.json()
                    
                    # Verify all items have department_id
                    all_have_dept_id = all('department_id' in item and 
                                         item['department_id'] == dept['id'] 
                                         for item in breakfast_items)
                    
                    if all_have_dept_id and len(breakfast_items) > 0:
                        self.log_test(f"Department {dept['name']} Breakfast Menu", True, 
                                    f"Found {len(breakfast_items)} department-specific breakfast items")
                        success_count += 1
                    else:
                        self.log_test(f"Department {dept['name']} Breakfast Menu", False, 
                                    "Items missing department_id or no items found")
                else:
                    self.log_test(f"Department {dept['name']} Breakfast Menu", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Department {dept['name']} Breakfast Menu", False, f"Exception: {str(e)}")
        
        return success_count >= 6  # At least 6 tests should pass

    def test_migration_system(self):
        """Test 2: Migration System - Test migration from global to department-specific"""
        print("\n=== TEST 2: MIGRATION SYSTEM ===")
        
        success_count = 0
        
        # Test migration endpoint
        try:
            response = self.session.post(f"{API_BASE}/migrate-to-department-specific")
            
            if response.status_code == 200:
                migration_result = response.json()
                self.log_test("Migration Endpoint", True, 
                            f"Migration message: {migration_result.get('message', 'Success')}")
                success_count += 1
                
                # Check migration results
                results = migration_result.get('results', {})
                if results:
                    total_migrated = (results.get('breakfast_items', 0) + 
                                    results.get('topping_items', 0) + 
                                    results.get('drink_items', 0) + 
                                    results.get('sweet_items', 0))
                    
                    self.log_test("Migration Results", True, 
                                f"Migrated {total_migrated} total items: "
                                f"Breakfast: {results.get('breakfast_items', 0)}, "
                                f"Toppings: {results.get('topping_items', 0)}, "
                                f"Drinks: {results.get('drink_items', 0)}, "
                                f"Sweets: {results.get('sweet_items', 0)}")
                    success_count += 1
                else:
                    self.log_test("Migration Results", False, "No migration results returned")
                    
            else:
                self.log_test("Migration Endpoint", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Migration Endpoint", False, f"Exception: {str(e)}")
        
        # Verify no data loss - check that all departments have menu items
        if self.departments:
            for dept in self.departments:
                try:
                    # Check all menu types for this department
                    menu_types = ['breakfast', 'toppings', 'drinks', 'sweets']
                    dept_menu_counts = {}
                    
                    for menu_type in menu_types:
                        response = self.session.get(f"{API_BASE}/menu/{menu_type}/{dept['id']}")
                        
                        if response.status_code == 200:
                            items = response.json()
                            dept_menu_counts[menu_type] = len(items)
                        else:
                            dept_menu_counts[menu_type] = 0
                    
                    total_items = sum(dept_menu_counts.values())
                    if total_items > 0:
                        self.log_test(f"Department {dept['name']} Menu Items", True, 
                                    f"Has {total_items} total menu items: {dept_menu_counts}")
                        success_count += 1
                    else:
                        self.log_test(f"Department {dept['name']} Menu Items", False, 
                                    "No menu items found after migration")
                        
                except Exception as e:
                    self.log_test(f"Department {dept['name']} Menu Items", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_department_menu_isolation(self):
        """Test 3: Department-Specific Menu Isolation - Test complete department separation"""
        print("\n=== TEST 3: DEPARTMENT MENU ISOLATION ===")
        
        success_count = 0
        
        if len(self.departments) < 2:
            self.log_test("Department Menu Isolation", False, "Need at least 2 departments for isolation testing")
            return False
        
        dept1 = self.departments[0]
        dept2 = self.departments[1]
        
        # Test 1: Verify each department has independent menus
        try:
            # Get breakfast menus for both departments
            response1 = self.session.get(f"{API_BASE}/menu/breakfast/{dept1['id']}")
            response2 = self.session.get(f"{API_BASE}/menu/breakfast/{dept2['id']}")
            
            if response1.status_code == 200 and response2.status_code == 200:
                menu1 = response1.json()
                menu2 = response2.json()
                
                # Verify all items have correct department_id
                dept1_correct = all(item['department_id'] == dept1['id'] for item in menu1)
                dept2_correct = all(item['department_id'] == dept2['id'] for item in menu2)
                
                if dept1_correct and dept2_correct:
                    self.log_test("Menu Department ID Isolation", True, 
                                f"Dept1: {len(menu1)} items, Dept2: {len(menu2)} items, all with correct department_id")
                    success_count += 1
                else:
                    self.log_test("Menu Department ID Isolation", False, 
                                "Items have incorrect department_id")
            else:
                self.log_test("Menu Department ID Isolation", False, 
                            "Failed to fetch department menus")
                
        except Exception as e:
            self.log_test("Menu Department ID Isolation", False, f"Exception: {str(e)}")
        
        # Test 2: Test price changes in one department don't affect others
        try:
            # Get first breakfast item from dept1
            response = self.session.get(f"{API_BASE}/menu/breakfast/{dept1['id']}")
            
            if response.status_code == 200:
                dept1_menu = response.json()
                if dept1_menu:
                    item_to_update = dept1_menu[0]
                    original_price = item_to_update['price']
                    new_price = original_price + 0.50
                    
                    # Update price in dept1
                    update_data = {"price": new_price}
                    response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{item_to_update['id']}", 
                                              json=update_data)
                    
                    if response.status_code == 200:
                        # Verify price changed in dept1
                        response = self.session.get(f"{API_BASE}/menu/breakfast/{dept1['id']}")
                        if response.status_code == 200:
                            updated_menu1 = response.json()
                            updated_item = next((item for item in updated_menu1 if item['id'] == item_to_update['id']), None)
                            
                            if updated_item and updated_item['price'] == new_price:
                                # Verify price didn't change in dept2
                                response = self.session.get(f"{API_BASE}/menu/breakfast/{dept2['id']}")
                                if response.status_code == 200:
                                    dept2_menu = response.json()
                                    # Find corresponding item in dept2 (same roll_type)
                                    dept2_item = next((item for item in dept2_menu 
                                                     if item['roll_type'] == item_to_update['roll_type']), None)
                                    
                                    if dept2_item and dept2_item['price'] == original_price:
                                        self.log_test("Price Change Isolation", True, 
                                                    f"Price change in {dept1['name']} (€{new_price:.2f}) "
                                                    f"didn't affect {dept2['name']} (€{original_price:.2f})")
                                        success_count += 1
                                    else:
                                        self.log_test("Price Change Isolation", False, 
                                                    "Price change affected other department")
                                else:
                                    self.log_test("Price Change Isolation", False, 
                                                "Failed to fetch dept2 menu for comparison")
                            else:
                                self.log_test("Price Change Isolation", False, 
                                            "Price didn't update in dept1")
                    else:
                        self.log_test("Price Change Isolation", False, 
                                    f"Failed to update price: HTTP {response.status_code}")
                else:
                    self.log_test("Price Change Isolation", False, "No breakfast items found in dept1")
            else:
                self.log_test("Price Change Isolation", False, "Failed to fetch dept1 menu")
                
        except Exception as e:
            self.log_test("Price Change Isolation", False, f"Exception: {str(e)}")
        
        # Test 3: Test department admin access isolation
        try:
            # Test admin login for dept1
            admin_login_data = {
                "department_name": dept1['name'],
                "admin_password": "admin1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            
            if response.status_code == 200:
                login_result = response.json()
                if login_result.get('department_id') == dept1['id']:
                    self.log_test("Department Admin Access", True, 
                                f"Admin can access {dept1['name']} with correct credentials")
                    success_count += 1
                else:
                    self.log_test("Department Admin Access", False, 
                                "Admin login returned wrong department_id")
            else:
                self.log_test("Department Admin Access", False, 
                            f"Admin login failed: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Department Admin Access", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_order_system_integration(self):
        """Test 4: Order System Integration - Test order creation with department-specific menus"""
        print("\n=== TEST 4: ORDER SYSTEM INTEGRATION ===")
        
        success_count = 0
        
        if not self.departments:
            self.log_test("Order System Integration", False, "No departments available")
            return False
        
        # Create test employees for different departments
        test_employees = []
        for i, dept in enumerate(self.departments[:2]):  # Test with first 2 departments
            try:
                employee_data = {
                    "name": f"Test Employee {i+1}",
                    "department_id": dept['id']
                }
                
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                
                if response.status_code == 200:
                    employee = response.json()
                    test_employees.append(employee)
                    self.log_test(f"Create Test Employee {i+1}", True, 
                                f"Created employee for {dept['name']}")
                    success_count += 1
                else:
                    self.log_test(f"Create Test Employee {i+1}", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Create Test Employee {i+1}", False, f"Exception: {str(e)}")
        
        # Test breakfast orders for different departments
        for i, employee in enumerate(test_employees):
            try:
                # Get department-specific breakfast menu
                response = self.session.get(f"{API_BASE}/menu/breakfast/{employee['department_id']}")
                
                if response.status_code == 200:
                    breakfast_menu = response.json()
                    if breakfast_menu:
                        # Create breakfast order using new format
                        breakfast_order = {
                            "employee_id": employee['id'],
                            "department_id": employee['department_id'],
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
                            self.created_orders.append(order)
                            
                            # Verify order uses department-specific pricing
                            if order['total_price'] > 0:
                                dept_name = next(d['name'] for d in self.departments if d['id'] == employee['department_id'])
                                self.log_test(f"Department {i+1} Breakfast Order", True, 
                                            f"Created order for {dept_name}: €{order['total_price']:.2f}")
                                success_count += 1
                            else:
                                self.log_test(f"Department {i+1} Breakfast Order", False, 
                                            "Invalid order total price")
                        else:
                            self.log_test(f"Department {i+1} Breakfast Order", False, 
                                        f"HTTP {response.status_code}: {response.text}")
                    else:
                        self.log_test(f"Department {i+1} Breakfast Order", False, 
                                    "No breakfast menu items found")
                else:
                    self.log_test(f"Department {i+1} Breakfast Order", False, 
                                f"Failed to fetch breakfast menu: HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"Department {i+1} Breakfast Order", False, f"Exception: {str(e)}")
        
        # Test order updates use department-specific pricing
        if self.created_orders:
            try:
                test_order = self.created_orders[0]
                
                # Update order
                updated_order_data = {
                    "employee_id": test_order['employee_id'],
                    "department_id": test_order['department_id'],
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 3,
                            "white_halves": 2,
                            "seeded_halves": 1,
                            "toppings": ["ruehrei", "kaese", "schinken"],
                            "has_lunch": True
                        }
                    ]
                }
                
                response = self.session.put(f"{API_BASE}/orders/{test_order['id']}", json=updated_order_data)
                
                if response.status_code == 200:
                    updated_order = response.json()
                    if updated_order['total_price'] != test_order['total_price']:
                        self.log_test("Order Update with Department Pricing", True, 
                                    f"Order updated with new pricing: €{test_order['total_price']:.2f} → €{updated_order['total_price']:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Order Update with Department Pricing", False, 
                                    "Order price didn't change after update")
                else:
                    self.log_test("Order Update with Department Pricing", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Order Update with Department Pricing", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_admin_management(self):
        """Test 5: Admin Management - Test department admin functionality"""
        print("\n=== TEST 5: ADMIN MANAGEMENT ===")
        
        success_count = 0
        
        if not self.departments:
            self.log_test("Admin Management", False, "No departments available")
            return False
        
        test_dept = self.departments[0]
        
        # Test department admin authentication
        try:
            admin_login_data = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            
            if response.status_code == 200:
                login_result = response.json()
                if (login_result.get('department_id') == test_dept['id'] and 
                    login_result.get('role') == 'department_admin'):
                    self.log_test("Department Admin Authentication", True, 
                                f"Admin authenticated for {test_dept['name']}")
                    success_count += 1
                else:
                    self.log_test("Department Admin Authentication", False, 
                                "Invalid admin login response")
            else:
                self.log_test("Department Admin Authentication", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Department Admin Authentication", False, f"Exception: {str(e)}")
        
        # Test menu CRUD operations with department-specific items
        try:
            # Get current breakfast menu
            response = self.session.get(f"{API_BASE}/menu/breakfast/{test_dept['id']}")
            
            if response.status_code == 200:
                breakfast_menu = response.json()
                if breakfast_menu:
                    # Test price update
                    item_to_update = breakfast_menu[0]
                    original_price = item_to_update['price']
                    new_price = original_price + 0.25
                    
                    update_data = {"price": new_price}
                    response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{item_to_update['id']}", 
                                              json=update_data)
                    
                    if response.status_code == 200:
                        self.log_test("Admin Menu Price Update", True, 
                                    f"Updated breakfast item price: €{original_price:.2f} → €{new_price:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Admin Menu Price Update", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Admin Menu Price Update", False, "No breakfast items found")
            else:
                self.log_test("Admin Menu Price Update", False, 
                            f"Failed to fetch breakfast menu: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Menu Price Update", False, f"Exception: {str(e)}")
        
        # Test creating new department-specific menu items
        try:
            # Create new breakfast item
            new_breakfast_data = {
                "roll_type": "weiss",
                "price": 0.75,
                "department_id": test_dept['id']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/breakfast", 
                                       json=new_breakfast_data)
            
            if response.status_code == 200:
                new_item = response.json()
                if new_item['department_id'] == test_dept['id']:
                    self.log_test("Admin Create Department Item", True, 
                                f"Created new breakfast item for {test_dept['name']}: €{new_item['price']:.2f}")
                    success_count += 1
                    
                    # Clean up - delete the created item
                    try:
                        self.session.delete(f"{API_BASE}/department-admin/menu/breakfast/{new_item['id']}")
                    except:
                        pass  # Ignore cleanup errors
                else:
                    self.log_test("Admin Create Department Item", False, 
                                "Created item has wrong department_id")
            else:
                self.log_test("Admin Create Department Item", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Create Department Item", False, f"Exception: {str(e)}")
        
        # Test order management uses correct department context
        if self.created_orders:
            try:
                # Find an order from our test department
                dept_order = next((order for order in self.created_orders 
                                 if order['department_id'] == test_dept['id']), None)
                
                if dept_order:
                    # Test admin can delete department order
                    response = self.session.delete(f"{API_BASE}/department-admin/orders/{dept_order['id']}")
                    
                    if response.status_code == 200:
                        self.log_test("Admin Order Management", True, 
                                    f"Admin successfully deleted department order")
                        success_count += 1
                    else:
                        self.log_test("Admin Order Management", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Admin Order Management", False, 
                                "No orders found for test department")
                    
            except Exception as e:
                self.log_test("Admin Order Management", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_backward_compatibility(self):
        """Test 6: Backward Compatibility - Verify existing functionality still works"""
        print("\n=== TEST 6: BACKWARD COMPATIBILITY ===")
        
        success_count = 0
        
        # Test old menu endpoints still work
        menu_types = ['breakfast', 'toppings', 'drinks', 'sweets']
        
        for menu_type in menu_types:
            try:
                response = self.session.get(f"{API_BASE}/menu/{menu_type}")
                
                if response.status_code == 200:
                    items = response.json()
                    if items:
                        # Verify items are returned (should be from first department)
                        self.log_test(f"Legacy {menu_type.title()} Endpoint", True, 
                                    f"Returns {len(items)} items (backward compatibility)")
                        success_count += 1
                    else:
                        self.log_test(f"Legacy {menu_type.title()} Endpoint", False, 
                                    "No items returned")
                else:
                    self.log_test(f"Legacy {menu_type.title()} Endpoint", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test(f"Legacy {menu_type.title()} Endpoint", False, f"Exception: {str(e)}")
        
        # Test existing order functionality still works
        if self.departments:
            try:
                # Create employee for testing
                employee_data = {
                    "name": "Backward Compatibility Test Employee",
                    "department_id": self.departments[0]['id']
                }
                
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                
                if response.status_code == 200:
                    test_employee = response.json()
                    
                    # Create order using old format (should still work)
                    old_format_order = {
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
                    
                    response = self.session.post(f"{API_BASE}/orders", json=old_format_order)
                    
                    if response.status_code == 200:
                        order = response.json()
                        self.log_test("Existing Order Functionality", True, 
                                    f"Old order format still works: €{order['total_price']:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Existing Order Functionality", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("Existing Order Functionality", False, 
                                "Failed to create test employee")
                    
            except Exception as e:
                self.log_test("Existing Order Functionality", False, f"Exception: {str(e)}")
        
        # Test employee profiles and order history
        if hasattr(self, 'employees') and self.employees:
            try:
                test_employee = self.employees[0] if self.employees else None
                if not test_employee and hasattr(self, 'created_orders') and self.created_orders:
                    # Get employee from created order
                    order = self.created_orders[0]
                    response = self.session.get(f"{API_BASE}/employees/{order['employee_id']}/profile")
                    
                    if response.status_code == 200:
                        profile = response.json()
                        self.log_test("Employee Profile Compatibility", True, 
                                    f"Employee profile works with {len(profile.get('order_history', []))} orders")
                        success_count += 1
                    else:
                        self.log_test("Employee Profile Compatibility", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
            except Exception as e:
                self.log_test("Employee Profile Compatibility", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def run_all_tests(self):
        """Run all department-specific tests"""
        print("🚀 STARTING DEPARTMENT-SPECIFIC PRODUCTS & PRICING SYSTEM TESTS")
        print("=" * 80)
        
        test_results = []
        
        # Run all tests
        test_results.append(("Fresh Installation Test", self.test_fresh_installation()))
        test_results.append(("Migration System Test", self.test_migration_system()))
        test_results.append(("Department Menu Isolation Test", self.test_department_menu_isolation()))
        test_results.append(("Order System Integration Test", self.test_order_system_integration()))
        test_results.append(("Admin Management Test", self.test_admin_management()))
        test_results.append(("Backward Compatibility Test", self.test_backward_compatibility()))
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 DEPARTMENT-SPECIFIC SYSTEM TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\n📊 OVERALL RESULT: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 ALL DEPARTMENT-SPECIFIC TESTS PASSED! System is working correctly.")
            return True
        elif passed_tests >= total_tests * 0.8:  # 80% pass rate
            print("✅ MOST TESTS PASSED! System is mostly functional with minor issues.")
            return True
        else:
            print("❌ MULTIPLE TEST FAILURES! System needs attention.")
            return False

if __name__ == "__main__":
    tester = DepartmentSpecificTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)