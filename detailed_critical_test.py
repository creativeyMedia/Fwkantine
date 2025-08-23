#!/usr/bin/env python3
"""
Detailed Critical Bug Analysis for German Canteen Management System
"""

import requests
import json
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
if BACKEND_URL == 'https://dept-order-system.preview.emergentagent.com':
    BACKEND_URL = 'http://localhost:8001'
API_BASE = f"{BACKEND_URL}/api"

def test_price_calculation_detailed():
    """Detailed analysis of price calculation"""
    session = requests.Session()
    
    print("=== DETAILED PRICE CALCULATION ANALYSIS ===")
    
    # Initialize data
    session.post(f"{API_BASE}/init-data")
    
    # Get departments and create employee
    departments = session.get(f"{API_BASE}/departments").json()
    dept = departments[0]
    
    employee_data = {"name": "Price Test Employee", "department_id": dept['id']}
    employee = session.post(f"{API_BASE}/employees", json=employee_data).json()
    
    # Get menu prices
    breakfast_menu = session.get(f"{API_BASE}/menu/breakfast").json()
    print(f"Current breakfast menu: {breakfast_menu}")
    
    # Update white roll price to €0.75 for testing
    white_item = next((item for item in breakfast_menu if item['roll_type'] == 'weiss'), None)
    if white_item:
        update_data = {"price": 0.75}
        session.put(f"{API_BASE}/department-admin/menu/breakfast/{white_item['id']}", json=update_data)
        print(f"Updated white roll price to €0.75")
    
    # Test order with 3 halves
    test_order = {
        "employee_id": employee['id'],
        "department_id": employee['department_id'],
        "order_type": "breakfast",
        "breakfast_items": [
            {
                "total_halves": 3,
                "white_halves": 3,
                "seeded_halves": 0,
                "toppings": ["ruehrei", "kaese", "schinken"],
                "has_lunch": False
            }
        ]
    }
    
    response = session.post(f"{API_BASE}/orders", json=test_order)
    if response.status_code == 200:
        order = response.json()
        actual_price = order['total_price']
        print(f"Order created with price: €{actual_price:.2f}")
        print(f"Expected per-half calculation: 3 × (€0.75 ÷ 2) = €1.125")
        print(f"Current calculation appears to be: 3 × €0.75 = €2.25")
        
        # Check if it's using full price instead of half price
        if abs(actual_price - 2.25) < 0.01:
            print("❌ ISSUE: Using full roll price for halves instead of half price")
        elif abs(actual_price - 1.125) < 0.01:
            print("✅ CORRECT: Using proper per-half pricing")
        else:
            print(f"❓ UNKNOWN: Unexpected price calculation: €{actual_price:.2f}")
    else:
        print(f"❌ Failed to create order: {response.status_code}")

def test_single_breakfast_order_detailed():
    """Detailed analysis of single breakfast order constraint"""
    session = requests.Session()
    
    print("\n=== DETAILED SINGLE BREAKFAST ORDER ANALYSIS ===")
    
    # Initialize data
    session.post(f"{API_BASE}/init-data")
    
    # Get departments and create employee
    departments = session.get(f"{API_BASE}/departments").json()
    dept = departments[0]
    
    employee_data = {"name": "Single Order Test Employee", "department_id": dept['id']}
    employee = session.post(f"{API_BASE}/employees", json=employee_data).json()
    
    print(f"Created employee: {employee['name']}")
    
    # Create first breakfast order
    first_order = {
        "employee_id": employee['id'],
        "department_id": employee['department_id'],
        "order_type": "breakfast",
        "breakfast_items": [
            {
                "total_halves": 2,
                "white_halves": 2,
                "seeded_halves": 0,
                "toppings": ["ruehrei", "kaese"],
                "has_lunch": False
            }
        ]
    }
    
    response = session.post(f"{API_BASE}/orders", json=first_order)
    if response.status_code == 200:
        first_order_result = response.json()
        print(f"✅ First breakfast order created: {first_order_result['id']}")
        
        # Check current orders
        orders_response = session.get(f"{API_BASE}/employees/{employee['id']}/orders")
        if orders_response.status_code == 200:
            orders_data = orders_response.json()
            breakfast_orders = [o for o in orders_data.get('orders', []) if o.get('order_type') == 'breakfast']
            print(f"Breakfast orders after first order: {len(breakfast_orders)}")
            
            # Create second breakfast order
            second_order = {
                "employee_id": employee['id'],
                "department_id": employee['department_id'],
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 1,
                        "white_halves": 0,
                        "seeded_halves": 1,
                        "toppings": ["schinken"],
                        "has_lunch": True
                    }
                ]
            }
            
            response = session.post(f"{API_BASE}/orders", json=second_order)
            if response.status_code == 200:
                second_order_result = response.json()
                print(f"Second breakfast order created: {second_order_result['id']}")
                
                # Check orders again
                orders_response = session.get(f"{API_BASE}/employees/{employee['id']}/orders")
                if orders_response.status_code == 200:
                    orders_data = orders_response.json()
                    breakfast_orders = [o for o in orders_data.get('orders', []) if o.get('order_type') == 'breakfast']
                    print(f"Breakfast orders after second order: {len(breakfast_orders)}")
                    
                    if len(breakfast_orders) == 1:
                        print("✅ CORRECT: Only one breakfast order exists (updated existing)")
                        remaining_order = breakfast_orders[0]
                        print(f"Remaining order ID: {remaining_order['id']}")
                        print(f"Order details: {remaining_order.get('breakfast_items', [{}])[0]}")
                    elif len(breakfast_orders) == 2:
                        print("❌ ISSUE: Two separate breakfast orders exist (should be one updated order)")
                        for i, order in enumerate(breakfast_orders):
                            print(f"Order {i+1}: ID={order['id']}, items={order.get('breakfast_items', [{}])[0]}")
                    else:
                        print(f"❓ UNEXPECTED: {len(breakfast_orders)} breakfast orders found")
            else:
                print(f"❌ Failed to create second order: {response.status_code}")
    else:
        print(f"❌ Failed to create first order: {response.status_code}")

if __name__ == "__main__":
    test_price_calculation_detailed()
    test_single_breakfast_order_detailed()