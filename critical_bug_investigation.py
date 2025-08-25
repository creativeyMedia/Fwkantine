#!/usr/bin/env python3
"""
CRITICAL BACKEND BUG INVESTIGATION: HTTP 422 Unprocessable Content errors on order creation API

LIVE SYSTEM: https://fw-kantine.de
CRITICAL ERRORS FROM BROWSER CONSOLE:
- POST /api/login/department: 401 (Unauthorized)
- POST https://fw-kantine.de/api/orders: 422 (Unprocessable Content) - REPEATED FAILURES
- "Fehler beim Prüfen bestehender Bestellungen" - repeated errors
- "Fehler beim Speichern der Bestellung" - repeated errors

ROOT CAUSE ANALYSIS NEEDED:
HTTP 422 means the request data is malformed or validation is failing. This indicates:

1. **Request Validation Issues:**
   - Frontend sending malformed order data
   - Backend validation rejecting valid requests
   - Menu item IDs mismatch between frontend/backend

2. **Authentication Issues:**
   - HTTP 401 on department login suggests auth pipeline broken
   - Without proper auth, orders fail validation

3. **Data Format Problems:**
   - Order structure mismatch after database recreation
   - Department ID inconsistencies
   - Employee ID validation failures

URGENT INVESTIGATION:
1. Test /api/login/department with exact credentials from browser
2. Test /api/orders endpoint with sample breakfast order data
3. Check FastAPI validation errors in backend logs
4. Verify request/response data structures match backend expectations
5. Test menu item retrieval and validate IDs exist in database
6. Check department authentication flow completely

EXPECTED FINDINGS: Backend validation is rejecting frontend requests due to data format mismatches or missing required fields after database recreation.

This is a production-blocking bug affecting all order functionality, not just breakfast orders.
"""

import requests
import json
import sys
from datetime import datetime
import traceback

# Configuration - LIVE SYSTEM
BASE_URL = "https://fw-kantine.de/api"

