#!/usr/bin/env python3
"""
Debug Saldo Discrepancy (33.10€ vs 28.10€)

Untersucht die Diskrepanz zwischen angezeigtem Order-Preis und tatsächlichem Saldo
"""

import requests
import json
from datetime import datetime, date

BASE_URL = "https://canteen-manager-1.preview.emergentagent.com/api"
DEPARTMENT_ID = "fw4abteilung3"  # 3. Wachabteilung wie vom User angegeben

def debug_saldo_discrepancy():
    print("🔍 Debugging Saldo Discrepancy in Department 3...")
    
    # Get all employees with non-zero balances
    print("\n1. Current Employee Balances:")
    employees_resp = requests.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
    if employees_resp.status_code == 200:
        employees = employees_resp.json()
        target_employees = []
        
        for emp in employees:
            balance = emp.get('breakfast_balance', 0)
            if balance != 0:
                print(f"   • {emp['name']}: {balance:.2f}€")
                target_employees.append(emp)
        
        # Focus on employees with significant balances (around 28-33€)
        suspicious_employees = [emp for emp in target_employees if 25 <= emp.get('breakfast_balance', 0) <= 35]
        
        if suspicious_employees:
            print(f"\n2. Analyzing suspicious employees (25-35€ range):")
            for emp in suspicious_employees[:3]:  # Analyze max 3
                print(f"\n   🎯 Analyzing {emp['name']} (Balance: {emp['breakfast_balance']:.2f}€)")
                
                # Get their orders
                orders_resp = requests.get(f"{BASE_URL}/employees/{emp['id']}/orders")
                if orders_resp.status_code == 200:
                    orders_data = orders_resp.json()
                    orders = orders_data.get("orders", [])
                    
                    today = date.today().isoformat()
                    today_orders = [order for order in orders if order.get('timestamp', '').startswith(today)]
                    
                    print(f"      Today's orders: {len(today_orders)}")
                    
                    total_calculated_cost = 0
                    for i, order in enumerate(today_orders):
                        print(f"      Order {i+1}:")
                        print(f"         Total Price: {order.get('total_price', 0):.2f}€")
                        print(f"         Is Sponsor Order: {order.get('is_sponsor_order', False)}")
                        print(f"         Is Sponsored: {order.get('is_sponsored', False)}")
                        
                        # Check for sponsor details
                        if order.get('is_sponsor_order'):
                            print(f"         Sponsor Details: {order.get('sponsor_details', 'N/A')}")
                            print(f"         Sponsor Cost Breakdown: {order.get('sponsor_cost_breakdown', 'N/A')}")
                            print(f"         Sponsor Total Cost: {order.get('sponsor_total_cost', 'N/A')}")
                        
                        # Analyze readable_items
                        readable_items = order.get('readable_items', [])
                        items_total = 0
                        for item in readable_items:
                            desc = item.get('description', '')
                            price_str = item.get('total_price', '0')
                            try:
                                # Extract price from string like "5.50 €"
                                if '€' in price_str:
                                    price = float(price_str.replace('€', '').replace(',', '.').strip())
                                else:
                                    price = float(price_str) if price_str else 0
                                items_total += price
                                print(f"            - {desc}: {price:.2f}€")
                            except:
                                print(f"            - {desc}: {price_str} (could not parse)")
                        
                        print(f"         Items Total: {items_total:.2f}€")
                        print(f"         Discrepancy: {order.get('total_price', 0) - items_total:.2f}€")
                        
                        total_calculated_cost += order.get('total_price', 0)
                    
                    print(f"      SUMMARY:")
                    print(f"         Employee Balance: {emp['breakfast_balance']:.2f}€")
                    print(f"         Total Order Prices: {total_calculated_cost:.2f}€")
                    print(f"         Discrepancy: {total_calculated_cost - emp['breakfast_balance']:.2f}€")
        else:
            print("   No employees found with balances in suspicious range")
    
    else:
        print(f"   Failed to get employees: {employees_resp.status_code}")

if __name__ == "__main__":
    debug_saldo_discrepancy()