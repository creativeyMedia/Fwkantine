#!/usr/bin/env python3
"""
Debug script to test retroactive lunch price update logic
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://firebrigade-food.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def debug_retroactive_update():
    print("🔍 DEBUGGING RETROACTIVE LUNCH PRICE UPDATE")
    print("=" * 50)
    
    # 1. Check current lunch settings
    print("\n1. Current lunch settings:")
    response = requests.get(f"{API_BASE}/lunch-settings")
    if response.status_code == 200:
        settings = response.json()
        print(f"   Global lunch price: €{settings.get('price', 'N/A')}")
    else:
        print(f"   Failed to get lunch settings: {response.status_code}")
    
    # 2. Get today's orders before update
    print("\n2. Today's orders before update:")
    response = requests.get(f"{API_BASE}/orders/breakfast-history/fw4abteilung1")
    if response.status_code == 200:
        history = response.json()
        if history.get("history"):
            today_data = history["history"][0]  # Most recent day
            print(f"   Date: {today_data.get('date')}")
            print(f"   Total orders: {today_data.get('total_orders')}")
            print(f"   Daily lunch price: €{today_data.get('daily_lunch_price')}")
            
            for emp_key, emp_data in today_data.get("employee_orders", {}).items():
                if emp_data.get("has_lunch"):
                    print(f"   {emp_key}: Total €{emp_data.get('total_amount')}, Has lunch: {emp_data.get('has_lunch')}")
    else:
        print(f"   Failed to get breakfast history: {response.status_code}")
    
    # 3. Apply retroactive update with debugging
    print("\n3. Applying retroactive lunch price update (€5.0 → €4.0):")
    response = requests.put(f"{API_BASE}/lunch-settings?price=4.0&department_id=fw4abteilung1")
    if response.status_code == 200:
        result = response.json()
        print(f"   Result: {result}")
        print(f"   Updated orders: {result.get('updated_orders', 0)}")
    else:
        print(f"   Failed to update lunch price: {response.status_code} - {response.text}")
    
    # 4. Check orders after update
    print("\n4. Today's orders after update:")
    response = requests.get(f"{API_BASE}/orders/breakfast-history/fw4abteilung1")
    if response.status_code == 200:
        history = response.json()
        if history.get("history"):
            today_data = history["history"][0]  # Most recent day
            print(f"   Date: {today_data.get('date')}")
            print(f"   Total orders: {today_data.get('total_orders')}")
            print(f"   Daily lunch price: €{today_data.get('daily_lunch_price')}")
            
            for emp_key, emp_data in today_data.get("employee_orders", {}).items():
                if emp_data.get("has_lunch"):
                    print(f"   {emp_key}: Total €{emp_data.get('total_amount')}, Has lunch: {emp_data.get('has_lunch')}")
    else:
        print(f"   Failed to get breakfast history: {response.status_code}")
    
    # 5. Check individual employee profiles
    print("\n5. Individual employee order details:")
    
    # Get employees from today's orders
    guest_id = "06b94b1f-2f63-478d-ae8f-ac13d239f258"
    regular_id = "4007d117-e917-4e0c-86b6-65c9a56a725d"
    
    for emp_id, emp_name in [(guest_id, "Guest"), (regular_id, "Regular")]:
        print(f"\n   {emp_name} Employee ({emp_id}):")
        response = requests.get(f"{API_BASE}/employees/{emp_id}/profile")
        if response.status_code == 200:
            profile = response.json()
            for order in profile.get("order_history", []):
                if order.get("has_lunch"):
                    print(f"     Order {order['id'][:8]}...")
                    print(f"       Total price: €{order['total_price']}")
                    print(f"       Lunch price: €{order.get('lunch_price', 'N/A')}")
                    print(f"       Has lunch: {order.get('has_lunch')}")
                    print(f"       Timestamp: {order.get('timestamp')}")
        else:
            print(f"     Failed to get profile: {response.status_code}")

if __name__ == "__main__":
    debug_retroactive_update()