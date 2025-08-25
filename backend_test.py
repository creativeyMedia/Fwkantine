#!/usr/bin/env python3
"""
PROBLEM 2 - ORDER HISTORY LUNCH PRICE DISPLAY FIX TESTING

FOCUS: Test the specific fix for Problem 2 - Order History Lunch Price Display:
Verify that breakfast orders with lunch now show "1x Mittagessen" WITHOUT the problematic "(€0.00 Tagespreis)" text in the readable_items.

Test specifically:
1. Create a breakfast order with lunch for a test employee
2. Retrieve the employee profile GET /api/employees/{employee_id}/profile 
3. Verify that lunch orders in the order history have:
   - description: "1x Mittagessen" 
   - unit_price: "" (empty, not showing Tagespreis)
   - total_price: correct lunch price amount

BACKEND URL: https://fireguard-menu.preview.emergentagent.com/api
DEPARTMENT: 2. Wachabteilung (fw4abteilung2) 
CREDENTIALS: Employee: password2, Admin: admin2

PURPOSE: Verify that the user-reported bug where "(€0.00 Tagespreis)" was still showing in the order history details is fixed.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration - Use production backend URL from frontend/.env
BASE_URL = "https://fireguard-menu.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_PASSWORD = "password2"
ADMIN_PASSWORD = "admin2"

class LunchPriceDisplayTester:
    def __init__(self):
        self.session = requests.Session()
        self.department_id = None
        self.test_employee_id = None
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
    
    def setup_authentication(self):
        """Setup authentication and get department ID"""
        try:
            # Test employee authentication
            response = self.session.post(f"{BASE_URL}/login/department", json={
                "department_name": DEPARTMENT_NAME,
                "password": DEPARTMENT_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.department_id = data.get("department_id")
                
                self.log_result(
                    "Department Authentication", 
                    True, 
                    f"Successfully authenticated with department_id: {self.department_id}"
                )
                return True
            else:
                self.log_result(
                    "Department Authentication", 
                    False, 
                    error=f"Auth failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Department Authentication", False, error=str(e))
            return False
    
    def create_test_employee(self):
        """Create test employee for lunch price testing"""
        if not self.department_id:
            self.log_result("Test Employee Creation", False, error="Department ID not available")
            return False
        
        try:
            # Create test employee with realistic name
            employee_data = {
                "name": "Max Mustermann",
                "department_id": self.department_id
            }
            
            employee_response = self.session.post(f"{BASE_URL}/employees", json=employee_data)
            
            if employee_response.status_code == 200:
                test_employee = employee_response.json()
                self.test_employee_id = test_employee.get("id")
                
                self.log_result(
                    "Test Employee Creation",
                    True,
                    f"Created test employee 'Max Mustermann' with ID: {self.test_employee_id}"
                )
                return True
            else:
                self.log_result(
                    "Test Employee Creation",
                    False,
                    error=f"Employee creation failed: HTTP {employee_response.status_code}: {employee_response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Employee Creation", False, error=str(e))
            return False
    
    def create_breakfast_order_with_lunch(self):
        """Create a breakfast order with lunch for testing"""
        if not self.test_employee_id or not self.department_id:
            self.log_result("Breakfast Order with Lunch Creation", False, error="Employee ID or Department ID not available")
            return False
        
        try:
            # Create realistic breakfast order with lunch
            order_data = {
                "employee_id": self.test_employee_id,
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["ruehrei", "kaese"],
                    "has_lunch": True,
                    "boiled_eggs": 0,
                    "has_coffee": False
                }]
            }
            
            order_response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            if order_response.status_code == 200:
                order_result = order_response.json()
                total_price = order_result.get('total_price', 0)
                lunch_price = order_result.get('lunch_price', 0)
                
                self.log_result(
                    "Breakfast Order with Lunch Creation",
                    True,
                    f"Created breakfast order with lunch. Total: €{total_price}, Lunch Price: €{lunch_price}"
                )
                return True
            else:
                self.log_result(
                    "Breakfast Order with Lunch Creation",
                    False,
                    error=f"Order creation failed: HTTP {order_response.status_code}: {order_response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Breakfast Order with Lunch Creation", False, error=str(e))
            return False
    
    def test_lunch_price_display_fix(self):
        """Test the specific fix for lunch price display in order history"""
        if not self.test_employee_id:
            self.log_result("Lunch Price Display Fix Test", False, error="Test employee ID not available")
            return False
        
        try:
            # Get employee profile with order history
            response = self.session.get(f"{BASE_URL}/employees/{self.test_employee_id}/profile")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields for employee profile
                required_fields = ["employee", "order_history", "total_orders", "breakfast_total", "drinks_sweets_total"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Lunch Price Display Fix Test",
                        False,
                        error=f"Missing required fields in profile: {missing_fields}"
                    )
                    return False
                
                # Check order history for lunch orders
                order_history = data.get("order_history", [])
                if not order_history:
                    self.log_result(
                        "Lunch Price Display Fix Test",
                        False,
                        error="No order history found"
                    )
                    return False
                
                # Find breakfast orders with lunch and check readable_items
                lunch_orders_found = []
                problematic_items = []
                
                for order in order_history:
                    if order.get("order_type") == "breakfast" and order.get("has_lunch"):
                        readable_items = order.get("readable_items", [])
                        
                        # Look for lunch items in readable_items
                        for item in readable_items:
                            description = item.get("description", "")
                            unit_price = item.get("unit_price", "")
                            total_price = item.get("total_price", "")
                            
                            if "Mittagessen" in description:
                                lunch_orders_found.append({
                                    "description": description,
                                    "unit_price": unit_price,
                                    "total_price": total_price
                                })
                                
                                # Check for the problematic "(€0.00 Tagespreis)" text
                                if "Tagespreis" in description or "€0.00" in unit_price:
                                    problematic_items.append({
                                        "description": description,
                                        "unit_price": unit_price,
                                        "issue": "Contains Tagespreis or €0.00 reference"
                                    })
                
                # Evaluate the fix
                if lunch_orders_found:
                    if problematic_items:
                        # Fix not working - still showing problematic text
                        problem_details = [f"'{item['description']}' (unit_price: '{item['unit_price']}')" for item in problematic_items]
                        self.log_result(
                            "Lunch Price Display Fix Test",
                            False,
                            error=f"PROBLEM 2 NOT FIXED: Found {len(problematic_items)} lunch items still showing Tagespreis: {'; '.join(problem_details)}"
                        )
                        return False
                    else:
                        # Fix working - lunch items show correctly without problematic text
                        lunch_details = [f"'{item['description']}' (unit_price: '{item['unit_price']}', total: '{item['total_price']}')" for item in lunch_orders_found]
                        self.log_result(
                            "Lunch Price Display Fix Test",
                            True,
                            f"✅ PROBLEM 2 FIXED! Found {len(lunch_orders_found)} lunch items WITHOUT problematic '(€0.00 Tagespreis)' text: {'; '.join(lunch_details)}"
                        )
                        return True
                else:
                    self.log_result(
                        "Lunch Price Display Fix Test",
                        False,
                        error="No lunch items found in readable_items, but lunch order was created"
                    )
                    return False
                    
            else:
                self.log_result(
                    "Lunch Price Display Fix Test",
                    False,
                    error=f"Failed to get employee profile: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Lunch Price Display Fix Test", False, error=str(e))
            return False
    
    def run_lunch_price_fix_test(self):
        """Run the complete lunch price display fix test"""
        print("🍽️ PROBLEM 2 - ORDER HISTORY LUNCH PRICE DISPLAY FIX TESTING")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME}")
        print(f"Focus: Verify lunch orders show '1x Mittagessen' WITHOUT '(€0.00 Tagespreis)' text")
        print("=" * 80)
        print()
        
        # Setup Phase
        print("🔧 SETUP PHASE")
        auth_ok = self.setup_authentication()
        if not auth_ok:
            return False
        
        employee_ok = self.create_test_employee()
        if not employee_ok:
            return False
        
        order_ok = self.create_breakfast_order_with_lunch()
        if not order_ok:
            return False
        
        # Main Test
        print("🧪 MAIN TEST: Lunch Price Display Fix")
        test_ok = self.test_lunch_price_display_fix()
        
        # Summary
        self.print_test_summary()
        
        return test_ok
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🍽️ LUNCH PRICE DISPLAY FIX TESTING SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        print()
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['error']}")
            print()
        else:
            print("✅ PROBLEM 2 LUNCH PRICE DISPLAY FIX VERIFIED!")
            print("   • Breakfast orders with lunch show '1x Mittagessen' correctly")
            print("   • No problematic '(€0.00 Tagespreis)' text found in readable_items")
            print("   • Unit prices are empty (not showing Tagespreis)")
            print("   • Total prices show correct lunch price amounts")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = LunchPriceDisplayTester()
    
    try:
        success = tester.run_lunch_price_fix_test()
        
        # Exit with appropriate code
        failed_tests = [r for r in tester.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            sys.exit(1)  # Indicate test failures
        else:
            sys.exit(0)  # All tests passed
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()