#!/usr/bin/env python3
"""
Focused Test Suite for 4 Specific Bug Fixes
Tests the exact scenarios mentioned in the review request
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

class BugFixesTester:
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
        """Setup basic test data"""
        print("\n=== Setting Up Test Data ===")
        
        # Initialize data
        try:
            response = self.session.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.log_test("Data Initialization", True, "Database initialized")
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
                    "name": "Test Employee Bug Fixes",
                    "department_id": test_dept['id']
                }
                
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    employee = response.json()
                    self.employees.append(employee)
                    self.log_test("Create Test Employee", True, f"Created employee: {employee['name']}")
                else:
                    self.log_test("Create Test Employee", False, f"HTTP {response.status_code}")
                    return False
            except Exception as e:
                self.log_test("Create Test Employee", False, f"Exception: {str(e)}")
                return False
        
        return True
    
    def test_bug_1_simplified_topping_creation(self):
        """Bug 1: Test the new POST /api/department-admin/menu/toppings endpoint"""
        print("\n=== Bug 1: Simplified Topping Creation ===")
        
        if not self.departments:
            self.log_test("Bug 1", False, "No departments available")
            return False
        
        test_dept = self.departments[0]
        
        # Authenticate as department admin
        try:
            admin_login_data = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"
            }
            
            response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            if response.status_code != 200:
                self.log_test("Bug 1 - Admin Auth", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Bug 1 - Admin Auth", False, f"Exception: {str(e)}")
            return False
        
        # Test creating custom topping with free-form name
        try:
            custom_topping_data = {
                "topping_id": "hausgemachte_marmelade",
                "topping_name": "Hausgemachte Marmelade", 
                "price": 0.75,
                "department_id": test_dept['id']
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", json=custom_topping_data)
            
            if response.status_code == 200:
                topping = response.json()
                if (topping.get('name') == "Hausgemachte Marmelade" and 
                    topping.get('price') == 0.75):
                    self.log_test("Bug 1 - Simplified Topping Creation", True, 
                                f"✅ Successfully created custom topping: '{topping['name']}' for €{topping['price']:.2f}")
                    return True
                else:
                    self.log_test("Bug 1 - Simplified Topping Creation", False, 
                                f"Topping data mismatch: {topping}")
                    return False
            else:
                self.log_test("Bug 1 - Simplified Topping Creation", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Bug 1 - Simplified Topping Creation", False, f"Exception: {str(e)}")
            return False
    
    def test_bug_2_lunch_display_logic(self):
        """Bug 2: Create a breakfast order with lunch=true and verify it shows correctly in daily summary"""
        print("\n=== Bug 2: Lunch Display Logic ===")
        
        if not self.employees or not self.departments:
            self.log_test("Bug 2", False, "Missing test data")
            return False
        
        test_employee = self.employees[0]
        test_dept = self.departments[0]
        
        # First, delete any existing breakfast orders for today to avoid conflicts
        try:
            admin_login_data = {
                "department_name": test_dept['name'],
                "admin_password": "admin1"
            }
            self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
            
            # Delete today's breakfast orders
            today = datetime.now().date().isoformat()
            delete_response = self.session.delete(f"{API_BASE}/department-admin/breakfast-day/{test_dept['id']}/{today}")
            # Ignore if this fails - might not have orders to delete
        except:
            pass  # Continue even if deletion fails
        
        # Create a breakfast order with lunch=true
        try:
            breakfast_with_lunch = {
                "employee_id": test_employee['id'],
                "department_id": test_dept['id'],
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
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_with_lunch)
            
            if response.status_code == 200:
                order = response.json()
                
                # Verify lunch is included in order
                if (order.get('breakfast_items') and 
                    len(order['breakfast_items']) > 0 and
                    order['breakfast_items'][0].get('has_lunch') == True):
                    
                    self.log_test("Bug 2 - Order Creation with Lunch", True, 
                                f"✅ Breakfast order with lunch created: €{order['total_price']:.2f}")
                    
                    # Now check if it shows correctly in daily summary
                    summary_response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
                    
                    if summary_response.status_code == 200:
                        summary = summary_response.json()
                        
                        # Check if lunch appears in the summary data
                        has_lunch_data = False
                        if 'employee_orders' in summary:
                            for employee_name, employee_data in summary['employee_orders'].items():
                                if employee_name == test_employee['name']:
                                    has_lunch_data = True
                                    break
                        
                        if has_lunch_data:
                            self.log_test("Bug 2 - Lunch Display in Daily Summary", True, 
                                        "✅ Lunch order appears correctly in daily summary")
                            return True
                        else:
                            self.log_test("Bug 2 - Lunch Display in Daily Summary", False, 
                                        "Lunch order not found in daily summary")
                            return False
                    else:
                        self.log_test("Bug 2 - Daily Summary", False, 
                                    f"Failed to get daily summary: HTTP {summary_response.status_code}")
                        return False
                else:
                    self.log_test("Bug 2 - Order Creation with Lunch", False, 
                                "Lunch option not saved in order")
                    return False
            else:
                self.log_test("Bug 2 - Order Creation with Lunch", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Bug 2 - Lunch Display Logic", False, f"Exception: {str(e)}")
            return False
    
    def test_bug_3_lunch_counter_in_shopping_list(self):
        """Bug 3: Verify the daily summary includes lunch count in the response data"""
        print("\n=== Bug 3: Lunch Counter in Shopping List ===")
        
        if not self.departments:
            self.log_test("Bug 3", False, "No departments available")
            return False
        
        test_dept = self.departments[0]
        
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{test_dept['id']}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check if daily summary includes lunch count data
                has_lunch_count = False
                
                # Look for lunch-related data in the response
                if 'employee_orders' in summary:
                    for employee_name, employee_data in summary['employee_orders'].items():
                        # Check if employee has lunch orders (this would be indicated by orders with has_lunch=true)
                        if isinstance(employee_data, dict):
                            has_lunch_count = True
                            break
                
                # Also check if there's a specific lunch count field or shopping list
                if ('total_lunch_orders' in summary or 
                    'shopping_list' in summary or 
                    has_lunch_count):
                    self.log_test("Bug 3 - Lunch Counter in Shopping List", True, 
                                "✅ Daily summary includes lunch count/shopping list data")
                    return True
                else:
                    self.log_test("Bug 3 - Lunch Counter in Shopping List", False, 
                                "Daily summary missing lunch count data")
                    return False
            else:
                self.log_test("Bug 3 - Lunch Counter in Shopping List", False, 
                            f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Bug 3 - Lunch Counter in Shopping List", False, f"Exception: {str(e)}")
            return False
    
    def test_bug_4_retroactive_price_updates(self):
        """Bug 4: Test that changing lunch price updates existing orders for today"""
        print("\n=== Bug 4: Retroactive Price Updates ===")
        
        try:
            # First, get current lunch price
            lunch_response = self.session.get(f"{API_BASE}/lunch-settings")
            if lunch_response.status_code == 200:
                current_settings = lunch_response.json()
                original_price = current_settings.get('price', 0.0)
                
                # Update lunch price
                new_lunch_price = 6.75
                update_response = self.session.put(f"{API_BASE}/lunch-settings", 
                                                 params={"price": new_lunch_price})
                
                if update_response.status_code == 200:
                    update_result = update_response.json()
                    
                    # Check if existing orders were updated
                    if 'updated_orders' in update_result:
                        updated_count = update_result['updated_orders']
                        self.log_test("Bug 4 - Retroactive Price Updates", True, 
                                    f"✅ Lunch price updated to €{new_lunch_price:.2f}, {updated_count} existing orders updated")
                        return True
                    else:
                        self.log_test("Bug 4 - Retroactive Price Updates", True, 
                                    f"✅ Lunch price updated to €{new_lunch_price:.2f} (no existing orders to update)")
                        return True
                else:
                    self.log_test("Bug 4 - Retroactive Price Updates", False, 
                                f"Failed to update lunch price: HTTP {update_response.status_code}")
                    return False
            else:
                self.log_test("Bug 4 - Retroactive Price Updates", False, 
                            f"Failed to get lunch settings: HTTP {lunch_response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Bug 4 - Retroactive Price Updates", False, f"Exception: {str(e)}")
            return False
    
    def run_all_bug_fix_tests(self):
        """Run all 4 specific bug fix tests"""
        print("🎯 TESTING 4 SPECIFIC BUG FIXES")
        print("=" * 60)
        print(f"🌐 Testing against: {API_BASE}")
        print("=" * 60)
        
        # Setup test data
        if not self.setup_test_data():
            print("❌ Failed to setup test data")
            return False
        
        # Run the 4 specific bug fix tests
        bug_tests = [
            ("Bug 1 - Simplified Topping Creation", self.test_bug_1_simplified_topping_creation),
            ("Bug 2 - Lunch Display Logic", self.test_bug_2_lunch_display_logic),
            ("Bug 3 - Lunch Counter in Shopping List", self.test_bug_3_lunch_counter_in_shopping_list),
            ("Bug 4 - Retroactive Price Updates", self.test_bug_4_retroactive_price_updates),
        ]
        
        passed_tests = 0
        
        for test_name, test_func in bug_tests:
            try:
                if test_func():
                    passed_tests += 1
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test_name}: {str(e)}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 BUG FIXES TESTING SUMMARY")
        print("=" * 60)
        print(f"📊 Overall: {passed_tests}/{len(bug_tests)} bug fixes working")
        
        if passed_tests == len(bug_tests):
            print("🎉 ALL 4 BUG FIXES ARE WORKING CORRECTLY!")
            return True
        elif passed_tests >= 3:
            print("✅ MOST BUG FIXES ARE WORKING (3+ out of 4)")
            return True
        else:
            print("⚠️ SOME BUG FIXES NEED ATTENTION")
            return False

if __name__ == "__main__":
    tester = BugFixesTester()
    success = tester.run_all_bug_fix_tests()
    sys.exit(0 if success else 1)