#!/usr/bin/env python3
"""
CRITICAL DEBUG TEST - Tagespreis Text Verification

FOCUS: Create brand new breakfast order with lunch and immediately verify readable_items:

EXACT STEPS:
1. Authenticate with department
2. Create new test employee 
3. Create NEW breakfast order with lunch for today
4. IMMEDIATELY retrieve employee profile 
5. Check the EXACT readable_items content for lunch items
6. Verify there is NO "(€0.00 Tagespreis)" or "Tagespreis" text anywhere

This is to debug why the user still sees "Tagespreis" text despite our backend fix.

BACKEND URL: https://fireguard-menu.preview.emergentagent.com/api
DEPARTMENT: 1. Wachabteilung (fw4abteilung1)
CREDENTIALS: Employee: password1, Admin: admin1

PURPOSE: Test if the backend changes are actually taking effect by creating a completely fresh order.
"""

import requests
import json
import sys
from datetime import datetime

# Configuration - Use production backend URL from frontend/.env
BASE_URL = "https://fireguard-menu.preview.emergentagent.com/api"
DEPARTMENT_NAME = "1. Wachabteilung"
DEPARTMENT_PASSWORD = "newTestPassword123"  # Updated password from API response
ADMIN_PASSWORD = "admin1"

class TagespreisDebugTester:
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
            # Create test employee with realistic name and timestamp to avoid duplicates
            timestamp = datetime.now().strftime("%H%M%S")
            employee_data = {
                "name": f"Debug Test Employee {timestamp}",
                "department_id": self.department_id
            }
            
            employee_response = self.session.post(f"{BASE_URL}/employees", json=employee_data)
            
            if employee_response.status_code == 200:
                test_employee = employee_response.json()
                self.test_employee_id = test_employee.get("id")
                
                self.log_result(
                    "Test Employee Creation",
                    True,
                    f"Created test employee '{employee_data['name']}' with ID: {self.test_employee_id}"
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
    
    def test_tagespreis_debug(self):
        """CRITICAL DEBUG: Test for Tagespreis text in readable_items"""
        if not self.test_employee_id:
            self.log_result("Tagespreis Debug Test", False, error="Test employee ID not available")
            return False
        
        try:
            # Get employee profile with order history IMMEDIATELY after order creation
            response = self.session.get(f"{BASE_URL}/employees/{self.test_employee_id}/profile")
            
            if response.status_code == 200:
                data = response.json()
                
                # Check order history for lunch orders
                order_history = data.get("order_history", [])
                if not order_history:
                    self.log_result(
                        "Tagespreis Debug Test",
                        False,
                        error="No order history found immediately after order creation"
                    )
                    return False
                
                # Debug: Print full response for analysis
                print("🔍 DEBUG: Full employee profile response:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                print()
                
                # Find breakfast orders with lunch and check readable_items
                lunch_orders_found = []
                problematic_items = []
                all_readable_items = []
                
                for order in order_history:
                    if order.get("order_type") == "breakfast" and order.get("has_lunch"):
                        readable_items = order.get("readable_items", [])
                        
                        print(f"🔍 DEBUG: Found breakfast order with lunch, readable_items:")
                        print(json.dumps(readable_items, indent=2, ensure_ascii=False))
                        print()
                        
                        # Look for lunch items in readable_items
                        for item in readable_items:
                            description = item.get("description", "")
                            unit_price = item.get("unit_price", "")
                            total_price = item.get("total_price", "")
                            
                            all_readable_items.append({
                                "description": description,
                                "unit_price": unit_price,
                                "total_price": total_price
                            })
                            
                            if "Mittagessen" in description:
                                lunch_orders_found.append({
                                    "description": description,
                                    "unit_price": unit_price,
                                    "total_price": total_price
                                })
                                
                                # Check for ANY occurrence of "Tagespreis" text
                                if "Tagespreis" in description or "Tagespreis" in unit_price or "€0.00" in description or "€0.00" in unit_price:
                                    problematic_items.append({
                                        "description": description,
                                        "unit_price": unit_price,
                                        "total_price": total_price,
                                        "issue": "Contains Tagespreis or €0.00 reference"
                                    })
                
                # Detailed analysis
                print(f"🔍 DEBUG ANALYSIS:")
                print(f"   Total readable_items found: {len(all_readable_items)}")
                print(f"   Lunch items found: {len(lunch_orders_found)}")
                print(f"   Problematic items: {len(problematic_items)}")
                print()
                
                if all_readable_items:
                    print("🔍 ALL READABLE ITEMS:")
                    for i, item in enumerate(all_readable_items):
                        print(f"   {i+1}. Description: '{item['description']}'")
                        print(f"      Unit Price: '{item['unit_price']}'")
                        print(f"      Total Price: '{item['total_price']}'")
                    print()
                
                # Final evaluation
                if lunch_orders_found:
                    if problematic_items:
                        # CRITICAL: Still showing Tagespreis text
                        problem_details = []
                        for item in problematic_items:
                            problem_details.append(f"Description: '{item['description']}', Unit Price: '{item['unit_price']}'")
                        
                        self.log_result(
                            "Tagespreis Debug Test",
                            False,
                            error=f"❌ CRITICAL: Found {len(problematic_items)} lunch items STILL showing Tagespreis text: {'; '.join(problem_details)}"
                        )
                        return False
                    else:
                        # SUCCESS: No Tagespreis text found
                        lunch_details = []
                        for item in lunch_orders_found:
                            lunch_details.append(f"Description: '{item['description']}', Unit Price: '{item['unit_price']}', Total: '{item['total_price']}'")
                        
                        self.log_result(
                            "Tagespreis Debug Test",
                            True,
                            f"✅ SUCCESS: Found {len(lunch_orders_found)} lunch items WITHOUT Tagespreis text: {'; '.join(lunch_details)}"
                        )
                        return True
                else:
                    self.log_result(
                        "Tagespreis Debug Test",
                        False,
                        error="No lunch items found in readable_items, but lunch order was created"
                    )
                    return False
                    
            else:
                self.log_result(
                    "Tagespreis Debug Test",
                    False,
                    error=f"Failed to get employee profile: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Tagespreis Debug Test", False, error=str(e))
            return False
    
    def run_debug_test(self):
        """Run the complete Tagespreis debug test"""
        print("🔍 CRITICAL DEBUG TEST - Tagespreis Text Verification")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME}")
        print(f"Focus: Create fresh order and verify NO 'Tagespreis' text in readable_items")
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
        print("🧪 CRITICAL DEBUG TEST: Tagespreis Text Check")
        test_ok = self.test_tagespreis_debug()
        
        # Summary
        self.print_test_summary()
        
        return test_ok
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🔍 TAGESPREIS DEBUG TEST SUMMARY")
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
            print("🚨 CONCLUSION: Backend changes are NOT taking effect!")
            print("   The user is still seeing 'Tagespreis' text despite backend fixes.")
            print("   This suggests either:")
            print("   1. Frontend is caching old data")
            print("   2. Backend fix is not complete")
            print("   3. Different code path is being used")
        else:
            print("✅ TAGESPREIS DEBUG TEST PASSED!")
            print("   • Fresh breakfast order with lunch created successfully")
            print("   • NO 'Tagespreis' text found in readable_items")
            print("   • Backend changes are taking effect correctly")
            print("   • User issue may be frontend caching or different scenario")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = TagespreisDebugTester()
    
    try:
        success = tester.run_debug_test()
        
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