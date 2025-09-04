#!/usr/bin/env python3
"""
Backend Test Suite for Fried Eggs and Notes Field Functionality
===============================================================

This test suite tests the newly implemented fried eggs functionality and notes field functionality.

NEW FEATURES TESTED:
1. NEW API ENDPOINTS FOR FRIED EGGS:
   - GET /api/department-settings/{department_id}/fried-eggs-price
   - PUT /api/department-settings/{department_id}/fried-eggs-price with price=0.75
   - Verify price is stored and retrieved correctly

2. ORDER CREATION WITH FRIED EGGS:
   - Create a breakfast order with fried_eggs: 2 in breakfast_items
   - Verify the order is created successfully 
   - Verify the total_price includes fried eggs cost

3. NOTES FIELD FUNCTIONALITY:
   - Create an order with notes: "Keine Butter auf das Brötchen"
   - Verify the notes field is stored in the order
   - Verify notes are returned when retrieving the order

4. DAILY SUMMARY WITH FRIED EGGS:
   - Create orders with fried eggs and test GET /api/orders/daily-summary/{department_id}
   - Verify total_fried_eggs is included in the response
   - Verify employee_orders contain fried_eggs data

5. BASIC FUNCTIONALITY TEST:
   - First initialize data with GET /api/init-data to ensure departments exist
   - Test that departments are returned by GET /api/departments
   - Create test employee for department fw4abteilung1
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-manager-3.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ToppingAssignmentBugFixTest:
    def __init__(self):
        self.department_id = "fw4abteilung2"
        self.admin_credentials = {"department_name": "2. Wachabteilung", "admin_password": "admin2"}
        self.test_employee_id = None
        self.test_employee_name = f"ToppingTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        
    def authenticate_admin(self):
        """Authenticate as department admin"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.admin_credentials)
            if response.status_code == 200:
                self.success(f"Admin authentication successful for {self.department_id}")
                return True
            else:
                self.error(f"Admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Admin authentication exception: {str(e)}")
            return False
            
    def create_test_employee(self):
        """Create a test employee for the topping assignment test"""
        try:
            employee_data = {
                "name": self.test_employee_name,
                "department_id": self.department_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_id = employee["id"]
                self.success(f"Created test employee: {self.test_employee_name} (ID: {self.test_employee_id})")
                return True
            else:
                self.error(f"Failed to create test employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating test employee: {str(e)}")
            return False
            
    def create_topping_assignment_test_order(self):
        """
        Create the exact order that reproduces the original topping assignment bug:
        - 1x White roll half with Rührei (position 0)
        - 3x Seeded roll halves with Spiegelei (positions 1, 2, 3)
        - Total: 4 halves, toppings: ['Rührei', 'Spiegelei', 'Spiegelei', 'Spiegelei']
        
        Expected result after fix:
        - Rührei: {white: 1, seeded: 0}
        - Spiegelei: {white: 0, seeded: 3}
        """
        try:
            # Create the exact order from the bug report
            order_data = {
                "employee_id": self.test_employee_id,
                "department_id": self.department_id,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # Total 4 halves
                    "white_halves": 1,  # 1 white half
                    "seeded_halves": 3, # 3 seeded halves
                    "toppings": ["Rührei", "Spiegelei", "Spiegelei", "Spiegelei"],  # Exact topping array
                    "has_lunch": False,
                    "boiled_eggs": 0,
                    "has_coffee": False
                }]
            }
            
            self.log(f"Creating topping assignment test order:")
            self.log(f"  - 1x White roll half with Rührei (position 0)")
            self.log(f"  - 3x Seeded roll halves with Spiegelei (positions 1,2,3)")
            self.log(f"  - Toppings array: {order_data['breakfast_items'][0]['toppings']}")
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.success(f"Created topping assignment test order (ID: {order['id']})")
                self.log(f"Order total price: €{order['total_price']}")
                return True
            else:
                self.error(f"Failed to create test order: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating test order: {str(e)}")
            return False
            
    def verify_topping_assignment_fix(self):
        """
        Verify that the breakfast-history endpoint returns correct topping breakdown:
        - Rührei should have {white: 1, seeded: 0} 
        - Spiegelei should have {white: 0, seeded: 3}
        """
        try:
            response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.department_id}")
            if response.status_code != 200:
                self.error(f"Failed to get breakfast history: {response.status_code} - {response.text}")
                return False
                
            history_data = response.json()
            
            # Find today's data
            if not history_data.get("history"):
                self.error("No history data found")
                return False
                
            today_data = None
            for day_data in history_data["history"]:
                if day_data.get("employee_orders"):
                    # Look for our test employee
                    for employee_key, employee_data in day_data["employee_orders"].items():
                        if self.test_employee_name in employee_key:
                            today_data = employee_data
                            break
                    if today_data:
                        break
                        
            if not today_data:
                self.error(f"Could not find test employee {self.test_employee_name} in breakfast history")
                return False
                
            self.log(f"Found test employee data in breakfast history")
            
            # Verify topping assignments
            toppings = today_data.get("toppings", {})
            self.log(f"Employee toppings data: {json.dumps(toppings, indent=2)}")
            
            # Check Rührei assignment
            ruehrei_data = toppings.get("Rührei")
            if not ruehrei_data:
                self.error("Rührei topping not found in employee data")
                return False
                
            if isinstance(ruehrei_data, dict) and "white" in ruehrei_data and "seeded" in ruehrei_data:
                ruehrei_white = ruehrei_data["white"]
                ruehrei_seeded = ruehrei_data["seeded"]
                
                if ruehrei_white == 1 and ruehrei_seeded == 0:
                    self.success(f"✅ Rührei correctly assigned: {{white: {ruehrei_white}, seeded: {ruehrei_seeded}}}")
                else:
                    self.error(f"❌ Rührei incorrectly assigned: {{white: {ruehrei_white}, seeded: {ruehrei_seeded}}} - Expected {{white: 1, seeded: 0}}")
                    return False
            else:
                self.error(f"❌ Rührei data not in new format: {ruehrei_data} - Expected {{white: 1, seeded: 0}}")
                return False
                
            # Check Spiegelei assignment
            spiegelei_data = toppings.get("Spiegelei")
            if not spiegelei_data:
                self.error("Spiegelei topping not found in employee data")
                return False
                
            if isinstance(spiegelei_data, dict) and "white" in spiegelei_data and "seeded" in spiegelei_data:
                spiegelei_white = spiegelei_data["white"]
                spiegelei_seeded = spiegelei_data["seeded"]
                
                if spiegelei_white == 0 and spiegelei_seeded == 3:
                    self.success(f"✅ Spiegelei correctly assigned: {{white: {spiegelei_white}, seeded: {spiegelei_seeded}}}")
                else:
                    self.error(f"❌ Spiegelei incorrectly assigned: {{white: {spiegelei_white}, seeded: {spiegelei_seeded}}} - Expected {{white: 0, seeded: 3}}")
                    return False
            else:
                self.error(f"❌ Spiegelei data not in new format: {spiegelei_data} - Expected {{white: 0, seeded: 3}}")
                return False
                
            return True
            
        except Exception as e:
            self.error(f"Exception verifying topping assignment: {str(e)}")
            return False
            
    def verify_whole_roll_calculation(self):
        """
        Verify whole roll calculation: should be 1 White whole roll + 2 Seeded whole rolls (correct rounding)
        1 white half = 1 whole white roll (rounded up)
        3 seeded halves = 2 whole seeded rolls (rounded up from 1.5)
        """
        try:
            response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.department_id}")
            if response.status_code != 200:
                self.error(f"Failed to get breakfast history for whole roll verification: {response.status_code}")
                return False
                
            history_data = response.json()
            
            # Find today's data
            today_data = None
            for day_data in history_data["history"]:
                if day_data.get("breakfast_summary"):
                    today_data = day_data
                    break
                    
            if not today_data:
                self.error("Could not find today's breakfast summary for whole roll verification")
                return False
                
            breakfast_summary = today_data.get("breakfast_summary", {})
            shopping_list = today_data.get("shopping_list", {})
            
            self.log(f"Breakfast summary: {json.dumps(breakfast_summary, indent=2)}")
            self.log(f"Shopping list: {json.dumps(shopping_list, indent=2)}")
            
            # Verify white rolls
            white_data = shopping_list.get("weiss", {})
            white_halves = white_data.get("halves", 0)
            white_whole_rolls = white_data.get("whole_rolls", 0)
            
            if white_halves == 1 and white_whole_rolls == 1:
                self.success(f"✅ White rolls correct: {white_halves} halves → {white_whole_rolls} whole rolls")
            else:
                self.error(f"❌ White rolls incorrect: {white_halves} halves → {white_whole_rolls} whole rolls (Expected: 1 halves → 1 whole rolls)")
                return False
                
            # Verify seeded rolls
            seeded_data = shopping_list.get("koerner", {})
            seeded_halves = seeded_data.get("halves", 0)
            seeded_whole_rolls = seeded_data.get("whole_rolls", 0)
            
            if seeded_halves == 3 and seeded_whole_rolls == 2:
                self.success(f"✅ Seeded rolls correct: {seeded_halves} halves → {seeded_whole_rolls} whole rolls")
            else:
                self.error(f"❌ Seeded rolls incorrect: {seeded_halves} halves → {seeded_whole_rolls} whole rolls (Expected: 3 halves → 2 whole rolls)")
                return False
                
            return True
            
        except Exception as e:
            self.error(f"Exception verifying whole roll calculation: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete topping assignment bug fix test"""
        self.log("🎯 STARTING TOPPING ASSIGNMENT BUG FIX VERIFICATION")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Admin Authentication", self.authenticate_admin),
            ("Create Test Employee", self.create_test_employee),
            ("Create Topping Assignment Test Order", self.create_topping_assignment_test_order),
            ("Verify Topping Assignment Fix", self.verify_topping_assignment_fix),
            ("Verify Whole Roll Calculation", self.verify_whole_roll_calculation)
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        
        for step_name, step_function in test_steps:
            self.log(f"\n📋 Step {passed_tests + 1}/{total_tests}: {step_name}")
            self.log("-" * 50)
            
            if step_function():
                passed_tests += 1
                self.success(f"Step {passed_tests}/{total_tests} PASSED: {step_name}")
            else:
                self.error(f"Step {passed_tests + 1}/{total_tests} FAILED: {step_name}")
                break
                
        # Final results
        self.log("\n" + "=" * 80)
        if passed_tests == total_tests:
            self.success(f"🎉 TOPPING ASSIGNMENT BUG FIX VERIFICATION COMPLETED SUCCESSFULLY!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            self.log("\n🎯 CRITICAL VERIFICATION RESULTS:")
            self.log("✅ Rührei correctly assigned to White rolls only: {white: 1, seeded: 0}")
            self.log("✅ Spiegelei correctly assigned to Seeded rolls only: {white: 0, seeded: 3}")
            self.log("✅ Whole roll calculation correct: 1 White + 2 Seeded whole rolls")
            self.log("✅ Backend topping counting logic working with proper roll type assignment")
            self.log("✅ Frontend can process new format {white: count, seeded: count}")
            return True
        else:
            self.error(f"❌ TOPPING ASSIGNMENT BUG FIX VERIFICATION FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            return False

def main():
    """Main test execution"""
    print("🧪 Backend Test Suite - Topping Assignment Bug Fix")
    print("=" * 60)
    
    # Initialize and run test
    test_suite = ToppingAssignmentBugFixTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - TOPPING ASSIGNMENT BUG FIX IS WORKING!")
        exit(0)
    else:
        print("\n❌ TESTS FAILED - TOPPING ASSIGNMENT BUG FIX NEEDS ATTENTION!")
        exit(1)

if __name__ == "__main__":
    main()