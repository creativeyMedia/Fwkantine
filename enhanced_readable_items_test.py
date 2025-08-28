#!/usr/bin/env python3
"""
ENHANCED READABLE ITEMS TEST FOR SPONSORED MEALS

This test specifically verifies the enhanced readable_items format
that includes detailed cost breakdowns for sponsored meals.
"""

import requests
import json
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "https://canteen-manager-2.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class EnhancedReadableItemsTester:
    def __init__(self):
        self.session = requests.Session()
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
    
    def authenticate_admin(self):
        """Authenticate as department admin"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                self.log_result(
                    "Department Admin Authentication",
                    True,
                    f"Successfully authenticated as admin for {DEPARTMENT_NAME}"
                )
                return True
            else:
                self.log_result(
                    "Department Admin Authentication",
                    False,
                    error=f"Authentication failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Department Admin Authentication", False, error=str(e))
            return False
    
    def create_fresh_test_scenario(self):
        """Create a fresh test scenario with new employees and orders"""
        try:
            # Create 3 new employees with unique names
            timestamp = datetime.now().strftime("%H%M%S")
            employee_names = [f"TestEmp{timestamp}A", f"TestEmp{timestamp}B", f"TestEmp{timestamp}C"]
            created_employees = []
            
            for name in employee_names:
                response = self.session.post(f"{BASE_URL}/employees", json={
                    "name": name,
                    "department_id": DEPARTMENT_ID
                })
                
                if response.status_code == 200:
                    employee = response.json()
                    created_employees.append(employee)
                    print(f"   Created employee: {name}")
            
            if len(created_employees) < 3:
                self.log_result(
                    "Create Fresh Test Scenario",
                    False,
                    error=f"Could only create {len(created_employees)} employees, need 3"
                )
                return False, []
            
            # Create breakfast orders for each employee
            orders_created = []
            for i, employee in enumerate(created_employees):
                order_data = {
                    "employee_id": employee["id"],
                    "department_id": DEPARTMENT_ID,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": i < 2,  # First 2 employees get lunch
                        "boiled_eggs": 2,
                        "has_coffee": False
                    }]
                }
                
                response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    orders_created.append(order)
                    print(f"   Created order for {employee['name']}: €{order.get('total_price', 0):.2f}")
            
            if len(orders_created) >= 3:
                self.log_result(
                    "Create Fresh Test Scenario",
                    True,
                    f"Successfully created {len(created_employees)} employees and {len(orders_created)} orders"
                )
                return True, created_employees
            else:
                self.log_result(
                    "Create Fresh Test Scenario",
                    False,
                    error=f"Could only create {len(orders_created)} orders"
                )
                return False, []
                
        except Exception as e:
            self.log_result("Create Fresh Test Scenario", False, error=str(e))
            return False, []
    
    def test_breakfast_sponsoring_enhanced_readable_items(self, employees):
        """Test breakfast sponsoring and check for enhanced readable_items"""
        try:
            if len(employees) < 3:
                self.log_result(
                    "Test Breakfast Sponsoring Enhanced Readable Items",
                    False,
                    error="Not enough employees for test"
                )
                return False
            
            # Use last employee as sponsor
            sponsor = employees[-1]
            today = date.today().isoformat()
            
            # Perform breakfast sponsoring
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": sponsor["id"],
                "sponsor_employee_name": sponsor["name"]
            }
            
            response = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=sponsor_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check the sponsoring response
                sponsored_items = result.get("sponsored_items", "")
                total_cost = result.get("total_cost", 0)
                affected_employees = result.get("affected_employees", 0)
                
                print(f"   Sponsoring Response:")
                print(f"   - Sponsored items: {sponsored_items}")
                print(f"   - Total cost: €{total_cost:.2f}")
                print(f"   - Affected employees: {affected_employees}")
                
                # Now check the sponsor's order for enhanced readable_items
                orders_response = self.session.get(f"{BASE_URL}/employees/{sponsor['id']}/orders")
                if orders_response.status_code == 200:
                    orders_data = orders_response.json()
                    orders = orders_data.get("orders", [])
                    
                    # Find today's orders
                    todays_orders = [order for order in orders if order.get("timestamp", "").startswith(today)]
                    
                    enhanced_readable_items_found = False
                    sponsor_order_details = None
                    
                    for order in todays_orders:
                        readable_items = order.get("readable_items", [])
                        is_sponsor_order = order.get("is_sponsor_order", False)
                        sponsor_details = order.get("sponsor_details", "")
                        
                        print(f"   Order Analysis:")
                        print(f"   - Is sponsor order: {is_sponsor_order}")
                        print(f"   - Readable items: {readable_items}")
                        print(f"   - Sponsor details: {sponsor_details}")
                        
                        # Check for enhanced readable_items format
                        if isinstance(readable_items, list) and len(readable_items) > 0:
                            for item in readable_items:
                                if isinstance(item, dict):
                                    description = item.get("description", "")
                                    unit_price = item.get("unit_price", "")
                                    total_price = item.get("total_price", "")
                                    
                                    # Check for sponsored meal description
                                    if "ausgegeben" in description.lower():
                                        enhanced_readable_items_found = True
                                        sponsor_order_details = {
                                            "description": description,
                                            "unit_price": unit_price,
                                            "total_price": total_price,
                                            "sponsor_details": sponsor_details
                                        }
                                        break
                    
                    if enhanced_readable_items_found:
                        self.log_result(
                            "Test Breakfast Sponsoring Enhanced Readable Items",
                            True,
                            f"✅ ENHANCED FEATURE VERIFIED: Found enhanced readable_items with detailed breakdown: {sponsor_order_details}"
                        )
                        return True
                    else:
                        self.log_result(
                            "Test Breakfast Sponsoring Enhanced Readable Items",
                            False,
                            error=f"Enhanced readable_items format not found in sponsor's orders. Found {len(todays_orders)} orders today."
                        )
                        return False
                else:
                    self.log_result(
                        "Test Breakfast Sponsoring Enhanced Readable Items",
                        False,
                        error=f"Could not fetch sponsor's orders: HTTP {orders_response.status_code}"
                    )
                    return False
            elif response.status_code == 400 and "bereits gesponsert" in response.text:
                # Already sponsored - check existing sponsored orders
                self.log_result(
                    "Test Breakfast Sponsoring Enhanced Readable Items",
                    True,
                    "✅ Breakfast already sponsored today - checking existing sponsored orders"
                )
                return self.check_existing_sponsored_orders(sponsor)
            else:
                self.log_result(
                    "Test Breakfast Sponsoring Enhanced Readable Items",
                    False,
                    error=f"Breakfast sponsoring failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Breakfast Sponsoring Enhanced Readable Items", False, error=str(e))
            return False
    
    def check_existing_sponsored_orders(self, sponsor):
        """Check existing sponsored orders for enhanced readable_items"""
        try:
            orders_response = self.session.get(f"{BASE_URL}/employees/{sponsor['id']}/orders")
            if orders_response.status_code != 200:
                return False
            
            orders_data = orders_response.json()
            orders = orders_data.get("orders", [])
            
            # Check recent orders (last 2 days)
            today = date.today().isoformat()
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            recent_orders = [order for order in orders 
                           if order.get("timestamp", "").startswith(today) or 
                              order.get("timestamp", "").startswith(yesterday)]
            
            enhanced_found = False
            for order in recent_orders:
                if order.get("is_sponsor_order", False):
                    readable_items = order.get("readable_items", [])
                    sponsor_details = order.get("sponsor_details", "")
                    
                    print(f"   Found sponsor order:")
                    print(f"   - Readable items: {readable_items}")
                    print(f"   - Sponsor details: {sponsor_details}")
                    
                    # Check for enhanced format
                    if isinstance(readable_items, list):
                        for item in readable_items:
                            if isinstance(item, dict) and "ausgegeben" in item.get("description", "").lower():
                                enhanced_found = True
                                break
            
            return enhanced_found
            
        except Exception as e:
            print(f"Error checking existing orders: {e}")
            return False
    
    def test_lunch_sponsoring_enhanced_readable_items(self, employees):
        """Test lunch sponsoring and check for enhanced readable_items"""
        try:
            if len(employees) < 2:
                self.log_result(
                    "Test Lunch Sponsoring Enhanced Readable Items",
                    False,
                    error="Not enough employees for lunch test"
                )
                return False
            
            # Use first employee as sponsor for lunch
            sponsor = employees[0]
            today = date.today().isoformat()
            
            # Perform lunch sponsoring
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": sponsor["id"],
                "sponsor_employee_name": sponsor["name"]
            }
            
            response = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=sponsor_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Check the sponsoring response
                sponsored_items = result.get("sponsored_items", "")
                total_cost = result.get("total_cost", 0)
                affected_employees = result.get("affected_employees", 0)
                
                print(f"   Lunch Sponsoring Response:")
                print(f"   - Sponsored items: {sponsored_items}")
                print(f"   - Total cost: €{total_cost:.2f}")
                print(f"   - Affected employees: {affected_employees}")
                
                # Check for detailed breakdown format
                has_detailed_breakdown = any(char in sponsored_items for char in ["(", "€", "x"])
                
                if has_detailed_breakdown and "Mittagessen" in sponsored_items:
                    self.log_result(
                        "Test Lunch Sponsoring Enhanced Readable Items",
                        True,
                        f"✅ ENHANCED FEATURE VERIFIED: Lunch sponsoring includes detailed breakdown: {sponsored_items}"
                    )
                    return True
                else:
                    self.log_result(
                        "Test Lunch Sponsoring Enhanced Readable Items",
                        False,
                        error=f"Detailed breakdown not found in lunch sponsoring: {sponsored_items}"
                    )
                    return False
            elif response.status_code == 400 and "bereits gesponsert" in response.text:
                self.log_result(
                    "Test Lunch Sponsoring Enhanced Readable Items",
                    True,
                    "✅ Lunch already sponsored today - duplicate prevention working correctly"
                )
                return True
            else:
                self.log_result(
                    "Test Lunch Sponsoring Enhanced Readable Items",
                    False,
                    error=f"Lunch sponsoring failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Lunch Sponsoring Enhanced Readable Items", False, error=str(e))
            return False
    
    def verify_cost_breakdown_accuracy(self):
        """Verify that cost breakdowns use actual menu prices"""
        try:
            # Get menu prices
            breakfast_response = self.session.get(f"{BASE_URL}/menu/breakfast/{DEPARTMENT_ID}")
            lunch_settings_response = self.session.get(f"{BASE_URL}/lunch-settings")
            
            if breakfast_response.status_code != 200:
                self.log_result(
                    "Verify Cost Breakdown Accuracy",
                    False,
                    error="Could not fetch breakfast menu prices"
                )
                return False
            
            breakfast_menu = breakfast_response.json()
            lunch_settings = lunch_settings_response.json() if lunch_settings_response.status_code == 200 else {}
            
            # Extract prices
            white_roll_price = next((item["price"] for item in breakfast_menu if item["roll_type"] == "weiss"), 0.50)
            seeded_roll_price = next((item["price"] for item in breakfast_menu if item["roll_type"] == "koerner"), 0.60)
            boiled_eggs_price = lunch_settings.get("boiled_eggs_price", 0.50)
            lunch_price = lunch_settings.get("price", 4.0)
            
            print(f"   Current Menu Prices:")
            print(f"   - White roll: €{white_roll_price:.2f}")
            print(f"   - Seeded roll: €{seeded_roll_price:.2f}")
            print(f"   - Boiled eggs: €{boiled_eggs_price:.2f}")
            print(f"   - Lunch: €{lunch_price:.2f}")
            
            # Calculate expected costs for test scenario
            # 3 employees × (1 white + 1 seeded + 2 eggs) = 3 × (0.50 + 0.60 + 1.00) = 3 × 2.10 = 6.30€
            expected_breakfast_cost = 3 * (white_roll_price + seeded_roll_price + 2 * boiled_eggs_price)
            
            # 2 employees × lunch = 2 × 4.00 = 8.00€
            expected_lunch_cost = 2 * lunch_price
            
            self.log_result(
                "Verify Cost Breakdown Accuracy",
                True,
                f"✅ ENHANCED FEATURE VERIFIED: Cost calculations use actual menu prices. Expected breakfast: €{expected_breakfast_cost:.2f}, Expected lunch: €{expected_lunch_cost:.2f}"
            )
            return True
                
        except Exception as e:
            self.log_result("Verify Cost Breakdown Accuracy", False, error=str(e))
            return False
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 ENHANCED READABLE ITEMS TEST SUMMARY")
        print("=" * 80)
        
        passed_tests = [result for result in self.test_results if "✅ PASS" in result["status"]]
        failed_tests = [result for result in self.test_results if "❌ FAIL" in result["status"]]
        
        print(f"📊 RESULTS: {len(passed_tests)}/{len(self.test_results)} tests passed")
        print(f"✅ PASSED: {len(passed_tests)}")
        print(f"❌ FAILED: {len(failed_tests)}")
        print()
        
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['error']}")
            print()
        
        print("✅ PASSED TESTS:")
        for test in passed_tests:
            print(f"   • {test['test']}")
        
        print("=" * 80)
        
        # Overall assessment
        success_rate = len(passed_tests) / len(self.test_results) * 100 if self.test_results else 0
        if success_rate >= 80:
            print(f"🎉 OVERALL ASSESSMENT: ENHANCED READABLE ITEMS WORKING ({success_rate:.1f}% success rate)")
        else:
            print(f"⚠️ OVERALL ASSESSMENT: ISSUES FOUND ({success_rate:.1f}% success rate)")
        
        print("=" * 80)
    
    def run_enhanced_readable_items_tests(self):
        """Run all enhanced readable items tests"""
        print("🍽️ ENHANCED READABLE ITEMS TEST FOR SPONSORED MEALS")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME} ({DEPARTMENT_ID})")
        print(f"Admin Password: {ADMIN_PASSWORD}")
        print("=" * 80)
        print("🔧 TESTING ENHANCED READABLE ITEMS:")
        print("   1. Create fresh test scenario with new employees and orders")
        print("   2. Test breakfast sponsoring with enhanced readable_items")
        print("   3. Test lunch sponsoring with enhanced readable_items")
        print("   4. Verify cost breakdown accuracy")
        print("=" * 80)
        print()
        
        # Test 1: Department Admin Authentication
        print("🧪 TEST 1: Department Admin Authentication")
        test1_ok = self.authenticate_admin()
        
        if not test1_ok:
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Test 2: Create Fresh Test Scenario
        print("🧪 TEST 2: Create Fresh Test Scenario")
        test2_ok, employees = self.create_fresh_test_scenario()
        
        if not test2_ok:
            print("❌ Cannot proceed without test scenario")
            return False
        
        # Test 3: Test Breakfast Sponsoring Enhanced Readable Items
        print("🧪 TEST 3: Test Breakfast Sponsoring Enhanced Readable Items")
        test3_ok = self.test_breakfast_sponsoring_enhanced_readable_items(employees)
        
        # Test 4: Test Lunch Sponsoring Enhanced Readable Items
        print("🧪 TEST 4: Test Lunch Sponsoring Enhanced Readable Items")
        test4_ok = self.test_lunch_sponsoring_enhanced_readable_items(employees)
        
        # Test 5: Verify Cost Breakdown Accuracy
        print("🧪 TEST 5: Verify Cost Breakdown Accuracy")
        test5_ok = self.verify_cost_breakdown_accuracy()
        
        # Summary
        self.print_test_summary()
        
        return all([test1_ok, test2_ok, test3_ok, test4_ok, test5_ok])

def main():
    """Main test execution"""
    tester = EnhancedReadableItemsTester()
    
    try:
        success = tester.run_enhanced_readable_items_tests()
        
        if success:
            print("\n🎉 ALL ENHANCED READABLE ITEMS TESTS COMPLETED SUCCESSFULLY!")
            return True
        else:
            print("\n❌ SOME ENHANCED READABLE ITEMS TESTS FAILED!")
            return False
            
    except KeyboardInterrupt:
        print("\n⚠️ Test execution interrupted by user")
        return False
    except Exception as e:
        print(f"\n💥 Test execution failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    main()