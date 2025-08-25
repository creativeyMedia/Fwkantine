#!/usr/bin/env python3
"""
SICHERHEITSTEST - Kritische Überprüfung
Backend Security and Functionality Testing

This script tests critical security aspects and system functionality
as requested in the security review.
"""

import requests
import json
import sys
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://canteenflow.preview.emergentagent.com/api"

class SecurityTester:
    def __init__(self):
        self.results = []
        self.critical_failures = []
        
    def log_result(self, test_name, success, message, is_critical=False):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.results.append(f"{status} {test_name}: {message}")
        
        if not success and is_critical:
            self.critical_failures.append(f"CRITICAL: {test_name} - {message}")
        
        print(f"{status} {test_name}: {message}")
    
    def test_dangerous_apis_blocked(self):
        """Test that dangerous APIs are blocked in production"""
        print("\n🔒 TESTING DANGEROUS APIs - Should be BLOCKED in Production")
        
        # Test /api/init-data
        try:
            response = requests.post(f"{BACKEND_URL}/init-data", timeout=10)
            if response.status_code == 403:
                message = response.json().get('detail', 'No detail provided')
                if "Production" in message or "production" in message:
                    self.log_result("init-data API Block", True, f"Correctly blocked with 403: {message}", is_critical=True)
                else:
                    self.log_result("init-data API Block", False, f"Blocked but wrong message: {message}", is_critical=True)
            else:
                self.log_result("init-data API Block", False, f"NOT BLOCKED! Status: {response.status_code}", is_critical=True)
        except Exception as e:
            self.log_result("init-data API Block", False, f"Request failed: {str(e)}", is_critical=True)
        
        # Test /api/migrate-to-department-specific
        try:
            response = requests.post(f"{BACKEND_URL}/migrate-to-department-specific", timeout=10)
            if response.status_code == 403:
                message = response.json().get('detail', 'No detail provided')
                if "Production" in message or "production" in message:
                    self.log_result("migrate API Block", True, f"Correctly blocked with 403: {message}", is_critical=True)
                else:
                    self.log_result("migrate API Block", False, f"Blocked but wrong message: {message}", is_critical=True)
            else:
                self.log_result("migrate API Block", False, f"NOT BLOCKED! Status: {response.status_code}", is_critical=True)
        except Exception as e:
            self.log_result("migrate API Block", False, f"Request failed: {str(e)}", is_critical=True)
    
    def test_boiled_eggs_price_stability(self):
        """Test boiled eggs price is stable and not 999.99€"""
        print("\n🥚 TESTING BOILED EGGS PRICE STABILITY")
        
        try:
            response = requests.get(f"{BACKEND_URL}/lunch-settings", timeout=10)
            if response.status_code == 200:
                data = response.json()
                boiled_eggs_price = data.get('boiled_eggs_price', 'NOT_FOUND')
                
                if boiled_eggs_price == 'NOT_FOUND':
                    self.log_result("Boiled Eggs Price Field", False, "boiled_eggs_price field missing", is_critical=True)
                elif boiled_eggs_price == 999.99:
                    self.log_result("Boiled Eggs Price Value", False, f"CRITICAL BUG: Price is 999.99€!", is_critical=True)
                elif isinstance(boiled_eggs_price, (int, float)) and 0.10 <= boiled_eggs_price <= 2.00:
                    self.log_result("Boiled Eggs Price Value", True, f"Reasonable price: €{boiled_eggs_price}")
                else:
                    self.log_result("Boiled Eggs Price Value", False, f"Unreasonable price: €{boiled_eggs_price}", is_critical=True)
                
                # Log all lunch settings for debugging
                print(f"   📋 Full lunch settings: {json.dumps(data, indent=2)}")
            else:
                self.log_result("Lunch Settings API", False, f"Failed to get lunch settings: {response.status_code}", is_critical=True)
        except Exception as e:
            self.log_result("Lunch Settings API", False, f"Request failed: {str(e)}", is_critical=True)
    
    def test_boiled_eggs_price_update(self):
        """Test that boiled eggs price update endpoint still works"""
        print("\n🔧 TESTING BOILED EGGS PRICE UPDATE FUNCTIONALITY")
        
        # First get current price
        try:
            response = requests.get(f"{BACKEND_URL}/lunch-settings", timeout=10)
            if response.status_code == 200:
                current_price = response.json().get('boiled_eggs_price', 0.50)
                print(f"   📋 Current boiled eggs price: €{current_price}")
            else:
                current_price = 0.50
                print(f"   ⚠️ Could not get current price, using default: €{current_price}")
        except:
            current_price = 0.50
            print(f"   ⚠️ Could not get current price, using default: €{current_price}")
        
        # Test updating price
        test_price = 0.75  # Test with a reasonable price
        try:
            response = requests.put(f"{BACKEND_URL}/lunch-settings/boiled-eggs-price?price={test_price}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('price') == test_price:
                    self.log_result("Boiled Eggs Price Update", True, f"Successfully updated to €{test_price}")
                else:
                    self.log_result("Boiled Eggs Price Update", False, f"Update response incorrect: {data}")
            else:
                self.log_result("Boiled Eggs Price Update", False, f"Update failed: {response.status_code}")
        except Exception as e:
            self.log_result("Boiled Eggs Price Update", False, f"Update request failed: {str(e)}")
        
        # Restore original price
        try:
            requests.put(f"{BACKEND_URL}/lunch-settings/boiled-eggs-price?price={current_price}", timeout=10)
            print(f"   🔄 Restored original price: €{current_price}")
        except:
            print(f"   ⚠️ Could not restore original price")
    
    def test_department_authentication(self):
        """Test that department authentication still works"""
        print("\n🔐 TESTING DEPARTMENT AUTHENTICATION")
        
        # Try multiple department credentials
        test_credentials = [
            {"department_name": "2. Wachabteilung", "password": "password2"},
            {"department_name": "3. Wachabteilung", "password": "password3"},
            {"department_name": "4. Wachabteilung", "password": "password4"},
            {"department_name": "1. Wachabteilung", "password": "newTestPassword123"}  # Updated password
        ]
        
        for login_data in test_credentials:
            try:
                response = requests.post(f"{BACKEND_URL}/login/department", 
                                       json=login_data, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'department_id' in data and 'department_name' in data:
                        self.log_result("Department Authentication", True, f"Login successful for {data['department_name']}")
                        return data['department_id']
                    else:
                        print(f"   ⚠️ Login response missing fields for {login_data['department_name']}: {data}")
                else:
                    print(f"   ⚠️ Login failed for {login_data['department_name']}: {response.status_code}")
            except Exception as e:
                print(f"   ⚠️ Login request failed for {login_data['department_name']}: {str(e)}")
        
        self.log_result("Department Authentication", False, "All department login attempts failed")
        return None
    
    def test_order_creation(self, department_id):
        """Test that order creation still works"""
        print("\n📝 TESTING ORDER CREATION FUNCTIONALITY")
        
        if not department_id:
            self.log_result("Order Creation", False, "No department_id available for testing")
            return
        
        # First, get or create a test employee
        employee_id = self.get_or_create_test_employee(department_id)
        if not employee_id:
            self.log_result("Order Creation", False, "Could not get test employee")
            return
        
        # Create a simple breakfast order
        order_data = {
            "employee_id": employee_id,
            "department_id": department_id,
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 2,
                "white_halves": 1,
                "seeded_halves": 1,
                "toppings": ["ruehrei", "kaese"],
                "has_lunch": False,
                "boiled_eggs": 1,
                "has_coffee": False
            }],
            "drink_items": {},
            "sweet_items": {}
        }
        
        try:
            response = requests.post(f"{BACKEND_URL}/orders", 
                                   json=order_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'id' in data and 'total_price' in data:
                    self.log_result("Order Creation", True, f"Order created successfully, total: €{data['total_price']}")
                    return data['id']
                else:
                    self.log_result("Order Creation", False, f"Order response missing fields: {data}")
            elif response.status_code == 400:
                # Check if it's the single breakfast constraint
                error_detail = response.json().get('detail', '')
                if "bereits eine Frühstücksbestellung" in error_detail:
                    self.log_result("Order Creation", True, "Order creation working (single breakfast constraint active)")
                else:
                    self.log_result("Order Creation", False, f"Order creation failed with validation error: {error_detail}")
            else:
                self.log_result("Order Creation", False, f"Order creation failed: {response.status_code}")
        except Exception as e:
            self.log_result("Order Creation", False, f"Order request failed: {str(e)}")
        
        return None
    
    def get_or_create_test_employee(self, department_id):
        """Get existing test employee or create one"""
        try:
            # Try to get existing employees
            response = requests.get(f"{BACKEND_URL}/departments/{department_id}/employees", timeout=10)
            if response.status_code == 200:
                employees = response.json()
                if employees:
                    # Use first employee
                    employee_id = employees[0]['id']
                    print(f"   👤 Using existing employee: {employees[0]['name']} (ID: {employee_id})")
                    return employee_id
            
            # Create test employee if none exist
            employee_data = {
                "name": "Security Test Employee",
                "department_id": department_id
            }
            
            response = requests.post(f"{BACKEND_URL}/employees", 
                                   json=employee_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                employee_id = data['id']
                print(f"   👤 Created test employee: {data['name']} (ID: {employee_id})")
                return employee_id
        except Exception as e:
            print(f"   ⚠️ Error managing test employee: {str(e)}")
        
        return None
    
    def test_employee_orders_endpoint(self):
        """Test the employee orders endpoint (History Button Fix)"""
        print("\n📋 TESTING EMPLOYEE ORDERS ENDPOINT (History Button Fix)")
        
        # Get a department first
        department_id = self.test_department_authentication()
        if not department_id:
            self.log_result("Employee Orders Endpoint", False, "Could not authenticate to get department")
            return
        
        # Get an employee
        employee_id = self.get_or_create_test_employee(department_id)
        if not employee_id:
            self.log_result("Employee Orders Endpoint", False, "Could not get test employee")
            return
        
        # Test the endpoint
        try:
            response = requests.get(f"{BACKEND_URL}/employees/{employee_id}/orders", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'orders' in data and isinstance(data['orders'], list):
                    self.log_result("Employee Orders Endpoint", True, f"Endpoint working, found {len(data['orders'])} orders")
                else:
                    self.log_result("Employee Orders Endpoint", False, f"Response format incorrect: {data}")
            else:
                self.log_result("Employee Orders Endpoint", False, f"Endpoint failed: {response.status_code}")
        except Exception as e:
            self.log_result("Employee Orders Endpoint", False, f"Request failed: {str(e)}")
    
    def run_all_tests(self):
        """Run all security and functionality tests"""
        print("🔒 SICHERHEITSTEST - Kritische Überprüfung")
        print("=" * 60)
        print(f"Testing backend at: {BACKEND_URL}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run all tests
        self.test_dangerous_apis_blocked()
        self.test_boiled_eggs_price_stability()
        self.test_boiled_eggs_price_update()
        department_id = self.test_department_authentication()
        self.test_order_creation(department_id)
        self.test_employee_orders_endpoint()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if r.startswith("✅")])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if self.critical_failures:
            print(f"\n🚨 CRITICAL FAILURES ({len(self.critical_failures)}):")
            for failure in self.critical_failures:
                print(f"   {failure}")
        else:
            print("\n✅ NO CRITICAL FAILURES DETECTED")
        
        print("\n📋 DETAILED RESULTS:")
        for result in self.results:
            print(f"   {result}")
        
        return len(self.critical_failures) == 0

if __name__ == "__main__":
    tester = SecurityTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 ALL SECURITY TESTS PASSED!")
        sys.exit(0)
    else:
        print("\n❌ SECURITY TESTS FAILED!")
        sys.exit(1)