#!/usr/bin/env python3
"""
Backend Test Suite for Developer Dashboard Employee Management

TESTING FOCUS:
Testing the fixed Developer Dashboard backend endpoints for employee management,
specifically the `/api/developer/move-employee/{employee_id}` endpoint.

BACKEND ENDPOINT TO TEST:
PUT /api/developer/move-employee/{employee_id} - Move employee between departments

TEST SCENARIOS TO VERIFY:
1. Valid employee move between departments
2. Invalid employee ID (should return 404)
3. Invalid target department ID (should return 404)
4. Verify database update actually occurred
5. Test MoveEmployeeRequest model with proper request body

EXPECTED FUNCTIONALITY:
- POST body should contain {"new_department_id": "target_dept_id"}
- Employee's department_id should be updated in database
- Response should confirm successful move with department name
- Error handling for missing employees and departments

TEST DEPARTMENTS:
- fw4abteilung1 (admin1/password1)
- fw4abteilung2 (admin2/password2)
- fw4abteilung3 (admin3/password3)
- fw4abteilung4 (admin4/password4)

This endpoint provides the backend functionality for the Developer Dashboard
employee moving feature.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://feuerwehr-kantine.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class DeveloperDashboardTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.departments = [
            {"id": "fw4abteilung1", "name": "1. Wachabteilung", "admin_password": "admin1", "password": "password1"},
            {"id": "fw4abteilung2", "name": "2. Wachabteilung", "admin_password": "admin2", "password": "password1"},
            {"id": "fw4abteilung3", "name": "3. Wachabteilung", "admin_password": "admin3", "password": "password3"},
            {"id": "fw4abteilung4", "name": "4. Wachabteilung", "admin_password": "admin4", "password": "password4"}
        ]
        self.test_employees = []  # Track created test employees for cleanup
        
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
        """Create a test employee for testing"""
        employee_data = {
            "name": name,
            "department_id": department_id,
            "is_guest": is_guest
        }
        
        response, status = await self.make_request('POST', '/employees', employee_data)
        if status == 200:
            print(f"✅ Created test employee: {name} in {department_id} (guest: {is_guest})")
            self.test_employees.append(response['id'])  # Track for cleanup
            return response
        else:
            print(f"❌ Failed to create employee {name}: {response}")
            return None
    
    async def get_employee_details(self, employee_id):
        """Get employee details to verify department assignment"""
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        if status == 200:
            return response
        else:
            print(f"❌ Failed to get employee details: {response}")
            return None
    
    async def move_employee_to_department(self, employee_id, new_department_id):
        """Test the move-employee endpoint"""
        move_data = {
            "new_department_id": new_department_id
        }
        
        response, status = await self.make_request('PUT', f'/developer/move-employee/{employee_id}', move_data)
        return response, status
    
    async def test_valid_employee_move(self):
        """Test Case 1: Valid employee move between departments"""
        print(f"\n🧪 TEST CASE 1: Valid employee move between departments")
        
        # Create test employee in department 1
        employee = await self.create_test_employee("fw4abteilung1", "TestMoveEmployee")
        if not employee:
            return {"test": "Valid employee move", "success": False, "error": "Failed to create test employee"}
        
        employee_id = employee['id']
        original_dept = employee['department_id']
        target_dept = "fw4abteilung2"
        
        print(f"   Employee ID: {employee_id}")
        print(f"   Original Department: {original_dept}")
        print(f"   Target Department: {target_dept}")
        
        # Verify original department assignment
        original_details = await self.get_employee_details(employee_id)
        if not original_details or original_details.get('department_id') != original_dept:
            return {"test": "Valid employee move", "success": False, "error": "Employee not in expected original department"}
        
        # Move employee to department 2
        move_response, move_status = await self.move_employee_to_department(employee_id, target_dept)
        
        if move_status != 200:
            return {
                "test": "Valid employee move", 
                "success": False, 
                "error": f"Move failed with status {move_status}: {move_response}"
            }
        
        print(f"   ✅ Move API response: {move_response}")
        
        # Verify database update occurred
        updated_details = await self.get_employee_details(employee_id)
        if not updated_details:
            return {"test": "Valid employee move", "success": False, "error": "Could not verify database update"}
        
        updated_dept = updated_details.get('department_id')
        if updated_dept != target_dept:
            return {
                "test": "Valid employee move", 
                "success": False, 
                "error": f"Database not updated. Expected: {target_dept}, Found: {updated_dept}"
            }
        
        print(f"   ✅ Database updated successfully: {original_dept} → {updated_dept}")
        
        # Verify response message contains department name
        message = move_response.get('message', '')
        target_dept_info = next((d for d in self.departments if d['id'] == target_dept), None)
        if target_dept_info and target_dept_info['name'] not in message:
            return {
                "test": "Valid employee move", 
                "success": False, 
                "error": f"Response message doesn't contain department name: {message}"
            }
        
        print(f"   ✅ Response message contains department name: {message}")
        
        return {
            "test": "Valid employee move",
            "success": True,
            "employee_id": employee_id,
            "original_department": original_dept,
            "target_department": target_dept,
            "response_message": message
        }
    
    async def test_invalid_employee_id(self):
        """Test Case 2: Invalid employee ID (should return 404)"""
        print(f"\n🧪 TEST CASE 2: Invalid employee ID (should return 404)")
        
        invalid_employee_id = "invalid-employee-id-12345"
        target_dept = "fw4abteilung1"
        
        print(f"   Invalid Employee ID: {invalid_employee_id}")
        print(f"   Target Department: {target_dept}")
        
        move_response, move_status = await self.move_employee_to_department(invalid_employee_id, target_dept)
        
        if move_status == 404:
            print(f"   ✅ Correctly returned 404 for invalid employee ID")
            print(f"   ✅ Error message: {move_response}")
            return {
                "test": "Invalid employee ID",
                "success": True,
                "expected_status": 404,
                "actual_status": move_status,
                "error_message": move_response
            }
        else:
            return {
                "test": "Invalid employee ID",
                "success": False,
                "error": f"Expected 404, got {move_status}: {move_response}"
            }
    
    async def test_invalid_department_id(self):
        """Test Case 3: Invalid target department ID (should return 404)"""
        print(f"\n🧪 TEST CASE 3: Invalid target department ID (should return 404)")
        
        # Create test employee
        employee = await self.create_test_employee("fw4abteilung1", "TestInvalidDeptMove")
        if not employee:
            return {"test": "Invalid department ID", "success": False, "error": "Failed to create test employee"}
        
        employee_id = employee['id']
        invalid_dept_id = "invalid-department-id-12345"
        
        print(f"   Employee ID: {employee_id}")
        print(f"   Invalid Department ID: {invalid_dept_id}")
        
        move_response, move_status = await self.move_employee_to_department(employee_id, invalid_dept_id)
        
        if move_status == 404:
            print(f"   ✅ Correctly returned 404 for invalid department ID")
            print(f"   ✅ Error message: {move_response}")
            return {
                "test": "Invalid department ID",
                "success": True,
                "expected_status": 404,
                "actual_status": move_status,
                "error_message": move_response
            }
        else:
            return {
                "test": "Invalid department ID",
                "success": False,
                "error": f"Expected 404, got {move_status}: {move_response}"
            }
    
    async def test_move_employee_request_model(self):
        """Test Case 4: Verify MoveEmployeeRequest model accepts proper request body"""
        print(f"\n🧪 TEST CASE 4: MoveEmployeeRequest model validation")
        
        # Create test employee
        employee = await self.create_test_employee("fw4abteilung3", "TestRequestModel")
        if not employee:
            return {"test": "MoveEmployeeRequest model", "success": False, "error": "Failed to create test employee"}
        
        employee_id = employee['id']
        target_dept = "fw4abteilung4"
        
        print(f"   Employee ID: {employee_id}")
        print(f"   Target Department: {target_dept}")
        
        # Test with correct request body format
        correct_request = {"new_department_id": target_dept}
        print(f"   Request body: {correct_request}")
        
        move_response, move_status = await self.move_employee_to_department(employee_id, target_dept)
        
        if move_status == 200:
            print(f"   ✅ MoveEmployeeRequest model accepted correct request body")
            print(f"   ✅ Response: {move_response}")
            
            # Verify the move actually happened
            updated_details = await self.get_employee_details(employee_id)
            if updated_details and updated_details.get('department_id') == target_dept:
                print(f"   ✅ Database update confirmed")
                return {
                    "test": "MoveEmployeeRequest model",
                    "success": True,
                    "request_body": correct_request,
                    "response": move_response,
                    "database_updated": True
                }
            else:
                return {
                    "test": "MoveEmployeeRequest model",
                    "success": False,
                    "error": "Request accepted but database not updated"
                }
        else:
            return {
                "test": "MoveEmployeeRequest model",
                "success": False,
                "error": f"Request rejected with status {move_status}: {move_response}"
            }
    
    async def test_multiple_department_moves(self):
        """Test Case 5: Test moving employee through multiple departments"""
        print(f"\n🧪 TEST CASE 5: Multiple department moves")
        
        # Create test employee
        employee = await self.create_test_employee("fw4abteilung1", "TestMultipleMoves")
        if not employee:
            return {"test": "Multiple department moves", "success": False, "error": "Failed to create test employee"}
        
        employee_id = employee['id']
        move_sequence = ["fw4abteilung2", "fw4abteilung3", "fw4abteilung4", "fw4abteilung1"]
        
        print(f"   Employee ID: {employee_id}")
        print(f"   Move sequence: {' → '.join(move_sequence)}")
        
        moves_completed = []
        
        for target_dept in move_sequence:
            print(f"   Moving to {target_dept}...")
            
            move_response, move_status = await self.move_employee_to_department(employee_id, target_dept)
            
            if move_status != 200:
                return {
                    "test": "Multiple department moves",
                    "success": False,
                    "error": f"Move to {target_dept} failed with status {move_status}: {move_response}",
                    "completed_moves": moves_completed
                }
            
            # Verify database update
            updated_details = await self.get_employee_details(employee_id)
            if not updated_details or updated_details.get('department_id') != target_dept:
                return {
                    "test": "Multiple department moves",
                    "success": False,
                    "error": f"Database not updated for move to {target_dept}",
                    "completed_moves": moves_completed
                }
            
            moves_completed.append({
                "target_department": target_dept,
                "response": move_response,
                "database_updated": True
            })
            
            print(f"   ✅ Successfully moved to {target_dept}")
        
        print(f"   ✅ All {len(move_sequence)} moves completed successfully")
        
        return {
            "test": "Multiple department moves",
            "success": True,
            "employee_id": employee_id,
            "move_sequence": move_sequence,
            "completed_moves": moves_completed
        }
    
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
    
    async def make_payment(self, employee_id, department_id, amount, balance_type="breakfast"):
        """Make a payment to adjust employee balance"""
        payment_data = {
            "payment_type": "breakfast" if balance_type == "breakfast" else "drinks_sweets",
            "balance_type": balance_type,
            "amount": amount,
            "payment_method": "cash",
            "notes": f"Test payment for balance scenario"
        }
        
        response, status = await self.make_request('POST', f'/department-admin/subaccount-payment/{employee_id}', 
                                                 payment_data, params={"admin_department": department_id})
        
        if status == 200:
            print(f"✅ Payment of €{amount} successful for {balance_type} balance")
            return response, True
        else:
            print(f"❌ Payment FAILED with status {status}")
            print(f"   Error: {response}")
            return response, False
    
    async def setup_employee_with_positive_main_balance(self, department_id):
        """Create employee with positive main balance"""
        employee_name = f"PositiveMainBalance_{department_id}"
        employee = await self.create_test_employee(department_id, employee_name)
        
        if not employee:
            return None
        
        employee_id = employee['id']
        
        # Make a payment to create positive balance
        payment_response, payment_success = await self.make_payment(employee_id, department_id, 10.0, "breakfast")
        
        if payment_success:
            print(f"✅ Created employee with positive main balance: {employee_name}")
            return employee_id
        else:
            print(f"❌ Failed to create positive balance for {employee_name}")
            return None
    
    async def setup_employee_with_negative_main_balance(self, department_id):
        """Create employee with negative main balance (via order)"""
        employee_name = f"NegativeMainBalance_{department_id}"
        employee = await self.create_test_employee(department_id, employee_name)
        
        if not employee:
            return None
        
        employee_id = employee['id']
        
        # Create an order to generate negative balance
        order_response, order_success = await self.create_breakfast_order(employee_id, department_id, "Order for negative balance")
        
        if order_success:
            print(f"✅ Created employee with negative main balance: {employee_name}")
            return employee_id
        else:
            print(f"❌ Failed to create negative balance for {employee_name}")
            return None
    
    async def setup_employee_with_zero_main_nonzero_subaccount(self, home_dept_id, target_dept_id):
        """Create employee with zero main balance but non-zero subaccount balance"""
        employee_name = f"ZeroMainNonzeroSub_{home_dept_id}_to_{target_dept_id}"
        employee = await self.create_test_employee(home_dept_id, employee_name)
        
        if not employee:
            return None
        
        employee_id = employee['id']
        
        # Add as temporary employee to target department
        assignment = await self.create_temporary_assignment(target_dept_id, employee_id)
        if not assignment:
            print(f"❌ Failed to create temporary assignment")
            return None
        
        # Create order in target department (creates subaccount balance)
        order_response, order_success = await self.create_breakfast_order(employee_id, target_dept_id, "Order for subaccount balance")
        
        if order_success:
            print(f"✅ Created employee with zero main, non-zero subaccount balance: {employee_name}")
            return employee_id
        else:
            print(f"❌ Failed to create subaccount balance for {employee_name}")
            return None
    
    async def setup_employee_with_all_zero_balances(self, department_id):
        """Create employee with all balances at 0€"""
        employee_name = f"AllZeroBalances_{department_id}"
        employee = await self.create_test_employee(department_id, employee_name)
        
        if employee:
            print(f"✅ Created employee with all zero balances: {employee_name}")
            return employee['id']
        else:
            print(f"❌ Failed to create employee with zero balances")
            return None
    
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
    
    # Removed unused methods for employee deletion security testing
    
    # Additional unused methods removed for employee deletion security testing
    
    async def test_duplicate_order_validation_unused(self):
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
        """Run comprehensive test of Developer Dashboard employee management"""
        print("🚀 STARTING DEVELOPER DASHBOARD EMPLOYEE MANAGEMENT TEST")
        print("=" * 80)
        print("TESTING: Developer Dashboard move-employee endpoint")
        print("- Endpoint: PUT /api/developer/move-employee/{employee_id}")
        print("- Feature: Move employees between departments")
        print("- Model: MoveEmployeeRequest with new_department_id")
        print("=" * 80)
        
        test_results = []
        
        # Test Case 1: Valid employee move between departments
        result_1 = await self.test_valid_employee_move()
        test_results.append(result_1)
        
        # Test Case 2: Invalid employee ID (should return 404)
        result_2 = await self.test_invalid_employee_id()
        test_results.append(result_2)
        
        # Test Case 3: Invalid target department ID (should return 404)
        result_3 = await self.test_invalid_department_id()
        test_results.append(result_3)
        
        # Test Case 4: Verify MoveEmployeeRequest model
        result_4 = await self.test_move_employee_request_model()
        test_results.append(result_4)
        
        # Test Case 5: Multiple department moves
        result_5 = await self.test_multiple_department_moves()
        test_results.append(result_5)
        
        # Analyze results
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results if result.get('success', False))
        failed_tests = [result for result in test_results if not result.get('success', False)]
        
        print(f"\n{'='*80}")
        print(f"🎯 DETAILED TEST RESULTS ANALYSIS")
        print(f"{'='*80}")
        
        for result in test_results:
            test_name = result['test']
            success = result.get('success', False)
            
            print(f"\n📋 TEST: {test_name}")
            print(f"   Result: {'✅ PASSED' if success else '❌ FAILED'}")
            
            if success:
                # Show success details
                if 'response_message' in result:
                    print(f"   Response: {result['response_message']}")
                if 'database_updated' in result:
                    print(f"   Database Updated: {'✅' if result['database_updated'] else '❌'}")
                if 'completed_moves' in result:
                    print(f"   Completed Moves: {len(result['completed_moves'])}")
            else:
                # Show error details
                if 'error' in result:
                    print(f"   🚨 ERROR: {result['error']}")
        
        # Final analysis
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL ANALYSIS")
        print(f"{'='*80}")
        print(f"Total Test Cases: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Failed Tests: {len(failed_tests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if successful_tests == total_tests:
            print(f"\n🎉 ALL DEVELOPER DASHBOARD TESTS PASSED!")
            print(f"✅ The /api/developer/move-employee/{{employee_id}} endpoint is working correctly")
            print(f"✅ MoveEmployeeRequest model accepts proper request body format")
            print(f"✅ Employee department_id is updated correctly in database")
            print(f"✅ Response confirms successful move with department name")
            print(f"✅ Error handling works for invalid employee IDs (404)")
            print(f"✅ Error handling works for invalid department IDs (404)")
            print(f"✅ Multiple department moves work correctly")
            print(f"✅ Developer Dashboard employee management is FULLY FUNCTIONAL")
        else:
            print(f"\n🚨 CRITICAL ISSUES DETECTED!")
            print(f"❌ {len(failed_tests)} test cases failed")
            print(f"❌ This may affect the Developer Dashboard functionality")
            
            # Identify patterns in failures
            print(f"\n🔍 FAILURE PATTERN ANALYSIS:")
            for result in failed_tests:
                test_name = result['test']
                error = result.get('error', 'Unknown error')
                print(f"   - {test_name}: {error}")
            
            print(f"\n💡 RECOMMENDED FIXES:")
            if any('404' in result.get('error', '') for result in failed_tests):
                print(f"   1. Check endpoint URL and routing configuration")
            if any('database' in result.get('error', '').lower() for result in failed_tests):
                print(f"   2. Verify database update logic in move-employee endpoint")
            if any('model' in result.get('error', '').lower() for result in failed_tests):
                print(f"   3. Check MoveEmployeeRequest model validation")
        
        return successful_tests == total_tests

async def main():
    """Main test execution"""
    async with EmployeeDeletionSecurityTester() as tester:
        success = await tester.run_comprehensive_test()
        return success

if __name__ == "__main__":
    print("Backend Test Suite: Employee Deletion Security Feature")
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