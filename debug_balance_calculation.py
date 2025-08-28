#!/usr/bin/env python3
"""
Balance Calculation Debugging Script

Debuggt die 0.80€ vs 1.00€ Problem bei gesponserten Bestellungen
"""

import requests
import json
from datetime import datetime, date

BASE_URL = "https://canteen-manager-2.preview.emergentagent.com/api"
DEPARTMENT_ID = "fw4abteilung2"

def debug_balance_calculations():
    print("🔍 Debugging Balance Calculations...")
    
    # Get all employees with non-zero balances
    print("\n1. Current Employee Balances:")
    employees_resp = requests.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
    if employees_resp.status_code == 200:
        employees = employees_resp.json()
        non_zero_employees = [emp for emp in employees if emp.get('breakfast_balance', 0) != 0]
        for emp in non_zero_employees:
            print(f"   • {emp['name']}: {emp.get('breakfast_balance', 0):.2f}€")
    
    # Get menu prices for verification
    print("\n2. Menu Prices:")
    menu_resp = requests.get(f"{BASE_URL}/menu/breakfast/{DEPARTMENT_ID}")
    if menu_resp.status_code == 200:
        menu = menu_resp.json()
        for item in menu:
            print(f"   • {item['roll_type']}: {item['price']:.2f}€")
    
    # Get lunch settings
    lunch_resp = requests.get(f"{BASE_URL}/lunch-settings")
    if lunch_resp.status_code == 200:
        lunch_settings = lunch_resp.json()
        print(f"   • Eggs: {lunch_settings.get('boiled_eggs_price', 0):.2f}€")
        print(f"   • Lunch: {lunch_settings.get('price', 0):.2f}€")
        print(f"   • Coffee: {lunch_settings.get('coffee_price', 0):.2f}€")
    
    # Get recent orders to see actual costs
    print("\n3. Recent Orders (today):")
    today = date.today().isoformat()
    
    # Try to get orders via breakfast history
    try:
        history_resp = requests.post(
            f"{BASE_URL}/department-admin/breakfast-history",
            headers={"Content-Type": "application/json"},
            json={
                "department_id": DEPARTMENT_ID,
                "admin_password": "admin2"
            }
        )
        if history_resp.status_code == 200:
            history = history_resp.json()
            today_data = None
            for day_data in history:
                if day_data.get('date') == today:
                    today_data = day_data
                    break
            
            if today_data:
                print(f"   📅 {today}: {today_data.get('total_orders', 0)} orders, {today_data.get('total_amount', 0):.2f}€")
                
                # Get individual orders
                orders_resp = requests.post(
                    f"{BASE_URL}/department-admin/orders",
                    headers={"Content-Type": "application/json"},
                    json={
                        "department_id": DEPARTMENT_ID,
                        "admin_password": "admin2"
                    }
                )
                if orders_resp.status_code == 200:
                    orders = orders_resp.json()
                    today_orders = [order for order in orders if order.get('timestamp', '').startswith(today)]
                    
                    print(f"\n4. Today's Order Details:")
                    for i, order in enumerate(today_orders[:10]):  # Show max 10
                        print(f"   Order {i+1}:")
                        print(f"      Employee: {order.get('employee_name', 'Unknown')}")
                        print(f"      Total: {order.get('total_price', 0):.2f}€")
                        print(f"      Sponsored: {order.get('is_sponsored', False)}")
                        if order.get('is_sponsored'):
                            print(f"      Sponsored by: {order.get('sponsored_by_name', 'Unknown')}")
                        
                        # Show readable items
                        readable_items = order.get('readable_items', [])
                        for item in readable_items:
                            desc = item.get('description', '')
                            price = item.get('total_price', '')
                            print(f"         - {desc}: {price}")
            else:
                print(f"   No orders found for {today}")
        else:
            print(f"   Failed to get breakfast history: {history_resp.status_code}")
    except Exception as e:
        print(f"   Error getting order details: {str(e)}")

if __name__ == "__main__":
    debug_balance_calculations()