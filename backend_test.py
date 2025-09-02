#!/usr/bin/env python3
"""
🔍 DETAILLIERTE TOTAL-BERECHNUNGS-ANALYSE: Debug warum 24.30€ statt 31.00€

KRITISCHE BERECHNUNG-DEBUG:

1. **User's Expected Scenario:**
   - Mit1: €7.60 (0.50 + 0.60 + 1.50 + 5.00)
   - Mit2: €7.60 (same as Mit1)
   - Mit3: €7.60 (same as Mit1)  
   - Mit4: €8.20 (1.00 + 0.60 + 1.50 + 5.00)
   - EXPECTED TOTAL: €31.00

2. **BACKEND SHOWS:**
   - Total: €24.30 (WRONG - missing €6.70)
   - Breakfast Revenue: €5.00 (should be €4.90 without coffee)
   - Lunch Revenue: €20.00 (correct)

3. **DETAILED ORDER ANALYSIS:**
   - Get breakfast-history response
   - Show EXACT total_price for each order  
   - Show EXACT calculation for each employee
   - Identify where the missing €6.70 goes

4. **SPONSORING IMPACT ANALYSIS:**
   - Check if sponsored orders affect total calculation
   - Verify that real_orders filtering works correctly
   - Check if sponsored amounts are incorrectly subtracted from totals

5. **COFFEE CALCULATION CHECK:**
   - Coffee should be EXCLUDED from breakfast revenue (per user request)
   - But coffee should be INCLUDED in daily total (€6.00 total coffee)
   - Verify coffee is counted in daily total but not breakfast revenue

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Find exactly where the missing €6.70 went and why totals don't match!
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

class TotalCalculationDebugAnalysis:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.mit1_employee_id = None
        self.mit2_employee_id = None
        self.mit3_employee_id = None
        self.mit4_employee_id = None
        self.employee_orders = {}
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
    
    def create_exact_user_scenario_orders(self):
        """Create the EXACT orders from user's expected scenario"""
        
        # Set lunch price to 5.00 as expected by user
        today = self.get_berlin_date()
        print(f"\n🔧 Setting lunch price to €5.00 for {today}")
        
        try:
            response = self.session.put(f"{API_BASE}/daily-lunch-settings/{DEPARTMENT_ID}/{today}", 
                                      json={"lunch_price": 5.00})
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
                        "expected": 7.60
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
                    "expected": 8.20
                }
                print(f"✅ Created Mit4 order: €{order['total_price']:.2f} (expected €8.20)")
            else:
                print(f"❌ Failed to create Mit4 order: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating Mit4 order: {e}")
            return None
        
        return orders_created
    
    def analyze_breakfast_history_totals(self):
        """Analyze breakfast-history endpoint for total calculation issues"""
        try:
            print(f"\n🔍 ANALYZING BREAKFAST-HISTORY TOTALS:")
            print("=" * 80)
            
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    
                    # Extract key totals
                    total_orders = today_data.get("total_orders", 0)
                    total_amount = today_data.get("total_amount", 0.0)
                    breakfast_summary = today_data.get("breakfast_summary", {})
                    employee_orders = today_data.get("employee_orders", {})
                    
                    print(f"📊 DAILY TOTALS FROM BREAKFAST-HISTORY:")
                    print(f"   - Total Orders: {total_orders}")
                    print(f"   - Total Amount: €{total_amount:.2f}")
                    print(f"   - Expected Total: €{self.expected_grand_total:.2f}")
                    print(f"   - Difference: €{abs(total_amount - self.expected_grand_total):.2f}")
                    
                    if breakfast_summary:
                        print(f"\n📊 BREAKFAST SUMMARY:")
                        for key, value in breakfast_summary.items():
                            print(f"   - {key}: {value}")
                    
                    print(f"\n🔍 INDIVIDUAL EMPLOYEE ANALYSIS:")
                    individual_total = 0.0
                    
                    for emp_name, emp_data in employee_orders.items():
                        emp_total = emp_data.get("total_amount", 0.0)
                        individual_total += emp_total
                        
                        # Find expected total for this employee
                        expected = 0.0
                        for expected_name, expected_total in self.expected_totals.items():
                            if expected_name in emp_name:
                                expected = expected_total
                                break
                        
                        difference = abs(emp_total - expected)
                        status = "✅" if difference < 0.01 else "❌"
                        
                        print(f"   {status} {emp_name}: €{emp_total:.2f} (expected €{expected:.2f}, diff: €{difference:.2f})")
                        
                        # Show detailed breakdown if available
                        if "breakfast_items" in emp_data:
                            items = emp_data["breakfast_items"]
                            print(f"      Items: {len(items)} breakfast items")
                            for i, item in enumerate(items):
                                print(f"        Item {i+1}: {item}")
                    
                    print(f"\n📊 CALCULATION VERIFICATION:")
                    print(f"   - Sum of Individual Totals: €{individual_total:.2f}")
                    print(f"   - Daily Total from API: €{total_amount:.2f}")
                    print(f"   - Expected Grand Total: €{self.expected_grand_total:.2f}")
                    
                    # Check for discrepancies
                    individual_vs_daily = abs(individual_total - total_amount)
                    daily_vs_expected = abs(total_amount - self.expected_grand_total)
                    
                    print(f"\n🔍 DISCREPANCY ANALYSIS:")
                    print(f"   - Individual vs Daily Total: €{individual_vs_daily:.2f}")
                    print(f"   - Daily vs Expected Total: €{daily_vs_expected:.2f}")
                    
                    if individual_vs_daily > 0.01:
                        print(f"   ❌ CRITICAL: Individual totals don't match daily total!")
                    
                    if daily_vs_expected > 0.01:
                        print(f"   ❌ CRITICAL: Daily total doesn't match expected total!")
                        print(f"   🔍 Missing amount: €{self.expected_grand_total - total_amount:.2f}")
                    
                    return {
                        "total_orders": total_orders,
                        "total_amount": total_amount,
                        "individual_total": individual_total,
                        "expected_total": self.expected_grand_total,
                        "missing_amount": self.expected_grand_total - total_amount,
                        "employee_data": employee_orders
                    }
                else:
                    print(f"❌ No history data found")
                    return {"error": "No history data"}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": f"API call failed: {response.text}"}
                
        except Exception as e:
            print(f"❌ Error analyzing breakfast history: {e}")
            return {"error": str(e)}
    
    def analyze_separated_revenue(self):
        """Analyze separated revenue endpoints"""
        try:
            print(f"\n🔍 ANALYZING SEPARATED REVENUE:")
            print("=" * 80)
            
            today = self.get_berlin_date()
            
            # Check daily revenue
            response = self.session.get(f"{API_BASE}/orders/daily-revenue/{DEPARTMENT_ID}/{today}")
            
            if response.status_code == 200:
                revenue_data = response.json()
                
                breakfast_revenue = revenue_data.get("breakfast_revenue", 0.0)
                lunch_revenue = revenue_data.get("lunch_revenue", 0.0)
                total_orders = revenue_data.get("total_orders", 0)
                
                print(f"📊 SEPARATED REVENUE ANALYSIS:")
                print(f"   - Breakfast Revenue: €{breakfast_revenue:.2f}")
                print(f"   - Lunch Revenue: €{lunch_revenue:.2f}")
                print(f"   - Total Revenue: €{breakfast_revenue + lunch_revenue:.2f}")
                print(f"   - Total Orders: {total_orders}")
                
                # Expected breakdown:
                # Breakfast (without coffee): Mit1,2,3: (0.50+0.60)*3 = 3.30, Mit4: (1.00+0.60) = 1.60, Total: 4.90
                # Lunch: 4 * 5.00 = 20.00
                # Coffee: 4 * 1.50 = 6.00 (should be excluded from breakfast revenue)
                
                expected_breakfast = 4.90  # Rolls + eggs only
                expected_lunch = 20.00     # 4 * 5.00
                expected_coffee = 6.00     # 4 * 1.50 (excluded from revenue)
                
                print(f"\n🔍 EXPECTED BREAKDOWN:")
                print(f"   - Expected Breakfast Revenue: €{expected_breakfast:.2f} (rolls + eggs only)")
                print(f"   - Expected Lunch Revenue: €{expected_lunch:.2f} (4 * €5.00)")
                print(f"   - Expected Coffee (excluded): €{expected_coffee:.2f} (4 * €1.50)")
                print(f"   - Expected Total Revenue: €{expected_breakfast + expected_lunch:.2f}")
                
                breakfast_diff = abs(breakfast_revenue - expected_breakfast)
                lunch_diff = abs(lunch_revenue - expected_lunch)
                
                print(f"\n🔍 REVENUE VERIFICATION:")
                breakfast_status = "✅" if breakfast_diff < 0.01 else "❌"
                lunch_status = "✅" if lunch_diff < 0.01 else "❌"
                
                print(f"   {breakfast_status} Breakfast Revenue: €{breakfast_revenue:.2f} vs €{expected_breakfast:.2f} (diff: €{breakfast_diff:.2f})")
                print(f"   {lunch_status} Lunch Revenue: €{lunch_revenue:.2f} vs €{expected_lunch:.2f} (diff: €{lunch_diff:.2f})")
                
                return {
                    "breakfast_revenue": breakfast_revenue,
                    "lunch_revenue": lunch_revenue,
                    "total_revenue": breakfast_revenue + lunch_revenue,
                    "expected_breakfast": expected_breakfast,
                    "expected_lunch": expected_lunch,
                    "breakfast_correct": breakfast_diff < 0.01,
                    "lunch_correct": lunch_diff < 0.01
                }
            else:
                print(f"❌ Failed to get daily revenue: {response.status_code} - {response.text}")
                return {"error": f"Daily revenue API failed: {response.text}"}
                
        except Exception as e:
            print(f"❌ Error analyzing separated revenue: {e}")
            return {"error": str(e)}
    
    def run_total_calculation_debug(self):
        """Run the complete total calculation debug analysis"""
        print("🔍 DETAILLIERTE TOTAL-BERECHNUNGS-ANALYSE")
        print("=" * 100)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 1 (fw1abteilung1)")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Clean up existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create employees
        print(f"\n2️⃣ Creating Test Employees")
        
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
        
        # Step 3: Create exact user scenario orders
        print(f"\n3️⃣ Creating EXACT User Scenario Orders")
        
        orders_created = self.create_exact_user_scenario_orders()
        if not orders_created:
            print("❌ CRITICAL FAILURE: Cannot create orders")
            return False
        
        # Step 4: Analyze breakfast-history totals
        print(f"\n4️⃣ Analyzing Breakfast-History Totals")
        
        history_analysis = self.analyze_breakfast_history_totals()
        if "error" in history_analysis:
            print(f"❌ History analysis failed: {history_analysis['error']}")
            return False
        
        # Step 5: Analyze separated revenue
        print(f"\n5️⃣ Analyzing Separated Revenue")
        
        revenue_analysis = self.analyze_separated_revenue()
        if "error" in revenue_analysis:
            print(f"❌ Revenue analysis failed: {revenue_analysis['error']}")
            return False
        
        # Final Results
        print(f"\n🏁 FINAL TOTAL CALCULATION DEBUG RESULTS:")
        print("=" * 100)
        
        # Check if totals match expectations
        total_amount = history_analysis.get("total_amount", 0.0)
        missing_amount = history_analysis.get("missing_amount", 0.0)
        
        success_criteria = [
            (abs(missing_amount) < 0.01, f"Daily total matches expected (€{total_amount:.2f} vs €{self.expected_grand_total:.2f})"),
            (revenue_analysis.get("breakfast_correct", False), f"Breakfast revenue correct (€{revenue_analysis.get('breakfast_revenue', 0):.2f} vs €{revenue_analysis.get('expected_breakfast', 0):.2f})"),
            (revenue_analysis.get("lunch_correct", False), f"Lunch revenue correct (€{revenue_analysis.get('lunch_revenue', 0):.2f} vs €{revenue_analysis.get('expected_lunch', 0):.2f})")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Total Calculation Debug Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print detailed findings
        print(f"\n🔍 DETAILED FINDINGS:")
        if abs(missing_amount) > 0.01:
            print(f"❌ CRITICAL BUG CONFIRMED: Missing €{abs(missing_amount):.2f} from daily total")
            print(f"   - Expected: €{self.expected_grand_total:.2f}")
            print(f"   - Actual: €{total_amount:.2f}")
            print(f"   - This matches the user's report of €24.30 vs €31.00 (missing €6.70)")
        
        if not revenue_analysis.get("breakfast_correct", False):
            print(f"❌ Breakfast revenue calculation issue detected")
        
        if not revenue_analysis.get("lunch_correct", False):
            print(f"❌ Lunch revenue calculation issue detected")
        
        all_correct = all(test for test, _ in success_criteria)
        
        if all_correct:
            print(f"\n✅ TOTAL CALCULATION: WORKING CORRECTLY!")
        else:
            print(f"\n❌ TOTAL CALCULATION: CRITICAL ISSUES DETECTED!")
            print(f"❌ The user's report of missing €6.70 appears to be confirmed")
        
        return all_correct

def main():
    """Main test execution"""
    test = TotalCalculationDebugAnalysis()
    
    try:
        success = test.run_total_calculation_debug()
        
        if success:
            print(f"\n✅ TOTAL CALCULATION DEBUG: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ TOTAL CALCULATION DEBUG: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()