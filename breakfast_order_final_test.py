#!/usr/bin/env python3
"""
FINAL BREAKFAST ORDER TEST: Verify the critical HTTP 422 errors are resolved

This test focuses specifically on the breakfast ordering functionality that was failing
with HTTP 422 errors as reported in the review request.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "https://fw-kantine.de/api"

class BreakfastOrderFinalTest:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.department_id = None
        self.employee_id = None
        self.test_results = []
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def test_department_login(self):
        """Test department login - addressing HTTP 401 errors"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department", json={
                "department_name": "1. Wachabteilung",
                "password": "password1"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.department_id = data.get("department_id")
                
                self.log_result(
                    "Department Login (HTTP 401 Fix)",
                    True,
                    f"✅ FIXED! Department login successful with department_id: {self.department_id}"
                )
                return True
            else:
                self.log_result(
                    "Department Login (HTTP 401 Fix)",
                    False,
                    error=f"Login failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Department Login (HTTP 401 Fix)", False, error=str(e))
            return False
    
    def test_existing_orders_check(self):
        """Test existing orders check - addressing 'Fehler beim Prüfen bestehender Bestellungen'"""
        if not self.department_id:
            self.log_result(
                "Existing Orders Check",
                False,
                error="No department_id available"
            )
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/orders/daily-summary/{self.department_id}")
            
            if response.status_code == 200:
                summary = response.json()
                employee_orders = summary.get('employee_orders', {})
                
                self.log_result(
                    "Existing Orders Check (Error Fix)",
                    True,
                    f"✅ FIXED! 'Fehler beim Prüfen bestehender Bestellungen' resolved. Found {len(employee_orders)} existing orders."
                )
                return True
            else:
                self.log_result(
                    "Existing Orders Check (Error Fix)",
                    False,
                    error=f"Failed to check existing orders: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Existing Orders Check (Error Fix)", False, error=str(e))
            return False
    
    def create_test_employee(self):
        """Create test employee for order testing"""
        if not self.department_id:
            return False
        
        try:
            employee_data = {
                "name": "Final Test Employee",
                "department_id": self.department_id
            }
            
            response = self.session.post(f"{BASE_URL}/employees", json=employee_data)
            
            if response.status_code == 200:
                employee = response.json()
                self.employee_id = employee.get("id")
                
                self.log_result(
                    "Test Employee Creation",
                    True,
                    f"Created test employee with ID: {self.employee_id}"
                )
                return True
            else:
                self.log_result(
                    "Test Employee Creation",
                    False,
                    error=f"Failed to create employee: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Employee Creation", False, error=str(e))
            return False
    
    def test_breakfast_order_creation(self):
        """Test breakfast order creation - addressing HTTP 422 and 'Fehler beim Speichern der Bestellung'"""
        if not self.department_id or not self.employee_id:
            self.log_result(
                "Breakfast Order Creation",
                False,
                error="Missing department_id or employee_id"
            )
            return False
        
        # Test multiple breakfast order scenarios
        test_orders = [
            {
                "name": "Simple Breakfast Order",
                "data": {
                    "employee_id": self.employee_id,
                    "department_id": self.department_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 2,
                        "white_halves": 2,
                        "seeded_halves": 0,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": False,
                        "boiled_eggs": 0,
                        "has_coffee": False
                    }]
                }
            },
            {
                "name": "Breakfast with Lunch",
                "data": {
                    "employee_id": self.employee_id,
                    "department_id": self.department_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 1,
                        "white_halves": 0,
                        "seeded_halves": 1,
                        "toppings": ["butter"],
                        "has_lunch": True,
                        "boiled_eggs": 0,
                        "has_coffee": False
                    }]
                }
            },
            {
                "name": "Breakfast with Boiled Eggs",
                "data": {
                    "employee_id": self.employee_id,
                    "department_id": self.department_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 1,
                        "white_halves": 1,
                        "seeded_halves": 0,
                        "toppings": ["schinken"],
                        "has_lunch": False,
                        "boiled_eggs": 2,
                        "has_coffee": False
                    }]
                }
            }
        ]
        
        success_count = 0
        
        for test_order in test_orders:
            try:
                print(f"Testing: {test_order['name']}")
                
                response = self.session.post(f"{BASE_URL}/orders", json=test_order['data'])
                
                if response.status_code == 200:
                    order_result = response.json()
                    self.log_result(
                        f"Breakfast Order - {test_order['name']}",
                        True,
                        f"✅ FIXED! 'Fehler beim Speichern der Bestellung' resolved. Order created with total: €{order_result.get('total_price', 'N/A')}"
                    )
                    success_count += 1
                elif response.status_code == 422:
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', 'No detail provided')
                        
                        self.log_result(
                            f"Breakfast Order - {test_order['name']}",
                            False,
                            error=f"❌ HTTP 422 STILL OCCURRING: {detail}"
                        )
                    except:
                        self.log_result(
                            f"Breakfast Order - {test_order['name']}",
                            False,
                            error=f"❌ HTTP 422 STILL OCCURRING: {response.text}"
                        )
                elif response.status_code == 400:
                    # This might be expected for duplicate orders
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', 'No detail provided')
                        
                        if "bereits eine Frühstücksbestellung" in detail:
                            self.log_result(
                                f"Breakfast Order - {test_order['name']}",
                                True,
                                f"✅ EXPECTED: Single breakfast constraint working: {detail}"
                            )
                            success_count += 1
                        else:
                            self.log_result(
                                f"Breakfast Order - {test_order['name']}",
                                False,
                                error=f"HTTP 400: {detail}"
                            )
                    except:
                        self.log_result(
                            f"Breakfast Order - {test_order['name']}",
                            False,
                            error=f"HTTP 400: {response.text}"
                        )
                else:
                    self.log_result(
                        f"Breakfast Order - {test_order['name']}",
                        False,
                        error=f"Unexpected status: HTTP {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                self.log_result(
                    f"Breakfast Order - {test_order['name']}",
                    False,
                    error=f"Exception: {str(e)}"
                )
        
        return success_count > 0
    
    def test_menu_item_validation(self):
        """Test that menu items exist and are properly formatted"""
        if not self.department_id:
            return False
        
        try:
            # Test breakfast menu
            breakfast_response = self.session.get(f"{BASE_URL}/menu/breakfast/{self.department_id}")
            toppings_response = self.session.get(f"{BASE_URL}/menu/toppings/{self.department_id}")
            
            if breakfast_response.status_code == 200 and toppings_response.status_code == 200:
                breakfast_items = breakfast_response.json()
                toppings_items = toppings_response.json()
                
                # Verify menu items have required fields
                breakfast_valid = all('roll_type' in item and 'price' in item for item in breakfast_items)
                toppings_valid = all('topping_type' in item and 'price' in item for item in toppings_items)
                
                if breakfast_valid and toppings_valid and len(breakfast_items) > 0 and len(toppings_items) > 0:
                    self.log_result(
                        "Menu Item Validation",
                        True,
                        f"✅ FIXED! Menu items properly structured. Breakfast: {len(breakfast_items)} items, Toppings: {len(toppings_items)} items"
                    )
                    return True
                else:
                    self.log_result(
                        "Menu Item Validation",
                        False,
                        error=f"Menu items missing or invalid structure. Breakfast valid: {breakfast_valid}, Toppings valid: {toppings_valid}"
                    )
                    return False
            else:
                self.log_result(
                    "Menu Item Validation",
                    False,
                    error=f"Failed to get menu items. Breakfast: HTTP {breakfast_response.status_code}, Toppings: HTTP {toppings_response.status_code}"
                )
                return False
                
        except Exception as e:
            self.log_result("Menu Item Validation", False, error=str(e))
            return False
    
    def run_final_test(self):
        """Run the final comprehensive breakfast order test"""
        print("🎯 FINAL BREAKFAST ORDER TEST")
        print("=" * 80)
        print("Goal: Verify all critical HTTP 422 and 401 errors are resolved")
        print("Focus: Breakfast ordering functionality")
        print("=" * 80)
        
        # Test 1: Department login (HTTP 401 fix)
        print("\n🔍 TEST 1: Department Login (HTTP 401 Fix)")
        login_success = self.test_department_login()
        
        if not login_success:
            print("❌ Cannot proceed without successful login")
            return False
        
        # Test 2: Menu item validation
        print("\n🔍 TEST 2: Menu Item Validation")
        menu_success = self.test_menu_item_validation()
        
        # Test 3: Existing orders check
        print("\n🔍 TEST 3: Existing Orders Check")
        existing_orders_success = self.test_existing_orders_check()
        
        # Test 4: Create test employee
        print("\n🔍 TEST 4: Create Test Employee")
        employee_success = self.create_test_employee()
        
        # Test 5: Breakfast order creation (HTTP 422 fix)
        print("\n🔍 TEST 5: Breakfast Order Creation (HTTP 422 Fix)")
        if employee_success and menu_success:
            order_success = self.test_breakfast_order_creation()
        else:
            print("❌ Skipping order creation - prerequisites not met")
            order_success = False
        
        # Summary
        self.print_final_summary()
        
        return login_success and menu_success and existing_orders_success and employee_success and order_success
    
    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("🎯 FINAL BREAKFAST ORDER TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        print()
        
        # Show results for critical issues
        critical_fixes = [
            "Department Login (HTTP 401 Fix)",
            "Existing Orders Check (Error Fix)",
            "Menu Item Validation",
            "Breakfast Order"
        ]
        
        print("🔍 CRITICAL ISSUE RESOLUTION STATUS:")
        for fix in critical_fixes:
            matching_results = [r for r in self.test_results if fix in r["test"]]
            if matching_results:
                for result in matching_results:
                    status_icon = "✅" if "✅ PASS" in result["status"] else "❌"
                    print(f"   {status_icon} {result['test']}")
                    if result.get('details') and "FIXED" in result['details']:
                        print(f"      → {result['details']}")
        
        print()
        
        # Overall assessment
        if failed == 0:
            print("🎉 SUCCESS! All critical breakfast ordering issues have been resolved!")
            print("✅ HTTP 401 (Unauthorized) errors: FIXED")
            print("✅ HTTP 422 (Unprocessable Content) errors: FIXED")
            print("✅ 'Fehler beim Prüfen bestehender Bestellungen': FIXED")
            print("✅ 'Fehler beim Speichern der Bestellung': FIXED")
            print("\n🚀 The breakfast ordering system is now fully functional!")
        else:
            print("⚠️ Some issues remain:")
            failed_tests = [r for r in self.test_results if "❌ FAIL" in r["status"]]
            for test in failed_tests:
                print(f"   • {test['test']}: {test['error']}")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = BreakfastOrderFinalTest()
    
    try:
        success = tester.run_final_test()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()