class CriticalBugInvestigator:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.test_results = []
        self.department_id = None
        self.employee_id = None
        self.menu_data = {}
        
    def log_result(self, test_name, success, details="", error="", http_status=None):
        """Log test result with detailed information"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "http_status": http_status,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if http_status:
            print(f"   HTTP Status: {http_status}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def test_department_authentication_comprehensive(self):
        """Test department authentication with various credential combinations"""
        print("🔍 TESTING DEPARTMENT AUTHENTICATION WITH VARIOUS CREDENTIALS")
        
        # Test common department names and passwords
        test_credentials = [
            ("1. Wachabteilung", "password1"),
            ("2. Wachabteilung", "password2"), 
            ("3. Wachabteilung", "password3"),
            ("4. Wachabteilung", "password4"),
            ("1. Schichtabteilung", "password1"),
            ("2. Schichtabteilung", "password2"),
            ("3. Schichtabteilung", "password3"),
            ("4. Schichtabteilung", "password4"),
            ("fw4abteilung1", "password1"),
            ("fw4abteilung2", "password2"),
            ("fw4abteilung3", "password3"),
            ("fw4abteilung4", "password4"),
        ]
        
        successful_auth = False
        
        for dept_name, password in test_credentials:
            try:
                response = self.session.post(f"{BASE_URL}/login/department", json={
                    "department_name": dept_name,
                    "password": password
                })
                
                if response.status_code == 200:
                    data = response.json()
                    self.department_id = data.get("department_id")
                    
                    self.log_result(
                        f"Department Authentication: {dept_name}",
                        True,
                        f"Successfully authenticated with department_id: {self.department_id}",
                        http_status=response.status_code
                    )
                    successful_auth = True
                    break
                elif response.status_code == 401:
                    self.log_result(
                        f"Department Authentication: {dept_name}",
                        False,
                        error=f"401 Unauthorized - Invalid credentials",
                        http_status=response.status_code
                    )
                else:
                    self.log_result(
                        f"Department Authentication: {dept_name}",
                        False,
                        error=f"Unexpected status: {response.text}",
                        http_status=response.status_code
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Department Authentication: {dept_name}",
                    False,
                    error=f"Exception: {str(e)}"
                )
        
        if not successful_auth:
            self.log_result(
                "Overall Department Authentication",
                False,
                error="❌ CRITICAL: No valid department credentials found! This explains the 401 errors."
            )
            return False
        
        return True
    
    def test_departments_list(self):
        """Test departments endpoint to see what departments exist"""
        try:
            response = self.session.get(f"{BASE_URL}/departments")
            
            if response.status_code == 200:
                departments = response.json()
                dept_names = [dept.get('name', 'Unknown') for dept in departments]
                dept_ids = [dept.get('id', 'Unknown') for dept in departments]
                
                self.log_result(
                    "Departments List",
                    True,
                    f"Found {len(departments)} departments: {dept_names} with IDs: {dept_ids}",
                    http_status=response.status_code
                )
                return True
            else:
                self.log_result(
                    "Departments List",
                    False,
                    error=f"Failed to get departments list: {response.text}",
                    http_status=response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("Departments List", False, error=f"Exception: {str(e)}")
            return False
    
    def test_menu_items_comprehensive(self):
        """Test all menu endpoints to verify data exists"""
        if not self.department_id:
            self.log_result(
                "Menu Items Test",
                False,
                error="No department_id available - cannot test menu items"
            )
            return False
        
        menu_endpoints = [
            ("breakfast", f"/menu/breakfast/{self.department_id}"),
            ("toppings", f"/menu/toppings/{self.department_id}"),
            ("drinks", f"/menu/drinks/{self.department_id}"),
            ("sweets", f"/menu/sweets/{self.department_id}")
        ]
        
        all_success = True
        
        for menu_type, endpoint in menu_endpoints:
            try:
                response = self.session.get(f"{BASE_URL}{endpoint}")
                
                if response.status_code == 200:
                    items = response.json()
                    self.menu_data[menu_type] = items
                    
                    if items:
                        item_details = []
                        for item in items[:3]:  # Show first 3 items
                            name = item.get('name', item.get('roll_type', item.get('topping_type', 'Unknown')))
                            price = item.get('price', 0)
                            item_id = item.get('id', 'No ID')
                            item_details.append(f"{name} (€{price}, ID: {item_id[:8]}...)")
                        
                        self.log_result(
                            f"Menu Items - {menu_type.title()}",
                            True,
                            f"Found {len(items)} items: {', '.join(item_details)}",
                            http_status=response.status_code
                        )
                    else:
                        self.log_result(
                            f"Menu Items - {menu_type.title()}",
                            False,
                            error=f"No {menu_type} items found - this will cause order validation failures!",
                            http_status=response.status_code
                        )
                        all_success = False
                else:
                    self.log_result(
                        f"Menu Items - {menu_type.title()}",
                        False,
                        error=f"Failed to get {menu_type} menu: {response.text}",
                        http_status=response.status_code
                    )
                    all_success = False
                    
            except Exception as e:
                self.log_result(f"Menu Items - {menu_type.title()}", False, error=f"Exception: {str(e)}")
                all_success = False
        
        return all_success
    
    def create_test_employee(self):
        """Create a test employee for order testing"""
        if not self.department_id:
            self.log_result(
                "Test Employee Creation",
                False,
                error="No department_id available"
            )
            return False
        
        try:
            employee_data = {
                "name": "Test Employee for Bug Investigation",
                "department_id": self.department_id
            }
            
            response = self.session.post(f"{BASE_URL}/employees", json=employee_data)
            
            if response.status_code == 200:
                employee = response.json()
                self.employee_id = employee.get("id")
                
                self.log_result(
                    "Test Employee Creation",
                    True,
                    f"Created test employee with ID: {self.employee_id}",
                    http_status=response.status_code
                )
                return True
            else:
                self.log_result(
                    "Test Employee Creation",
                    False,
                    error=f"Failed to create employee: {response.text}",
                    http_status=response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("Test Employee Creation", False, error=f"Exception: {str(e)}")
            return False
    
    def test_order_creation_with_validation_details(self):
        """Test order creation with detailed validation error analysis"""
        if not self.department_id or not self.employee_id:
            self.log_result(
                "Order Creation Test",
                False,
                error="Missing department_id or employee_id"
            )
            return False
        
        # Get available toppings for validation
        toppings = self.menu_data.get('toppings', [])
        if not toppings:
            self.log_result(
                "Order Creation Test",
                False,
                error="No toppings available - cannot create valid order"
            )
            return False
        
        # Use actual topping types from the menu
        available_toppings = []
        for topping in toppings:
            topping_type = topping.get('topping_type')
            if topping_type:
                available_toppings.append(topping_type)
        
        if not available_toppings:
            self.log_result(
                "Order Creation Test",
                False,
                error="No valid topping_type values found in menu"
            )
            return False
        
        # Test different order structures to identify validation issues
        test_orders = [
            {
                "name": "Basic Breakfast Order",
                "data": {
                    "employee_id": self.employee_id,
                    "department_id": self.department_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": available_toppings[:2],  # Use first 2 available toppings
                        "has_lunch": False,
                        "boiled_eggs": 0,
                        "has_coffee": False
                    }]
                }
            },
            {
                "name": "Minimal Breakfast Order",
                "data": {
                    "employee_id": self.employee_id,
                    "department_id": self.department_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 1,
                        "white_halves": 1,
                        "seeded_halves": 0,
                        "toppings": [available_toppings[0]],  # Use first available topping
                        "has_lunch": False,
                        "boiled_eggs": 0,
                        "has_coffee": False
                    }]
                }
            },
            {
                "name": "Order with Lunch",
                "data": {
                    "employee_id": self.employee_id,
                    "department_id": self.department_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 2,
                        "white_halves": 2,
                        "seeded_halves": 0,
                        "toppings": available_toppings[:2],
                        "has_lunch": True,
                        "boiled_eggs": 0,
                        "has_coffee": False
                    }]
                }
            }
        ]
        
        success_count = 0
        
        for test_order in test_orders:
            try:
                print(f"Testing: {test_order['name']}")
                print(f"Order data: {json.dumps(test_order['data'], indent=2)}")
                
                response = self.session.post(f"{BASE_URL}/orders", json=test_order['data'])
                
                if response.status_code == 200:
                    order_result = response.json()
                    self.log_result(
                        f"Order Creation - {test_order['name']}",
                        True,
                        f"✅ SUCCESS! Order created with total: €{order_result.get('total_price', 'N/A')}",
                        http_status=response.status_code
                    )
                    success_count += 1
                elif response.status_code == 422:
                    # Parse validation error details
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', 'No detail provided')
                        
                        self.log_result(
                            f"Order Creation - {test_order['name']}",
                            False,
                            error=f"🚨 HTTP 422 VALIDATION ERROR: {detail}",
                            http_status=response.status_code
                        )
                        
                        # Print detailed validation error for analysis
                        print(f"   Detailed validation error: {json.dumps(error_data, indent=2)}")
                        
                    except:
                        self.log_result(
                            f"Order Creation - {test_order['name']}",
                            False,
                            error=f"🚨 HTTP 422 VALIDATION ERROR: {response.text}",
                            http_status=response.status_code
                        )
                else:
                    self.log_result(
                        f"Order Creation - {test_order['name']}",
                        False,
                        error=f"Unexpected status: {response.text}",
                        http_status=response.status_code
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Order Creation - {test_order['name']}",
                    False,
                    error=f"Exception: {str(e)}"
                )
        
        return success_count > 0
    
    def test_existing_orders_check(self):
        """Test the existing orders check that might be causing issues"""
        if not self.department_id or not self.employee_id:
            self.log_result(
                "Existing Orders Check",
                False,
                error="Missing department_id or employee_id"
            )
            return False
        
        try:
            # Test daily summary endpoint
            response = self.session.get(f"{BASE_URL}/orders/daily-summary/{self.department_id}")
            
            if response.status_code == 200:
                summary = response.json()
                employee_orders = summary.get('employee_orders', {})
                breakfast_summary = summary.get('breakfast_summary', {})
                
                self.log_result(
                    "Daily Summary Check",
                    True,
                    f"Daily summary retrieved. Employee orders: {len(employee_orders)}, Breakfast items: {len(breakfast_summary)}",
                    http_status=response.status_code
                )
                
                # Check if there are existing orders that might block new ones
                if employee_orders:
                    print(f"   Found existing employee orders: {list(employee_orders.keys())}")
                
                return True
            else:
                self.log_result(
                    "Daily Summary Check",
                    False,
                    error=f"Failed to get daily summary: {response.text}",
                    http_status=response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("Daily Summary Check", False, error=f"Exception: {str(e)}")
            return False
    
    def test_lunch_settings(self):
        """Test lunch settings that might affect order validation"""
        try:
            response = self.session.get(f"{BASE_URL}/lunch-settings")
            
            if response.status_code == 200:
                settings = response.json()
                self.log_result(
                    "Lunch Settings Check",
                    True,
                    f"Lunch settings: Price €{settings.get('price', 0)}, Enabled: {settings.get('enabled', False)}, Boiled eggs: €{settings.get('boiled_eggs_price', 0)}",
                    http_status=response.status_code
                )
                return True
            else:
                self.log_result(
                    "Lunch Settings Check",
                    False,
                    error=f"Failed to get lunch settings: {response.text}",
                    http_status=response.status_code
                )
                return False
                
        except Exception as e:
            self.log_result("Lunch Settings Check", False, error=f"Exception: {str(e)}")
            return False
    
    def run_critical_investigation(self):
        """Run the complete critical bug investigation"""
        print("🚨 CRITICAL BACKEND BUG INVESTIGATION")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Focus: HTTP 422 Unprocessable Content and 401 Unauthorized errors")
        print("=" * 80)
        print()
        
        # Step 1: Test departments list
        print("🔍 STEP 1: Check Available Departments")
        self.test_departments_list()
        
        # Step 2: Test authentication comprehensively
        print("🔍 STEP 2: Test Department Authentication")
        auth_success = self.test_department_authentication_comprehensive()
        
        if not auth_success:
            print("❌ CRITICAL: Authentication failed - cannot proceed with order testing")
            self.print_investigation_summary()
            return False
        
        # Step 3: Test menu items
        print("🔍 STEP 3: Test Menu Items")
        menu_success = self.test_menu_items_comprehensive()
        
        # Step 4: Create test employee
        print("🔍 STEP 4: Create Test Employee")
        employee_success = self.create_test_employee()
        
        # Step 5: Test lunch settings
        print("🔍 STEP 5: Test Lunch Settings")
        self.test_lunch_settings()
        
        # Step 6: Test existing orders check
        print("🔍 STEP 6: Test Existing Orders Check")
        self.test_existing_orders_check()
        
        # Step 7: Test order creation with detailed validation
        print("🔍 STEP 7: Test Order Creation with Validation Analysis")
        if employee_success and menu_success:
            order_success = self.test_order_creation_with_validation_details()
        else:
            print("❌ Skipping order creation tests due to missing prerequisites")
            order_success = False
        
        # Summary
        self.print_investigation_summary()
        
        return auth_success and menu_success and employee_success and order_success
    
    def print_investigation_summary(self):
        """Print investigation summary with root cause analysis"""
        print("\n" + "=" * 80)
        print("🔍 CRITICAL BUG INVESTIGATION SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        print()
        
        # Show failed tests with HTTP status codes
        failed_tests = [r for r in self.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                status_info = f" (HTTP {test['http_status']})" if test['http_status'] else ""
                print(f"   • {test['test']}{status_info}: {test['error']}")
            print()
        
        # ROOT CAUSE ANALYSIS
        print("🔍 ROOT CAUSE ANALYSIS:")
        
        # Check for 401 authentication issues
        auth_failures = [r for r in self.test_results if r.get('http_status') == 401]
        if auth_failures:
            print("   🚨 HTTP 401 UNAUTHORIZED ERRORS CONFIRMED:")
            for failure in auth_failures:
                print(f"   • {failure['test']}: Authentication failed")
            print("   → ROOT CAUSE: Invalid department credentials or department doesn't exist")
            print()
        
        # Check for 422 validation issues
        validation_failures = [r for r in self.test_results if r.get('http_status') == 422]
        if validation_failures:
            print("   🚨 HTTP 422 VALIDATION ERRORS CONFIRMED:")
            for failure in validation_failures:
                print(f"   • {failure['test']}: {failure['error']}")
            print("   → ROOT CAUSE: Request data format doesn't match backend validation requirements")
            print()
        
        # Check for missing menu items
        menu_failures = [r for r in self.test_results if "Menu Items" in r["test"] and "❌ FAIL" in r["status"]]
        if menu_failures:
            print("   🚨 MISSING MENU ITEMS:")
            for failure in menu_failures:
                print(f"   • {failure['error']}")
            print("   → ROOT CAUSE: Database recreation didn't properly restore menu items")
            print()
        
        # Recommendations
        print("🔧 IMMEDIATE FIXES NEEDED:")
        if auth_failures:
            print("   1. ❗ CRITICAL: Fix department authentication")
            print("      - Verify department names and passwords in database")
            print("      - Check if departments were properly recreated after cleanup")
        
        if validation_failures:
            print("   2. ❗ CRITICAL: Fix order validation")
            print("      - Check FastAPI validation schemas match frontend data structure")
            print("      - Verify menu item IDs are valid and exist in database")
            print("      - Check topping_type enum values match available toppings")
        
        if menu_failures:
            print("   3. ❗ CRITICAL: Restore missing menu items")
            print("      - Run database initialization to recreate menu items")
            print("      - Verify department-specific menu items exist")
        
        if not failed_tests:
            print("   ✅ All tests passed - backend is working correctly")
            print("   → Issue may be frontend-specific or browser-related")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    investigator = CriticalBugInvestigator()
    
    try:
        success = investigator.run_critical_investigation()
        
        # Exit with appropriate code
        if success:
            print("✅ Investigation completed successfully")
            sys.exit(0)
        else:
            print("❌ Investigation found critical issues")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Investigation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()