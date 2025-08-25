#!/usr/bin/env python3
"""
CRITICAL ID CONSISTENCY INVESTIGATION: Department, Employee, and Menu Item ID mismatch causing breakfast order failures

LIVE SYSTEM: https://fw-kantine.de
FOCUS: 2. Wachabteilung (fw4abteilung2) - freshly recreated menu items
CREDENTIALS: Employee: costa, Admin: lenny

USER CONTEXT: User experienced similar bug before with incorrect IDs between departments, breakfast items, and employee IDs. 
User has recreated all menu items in 2. Wachabteilung and can see them in database, but breakfast orders still fail.

CRITICAL ID CONSISTENCY CHECKS NEEDED:
1. Department ID Verification - Verify department "2. Wachabteilung" has correct ID "fw4abteilung2"
2. Employee ID Consistency - Get employees from department fw4abteilung2, check Jonas Parlow employee record
3. Menu Item ID Verification - GET /api/menu/breakfast/fw4abteilung2 - verify menu items exist and have correct department_id
4. Cross-Reference ID Matching - Compare department_id in menu items vs department authentication
5. Order Creation ID Flow - Trace an order creation request to see which IDs are being passed

EXPECTED FINDINGS: ID mismatch between frontend requests and backend database
"""

import requests
import json
import sys
from datetime import datetime

# Configuration - Using environment variables from frontend/.env
BASE_URL = "https://canteen-keeper.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_PASSWORD = "costa"  # User provided credentials
ADMIN_PASSWORD = "lenny"       # User provided credentials

