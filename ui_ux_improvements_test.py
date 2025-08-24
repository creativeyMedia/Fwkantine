#!/usr/bin/env python3
"""
UI/UX Improvements Backend Test Suite
Tests the new UI/UX improvements in the backend, specifically:
1. Enhanced Daily Summary with Lunch Tracking
2. Order Creation with Various Combinations
3. Breakfast Status Check
4. Complete Order Display
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

class UIUXImprovementsTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.department_id = None
        self.employee_id = None
        
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
        """Setup test environment with department and multiple employees"""
        print("\n=== Setting Up Test Environment ===")
        
        # Get first available department
        try:
            response = self.session.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                departments = response.json()
                if departments:
                    self.department_id = departments[0]['id']
                    dept_name = departments[0]['name']
                    self.log_test("Get Department", True, f"Using department: {dept_name} (ID: {self.department_id})")
                else:
                    self.log_test("Get Department", False, "No departments found")
                    return False
            else:
                self.log_test("Get Department", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Get Department", False, f"Exception: {str(e)}")
            return False
        
        # Authenticate with department credentials
        try:
            login_data = {
                "department_name": dept_name,
                "password": "password1"
            }
            response = self.session.post(f"{API_BASE}/login/department", json=login_data)
            if response.status_code == 200:
                self.log_test("Department Authentication", True, "Successfully authenticated with password1")
            else:
                self.log_test("Department Authentication", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Department Authentication", False, f"Exception: {str(e)}")
            return False
        
        # Create multiple test employees for different order types
        self.test_employees = []
        employee_names = [
            "UI Test Employee 1",
            "UI Test Employee 2", 
            "UI Test Employee 3",
            "UI Test Employee 4",
            "UI Test Employee 5"
        ]
        
        for name in employee_names:
            try:
                employee_data = {
                    "name": name,
                    "department_id": self.department_id
                }
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    employee = response.json()
                    self.test_employees.append(employee)
                    self.log_test(f"Create {name}", True, f"Created employee: {employee['name']} (ID: {employee['id']})")
                else:
                    self.log_test(f"Create {name}", False, f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test(f"Create {name}", False, f"Exception: {str(e)}")
        
        if len(self.test_employees) >= 3:
            self.employee_id = self.test_employees[0]['id']  # Set primary employee for backward compatibility
            return True
        else:
            self.log_test("Setup Test Employees", False, "Failed to create enough test employees")
            return False
    
    def test_enhanced_daily_summary_with_lunch_tracking(self):
        """Test GET /api/orders/daily-summary/{department_id} endpoint for lunch tracking"""
        print("\n=== Testing Enhanced Daily Summary with Lunch Tracking ===")
        
        if not self.department_id or not hasattr(self, 'test_employees') or len(self.test_employees) < 2:
            self.log_test("Enhanced Daily Summary", False, "Missing department or employees for testing")
            return False
        
        success_count = 0
        
        # Create test breakfast orders with has_lunch=true and has_lunch=false using different employees
        try:
            # Order 1: Breakfast with lunch (has_lunch=true) - Employee 1
            breakfast_with_lunch = {
                "employee_id": self.test_employees[0]['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 2,
                        "white_halves": 2,
                        "seeded_halves": 0,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": True,
                        "boiled_eggs": 0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_with_lunch)
            if response.status_code == 200:
                order = response.json()
                self.log_test("Create Breakfast Order with Lunch", True, 
                            f"Created order with has_lunch=true, total: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create Breakfast Order with Lunch", False, 
                            f"HTTP {response.status_code}: {response.text}")
            
            # Order 2: Breakfast without lunch (has_lunch=false) - Employee 2
            breakfast_without_lunch = {
                "employee_id": self.test_employees[1]['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 1,
                        "white_halves": 0,
                        "seeded_halves": 1,
                        "toppings": ["schinken"],
                        "has_lunch": False,
                        "boiled_eggs": 0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_without_lunch)
            if response.status_code == 200:
                order = response.json()
                self.log_test("Create Breakfast Order without Lunch", True, 
                            f"Created order with has_lunch=false, total: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create Breakfast Order without Lunch", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Test Breakfast Orders", False, f"Exception: {str(e)}")
        
        # Test daily summary includes has_lunch property for each employee
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{self.department_id}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check if employee_orders section exists
                if 'employee_orders' in summary:
                    employee_orders = summary['employee_orders']
                    
                    # Find employees with has_lunch property
                    employees_with_lunch_property = 0
                    employees_with_lunch_true = 0
                    employees_with_lunch_false = 0
                    
                    for employee_name, employee_data in employee_orders.items():
                        if 'has_lunch' in employee_data:
                            employees_with_lunch_property += 1
                            has_lunch_value = employee_data['has_lunch']
                            if has_lunch_value:
                                employees_with_lunch_true += 1
                            else:
                                employees_with_lunch_false += 1
                    
                    if employees_with_lunch_property >= 2:
                        self.log_test("Employee has_lunch Property", True, 
                                    f"Found {employees_with_lunch_property} employees with has_lunch property")
                        success_count += 1
                    else:
                        self.log_test("Employee has_lunch Property", False, 
                                    f"Only found {employees_with_lunch_property} employees with has_lunch property")
                    
                    # Verify lunch count is calculated correctly
                    if employees_with_lunch_true > 0:
                        self.log_test("Lunch Count Calculation", True, 
                                    f"Found {employees_with_lunch_true} employees with lunch orders")
                        success_count += 1
                    else:
                        self.log_test("Lunch Count Calculation", False, 
                                    "No lunch orders found in daily summary")
                else:
                    self.log_test("Daily Summary Structure", False, 
                                "employee_orders section missing from daily summary")
                
            else:
                self.log_test("Get Daily Summary", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Daily Summary", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_order_creation_various_combinations(self):
        """Test POST /api/orders endpoint with different order types"""
        print("\n=== Testing Order Creation with Various Combinations ===")
        
        if not self.department_id or not hasattr(self, 'test_employees') or len(self.test_employees) < 4:
            self.log_test("Order Creation Various Combinations", False, "Missing department or employees for testing")
            return False
        
        success_count = 0
        
        # Test 1: Only breakfast rolls with toppings - Employee 2 (if not already used)
        try:
            # Use employee 2 or 3 depending on availability
            employee_idx = 2 if len(self.test_employees) > 2 else 1
            rolls_only_order = {
                "employee_id": self.test_employees[employee_idx]['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 2,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese", "schinken"],
                        "has_lunch": False,
                        "boiled_eggs": 0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=rolls_only_order)
            if response.status_code == 200:
                order = response.json()
                self.log_test("Only Breakfast Rolls with Toppings", True, 
                            f"Created rolls-only order, total: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Only Breakfast Rolls with Toppings", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Only Breakfast Rolls with Toppings", False, f"Exception: {str(e)}")
        
        # Test 2: Only boiled eggs (no rolls) - Employee 3
        try:
            employee_idx = 3 if len(self.test_employees) > 3 else 2
            eggs_only_order = {
                "employee_id": self.test_employees[employee_idx]['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 0,
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],
                        "has_lunch": False,
                        "boiled_eggs": 3
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=eggs_only_order)
            if response.status_code == 200:
                order = response.json()
                self.log_test("Only Boiled Eggs (no rolls)", True, 
                            f"Created eggs-only order, total: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Only Boiled Eggs (no rolls)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Only Boiled Eggs (no rolls)", False, f"Exception: {str(e)}")
        
        # Test 3: Only lunch (no rolls, no eggs) - Employee 4
        try:
            employee_idx = 4 if len(self.test_employees) > 4 else 3
            lunch_only_order = {
                "employee_id": self.test_employees[employee_idx]['id'],
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 0,
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],
                        "has_lunch": True,
                        "boiled_eggs": 0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=lunch_only_order)
            if response.status_code == 200:
                order = response.json()
                self.log_test("Only Lunch (no rolls, no eggs)", True, 
                            f"Created lunch-only order, total: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Only Lunch (no rolls, no eggs)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Only Lunch (no rolls, no eggs)", False, f"Exception: {str(e)}")
        
        # Test 4: Mixed orders (rolls + eggs + lunch) - Create new employee if needed
        try:
            # Create a new employee for mixed order if we don't have enough
            if len(self.test_employees) < 5:
                employee_data = {
                    "name": "Mixed Order Employee",
                    "department_id": self.department_id
                }
                response = self.session.post(f"{API_BASE}/employees", json=employee_data)
                if response.status_code == 200:
                    mixed_employee = response.json()
                    mixed_employee_id = mixed_employee['id']
                else:
                    # Fallback to existing employee
                    mixed_employee_id = self.test_employees[0]['id']
            else:
                mixed_employee_id = self.test_employees[4]['id']
            
            mixed_order = {
                "employee_id": mixed_employee_id,
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": True,
                        "boiled_eggs": 2
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=mixed_order)
            if response.status_code == 200:
                order = response.json()
                self.log_test("Mixed Orders (rolls + eggs + lunch)", True, 
                            f"Created mixed order, total: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Mixed Orders (rolls + eggs + lunch)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Mixed Orders (rolls + eggs + lunch)", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def test_breakfast_status_check(self):
        """Test GET /api/breakfast-status/{department_id} endpoint"""
        print("\n=== Testing Breakfast Status Check ===")
        
        if not self.department_id:
            self.log_test("Breakfast Status Check", False, "Missing department for testing")
            return False
        
        success_count = 0
        
        # Test getting breakfast status
        try:
            response = self.session.get(f"{API_BASE}/breakfast-status/{self.department_id}")
            
            if response.status_code == 200:
                status = response.json()
                
                # Check required fields
                required_fields = ['is_closed', 'date']
                missing_fields = [field for field in required_fields if field not in status]
                
                if not missing_fields:
                    is_closed = status['is_closed']
                    date = status['date']
                    self.log_test("Breakfast Status Structure", True, 
                                f"Status: is_closed={is_closed}, date={date}")
                    success_count += 1
                    
                    # Verify date is today's date
                    today = datetime.now().date().isoformat()
                    if status['date'] == today:
                        self.log_test("Breakfast Status Date", True, f"Correct date: {today}")
                        success_count += 1
                    else:
                        self.log_test("Breakfast Status Date", False, 
                                    f"Expected {today}, got {status['date']}")
                else:
                    self.log_test("Breakfast Status Structure", False, 
                                f"Missing fields: {missing_fields}")
                
            else:
                self.log_test("Get Breakfast Status", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Breakfast Status", False, f"Exception: {str(e)}")
        
        return success_count >= 1
    
    def test_complete_order_display(self):
        """Verify that all order types are properly stored and retrieved in daily summary"""
        print("\n=== Testing Complete Order Display ===")
        
        if not self.department_id:
            self.log_test("Complete Order Display", False, "Missing department for testing")
            return False
        
        success_count = 0
        
        # Test that all order types appear in daily summary
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{self.department_id}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check if employee_orders section exists and contains our test employees
                if 'employee_orders' in summary:
                    employee_orders = summary['employee_orders']
                    
                    # Count different order types found
                    employees_with_eggs = 0
                    employees_with_lunch = 0
                    employees_with_rolls = 0
                    
                    for employee_name, employee_data in employee_orders.items():
                        # Check for boiled eggs
                        if employee_data.get('boiled_eggs', 0) > 0:
                            employees_with_eggs += 1
                        
                        # Check for lunch
                        if employee_data.get('has_lunch', False):
                            employees_with_lunch += 1
                        
                        # Check for rolls
                        if (employee_data.get('white_halves', 0) + employee_data.get('seeded_halves', 0)) > 0:
                            employees_with_rolls += 1
                    
                    order_types_found = []
                    if employees_with_eggs > 0:
                        order_types_found.append(f"boiled_eggs({employees_with_eggs})")
                    if employees_with_lunch > 0:
                        order_types_found.append(f"lunch({employees_with_lunch})")
                    if employees_with_rolls > 0:
                        order_types_found.append(f"rolls({employees_with_rolls})")
                    
                    if len(order_types_found) >= 2:  # At least 2 different order types
                        self.log_test("Complete Order Types Display", True, 
                                    f"Multiple order types found: {', '.join(order_types_found)}")
                        success_count += 1
                    else:
                        self.log_test("Complete Order Types Display", False, 
                                    f"Only found order types: {', '.join(order_types_found)}")
                    
                    # Check that we have multiple employees with orders
                    if len(employee_orders) >= 3:
                        self.log_test("Multiple Employees in Summary", True, 
                                    f"Found {len(employee_orders)} employees with orders")
                        success_count += 1
                    else:
                        self.log_test("Multiple Employees in Summary", False, 
                                    f"Only found {len(employee_orders)} employees with orders")
                else:
                    self.log_test("Daily Summary Structure", False, 
                                "employee_orders section missing from daily summary")
                
                # Check shopping list includes all components
                if 'shopping_list' in summary:
                    shopping_list = summary['shopping_list']
                    self.log_test("Shopping List Present", True, 
                                f"Shopping list contains: {list(shopping_list.keys())}")
                    success_count += 1
                
                # Check total boiled eggs tracking
                if 'total_boiled_eggs' in summary:
                    total_eggs = summary['total_boiled_eggs']
                    if total_eggs > 0:
                        self.log_test("Total Boiled Eggs Tracking", True, 
                                    f"Total boiled eggs tracked: {total_eggs}")
                        success_count += 1
                    else:
                        self.log_test("Total Boiled Eggs Tracking", False, 
                                    "No boiled eggs found in summary")
                
            else:
                self.log_test("Get Daily Summary for Complete Display", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Daily Summary for Complete Display", False, f"Exception: {str(e)}")
        
        return success_count >= 3
    
    def run_all_tests(self):
        """Run all UI/UX improvement tests"""
        print("🎯 UI/UX IMPROVEMENTS BACKEND TESTING STARTED")
        print("=" * 60)
        
        # Setup test environment
        if not self.setup_test_environment():
            print("\n❌ FAILED TO SETUP TEST ENVIRONMENT - ABORTING TESTS")
            return False
        
        # Run all tests
        test_methods = [
            self.test_enhanced_daily_summary_with_lunch_tracking,
            self.test_order_creation_various_combinations,
            self.test_breakfast_status_check,
            self.test_complete_order_display
        ]
        
        passed_tests = 0
        total_tests = len(test_methods)
        
        for test_method in test_methods:
            if test_method():
                passed_tests += 1
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎯 UI/UX IMPROVEMENTS BACKEND TESTING SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print individual test results
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}")
            if result['message']:
                print(f"    {result['message']}")
        
        return passed_tests == total_tests

def main():
    """Main test execution"""
    tester = UIUXImprovementsTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL UI/UX IMPROVEMENTS BACKEND TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n⚠️ SOME UI/UX IMPROVEMENTS BACKEND TESTS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    main()