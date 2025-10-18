#!/usr/bin/env python3
"""
Detailed Sponsoring Analysis
===========================

Analyze the specific €5.05 case to understand the calculation.
"""

import requests
import json
import os

BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://brigade-meals.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def analyze_specific_employee():
    """Analyze the specific problematic employee 1WaTest1"""
    
    # Get breakfast history
    response = requests.get(f"{API_BASE}/orders/breakfast-history/fw4abteilung1")
    if response.status_code == 200:
        history_data = response.json()
        
        if history_data.get("history"):
            for day_data in history_data["history"]:
                employee_orders = day_data.get("employee_orders", {})
                for employee_key, employee_data in employee_orders.items():
                    if "1WaTest1" in employee_key:
                        print(f"🔍 DETAILED ANALYSIS OF {employee_key}:")
                        print(f"  - total_amount: €{employee_data.get('total_amount', 0):.2f}")
                        print(f"  - is_sponsored: {employee_data.get('is_sponsored', False)}")
                        print(f"  - sponsored_meal_type: {employee_data.get('sponsored_meal_type', 'None')}")
                        print(f"  - has_lunch: {employee_data.get('has_lunch', False)}")
                        print(f"  - has_coffee: {employee_data.get('has_coffee', False)}")
                        print(f"  - breakfast_items: {employee_data.get('breakfast_items', [])}")
                        print(f"  - lunch_price: {employee_data.get('lunch_price', 'Not specified')}")
                        
                        # Calculate what the remaining cost should be
                        total_amount = employee_data.get('total_amount', 0)
                        print(f"\n🧮 CALCULATION ANALYSIS:")
                        print(f"  - Current display: €{total_amount:.2f}")
                        
                        # If this was €10.05 originally and lunch was €5.00, remaining should be €5.05
                        # But if lunch was different, the calculation might be wrong
                        
                        # Check individual employee profile for original order details
                        employee_id = employee_key.split("ID: ")[1].split(")")[0] if "ID: " in employee_key else None
                        if employee_id:
                            profile_response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
                            if profile_response.status_code == 200:
                                profile_data = profile_response.json()
                                order_history = profile_data.get("order_history", [])
                                
                                for order in order_history:
                                    if order.get("is_sponsored") or order.get("sponsored_meal_type"):
                                        print(f"\n📋 ORIGINAL ORDER DETAILS:")
                                        print(f"  - Original total_price: €{order.get('total_price', 0):.2f}")
                                        print(f"  - Order lunch_price: €{order.get('lunch_price', 'Not specified')}")
                                        print(f"  - Has lunch: {order.get('has_lunch', False)}")
                                        print(f"  - Sponsored meal type: {order.get('sponsored_meal_type', 'None')}")
                                        
                                        original_price = order.get('total_price', 0)
                                        order_lunch_price = order.get('lunch_price', 5.0)  # Default to global
                                        
                                        print(f"\n🎯 EXPECTED CALCULATION:")
                                        print(f"  - Original order: €{original_price:.2f}")
                                        print(f"  - Lunch price to subtract: €{order_lunch_price:.2f}")
                                        print(f"  - Expected remaining: €{original_price - order_lunch_price:.2f}")
                                        print(f"  - Actual display: €{total_amount:.2f}")
                                        
                                        if abs((original_price - order_lunch_price) - total_amount) < 0.01:
                                            print(f"  ✅ CALCULATION IS CORRECT!")
                                        else:
                                            print(f"  ❌ CALCULATION IS WRONG!")
                                            print(f"     Expected: €{original_price - order_lunch_price:.2f}")
                                            print(f"     Actual: €{total_amount:.2f}")
                                            print(f"     Difference: €{abs((original_price - order_lunch_price) - total_amount):.2f}")
                                        
                                        break
                        break
                break

def check_lunch_price_sources():
    """Check different sources of lunch price"""
    print("\n🔍 LUNCH PRICE SOURCES ANALYSIS:")
    
    # Global lunch settings
    response = requests.get(f"{API_BASE}/lunch-settings")
    if response.status_code == 200:
        lunch_settings = response.json()
        print(f"  - Global lunch price: €{lunch_settings.get('price', 0):.2f}")
    
    # Daily lunch price (if any)
    from datetime import datetime
    today = datetime.now().strftime('%Y-%m-%d')
    response = requests.get(f"{API_BASE}/daily-lunch-price/fw4abteilung1/{today}")
    if response.status_code == 200:
        daily_price = response.json()
        print(f"  - Daily lunch price for {today}: €{daily_price.get('lunch_price', 'Not set')}")
    else:
        print(f"  - Daily lunch price for {today}: Not set (using global)")

if __name__ == "__main__":
    print("🔍 Detailed Sponsoring Analysis")
    print("=" * 50)
    
    analyze_specific_employee()
    check_lunch_price_sources()