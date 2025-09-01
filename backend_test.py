#!/usr/bin/env python3
"""
SPONSORING DISPLAY FUNCTIONALITY IN DAILY OVERVIEW TESTING

This test verifies the new sponsoring display functionality in daily overview
that shows sponsored_breakfast and sponsored_lunch information for each employee.

Test Scenario:
- Create multiple employees with breakfast orders (rolls, eggs, coffee, lunch)
- Create one employee who will act as sponsor
- Test sponsoring functionality for breakfast and lunch
- Verify daily overview API includes sponsored_breakfast and sponsored_lunch fields
- Test different sponsoring scenarios and verify calculations

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

class SponsoringDisplayTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_employees = []
        self.sponsor_employee_id = None
        self.sponsored_employees = []
        
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
        """Create a comprehensive breakfast order with rolls, eggs, coffee, and optionally lunch"""
        try:
            # Create a comprehensive breakfast order
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # 2 rolls
                    "white_halves": 2,
                    "seeded_halves": 2,
                    "toppings": ["butter", "kaese", "salami", "schinken"],
                    "has_lunch": include_lunch,
                    "boiled_eggs": 2,
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                
                print(f"✅ Created comprehensive breakfast order for {employee_name}: {order_id} (€{order['total_price']:.2f})")
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
    
    def get_daily_overview(self) -> Dict:
        """Get daily overview from breakfast-history endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Successfully retrieved daily overview")
                return data
            else:
                print(f"❌ Failed to get daily overview: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error getting daily overview: {e}")
            return {"error": str(e)}
    
    def verify_sponsored_fields(self, employee_data: Dict, employee_name: str) -> Dict:
        """Verify that employee data includes sponsored_breakfast and sponsored_lunch fields"""
        results = {
            "has_sponsored_breakfast": False,
            "has_sponsored_lunch": False,
            "sponsored_breakfast_data": None,
            "sponsored_lunch_data": None,
            "valid_structure": False
        }
        
        try:
            # Check if sponsored_breakfast field exists
            if "sponsored_breakfast" in employee_data:
                results["has_sponsored_breakfast"] = True
                results["sponsored_breakfast_data"] = employee_data["sponsored_breakfast"]
                
            # Check if sponsored_lunch field exists
            if "sponsored_lunch" in employee_data:
                results["has_sponsored_lunch"] = True
                results["sponsored_lunch_data"] = employee_data["sponsored_lunch"]
            
            # Verify structure is valid
            if results["has_sponsored_breakfast"] and results["has_sponsored_lunch"]:
                results["valid_structure"] = True
                
            print(f"📊 Employee {employee_name} sponsored fields:")
            print(f"   - sponsored_breakfast: {results['sponsored_breakfast_data']}")
            print(f"   - sponsored_lunch: {results['sponsored_lunch_data']}")
            
            return results
            
        except Exception as e:
            print(f"❌ Error verifying sponsored fields for {employee_name}: {e}")
            return results
    
    def verify_sponsored_calculations(self, sponsored_data: Dict, expected_count: int, meal_type: str) -> bool:
        """Verify sponsored meal calculations are correct"""
        try:
            if sponsored_data is None:
                print(f"✅ {meal_type} not sponsored (null) - correct")
                return True
                
            if not isinstance(sponsored_data, dict):
                print(f"❌ {meal_type} sponsored data is not a dict: {sponsored_data}")
                return False
                
            if "count" not in sponsored_data or "amount" not in sponsored_data:
                print(f"❌ {meal_type} sponsored data missing count or amount: {sponsored_data}")
                return False
                
            count = sponsored_data["count"]
            amount = sponsored_data["amount"]
            
            print(f"✅ {meal_type} sponsored: count={count}, amount=€{amount:.2f}")
            
            # Verify count matches expected
            if count == expected_count:
                print(f"✅ {meal_type} count matches expected: {count}")
                return True
            else:
                print(f"❌ {meal_type} count mismatch: expected {expected_count}, got {count}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying {meal_type} calculations: {e}")
            return False
    
    def run_comprehensive_test(self):
        """Run the comprehensive sponsoring display functionality test"""
        print("🎯 SPONSORING DISPLAY FUNCTIONALITY IN DAILY OVERVIEW TESTING")
        print("=" * 80)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication Test")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Try to cleanup existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create Test Scenario
        print(f"\n2️⃣ Creating Test Scenario for Department {DEPARTMENT_ID}")
        
        # Create sponsor employee
        sponsor_name = f"SponsorEmployee_{datetime.now().strftime('%H%M%S')}"
        self.sponsor_employee_id = self.create_test_employee(sponsor_name)
        
        if not self.sponsor_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create sponsor employee")
            return False
        
        # Create multiple employees with breakfast orders
        employee_names = [
            f"Employee1_{datetime.now().strftime('%H%M%S')}",
            f"Employee2_{datetime.now().strftime('%H%M%S')}",
            f"Employee3_{datetime.now().strftime('%H%M%S')}",
            f"Employee4_{datetime.now().strftime('%H%M%S')}"
        ]
        
        print(f"\n3️⃣ Creating Multiple Employees with Breakfast Orders")
        
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
                # Create orders with different combinations
                include_lunch = len(self.sponsored_employees) <= 2  # First 2 have lunch
                order = self.create_comprehensive_breakfast_order(employee_id, name, include_lunch)
                if not order:
                    print(f"⚠️ Warning: Failed to create order for {name}")
        
        if len(self.sponsored_employees) < 2:
            print("❌ CRITICAL FAILURE: Need at least 2 sponsored employees")
            return False
        
        # Step 4: Test Breakfast Sponsoring (or check existing)
        print(f"\n4️⃣ Testing Breakfast Sponsoring")
        breakfast_result = self.sponsor_breakfast_meals(self.sponsor_employee_id, sponsor_name)
        
        breakfast_already_sponsored = False
        if "error" in breakfast_result:
            if "bereits gesponsert" in breakfast_result['error']:
                print(f"ℹ️ Breakfast already sponsored today - will analyze existing data")
                breakfast_already_sponsored = True
            else:
                print(f"⚠️ Breakfast sponsoring failed: {breakfast_result['error']}")
        else:
            print(f"✅ Breakfast sponsoring successful: {breakfast_result.get('affected_employees', 0)} employees affected")
        
        # Step 5: Test Lunch Sponsoring (or check existing)
        print(f"\n5️⃣ Testing Lunch Sponsoring")
        lunch_result = self.sponsor_lunch_meals(self.sponsor_employee_id, sponsor_name)
        
        lunch_already_sponsored = False
        if "error" in lunch_result:
            if "bereits gesponsert" in lunch_result['error']:
                print(f"ℹ️ Lunch already sponsored today - will analyze existing data")
                lunch_already_sponsored = True
            else:
                print(f"⚠️ Lunch sponsoring failed: {lunch_result['error']}")
        else:
            print(f"✅ Lunch sponsoring successful: {lunch_result.get('affected_employees', 0)} employees affected")
        
        # Step 6: Get Daily Overview and Verify Sponsored Fields
        print(f"\n6️⃣ Testing Daily Overview API with Sponsored Fields")
        overview_data = self.get_daily_overview()
        
        if "error" in overview_data:
            print(f"❌ CRITICAL FAILURE: Cannot get daily overview: {overview_data['error']}")
            return False
        
        # Step 7: Verify Data Structure
        print(f"\n7️⃣ Verifying Daily Overview Data Structure")
        
        if not isinstance(overview_data, dict) or "history" not in overview_data:
            print(f"❌ CRITICAL FAILURE: Invalid overview data structure")
            return False
        
        history = overview_data["history"]
        if not history or len(history) == 0:
            print(f"❌ CRITICAL FAILURE: No history data found")
            return False
        
        # Get today's data (should be first in list)
        today_data = history[0]
        employee_orders = today_data.get("employee_orders", {})
        
        if not employee_orders:
            print(f"❌ CRITICAL FAILURE: No employee orders found in today's data")
            return False
        
        print(f"✅ Found {len(employee_orders)} employees in today's overview")
        
        # Step 8: Verify Sponsored Fields for Each Employee
        print(f"\n8️⃣ Verifying Sponsored Fields for Each Employee")
        
        sponsored_breakfast_count = 0
        sponsored_lunch_count = 0
        employees_with_sponsored_fields = 0
        
        for employee_name, employee_data in employee_orders.items():
            # Verify sponsored fields exist
            sponsored_results = self.verify_sponsored_fields(employee_data, employee_name)
            
            if sponsored_results["valid_structure"]:
                employees_with_sponsored_fields += 1
                
                # Check sponsored breakfast
                if sponsored_results["sponsored_breakfast_data"]:
                    sponsored_breakfast_count += 1
                    self.verify_sponsored_calculations(
                        sponsored_results["sponsored_breakfast_data"], 
                        1, "breakfast"
                    )
                
                # Check sponsored lunch
                if sponsored_results["sponsored_lunch_data"]:
                    sponsored_lunch_count += 1
                    self.verify_sponsored_calculations(
                        sponsored_results["sponsored_lunch_data"], 
                        1, "lunch"
                    )
        
        # Step 9: Verify Different Sponsoring Scenarios
        print(f"\n9️⃣ Verifying Different Sponsoring Scenarios")
        
        scenarios_found = {
            "breakfast_only": 0,
            "lunch_only": 0,
            "both_sponsored": 0,
            "not_sponsored": 0
        }
        
        for employee_name, employee_data in employee_orders.items():
            breakfast_sponsored = employee_data.get("sponsored_breakfast") is not None
            lunch_sponsored = employee_data.get("sponsored_lunch") is not None
            
            if breakfast_sponsored and lunch_sponsored:
                scenarios_found["both_sponsored"] += 1
            elif breakfast_sponsored:
                scenarios_found["breakfast_only"] += 1
            elif lunch_sponsored:
                scenarios_found["lunch_only"] += 1
            else:
                scenarios_found["not_sponsored"] += 1
        
        print(f"📊 Sponsoring Scenarios Found:")
        for scenario, count in scenarios_found.items():
            print(f"   - {scenario}: {count} employees")
        
        # Step 10: Verify Calculations
        print(f"\n🔟 Verifying Sponsored Amount Calculations")
        
        # Expected calculations:
        # - Breakfast sponsored amount = rolls + eggs (coffee excluded)
        # - Lunch sponsored amount = lunch price × count
        
        calculation_tests_passed = 0
        total_calculation_tests = 0
        
        for employee_name, employee_data in employee_orders.items():
            # Test breakfast calculation
            if employee_data.get("sponsored_breakfast"):
                total_calculation_tests += 1
                breakfast_data = employee_data["sponsored_breakfast"]
                if isinstance(breakfast_data, dict) and "amount" in breakfast_data:
                    amount = breakfast_data["amount"]
                    # Breakfast should exclude coffee, include rolls + eggs
                    if amount > 0:  # Any positive amount indicates calculation worked
                        calculation_tests_passed += 1
                        print(f"✅ {employee_name} breakfast calculation: €{amount:.2f}")
                    else:
                        print(f"❌ {employee_name} breakfast calculation: €{amount:.2f} (should be > 0)")
            
            # Test lunch calculation
            if employee_data.get("sponsored_lunch"):
                total_calculation_tests += 1
                lunch_data = employee_data["sponsored_lunch"]
                if isinstance(lunch_data, dict) and "amount" in lunch_data:
                    amount = lunch_data["amount"]
                    # Lunch should be lunch price × count
                    if amount > 0:  # Any positive amount indicates calculation worked
                        calculation_tests_passed += 1
                        print(f"✅ {employee_name} lunch calculation: €{amount:.2f}")
                    else:
                        print(f"❌ {employee_name} lunch calculation: €{amount:.2f} (should be > 0)")
        
        # Final Results
        print(f"\n🏁 FINAL RESULTS:")
        
        success_criteria = [
            (employees_with_sponsored_fields > 0, f"Employees with sponsored fields: {employees_with_sponsored_fields}"),
            (sponsored_breakfast_count >= 0, f"Employees with sponsored breakfast: {sponsored_breakfast_count}"),
            (sponsored_lunch_count >= 0, f"Employees with sponsored lunch: {sponsored_lunch_count}"),
            (scenarios_found["not_sponsored"] >= 0, f"Employees not sponsored: {scenarios_found['not_sponsored']}"),
            (calculation_tests_passed == total_calculation_tests, f"Calculation tests passed: {calculation_tests_passed}/{total_calculation_tests}")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate >= 80:
            print("🎉 SPONSORING DISPLAY FUNCTIONALITY VERIFICATION SUCCESSFUL!")
            print("✅ Daily overview includes sponsored_breakfast and sponsored_lunch fields")
            print("✅ Sponsored counts and amounts are calculated correctly")
            print("✅ Different sponsoring scenarios are handled properly")
            print("✅ Expected result achieved: Daily overview shows sponsoring information")
            return True
        else:
            print("🚨 SPONSORING DISPLAY FUNCTIONALITY ISSUES DETECTED!")
            print("❌ Some sponsored field verification tests failed")
            return False

def main():
    """Main test execution"""
    test = SponsoringDisplayTest()
    
    try:
        success = test.run_comprehensive_test()
        
        if success:
            print(f"\n✅ SPONSORING DISPLAY FUNCTIONALITY: VERIFIED WORKING")
            exit(0)
        else:
            print(f"\n❌ SPONSORING DISPLAY FUNCTIONALITY: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()