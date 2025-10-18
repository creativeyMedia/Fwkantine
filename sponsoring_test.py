#!/usr/bin/env python3
"""
CRITICAL SPONSORING DOUBLE-CALCULATION BUG FIX TEST

CRITICAL BUG FIXED:
The user reported that sponsoring calculations were doubled:
1. Sponsored employees: Instead of getting -3€ (making 0€ balance), they got +6€ (double positive calculation)
2. Sponsors: Instead of paying 25€, they were charged 50€ (double negative calculation)

ROOT CAUSE IDENTIFIED AND FIXED:
- Both sponsor and sponsored employee balances were updated TWICE:
  1. Direct database update
  2. Additional update_employee_balance() call
- This caused double crediting/debiting

WHAT WAS FIXED:
- Removed duplicate balance updates in sponsor_employee_for_order endpoint
- Now uses ONLY update_employee_balance() function for consistency
- Should eliminate all double calculations

CRITICAL TEST SCENARIO:
1. Create employees with known starting balances
2. Create breakfast orders for multiple employees 
3. Have one employee sponsor others' breakfast
4. Verify EXACT balance calculations:
   - Sponsored employees: Should get credited exact sponsored amount (no double)
   - Sponsor: Should pay exact total cost (no double charging)
5. Test both scenarios:
   - Sponsor WITH own order (pays additional for others)
   - Sponsor WITHOUT own order (pays for all)

EXPECTED RESULTS:
✅ Sponsored employee with 3€ breakfast debt should have 0€ balance after sponsoring (not +6€)
✅ Sponsor paying 25€ total should be charged exactly 25€ (not 50€)
✅ All balance calculations should be single, not double
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

class SponsoringDoubleCalculationTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.departments = [
            {"id": "fw4abteilung1", "name": "1. Wachabteilung", "admin_password": "admin1", "password": "password1"},
            {"id": "fw4abteilung2", "name": "2. Wachabteilung", "admin_password": "admin2", "password": "password2"}
        ]
        
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
            elif method.upper() == 'PUT':
                async with self.session.put(url, json=data, params=params) as response:
                    return await response.json(), response.status
            elif method.upper() == 'DELETE':
                async with self.session.delete(url, params=params) as response:
                    return await response.json(), response.status
        except Exception as e:
            print(f"❌ Request failed: {method} {url} - {str(e)}")
            return None, 500
    
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
    
    async def create_test_employee(self, department_id, name, is_guest=False):
        """Create a test employee for sponsoring testing"""
        employee_data = {
            "name": name,
            "department_id": department_id,
            "is_guest": is_guest
        }
        
        response, status = await self.make_request('POST', '/employees', employee_data)
        if status == 200:
            print(f"✅ Created test employee: {name} in {department_id}")
            return response
        else:
            print(f"❌ Failed to create employee {name}: {response}")
            return None
    
    async def get_employee_balance(self, employee_id):
        """Get employee balance details"""
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        if status == 200:
            employee_data = response.get('employee', {})
            return {
                'breakfast_balance': employee_data.get('breakfast_balance', 0.0),
                'drinks_sweets_balance': employee_data.get('drinks_sweets_balance', 0.0),
                'subaccount_balances': employee_data.get('subaccount_balances', {})
            }
        else:
            print(f"❌ Failed to get employee balance: {response}")
            return None
    
    async def create_breakfast_order(self, employee_id, department_id, total_cost_expected=None, notes="Sponsoring test order"):
        """Create a breakfast order with known cost"""
        print(f"🧪 Creating breakfast order for employee {employee_id} in {department_id}")
        
        # Create a standard breakfast order with known costs
        order_data = {
            "employee_id": employee_id,
            "department_id": department_id,
            "order_type": "breakfast",
            "breakfast_items": [
                {
                    "total_halves": 2,
                    "white_halves": 1,  # €0.50
                    "seeded_halves": 1,  # €0.60
                    "toppings": ["ruehrei", "butter"],  # Free toppings
                    "has_lunch": True,  # €5.00 (typical lunch price)
                    "boiled_eggs": 1,   # €0.50
                    "fried_eggs": 0,
                    "has_coffee": True  # €1.50 (typical coffee price)
                }
            ],
            "notes": notes
        }
        
        response, status = await self.make_request('POST', '/orders', order_data)
        
        if status == 200:
            actual_cost = response.get('total_price', 0.0)
            print(f"✅ Breakfast order created successfully")
            print(f"   Order ID: {response.get('id', 'N/A')}")
            print(f"   Total Price: €{actual_cost}")
            if total_cost_expected:
                print(f"   Expected: €{total_cost_expected}")
                if abs(actual_cost - total_cost_expected) > 0.01:
                    print(f"⚠️  Price mismatch! Expected €{total_cost_expected}, got €{actual_cost}")
            return response, True
        else:
            print(f"❌ Breakfast order FAILED with status {status}")
            print(f"   Error: {response}")
            return response, False
    
    async def sponsor_meal(self, department_id, sponsor_employee_id, sponsor_employee_name, meal_type="breakfast"):
        """Sponsor meals for all employees in department"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        sponsor_data = {
            "department_id": department_id,
            "date": today,
            "meal_type": meal_type,
            "sponsor_employee_id": sponsor_employee_id,
            "sponsor_employee_name": sponsor_employee_name
        }
        
        response, status = await self.make_request('POST', '/department-admin/sponsor-meal', sponsor_data)
        
        if status == 200:
            print(f"✅ Sponsoring successful")
            print(f"   Sponsored items: {response.get('sponsored_items', 'N/A')}")
            print(f"   Total cost: €{response.get('total_cost', 'N/A')}")
            print(f"   Affected employees: {response.get('affected_employees', 'N/A')}")
            print(f"   Sponsor additional cost: €{response.get('sponsor_additional_cost', 'N/A')}")
            return response, True
        else:
            print(f"❌ Sponsoring FAILED with status {status}")
            print(f"   Error: {response}")
            return response, False
    
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
    
    async def test_scenario_1_sponsor_with_own_order(self):
        """
        CRITICAL TEST SCENARIO 1: Sponsor WITH own order
        - Create 3 employees with breakfast orders
        - Employee 1 sponsors breakfast for all (including themselves)
        - Verify exact balance calculations (no double charging)
        """
        print(f"\n{'='*80}")
        print(f"🎯 CRITICAL TEST SCENARIO 1: SPONSOR WITH OWN ORDER")
        print(f"{'='*80}")
        
        department_id = "fw4abteilung1"
        
        # Step 1: Create test employees
        employees = []
        for i in range(1, 4):
            employee = await self.create_test_employee(department_id, f"SponsorTest_{i}")
            if not employee:
                return False
            employees.append(employee)
        
        # Step 2: Record initial balances
        print(f"\n📊 Recording initial balances...")
        initial_balances = {}
        for emp in employees:
            balance = await self.get_employee_balance(emp['id'])
            initial_balances[emp['id']] = balance
            print(f"   {emp['name']}: €{balance['breakfast_balance']}")
        
        # Step 3: Create breakfast orders for all employees
        print(f"\n🍞 Creating breakfast orders for all employees...")
        order_costs = []
        for emp in employees:
            order, success = await self.create_breakfast_order(emp['id'], department_id, 8.10)  # Expected: 0.50+0.60+5.00+0.50+1.50 = 8.10
            if not success:
                print(f"❌ Failed to create order for {emp['name']}")
                return False
            order_costs.append(order.get('total_price', 0.0))
        
        # Step 4: Record balances after orders (should be negative)
        print(f"\n📊 Recording balances after orders...")
        after_order_balances = {}
        for emp in employees:
            balance = await self.get_employee_balance(emp['id'])
            after_order_balances[emp['id']] = balance
            print(f"   {emp['name']}: €{balance['breakfast_balance']} (debt from order)")
        
        # Step 5: Employee 1 sponsors breakfast for all
        print(f"\n💰 Employee 1 sponsors breakfast for all employees...")
        sponsor_employee = employees[0]
        sponsor_response, sponsor_success = await self.sponsor_meal(
            department_id, 
            sponsor_employee['id'], 
            sponsor_employee['name'], 
            "breakfast"
        )
        
        if not sponsor_success:
            print(f"❌ Sponsoring failed")
            return False
        
        # Step 6: Record final balances and verify calculations
        print(f"\n📊 Recording final balances and verifying calculations...")
        final_balances = {}
        calculation_errors = []
        
        for i, emp in enumerate(employees):
            balance = await self.get_employee_balance(emp['id'])
            final_balances[emp['id']] = balance
            
            initial_bal = initial_balances[emp['id']]['breakfast_balance']
            after_order_bal = after_order_balances[emp['id']]['breakfast_balance']
            final_bal = balance['breakfast_balance']
            order_cost = order_costs[i]
            
            print(f"\n   {emp['name']} Balance Analysis:")
            print(f"      Initial: €{initial_bal}")
            print(f"      After Order: €{after_order_bal} (should be €{initial_bal - order_cost})")
            print(f"      Final: €{final_bal}")
            
            # Calculate expected values
            expected_after_order = round(initial_bal - order_cost, 2)
            
            if i == 0:  # Sponsor
                # Sponsor should pay for others' breakfast portions only (not their own)
                # Breakfast portion = rolls + eggs = 0.50 + 0.60 + 0.50 = 1.60 per person
                breakfast_portion_per_person = 1.60
                others_count = len(employees) - 1  # Exclude sponsor
                sponsor_additional_cost = breakfast_portion_per_person * others_count
                expected_final = round(after_order_bal - sponsor_additional_cost, 2)
                
                print(f"      Expected Final: €{expected_final} (after paying €{sponsor_additional_cost} for {others_count} others)")
                
                if abs(final_bal - expected_final) > 0.01:
                    error_msg = f"SPONSOR DOUBLE-CHARGING DETECTED! {emp['name']} expected €{expected_final}, got €{final_bal}"
                    calculation_errors.append(error_msg)
                    print(f"      🚨 {error_msg}")
                else:
                    print(f"      ✅ Sponsor balance correct (no double charging)")
            else:  # Sponsored employee
                # Sponsored employee should get breakfast portion refunded
                breakfast_portion = 1.60  # rolls + eggs
                expected_final = round(after_order_bal + breakfast_portion, 2)
                
                print(f"      Expected Final: €{expected_final} (after €{breakfast_portion} breakfast refund)")
                
                if abs(final_bal - expected_final) > 0.01:
                    error_msg = f"SPONSORED EMPLOYEE DOUBLE-CREDIT DETECTED! {emp['name']} expected €{expected_final}, got €{final_bal}"
                    calculation_errors.append(error_msg)
                    print(f"      🚨 {error_msg}")
                else:
                    print(f"      ✅ Sponsored employee balance correct (no double credit)")
        
        # Final verification
        if calculation_errors:
            print(f"\n🚨 CRITICAL ERRORS DETECTED:")
            for error in calculation_errors:
                print(f"   - {error}")
            return False
        else:
            print(f"\n✅ SCENARIO 1 PASSED: No double calculation errors detected!")
            return True
    
    async def test_scenario_2_sponsor_without_own_order(self):
        """
        CRITICAL TEST SCENARIO 2: Sponsor WITHOUT own order
        - Create 2 employees with breakfast orders
        - Create 1 sponsor employee without order
        - Sponsor sponsors breakfast for the 2 employees
        - Verify exact balance calculations (no double charging)
        """
        print(f"\n{'='*80}")
        print(f"🎯 CRITICAL TEST SCENARIO 2: SPONSOR WITHOUT OWN ORDER")
        print(f"{'='*80}")
        
        department_id = "fw4abteilung2"
        
        # Step 1: Create employees with orders
        employees_with_orders = []
        for i in range(1, 3):
            employee = await self.create_test_employee(department_id, f"OrderEmployee_{i}")
            if not employee:
                return False
            employees_with_orders.append(employee)
        
        # Step 2: Create sponsor employee (no order)
        sponsor_employee = await self.create_test_employee(department_id, "SponsorOnly")
        if not sponsor_employee:
            return False
        
        # Step 3: Record initial balances
        print(f"\n📊 Recording initial balances...")
        initial_balances = {}
        all_employees = employees_with_orders + [sponsor_employee]
        
        for emp in all_employees:
            balance = await self.get_employee_balance(emp['id'])
            initial_balances[emp['id']] = balance
            print(f"   {emp['name']}: €{balance['breakfast_balance']}")
        
        # Step 4: Create breakfast orders for employees (not sponsor)
        print(f"\n🍞 Creating breakfast orders for employees (not sponsor)...")
        order_costs = []
        for emp in employees_with_orders:
            order, success = await self.create_breakfast_order(emp['id'], department_id, 8.10)
            if not success:
                print(f"❌ Failed to create order for {emp['name']}")
                return False
            order_costs.append(order.get('total_price', 0.0))
        
        # Step 5: Record balances after orders
        print(f"\n📊 Recording balances after orders...")
        after_order_balances = {}
        for emp in all_employees:
            balance = await self.get_employee_balance(emp['id'])
            after_order_balances[emp['id']] = balance
            print(f"   {emp['name']}: €{balance['breakfast_balance']}")
        
        # Step 6: Sponsor sponsors breakfast for all employees with orders
        print(f"\n💰 Sponsor sponsors breakfast for employees with orders...")
        sponsor_response, sponsor_success = await self.sponsor_meal(
            department_id, 
            sponsor_employee['id'], 
            sponsor_employee['name'], 
            "breakfast"
        )
        
        if not sponsor_success:
            print(f"❌ Sponsoring failed")
            return False
        
        # Step 7: Record final balances and verify calculations
        print(f"\n📊 Recording final balances and verifying calculations...")
        final_balances = {}
        calculation_errors = []
        
        # Check employees with orders (should get breakfast refund)
        for i, emp in enumerate(employees_with_orders):
            balance = await self.get_employee_balance(emp['id'])
            final_balances[emp['id']] = balance
            
            initial_bal = initial_balances[emp['id']]['breakfast_balance']
            after_order_bal = after_order_balances[emp['id']]['breakfast_balance']
            final_bal = balance['breakfast_balance']
            
            print(f"\n   {emp['name']} (Sponsored Employee) Balance Analysis:")
            print(f"      Initial: €{initial_bal}")
            print(f"      After Order: €{after_order_bal}")
            print(f"      Final: €{final_bal}")
            
            # Sponsored employee should get breakfast portion refunded
            breakfast_portion = 1.60  # rolls + eggs
            expected_final = round(after_order_bal + breakfast_portion, 2)
            
            print(f"      Expected Final: €{expected_final} (after €{breakfast_portion} breakfast refund)")
            
            if abs(final_bal - expected_final) > 0.01:
                error_msg = f"SPONSORED EMPLOYEE DOUBLE-CREDIT DETECTED! {emp['name']} expected €{expected_final}, got €{final_bal}"
                calculation_errors.append(error_msg)
                print(f"      🚨 {error_msg}")
            else:
                print(f"      ✅ Sponsored employee balance correct (no double credit)")
        
        # Check sponsor (should pay for all breakfast portions)
        sponsor_balance = await self.get_employee_balance(sponsor_employee['id'])
        final_balances[sponsor_employee['id']] = sponsor_balance
        
        sponsor_initial_bal = initial_balances[sponsor_employee['id']]['breakfast_balance']
        sponsor_after_order_bal = after_order_balances[sponsor_employee['id']]['breakfast_balance']
        sponsor_final_bal = sponsor_balance['breakfast_balance']
        
        print(f"\n   {sponsor_employee['name']} (Sponsor) Balance Analysis:")
        print(f"      Initial: €{sponsor_initial_bal}")
        print(f"      After Order: €{sponsor_after_order_bal} (no order created)")
        print(f"      Final: €{sponsor_final_bal}")
        
        # Sponsor should pay for all breakfast portions
        breakfast_portion_per_person = 1.60
        total_sponsored_employees = len(employees_with_orders)
        total_sponsor_cost = breakfast_portion_per_person * total_sponsored_employees
        expected_sponsor_final = round(sponsor_after_order_bal - total_sponsor_cost, 2)
        
        print(f"      Expected Final: €{expected_sponsor_final} (after paying €{total_sponsor_cost} for {total_sponsored_employees} employees)")
        
        if abs(sponsor_final_bal - expected_sponsor_final) > 0.01:
            error_msg = f"SPONSOR DOUBLE-CHARGING DETECTED! {sponsor_employee['name']} expected €{expected_sponsor_final}, got €{sponsor_final_bal}"
            calculation_errors.append(error_msg)
            print(f"      🚨 {error_msg}")
        else:
            print(f"      ✅ Sponsor balance correct (no double charging)")
        
        # Final verification
        if calculation_errors:
            print(f"\n🚨 CRITICAL ERRORS DETECTED:")
            for error in calculation_errors:
                print(f"   - {error}")
            return False
        else:
            print(f"\n✅ SCENARIO 2 PASSED: No double calculation errors detected!")
            return True
    
    async def test_scenario_3_exact_user_reported_case(self):
        """
        CRITICAL TEST SCENARIO 3: Exact user-reported case
        - Sponsored employee with 3€ breakfast debt should have 0€ balance after sponsoring (not +6€)
        - Sponsor paying 25€ total should be charged exactly 25€ (not 50€)
        """
        print(f"\n{'='*80}")
        print(f"🎯 CRITICAL TEST SCENARIO 3: EXACT USER-REPORTED CASE")
        print(f"{'='*80}")
        print(f"Testing the exact scenario reported by user:")
        print(f"- Sponsored employee: -3€ → 0€ (NOT +6€ double credit)")
        print(f"- Sponsor: pays 25€ (NOT 50€ double charge)")
        
        department_id = "fw4abteilung1"
        
        # Step 1: Create employees
        sponsored_employee = await self.create_test_employee(department_id, "SponsoredEmployee_3Euro")
        sponsor_employee = await self.create_test_employee(department_id, "Sponsor_25Euro")
        
        if not sponsored_employee or not sponsor_employee:
            return False
        
        # Step 2: Create a breakfast order that costs exactly 3€ for breakfast portion
        print(f"\n🍞 Creating breakfast order with 3€ breakfast portion...")
        
        # Create order with specific items to get 3€ breakfast cost
        order_data = {
            "employee_id": sponsored_employee['id'],
            "department_id": department_id,
            "order_type": "breakfast",
            "breakfast_items": [
                {
                    "total_halves": 4,
                    "white_halves": 2,  # €1.00 (2 * 0.50)
                    "seeded_halves": 2,  # €1.20 (2 * 0.60)
                    "toppings": ["ruehrei", "butter", "kaese", "salami"],  # Free toppings
                    "has_lunch": True,  # €5.00
                    "boiled_eggs": 2,   # €1.00 (2 * 0.50) - Total breakfast: 1.00 + 1.20 + 1.00 = 3.20
                    "fried_eggs": 0,
                    "has_coffee": True  # €1.50
                }
            ],
            "notes": "Exact user case test - 3€ breakfast portion"
        }
        
        response, status = await self.make_request('POST', '/orders', order_data)
        if status != 200:
            print(f"❌ Failed to create specific order: {response}")
            return False
        
        order_total = response.get('total_price', 0.0)
        print(f"✅ Order created with total: €{order_total}")
        
        # Step 3: Record balances after order
        sponsored_balance = await self.get_employee_balance(sponsored_employee['id'])
        sponsor_balance = await self.get_employee_balance(sponsor_employee['id'])
        
        print(f"\n📊 Balances after order:")
        print(f"   Sponsored Employee: €{sponsored_balance['breakfast_balance']}")
        print(f"   Sponsor: €{sponsor_balance['breakfast_balance']}")
        
        # Step 4: Sponsor sponsors breakfast
        print(f"\n💰 Sponsor sponsors breakfast...")
        sponsor_response, sponsor_success = await self.sponsor_meal(
            department_id, 
            sponsor_employee['id'], 
            sponsor_employee['name'], 
            "breakfast"
        )
        
        if not sponsor_success:
            print(f"❌ Sponsoring failed: {sponsor_response}")
            return False
        
        sponsored_cost = sponsor_response.get('total_cost', 0.0)
        print(f"✅ Sponsoring successful, total cost: €{sponsored_cost}")
        
        # Step 5: Record final balances and verify exact calculations
        print(f"\n📊 Final balance verification...")
        final_sponsored_balance = await self.get_employee_balance(sponsored_employee['id'])
        final_sponsor_balance = await self.get_employee_balance(sponsor_employee['id'])
        
        sponsored_final = final_sponsored_balance['breakfast_balance']
        sponsor_final = final_sponsor_balance['breakfast_balance']
        
        print(f"   Sponsored Employee Final: €{sponsored_final}")
        print(f"   Sponsor Final: €{sponsor_final}")
        
        # Calculate expected values
        breakfast_portion = 3.20  # From our order calculation above
        expected_sponsored_final = round(sponsored_balance['breakfast_balance'] + breakfast_portion, 2)
        expected_sponsor_final = round(sponsor_balance['breakfast_balance'] - breakfast_portion, 2)
        
        print(f"\n🎯 CRITICAL VERIFICATION:")
        print(f"   Expected Sponsored Employee: €{expected_sponsored_final}")
        print(f"   Expected Sponsor: €{expected_sponsor_final}")
        
        # Check for double calculation errors
        errors = []
        
        # Check sponsored employee (should NOT have double credit)
        if abs(sponsored_final - expected_sponsored_final) > 0.01:
            if sponsored_final > expected_sponsored_final + 3.0:  # More than 3€ extra = double credit
                errors.append(f"DOUBLE CREDIT DETECTED! Sponsored employee got €{sponsored_final}, expected €{expected_sponsored_final}")
            else:
                errors.append(f"Sponsored employee balance incorrect: got €{sponsored_final}, expected €{expected_sponsored_final}")
        
        # Check sponsor (should NOT have double charge)
        if abs(sponsor_final - expected_sponsor_final) > 0.01:
            if sponsor_final < expected_sponsor_final - 20.0:  # More than 20€ extra charge = double charge
                errors.append(f"DOUBLE CHARGE DETECTED! Sponsor charged €{abs(sponsor_final)}, expected €{abs(expected_sponsor_final)}")
            else:
                errors.append(f"Sponsor balance incorrect: got €{sponsor_final}, expected €{expected_sponsor_final}")
        
        if errors:
            print(f"\n🚨 CRITICAL ERRORS IN EXACT USER CASE:")
            for error in errors:
                print(f"   - {error}")
            return False
        else:
            print(f"\n✅ EXACT USER CASE PASSED:")
            print(f"   ✅ Sponsored employee: Correct balance (no double credit)")
            print(f"   ✅ Sponsor: Correct balance (no double charge)")
            print(f"   ✅ Double calculation bug is FIXED!")
            return True
    
    async def run_comprehensive_sponsoring_test(self):
        """Run comprehensive test of sponsoring double-calculation bug fix"""
        print("🚀 STARTING CRITICAL SPONSORING DOUBLE-CALCULATION BUG FIX TEST")
        print("=" * 80)
        print("TESTING: Sponsoring calculations were doubled")
        print("- Sponsored employees: Instead of -3€ → 0€, they got +6€ (double positive)")
        print("- Sponsors: Instead of paying 25€, they were charged 50€ (double negative)")
        print("- ROOT CAUSE: Both sponsor and sponsored balances updated TWICE")
        print("- FIX: Use ONLY update_employee_balance() function (no direct DB updates)")
        print("=" * 80)
        
        # Clean up test data first
        await self.cleanup_test_data()
        
        # Authenticate as admin for both departments
        auth1 = await self.authenticate_admin("1. Wachabteilung", "admin1")
        auth2 = await self.authenticate_admin("2. Wachabteilung", "admin2")
        
        if not auth1 or not auth2:
            print("❌ Failed to authenticate as admin")
            return False
        
        # Run all test scenarios
        test_results = []
        
        # Scenario 1: Sponsor with own order
        print(f"\n🧪 Running Scenario 1...")
        result1 = await self.test_scenario_1_sponsor_with_own_order()
        test_results.append(("Sponsor WITH own order", result1))
        
        # Scenario 2: Sponsor without own order
        print(f"\n🧪 Running Scenario 2...")
        result2 = await self.test_scenario_2_sponsor_without_own_order()
        test_results.append(("Sponsor WITHOUT own order", result2))
        
        # Scenario 3: Exact user-reported case
        print(f"\n🧪 Running Scenario 3...")
        result3 = await self.test_scenario_3_exact_user_reported_case()
        test_results.append(("Exact user-reported case", result3))
        
        # Final analysis
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL SPONSORING DOUBLE-CALCULATION TEST RESULTS")
        print(f"{'='*80}")
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            print(f"   {test_name}: {status}")
        
        print(f"\nOverall Results: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL SPONSORING TESTS PASSED!")
            print(f"✅ Sponsoring double-calculation bug is FIXED!")
            print(f"✅ Sponsored employees get correct refunds (no double credit)")
            print(f"✅ Sponsors pay correct amounts (no double charging)")
            print(f"✅ Balance calculations are mathematically correct")
            print(f"✅ update_employee_balance() function working correctly")
            return True
        else:
            print(f"\n🚨 CRITICAL SPONSORING ISSUES DETECTED!")
            print(f"❌ {total_tests - passed_tests} test(s) failed")
            print(f"❌ Double calculation bug may still exist")
            print(f"❌ Immediate fix required for production use")
            return False

async def main():
    """Main test execution"""
    async with SponsoringDoubleCalculationTester() as tester:
        success = await tester.run_comprehensive_sponsoring_test()
        return success

if __name__ == "__main__":
    print("CRITICAL SPONSORING DOUBLE-CALCULATION BUG FIX TEST")
    print("=" * 60)
    
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