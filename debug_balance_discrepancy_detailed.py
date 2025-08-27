#!/usr/bin/env python3
"""
Detailed Balance Discrepancy Debug

Systematische Analyse der Saldo-Diskrepanz zwischen Order und Balance
"""

import requests
import json
from datetime import datetime, date

BASE_URL = "https://mealflow-1.preview.emergentagent.com/api"
DEPARTMENT_ID = "fw4abteilung3"
ADMIN_PASSWORD = "admin3"

def debug_balance_discrepancy():
    print("🔍 Systematic Balance Discrepancy Analysis...")
    
    # 1. Get current employee balances
    employees_resp = requests.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
    if employees_resp.status_code != 200:
        print(f"❌ Failed to get employees: {employees_resp.status_code}")
        return
    
    employees = employees_resp.json()
    print(f"\n📊 Found {len(employees)} employees in Department 3")
    
    # Focus on employees with significant balances
    target_employees = [emp for emp in employees if emp.get('breakfast_balance', 0) > 10]
    print(f"🎯 Target employees (>10€): {len(target_employees)}")
    
    for emp in target_employees[:3]:  # Analyze first 3
        print(f"\n{'='*60}")
        print(f"👤 ANALYZING: {emp['name']} (ID: {emp['id'][-8:]})")
        print(f"💰 Current Balance: {emp['breakfast_balance']:.2f}€")
        
        # Get their orders
        orders_resp = requests.get(f"{BASE_URL}/employees/{emp['id']}/orders")
        if orders_resp.status_code != 200:
            print(f"   ❌ Failed to get orders: {orders_resp.status_code}")
            continue
        
        orders_data = orders_resp.json()
        orders = orders_data.get("orders", [])
        
        today = date.today().isoformat()
        today_orders = [order for order in orders if order.get('timestamp', '').startswith(today)]
        
        print(f"📋 Today's Orders: {len(today_orders)}")
        
        balance_calculation = 0.0
        for i, order in enumerate(today_orders):
            print(f"\n   📝 Order {i+1}:")
            print(f"      Order ID: {order.get('id', 'N/A')[-8:]}")
            print(f"      Total Price: {order.get('total_price', 0):.2f}€")
            print(f"      Is Sponsored: {order.get('is_sponsored', False)}")
            print(f"      Is Sponsor Order: {order.get('is_sponsor_order', False)}")
            
            # Analyze readable_items
            readable_items = order.get('readable_items', [])
            items_total = 0.0
            print(f"      Readable Items ({len(readable_items)}):")
            
            for item in readable_items:
                desc = item.get('description', '')
                price_str = item.get('total_price', '0')
                unit_price = item.get('unit_price', '')
                
                # Parse price
                try:
                    if '€' in str(price_str):
                        price = float(str(price_str).replace('€', '').replace(',', '.').strip())
                    else:
                        price = float(price_str) if price_str else 0
                    items_total += price
                except:
                    price = 0
                
                print(f"         - {desc}: {price:.2f}€ (unit: {unit_price})")
            
            print(f"      Items Total: {items_total:.2f}€")
            print(f"      Price vs Items Diff: {order.get('total_price', 0) - items_total:.2f}€")
            
            # Check if this order affects balance
            if order.get('is_sponsored') and not order.get('is_sponsor_order'):
                # For sponsored orders, only certain costs remain
                if order.get('sponsored_meal_type') == 'breakfast':
                    # Only coffee remains
                    remaining_cost = 0
                    for item in order.get('breakfast_items', []):
                        if item.get('has_coffee', False):
                            remaining_cost += 1.0  # Coffee price
                    print(f"      Sponsored (Breakfast): Only coffee remains = {remaining_cost:.2f}€")
                    balance_calculation += remaining_cost
                elif order.get('sponsored_meal_type') == 'lunch':
                    # Only breakfast remains
                    full_cost = order.get('total_price', 0)
                    lunch_cost = 0  # Calculate lunch cost
                    for item in order.get('breakfast_items', []):
                        if item.get('has_lunch', False):
                            # Estimate lunch cost (total - breakfast cost)
                            lunch_cost = 5.0  # Approximate
                    remaining_cost = full_cost - lunch_cost
                    print(f"      Sponsored (Lunch): Breakfast remains = {remaining_cost:.2f}€")
                    balance_calculation += remaining_cost
                else:
                    print(f"      Sponsored (Unknown type): Full cost = {order.get('total_price', 0):.2f}€")
                    balance_calculation += order.get('total_price', 0)
            else:
                # Regular order or sponsor order - full cost
                print(f"      Regular/Sponsor Order: Full cost = {order.get('total_price', 0):.2f}€")
                balance_calculation += order.get('total_price', 0)
        
        print(f"\n💡 SUMMARY:")
        print(f"   Actual Balance: {emp['breakfast_balance']:.2f}€")
        print(f"   Calculated Balance: {balance_calculation:.2f}€")
        print(f"   DISCREPANCY: {emp['breakfast_balance'] - balance_calculation:.2f}€")
        
        if abs(emp['breakfast_balance'] - balance_calculation) > 0.01:
            print(f"   ⚠️  SIGNIFICANT DISCREPANCY FOUND!")
        else:
            print(f"   ✅ Balance matches calculation")

if __name__ == "__main__":
    debug_balance_discrepancy()