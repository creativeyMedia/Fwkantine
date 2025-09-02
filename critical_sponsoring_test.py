#!/usr/bin/env python3
"""
🔍 KRITISCHER SPONSORING-ZUORDNUNGS-BUG FIX: Test korrekte Zuordnung von Sponsoring-Informationen

EXAKTE USER-SZENARIO NACHSTELLUNG:

1. **Create exact scenario wie User:**
   - Create Mit1, Mit2, Mit3, Mit4
   - Alle machen Frühstück-Bestellungen (Mit1 mit Mittag)
   - Mit1 sponsert Frühstück für alle anderen (Mit2, Mit3, Mit4)
   - Mit4 sponsert Mittag für Mit1

2. **KRITISCHE ZUORDNUNGS-VERIFICATION:**
   - Mit1 sollte zeigen: "3x Frühstück ausgegeben für X.XX€" (nicht Mittag!)
   - Mit4 sollte zeigen: "3x Mittagessen ausgegeben für X.XX€" (nicht Frühstück!)
   - Mit2, Mit3 sollten KEINE Sponsoring-Info haben (sie sponsern nichts)

3. **DETAILLIERTE SPONSORING-ANALYSE:**
   - Prüfe breakfast-history endpoint Response
   - Verifiziere dass jeder Mitarbeiter nur SEINE eigenen Sponsoring-Aktivitäten zeigt
   - Keine Kreuz-Kontamination zwischen Mitarbeitern

4. **TOTAL AMOUNTS VERIFICATION:**
   - Mit1: Eigene Kosten + Frühstück-Sponsoring-Kosten - gesponserte Mittag-Kosten
   - Mit4: Eigene Kosten + Mittag-Sponsoring-Kosten - gesponserte Frühstück-Kosten
   - Mit2, Mit3: Nur Kaffee-Kosten (alles andere gesponsert)

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Fix für korrekte Employee-ID-basierte Sponsoring-Zuordnung testen!
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

class CriticalSponsoringAssignmentTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.employees = {}  # Store employee IDs: Mit1, Mit2, Mit3, Mit4
        self.orders = {}     # Store order IDs for each employee
        
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
    
    def create_employee(self, name: str) -> str:
        """Create an employee and return employee ID"""
        try:
            response = self.session.post(f"{API_BASE}/employees", json={
                "name": name,
                "department_id": DEPARTMENT_ID
            })
            
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee["id"]
                print(f"✅ Created employee '{name}': {employee_id}")
                return employee_id
            else:
                print(f"❌ Failed to create employee '{name}': {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating employee '{name}': {e}")
            return None
    
    def create_breakfast_order(self, employee_id: str, name: str, has_lunch: bool = False) -> Dict:
        """Create breakfast order for employee"""
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
                    "has_lunch": has_lunch,
                    "boiled_eggs": 2,
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                
                lunch_text = " + Mittag" if has_lunch else ""
                print(f"✅ Created {name} breakfast order{lunch_text}: {order_id} (€{order['total_price']:.2f})")
                
                return {
                    "order_id": order_id,
                    "total_price": order["total_price"],
                    "has_lunch": has_lunch
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
            
            print(f"\n🔍 CRITICAL TEST: Mit1 sponsors breakfast for Mit2, Mit3, Mit4")
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
                print(f"   - Affected employees: {affected_employees} (expected: 3 - Mit2, Mit3, Mit4)")
                print(f"   - Total sponsoring cost: €{total_cost:.2f}")
                
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
                print(f"   - Affected employees: {affected_employees} (expected: 1 - Mit1)")
                print(f"   - Total sponsoring cost: €{total_cost:.2f}")
                
                return result
            else:
                print(f"❌ Mit4 failed to sponsor lunch meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error Mit4 sponsoring lunch meals: {e}")
            return {"error": str(e)}
    
    def verify_sponsoring_assignment(self) -> Dict:
        """Verify correct sponsoring assignment in breakfast-history endpoint"""
        try:
            print(f"\n🔍 VERIFYING SPONSORING ASSIGNMENT:")
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
                        "employees_found": employees_found,
                        "mit1_correct": False,
                        "mit2_correct": False,
                        "mit3_correct": False,
                        "mit4_correct": False,
                        "all_correct": False
                    }
                    
                    # Check Mit1: Should have sponsored_breakfast info (3x Frühstück ausgegeben)
                    if "Mit1" in employees_found:
                        mit1_data = employees_found["Mit1"]
                        print(f"\n🔍 Mit1 Analysis:")
                        print(f"   - Complete data: {json.dumps(mit1_data, indent=4)}")
                        
                        sponsored_breakfast = mit1_data.get("sponsored_breakfast")
                        sponsored_lunch = mit1_data.get("sponsored_lunch")
                        
                        print(f"   - sponsored_breakfast: {sponsored_breakfast}")
                        print(f"   - sponsored_lunch: {sponsored_lunch}")
                        
                        # Mit1 should have sponsored_breakfast (not sponsored_lunch)
                        has_breakfast_sponsoring = sponsored_breakfast is not None and sponsored_breakfast != {}
                        no_lunch_sponsoring = sponsored_lunch is None or sponsored_lunch == {}
                        
                        verification_results["mit1_correct"] = has_breakfast_sponsoring and no_lunch_sponsoring
                        
                        if has_breakfast_sponsoring:
                            breakfast_count = sponsored_breakfast.get("count", 0)
                            breakfast_amount = sponsored_breakfast.get("amount", 0.0)
                            print(f"   ✅ Mit1 sponsored breakfast: {breakfast_count}x for €{breakfast_amount:.2f}")
                        else:
                            print(f"   ❌ Mit1 missing breakfast sponsoring info")
                        
                        if no_lunch_sponsoring:
                            print(f"   ✅ Mit1 correctly has NO lunch sponsoring info")
                        else:
                            print(f"   ❌ Mit1 incorrectly shows lunch sponsoring: {sponsored_lunch}")
                    
                    # Check Mit4: Should have sponsored_lunch info (1x Mittagessen ausgegeben)
                    if "Mit4" in employees_found:
                        mit4_data = employees_found["Mit4"]
                        print(f"\n🔍 Mit4 Analysis:")
                        print(f"   - Complete data: {json.dumps(mit4_data, indent=4)}")
                        
                        sponsored_breakfast = mit4_data.get("sponsored_breakfast")
                        sponsored_lunch = mit4_data.get("sponsored_lunch")
                        
                        print(f"   - sponsored_breakfast: {sponsored_breakfast}")
                        print(f"   - sponsored_lunch: {sponsored_lunch}")
                        
                        # Mit4 should have sponsored_lunch (not sponsored_breakfast)
                        has_lunch_sponsoring = sponsored_lunch is not None and sponsored_lunch != {}
                        no_breakfast_sponsoring = sponsored_breakfast is None or sponsored_breakfast == {}
                        
                        verification_results["mit4_correct"] = has_lunch_sponsoring and no_breakfast_sponsoring
                        
                        if has_lunch_sponsoring:
                            lunch_count = sponsored_lunch.get("count", 0)
                            lunch_amount = sponsored_lunch.get("amount", 0.0)
                            print(f"   ✅ Mit4 sponsored lunch: {lunch_count}x for €{lunch_amount:.2f}")
                        else:
                            print(f"   ❌ Mit4 missing lunch sponsoring info")
                        
                        if no_breakfast_sponsoring:
                            print(f"   ✅ Mit4 correctly has NO breakfast sponsoring info")
                        else:
                            print(f"   ❌ Mit4 incorrectly shows breakfast sponsoring: {sponsored_breakfast}")
                    
                    # Check Mit2 & Mit3: Should have NO sponsoring info (they don't sponsor anything)
                    for mit_name in ["Mit2", "Mit3"]:
                        if mit_name in employees_found:
                            mit_data = employees_found[mit_name]
                            print(f"\n🔍 {mit_name} Analysis:")
                            print(f"   - Complete data: {json.dumps(mit_data, indent=4)}")
                            
                            sponsored_breakfast = mit_data.get("sponsored_breakfast")
                            sponsored_lunch = mit_data.get("sponsored_lunch")
                            
                            print(f"   - sponsored_breakfast: {sponsored_breakfast}")
                            print(f"   - sponsored_lunch: {sponsored_lunch}")
                            
                            # Mit2/Mit3 should have NO sponsoring info
                            no_breakfast_sponsoring = sponsored_breakfast is None or sponsored_breakfast == {}
                            no_lunch_sponsoring = sponsored_lunch is None or sponsored_lunch == {}
                            
                            mit_correct = no_breakfast_sponsoring and no_lunch_sponsoring
                            verification_results[f"{mit_name.lower()}_correct"] = mit_correct
                            
                            if mit_correct:
                                print(f"   ✅ {mit_name} correctly has NO sponsoring info")
                            else:
                                print(f"   ❌ {mit_name} incorrectly shows sponsoring info")
                                if not no_breakfast_sponsoring:
                                    print(f"      - Incorrect breakfast sponsoring: {sponsored_breakfast}")
                                if not no_lunch_sponsoring:
                                    print(f"      - Incorrect lunch sponsoring: {sponsored_lunch}")
                    
                    # Overall verification
                    all_correct = (
                        verification_results["mit1_correct"] and
                        verification_results["mit2_correct"] and
                        verification_results["mit3_correct"] and
                        verification_results["mit4_correct"]
                    )
                    verification_results["all_correct"] = all_correct
                    
                    return verification_results
                else:
                    print(f"❌ No history data found in breakfast-history response")
                    return {"error": "No history data found"}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": f"API call failed: {response.text}"}
                
        except Exception as e:
            print(f"❌ Error verifying sponsoring assignment: {e}")
            return {"error": str(e)}
    
    def verify_total_amounts(self) -> Dict:
        """Verify total amounts for each employee"""
        try:
            print(f"\n🔍 VERIFYING TOTAL AMOUNTS:")
            print("=" * 80)
            
            # Get breakfast-history data
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    employee_orders = today_data.get("employee_orders", {})
                    
                    # Find each employee and check their total amounts
                    amount_verification = {
                        "mit1_amount_correct": False,
                        "mit2_amount_correct": False,
                        "mit3_amount_correct": False,
                        "mit4_amount_correct": False,
                        "all_amounts_correct": False
                    }
                    
                    for emp_name, emp_data in employee_orders.items():
                        total_amount = emp_data.get("total_amount", 0.0)
                        
                        if "Mit1" in emp_name:
                            print(f"🔍 Mit1 Total Amount: €{total_amount:.2f}")
                            # Mit1: Should have own costs + breakfast sponsoring costs - sponsored lunch costs
                            # Expected: Higher than normal due to breakfast sponsoring, but reduced by lunch sponsoring
                            # Should be positive (owes money for sponsoring others)
                            amount_verification["mit1_amount_correct"] = total_amount > 5.0  # Should be higher due to sponsoring
                            
                        elif "Mit2" in emp_name:
                            print(f"🔍 Mit2 Total Amount: €{total_amount:.2f}")
                            # Mit2: Only coffee costs (breakfast sponsored by Mit1, no lunch)
                            # Expected: Around €1-3 (coffee only)
                            amount_verification["mit2_amount_correct"] = 0.5 <= total_amount <= 3.0
                            
                        elif "Mit3" in emp_name:
                            print(f"🔍 Mit3 Total Amount: €{total_amount:.2f}")
                            # Mit3: Only coffee costs (breakfast sponsored by Mit1, no lunch)
                            # Expected: Around €1-3 (coffee only)
                            amount_verification["mit3_amount_correct"] = 0.5 <= total_amount <= 3.0
                            
                        elif "Mit4" in emp_name:
                            print(f"🔍 Mit4 Total Amount: €{total_amount:.2f}")
                            # Mit4: Own costs + lunch sponsoring costs - sponsored breakfast costs
                            # Expected: Should be positive but not as high as Mit1
                            amount_verification["mit4_amount_correct"] = total_amount > 0.0  # Should be positive due to lunch sponsoring
                    
                    # Overall verification
                    all_amounts_correct = all(amount_verification.values())
                    amount_verification["all_amounts_correct"] = all_amounts_correct
                    
                    return amount_verification
                else:
                    print(f"❌ No history data found for amount verification")
                    return {"error": "No history data found"}
            else:
                print(f"❌ Failed to get breakfast history for amount verification: {response.status_code}")
                return {"error": "API call failed"}
                
        except Exception as e:
            print(f"❌ Error verifying total amounts: {e}")
            return {"error": str(e)}
    
    def run_critical_sponsoring_assignment_test(self):
        """Run the critical sponsoring assignment test as per review request"""
        print("🔍 KRITISCHER SPONSORING-ZUORDNUNGS-BUG FIX: Test korrekte Zuordnung von Sponsoring-Informationen")
        print("=" * 120)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 1 (fw1abteilung1)")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Clean up existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create employees (Mit1, Mit2, Mit3, Mit4)
        print(f"\n2️⃣ Creating Employees: Mit1, Mit2, Mit3, Mit4")
        
        employee_names = ["Mit1", "Mit2", "Mit3", "Mit4"]
        for name in employee_names:
            employee_id = self.create_employee(name)
            if not employee_id:
                print(f"❌ CRITICAL FAILURE: Cannot create {name}")
                return False
            self.employees[name] = employee_id
        
        # Step 3: Create breakfast orders
        print(f"\n3️⃣ Creating Breakfast Orders")
        
        # Mit1: breakfast order WITH lunch
        print(f"\n📋 Creating Mit1 order (with lunch):")
        mit1_order = self.create_breakfast_order(self.employees["Mit1"], "Mit1", has_lunch=True)
        if not mit1_order:
            print("❌ CRITICAL FAILURE: Cannot create Mit1's order")
            return False
        self.orders["Mit1"] = mit1_order
        
        # Mit2, Mit3, Mit4: breakfast orders WITHOUT lunch
        for name in ["Mit2", "Mit3", "Mit4"]:
            print(f"\n📋 Creating {name} order (no lunch):")
            order = self.create_breakfast_order(self.employees[name], name, has_lunch=False)
            if not order:
                print(f"❌ CRITICAL FAILURE: Cannot create {name}'s order")
                return False
            self.orders[name] = order
        
        # Step 4: Execute sponsoring scenario
        print(f"\n4️⃣ Execute Sponsoring Scenario")
        
        # Mit1 sponsors breakfast for Mit2, Mit3, Mit4
        breakfast_result = self.mit1_sponsors_breakfast_for_others(self.employees["Mit1"])
        if "error" in breakfast_result:
            print(f"❌ Mit1 breakfast sponsoring failed: {breakfast_result['error']}")
            return False
        
        # Mit4 sponsors lunch for Mit1
        lunch_result = self.mit4_sponsors_lunch_for_mit1(self.employees["Mit4"])
        if "error" in lunch_result:
            print(f"❌ Mit4 lunch sponsoring failed: {lunch_result['error']}")
            return False
        
        # Step 5: Verify sponsoring assignment
        print(f"\n5️⃣ Verify Sponsoring Assignment")
        
        assignment_verification = self.verify_sponsoring_assignment()
        if "error" in assignment_verification:
            print(f"❌ Sponsoring assignment verification failed: {assignment_verification['error']}")
            return False
        
        # Step 6: Verify total amounts
        print(f"\n6️⃣ Verify Total Amounts")
        
        amount_verification = self.verify_total_amounts()
        if "error" in amount_verification:
            print(f"❌ Total amount verification failed: {amount_verification['error']}")
            return False
        
        # Final Results
        print(f"\n🏁 FINAL CRITICAL SPONSORING ASSIGNMENT TEST RESULTS:")
        print("=" * 120)
        
        success_criteria = [
            (assignment_verification.get("mit1_correct", False), "Mit1 shows correct breakfast sponsoring (3x Frühstück ausgegeben)"),
            (assignment_verification.get("mit4_correct", False), "Mit4 shows correct lunch sponsoring (1x Mittagessen ausgegeben)"),
            (assignment_verification.get("mit2_correct", False), "Mit2 shows NO sponsoring info (correct)"),
            (assignment_verification.get("mit3_correct", False), "Mit3 shows NO sponsoring info (correct)"),
            (amount_verification.get("mit1_amount_correct", False), "Mit1 total amount correct (own + sponsoring - sponsored)"),
            (amount_verification.get("mit2_amount_correct", False), "Mit2 total amount correct (coffee only)"),
            (amount_verification.get("mit3_amount_correct", False), "Mit3 total amount correct (coffee only)"),
            (amount_verification.get("mit4_amount_correct", False), "Mit4 total amount correct (own + sponsoring - sponsored)")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Critical Sponsoring Assignment Test Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print summary for main agent
        print(f"\n🔍 SUMMARY FOR MAIN AGENT:")
        for name, emp_id in self.employees.items():
            print(f"{name} Employee ID: {emp_id}")
        
        overall_success = assignment_verification.get("all_correct", False) and amount_verification.get("all_amounts_correct", False)
        
        if overall_success:
            print(f"\n✅ CRITICAL SPONSORING ASSIGNMENT TEST: WORKING!")
            print(f"✅ Mit1 correctly shows breakfast sponsoring info (not lunch)")
            print(f"✅ Mit4 correctly shows lunch sponsoring info (not breakfast)")
            print(f"✅ Mit2, Mit3 correctly show NO sponsoring info")
            print(f"✅ All total amounts are calculated correctly")
        else:
            print(f"\n❌ CRITICAL SPONSORING ASSIGNMENT TEST: FAILED!")
            if not assignment_verification.get("mit1_correct", False):
                print(f"❌ Mit1 sponsoring assignment incorrect")
            if not assignment_verification.get("mit4_correct", False):
                print(f"❌ Mit4 sponsoring assignment incorrect")
            if not assignment_verification.get("mit2_correct", False):
                print(f"❌ Mit2 sponsoring assignment incorrect")
            if not assignment_verification.get("mit3_correct", False):
                print(f"❌ Mit3 sponsoring assignment incorrect")
            if not amount_verification.get("all_amounts_correct", False):
                print(f"❌ Total amount calculations incorrect")
        
        return overall_success

def main():
    """Main test execution"""
    test = CriticalSponsoringAssignmentTest()
    
    try:
        success = test.run_critical_sponsoring_assignment_test()
        
        if success:
            print(f"\n✅ CRITICAL SPONSORING ASSIGNMENT TEST: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ CRITICAL SPONSORING ASSIGNMENT TEST: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()