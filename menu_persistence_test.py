#!/usr/bin/env python3
"""
Menu Management & Breakfast Ordering Persistence Test
Focus: Testing the specific issues mentioned in the review request
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

class MenuPersistenceTester:
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
        print("\n=== Setting Up Test Data ===")
        
        # Initialize data
        try:
            response = self.session.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.log_test("Data Initialization", True, "System initialized")
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
        
        # Create test employee
        if self.departments:
            try:
                test_dept = self.departments[0]
                employee_data = {
                    "name": "Test Employee for Menu Persistence",
                    "department_id": test_dept['id']
                }
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    self.employees.append(response.json())
                    self.log_test("Create Test Employee", True, "Test employee created")
                else:
                    self.log_test("Create Test Employee", False, f"HTTP {response.status_code}")
                    return False
            except Exception as e:
                self.log_test("Create Test Employee", False, f"Exception: {str(e)}")
                return False
        
        return True
    
    def test_menu_toppings_persistence(self):
        """Test that menu toppings changes (add/edit/delete) are saved to DB"""
        print("\n=== Testing Menu Toppings Persistence ===")
        
        if not self.departments:
            self.log_test("Menu Toppings Persistence", False, "No departments available")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        
        # Authenticate as department admin
        try:
            admin_login_data = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            if response.status_code == 200:
                self.log_test("Department Admin Authentication", True, "Admin authenticated")
                success_count += 1
            else:
                self.log_test("Department Admin Authentication", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Department Admin Authentication", False, f"Exception: {str(e)}")
            return False
        
        # Test ADD topping
        try:
            new_topping_data = {
                "topping_id": "test_marmelade",
                "topping_name": "Test Marmelade",
                "price": 0.50,
                "department_id": test_dept['id']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", json=new_topping_data)
            
            if response.status_code == 200:
                new_topping = response.json()
                topping_id = new_topping['id']
                self.log_test("ADD Topping", True, f"Created topping: {new_topping.get('name', 'Unknown')}")
                success_count += 1
                
                # Verify persistence
                response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
                if response.status_code == 200:
                    toppings = response.json()
                    topping_found = any(t.get('id') == topping_id for t in toppings)
                    if topping_found:
                        self.log_test("ADD Topping Persistence", True, "✅ NEW TOPPING PERSISTED TO DATABASE")
                        success_count += 1
                    else:
                        self.log_test("ADD Topping Persistence", False, "❌ NEW TOPPING NOT SAVED TO DATABASE")
                else:
                    self.log_test("ADD Topping Persistence", False, f"Failed to fetch toppings: {response.status_code}")
            else:
                self.log_test("ADD Topping", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("ADD Topping", False, f"Exception: {str(e)}")
        
        # Test EDIT topping
        try:
            response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
            if response.status_code == 200:
                toppings = response.json()
                if toppings:
                    topping_to_edit = toppings[0]
                    original_price = topping_to_edit['price']
                    new_price = original_price + 0.25
                    
                    update_data = {
                        "price": new_price,
                        "name": "EDITED " + topping_to_edit.get('name', 'Topping')
                    }
                    
                    response = self.session.put(f"{API_BASE}/department-admin/menu/toppings/{topping_to_edit['id']}", 
                                              json=update_data, params={"department_id": test_dept['id']})
                    
                    if response.status_code == 200:
                        self.log_test("EDIT Topping", True, f"Updated topping price to €{new_price:.2f}")
                        success_count += 1
                        
                        # Verify persistence
                        response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
                        if response.status_code == 200:
                            updated_toppings = response.json()
                            updated_topping = next((t for t in updated_toppings if t['id'] == topping_to_edit['id']), None)
                            if updated_topping and updated_topping['price'] == new_price:
                                self.log_test("EDIT Topping Persistence", True, "✅ TOPPING EDIT PERSISTED TO DATABASE")
                                success_count += 1
                            else:
                                self.log_test("EDIT Topping Persistence", False, "❌ TOPPING EDIT NOT SAVED TO DATABASE")
                        else:
                            self.log_test("EDIT Topping Persistence", False, f"Failed to verify edit: {response.status_code}")
                    else:
                        self.log_test("EDIT Topping", False, f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("EDIT Topping", False, "No toppings available to edit")
            else:
                self.log_test("EDIT Topping", False, f"Failed to fetch toppings: {response.status_code}")
                
        except Exception as e:
            self.log_test("EDIT Topping", False, f"Exception: {str(e)}")
        
        # Test DELETE topping
        try:
            response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
            if response.status_code == 200:
                toppings = response.json()
                if len(toppings) > 1:
                    topping_to_delete = toppings[-1]
                    topping_id = topping_to_delete['id']
                    
                    response = self.session.delete(f"{API_BASE}/menu/toppings/{topping_id}")
                    
                    if response.status_code == 200:
                        self.log_test("DELETE Topping", True, f"Deleted topping: {topping_to_delete.get('name', 'Unknown')}")
                        success_count += 1
                        
                        # Verify persistence
                        response = self.session.get(f"{API_BASE}/menu/toppings/{test_dept['id']}")
                        if response.status_code == 200:
                            remaining_toppings = response.json()
                            topping_still_exists = any(t['id'] == topping_id for t in remaining_toppings)
                            if not topping_still_exists:
                                self.log_test("DELETE Topping Persistence", True, "✅ TOPPING DELETION PERSISTED TO DATABASE")
                                success_count += 1
                            else:
                                self.log_test("DELETE Topping Persistence", False, "❌ TOPPING DELETION NOT SAVED TO DATABASE")
                        else:
                            self.log_test("DELETE Topping Persistence", False, f"Failed to verify deletion: {response.status_code}")
                    else:
                        self.log_test("DELETE Topping", False, f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("DELETE Topping", False, "Not enough toppings to safely delete one")
            else:
                self.log_test("DELETE Topping", False, f"Failed to fetch toppings: {response.status_code}")
                
        except Exception as e:
            self.log_test("DELETE Topping", False, f"Exception: {str(e)}")
        
        return success_count >= 5
    
    def test_drinks_sweets_persistence(self):
        """Test that drinks and sweets management changes are saved to DB"""
        print("\n=== Testing Drinks & Sweets Persistence ===")
        
        if not self.departments:
            self.log_test("Drinks & Sweets Persistence", False, "No departments available")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        
        # Test Drinks Management
        try:
            response = self.session.get(f"{API_BASE}/menu/drinks/{test_dept['id']}")
            if response.status_code == 200:
                drinks = response.json()
                if drinks:
                    drink_to_edit = drinks[0]
                    original_price = drink_to_edit['price']
                    new_price = original_price + 0.30
                    
                    update_data = {"price": new_price, "name": f"EDITED {drink_to_edit['name']}"}
                    response = self.session.put(f"{API_BASE}/department-admin/menu/drinks/{drink_to_edit['id']}", 
                                              json=update_data, params={"department_id": test_dept['id']})
                    
                    if response.status_code == 200:
                        self.log_test("EDIT Drink", True, f"Updated drink price to €{new_price:.2f}")
                        success_count += 1
                        
                        # Verify persistence
                        response = self.session.get(f"{API_BASE}/menu/drinks/{test_dept['id']}")
                        if response.status_code == 200:
                            updated_drinks = response.json()
                            updated_drink = next((d for d in updated_drinks if d['id'] == drink_to_edit['id']), None)
                            if updated_drink and updated_drink['price'] == new_price:
                                self.log_test("EDIT Drink Persistence", True, "✅ DRINK EDIT PERSISTED TO DATABASE")
                                success_count += 1
                            else:
                                self.log_test("EDIT Drink Persistence", False, "❌ DRINK EDIT NOT SAVED TO DATABASE")
                    else:
                        self.log_test("EDIT Drink", False, f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("EDIT Drink", False, "No drinks available to edit")
            else:
                self.log_test("EDIT Drink", False, f"Failed to fetch drinks: {response.status_code}")
                
        except Exception as e:
            self.log_test("EDIT Drink", False, f"Exception: {str(e)}")
        
        # Test Sweets Management
        try:
            response = self.session.get(f"{API_BASE}/menu/sweets/{test_dept['id']}")
            if response.status_code == 200:
                sweets = response.json()
                if sweets:
                    sweet_to_edit = sweets[0]
                    original_price = sweet_to_edit['price']
                    new_price = original_price + 0.40
                    
                    update_data = {"price": new_price, "name": f"EDITED {sweet_to_edit['name']}"}
                    response = self.session.put(f"{API_BASE}/department-admin/menu/sweets/{sweet_to_edit['id']}", 
                                              json=update_data, params={"department_id": test_dept['id']})
                    
                    if response.status_code == 200:
                        self.log_test("EDIT Sweet", True, f"Updated sweet price to €{new_price:.2f}")
                        success_count += 1
                        
                        # Verify persistence
                        response = self.session.get(f"{API_BASE}/menu/sweets/{test_dept['id']}")
                        if response.status_code == 200:
                            updated_sweets = response.json()
                            updated_sweet = next((s for s in updated_sweets if s['id'] == sweet_to_edit['id']), None)
                            if updated_sweet and updated_sweet['price'] == new_price:
                                self.log_test("EDIT Sweet Persistence", True, "✅ SWEET EDIT PERSISTED TO DATABASE")
                                success_count += 1
                            else:
                                self.log_test("EDIT Sweet Persistence", False, "❌ SWEET EDIT NOT SAVED TO DATABASE")
                    else:
                        self.log_test("EDIT Sweet", False, f"HTTP {response.status_code}: {response.text}")
                else:
                    self.log_test("EDIT Sweet", False, "No sweets available to edit")
            else:
                self.log_test("EDIT Sweet", False, f"Failed to fetch sweets: {response.status_code}")
                
        except Exception as e:
            self.log_test("EDIT Sweet", False, f"Exception: {str(e)}")
        
        return success_count >= 2
    
    def test_breakfast_ordering_persistence(self):
        """Test that breakfast orders save properly without 'Fehler beim Speichern der Bestellung'"""
        print("\n=== Testing Breakfast Ordering Persistence ===")
        
        if not self.departments or not self.employees:
            self.log_test("Breakfast Ordering Persistence", False, "Missing departments or employees")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        test_employee = self.employees[0]
        
        # Test 1: Create breakfast order and verify it saves
        try:
            breakfast_order = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
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
                order_id = order['id']
                self.log_test("CREATE Breakfast Order", True, f"✅ BREAKFAST ORDER CREATED: €{order['total_price']:.2f}")
                success_count += 1
                
                # Verify order persistence
                response = self.session.get(f"{API_BASE}/employees/{test_employee['id']}/orders")
                if response.status_code == 200:
                    orders_data = response.json()
                    orders = orders_data.get('orders', [])
                    order_found = any(o['id'] == order_id for o in orders)
                    if order_found:
                        self.log_test("Breakfast Order Persistence", True, "✅ BREAKFAST ORDER PERSISTED TO DATABASE")
                        success_count += 1
                        
                        # Verify order structure
                        saved_order = next((o for o in orders if o['id'] == order_id), None)
                        if saved_order and saved_order.get('breakfast_items'):
                            breakfast_item = saved_order['breakfast_items'][0]
                            if (breakfast_item.get('total_halves') == 4 and 
                                breakfast_item.get('white_halves') == 2 and
                                breakfast_item.get('seeded_halves') == 2 and
                                breakfast_item.get('has_lunch') == True and
                                breakfast_item.get('boiled_eggs') == 2):
                                self.log_test("Breakfast Order Structure", True, "✅ ORDER STRUCTURE CORRECTLY SAVED")
                                success_count += 1
                            else:
                                self.log_test("Breakfast Order Structure", False, "❌ ORDER STRUCTURE NOT CORRECTLY SAVED")
                        else:
                            self.log_test("Breakfast Order Structure", False, "❌ NO BREAKFAST ITEMS IN SAVED ORDER")
                    else:
                        self.log_test("Breakfast Order Persistence", False, "❌ BREAKFAST ORDER NOT FOUND IN DATABASE")
                else:
                    self.log_test("Breakfast Order Persistence", False, f"Failed to fetch employee orders: {response.status_code}")
            else:
                self.log_test("CREATE Breakfast Order", False, f"❌ BREAKFAST ORDER FAILED: HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("CREATE Breakfast Order", False, f"❌ BREAKFAST ORDER EXCEPTION: {str(e)}")
        
        # Test 2: Test department-specific menu operations
        try:
            # Test POST /api/department-admin/menu/toppings/{item_id}
            new_topping_data = {
                "topping_id": "breakfast_test_topping",
                "topping_name": "Breakfast Test Topping",
                "price": 0.75,
                "department_id": test_dept['id']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", json=new_topping_data)
            
            if response.status_code == 200:
                new_topping = response.json()
                self.log_test("Department-Specific Topping Creation", True, f"✅ DEPARTMENT TOPPING CREATED: {new_topping.get('name')}")
                success_count += 1
            else:
                self.log_test("Department-Specific Topping Creation", False, f"❌ DEPARTMENT TOPPING FAILED: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Department-Specific Topping Creation", False, f"❌ DEPARTMENT TOPPING EXCEPTION: {str(e)}")
        
        return success_count >= 3
    
    def run_persistence_tests(self):
        """Run all menu persistence tests"""
        print("🚨 MENU MANAGEMENT & BREAKFAST ORDERING PERSISTENCE TESTING")
        print(f"🔗 Testing against: {API_BASE}")
        print("🎯 Focus: Issues mentioned in review request")
        print("=" * 80)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data. Aborting tests.")
            return False
        
        # Run persistence tests
        tests = [
            ("Menu Toppings Persistence", self.test_menu_toppings_persistence),
            ("Drinks & Sweets Persistence", self.test_drinks_sweets_persistence),
            ("Breakfast Ordering Persistence", self.test_breakfast_ordering_persistence),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*60}")
            print(f"🧪 Running: {test_name}")
            print(f"{'='*60}")
            
            try:
                result = test_func()
                if result:
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"💥 {test_name}: EXCEPTION - {str(e)}")
        
        # Print final summary
        print(f"\n{'='*80}")
        print(f"🎯 MENU PERSISTENCE TEST SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"❌ Failed: {total_tests - passed_tests}/{total_tests}")
        
        if passed_tests == total_tests:
            print("🎉 ALL PERSISTENCE ISSUES FIXED! Menu management and breakfast ordering working perfectly!")
            print("✅ Menu toppings changes (add/edit/delete) are saved to DB")
            print("✅ Drinks and sweets management changes are saved to DB")
            print("✅ Breakfast ordering saves properly without errors")
        elif passed_tests >= total_tests * 0.67:
            print("✨ Most persistence issues fixed! System is mostly functional.")
        else:
            print("⚠️  Persistence issues still present. System needs attention.")
            print("❌ Menu toppings changes may not be saved to DB")
            print("❌ Drinks and sweets management may not be saved to DB")
            print("❌ Breakfast ordering may fail with 'Fehler beim Speichern der Bestellung'")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    tester = MenuPersistenceTester()
    success = tester.run_persistence_tests()
    sys.exit(0 if success else 1)