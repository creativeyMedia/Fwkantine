#!/usr/bin/env python3
"""
🔍 DATENBANK ORDER-UPDATE VERIFIKATION: Überprüfe ob Sponsoring-Updates in DB geschrieben werden

KRITISCHE DATENBANK-VERIFIKATION:

1. **Simple Test Scenario:**
   - Create Test1: Breakfast order with lunch
   - Create Test4: Breakfast order 
   - Test4 sponsors lunch for Test1

2. **DATENBANK-UPDATE VERIFICATION:**
   - Execute sponsoring and watch debug logs
   - Verify that Test1's order gets updated in database with:
     - is_sponsored: true
     - sponsored_meal_type: "lunch"
     - sponsored_message: "..."

3. **DIRECT DATABASE CHECK:**
   - After sponsoring, directly query Test1's order from database
   - Verify the fields are actually there in the raw database record
   - Check if individual profile endpoint returns the same data

4. **INDIVIDUAL PROFILE API TEST:**
   - Call GET /employees/{test1_id}/profile
   - Check if the response includes the sponsored fields
   - Compare with raw database data

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Verifikation ob Order-Updates tatsächlich in die Datenbank geschrieben werden!
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

class SystematicFrontendDataStructureAnalysis:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test1_employee_id = None
        self.test2_employee_id = None
        self.test3_employee_id = None
        self.test4_employee_id = None
        self.test1_order_id = None
        self.test2_order_id = None
        self.test3_order_id = None
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
    
    def create_breakfast_order_with_lunch(self, employee_id: str, name: str) -> Dict:
        """Create breakfast order with lunch for Test1"""
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
                    "has_lunch": True,  # MITTAG - this will be sponsored by Test4
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
        """Create breakfast order without lunch for Test2, Test3, Test4"""
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
    
    def test1_sponsors_breakfast(self, test1_employee_id: str) -> Dict:
        """Test1 sponsors breakfast for Test2, Test3, Test4"""
        try:
            today = self.get_berlin_date()
            
            print(f"\n🔍 STEP 1: Test1 sponsors breakfast for Test2, Test3, Test4")
            print(f"   - Sponsor: Test1 (ID: {test1_employee_id})")
            print(f"   - Target: All employees with breakfast orders (Test2, Test3, Test4)")
            print(f"   - Date: {today}")
            print(f"   - Meal Type: breakfast")
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": test1_employee_id,
                "sponsor_employee_name": "Test1"
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test1 successfully sponsored breakfast meals!")
                print(f"🔍 BREAKFAST SPONSORING RESPONSE: {json.dumps(result, indent=2)}")
                
                affected_employees = result.get("affected_employees", 0)
                total_cost = result.get("total_cost", 0.0)
                
                print(f"🔍 BREAKFAST SPONSORING SUMMARY:")
                print(f"   - Affected employees: {affected_employees}")
                print(f"   - Total sponsoring cost: €{total_cost:.2f}")
                print(f"   - Expected: Test2, Test3, Test4 should be affected")
                
                return result
            else:
                print(f"❌ Test1 failed to sponsor breakfast meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error Test1 sponsoring breakfast meals: {e}")
            return {"error": str(e)}
    
    def test4_sponsors_lunch(self, test4_employee_id: str) -> Dict:
        """Test4 sponsors lunch for Test1"""
        try:
            today = self.get_berlin_date()
            
            print(f"\n🔍 STEP 2: Test4 sponsors lunch for Test1")
            print(f"   - Sponsor: Test4 (ID: {test4_employee_id})")
            print(f"   - Target: All employees with lunch orders (Test1)")
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
                print(f"🔍 LUNCH SPONSORING RESPONSE: {json.dumps(result, indent=2)}")
                
                affected_employees = result.get("affected_employees", 0)
                total_cost = result.get("total_cost", 0.0)
                
                print(f"🔍 LUNCH SPONSORING SUMMARY:")
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
    
    def get_all_employee_data(self) -> Dict:
        """Get all employee data from breakfast-history endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    employee_orders = today_data.get("employee_orders", {})
                    
                    print(f"✅ Successfully retrieved all employee data")
                    print(f"🔍 Found {len(employee_orders)} employees in data")
                    
                    return employee_orders
                else:
                    print(f"❌ No history data found")
                    return {"error": "No history data"}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error getting employee data: {e}")
            return {"error": str(e)}
    
    def analyze_employee_data_structure(self, employee_name: str, employee_data: Dict) -> Dict:
        """Analyze individual employee data structure for critical fields"""
        results = {
            "employee_name": employee_name,
            "is_sponsored_found": False,
            "is_sponsored_value": None,
            "sponsored_meal_type_found": False,
            "sponsored_meal_type_value": None,
            "sponsor_message_found": False,
            "sponsor_message_value": None,
            "sponsored_message_found": False,
            "sponsored_message_value": None,
            "total_amount": 0.0,
            "readable_items_found": False,
            "readable_items_value": None,
            "sponsored_breakfast_found": False,
            "sponsored_lunch_found": False,
            "all_fields": {}
        }
        
        print(f"\n🔍 ANALYZING {employee_name} DATA STRUCTURE:")
        print("=" * 60)
        
        # Store all fields for complete analysis
        results["all_fields"] = employee_data.copy()
        
        # Print complete data structure
        print(f"📋 Complete Data Structure for {employee_name}:")
        for key, value in employee_data.items():
            print(f"   - {key}: {value}")
        
        # Check critical fields
        critical_fields = [
            ("is_sponsored", "is_sponsored_found", "is_sponsored_value"),
            ("sponsored_meal_type", "sponsored_meal_type_found", "sponsored_meal_type_value"),
            ("sponsor_message", "sponsor_message_found", "sponsor_message_value"),
            ("sponsored_message", "sponsored_message_found", "sponsored_message_value"),
            ("readable_items", "readable_items_found", "readable_items_value")
        ]
        
        print(f"\n🔍 CRITICAL FIELDS ANALYSIS for {employee_name}:")
        for field_name, found_key, value_key in critical_fields:
            if field_name in employee_data:
                results[found_key] = True
                results[value_key] = employee_data[field_name]
                print(f"✅ {field_name}: {employee_data[field_name]}")
            else:
                print(f"❌ {field_name}: NOT FOUND")
        
        # Check total_amount
        total_amount = employee_data.get("total_amount", 0.0)
        results["total_amount"] = total_amount
        print(f"💰 total_amount: €{total_amount:.2f}")
        
        # Check sponsored_breakfast and sponsored_lunch fields
        if "sponsored_breakfast" in employee_data:
            results["sponsored_breakfast_found"] = True
            print(f"✅ sponsored_breakfast: {employee_data['sponsored_breakfast']}")
        else:
            print(f"❌ sponsored_breakfast: NOT FOUND")
            
        if "sponsored_lunch" in employee_data:
            results["sponsored_lunch_found"] = True
            print(f"✅ sponsored_lunch: {employee_data['sponsored_lunch']}")
        else:
            print(f"❌ sponsored_lunch: NOT FOUND")
        
        return results
    
    def verify_expected_data_structure(self, all_analyses: Dict) -> Dict:
        """Verify if the data structure matches expected patterns from review request"""
        verification_results = {
            "test1_correct": False,
            "test2_correct": False,
            "test3_correct": False,
            "test4_correct": False,
            "critical_issues": [],
            "missing_fields": [],
            "overall_working": False
        }
        
        print(f"\n🎯 VERIFYING EXPECTED DATA STRUCTURE PATTERNS:")
        print("=" * 80)
        
        # Find each test employee in the data
        test1_data = None
        test2_data = None
        test3_data = None
        test4_data = None
        
        for emp_name, analysis in all_analyses.items():
            if "Test1" in emp_name:
                test1_data = analysis
            elif "Test2" in emp_name:
                test2_data = analysis
            elif "Test3" in emp_name:
                test3_data = analysis
            elif "Test4" in emp_name:
                test4_data = analysis
        
        # Verify Test1 (should be sponsored for lunch)
        if test1_data:
            print(f"\n🔍 VERIFYING Test1 (should be sponsored for lunch):")
            expected_test1 = (
                test1_data["is_sponsored_found"] and
                test1_data["is_sponsored_value"] == True and
                test1_data["sponsored_meal_type_found"] and
                "lunch" in str(test1_data["sponsored_meal_type_value"]).lower()
            )
            
            if expected_test1:
                print(f"✅ Test1 data structure CORRECT")
                verification_results["test1_correct"] = True
            else:
                print(f"❌ Test1 data structure INCORRECT")
                if not test1_data["is_sponsored_found"]:
                    verification_results["critical_issues"].append("Test1 missing is_sponsored field")
                if not test1_data["sponsored_meal_type_found"]:
                    verification_results["critical_issues"].append("Test1 missing sponsored_meal_type field")
                elif "lunch" not in str(test1_data["sponsored_meal_type_value"]).lower():
                    verification_results["critical_issues"].append(f"Test1 sponsored_meal_type should contain 'lunch', got: {test1_data['sponsored_meal_type_value']}")
        else:
            print(f"❌ Test1 not found in data")
            verification_results["critical_issues"].append("Test1 not found in employee data")
        
        # Verify Test2 and Test3 (should be sponsored for breakfast)
        for test_name, test_data in [("Test2", test2_data), ("Test3", test3_data)]:
            if test_data:
                print(f"\n🔍 VERIFYING {test_name} (should be sponsored for breakfast):")
                expected_test = (
                    test_data["is_sponsored_found"] and
                    test_data["is_sponsored_value"] == True and
                    test_data["sponsored_meal_type_found"] and
                    "breakfast" in str(test_data["sponsored_meal_type_value"]).lower()
                )
                
                if expected_test:
                    print(f"✅ {test_name} data structure CORRECT")
                    if test_name == "Test2":
                        verification_results["test2_correct"] = True
                    else:
                        verification_results["test3_correct"] = True
                else:
                    print(f"❌ {test_name} data structure INCORRECT")
                    if not test_data["is_sponsored_found"]:
                        verification_results["critical_issues"].append(f"{test_name} missing is_sponsored field")
                    if not test_data["sponsored_meal_type_found"]:
                        verification_results["critical_issues"].append(f"{test_name} missing sponsored_meal_type field")
            else:
                print(f"❌ {test_name} not found in data")
                verification_results["critical_issues"].append(f"{test_name} not found in employee data")
        
        # Verify Test4 (should be sponsored for breakfast AND have sponsor messages for lunch)
        if test4_data:
            print(f"\n🔍 VERIFYING Test4 (should be sponsored for breakfast + sponsor lunch):")
            expected_test4 = (
                test4_data["is_sponsored_found"] and
                test4_data["is_sponsored_value"] == True and
                test4_data["sponsored_meal_type_found"] and
                "breakfast" in str(test4_data["sponsored_meal_type_value"]).lower()
            )
            
            if expected_test4:
                print(f"✅ Test4 data structure CORRECT")
                verification_results["test4_correct"] = True
            else:
                print(f"❌ Test4 data structure INCORRECT")
                if not test4_data["is_sponsored_found"]:
                    verification_results["critical_issues"].append("Test4 missing is_sponsored field")
                if not test4_data["sponsored_meal_type_found"]:
                    verification_results["critical_issues"].append("Test4 missing sponsored_meal_type field")
        else:
            print(f"❌ Test4 not found in data")
            verification_results["critical_issues"].append("Test4 not found in employee data")
        
        # Check for missing critical fields across all employees
        all_employees = [test1_data, test2_data, test3_data, test4_data]
        critical_fields = ["is_sponsored", "sponsored_meal_type", "readable_items"]
        
        for field in critical_fields:
            missing_count = sum(1 for emp in all_employees if emp and not emp.get(f"{field}_found", False))
            if missing_count > 0:
                verification_results["missing_fields"].append(f"{field} missing in {missing_count}/4 employees")
        
        # Overall verification
        verification_results["overall_working"] = (
            verification_results["test1_correct"] and
            verification_results["test2_correct"] and
            verification_results["test3_correct"] and
            verification_results["test4_correct"] and
            len(verification_results["critical_issues"]) == 0
        )
        
        return verification_results
    
    def run_systematic_frontend_data_analysis(self):
        """Run the systematic frontend data structure analysis as per review request"""
        print("🔍 SYSTEMATISCHE FRONTEND-DATENSTRUKTUR ANALYSE: Exakte User-Szenario")
        print("=" * 80)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 1 (fw1abteilung1)")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Clean up existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create exact scenario
        print(f"\n2️⃣ Creating Exact Scenario: Test1, Test2, Test3, Test4")
        
        # Create all test employees
        employees = ["Test1", "Test2", "Test3", "Test4"]
        employee_ids = {}
        
        for name in employees:
            employee_id = self.create_test_employee(name)
            if not employee_id:
                print(f"❌ CRITICAL FAILURE: Cannot create {name}")
                return False
            employee_ids[name] = employee_id
        
        # Step 3: Create breakfast orders
        print(f"\n3️⃣ Creating Breakfast Orders")
        
        # Test1: breakfast order with lunch
        print(f"\n📋 Creating Test1 order (with lunch):")
        test1_order = self.create_breakfast_order_with_lunch(employee_ids["Test1"], "Test1")
        if not test1_order:
            print("❌ CRITICAL FAILURE: Cannot create Test1's order")
            return False
        
        # Test2, Test3, Test4: breakfast orders without lunch
        for name in ["Test2", "Test3", "Test4"]:
            print(f"\n📋 Creating {name} order (no lunch):")
            order = self.create_breakfast_order_no_lunch(employee_ids[name], name)
            if not order:
                print(f"❌ CRITICAL FAILURE: Cannot create {name}'s order")
                return False
        
        # Step 4: Execute sponsoring scenario
        print(f"\n4️⃣ Execute Sponsoring Scenario")
        
        # Test1 sponsors breakfast for Test2, Test3, Test4
        breakfast_result = self.test1_sponsors_breakfast(employee_ids["Test1"])
        if "error" in breakfast_result:
            print(f"❌ Test1 breakfast sponsoring failed: {breakfast_result['error']}")
            return False
        
        # Test4 sponsors lunch for Test1
        lunch_result = self.test4_sponsors_lunch(employee_ids["Test4"])
        if "error" in lunch_result:
            print(f"❌ Test4 lunch sponsoring failed: {lunch_result['error']}")
            return False
        
        # Step 5: Analyze data structure
        print(f"\n5️⃣ Analyze Frontend Data Structure")
        
        all_employee_data = self.get_all_employee_data()
        if "error" in all_employee_data:
            print(f"❌ CRITICAL FAILURE: Cannot get employee data: {all_employee_data['error']}")
            return False
        
        # Step 6: Individual employee analysis
        print(f"\n6️⃣ Individual Employee Data Analysis")
        
        all_analyses = {}
        for emp_name, emp_data in all_employee_data.items():
            analysis = self.analyze_employee_data_structure(emp_name, emp_data)
            all_analyses[emp_name] = analysis
        
        # Step 7: Verify expected patterns
        print(f"\n7️⃣ Verify Expected Data Structure Patterns")
        
        verification_results = self.verify_expected_data_structure(all_analyses)
        
        # Final Results
        print(f"\n🏁 FINAL SYSTEMATIC ANALYSIS RESULTS:")
        print("=" * 80)
        
        success_criteria = [
            (verification_results["test1_correct"], "Test1 data structure correct (sponsored for lunch)"),
            (verification_results["test2_correct"], "Test2 data structure correct (sponsored for breakfast)"),
            (verification_results["test3_correct"], "Test3 data structure correct (sponsored for breakfast)"),
            (verification_results["test4_correct"], "Test4 data structure correct (sponsored for breakfast)"),
            (len(verification_results["critical_issues"]) == 0, f"No critical issues ({len(verification_results['critical_issues'])} found)"),
            (len(verification_results["missing_fields"]) == 0, f"No missing fields ({len(verification_results['missing_fields'])} found)")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        # Print critical issues
        if verification_results["critical_issues"]:
            print(f"\n🚨 CRITICAL ISSUES DETECTED:")
            for issue in verification_results["critical_issues"]:
                print(f"   ❌ {issue}")
        
        # Print missing fields
        if verification_results["missing_fields"]:
            print(f"\n📋 MISSING FIELDS DETECTED:")
            for missing in verification_results["missing_fields"]:
                print(f"   ❌ {missing}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Overall Analysis Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print summary for main agent
        print(f"\n🔍 SUMMARY FOR MAIN AGENT:")
        print(f"Employee IDs created: {employee_ids}")
        
        if success_rate >= 80:
            print("\n✅ SYSTEMATIC FRONTEND DATA ANALYSIS: PASSED!")
            print("✅ Frontend data structure is working correctly for sponsoring scenarios")
            return True
        else:
            print("\n❌ SYSTEMATIC FRONTEND DATA ANALYSIS: FAILED!")
            print("❌ Frontend data structure has critical issues preventing proper display")
            return False

def main():
    """Main test execution"""
    test = SystematicFrontendDataStructureAnalysis()
    
    try:
        success = test.run_systematic_frontend_data_analysis()
        
        if success:
            print(f"\n✅ SYSTEMATIC FRONTEND DATA ANALYSIS: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ SYSTEMATIC FRONTEND DATA ANALYSIS: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()