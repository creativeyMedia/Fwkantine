#!/usr/bin/env python3
"""
Debug script to understand the sponsoring data structure issue
"""

import requests
import json
from datetime import datetime
import pytz
import os

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteen-fire.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

DEPARTMENT_ID = "fw1abteilung1"
ADMIN_PASSWORD = "admin1"
DEPARTMENT_NAME = "1. Wachabteilung"

def main():
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{API_BASE}/login/department-admin", json={
        "department_name": DEPARTMENT_NAME,
        "admin_password": ADMIN_PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.status_code}")
        return
    
    print("✅ Authenticated successfully")
    
    # Get breakfast history to see current data structure
    response = session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
    
    if response.status_code == 200:
        data = response.json()
        
        if "history" in data and len(data["history"]) > 0:
            today_data = data["history"][0]
            employee_orders = today_data.get("employee_orders", {})
            
            print(f"\n🔍 Current Employee Orders Structure:")
            print("=" * 80)
            
            for emp_name, emp_data in employee_orders.items():
                print(f"\n👤 {emp_name}:")
                print(f"   - total_amount: €{emp_data.get('total_amount', 0):.2f}")
                print(f"   - is_sponsored: {emp_data.get('is_sponsored')}")
                print(f"   - sponsored_meal_type: {emp_data.get('sponsored_meal_type')}")
                print(f"   - sponsored_breakfast: {emp_data.get('sponsored_breakfast')}")
                print(f"   - sponsored_lunch: {emp_data.get('sponsored_lunch')}")
                
                # Check if this employee should have sponsoring info
                if "Mit1" in emp_name:
                    print(f"   ❓ Mit1 should show breakfast sponsoring info (sponsored others)")
                elif "Mit4" in emp_name:
                    print(f"   ❓ Mit4 should show lunch sponsoring info (sponsored Mit1)")
                elif "Mit2" in emp_name or "Mit3" in emp_name:
                    print(f"   ❓ {emp_name.split()[0]} should show NO sponsoring info (was sponsored)")
            
            print(f"\n🔍 Analysis:")
            print("=" * 80)
            print("The issue is that sponsored_breakfast and sponsored_lunch are all null.")
            print("This suggests the breakfast-history endpoint logic for finding sponsoring activities is incorrect.")
            print("\nThe current logic looks for orders with sponsored_by_employee_id = current_employee_id")
            print("But this finds orders that were sponsored BY others FOR this employee.")
            print("We need to find orders where this employee sponsored others.")
            
        else:
            print("❌ No history data found")
    else:
        print(f"❌ Failed to get breakfast history: {response.status_code}")

if __name__ == "__main__":
    main()