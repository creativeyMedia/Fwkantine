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
    
    async def test_balance_values_accuracy(self, employee_id, employee_name):
        """Test Case 3: Verify balance values reflect actual transaction history"""
        print(f"\n🧪 TEST CASE 3: Balance Values Accuracy - {employee_name}")
        
        # Get employee profile
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        
        if status != 200:
            return {
                "test": "Balance values accuracy",
                "success": False,
                "error": f"Profile endpoint failed with status {status}: {response}"
            }
        
        employee_obj = response.get('employee', {})
        order_history = response.get('order_history', [])
        payment_history = response.get('payment_history', [])
        
        # Get balance values
        breakfast_balance = employee_obj.get('breakfast_balance', 0)
        drinks_sweets_balance = employee_obj.get('drinks_sweets_balance', 0)
        
        # Analyze order history for balance calculation
        calculated_breakfast_debt = 0.0
        calculated_drinks_debt = 0.0
        
        for order in order_history:
            order_type = order.get('order_type', '')
            total_price = order.get('total_price', 0)
            
            if order_type == 'breakfast':
                calculated_breakfast_debt += total_price
            elif order_type in ['drinks', 'sweets']:
                calculated_drinks_debt += total_price
        
        # Analyze payment history for balance adjustments
        total_breakfast_payments = 0.0
        total_drinks_payments = 0.0
        
        for payment in payment_history:
            payment_type = payment.get('payment_type', '')
            amount = payment.get('amount', 0)
            
            if payment_type == 'breakfast':
                total_breakfast_payments += amount
            elif payment_type in ['drinks_sweets', 'drinks']:
                total_drinks_payments += amount
        
        # Calculate expected balances (payments - orders = balance)
        expected_breakfast = total_breakfast_payments - calculated_breakfast_debt
        expected_drinks = total_drinks_payments - calculated_drinks_debt
        
        print(f"   📊 Balance Analysis:")
        print(f"      Current breakfast_balance: €{breakfast_balance}")
        print(f"      Current drinks_sweets_balance: €{drinks_sweets_balance}")
        print(f"   📊 Transaction History:")
        print(f"      Breakfast orders total: €{calculated_breakfast_debt}")
        print(f"      Drinks/sweets orders total: €{calculated_drinks_debt}")
        print(f"      Breakfast payments total: €{total_breakfast_payments}")
        print(f"      Drinks payments total: €{total_drinks_payments}")
        print(f"   📊 Expected Balances:")
        print(f"      Expected breakfast: €{expected_breakfast}")
        print(f"      Expected drinks: €{expected_drinks}")
        
        # Check if balances are not defaulting to 0
        has_non_zero_balances = (breakfast_balance != 0 or drinks_sweets_balance != 0)
        has_transaction_history = (len(order_history) > 0 or len(payment_history) > 0)
        
        # Check balance accuracy (allowing for small floating point differences)
        breakfast_accurate = abs(breakfast_balance - expected_breakfast) < 0.01
        drinks_accurate = abs(drinks_sweets_balance - expected_drinks) < 0.01
        
        return {
            "test": "Balance values accuracy",
            "success": True,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "current_balances": {
                "breakfast_balance": breakfast_balance,
                "drinks_sweets_balance": drinks_sweets_balance
            },
            "transaction_totals": {
                "breakfast_orders": calculated_breakfast_debt,
                "drinks_orders": calculated_drinks_debt,
                "breakfast_payments": total_breakfast_payments,
                "drinks_payments": total_drinks_payments
            },
            "expected_balances": {
                "breakfast": expected_breakfast,
                "drinks": expected_drinks
            },
            "accuracy_check": {
                "breakfast_accurate": breakfast_accurate,
                "drinks_accurate": drinks_accurate
            },
            "has_non_zero_balances": has_non_zero_balances,
            "has_transaction_history": has_transaction_history,
            "order_count": len(order_history),
            "payment_count": len(payment_history)
        }
    
    async def test_data_completeness(self, employee_id, employee_name):
        """Test Case 4: Verify data completeness - payment_history and order_history"""
        print(f"\n🧪 TEST CASE 4: Data Completeness - {employee_name}")
        
        # Get employee profile
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        
        if status != 200:
            return {
                "test": "Data completeness",
                "success": False,
                "error": f"Profile endpoint failed with status {status}: {response}"
            }
        
        # Check required data fields
        required_data_fields = ['order_history', 'payment_history']
        missing_data = []
        
        for field in required_data_fields:
            if field not in response:
                missing_data.append(field)
        
        if missing_data:
            return {
                "test": "Data completeness",
                "success": False,
                "error": f"Missing required data fields: {missing_data}"
            }
        
        order_history = response.get('order_history', [])
        payment_history = response.get('payment_history', [])
        
        print(f"   📊 Data Completeness Check:")
        print(f"      order_history: {len(order_history)} entries")
        print(f"      payment_history: {len(payment_history)} entries")
        
        # Analyze order history structure
        order_structure_complete = True
        order_sample = None
        
        if order_history:
            order_sample = order_history[0]
            required_order_fields = ['id', 'order_type', 'total_price', 'timestamp']
            missing_order_fields = []
            
            for field in required_order_fields:
                if field not in order_sample:
                    missing_order_fields.append(field)
            
            if missing_order_fields:
                order_structure_complete = False
                print(f"      ❌ Order structure incomplete: missing {missing_order_fields}")
            else:
                print(f"      ✅ Order structure complete")
        
        # Analyze payment history structure
        payment_structure_complete = True
        payment_sample = None
        
        if payment_history:
            payment_sample = payment_history[0]
            required_payment_fields = ['id', 'amount', 'payment_type', 'timestamp']
            missing_payment_fields = []
            
            for field in required_payment_fields:
                if field not in payment_sample:
                    missing_payment_fields.append(field)
            
            if missing_payment_fields:
                payment_structure_complete = False
                print(f"      ❌ Payment structure incomplete: missing {missing_payment_fields}")
            else:
                print(f"      ✅ Payment structure complete")
        
        # Check for readable_items in orders (enriched data)
        has_readable_items = False
        if order_history:
            for order in order_history:
                if 'readable_items' in order and order['readable_items']:
                    has_readable_items = True
                    break
        
        print(f"      {'✅' if has_readable_items else '❌'} Orders have readable_items (enriched data)")
        
        return {
            "test": "Data completeness",
            "success": True,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "data_fields_present": len(missing_data) == 0,
            "order_history_count": len(order_history),
            "payment_history_count": len(payment_history),
            "order_structure_complete": order_structure_complete,
            "payment_structure_complete": payment_structure_complete,
            "has_readable_items": has_readable_items,
            "order_sample": order_sample,
            "payment_sample": payment_sample
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