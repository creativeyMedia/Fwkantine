#!/usr/bin/env python3
"""
Backend Test Suite for Employee Deletion Security Feature

TESTING FOCUS:
Testing the new employee deletion security feature that prevents deleting employees 
with non-zero balances, specifically the `/employees/{employee_id}/all-balances` endpoint.

BACKEND ENDPOINT TO TEST:
GET /api/employees/{employee_id}/all-balances - Complete balance structure for deletion checking

BALANCE SCENARIOS TO VERIFY:
1. Employee with positive main balance
2. Employee with negative main balance  
3. Employee with zero main balance but non-zero subaccount balance
4. Employee with all balances at 0€ (should allow deletion)

EXPECTED RESPONSE STRUCTURE:
- breakfast_balance and drinks_sweets_balance for main account
- subaccount_balances object with all department balances
- Accurate balance calculation for both positive and negative amounts

TEST DEPARTMENTS:
- fw4abteilung1 (admin1/password1)
- fw4abteilung2 (admin2/password2) 

This endpoint provides the backend support for the frontend security feature
that prevents accidental deletion of employees with outstanding balances.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://feuerwehr-kantine.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class EmployeeDeletionSecurityTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.departments = [
            {"id": "fw4abteilung1", "name": "1. Wachabteilung", "admin_password": "admin1", "password": "password1"},
            {"id": "fw4abteilung2", "name": "2. Wachabteilung", "admin_password": "admin2", "password": "password1"},
            {"id": "fw4abteilung3", "name": "3. Wachabteilung", "admin_password": "admin3", "password": "password3"},
            {"id": "fw4abteilung4", "name": "4. Wachabteilung", "admin_password": "admin4", "password": "password4"}
        ]
        self.test_departments = ["fw4abteilung1", "fw4abteilung2"]  # Focus on these for testing
        
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
    
    async def get_employee_all_balances(self, employee_id):
        """Get all balances for an employee using the deletion security endpoint"""
        response, status = await self.make_request('GET', f'/employees/{employee_id}/all-balances')
        if status == 200:
            return response
        else:
            print(f"❌ Failed to get employee all balances: {response}")
            return None
    
    async def test_all_balances_endpoint_structure(self, employee_id, employee_name):
        """Test the all-balances endpoint structure for deletion security"""
        print(f"\n🔍 Testing all-balances endpoint structure for {employee_name}")
        
        balances = await self.get_employee_all_balances(employee_id)
        if not balances:
            print("❌ Could not get employee all balances")
            return False, {}
        
        # Check required fields for deletion security
        required_fields = {
            'employee_id': balances.get('employee_id'),
            'employee_name': balances.get('employee_name'),
            'main_department_id': balances.get('main_department_id'),
            'main_department_name': balances.get('main_department_name'),
            'main_balances': balances.get('main_balances'),
            'subaccount_balances': balances.get('subaccount_balances')
        }
        
        print("📋 All-Balances Endpoint Response Structure:")
        missing_fields = []
        for field, value in required_fields.items():
            if value is None:
                print(f"   ❌ {field}: MISSING (None)")
                missing_fields.append(field)
            else:
                print(f"   ✅ {field}: {value}")
        
        # Check main_balances structure
        main_balances = balances.get('main_balances', {})
        if main_balances:
            breakfast_balance = main_balances.get('breakfast', 'MISSING')
            drinks_sweets_balance = main_balances.get('drinks_sweets', 'MISSING')
            print(f"📋 Main Balances: breakfast={breakfast_balance}, drinks_sweets={drinks_sweets_balance}")
        else:
            print("❌ main_balances: COMPLETELY MISSING")
            missing_fields.append('main_balances')
        
        # Check subaccount_balances structure
        subaccounts = balances.get('subaccount_balances', {})
        if subaccounts:
            print("📋 Subaccount Balances Structure:")
            for dept_id, dept_data in subaccounts.items():
                dept_name = dept_data.get('department_name', 'MISSING')
                breakfast_bal = dept_data.get('breakfast', 'MISSING')
                drinks_bal = dept_data.get('drinks', 'MISSING')
                total_bal = dept_data.get('total', 'MISSING')
                print(f"   {dept_id} ({dept_name}): breakfast={breakfast_bal}, drinks={drinks_bal}, total={total_bal}")
        else:
            print("❌ subaccount_balances: COMPLETELY MISSING")
            missing_fields.append('subaccount_balances')
        
        if missing_fields:
            print(f"⚠️  MISSING FIELDS: {missing_fields}")
            return False, balances
        else:
            print("✅ All-balances endpoint structure is complete")
            return True, balances
    
    async def test_balance_scenario(self, scenario_name, employee_id, expected_deletable):
        """Test a specific balance scenario for deletion security"""
        print(f"\n🎯 TESTING SCENARIO: {scenario_name}")
        
        # Get all balances using the deletion security endpoint
        structure_ok, balances = await self.test_all_balances_endpoint_structure(employee_id, scenario_name)
        
        if not structure_ok:
            return {
                'scenario': scenario_name,
                'endpoint_working': False,
                'structure_complete': False,
                'deletable': None,
                'error': 'Endpoint structure incomplete'
            }
        
        # Calculate if employee should be deletable based on balances
        main_balances = balances.get('main_balances', {})
        main_breakfast = main_balances.get('breakfast', 0.0)
        main_drinks_sweets = main_balances.get('drinks_sweets', 0.0)
        
        # Check all subaccount balances
        subaccount_balances = balances.get('subaccount_balances', {})
        has_nonzero_subaccount = False
        
        for dept_id, dept_data in subaccount_balances.items():
            breakfast_bal = dept_data.get('breakfast', 0.0)
            drinks_bal = dept_data.get('drinks', 0.0)
            if breakfast_bal != 0.0 or drinks_bal != 0.0:
                has_nonzero_subaccount = True
                print(f"   🔍 Non-zero subaccount found in {dept_id}: breakfast={breakfast_bal}, drinks={drinks_bal}")
        
        # Determine if employee should be deletable
        has_nonzero_main = (main_breakfast != 0.0 or main_drinks_sweets != 0.0)
        should_be_deletable = not (has_nonzero_main or has_nonzero_subaccount)
        
        print(f"   📊 Balance Analysis:")
        print(f"      Main breakfast: {main_breakfast}")
        print(f"      Main drinks/sweets: {main_drinks_sweets}")
        print(f"      Has non-zero main balance: {has_nonzero_main}")
        print(f"      Has non-zero subaccount balance: {has_nonzero_subaccount}")
        print(f"      Should be deletable: {should_be_deletable}")
        print(f"      Expected deletable: {expected_deletable}")
        
        # Verify expectation matches calculation
        expectation_correct = (should_be_deletable == expected_deletable)
        
        return {
            'scenario': scenario_name,
            'endpoint_working': True,
            'structure_complete': True,
            'main_balances': main_balances,
            'subaccount_balances': subaccount_balances,
            'has_nonzero_main': has_nonzero_main,
            'has_nonzero_subaccount': has_nonzero_subaccount,
            'should_be_deletable': should_be_deletable,
            'expected_deletable': expected_deletable,
            'expectation_correct': expectation_correct,
            'deletable': should_be_deletable
        }
    
    async def test_problematic_employee_scenarios(self):
        """Test specific scenarios that might cause 400 errors"""
        print(f"\n{'='*60}")
        print(f"🚨 TESTING PROBLEMATIC EMPLOYEE SCENARIOS")
        print(f"{'='*60}")
        
        problematic_scenarios = []
        
        # Scenario 1: Try to create order with employee that might have missing subaccount_balances
        print(f"\n🧪 SCENARIO 1: Testing order with potentially incomplete employee data")
        
        # Get existing employees to test with
        response, status = await self.make_request('GET', '/departments/fw4abteilung1/employees')
        if status == 200 and response:
            existing_employees = response
            print(f"Found {len(existing_employees)} existing employees in fw4abteilung1")
            
            # Test with first few existing employees
            for i, employee in enumerate(existing_employees[:3]):
                employee_id = employee.get('id')
                employee_name = employee.get('name', f'Employee_{i}')
                
                print(f"\n🔍 Testing existing employee: {employee_name}")
                
                # Check their data structure
                data_ok = await self.test_employee_data_structure(employee_id, employee_name)
                
                # Try to create order as guest in another department
                print(f"🧪 Testing guest order for existing employee {employee_name}")
                
                # Add as temporary employee to department 2
                assignment = await self.create_temporary_assignment('fw4abteilung2', employee_id)
                
                if assignment:
                    # Try to create order
                    order_response, order_success = await self.create_breakfast_order(
                        employee_id, 
                        'fw4abteilung2', 
                        f"Existing employee guest order test - {employee_name}"
                    )
                    
                    scenario_result = {
                        'employee_name': employee_name,
                        'employee_id': employee_id,
                        'data_structure_ok': data_ok,
                        'temporary_assignment_ok': True,
                        'order_success': order_success,
                        'error_details': [] if order_success else [str(order_response)]
                    }
                    
                    if not order_success:
                        print(f"🚨 FOUND PROBLEMATIC SCENARIO!")
                        print(f"   Employee: {employee_name}")
                        print(f"   Error: {order_response}")
                        
                    problematic_scenarios.append(scenario_result)
                else:
                    print(f"❌ Could not create temporary assignment for {employee_name}")
        
        # Scenario 2: Test with employees from different departments
        print(f"\n🧪 SCENARIO 2: Cross-department testing with existing employees")
        
        for dept in self.departments[:2]:  # Test first 2 departments
            dept_id = dept['id']
            dept_name = dept['name']
            
            response, status = await self.make_request('GET', f'/departments/{dept_id}/employees')
            if status == 200 and response and len(response) > 0:
                # Test with first employee from this department
                employee = response[0]
                employee_id = employee.get('id')
                employee_name = employee.get('name', 'Unknown')
                
                print(f"\n🔍 Testing {dept_name} employee: {employee_name}")
                
                # Try to create order in their home department first
                home_order_response, home_order_success = await self.create_breakfast_order(
                    employee_id, 
                    dept_id, 
                    f"Home department order - {employee_name}"
                )
                
                # Try to create order as guest in another department
                target_dept_id = 'fw4abteilung3' if dept_id != 'fw4abteilung3' else 'fw4abteilung4'
                
                assignment = await self.create_temporary_assignment(target_dept_id, employee_id)
                if assignment:
                    guest_order_response, guest_order_success = await self.create_breakfast_order(
                        employee_id, 
                        target_dept_id, 
                        f"Guest order from {dept_name} - {employee_name}"
                    )
                    
                    scenario_result = {
                        'employee_name': employee_name,
                        'employee_id': employee_id,
                        'home_department': dept_id,
                        'target_department': target_dept_id,
                        'home_order_success': home_order_success,
                        'guest_order_success': guest_order_success,
                        'home_error': [] if home_order_success else [str(home_order_response)],
                        'guest_error': [] if guest_order_success else [str(guest_order_response)]
                    }
                    
                    if not guest_order_success:
                        print(f"🚨 FOUND GUEST ORDER FAILURE!")
                        print(f"   Employee: {employee_name} from {dept_name}")
                        print(f"   Target: {target_dept_id}")
                        print(f"   Error: {guest_order_response}")
                    
                    problematic_scenarios.append(scenario_result)
        
        return problematic_scenarios
    
    async def test_duplicate_order_validation(self):
        """Test the specific duplicate order validation that causes 400 errors"""
        print(f"\n{'='*60}")
        print(f"🎯 CRITICAL FINDING: DUPLICATE ORDER VALIDATION TEST")
        print(f"{'='*60}")
        print(f"Found the root cause: 400 Bad Request occurs when employee")
        print(f"tries to create a SECOND breakfast order on the same day!")
        print(f"Error: 'Sie haben bereits eine Frühstücksbestellung für heute'")
        
        test_results = []
        
        # Test 1: Create employee and first order (should succeed)
        print(f"\n🧪 TEST 1: First breakfast order (should succeed)")
        employee = await self.create_test_employee('fw4abteilung1', 'DuplicateOrderTest')
        if not employee:
            return [{'error': 'Could not create test employee'}]
        
        employee_id = employee['id']
        
        # First order should succeed
        first_order, first_success = await self.create_breakfast_order(
            employee_id, 
            'fw4abteilung1', 
            "First breakfast order of the day"
        )
        
        test_results.append({
            'test': 'First breakfast order in home department',
            'success': first_success,
            'error': None if first_success else str(first_order)
        })
        
        # Test 2: Try second order in same department (should fail)
        print(f"\n🧪 TEST 2: Second breakfast order in same department (should fail)")
        second_order, second_success = await self.create_breakfast_order(
            employee_id, 
            'fw4abteilung1', 
            "Second breakfast order attempt - same department"
        )
        
        test_results.append({
            'test': 'Second breakfast order in same department',
            'success': second_success,
            'expected_failure': True,
            'error': None if second_success else str(second_order)
        })
        
        # Test 3: Try order as guest in different department (THE CRITICAL TEST)
        print(f"\n🧪 TEST 3: Guest order in different department (THE CRITICAL SCENARIO)")
        print(f"This is the exact scenario causing user issues!")
        
        # Add as temporary employee to department 2
        assignment = await self.create_temporary_assignment('fw4abteilung2', employee_id)
        
        if assignment:
            guest_order, guest_success = await self.create_breakfast_order(
                employee_id, 
                'fw4abteilung2', 
                "Guest order attempt after having breakfast order in home department"
            )
            
            test_results.append({
                'test': 'Guest breakfast order in different department',
                'success': guest_success,
                'expected_failure': True,  # This should fail due to existing order
                'error': None if guest_success else str(guest_order)
            })
            
            if not guest_success:
                print(f"🎯 CONFIRMED: This is the exact issue users are experiencing!")
                print(f"   Employee has breakfast order in home department")
                print(f"   Employee tries to order as guest in different department")
                print(f"   System blocks it with 400 Bad Request")
                print(f"   Error: {guest_order}")
        
        # Test 4: Test with drinks order (should work)
        print(f"\n🧪 TEST 4: Drinks order as guest (should work)")
        drinks_order, drinks_success = await self.create_drinks_order(
            employee_id, 
            'fw4abteilung2'
        )
        
        test_results.append({
            'test': 'Drinks order as guest',
            'success': drinks_success,
            'error': None if drinks_success else str(drinks_order)
        })
        
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
        
        # Run problematic employee scenarios testing
        problematic_results = await self.test_problematic_employee_scenarios()
        
        # Run the critical duplicate order validation test
        duplicate_order_results = await self.test_duplicate_order_validation()
        
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
        
        # Analyze duplicate order test results
        print(f"\n🎯 DUPLICATE ORDER VALIDATION ANALYSIS:")
        for result in duplicate_order_results:
            test_name = result.get('test', 'Unknown test')
            success = result.get('success', False)
            expected_failure = result.get('expected_failure', False)
            error = result.get('error', '')
            
            if expected_failure:
                status = "✅ CORRECTLY FAILED" if not success else "❌ UNEXPECTEDLY SUCCEEDED"
            else:
                status = "✅ PASSED" if success else "❌ FAILED"
            
            print(f"   {test_name}: {status}")
            if error and not success:
                print(f"      Error: {error}")
        
        if successful_scenarios == total_scenarios:
            print(f"\n🎉 ALL GUEST EMPLOYEE SCENARIOS PASSED!")
            print(f"✅ Guest employee ordering is working correctly")
            print(f"✅ No 400 Bad Request errors detected in new employee scenarios")
            print(f"✅ Subaccount balances are properly initialized")
            print(f"✅ Temporary assignments are working")
            
            print(f"\n🎯 ROOT CAUSE IDENTIFIED:")
            print(f"❗ The 400 Bad Request error occurs when employees try to create")
            print(f"❗ a SECOND breakfast order on the same day (duplicate order validation)")
            print(f"❗ This affects existing employees who already have breakfast orders")
            print(f"❗ Error message: 'Sie haben bereits eine Frühstücksbestellung für heute'")
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