#!/usr/bin/env python3
"""
Backend Test Suite for Employee Profile Endpoint Balance Data Structure

TESTING FOCUS:
Testing the employee profile endpoint to verify balance data structure and values.

BACKEND ENDPOINT TO TEST:
GET /api/employees/{employee_id}/profile - Employee profile with balance data

TEST SCENARIOS TO VERIFY:
1. Test GET /api/employees/{employee_id}/profile endpoint
2. Verify the exact structure of returned balance data
3. Check if balance fields contain actual values (not 0)
4. Examine both the main response structure and nested employee object
5. Verify payment_history and order_history are included

FOCUS AREAS:
- Balance field names: breakfast_balance vs breakfast_total, drinks_sweets_balance vs drinks_sweets_total
- Response structure: Are balances in main response or nested under employee object?
- Actual balance values: Do they reflect real transaction history?
- Data completeness: Are all expected fields present?

EXPECTED INVESTIGATION:
- Identify correct field names for balance display
- Confirm balance values are not defaulting to 0
- Verify API response structure matches frontend expectations
- Check if employee object contains balance data vs main response level

TEST EMPLOYEE: Use any employee ID with existing order/payment history from fw4abteilung1 or fw4abteilung2
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://feuerwehr-kantine.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class EmployeeProfileTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.departments = [
            {"id": "fw4abteilung1", "name": "1. Wachabteilung", "admin_password": "admin1", "password": "password1"},
            {"id": "fw4abteilung2", "name": "2. Wachabteilung", "admin_password": "admin2", "password": "password2"},
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
            # The profile endpoint returns an object with "employee" field
            return response.get('employee')
        else:
            print(f"❌ Failed to get employee details: {response}")
            return None
    
    async def get_employee_all_balances(self, employee_id):
        """Get all balances (main + subaccounts) for an employee"""
        response, status = await self.make_request('GET', f'/employees/{employee_id}/all-balances')
        if status == 200:
            return response
        else:
            print(f"❌ Failed to get employee balances: {response}")
            return None
    
    async def set_employee_balance(self, employee_id, department_id, balance_type, amount):
        """Set employee balance for testing purposes using flexible payment"""
        # First get current balance
        balances = await self.get_employee_all_balances(employee_id)
        if not balances:
            return False
        
        # Calculate current balance
        if balance_type == "breakfast":
            current_balance = balances["main_balances"]["breakfast"]
        elif balance_type == "drinks":
            current_balance = balances["main_balances"]["drinks_sweets"]
        else:
            print(f"❌ Invalid balance type: {balance_type}")
            return False
        
        # Calculate payment amount needed to reach target balance
        payment_amount = amount - current_balance
        
        if payment_amount == 0:
            return True  # Already at target balance
        
        # Use flexible payment to adjust balance with admin_department parameter
        payment_data = {
            "payment_type": balance_type if balance_type != "drinks" else "drinks_sweets",
            "amount": payment_amount,
            "payment_method": "adjustment",
            "notes": f"Test balance adjustment to {amount}"
        }
        
        # Add admin_department as query parameter
        params = {"admin_department": department_id}
        
        response, status = await self.make_request('POST', f'/department-admin/flexible-payment/{employee_id}', payment_data, params)
        if status == 200:
            print(f"✅ Set {balance_type} balance to €{amount} for employee {employee_id[:8]}")
            return True
        else:
            print(f"❌ Failed to set balance: {response}")
            return False
    
    async def move_employee_to_department(self, employee_id, new_department_id):
        """Test the move-employee endpoint"""
        move_data = {
            "new_department_id": new_department_id
        }
        
        response, status = await self.make_request('PUT', f'/developer/move-employee/{employee_id}', move_data)
        return response, status
    
    async def get_employees_with_history(self, department_id):
        """Get employees from a department that have order/payment history"""
        response, status = await self.make_request('GET', f'/departments/{department_id}/employees')
        if status == 200:
            employees = response
            # Filter employees with non-zero balances (indicating history)
            employees_with_history = []
            for emp in employees:
                if (emp.get('breakfast_balance', 0) != 0 or 
                    emp.get('drinks_sweets_balance', 0) != 0):
                    employees_with_history.append(emp)
            return employees_with_history
        return []

    async def test_employee_profile_structure(self, employee_id, employee_name):
        """Test Case 1: Verify employee profile endpoint structure and balance fields"""
        print(f"\n🧪 TEST CASE 1: Employee Profile Structure - {employee_name}")
        
        # Get employee profile
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        
        if status != 200:
            return {
                "test": "Employee profile structure",
                "success": False,
                "error": f"Profile endpoint failed with status {status}: {response}"
            }
        
        print(f"   ✅ Profile endpoint accessible (HTTP 200)")
        
        # Analyze response structure
        required_fields = ['employee', 'order_history', 'payment_history', 'total_orders']
        missing_fields = []
        
        for field in required_fields:
            if field not in response:
                missing_fields.append(field)
        
        if missing_fields:
            return {
                "test": "Employee profile structure",
                "success": False,
                "error": f"Missing required fields: {missing_fields}"
            }
        
        print(f"   ✅ All required fields present: {required_fields}")
        
        # Check employee object structure
        employee_obj = response.get('employee', {})
        employee_balance_fields = ['breakfast_balance', 'drinks_sweets_balance']
        
        for field in employee_balance_fields:
            if field not in employee_obj:
                return {
                    "test": "Employee profile structure",
                    "success": False,
                    "error": f"Employee object missing balance field: {field}"
                }
        
        print(f"   ✅ Employee object has balance fields: {employee_balance_fields}")
        
        # Check for balance fields in main response
        main_balance_fields = ['breakfast_total', 'drinks_sweets_total']
        main_balance_present = []
        
        for field in main_balance_fields:
            if field in response:
                main_balance_present.append(field)
        
        print(f"   📊 Main response balance fields: {main_balance_present}")
        
        # Analyze balance values
        employee_breakfast = employee_obj.get('breakfast_balance', 0)
        employee_drinks = employee_obj.get('drinks_sweets_balance', 0)
        main_breakfast = response.get('breakfast_total', 'NOT_FOUND')
        main_drinks = response.get('drinks_sweets_total', 'NOT_FOUND')
        
        print(f"   📊 Employee object balances:")
        print(f"      breakfast_balance: €{employee_breakfast}")
        print(f"      drinks_sweets_balance: €{employee_drinks}")
        print(f"   📊 Main response balances:")
        print(f"      breakfast_total: {main_breakfast}")
        print(f"      drinks_sweets_total: {main_drinks}")
        
        # Check if balances are actual values (not 0)
        has_actual_values = (employee_breakfast != 0 or employee_drinks != 0)
        
        return {
            "test": "Employee profile structure",
            "success": True,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "structure_complete": len(missing_fields) == 0,
            "employee_balance_fields": employee_balance_fields,
            "main_balance_fields": main_balance_present,
            "employee_balances": {
                "breakfast_balance": employee_breakfast,
                "drinks_sweets_balance": employee_drinks
            },
            "main_balances": {
                "breakfast_total": main_breakfast,
                "drinks_sweets_total": main_drinks
            },
            "has_actual_values": has_actual_values,
            "order_history_count": len(response.get('order_history', [])),
            "payment_history_count": len(response.get('payment_history', []))
        }
    
    async def test_balance_field_names(self, employee_id, employee_name):
        """Test Case 2: Verify correct balance field names and values"""
        print(f"\n🧪 TEST CASE 2: Balance Field Names - {employee_name}")
        
        # Get employee profile
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        
        if status != 200:
            return {
                "test": "Balance field names",
                "success": False,
                "error": f"Profile endpoint failed with status {status}: {response}"
            }
        
        # Check for different possible field name variations
        employee_obj = response.get('employee', {})
        
        # Check employee object field names
        employee_field_variations = {
            'breakfast': ['breakfast_balance', 'breakfast_total'],
            'drinks_sweets': ['drinks_sweets_balance', 'drinks_sweets_total']
        }
        
        employee_fields_found = {}
        for category, variations in employee_field_variations.items():
            found_fields = []
            for field in variations:
                if field in employee_obj:
                    found_fields.append({
                        'field': field,
                        'value': employee_obj[field]
                    })
            employee_fields_found[category] = found_fields
        
        # Check main response field names
        main_field_variations = {
            'breakfast': ['breakfast_balance', 'breakfast_total'],
            'drinks_sweets': ['drinks_sweets_balance', 'drinks_sweets_total']
        }
        
        main_fields_found = {}
        for category, variations in main_field_variations.items():
            found_fields = []
            for field in variations:
                if field in response:
                    found_fields.append({
                        'field': field,
                        'value': response[field]
                    })
            main_fields_found[category] = found_fields
        
        print(f"   📊 Employee object balance fields:")
        for category, fields in employee_fields_found.items():
            if fields:
                for field_info in fields:
                    print(f"      {field_info['field']}: €{field_info['value']}")
            else:
                print(f"      {category}: No fields found")
        
        print(f"   📊 Main response balance fields:")
        for category, fields in main_fields_found.items():
            if fields:
                for field_info in fields:
                    print(f"      {field_info['field']}: {field_info['value']}")
            else:
                print(f"      {category}: No fields found")
        
        # Determine the correct field names being used
        correct_employee_fields = {}
        correct_main_fields = {}
        
        for category, fields in employee_fields_found.items():
            if fields:
                correct_employee_fields[category] = fields[0]['field']  # Use first found
        
        for category, fields in main_fields_found.items():
            if fields:
                correct_main_fields[category] = fields[0]['field']  # Use first found
        
        return {
            "test": "Balance field names",
            "success": True,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "employee_fields_found": employee_fields_found,
            "main_fields_found": main_fields_found,
            "correct_employee_fields": correct_employee_fields,
            "correct_main_fields": correct_main_fields
        }
    
    async def test_multiple_moves_accumulation(self):
        """Test Case 3: Multiple Moves - Employee moves A→B→C to test subaccount accumulation"""
        print(f"\n🧪 TEST CASE 3: Multiple Moves with Subaccount Accumulation (A→B→C→A)")
        
        # Create test employee in department 1
        employee = await self.create_test_employee("fw4abteilung1", "TestMultipleMoves")
        if not employee:
            return {"test": "Multiple moves accumulation", "success": False, "error": "Failed to create test employee"}
        
        employee_id = employee['id']
        
        print(f"   Employee ID: {employee_id}")
        print(f"   Testing: Dept1 → Dept2 → Dept3 → Dept1 (full circle)")
        
        # Set initial balance: €20 breakfast, €10 drinks
        if not await self.set_employee_balance(employee_id, "fw4abteilung1", "breakfast", 20.0):
            return {"test": "Multiple moves accumulation", "success": False, "error": "Failed to set initial breakfast balance"}
        if not await self.set_employee_balance(employee_id, "fw4abteilung1", "drinks", 10.0):
            return {"test": "Multiple moves accumulation", "success": False, "error": "Failed to set initial drinks balance"}
        
        # Track total balance for consistency check
        initial_total = 30.0
        
        # MOVE 1: Dept1 → Dept2
        print(f"   🔄 MOVE 1: fw4abteilung1 → fw4abteilung2")
        move1_response, move1_status = await self.move_employee_to_department(employee_id, "fw4abteilung2")
        if move1_status != 200:
            return {"test": "Multiple moves accumulation", "success": False, "error": f"Move 1 failed: {move1_response}"}
        
        # Add some balance in dept2
        if not await self.set_employee_balance(employee_id, "fw4abteilung2", "breakfast", -5.0):
            return {"test": "Multiple moves accumulation", "success": False, "error": "Failed to set dept2 balance"}
        
        # MOVE 2: Dept2 → Dept3
        print(f"   🔄 MOVE 2: fw4abteilung2 → fw4abteilung3")
        move2_response, move2_status = await self.move_employee_to_department(employee_id, "fw4abteilung3")
        if move2_status != 200:
            return {"test": "Multiple moves accumulation", "success": False, "error": f"Move 2 failed: {move2_response}"}
        
        # Add some balance in dept3
        if not await self.set_employee_balance(employee_id, "fw4abteilung3", "drinks", 7.0):
            return {"test": "Multiple moves accumulation", "success": False, "error": "Failed to set dept3 balance"}
        
        # MOVE 3: Dept3 → Dept1 (back to original)
        print(f"   🔄 MOVE 3: fw4abteilung3 → fw4abteilung1 (back to original)")
        move3_response, move3_status = await self.move_employee_to_department(employee_id, "fw4abteilung1")
        if move3_status != 200:
            return {"test": "Multiple moves accumulation", "success": False, "error": f"Move 3 failed: {move3_response}"}
        
        # Get final balances
        final_balances = await self.get_employee_all_balances(employee_id)
        
        # Calculate total balance across all accounts
        main_total = final_balances['main_balances']['breakfast'] + final_balances['main_balances']['drinks_sweets']
        subaccount_total = 0.0
        
        for dept_id, balances in final_balances['subaccount_balances'].items():
            dept_total = balances.get('breakfast', 0.0) + balances.get('drinks', 0.0)
            subaccount_total += dept_total
            print(f"   Subaccount {dept_id}: Breakfast €{balances.get('breakfast')}, Drinks €{balances.get('drinks')}, Total €{dept_total}")
        
        total_balance = main_total + subaccount_total
        
        print(f"   Main balances total: €{main_total}")
        print(f"   Subaccounts total: €{subaccount_total}")
        print(f"   Grand total: €{total_balance}")
        print(f"   Expected total: €{initial_total + (-5.0) + 7.0}")  # Initial + dept2 change + dept3 change
        
        # Verify balance consistency (allowing for small floating point differences)
        expected_total = initial_total + (-5.0) + 7.0  # 30 - 5 + 7 = 32
        if abs(total_balance - expected_total) > 0.01:
            return {
                "test": "Multiple moves accumulation",
                "success": False,
                "error": f"Balance inconsistency. Expected total: €{expected_total}, Got: €{total_balance}"
            }
        
        # Verify employee is back in original department
        if final_balances['main_department_id'] != 'fw4abteilung1':
            return {
                "test": "Multiple moves accumulation",
                "success": False,
                "error": f"Employee not in expected final department. Expected: fw4abteilung1, Got: {final_balances['main_department_id']}"
            }
        
        # Verify original dept1 balances are now main balances
        expected_main_breakfast = 20.0  # Original dept1 breakfast balance
        expected_main_drinks = 10.0     # Original dept1 drinks balance
        
        if abs(final_balances['main_balances']['breakfast'] - expected_main_breakfast) > 0.01:
            return {
                "test": "Multiple moves accumulation",
                "success": False,
                "error": f"Main breakfast balance incorrect. Expected: €{expected_main_breakfast}, Got: €{final_balances['main_balances']['breakfast']}"
            }
        
        print(f"   ✅ Balance consistency maintained across {3} moves")
        print(f"   ✅ Original department balances restored as main balances")
        
        return {
            "test": "Multiple moves accumulation",
            "success": True,
            "employee_id": employee_id,
            "moves_completed": 3,
            "total_balance_maintained": True,
            "final_total": total_balance,
            "expected_total": expected_total,
            "back_to_original_dept": True
        }
    
    async def test_zero_balance_move(self):
        """Test Case 4: Zero Balance Move - Employee with €0 balances moves departments"""
        print(f"\n🧪 TEST CASE 4: Zero Balance Move")
        
        # Create test employee
        employee = await self.create_test_employee("fw4abteilung3", "TestZeroBalance")
        if not employee:
            return {"test": "Zero balance move", "success": False, "error": "Failed to create test employee"}
        
        employee_id = employee['id']
        target_dept = "fw4abteilung4"
        
        print(f"   Employee ID: {employee_id}")
        print(f"   Testing: Zero balance move fw4abteilung3 → fw4abteilung4")
        
        # Verify initial balances are zero
        initial_balances = await self.get_employee_all_balances(employee_id)
        if not initial_balances:
            return {"test": "Zero balance move", "success": False, "error": "Failed to get initial balances"}
        
        print(f"   Initial breakfast balance: €{initial_balances['main_balances']['breakfast']}")
        print(f"   Initial drinks balance: €{initial_balances['main_balances']['drinks_sweets']}")
        
        if initial_balances['main_balances']['breakfast'] != 0.0 or initial_balances['main_balances']['drinks_sweets'] != 0.0:
            return {"test": "Zero balance move", "success": False, "error": "Initial balances are not zero"}
        
        # Move employee
        move_response, move_status = await self.move_employee_to_department(employee_id, target_dept)
        
        if move_status != 200:
            return {"test": "Zero balance move", "success": False, "error": f"Move failed: {move_response}"}
        
        print(f"   ✅ Move successful: {move_response.get('message')}")
        
        # Verify balance migration response shows zeros
        balance_migration = move_response.get('balance_migration', {})
        old_balances = balance_migration.get('old_main_balances_moved_to_subaccount', {})
        new_balances = balance_migration.get('new_main_balances_from_subaccount', {})
        
        if old_balances.get('breakfast') != 0.0 or old_balances.get('drinks') != 0.0:
            return {
                "test": "Zero balance move",
                "success": False,
                "error": f"Expected zero old balances, got breakfast: {old_balances.get('breakfast')}, drinks: {old_balances.get('drinks')}"
            }
        
        # Get final balances
        final_balances = await self.get_employee_all_balances(employee_id)
        if not final_balances:
            return {"test": "Zero balance move", "success": False, "error": "Failed to get final balances"}
        
        # Verify all balances remain zero
        if final_balances['main_balances']['breakfast'] != 0.0 or final_balances['main_balances']['drinks_sweets'] != 0.0:
            return {
                "test": "Zero balance move",
                "success": False,
                "error": f"Final main balances not zero: breakfast {final_balances['main_balances']['breakfast']}, drinks {final_balances['main_balances']['drinks_sweets']}"
            }
        
        # Verify subaccount for old department shows zeros
        old_dept_subaccount = final_balances['subaccount_balances'].get('fw4abteilung3', {})
        if old_dept_subaccount.get('breakfast') != 0.0 or old_dept_subaccount.get('drinks') != 0.0:
            return {
                "test": "Zero balance move",
                "success": False,
                "error": f"Old dept subaccount not zero: breakfast {old_dept_subaccount.get('breakfast')}, drinks {old_dept_subaccount.get('drinks')}"
            }
        
        print(f"   ✅ All balances remain zero after move")
        print(f"   ✅ Zero balance migration handled correctly")
        
        return {
            "test": "Zero balance move",
            "success": True,
            "employee_id": employee_id,
            "original_department": "fw4abteilung3",
            "target_department": target_dept,
            "all_balances_zero": True
        }
    
    async def test_negative_balance_move(self):
        """Test Case 5: Negative Balance Move - Employee with negative balances moves departments"""
        print(f"\n🧪 TEST CASE 5: Negative Balance Move")
        
        # Create test employee
        employee = await self.create_test_employee("fw4abteilung1", "TestNegativeBalance")
        if not employee:
            return {"test": "Negative balance move", "success": False, "error": "Failed to create test employee"}
        
        employee_id = employee['id']
        target_dept = "fw4abteilung2"
        
        print(f"   Employee ID: {employee_id}")
        print(f"   Testing: Negative balance move fw4abteilung1 → fw4abteilung2")
        
        # Set negative balances: -€25 breakfast, -€15 drinks (employee owes money)
        if not await self.set_employee_balance(employee_id, "fw4abteilung1", "breakfast", -25.0):
            return {"test": "Negative balance move", "success": False, "error": "Failed to set negative breakfast balance"}
        if not await self.set_employee_balance(employee_id, "fw4abteilung1", "drinks", -15.0):
            return {"test": "Negative balance move", "success": False, "error": "Failed to set negative drinks balance"}
        
        # Get initial balances
        initial_balances = await self.get_employee_all_balances(employee_id)
        if not initial_balances:
            return {"test": "Negative balance move", "success": False, "error": "Failed to get initial balances"}
        
        print(f"   Initial breakfast balance: €{initial_balances['main_balances']['breakfast']}")
        print(f"   Initial drinks balance: €{initial_balances['main_balances']['drinks_sweets']}")
        
        # Verify negative balances are set
        if initial_balances['main_balances']['breakfast'] != -25.0 or initial_balances['main_balances']['drinks_sweets'] != -15.0:
            return {"test": "Negative balance move", "success": False, "error": "Failed to set negative balances correctly"}
        
        # Move employee
        move_response, move_status = await self.move_employee_to_department(employee_id, target_dept)
        
        if move_status != 200:
            return {"test": "Negative balance move", "success": False, "error": f"Move failed: {move_response}"}
        
        print(f"   ✅ Move successful: {move_response.get('message')}")
        
        # Verify balance migration response shows negative values
        balance_migration = move_response.get('balance_migration', {})
        old_balances = balance_migration.get('old_main_balances_moved_to_subaccount', {})
        new_balances = balance_migration.get('new_main_balances_from_subaccount', {})
        
        if old_balances.get('breakfast') != -25.0 or old_balances.get('drinks') != -15.0:
            return {
                "test": "Negative balance move",
                "success": False,
                "error": f"Expected negative old balances, got breakfast: {old_balances.get('breakfast')}, drinks: {old_balances.get('drinks')}"
            }
        
        # Get final balances
        final_balances = await self.get_employee_all_balances(employee_id)
        if not final_balances:
            return {"test": "Negative balance move", "success": False, "error": "Failed to get final balances"}
        
        # Verify main balances are now 0 (moved to subaccount)
        if final_balances['main_balances']['breakfast'] != 0.0 or final_balances['main_balances']['drinks_sweets'] != 0.0:
            return {
                "test": "Negative balance move",
                "success": False,
                "error": f"Expected zero main balances, got breakfast: {final_balances['main_balances']['breakfast']}, drinks: {final_balances['main_balances']['drinks_sweets']}"
            }
        
        # Verify old department subaccount has the negative balances
        old_dept_subaccount = final_balances['subaccount_balances'].get('fw4abteilung1', {})
        if old_dept_subaccount.get('breakfast') != -25.0 or old_dept_subaccount.get('drinks') != -15.0:
            return {
                "test": "Negative balance move",
                "success": False,
                "error": f"Old dept subaccount incorrect: breakfast {old_dept_subaccount.get('breakfast')}, drinks {old_dept_subaccount.get('drinks')}"
            }
        
        print(f"   ✅ Negative balances correctly migrated to subaccount")
        print(f"   ✅ Old dept subaccount: Breakfast €{old_dept_subaccount.get('breakfast')}, Drinks €{old_dept_subaccount.get('drinks')}")
        
        # Calculate total debt to verify no money created/lost
        total_debt = old_dept_subaccount.get('breakfast', 0.0) + old_dept_subaccount.get('drinks', 0.0)
        expected_total_debt = -25.0 + (-15.0)  # -40.0
        
        if abs(total_debt - expected_total_debt) > 0.01:
            return {
                "test": "Negative balance move",
                "success": False,
                "error": f"Total debt inconsistency. Expected: €{expected_total_debt}, Got: €{total_debt}"
            }
        
        print(f"   ✅ Total debt preserved: €{total_debt}")
        
        return {
            "test": "Negative balance move",
            "success": True,
            "employee_id": employee_id,
            "original_department": "fw4abteilung1",
            "target_department": target_dept,
            "negative_balances_migrated": True,
            "total_debt_preserved": total_debt
        }
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of Employee Department Moving with Balance Migration"""
        print("🚀 STARTING EMPLOYEE DEPARTMENT MOVING WITH BALANCE MIGRATION TEST")
        print("=" * 80)
        print("TESTING: Employee department moving with proper balance migration logic")
        print("- Endpoint: PUT /api/developer/move-employee/{employee_id}")
        print("- Feature: Balance migration between main and subaccounts")
        print("- Logic: Main balances → subaccount, subaccount → main balances")
        print("=" * 80)
        
        test_results = []
        
        # Test Case 1: Simple Move - Employee with €10 main balance (breakfast) moves A→B
        result_1 = await self.test_simple_balance_migration()
        test_results.append(result_1)
        
        # Test Case 2: Complex Move - Employee with existing subaccount balances moves between departments
        result_2 = await self.test_complex_balance_migration()
        test_results.append(result_2)
        
        # Test Case 3: Multiple Moves - Employee moves A→B→C to test subaccount accumulation
        result_3 = await self.test_multiple_moves_accumulation()
        test_results.append(result_3)
        
        # Test Case 4: Zero Balance Move - Employee with €0 balances moves departments
        result_4 = await self.test_zero_balance_move()
        test_results.append(result_4)
        
        # Test Case 5: Negative Balance Move - Employee with negative balances moves departments
        result_5 = await self.test_negative_balance_move()
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
            print(f"\n🎉 ALL BALANCE MIGRATION TESTS PASSED!")
            print(f"✅ The /api/developer/move-employee/{{employee_id}} endpoint is working correctly")
            print(f"✅ Balance migration logic works properly (main ↔ subaccount)")
            print(f"✅ Main balances correctly become subaccount balances for old department")
            print(f"✅ Subaccount balances correctly become main balances for target department")
            print(f"✅ Complex scenarios with multiple moves work correctly")
            print(f"✅ Balance consistency maintained (no money created/lost)")
            print(f"✅ Zero and negative balance moves handled correctly")
            print(f"✅ Employee department moving with balance migration is FULLY FUNCTIONAL")
        else:
            print(f"\n🚨 CRITICAL BALANCE MIGRATION ISSUES DETECTED!")
            print(f"❌ {len(failed_tests)} test cases failed")
            print(f"❌ This may affect balance integrity during employee moves")
            
            # Identify patterns in failures
            print(f"\n🔍 FAILURE PATTERN ANALYSIS:")
            for result in failed_tests:
                test_name = result['test']
                error = result.get('error', 'Unknown error')
                print(f"   - {test_name}: {error}")
            
            print(f"\n💡 RECOMMENDED FIXES:")
            if any('balance' in result.get('error', '').lower() for result in failed_tests):
                print(f"   1. Check balance migration logic in move-employee endpoint")
            if any('subaccount' in result.get('error', '').lower() for result in failed_tests):
                print(f"   2. Verify subaccount balance initialization and updates")
            if any('inconsistency' in result.get('error', '').lower() for result in failed_tests):
                print(f"   3. Review balance calculation and preservation logic")
            if any('database' in result.get('error', '').lower() for result in failed_tests):
                print(f"   4. Verify database update operations for balance migration")
        
        return successful_tests == total_tests

async def main():
    """Main test execution"""
    async with BalanceMigrationTester() as tester:
        success = await tester.run_comprehensive_test()
        return success

if __name__ == "__main__":
    print("Backend Test Suite: Employee Department Moving with Balance Migration")
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