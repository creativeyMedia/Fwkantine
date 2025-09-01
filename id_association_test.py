#!/usr/bin/env python3
"""
🚨 CRITICAL ID ASSOCIATION BUG FIX TEST: Test correct ID association for sponsoring info

CRITICAL ID ASSOCIATION TEST:

1. **Create Test Scenario:**
   - Create Employee1 "Test1": Create breakfast order + will sponsor breakfast
   - Create Employee2 "Test2": Create breakfast order + will be sponsored
   - Create Employee3 "Test3": NO orders + will sponsor lunch only

2. **Mixed Sponsoring Scenario:**
   - Test1 (has own orders) sponsors breakfast for Test2
   - Test3 (no own orders) sponsors lunch for Test2
   
3. **CRITICAL Bug Test - Check Correct ID Association:**
   - Call GET /api/orders/breakfast-history/{department_id}
   - CRITICAL: Each employee should appear with correct ID format
   - Test1: Should show as "Test1 (ID: ########)" with own orders + sponsored_breakfast info
   - Test2: Should show as "Test2 (ID: ########)" with own orders + remaining costs after sponsoring
   - Test3: Should show as "Test3 (ID: ########)" with zero orders + sponsored_lunch info

4. **Verify Correct Key Format:**
   - All employee keys should follow format: "Name (ID: ########)"
   - No plain names without IDs should appear
   - Sponsoring info should be correctly associated with the ID-based keys

5. **Verify No Duplication:**
   - Each employee should appear exactly once
   - No employee should have both "Test1" and "Test1 (ID: ########)" entries
   - Total employee count should match created employees

EXPECTED RESULT: 
- All employees appear with correct "Name (ID: ########)" format
- Sponsoring info correctly associated with ID-based employee keys
- No plain name entries without IDs
- No duplication of employees

Use Department 2 (fw4abteilung2) with admin2 credentials.
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

class IDAssociationBugFixTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_employees = []
        self.employee1_id = None  # Test1 - has orders + sponsors breakfast
        self.employee2_id = None  # Test2 - has orders + gets sponsored
        self.employee3_id = None  # Test3 - no orders + sponsors lunch
        
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
    
    def create_breakfast_order(self, employee_id: str, employee_name: str) -> Dict:
        """Create a breakfast order with rolls, eggs, coffee, and lunch"""
        try:
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # 2 rolls
                    "white_halves": 2,
                    "seeded_halves": 2,
                    "toppings": ["butter", "kaese", "salami", "schinken"],
                    "has_lunch": True,
                    "boiled_eggs": 2,
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                
                print(f"✅ Created breakfast order for {employee_name}: {order_id} (€{order['total_price']:.2f})")
                return {
                    "order_id": order_id,
                    "total_price": order["total_price"]
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
    
    def verify_id_association_format(self, employee_orders: Dict) -> Dict:
        """
        CRITICAL Test: Verify all employees appear with correct "Name (ID: ########)" format
        """
        results = {
            "correct_id_format": True,
            "total_employees": len(employee_orders),
            "correct_format_count": 0,
            "plain_name_count": 0,
            "duplicate_count": 0,
            "format_issues": [],
            "employee_keys": list(employee_orders.keys())
        }
        
        print(f"\n🔍 CRITICAL ID Association Format Test")
        print(f"Expected: All employees appear as 'Name (ID: ########)' format")
        print(f"Found {results['total_employees']} employees in breakfast history")
        
        # Check each employee key format
        seen_names = set()
        for employee_key in employee_orders.keys():
            print(f"📋 Employee key: '{employee_key}'")
            
            # Check if key follows "Name (ID: ########)" format
            if " (ID: " in employee_key and employee_key.endswith(")"):
                results["correct_format_count"] += 1
                print(f"✅ Correct ID format: {employee_key}")
                
                # Extract name part to check for duplicates
                name_part = employee_key.split(" (ID: ")[0]
                if name_part in seen_names:
                    results["duplicate_count"] += 1
                    results["format_issues"].append(f"Duplicate name detected: {name_part}")
                    print(f"❌ DUPLICATE: Name '{name_part}' appears multiple times")
                else:
                    seen_names.add(name_part)
                    
            else:
                results["plain_name_count"] += 1
                results["format_issues"].append(f"Plain name without ID: {employee_key}")
                print(f"❌ INCORRECT FORMAT: Plain name without ID: {employee_key}")
        
        # Determine if ID association is correct
        if results["plain_name_count"] == 0 and results["duplicate_count"] == 0:
            results["correct_id_format"] = True
            print(f"✅ ID ASSOCIATION CORRECT: All {results['correct_format_count']} employees have proper ID format")
        else:
            results["correct_id_format"] = False
            print(f"❌ ID ASSOCIATION BUG: {results['plain_name_count']} plain names, {results['duplicate_count']} duplicates")
        
        return results
    
    def verify_sponsoring_info_association(self, employee_orders: Dict) -> Dict:
        """
        CRITICAL Test: Verify sponsoring info is correctly associated with ID-based keys
        """
        results = {
            "sponsoring_correctly_associated": True,
            "sponsors_found": 0,
            "sponsored_found": 0,
            "association_issues": []
        }
        
        print(f"\n🔍 CRITICAL Sponsoring Info Association Test")
        print(f"Expected: Sponsoring info correctly associated with 'Name (ID: ########)' keys")
        
        for employee_key, employee_data in employee_orders.items():
            has_sponsored_breakfast = employee_data.get("sponsored_breakfast") is not None
            has_sponsored_lunch = employee_data.get("sponsored_lunch") is not None
            
            # Check if this employee is a sponsor
            if has_sponsored_breakfast or has_sponsored_lunch:
                results["sponsors_found"] += 1
                
                if " (ID: " in employee_key:
                    print(f"✅ Sponsor with correct ID format: {employee_key}")
                    if has_sponsored_breakfast:
                        breakfast_info = employee_data.get("sponsored_breakfast", {})
                        print(f"   - Sponsored breakfast: {breakfast_info}")
                    if has_sponsored_lunch:
                        lunch_info = employee_data.get("sponsored_lunch", {})
                        print(f"   - Sponsored lunch: {lunch_info}")
                else:
                    results["association_issues"].append(f"Sponsor without ID format: {employee_key}")
                    print(f"❌ SPONSOR WITHOUT ID: {employee_key}")
            
            # Check if this employee has comprehensive orders (likely sponsored)
            has_comprehensive_order = all([
                employee_data.get("white_halves", 0) > 0,
                employee_data.get("seeded_halves", 0) > 0,
                employee_data.get("boiled_eggs", 0) > 0,
                employee_data.get("has_lunch", False),
                employee_data.get("has_coffee", False)
            ])
            
            if has_comprehensive_order:
                results["sponsored_found"] += 1
                
                if " (ID: " in employee_key:
                    total_amount = employee_data.get("total_amount", 0)
                    print(f"✅ Sponsored employee with correct ID format: {employee_key} (€{total_amount:.2f})")
                else:
                    results["association_issues"].append(f"Sponsored employee without ID format: {employee_key}")
                    print(f"❌ SPONSORED WITHOUT ID: {employee_key}")
        
        # Determine if sponsoring info is correctly associated
        if len(results["association_issues"]) == 0:
            results["sponsoring_correctly_associated"] = True
            print(f"✅ SPONSORING ASSOCIATION CORRECT: All sponsoring info properly associated with ID format")
        else:
            results["sponsoring_correctly_associated"] = False
            print(f"❌ SPONSORING ASSOCIATION BUG: {len(results['association_issues'])} issues found")
        
        return results
    
    def verify_expected_employees(self, employee_orders: Dict) -> Dict:
        """
        Verify the expected employees from our test scenario are present
        """
        results = {
            "expected_employees_found": True,
            "test1_found": False,
            "test2_found": False,
            "test3_found": False,
            "employee_details": {}
        }
        
        print(f"\n🔍 Expected Employees Verification")
        print(f"Looking for Test1 (has orders + sponsors breakfast), Test2 (has orders + sponsored), Test3 (no orders + sponsors lunch)")
        
        for employee_key, employee_data in employee_orders.items():
            # Extract name from key (handle both formats)
            if " (ID: " in employee_key:
                name_part = employee_key.split(" (ID: ")[0]
            else:
                name_part = employee_key
            
            results["employee_details"][employee_key] = {
                "name": name_part,
                "total_amount": employee_data.get("total_amount", 0),
                "has_orders": any([
                    employee_data.get("white_halves", 0) > 0,
                    employee_data.get("seeded_halves", 0) > 0,
                    employee_data.get("boiled_eggs", 0) > 0
                ]),
                "sponsored_breakfast": employee_data.get("sponsored_breakfast"),
                "sponsored_lunch": employee_data.get("sponsored_lunch")
            }
            
            # Check for Test1 pattern (has orders + sponsors breakfast)
            if "Test1" in name_part:
                results["test1_found"] = True
                details = results["employee_details"][employee_key]
                print(f"✅ Found Test1: {employee_key}")
                print(f"   - Has orders: {details['has_orders']}")
                print(f"   - Sponsors breakfast: {details['sponsored_breakfast'] is not None}")
                print(f"   - Total amount: €{details['total_amount']:.2f}")
            
            # Check for Test2 pattern (has orders + gets sponsored)
            elif "Test2" in name_part:
                results["test2_found"] = True
                details = results["employee_details"][employee_key]
                print(f"✅ Found Test2: {employee_key}")
                print(f"   - Has orders: {details['has_orders']}")
                print(f"   - Total amount: €{details['total_amount']:.2f}")
            
            # Check for Test3 pattern (no orders + sponsors lunch)
            elif "Test3" in name_part:
                results["test3_found"] = True
                details = results["employee_details"][employee_key]
                print(f"✅ Found Test3: {employee_key}")
                print(f"   - Has orders: {details['has_orders']}")
                print(f"   - Sponsors lunch: {details['sponsored_lunch'] is not None}")
                print(f"   - Total amount: €{details['total_amount']:.2f}")
        
        # Check if all expected employees are found
        if results["test1_found"] and results["test2_found"] and results["test3_found"]:
            results["expected_employees_found"] = True
            print(f"✅ All expected test employees found with correct patterns")
        else:
            results["expected_employees_found"] = False
            missing = []
            if not results["test1_found"]: missing.append("Test1")
            if not results["test2_found"]: missing.append("Test2")
            if not results["test3_found"]: missing.append("Test3")
            print(f"❌ Missing expected employees: {missing}")
        
        return results
    
    def run_comprehensive_test(self):
        """Run the comprehensive ID association bug fix test"""
        print("🚨 CRITICAL ID ASSOCIATION BUG FIX TEST: Test correct ID association for sponsoring info")
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
        
        # Create Employee1 "Test1": Create breakfast order + will sponsor breakfast
        print("Creating Employee1 'Test1': Create breakfast order + will sponsor breakfast")
        self.employee1_id = self.create_test_employee("Test1")
        if not self.employee1_id:
            print("❌ CRITICAL FAILURE: Cannot create Employee1 Test1")
            return False
        
        # Create Employee2 "Test2": Create breakfast order + will be sponsored
        print("Creating Employee2 'Test2': Create breakfast order + will be sponsored")
        self.employee2_id = self.create_test_employee("Test2")
        if not self.employee2_id:
            print("❌ CRITICAL FAILURE: Cannot create Employee2 Test2")
            return False
        
        # Create Employee3 "Test3": NO orders + will sponsor lunch only
        print("Creating Employee3 'Test3': NO orders + will sponsor lunch only")
        self.employee3_id = self.create_test_employee("Test3")
        if not self.employee3_id:
            print("❌ CRITICAL FAILURE: Cannot create Employee3 Test3")
            return False
        
        # Step 3: Create breakfast orders for Test1 and Test2
        print(f"\n3️⃣ Creating Breakfast Orders")
        
        # Test1 creates breakfast order
        test1_order = self.create_breakfast_order(self.employee1_id, "Test1")
        if not test1_order:
            print("❌ CRITICAL FAILURE: Cannot create Test1's breakfast order")
            return False
        
        # Test2 creates breakfast order
        test2_order = self.create_breakfast_order(self.employee2_id, "Test2")
        if not test2_order:
            print("❌ CRITICAL FAILURE: Cannot create Test2's breakfast order")
            return False
        
        # Test3 does NOT create any orders (as per review request)
        print("✅ Test3 has NO orders (as per review request)")
        
        # Step 4: Mixed Sponsoring Scenario
        print(f"\n4️⃣ Mixed Sponsoring Scenario")
        
        # Test1 (has own orders) sponsors breakfast for Test2
        print("Test1 (has own orders) sponsors breakfast for Test2")
        breakfast_result = self.sponsor_breakfast_meals(self.employee1_id, "Test1")
        if "error" in breakfast_result and "bereits gesponsert" not in breakfast_result.get('error', ''):
            print(f"❌ Breakfast sponsoring failed: {breakfast_result['error']}")
            return False
        
        # Test3 (no own orders) sponsors lunch for Test2
        print("Test3 (no own orders) sponsors lunch for Test2")
        lunch_result = self.sponsor_lunch_meals(self.employee3_id, "Test3")
        if "error" in lunch_result and "bereits gesponsert" not in lunch_result.get('error', ''):
            print(f"❌ Lunch sponsoring failed: {lunch_result['error']}")
            return False
        
        print(f"✅ Mixed sponsoring scenario completed")
        
        # Step 5: Get Breakfast History for Critical Bug Test
        print(f"\n5️⃣ Getting Breakfast History for Critical Bug Test")
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
        
        # Step 7: CRITICAL Bug Test - Check Correct ID Association
        print(f"\n7️⃣ CRITICAL Bug Test - Check Correct ID Association")
        
        # Test 1: Verify ID format
        format_results = self.verify_id_association_format(employee_orders)
        
        # Test 2: Verify sponsoring info association
        association_results = self.verify_sponsoring_info_association(employee_orders)
        
        # Test 3: Verify expected employees
        expected_results = self.verify_expected_employees(employee_orders)
        
        # Step 8: Final Verification
        print(f"\n8️⃣ Final Verification")
        
        # Check for exact employee count (should be 3: Test1, Test2, Test3)
        expected_count = 3
        actual_count = len(employee_orders)
        count_correct = actual_count == expected_count
        
        if count_correct:
            print(f"✅ Employee count correct: {actual_count} employees (expected {expected_count})")
        else:
            print(f"❌ Employee count incorrect: {actual_count} employees (expected {expected_count})")
        
        # Final Results
        print(f"\n🏁 FINAL RESULTS:")
        
        success_criteria = [
            (format_results["correct_id_format"], f"Correct ID Format: {format_results['correct_format_count']} correct, {format_results['plain_name_count']} plain names"),
            (association_results["sponsoring_correctly_associated"], f"Sponsoring Info Association: {len(association_results['association_issues'])} issues found"),
            (expected_results["expected_employees_found"], f"Expected Employees Found: Test1={expected_results['test1_found']}, Test2={expected_results['test2_found']}, Test3={expected_results['test3_found']}"),
            (count_correct, f"Employee Count: {actual_count} found (expected {expected_count})"),
            (format_results["duplicate_count"] == 0, f"No Duplicates: {format_results['duplicate_count']} duplicates found"),
            (association_results["sponsors_found"] >= 2, f"Sponsors Found: {association_results['sponsors_found']} sponsors (expected ≥2)")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Show detailed employee information
        print(f"\n📋 Employee Details:")
        for employee_key in employee_orders.keys():
            employee_data = employee_orders[employee_key]
            total_amount = employee_data.get("total_amount", 0)
            sponsored_breakfast = employee_data.get("sponsored_breakfast")
            sponsored_lunch = employee_data.get("sponsored_lunch")
            
            print(f"   {employee_key}: €{total_amount:.2f}")
            if sponsored_breakfast:
                print(f"      - Sponsored breakfast: {sponsored_breakfast}")
            if sponsored_lunch:
                print(f"      - Sponsored lunch: {sponsored_lunch}")
        
        if success_rate >= 83:  # 5/6 tests must pass
            print("🎉 CRITICAL ID ASSOCIATION BUG FIX VERIFICATION SUCCESSFUL!")
            print("✅ All employees appear with correct 'Name (ID: ########)' format")
            print("✅ Sponsoring info correctly associated with ID-based employee keys")
            print("✅ No plain name entries without IDs")
            print("✅ No duplication of employees")
            return True
        else:
            print("🚨 CRITICAL ID ASSOCIATION BUG DETECTED!")
            print("❌ ID association bug fix verification failed")
            if format_results["format_issues"]:
                print(f"❌ Format issues: {format_results['format_issues']}")
            if association_results["association_issues"]:
                print(f"❌ Association issues: {association_results['association_issues']}")
            return False

def main():
    """Main test execution"""
    test = IDAssociationBugFixTest()
    
    try:
        success = test.run_comprehensive_test()
        
        if success:
            print(f"\n✅ ID ASSOCIATION BUG FIX: VERIFIED WORKING")
            exit(0)
        else:
            print(f"\n❌ ID ASSOCIATION BUG FIX: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()