#!/usr/bin/env python3
"""
🔍 DEBUG SPONSORED ORDER UPDATES: Test order updates with debug logging

KRITISCHER DEBUG TEST:

1. **Create simple sponsoring scenario:**
   - Create Test1: breakfast order with Mittag
   - Create Test4: breakfast order
   - Test4 sponsors lunch for Test1

2. **Execute sponsoring with debug logging:**
   - Test4 sponsors lunch for Test1
   - Watch debug logs to see:
     - How many orders are being updated
     - What order IDs are being targeted
     - Whether updates are successful (matched_count, modified_count)

3. **Verify after sponsoring:**
   - Get Test1's individual profile
   - Check if Test1 now has is_sponsored=True, sponsored_meal_type="lunch"
   - Check if update actually worked

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Debug-Logs sollen zeigen ob und warum Order-Updates fehlschlagen!
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

# Test Configuration - EXACT from review request
DEPARTMENT_ID = "fw1abteilung1"  # Department 1 (1. Wachabteilung)
ADMIN_PASSWORD = "admin1"
DEPARTMENT_NAME = "1. Wachabteilung"

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

class SponsoredOrderUpdatesDebugTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test1_employee_id = None
        self.test4_employee_id = None
        self.test1_order_id = None
        self.test4_order_id = None
        
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
        """Authenticate as admin for Department 1"""
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
                print(f"✅ Created test employee '{name}': {employee_id}")
                return employee_id
            else:
                print(f"❌ Failed to create employee '{name}': {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating employee '{name}': {e}")
            return None
    
    def create_test1_breakfast_order_with_lunch(self, employee_id: str) -> Dict:
        """Create Test1's breakfast order with Mittag (lunch)"""
        try:
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 1 Brötchen (2 halves)
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["butter", "kaese"],
                    "has_lunch": True,  # MITTAG - this is what will be sponsored
                    "boiled_eggs": 1,
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                self.test1_order_id = order_id
                
                print(f"✅ Created Test1 breakfast order with Mittag: {order_id} (€{order['total_price']:.2f})")
                print(f"   - Brötchen: 1 (2 halves)")
                print(f"   - Eier: 1")
                print(f"   - Kaffee: Yes")
                print(f"   - Mittag: Yes ← THIS WILL BE SPONSORED BY Test4")
                
                return {
                    "order_id": order_id,
                    "total_price": order["total_price"],
                    "has_lunch": True
                }
            else:
                print(f"❌ Failed to create Test1 breakfast order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating Test1 breakfast order: {e}")
            return None
    
    def create_test4_breakfast_order(self, employee_id: str) -> Dict:
        """Create Test4's breakfast order (simple order)"""
        try:
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 2,
                    "seeded_halves": 0,
                    "toppings": ["butter", "schinken"],
                    "has_lunch": False,  # Test4 has no lunch
                    "boiled_eggs": 0,
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                self.test4_order_id = order_id
                
                print(f"✅ Created Test4 breakfast order: {order_id} (€{order['total_price']:.2f})")
                print(f"   - Brötchen: 1 (2 white halves)")
                print(f"   - Kaffee: Yes")
                print(f"   - Mittag: No")
                
                return {
                    "order_id": order_id,
                    "total_price": order["total_price"],
                    "has_lunch": False
                }
            else:
                print(f"❌ Failed to create Test4 breakfast order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating Test4 breakfast order: {e}")
            return None
    
    def test4_sponsors_lunch_for_test1(self, test4_employee_id: str) -> Dict:
        """🔍 CRITICAL: Test4 sponsors lunch for Test1 with debug logging"""
        try:
            today = self.get_berlin_date()
            
            print(f"\n🔍 DEBUG: Executing lunch sponsoring with debug logging")
            print(f"   - Sponsor: Test4 (ID: {test4_employee_id})")
            print(f"   - Target: All employees with lunch orders (including Test1)")
            print(f"   - Date: {today}")
            print(f"   - Meal Type: lunch")
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": test4_employee_id,
                "sponsor_employee_name": "Test4"
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test4 successfully sponsored lunch meals!")
                print(f"🔍 DEBUG RESPONSE: {json.dumps(result, indent=2)}")
                
                # Extract debug information
                affected_employees = result.get("affected_employees", 0)
                total_cost = result.get("total_cost", 0.0)
                
                print(f"🔍 DEBUG SUMMARY:")
                print(f"   - Affected employees: {affected_employees}")
                print(f"   - Total sponsoring cost: €{total_cost:.2f}")
                print(f"   - Expected: Test1 should be affected (has lunch order)")
                
                return result
            else:
                print(f"❌ Test4 failed to sponsor lunch meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error Test4 sponsoring lunch meals: {e}")
            return {"error": str(e)}
    
    def get_test1_individual_profile(self) -> Dict:
        """Get Test1's individual employee profile to verify sponsoring worked"""
        try:
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Find Test1 in the data
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    employee_orders = today_data.get("employee_orders", {})
                    
                    test1_data = None
                    for emp_name, emp_data in employee_orders.items():
                        if "Test1" in emp_name:
                            test1_data = emp_data
                            break
                    
                    if test1_data:
                        print(f"✅ Successfully retrieved Test1's individual profile")
                        return test1_data
                    else:
                        print(f"❌ Test1 not found in employee orders")
                        return {"error": "Test1 not found"}
                else:
                    print(f"❌ No history data found")
                    return {"error": "No history data"}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error getting Test1's profile: {e}")
            return {"error": str(e)}
    
    def verify_test1_sponsoring_status(self, test1_data: Dict) -> Dict:
        """🔍 CRITICAL: Verify if Test1 now has correct sponsoring status"""
        results = {
            "is_sponsored_found": False,
            "is_sponsored_value": None,
            "sponsored_meal_type_found": False,
            "sponsored_meal_type_value": None,
            "total_amount": 0.0,
            "expected_coffee_only_cost": False,
            "sponsoring_working": False
        }
        
        print(f"\n🔍 CRITICAL VERIFICATION: Test1's Sponsoring Status")
        print(f"Expected after lunch sponsoring:")
        print(f"   - is_sponsored: True")
        print(f"   - sponsored_meal_type: 'lunch' or contains 'lunch'")
        print(f"   - total_amount: Should be coffee-only cost (~€1.50)")
        
        # Check complete data structure
        print(f"\n🔍 Test1 Complete Data Structure:")
        for key, value in test1_data.items():
            print(f"   - {key}: {value}")
        
        # Check is_sponsored
        if "is_sponsored" in test1_data:
            results["is_sponsored_found"] = True
            results["is_sponsored_value"] = test1_data["is_sponsored"]
            print(f"\n✅ is_sponsored field found: {test1_data['is_sponsored']}")
            
            if test1_data["is_sponsored"] == True:
                print(f"✅ is_sponsored=True - CORRECT for sponsored employee")
            else:
                print(f"❌ is_sponsored={test1_data['is_sponsored']} - should be True")
        else:
            print(f"\n❌ is_sponsored field NOT found in Test1 data")
        
        # Check sponsored_meal_type
        if "sponsored_meal_type" in test1_data:
            results["sponsored_meal_type_found"] = True
            results["sponsored_meal_type_value"] = test1_data["sponsored_meal_type"]
            print(f"✅ sponsored_meal_type field found: {test1_data['sponsored_meal_type']}")
            
            if "lunch" in str(test1_data["sponsored_meal_type"]).lower():
                print(f"✅ sponsored_meal_type contains 'lunch' - CORRECT for lunch sponsoring")
            else:
                print(f"❌ sponsored_meal_type does NOT contain 'lunch': {test1_data['sponsored_meal_type']}")
        else:
            print(f"❌ sponsored_meal_type field NOT found in Test1 data")
        
        # Check total_amount (should be coffee-only cost after lunch sponsoring)
        total_amount = test1_data.get("total_amount", 0.0)
        results["total_amount"] = total_amount
        print(f"\n🔍 Total Amount Analysis:")
        print(f"   - Test1 total_amount: €{total_amount:.2f}")
        
        # Expected coffee-only cost should be around €1.00-€2.00
        if 0.50 <= total_amount <= 3.00:
            results["expected_coffee_only_cost"] = True
            print(f"✅ Total amount in expected coffee-only range (€0.50-€3.00)")
        else:
            print(f"❌ Total amount NOT in expected coffee-only range: €{total_amount:.2f}")
            print(f"   - This suggests lunch sponsoring did NOT work correctly")
        
        # Overall sponsoring working check
        sponsoring_working = (
            results["is_sponsored_found"] and 
            results["is_sponsored_value"] == True and
            results["sponsored_meal_type_found"] and
            "lunch" in str(results["sponsored_meal_type_value"]).lower() and
            results["expected_coffee_only_cost"]
        )
        
        results["sponsoring_working"] = sponsoring_working
        
        if sponsoring_working:
            print(f"\n✅ SPONSORING VERIFICATION: WORKING CORRECTLY!")
            print(f"   - Test1 is properly marked as sponsored for lunch")
            print(f"   - Total amount reflects coffee-only cost")
        else:
            print(f"\n❌ SPONSORING VERIFICATION: NOT WORKING CORRECTLY!")
            print(f"   - Test1 sponsoring status is incorrect or incomplete")
        
        return results
    
    def run_debug_sponsored_order_updates_test(self):
        """Run the debug sponsored order updates test as per review request"""
        print("🔍 DEBUG SPONSORED ORDER UPDATES: Test order updates with debug logging")
        print("=" * 80)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 1 (fw1abteilung1)")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Clean up existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create simple sponsoring scenario
        print(f"\n2️⃣ Creating Simple Sponsoring Scenario")
        print("- Create Test1: breakfast order with Mittag")
        print("- Create Test4: breakfast order")
        print("- Test4 sponsors lunch for Test1")
        
        # Create Test1
        self.test1_employee_id = self.create_test_employee("Test1")
        if not self.test1_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Test1")
            return False
        
        # Create Test4
        self.test4_employee_id = self.create_test_employee("Test4")
        if not self.test4_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Test4")
            return False
        
        # Step 3: Create Test1's breakfast order with Mittag
        print(f"\n3️⃣ Creating Test1's Breakfast Order with Mittag")
        test1_order = self.create_test1_breakfast_order_with_lunch(self.test1_employee_id)
        if not test1_order:
            print("❌ CRITICAL FAILURE: Cannot create Test1's order")
            return False
        
        # Step 4: Create Test4's breakfast order
        print(f"\n4️⃣ Creating Test4's Breakfast Order")
        test4_order = self.create_test4_breakfast_order(self.test4_employee_id)
        if not test4_order:
            print("❌ CRITICAL FAILURE: Cannot create Test4's order")
            return False
        
        # Step 5: Execute sponsoring with debug logging
        print(f"\n5️⃣ Execute Sponsoring with Debug Logging")
        print("🔍 CRITICAL: Test4 sponsors lunch for Test1")
        lunch_result = self.test4_sponsors_lunch_for_test1(self.test4_employee_id)
        if "error" in lunch_result:
            print(f"❌ Test4 lunch sponsoring failed: {lunch_result['error']}")
            return False
        
        # Step 6: Verify after sponsoring
        print(f"\n6️⃣ Verify After Sponsoring")
        print("🔍 CRITICAL: Get Test1's individual profile")
        test1_profile = self.get_test1_individual_profile()
        
        if "error" in test1_profile:
            print(f"❌ CRITICAL FAILURE: Cannot get Test1's profile: {test1_profile['error']}")
            return False
        
        # Step 7: Verify sponsoring status
        print(f"\n7️⃣ Verify Test1's Sponsoring Status")
        verification_results = self.verify_test1_sponsoring_status(test1_profile)
        
        # Final Results
        print(f"\n🏁 FINAL DEBUG TEST RESULTS:")
        
        success_criteria = [
            (verification_results["is_sponsored_found"], f"is_sponsored field found: {verification_results['is_sponsored_found']}"),
            (verification_results["is_sponsored_value"] == True, f"is_sponsored=True: {verification_results['is_sponsored_value']}"),
            (verification_results["sponsored_meal_type_found"], f"sponsored_meal_type field found: {verification_results['sponsored_meal_type_found']}"),
            ("lunch" in str(verification_results["sponsored_meal_type_value"]).lower() if verification_results["sponsored_meal_type_value"] else False, f"sponsored_meal_type contains 'lunch': {verification_results['sponsored_meal_type_value']}"),
            (verification_results["expected_coffee_only_cost"], f"Total amount in coffee-only range: €{verification_results['total_amount']:.2f}"),
            (verification_results["sponsoring_working"], f"Overall sponsoring working: {verification_results['sponsoring_working']}")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Overall Debug Test Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print debug summary
        print(f"\n🔍 DEBUG SUMMARY:")
        print(f"Test1 Employee ID: {self.test1_employee_id}")
        print(f"Test4 Employee ID: {self.test4_employee_id}")
        print(f"Test1 Order ID: {self.test1_order_id}")
        print(f"Test4 Order ID: {self.test4_order_id}")
        print(f"Test1 Final Total: €{verification_results['total_amount']:.2f}")
        
        if success_rate >= 80:
            print("\n✅ DEBUG SPONSORED ORDER UPDATES TEST: PASSED!")
            print("✅ Order updates are working correctly with proper debug logging")
            return True
        else:
            print("\n❌ DEBUG SPONSORED ORDER UPDATES TEST: FAILED!")
            print("❌ Order updates are NOT working correctly - debug logs show issues")
            return False

def main():
    """Main test execution"""
    test = SponsoredOrderUpdatesDebugTest()
    
    try:
        success = test.run_debug_sponsored_order_updates_test()
        
        if success:
            print(f"\n✅ DEBUG SPONSORED ORDER UPDATES: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ DEBUG SPONSORED ORDER UPDATES: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()