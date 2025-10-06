#!/usr/bin/env python3
"""
Debug Multiple Employees Sponsoring Issue
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://feuerwehr-kantine.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class MultipleEmployeesDebugger:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to backend API"""
        url = f"{API_BASE}{endpoint}"
        try:
            if method.upper() == 'GET':
                async with self.session.get(url, params=params) as response:
                    return await response.json(), response.status
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data, params=params) as response:
                    return await response.json(), response.status
        except Exception as e:
            print(f"❌ Request failed: {method} {url} - {str(e)}")
            return None, 500
    
    async def debug_multiple_employees_sponsoring(self):
        """Debug the multiple employees sponsoring calculation"""
        print("🔍 DEBUGGING MULTIPLE EMPLOYEES SPONSORING")
        print("=" * 50)
        
        # Clean up and authenticate
        await self.make_request('POST', '/admin/cleanup-testing-data')
        
        auth_data = {
            "department_name": "2. Wachabteilung",
            "admin_password": "admin2"
        }
        await self.make_request('POST', '/login/department-admin', auth_data)
        
        department_id = "fw4abteilung2"
        
        # Create 3 employees
        employees = []
        for i in range(3):
            employee_data = {
                "name": f"DebugEmployee_{i+1}",
                "department_id": department_id,
                "is_guest": False
            }
            
            response, status = await self.make_request('POST', '/employees', employee_data)
            if status == 200:
                employees.append(response)
                print(f"✅ Created employee: {response['name']} ({response['id']})")
        
        # Create sponsor
        sponsor_data = {
            "name": "DebugSponsor",
            "department_id": department_id,
            "is_guest": False
        }
        
        sponsor_response, status = await self.make_request('POST', '/employees', sponsor_data)
        if status == 200:
            sponsor = sponsor_response
            print(f"✅ Created sponsor: {sponsor['name']} ({sponsor['id']})")
        
        # Create orders for all employees
        print(f"\n🍞 Creating orders for all employees...")
        order_details = []
        
        for emp in employees:
            order_data = {
                "employee_id": emp['id'],
                "department_id": department_id,
                "order_type": "breakfast",
                "breakfast_items": [
                    {
                        "total_halves": 2,
                        "white_halves": 1,  # €0.50
                        "seeded_halves": 1,  # €0.60
                        "toppings": ["ruehrei", "butter"],  # Free
                        "has_lunch": True,  # €5.00 (not in total)
                        "boiled_eggs": 1,   # €0.60
                        "fried_eggs": 0,
                        "has_coffee": True  # €1.50
                    }
                ],
                "notes": f"Debug order for {emp['name']}"
            }
            
            order_response, status = await self.make_request('POST', '/orders', order_data)
            if status == 200:
                order_total = order_response.get('total_price', 0.0)
                order_details.append({
                    'employee': emp,
                    'order_id': order_response.get('id'),
                    'total': order_total
                })
                print(f"   {emp['name']}: €{order_total}")
        
        # Get all orders to analyze
        print(f"\n📋 Analyzing all orders in department...")
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get breakfast history to see what the sponsoring endpoint will see
        history_response, status = await self.make_request('GET', f'/orders/breakfast-history/{department_id}')
        if status == 200:
            history_data = history_response.get('history', [])
            if history_data:
                today_data = history_data[0]  # Most recent day
                employee_orders = today_data.get('employee_orders', {})
                
                print(f"   Found {len(employee_orders)} employee orders:")
                for emp_key, emp_data in employee_orders.items():
                    total_amount = emp_data.get('total_amount', 0.0)
                    print(f"      {emp_key}: €{total_amount}")
        
        # Now sponsor the breakfast
        print(f"\n💰 Sponsoring breakfast...")
        sponsor_data = {
            "department_id": department_id,
            "date": today,
            "meal_type": "breakfast",
            "sponsor_employee_id": sponsor['id'],
            "sponsor_employee_name": sponsor['name']
        }
        
        sponsor_response, status = await self.make_request('POST', '/department-admin/sponsor-meal', sponsor_data)
        if status == 200:
            print(f"✅ Sponsoring successful:")
            print(f"   Sponsored items: {sponsor_response.get('sponsored_items', 'N/A')}")
            print(f"   Total cost: €{sponsor_response.get('total_cost', 'N/A')}")
            print(f"   Affected employees: {sponsor_response.get('affected_employees', 'N/A')}")
            print(f"   Sponsor additional cost: €{sponsor_response.get('sponsor_additional_cost', 'N/A')}")
            
            # Analyze the breakdown
            total_cost = sponsor_response.get('total_cost', 0.0)
            affected_employees = sponsor_response.get('affected_employees', 0)
            
            if affected_employees > 0:
                cost_per_employee = total_cost / affected_employees
                print(f"\n🔍 COST BREAKDOWN:")
                print(f"   Cost per employee: €{cost_per_employee:.2f}")
                print(f"   Expected per employee: €1.70 (0.50 + 0.60 + 0.60)")
                
                if abs(cost_per_employee - 1.70) > 0.01:
                    print(f"   ⚠️  Cost per employee mismatch!")
                    
                    # Check if it's including coffee or other items
                    if abs(cost_per_employee - 3.20) < 0.01:
                        print(f"   🚨 ISSUE: Cost includes full order (€3.20) instead of just breakfast portion (€1.70)")
                    elif abs(cost_per_employee - 2.25) < 0.01:
                        print(f"   🚨 ISSUE: Cost includes breakfast + coffee (€2.25) instead of just breakfast (€1.70)")
        else:
            print(f"❌ Sponsoring failed: {sponsor_response}")
        
        # Check final balances
        print(f"\n📊 Final balance analysis...")
        for detail in order_details:
            emp = detail['employee']
            profile_response, status = await self.make_request('GET', f'/employees/{emp["id"]}/profile')
            if status == 200:
                employee_data = profile_response.get('employee', {})
                final_balance = employee_data.get('breakfast_balance', 0.0)
                original_total = detail['total']
                
                print(f"   {emp['name']}:")
                print(f"      Original order: €{original_total}")
                print(f"      Final balance: €{final_balance}")
                print(f"      Refund received: €{original_total + final_balance:.2f}")
        
        # Check sponsor balance
        sponsor_profile, status = await self.make_request('GET', f'/employees/{sponsor["id"]}/profile')
        if status == 200:
            sponsor_data = sponsor_profile.get('employee', {})
            sponsor_balance = sponsor_data.get('breakfast_balance', 0.0)
            print(f"   {sponsor['name']} (Sponsor): €{sponsor_balance}")

async def main():
    """Main debug execution"""
    async with MultipleEmployeesDebugger() as debugger:
        await debugger.debug_multiple_employees_sponsoring()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n💥 Debug failed with exception: {str(e)}")
        exit(1)