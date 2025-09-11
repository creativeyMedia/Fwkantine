#!/usr/bin/env python3
"""
Detailed Balance Test - Check drinks/sweets balance updates in detail
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def detailed_balance_test():
    """Test balance updates in detail"""
    
    print("🧪 Detailed Balance Test - Drinks/Sweets Orders")
    print("=" * 60)
    
    # Create a test employee
    employee_data = {
        "name": f"DetailedTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "department_id": "fw4abteilung1"
    }
    
    response = requests.post(f"{API_BASE}/employees", json=employee_data)
    if response.status_code != 200:
        print(f"❌ Failed to create employee: {response.status_code}")
        return
        
    employee = response.json()
    employee_id = employee["id"]
    print(f"✅ Created test employee: {employee['name']} (ID: {employee_id[:8]}...)")
    
    # Check initial balances (both profile and all-balances)
    def check_balances(label):
        print(f"\n📊 {label}:")
        
        # Profile endpoint
        response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
        if response.status_code == 200:
            profile = response.json()
            breakfast_balance = profile.get("breakfast_balance", 0.0)
            drinks_balance = profile.get("drinks_sweets_balance", 0.0)
            print(f"   Profile - Breakfast: €{breakfast_balance}, Drinks/Sweets: €{drinks_balance}")
        
        # All balances endpoint
        response = requests.get(f"{API_BASE}/employees/{employee_id}/all-balances")
        if response.status_code == 200:
            all_balances = response.json()
            main_breakfast = all_balances["main_balances"]["breakfast"]
            main_drinks = all_balances["main_balances"]["drinks_sweets"]
            dept1_breakfast = all_balances["subaccount_balances"]["fw4abteilung1"]["breakfast"]
            dept1_drinks = all_balances["subaccount_balances"]["fw4abteilung1"]["drinks"]
            print(f"   Main Account - Breakfast: €{main_breakfast}, Drinks/Sweets: €{main_drinks}")
            print(f"   Dept1 Subaccount - Breakfast: €{dept1_breakfast}, Drinks: €{dept1_drinks}")
    
    check_balances("Initial Balances")
    
    # Get drinks menu
    response = requests.get(f"{API_BASE}/menu/drinks/fw4abteilung1")
    if response.status_code != 200:
        print(f"❌ Failed to get drinks menu: {response.status_code}")
        return
        
    drinks_menu = response.json()
    if not drinks_menu:
        print("❌ No drinks in menu")
        return
        
    first_drink = drinks_menu[0]
    drink_id = first_drink["id"]
    drink_name = first_drink["name"]
    drink_price = first_drink["price"]
    print(f"\n🍺 Ordering: {drink_name} €{drink_price}")
    
    # Create drinks order
    order_data = {
        "employee_id": employee_id,
        "department_id": "fw4abteilung1",
        "order_type": "drinks",
        "drink_items": {drink_id: 1}
    }
    
    response = requests.post(f"{API_BASE}/orders", json=order_data)
    if response.status_code == 200:
        order = response.json()
        order_id = order["id"]
        order_total = order["total_price"]
        print(f"✅ Created drinks order (ID: {order_id[:8]}..., Total: €{order_total})")
    else:
        print(f"❌ Failed to create order: {response.status_code} - {response.text}")
        return
    
    check_balances("After Drinks Order")
    
    # Cancel the order
    print(f"\n🗑️ Cancelling drinks order...")
    response = requests.delete(f"{API_BASE}/employee/{employee_id}/orders/{order_id}")
    if response.status_code == 200:
        print("✅ Order cancelled successfully")
    else:
        print(f"❌ Failed to cancel order: {response.status_code} - {response.text}")
        return
    
    check_balances("After Cancellation")
    
    # Now test sweets
    print(f"\n" + "=" * 60)
    print("🍫 TESTING SWEETS ORDER")
    
    # Get sweets menu
    response = requests.get(f"{API_BASE}/menu/sweets/fw4abteilung1")
    if response.status_code != 200:
        print(f"❌ Failed to get sweets menu: {response.status_code}")
        return
        
    sweets_menu = response.json()
    if not sweets_menu:
        print("❌ No sweets in menu")
        return
        
    first_sweet = sweets_menu[0]
    sweet_id = first_sweet["id"]
    sweet_name = first_sweet["name"]
    sweet_price = first_sweet["price"]
    print(f"🍫 Ordering: {sweet_name} €{sweet_price}")
    
    # Create sweets order
    order_data = {
        "employee_id": employee_id,
        "department_id": "fw4abteilung1",
        "order_type": "sweets",
        "sweet_items": {sweet_id: 1}
    }
    
    response = requests.post(f"{API_BASE}/orders", json=order_data)
    if response.status_code == 200:
        order = response.json()
        order_id = order["id"]
        order_total = order["total_price"]
        print(f"✅ Created sweets order (ID: {order_id[:8]}..., Total: €{order_total})")
    else:
        print(f"❌ Failed to create sweets order: {response.status_code} - {response.text}")
        return
    
    check_balances("After Sweets Order")
    
    # Cancel the sweets order
    print(f"\n🗑️ Cancelling sweets order...")
    response = requests.delete(f"{API_BASE}/employee/{employee_id}/orders/{order_id}")
    if response.status_code == 200:
        print("✅ Sweets order cancelled successfully")
    else:
        print(f"❌ Failed to cancel sweets order: {response.status_code} - {response.text}")
        return
    
    check_balances("After Sweets Cancellation")
    
    print(f"\n🎯 CONCLUSION:")
    print("If balances return to 0 after cancellation, BUG 1 is FIXED")
    print("If balances become positive after cancellation, BUG 1 still EXISTS")

if __name__ == "__main__":
    detailed_balance_test()