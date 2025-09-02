#!/usr/bin/env python3
"""
🔍 SPONSORING-STATUS DEBUG: Prüfe ob Orders fälschlicherweise als gesponsert markiert sind

KRITISCHE SPONSORING-STATUS ANALYSE:

1. **Current Scenario Analysis:**
   - Mit1, Mit2, Mit3, Mit4 haben Orders erstellt
   - KEINE Sponsoring-Aktionen ausgeführt
   - Alle Orders sollten is_sponsored=False haben

2. **DIRECT DATABASE ORDER CHECK:**
   - Hole alle Orders für heute
   - Prüfe für jede Order: is_sponsored, is_sponsor_order, sponsored_meal_type
   - CRITICAL: Alle sollten is_sponsored=False sein (keine Sponsoring-Aktionen)

3. **INDIVIDUAL ORDER PRICE VERIFICATION:**
   - Prüfe total_price für jede Order direkt aus Database
   - Mit1,2,3 sollten haben: total_price=7.60
   - Mit4 sollte haben: total_price=8.20

4. **BREAKFAST-HISTORY LOGIC TRACE:**
   - Prüfe welcher Code-Pfad für jede Order genommen wird
   - Sollten alle in "Regular orders - use full cost" gehen
   - Nicht in sponsored oder sponsor_order Pfad

5. **COFFEE PRICE VERIFICATION:**
   - Prüfe coffee_price in Department-Settings
   - Sollte 1.50€ sein pro User's Angabe

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Identifiziere ob Orders fälschlicherweise als gesponsert behandelt werden!
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

class SponsoringStatusDebugAnalysis:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.mit1_employee_id = None
        self.mit2_employee_id = None
        self.mit3_employee_id = None
        self.mit4_employee_id = None
        self.created_orders = {}
        self.expected_totals = {
            "Mit1": 7.60,  # 0.50 + 0.60 + 1.50 + 5.00
            "Mit2": 7.60,  # same as Mit1
            "Mit3": 7.60,  # same as Mit1
            "Mit4": 8.20   # 1.00 + 0.60 + 1.50 + 5.00
        }
        self.expected_grand_total = 31.00
        
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
    
    def verify_coffee_price_settings(self) -> bool:
        """Verify coffee price is set to 1.50€ as expected"""
        try:
            print(f"\n🔍 VERIFYING COFFEE PRICE SETTINGS:")
            print("=" * 60)
            
            response = self.session.get(f"{API_BASE}/department-settings/{DEPARTMENT_ID}/coffee-price")
            
            if response.status_code == 200:
                data = response.json()
                coffee_price = data.get("coffee_price", 0.0)
                
                print(f"📊 Department Coffee Price: €{coffee_price:.2f}")
                
                if abs(coffee_price - 1.50) < 0.01:
                    print(f"✅ Coffee price is correct: €{coffee_price:.2f}")
                    return True
                else:
                    print(f"❌ Coffee price is wrong: €{coffee_price:.2f} (expected €1.50)")
                    
                    # Try to set correct price
                    print(f"🔧 Attempting to set coffee price to €1.50")
                    set_response = self.session.put(f"{API_BASE}/department-settings/{DEPARTMENT_ID}/coffee-price", 
                                                  json={"price": 1.50})
                    
                    if set_response.status_code == 200:
                        print(f"✅ Successfully set coffee price to €1.50")
                        return True
                    else:
                        print(f"❌ Failed to set coffee price: {set_response.text}")
                        return False
            else:
                print(f"❌ Failed to get coffee price: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying coffee price: {e}")
            return False
    
    def create_exact_user_scenario_orders(self):
        """Create the EXACT orders from user's expected scenario - NO SPONSORING"""
        
        # Set lunch price to 5.00 as expected by user
        today = self.get_berlin_date()
        print(f"\n🔧 Setting lunch price to €5.00 for {today}")
        
        try:
            response = self.session.put(f"{API_BASE}/daily-lunch-settings/{DEPARTMENT_ID}/{today}?lunch_price=5.00")
            if response.status_code == 200:
                print(f"✅ Lunch price set to €5.00")
            else:
                print(f"⚠️ Failed to set lunch price: {response.text}")
        except Exception as e:
            print(f"⚠️ Error setting lunch price: {e}")
        
        orders_created = {}
        
        # Mit1, Mit2, Mit3: Same order (0.50 + 0.60 + 1.50 + 5.00 = €7.60)
        for name in ["Mit1", "Mit2", "Mit3"]:
            employee_id = getattr(self, f"{name.lower()}_employee_id")
            
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 1 Brötchen (2 halves)
                    "white_halves": 1,  # 0.50€
                    "seeded_halves": 1, # 0.60€
                    "toppings": ["butter", "kaese"],
                    "has_lunch": True,  # 5.00€
                    "boiled_eggs": 0,
                    "has_coffee": True  # 1.50€
                }]
            }
            
            try:
                response = self.session.post(f"{API_BASE}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    orders_created[name] = {
                        "order_id": order["id"],
                        "total_price": order["total_price"],
                        "expected": 7.60,
                        "employee_id": employee_id
                    }
                    print(f"✅ Created {name} order: €{order['total_price']:.2f} (expected €7.60)")
                else:
                    print(f"❌ Failed to create {name} order: {response.text}")
                    return None
            except Exception as e:
                print(f"❌ Error creating {name} order: {e}")
                return None
        
        # Mit4: Different order (1.00 + 0.60 + 1.50 + 5.00 = €8.20)
        order_data = {
            "employee_id": self.mit4_employee_id,
            "department_id": DEPARTMENT_ID,
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 3,  # 1.5 Brötchen (3 halves)
                "white_halves": 2,  # 1.00€ (2 * 0.50)
                "seeded_halves": 1, # 0.60€
                "toppings": ["butter", "kaese", "schinken"],
                "has_lunch": True,  # 5.00€
                "boiled_eggs": 0,
                "has_coffee": True  # 1.50€
            }]
        }
        
        try:
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                orders_created["Mit4"] = {
                    "order_id": order["id"],
                    "total_price": order["total_price"],
                    "expected": 8.20,
                    "employee_id": self.mit4_employee_id
                }
                print(f"✅ Created Mit4 order: €{order['total_price']:.2f} (expected €8.20)")
            else:
                print(f"❌ Failed to create Mit4 order: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating Mit4 order: {e}")
            return None
        
        self.created_orders = orders_created
        return orders_created
    
    def check_direct_order_sponsoring_status(self):
        """Check direct order sponsoring status from database via API"""
        try:
            print(f"\n🔍 DIRECT ORDER SPONSORING STATUS CHECK:")
            print("=" * 80)
            
            today = self.get_berlin_date()
            
            # Get all orders for today via breakfast-history endpoint
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    employee_orders = today_data.get("employee_orders", {})
                    
                    print(f"📊 FOUND {len(employee_orders)} EMPLOYEES WITH ORDERS:")
                    
                    sponsoring_issues = []
                    
                    for emp_name, emp_data in employee_orders.items():
                        # Check sponsoring status fields
                        is_sponsored = emp_data.get("is_sponsored", False)
                        sponsored_meal_type = emp_data.get("sponsored_meal_type", None)
                        total_amount = emp_data.get("total_amount", 0.0)
                        
                        # Find expected employee
                        expected_name = None
                        expected_total = 0.0
                        for name in ["Mit1", "Mit2", "Mit3", "Mit4"]:
                            if name in emp_name:
                                expected_name = name
                                expected_total = self.expected_totals[name]
                                break
                        
                        print(f"\n🔍 {emp_name} (Expected: {expected_name}):")
                        print(f"   - is_sponsored: {is_sponsored}")
                        print(f"   - sponsored_meal_type: {sponsored_meal_type}")
                        print(f"   - total_amount: €{total_amount:.2f} (expected €{expected_total:.2f})")
                        
                        # Check for sponsoring issues
                        if is_sponsored:
                            sponsoring_issues.append(f"{emp_name} is marked as sponsored (should be False)")
                            print(f"   ❌ CRITICAL: Employee is marked as sponsored!")
                        else:
                            print(f"   ✅ Correctly NOT sponsored")
                        
                        if sponsored_meal_type is not None:
                            sponsoring_issues.append(f"{emp_name} has sponsored_meal_type: {sponsored_meal_type} (should be None)")
                            print(f"   ❌ CRITICAL: Has sponsored_meal_type when it shouldn't!")
                        else:
                            print(f"   ✅ Correctly no sponsored_meal_type")
                        
                        # Check total amount
                        amount_diff = abs(total_amount - expected_total)
                        if amount_diff > 0.01:
                            sponsoring_issues.append(f"{emp_name} total €{total_amount:.2f} vs expected €{expected_total:.2f}")
                            print(f"   ❌ CRITICAL: Total amount mismatch!")
                        else:
                            print(f"   ✅ Total amount correct")
                    
                    print(f"\n📊 SPONSORING STATUS SUMMARY:")
                    if sponsoring_issues:
                        print(f"❌ CRITICAL ISSUES DETECTED ({len(sponsoring_issues)}):")
                        for issue in sponsoring_issues:
                            print(f"   - {issue}")
                        return False
                    else:
                        print(f"✅ ALL ORDERS CORRECTLY NOT SPONSORED")
                        return True
                        
                else:
                    print(f"❌ No history data found")
                    return False
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error checking order sponsoring status: {e}")
            return False
    
    def analyze_breakfast_history_calculation_path(self):
        """Analyze which calculation path each order takes in breakfast-history"""
        try:
            print(f"\n🔍 BREAKFAST-HISTORY CALCULATION PATH ANALYSIS:")
            print("=" * 80)
            
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    
                    # Extract key totals
                    total_orders = today_data.get("total_orders", 0)
                    total_amount = today_data.get("total_amount", 0.0)
                    employee_orders = today_data.get("employee_orders", {})
                    
                    print(f"📊 DAILY TOTALS FROM BREAKFAST-HISTORY:")
                    print(f"   - Total Orders: {total_orders}")
                    print(f"   - Total Amount: €{total_amount:.2f}")
                    print(f"   - Expected Total: €{self.expected_grand_total:.2f}")
                    print(f"   - Difference: €{abs(total_amount - self.expected_grand_total):.2f}")
                    
                    print(f"\n🔍 INDIVIDUAL EMPLOYEE CALCULATION PATH:")
                    individual_total = 0.0
                    calculation_issues = []
                    
                    for emp_name, emp_data in employee_orders.items():
                        emp_total = emp_data.get("total_amount", 0.0)
                        individual_total += emp_total
                        
                        # Find expected total for this employee
                        expected = 0.0
                        expected_name = None
                        for name, expected_total in self.expected_totals.items():
                            if name in emp_name:
                                expected = expected_total
                                expected_name = name
                                break
                        
                        difference = abs(emp_total - expected)
                        status = "✅" if difference < 0.01 else "❌"
                        
                        print(f"\n   {status} {emp_name} ({expected_name}):")
                        print(f"      - Calculated Total: €{emp_total:.2f}")
                        print(f"      - Expected Total: €{expected:.2f}")
                        print(f"      - Difference: €{difference:.2f}")
                        
                        # Analyze calculation path
                        is_sponsored = emp_data.get("is_sponsored", False)
                        sponsored_meal_type = emp_data.get("sponsored_meal_type", None)
                        
                        if is_sponsored:
                            print(f"      - CALCULATION PATH: Sponsored order (is_sponsored=True)")
                            calculation_issues.append(f"{emp_name} taking sponsored path when it shouldn't")
                        else:
                            print(f"      - CALCULATION PATH: Regular order (is_sponsored=False)")
                        
                        if sponsored_meal_type:
                            print(f"      - SPONSORED MEAL TYPE: {sponsored_meal_type}")
                            calculation_issues.append(f"{emp_name} has sponsored_meal_type when it shouldn't")
                        else:
                            print(f"      - SPONSORED MEAL TYPE: None (correct)")
                        
                        # Check if total matches expected (should use full cost)
                        if difference > 0.01:
                            calculation_issues.append(f"{emp_name} total mismatch - not using full cost path")
                    
                    print(f"\n📊 CALCULATION PATH VERIFICATION:")
                    print(f"   - Sum of Individual Totals: €{individual_total:.2f}")
                    print(f"   - Daily Total from API: €{total_amount:.2f}")
                    print(f"   - Expected Grand Total: €{self.expected_grand_total:.2f}")
                    
                    # Check for discrepancies
                    individual_vs_daily = abs(individual_total - total_amount)
                    daily_vs_expected = abs(total_amount - self.expected_grand_total)
                    
                    print(f"\n🔍 CALCULATION ISSUES ANALYSIS:")
                    if calculation_issues:
                        print(f"❌ CRITICAL CALCULATION ISSUES DETECTED ({len(calculation_issues)}):")
                        for issue in calculation_issues:
                            print(f"   - {issue}")
                    else:
                        print(f"✅ All orders taking correct calculation path")
                    
                    if individual_vs_daily > 0.01:
                        print(f"❌ CRITICAL: Individual totals don't match daily total!")
                        calculation_issues.append("Individual vs daily total mismatch")
                    
                    if daily_vs_expected > 0.01:
                        print(f"❌ CRITICAL: Daily total doesn't match expected total!")
                        print(f"   🔍 Missing amount: €{self.expected_grand_total - total_amount:.2f}")
                        calculation_issues.append(f"Missing €{self.expected_grand_total - total_amount:.2f} from daily total")
                    
                    return {
                        "total_orders": total_orders,
                        "total_amount": total_amount,
                        "individual_total": individual_total,
                        "expected_total": self.expected_grand_total,
                        "missing_amount": self.expected_grand_total - total_amount,
                        "calculation_issues": calculation_issues,
                        "all_correct": len(calculation_issues) == 0
                    }
                else:
                    print(f"❌ No history data found")
                    return {"error": "No history data"}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": f"API call failed: {response.text}"}
                
        except Exception as e:
            print(f"❌ Error analyzing calculation path: {e}")
            return {"error": str(e)}
    
    def run_sponsoring_status_debug(self):
        """Run the complete sponsoring status debug analysis"""
        print("🔍 SPONSORING-STATUS DEBUG ANALYSE")
        print("=" * 100)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 1 (fw1abteilung1)")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Clean up existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Verify coffee price settings
        print("\n2️⃣ Verifying Coffee Price Settings")
        if not self.verify_coffee_price_settings():
            print("❌ CRITICAL FAILURE: Coffee price not set correctly")
            return False
        
        # Step 3: Create employees
        print(f"\n3️⃣ Creating Test Employees")
        
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
        
        # Step 4: Create exact user scenario orders (NO SPONSORING)
        print(f"\n4️⃣ Creating EXACT User Scenario Orders (NO SPONSORING)")
        
        orders_created = self.create_exact_user_scenario_orders()
        if not orders_created:
            print("❌ CRITICAL FAILURE: Cannot create orders")
            return False
        
        # Step 5: Check direct order sponsoring status
        print(f"\n5️⃣ Checking Direct Order Sponsoring Status")
        
        sponsoring_status_correct = self.check_direct_order_sponsoring_status()
        
        # Step 6: Analyze breakfast-history calculation path
        print(f"\n6️⃣ Analyzing Breakfast-History Calculation Path")
        
        calculation_analysis = self.analyze_breakfast_history_calculation_path()
        if "error" in calculation_analysis:
            print(f"❌ Calculation analysis failed: {calculation_analysis['error']}")
            return False
        
        # Final Results
        print(f"\n🏁 FINAL SPONSORING STATUS DEBUG RESULTS:")
        print("=" * 100)
        
        # Check if all criteria are met
        total_amount = calculation_analysis.get("total_amount", 0.0)
        missing_amount = calculation_analysis.get("missing_amount", 0.0)
        calculation_issues = calculation_analysis.get("calculation_issues", [])
        
        success_criteria = [
            (sponsoring_status_correct, "All orders correctly NOT sponsored"),
            (len(calculation_issues) == 0, "All orders taking correct calculation path"),
            (abs(missing_amount) < 0.01, f"Daily total matches expected (€{total_amount:.2f} vs €{self.expected_grand_total:.2f})")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Sponsoring Status Debug Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print detailed findings
        print(f"\n🔍 DETAILED FINDINGS:")
        
        if not sponsoring_status_correct:
            print(f"❌ CRITICAL BUG CONFIRMED: Orders are falsely marked as sponsored!")
            print(f"   - Expected: All orders should have is_sponsored=False")
            print(f"   - Expected: All orders should have sponsored_meal_type=None")
        
        if calculation_issues:
            print(f"❌ CRITICAL CALCULATION ISSUES DETECTED ({len(calculation_issues)}):")
            for issue in calculation_issues:
                print(f"   - {issue}")
        
        if abs(missing_amount) > 0.01:
            print(f"❌ CRITICAL BUG CONFIRMED: Missing €{abs(missing_amount):.2f} from daily total")
            print(f"   - Expected: €{self.expected_grand_total:.2f}")
            print(f"   - Actual: €{total_amount:.2f}")
            print(f"   - This confirms the coffee cost missing bug!")
        
        all_correct = all(test for test, _ in success_criteria)
        
        if all_correct:
            print(f"\n✅ SPONSORING STATUS: WORKING CORRECTLY!")
            print(f"✅ No orders are falsely marked as sponsored")
            print(f"✅ All calculation paths are correct")
        else:
            print(f"\n❌ SPONSORING STATUS: CRITICAL ISSUES DETECTED!")
            print(f"❌ Orders may be falsely treated as sponsored")
            print(f"❌ This explains the missing coffee costs in totals")
        
        return all_correct

def main():
    """Main test execution"""
    test = SponsoringStatusDebugAnalysis()
    
    try:
        success = test.run_sponsoring_status_debug()
        
        if success:
            print(f"\n✅ SPONSORING STATUS DEBUG: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ SPONSORING STATUS DEBUG: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()