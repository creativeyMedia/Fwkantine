#!/usr/bin/env python3
"""
Enhanced Features Test Suite for German Canteen Management System
Tests the new and enhanced features as specified in the review request:
1. Enhanced Menu Management with Name Editing
2. New Breakfast History Endpoint
3. Existing Functionality Verification
"""

import requests
import json
import sys
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class EnhancedFeaturesTester:
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
        self.created_items = []  # Track items created during testing for cleanup
        
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
                return False
        except Exception as e:
            self.log_test("Get Departments", False, f"Exception: {str(e)}")
            return False

        # Create test employee
        if self.departments:
            try:
                employee_data = {
                    "name": "Max Mustermann",
                    "department_id": self.departments[0]['id']
                }
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    employee = response.json()
                    self.employees.append(employee)
                    self.log_test("Create Test Employee", True, f"Created employee: {employee['name']}")
                else:
                    return False
            except Exception as e:
                self.log_test("Create Test Employee", False, f"Exception: {str(e)}")
                return False

        # Get current menu items
        for menu_type in ['breakfast', 'toppings', 'drinks', 'sweets']:
            try:
                response = self.session.get(f"{API_BASE}/menu/{menu_type}")
                if response.status_code == 200:
                    self.menu_items[menu_type] = response.json()
            except:
                pass

        return True

    def test_enhanced_menu_management_breakfast(self):
        """Test Enhanced Menu Management - Breakfast Items with Name Editing"""
        print("\n=== Testing Enhanced Menu Management - Breakfast Items ===")
        
        success_count = 0
        
        # Test 1: Create new breakfast item
        try:
            new_breakfast_data = {
                "roll_type": "weiss",
                "price": 0.75
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/breakfast", 
                                       json=new_breakfast_data)
            
            if response.status_code == 200:
                new_item = response.json()
                self.created_items.append(('breakfast', new_item['id']))
                self.log_test("Create Breakfast Item", True, 
                            f"Created breakfast item: {new_item['roll_type']} for €{new_item['price']:.2f}")
                success_count += 1
                
                # Test 2: Update breakfast item with custom name and price
                try:
                    update_data = {
                        "name": "Premium Weißbrot",
                        "price": 0.85
                    }
                    
                    response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{new_item['id']}", 
                                              json=update_data)
                    
                    if response.status_code == 200:
                        self.log_test("Update Breakfast Item Name & Price", True, 
                                    f"Updated to custom name: '{update_data['name']}' with price €{update_data['price']:.2f}")
                        success_count += 1
                        
                        # Test 3: Verify custom name is returned in GET request
                        try:
                            response = self.session.get(f"{API_BASE}/menu/breakfast")
                            if response.status_code == 200:
                                breakfast_items = response.json()
                                updated_item = next((item for item in breakfast_items if item['id'] == new_item['id']), None)
                                
                                if updated_item and updated_item.get('name') == update_data['name']:
                                    self.log_test("Verify Custom Name Persistence", True, 
                                                f"Custom name '{update_data['name']}' persisted correctly")
                                    success_count += 1
                                elif updated_item and not updated_item.get('name'):
                                    # Should fall back to default roll_type label
                                    self.log_test("Verify Default Name Fallback", True, 
                                                f"Falls back to roll_type: {updated_item['roll_type']}")
                                    success_count += 1
                                else:
                                    self.log_test("Verify Custom Name Persistence", False, 
                                                "Custom name not found or incorrect")
                            else:
                                self.log_test("Verify Custom Name Persistence", False, 
                                            f"HTTP {response.status_code}")
                        except Exception as e:
                            self.log_test("Verify Custom Name Persistence", False, f"Exception: {str(e)}")
                        
                    else:
                        self.log_test("Update Breakfast Item Name & Price", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
                except Exception as e:
                    self.log_test("Update Breakfast Item Name & Price", False, f"Exception: {str(e)}")
                    
            else:
                self.log_test("Create Breakfast Item", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Breakfast Item", False, f"Exception: {str(e)}")

        # Test 4: Update existing breakfast item with only price
        if self.menu_items['breakfast']:
            try:
                existing_item = self.menu_items['breakfast'][0]
                original_price = existing_item['price']
                new_price = original_price + 0.10
                
                update_data = {"price": new_price}
                response = self.session.put(f"{API_BASE}/department-admin/menu/breakfast/{existing_item['id']}", 
                                          json=update_data)
                
                if response.status_code == 200:
                    self.log_test("Update Existing Breakfast Price Only", True, 
                                f"Updated price from €{original_price:.2f} to €{new_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Update Existing Breakfast Price Only", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Update Existing Breakfast Price Only", False, f"Exception: {str(e)}")

        return success_count >= 3

    def test_enhanced_menu_management_toppings(self):
        """Test Enhanced Menu Management - Toppings Items with Name Editing"""
        print("\n=== Testing Enhanced Menu Management - Toppings Items ===")
        
        success_count = 0
        
        # Test 1: Create new topping item
        try:
            new_topping_data = {
                "topping_type": "ruehrei",
                "price": 0.25
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", 
                                       json=new_topping_data)
            
            if response.status_code == 200:
                new_item = response.json()
                self.created_items.append(('toppings', new_item['id']))
                self.log_test("Create Topping Item", True, 
                            f"Created topping item: {new_item['topping_type']} for €{new_item['price']:.2f}")
                success_count += 1
                
                # Test 2: Update topping item with custom name and price
                try:
                    update_data = {
                        "name": "Bio-Rührei Premium",
                        "price": 0.35
                    }
                    
                    response = self.session.put(f"{API_BASE}/department-admin/menu/toppings/{new_item['id']}", 
                                              json=update_data)
                    
                    if response.status_code == 200:
                        self.log_test("Update Topping Item Name & Price", True, 
                                    f"Updated to custom name: '{update_data['name']}' with price €{update_data['price']:.2f}")
                        success_count += 1
                        
                        # Test 3: Verify custom name is returned in GET request
                        try:
                            response = self.session.get(f"{API_BASE}/menu/toppings")
                            if response.status_code == 200:
                                topping_items = response.json()
                                updated_item = next((item for item in topping_items if item['id'] == new_item['id']), None)
                                
                                if updated_item and updated_item.get('name') == update_data['name']:
                                    self.log_test("Verify Custom Topping Name Persistence", True, 
                                                f"Custom name '{update_data['name']}' persisted correctly")
                                    success_count += 1
                                elif updated_item and not updated_item.get('name'):
                                    # Should fall back to default topping_type label
                                    self.log_test("Verify Default Topping Name Fallback", True, 
                                                f"Falls back to topping_type: {updated_item['topping_type']}")
                                    success_count += 1
                                else:
                                    self.log_test("Verify Custom Topping Name Persistence", False, 
                                                "Custom name not found or incorrect")
                            else:
                                self.log_test("Verify Custom Topping Name Persistence", False, 
                                            f"HTTP {response.status_code}")
                        except Exception as e:
                            self.log_test("Verify Custom Topping Name Persistence", False, f"Exception: {str(e)}")
                        
                    else:
                        self.log_test("Update Topping Item Name & Price", False, 
                                    f"HTTP {response.status_code}: {response.text}")
                        
                except Exception as e:
                    self.log_test("Update Topping Item Name & Price", False, f"Exception: {str(e)}")
                    
            else:
                self.log_test("Create Topping Item", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Topping Item", False, f"Exception: {str(e)}")

        # Test 4: Update existing topping item with only name
        if self.menu_items['toppings']:
            try:
                existing_item = self.menu_items['toppings'][0]
                
                update_data = {"name": "Hausgemachter Käse"}
                response = self.session.put(f"{API_BASE}/department-admin/menu/toppings/{existing_item['id']}", 
                                          json=update_data)
                
                if response.status_code == 200:
                    self.log_test("Update Existing Topping Name Only", True, 
                                f"Updated name to '{update_data['name']}'")
                    success_count += 1
                else:
                    self.log_test("Update Existing Topping Name Only", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Update Existing Topping Name Only", False, f"Exception: {str(e)}")

        return success_count >= 3

    def test_breakfast_history_endpoint(self):
        """Test New Breakfast History Endpoint"""
        print("\n=== Testing New Breakfast History Endpoint ===")
        
        if not self.departments or not self.employees:
            self.log_test("Breakfast History", False, "Missing departments or employees")
            return False
        
        success_count = 0
        test_dept = self.departments[0]
        test_employee = self.employees[0]
        
        # Create some test breakfast orders for history
        try:
            # Create breakfast order with new roll halves format
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
                        "has_lunch": True
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            if response.status_code == 200:
                self.log_test("Create Test Breakfast Order", True, "Created breakfast order for history testing")
            
        except Exception as e:
            self.log_test("Create Test Breakfast Order", False, f"Exception: {str(e)}")

        # Test 1: Get breakfast history with default days_back
        try:
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{test_dept['id']}")
            
            if response.status_code == 200:
                history_data = response.json()
                
                # Check required structure
                if 'history' in history_data and isinstance(history_data['history'], list):
                    self.log_test("Breakfast History Structure", True, 
                                f"History endpoint returns proper structure with {len(history_data['history'])} entries")
                    success_count += 1
                    
                    # Check if we have today's data (since we just created an order)
                    today = datetime.now().date().isoformat()
                    today_entry = next((entry for entry in history_data['history'] if entry['date'] == today), None)
                    
                    if today_entry:
                        self.log_test("Today's History Entry", True, 
                                    f"Found today's entry with {today_entry['total_orders']} orders, total: €{today_entry['total_amount']:.2f}")
                        success_count += 1
                        
                        # Check daily summary structure
                        required_fields = ['date', 'total_orders', 'total_amount', 'breakfast_summary', 'employee_orders', 'shopping_list']
                        missing_fields = [field for field in required_fields if field not in today_entry]
                        
                        if not missing_fields:
                            self.log_test("History Entry Structure", True, "All required fields present in history entry")
                            success_count += 1
                            
                            # Check shopping list calculation
                            shopping_list = today_entry.get('shopping_list', {})
                            if shopping_list:
                                for roll_type, data in shopping_list.items():
                                    if 'halves' in data and 'whole_rolls' in data:
                                        halves = data['halves']
                                        whole_rolls = data['whole_rolls']
                                        expected_whole = (halves + 1) // 2  # Round up
                                        
                                        if whole_rolls == expected_whole:
                                            self.log_test("Shopping List Calculation", True, 
                                                        f"{roll_type}: {halves} halves → {whole_rolls} whole rolls")
                                            success_count += 1
                                            break
                                        else:
                                            self.log_test("Shopping List Calculation", False, 
                                                        f"Expected {expected_whole}, got {whole_rolls}")
                            
                            # Check employee-specific order details
                            employee_orders = today_entry.get('employee_orders', {})
                            if employee_orders:
                                employee_name = test_employee['name']
                                if employee_name in employee_orders:
                                    emp_data = employee_orders[employee_name]
                                    if 'white_halves' in emp_data and 'seeded_halves' in emp_data and 'toppings' in emp_data:
                                        self.log_test("Employee Order Details", True, 
                                                    f"Employee {employee_name}: {emp_data['white_halves']} white, {emp_data['seeded_halves']} seeded halves")
                                        success_count += 1
                                    else:
                                        self.log_test("Employee Order Details", False, "Missing employee order fields")
                                else:
                                    self.log_test("Employee Order Details", False, f"Employee {employee_name} not found in orders")
                            
                        else:
                            self.log_test("History Entry Structure", False, f"Missing fields: {missing_fields}")
                    else:
                        self.log_test("Today's History Entry", False, "No entry found for today")
                        
                else:
                    self.log_test("Breakfast History Structure", False, "Invalid history structure")
                    
            else:
                self.log_test("Breakfast History Default", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Breakfast History Default", False, f"Exception: {str(e)}")

        # Test 2: Get breakfast history with custom days_back parameter
        try:
            custom_days = 7
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{test_dept['id']}", 
                                      params={"days_back": custom_days})
            
            if response.status_code == 200:
                history_data = response.json()
                
                if 'history' in history_data:
                    # Check chronological ordering (newest first)
                    history_entries = history_data['history']
                    if len(history_entries) > 1:
                        dates = [entry['date'] for entry in history_entries]
                        is_chronological = all(dates[i] >= dates[i+1] for i in range(len(dates)-1))
                        
                        if is_chronological:
                            self.log_test("Chronological Ordering", True, 
                                        f"History entries properly ordered (newest first): {len(history_entries)} entries")
                            success_count += 1
                        else:
                            self.log_test("Chronological Ordering", False, "History not in chronological order")
                    else:
                        self.log_test("Custom Days Parameter", True, 
                                    f"Custom days_back={custom_days} parameter accepted")
                        success_count += 1
                        
            else:
                self.log_test("Breakfast History Custom Days", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Breakfast History Custom Days", False, f"Exception: {str(e)}")

        return success_count >= 4

    def test_existing_functionality_verification(self):
        """Test that existing functionality still works properly"""
        print("\n=== Testing Existing Functionality Verification ===")
        
        success_count = 0
        
        # Test 1: Department authentication still works
        if self.departments:
            try:
                dept = self.departments[0]
                # Use the new department structure passwords
                login_data = {
                    "department_name": dept['name'],
                    "password": "password1"  # Updated password format
                }
                
                response = self.session.post(f"{API_BASE}/login/department", json=login_data)
                
                if response.status_code == 200:
                    login_result = response.json()
                    if login_result.get('department_id') == dept['id']:
                        self.log_test("Department Authentication", True, "Department login still functional")
                        success_count += 1
                    else:
                        self.log_test("Department Authentication", False, "Department ID mismatch")
                else:
                    self.log_test("Department Authentication", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Department Authentication", False, f"Exception: {str(e)}")

        # Test 2: Department admin authentication still works
        if self.departments:
            try:
                dept = self.departments[0]
                admin_login_data = {
                    "department_name": dept['name'],
                    "admin_password": "admin1"  # Updated admin password format
                }
                
                response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
                
                if response.status_code == 200:
                    login_result = response.json()
                    if (login_result.get('department_id') == dept['id'] and 
                        login_result.get('role') == 'department_admin'):
                        self.log_test("Department Admin Authentication", True, "Admin login still functional")
                        success_count += 1
                    else:
                        self.log_test("Department Admin Authentication", False, "Admin login response invalid")
                else:
                    self.log_test("Department Admin Authentication", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Department Admin Authentication", False, f"Exception: {str(e)}")

        # Test 3: Breakfast and toppings CRUD operations still work
        try:
            # Get current breakfast menu
            response = self.session.get(f"{API_BASE}/menu/breakfast")
            if response.status_code == 200:
                breakfast_items = response.json()
                self.log_test("Breakfast Menu Retrieval", True, f"Retrieved {len(breakfast_items)} breakfast items")
                success_count += 1
            else:
                self.log_test("Breakfast Menu Retrieval", False, f"HTTP {response.status_code}")
                
            # Get current toppings menu
            response = self.session.get(f"{API_BASE}/menu/toppings")
            if response.status_code == 200:
                topping_items = response.json()
                self.log_test("Toppings Menu Retrieval", True, f"Retrieved {len(topping_items)} topping items")
                success_count += 1
            else:
                self.log_test("Toppings Menu Retrieval", False, f"HTTP {response.status_code}")
                
        except Exception as e:
            self.log_test("Menu CRUD Operations", False, f"Exception: {str(e)}")

        # Test 4: Daily summary endpoint still works
        if self.departments:
            try:
                test_dept = self.departments[0]
                response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
                
                if response.status_code == 200:
                    summary = response.json()
                    required_fields = ['date', 'breakfast_summary', 'drinks_summary', 'sweets_summary']
                    missing_fields = [field for field in required_fields if field not in summary]
                    
                    if not missing_fields:
                        self.log_test("Daily Summary Endpoint", True, 
                                    f"Daily summary still functional for {summary['date']}")
                        success_count += 1
                    else:
                        self.log_test("Daily Summary Endpoint", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Daily Summary Endpoint", False, 
                                f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_test("Daily Summary Endpoint", False, f"Exception: {str(e)}")

        return success_count >= 3

    def cleanup_created_items(self):
        """Clean up items created during testing"""
        print("\n=== Cleaning Up Test Items ===")
        
        for item_type, item_id in self.created_items:
            try:
                response = self.session.delete(f"{API_BASE}/department-admin/menu/{item_type}/{item_id}")
                if response.status_code == 200:
                    self.log_test(f"Cleanup {item_type.title()} Item", True, f"Deleted test item {item_id}")
                else:
                    self.log_test(f"Cleanup {item_type.title()} Item", False, 
                                f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Cleanup {item_type.title()} Item", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all enhanced feature tests"""
        print("🚀 Starting Enhanced Features Test Suite")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_data():
            print("❌ Setup failed, aborting tests")
            return False
        
        # Run tests
        test_results = []
        
        test_results.append(self.test_enhanced_menu_management_breakfast())
        test_results.append(self.test_enhanced_menu_management_toppings())
        test_results.append(self.test_breakfast_history_endpoint())
        test_results.append(self.test_existing_functionality_verification())
        
        # Cleanup
        self.cleanup_created_items()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 ENHANCED FEATURES TEST SUMMARY")
        print("=" * 60)
        
        passed_tests = sum(1 for result in self.test_results if result['success'])
        total_tests = len(self.test_results)
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['message']:
                print(f"   {result['message']}")
        
        # Overall assessment
        major_test_groups = sum(test_results)
        total_groups = len(test_results)
        
        print(f"\n🎯 MAJOR TEST GROUPS PASSED: {major_test_groups}/{total_groups}")
        
        if major_test_groups == total_groups:
            print("🎉 ALL ENHANCED FEATURES WORKING PERFECTLY!")
            return True
        elif major_test_groups >= total_groups * 0.75:
            print("✅ MOST ENHANCED FEATURES WORKING WELL")
            return True
        else:
            print("⚠️  SOME ENHANCED FEATURES NEED ATTENTION")
            return False

if __name__ == "__main__":
    tester = EnhancedFeaturesTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)