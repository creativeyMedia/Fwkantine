#!/usr/bin/env python3
"""
Debug Persistent 5€ Problem

Screenshot zeigt: 5x5€ Mittag + 0,50€ Ei = 25,50€ sollte sein
Tatsächlich: 30,50€ (5€ zu viel)
"""

import requests
import json
from datetime import datetime, date

BASE_URL = "https://fire-dept-cafe.preview.emergentagent.com/api"

def debug_persistent_problem():
    print("🔍 Debugging Persistent 5€ Problem...")
    
    # Look for departments with recent activity matching screenshot (30.50€)
    for dept_id in ["fw4abteilung1", "fw4abteilung2", "fw4abteilung3", "fw4abteilung4"]:
        print(f"\n📊 Department: {dept_id}")
        
        # Get daily summary 
        summary_resp = requests.get(f"{BASE_URL}/orders/daily-summary/{dept_id}")
        if summary_resp.status_code == 200:
            summary = summary_resp.json()
            employee_orders = summary.get("employee_orders", {})
            
            # Count lunch orders and calculate what we expect vs what we see
            lunch_count = sum(1 for emp_data in employee_orders.values() if emp_data.get("has_lunch", False))
            egg_count = sum(emp_data.get("boiled_eggs", 0) for emp_data in employee_orders.values())
            
            print(f"   Summary lunch count: {lunch_count}")
            print(f"   Summary egg count: {egg_count}")
            
            # Get employee balances to see total
            employees_resp = requests.get(f"{BASE_URL}/departments/{dept_id}/employees")
            if employees_resp.status_code == 200:
                employees = employees_resp.json()
                
                total_balance = 0
                employees_with_balance = []
                
                for emp in employees:
                    balance = emp.get('breakfast_balance', 0)
                    if balance > 0:
                        total_balance += balance
                        employees_with_balance.append((emp['name'], balance))
                
                print(f"   Total balance: {total_balance:.2f}€")
                
                # Check if this matches screenshot (30.50€)
                if abs(total_balance - 30.50) < 0.01:
                    print(f"   🎯 FOUND THE DEPARTMENT! This matches screenshot (30.50€)")
                    print(f"   Expected: {lunch_count * 5 + egg_count * 0.5:.2f}€")
                    print(f"   Actual: {total_balance:.2f}€")
                    print(f"   Discrepancy: {total_balance - (lunch_count * 5 + egg_count * 0.5):.2f}€")
                    
                    print(f"\n   👥 Individual Balances:")
                    for name, balance in employees_with_balance:
                        print(f"   - {name}: {balance:.2f}€")
                    
                    # Get breakfast history to see the daily summary calculation
                    try:
                        history_resp = requests.post(
                            f"{BASE_URL}/department-admin/breakfast-history",
                            headers={"Content-Type": "application/json"},
                            json={
                                "department_id": dept_id,
                                "admin_password": f"admin{dept_id[-1]}"
                            }
                        )
                        
                        if history_resp.status_code == 200:
                            history = history_resp.json()
                            today = date.today().isoformat()
                            
                            for day in history:
                                if day.get('date') == today:
                                    print(f"\n   📅 Today's Daily Summary:")
                                    print(f"   - Total Orders: {day.get('total_orders', 0)}")
                                    print(f"   - Total Amount: {day.get('total_amount', 0):.2f}€")
                                    print(f"   - Employee Orders: {len(day.get('employee_orders', {}))}")
                                    
                                    # This total_amount might be wrong!
                                    expected_from_balances = total_balance
                                    actual_in_summary = day.get('total_amount', 0)
                                    
                                    print(f"\n   🔍 DISCREPANCY ANALYSIS:")
                                    print(f"   - Employee balances sum: {expected_from_balances:.2f}€")
                                    print(f"   - Daily summary amount: {actual_in_summary:.2f}€")
                                    print(f"   - Difference: {abs(expected_from_balances - actual_in_summary):.2f}€")
                                    
                                    if abs(expected_from_balances - actual_in_summary) > 0.01:
                                        print(f"   ⚠️  MISMATCH between balances and daily summary!")
                                    
                                    break
                    
                    except Exception as e:
                        print(f"   Could not get breakfast history: {str(e)}")
                    
                    return dept_id  # Found it
    
    return None

def analyze_orders_in_detail(dept_id):
    """Analyze individual orders to find the source of 5€ extra"""
    print(f"\n🔍 Analyzing individual orders in {dept_id}...")
    
    try:
        # We need to get individual orders somehow
        # Let's try the employee orders endpoint for each employee
        employees_resp = requests.get(f"{BASE_URL}/departments/{dept_id}/employees")
        if employees_resp.status_code != 200:
            print("Could not get employees")
            return
        
        employees = employees_resp.json()
        today = date.today().isoformat()
        
        total_calculated_from_orders = 0
        
        for emp in employees:
            if emp.get('breakfast_balance', 0) > 0:
                print(f"\n   👤 {emp['name']} (Balance: {emp['breakfast_balance']:.2f}€)")
                
                # Get their orders
                orders_resp = requests.get(f"{BASE_URL}/employees/{emp['id']}/orders")
                if orders_resp.status_code == 200:
                    orders_data = orders_resp.json()
                    orders = orders_data.get("orders", [])
                    
                    today_orders = [order for order in orders if order.get('timestamp', '').startswith(today)]
                    
                    order_total = 0
                    for order in today_orders:
                        order_price = order.get('total_price', 0)
                        order_total += order_price
                        
                        print(f"   📝 Order: {order_price:.2f}€")
                        print(f"      - Is Sponsored: {order.get('is_sponsored', False)}")
                        print(f"      - Is Sponsor Order: {order.get('is_sponsor_order', False)}")
                        
                        # Look at readable items
                        for item in order.get('readable_items', []):
                            desc = item.get('description', '')
                            price = item.get('total_price', '')
                            print(f"         - {desc}: {price}")
                    
                    total_calculated_from_orders += order_total
                    
                    balance_vs_orders = emp['breakfast_balance'] - order_total
                    if abs(balance_vs_orders) > 0.01:
                        print(f"   ⚠️  Balance vs Orders mismatch: {balance_vs_orders:.2f}€")
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total from individual orders: {total_calculated_from_orders:.2f}€")
        print(f"   This should match employee balances and daily summary")
        
    except Exception as e:
        print(f"Error analyzing orders: {str(e)}")

if __name__ == "__main__":
    problem_dept = debug_persistent_problem()
    if problem_dept:
        analyze_orders_in_detail(problem_dept)