#!/usr/bin/env python3
"""
Debug Sponsoring Calculations - Investigate actual menu prices and calculations
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://firebrigade-food.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SponsoringDebugger:
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
    
    async def get_menu_prices(self, department_id):
        """Get all menu prices for a department"""
        print(f"\n🔍 Investigating menu prices for {department_id}...")
        
        # Get breakfast menu
        breakfast_response, status = await self.make_request('GET', f'/menu/breakfast/{department_id}')
        if status == 200:
            print(f"✅ Breakfast Menu:")
            for item in breakfast_response:
                print(f"   {item.get('roll_type', 'Unknown')}: €{item.get('price', 0.0)}")
        else:
            print(f"❌ Failed to get breakfast menu: {breakfast_response}")
        
        # Get department settings (eggs and coffee prices)
        dept_settings_response, status = await self.make_request('GET', f'/department-settings/{department_id}')
        if status == 200:
            print(f"✅ Department Settings:")
            print(f"   Boiled Eggs: €{dept_settings_response.get('boiled_eggs_price', 0.0)}")
            print(f"   Fried Eggs: €{dept_settings_response.get('fried_eggs_price', 0.0)}")
            print(f"   Coffee: €{dept_settings_response.get('coffee_price', 0.0)}")
        else:
            print(f"❌ Failed to get department settings: {dept_settings_response}")
        
        # Get lunch settings
        lunch_response, status = await self.make_request('GET', '/lunch-settings')
        if status == 200:
            print(f"✅ Lunch Settings:")
            print(f"   Lunch Price: €{lunch_response.get('price', 0.0)}")
        else:
            print(f"❌ Failed to get lunch settings: {lunch_response}")
        
        return breakfast_response, dept_settings_response, lunch_response
    
    async def create_test_order_and_analyze(self, department_id):
        """Create a test order and analyze the actual costs"""
        print(f"\n🧪 Creating test order and analyzing costs...")
        
        # First clean up
        await self.make_request('POST', '/admin/cleanup-testing-data')
        
        # Create test employee
        employee_data = {
            "name": "DebugEmployee",
            "department_id": department_id,
            "is_guest": False
        }
        
        employee_response, status = await self.make_request('POST', '/employees', employee_data)
        if status != 200:
            print(f"❌ Failed to create employee: {employee_response}")
            return
        
        employee_id = employee_response['id']
        print(f"✅ Created test employee: {employee_id}")
        
        # Create breakfast order
        order_data = {
            "employee_id": employee_id,
            "department_id": department_id,
            "order_type": "breakfast",
            "breakfast_items": [
                {
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["ruehrei", "butter"],
                    "has_lunch": True,
                    "boiled_eggs": 1,
                    "fried_eggs": 0,
                    "has_coffee": True
                }
            ],
            "notes": "Debug order analysis"
        }
        
        order_response, status = await self.make_request('POST', '/orders', order_data)
        if status != 200:
            print(f"❌ Failed to create order: {order_response}")
            return
        
        order_total = order_response.get('total_price', 0.0)
        order_id = order_response.get('id', 'N/A')
        
        print(f"✅ Order created:")
        print(f"   Order ID: {order_id}")
        print(f"   Total Price: €{order_total}")
        
        # Get employee profile to see balance
        profile_response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        if status == 200:
            employee_data = profile_response.get('employee', {})
            balance = employee_data.get('breakfast_balance', 0.0)
            print(f"   Employee Balance: €{balance}")
        
        # Now test sponsoring
        print(f"\n💰 Testing sponsoring...")
        
        # Create sponsor employee
        sponsor_data = {
            "name": "DebugSponsor",
            "department_id": department_id,
            "is_guest": False
        }
        
        sponsor_response, status = await self.make_request('POST', '/employees', sponsor_data)
        if status != 200:
            print(f"❌ Failed to create sponsor: {sponsor_response}")
            return
        
        sponsor_id = sponsor_response['id']
        print(f"✅ Created sponsor: {sponsor_id}")
        
        # Get initial sponsor balance
        sponsor_profile, status = await self.make_request('GET', f'/employees/{sponsor_id}/profile')
        if status == 200:
            sponsor_data = sponsor_profile.get('employee', {})
            initial_sponsor_balance = sponsor_data.get('breakfast_balance', 0.0)
            print(f"   Initial Sponsor Balance: €{initial_sponsor_balance}")
        
        # Sponsor the meal
        today = datetime.now().strftime('%Y-%m-%d')
        sponsor_meal_data = {
            "department_id": department_id,
            "date": today,
            "meal_type": "breakfast",
            "sponsor_employee_id": sponsor_id,
            "sponsor_employee_name": "DebugSponsor"
        }
        
        sponsor_result, status = await self.make_request('POST', '/department-admin/sponsor-meal', sponsor_meal_data)
        if status != 200:
            print(f"❌ Sponsoring failed: {sponsor_result}")
            return
        
        print(f"✅ Sponsoring successful:")
        print(f"   Sponsored items: {sponsor_result.get('sponsored_items', 'N/A')}")
        print(f"   Total cost: €{sponsor_result.get('total_cost', 'N/A')}")
        print(f"   Affected employees: {sponsor_result.get('affected_employees', 'N/A')}")
        print(f"   Sponsor additional cost: €{sponsor_result.get('sponsor_additional_cost', 'N/A')}")
        
        # Check final balances
        print(f"\n📊 Final balance analysis...")
        
        # Sponsored employee final balance
        final_profile, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        if status == 200:
            employee_data = final_profile.get('employee', {})
            final_balance = employee_data.get('breakfast_balance', 0.0)
            print(f"   Sponsored Employee Final Balance: €{final_balance}")
            print(f"   Change: €{balance} → €{final_balance} (difference: €{final_balance - balance})")
        
        # Sponsor final balance
        final_sponsor_profile, status = await self.make_request('GET', f'/employees/{sponsor_id}/profile')
        if status == 200:
            sponsor_data = final_sponsor_profile.get('employee', {})
            final_sponsor_balance = sponsor_data.get('breakfast_balance', 0.0)
            print(f"   Sponsor Final Balance: €{final_sponsor_balance}")
            print(f"   Change: €{initial_sponsor_balance} → €{final_sponsor_balance} (difference: €{final_sponsor_balance - initial_sponsor_balance})")
        
        return order_total, sponsor_result
    
    async def run_debug_analysis(self):
        """Run comprehensive debug analysis"""
        print("🔍 SPONSORING CALCULATION DEBUG ANALYSIS")
        print("=" * 60)
        
        department_id = "fw4abteilung1"
        
        # Authenticate as admin
        auth_data = {
            "department_name": "1. Wachabteilung",
            "admin_password": "admin1"
        }
        
        auth_response, status = await self.make_request('POST', '/login/department-admin', auth_data)
        if status != 200:
            print(f"❌ Authentication failed: {auth_response}")
            return
        
        print(f"✅ Authenticated as admin")
        
        # Get menu prices
        breakfast_menu, dept_settings, lunch_settings = await self.get_menu_prices(department_id)
        
        # Create test order and analyze
        await self.create_test_order_and_analyze(department_id)

async def main():
    """Main debug execution"""
    async with SponsoringDebugger() as debugger:
        await debugger.run_debug_analysis()

if __name__ == "__main__":
    print("Sponsoring Calculation Debug Analysis")
    print("=" * 40)
    
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n💥 Debug failed with exception: {str(e)}")
        exit(1)