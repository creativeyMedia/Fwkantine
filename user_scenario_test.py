#!/usr/bin/env python3
"""
🚨 USER SCENARIO TEST: Test the exact scenario reported by the user

User reported: "Gesamt Umsatz Frühstück nur bei 3,5€" after sponsoring
This should show full breakfast revenue of all employees, not just sponsor.

Test Department 2 (2. Wachabteilung) as mentioned by user.
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

class UserScenarioTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        
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
                print(f"✅ Created test employee '{name}': {employee_id}")
                return employee_id
            else:
                print(f"❌ Failed to create employee '{name}': {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating employee '{name}': {e}")
            return None
    
    def create_simple_breakfast_order(self, employee_id: str, employee_name: str) -> Dict:
        """Create a simple breakfast order that would result in ~3.5€ total"""
        try:
            # Create a simple breakfast order (similar to what user might have)
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 1 full roll
                    "white_halves": 2,
                    "seeded_halves": 0,
                    "toppings": ["butter", "kaese"],
                    "has_lunch": False,  # No lunch
                    "boiled_eggs": 1,    # 1 breakfast egg
                    "has_coffee": False  # No coffee
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                total_price = order["total_price"]
                
                print(f"✅ Created simple breakfast order for {employee_name}: €{total_price:.2f}")
                return {
                    "order_id": order_id,
                    "total_price": total_price,
                    "employee_id": employee_id,
                    "employee_name": employee_name
                }
            else:
                print(f"❌ Failed to create breakfast order for {employee_name}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating breakfast order for {employee_name}: {e}")
            return None
    
    def get_separated_revenue(self) -> Dict:
        """Get separated breakfast and lunch revenue"""
        try:
            response = self.session.get(f"{API_BASE}/orders/separated-revenue/{DEPARTMENT_ID}?days_back=1")
            
            if response.status_code == 200:
                revenue_data = response.json()
                print(f"📊 Separated Revenue: Breakfast €{revenue_data.get('breakfast_revenue', 0):.2f}, Lunch €{revenue_data.get('lunch_revenue', 0):.2f}")
                return revenue_data
            else:
                print(f"❌ Failed to get separated revenue: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error getting separated revenue: {e}")
            return {}
    
    def sponsor_breakfast_meals(self, sponsor_employee_id: str, sponsor_employee_name: str) -> Dict:
        """Sponsor breakfast meals"""
        try:
            today = self.get_berlin_date()
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": sponsor_employee_id,
                "sponsor_employee_name": sponsor_employee_name
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Breakfast sponsoring successful: {result}")
                return result
            else:
                print(f"❌ Failed to sponsor breakfast meals: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error sponsoring breakfast meals: {e}")
            return {}
    
    def cleanup_test_data(self):
        """Clean up test data using debug cleanup endpoint"""
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/debug-cleanup/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test data cleanup successful: {result}")
                return True
            else:
                print(f"⚠️ Test data cleanup failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Error during test data cleanup: {e}")
            return False
    
    def run_user_scenario_test(self):
        """Run the user scenario test"""
        print("🚨 USER SCENARIO TEST: Test the exact scenario reported by the user")
        print("User reported: 'Gesamt Umsatz Frühstück nur bei 3,5€' after sponsoring")
        print("=" * 80)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication Test")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 2: Clean up any existing test data
        print("\n2️⃣ Cleaning Up Existing Test Data")
        self.cleanup_test_data()
        
        # Step 3: Create Test Employees (simulate user scenario)
        print(f"\n3️⃣ Creating Test Employees for Department {DEPARTMENT_ID}")
        employee1 = self.create_test_employee(f"UserTest1_{datetime.now().strftime('%H%M%S')}")
        employee2 = self.create_test_employee(f"UserTest2_{datetime.now().strftime('%H%M%S')}")
        employee3 = self.create_test_employee(f"UserTest3_{datetime.now().strftime('%H%M%S')}")
        sponsor = self.create_test_employee(f"UserSponsor_{datetime.now().strftime('%H%M%S')}")
        
        if not all([employee1, employee2, employee3, sponsor]):
            print("❌ CRITICAL FAILURE: Cannot create test employees")
            return False
        
        # Step 4: Create Simple Breakfast Orders (simulate user scenario)
        print(f"\n4️⃣ Creating Simple Breakfast Orders (User Scenario)")
        
        order1 = self.create_simple_breakfast_order(employee1, "UserTest1")
        order2 = self.create_simple_breakfast_order(employee2, "UserTest2")
        order3 = self.create_simple_breakfast_order(employee3, "UserTest3")
        sponsor_order = self.create_simple_breakfast_order(sponsor, "UserSponsor")
        
        if not all([order1, order2, order3, sponsor_order]):
            print("❌ CRITICAL FAILURE: Cannot create test orders")
            return False
        
        # Calculate total expected breakfast revenue
        total_breakfast_revenue = sum([order["total_price"] for order in [order1, order2, order3, sponsor_order]])
        print(f"📊 Total Expected Breakfast Revenue: €{total_breakfast_revenue:.2f}")
        
        # Step 5: Get Revenue BEFORE Sponsoring
        print(f"\n5️⃣ Get Revenue BEFORE Sponsoring")
        revenue_before = self.get_separated_revenue()
        breakfast_revenue_before = revenue_before.get('breakfast_revenue', 0)
        
        # Step 6: Verify Revenue is Correct BEFORE Sponsoring
        print(f"\n6️⃣ Verify Revenue is Correct BEFORE Sponsoring")
        if abs(breakfast_revenue_before - total_breakfast_revenue) < 0.01:
            print(f"✅ Revenue BEFORE sponsoring is correct: €{breakfast_revenue_before:.2f}")
        else:
            print(f"❌ Revenue BEFORE sponsoring is incorrect: Expected €{total_breakfast_revenue:.2f}, Got €{breakfast_revenue_before:.2f}")
        
        # Step 7: CRITICAL TEST - Sponsor Breakfast Meals
        print(f"\n7️⃣ 🚨 CRITICAL TEST: Sponsor Breakfast Meals (User Scenario)")
        sponsor_result = self.sponsor_breakfast_meals(sponsor, "UserSponsor")
        
        if not sponsor_result:
            print("❌ CRITICAL FAILURE: Cannot sponsor breakfast meals")
            return False
        
        # Step 8: Get Revenue AFTER Sponsoring (This is where the bug was)
        print(f"\n8️⃣ Get Revenue AFTER Sponsoring (Critical Bug Check)")
        revenue_after = self.get_separated_revenue()
        breakfast_revenue_after = revenue_after.get('breakfast_revenue', 0)
        
        # Step 9: CRITICAL VERIFICATION - Check if bug exists
        print(f"\n9️⃣ 🎯 CRITICAL VERIFICATION: Check User's Bug Report")
        
        print(f"📊 Revenue Comparison:")
        print(f"   - BEFORE Sponsoring: €{breakfast_revenue_before:.2f}")
        print(f"   - AFTER Sponsoring: €{breakfast_revenue_after:.2f}")
        print(f"   - Expected (should remain same): €{total_breakfast_revenue:.2f}")
        
        # Check if the user's bug exists
        revenue_unchanged = abs(breakfast_revenue_after - breakfast_revenue_before) < 0.01
        revenue_matches_expected = abs(breakfast_revenue_after - total_breakfast_revenue) < 0.01
        
        # Check if we get the problematic "3.5€" value
        is_problematic_value = abs(breakfast_revenue_after - 3.5) < 0.01
        
        # Step 10: Final Analysis
        print(f"\n🔟 🏁 FINAL ANALYSIS:")
        
        if revenue_unchanged and revenue_matches_expected and not is_problematic_value:
            print("🎉 USER'S BUG REPORT SCENARIO: RESOLVED!")
            print("✅ Revenue remains the same after sponsoring")
            print("✅ Total revenue shows ALL employees' breakfast, not just sponsor")
            print("✅ No problematic '3.5€' value detected")
            print("✅ The user's issue 'Gesamt Umsatz Frühstück nur bei 3,5€' is FIXED")
            return True
        else:
            print("🚨 USER'S BUG REPORT SCENARIO: STILL EXISTS!")
            if not revenue_unchanged:
                print("❌ Revenue changes after sponsoring (should remain same)")
            if not revenue_matches_expected:
                print("❌ Revenue doesn't match expected total")
            if is_problematic_value:
                print(f"❌ CRITICAL: Found the problematic '3.5€' value! (Got €{breakfast_revenue_after:.2f})")
                print("❌ This confirms the user's bug: only sponsor's revenue shows instead of total")
            return False

def main():
    """Main test execution"""
    test = UserScenarioTest()
    
    try:
        success = test.run_user_scenario_test()
        
        if success:
            print(f"\n✅ USER SCENARIO TEST: BUG RESOLVED")
            exit(0)
        else:
            print(f"\n❌ USER SCENARIO TEST: BUG STILL EXISTS")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()