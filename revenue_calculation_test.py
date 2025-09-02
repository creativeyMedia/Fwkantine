#!/usr/bin/env python3
"""
🚨 CRITICAL REVENUE CALCULATION BUG TEST: Test the fixed revenue calculation after sponsoring

URGENT TESTING NEEDED:

1. **Test Revenue Before Sponsoring:**
   - Create breakfast orders with rolls, eggs, and lunch for multiple employees
   - Calculate expected breakfast revenue (rolls + eggs only, coffee excluded)  
   - Calculate expected lunch revenue (lunch portions only)
   - Verify /orders/separated-revenue/ shows correct totals

2. **Test Revenue AFTER Sponsoring:**
   - Sponsor breakfast for some employees
   - Sponsor lunch for some employees  
   - CRITICAL: Verify revenue totals REMAIN THE SAME
   - Revenue should not decrease when items are sponsored

3. **Verify Logic:**
   - Sponsored orders should count toward revenue (they're real food)
   - Only pure sponsor orders (no breakfast_items) should be excluded
   - Total revenue = sum of all actual food items regardless of who pays

4. **Test Scenario from User:**
   - User reported: "Gesamt Umsatz Frühstück nur bei 3,5€" after sponsoring
   - Should show full breakfast revenue of all employees, not just sponsor
   - Test Department 2 (2. Wachabteilung) as mentioned by user

CRITICAL: The user reported that after sponsoring, only the sponsor's individual revenue shows instead of total revenue. This indicates sponsored orders are incorrectly excluded from revenue calculation.

Use Department 2 (fw4abteilung2) with admin2 credentials.
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

# Test Configuration
DEPARTMENT_ID = "fw4abteilung2"  # Department 2
ADMIN_PASSWORD = "admin2"
DEPARTMENT_NAME = "2. Wachabteilung"

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

class RevenueCalculationTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_employees = []
        self.test_orders = []
        
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
    
    def create_comprehensive_breakfast_order(self, employee_id: str, employee_name: str, include_lunch: bool = True) -> Dict:
        """Create a comprehensive breakfast order with rolls, eggs, coffee, and optionally lunch"""
        try:
            # Create a comprehensive breakfast order
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # 2 full rolls
                    "white_halves": 2,
                    "seeded_halves": 2,
                    "toppings": ["butter", "kaese", "schinken", "salami"],
                    "has_lunch": include_lunch,
                    "boiled_eggs": 2,  # 2 breakfast eggs
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                total_price = order["total_price"]
                
                self.test_orders.append({
                    "order_id": order_id,
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "total_price": total_price,
                    "has_lunch": include_lunch
                })
                
                lunch_text = "with lunch" if include_lunch else "without lunch"
                print(f"✅ Created comprehensive breakfast order for {employee_name} ({lunch_text}): €{total_price:.2f}")
                return {
                    "order_id": order_id,
                    "total_price": total_price,
                    "has_lunch": include_lunch
                }
            else:
                print(f"❌ Failed to create breakfast order for {employee_name}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating breakfast order for {employee_name}: {e}")
            return None
    
    def get_separated_revenue(self, days_back: int = 1) -> Dict:
        """Get separated breakfast and lunch revenue"""
        try:
            response = self.session.get(f"{API_BASE}/orders/separated-revenue/{DEPARTMENT_ID}?days_back={days_back}")
            
            if response.status_code == 200:
                revenue_data = response.json()
                print(f"📊 Separated Revenue (last {days_back} days): Breakfast €{revenue_data.get('breakfast_revenue', 0):.2f}, Lunch €{revenue_data.get('lunch_revenue', 0):.2f}")
                return revenue_data
            else:
                print(f"❌ Failed to get separated revenue: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error getting separated revenue: {e}")
            return {}
    
    def get_daily_revenue(self, date: str) -> Dict:
        """Get daily revenue for a specific date"""
        try:
            response = self.session.get(f"{API_BASE}/orders/daily-revenue/{DEPARTMENT_ID}/{date}")
            
            if response.status_code == 200:
                revenue_data = response.json()
                print(f"📊 Daily Revenue ({date}): Breakfast €{revenue_data.get('breakfast_revenue', 0):.2f}, Lunch €{revenue_data.get('lunch_revenue', 0):.2f}")
                return revenue_data
            else:
                print(f"❌ Failed to get daily revenue for {date}: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error getting daily revenue for {date}: {e}")
            return {}
    
    def sponsor_breakfast_meals(self, sponsor_employee_id: str, sponsor_employee_name: str) -> Dict:
        """Sponsor breakfast meals for all employees with breakfast orders"""
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
    
    def sponsor_lunch_meals(self, sponsor_employee_id: str, sponsor_employee_name: str) -> Dict:
        """Sponsor lunch meals for all employees with lunch orders"""
        try:
            today = self.get_berlin_date()
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": sponsor_employee_id,
                "sponsor_employee_name": sponsor_employee_name
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Lunch sponsoring successful: {result}")
                return result
            else:
                print(f"❌ Failed to sponsor lunch meals: {response.status_code} - {response.text}")
                return {}
                
        except Exception as e:
            print(f"❌ Error sponsoring lunch meals: {e}")
            return {}
    
    def calculate_expected_revenue(self, orders: List[Dict]) -> Dict:
        """Calculate expected breakfast and lunch revenue based on orders"""
        # Get current menu prices for Department 2
        try:
            # Get roll prices
            breakfast_menu_response = self.session.get(f"{API_BASE}/menu/breakfast/{DEPARTMENT_ID}")
            breakfast_menu = breakfast_menu_response.json() if breakfast_menu_response.status_code == 200 else []
            
            # Get department-specific prices
            dept_settings_response = self.session.get(f"{API_BASE}/department-settings/{DEPARTMENT_ID}")
            dept_settings = dept_settings_response.json() if dept_settings_response.status_code == 200 else {}
            
            # Get daily lunch price
            today = self.get_berlin_date()
            lunch_price_response = self.session.get(f"{API_BASE}/daily-lunch-price/{DEPARTMENT_ID}/{today}")
            lunch_price_data = lunch_price_response.json() if lunch_price_response.status_code == 200 else {}
            
            # Extract prices
            white_roll_price = 0.50  # Default
            seeded_roll_price = 0.60  # Default
            for item in breakfast_menu:
                if item.get("roll_type") == "weiss":
                    white_roll_price = item.get("price", 0.50)
                elif item.get("roll_type") == "koerner":
                    seeded_roll_price = item.get("price", 0.60)
            
            eggs_price = dept_settings.get("boiled_eggs_price", 0.50)
            coffee_price = dept_settings.get("coffee_price", 1.50)
            lunch_price = lunch_price_data.get("lunch_price", 0.0)
            
            print(f"📋 Current Prices: White Roll €{white_roll_price}, Seeded Roll €{seeded_roll_price}, Eggs €{eggs_price}, Coffee €{coffee_price}, Lunch €{lunch_price}")
            
            expected_breakfast_revenue = 0.0
            expected_lunch_revenue = 0.0
            
            for order in orders:
                if order.get("has_lunch"):
                    # Breakfast revenue: 2 white halves + 2 seeded halves + 2 eggs (coffee excluded from revenue)
                    breakfast_item_revenue = (2 * white_roll_price) + (2 * seeded_roll_price) + (2 * eggs_price)
                    expected_breakfast_revenue += breakfast_item_revenue
                    
                    # Lunch revenue
                    expected_lunch_revenue += lunch_price
                else:
                    # Only breakfast items (no lunch)
                    breakfast_item_revenue = (2 * white_roll_price) + (2 * seeded_roll_price) + (2 * eggs_price)
                    expected_breakfast_revenue += breakfast_item_revenue
            
            return {
                "expected_breakfast_revenue": round(expected_breakfast_revenue, 2),
                "expected_lunch_revenue": round(expected_lunch_revenue, 2),
                "total_expected_revenue": round(expected_breakfast_revenue + expected_lunch_revenue, 2)
            }
            
        except Exception as e:
            print(f"❌ Error calculating expected revenue: {e}")
            return {"expected_breakfast_revenue": 0.0, "expected_lunch_revenue": 0.0, "total_expected_revenue": 0.0}
    
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
    
    def run_comprehensive_revenue_test(self):
        """Run the comprehensive revenue calculation test"""
        print("🚨 CRITICAL REVENUE CALCULATION BUG TEST: Test the fixed revenue calculation after sponsoring")
        print("=" * 100)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication Test")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 2: Clean up any existing test data
        print("\n2️⃣ Cleaning Up Existing Test Data")
        self.cleanup_test_data()
        
        # Step 3: Create Test Employees
        print(f"\n3️⃣ Creating Test Employees for Department {DEPARTMENT_ID}")
        employee1 = self.create_test_employee(f"RevenueTest1_{datetime.now().strftime('%H%M%S')}")
        employee2 = self.create_test_employee(f"RevenueTest2_{datetime.now().strftime('%H%M%S')}")
        employee3 = self.create_test_employee(f"RevenueTest3_{datetime.now().strftime('%H%M%S')}")
        employee4 = self.create_test_employee(f"RevenueSponsor_{datetime.now().strftime('%H%M%S')}")
        
        if not all([employee1, employee2, employee3, employee4]):
            print("❌ CRITICAL FAILURE: Cannot create test employees")
            return False
        
        # Step 4: Create Comprehensive Breakfast Orders
        print(f"\n4️⃣ Creating Comprehensive Breakfast Orders (Rolls + Eggs + Coffee + Lunch)")
        
        # Create orders with lunch for first 3 employees
        order1 = self.create_comprehensive_breakfast_order(employee1, "RevenueTest1", include_lunch=True)
        order2 = self.create_comprehensive_breakfast_order(employee2, "RevenueTest2", include_lunch=True)
        order3 = self.create_comprehensive_breakfast_order(employee3, "RevenueTest3", include_lunch=True)
        
        # Create order for sponsor (will sponsor others)
        sponsor_order = self.create_comprehensive_breakfast_order(employee4, "RevenueSponsor", include_lunch=True)
        
        if not all([order1, order2, order3, sponsor_order]):
            print("❌ CRITICAL FAILURE: Cannot create test orders")
            return False
        
        # Step 5: Calculate Expected Revenue BEFORE Sponsoring
        print(f"\n5️⃣ Calculate Expected Revenue BEFORE Sponsoring")
        expected_revenue = self.calculate_expected_revenue(self.test_orders)
        
        print(f"📊 Expected Breakfast Revenue: €{expected_revenue['expected_breakfast_revenue']:.2f}")
        print(f"📊 Expected Lunch Revenue: €{expected_revenue['expected_lunch_revenue']:.2f}")
        print(f"📊 Total Expected Revenue: €{expected_revenue['total_expected_revenue']:.2f}")
        
        # Step 6: Get Actual Revenue BEFORE Sponsoring
        print(f"\n6️⃣ Get Actual Revenue BEFORE Sponsoring")
        today = self.get_berlin_date()
        
        revenue_before_separated = self.get_separated_revenue(days_back=1)
        revenue_before_daily = self.get_daily_revenue(today)
        
        breakfast_revenue_before = revenue_before_separated.get('breakfast_revenue', 0)
        lunch_revenue_before = revenue_before_separated.get('lunch_revenue', 0)
        total_revenue_before = breakfast_revenue_before + lunch_revenue_before
        
        print(f"📊 ACTUAL Revenue BEFORE Sponsoring:")
        print(f"   - Breakfast: €{breakfast_revenue_before:.2f}")
        print(f"   - Lunch: €{lunch_revenue_before:.2f}")
        print(f"   - Total: €{total_revenue_before:.2f}")
        
        # Step 7: Verify Revenue Matches Expected BEFORE Sponsoring
        print(f"\n7️⃣ Verify Revenue Matches Expected BEFORE Sponsoring")
        
        breakfast_match_before = abs(breakfast_revenue_before - expected_revenue['expected_breakfast_revenue']) < 0.01
        lunch_match_before = abs(lunch_revenue_before - expected_revenue['expected_lunch_revenue']) < 0.01
        
        if breakfast_match_before and lunch_match_before:
            print(f"✅ Revenue calculation BEFORE sponsoring is CORRECT")
        else:
            print(f"❌ Revenue calculation BEFORE sponsoring is INCORRECT")
            print(f"   Expected: Breakfast €{expected_revenue['expected_breakfast_revenue']:.2f}, Lunch €{expected_revenue['expected_lunch_revenue']:.2f}")
            print(f"   Actual: Breakfast €{breakfast_revenue_before:.2f}, Lunch €{lunch_revenue_before:.2f}")
        
        # Step 8: CRITICAL TEST - Sponsor Breakfast Meals
        print(f"\n8️⃣ 🚨 CRITICAL TEST: Sponsor Breakfast Meals")
        breakfast_sponsor_result = self.sponsor_breakfast_meals(employee4, "RevenueSponsor")  # RevenueSponsor sponsors breakfast
        
        if not breakfast_sponsor_result:
            print("❌ CRITICAL FAILURE: Cannot sponsor breakfast meals")
            return False
        
        # Step 9: CRITICAL TEST - Sponsor Lunch Meals  
        print(f"\n9️⃣ 🚨 CRITICAL TEST: Sponsor Lunch Meals")
        lunch_sponsor_result = self.sponsor_lunch_meals(employee4, "RevenueSponsor")  # RevenueSponsor sponsors lunch
        
        if not lunch_sponsor_result:
            print("❌ CRITICAL FAILURE: Cannot sponsor lunch meals")
            return False
        
        # Step 10: Get Actual Revenue AFTER Sponsoring
        print(f"\n🔟 Get Actual Revenue AFTER Sponsoring")
        
        revenue_after_separated = self.get_separated_revenue(days_back=1)
        revenue_after_daily = self.get_daily_revenue(today)
        
        breakfast_revenue_after = revenue_after_separated.get('breakfast_revenue', 0)
        lunch_revenue_after = revenue_after_separated.get('lunch_revenue', 0)
        total_revenue_after = breakfast_revenue_after + lunch_revenue_after
        
        print(f"📊 ACTUAL Revenue AFTER Sponsoring:")
        print(f"   - Breakfast: €{breakfast_revenue_after:.2f}")
        print(f"   - Lunch: €{lunch_revenue_after:.2f}")
        print(f"   - Total: €{total_revenue_after:.2f}")
        
        # Step 11: CRITICAL VERIFICATION - Revenue Should REMAIN THE SAME
        print(f"\n1️⃣1️⃣ 🎯 CRITICAL VERIFICATION: Revenue Should REMAIN THE SAME After Sponsoring")
        
        breakfast_unchanged = abs(breakfast_revenue_after - breakfast_revenue_before) < 0.01
        lunch_unchanged = abs(lunch_revenue_after - lunch_revenue_before) < 0.01
        total_unchanged = abs(total_revenue_after - total_revenue_before) < 0.01
        
        print(f"📊 Revenue Comparison:")
        print(f"   - Breakfast: Before €{breakfast_revenue_before:.2f} → After €{breakfast_revenue_after:.2f} (Change: €{breakfast_revenue_after - breakfast_revenue_before:.2f})")
        print(f"   - Lunch: Before €{lunch_revenue_before:.2f} → After €{lunch_revenue_after:.2f} (Change: €{lunch_revenue_after - lunch_revenue_before:.2f})")
        print(f"   - Total: Before €{total_revenue_before:.2f} → After €{total_revenue_after:.2f} (Change: €{total_revenue_after - total_revenue_before:.2f})")
        
        # Step 12: Final Result Analysis
        print(f"\n1️⃣2️⃣ 🏁 FINAL RESULT ANALYSIS:")
        
        revenue_calculation_correct = breakfast_match_before and lunch_match_before
        revenue_unchanged_after_sponsoring = breakfast_unchanged and lunch_unchanged and total_unchanged
        
        if revenue_calculation_correct and revenue_unchanged_after_sponsoring:
            print("🎉 REVENUE CALCULATION BUG FIX VERIFICATION SUCCESSFUL!")
            print("✅ Revenue calculation is correct BEFORE sponsoring")
            print("✅ Revenue totals REMAIN THE SAME after sponsoring")
            print("✅ Sponsored orders correctly count toward revenue")
            print("✅ The user's issue 'Gesamt Umsatz Frühstück nur bei 3,5€' is RESOLVED")
            return True
        else:
            print("🚨 REVENUE CALCULATION BUG STILL EXISTS!")
            if not revenue_calculation_correct:
                print("❌ Revenue calculation is incorrect BEFORE sponsoring")
            if not revenue_unchanged_after_sponsoring:
                print("❌ Revenue totals CHANGE after sponsoring (BUG CONFIRMED)")
                print("❌ This confirms the user's report: revenue decreases after sponsoring")
                print("❌ Sponsored orders are incorrectly excluded from revenue calculation")
            return False

def main():
    """Main test execution"""
    test = RevenueCalculationTest()
    
    try:
        success = test.run_comprehensive_revenue_test()
        
        if success:
            print(f"\n✅ REVENUE CALCULATION BUG FIX: VERIFIED WORKING")
            exit(0)
        else:
            print(f"\n❌ REVENUE CALCULATION BUG: STILL EXISTS - NEEDS FIXING")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()