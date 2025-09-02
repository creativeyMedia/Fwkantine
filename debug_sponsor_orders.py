#!/usr/bin/env python3
"""
Debug script to check sponsor orders in database
"""

import requests
import json
import os
from datetime import datetime
import pytz

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteenio.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test Configuration
DEPARTMENT_ID = "fw4abteilung1"  # Department 1 (1. Wachabteilung)
ADMIN_PASSWORD = "admin1"
DEPARTMENT_NAME = "1. Wachabteilung"

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

def get_berlin_date():
    """Get current date in Berlin timezone"""
    return datetime.now(BERLIN_TZ).date().strftime('%Y-%m-%d')

def authenticate_admin():
    """Authenticate as admin"""
    session = requests.Session()
    response = session.post(f"{API_BASE}/login/department-admin", json={
        "department_name": DEPARTMENT_NAME,
        "admin_password": ADMIN_PASSWORD
    })
    
    if response.status_code == 200:
        print(f"✅ Admin Authentication Success")
        return session
    else:
        print(f"❌ Admin Authentication Failed: {response.status_code} - {response.text}")
        return None

def debug_sponsor_orders():
    """Debug sponsor orders in database"""
    session = authenticate_admin()
    if not session:
        return
    
    today = get_berlin_date()
    print(f"\n🔍 DEBUGGING SPONSOR ORDERS FOR {today}")
    print("=" * 80)
    
    # Get all orders for today
    response = session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Got breakfast-history data")
        
        if "history" in data and len(data["history"]) > 0:
            today_data = data["history"][0]
            employee_orders = today_data.get("employee_orders", {})
            
            print(f"\n📊 Found {len(employee_orders)} employees:")
            for emp_name, emp_data in employee_orders.items():
                print(f"\n👤 {emp_name}:")
                print(f"   - total_amount: €{emp_data.get('total_amount', 0):.2f}")
                print(f"   - sponsored_breakfast: {emp_data.get('sponsored_breakfast')}")
                print(f"   - sponsored_lunch: {emp_data.get('sponsored_lunch')}")
                
                # Check individual order items
                order_items = emp_data.get("order_items", [])
                print(f"   - order_items count: {len(order_items)}")
                for i, item in enumerate(order_items):
                    print(f"     [{i}] {item.get('description', 'No description')} - €{item.get('total_price', 'N/A')}")
        else:
            print(f"❌ No history data found")
    else:
        print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")

if __name__ == "__main__":
    debug_sponsor_orders()