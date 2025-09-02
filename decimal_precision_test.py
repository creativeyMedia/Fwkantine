#!/usr/bin/env python3
"""
🎯 DECIMAL PRECISION FIX VERIFICATION TEST

This test specifically verifies the decimal precision fix for the rounding error
mentioned in the review request: €24.30 vs €24.40 discrepancy.

Expected behavior after fix:
- 4 employees with €7.60 orders each
- Mit1 sponsors breakfast (€4.40 cost)  
- Mit4 sponsors lunch (€20.00 cost)
- Daily total should be €24.40 exactly (NOT €24.30 or €30.40)
"""

import requests
import json
from decimal import Decimal, ROUND_HALF_UP
import os

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteenio.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
DEPARTMENT_ID = "fw1abteilung1"
ADMIN_PASSWORD = "admin1"
DEPARTMENT_NAME = "1. Wachabteilung"

def test_decimal_precision_fix():
    """Test the specific decimal precision scenario from review request"""
    
    print("🎯 DECIMAL PRECISION FIX VERIFICATION")
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
    
    # 2. Get breakfast history to check current totals
    response = session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
    
    if response.status_code != 200:
        print(f"❌ Failed to get breakfast history: {response.text}")
        return False
    
    data = response.json()
    
    if "history" not in data or len(data["history"]) == 0:
        print("❌ No history data found")
        return False
    
    today_data = data["history"][0]
    total_orders = today_data.get("total_orders", 0)
    total_amount = today_data.get("total_amount", 0.0)
    employee_orders = today_data.get("employee_orders", {})
    
    print(f"\n📊 CURRENT BREAKFAST HISTORY DATA:")
    print(f"  - Total Orders: {total_orders}")
    print(f"  - Total Amount: €{total_amount:.2f}")
    print(f"  - Employees: {len(employee_orders)}")
    
    # 3. Analyze individual employee totals
    print(f"\n🔍 INDIVIDUAL EMPLOYEE ANALYSIS:")
    individual_sum = Decimal('0')
    sponsor_costs = Decimal('0')
    
    for emp_key, emp_data in employee_orders.items():
        emp_total = Decimal(str(emp_data.get('total_amount', 0.0)))
        individual_sum += emp_total
        
        # Check if this employee has sponsoring costs
        sponsored_breakfast = emp_data.get('sponsored_breakfast')
        sponsored_lunch = emp_data.get('sponsored_lunch')
        
        sponsor_cost_for_employee = Decimal('0')
        if sponsored_breakfast:
            sponsor_cost_for_employee += Decimal(str(sponsored_breakfast.get('amount', 0.0)))
        if sponsored_lunch:
            sponsor_cost_for_employee += Decimal(str(sponsored_lunch.get('amount', 0.0)))
        
        sponsor_costs += sponsor_cost_for_employee
        
        print(f"  - {emp_key}: €{float(emp_total):.2f}")
        if sponsor_cost_for_employee > 0:
            print(f"    - Sponsor costs: €{float(sponsor_cost_for_employee):.2f}")
        if emp_data.get('is_sponsored'):
            print(f"    - Is sponsored: {emp_data.get('sponsored_meal_type', 'unknown')}")
    
    # 4. Calculate expected totals
    expected_daily_total = Decimal('24.40')  # 4.40 + 20.00 from review request
    
    print(f"\n🧮 CALCULATION ANALYSIS:")
    print(f"  - Sum of individual totals: €{float(individual_sum):.2f}")
    print(f"  - Total sponsor costs: €{float(sponsor_costs):.2f}")
    print(f"  - Expected daily total: €{float(expected_daily_total):.2f}")
    print(f"  - Actual daily total: €{total_amount:.2f}")
    
    # 5. Check for the specific issues
    print(f"\n🎯 DECIMAL PRECISION VERIFICATION:")
    
    # Check if we have the expected 4 orders
    if total_orders != 4:
        print(f"❌ Expected 4 orders, found {total_orders}")
        return False
    else:
        print(f"✅ Correct order count: {total_orders}")
    
    # Check if daily total matches expected (24.40€)
    actual_total = Decimal(str(total_amount))
    total_difference = abs(actual_total - expected_daily_total)
    
    if total_difference < Decimal('0.01'):
        print(f"✅ Daily total is CORRECT: €{total_amount:.2f}")
        print(f"🎉 DECIMAL PRECISION FIX VERIFIED SUCCESSFULLY!")
        return True
    else:
        print(f"❌ Daily total is INCORRECT:")
        print(f"   Expected: €{float(expected_daily_total):.2f}")
        print(f"   Actual: €{total_amount:.2f}")
        print(f"   Difference: €{float(total_difference):.2f}")
        
        # Diagnose the specific issue
        if abs(actual_total - Decimal('30.40')) < Decimal('0.01'):
            print(f"🚨 ROOT CAUSE: Daily total includes sponsor costs (should exclude them)")
            print(f"   Individual sum: €{float(individual_sum):.2f}")
            print(f"   Should be: €{float(individual_sum - sponsor_costs):.2f}")
        elif abs(actual_total - Decimal('24.30')) < Decimal('0.01'):
            print(f"🚨 ROOT CAUSE: Original rounding error still present (€0.10 missing)")
        
        return False

if __name__ == "__main__":
    success = test_decimal_precision_fix()
    exit(0 if success else 1)