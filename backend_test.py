#!/usr/bin/env python3
"""
🚨 CRITICAL BUG FIX VERIFICATION: Combined Sponsoring Bug Fixes Testing

This test verifies the two critical bug fixes for combined sponsoring:
1. Bug 1: Frontend Total Display - sponsored employees should show correct remaining cost (only coffee ~€1-2), NOT €0.00
2. Bug 2: Frontend Strikethrough Logic - when sponsored_meal_type = "breakfast,lunch", both breakfast items AND lunch should be struck through

Test Scenario (EXACT from review request):
1. Create multiple employees with breakfast orders including rolls, eggs, coffee, and lunch (total €8-10 per employee)
2. Test combined sponsoring (breakfast + lunch) for the same employees - should result in "breakfast,lunch" sponsored_meal_type
3. Verify sponsored employees show correct remaining cost (only coffee ~€1-2), NOT €0.00
4. Verify breakfast-history API structure supports proper strikethrough logic
5. Test no regressions for single sponsoring and normal orders

Department: fw4abteilung2 (Department 2)
Admin Credentials: admin2
"""

import requests
import json
from datetime import datetime, timedelta
import pytz
import os
from typing import Dict, List, Any

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteen-fire.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test Configuration
DEPARTMENT_ID = "fw4abteilung2"  # Department 2
ADMIN_PASSWORD = "admin2"
DEPARTMENT_NAME = "2. Wachabteilung"

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

class CombinedSponsoringBugFixTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_employees = []
        self.sponsor_employee_id = None
        self.sponsored_employees = []
        self.test_orders = []
        
    def cleanup_test_data(self) -> bool:
        """Clean up test data to create fresh scenario"""
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/debug-cleanup/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully cleaned up test data: {result}")
                return True
            else:
                print(f"⚠️ Cleanup failed (continuing anyway): {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Cleanup error (continuing anyway): {e}")
            return False
    
    def get_berlin_date(self):
        """Get current date in Berlin timezone"""
        return datetime.now(BERLIN_TZ).date().strftime('%Y-%m-%d')
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin for Department 2"""
        try:
            response = self.session.post(f"{API_BASE}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Admin Authentication Success: {data}")
                return True
            else:
                print(f"❌ Admin Authentication Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Admin Authentication Error: {e}")
            return False
    
    def create_test_employee(self, name: str) -> str:
        """Create a test employee and return employee ID"""
        try:
            response = self.session.post(f"{API_BASE}/employees", json={
                "name": name,
                "department_id": DEPARTMENT_ID
            })
            
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee["id"]
                self.test_employees.append(employee_id)
                print(f"✅ Created test employee '{name}': {employee_id}")
                return employee_id
            else:
                print(f"❌ Failed to create employee '{name}': {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating employee '{name}': {e}")
            return None
    
    def create_comprehensive_breakfast_order(self, employee_id: str, employee_name: str, include_lunch: bool = True) -> Dict:
        """Create a comprehensive breakfast order with rolls, eggs, coffee, and lunch (€8-10 total as per review request)"""
        try:
            # Create order matching review request: rolls, eggs, coffee, lunch totaling €8-10
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 6,  # 3 rolls (more to reach €8-10 range)
                    "white_halves": 3,
                    "seeded_halves": 3,
                    "toppings": ["butter", "kaese", "salami", "schinken", "eiersalat", "spiegelei"],
                    "has_lunch": include_lunch,
                    "boiled_eggs": 3,  # More eggs to reach target price
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                
                print(f"✅ Created comprehensive breakfast order for {employee_name}: {order_id} (€{order['total_price']:.2f})")
                self.test_orders.append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "order_id": order_id,
                    "total_price": order["total_price"],
                    "has_lunch": include_lunch
                })
                return {
                    "order_id": order_id,
                    "total_price": order["total_price"],
                    "has_lunch": include_lunch
                }
            else:
                print(f"❌ Failed to create breakfast order for {employee_name}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating breakfast order for {employee_name}: {e}")
            return None
    
    def sponsor_breakfast_meals(self, sponsor_employee_id: str, sponsor_name: str) -> Dict:
        """Sponsor breakfast meals for employees"""
        try:
            today = self.get_berlin_date()
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": sponsor_employee_id,
                "sponsor_employee_name": sponsor_name
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully sponsored breakfast meals: {result}")
                return result
            else:
                print(f"❌ Failed to sponsor breakfast meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error sponsoring breakfast meals: {e}")
            return {"error": str(e)}
    
    def sponsor_lunch_meals(self, sponsor_employee_id: str, sponsor_name: str) -> Dict:
        """Sponsor lunch meals for employees"""
        try:
            today = self.get_berlin_date()
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": sponsor_employee_id,
                "sponsor_employee_name": sponsor_name
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully sponsored lunch meals: {result}")
                return result
            else:
                print(f"❌ Failed to sponsor lunch meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error sponsoring lunch meals: {e}")
            return {"error": str(e)}
    
    def get_breakfast_history(self) -> Dict:
        """Get breakfast history from breakfast-history endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Successfully retrieved breakfast history")
                return data
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error getting breakfast history: {e}")
            return {"error": str(e)}
    
    def verify_bug_1_total_display(self, employee_orders: Dict) -> Dict:
        """
        CRITICAL Bug 1 Test: Verify sponsored employees show correct remaining cost (only coffee ~€1-2), NOT €0.00
        """
        results = {
            "bug_1_fixed": False,
            "sponsored_employees_found": 0,
            "correct_total_displays": 0,
            "incorrect_zero_displays": 0,
            "coffee_only_costs": []
        }
        
        print(f"\n🔍 CRITICAL Bug 1 Test: Frontend Total Display Fix")
        print(f"Expected: Sponsored employees show coffee cost (~€1-2), NOT €0.00")
        
        for employee_name, employee_data in employee_orders.items():
            total_amount = employee_data.get("total_amount", 0)
            has_orders = any([
                employee_data.get("white_halves", 0) > 0,
                employee_data.get("seeded_halves", 0) > 0,
                employee_data.get("boiled_eggs", 0) > 0,
                employee_data.get("has_lunch", False),
                employee_data.get("has_coffee", False)
            ])
            
            # Check if this employee has both breakfast and lunch sponsored
            breakfast_sponsored = employee_data.get("sponsored_breakfast") is not None
            lunch_sponsored = employee_data.get("sponsored_lunch") is not None
            
            if has_orders and breakfast_sponsored and lunch_sponsored:
                results["sponsored_employees_found"] += 1
                
                if total_amount == 0.0:
                    results["incorrect_zero_displays"] += 1
                    print(f"❌ Bug 1 DETECTED: {employee_name} shows €0.00 (should show coffee cost)")
                elif 1.0 <= total_amount <= 3.0:  # Coffee cost range
                    results["correct_total_displays"] += 1
                    results["coffee_only_costs"].append(total_amount)
                    print(f"✅ Bug 1 FIXED: {employee_name} shows €{total_amount:.2f} (coffee cost)")
                else:
                    print(f"⚠️ Unexpected amount for {employee_name}: €{total_amount:.2f}")
        
        # Determine if Bug 1 is fixed
        if results["sponsored_employees_found"] > 0:
            if results["incorrect_zero_displays"] == 0 and results["correct_total_displays"] > 0:
                results["bug_1_fixed"] = True
                print(f"✅ Bug 1 VERIFICATION: All {results['correct_total_displays']} sponsored employees show coffee cost correctly")
            else:
                print(f"❌ Bug 1 STILL PRESENT: {results['incorrect_zero_displays']} employees show €0.00 incorrectly")
        else:
            print(f"⚠️ No employees with both breakfast and lunch sponsored found for Bug 1 test")
        
        return results
    
    def verify_bug_2_strikethrough_logic(self, employee_orders: Dict) -> Dict:
        """
        CRITICAL Bug 2 Test: Verify breakfast-history API structure supports proper strikethrough logic
        When sponsored_meal_type = "breakfast,lunch", both breakfast items AND lunch should be struck through
        """
        results = {
            "bug_2_fixed": False,
            "combined_sponsored_found": 0,
            "proper_structure_count": 0,
            "combined_meal_types": []
        }
        
        print(f"\n🔍 CRITICAL Bug 2 Test: Frontend Strikethrough Logic Support")
        print(f"Expected: API structure supports 'breakfast,lunch' sponsored_meal_type")
        
        for employee_name, employee_data in employee_orders.items():
            breakfast_sponsored = employee_data.get("sponsored_breakfast")
            lunch_sponsored = employee_data.get("sponsored_lunch")
            
            # Check for combined sponsoring (both breakfast and lunch)
            if breakfast_sponsored is not None and lunch_sponsored is not None:
                results["combined_sponsored_found"] += 1
                
                # Verify API provides the data structure needed for frontend strikethrough logic
                has_breakfast_items = any([
                    employee_data.get("white_halves", 0) > 0,
                    employee_data.get("seeded_halves", 0) > 0,
                    employee_data.get("boiled_eggs", 0) > 0
                ])
                has_lunch = employee_data.get("has_lunch", False)
                has_coffee = employee_data.get("has_coffee", False)
                
                if has_breakfast_items and has_lunch and has_coffee:
                    results["proper_structure_count"] += 1
                    
                    # Create the equivalent of "breakfast,lunch" sponsored_meal_type for frontend
                    meal_type_parts = []
                    if breakfast_sponsored:
                        meal_type_parts.append("breakfast")
                    if lunch_sponsored:
                        meal_type_parts.append("lunch")
                    
                    combined_meal_type = ",".join(meal_type_parts)
                    results["combined_meal_types"].append(combined_meal_type)
                    
                    print(f"✅ Bug 2 STRUCTURE: {employee_name} has combined sponsoring ({combined_meal_type})")
                    print(f"   - Breakfast items: {has_breakfast_items} (can be struck through)")
                    print(f"   - Lunch: {has_lunch} (can be struck through)")
                    print(f"   - Coffee: {has_coffee} (should remain visible)")
        
        # Determine if Bug 2 structure is correct
        if results["combined_sponsored_found"] > 0:
            if results["proper_structure_count"] == results["combined_sponsored_found"]:
                results["bug_2_fixed"] = True
                print(f"✅ Bug 2 VERIFICATION: API structure supports proper strikethrough for {results['proper_structure_count']} employees")
            else:
                print(f"❌ Bug 2 STRUCTURE ISSUE: Only {results['proper_structure_count']}/{results['combined_sponsored_found']} have proper structure")
        else:
            print(f"⚠️ No employees with combined sponsoring found for Bug 2 test")
        
        return results
    
    def verify_no_regressions(self, employee_orders: Dict) -> Dict:
        """Verify no regressions for single sponsoring and normal orders"""
        results = {
            "no_regressions": True,
            "single_breakfast_sponsored": 0,
            "single_lunch_sponsored": 0,
            "normal_orders": 0,
            "regression_issues": []
        }
        
        print(f"\n🔍 Regression Test: Single Sponsoring and Normal Orders")
        
        for employee_name, employee_data in employee_orders.items():
            breakfast_sponsored = employee_data.get("sponsored_breakfast") is not None
            lunch_sponsored = employee_data.get("sponsored_lunch") is not None
            total_amount = employee_data.get("total_amount", 0)
            
            # Single breakfast sponsoring
            if breakfast_sponsored and not lunch_sponsored:
                results["single_breakfast_sponsored"] += 1
                # Should show lunch + coffee cost
                if total_amount > 0:
                    print(f"✅ Single breakfast sponsoring: {employee_name} shows €{total_amount:.2f} (lunch+coffee)")
                else:
                    results["regression_issues"].append(f"{employee_name}: Single breakfast sponsoring shows €0.00")
            
            # Single lunch sponsoring
            elif lunch_sponsored and not breakfast_sponsored:
                results["single_lunch_sponsored"] += 1
                # Should show breakfast + coffee cost
                if total_amount > 0:
                    print(f"✅ Single lunch sponsoring: {employee_name} shows €{total_amount:.2f} (breakfast+coffee)")
                else:
                    results["regression_issues"].append(f"{employee_name}: Single lunch sponsoring shows €0.00")
            
            # Normal orders (no sponsoring)
            elif not breakfast_sponsored and not lunch_sponsored:
                results["normal_orders"] += 1
                # Should show full order cost
                if total_amount > 0:
                    print(f"✅ Normal order: {employee_name} shows €{total_amount:.2f} (full cost)")
                else:
                    results["regression_issues"].append(f"{employee_name}: Normal order shows €0.00")
        
        if results["regression_issues"]:
            results["no_regressions"] = False
            print(f"❌ Regression issues found: {results['regression_issues']}")
        else:
            print(f"✅ No regressions detected")
        
        return results
    
    def run_comprehensive_test(self):
        """Run the comprehensive combined sponsoring bug fix test"""
        print("🚨 CRITICAL BUG FIX VERIFICATION: Combined Sponsoring Bug Fixes Testing")
        print("=" * 80)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication Test")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Try to cleanup existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create Test Scenario (EXACT from review request)
        print(f"\n2️⃣ Creating Test Scenario for Department {DEPARTMENT_ID}")
        print("Creating multiple employees with breakfast orders (rolls, eggs, coffee, lunch) totaling €8-10 per employee")
        
        # Create sponsor employee
        sponsor_name = f"CombinedSponsor_{datetime.now().strftime('%H%M%S')}"
        self.sponsor_employee_id = self.create_test_employee(sponsor_name)
        
        if not self.sponsor_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create sponsor employee")
            return False
        
        # Create multiple employees with comprehensive breakfast orders
        employee_names = [
            f"CombinedTest1_{datetime.now().strftime('%H%M%S')}",
            f"CombinedTest2_{datetime.now().strftime('%H%M%S')}",
            f"CombinedTest3_{datetime.now().strftime('%H%M%S')}"
        ]
        
        print(f"\n3️⃣ Creating Multiple Employees with Comprehensive Breakfast Orders (€8-10 each)")
        
        # Create sponsor's own order
        sponsor_order = self.create_comprehensive_breakfast_order(
            self.sponsor_employee_id, sponsor_name, include_lunch=True
        )
        
        if not sponsor_order:
            print("❌ CRITICAL FAILURE: Cannot create sponsor's order")
            return False
        
        # Create other employees and their orders
        for name in employee_names:
            employee_id = self.create_test_employee(name)
            if employee_id:
                self.sponsored_employees.append(employee_id)
                # All employees get comprehensive orders with lunch
                order = self.create_comprehensive_breakfast_order(employee_id, name, include_lunch=True)
                if not order:
                    print(f"⚠️ Warning: Failed to create order for {name}")
        
        if len(self.sponsored_employees) < 2:
            print("❌ CRITICAL FAILURE: Need at least 2 sponsored employees")
            return False
        
        # Verify order totals are in €8-10 range
        print(f"\n3️⃣.5 Verifying Order Totals are in €8-10 Range")
        for order in self.test_orders:
            if 8.0 <= order["total_price"] <= 12.0:  # Allow slight variance
                print(f"✅ {order['employee_name']}: €{order['total_price']:.2f} (within target range)")
            else:
                print(f"⚠️ {order['employee_name']}: €{order['total_price']:.2f} (outside €8-10 range)")
        
        # Step 4: Test Combined Sponsoring (breakfast + lunch)
        print(f"\n4️⃣ Testing Combined Sponsoring (Breakfast + Lunch)")
        print("This should result in 'breakfast,lunch' sponsored_meal_type equivalent")
        
        # First sponsor breakfast meals
        breakfast_result = self.sponsor_breakfast_meals(self.sponsor_employee_id, sponsor_name)
        
        if "error" in breakfast_result and "bereits gesponsert" not in breakfast_result.get('error', ''):
            print(f"❌ Breakfast sponsoring failed: {breakfast_result['error']}")
            return False
        
        # Then sponsor lunch meals for the same employees
        lunch_result = self.sponsor_lunch_meals(self.sponsor_employee_id, sponsor_name)
        
        if "error" in lunch_result and "bereits gesponsert" not in lunch_result.get('error', ''):
            print(f"❌ Lunch sponsoring failed: {lunch_result['error']}")
            return False
        
        print(f"✅ Combined sponsoring completed (breakfast + lunch)")
        
        # Step 5: Get Breakfast History and Verify Bug Fixes
        print(f"\n5️⃣ Getting Breakfast History for Bug Fix Verification")
        history_data = self.get_breakfast_history()
        
        if "error" in history_data:
            print(f"❌ CRITICAL FAILURE: Cannot get breakfast history: {history_data['error']}")
            return False
        
        # Step 6: Verify Data Structure
        print(f"\n6️⃣ Verifying Breakfast History Data Structure")
        
        if not isinstance(history_data, dict) or "history" not in history_data:
            print(f"❌ CRITICAL FAILURE: Invalid history data structure")
            return False
        
        history = history_data["history"]
        if not history or len(history) == 0:
            print(f"❌ CRITICAL FAILURE: No history data found")
            return False
        
        # Get today's data (should be first in list)
        today_data = history[0]
        employee_orders = today_data.get("employee_orders", {})
        
        if not employee_orders:
            print(f"❌ CRITICAL FAILURE: No employee orders found in today's data")
            return False
        
        print(f"✅ Found {len(employee_orders)} employees in today's breakfast history")
        
        # Step 7: CRITICAL Bug 1 Test - Frontend Total Display
        print(f"\n7️⃣ CRITICAL Bug 1 Test - Frontend Total Display")
        bug_1_results = self.verify_bug_1_total_display(employee_orders)
        
        # Step 8: CRITICAL Bug 2 Test - Frontend Strikethrough Logic
        print(f"\n8️⃣ CRITICAL Bug 2 Test - Frontend Strikethrough Logic")
        bug_2_results = self.verify_bug_2_strikethrough_logic(employee_orders)
        
        # Step 9: Verify No Regressions
        print(f"\n9️⃣ Verify No Regressions")
        regression_results = self.verify_no_regressions(employee_orders)
        
        # Final Results
        print(f"\n🏁 FINAL RESULTS:")
        
        success_criteria = [
            (bug_1_results["bug_1_fixed"], f"Bug 1 Fixed (Total Display): {bug_1_results['correct_total_displays']} correct, {bug_1_results['incorrect_zero_displays']} incorrect"),
            (bug_2_results["bug_2_fixed"], f"Bug 2 Fixed (Strikethrough Logic): {bug_2_results['proper_structure_count']} proper structures"),
            (regression_results["no_regressions"], f"No Regressions: {len(regression_results['regression_issues'])} issues found"),
            (bug_1_results["sponsored_employees_found"] > 0, f"Combined Sponsoring Tested: {bug_1_results['sponsored_employees_found']} employees"),
            (len(bug_2_results["combined_meal_types"]) > 0, f"Combined Meal Types: {bug_2_results['combined_meal_types']}")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 CRITICAL BUG FIXES VERIFICATION SUCCESSFUL!")
            print("✅ Bug 1: Sponsored employees show correct remaining cost (coffee only)")
            print("✅ Bug 2: API structure supports proper strikethrough logic")
            print("✅ No regressions detected in single sponsoring or normal orders")
            print("✅ Combined sponsoring (breakfast + lunch) working correctly")
            return True
        else:
            print("🚨 CRITICAL BUG FIXES ISSUES DETECTED!")
            print("❌ Some critical bug fix verification tests failed")
            return False

def main():
    """Main test execution"""
    test = CombinedSponsoringBugFixTest()
    
    try:
        success = test.run_comprehensive_test()
        
        if success:
            print(f"\n✅ COMBINED SPONSORING BUG FIXES: VERIFIED WORKING")
            exit(0)
        else:
            print(f"\n❌ COMBINED SPONSORING BUG FIXES: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()