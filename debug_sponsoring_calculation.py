#!/usr/bin/env python3
"""
Debug Sponsoring Calculation
============================

This script debugs the sponsoring calculation issue by examining the raw data
and understanding why some sponsored employees still show large amounts.
"""

import requests
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://feuerwehr-kantine.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

def log(message):
    """Log debug information"""
    print(f"🔍 {message}")

def error(message):
    """Log errors"""
    print(f"❌ ERROR: {message}")

def success(message):
    """Log success"""
    print(f"✅ SUCCESS: {message}")

def debug_sponsored_employee(employee_key, employee_data):
    """Debug a specific sponsored employee's calculation"""
    log(f"\n=== DEBUGGING SPONSORED EMPLOYEE: {employee_key} ===")
    
    # Extract employee ID from key
    if "(ID: " in employee_key:
        partial_id = employee_key.split("(ID: ")[1].split(")")[0]
        log(f"Partial Employee ID: {partial_id}")
        
        # Get full employee ID
        response = requests.get(f"{API_BASE}/departments/fw4abteilung1/employees")
        if response.status_code == 200:
            employees = response.json()
            full_employee_id = None
            
            for employee in employees:
                if employee["id"].endswith(partial_id):
                    full_employee_id = employee["id"]
                    break
                    
            if full_employee_id:
                log(f"Full Employee ID: {full_employee_id}")
                
                # Get employee profile to see raw order data
                profile_response = requests.get(f"{API_BASE}/employees/{full_employee_id}/profile")
                if profile_response.status_code == 200:
                    profile = profile_response.json()
                    order_history = profile.get("order_history", [])
                    
                    log(f"Employee has {len(order_history)} orders in history")
                    
                    # Find sponsored orders
                    for i, order in enumerate(order_history):
                        if order.get("is_sponsored"):
                            log(f"\n--- SPONSORED ORDER {i+1} ---")
                            log(f"Order ID: {order.get('id', 'N/A')}")
                            log(f"Original total_price: €{order.get('total_price', 0)}")
                            log(f"is_sponsored: {order.get('is_sponsored', False)}")
                            log(f"sponsored_meal_type: {order.get('sponsored_meal_type', 'None')}")
                            log(f"sponsored_by_name: {order.get('sponsored_by_name', 'None')}")
                            
                            # Check breakfast items
                            breakfast_items = order.get("breakfast_items", [])
                            for j, item in enumerate(breakfast_items):
                                log(f"  Breakfast Item {j+1}:")
                                log(f"    white_halves: {item.get('white_halves', 0)}")
                                log(f"    seeded_halves: {item.get('seeded_halves', 0)}")
                                log(f"    has_lunch: {item.get('has_lunch', False)}")
                                log(f"    has_coffee: {item.get('has_coffee', False)}")
                                log(f"    boiled_eggs: {item.get('boiled_eggs', 0)}")
                                log(f"    fried_eggs: {item.get('fried_eggs', 0)}")
                                
                            # Calculate what the remaining cost SHOULD be
                            if order.get("sponsored_meal_type") == "lunch":
                                log(f"\n  LUNCH SPONSORED - Should show breakfast + coffee cost only")
                                # Estimate remaining cost (this is approximate)
                                white_halves = sum(item.get('white_halves', 0) for item in breakfast_items)
                                seeded_halves = sum(item.get('seeded_halves', 0) for item in breakfast_items)
                                has_coffee = any(item.get('has_coffee', False) for item in breakfast_items)
                                boiled_eggs = sum(item.get('boiled_eggs', 0) for item in breakfast_items)
                                fried_eggs = sum(item.get('fried_eggs', 0) for item in breakfast_items)
                                
                                estimated_remaining = 0
                                estimated_remaining += white_halves * 0.50  # Approximate white roll price
                                estimated_remaining += seeded_halves * 0.60  # Approximate seeded roll price
                                estimated_remaining += boiled_eggs * 0.50  # Approximate egg price
                                estimated_remaining += fried_eggs * 0.50  # Approximate fried egg price
                                if has_coffee:
                                    estimated_remaining += 1.50  # Approximate coffee price
                                    
                                log(f"  ESTIMATED remaining cost: €{estimated_remaining:.2f}")
                                log(f"  ACTUAL display amount: €{employee_data.get('total_amount', 0)}")
                                
                                if abs(estimated_remaining - employee_data.get('total_amount', 0)) < 0.1:
                                    success(f"  ✅ CALCULATION APPEARS CORRECT")
                                else:
                                    error(f"  ❌ CALCULATION APPEARS WRONG")
                                    error(f"     Expected: ~€{estimated_remaining:.2f}")
                                    error(f"     Actual: €{employee_data.get('total_amount', 0)}")
                        else:
                            log(f"Order {i+1}: Not sponsored (total_price: €{order.get('total_price', 0)})")
                else:
                    error(f"Failed to get employee profile: {profile_response.status_code}")
            else:
                error(f"Could not find full employee ID for partial ID: {partial_id}")
        else:
            error(f"Failed to get employees list: {response.status_code}")

def main():
    """Main debug execution"""
    print("🔍 Debug Sponsoring Calculation")
    print("=" * 50)
    
    # Get breakfast history to find sponsored employees
    response = requests.get(f"{API_BASE}/orders/breakfast-history/fw4abteilung1")
    if response.status_code == 200:
        history_data = response.json()
        
        if history_data.get("history"):
            for day_data in history_data["history"]:
                employee_orders = day_data.get("employee_orders", {})
                
                log(f"\nFound {len(employee_orders)} employees in history for date: {day_data.get('date', 'Unknown')}")
                
                # Focus on sponsored employees with issues
                for employee_key, employee_data in employee_orders.items():
                    is_sponsored = employee_data.get("is_sponsored", False)
                    sponsored_meal_type = employee_data.get("sponsored_meal_type", None)
                    total_amount = employee_data.get("total_amount", 0)
                    
                    if is_sponsored:
                        log(f"\nSponsored Employee: {employee_key}")
                        log(f"  Sponsored meal type: {sponsored_meal_type}")
                        log(f"  Display amount: €{total_amount}")
                        
                        # Debug employees with suspicious amounts
                        if sponsored_meal_type == "lunch" and total_amount > 3.0:
                            error(f"  ❌ SUSPICIOUS: Lunch-sponsored employee shows high amount: €{total_amount}")
                            debug_sponsored_employee(employee_key, employee_data)
                        elif sponsored_meal_type == "breakfast" and total_amount > 7.0:
                            error(f"  ❌ SUSPICIOUS: Breakfast-sponsored employee shows high amount: €{total_amount}")
                            debug_sponsored_employee(employee_key, employee_data)
                        else:
                            success(f"  ✅ REASONABLE: Amount seems correct for {sponsored_meal_type} sponsoring")
                
                break  # Only check the most recent day
    else:
        error(f"Failed to get breakfast history: {response.status_code}")

if __name__ == "__main__":
    main()