#!/usr/bin/env python3
"""
CORRECTED SPONSORING DOUBLE-CALCULATION BUG FIX TEST

Based on debug analysis, the actual calculations are:
- Order total: €3.20 (rolls + eggs + coffee, lunch not included in total)
- Breakfast portion: €1.70 (rolls + eggs only)
- Coffee portion: €1.50 (not sponsored)

CRITICAL TEST: Verify that sponsoring calculations are done ONCE, not TWICE
- Sponsored employee should get exactly €1.70 refund (breakfast portion)
- Sponsor should pay exactly €1.70 (breakfast portion cost)
- NO double calculations should occur
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://feuerwehr-kantine.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class CorrectedSponsoringTester:
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
    
    def round_currency(self, amount):
        """Round currency to 2 decimal places to avoid floating point issues"""
        return float(Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
    
    async def authenticate_admin(self, department_name, admin_password):
        """Authenticate as department admin"""
        auth_data = {
            "department_name": department_name,
            "admin_password": admin_password
        }
        
        response, status = await self.make_request('POST', '/login/department-admin', auth_data)
        if status == 200:
            print(f"✅ Admin authentication successful for {department_name}")
            return response
        else:
            print(f"❌ Admin authentication failed for {department_name}: {response}")
            return None
    
    async def cleanup_test_data(self):
        """Clean up test data before starting"""
        print("🧹 Cleaning up test data...")
        response, status = await self.make_request('POST', '/admin/cleanup-testing-data')
        if status == 200:
            print("✅ Test data cleaned up successfully")
            return True
        else:
            print(f"⚠️  Cleanup failed: {response}")
            return False
    
    async def create_test_employee(self, department_id, name):
        """Create a test employee"""
        employee_data = {
            "name": name,
            "department_id": department_id,
            "is_guest": False
        }
        
        response, status = await self.make_request('POST', '/employees', employee_data)
        if status == 200:
            print(f"✅ Created test employee: {name}")
            return response
        else:
            print(f"❌ Failed to create employee {name}: {response}")
            return None
    
    async def get_employee_balance(self, employee_id):
        """Get employee balance"""
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        if status == 200:
            employee_data = response.get('employee', {})
            return employee_data.get('breakfast_balance', 0.0)
        else:
            print(f"❌ Failed to get employee balance: {response}")
            return None
    
    async def create_standard_breakfast_order(self, employee_id, department_id):
        """Create a standard breakfast order with known costs"""
        order_data = {
            "employee_id": employee_id,
            "department_id": department_id,
            "order_type": "breakfast",
            "breakfast_items": [
                {
                    "total_halves": 2,
                    "white_halves": 1,  # €0.50
                    "seeded_halves": 1,  # €0.60
                    "toppings": ["ruehrei", "butter"],  # Free
                    "has_lunch": True,  # €5.00 (not included in total)
                    "boiled_eggs": 1,   # €0.60
                    "fried_eggs": 0,
                    "has_coffee": True  # €1.50
                }
            ],
            "notes": "Standard test order"
        }
        
        response, status = await self.make_request('POST', '/orders', order_data)
        if status == 200:
            return response.get('total_price', 0.0), True
        else:
            print(f"❌ Order creation failed: {response}")
            return 0.0, False
    
    async def sponsor_breakfast(self, department_id, sponsor_id, sponsor_name):
        """Sponsor breakfast for all employees"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        sponsor_data = {
            "department_id": department_id,
            "date": today,
            "meal_type": "breakfast",
            "sponsor_employee_id": sponsor_id,
            "sponsor_employee_name": sponsor_name
        }
        
        response, status = await self.make_request('POST', '/department-admin/sponsor-meal', sponsor_data)
        if status == 200:
            return response, True
        else:
            print(f"❌ Sponsoring failed: {response}")
            return response, False
    
    async def test_single_calculation_verification(self):
        """
        CRITICAL TEST: Verify sponsoring calculations are done exactly ONCE
        
        Expected behavior:
        - Order total: €3.20 (0.50 + 0.60 + 0.60 + 1.50)
        - Breakfast portion: €1.70 (0.50 + 0.60 + 0.60)
        - Sponsored employee: -3.20 + 1.70 = -1.50 (coffee remaining)
        - Sponsor: 0.00 - 1.70 = -1.70 (pays breakfast portion)
        """
        print(f"\n{'='*80}")
        print(f"🎯 CRITICAL TEST: SINGLE CALCULATION VERIFICATION")
        print(f"{'='*80}")
        print(f"Testing that sponsoring calculations are done EXACTLY ONCE (no double calculation)")
        
        department_id = "fw4abteilung1"
        
        # Step 1: Create employees
        sponsored_employee = await self.create_test_employee(department_id, "SponsoredEmployee")
        sponsor_employee = await self.create_test_employee(department_id, "SponsorEmployee")
        
        if not sponsored_employee or not sponsor_employee:
            return False
        
        sponsored_id = sponsored_employee['id']
        sponsor_id = sponsor_employee['id']
        
        # Step 2: Record initial balances
        initial_sponsored_balance = await self.get_employee_balance(sponsored_id)
        initial_sponsor_balance = await self.get_employee_balance(sponsor_id)
        
        print(f"\n📊 Initial Balances:")
        print(f"   Sponsored Employee: €{initial_sponsored_balance}")
        print(f"   Sponsor: €{initial_sponsor_balance}")
        
        # Step 3: Create order for sponsored employee
        order_total, order_success = await self.create_standard_breakfast_order(sponsored_id, department_id)
        if not order_success:
            return False
        
        print(f"\n🍞 Order Created:")
        print(f"   Total: €{order_total}")
        
        # Step 4: Record balance after order
        after_order_balance = await self.get_employee_balance(sponsored_id)
        print(f"   Sponsored Employee Balance After Order: €{after_order_balance}")
        
        # Verify order balance calculation
        expected_after_order = self.round_currency(initial_sponsored_balance - order_total)
        actual_after_order = self.round_currency(after_order_balance)
        
        if abs(actual_after_order - expected_after_order) > 0.01:
            print(f"❌ Order balance calculation error: expected €{expected_after_order}, got €{actual_after_order}")
            return False
        
        print(f"✅ Order balance calculation correct")
        
        # Step 5: Sponsor the breakfast
        sponsor_response, sponsor_success = await self.sponsor_breakfast(department_id, sponsor_id, "SponsorEmployee")
        if not sponsor_success:
            return False
        
        sponsored_cost = sponsor_response.get('total_cost', 0.0)
        print(f"\n💰 Sponsoring Completed:")
        print(f"   Total Sponsored Cost: €{sponsored_cost}")
        
        # Step 6: Record final balances
        final_sponsored_balance = await self.get_employee_balance(sponsored_id)
        final_sponsor_balance = await self.get_employee_balance(sponsor_id)
        
        print(f"\n📊 Final Balances:")
        print(f"   Sponsored Employee: €{final_sponsored_balance}")
        print(f"   Sponsor: €{final_sponsor_balance}")
        
        # Step 7: Verify calculations are EXACTLY correct (no double calculation)
        print(f"\n🔍 CRITICAL VERIFICATION:")
        
        # Expected breakfast portion (what should be sponsored)
        expected_breakfast_portion = 1.70  # 0.50 + 0.60 + 0.60
        
        # Sponsored employee should get breakfast portion refunded
        expected_sponsored_final = self.round_currency(after_order_balance + expected_breakfast_portion)
        actual_sponsored_final = self.round_currency(final_sponsored_balance)
        
        print(f"   Sponsored Employee:")
        print(f"      After Order: €{after_order_balance}")
        print(f"      Expected Refund: €{expected_breakfast_portion}")
        print(f"      Expected Final: €{expected_sponsored_final}")
        print(f"      Actual Final: €{actual_sponsored_final}")
        
        # Sponsor should pay breakfast portion
        expected_sponsor_final = self.round_currency(initial_sponsor_balance - expected_breakfast_portion)
        actual_sponsor_final = self.round_currency(final_sponsor_balance)
        
        print(f"   Sponsor:")
        print(f"      Initial: €{initial_sponsor_balance}")
        print(f"      Expected Charge: €{expected_breakfast_portion}")
        print(f"      Expected Final: €{expected_sponsor_final}")
        print(f"      Actual Final: €{actual_sponsor_final}")
        
        # Check for double calculation errors
        errors = []
        
        # Check sponsored employee (no double credit)
        if abs(actual_sponsored_final - expected_sponsored_final) > 0.01:
            difference = actual_sponsored_final - expected_sponsored_final
            if abs(difference - expected_breakfast_portion) < 0.01:
                errors.append(f"DOUBLE CREDIT DETECTED! Sponsored employee got extra €{expected_breakfast_portion} credit")
            else:
                errors.append(f"Sponsored employee balance incorrect: expected €{expected_sponsored_final}, got €{actual_sponsored_final}")
        
        # Check sponsor (no double charge)
        if abs(actual_sponsor_final - expected_sponsor_final) > 0.01:
            difference = expected_sponsor_final - actual_sponsor_final
            if abs(difference - expected_breakfast_portion) < 0.01:
                errors.append(f"DOUBLE CHARGE DETECTED! Sponsor charged extra €{expected_breakfast_portion}")
            else:
                errors.append(f"Sponsor balance incorrect: expected €{expected_sponsor_final}, got €{actual_sponsor_final}")
        
        # Verify total cost matches breakfast portion
        if abs(sponsored_cost - expected_breakfast_portion) > 0.01:
            errors.append(f"Sponsored cost incorrect: expected €{expected_breakfast_portion}, got €{sponsored_cost}")
        
        if errors:
            print(f"\n🚨 CRITICAL ERRORS DETECTED:")
            for error in errors:
                print(f"   - {error}")
            return False
        else:
            print(f"\n✅ SINGLE CALCULATION VERIFIED:")
            print(f"   ✅ Sponsored employee got exactly €{expected_breakfast_portion} refund")
            print(f"   ✅ Sponsor paid exactly €{expected_breakfast_portion}")
            print(f"   ✅ No double calculations detected")
            print(f"   ✅ Sponsoring double-calculation bug is FIXED!")
            return True
    
    async def test_multiple_employees_scenario(self):
        """
        Test sponsoring with multiple employees to verify no double calculations
        """
        print(f"\n{'='*80}")
        print(f"🎯 MULTIPLE EMPLOYEES SPONSORING TEST")
        print(f"{'='*80}")
        
        department_id = "fw4abteilung2"
        
        # Create multiple employees with orders
        employees = []
        for i in range(3):
            employee = await self.create_test_employee(department_id, f"Employee_{i+1}")
            if not employee:
                return False
            employees.append(employee)
        
        # Create sponsor
        sponsor = await self.create_test_employee(department_id, "MultiSponsor")
        if not sponsor:
            return False
        
        # Record initial balances
        initial_balances = {}
        for emp in employees + [sponsor]:
            balance = await self.get_employee_balance(emp['id'])
            initial_balances[emp['id']] = balance
            print(f"   {emp['name']}: €{balance}")
        
        # Create orders for all employees (not sponsor)
        order_totals = []
        for emp in employees:
            order_total, success = await self.create_standard_breakfast_order(emp['id'], department_id)
            if not success:
                return False
            order_totals.append(order_total)
        
        print(f"\n🍞 Orders created for {len(employees)} employees")
        
        # Record balances after orders
        after_order_balances = {}
        for emp in employees + [sponsor]:
            balance = await self.get_employee_balance(emp['id'])
            after_order_balances[emp['id']] = balance
        
        # Sponsor sponsors breakfast for all
        sponsor_response, success = await self.sponsor_breakfast(department_id, sponsor['id'], sponsor['name'])
        if not success:
            return False
        
        total_sponsored_cost = sponsor_response.get('total_cost', 0.0)
        print(f"\n💰 Sponsoring completed: €{total_sponsored_cost} total")
        
        # Verify calculations
        expected_breakfast_portion = 1.70
        expected_total_cost = expected_breakfast_portion * len(employees)
        
        print(f"\n🔍 VERIFICATION:")
        print(f"   Expected cost per employee: €{expected_breakfast_portion}")
        print(f"   Expected total cost: €{expected_total_cost}")
        print(f"   Actual total cost: €{total_sponsored_cost}")
        
        if abs(total_sponsored_cost - expected_total_cost) > 0.01:
            print(f"❌ Total cost calculation error")
            return False
        
        # Check final balances
        errors = []
        for emp in employees:
            final_balance = await self.get_employee_balance(emp['id'])
            after_order = after_order_balances[emp['id']]
            expected_final = self.round_currency(after_order + expected_breakfast_portion)
            actual_final = self.round_currency(final_balance)
            
            if abs(actual_final - expected_final) > 0.01:
                errors.append(f"{emp['name']}: expected €{expected_final}, got €{actual_final}")
        
        # Check sponsor
        sponsor_final = await self.get_employee_balance(sponsor['id'])
        sponsor_initial = initial_balances[sponsor['id']]
        expected_sponsor_final = self.round_currency(sponsor_initial - expected_total_cost)
        actual_sponsor_final = self.round_currency(sponsor_final)
        
        if abs(actual_sponsor_final - expected_sponsor_final) > 0.01:
            errors.append(f"Sponsor: expected €{expected_sponsor_final}, got €{actual_sponsor_final}")
        
        if errors:
            print(f"\n🚨 ERRORS IN MULTIPLE EMPLOYEE TEST:")
            for error in errors:
                print(f"   - {error}")
            return False
        else:
            print(f"\n✅ MULTIPLE EMPLOYEE TEST PASSED:")
            print(f"   ✅ All {len(employees)} employees got correct refunds")
            print(f"   ✅ Sponsor paid correct total amount")
            print(f"   ✅ No double calculations in multi-employee scenario")
            return True
    
    async def run_corrected_sponsoring_test(self):
        """Run the corrected sponsoring test with proper expectations"""
        print("🚀 CORRECTED SPONSORING DOUBLE-CALCULATION BUG FIX TEST")
        print("=" * 70)
        print("Testing with CORRECT expectations based on actual system behavior:")
        print("- Order total: €3.20 (rolls + eggs + coffee)")
        print("- Breakfast portion: €1.70 (rolls + eggs only)")
        print("- Sponsoring should affect ONLY breakfast portion")
        print("- NO double calculations should occur")
        print("=" * 70)
        
        # Clean up and authenticate
        await self.cleanup_test_data()
        
        auth = await self.authenticate_admin("1. Wachabteilung", "admin1")
        if not auth:
            return False
        
        auth2 = await self.authenticate_admin("2. Wachabteilung", "admin2")
        if not auth2:
            return False
        
        # Run tests
        test_results = []
        
        # Test 1: Single calculation verification
        result1 = await self.test_single_calculation_verification()
        test_results.append(("Single Calculation Verification", result1))
        
        # Test 2: Multiple employees scenario
        result2 = await self.test_multiple_employees_scenario()
        test_results.append(("Multiple Employees Scenario", result2))
        
        # Final results
        passed = sum(1 for _, result in test_results if result)
        total = len(test_results)
        
        print(f"\n{'='*80}")
        print(f"🎯 CORRECTED SPONSORING TEST RESULTS")
        print(f"{'='*80}")
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        print(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            print(f"\n🎉 ALL CORRECTED SPONSORING TESTS PASSED!")
            print(f"✅ Sponsoring double-calculation bug is CONFIRMED FIXED!")
            print(f"✅ All calculations are performed exactly ONCE")
            print(f"✅ No double crediting or double charging detected")
            print(f"✅ System is working as expected")
            return True
        else:
            print(f"\n🚨 SPONSORING ISSUES STILL EXIST!")
            print(f"❌ {total - passed} test(s) failed")
            print(f"❌ Double calculation bug may still be present")
            return False

async def main():
    """Main test execution"""
    async with CorrectedSponsoringTester() as tester:
        success = await tester.run_corrected_sponsoring_test()
        return success

if __name__ == "__main__":
    print("CORRECTED SPONSORING DOUBLE-CALCULATION BUG FIX TEST")
    print("=" * 55)
    
    try:
        result = asyncio.run(main())
        exit_code = 0 if result else 1
        print(f"\nTest completed with exit code: {exit_code}")
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        exit(1)