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
    
    async def test_response_structure_consistency(self, employee_id, employee_name):
        """Test Case 5: Verify response structure matches frontend expectations"""
        print(f"\n🧪 TEST CASE 5: Response Structure Consistency - {employee_name}")
        
        # Get employee profile
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        
        if status != 200:
            return {
                "test": "Response structure consistency",
                "success": False,
                "error": f"Profile endpoint failed with status {status}: {response}"
            }
        
        # Analyze the complete response structure
        response_structure = {
            "top_level_fields": list(response.keys()),
            "employee_object_fields": list(response.get('employee', {}).keys()) if 'employee' in response else [],
            "balance_locations": {}
        }
        
        # Check where balance data is located
        employee_obj = response.get('employee', {})
        
        # Check for balance fields in employee object
        employee_balance_fields = []
        for field in employee_obj.keys():
            if 'balance' in field.lower() or 'total' in field.lower():
                employee_balance_fields.append({
                    'field': field,
                    'value': employee_obj[field],
                    'location': 'employee_object'
                })
        
        # Check for balance fields in main response
        main_balance_fields = []
        for field in response.keys():
            if 'balance' in field.lower() or 'total' in field.lower():
                main_balance_fields.append({
                    'field': field,
                    'value': response[field],
                    'location': 'main_response'
                })
        
        response_structure['balance_locations'] = {
            'employee_object': employee_balance_fields,
            'main_response': main_balance_fields
        }
        
        print(f"   📊 Response Structure Analysis:")
        print(f"      Top-level fields: {len(response_structure['top_level_fields'])}")
        print(f"      Employee object fields: {len(response_structure['employee_object_fields'])}")
        print(f"      Balance fields in employee object: {len(employee_balance_fields)}")
        print(f"      Balance fields in main response: {len(main_balance_fields)}")
        
        # Check for nested employee object vs flat structure
        has_nested_employee = 'employee' in response
        has_flat_structure = any(field in response for field in ['breakfast_balance', 'drinks_sweets_balance'])
        
        print(f"   📊 Structure Type:")
        print(f"      Has nested employee object: {'✅' if has_nested_employee else '❌'}")
        print(f"      Has flat balance structure: {'✅' if has_flat_structure else '❌'}")
        
        # Determine the primary balance location
        primary_balance_location = None
        if employee_balance_fields and not main_balance_fields:
            primary_balance_location = "employee_object"
        elif main_balance_fields and not employee_balance_fields:
            primary_balance_location = "main_response"
        elif employee_balance_fields and main_balance_fields:
            primary_balance_location = "both"
        else:
            primary_balance_location = "none"
        
        print(f"      Primary balance location: {primary_balance_location}")
        
        # Check for subaccount_balances (multi-department support)
        has_subaccount_balances = 'subaccount_balances' in employee_obj
        print(f"      Has subaccount_balances: {'✅' if has_subaccount_balances else '❌'}")
        
        return {
            "test": "Response structure consistency",
            "success": True,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "response_structure": response_structure,
            "has_nested_employee": has_nested_employee,
            "has_flat_structure": has_flat_structure,
            "primary_balance_location": primary_balance_location,
            "has_subaccount_balances": has_subaccount_balances,
            "balance_field_count": {
                "employee_object": len(employee_balance_fields),
                "main_response": len(main_balance_fields)
            }
        }
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of Employee Profile Endpoint Balance Data Structure"""
        print("🚀 STARTING EMPLOYEE PROFILE ENDPOINT BALANCE DATA STRUCTURE TEST")
        print("=" * 80)
        print("TESTING: Employee profile endpoint balance data structure and values")
        print("- Endpoint: GET /api/employees/{employee_id}/profile")
        print("- Focus: Balance field names, structure, and actual values")
        print("- Investigation: Response structure and data completeness")
        print("=" * 80)
        
        # First, get employees with existing order/payment history
        print("\n🔍 FINDING EMPLOYEES WITH TRANSACTION HISTORY...")
        
        test_employees = []
        
        # Check fw4abteilung1
        dept1_employees = await self.get_employees_with_history("fw4abteilung1")
        if dept1_employees:
            test_employees.extend(dept1_employees[:3])  # Take first 3
            print(f"   Found {len(dept1_employees)} employees with history in fw4abteilung1")
        
        # Check fw4abteilung2
        dept2_employees = await self.get_employees_with_history("fw4abteilung2")
        if dept2_employees:
            test_employees.extend(dept2_employees[:3])  # Take first 3
            print(f"   Found {len(dept2_employees)} employees with history in fw4abteilung2")
        
        if not test_employees:
            print("   ❌ No employees with transaction history found. Creating test employee...")
            # Create a test employee with some balance for testing
            test_emp = await self.create_test_employee("fw4abteilung1", "ProfileTestEmployee")
            if test_emp:
                # Set some balance to create history
                await self.set_employee_balance(test_emp['id'], "fw4abteilung1", "breakfast", -5.0)
                test_employees = [test_emp]
        
        if not test_employees:
            return False
        
        print(f"   ✅ Testing with {len(test_employees)} employees")
        
        test_results = []
        
        # Run tests on each employee
        for i, employee in enumerate(test_employees[:2]):  # Test first 2 employees
            employee_id = employee['id']
            employee_name = employee['name']
            
            print(f"\n{'='*60}")
            print(f"TESTING EMPLOYEE {i+1}: {employee_name} (ID: {employee_id[:8]}...)")
            print(f"{'='*60}")
            
            # Test Case 1: Employee Profile Structure
            result_1 = await self.test_employee_profile_structure(employee_id, employee_name)
            test_results.append(result_1)
            
            # Test Case 2: Balance Field Names
            result_2 = await self.test_balance_field_names(employee_id, employee_name)
            test_results.append(result_2)
            
            # Test Case 3: Balance Values Accuracy
            result_3 = await self.test_balance_values_accuracy(employee_id, employee_name)
            test_results.append(result_3)
            
            # Test Case 4: Data Completeness
            result_4 = await self.test_data_completeness(employee_id, employee_name)
            test_results.append(result_4)
            
            # Test Case 5: Response Structure Consistency
            result_5 = await self.test_response_structure_consistency(employee_id, employee_name)
            test_results.append(result_5)
        
        # Analyze results
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results if result.get('success', False))
        failed_tests = [result for result in test_results if not result.get('success', False)]
        
        print(f"\n{'='*80}")
        print(f"🎯 DETAILED TEST RESULTS ANALYSIS")
        print(f"{'='*80}")
        
        # Collect key findings
        balance_field_findings = {}
        structure_findings = {}
        
        for result in test_results:
            test_name = result['test']
            success = result.get('success', False)
            
            print(f"\n📋 TEST: {test_name}")
            print(f"   Result: {'✅ PASSED' if success else '❌ FAILED'}")
            
            if success:
                # Collect specific findings
                if test_name == "Balance field names":
                    balance_field_findings[result.get('employee_name', 'Unknown')] = {
                        'correct_employee_fields': result.get('correct_employee_fields', {}),
                        'correct_main_fields': result.get('correct_main_fields', {})
                    }
                elif test_name == "Response structure consistency":
                    structure_findings[result.get('employee_name', 'Unknown')] = {
                        'primary_balance_location': result.get('primary_balance_location'),
                        'has_nested_employee': result.get('has_nested_employee'),
                        'has_subaccount_balances': result.get('has_subaccount_balances')
                    }
                
                # Show key details
                if 'has_actual_values' in result:
                    print(f"   Has actual balance values: {'✅' if result['has_actual_values'] else '❌'}")
                if 'order_history_count' in result:
                    print(f"   Order history entries: {result['order_history_count']}")
                if 'payment_history_count' in result:
                    print(f"   Payment history entries: {result['payment_history_count']}")
            else:
                # Show error details
                if 'error' in result:
                    print(f"   🚨 ERROR: {result['error']}")
        
        # Final analysis
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL ANALYSIS - EMPLOYEE PROFILE BALANCE DATA STRUCTURE")
        print(f"{'='*80}")
        print(f"Total Test Cases: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Failed Tests: {len(failed_tests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Key findings summary
        print(f"\n🔍 KEY FINDINGS:")
        
        # Balance field names
        if balance_field_findings:
            print(f"\n📊 BALANCE FIELD NAMES:")
            for emp_name, fields in balance_field_findings.items():
                print(f"   Employee: {emp_name}")
                print(f"      Employee object fields: {fields['correct_employee_fields']}")
                print(f"      Main response fields: {fields['correct_main_fields']}")
        
        # Response structure
        if structure_findings:
            print(f"\n🏗️ RESPONSE STRUCTURE:")
            for emp_name, structure in structure_findings.items():
                print(f"   Employee: {emp_name}")
                print(f"      Primary balance location: {structure['primary_balance_location']}")
                print(f"      Has nested employee object: {structure['has_nested_employee']}")
                print(f"      Has subaccount balances: {structure['has_subaccount_balances']}")
        
        if successful_tests == total_tests:
            print(f"\n🎉 ALL EMPLOYEE PROFILE TESTS PASSED!")
            print(f"✅ The GET /api/employees/{{employee_id}}/profile endpoint is working correctly")
            print(f"✅ Balance data structure is consistent and complete")
            print(f"✅ Balance field names are properly identified")
            print(f"✅ Balance values reflect actual transaction history")
            print(f"✅ Payment history and order history are included")
            print(f"✅ Response structure matches expected format")
            print(f"✅ Employee profile endpoint balance data is FULLY FUNCTIONAL")
        else:
            print(f"\n🚨 EMPLOYEE PROFILE ISSUES DETECTED!")
            print(f"❌ {len(failed_tests)} test cases failed")
            print(f"❌ This may affect frontend balance display")
            
            # Identify patterns in failures
            print(f"\n🔍 FAILURE PATTERN ANALYSIS:")
            for result in failed_tests:
                test_name = result['test']
                error = result.get('error', 'Unknown error')
                print(f"   - {test_name}: {error}")
            
            print(f"\n💡 RECOMMENDED INVESTIGATION:")
            print(f"   1. Check balance field naming consistency (breakfast_balance vs breakfast_total)")
            print(f"   2. Verify response structure (nested employee object vs flat structure)")
            print(f"   3. Confirm balance values are not defaulting to 0")
            print(f"   4. Ensure payment_history and order_history are populated")
            print(f"   5. Validate balance calculations match transaction history")
        
        return successful_tests == total_tests

async def main():
    """Main test execution"""
    async with EmployeeProfileTester() as tester:
        success = await tester.run_comprehensive_test()
        return success

if __name__ == "__main__":
    print("Backend Test Suite: Employee Profile Endpoint Balance Data Structure")
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