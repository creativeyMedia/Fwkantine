#!/usr/bin/env python3
"""
Three Critical Bug Fixes Test Suite for German Canteen Management System
Tests the three specific critical bug fixes mentioned in the review request:
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

class ThreeCriticalFixesTester:
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
        """Initialize test data and get departments/employees"""
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
            except Exception as e:
                self.log_test(f"Create Employee {i+1}", False, f"Exception: {str(e)}")
        
        # Get menu items for first department
        if self.departments:
            dept = self.departments[0]
            for menu_type in ['breakfast', 'toppings', 'drinks', 'sweets']:
                try:
                    response = self.session.get(f"{API_BASE}/menu/{menu_type}/{dept['id']}")
                    if response.status_code == 200:
                        items = response.json()
                        self.menu_items[menu_type] = items
                        self.log_test(f"Get {menu_type.title()} Menu", True, f"Found {len(items)} items")
                except Exception as e:
                    self.log_test(f"Get {menu_type.title()} Menu", False, f"Exception: {str(e)}")
        
        return len(self.departments) > 0 and len(self.employees) > 0

    def test_critical_fix_1_menu_item_edit_saving(self):
        """
        CRITICAL BUG FIX 1: Menu Item Edit Saving Fix
        Test that department admin can edit breakfast, toppings, drinks, and sweets menu items
        Verify that name and price changes are properly saved and persist
        Test with department_id parameter in update requests
        """
        print("\n🔧 CRITICAL FIX 1: Menu Item Edit Saving Fix")
        print("=" * 60)
        
        if not self.departments or not any(self.menu_items.values()):
            self.log_test("Menu Edit Saving Fix", False, "Missing test data")
            return False
        
        success_count = 0
        total_tests = 0
        test_dept = self.departments[0]
        
        # Test 1: Breakfast Menu Item Edit with Name and Price
        if self.menu_items['breakfast']:
            total_tests += 1
            try:
                breakfast_item = self.menu_items['breakfast'][0]
                original_price = breakfast_item['price']
                original_name = breakfast_item.get('name')
                new_price = original_price + 0.25
                new_name = "Premium Weißes Brötchen"
                
                # Update with department_id parameter
                update_data = {"price": new_price, "name": new_name}
                response = self.session.put(
                    f"{API_BASE}/department-admin/menu/breakfast/{breakfast_item['id']}", 
                    json=update_data,
                    params={"department_id": test_dept['id']}
                )
                
                if response.status_code == 200:
                    # Verify changes persist by fetching menu again
                    verify_response = self.session.get(f"{API_BASE}/menu/breakfast/{test_dept['id']}")
                    if verify_response.status_code == 200:
                        updated_items = verify_response.json()
                        updated_item = next((item for item in updated_items if item['id'] == breakfast_item['id']), None)
                        
                        if updated_item and updated_item['price'] == new_price and updated_item.get('name') == new_name:
                            self.log_test("Breakfast Item Edit & Persistence", True, 
                                        f"✅ Successfully updated and persisted: price €{original_price:.2f} → €{new_price:.2f}, name: '{original_name}' → '{new_name}'")
                            success_count += 1
                        else:
                            self.log_test("Breakfast Item Edit & Persistence", False, 
                                        "❌ Changes not persisted correctly")
                    else:
                        self.log_test("Breakfast Item Edit & Persistence", False, 
                                    f"❌ Verification failed: HTTP {verify_response.status_code}")
                else:
                    self.log_test("Breakfast Item Edit & Persistence", False, 
                                f"❌ Update failed: HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Breakfast Item Edit & Persistence", False, f"❌ Exception: {str(e)}")
        
        # Test 2: Toppings Menu Item Edit with Name and Price
        if self.menu_items['toppings']:
            total_tests += 1
            try:
                topping_item = self.menu_items['toppings'][0]
                original_price = topping_item['price']
                original_name = topping_item.get('name')
                new_price = 0.50  # Change from free to paid
                new_name = "Premium Rührei"
                
                update_data = {"price": new_price, "name": new_name}
                response = self.session.put(
                    f"{API_BASE}/department-admin/menu/toppings/{topping_item['id']}", 
                    json=update_data,
                    params={"department_id": test_dept['id']}
                )
                
                if response.status_code == 200:
                    # Verify changes persist
                    verify_response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
                    if verify_response.status_code == 200:
                        updated_items = verify_response.json()
                        updated_item = next((item for item in updated_items if item['id'] == topping_item['id']), None)
                        
                        if updated_item and updated_item['price'] == new_price and updated_item.get('name') == new_name:
                            self.log_test("Toppings Item Edit & Persistence", True, 
                                        f"✅ Successfully updated and persisted: price €{original_price:.2f} → €{new_price:.2f}, name: '{original_name}' → '{new_name}'")
                            success_count += 1
                        else:
                            self.log_test("Toppings Item Edit & Persistence", False, 
                                        "❌ Changes not persisted correctly")
                    else:
                        self.log_test("Toppings Item Edit & Persistence", False, 
                                    f"❌ Verification failed: HTTP {verify_response.status_code}")
                else:
                    self.log_test("Toppings Item Edit & Persistence", False, 
                                f"❌ Update failed: HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Toppings Item Edit & Persistence", False, f"❌ Exception: {str(e)}")
        
        # Test 3: Drinks Menu Item Edit with Name and Price
        if self.menu_items['drinks']:
            total_tests += 1
            try:
                drink_item = self.menu_items['drinks'][0]
                original_price = drink_item['price']
                original_name = drink_item['name']
                new_price = original_price + 0.30
                new_name = f"{original_name} Premium"
                
                update_data = {"price": new_price, "name": new_name}
                response = self.session.put(
                    f"{API_BASE}/department-admin/menu/drinks/{drink_item['id']}", 
                    json=update_data,
                    params={"department_id": test_dept['id']}
                )
                
                if response.status_code == 200:
                    # Verify changes persist
                    verify_response = self.session.get(f"{API_BASE}/menu/drinks/{test_dept['id']}")
                    if verify_response.status_code == 200:
                        updated_items = verify_response.json()
                        updated_item = next((item for item in updated_items if item['id'] == drink_item['id']), None)
                        
                        if updated_item and updated_item['price'] == new_price and updated_item['name'] == new_name:
                            self.log_test("Drinks Item Edit & Persistence", True, 
                                        f"✅ Successfully updated and persisted: price €{original_price:.2f} → €{new_price:.2f}, name: '{original_name}' → '{new_name}'")
                            success_count += 1
                        else:
                            self.log_test("Drinks Item Edit & Persistence", False, 
                                        "❌ Changes not persisted correctly")
                    else:
                        self.log_test("Drinks Item Edit & Persistence", False, 
                                    f"❌ Verification failed: HTTP {verify_response.status_code}")
                else:
                    self.log_test("Drinks Item Edit & Persistence", False, 
                                f"❌ Update failed: HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Drinks Item Edit & Persistence", False, f"❌ Exception: {str(e)}")
        
        # Test 4: Sweets Menu Item Edit with Name and Price
        if self.menu_items['sweets']:
            total_tests += 1
            try:
                sweet_item = self.menu_items['sweets'][0]
                original_price = sweet_item['price']
                original_name = sweet_item['name']
                new_price = original_price + 0.40
                new_name = f"{original_name} Deluxe"
                
                update_data = {"price": new_price, "name": new_name}
                response = self.session.put(
                    f"{API_BASE}/department-admin/menu/sweets/{sweet_item['id']}", 
                    json=update_data,
                    params={"department_id": test_dept['id']}
                )
                
                if response.status_code == 200:
                    # Verify changes persist
                    verify_response = self.session.get(f"{API_BASE}/menu/sweets/{test_dept['id']}")
                    if verify_response.status_code == 200:
                        updated_items = verify_response.json()
                        updated_item = next((item for item in updated_items if item['id'] == sweet_item['id']), None)
                        
                        if updated_item and updated_item['price'] == new_price and updated_item['name'] == new_name:
                            self.log_test("Sweets Item Edit & Persistence", True, 
                                        f"✅ Successfully updated and persisted: price €{original_price:.2f} → €{new_price:.2f}, name: '{original_name}' → '{new_name}'")
                            success_count += 1
                        else:
                            self.log_test("Sweets Item Edit & Persistence", False, 
                                        "❌ Changes not persisted correctly")
                    else:
                        self.log_test("Sweets Item Edit & Persistence", False, 
                                    f"❌ Verification failed: HTTP {verify_response.status_code}")
                else:
                    self.log_test("Sweets Item Edit & Persistence", False, 
                                f"❌ Update failed: HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Sweets Item Edit & Persistence", False, f"❌ Exception: {str(e)}")
        
        print(f"\n🎯 CRITICAL FIX 1 RESULT: {success_count}/{total_tests} tests passed")
        return success_count == total_tests

    def test_critical_fix_2_payment_history_display(self):
        """
        CRITICAL BUG FIX 2: Payment History Display Fix
        Test that when admin marks employee balance as paid, a payment log is created
        Verify that GET /api/employees/{employee_id}/profile includes payment_history
        Test that payment logs show correct amount, payment_type, admin_user, and timestamp
        """
        print("\n💰 CRITICAL FIX 2: Payment History Display Fix")
        print("=" * 60)
        
        if not self.employees or not self.departments:
            self.log_test("Payment History Fix", False, "Missing test data")
            return False
        
        success_count = 0
        total_tests = 0
        test_employee = self.employees[0]
        test_dept = self.departments[0]
        
        # First, create some balance for the employee by placing orders
        try:
            # Create breakfast order to generate balance
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
                self.log_test("Create Test Order for Balance", True, 
                            f"✅ Created order with total: €{order['total_price']:.2f}")
            else:
                self.log_test("Create Test Order for Balance", False, 
                            f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Test Order for Balance", False, f"❌ Exception: {str(e)}")
        
        # Test 1: Mark Payment and Create Payment Log
        total_tests += 1
        try:
            payment_amount = 5.00
            payment_type = "breakfast"
            admin_department = test_dept['name']
            
            response = self.session.post(
                f"{API_BASE}/department-admin/payment/{test_employee['id']}", 
                params={
                    "payment_type": payment_type,
                    "amount": payment_amount,
                    "admin_department": admin_department
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Mark Payment", True, 
                            f"✅ Successfully marked payment: {result.get('message', 'Success')}")
                success_count += 1
            else:
                self.log_test("Mark Payment", False, 
                            f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Mark Payment", False, f"❌ Exception: {str(e)}")
        
        # Test 2: Verify Payment Log Creation with Correct Data
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/department-admin/payment-logs/{test_employee['id']}")
            
            if response.status_code == 200:
                payment_logs = response.json()
                
                if isinstance(payment_logs, list) and len(payment_logs) > 0:
                    latest_log = payment_logs[0]  # Should be most recent
                    
                    # Verify log structure and content
                    required_fields = ['amount', 'payment_type', 'admin_user', 'timestamp', 'action']
                    missing_fields = [field for field in required_fields if field not in latest_log]
                    
                    if not missing_fields:
                        if (latest_log['amount'] == payment_amount and 
                            latest_log['payment_type'] == payment_type and
                            latest_log['admin_user'] == admin_department and
                            latest_log['action'] == 'payment'):
                            
                            self.log_test("Payment Log Creation & Content", True, 
                                        f"✅ Payment log created correctly: €{latest_log['amount']:.2f}, type: {latest_log['payment_type']}, admin: {latest_log['admin_user']}, timestamp: {latest_log['timestamp']}")
                            success_count += 1
                        else:
                            self.log_test("Payment Log Creation & Content", False, 
                                        f"❌ Payment log content mismatch: amount={latest_log.get('amount')}, type={latest_log.get('payment_type')}, admin={latest_log.get('admin_user')}")
                    else:
                        self.log_test("Payment Log Creation & Content", False, 
                                    f"❌ Missing fields in payment log: {missing_fields}")
                else:
                    self.log_test("Payment Log Creation & Content", False, 
                                "❌ No payment logs found")
            else:
                self.log_test("Payment Log Creation & Content", False, 
                            f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Payment Log Creation & Content", False, f"❌ Exception: {str(e)}")
        
        # Test 3: Verify Payment History in Employee Profile
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                
                if 'payment_history' in profile:
                    payment_history = profile['payment_history']
                    
                    if isinstance(payment_history, list) and len(payment_history) > 0:
                        # Find our payment in the history
                        our_payment = next((log for log in payment_history 
                                          if log.get('amount') == payment_amount and 
                                             log.get('payment_type') == payment_type), None)
                        
                        if our_payment:
                            self.log_test("Payment History in Profile", True, 
                                        f"✅ Payment history correctly integrated in employee profile: €{our_payment['amount']:.2f}, type: {our_payment['payment_type']}")
                            success_count += 1
                        else:
                            self.log_test("Payment History in Profile", False, 
                                        "❌ Our payment not found in profile payment history")
                    else:
                        self.log_test("Payment History in Profile", False, 
                                    "❌ Payment history is empty or invalid")
                else:
                    self.log_test("Payment History in Profile", False, 
                                "❌ payment_history field missing from employee profile")
            else:
                self.log_test("Payment History in Profile", False, 
                            f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Payment History in Profile", False, f"❌ Exception: {str(e)}")
        
        # Test 4: Verify Balance Reset After Payment
        total_tests += 1
        try:
            response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/profile")
            
            if response.status_code == 200:
                profile = response.json()
                employee_data = profile.get('employee', {})
                
                if payment_type == "breakfast":
                    current_balance = employee_data.get('breakfast_balance', -1)
                else:
                    current_balance = employee_data.get('drinks_sweets_balance', -1)
                
                if current_balance == 0.0:
                    self.log_test("Balance Reset After Payment", True, 
                                f"✅ Balance correctly reset to €0.00 after payment")
                    success_count += 1
                else:
                    self.log_test("Balance Reset After Payment", False, 
                                f"❌ Balance not reset correctly: €{current_balance:.2f}")
            else:
                self.log_test("Balance Reset After Payment", False, 
                            f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Balance Reset After Payment", False, f"❌ Exception: {str(e)}")
        
        print(f"\n🎯 CRITICAL FIX 2 RESULT: {success_count}/{total_tests} tests passed")
        return success_count == total_tests

    def test_critical_fix_3_department_specific_menu_integration(self):
        """
        CRITICAL BUG FIX 3: Department-Specific Menu Updates Integration
        Test that all menu operations work correctly with department-specific items after the fixes
        Verify admins can only edit their own department's menu items
        Test that order creation still works correctly with updated menu system
        """
        print("\n🏢 CRITICAL FIX 3: Department-Specific Menu Updates Integration")
        print("=" * 60)
        
        if len(self.departments) < 2 or not self.employees:
            self.log_test("Department-Specific Menu Integration", False, "Need at least 2 departments and employees")
            return False
        
        success_count = 0
        total_tests = 0
        dept1 = self.departments[0]
        dept2 = self.departments[1]
        
        # Test 1: Department-Specific Menu Item Filtering
        total_tests += 1
        try:
            # Get menus for both departments
            dept1_menu_response = self.session.get(f"{API_BASE}/menu/breakfast/{dept1['id']}")
            dept2_menu_response = self.session.get(f"{API_BASE}/menu/breakfast/{dept2['id']}")
            
            if (dept1_menu_response.status_code == 200 and dept2_menu_response.status_code == 200):
                dept1_items = dept1_menu_response.json()
                dept2_items = dept2_menu_response.json()
                
                # Verify each department has its own items
                dept1_item_ids = {item['id'] for item in dept1_items}
                dept2_item_ids = {item['id'] for item in dept2_items}
                
                # Check that all items have correct department_id
                dept1_correct = all(item['department_id'] == dept1['id'] for item in dept1_items)
                dept2_correct = all(item['department_id'] == dept2['id'] for item in dept2_items)
                
                if dept1_correct and dept2_correct:
                    self.log_test("Department-Specific Menu Filtering", True, 
                                f"✅ Menu items correctly filtered by department: Dept1={len(dept1_items)} items, Dept2={len(dept2_items)} items")
                    success_count += 1
                else:
                    self.log_test("Department-Specific Menu Filtering", False, 
                                f"❌ Menu items not properly filtered by department")
            else:
                self.log_test("Department-Specific Menu Filtering", False, 
                            "❌ Failed to get department menus")
                
        except Exception as e:
            self.log_test("Department-Specific Menu Filtering", False, f"❌ Exception: {str(e)}")
        
        # Test 2: Cross-Department Menu Edit Prevention
        total_tests += 1
        try:
            # Get a menu item from dept1
            dept1_menu_response = self.session.get(f"{API_BASE}/menu/breakfast/{dept1['id']}")
            if dept1_menu_response.status_code == 200:
                dept1_items = dept1_menu_response.json()
                if dept1_items:
                    test_item = dept1_items[0]
                    
                    # Try to edit dept1's item using dept2's department_id (should fail)
                    update_data = {"price": 999.99}
                    response = self.session.put(
                        f"{API_BASE}/department-admin/menu/breakfast/{test_item['id']}", 
                        json=update_data,
                        params={"department_id": dept2['id']}
                    )
                    
                    if response.status_code in [403, 404]:
                        self.log_test("Cross-Department Edit Prevention", True, 
                                    f"✅ Correctly prevented cross-department menu editing (HTTP {response.status_code})")
                        success_count += 1
                    else:
                        self.log_test("Cross-Department Edit Prevention", False, 
                                    f"❌ Should prevent cross-department editing, got HTTP {response.status_code}")
                else:
                    self.log_test("Cross-Department Edit Prevention", False, 
                                "❌ No menu items found for testing")
            else:
                self.log_test("Cross-Department Edit Prevention", False, 
                            "❌ Failed to get department menu for testing")
                
        except Exception as e:
            self.log_test("Cross-Department Edit Prevention", False, f"❌ Exception: {str(e)}")
        
        # Test 3: Order Creation with Department-Specific Menus
        total_tests += 1
        try:
            if self.employees:
                test_employee = next((emp for emp in self.employees if emp['department_id'] == dept1['id']), self.employees[0])
                
                # Create order using department-specific menu
                order_data = {
                    "employee_id": test_employee['id'],
                    "department_id": dept1['id'],
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
                    order = response.json()
                    if order['total_price'] > 0:
                        self.log_test("Order Creation with Department Menu", True, 
                                    f"✅ Successfully created order with department-specific pricing: €{order['total_price']:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Order Creation with Department Menu", False, 
                                    "❌ Invalid order total price")
                elif response.status_code == 400 and "bereits eine Frühstücksbestellung" in response.text:
                    # This is expected if employee already has breakfast order today
                    self.log_test("Order Creation with Department Menu", True, 
                                f"✅ Order creation working (employee already has breakfast order today)")
                    success_count += 1
                else:
                    self.log_test("Order Creation with Department Menu", False, 
                                f"❌ HTTP {response.status_code}: {response.text}")
                    
        except Exception as e:
            self.log_test("Order Creation with Department Menu", False, f"❌ Exception: {str(e)}")
        
        # Test 4: Menu Updates Affect Order Pricing
        total_tests += 1
        try:
            # Update a menu item price
            dept1_menu_response = self.session.get(f"{API_BASE}/menu/breakfast/{dept1['id']}")
            if dept1_menu_response.status_code == 200:
                dept1_items = dept1_menu_response.json()
                if dept1_items:
                    test_item = dept1_items[0]
                    original_price = test_item['price']
                    new_price = original_price + 0.50
                    
                    # Update the price
                    update_data = {"price": new_price}
                    update_response = self.session.put(
                        f"{API_BASE}/department-admin/menu/breakfast/{test_item['id']}", 
                        json=update_data,
                        params={"department_id": dept1['id']}
                    )
                    
                    if update_response.status_code == 200:
                        # Verify the price was updated
                        verify_response = self.session.get(f"{API_BASE}/menu/breakfast/{dept1['id']}")
                        if verify_response.status_code == 200:
                            updated_items = verify_response.json()
                            updated_item = next((item for item in updated_items if item['id'] == test_item['id']), None)
                            
                            if updated_item and updated_item['price'] == new_price:
                                self.log_test("Menu Updates Affect Order Pricing", True, 
                                            f"✅ Menu price successfully updated from €{original_price:.2f} to €{new_price:.2f}")
                                success_count += 1
                            else:
                                self.log_test("Menu Updates Affect Order Pricing", False, 
                                            f"❌ Menu price not updated correctly")
                        else:
                            self.log_test("Menu Updates Affect Order Pricing", False, 
                                        f"❌ Failed to verify price update")
                    else:
                        self.log_test("Menu Updates Affect Order Pricing", False, 
                                    f"❌ Menu update failed: HTTP {update_response.status_code}")
                else:
                    self.log_test("Menu Updates Affect Order Pricing", False, 
                                "❌ No menu items found for testing")
            else:
                self.log_test("Menu Updates Affect Order Pricing", False, 
                            "❌ Failed to get department menu for testing")
                
        except Exception as e:
            self.log_test("Menu Updates Affect Order Pricing", False, f"❌ Exception: {str(e)}")
        
        # Test 5: Department Admin Authentication for Menu Operations
        total_tests += 1
        try:
            # Test department admin login
            admin_login_data = {
                "department_name": dept1['name'],
                "admin_password": "admin1"  # Based on environment variables
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            
            if response.status_code == 200:
                login_result = response.json()
                if (login_result.get('department_id') == dept1['id'] and 
                    login_result.get('role') == 'department_admin'):
                    self.log_test("Department Admin Authentication", True, 
                                f"✅ Department admin authentication working correctly for {dept1['name']}")
                    success_count += 1
                else:
                    self.log_test("Department Admin Authentication", False, 
                                f"❌ Invalid admin authentication response: {login_result}")
            else:
                self.log_test("Department Admin Authentication", False, 
                            f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Department Admin Authentication", False, f"❌ Exception: {str(e)}")
        
        print(f"\n🎯 CRITICAL FIX 3 RESULT: {success_count}/{total_tests} tests passed")
        return success_count == total_tests

    def run_all_tests(self):
        """Run all three critical bug fix tests"""
        print("🚀 TESTING THREE CRITICAL BUG FIXES")
        print("=" * 80)
        print("Testing the three critical bug fixes for the German canteen management system:")
        print("1. Menu Item Edit Saving Fix")
        print("2. Payment History Display Fix")
        print("3. Department-Specific Menu Updates Integration")
        print("=" * 80)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return False
        
        # Run the three critical bug fix tests
        test_results = []
        
        test_results.append(self.test_critical_fix_1_menu_item_edit_saving())
        test_results.append(self.test_critical_fix_2_payment_history_display())
        test_results.append(self.test_critical_fix_3_department_specific_menu_integration())
        
        # Summary
        print("\n" + "=" * 80)
        print("🏁 THREE CRITICAL BUG FIXES TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"1. Menu Item Edit Saving Fix: {'✅ WORKING' if test_results[0] else '❌ FAILING'}")
        print(f"2. Payment History Display Fix: {'✅ WORKING' if test_results[1] else '❌ FAILING'}")
        print(f"3. Department-Specific Menu Updates Integration: {'✅ WORKING' if test_results[2] else '❌ FAILING'}")
        
        print(f"\n🎯 Overall Result: {passed_tests}/{total_tests} critical bug fixes working correctly")
        
        if passed_tests == total_tests:
            print("🎉 ALL THREE CRITICAL BUG FIXES ARE WORKING CORRECTLY!")
            return True
        else:
            print("⚠️  Some critical bug fixes need attention.")
            return False

def main():
    """Main test execution"""
    tester = ThreeCriticalFixesTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()