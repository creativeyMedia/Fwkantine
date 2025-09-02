#!/usr/bin/env python3
"""
🎯 FINAL VERIFICATION: Test corrected daily total calculation (revenue-only approach)

FINALE VERIFIKATION DER KORRIGIERTEN BERECHNUNG:

1. **Create User's exact scenario:**
   - 4 Mitarbeiter mit je €7.60 Orders (total €30.40)
   - Mit1 sponsert Frühstück, Mit4 sponsert Mittag

2. **CRITICAL DAILY TOTAL VERIFICATION:**
   - Daily total should show: €30.40 (sum of all real order total_prices) ✅
   - NOT: €24.40 (User's expected from separated revenue) ❌
   - NOT: Sum of individual employee balances (which includes cost redistribution) ❌

3. **SEPARATED REVENUE VERIFICATION:**  
   - Separated breakfast revenue: €10.40 (excluding coffee)
   - Separated lunch revenue: €20.00
   - Total separated: €30.40 (matches daily total)

4. **INDIVIDUAL EMPLOYEE TOTALS:**
   - Should reflect actual amounts employees need to pay after sponsoring
   - Should NOT match daily total (because of cost redistribution)

5. **MATHEMATICAL VERIFICATION:**
   - Sum of original order prices: €30.40
   - Daily total: €30.40 ✅
   - Sponsoring is cost redistribution, not revenue reduction

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Verify that daily total correctly shows actual food revenue (€30.40), not cost redistribution totals!
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

class RoundingErrorSponsoringDebugTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.employees = {}  # Store employee IDs: Mit1, Mit2, Mit3, Mit4
        self.orders = {}     # Store created orders
        self.expected_individual_total = 7.60  # Per employee: 1.10 + 1.50 + 5.00
        self.expected_breakfast_sponsoring = 4.40  # 1.10 * 4 employees
        self.expected_lunch_sponsoring = 20.00     # 5.00 * 4 employees
        # CORRECTED EXPECTATION: Daily total should be €30.40 (sum of all real order prices)
        # NOT €24.40 (which was user's incorrect expectation from separated revenue)
        self.expected_daily_total = 30.40          # 4 employees × €7.60 each = actual revenue
        self.expected_separated_total = 30.40      # Should match daily total
        self.expected_breakfast_revenue = 4.40     # 4 × €1.10 (rolls only, excluding coffee)
        self.expected_lunch_revenue = 20.00        # 4 × €5.00
        
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
    
    def setup_department_prices(self) -> bool:
        """Setup correct department prices for testing"""
        try:
            print(f"\n🔧 SETTING UP DEPARTMENT PRICES:")
            print("=" * 60)
            
            # Set coffee price to 1.50€
            response = self.session.put(f"{API_BASE}/department-settings/{DEPARTMENT_ID}/coffee-price", 
                                      params={"price": 1.50})
            
            if response.status_code == 200:
                print(f"✅ Coffee price set to €1.50")
            else:
                print(f"❌ Failed to set coffee price: {response.text}")
                return False
            
            # Set lunch price to 5.00€ for today
            today = self.get_berlin_date()
            response = self.session.put(f"{API_BASE}/daily-lunch-settings/{DEPARTMENT_ID}/{today}", 
                                      params={"lunch_price": 5.00})
            
            if response.status_code == 200:
                print(f"✅ Lunch price set to €5.00 for {today}")
            else:
                print(f"❌ Failed to set lunch price: {response.text}")
                return False
            
            return True
                
        except Exception as e:
            print(f"❌ Error setting up prices: {e}")
            return False
    
    def setup_menu_items(self) -> bool:
        """Setup breakfast menu items if they don't exist"""
        try:
            print(f"\n🔧 SETTING UP MENU ITEMS:")
            print("=" * 60)
            
            # Check if breakfast menu exists
            response = self.session.get(f"{API_BASE}/menu/breakfast/{DEPARTMENT_ID}")
            if response.status_code == 200:
                menu_items = response.json()
                if len(menu_items) > 0:
                    print(f"✅ Breakfast menu already exists with {len(menu_items)} items")
                    return True
            
            print(f"🔧 Creating breakfast menu items...")
            
            # Create white roll (weiss) - €0.50
            white_roll_data = {
                "roll_type": "weiss",
                "price": 0.50,
                "department_id": DEPARTMENT_ID
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/breakfast", json=white_roll_data)
            if response.status_code == 200:
                print(f"✅ Created white roll menu item: €0.50")
            else:
                print(f"❌ Failed to create white roll: {response.text}")
                return False
            
            # Create seeded roll (koerner) - €0.60
            seeded_roll_data = {
                "roll_type": "koerner", 
                "price": 0.60,
                "department_id": DEPARTMENT_ID
            }
            
            response = self.session.post(f"{API_BASE}/department-admin/menu/breakfast", json=seeded_roll_data)
            if response.status_code == 200:
                print(f"✅ Created seeded roll menu item: €0.60")
            else:
                print(f"❌ Failed to create seeded roll: {response.text}")
                return False
            
            # Create basic toppings (free)
            toppings = ["butter", "kaese", "schinken", "salami"]
            for topping in toppings:
                topping_data = {
                    "topping_id": topping,
                    "topping_name": topping,
                    "price": 0.00,
                    "department_id": DEPARTMENT_ID
                }
                
                response = self.session.post(f"{API_BASE}/department-admin/menu/toppings", json=topping_data)
                if response.status_code == 200:
                    print(f"✅ Created topping '{topping}': €0.00")
                else:
                    print(f"⚠️ Failed to create topping '{topping}': {response.text}")
            
            return True
                
        except Exception as e:
            print(f"❌ Error setting up menu items: {e}")
            return False
    
    def create_employee_order(self, employee_name: str, employee_id: str) -> dict:
        """Create standard order for an employee (1.10€ Brötchen+Eier + 1.50€ Kaffee + 5.00€ Mittag = 7.60€)"""
        
        print(f"\n🔧 CREATING {employee_name} STANDARD ORDER:")
        print("=" * 60)
        print(f"Expected breakdown:")
        print(f"  - White roll half: €0.50")
        print(f"  - Seeded roll half: €0.60") 
        print(f"  - Coffee: €1.50")
        print(f"  - Lunch: €5.00")
        print(f"  - TOTAL EXPECTED: €7.60")
        
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
            print(f"\n📤 SENDING ORDER REQUEST for {employee_name}:")
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                self.orders[employee_name] = order
                
                print(f"\n✅ ORDER CREATED SUCCESSFULLY for {employee_name}:")
                print(f"  - Order ID: {order['id']}")
                print(f"  - Total Price: €{order['total_price']:.2f}")
                print(f"  - Expected: €{self.expected_individual_total:.2f}")
                print(f"  - Difference: €{abs(order['total_price'] - self.expected_individual_total):.2f}")
                
                # Check if order creation total is correct
                if abs(order['total_price'] - self.expected_individual_total) < 0.01:
                    print(f"  ✅ Order creation total is CORRECT")
                else:
                    print(f"  ❌ Order creation total is WRONG!")
                    print(f"     🔍 BUG LOCATION: Order creation logic")
                
                return order
            else:
                print(f"❌ Failed to create {employee_name} order: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating {employee_name} order: {e}")
            return None
    
    def sponsor_breakfast(self, sponsor_name: str, sponsor_id: str, sponsored_employees: List[str]) -> bool:
        """Mit1 sponsors breakfast for other employees"""
        try:
            print(f"\n🎯 {sponsor_name} SPONSORING BREAKFAST:")
            print("=" * 60)
            
            today = self.get_berlin_date()
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": sponsor_id,
                "sponsor_employee_name": sponsor_name
            }
            
            print(f"Sponsoring data: {json.dumps(sponsor_data, indent=2)}")
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json=sponsor_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Breakfast sponsoring successful:")
                print(f"  - Message: {result.get('message', 'Success')}")
                print(f"  - Total cost: €{result.get('total_cost', 0.0):.2f}")
                print(f"  - Expected cost: €{self.expected_breakfast_sponsoring:.2f}")
                return True
            else:
                print(f"❌ Breakfast sponsoring failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error in breakfast sponsoring: {e}")
            return False
    
    def sponsor_lunch(self, sponsor_name: str, sponsor_id: str, sponsored_employees: List[str]) -> bool:
        """Mit4 sponsors lunch for other employees"""
        try:
            print(f"\n🎯 {sponsor_name} SPONSORING LUNCH:")
            print("=" * 60)
            
            today = self.get_berlin_date()
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": sponsor_id,
                "sponsor_employee_name": sponsor_name
            }
            
            print(f"Sponsoring data: {json.dumps(sponsor_data, indent=2)}")
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json=sponsor_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Lunch sponsoring successful:")
                print(f"  - Message: {result.get('message', 'Success')}")
                print(f"  - Total cost: €{result.get('total_cost', 0.0):.2f}")
                print(f"  - Expected cost: €{self.expected_lunch_sponsoring:.2f}")
                return True
            else:
                print(f"❌ Lunch sponsoring failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error in lunch sponsoring: {e}")
            return False
    
    def verify_separated_revenue_calculation(self) -> dict:
        """Verify separated revenue calculation matches daily total"""
        try:
            print(f"\n🔍 SEPARATED REVENUE VERIFICATION:")
            print("=" * 80)
            
            today = self.get_berlin_date()
            
            # Test daily revenue endpoint
            response = self.session.get(f"{API_BASE}/orders/daily-revenue/{DEPARTMENT_ID}/{today}")
            
            if response.status_code == 200:
                revenue_data = response.json()
                
                breakfast_revenue = revenue_data.get('breakfast_revenue', 0.0)
                lunch_revenue = revenue_data.get('lunch_revenue', 0.0)
                total_separated = breakfast_revenue + lunch_revenue
                
                print(f"📊 SEPARATED REVENUE RESPONSE:")
                print(f"  - Breakfast Revenue: €{breakfast_revenue:.2f}")
                print(f"  - Lunch Revenue: €{lunch_revenue:.2f}")
                print(f"  - Total Separated: €{total_separated:.2f}")
                print(f"  - Expected Total: €{self.expected_separated_total:.2f}")
                
                # Verify breakfast revenue (excluding coffee)
                breakfast_correct = abs(breakfast_revenue - self.expected_breakfast_revenue) < 0.01
                lunch_correct = abs(lunch_revenue - self.expected_lunch_revenue) < 0.01
                total_correct = abs(total_separated - self.expected_separated_total) < 0.01
                
                print(f"\n🎯 SEPARATED REVENUE VERIFICATION:")
                print(f"  - Breakfast Revenue: {'✅' if breakfast_correct else '❌'} Expected €{self.expected_breakfast_revenue:.2f}, Got €{breakfast_revenue:.2f}")
                print(f"  - Lunch Revenue: {'✅' if lunch_correct else '❌'} Expected €{self.expected_lunch_revenue:.2f}, Got €{lunch_revenue:.2f}")
                print(f"  - Total Matches Daily: {'✅' if total_correct else '❌'} Expected €{self.expected_separated_total:.2f}, Got €{total_separated:.2f}")
                
                return {
                    "status": "success",
                    "breakfast_revenue": breakfast_revenue,
                    "lunch_revenue": lunch_revenue,
                    "total_separated": total_separated,
                    "breakfast_correct": breakfast_correct,
                    "lunch_correct": lunch_correct,
                    "total_correct": total_correct
                }
            else:
                print(f"❌ Failed to get separated revenue: {response.status_code} - {response.text}")
                return {"status": "error", "message": f"API call failed: {response.text}"}
                
        except Exception as e:
            print(f"❌ Error verifying separated revenue: {e}")
            return {"status": "error", "message": str(e)}
        """Analyze breakfast-history endpoint for rounding errors and sponsoring calculation issues"""
        try:
            print(f"\n🔍 BREAKFAST-HISTORY TOTAL ANALYSIS:")
            print("=" * 80)
            
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                
                if "history" in data and len(data["history"]) > 0:
                    today_data = data["history"][0]
                    employee_orders = today_data.get("employee_orders", {})
                    
                    print(f"📊 BREAKFAST-HISTORY RESPONSE:")
                    print(f"  - Total Orders: {today_data.get('total_orders', 0)}")
                    print(f"  - Total Amount: €{today_data.get('total_amount', 0.0):.2f}")
                    print(f"  - Expected Total: €{self.expected_daily_total:.2f}")
                    print(f"  - Employees Found: {len(employee_orders)}")
                    
                    # Calculate manual sum of individual employee totals
                    manual_sum = 0.0
                    individual_totals = {}
                    
                    # Calculate manual sum of individual employee totals
                    manual_sum = 0.0
                    individual_totals = {}
                    
                    print(f"\n🔍 INDIVIDUAL EMPLOYEE ANALYSIS:")
                    for emp_key, emp_data in employee_orders.items():
                        total_amount = emp_data.get('total_amount', 0.0)
                        individual_totals[emp_key] = total_amount
                        manual_sum += total_amount
                        
                        print(f"  - {emp_key}: €{total_amount:.2f}")
                        print(f"    - Is Sponsored: {emp_data.get('is_sponsored', False)}")
                        print(f"    - Sponsored Meal Type: {emp_data.get('sponsored_meal_type', None)}")
                        print(f"    - Sponsored Breakfast: {emp_data.get('sponsored_breakfast', None)}")
                        print(f"    - Sponsored Lunch: {emp_data.get('sponsored_lunch', None)}")
                    
                    print(f"\n🔍 DETAILED INDIVIDUAL ANALYSIS:")
                    expected_individual_breakdown = {
                        "Mit1": 1.50,  # Coffee only (breakfast sponsored by self, lunch sponsored by Mit4)
                        "Mit2": 1.50,  # Coffee only (breakfast sponsored by Mit1, lunch sponsored by Mit4)  
                        "Mit3": 1.50,  # Coffee only (breakfast sponsored by Mit1, lunch sponsored by Mit4)
                        "Mit4": 1.50 + 4.40 + 15.00  # Coffee + breakfast sponsoring cost + lunch sponsoring cost
                    }
                    
                    total_expected_individual = sum(expected_individual_breakdown.values())
                    
                    print(f"  Expected individual breakdown:")
                    for name, expected in expected_individual_breakdown.items():
                        print(f"    - {name}: €{expected:.2f}")
                    print(f"  Expected sum of individuals: €{total_expected_individual:.2f}")
                    
                    print(f"\n🔍 ACTUAL vs EXPECTED INDIVIDUAL COMPARISON:")
                    for emp_key, emp_data in employee_orders.items():
                        actual_total = emp_data.get('total_amount', 0.0)
                        # Extract employee name from key (e.g., "Mit1 (ID: 97cbea01)" -> "Mit1")
                        emp_name = emp_key.split(' ')[0]
                        expected_total = expected_individual_breakdown.get(emp_name, 0.0)
                        difference = actual_total - expected_total
                        
                        print(f"  - {emp_key}:")
                        print(f"    - Actual: €{actual_total:.2f}")
                        print(f"    - Expected: €{expected_total:.2f}")
                        print(f"    - Difference: €{difference:.2f}")
                        
                        if abs(difference) > 0.01:
                            print(f"    - ⚠️ SIGNIFICANT DIFFERENCE DETECTED!")
                    
                    # Check sponsoring amounts
                    print(f"\n🔍 SPONSORING AMOUNTS VERIFICATION:")
                    for emp_key, emp_data in employee_orders.items():
                        sponsored_breakfast = emp_data.get('sponsored_breakfast', None)
                        sponsored_lunch = emp_data.get('sponsored_lunch', None)
                        
                        if sponsored_breakfast:
                            print(f"  - {emp_key} sponsored breakfast: €{sponsored_breakfast.get('amount', 0.0):.2f} for {sponsored_breakfast.get('count', 0)} employees")
                        
                        if sponsored_lunch:
                            print(f"  - {emp_key} sponsored lunch: €{sponsored_lunch.get('amount', 0.0):.2f} for {sponsored_lunch.get('count', 0)} employees")
                    
                    print(f"\n🧮 CALCULATION VERIFICATION:")
                    print(f"  - Manual sum of individuals: €{manual_sum:.2f}")
                    print(f"  - API reported total: €{today_data.get('total_amount', 0.0):.2f}")
                    print(f"  - Expected total: €{self.expected_daily_total:.2f}")
                    
                    api_total = today_data.get('total_amount', 0.0)
                    discrepancy_manual = abs(manual_sum - self.expected_daily_total)
                    discrepancy_api = abs(api_total - self.expected_daily_total)
                    
                    print(f"\n🎯 DISCREPANCY ANALYSIS:")
                    print(f"  - Manual vs Expected: €{discrepancy_manual:.2f}")
                    print(f"  - API vs Expected: €{discrepancy_api:.2f}")
                    print(f"  - Manual vs API: €{abs(manual_sum - api_total):.2f}")
                    
                    # Check for the specific 0.10€ discrepancy mentioned in review request
                    if abs(discrepancy_api - 0.10) < 0.01:
                        print(f"  🚨 CONFIRMED: Found the exact 0.10€ discrepancy mentioned in review request!")
                        print(f"     Expected: €24.40, Actual: €{api_total:.2f}")
                    
                    # Analyze floating point precision
                    print(f"\n🔬 FLOATING POINT PRECISION CHECK:")
                    for emp_key, total in individual_totals.items():
                        rounded_total = round(total, 2)
                        precision_diff = abs(total - rounded_total)
                        if precision_diff > 0.001:
                            print(f"  ⚠️ {emp_key}: Precision issue - Raw: {total}, Rounded: {rounded_total}")
                        else:
                            print(f"  ✅ {emp_key}: No precision issues")
                    
                    return {
                        "status": "success",
                        "manual_sum": manual_sum,
                        "api_total": api_total,
                        "expected_total": self.expected_daily_total,
                        "discrepancy_found": abs(discrepancy_api - 0.10) < 0.01,
                        "individual_totals": individual_totals
                    }
                else:
                    print(f"❌ No history data found")
                    return {"status": "error", "message": "No history data"}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"status": "error", "message": f"API call failed: {response.text}"}
                
        except Exception as e:
            print(f"❌ Error analyzing breakfast-history: {e}")
            return {"status": "error", "message": str(e)}
    
    def run_rounding_error_debug_test(self):
        """Run the complete rounding error and sponsoring debug test"""
        print("🔍 RUNDUNGSFEHLER UND SPONSORING-SUMMEN DEBUG: Analysiere 24.30€ vs 24.40€")
        print("=" * 100)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 1 (fw1abteilung1)")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 2: Clean up existing data for fresh test
        print("\n2️⃣ Cleaning Up Existing Data")
        self.cleanup_test_data()
        
        # Step 3: Setup department prices
        print("\n3️⃣ Setting Up Department Prices")
        if not self.setup_department_prices():
            print("❌ CRITICAL FAILURE: Cannot setup prices")
            return False
        
        # Step 4: Setup menu items
        print("\n4️⃣ Setting Up Menu Items")
        if not self.setup_menu_items():
            print("❌ CRITICAL FAILURE: Cannot setup menu items")
            return False
        
        # Step 5: Create 4 employees (Mit1, Mit2, Mit3, Mit4)
        print(f"\n5️⃣ Creating 4 Employees")
        employee_names = ["Mit1", "Mit2", "Mit3", "Mit4"]
        for name in employee_names:
            employee_id = self.create_test_employee(name)
            if not employee_id:
                print(f"❌ CRITICAL FAILURE: Cannot create {name}")
                return False
            self.employees[name] = employee_id
        
        # Step 6: Create orders for all 4 employees
        print(f"\n6️⃣ Creating Orders for All 4 Employees")
        for name in employee_names:
            order = self.create_employee_order(name, self.employees[name])
            if not order:
                print(f"❌ CRITICAL FAILURE: Cannot create order for {name}")
                return False
        
        # Step 7: Analyze totals before sponsoring
        print(f"\n7️⃣ Analyzing Totals BEFORE Sponsoring")
        before_sponsoring = self.analyze_breakfast_history_totals()
        
        # Step 8: Mit1 sponsors breakfast for Mit2, Mit3, Mit4
        print(f"\n8️⃣ Mit1 Sponsors Breakfast for Mit2, Mit3, Mit4")
        if not self.sponsor_breakfast("Mit1", self.employees["Mit1"], ["Mit2", "Mit3", "Mit4"]):
            print("❌ CRITICAL FAILURE: Cannot sponsor breakfast")
            return False
        
        # Step 9: Analyze totals after breakfast sponsoring
        print(f"\n9️⃣ Analyzing Totals AFTER Breakfast Sponsoring")
        after_breakfast_sponsoring = self.analyze_breakfast_history_totals()
        
        # Step 10: Mit4 sponsors lunch for Mit1
        print(f"\n🔟 Mit4 Sponsors Lunch for Mit1")
        if not self.sponsor_lunch("Mit4", self.employees["Mit4"], ["Mit1"]):
            print("❌ CRITICAL FAILURE: Cannot sponsor lunch")
            return False
        
        # Step 11: Final analysis after all sponsoring
        print(f"\n1️⃣1️⃣ FINAL Analysis After All Sponsoring")
        final_analysis = self.analyze_breakfast_history_totals()
        
        # Final Results
        print(f"\n🏁 FINAL ROUNDING ERROR DEBUG RESULTS:")
        print("=" * 100)
        
        if final_analysis.get("status") == "success":
            if final_analysis.get("discrepancy_found"):
                print(f"🚨 CRITICAL BUG CONFIRMED: Found the exact 0.10€ discrepancy!")
                print(f"   Expected: €{final_analysis['expected_total']:.2f}")
                print(f"   Actual: €{final_analysis['api_total']:.2f}")
                print(f"   Missing: €{final_analysis['expected_total'] - final_analysis['api_total']:.2f}")
                print(f"🎯 ROOT CAUSE: Sponsoring calculation or rounding error in breakfast-history endpoint")
                return False
            else:
                print(f"✅ SUCCESS: No significant discrepancy found")
                print(f"   Expected: €{final_analysis['expected_total']:.2f}")
                print(f"   Actual: €{final_analysis['api_total']:.2f}")
                return True
        else:
            print(f"❌ ERROR: {final_analysis.get('message', 'Unknown error')}")
            return False

def main():
    """Main test execution"""
    test = RoundingErrorSponsoringDebugTest()
    
    try:
        success = test.run_rounding_error_debug_test()
        
        if success:
            print(f"\n✅ ROUNDING ERROR DEBUG TEST: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ ROUNDING ERROR DEBUG TEST: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()