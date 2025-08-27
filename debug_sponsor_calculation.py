#!/usr/bin/env python3
"""
DEBUG SPONSOR CALCULATION STEP BY STEP

Now that I found the exact -17.50€ balance issue, let me trace through the 
sponsor calculation logic step by step to understand where the error occurs.

From the analysis:
- Brauni (ID: 5d1bb273): €-17.50 (PROBLEM)
- Expected: €27.50
- Difference: €45.00

Let me examine the exact calculation that led to this negative balance.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "https://mealflow-1.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class DebugSponsorCalculation:
    def __init__(self):
        self.session = requests.Session()
        self.admin_auth = None
        
    def authenticate_admin(self):
        """Authenticate as department admin"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                self.admin_auth = response.json()
                print(f"✅ Successfully authenticated as admin for {DEPARTMENT_NAME}")
                return True
            else:
                print(f"❌ Authentication failed: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def get_problem_employee_details(self):
        """Get details of the employee with -17.50€ balance"""
        try:
            print(f"\n🔍 GETTING PROBLEM EMPLOYEE DETAILS:")
            print("=" * 60)
            
            # Get all employees to find the one with -17.50€
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            if response.status_code != 200:
                print(f"❌ Could not fetch employees: {response.status_code} - {response.text}")
                return None
            
            employees = response.json()
            problem_employee = None
            
            for employee in employees:
                balance = employee.get("breakfast_balance", 0)
                if abs(balance + 17.50) < 0.1:  # Find the -17.50€ balance
                    problem_employee = employee
                    break
            
            if not problem_employee:
                print("❌ Could not find employee with -17.50€ balance")
                return None
            
            print(f"🎯 FOUND PROBLEM EMPLOYEE:")
            print(f"- Name: {problem_employee['name']}")
            print(f"- ID: {problem_employee['id']}")
            print(f"- Balance: €{problem_employee['breakfast_balance']:.2f}")
            
            return problem_employee
                
        except Exception as e:
            print(f"❌ Error getting employee details: {str(e)}")
            return None
    
    def get_employee_orders(self, employee_id):
        """Get orders for the problem employee"""
        try:
            print(f"\n🔍 GETTING EMPLOYEE ORDERS:")
            print("=" * 60)
            
            response = self.session.get(f"{BASE_URL}/employees/{employee_id}/orders")
            if response.status_code != 200:
                print(f"❌ Could not fetch employee orders: {response.status_code} - {response.text}")
                return None
            
            orders_data = response.json()
            orders_list = orders_data.get("orders", [])
            
            # Find today's order
            today_date = date.today().isoformat()
            today_orders = []
            
            for order in orders_list:
                order_date = order.get("timestamp", "")[:10]
                if order_date == today_date:
                    today_orders.append(order)
            
            if not today_orders:
                print("❌ No orders found for today")
                return None
            
            print(f"📋 FOUND {len(today_orders)} ORDER(S) FOR TODAY:")
            
            for i, order in enumerate(today_orders):
                print(f"\n--- ORDER {i+1} ---")
                print(f"- Order ID: {order.get('id', 'Unknown')}")
                print(f"- Total Price: €{order.get('total_price', 0):.2f}")
                print(f"- Is Sponsor Order: {order.get('is_sponsor_order', False)}")
                print(f"- Is Sponsored: {order.get('is_sponsored', False)}")
                
                # Check if this is a sponsor order
                if order.get('is_sponsor_order'):
                    print(f"🎯 THIS IS A SPONSOR ORDER!")
                    print(f"- Sponsor Total Cost: €{order.get('sponsor_total_cost', 0):.2f}")
                    print(f"- Sponsor Employee Count: {order.get('sponsor_employee_count', 0)}")
                    print(f"- Sponsored Meal Type: {order.get('sponsored_meal_type', 'Unknown')}")
                    
                    # This should help us understand the calculation
                    sponsor_total_cost = order.get('sponsor_total_cost', 0)
                    original_order_cost = order.get('total_price', 0)
                    
                    print(f"\n📊 SPONSOR CALCULATION ANALYSIS:")
                    print(f"- Original order cost: €{original_order_cost:.2f}")
                    print(f"- Total sponsored cost: €{sponsor_total_cost:.2f}")
                    print(f"- Expected additional cost: €{sponsor_total_cost - original_order_cost:.2f}")
                    print(f"- Expected final balance: €{original_order_cost + (sponsor_total_cost - original_order_cost):.2f}")
                    print(f"- Actual balance: €-17.50")
                    
                    # Calculate what went wrong
                    expected_balance = sponsor_total_cost
                    actual_balance = -17.50
                    error_amount = expected_balance - actual_balance
                    print(f"- Error amount: €{error_amount:.2f}")
                
                # Show breakfast items
                breakfast_items = order.get('breakfast_items', [])
                if breakfast_items:
                    print(f"- Breakfast Items:")
                    for item in breakfast_items:
                        print(f"  - White halves: {item.get('white_halves', 0)}")
                        print(f"  - Seeded halves: {item.get('seeded_halves', 0)}")
                        print(f"  - Boiled eggs: {item.get('boiled_eggs', 0)}")
                        print(f"  - Has lunch: {item.get('has_lunch', False)}")
                        print(f"  - Has coffee: {item.get('has_coffee', False)}")
            
            return today_orders
                
        except Exception as e:
            print(f"❌ Error getting employee orders: {str(e)}")
            return None
    
    def analyze_calculation_error(self):
        """Analyze what went wrong in the sponsor calculation"""
        try:
            print(f"\n🔍 ANALYZING CALCULATION ERROR:")
            print("=" * 60)
            
            print("Based on the sponsor-meal endpoint logic:")
            print("1. sponsor_additional_cost = total_sponsored_cost - sponsor_contributed_amount")
            print("2. new_sponsor_balance = current_balance + sponsor_additional_cost")
            print()
            
            print("Expected scenario:")
            print("- Sponsor initial balance: €6.50 (from own order)")
            print("- Total sponsored cost: €25.00 (5 employees × €5.00 lunch each)")
            print("- Sponsor contributed amount: €5.00 (sponsor's own lunch)")
            print("- Sponsor additional cost: €25.00 - €5.00 = €20.00")
            print("- Final balance: €6.50 + €20.00 = €26.50")
            print()
            
            print("Actual result: €-17.50")
            print()
            
            print("🚨 POSSIBLE ERROR SCENARIOS:")
            print("1. Sign error: new_balance = current_balance - sponsor_additional_cost")
            print("   Result: €6.50 - €20.00 = €-13.50 (close but not exact)")
            print()
            print("2. Wrong formula: new_balance = current_balance - total_sponsored_cost")
            print("   Result: €6.50 - €25.00 = €-18.50 (very close!)")
            print()
            print("3. Double subtraction: new_balance = current_balance - total_sponsored_cost - sponsor_additional_cost")
            print("   Result: €6.50 - €25.00 - €20.00 = €-38.50 (too negative)")
            print()
            
            print("🎯 MOST LIKELY CAUSE:")
            print("The code is using 'total_sponsored_cost' instead of 'sponsor_additional_cost'")
            print("OR there's a sign error where it subtracts instead of adds")
            
            # Calculate the exact error
            expected = 26.50
            actual = -17.50
            difference = expected - actual
            print(f"\nDifference: €{expected:.2f} - €{actual:.2f} = €{difference:.2f}")
            
            if abs(difference - 44.0) < 1.0:
                print("🎯 This suggests the calculation is: current_balance - total_sponsored_cost")
                print("   Instead of: current_balance + sponsor_additional_cost")
            
            return True
                
        except Exception as e:
            print(f"❌ Error analyzing calculation: {str(e)}")
            return False

    def run_debug(self):
        """Run complete debug analysis"""
        print("🔍 DEBUG SPONSOR CALCULATION STEP BY STEP")
        print("=" * 80)
        print("GOAL: Understand why sponsor gets -17.50€ instead of +27.50€")
        print("DEPARTMENT: 2. Wachabteilung")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_admin():
            return False
        
        # Get problem employee details
        problem_employee = self.get_problem_employee_details()
        if not problem_employee:
            return False
        
        # Get employee orders
        orders = self.get_employee_orders(problem_employee['id'])
        if not orders:
            return False
        
        # Analyze the calculation error
        self.analyze_calculation_error()
        
        print(f"\n" + "=" * 80)
        print("🔍 DEBUG SUMMARY")
        print("=" * 80)
        print("🎯 NEGATIVE BALANCE ISSUE IDENTIFIED!")
        print(f"- Employee: {problem_employee['name']}")
        print(f"- Balance: €{problem_employee['breakfast_balance']:.2f}")
        print("- Root cause: Likely wrong formula in sponsor balance calculation")
        print("- Fix needed: Check sponsor-meal endpoint balance update logic")
        
        return True

if __name__ == "__main__":
    debugger = DebugSponsorCalculation()
    success = debugger.run_debug()
    sys.exit(0 if success else 1)