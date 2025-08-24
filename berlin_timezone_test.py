#!/usr/bin/env python3
"""
Berlin Timezone Fix Testing Suite
Tests the critical APIs that should now use Berlin timezone to resolve the "new day" problem
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

class BerlinTimezoneTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.department_id = "fw4abteilung1"  # Use specific department as requested
        self.admin_token = None
        
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

    def authenticate_admin(self):
        """Authenticate as department admin for fw4abteilung1"""
        print("\n=== Authenticating as Department Admin ===")
        
        try:
            # Try different admin password variations for fw4abteilung1
            admin_passwords = ["admin1", "admin1a", "adminA"]
            
            for password in admin_passwords:
                admin_login_data = {
                    "department_name": "1. Wachabteilung",
                    "admin_password": password
                }
                
                response = self.session.post(f"{API_BASE}/login/department-admin", json=admin_login_data)
                
                if response.status_code == 200:
                    login_result = response.json()
                    self.admin_token = login_result
                    self.log_test("Department Admin Authentication", True, 
                                f"Successfully authenticated with password: {password}")
                    return True
            
            self.log_test("Department Admin Authentication", False, 
                        "Failed to authenticate with any admin password")
            return False
                
        except Exception as e:
            self.log_test("Department Admin Authentication", False, f"Exception: {str(e)}")
            return False

    def test_daily_summary_api(self):
        """Test GET /api/orders/daily-summary/{department_id} - Berlin timezone date handling"""
        print("\n=== Testing Daily Summary API (Berlin Timezone) ===")
        
        success_count = 0
        
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{self.department_id}")
            
            if response.status_code == 200:
                summary = response.json()
                
                # Check if summary has expected structure
                required_fields = ['date', 'breakfast_summary', 'employee_orders', 'drinks_summary', 'sweets_summary']
                missing_fields = [field for field in required_fields if field not in summary]
                
                if not missing_fields:
                    self.log_test("Daily Summary Structure", True, 
                                f"All required fields present")
                    success_count += 1
                else:
                    self.log_test("Daily Summary Structure", False, 
                                f"Missing fields: {missing_fields}")
                
                # Check if date shows Berlin timezone date (2025-08-25)
                summary_date = summary.get('date', '')
                expected_date = "2025-08-25"  # Expected Berlin time date
                
                if summary_date == expected_date:
                    self.log_test("Berlin Timezone Date Recognition", True, 
                                f"Correct Berlin date: {summary_date}")
                    success_count += 1
                else:
                    self.log_test("Berlin Timezone Date Recognition", False, 
                                f"Expected {expected_date}, got {summary_date}")
                
                # Check if it returns empty results for today (new day)
                employee_orders = summary.get('employee_orders', {})
                breakfast_summary = summary.get('breakfast_summary', {})
                
                if len(employee_orders) == 0 and len(breakfast_summary) == 0:
                    self.log_test("New Day Empty Results", True, 
                                "Correctly shows empty results for new day (2025-08-25)")
                    success_count += 1
                else:
                    self.log_test("New Day Empty Results", False, 
                                f"Expected empty results, found {len(employee_orders)} employee orders")
                
            else:
                self.log_test("Daily Summary API", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Daily Summary API", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_breakfast_status_api(self):
        """Test GET /api/breakfast-status/{department_id} - Berlin timezone and auto-reopening"""
        print("\n=== Testing Breakfast Status API (Berlin Timezone) ===")
        
        success_count = 0
        
        try:
            response = self.session.get(f"{API_BASE}/breakfast-status/{self.department_id}")
            
            if response.status_code == 200:
                status = response.json()
                
                # Check if status has expected structure
                required_fields = ['is_closed', 'date']
                missing_fields = [field for field in required_fields if field not in status]
                
                if not missing_fields:
                    self.log_test("Breakfast Status Structure", True, 
                                f"All required fields present")
                    success_count += 1
                else:
                    self.log_test("Breakfast Status Structure", False, 
                                f"Missing fields: {missing_fields}")
                
                # Check if date shows Berlin timezone date (2025-08-25)
                status_date = status.get('date', '')
                expected_date = "2025-08-25"
                
                if status_date == expected_date:
                    self.log_test("Breakfast Status Berlin Date", True, 
                                f"Correct Berlin date: {status_date}")
                    success_count += 1
                else:
                    self.log_test("Breakfast Status Berlin Date", False, 
                                f"Expected {expected_date}, got {status_date}")
                
                # Check if breakfast is automatically reopened for new day
                is_closed = status.get('is_closed', True)
                
                if not is_closed:
                    self.log_test("Auto-Reopening for New Day", True, 
                                "Breakfast automatically reopened for new day")
                    success_count += 1
                else:
                    self.log_test("Auto-Reopening for New Day", False, 
                                "Breakfast should be automatically reopened for new day")
                
            else:
                self.log_test("Breakfast Status API", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Breakfast Status API", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def test_daily_lunch_price_integration(self):
        """Test daily lunch price integration with Berlin timezone"""
        print("\n=== Testing Daily Lunch Price Integration (Berlin Timezone) ===")
        
        success_count = 0
        
        # Test 1: Set daily lunch price for today (Berlin time)
        try:
            today_berlin = "2025-08-25"  # Berlin timezone date
            lunch_price = 4.60
            
            response = self.session.put(f"{API_BASE}/daily-lunch-settings/{self.department_id}/{today_berlin}", 
                                      params={"lunch_price": lunch_price})
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Set Daily Lunch Price (Berlin Date)", True, 
                            f"Set lunch price €{lunch_price:.2f} for {today_berlin}")
                success_count += 1
            else:
                self.log_test("Set Daily Lunch Price (Berlin Date)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Set Daily Lunch Price (Berlin Date)", False, f"Exception: {str(e)}")
        
        # Test 2: Get daily lunch price for today
        try:
            response = self.session.get(f"{API_BASE}/daily-lunch-price/{self.department_id}/2025-08-25")
            
            if response.status_code == 200:
                price_data = response.json()
                retrieved_price = price_data.get('lunch_price', 0)
                
                if abs(retrieved_price - 4.60) < 0.01:
                    self.log_test("Get Daily Lunch Price (Berlin Date)", True, 
                                f"Retrieved correct price: €{retrieved_price:.2f}")
                    success_count += 1
                else:
                    self.log_test("Get Daily Lunch Price (Berlin Date)", False, 
                                f"Expected €4.60, got €{retrieved_price:.2f}")
            else:
                self.log_test("Get Daily Lunch Price (Berlin Date)", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Get Daily Lunch Price (Berlin Date)", False, f"Exception: {str(e)}")
        
        return success_count >= 1

    def test_close_reopen_breakfast_apis(self):
        """Test close/reopen breakfast APIs with Berlin timezone"""
        print("\n=== Testing Close/Reopen Breakfast APIs (Berlin Timezone) ===")
        
        if not self.admin_token:
            self.log_test("Close/Reopen Breakfast APIs", False, "Admin authentication required")
            return False
        
        success_count = 0
        
        # Test 1: Close breakfast for today
        try:
            response = self.session.post(f"{API_BASE}/department-admin/close-breakfast/{self.department_id}", 
                                       params={"admin_name": "Test Admin"})
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Close Breakfast API", True, 
                            f"Successfully closed breakfast: {result.get('message', 'Success')}")
                success_count += 1
            else:
                self.log_test("Close Breakfast API", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Close Breakfast API", False, f"Exception: {str(e)}")
        
        # Test 2: Verify breakfast is closed
        try:
            response = self.session.get(f"{API_BASE}/breakfast-status/{self.department_id}")
            
            if response.status_code == 200:
                status = response.json()
                is_closed = status.get('is_closed', False)
                
                if is_closed:
                    self.log_test("Verify Breakfast Closed", True, 
                                "Breakfast status correctly shows closed")
                    success_count += 1
                else:
                    self.log_test("Verify Breakfast Closed", False, 
                                "Breakfast should be closed but shows open")
            else:
                self.log_test("Verify Breakfast Closed", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Verify Breakfast Closed", False, f"Exception: {str(e)}")
        
        # Test 3: Reopen breakfast
        try:
            response = self.session.post(f"{API_BASE}/department-admin/reopen-breakfast/{self.department_id}")
            
            if response.status_code == 200:
                result = response.json()
                self.log_test("Reopen Breakfast API", True, 
                            f"Successfully reopened breakfast: {result.get('message', 'Success')}")
                success_count += 1
            else:
                self.log_test("Reopen Breakfast API", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Reopen Breakfast API", False, f"Exception: {str(e)}")
        
        # Test 4: Verify breakfast is reopened
        try:
            response = self.session.get(f"{API_BASE}/breakfast-status/{self.department_id}")
            
            if response.status_code == 200:
                status = response.json()
                is_closed = status.get('is_closed', True)
                
                if not is_closed:
                    self.log_test("Verify Breakfast Reopened", True, 
                                "Breakfast status correctly shows reopened")
                    success_count += 1
                else:
                    self.log_test("Verify Breakfast Reopened", False, 
                                "Breakfast should be reopened but shows closed")
            else:
                self.log_test("Verify Breakfast Reopened", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Verify Breakfast Reopened", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_end_to_end_new_day(self):
        """Test end-to-end new day functionality"""
        print("\n=== Testing End-to-End New Day Functionality ===")
        
        success_count = 0
        
        # First, create a test employee for fw4abteilung1
        test_employee_id = None
        try:
            employee_data = {
                "name": "Berlin Timezone Test Employee",
                "department_id": self.department_id
            }
            
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                test_employee_id = employee['id']
                self.log_test("Create Test Employee", True, 
                            f"Created test employee: {employee['name']}")
                success_count += 1
            else:
                self.log_test("Create Test Employee", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create Test Employee", False, f"Exception: {str(e)}")
        
        if not test_employee_id:
            self.log_test("End-to-End New Day Test", False, "Could not create test employee")
            return False
        
        # Test 1: Create a new breakfast order for today (2025-08-25)
        try:
            breakfast_order = {
                "employee_id": test_employee_id,
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": True,
                        "boiled_eggs": 0
                    }
                ]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
            
            if response.status_code == 200:
                order = response.json()
                self.log_test("Create New Day Breakfast Order", True, 
                            f"Created breakfast order for today: €{order['total_price']:.2f}")
                success_count += 1
            else:
                self.log_test("Create New Day Breakfast Order", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Create New Day Breakfast Order", False, f"Exception: {str(e)}")
        
        # Test 2: Verify order appears in daily summary
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-summary/{self.department_id}")
            
            if response.status_code == 200:
                summary = response.json()
                employee_orders = summary.get('employee_orders', {})
                
                # Check if our test employee appears in the summary
                test_employee_found = False
                for employee_name, order_data in employee_orders.items():
                    if "Berlin Timezone Test Employee" in employee_name:
                        test_employee_found = True
                        break
                
                if test_employee_found:
                    self.log_test("Order in Daily Summary", True, 
                                "New order correctly appears in daily summary")
                    success_count += 1
                else:
                    self.log_test("Order in Daily Summary", False, 
                                "New order does not appear in daily summary")
            else:
                self.log_test("Order in Daily Summary", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Order in Daily Summary", False, f"Exception: {str(e)}")
        
        # Test 3: Verify breakfast history shows separate entries for different dates
        try:
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{self.department_id}?days_back=5")
            
            if response.status_code == 200:
                history_data = response.json()
                history = history_data.get('history', [])
                
                # Check if we have entries for different dates
                dates_found = [entry.get('date', '') for entry in history]
                
                # Look for both 2025-08-24 and 2025-08-25
                has_2024_08_24 = "2025-08-24" in dates_found
                has_2025_08_25 = "2025-08-25" in dates_found
                
                if has_2025_08_25:
                    self.log_test("Breakfast History - New Day Entry", True, 
                                "Breakfast history shows entry for 2025-08-25")
                    success_count += 1
                else:
                    self.log_test("Breakfast History - New Day Entry", False, 
                                f"Expected 2025-08-25 in history, found dates: {dates_found}")
                
                if len(dates_found) > 1:
                    self.log_test("Breakfast History - Separate Date Entries", True, 
                                f"History shows separate entries for different dates: {dates_found}")
                    success_count += 1
                else:
                    self.log_test("Breakfast History - Separate Date Entries", False, 
                                f"Expected multiple date entries, found: {dates_found}")
                
            else:
                self.log_test("Breakfast History Check", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Breakfast History Check", False, f"Exception: {str(e)}")
        
        return success_count >= 3

    def test_order_update_daily_pricing(self):
        """Test order update integration with daily lunch pricing"""
        print("\n=== Testing Order Update with Daily Lunch Pricing ===")
        
        success_count = 0
        
        # First, create a test employee and order
        test_employee_id = None
        test_order_id = None
        
        try:
            employee_data = {
                "name": "Order Update Test Employee",
                "department_id": self.department_id
            }
            
            response = self.session.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                test_employee_id = employee['id']
                
                # Create initial order
                breakfast_order = {
                    "employee_id": test_employee_id,
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
                
                response = self.session.post(f"{API_BASE}/orders", json=breakfast_order)
                if response.status_code == 200:
                    order = response.json()
                    test_order_id = order['id']
                    original_price = order['total_price']
                    
                    self.log_test("Create Order for Update Test", True, 
                                f"Created order with price: €{original_price:.2f}")
                    success_count += 1
                
        except Exception as e:
            self.log_test("Create Order for Update Test", False, f"Exception: {str(e)}")
        
        if not test_order_id:
            self.log_test("Order Update Test", False, "Could not create test order")
            return False
        
        # Test updating the order - this should use today's daily lunch price
        try:
            update_data = {
                "breakfast_items": [
                    {
                        "total_halves": 3,
                        "white_halves": 2,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese", "schinken"],
                        "has_lunch": True,
                        "boiled_eggs": 1
                    }
                ]
            }
            
            response = self.session.put(f"{API_BASE}/orders/{test_order_id}", json=update_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Get the updated order to check lunch price
                order_response = self.session.get(f"{API_BASE}/employees/{test_employee_id}/orders")
                if order_response.status_code == 200:
                    orders_data = order_response.json()
                    orders = orders_data.get('orders', [])
                    
                    # Find our updated order
                    updated_order = None
                    for order in orders:
                        if order['id'] == test_order_id:
                            updated_order = order
                            break
                    
                    if updated_order:
                        lunch_price_used = updated_order.get('lunch_price', 0)
                        
                        if abs(lunch_price_used - 4.60) < 0.01:
                            self.log_test("Order Update Uses Daily Lunch Price", True, 
                                        f"Updated order uses correct daily lunch price: €{lunch_price_used:.2f}")
                            success_count += 1
                        else:
                            self.log_test("Order Update Uses Daily Lunch Price", False, 
                                        f"Expected daily lunch price €4.60, got €{lunch_price_used:.2f}")
                        
                        self.log_test("Order Update Successful", True, 
                                    f"Order updated successfully")
                        success_count += 1
                    else:
                        self.log_test("Order Update", False, "Could not find updated order")
                else:
                    self.log_test("Order Update", False, "Could not retrieve updated order")
                
            else:
                self.log_test("Order Update", False, 
                            f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Order Update", False, f"Exception: {str(e)}")
        
        return success_count >= 2

    def run_all_tests(self):
        """Run all Berlin timezone tests"""
        print("🕐 BERLIN TIMEZONE FIX TESTING SUITE")
        print("=" * 60)
        print(f"Testing department: {self.department_id}")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 60)
        
        # Authenticate first
        if not self.authenticate_admin():
            print("\n❌ CRITICAL: Could not authenticate as admin. Some tests will be skipped.")
        
        # Run all tests
        test_methods = [
            self.test_daily_summary_api,
            self.test_breakfast_status_api,
            self.test_daily_lunch_price_integration,
            self.test_close_reopen_breakfast_apis,
            self.test_end_to_end_new_day,
            self.test_order_update_daily_pricing
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
        print("🕐 BERLIN TIMEZONE FIX TEST SUMMARY")
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
        
        if success_rate >= 75:
            print("🎉 BERLIN TIMEZONE FIX TESTS MOSTLY SUCCESSFUL!")
            return True
        else:
            print("⚠️ BERLIN TIMEZONE FIX TESTS NEED ATTENTION!")
            return False

def main():
    """Main function to run the Berlin timezone tests"""
    tester = BerlinTimezoneTest()
    success = tester.run_all_tests()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()