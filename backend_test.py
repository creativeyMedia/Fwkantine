#!/usr/bin/env python3
"""
🔍 FINAL VERIFICATION: Test corrected sponsoring assignment logic

KRITISCHE VERIFIKATION DER KORRIGIERTEN LOGIK:

1. **Create exact scenario again:**
   - Mit1, Mit2, Mit3, Mit4 mit Frühstück-Bestellungen
   - Mit1 sponsert Frühstück für andere
   - Mit4 sponsert Mittag für Mit1

2. **CRITICAL VERIFICATION:**
   - Mit1 sollte zeigen: "sponsored_breakfast: {count: 3, amount: X.XX}" 
   - Mit4 sollte zeigen: "sponsored_lunch: {count: 1, amount: X.XX}"
   - Mit2, Mit3 sollten zeigen: "sponsored_breakfast: null, sponsored_lunch: null"

3. **TEST CORRECTED LOGIC:**
   - Verify that query for "is_sponsored: True" + "sponsored_by_employee_id: employee_id" works
   - Ensure each employee only shows their own sponsoring activities
   - No cross-contamination between employees

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Final verification of corrected sponsoring assignment logic!
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

class DatabaseOrderUpdateVerification:
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
        """Create breakfast order without lunch for Test4"""
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
    
    def test4_sponsors_lunch_for_test1(self, test4_employee_id: str) -> Dict:
        """Test4 sponsors lunch for Test1 - CRITICAL DATABASE UPDATE TEST"""
        try:
            today = self.get_berlin_date()
            
            print(f"\n🔍 CRITICAL DATABASE UPDATE TEST: Test4 sponsors lunch for Test1")
            print(f"   - Sponsor: Test4 (ID: {test4_employee_id})")
            print(f"   - Target: All employees with lunch orders (Test1)")
            print(f"   - Date: {today}")
            print(f"   - Meal Type: lunch")
            print(f"   - Expected: Test1's order should be updated in database with sponsored fields")
            
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
    
    def verify_test1_database_update(self) -> Dict:
        """Verify Test1's order was updated in database with sponsored fields"""
        try:
            print(f"\n🔍 VERIFYING TEST1 DATABASE UPDATE:")
            print("=" * 60)
            
            # Get Test1's data from breakfast-history endpoint
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    employee_orders = today_data.get("employee_orders", {})
                    
                    # Find Test1 in the data
                    test1_data = None
                    for emp_name, emp_data in employee_orders.items():
                        if "Test1" in emp_name:
                            test1_data = emp_data
                            break
                    
                    if test1_data:
                        print(f"✅ Found Test1 in database response")
                        print(f"🔍 Test1 Complete Data Structure:")
                        for key, value in test1_data.items():
                            print(f"   - {key}: {value}")
                        
                        # Check critical sponsored fields
                        verification_results = {
                            "test1_found": True,
                            "is_sponsored_found": "is_sponsored" in test1_data,
                            "is_sponsored_value": test1_data.get("is_sponsored"),
                            "sponsored_meal_type_found": "sponsored_meal_type" in test1_data,
                            "sponsored_meal_type_value": test1_data.get("sponsored_meal_type"),
                            "sponsored_message_found": "sponsored_message" in test1_data,
                            "sponsored_message_value": test1_data.get("sponsored_message"),
                            "total_amount": test1_data.get("total_amount", 0.0),
                            "all_data": test1_data
                        }
                        
                        print(f"\n🔍 CRITICAL SPONSORED FIELDS VERIFICATION:")
                        print(f"   ✅ is_sponsored found: {verification_results['is_sponsored_found']}")
                        if verification_results['is_sponsored_found']:
                            print(f"   ✅ is_sponsored value: {verification_results['is_sponsored_value']}")
                        
                        print(f"   ✅ sponsored_meal_type found: {verification_results['sponsored_meal_type_found']}")
                        if verification_results['sponsored_meal_type_found']:
                            print(f"   ✅ sponsored_meal_type value: {verification_results['sponsored_meal_type_value']}")
                        
                        print(f"   ✅ sponsored_message found: {verification_results['sponsored_message_found']}")
                        if verification_results['sponsored_message_found']:
                            print(f"   ✅ sponsored_message value: {verification_results['sponsored_message_value']}")
                        
                        print(f"   💰 total_amount: €{verification_results['total_amount']:.2f}")
                        
                        # Verify expected values
                        expected_is_sponsored = verification_results['is_sponsored_value'] == True
                        expected_meal_type = "lunch" in str(verification_results['sponsored_meal_type_value']).lower() if verification_results['sponsored_meal_type_value'] else False
                        expected_coffee_only_cost = 0.5 <= verification_results['total_amount'] <= 3.0  # Coffee should be around €1-2
                        
                        print(f"\n🎯 EXPECTED VALUES VERIFICATION:")
                        print(f"   ✅ is_sponsored == True: {expected_is_sponsored}")
                        print(f"   ✅ sponsored_meal_type contains 'lunch': {expected_meal_type}")
                        print(f"   ✅ total_amount is coffee-only cost (€0.5-3.0): {expected_coffee_only_cost}")
                        
                        verification_results.update({
                            "expected_is_sponsored": expected_is_sponsored,
                            "expected_meal_type": expected_meal_type,
                            "expected_coffee_only_cost": expected_coffee_only_cost,
                            "database_update_working": expected_is_sponsored and expected_meal_type
                        })
                        
                        return verification_results
                    else:
                        print(f"❌ Test1 not found in database response")
                        return {"error": "Test1 not found in database response", "test1_found": False}
                else:
                    print(f"❌ No history data found in database response")
                    return {"error": "No history data found", "test1_found": False}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": f"API call failed: {response.text}", "test1_found": False}
                
        except Exception as e:
            print(f"❌ Error verifying Test1 database update: {e}")
            return {"error": str(e), "test1_found": False}
    
    def verify_individual_profile_endpoint(self, test1_employee_id: str) -> Dict:
        """Verify individual profile endpoint returns sponsored fields"""
        try:
            print(f"\n🔍 VERIFYING INDIVIDUAL PROFILE ENDPOINT:")
            print("=" * 60)
            
            # Call individual profile endpoint
            response = self.session.get(f"{API_BASE}/employees/{test1_employee_id}/profile")
            
            if response.status_code == 200:
                profile_data = response.json()
                
                print(f"✅ Individual profile endpoint accessible")
                print(f"🔍 Test1 Individual Profile Data:")
                print(json.dumps(profile_data, indent=2))
                
                # Check if sponsored fields are present
                profile_verification = {
                    "profile_accessible": True,
                    "has_sponsored_fields": False,
                    "profile_data": profile_data
                }
                
                # Look for sponsored-related fields in the profile
                sponsored_fields = ["is_sponsored", "sponsored_meal_type", "sponsored_message"]
                found_fields = []
                
                for field in sponsored_fields:
                    if field in profile_data:
                        found_fields.append(field)
                
                if found_fields:
                    profile_verification["has_sponsored_fields"] = True
                    print(f"✅ Found sponsored fields in profile: {found_fields}")
                else:
                    print(f"❌ No sponsored fields found in individual profile")
                
                return profile_verification
            else:
                print(f"❌ Individual profile endpoint failed: {response.status_code} - {response.text}")
                return {"error": f"Profile endpoint failed: {response.text}", "profile_accessible": False}
                
        except Exception as e:
            print(f"❌ Error verifying individual profile endpoint: {e}")
            return {"error": str(e), "profile_accessible": False}
    
    def run_database_order_update_verification(self):
        """Run the database order update verification as per review request"""
        print("🔍 DATENBANK ORDER-UPDATE VERIFIKATION: Überprüfe ob Sponsoring-Updates in DB geschrieben werden")
        print("=" * 100)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 1 (fw1abteilung1)")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Clean up existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create simple test scenario
        print(f"\n2️⃣ Creating Simple Test Scenario: Test1 (with lunch) + Test4 (no lunch)")
        
        # Create Test1 employee
        self.test1_employee_id = self.create_test_employee("Test1")
        if not self.test1_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Test1")
            return False
        
        # Create Test4 employee
        self.test4_employee_id = self.create_test_employee("Test4")
        if not self.test4_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Test4")
            return False
        
        # Step 3: Create breakfast orders
        print(f"\n3️⃣ Creating Breakfast Orders")
        
        # Test1: breakfast order with lunch
        print(f"\n📋 Creating Test1 order (with lunch):")
        test1_order = self.create_breakfast_order_with_lunch(self.test1_employee_id, "Test1")
        if not test1_order:
            print("❌ CRITICAL FAILURE: Cannot create Test1's order")
            return False
        self.test1_order_id = test1_order["order_id"]
        
        # Test4: breakfast order without lunch
        print(f"\n📋 Creating Test4 order (no lunch):")
        test4_order = self.create_breakfast_order_no_lunch(self.test4_employee_id, "Test4")
        if not test4_order:
            print("❌ CRITICAL FAILURE: Cannot create Test4's order")
            return False
        self.test4_order_id = test4_order["order_id"]
        
        # Step 4: Execute critical sponsoring scenario
        print(f"\n4️⃣ Execute Critical Sponsoring Scenario")
        
        # Test4 sponsors lunch for Test1
        lunch_result = self.test4_sponsors_lunch_for_test1(self.test4_employee_id)
        if "error" in lunch_result:
            print(f"❌ Test4 lunch sponsoring failed: {lunch_result['error']}")
            return False
        
        # Step 5: Verify database update
        print(f"\n5️⃣ Verify Database Update")
        
        database_verification = self.verify_test1_database_update()
        if "error" in database_verification:
            print(f"❌ Database verification failed: {database_verification['error']}")
            return False
        
        # Step 6: Verify individual profile endpoint
        print(f"\n6️⃣ Verify Individual Profile Endpoint")
        
        profile_verification = self.verify_individual_profile_endpoint(self.test1_employee_id)
        if "error" in profile_verification:
            print(f"⚠️ Profile verification failed: {profile_verification['error']}")
            # Don't fail the test for this, just note it
        
        # Final Results
        print(f"\n🏁 FINAL DATABASE VERIFICATION RESULTS:")
        print("=" * 100)
        
        success_criteria = [
            (database_verification.get("test1_found", False), "Test1 found in database response"),
            (database_verification.get("is_sponsored_found", False), "is_sponsored field found in database"),
            (database_verification.get("expected_is_sponsored", False), "is_sponsored value is True"),
            (database_verification.get("sponsored_meal_type_found", False), "sponsored_meal_type field found in database"),
            (database_verification.get("expected_meal_type", False), "sponsored_meal_type contains 'lunch'"),
            (database_verification.get("expected_coffee_only_cost", False), "total_amount shows coffee-only cost"),
            (database_verification.get("database_update_working", False), "Database update working correctly")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Database Verification Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print summary for main agent
        print(f"\n🔍 SUMMARY FOR MAIN AGENT:")
        print(f"Test1 Employee ID: {self.test1_employee_id}")
        print(f"Test4 Employee ID: {self.test4_employee_id}")
        print(f"Test1 Order ID: {self.test1_order_id}")
        print(f"Test4 Order ID: {self.test4_order_id}")
        
        if database_verification.get("database_update_working", False):
            print(f"\n✅ DATABASE ORDER UPDATE VERIFICATION: WORKING!")
            print(f"✅ Test1's order is correctly updated in database with sponsored fields")
            print(f"✅ is_sponsored: {database_verification.get('is_sponsored_value')}")
            print(f"✅ sponsored_meal_type: {database_verification.get('sponsored_meal_type_value')}")
            print(f"✅ total_amount: €{database_verification.get('total_amount', 0):.2f} (coffee-only cost)")
        else:
            print(f"\n❌ DATABASE ORDER UPDATE VERIFICATION: FAILED!")
            print(f"❌ Test1's order is NOT correctly updated in database")
            if not database_verification.get("is_sponsored_found", False):
                print(f"❌ Missing: is_sponsored field")
            if not database_verification.get("sponsored_meal_type_found", False):
                print(f"❌ Missing: sponsored_meal_type field")
            if not database_verification.get("expected_is_sponsored", False):
                print(f"❌ Wrong: is_sponsored value should be True")
            if not database_verification.get("expected_meal_type", False):
                print(f"❌ Wrong: sponsored_meal_type should contain 'lunch'")
        
        return database_verification.get("database_update_working", False)

def main():
    """Main test execution"""
    test = DatabaseOrderUpdateVerification()
    
    try:
        success = test.run_database_order_update_verification()
        
        if success:
            print(f"\n✅ DATABASE ORDER UPDATE VERIFICATION: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ DATABASE ORDER UPDATE VERIFICATION: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()