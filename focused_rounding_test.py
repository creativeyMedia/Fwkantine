#!/usr/bin/env python3
"""
Focused test for the specific failing case
"""

import asyncio
import aiohttp
import json
import os
from decimal import Decimal, ROUND_HALF_UP

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://firebrigade-food.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def focused_test():
    async with aiohttp.ClientSession() as session:
        # Authenticate as admin
        auth_data = {
            "department_name": "1. Wachabteilung",
            "admin_password": "admin1"
        }
        
        async with session.post(f"{API_BASE}/login/department-admin", json=auth_data) as response:
            if response.status != 200:
                print("❌ Authentication failed")
                return
        
        print("✅ Authenticated successfully")
        
        # Create test employee
        employee_data = {
            "name": "FocusedRoundingTest",
            "department_id": "fw4abteilung1"
        }
        
        async with session.post(f"{API_BASE}/employees", json=employee_data) as response:
            if response.status != 200:
                print("❌ Failed to create employee")
                return
            employee = await response.json()
            employee_id = employee['id']
        
        print(f"✅ Created test employee: {employee_id[:8]}")
        
        # Test the specific failing case: 0.005 payment
        print("\n🔍 Testing 0.005 payment case (exact test logic):")
        
        # Get initial balance
        async with session.get(f"{API_BASE}/employees/{employee_id}/profile") as response:
            profile = await response.json()
            initial_balance = profile['employee']['breakfast_balance']
            print(f"   Initial balance: {initial_balance}")
        
        # Make 0.005 payment
        amount = 0.005
        payment_data = {
            "payment_type": "breakfast",
            "amount": amount,
            "payment_method": "adjustment",
            "notes": "Focused test 0.005 payment"
        }
        
        async with session.post(f"{API_BASE}/department-admin/flexible-payment/{employee_id}?admin_department=fw4abteilung1", json=payment_data) as response:
            if response.status != 200:
                print(f"❌ Payment failed: {response.status}")
                return
        
        # Get final balance
        async with session.get(f"{API_BASE}/employees/{employee_id}/profile") as response:
            profile = await response.json()
            final_balance = profile['employee']['breakfast_balance']
            print(f"   Final balance: {final_balance}")
        
        # Calculate expected change using same logic as test
        decimal_amount = Decimal(str(float(amount)))
        expected_change = float(decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        # Calculate actual change
        balance_change = final_balance - initial_balance
        
        print(f"   Amount: {amount}")
        print(f"   Expected change: {expected_change}")
        print(f"   Actual change: {balance_change}")
        print(f"   Difference: {abs(balance_change - expected_change)}")
        print(f"   Test passes: {abs(balance_change - expected_change) < 0.001}")

if __name__ == "__main__":
    asyncio.run(focused_test())