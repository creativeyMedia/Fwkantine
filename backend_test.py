#!/usr/bin/env python3
"""
🔍 FINAL CORRECTED APPROACH: Test simplified sponsor order lookup

KRITISCHER TEST MIT VEREINFACHTEM ANSATZ:

1. **Create exact User scenario:**
   - Mit1, Mit2, Mit3, Mit4 mit breakfast orders
   - Mit1 sponsert Frühstück für andere (creates sponsor order for Mit1)
   - Mit4 sponsert Mittag für Mit1 (creates sponsor order for Mit4)

2. **TEST SIMPLIFIED LOGIC:**
   - Logic now looks for is_sponsor_order=True orders belonging to each employee
   - Mit1 should have sponsor order with breakfast sponsoring info
   - Mit4 should have sponsor order with lunch sponsoring info
   - Mit2, Mit3 should have no sponsor orders

3. **VERIFY SPONSOR ORDER STRUCTURE:**
   - Check what fields are actually stored in sponsor orders
   - Verify sponsor_employee_count, sponsor_total_cost, sponsored_meal_type fields
   - Ensure the simplified approach extracts correct data

4. **FINAL VERIFICATION:**
   - Mit1 breakfast-history should show: sponsored_breakfast: {count: 3, amount: X.XX}
   - Mit4 breakfast-history should show: sponsored_lunch: {count: 1, amount: X.XX}
   - No cross-contamination between employees

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Test the corrected simplified approach that looks for sponsor orders instead of sponsored orders!
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

class SponsoringAssignmentVerification:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.mit1_employee_id = None
        self.mit2_employee_id = None
        self.mit3_employee_id = None
        self.mit4_employee_id = None
        self.employee_orders = {}
        
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
    
    def create_breakfast_order_with_lunch(self, employee_id: str, name: str) -> Dict:
        """Create breakfast order with lunch"""
        try:
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # 2 Brötchen (4 halves)
                    "white_halves": 2,
                    "seeded_halves": 2,
                    "toppings": ["butter", "kaese", "schinken", "salami"],
                    "has_lunch": True,  # MITTAG
                    "boiled_eggs": 2,
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                
                print(f"✅ Created {name} breakfast order with Mittag: {order_id} (€{order['total_price']:.2f})")
                print(f"   - Brötchen: 2 (4 halves)")
                print(f"   - Eier: 2")
                print(f"   - Kaffee: Yes")
                print(f"   - Mittag: Yes")
                
                return {
                    "order_id": order_id,
                    "total_price": order["total_price"],
                    "has_lunch": True
                }
            else:
                print(f"❌ Failed to create {name} breakfast order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating {name} breakfast order: {e}")
            return None
    
    def create_breakfast_order_no_lunch(self, employee_id: str, name: str) -> Dict:
        """Create breakfast order without lunch"""
        try:
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["butter", "kaese"],
                    "has_lunch": False,  # No lunch
                    "boiled_eggs": 1,
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                
                print(f"✅ Created {name} breakfast order: {order_id} (€{order['total_price']:.2f})")
                print(f"   - Brötchen: 1 (2 halves)")
                print(f"   - Eier: 1")
                print(f"   - Kaffee: Yes")
                print(f"   - Mittag: No")
                
                return {
                    "order_id": order_id,
                    "total_price": order["total_price"],
                    "has_lunch": False
                }
            else:
                print(f"❌ Failed to create {name} breakfast order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating {name} breakfast order: {e}")
            return None
    
    def mit1_sponsors_breakfast_for_others(self, mit1_employee_id: str) -> Dict:
        """Mit1 sponsors breakfast for Mit2, Mit3, Mit4"""
        try:
            today = self.get_berlin_date()
            
            print(f"\n🔍 CRITICAL TEST: Mit1 sponsors breakfast for others")
            print(f"   - Sponsor: Mit1 (ID: {mit1_employee_id})")
            print(f"   - Target: All employees with breakfast orders (Mit2, Mit3, Mit4)")
            print(f"   - Date: {today}")
            print(f"   - Meal Type: breakfast")
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": mit1_employee_id,
                "sponsor_employee_name": "Mit1"
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Mit1 successfully sponsored breakfast meals!")
                print(f"🔍 BREAKFAST SPONSORING RESPONSE: {json.dumps(result, indent=2)}")
                
                affected_employees = result.get("affected_employees", 0)
                total_cost = result.get("total_cost", 0.0)
                
                print(f"🔍 BREAKFAST SPONSORING SUMMARY:")
                print(f"   - Affected employees: {affected_employees}")
                print(f"   - Total sponsoring cost: €{total_cost:.2f}")
                print(f"   - Expected: Mit2, Mit3, Mit4 should be affected (3 employees)")
                
                return result
            else:
                print(f"❌ Mit1 failed to sponsor breakfast meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error Mit1 sponsoring breakfast meals: {e}")
            return {"error": str(e)}
    
    def mit4_sponsors_lunch_for_mit1(self, mit4_employee_id: str) -> Dict:
        """Mit4 sponsors lunch for Mit1"""
        try:
            today = self.get_berlin_date()
            
            print(f"\n🔍 CRITICAL TEST: Mit4 sponsors lunch for Mit1")
            print(f"   - Sponsor: Mit4 (ID: {mit4_employee_id})")
            print(f"   - Target: All employees with lunch orders (Mit1)")
            print(f"   - Date: {today}")
            print(f"   - Meal Type: lunch")
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": mit4_employee_id,
                "sponsor_employee_name": "Mit4"
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Mit4 successfully sponsored lunch meals!")
                print(f"🔍 LUNCH SPONSORING RESPONSE: {json.dumps(result, indent=2)}")
                
                affected_employees = result.get("affected_employees", 0)
                total_cost = result.get("total_cost", 0.0)
                
                print(f"🔍 LUNCH SPONSORING SUMMARY:")
                print(f"   - Affected employees: {affected_employees}")
                print(f"   - Total sponsoring cost: €{total_cost:.2f}")
                print(f"   - Expected: Mit1 should be affected (1 employee)")
                
                return result
            else:
                print(f"❌ Mit4 failed to sponsor lunch meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error Mit4 sponsoring lunch meals: {e}")
            return {"error": str(e)}
    
    def verify_sponsoring_assignment_logic(self) -> Dict:
        """Verify the corrected sponsoring assignment logic"""
        try:
            print(f"\n🔍 VERIFYING CORRECTED SPONSORING ASSIGNMENT LOGIC:")
            print("=" * 80)
            
            # Get breakfast-history data
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    employee_orders = today_data.get("employee_orders", {})
                    
                    print(f"✅ Found {len(employee_orders)} employees in breakfast-history")
                    
                    # Find each employee in the data
                    employees_found = {}
                    for emp_name, emp_data in employee_orders.items():
                        if "Mit1" in emp_name:
                            employees_found["Mit1"] = emp_data
                        elif "Mit2" in emp_name:
                            employees_found["Mit2"] = emp_data
                        elif "Mit3" in emp_name:
                            employees_found["Mit3"] = emp_data
                        elif "Mit4" in emp_name:
                            employees_found["Mit4"] = emp_data
                    
                    print(f"✅ Found employees: {list(employees_found.keys())}")
                    
                    # Verify sponsoring assignment for each employee
                    verification_results = {
                        "employees_found": len(employees_found),
                        "mit1_correct": False,
                        "mit2_correct": False,
                        "mit3_correct": False,
                        "mit4_correct": False,
                        "all_data": employees_found
                    }
                    
                    # Check Mit1 - should show sponsored_breakfast info (sponsors breakfast for others)
                    if "Mit1" in employees_found:
                        mit1_data = employees_found["Mit1"]
                        sponsored_breakfast = mit1_data.get("sponsored_breakfast")
                        sponsored_lunch = mit1_data.get("sponsored_lunch")
                        
                        print(f"\n🔍 Mit1 Sponsoring Assignment:")
                        print(f"   - sponsored_breakfast: {sponsored_breakfast}")
                        print(f"   - sponsored_lunch: {sponsored_lunch}")
                        
                        # Mit1 should have sponsored_breakfast info (count: 3, amount: X.XX)
                        mit1_breakfast_correct = (
                            sponsored_breakfast is not None and 
                            isinstance(sponsored_breakfast, dict) and
                            sponsored_breakfast.get("count", 0) == 3 and
                            sponsored_breakfast.get("amount", 0) > 0
                        )
                        
                        # Mit1 should NOT have sponsored_lunch info (should be null)
                        mit1_lunch_correct = sponsored_lunch is None
                        
                        verification_results["mit1_correct"] = mit1_breakfast_correct and mit1_lunch_correct
                        
                        print(f"   ✅ Mit1 breakfast sponsoring correct: {mit1_breakfast_correct}")
                        print(f"   ✅ Mit1 lunch sponsoring correct (null): {mit1_lunch_correct}")
                    
                    # Check Mit2 - should show NO sponsoring info (sponsored by others, doesn't sponsor)
                    if "Mit2" in employees_found:
                        mit2_data = employees_found["Mit2"]
                        sponsored_breakfast = mit2_data.get("sponsored_breakfast")
                        sponsored_lunch = mit2_data.get("sponsored_lunch")
                        
                        print(f"\n🔍 Mit2 Sponsoring Assignment:")
                        print(f"   - sponsored_breakfast: {sponsored_breakfast}")
                        print(f"   - sponsored_lunch: {sponsored_lunch}")
                        
                        # Mit2 should have NO sponsoring info (both null)
                        verification_results["mit2_correct"] = (
                            sponsored_breakfast is None and sponsored_lunch is None
                        )
                        
                        print(f"   ✅ Mit2 no sponsoring info (correct): {verification_results['mit2_correct']}")
                    
                    # Check Mit3 - should show NO sponsoring info (sponsored by others, doesn't sponsor)
                    if "Mit3" in employees_found:
                        mit3_data = employees_found["Mit3"]
                        sponsored_breakfast = mit3_data.get("sponsored_breakfast")
                        sponsored_lunch = mit3_data.get("sponsored_lunch")
                        
                        print(f"\n🔍 Mit3 Sponsoring Assignment:")
                        print(f"   - sponsored_breakfast: {sponsored_breakfast}")
                        print(f"   - sponsored_lunch: {sponsored_lunch}")
                        
                        # Mit3 should have NO sponsoring info (both null)
                        verification_results["mit3_correct"] = (
                            sponsored_breakfast is None and sponsored_lunch is None
                        )
                        
                        print(f"   ✅ Mit3 no sponsoring info (correct): {verification_results['mit3_correct']}")
                    
                    # Check Mit4 - should show sponsored_lunch info (sponsors lunch for Mit1)
                    if "Mit4" in employees_found:
                        mit4_data = employees_found["Mit4"]
                        sponsored_breakfast = mit4_data.get("sponsored_breakfast")
                        sponsored_lunch = mit4_data.get("sponsored_lunch")
                        
                        print(f"\n🔍 Mit4 Sponsoring Assignment:")
                        print(f"   - sponsored_breakfast: {sponsored_breakfast}")
                        print(f"   - sponsored_lunch: {sponsored_lunch}")
                        
                        # Mit4 should have sponsored_lunch info (count: 1, amount: X.XX)
                        mit4_lunch_correct = (
                            sponsored_lunch is not None and 
                            isinstance(sponsored_lunch, dict) and
                            sponsored_lunch.get("count", 0) == 1 and
                            sponsored_lunch.get("amount", 0) > 0
                        )
                        
                        # Mit4 should NOT have sponsored_breakfast info (should be null)
                        mit4_breakfast_correct = sponsored_breakfast is None
                        
                        verification_results["mit4_correct"] = mit4_lunch_correct and mit4_breakfast_correct
                        
                        print(f"   ✅ Mit4 lunch sponsoring correct: {mit4_lunch_correct}")
                        print(f"   ✅ Mit4 breakfast sponsoring correct (null): {mit4_breakfast_correct}")
                    
                    return verification_results
                else:
                    print(f"❌ No history data found in breakfast-history response")
                    return {"error": "No history data found", "employees_found": 0}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": f"API call failed: {response.text}", "employees_found": 0}
                
        except Exception as e:
            print(f"❌ Error verifying sponsoring assignment logic: {e}")
            return {"error": str(e), "employees_found": 0}
    
    def run_sponsoring_assignment_verification(self):
        """Run the sponsoring assignment verification as per review request"""
        print("🔍 FINAL VERIFICATION: Test corrected sponsoring assignment logic")
        print("=" * 100)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 1 (fw1abteilung1)")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Clean up existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create exact scenario - Mit1, Mit2, Mit3, Mit4
        print(f"\n2️⃣ Creating Exact Scenario: Mit1, Mit2, Mit3, Mit4 with breakfast orders")
        
        # Create all employees
        self.mit1_employee_id = self.create_test_employee("Mit1")
        if not self.mit1_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Mit1")
            return False
        
        self.mit2_employee_id = self.create_test_employee("Mit2")
        if not self.mit2_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Mit2")
            return False
        
        self.mit3_employee_id = self.create_test_employee("Mit3")
        if not self.mit3_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Mit3")
            return False
        
        self.mit4_employee_id = self.create_test_employee("Mit4")
        if not self.mit4_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Mit4")
            return False
        
        # Step 3: Create breakfast orders
        print(f"\n3️⃣ Creating Breakfast Orders")
        
        # Mit1: breakfast order with lunch (will be sponsored by Mit4)
        print(f"\n📋 Creating Mit1 order (with lunch):")
        mit1_order = self.create_breakfast_order_with_lunch(self.mit1_employee_id, "Mit1")
        if not mit1_order:
            print("❌ CRITICAL FAILURE: Cannot create Mit1's order")
            return False
        
        # Mit2: breakfast order without lunch (will be sponsored by Mit1)
        print(f"\n📋 Creating Mit2 order (no lunch):")
        mit2_order = self.create_breakfast_order_no_lunch(self.mit2_employee_id, "Mit2")
        if not mit2_order:
            print("❌ CRITICAL FAILURE: Cannot create Mit2's order")
            return False
        
        # Mit3: breakfast order without lunch (will be sponsored by Mit1)
        print(f"\n📋 Creating Mit3 order (no lunch):")
        mit3_order = self.create_breakfast_order_no_lunch(self.mit3_employee_id, "Mit3")
        if not mit3_order:
            print("❌ CRITICAL FAILURE: Cannot create Mit3's order")
            return False
        
        # Mit4: breakfast order without lunch (will sponsor lunch for Mit1)
        print(f"\n📋 Creating Mit4 order (no lunch):")
        mit4_order = self.create_breakfast_order_no_lunch(self.mit4_employee_id, "Mit4")
        if not mit4_order:
            print("❌ CRITICAL FAILURE: Cannot create Mit4's order")
            return False
        
        # Step 4: Execute sponsoring scenarios
        print(f"\n4️⃣ Execute Sponsoring Scenarios")
        
        # Mit1 sponsors breakfast for Mit2, Mit3, Mit4
        print(f"\n🔍 SCENARIO 1: Mit1 sponsors breakfast for others")
        breakfast_result = self.mit1_sponsors_breakfast_for_others(self.mit1_employee_id)
        if "error" in breakfast_result:
            print(f"❌ Mit1 breakfast sponsoring failed: {breakfast_result['error']}")
            return False
        
        # Mit4 sponsors lunch for Mit1
        print(f"\n🔍 SCENARIO 2: Mit4 sponsors lunch for Mit1")
        lunch_result = self.mit4_sponsors_lunch_for_mit1(self.mit4_employee_id)
        if "error" in lunch_result:
            print(f"❌ Mit4 lunch sponsoring failed: {lunch_result['error']}")
            return False
        
        # Step 5: Verify corrected sponsoring assignment logic
        print(f"\n5️⃣ Verify Corrected Sponsoring Assignment Logic")
        
        assignment_verification = self.verify_sponsoring_assignment_logic()
        if "error" in assignment_verification:
            print(f"❌ Sponsoring assignment verification failed: {assignment_verification['error']}")
            return False
        
        # Final Results
        print(f"\n🏁 FINAL SPONSORING ASSIGNMENT VERIFICATION RESULTS:")
        print("=" * 100)
        
        success_criteria = [
            (assignment_verification.get("employees_found", 0) == 4, "All 4 employees found in breakfast-history"),
            (assignment_verification.get("mit1_correct", False), "Mit1 shows correct sponsoring info (sponsored_breakfast: count=3)"),
            (assignment_verification.get("mit2_correct", False), "Mit2 shows no sponsoring info (both null)"),
            (assignment_verification.get("mit3_correct", False), "Mit3 shows no sponsoring info (both null)"),
            (assignment_verification.get("mit4_correct", False), "Mit4 shows correct sponsoring info (sponsored_lunch: count=1)")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Sponsoring Assignment Verification Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print summary for main agent
        print(f"\n🔍 SUMMARY FOR MAIN AGENT:")
        print(f"Mit1 Employee ID: {self.mit1_employee_id}")
        print(f"Mit2 Employee ID: {self.mit2_employee_id}")
        print(f"Mit3 Employee ID: {self.mit3_employee_id}")
        print(f"Mit4 Employee ID: {self.mit4_employee_id}")
        
        all_correct = all(test for test, _ in success_criteria)
        
        if all_correct:
            print(f"\n✅ SPONSORING ASSIGNMENT LOGIC: WORKING CORRECTLY!")
            print(f"✅ Mit1 correctly shows sponsored_breakfast info (count: 3)")
            print(f"✅ Mit4 correctly shows sponsored_lunch info (count: 1)")
            print(f"✅ Mit2, Mit3 correctly show no sponsoring info (both null)")
            print(f"✅ No cross-contamination between employees detected")
        else:
            print(f"\n❌ SPONSORING ASSIGNMENT LOGIC: CRITICAL ISSUES DETECTED!")
            if not assignment_verification.get("mit1_correct", False):
                print(f"❌ Mit1 does NOT show correct sponsored_breakfast info")
            if not assignment_verification.get("mit4_correct", False):
                print(f"❌ Mit4 does NOT show correct sponsored_lunch info")
            if not assignment_verification.get("mit2_correct", False):
                print(f"❌ Mit2 shows incorrect sponsoring info (should be null)")
            if not assignment_verification.get("mit3_correct", False):
                print(f"❌ Mit3 shows incorrect sponsoring info (should be null)")
        
        return all_correct

def main():
    """Main test execution"""
    test = SponsoringAssignmentVerification()
    
    try:
        success = test.run_sponsoring_assignment_verification()
        
        if success:
            print(f"\n✅ SPONSORING ASSIGNMENT VERIFICATION: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ SPONSORING ASSIGNMENT VERIFICATION: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()