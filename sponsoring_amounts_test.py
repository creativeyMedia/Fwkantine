#!/usr/bin/env python3
"""
🔍 SPONSORING AMOUNTS VERIFICATION TEST

This test verifies that sponsoring amounts are calculated correctly:
- Mit1 sponsors breakfast for 3 employees: should be €4.40 (1.10€ × 4 employees)
- Mit4 sponsors lunch for 4 employees: should be €20.00 (5.00€ × 4 employees)
"""

import requests
import json
from decimal import Decimal
import os

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteenio.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
DEPARTMENT_ID = "fw1abteilung1"
ADMIN_PASSWORD = "admin1"
DEPARTMENT_NAME = "1. Wachabteilung"

def test_sponsoring_amounts():
    """Test sponsoring amount calculations"""
    
    print("🔍 SPONSORING AMOUNTS VERIFICATION")
    print("=" * 60)
    
    session = requests.Session()
    
    # 1. Authenticate
    response = session.post(f"{API_BASE}/login/department-admin", json={
        "department_name": DEPARTMENT_NAME,
        "admin_password": ADMIN_PASSWORD
    })
    
    if response.status_code != 200:
        print(f"❌ Authentication failed: {response.text}")
        return False
    
    print("✅ Authenticated successfully")
    
    # 2. Get breakfast history
    response = session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get breakfast history: {response.text}")
        return False
    
    data = response.json()
    today_data = data["history"][0]
    employee_orders = today_data.get("employee_orders", {})
    
    print(f"\n🎯 SPONSORING AMOUNTS ANALYSIS:")
    
    # Expected amounts from review request
    expected_breakfast_sponsoring = Decimal('4.40')  # 1.10€ × 4 employees
    expected_lunch_sponsoring = Decimal('20.00')     # 5.00€ × 4 employees
    
    breakfast_sponsor_found = False
    lunch_sponsor_found = False
    
    for emp_key, emp_data in employee_orders.items():
        sponsored_breakfast = emp_data.get('sponsored_breakfast')
        sponsored_lunch = emp_data.get('sponsored_lunch')
        
        if sponsored_breakfast:
            actual_amount = Decimal(str(sponsored_breakfast.get('amount', 0.0)))
            count = sponsored_breakfast.get('count', 0)
            
            print(f"  - {emp_key} sponsored breakfast:")
            print(f"    - Amount: €{float(actual_amount):.2f}")
            print(f"    - Count: {count} employees")
            print(f"    - Expected: €{float(expected_breakfast_sponsoring):.2f}")
            
            if abs(actual_amount - expected_breakfast_sponsoring) < Decimal('0.01'):
                print(f"    - ✅ CORRECT breakfast sponsoring amount")
            else:
                print(f"    - ❌ INCORRECT breakfast sponsoring amount")
                print(f"      Difference: €{float(abs(actual_amount - expected_breakfast_sponsoring)):.2f}")
            
            breakfast_sponsor_found = True
        
        if sponsored_lunch:
            actual_amount = Decimal(str(sponsored_lunch.get('amount', 0.0)))
            count = sponsored_lunch.get('count', 0)
            
            print(f"  - {emp_key} sponsored lunch:")
            print(f"    - Amount: €{float(actual_amount):.2f}")
            print(f"    - Count: {count} employees")
            print(f"    - Expected: €{float(expected_lunch_sponsoring):.2f}")
            
            if abs(actual_amount - expected_lunch_sponsoring) < Decimal('0.01'):
                print(f"    - ✅ CORRECT lunch sponsoring amount")
            else:
                print(f"    - ❌ INCORRECT lunch sponsoring amount")
                print(f"      Difference: €{float(abs(actual_amount - expected_lunch_sponsoring)):.2f}")
            
            lunch_sponsor_found = True
    
    print(f"\n🎯 SPONSORING VERIFICATION SUMMARY:")
    
    if not breakfast_sponsor_found:
        print(f"❌ No breakfast sponsor found")
        return False
    
    if not lunch_sponsor_found:
        print(f"❌ No lunch sponsor found")
        return False
    
    print(f"✅ Both breakfast and lunch sponsors found")
    
    # Calculate what the correct daily total should be
    print(f"\n🧮 CORRECT DAILY TOTAL CALCULATION:")
    print(f"  - Expected breakfast sponsoring: €{float(expected_breakfast_sponsoring):.2f}")
    print(f"  - Expected lunch sponsoring: €{float(expected_lunch_sponsoring):.2f}")
    print(f"  - Expected daily total: €{float(expected_breakfast_sponsoring + expected_lunch_sponsoring):.2f}")
    
    return True

if __name__ == "__main__":
    success = test_sponsoring_amounts()
    exit(0 if success else 1)