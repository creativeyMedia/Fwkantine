#!/usr/bin/env python3
"""
🔍 FINAL DEBUG: Test mit Debug-Logging für Regular Order total_price

FINALER DEBUG TEST:

1. **Create simple scenario:**
   - Create Mit1 mit standard order (expected €7.60)
   - NO sponsoring actions

2. **DEBUG REGULAR ORDER CALCULATION:**
   - Watch debug logs for regular order calculation
   - Should show: total_price=7.60, order_amount=7.60
   - Verify that regular orders path is taken

3. **BREAKFAST-HISTORY VERIFICATION:**
   - Call breakfast-history endpoint
   - Should show Mit1 with total_amount=7.60 (not 6.10)

4. **IDENTIFY EXACT BUG:**
   - If debug shows total_price=7.60 but total_amount=6.10
   - Then there's a calculation error in the logic
   - If total_price is already 6.10, then the order creation is wrong

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Final debug to identify exactly where the €1.50 coffee cost disappears!
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

class FinalDebugRegularOrderTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.mit1_employee_id = None
        self.created_order = None
        self.expected_total = 7.60  # 0.50 + 0.60 + 1.50 + 5.00
        
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
                                      json={"price": 1.50})
            
            if response.status_code == 200:
                print(f"✅ Coffee price set to €1.50")
            else:
                print(f"❌ Failed to set coffee price: {response.text}")
                return False
            
            # Set lunch price to 5.00€ for today
            today = self.get_berlin_date()
            response = self.session.put(f"{API_BASE}/daily-lunch-settings/{DEPARTMENT_ID}/{today}?lunch_price=5.00")
            
            if response.status_code == 200:
                print(f"✅ Lunch price set to €5.00 for {today}")
            else:
                print(f"❌ Failed to set lunch price: {response.text}")
                return False
            
            return True
                
        except Exception as e:
            print(f"❌ Error setting up prices: {e}")
            return False
    
    def create_mit1_standard_order(self) -> dict:
        """Create Mit1 standard order (expected €7.60) - NO SPONSORING"""
        
        print(f"\n🔧 CREATING MIT1 STANDARD ORDER:")
        print("=" * 60)
        print(f"Expected breakdown:")
        print(f"  - White roll half: €0.50")
        print(f"  - Seeded roll half: €0.60") 
        print(f"  - Coffee: €1.50")
        print(f"  - Lunch: €5.00")
        print(f"  - TOTAL EXPECTED: €7.60")
        
        order_data = {
            "employee_id": self.mit1_employee_id,
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
            print(f"\n📤 SENDING ORDER REQUEST:")
            print(f"Order data: {json.dumps(order_data, indent=2)}")
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                self.created_order = order
                
                print(f"\n✅ ORDER CREATED SUCCESSFULLY:")
                print(f"  - Order ID: {order['id']}")
                print(f"  - Total Price: €{order['total_price']:.2f}")
                print(f"  - Expected: €{self.expected_total:.2f}")
                print(f"  - Difference: €{abs(order['total_price'] - self.expected_total):.2f}")
                
                # Check if order creation total is correct
                if abs(order['total_price'] - self.expected_total) < 0.01:
                    print(f"  ✅ Order creation total is CORRECT")
                else:
                    print(f"  ❌ Order creation total is WRONG!")
                    print(f"     🔍 BUG LOCATION: Order creation logic")
                
                return order
            else:
                print(f"❌ Failed to create Mit1 order: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error creating Mit1 order: {e}")
            return None
    
    def verify_breakfast_history_calculation(self) -> dict:
        """Verify breakfast-history endpoint shows correct total_amount"""
        try:
            print(f"\n🔍 BREAKFAST-HISTORY ENDPOINT VERIFICATION:")
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
                    print(f"  - Employees Found: {len(employee_orders)}")
                    
                    # Find Mit1 in the response
                    mit1_data = None
                    mit1_key = None
                    
                    for emp_key, emp_data in employee_orders.items():
                        if "Mit1" in emp_key:
                            mit1_data = emp_data
                            mit1_key = emp_key
                            break
                    
                    if mit1_data:
                        print(f"\n🔍 MIT1 DATA FROM BREAKFAST-HISTORY:")
                        print(f"  - Employee Key: {mit1_key}")
                        print(f"  - Total Amount: €{mit1_data.get('total_amount', 0.0):.2f}")
                        print(f"  - Expected: €{self.expected_total:.2f}")
                        print(f"  - Is Sponsored: {mit1_data.get('is_sponsored', False)}")
                        print(f"  - Sponsored Meal Type: {mit1_data.get('sponsored_meal_type', None)}")
                        
                        # Check calculation path
                        breakfast_history_total = mit1_data.get('total_amount', 0.0)
                        order_creation_total = self.created_order['total_price'] if self.created_order else 0.0
                        
                        print(f"\n🔍 CALCULATION PATH ANALYSIS:")
                        print(f"  - Order Creation Total: €{order_creation_total:.2f}")
                        print(f"  - Breakfast-History Total: €{breakfast_history_total:.2f}")
                        print(f"  - Expected Total: €{self.expected_total:.2f}")
                        
                        # Identify where the bug occurs
                        creation_correct = abs(order_creation_total - self.expected_total) < 0.01
                        history_correct = abs(breakfast_history_total - self.expected_total) < 0.01
                        
                        print(f"\n🎯 BUG LOCATION ANALYSIS:")
                        if creation_correct and history_correct:
                            print(f"  ✅ Both order creation AND breakfast-history are correct")
                            return {"status": "correct", "bug_location": "none"}
                        elif creation_correct and not history_correct:
                            print(f"  ❌ Order creation is correct, but breakfast-history is WRONG")
                            print(f"     🔍 BUG LOCATION: breakfast-history endpoint calculation")
                            print(f"     🔍 Missing amount: €{self.expected_total - breakfast_history_total:.2f}")
                            return {"status": "bug_in_history", "bug_location": "breakfast-history", "missing_amount": self.expected_total - breakfast_history_total}
                        elif not creation_correct and history_correct:
                            print(f"  ❌ Order creation is WRONG, but breakfast-history is correct")
                            print(f"     🔍 BUG LOCATION: order creation logic")
                            return {"status": "bug_in_creation", "bug_location": "order_creation"}
                        else:
                            print(f"  ❌ BOTH order creation AND breakfast-history are WRONG")
                            print(f"     🔍 BUG LOCATION: Both systems have issues")
                            return {"status": "bug_in_both", "bug_location": "both"}
                    else:
                        print(f"❌ Mit1 not found in breakfast-history response")
                        print(f"Available employees: {list(employee_orders.keys())}")
                        return {"status": "error", "message": "Mit1 not found"}
                else:
                    print(f"❌ No history data found")
                    return {"status": "error", "message": "No history data"}
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"status": "error", "message": f"API call failed: {response.text}"}
                
        except Exception as e:
            print(f"❌ Error verifying breakfast-history: {e}")
            return {"status": "error", "message": str(e)}
    
    def debug_coffee_cost_calculation(self) -> bool:
        """Debug where coffee cost gets lost in calculation"""
        try:
            print(f"\n🔍 COFFEE COST DEBUG ANALYSIS:")
            print("=" * 80)
            
            # Get department coffee price
            response = self.session.get(f"{API_BASE}/department-settings/{DEPARTMENT_ID}/coffee-price")
            if response.status_code == 200:
                coffee_data = response.json()
                coffee_price = coffee_data.get("coffee_price", 0.0)
                print(f"📊 Department Coffee Price: €{coffee_price:.2f}")
            else:
                print(f"❌ Failed to get coffee price")
                return False
            
            # Get lunch price
            today = self.get_berlin_date()
            response = self.session.get(f"{API_BASE}/daily-lunch-price/{DEPARTMENT_ID}/{today}")
            if response.status_code == 200:
                lunch_data = response.json()
                lunch_price = lunch_data.get("lunch_price", 0.0)
                print(f"📊 Daily Lunch Price: €{lunch_price:.2f}")
            else:
                print(f"❌ Failed to get lunch price")
                return False
            
            # Get roll prices
            response = self.session.get(f"{API_BASE}/menu/breakfast/{DEPARTMENT_ID}")
            if response.status_code == 200:
                breakfast_menu = response.json()
                white_price = 0.0
                seeded_price = 0.0
                
                for item in breakfast_menu:
                    if item.get("roll_type") == "weiss":
                        white_price = item.get("price", 0.0)
                    elif item.get("roll_type") == "koerner":
                        seeded_price = item.get("price", 0.0)
                
                print(f"📊 Roll Prices: White €{white_price:.2f}, Seeded €{seeded_price:.2f}")
            else:
                print(f"❌ Failed to get breakfast menu")
                return False
            
            # Calculate expected total manually
            expected_breakdown = {
                "white_roll": white_price * 1,  # 1 half
                "seeded_roll": seeded_price * 1,  # 1 half
                "coffee": coffee_price,
                "lunch": lunch_price
            }
            
            manual_total = sum(expected_breakdown.values())
            
            print(f"\n🧮 MANUAL CALCULATION BREAKDOWN:")
            for item, cost in expected_breakdown.items():
                print(f"  - {item}: €{cost:.2f}")
            print(f"  - MANUAL TOTAL: €{manual_total:.2f}")
            print(f"  - EXPECTED TOTAL: €{self.expected_total:.2f}")
            print(f"  - DIFFERENCE: €{abs(manual_total - self.expected_total):.2f}")
            
            if abs(manual_total - self.expected_total) < 0.01:
                print(f"  ✅ Manual calculation matches expected")
            else:
                print(f"  ❌ Manual calculation doesn't match expected")
            
            return True
                
        except Exception as e:
            print(f"❌ Error in coffee cost debug: {e}")
            return False
    
    def run_final_debug_test(self):
        """Run the complete final debug test"""
        print("🔍 FINAL DEBUG: Regular Order total_price Test")
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
        
        # Step 4: Create Mit1 employee
        print(f"\n4️⃣ Creating Mit1 Employee")
        self.mit1_employee_id = self.create_test_employee("Mit1")
        if not self.mit1_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Mit1")
            return False
        
        # Step 5: Debug coffee cost calculation
        print(f"\n5️⃣ Debug Coffee Cost Calculation")
        if not self.debug_coffee_cost_calculation():
            print("❌ CRITICAL FAILURE: Cannot debug coffee cost")
            return False
        
        # Step 6: Create Mit1 standard order (NO SPONSORING)
        print(f"\n6️⃣ Creating Mit1 Standard Order (NO SPONSORING)")
        order_created = self.create_mit1_standard_order()
        if not order_created:
            print("❌ CRITICAL FAILURE: Cannot create order")
            return False
        
        # Step 7: Verify breakfast-history calculation
        print(f"\n7️⃣ Verifying Breakfast-History Calculation")
        history_result = self.verify_breakfast_history_calculation()
        
        # Final Results
        print(f"\n🏁 FINAL DEBUG RESULTS:")
        print("=" * 100)
        
        if history_result.get("status") == "correct":
            print(f"✅ SUCCESS: Both order creation and breakfast-history are working correctly!")
            print(f"✅ Mit1 shows €{self.expected_total:.2f} in both systems")
            return True
        elif history_result.get("status") == "bug_in_history":
            print(f"❌ BUG IDENTIFIED: breakfast-history endpoint calculation is wrong")
            print(f"❌ Order creation total: €{self.created_order['total_price']:.2f} (CORRECT)")
            print(f"❌ Breakfast-history total: Missing €{history_result.get('missing_amount', 0.0):.2f}")
            print(f"🎯 ROOT CAUSE: Coffee cost (€1.50) is missing from breakfast-history calculation")
            print(f"🎯 EXACT BUG LOCATION: breakfast-history endpoint individual employee total calculation")
            return False
        elif history_result.get("status") == "bug_in_creation":
            print(f"❌ BUG IDENTIFIED: Order creation logic is wrong")
            print(f"🎯 ROOT CAUSE: Coffee cost not included in order total_price calculation")
            print(f"🎯 EXACT BUG LOCATION: Order creation endpoint")
            return False
        elif history_result.get("status") == "bug_in_both":
            print(f"❌ BUG IDENTIFIED: Both systems have calculation errors")
            print(f"🎯 ROOT CAUSE: Coffee cost missing from multiple locations")
            return False
        else:
            print(f"❌ ERROR: {history_result.get('message', 'Unknown error')}")
            return False

def main():
    """Main test execution"""
    test = FinalDebugRegularOrderTest()
    
    try:
        success = test.run_final_debug_test()
        
        if success:
            print(f"\n✅ FINAL DEBUG TEST: COMPLETED SUCCESSFULLY")
            exit(0)
        else:
            print(f"\n❌ FINAL DEBUG TEST: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()