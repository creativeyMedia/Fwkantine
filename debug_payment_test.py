#!/usr/bin/env python3
"""
Debug the payment test issue
"""

import asyncio
import aiohttp
import json
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://brigade-meals.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def debug_payment():
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
            "name": "DebugPaymentTest",
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
        print("\n🔍 Testing 0.005 payment case:")
        
        # Get initial balance
        async with session.get(f"{API_BASE}/employees/{employee_id}/profile") as response:
            profile = await response.json()
            initial_balance = profile['employee']['breakfast_balance']
            print(f"   Initial balance: {initial_balance}")
        
        # Make 0.005 payment
        payment_data = {
            "payment_type": "breakfast",
            "amount": 0.005,
            "payment_method": "adjustment",
            "notes": "Debug 0.005 payment"
        }
        
        async with session.post(f"{API_BASE}/department-admin/flexible-payment/{employee_id}?admin_department=fw4abteilung1", json=payment_data) as response:
            if response.status == 200:
                payment_result = await response.json()
                print(f"   Payment result: {payment_result}")
            else:
                print(f"❌ Payment failed: {response.status}")
                return
        
        # Get final balance
        async with session.get(f"{API_BASE}/employees/{employee_id}/profile") as response:
            profile = await response.json()
            final_balance = profile['employee']['breakfast_balance']
            print(f"   Final balance: {final_balance}")
        
        # Calculate actual change
        actual_change = final_balance - initial_balance
        expected_change = 0.01  # 0.005 should round to 0.01
        
        print(f"   Expected change: {expected_change}")
        print(f"   Actual change: {actual_change}")
        print(f"   Difference: {abs(actual_change - expected_change)}")
        
        # Test multiple small payments vs single large payment
        print("\n🔍 Testing mathematical consistency:")
        
        # Reset balance to 0
        if final_balance != 0:
            reset_data = {
                "payment_type": "breakfast",
                "amount": -final_balance,
                "payment_method": "adjustment",
                "notes": "Reset"
            }
            async with session.post(f"{API_BASE}/department-admin/flexible-payment/{employee_id}?admin_department=fw4abteilung1", json=reset_data) as response:
                pass
        
        # Make multiple small payments
        small_amounts = [1.111, 2.222, 3.333]
        print(f"   Making small payments: {small_amounts}")
        
        for amount in small_amounts:
            payment_data = {
                "payment_type": "breakfast",
                "amount": amount,
                "payment_method": "adjustment",
                "notes": f"Small payment {amount}"
            }
            async with session.post(f"{API_BASE}/department-admin/flexible-payment/{employee_id}?admin_department=fw4abteilung1", json=payment_data) as response:
                pass
        
        # Get balance after small payments
        async with session.get(f"{API_BASE}/employees/{employee_id}/profile") as response:
            profile = await response.json()
            small_total = profile['employee']['breakfast_balance']
            print(f"   Balance after small payments: {small_total}")
        
        # Reset and make one large payment
        reset_data = {
            "payment_type": "breakfast",
            "amount": -small_total,
            "payment_method": "adjustment",
            "notes": "Reset"
        }
        async with session.post(f"{API_BASE}/department-admin/flexible-payment/{employee_id}?admin_department=fw4abteilung1", json=reset_data) as response:
            pass
        
        large_amount = sum(small_amounts)
        print(f"   Making large payment: {large_amount}")
        
        payment_data = {
            "payment_type": "breakfast",
            "amount": large_amount,
            "payment_method": "adjustment",
            "notes": f"Large payment {large_amount}"
        }
        async with session.post(f"{API_BASE}/department-admin/flexible-payment/{employee_id}?admin_department=fw4abteilung1", json=payment_data) as response:
            pass
        
        # Get balance after large payment
        async with session.get(f"{API_BASE}/employees/{employee_id}/profile") as response:
            profile = await response.json()
            large_total = profile['employee']['breakfast_balance']
            print(f"   Balance after large payment: {large_total}")
        
        print(f"   Difference: {abs(small_total - large_total)}")
        print(f"   Expected sum: {sum(small_amounts)}")

if __name__ == "__main__":
    asyncio.run(debug_payment())