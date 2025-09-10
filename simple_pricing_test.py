#!/usr/bin/env python3
"""
Simple test to understand the pricing issue
"""

import requests
import json
import os

# Get backend URL from environment
BACKEND_URL = "https://canteen-accounts.preview.emergentagent.com"
API_BASE = f"{BACKEND_URL}/api"

def test_guest_order_pricing():
    """Test guest order pricing issue"""
    
    # Create a guest employee in fw4abteilung2
    employee_data = {
        "name": "SimpleTest_Guest",
        "department_id": "fw4abteilung2"  # Home department
    }
    
    response = requests.post(f"{API_BASE}/employees", json=employee_data)
    if response.status_code != 200:
        print(f"Failed to create employee: {response.text}")
        return
        
    employee = response.json()
    employee_id = employee["id"]
    print(f"Created employee: {employee['name']} (ID: {employee_id})")
    
    # Add as temporary employee to fw4abteilung1
    assignment_data = {"employee_id": employee_id}
    response = requests.post(f"{API_BASE}/departments/fw4abteilung1/temporary-employees", json=assignment_data)
    if response.status_code != 200:
        print(f"Failed to add temporary employee: {response.text}")
        return
    print("Added as temporary employee to fw4abteilung1")
    
    # Create order in fw4abteilung1 (target department)
    order_data = {
        "employee_id": employee_id,
        "department_id": "fw4abteilung1",  # Target department
        "order_type": "breakfast",
        "breakfast_items": [{
            "total_halves": 2,
            "white_halves": 1,  # Should use fw4abteilung1 price: 0.50€
            "seeded_halves": 1,  # Should use fw4abteilung1 price: 0.60€
            "toppings": ["Rührei", "Spiegelei"],
            "has_lunch": True,  # Should use current lunch price
            "boiled_eggs": 1,   # Should use fw4abteilung1 egg price
            "fried_eggs": 0,
            "has_coffee": False
        }]
    }
    
    print("\nCreating order...")
    print(f"Expected calculation (fw4abteilung1 prices):")
    print(f"  White roll half: 0.50€")
    print(f"  Seeded roll half: 0.60€") 
    print(f"  Boiled egg: 0.50€")
    print(f"  Lunch: 6.00€")
    print(f"  Expected total: 7.60€")
    
    response = requests.post(f"{API_BASE}/orders", json=order_data)
    if response.status_code == 200:
        order = response.json()
        actual_total = order["total_price"]
        print(f"\nActual order total: {actual_total}€")
        
        if abs(actual_total - 7.60) < 0.01:
            print("✅ CORRECT: Order uses target department prices")
        else:
            print("❌ INCORRECT: Order may be using home department prices")
            print(f"If using fw4abteilung2 prices:")
            print(f"  White roll half: 0.75€")
            print(f"  Seeded roll half: 1.00€")
            print(f"  Boiled egg: 0.50€") 
            print(f"  Lunch: 6.00€")
            print(f"  fw4abteilung2 total would be: 8.25€")
            
        # Check breakfast history
        print(f"\nChecking breakfast history for fw4abteilung1...")
        history_response = requests.get(f"{API_BASE}/orders/breakfast-history/fw4abteilung1")
        if history_response.status_code == 200:
            history = history_response.json()
            print(f"History response structure: {list(history.keys())}")
            
            if "history" in history:
                for day in history["history"]:
                    employee_orders = day.get("employee_orders", {})
                    for emp_key, emp_data in employee_orders.items():
                        if "SimpleTest_Guest" in emp_key:
                            total_amount = emp_data.get("total_amount", 0)
                            print(f"History shows total: {total_amount}€")
                            if abs(total_amount - 7.60) < 0.01:
                                print("✅ CORRECT: History shows target department prices")
                            else:
                                print("❌ INCORRECT: History shows wrong prices")
                            break
        
        # Check employee profile
        print(f"\nChecking employee profile...")
        profile_response = requests.get(f"{API_BASE}/employees/{employee_id}/profile")
        if profile_response.status_code == 200:
            profile = profile_response.json()
            order_history = profile.get("order_history", [])
            for order_item in order_history:
                if order_item.get("id") == order["id"]:
                    profile_total = order_item.get("total_price", 0)
                    print(f"Profile shows total: {profile_total}€")
                    break
                    
    else:
        print(f"Failed to create order: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_guest_order_pricing()