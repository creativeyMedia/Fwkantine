#!/usr/bin/env python3
"""
Bestellen Button Functionality Test
Tests the critical daily summary API that powers the "Bestellen" button
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

class BestellenButtonTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.department_id = "fw4abteilung1"
        
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

    def test_bestellen_button_functionality(self):
        """Test the daily summary API that powers the Bestellen button"""
        print("\n=== Testing Bestellen Button Functionality ===")
        
        success_count = 0
        
        # Test 1: Get daily summary for today (Berlin timezone)
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{self.department_id}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check critical fields for Bestellen button
                required_fields = ['date', 'breakfast_summary', 'employee_orders', 'shopping_list', 'total_boiled_eggs']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Daily Summary - Required Fields", True, 
                                f"All fields required for Bestellen button present")
                    success_count += 1
                else:
                    self.log_test("Daily Summary - Required Fields", False, 
                                f"Missing fields: {missing_fields}")
                
                # Check date is Berlin timezone (2025-08-25)
                summary_date = summary.get('date', '')
                if summary_date == "2025-08-25":
                    self.log_test("Daily Summary - Berlin Date", True, 
                                f"Correct Berlin date for new day: {summary_date}")
                    success_count += 1
                else:
                    self.log_test("Daily Summary - Berlin Date", False, 
                                f"Expected 2025-08-25, got {summary_date}")
                
                # Check shopping list structure (critical for ordering)
                shopping_list = summary.get('shopping_list', {})
                if isinstance(shopping_list, dict):
                    # Check for roll types
                    roll_types = ['weiss', 'koerner']
                    shopping_list_valid = True
                    
                    for roll_type in roll_types:
                        if roll_type in shopping_list:
                            roll_data = shopping_list[roll_type]
                            if not (isinstance(roll_data, dict) and 
                                   'halves' in roll_data and 
                                   'whole_rolls' in roll_data):
                                shopping_list_valid = False
                                break
                    
                    if shopping_list_valid:
                        self.log_test("Daily Summary - Shopping List Structure", True, 
                                    f"Shopping list has correct structure for ordering")
                        success_count += 1
                    else:
                        self.log_test("Daily Summary - Shopping List Structure", False, 
                                    "Shopping list structure invalid")
                else:
                    self.log_test("Daily Summary - Shopping List Structure", False, 
                                "Shopping list is not a dictionary")
                
                # Check employee orders structure (for overview display)
                employee_orders = summary.get('employee_orders', {})
                if isinstance(employee_orders, dict):
                    self.log_test("Daily Summary - Employee Orders Structure", True, 
                                f"Employee orders structure valid ({len(employee_orders)} employees)")
                    success_count += 1
                    
                    # Check if employee orders have lunch tracking
                    has_lunch_tracking = False
                    for employee_name, order_data in employee_orders.items():
                        if isinstance(order_data, dict) and 'has_lunch' in order_data:
                            has_lunch_tracking = True
                            break
                    
                    if has_lunch_tracking:
                        self.log_test("Daily Summary - Lunch Tracking", True, 
                                    "Employee orders include lunch tracking for 'X' markers")
                        success_count += 1
                    else:
                        self.log_test("Daily Summary - Lunch Tracking", False, 
                                    "Employee orders missing lunch tracking")
                else:
                    self.log_test("Daily Summary - Employee Orders Structure", False, 
                                "Employee orders structure invalid")
                
                # Check total boiled eggs (for ordering)
                total_boiled_eggs = summary.get('total_boiled_eggs', 0)
                if isinstance(total_boiled_eggs, int) and total_boiled_eggs >= 0:
                    self.log_test("Daily Summary - Boiled Eggs Count", True, 
                                f"Total boiled eggs: {total_boiled_eggs}")
                    success_count += 1
                else:
                    self.log_test("Daily Summary - Boiled Eggs Count", False, 
                                f"Invalid boiled eggs count: {total_boiled_eggs}")
                
            else:
                self.log_test("Daily Summary API", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary API", False, f"Exception: {str(e)}")
        
        return success_count >= 4

    def test_bestellen_button_with_orders(self):
        """Test Bestellen button functionality with actual orders"""
        print("\n=== Testing Bestellen Button with Orders ===")
        
        success_count = 0
        
        # Create a test employee first
        test_employee_id = None
        try:
            employee_data = {
                "name": "Bestellen Test Employee",
                "department_id": self.department_id
            }
            
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                test_employee_id = employee['id']
                self.log_test("Create Test Employee for Bestellen", True, 
                            f"Created employee: {employee['name']}")
                success_count += 1
                
        except Exception as e:
            self.log_test("Create Test Employee for Bestellen", False, f"Exception: {str(e)}")
        
        if not test_employee_id:
            return False
        
        # Create a breakfast order with various items
        try:
            breakfast_order = {
                "employee_id": test_employee_id,
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 4,
                        "white_halves": 2,
                        "seeded_halves": 2,
                        "toppings": ["ruehrei", "kaese", "schinken", "butter"],
                        "has_lunch": True,
                        "boiled_eggs": 3
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            
            if response.status_code == 200:
                order = response.json()
                self.log_test("Create Complex Breakfast Order", True, 
                            f"Created order with rolls, toppings, lunch, and eggs: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create Complex Breakfast Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Complex Breakfast Order", False, f"Exception: {str(e)}")
        
        # Now test the daily summary with the order
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{self.department_id}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check shopping list calculations
                shopping_list = summary.get('shopping_list', {})
                
                # Should have white and seeded rolls
                white_rolls = shopping_list.get('weiss', {}).get('whole_rolls', 0)
                seeded_rolls = shopping_list.get('koerner', {}).get('whole_rolls', 0)
                
                if white_rolls > 0 and seeded_rolls > 0:
                    self.log_test("Shopping List - Roll Calculations", True, 
                                f"White rolls: {white_rolls}, Seeded rolls: {seeded_rolls}")
                    success_count += 1
                else:
                    self.log_test("Shopping List - Roll Calculations", False, 
                                f"Expected rolls in shopping list, got white: {white_rolls}, seeded: {seeded_rolls}")
                
                # Check boiled eggs total
                total_boiled_eggs = summary.get('total_boiled_eggs', 0)
                if total_boiled_eggs >= 3:  # We ordered 3 eggs
                    self.log_test("Shopping List - Boiled Eggs Total", True, 
                                f"Total boiled eggs: {total_boiled_eggs}")
                    success_count += 1
                else:
                    self.log_test("Shopping List - Boiled Eggs Total", False, 
                                f"Expected at least 3 boiled eggs, got {total_boiled_eggs}")
                
                # Check employee orders show lunch
                employee_orders = summary.get('employee_orders', {})
                lunch_found = False
                for employee_name, order_data in employee_orders.items():
                    if "Bestellen Test Employee" in employee_name:
                        if order_data.get('has_lunch', False):
                            lunch_found = True
                            break
                
                if lunch_found:
                    self.log_test("Employee Orders - Lunch Tracking", True, 
                                "Employee order correctly shows lunch option")
                    success_count += 1
                else:
                    self.log_test("Employee Orders - Lunch Tracking", False, 
                                "Employee order missing lunch tracking")
                
            else:
                self.log_test("Daily Summary with Orders", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary with Orders", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def run_all_tests(self):
        """Run all Bestellen button tests"""
        print("🛒 BESTELLEN BUTTON FUNCTIONALITY TESTING")
        print("=" * 60)
        print(f"Testing department: {self.department_id}")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Run all tests
        test_methods = [
            self.test_bestellen_button_functionality,
            self.test_bestellen_button_with_orders
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for test_method in test_methods:
            try:
                result = test_method()
                total_tests += 1
                if result:
                    passed_tests += 1
            except Exception as e:
                print(f"\n❌ EXCEPTION in {test_method.__name__}: {str(e)}")
                total_tests += 1
        
        # Print summary
        print("\n" + "=" * 60)
        print("🛒 BESTELLEN BUTTON TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Detailed results
        print("\nDetailed Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        return success_rate >= 75

def main():
    """Main function to run the Bestellen button tests"""
    tester = BestellenButtonTest()
    success = tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()