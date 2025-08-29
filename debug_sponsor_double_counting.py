#!/usr/bin/env python3
"""
Debug Sponsor Double Counting

Das Problem: 4x Mittag gebucht, aber 5x berechnet + 5€ zu viel im Gesamtsaldo
"""

import requests
import json
from datetime import datetime, date

BASE_URL = "https://meal-tracker-49.preview.emergentagent.com/api"

def debug_sponsor_counting():
    print("🔍 Debugging Sponsor Double Counting...")
    
    # Get all departments to find recent activity
    for dept_id in ["fw4abteilung1", "fw4abteilung2", "fw4abteilung3", "fw4abteilung4"]:
        print(f"\n📊 Analyzing Department: {dept_id}")
        
        # Get employees with recent balances
        employees_resp = requests.get(f"{BASE_URL}/departments/{dept_id}/employees")
        if employees_resp.status_code != 200:
            continue
            
        employees = employees_resp.json()
        recent_employees = [emp for emp in employees if emp.get('breakfast_balance', 0) > 5]
        
        if not recent_employees:
            print("   No recent activity")
            continue
            
        print(f"   Found {len(recent_employees)} employees with recent orders")
        
        # Get daily summary for this department
        today = date.today().isoformat()
        summary_resp = requests.get(f"{BASE_URL}/orders/daily-summary/{dept_id}")
        
        if summary_resp.status_code == 200:
            summary = summary_resp.json()
            employee_orders = summary.get("employee_orders", {})
            
            print(f"   📋 Daily Summary Analysis:")
            
            # Count lunch orders and calculate totals
            lunch_count = 0
            total_employee_balance = 0
            total_summary_cost = 0
            sponsor_employees = []
            sponsored_employees = []
            
            for emp_name, emp_data in employee_orders.items():
                has_lunch = emp_data.get("has_lunch", False)
                if has_lunch:
                    lunch_count += 1
                
                # Find this employee's balance
                employee_obj = next((emp for emp in employees if emp["name"] == emp_name), None)
                if employee_obj:
                    balance = employee_obj.get("breakfast_balance", 0)
                    total_employee_balance += balance
                    
                    # Check if this is a sponsor (high balance)
                    if balance > 20:
                        sponsor_employees.append((emp_name, balance))
                    elif balance > 0:
                        sponsored_employees.append((emp_name, balance))
            
            print(f"      Lunch count in summary: {lunch_count}")
            print(f"      Total employee balances: {total_employee_balance:.2f}€")
            
            if sponsor_employees:
                print(f"      Suspected sponsors: {sponsor_employees}")
            if sponsored_employees:
                print(f"      Sponsored employees: {sponsored_employees}")
            
            # Get individual orders to cross-check
            try:
                orders_resp = requests.post(
                    f"{BASE_URL}/department-admin/orders",
                    headers={"Content-Type": "application/json"},
                    json={
                        "department_id": dept_id,
                        "admin_password": f"admin{dept_id[-1]}"
                    }
                )
                
                if orders_resp.status_code == 200:
                    orders = orders_resp.json()
                    today_orders = [order for order in orders if order.get('timestamp', '').startswith(today)]
                    
                    print(f"      📝 Individual Orders Analysis:")
                    print(f"         Total orders today: {len(today_orders)}")
                    
                    # Categorize orders
                    regular_lunch_orders = []
                    sponsor_orders = []
                    sponsored_orders = []
                    
                    total_order_prices = 0
                    
                    for order in today_orders:
                        total_price = order.get('total_price', 0)
                        total_order_prices += total_price
                        
                        is_sponsored = order.get('is_sponsored', False)
                        is_sponsor_order = order.get('is_sponsor_order', False)
                        
                        # Check if order has lunch
                        has_lunch = False
                        for item in order.get('breakfast_items', []):
                            if item.get('has_lunch', False):
                                has_lunch = True
                                break
                        
                        if is_sponsor_order:
                            sponsor_orders.append({
                                'name': order.get('employee_name', 'Unknown'),
                                'price': total_price,
                                'sponsored_cost': order.get('sponsor_total_cost', 0)
                            })
                        elif is_sponsored and has_lunch:
                            sponsored_orders.append({
                                'name': order.get('employee_name', 'Unknown'),
                                'price': total_price,
                                'original_price': total_price  # Before sponsoring
                            })
                        elif has_lunch:
                            regular_lunch_orders.append({
                                'name': order.get('employee_name', 'Unknown'),
                                'price': total_price
                            })
                    
                    print(f"         Regular lunch orders: {len(regular_lunch_orders)}")
                    print(f"         Sponsored lunch orders: {len(sponsored_orders)}")
                    print(f"         Sponsor orders: {len(sponsor_orders)}")
                    print(f"         Total order prices: {total_order_prices:.2f}€")
                    
                    # Cross-check calculations
                    if len(regular_lunch_orders + sponsored_orders + sponsor_orders) > 0:
                        print(f"\n      🔍 DISCREPANCY ANALYSIS:")
                        print(f"         Summary lunch count: {lunch_count}")
                        print(f"         Actual lunch orders: {len(regular_lunch_orders + sponsored_orders)}")
                        print(f"         Employee total balances: {total_employee_balance:.2f}€")
                        print(f"         Order total prices: {total_order_prices:.2f}€")
                        
                        balance_vs_orders_diff = total_employee_balance - total_order_prices
                        
                        if abs(balance_vs_orders_diff) > 0.01:
                            print(f"         ⚠️  MISMATCH: {balance_vs_orders_diff:.2f}€ difference!")
                            print(f"         This suggests double-counting or incorrect balance calculation")
                        else:
                            print(f"         ✅ Balance matches order totals")
                        
                        return True  # Found the department with activity
            
            except Exception as e:
                print(f"      Could not get individual orders: {str(e)}")
    
    return False

if __name__ == "__main__":
    debug_sponsor_counting()