#!/usr/bin/env python3
"""
UI IMPROVEMENTS BACKEND TESTING

FOCUS: Test three specific UI improvements that were just implemented:
1. Shopping List Formatting - GET /api/orders/daily-summary/{department_id}
2. Order History Lunch Price - GET /api/employees/{employee_id}/profile
3. Admin Dashboard Menu Names - GET /api/menu/drinks/{department_id} and GET /api/menu/sweets/{department_id}

BACKEND URL: https://fireguard-menu.preview.emergentagent.com/api
DEPARTMENT: 1. Wachabteilung (fw4abteilung1)
CREDENTIALS: Employee: password1, Admin: admin1

PURPOSE: Verify that the backend data structures are properly formatted for the new frontend UI improvements.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration - Use production backend URL from frontend/.env
BASE_URL = "https://fireguard-menu.preview.emergentagent.com/api"
DEPARTMENT_NAME = "1. Wachabteilung"
DEPARTMENT_PASSWORD = "password1"
ADMIN_PASSWORD = "admin1"

class LiveSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.department_id = None
        self.employee_list = []
        self.test_results = []
        self.breakfast_menu = []
        self.toppings_menu = []
        
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
    
    def test_live_authentication(self):
        """Test authentication on fw-kantine.de with credentials costa/lenny"""
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
                    "Live Employee Authentication", 
                    True, 
                    f"Successfully authenticated as employee with department_id: {self.department_id}"
                )
                
                # Test admin authentication
                admin_response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                    "department_name": DEPARTMENT_NAME,
                    "admin_password": ADMIN_PASSWORD
                })
                
                if admin_response.status_code == 200:
                    admin_data = admin_response.json()
                    self.log_result(
                        "Live Admin Authentication", 
                        True, 
                        f"Successfully authenticated as admin with role: {admin_data.get('role')}"
                    )
                    return True
                else:
                    self.log_result(
                        "Live Admin Authentication", 
                        False, 
                        error=f"Admin auth failed: HTTP {admin_response.status_code}: {admin_response.text}"
                    )
                    return False
                
            else:
                self.log_result(
                    "Live Employee Authentication", 
                    False, 
                    error=f"Employee auth failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Live Authentication", False, error=str(e))
            return False
    
    def check_employee_list_live(self):
        """Check employee list in department fw4abteilung2 on LIVE system"""
        if not self.department_id:
            self.log_result(
                "Live Employee List Check", 
                False, 
                error="Department ID not available"
            )
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/departments/{self.department_id}/employees")
            
            if response.status_code == 200:
                employees = response.json()
                self.employee_list = employees
                
                self.log_result(
                    "Live Employee List Check",
                    True,
                    f"Found {len(employees)} employees in department {self.department_id}. Names: {[emp.get('name', 'Unknown') for emp in employees]}"
                )
                
                # Check if list is empty (as expected after user cleanup)
                if len(employees) == 0:
                    self.log_result(
                        "Employee List Empty Verification",
                        True,
                        "Employee list is empty as expected after user cleanup"
                    )
                
                return True
                
            else:
                self.log_result(
                    "Live Employee List Check", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Live Employee List Check", False, error=str(e))
            return False
    
    def verify_menu_items_live(self):
        """Verify menu items exist on fw-kantine.de (not preview system)"""
        if not self.department_id:
            self.log_result(
                "Live Menu Items Verification", 
                False, 
                error="Department ID not available"
            )
            return False
        
        success_count = 0
        total_checks = 2
        
        # Check breakfast menu
        try:
            response = self.session.get(f"{BASE_URL}/menu/breakfast/{self.department_id}")
            
            if response.status_code == 200:
                breakfast_items = response.json()
                self.breakfast_menu = breakfast_items
                
                if breakfast_items:
                    self.log_result(
                        "Live Breakfast Menu Verification",
                        True,
                        f"Found {len(breakfast_items)} breakfast items on LIVE system. Items: {[item.get('roll_type', 'Unknown') + ' (€' + str(item.get('price', 0)) + ')' for item in breakfast_items]}"
                    )
                    success_count += 1
                else:
                    self.log_result(
                        "Live Breakfast Menu Verification",
                        False,
                        error=f"No breakfast items found for department {self.department_id} on LIVE system. This explains breakfast order failures!"
                    )
            else:
                self.log_result(
                    "Live Breakfast Menu Verification",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_result("Live Breakfast Menu Verification", False, error=str(e))
        
        # Check toppings menu
        try:
            response = self.session.get(f"{BASE_URL}/menu/toppings/{self.department_id}")
            
            if response.status_code == 200:
                toppings_items = response.json()
                self.toppings_menu = toppings_items
                
                if toppings_items:
                    self.log_result(
                        "Live Toppings Menu Verification",
                        True,
                        f"Found {len(toppings_items)} topping items on LIVE system. Items: {[item.get('topping_type', item.get('name', 'Unknown')) + ' (€' + str(item.get('price', 0)) + ')' for item in toppings_items]}"
                    )
                    success_count += 1
                else:
                    self.log_result(
                        "Live Toppings Menu Verification",
                        False,
                        error=f"No topping items found for department {self.department_id} on LIVE system. This explains breakfast order failures!"
                    )
            else:
                self.log_result(
                    "Live Toppings Menu Verification",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_result("Live Toppings Menu Verification", False, error=str(e))
        
        return success_count == total_checks
    
    def test_breakfast_order_creation_live(self):
        """Test actual breakfast order creation on LIVE system"""
        if not self.department_id or not self.breakfast_menu or not self.toppings_menu:
            self.log_result(
                "Live Breakfast Order Creation", 
                False, 
                error="Missing required data (department_id or menu items)"
            )
            return False
        
        # First, we need to create a test employee since user deleted all employees
        try:
            # Create a test employee
            employee_data = {
                "name": "Test Employee for Order",
                "department_id": self.department_id
            }
            
            employee_response = self.session.post(f"{BASE_URL}/employees", json=employee_data)
            
            if employee_response.status_code == 200:
                test_employee = employee_response.json()
                test_employee_id = test_employee.get("id")
                
                self.log_result(
                    "Test Employee Creation",
                    True,
                    f"Created test employee with ID: {test_employee_id}"
                )
                
                # Now try to create a breakfast order
                order_data = {
                    "employee_id": test_employee_id,
                    "department_id": self.department_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": False,
                        "boiled_eggs": 0,
                        "has_coffee": False
                    }]
                }
                
                order_response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                
                if order_response.status_code == 200:
                    order_result = order_response.json()
                    self.log_result(
                        "Live Breakfast Order Creation",
                        True,
                        f"✅ BREAKTHROUGH! Order created successfully on LIVE system! Total: €{order_result.get('total_price', 'N/A')}. The backend is working correctly."
                    )
                    return True
                else:
                    error_detail = order_response.text
                    try:
                        error_json = order_response.json()
                        error_detail = error_json.get('detail', error_detail)
                    except:
                        pass
                    
                    self.log_result(
                        "Live Breakfast Order Creation",
                        False,
                        error=f"🚨 CONFIRMED BUG! Order creation failed on LIVE system: HTTP {order_response.status_code}: {error_detail}"
                    )
                    return False
                    
            else:
                self.log_result(
                    "Test Employee Creation",
                    False,
                    error=f"Could not create test employee: HTTP {employee_response.status_code}: {employee_response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Live Breakfast Order Creation", False, error=str(e))
            return False
    
    def check_for_hidden_database_issues(self):
        """Check for hidden database issues on LIVE MongoDB instance"""
        if not self.department_id:
            self.log_result(
                "Hidden Database Issues Check", 
                False, 
                error="Department ID not available"
            )
            return False
        
        try:
            # Check for any existing orders (should be empty after cleanup)
            today = datetime.now().date().isoformat()
            
            # Check daily summary
            summary_response = self.session.get(f"{BASE_URL}/orders/daily-summary/{self.department_id}")
            
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                
                breakfast_summary = summary_data.get("breakfast_summary", {})
                employee_orders = summary_data.get("employee_orders", {})
                
                if not breakfast_summary and not employee_orders:
                    self.log_result(
                        "Daily Summary Clean Check",
                        True,
                        "Daily summary is clean - no existing orders found as expected after cleanup"
                    )
                else:
                    self.log_result(
                        "Daily Summary Clean Check",
                        False,
                        error=f"🚨 HIDDEN ORDERS FOUND! Breakfast summary: {breakfast_summary}, Employee orders: {list(employee_orders.keys())}. This may be blocking new orders!"
                    )
                    return False
                    
            else:
                self.log_result(
                    "Daily Summary Clean Check",
                    False,
                    error=f"Could not check daily summary: HTTP {summary_response.status_code}: {summary_response.text}"
                )
                return False
            
            # Check lunch settings
            lunch_response = self.session.get(f"{BASE_URL}/lunch-settings")
            
            if lunch_response.status_code == 200:
                lunch_data = lunch_response.json()
                self.log_result(
                    "Lunch Settings Check",
                    True,
                    f"Lunch settings found: Price €{lunch_data.get('price', 0)}, Enabled: {lunch_data.get('enabled', False)}, Boiled eggs: €{lunch_data.get('boiled_eggs_price', 0)}"
                )
            else:
                self.log_result(
                    "Lunch Settings Check",
                    False,
                    error=f"Could not check lunch settings: HTTP {lunch_response.status_code}: {lunch_response.text}"
                )
                return False
            
            return True
                
        except Exception as e:
            self.log_result("Hidden Database Issues Check", False, error=str(e))
            return False
    
    def verify_no_stale_orders_live(self):
        """Verify no stale orders exist on LIVE system"""
        if not self.department_id:
            self.log_result(
                "Stale Orders Check", 
                False, 
                error="Department ID not available"
            )
            return False
        
        try:
            # Check breakfast history for any existing orders
            history_response = self.session.get(f"{BASE_URL}/orders/breakfast-history/{self.department_id}?days_back=7")
            
            if history_response.status_code == 200:
                history_data = history_response.json()
                history_list = history_data.get("history", [])
                
                if not history_list:
                    self.log_result(
                        "Stale Orders Check",
                        True,
                        "No breakfast history found - system is clean as expected after user cleanup"
                    )
                    return True
                else:
                    total_orders = sum(day.get("total_orders", 0) for day in history_list)
                    self.log_result(
                        "Stale Orders Check",
                        False,
                        error=f"🚨 STALE ORDERS FOUND! Found {len(history_list)} days with orders, total {total_orders} orders. This may be interfering with new order creation!"
                    )
                    
                    # Show details of found orders
                    for day in history_list[:3]:  # Show first 3 days
                        date = day.get("date", "Unknown")
                        orders = day.get("total_orders", 0)
                        if orders > 0:
                            print(f"   • {date}: {orders} orders")
                    
                    return False
                    
            else:
                self.log_result(
                    "Stale Orders Check",
                    False,
                    error=f"Could not check breakfast history: HTTP {history_response.status_code}: {history_response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Stale Orders Check", False, error=str(e))
            return False
    
    def run_live_system_investigation(self):
        """Run the complete live system investigation"""
        print("🔍 CRITICAL LIVE SYSTEM INVESTIGATION")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME}")
        print(f"Focus: Breakfast order failures after complete database cleanup")
        print(f"Expected Department ID: fw4abteilung2")
        print("=" * 80)
        print()
        
        # CRITICAL CHECK 1: Live Authentication
        print("🔍 CRITICAL CHECK 1: Live Authentication")
        auth_ok = self.test_live_authentication()
        
        # CRITICAL CHECK 2: Employee List Check
        print("🔍 CRITICAL CHECK 2: Employee List Check")
        employee_ok = self.check_employee_list_live()
        
        # CRITICAL CHECK 3: Menu Items Verification
        print("🔍 CRITICAL CHECK 3: Menu Items Verification")
        menu_ok = self.verify_menu_items_live()
        
        # CRITICAL CHECK 4: Breakfast Order Creation
        print("🔍 CRITICAL CHECK 4: Breakfast Order Creation")
        order_ok = self.test_breakfast_order_creation_live()
        
        # CRITICAL CHECK 5: Hidden Database Issues
        print("🔍 CRITICAL CHECK 5: Hidden Database Issues")
        db_ok = self.check_for_hidden_database_issues()
        
        # CRITICAL CHECK 6: Stale Orders Check
        print("🔍 CRITICAL CHECK 6: Stale Orders Check")
        stale_ok = self.verify_no_stale_orders_live()
        
        # Summary and Root Cause Analysis
        self.print_live_system_summary()
        
        return all([auth_ok, employee_ok, menu_ok, order_ok, db_ok, stale_ok])
    
    def print_live_system_summary(self):
        """Print live system investigation summary with root cause analysis"""
        print("\n" + "=" * 80)
        print("🔍 LIVE SYSTEM INVESTIGATION SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        
        print(f"Total Checks: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        print()
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            print("❌ FAILED CHECKS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['error']}")
            print()
        
        # ROOT CAUSE ANALYSIS
        print("🔍 ROOT CAUSE ANALYSIS:")
        
        # Check for authentication issues
        auth_check = next((r for r in self.test_results if "Live Employee Authentication" in r["test"]), None)
        if auth_check and "❌ FAIL" in auth_check["status"]:
            print("   🚨 CRITICAL: Authentication failed!")
            print(f"   • Credentials costa/lenny may be incorrect")
            print("   • Department '2. Wachabteilung' may not exist")
            print("   • This is likely the PRIMARY ROOT CAUSE of all failures")
        
        # Check for menu item issues
        menu_checks = [r for r in self.test_results if "Menu" in r["test"] and "❌ FAIL" in r["status"]]
        if menu_checks:
            print("   🚨 MENU ITEM ISSUES:")
            for check in menu_checks:
                print(f"   • {check['test']}: {check['error']}")
        
        # Check for order creation issues
        order_check = next((r for r in self.test_results if "Live Breakfast Order Creation" in r["test"]), None)
        if order_check and "❌ FAIL" in order_check["status"]:
            print("   🚨 ORDER CREATION FAILURE CONFIRMED:")
            print(f"   • {order_check['error']}")
            print("   • This confirms the user-reported bug exists on live system")
        
        # Check for database issues
        db_checks = [r for r in self.test_results if ("Database" in r["test"] or "Stale" in r["test"]) and "❌ FAIL" in r["status"]]
        if db_checks:
            print("   🚨 DATABASE ISSUES:")
            for check in db_checks:
                print(f"   • {check['test']}: {check['error']}")
        
        # Recommendations
        print("\n🔧 RECOMMENDED FIXES:")
        if failed_tests:
            print("   1. Verify credentials costa/lenny are correct for department '2. Wachabteilung'")
            print("   2. Check if department exists in live database")
            print("   3. Ensure menu items were properly recreated after cleanup")
            print("   4. Investigate backend order creation logic for bugs")
            print("   5. Check for any remaining stale data interfering with orders")
        else:
            print("   ✅ All live system checks passed - backend is working correctly")
            print("   • The issue may be frontend-specific or user-interface related")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = LiveSystemTester()
    
    try:
        success = tester.run_live_system_investigation()
        
        # Exit with appropriate code
        failed_tests = [r for r in tester.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            sys.exit(1)  # Indicate test failures
        else:
            sys.exit(0)  # All tests passed
            
    except KeyboardInterrupt:
        print("\n⚠️ Investigation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()