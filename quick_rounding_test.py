#!/usr/bin/env python3
"""
Quick test of the round_to_cents function
"""

import asyncio
import aiohttp
import json
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://brigade-meals.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

async def test_rounding():
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
            "name": "QuickRoundingTest",
            "department_id": "fw4abteilung1"
        }
        
        async with session.post(f"{API_BASE}/employees", json=employee_data) as response:
            if response.status != 200:
                print("❌ Failed to create employee")
                return
            employee = await response.json()
            employee_id = employee['id']
        
        print(f"✅ Created test employee: {employee_id[:8]}")
        
        # Test specific rounding cases
        test_cases = [
            (0.005, 0.01, "0.005 should round to 0.01"),
            (0.995, 1.00, "0.995 should round to 1.00"),
            (-0.005, -0.01, "-0.005 should round to -0.01"),
            (-0.995, -1.00, "-0.995 should round to -1.00"),
            (8.999999, 9.00, "8.999999 should round to 9.00"),
            (123.456789, 123.46, "123.456789 should round to 123.46")
        ]
        
        for amount, expected, description in test_cases:
            # Reset balance to 0
            reset_data = {
                "payment_type": "breakfast",
                "amount": 0,
                "payment_method": "adjustment",
                "notes": "Reset"
            }
            
            async with session.get(f"{API_BASE}/employees/{employee_id}/profile") as response:
                if response.status == 200:
                    profile = await response.json()
                    current_balance = profile['employee']['breakfast_balance']
                    if current_balance != 0:
                        reset_data['amount'] = -current_balance
                        async with session.post(f"{API_BASE}/department-admin/flexible-payment/{employee_id}?admin_department=fw4abteilung1", json=reset_data) as reset_response:
                            pass
            
            # Make payment with test amount
            payment_data = {
                "payment_type": "breakfast",
                "amount": amount,
                "payment_method": "adjustment",
                "notes": f"Test: {description}"
            }
            
            async with session.post(f"{API_BASE}/department-admin/flexible-payment/{employee_id}?admin_department=fw4abteilung1", json=payment_data) as response:
                if response.status != 200:
                    print(f"❌ Payment failed for {amount}")
                    continue
            
            # Get resulting balance
            async with session.get(f"{API_BASE}/employees/{employee_id}/profile") as response:
                if response.status == 200:
                    profile = await response.json()
                    actual = profile['employee']['breakfast_balance']
                    success = abs(actual - expected) < 0.001
                    
                    print(f"   {description}")
                    print(f"      Input: {amount}, Expected: {expected}, Actual: {actual}")
                    print(f"      Result: {'✅ PASS' if success else '❌ FAIL'}")
                else:
                    print(f"❌ Failed to get balance for {amount}")

if __name__ == "__main__":
    asyncio.run(test_rounding())