class IDConsistencyTester:
    def __init__(self):
        self.session = requests.Session()
        self.department_id = None
        self.jonas_id = None
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
    
    def verify_department_id(self):
        """CRITICAL CHECK 1: Verify department '2. Wachabteilung' has correct ID 'fw4abteilung2'"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department", json={
                "department_name": DEPARTMENT_NAME,
                "password": DEPARTMENT_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.department_id = data.get("department_id")
                expected_id = "fw4abteilung2"
                
                id_matches = self.department_id == expected_id
                
                self.log_result(
                    "Department ID Verification", 
                    id_matches, 
                    f"Expected: {expected_id}, Got: {self.department_id}, Match: {id_matches}"
                )
                
                if not id_matches:
                    self.log_result(
                        "CRITICAL ID MISMATCH DETECTED",
                        False,
                        error=f"Department '{DEPARTMENT_NAME}' has ID '{self.department_id}' but expected 'fw4abteilung2'. This is likely the root cause of breakfast order failures!"
                    )
                
                return id_matches
            else:
                self.log_result(
                    "Department ID Verification", 
                    False, 
                    error=f"Authentication failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Department ID Verification", False, error=str(e))
            return False
    
    def verify_employee_consistency(self):
        """CRITICAL CHECK 2: Get employees from department and check Jonas Parlow employee record"""
        if not self.department_id:
            self.log_result(
                "Employee ID Consistency", 
                False, 
                error="Department ID not available"
            )
            return False
        
        try:
            response = self.session.get(f"{BASE_URL}/departments/{self.department_id}/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                # Find Jonas Parlow
                jonas_employee = None
                for emp in employees:
                    if "Jonas Parlow" in emp.get("name", ""):
                        jonas_employee = emp
                        self.jonas_id = emp["id"]
                        break
                
                if jonas_employee:
                    # Verify employee belongs to correct department_id
                    emp_dept_id = jonas_employee.get("department_id")
                    dept_id_matches = emp_dept_id == self.department_id
                    
                    self.log_result(
                        "Employee ID Consistency",
                        dept_id_matches,
                        f"Jonas Parlow found (ID: {self.jonas_id}). Employee dept_id: {emp_dept_id}, Expected: {self.department_id}, Match: {dept_id_matches}"
                    )
                    
                    if not dept_id_matches:
                        self.log_result(
                            "CRITICAL EMPLOYEE DEPT MISMATCH",
                            False,
                            error=f"Jonas Parlow has department_id '{emp_dept_id}' but should be '{self.department_id}'. This causes order creation failures!"
                        )
                    
                    return dept_id_matches
                else:
                    self.log_result(
                        "Employee ID Consistency",
                        False,
                        error=f"Jonas Parlow not found in department {self.department_id}. Found {len(employees)} employees: {[emp.get('name') for emp in employees]}"
                    )
                    return False
                
            else:
                self.log_result(
                    "Employee ID Consistency", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Employee ID Consistency", False, error=str(e))
            return False
    
    def verify_menu_item_ids(self):
        """CRITICAL CHECK 3: Verify menu items exist and have correct department_id"""
        if not self.department_id:
            self.log_result(
                "Menu Item ID Verification", 
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
                    # Verify all items have correct department_id
                    dept_id_mismatches = []
                    for item in breakfast_items:
                        item_dept_id = item.get("department_id")
                        if item_dept_id != self.department_id:
                            dept_id_mismatches.append(f"Item {item.get('id', 'unknown')} has dept_id '{item_dept_id}'")
                    
                    if dept_id_mismatches:
                        self.log_result(
                            "Breakfast Menu ID Verification",
                            False,
                            error=f"Department ID mismatches found: {dept_id_mismatches}"
                        )
                    else:
                        self.log_result(
                            "Breakfast Menu ID Verification",
                            True,
                            f"Found {len(breakfast_items)} breakfast items, all have correct department_id: {self.department_id}"
                        )
                        success_count += 1
                else:
                    self.log_result(
                        "Breakfast Menu ID Verification",
                        False,
                        error=f"No breakfast items found for department {self.department_id}. This explains breakfast order failures!"
                    )
            else:
                self.log_result(
                    "Breakfast Menu ID Verification",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_result("Breakfast Menu ID Verification", False, error=str(e))
        
        # Check toppings menu
        try:
            response = self.session.get(f"{BASE_URL}/menu/toppings/{self.department_id}")
            
            if response.status_code == 200:
                toppings_items = response.json()
                self.toppings_menu = toppings_items
                
                if toppings_items:
                    # Verify all items have correct department_id
                    dept_id_mismatches = []
                    for item in toppings_items:
                        item_dept_id = item.get("department_id")
                        if item_dept_id != self.department_id:
                            dept_id_mismatches.append(f"Item {item.get('id', 'unknown')} has dept_id '{item_dept_id}'")
                    
                    if dept_id_mismatches:
                        self.log_result(
                            "Toppings Menu ID Verification",
                            False,
                            error=f"Department ID mismatches found: {dept_id_mismatches}"
                        )
                    else:
                        self.log_result(
                            "Toppings Menu ID Verification",
                            True,
                            f"Found {len(toppings_items)} topping items, all have correct department_id: {self.department_id}"
                        )
                        success_count += 1
                else:
                    self.log_result(
                        "Toppings Menu ID Verification",
                        False,
                        error=f"No topping items found for department {self.department_id}. This explains breakfast order failures!"
                    )
            else:
                self.log_result(
                    "Toppings Menu ID Verification",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                
        except Exception as e:
            self.log_result("Toppings Menu ID Verification", False, error=str(e))
        
        return success_count == total_checks
    
    def cross_reference_id_matching(self):
        """CRITICAL CHECK 4: Compare department_id in menu items vs department authentication"""
        if not self.department_id or not self.breakfast_menu:
            self.log_result(
                "Cross-Reference ID Matching", 
                False, 
                error="Missing department_id or menu data"
            )
            return False
        
        try:
            # Check if all menu items reference the same department_id as authentication
            auth_dept_id = self.department_id
            menu_dept_ids = set()
            
            for item in self.breakfast_menu:
                menu_dept_ids.add(item.get("department_id"))
            
            for item in self.toppings_menu:
                menu_dept_ids.add(item.get("department_id"))
            
            # Remove None values
            menu_dept_ids.discard(None)
            
            if len(menu_dept_ids) == 1 and auth_dept_id in menu_dept_ids:
                self.log_result(
                    "Cross-Reference ID Matching",
                    True,
                    f"All menu items consistently reference department_id: {auth_dept_id}"
                )
                return True
            else:
                self.log_result(
                    "Cross-Reference ID Matching",
                    False,
                    error=f"ID mismatch! Auth dept_id: {auth_dept_id}, Menu dept_ids: {menu_dept_ids}. This causes order creation failures!"
                )
                return False
                
        except Exception as e:
            self.log_result("Cross-Reference ID Matching", False, error=str(e))
            return False
    
    def trace_order_creation_id_flow(self):
        """CRITICAL CHECK 5: Trace an order creation request to see which IDs are being passed"""
        if not self.department_id or not self.jonas_id or not self.breakfast_menu or not self.toppings_menu:
            self.log_result(
                "Order Creation ID Flow", 
                False, 
                error="Missing required data (department_id, employee_id, or menu items)"
            )
            return False
        
        try:
            # Create a test breakfast order with detailed ID tracing
            order_data = {
                "employee_id": self.jonas_id,
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
            
            # Log the exact IDs being sent
            id_trace = f"Sending order with employee_id: {self.jonas_id}, department_id: {self.department_id}"
            print(f"🔍 ID TRACE: {id_trace}")
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            if response.status_code == 200:
                order_result = response.json()
                self.log_result(
                    "Order Creation ID Flow",
                    True,
                    f"Order created successfully! Total: €{order_result.get('total_price', 'N/A')}. All IDs are consistent."
                )
                return True
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_detail)
                except:
                    pass
                
                self.log_result(
                    "Order Creation ID Flow",
                    False,
                    error=f"Order creation failed: HTTP {response.status_code}: {error_detail}. This confirms ID consistency issues!"
                )
                
                # Additional debugging - check if it's a menu item lookup failure
                if "menu" in error_detail.lower() or "item" in error_detail.lower():
                    self.log_result(
                        "ROOT CAUSE IDENTIFIED",
                        False,
                        error="Order creation fails during menu item lookup - confirms department_id mismatch between order request and menu items!"
                    )
                
                return False
                
        except Exception as e:
            self.log_result("Order Creation ID Flow", False, error=str(e))
            return False
    
    def run_id_consistency_investigation(self):
        """Run the complete ID consistency investigation"""
        print("🔍 CRITICAL ID CONSISTENCY INVESTIGATION")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME}")
        print(f"Focus: ID mismatches causing breakfast order failures")
        print(f"Expected Department ID: fw4abteilung2")
        print("=" * 80)
        print()
        
        # CRITICAL CHECK 1: Department ID Verification
        print("🔍 CRITICAL CHECK 1: Department ID Verification")
        dept_id_ok = self.verify_department_id()
        
        # CRITICAL CHECK 2: Employee ID Consistency
        print("🔍 CRITICAL CHECK 2: Employee ID Consistency")
        employee_id_ok = self.verify_employee_consistency()
        
        # CRITICAL CHECK 3: Menu Item ID Verification
        print("🔍 CRITICAL CHECK 3: Menu Item ID Verification")
        menu_id_ok = self.verify_menu_item_ids()
        
        # CRITICAL CHECK 4: Cross-Reference ID Matching
        print("🔍 CRITICAL CHECK 4: Cross-Reference ID Matching")
        cross_ref_ok = self.cross_reference_id_matching()
        
        # CRITICAL CHECK 5: Order Creation ID Flow
        print("🔍 CRITICAL CHECK 5: Order Creation ID Flow")
        order_flow_ok = self.trace_order_creation_id_flow()
        
        # Summary and Root Cause Analysis
        self.print_id_consistency_summary()
        
        return all([dept_id_ok, employee_id_ok, menu_id_ok, cross_ref_ok, order_flow_ok])
    
    def print_id_consistency_summary(self):
        """Print ID consistency investigation summary with root cause analysis"""
        print("\n" + "=" * 80)
        print("🔍 ID CONSISTENCY INVESTIGATION SUMMARY")
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
        
        # Check for department ID mismatch
        dept_check = next((r for r in self.test_results if "Department ID Verification" in r["test"]), None)
        if dept_check and "❌ FAIL" in dept_check["status"]:
            print("   🚨 CRITICAL: Department ID mismatch detected!")
            print(f"   • Expected: fw4abteilung2")
            print(f"   • Actual: {self.department_id}")
            print("   • This is likely the PRIMARY ROOT CAUSE of breakfast order failures")
            print("   • Frontend may be using wrong department ID in API calls")
        
        # Check for menu item issues
        menu_checks = [r for r in self.test_results if "Menu" in r["test"] and "❌ FAIL" in r["status"]]
        if menu_checks:
            print("   🚨 MENU ITEM ISSUES:")
            for check in menu_checks:
                print(f"   • {check['test']}: {check['error']}")
        
        # Check for employee issues
        emp_check = next((r for r in self.test_results if "Employee ID Consistency" in r["test"]), None)
        if emp_check and "❌ FAIL" in emp_check["status"]:
            print("   🚨 EMPLOYEE ID ISSUES:")
            print(f"   • {emp_check['error']}")
        
        # Check for order creation issues
        order_check = next((r for r in self.test_results if "Order Creation ID Flow" in r["test"]), None)
        if order_check and "❌ FAIL" in order_check["status"]:
            print("   🚨 ORDER CREATION FAILURE CONFIRMED:")
            print(f"   • {order_check['error']}")
        
        # Recommendations
        print("\n🔧 RECOMMENDED FIXES:")
        if failed_tests:
            print("   1. Verify department ID consistency in database")
            print("   2. Check frontend API calls use correct department_id")
            print("   3. Ensure menu items have correct department_id")
            print("   4. Verify employee records have correct department_id")
            print("   5. Check order creation logic uses consistent IDs")
        else:
            print("   ✅ All ID consistency checks passed - no issues detected")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = IDConsistencyTester()
    
    try:
        success = tester.run_id_consistency_investigation()
        
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