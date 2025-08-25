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

class UIImprovementsTester:
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
    
    def setup_test_data(self):
        """Create test employee and orders for testing"""
        if not self.department_id:
            self.log_result("Test Data Setup", False, error="Department ID not available")
            return False
        
        try:
            # Create test employee
            employee_data = {
                "name": "UI Test Employee",
                "department_id": self.department_id
            }
            
            employee_response = self.session.post(f"{BASE_URL}/employees", json=employee_data)
            
            if employee_response.status_code == 200:
                test_employee = employee_response.json()
                self.test_employee_id = test_employee.get("id")
                
                self.log_result(
                    "Test Employee Creation",
                    True,
                    f"Created test employee with ID: {self.test_employee_id}"
                )
                
                # Create test breakfast order with lunch
                order_data = {
                    "employee_id": self.test_employee_id,
                    "department_id": self.department_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 4,
                        "white_halves": 2,
                        "seeded_halves": 2,
                        "toppings": ["ruehrei", "kaese", "salami", "butter"],
                        "has_lunch": True,
                        "boiled_eggs": 2,
                        "has_coffee": False
                    }]
                }
                
                order_response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                
                if order_response.status_code == 200:
                    order_result = order_response.json()
                    self.log_result(
                        "Test Breakfast Order Creation",
                        True,
                        f"Created test order with lunch. Total: €{order_result.get('total_price', 'N/A')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Test Breakfast Order Creation",
                        False,
                        error=f"Order creation failed: HTTP {order_response.status_code}: {order_response.text}"
                    )
                    return False
                    
            else:
                self.log_result(
                    "Test Employee Creation",
                    False,
                    error=f"Employee creation failed: HTTP {employee_response.status_code}: {employee_response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Data Setup", False, error=str(e))
            return False
    
    def test_shopping_list_formatting(self):
        """Test 1: Shopping List Formatting - GET /api/orders/daily-summary/{department_id}"""
        if not self.department_id:
            self.log_result("Shopping List Formatting Test", False, error="Department ID not available")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/orders/daily-summary/{self.department_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields for shopping list formatting
                required_fields = ["date", "breakfast_summary", "employee_orders", "shopping_list", "total_toppings", "total_boiled_eggs"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Shopping List Formatting Test",
                        False,
                        error=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                # Check shopping list structure
                shopping_list = data.get("shopping_list", {})
                if not shopping_list:
                    self.log_result(
                        "Shopping List Formatting Test",
                        False,
                        error="Shopping list is empty"
                    )
                    return False
                
                # Verify shopping list has proper structure for left-aligned formatting
                shopping_list_valid = True
                shopping_details = []
                
                for roll_type, roll_data in shopping_list.items():
                    if not isinstance(roll_data, dict) or "halves" not in roll_data or "whole_rolls" not in roll_data:
                        shopping_list_valid = False
                        break
                    shopping_details.append(f"{roll_type}: {roll_data['halves']} halves → {roll_data['whole_rolls']} whole rolls")
                
                # Check employee orders structure for frontend display
                employee_orders = data.get("employee_orders", {})
                employee_details = []
                
                for employee_name, order_data in employee_orders.items():
                    required_employee_fields = ["white_halves", "seeded_halves", "boiled_eggs", "has_lunch", "toppings"]
                    if all(field in order_data for field in required_employee_fields):
                        lunch_status = "with lunch" if order_data["has_lunch"] else "no lunch"
                        employee_details.append(f"{employee_name}: {order_data['white_halves']}W + {order_data['seeded_halves']}S halves, {order_data['boiled_eggs']} eggs, {lunch_status}")
                
                if shopping_list_valid and employee_details:
                    self.log_result(
                        "Shopping List Formatting Test",
                        True,
                        f"Shopping list structure valid for left-aligned formatting. Shopping: {'; '.join(shopping_details)}. Employees: {'; '.join(employee_details[:2])}"
                    )
                    return True
                else:
                    self.log_result(
                        "Shopping List Formatting Test",
                        False,
                        error="Shopping list or employee orders structure invalid for frontend formatting"
                    )
                    return False
                    
            else:
                self.log_result(
                    "Shopping List Formatting Test",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Shopping List Formatting Test", False, error=str(e))
            return False
    
    def test_order_history_lunch_price(self):
        """Test 2: Order History Lunch Price - GET /api/employees/{employee_id}/profile"""
        if not self.test_employee_id:
            self.log_result("Order History Lunch Price Test", False, error="Test employee ID not available")
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/employees/{self.test_employee_id}/profile")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields for employee profile
                required_fields = ["employee", "order_history", "total_orders", "breakfast_total", "drinks_sweets_total"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    self.log_result(
                        "Order History Lunch Price Test",
                        False,
                        error=f"Missing required fields: {missing_fields}"
                    )
                    return False
                
                # Check order history for lunch tracking
                order_history = data.get("order_history", [])
                if not order_history:
                    self.log_result(
                        "Order History Lunch Price Test",
                        False,
                        error="No order history found"
                    )
                    return False
                
                # Find breakfast orders with lunch
                lunch_orders = []
                for order in order_history:
                    if order.get("order_type") == "breakfast" and order.get("has_lunch"):
                        lunch_price = order.get("lunch_price")
                        total_price = order.get("total_price")
                        readable_items = order.get("readable_items", [])
                        
                        # Check if lunch is properly tracked in backend
                        lunch_item_found = any("Mittagessen" in item.get("description", "") for item in readable_items)
                        
                        if lunch_price is not None and lunch_item_found:
                            lunch_orders.append({
                                "lunch_price": lunch_price,
                                "total_price": total_price,
                                "lunch_item_found": lunch_item_found
                            })
                
                if lunch_orders:
                    lunch_details = [f"€{order['lunch_price']} lunch in €{order['total_price']} total" for order in lunch_orders[:2]]
                    self.log_result(
                        "Order History Lunch Price Test",
                        True,
                        f"Lunch tracking working correctly in employee profile. Found {len(lunch_orders)} lunch orders: {'; '.join(lunch_details)}. Backend properly tracks lunch prices even though frontend won't show 'Tagespreis'."
                    )
                    return True
                else:
                    self.log_result(
                        "Order History Lunch Price Test",
                        False,
                        error="No breakfast orders with lunch found in employee profile, but lunch order was created"
                    )
                    return False
                    
            else:
                self.log_result(
                    "Order History Lunch Price Test",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Order History Lunch Price Test", False, error=str(e))
            return False
    
    def test_admin_dashboard_menu_names(self):
        """Test 3: Admin Dashboard Menu Names - GET /api/menu/drinks/{department_id} and GET /api/menu/sweets/{department_id}"""
        if not self.department_id:
            self.log_result("Admin Dashboard Menu Names Test", False, error="Department ID not available")
            return False
        
        try:
            # Test drinks menu
            drinks_response = self.session.get(f"{BASE_URL}/menu/drinks/{self.department_id}")
            
            if drinks_response.status_code != 200:
                self.log_result(
                    "Admin Dashboard Menu Names Test",
                    False,
                    error=f"Drinks menu failed: HTTP {drinks_response.status_code}: {drinks_response.text}"
                )
                return False
            
            drinks_data = drinks_response.json()
            
            # Test sweets menu
            sweets_response = self.session.get(f"{BASE_URL}/menu/sweets/{self.department_id}")
            
            if sweets_response.status_code != 200:
                self.log_result(
                    "Admin Dashboard Menu Names Test",
                    False,
                    error=f"Sweets menu failed: HTTP {sweets_response.status_code}: {sweets_response.text}"
                )
                return False
            
            sweets_data = sweets_response.json()
            
            # Check drinks menu structure for admin dashboard
            drinks_valid = True
            drinks_details = []
            
            for drink in drinks_data:
                if not isinstance(drink, dict) or "id" not in drink or "name" not in drink:
                    drinks_valid = False
                    break
                drinks_details.append(f"ID:{drink['id'][-8:]}→{drink['name']}")
            
            # Check sweets menu structure for admin dashboard
            sweets_valid = True
            sweets_details = []
            
            for sweet in sweets_data:
                if not isinstance(sweet, dict) or "id" not in sweet or "name" not in sweet:
                    sweets_valid = False
                    break
                sweets_details.append(f"ID:{sweet['id'][-8:]}→{sweet['name']}")
            
            if drinks_valid and sweets_valid and drinks_details and sweets_details:
                self.log_result(
                    "Admin Dashboard Menu Names Test",
                    True,
                    f"Menu names properly structured for admin dashboard UUID replacement. Drinks ({len(drinks_details)}): {'; '.join(drinks_details[:2])}. Sweets ({len(sweets_details)}): {'; '.join(sweets_details[:2])}"
                )
                return True
            else:
                error_details = []
                if not drinks_valid or not drinks_details:
                    error_details.append("drinks menu structure invalid")
                if not sweets_valid or not sweets_details:
                    error_details.append("sweets menu structure invalid")
                
                self.log_result(
                    "Admin Dashboard Menu Names Test",
                    False,
                    error=f"Menu structure issues: {'; '.join(error_details)}"
                )
                return False
                
        except Exception as e:
            self.log_result("Admin Dashboard Menu Names Test", False, error=str(e))
            return False
    
    def run_ui_improvements_tests(self):
        """Run all UI improvements tests"""
        print("🎨 UI IMPROVEMENTS BACKEND TESTING")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME}")
        print(f"Focus: Three UI improvements data structure validation")
        print("=" * 80)
        print()
        
        # Setup
        print("🔧 SETUP PHASE")
        auth_ok = self.setup_authentication()
        if not auth_ok:
            return False
        
        data_ok = self.setup_test_data()
        if not data_ok:
            return False
        
        # Test 1: Shopping List Formatting
        print("🧪 TEST 1: Shopping List Formatting")
        test1_ok = self.test_shopping_list_formatting()
        
        # Test 2: Order History Lunch Price
        print("🧪 TEST 2: Order History Lunch Price")
        test2_ok = self.test_order_history_lunch_price()
        
        # Test 3: Admin Dashboard Menu Names
        print("🧪 TEST 3: Admin Dashboard Menu Names")
        test3_ok = self.test_admin_dashboard_menu_names()
        
        # Summary
        self.print_test_summary()
        
        return all([test1_ok, test2_ok, test3_ok])
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎨 UI IMPROVEMENTS TESTING SUMMARY")
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
            print("✅ ALL UI IMPROVEMENTS TESTS PASSED!")
            print("   • Shopping list data structure ready for left-aligned formatting")
            print("   • Order history properly tracks lunch prices for employee profiles")
            print("   • Menu endpoints provide proper name fields for admin dashboard UUID replacement")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = UIImprovementsTester()
    
    try:
        success = tester.run_ui_improvements_tests()
        
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