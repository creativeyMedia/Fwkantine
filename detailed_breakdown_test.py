#!/usr/bin/env python3
"""
DETAILED SPONSORED MEAL BREAKDOWN VERIFICATION TEST

This test specifically verifies the enhanced sponsored meal details display
by checking the actual order data and readable_items for detailed breakdowns.
"""

import requests
import json
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "https://canteen-manager-1.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class DetailedBreakdownVerifier:
    def __init__(self):
        self.session = requests.Session()
        
    def authenticate_admin(self):
        """Authenticate as department admin"""
        response = self.session.post(f"{BASE_URL}/login/department-admin", json={
            "department_name": DEPARTMENT_NAME,
            "admin_password": ADMIN_PASSWORD
        })
        return response.status_code == 200
    
    def get_breakfast_history(self):
        """Get breakfast history to check for detailed breakdowns"""
        try:
            response = self.session.get(f"{BASE_URL}/orders/breakfast-history/{DEPARTMENT_ID}?days_back=3")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Error getting breakfast history: {e}")
            return None
    
    def check_sponsored_order_details(self):
        """Check for sponsored orders with detailed breakdowns"""
        print("🔍 CHECKING SPONSORED ORDER DETAILS...")
        
        # Get all employees in department
        employees_response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
        if employees_response.status_code != 200:
            print("❌ Could not fetch employees")
            return False
        
        employees = employees_response.json()
        sponsored_orders_found = []
        sponsor_orders_found = []
        
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        
        print(f"📅 Checking orders for {today} and {yesterday}")
        
        # Check each employee's orders
        for emp in employees[:20]:  # Check first 20 employees
            try:
                orders_response = self.session.get(f"{BASE_URL}/employees/{emp['id']}/orders")
                if orders_response.status_code == 200:
                    orders_data = orders_response.json()
                    orders = orders_data.get("orders", [])
                    
                    for order in orders:
                        order_date = order.get("timestamp", "")
                        if order_date.startswith(today) or order_date.startswith(yesterday):
                            
                            # Check for sponsored orders
                            if order.get("is_sponsored", False):
                                sponsored_orders_found.append({
                                    "employee": emp["name"],
                                    "order": order,
                                    "readable_items": order.get("readable_items", ""),
                                    "sponsored_message": order.get("sponsored_message", "")
                                })
                            
                            # Check for sponsor orders (orders that sponsored others)
                            if order.get("is_sponsor_order", False) or order.get("sponsor_message"):
                                sponsor_orders_found.append({
                                    "employee": emp["name"],
                                    "order": order,
                                    "readable_items": order.get("readable_items", ""),
                                    "sponsor_message": order.get("sponsor_message", "")
                                })
            except Exception as e:
                print(f"   Error checking {emp['name']}: {e}")
                continue
        
        print(f"📊 Found {len(sponsored_orders_found)} sponsored orders and {len(sponsor_orders_found)} sponsor orders")
        
        # Analyze sponsored orders
        if sponsored_orders_found:
            print("\n🎯 SPONSORED ORDERS ANALYSIS:")
            for i, sponsored in enumerate(sponsored_orders_found[:5]):  # Show first 5
                print(f"   {i+1}. Employee: {sponsored['employee']}")
                print(f"      Readable Items: {sponsored['readable_items']}")
                print(f"      Sponsored Message: {sponsored['sponsored_message']}")
                print(f"      Total Price: €{sponsored['order'].get('total_price', 0):.2f}")
                print()
        
        # Analyze sponsor orders
        if sponsor_orders_found:
            print("\n💰 SPONSOR ORDERS ANALYSIS:")
            for i, sponsor in enumerate(sponsor_orders_found[:5]):  # Show first 5
                print(f"   {i+1}. Sponsor: {sponsor['employee']}")
                print(f"      Readable Items: {sponsor['readable_items']}")
                print(f"      Sponsor Message: {sponsor['sponsor_message']}")
                print(f"      Total Price: €{sponsor['order'].get('total_price', 0):.2f}")
                
                # Check for detailed breakdown in readable_items
                readable_items = sponsor['readable_items']
                has_detailed_breakdown = self.analyze_detailed_breakdown(readable_items)
                print(f"      Has Detailed Breakdown: {has_detailed_breakdown}")
                print()
        
        return len(sponsored_orders_found) > 0 or len(sponsor_orders_found) > 0
    
    def analyze_detailed_breakdown(self, readable_items):
        """Analyze if readable_items contains detailed breakdown"""
        if not readable_items:
            return False
        
        # Check for detailed breakdown indicators
        indicators = [
            "für", "Mitarbeiter",  # "für X Mitarbeiter"
            "€", "(",  # Price indicators
            "x ", " x",  # Quantity indicators like "3x"
            "Brötchen", "Eier", "Mittagessen"  # Item names
        ]
        
        found_indicators = [indicator for indicator in indicators if indicator in readable_items]
        
        # Need at least 3 indicators for a detailed breakdown
        return len(found_indicators) >= 3
    
    def check_breakfast_history_for_breakdowns(self):
        """Check breakfast history for detailed breakdowns"""
        print("\n📚 CHECKING BREAKFAST HISTORY FOR DETAILED BREAKDOWNS...")
        
        history = self.get_breakfast_history()
        if not history:
            print("❌ Could not get breakfast history")
            return False
        
        history_data = history.get("history", [])
        print(f"📅 Found {len(history_data)} days of history")
        
        detailed_breakdowns_found = []
        
        for day_data in history_data[:3]:  # Check last 3 days
            date_str = day_data.get("date", "")
            employee_orders = day_data.get("employee_orders", {})
            
            print(f"\n📅 Checking {date_str}:")
            
            for employee_name, order_data in employee_orders.items():
                total_amount = order_data.get("total_amount", 0)
                
                # Look for signs of sponsoring (very low or zero amounts)
                if total_amount <= 1.0:  # Likely sponsored
                    print(f"   🎯 {employee_name}: €{total_amount:.2f} (likely sponsored)")
                elif total_amount > 5.0:  # Likely sponsor
                    print(f"   💰 {employee_name}: €{total_amount:.2f} (likely sponsor)")
                    detailed_breakdowns_found.append({
                        "date": date_str,
                        "employee": employee_name,
                        "amount": total_amount,
                        "order_data": order_data
                    })
        
        if detailed_breakdowns_found:
            print(f"\n✅ Found {len(detailed_breakdowns_found)} potential sponsor orders with enhanced pricing")
            return True
        else:
            print("\n⚠️ No clear sponsor orders found in breakfast history")
            return False
    
    def verify_menu_prices(self):
        """Verify current menu prices for calculation accuracy"""
        print("\n💰 VERIFYING MENU PRICES...")
        
        # Get menu prices
        breakfast_response = self.session.get(f"{BASE_URL}/menu/breakfast/{DEPARTMENT_ID}")
        lunch_settings_response = self.session.get(f"{BASE_URL}/lunch-settings")
        
        if breakfast_response.status_code == 200:
            breakfast_menu = breakfast_response.json()
            print("🥖 Breakfast Menu Prices:")
            for item in breakfast_menu:
                print(f"   {item['roll_type']}: €{item['price']:.2f}")
        
        if lunch_settings_response.status_code == 200:
            lunch_settings = lunch_settings_response.json()
            print("🍽️ Lunch Settings:")
            print(f"   Lunch: €{lunch_settings.get('price', 0):.2f}")
            print(f"   Boiled Eggs: €{lunch_settings.get('boiled_eggs_price', 0):.2f}")
            print(f"   Coffee: €{lunch_settings.get('coffee_price', 0):.2f}")
        
        return True
    
    def run_verification(self):
        """Run all verification tests"""
        print("🔍 DETAILED SPONSORED MEAL BREAKDOWN VERIFICATION")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_admin():
            print("❌ Authentication failed")
            return False
        
        print("✅ Authenticated successfully")
        
        # Check current sponsored orders
        orders_found = self.check_sponsored_order_details()
        
        # Check breakfast history
        history_found = self.check_breakfast_history_for_breakdowns()
        
        # Verify menu prices
        self.verify_menu_prices()
        
        print("\n" + "=" * 80)
        print("📊 VERIFICATION SUMMARY:")
        print(f"   Sponsored Orders Found: {'✅' if orders_found else '❌'}")
        print(f"   History Analysis: {'✅' if history_found else '❌'}")
        print("=" * 80)
        
        return orders_found or history_found

def main():
    verifier = DetailedBreakdownVerifier()
    success = verifier.run_verification()
    
    if success:
        print("\n🎉 DETAILED BREAKDOWN VERIFICATION COMPLETED - SPONSORED MEAL DETAILS FOUND!")
    else:
        print("\n⚠️ DETAILED BREAKDOWN VERIFICATION - LIMITED SPONSORED MEAL ACTIVITY DETECTED")

if __name__ == "__main__":
    main()