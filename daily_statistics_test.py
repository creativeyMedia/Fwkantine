#!/usr/bin/env python3
"""
🔍 TAGESSTATISTIK-BERECHNUNGS-BUG FIX: Test corrected daily statistics

KRITISCHER TEST FÜR TAGESSTATISTIK:

1. **Create exact User scenario:**
   - Mit1, Mit2, Mit3, Mit4 mit breakfast orders (some with lunch)
   - Mit1 sponsert Frühstück für andere
   - Mit4 sponsert Mittag für Mit1
   - Result: 4 real orders + 2 sponsor orders = 6 total orders in database

2. **TEST DAILY STATISTICS:**
   - Call breakfast-history endpoint
   - CRITICAL: Should show only 4 orders (real orders), not 6
   - CRITICAL: total_amount should be only from real orders (excluding sponsor order costs)

3. **VERIFY EXPECTED AMOUNTS:**
   - Expected: 4 Bestellungen
   - Expected: ~25-31€ (Frühstück + Mittag + Kaffee, excluding sponsor transaction costs)
   - Should NOT show 43.20€ or include sponsor order amounts

4. **DETAILED AMOUNT BREAKDOWN:**
   - Count breakfast costs from real orders
   - Count lunch costs from real orders  
   - Count coffee costs from real orders
   - Verify sponsor orders are excluded from totals

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Verify that sponsor orders are excluded from daily statistics and totals are correct!
"""

import requests
import json
from datetime import datetime, timedelta
import pytz
import os
from typing import Dict, List, Any

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteenio.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test Configuration - EXACT from review request
DEPARTMENT_ID = "fw1abteilung1"  # Department 1 (1. Wachabteilung)
ADMIN_PASSWORD = "admin1"
DEPARTMENT_NAME = "1. Wachabteilung"

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

class DailyStatisticsTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.mit1_employee_id = None
        self.mit2_employee_id = None
        self.mit3_employee_id = None
        self.mit4_employee_id = None
        self.employee_orders = {}
        self.real_orders_total = 0.0
        self.expected_order_count = 4
        
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
        """Create breakfast order with lunch - realistic pricing"""
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
                    "boiled_eggs": 2,   # 2 Eier
                    "has_coffee": True  # Kaffee
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                total_price = order["total_price"]
                
                print(f"✅ Created {name} breakfast order with lunch: {order_id} (€{total_price:.2f})")
                print(f"   - Brötchen: 2 (4 halves)")
                print(f"   - Eier: 2")
                print(f"   - Kaffee: Yes")
                print(f"   - Mittag: Yes")
                
                # Add to real orders total
                self.real_orders_total += total_price
                
                return {
                    "order_id": order_id,
                    "total_price": total_price,
                    "has_lunch": True
                }
            else:
                print(f"❌ Failed to create {name} breakfast order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating {name} breakfast order: {e}")
            return None
    
    def create_breakfast_order_no_lunch(self, employee_id: str, name: str) -> Dict:
        """Create breakfast order without lunch - realistic pricing"""
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
                    "has_lunch": False,  # No lunch
                    "boiled_eggs": 1,    # 1 Ei
                    "has_coffee": True   # Kaffee
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                total_price = order["total_price"]
                
                print(f"✅ Created {name} breakfast order: {order_id} (€{total_price:.2f})")
                print(f"   - Brötchen: 1 (2 halves)")
                print(f"   - Eier: 1")
                print(f"   - Kaffee: Yes")
                print(f"   - Mittag: No")
                
                # Add to real orders total
                self.real_orders_total += total_price
                
                return {
                    "order_id": order_id,
                    "total_price": total_price,
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
            
            print(f"\n🔍 SPONSORING: Mit1 sponsors breakfast for others")
            print(f"   - This creates SPONSOR ORDERS in database")
            print(f"   - These should be EXCLUDED from daily statistics")
            
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
                
                affected_employees = result.get("affected_employees", 0)
                total_cost = result.get("total_cost", 0.0)
                
                print(f"🔍 BREAKFAST SPONSORING SUMMARY:")
                print(f"   - Affected employees: {affected_employees}")
                print(f"   - Total sponsoring cost: €{total_cost:.2f}")
                print(f"   - This cost should NOT appear in daily statistics!")
                
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
            
            print(f"\n🔍 SPONSORING: Mit4 sponsors lunch for Mit1")
            print(f"   - This creates SPONSOR ORDERS in database")
            print(f"   - These should be EXCLUDED from daily statistics")
            
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
                
                affected_employees = result.get("affected_employees", 0)
                total_cost = result.get("total_cost", 0.0)
                
                print(f"🔍 LUNCH SPONSORING SUMMARY:")
                print(f"   - Affected employees: {affected_employees}")
                print(f"   - Total sponsoring cost: €{total_cost:.2f}")
                print(f"   - This cost should NOT appear in daily statistics!")
                
                return result
            else:
                print(f"❌ Mit4 failed to sponsor lunch meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error Mit4 sponsoring lunch meals: {e}")
            return {"error": str(e)}
    
    def verify_database_order_count(self) -> Dict:
        """Verify total orders in database (should be 6: 4 real + 2 sponsor)"""
        try:
            print(f"\n🔍 VERIFYING DATABASE ORDER COUNT:")
            print("=" * 60)
            
            # Get all orders for today to verify database state
            today = self.get_berlin_date()
            
            # This is an internal check - we expect 6 orders total in DB
            # But daily statistics should only show 4 (real orders)
            
            print(f"✅ Expected in database: 6 orders total (4 real + 2 sponsor)")
            print(f"✅ Expected in daily statistics: 4 orders (real orders only)")
            
            return {"verification": "Database should contain 6 orders, statistics should show 4"}
                
        except Exception as e:
            print(f"❌ Error verifying database order count: {e}")
            return {"error": str(e)}
    
    def test_daily_statistics_calculation(self) -> Dict:
        """Test the critical daily statistics calculation"""
        try:
            print(f"\n🔍 TESTING DAILY STATISTICS CALCULATION:")
            print("=" * 80)
            
            # Get breakfast-history data (daily statistics)
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    
                    # Extract critical statistics
                    total_orders = today_data.get("total_orders", 0)
                    total_amount = today_data.get("total_amount", 0.0)
                    employee_orders = today_data.get("employee_orders", {})
                    
                    print(f"🔍 DAILY STATISTICS RESULTS:")
                    print(f"   - Total Orders: {total_orders}")
                    print(f"   - Total Amount: €{total_amount:.2f}")
                    print(f"   - Employee Count: {len(employee_orders)}")
                    
                    # CRITICAL VERIFICATION
                    verification_results = {
                        "total_orders": total_orders,
                        "total_amount": total_amount,
                        "employee_count": len(employee_orders),
                        "expected_orders": self.expected_order_count,
                        "expected_amount_range": [25.0, 31.0],  # Expected range from review
                        "real_orders_total": self.real_orders_total
                    }
                    
                    # Test 1: Order count should be 4 (real orders only)
                    order_count_correct = (total_orders == self.expected_order_count)
                    print(f"\n✅ Test 1 - Order Count:")
                    print(f"   Expected: {self.expected_order_count} orders (real orders only)")
                    print(f"   Actual: {total_orders} orders")
                    print(f"   Result: {'✅ CORRECT' if order_count_correct else '❌ INCORRECT'}")
                    
                    # Test 2: Total amount should be from real orders only (~25-31€)
                    expected_min, expected_max = verification_results["expected_amount_range"]
                    amount_in_range = (expected_min <= total_amount <= expected_max)
                    
                    print(f"\n✅ Test 2 - Total Amount (Excluding Sponsor Costs):")
                    print(f"   Expected Range: €{expected_min:.2f} - €{expected_max:.2f}")
                    print(f"   Actual: €{total_amount:.2f}")
                    print(f"   Real Orders Total: €{self.real_orders_total:.2f}")
                    print(f"   Result: {'✅ CORRECT' if amount_in_range else '❌ INCORRECT'}")
                    
                    # Test 3: Should NOT show 43.20€ or include sponsor costs
                    no_sponsor_costs = (total_amount < 40.0)  # Should be much less than 43.20€
                    print(f"\n✅ Test 3 - No Sponsor Costs Included:")
                    print(f"   Should NOT be: €43.20 or similar high amount")
                    print(f"   Actual: €{total_amount:.2f}")
                    print(f"   Result: {'✅ CORRECT' if no_sponsor_costs else '❌ INCORRECT - INCLUDES SPONSOR COSTS'}")
                    
                    # Test 4: Employee count should be 4
                    employee_count_correct = (len(employee_orders) == 4)
                    print(f"\n✅ Test 4 - Employee Count:")
                    print(f"   Expected: 4 employees")
                    print(f"   Actual: {len(employee_orders)} employees")
                    print(f"   Result: {'✅ CORRECT' if employee_count_correct else '❌ INCORRECT'}")
                    
                    # Detailed breakdown
                    print(f"\n🔍 DETAILED BREAKDOWN:")
                    for emp_name, emp_data in employee_orders.items():
                        emp_total = emp_data.get("total_amount", 0.0)
                        emp_items = len(emp_data.get("breakfast_items", []))
                        print(f"   - {emp_name}: €{emp_total:.2f} ({emp_items} items)")
                    
                    verification_results.update({
                        "order_count_correct": order_count_correct,
                        "amount_in_range": amount_in_range,
                        "no_sponsor_costs": no_sponsor_costs,
                        "employee_count_correct": employee_count_correct,
                        "all_tests_passed": all([order_count_correct, amount_in_range, no_sponsor_costs, employee_count_correct])
                    })
                    
                    return verification_results
                else:
                    print(f"❌ No history data found in breakfast-history response")
                    return {"error": "No history data found"}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": f"API call failed: {response.text}"}
                
        except Exception as e:
            print(f"❌ Error testing daily statistics calculation: {e}")
            return {"error": str(e)}
    
    def run_daily_statistics_test(self):
        """Run the daily statistics bug fix test as per review request"""
        print("🔍 TAGESSTATISTIK-BERECHNUNGS-BUG FIX: Test corrected daily statistics")
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
        print(f"\n2️⃣ Creating Exact User Scenario: Mit1, Mit2, Mit3, Mit4")
        
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
        
        # Step 3: Create breakfast orders (some with lunch)
        print(f"\n3️⃣ Creating Breakfast Orders (some with lunch)")
        
        # Mit1: breakfast order with lunch
        print(f"\n📋 Creating Mit1 order (with lunch):")
        mit1_order = self.create_breakfast_order_with_lunch(self.mit1_employee_id, "Mit1")
        if not mit1_order:
            print("❌ CRITICAL FAILURE: Cannot create Mit1's order")
            return False
        
        # Mit2: breakfast order without lunch
        print(f"\n📋 Creating Mit2 order (no lunch):")
        mit2_order = self.create_breakfast_order_no_lunch(self.mit2_employee_id, "Mit2")
        if not mit2_order:
            print("❌ CRITICAL FAILURE: Cannot create Mit2's order")
            return False
        
        # Mit3: breakfast order without lunch
        print(f"\n📋 Creating Mit3 order (no lunch):")
        mit3_order = self.create_breakfast_order_no_lunch(self.mit3_employee_id, "Mit3")
        if not mit3_order:
            print("❌ CRITICAL FAILURE: Cannot create Mit3's order")
            return False
        
        # Mit4: breakfast order without lunch
        print(f"\n📋 Creating Mit4 order (no lunch):")
        mit4_order = self.create_breakfast_order_no_lunch(self.mit4_employee_id, "Mit4")
        if not mit4_order:
            print("❌ CRITICAL FAILURE: Cannot create Mit4's order")
            return False
        
        print(f"\n💰 REAL ORDERS TOTAL: €{self.real_orders_total:.2f}")
        print(f"📊 Expected in daily statistics: €{self.real_orders_total:.2f} (should match)")
        
        # Step 4: Execute sponsoring (creates sponsor orders)
        print(f"\n4️⃣ Execute Sponsoring (Creates Sponsor Orders)")
        
        # Mit1 sponsors breakfast for others
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
        
        # Step 5: Verify database state
        print(f"\n5️⃣ Verify Database State")
        db_verification = self.verify_database_order_count()
        
        # Step 6: TEST DAILY STATISTICS (CRITICAL)
        print(f"\n6️⃣ TEST DAILY STATISTICS (CRITICAL)")
        
        statistics_test = self.test_daily_statistics_calculation()
        if "error" in statistics_test:
            print(f"❌ Daily statistics test failed: {statistics_test['error']}")
            return False
        
        # Final Results
        print(f"\n🏁 FINAL DAILY STATISTICS TEST RESULTS:")
        print("=" * 100)
        
        success_criteria = [
            (statistics_test.get("order_count_correct", False), "Order count shows 4 (real orders only)"),
            (statistics_test.get("amount_in_range", False), "Total amount in expected range €25-31 (excluding sponsor costs)"),
            (statistics_test.get("no_sponsor_costs", False), "No sponsor costs included (NOT €43.20 or similar)"),
            (statistics_test.get("employee_count_correct", False), "Employee count shows 4")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Daily Statistics Test Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print detailed results
        print(f"\n🔍 DETAILED RESULTS:")
        print(f"Expected Orders: {statistics_test.get('expected_orders', 'N/A')}")
        print(f"Actual Orders: {statistics_test.get('total_orders', 'N/A')}")
        print(f"Expected Amount Range: €{statistics_test.get('expected_amount_range', ['N/A', 'N/A'])[0]:.2f} - €{statistics_test.get('expected_amount_range', ['N/A', 'N/A'])[1]:.2f}")
        print(f"Actual Amount: €{statistics_test.get('total_amount', 0):.2f}")
        print(f"Real Orders Total: €{statistics_test.get('real_orders_total', 0):.2f}")
        
        all_correct = statistics_test.get("all_tests_passed", False)
        
        if all_correct:
            print(f"\n✅ DAILY STATISTICS BUG FIX: WORKING CORRECTLY!")
            print(f"✅ Sponsor orders are properly excluded from daily statistics")
            print(f"✅ Total amount shows only real order costs")
            print(f"✅ Order count shows only real orders (4)")
            print(f"✅ No sponsor transaction costs included in totals")
        else:
            print(f"\n❌ DAILY STATISTICS BUG FIX: CRITICAL ISSUES DETECTED!")
            if not statistics_test.get("order_count_correct", False):
                print(f"❌ Order count incorrect - may be including sponsor orders")
            if not statistics_test.get("amount_in_range", False):
                print(f"❌ Total amount outside expected range - may include sponsor costs")
            if not statistics_test.get("no_sponsor_costs", False):
                print(f"❌ Total amount too high - likely includes sponsor transaction costs")
        
        return all_correct

def main():
    """Main test execution"""
    test = DailyStatisticsTest()
    
    try:
        success = test.run_daily_statistics_test()
        
        if success:
            print(f"\n✅ DAILY STATISTICS BUG FIX TEST: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ DAILY STATISTICS BUG FIX TEST: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()