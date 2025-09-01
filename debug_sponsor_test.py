#!/usr/bin/env python3
"""
Debug script to examine the breakfast-history API response structure
"""

import requests
import json
import os

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteen-fire.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
DEPARTMENT_ID = "fw4abteilung2"

def debug_breakfast_history():
    """Debug the breakfast history API response"""
    try:
        response = requests.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("🔍 BREAKFAST HISTORY API RESPONSE STRUCTURE:")
            print("=" * 60)
            
            if "history" in data and len(data["history"]) > 0:
                today_data = data["history"][0]
                
                print(f"📅 Date: {today_data.get('date', 'N/A')}")
                print(f"📊 Total Orders: {today_data.get('total_orders', 0)}")
                print(f"💰 Total Amount: €{today_data.get('total_amount', 0):.2f}")
                
                employee_orders = today_data.get("employee_orders", {})
                print(f"👥 Employee Count: {len(employee_orders)}")
                
                print("\n🔍 DETAILED EMPLOYEE DATA:")
                print("-" * 40)
                
                for employee_name, employee_data in employee_orders.items():
                    print(f"\n👤 Employee: {employee_name}")
                    print(f"   Total Amount: €{employee_data.get('total_amount', 0):.2f}")
                    print(f"   White Halves: {employee_data.get('white_halves', 0)}")
                    print(f"   Seeded Halves: {employee_data.get('seeded_halves', 0)}")
                    print(f"   Boiled Eggs: {employee_data.get('boiled_eggs', 0)}")
                    print(f"   Has Lunch: {employee_data.get('has_lunch', False)}")
                    print(f"   Has Coffee: {employee_data.get('has_coffee', False)}")
                    
                    # Check for sponsored fields
                    sponsored_breakfast = employee_data.get('sponsored_breakfast')
                    sponsored_lunch = employee_data.get('sponsored_lunch')
                    
                    if sponsored_breakfast:
                        print(f"   ✅ Sponsored Breakfast: {sponsored_breakfast}")
                    else:
                        print(f"   ❌ No Sponsored Breakfast field")
                    
                    if sponsored_lunch:
                        print(f"   ✅ Sponsored Lunch: {sponsored_lunch}")
                    else:
                        print(f"   ❌ No Sponsored Lunch field")
                    
                    # Check for any other fields that might indicate sponsoring
                    other_fields = {k: v for k, v in employee_data.items() 
                                  if k not in ['total_amount', 'white_halves', 'seeded_halves', 
                                             'boiled_eggs', 'has_lunch', 'has_coffee', 
                                             'sponsored_breakfast', 'sponsored_lunch']}
                    
                    if other_fields:
                        print(f"   🔍 Other fields: {other_fields}")
                
                # Print raw JSON for detailed inspection
                print(f"\n📋 RAW JSON RESPONSE (first employee):")
                print("-" * 40)
                if employee_orders:
                    first_employee = list(employee_orders.keys())[0]
                    print(json.dumps(employee_orders[first_employee], indent=2))
                
            else:
                print("❌ No history data found")
                
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_breakfast_history()