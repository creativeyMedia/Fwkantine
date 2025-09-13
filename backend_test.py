#!/usr/bin/env python3
"""
Backend Test Suite for Critical Guest Employee Ordering Bug

CRITICAL LIVE PROBLEM:
User reports: "400 Bad Request beim Bestellen als Gastmitarbeiter - betrifft nur manche Mitarbeiter, bei anderen geht es"

ERROR DETAILS:
- POST /api/orders 400 (Bad Request) 
- "Fehler beim Prüfen bestehender Bestellungen"
- "Fehler beim Speichern der Bestellung"
- Only affects certain employees, not all

SUSPECTED DATA INCONSISTENCIES:
The problem points to different data structures between old/new employees:
1. Missing subaccount_balances: Old employees may not have Sub-Account structure
2. Null/undefined fields: Critical fields could be missing
3. Temporary Assignment Problems: Guest employee assignment fails
4. Validation errors: Backend validation fails for certain employee data

Test Focus:
- Test create_order endpoint with different employee data structures
- Test employees with/without subaccount_balances
- Test temporary employee assignments (guest workers)
- Identify exact cause of 400 Bad Request errors
- Test initialize_subaccount_balances functionality
- Test backend validation logic
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class GuestEmployeeOrderTester:
    def __init__(self):
        self.session = None
        self.test_employees = {}
        self.test_results = []
        self.departments = [
            {"id": "fw4abteilung1", "name": "1. Wachabteilung", "admin_password": "admin1", "password": "password1"},
            {"id": "fw4abteilung2", "name": "2. Wachabteilung", "admin_password": "admin2", "password": "password2"},
            {"id": "fw4abteilung3", "name": "3. Wachabteilung", "admin_password": "admin3", "password": "password3"},
            {"id": "fw4abteilung4", "name": "4. Wachabteilung", "admin_password": "admin4", "password": "password4"}
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
    
    async def authenticate_department(self, department_name, password):
        """Authenticate as department user"""
        auth_data = {
            "department_name": department_name,
            "password": password
        }
        
        response, status = await self.make_request('POST', '/login/department', auth_data)
        if status == 200:
            print(f"✅ Department authentication successful for {department_name}")
            return response
        else:
            print(f"❌ Department authentication failed for {department_name}: {response}")
            return None
    
    async def create_test_employee(self, department_id, name, is_guest=False):
        """Create a test employee for ordering testing"""
        employee_data = {
            "name": name,
            "department_id": department_id,
            "is_guest": is_guest
        }
        
        response, status = await self.make_request('POST', '/employees', employee_data)
        if status == 200:
            print(f"✅ Created test employee: {name} in {department_id} (guest: {is_guest})")
            return response
        else:
            print(f"❌ Failed to create employee {name}: {response}")
            return None
    
    async def get_employee_profile(self, employee_id):
        """Get employee profile to check data structure"""
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        if status == 200:
            return response
        else:
            print(f"❌ Failed to get employee profile: {response}")
            return None
    
    async def create_temporary_assignment(self, department_id, employee_id):
        """Add employee as temporary worker to another department"""
        assignment_data = {
            "employee_id": employee_id
        }
        
        response, status = await self.make_request('POST', f'/departments/{department_id}/temporary-employees', assignment_data)
        if status == 200:
            print(f"✅ Created temporary assignment for employee {employee_id} in {department_id}")
            return response
        else:
            print(f"❌ Failed to create temporary assignment: {response}")
            return None
    
    async def get_temporary_employees(self, department_id):
        """Get temporary employees for a department"""
        response, status = await self.make_request('GET', f'/departments/{department_id}/temporary-employees')
        if status == 200:
            return response
        else:
            print(f"❌ Failed to get temporary employees: {response}")
            return None
    
    async def create_breakfast_order(self, employee_id, department_id, notes="Test order"):
        """Create a breakfast order to test the critical 400 Bad Request issue"""
        print(f"\n🧪 Testing breakfast order creation for employee {employee_id} in {department_id}")
        
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
            "notes": notes
        }
        
        response, status = await self.make_request('POST', '/orders', order_data)
        
        if status == 200:
            print(f"✅ Breakfast order created successfully")
            print(f"   Order ID: {response.get('id', 'N/A')}")
            print(f"   Total Price: €{response.get('total_price', 'N/A')}")
            return response, True
        else:
            print(f"❌ Breakfast order FAILED with status {status}")
            print(f"   Error: {response}")
            return response, False
    
    async def create_drinks_order(self, employee_id, department_id):
        """Create a drinks order to test ordering functionality"""
        print(f"\n🧪 Testing drinks order creation for employee {employee_id} in {department_id}")
        
        order_data = {
            "employee_id": employee_id,
            "department_id": department_id,
            "order_type": "drinks",
            "drink_items": {
                "kaffee": 1,
                "cola": 1
            }
        }
        
        response, status = await self.make_request('POST', '/orders', order_data)
        
        if status == 200:
            print(f"✅ Drinks order created successfully")
            return response, True
        else:
            print(f"❌ Drinks order FAILED with status {status}")
            print(f"   Error: {response}")
            return response, False
    
    async def test_employee_data_structure(self, employee_id, employee_name):
        """Test employee data structure to identify missing fields"""
        print(f"\n🔍 Analyzing employee data structure for {employee_name}")
        
        profile = await self.get_employee_profile(employee_id)
        if not profile:
            print("❌ Could not get employee profile")
            return False
        
        # Check critical fields that might cause 400 errors
        critical_fields = {
            'id': profile.get('id'),
            'name': profile.get('name'),
            'department_id': profile.get('department_id'),
            'breakfast_balance': profile.get('breakfast_balance'),
            'drinks_sweets_balance': profile.get('drinks_sweets_balance'),
            'subaccount_balances': profile.get('subaccount_balances')
        }
        
        print("📋 Employee Data Structure:")
        missing_fields = []
        for field, value in critical_fields.items():
            if value is None:
                print(f"   ❌ {field}: MISSING (None)")
                missing_fields.append(field)
            else:
                print(f"   ✅ {field}: {value}")
        
        # Check subaccount_balances structure
        subaccounts = profile.get('subaccount_balances')
        if subaccounts:
            print("📋 Subaccount Balances Structure:")
            for dept_id, balances in subaccounts.items():
                breakfast_bal = balances.get('breakfast', 'MISSING')
                drinks_bal = balances.get('drinks', 'MISSING')
                print(f"   {dept_id}: breakfast={breakfast_bal}, drinks={drinks_bal}")
        else:
            print("❌ subaccount_balances: COMPLETELY MISSING")
            missing_fields.append('subaccount_balances')
        
        if missing_fields:
            print(f"⚠️  POTENTIAL ISSUE: Missing fields could cause 400 errors: {missing_fields}")
            return False
        else:
            print("✅ Employee data structure appears complete")
            return True
    
    async def test_guest_employee_scenario(self, home_dept, target_dept):
        """Test the exact guest employee scenario that causes 400 errors"""
        print(f"\n{'='*60}")
        print(f"🎯 CRITICAL TEST: Guest Employee Ordering")
        print(f"   Home Department: {home_dept['name']}")
        print(f"   Target Department: {target_dept['name']}")
        print(f"{'='*60}")
        
        test_results = {
            'employee_creation': False,
            'data_structure_check': False,
            'temporary_assignment': False,
            'guest_order_creation': False,
            'error_details': []
        }
        
        # Step 1: Create employee in home department
        employee_name = f"GuestTest_{home_dept['id']}_to_{target_dept['id']}"
        employee = await self.create_test_employee(home_dept['id'], employee_name, is_guest=False)
        
        if not employee:
            test_results['error_details'].append("Failed to create test employee")
            return test_results
        
        test_results['employee_creation'] = True
        employee_id = employee['id']
        
        # Step 2: Check employee data structure
        data_structure_ok = await self.test_employee_data_structure(employee_id, employee_name)
        test_results['data_structure_check'] = data_structure_ok
        
        # Step 3: Add as temporary employee to target department
        assignment = await self.create_temporary_assignment(target_dept['id'], employee_id)
        if assignment:
            test_results['temporary_assignment'] = True
            print(f"✅ Employee successfully added as guest worker")
        else:
            test_results['error_details'].append("Failed to create temporary assignment")
            print(f"❌ Failed to add employee as guest worker")
        
        # Step 4: Try to create order in target department (THE CRITICAL TEST)
        print(f"\n🚨 CRITICAL TEST: Creating order as guest employee...")
        order_response, order_success = await self.create_breakfast_order(
            employee_id, 
            target_dept['id'], 
            f"Guest order from {home_dept['name']} to {target_dept['name']}"
        )
        
        test_results['guest_order_creation'] = order_success
        
        if not order_success:
            # This is the critical failure we're debugging
            print(f"🚨 CRITICAL FAILURE DETECTED!")
            print(f"   Status: {order_response}")
            test_results['error_details'].append(f"Guest order failed: {order_response}")
            
            # Additional debugging
            if isinstance(order_response, dict):
                error_detail = order_response.get('detail', 'No detail provided')
                print(f"   Error Detail: {error_detail}")
                
                # Check for specific error patterns
                if "Fehler beim Prüfen bestehender Bestellungen" in str(error_detail):
                    print("🔍 ERROR PATTERN: 'Fehler beim Prüfen bestehender Bestellungen'")
                    test_results['error_details'].append("Error checking existing orders")
                
                if "Fehler beim Speichern der Bestellung" in str(error_detail):
                    print("🔍 ERROR PATTERN: 'Fehler beim Speichern der Bestellung'")
                    test_results['error_details'].append("Error saving order")
        
        return test_results
    
    async def test_regular_employee_orders(self, dept_info):
        """Test regular employee orders to establish baseline"""
        dept_id = dept_info["id"]
        dept_name = dept_info["name"]
        
        print(f"\n🧪 Testing regular employee orders in {dept_name}")
        
        # Create regular employee
        regular_employee = await self.create_test_employee(dept_id, f"RegularEmployee_{dept_id}")
        if not regular_employee:
            return False
        
        employee_id = regular_employee['id']
        
        # Test data structure
        data_ok = await self.test_employee_data_structure(employee_id, f"RegularEmployee_{dept_id}")
        
        # Test regular order creation
        order_response, order_success = await self.create_breakfast_order(employee_id, dept_id, "Regular employee order")
        
        if order_success:
            print(f"✅ Regular employee order successful in {dept_name}")
            return True
        else:
            print(f"❌ Regular employee order failed in {dept_name}: {order_response}")
            return False
    
    async def test_cross_department_scenarios(self):
        """Test all cross-department guest employee scenarios"""
        print(f"\n{'='*80}")
        print(f"🎯 COMPREHENSIVE GUEST EMPLOYEE TESTING")
        print(f"{'='*80}")
        
        scenario_results = []
        
        # Test regular employees first (baseline)
        print(f"\n📋 BASELINE TEST: Regular Employee Orders")
        for dept in self.departments:
            regular_result = await self.test_regular_employee_orders(dept)
            if not regular_result:
                print(f"⚠️  Baseline test failed for {dept['name']} - may indicate broader issues")
        
        # Test guest employee scenarios (the critical issue)
        print(f"\n📋 CRITICAL TEST: Guest Employee Cross-Department Orders")
        
        # Test key scenarios that are most likely to fail
        critical_scenarios = [
            (self.departments[0], self.departments[1]),  # Dept 1 -> Dept 2
            (self.departments[1], self.departments[0]),  # Dept 2 -> Dept 1
            (self.departments[0], self.departments[2]),  # Dept 1 -> Dept 3
            (self.departments[2], self.departments[0]),  # Dept 3 -> Dept 1
        ]
        
        for home_dept, target_dept in critical_scenarios:
            scenario_result = await self.test_guest_employee_scenario(home_dept, target_dept)
            scenario_results.append({
                'home_dept': home_dept['name'],
                'target_dept': target_dept['name'],
                'results': scenario_result
            })
        
        return scenario_results
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of guest employee ordering issue"""
        print("🚀 STARTING CRITICAL GUEST EMPLOYEE ORDERING DEBUG TEST")
        print("=" * 80)
        print("DEBUGGING: 400 Bad Request beim Bestellen als Gastmitarbeiter")
        print("- Error: 'Fehler beim Prüfen bestehender Bestellungen'")
        print("- Error: 'Fehler beim Speichern der Bestellung'")
        print("- Issue: Only affects certain employees, not all")
        print("=" * 80)
        
        # Run cross-department testing
        scenario_results = await self.test_cross_department_scenarios()
        
        # Analyze results
        total_scenarios = len(scenario_results)
        successful_scenarios = 0
        failed_scenarios = []
        
        print(f"\n{'='*80}")
        print(f"🎯 DETAILED TEST RESULTS ANALYSIS")
        print(f"{'='*80}")
        
        for scenario in scenario_results:
            home_dept = scenario['home_dept']
            target_dept = scenario['target_dept']
            results = scenario['results']
            
            print(f"\n📋 SCENARIO: {home_dept} → {target_dept}")
            print(f"   Employee Creation: {'✅' if results['employee_creation'] else '❌'}")
            print(f"   Data Structure: {'✅' if results['data_structure_check'] else '❌'}")
            print(f"   Temporary Assignment: {'✅' if results['temporary_assignment'] else '❌'}")
            print(f"   Guest Order Creation: {'✅' if results['guest_order_creation'] else '❌'}")
            
            if results['error_details']:
                print(f"   🚨 ERRORS:")
                for error in results['error_details']:
                    print(f"      - {error}")
            
            # Count as successful if guest order creation worked
            if results['guest_order_creation']:
                successful_scenarios += 1
                print(f"   ✅ SCENARIO PASSED")
            else:
                failed_scenarios.append(scenario)
                print(f"   ❌ SCENARIO FAILED")
        
        # Final analysis
        success_rate = (successful_scenarios / total_scenarios) * 100 if total_scenarios > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL ANALYSIS")
        print(f"{'='*80}")
        print(f"Total Scenarios Tested: {total_scenarios}")
        print(f"Successful Scenarios: {successful_scenarios}")
        print(f"Failed Scenarios: {len(failed_scenarios)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if successful_scenarios == total_scenarios:
            print(f"\n🎉 ALL GUEST EMPLOYEE SCENARIOS PASSED!")
            print(f"✅ Guest employee ordering is working correctly")
            print(f"✅ No 400 Bad Request errors detected")
            print(f"✅ Subaccount balances are properly initialized")
            print(f"✅ Temporary assignments are working")
        else:
            print(f"\n🚨 CRITICAL ISSUES DETECTED!")
            print(f"❌ {len(failed_scenarios)} guest employee scenarios failed")
            print(f"❌ This explains the user-reported 400 Bad Request errors")
            
            # Identify patterns in failures
            print(f"\n🔍 FAILURE PATTERN ANALYSIS:")
            error_patterns = {}
            for scenario in failed_scenarios:
                for error in scenario['results']['error_details']:
                    error_patterns[error] = error_patterns.get(error, 0) + 1
            
            for error, count in error_patterns.items():
                print(f"   - '{error}': {count} occurrences")
            
            print(f"\n💡 RECOMMENDED FIXES:")
            if any("Error checking existing orders" in error for scenario in failed_scenarios for error in scenario['results']['error_details']):
                print(f"   1. Fix 'Fehler beim Prüfen bestehender Bestellungen' validation logic")
            if any("Error saving order" in error for scenario in failed_scenarios for error in scenario['results']['error_details']):
                print(f"   2. Fix 'Fehler beim Speichern der Bestellung' save logic")
            if any("subaccount_balances" in str(scenario['results']) for scenario in failed_scenarios):
                print(f"   3. Ensure initialize_subaccount_balances is called for all employees")
            if any("temporary assignment" in str(scenario['results']) for scenario in failed_scenarios):
                print(f"   4. Fix temporary employee assignment logic")
        
        return successful_scenarios == total_scenarios

async def main():
    """Main test execution"""
    async with GuestEmployeeOrderTester() as tester:
        success = await tester.run_comprehensive_test()
        return success

if __name__ == "__main__":
    print("Backend Test Suite: Critical Guest Employee Ordering Bug Debug")
    print("=" * 70)
    
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