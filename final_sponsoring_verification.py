#!/usr/bin/env python3
"""
FINAL SPONSORING DOUBLE-CALCULATION BUG FIX VERIFICATION

CRITICAL FINDING: The sponsoring calculations are CORRECT!
- Department 1: Breakfast portion = €1.70 (0.50 + 0.60 + 0.60)
- Department 2: Breakfast portion = €2.25 (0.75 + 1.00 + 0.50)
- Different departments have different menu pricing
- Sponsoring correctly calculates breakfast portion (rolls + eggs) only
- Coffee is correctly excluded from sponsoring

VERIFICATION TESTS:
1. Single employee sponsoring in both departments
2. Verify exact balance calculations match expected values
3. Confirm NO double calculations occur
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://brigade-meals.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class FinalSponsoringVerifier:
    def __init__(self):
        self.session = None
        self.department_pricing = {
            'fw4abteilung1': {
                'name': '1. Wachabteilung',
                'breakfast_portion': 1.70,  # 0.50 + 0.60 + 0.60
                'total_with_coffee': 3.20
            },
            'fw4abteilung2': {
                'name': '2. Wachabteilung',
                'breakfast_portion': 2.25,  # 0.75 + 1.00 + 0.50
                'total_with_coffee': 3.25
            }
        }
        
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
    
    def round_currency(self, amount):
        """Round currency to 2 decimal places"""
        return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    async def authenticate_admin(self, department_name, admin_password):
        """Authenticate as department admin"""
        auth_data = {
            "department_name": department_name,
            "admin_password": admin_password
        }
        
        response, status = await self.make_request('POST', '/login/department-admin', auth_data)
        return status == 200
    
    async def cleanup_test_data(self):
        """Clean up test data"""
        await self.make_request('POST', '/admin/cleanup-testing-data')
    
    async def create_test_employee(self, department_id, name):
        """Create a test employee"""
        employee_data = {
            "name": name,
            "department_id": department_id,
            "is_guest": False
        }
        
        response, status = await self.make_request('POST', '/employees', employee_data)
        return response if status == 200 else None
    
    async def get_employee_balance(self, employee_id):
        """Get employee balance"""
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        if status == 200:
            employee_data = response.get('employee', {})
            return employee_data.get('breakfast_balance', 0.0)
        return None
    
    async def create_standard_order(self, employee_id, department_id):
        """Create standard breakfast order"""
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
            "notes": "Final verification order"
        }
        
        response, status = await self.make_request('POST', '/orders', order_data)
        return response.get('total_price', 0.0) if status == 200 else None
    
    async def sponsor_breakfast(self, department_id, sponsor_id, sponsor_name):
        """Sponsor breakfast"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        sponsor_data = {
            "department_id": department_id,
            "date": today,
            "meal_type": "breakfast",
            "sponsor_employee_id": sponsor_id,
            "sponsor_employee_name": sponsor_name
        }
        
        response, status = await self.make_request('POST', '/department-admin/sponsor-meal', sponsor_data)
        return response if status == 200 else None
    
    async def verify_department_sponsoring(self, department_id):
        """Verify sponsoring calculations for a specific department"""
        dept_info = self.department_pricing[department_id]
        dept_name = dept_info['name']
        expected_breakfast_portion = dept_info['breakfast_portion']
        expected_total_with_coffee = dept_info['total_with_coffee']
        
        print(f"\n{'='*80}")
        print(f"🎯 VERIFYING {dept_name.upper()} ({department_id})")
        print(f"{'='*80}")
        print(f"Expected breakfast portion: €{expected_breakfast_portion}")
        print(f"Expected total with coffee: €{expected_total_with_coffee}")
        
        # Create test employees
        sponsored_employee = await self.create_test_employee(department_id, f"Sponsored_{department_id}")
        sponsor_employee = await self.create_test_employee(department_id, f"Sponsor_{department_id}")
        
        if not sponsored_employee or not sponsor_employee:
            print("❌ Failed to create test employees")
            return False
        
        # Record initial balances
        initial_sponsored = await self.get_employee_balance(sponsored_employee['id'])
        initial_sponsor = await self.get_employee_balance(sponsor_employee['id'])
        
        print(f"\n📊 Initial balances:")
        print(f"   Sponsored: €{initial_sponsored}")
        print(f"   Sponsor: €{initial_sponsor}")
        
        # Create order
        order_total = await self.create_standard_order(sponsored_employee['id'], department_id)
        if order_total is None:
            print("❌ Failed to create order")
            return False
        
        print(f"\n🍞 Order created: €{order_total}")
        
        # Record balance after order
        after_order_balance = await self.get_employee_balance(sponsored_employee['id'])
        print(f"   Sponsored balance after order: €{after_order_balance}")
        
        # Sponsor the breakfast
        sponsor_response = await self.sponsor_breakfast(department_id, sponsor_employee['id'], sponsor_employee['name'])
        if not sponsor_response:
            print("❌ Sponsoring failed")
            return False
        
        sponsored_cost = sponsor_response.get('total_cost', 0.0)
        print(f"\n💰 Sponsoring completed: €{sponsored_cost}")
        
        # Verify sponsored cost matches expected breakfast portion
        if abs(sponsored_cost - expected_breakfast_portion) > 0.01:
            print(f"❌ Sponsored cost mismatch: expected €{expected_breakfast_portion}, got €{sponsored_cost}")
            return False
        
        # Record final balances
        final_sponsored = await self.get_employee_balance(sponsored_employee['id'])
        final_sponsor = await self.get_employee_balance(sponsor_employee['id'])
        
        print(f"\n📊 Final balances:")
        print(f"   Sponsored: €{final_sponsored}")
        print(f"   Sponsor: €{final_sponsor}")
        
        # Check for double calculation
        sponsored_refund = self.round_currency(final_sponsored - after_order_balance)
        sponsor_charge = self.round_currency(initial_sponsor - final_sponsor)
        
        print(f"\n🎯 DOUBLE CALCULATION CHECK:")
        print(f"   Sponsored refund: €{sponsored_refund} (expected: €{expected_breakfast_portion})")
        print(f"   Sponsor charge: €{sponsor_charge} (expected: €{expected_breakfast_portion})")
        
        refund_correct = abs(sponsored_refund - expected_breakfast_portion) <= 0.01
        charge_correct = abs(sponsor_charge - expected_breakfast_portion) <= 0.01
        
        if refund_correct and charge_correct:
            print(f"   ✅ NO DOUBLE CALCULATION - All amounts are exactly correct!")
            return True
        else:
            print(f"   ❌ CALCULATION ERROR DETECTED")
            if not refund_correct:
                print(f"      Refund error: got €{sponsored_refund}, expected €{expected_breakfast_portion}")
            if not charge_correct:
                print(f"      Charge error: got €{sponsor_charge}, expected €{expected_breakfast_portion}")
            return False
    
    async def run_final_verification(self):
        """Run final comprehensive verification"""
        print("🚀 FINAL SPONSORING DOUBLE-CALCULATION BUG FIX VERIFICATION")
        print("=" * 70)
        print("CRITICAL FINDING: Different departments have different menu pricing!")
        print("- Department 1: Breakfast portion = €1.70")
        print("- Department 2: Breakfast portion = €2.25")
        print("- Sponsoring should calculate correct breakfast portion per department")
        print("- NO double calculations should occur")
        print("=" * 70)
        
        # Clean up and authenticate
        await self.cleanup_test_data()
        
        auth1 = await self.authenticate_admin("1. Wachabteilung", "admin1")
        auth2 = await self.authenticate_admin("2. Wachabteilung", "admin2")
        
        if not auth1 or not auth2:
            print("❌ Authentication failed")
            return False
        
        # Test both departments
        results = []
        
        for department_id in ['fw4abteilung1', 'fw4abteilung2']:
            result = await self.verify_department_sponsoring(department_id)
            dept_name = self.department_pricing[department_id]['name']
            results.append((dept_name, result))
        
        # Final summary
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL VERIFICATION RESULTS")
        print(f"{'='*80}")
        
        for dept_name, result in results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {dept_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} departments verified")
        
        if passed == total:
            print(f"\n🎉 SPONSORING DOUBLE-CALCULATION BUG FIX FULLY VERIFIED!")
            print(f"✅ All departments calculate sponsoring correctly")
            print(f"✅ Breakfast portion (rolls + eggs) sponsored correctly")
            print(f"✅ Coffee correctly excluded from sponsoring")
            print(f"✅ NO double calculations detected in any department")
            print(f"✅ Different department pricing handled correctly")
            print(f"✅ Balance updates performed exactly ONCE per transaction")
            print(f"✅ SPONSORING SYSTEM IS WORKING PERFECTLY!")
            return True
        else:
            print(f"\n🚨 SPONSORING ISSUES DETECTED!")
            print(f"❌ {total - passed} department(s) failed verification")
            return False

async def main():
    """Main verification execution"""
    async with FinalSponsoringVerifier() as verifier:
        success = await verifier.run_final_verification()
        return success

if __name__ == "__main__":
    print("FINAL SPONSORING DOUBLE-CALCULATION BUG FIX VERIFICATION")
    print("=" * 60)
    
    try:
        result = asyncio.run(main())
        exit_code = 0 if result else 1
        print(f"\nVerification completed with exit code: {exit_code}")
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Verification interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n💥 Verification failed with exception: {str(e)}")
        exit(1)