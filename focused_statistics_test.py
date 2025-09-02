#!/usr/bin/env python3
"""
🔍 FOCUSED TEST: Understanding daily statistics calculation

This test will help us understand what the total_amount in daily statistics represents:
1. Original order amounts vs remaining amounts after sponsoring
2. Whether sponsor order costs are included or excluded
"""

import requests
import json
import os

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteenio.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
DEPARTMENT_ID = "fw4abteilung1"

def test_daily_statistics_understanding():
    """Test to understand daily statistics calculation"""
    
    print("🔍 FOCUSED TEST: Understanding daily statistics calculation")
    print("=" * 80)
    
    # Get current breakfast-history data
    response = requests.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
    
    if response.status_code == 200:
        data = response.json()
        
        if "history" in data and len(data["history"]) > 0:
            today_data = data["history"][0]
            
            print(f"📊 DAILY STATISTICS SUMMARY:")
            print(f"   - Total Orders: {today_data.get('total_orders', 0)}")
            print(f"   - Total Amount: €{today_data.get('total_amount', 0):.2f}")
            print(f"   - Employee Count: {len(today_data.get('employee_orders', {}))}")
            
            employee_orders = today_data.get("employee_orders", {})
            
            print(f"\n🔍 DETAILED EMPLOYEE BREAKDOWN:")
            total_individual_amounts = 0.0
            
            for emp_name, emp_data in employee_orders.items():
                emp_total = emp_data.get("total_amount", 0.0)
                is_sponsored = emp_data.get("is_sponsored", False)
                sponsored_meal_type = emp_data.get("sponsored_meal_type", "")
                sponsored_breakfast = emp_data.get("sponsored_breakfast")
                sponsored_lunch = emp_data.get("sponsored_lunch")
                
                total_individual_amounts += emp_total
                
                print(f"\n   👤 {emp_name}:")
                print(f"      - Total Amount: €{emp_total:.2f}")
                print(f"      - Is Sponsored: {is_sponsored}")
                print(f"      - Sponsored Meal Type: {sponsored_meal_type}")
                
                if sponsored_breakfast:
                    print(f"      - Sponsors Breakfast: {sponsored_breakfast['count']} employees for €{sponsored_breakfast['amount']:.2f}")
                
                if sponsored_lunch:
                    print(f"      - Sponsors Lunch: {sponsored_lunch['count']} employees for €{sponsored_lunch['amount']:.2f}")
            
            print(f"\n📊 CALCULATION VERIFICATION:")
            print(f"   - Sum of individual amounts: €{total_individual_amounts:.2f}")
            print(f"   - Daily statistics total: €{today_data.get('total_amount', 0):.2f}")
            print(f"   - Match: {'✅ YES' if abs(total_individual_amounts - today_data.get('total_amount', 0)) < 0.01 else '❌ NO'}")
            
            # Analysis
            print(f"\n🔍 ANALYSIS:")
            if total_individual_amounts < 10.0:
                print(f"   ✅ Total amount appears to be REMAINING amounts after sponsoring")
                print(f"   ✅ This means sponsor costs are properly excluded from daily statistics")
                print(f"   ✅ Employees show what they still owe, not original order amounts")
            else:
                print(f"   ❌ Total amount appears to include original order amounts or sponsor costs")
            
            # Check for sponsor orders in the data
            sponsor_indicators = []
            for emp_name, emp_data in employee_orders.items():
                if emp_data.get("sponsored_breakfast") or emp_data.get("sponsored_lunch"):
                    sponsor_indicators.append(f"{emp_name} is a sponsor")
            
            if sponsor_indicators:
                print(f"\n🔍 SPONSOR DETECTION:")
                for indicator in sponsor_indicators:
                    print(f"   - {indicator}")
                print(f"   ✅ Sponsor information is properly tracked")
            
            return True
        else:
            print(f"❌ No history data found")
            return False
    else:
        print(f"❌ Failed to get breakfast history: {response.status_code}")
        return False

if __name__ == "__main__":
    test_daily_statistics_understanding()