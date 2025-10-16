#!/usr/bin/env python3
"""
Backend Test Suite for 8H-Service Employee Ordering Fix RE-TEST

CRITICAL TEST: Verify 8H-Service Employee Uses Subaccounts Only

Test Setup:
- Create a NEW 8H-service employee (fresh start, no previous test data)
- Create orders in DIFFERENT departments

Test 1: Create 8H Employee
- POST /api/employees with is_8h_service=true
- Verify is_8h_service=true, main balances=0.0

Test 2: Order in Department 1
- Create a breakfast order for 8H employee in fw4abteilung1
- GET /api/employees/{id}/all-balances
- Verify:
  - ✅ breakfast_balance REMAINS 0.0 (main balance NOT updated)
  - ✅ drinks_sweets_balance REMAINS 0.0 (main balance NOT updated)
  - ✅ subaccount_balances.fw4abteilung1.breakfast is NEGATIVE (subaccount WAS updated)

Test 3: Order in Department 2
- Create a drinks order for same 8H employee in fw4abteilung2
- GET /api/employees/{id}/all-balances again
- Verify:
  - ✅ breakfast_balance STILL 0.0
  - ✅ drinks_sweets_balance STILL 0.0
  - ✅ subaccount_balances.fw4abteilung1.breakfast UNCHANGED (same negative value)
  - ✅ subaccount_balances.fw4abteilung2.drinks is NEGATIVE (drinks order adds to balance)

Test 4: Deletion Protection
- Try DELETE /api/department-admin/employees/{8h_employee_id}
- Verify:
  - ✅ Returns HTTP 400 (deletion blocked)
  - ✅ German error message about outstanding balances
  - ✅ Employee NOT deleted

BACKEND ENDPOINTS TO TEST:
- POST /api/employees (8H-service employee creation)
- POST /api/orders (8H-service employee ordering in different departments)
- GET /api/employees/{employee_id}/all-balances (balance verification)
- DELETE /api/department-admin/employees/{employee_id} (deletion protection)

TEST DEPARTMENTS: fw4abteilung1, fw4abteilung2
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://firebrigade-food.preview.emergentagent.com')
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
    
    async def test_topping_display_fix(self):
        """Test 1: Topping Display Fix - Verify topping names are displayed correctly"""
        print("\n🧪 TEST 1: TOPPING DISPLAY FIX")
        print("=" * 60)
        
        # Create test employee with custom toppings order
        test_employee = await self.create_test_employee("fw4abteilung1", "ToppingTestEmployee")
        if not test_employee:
            return {"test": "Topping Display Fix", "success": False, "error": "Failed to create test employee"}
        
        employee_id = test_employee['id']
        
        # Create a breakfast order with toppings (must match halves count)
        order_data = {
            "employee_id": employee_id,
            "department_id": "fw4abteilung1",
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 2,
                "white_halves": 1,
                "seeded_halves": 1,
                "toppings": ["ruehrei", "kaese"],  # 2 toppings for 2 halves
                "has_lunch": False,
                "boiled_eggs": 0,
                "fried_eggs": 0,
                "has_coffee": False
            }]
        }
        
        # Create the order
        order_response, order_status = await self.make_request('POST', '/orders', order_data)
        if order_status != 200:
            return {"test": "Topping Display Fix", "success": False, "error": f"Failed to create order: {order_response}"}
        
        print(f"   ✅ Created test order with toppings: ruehrei, kaese")
        
        # Get employee profile to check topping display
        profile_response, profile_status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        if profile_status != 200:
            return {"test": "Topping Display Fix", "success": False, "error": f"Failed to get profile: {profile_response}"}
        
        # Check readable_items in order history
        order_history = profile_response.get('order_history', [])
        if not order_history:
            return {"test": "Topping Display Fix", "success": False, "error": "No order history found"}
        
        latest_order = order_history[0]  # Most recent order
        readable_items = latest_order.get('readable_items', [])
        
        print(f"   📊 Readable items found: {readable_items}")
        
        # Check if topping names are properly capitalized and not IDs
        topping_names_correct = True
        topping_issues = []
        
        for item in readable_items:
            # Convert item to string for checking
            item_str = str(item)
            toppings_field = item.get('toppings', '') if isinstance(item, dict) else ''
            
            # Check if toppings are properly converted from IDs to readable names
            if 'ruehrei' in item_str.lower():
                if 'Ruehrei' not in toppings_field and 'Rührei' not in toppings_field:
                    topping_names_correct = False
                    topping_issues.append(f"'ruehrei' not properly converted in: {item}")
            
            if 'kaese' in item_str.lower():
                if 'Kaese' not in toppings_field and 'Käse' not in toppings_field:
                    topping_names_correct = False
                    topping_issues.append(f"'kaese' not properly converted in: {item}")
            
            # Check if we have proper capitalized topping names
            if isinstance(item, dict) and 'toppings' in item:
                toppings = item['toppings']
                if 'Ruehrei' in toppings or 'Rührei' in toppings:
                    print(f"   ✅ Found properly formatted 'Rührei' topping")
                if 'Kaese' in toppings or 'Käse' in toppings:
                    print(f"   ✅ Found properly formatted 'Käse' topping")
        
        if topping_names_correct and not topping_issues:
            print(f"   ✅ Topping names are displayed correctly (capitalized, not as IDs)")
        else:
            print(f"   ❌ Topping display issues found: {topping_issues}")
        
        return {
            "test": "Topping Display Fix",
            "success": topping_names_correct,
            "employee_id": employee_id,
            "readable_items": readable_items,
            "topping_issues": topping_issues,
            "order_created": True
        }
    
    async def test_8h_service_employee_creation(self):
        """Test 2: 8H-Service Employee Creation"""
        print("\n🧪 TEST 2: 8H-SERVICE EMPLOYEE CREATION")
        print("=" * 60)
        
        # Create 8H-service employee
        employee_data = {
            "name": "8H_Service_TestEmployee",
            "department_id": "fw4abteilung1",
            "is_8h_service": True
        }
        
        response, status = await self.make_request('POST', '/employees', employee_data)
        if status != 200:
            return {"test": "8H-Service Employee Creation", "success": False, "error": f"Failed to create employee: {response}"}
        
        employee_id = response['id']
        print(f"   ✅ Created 8H-service employee: {employee_id[:8]}...")
        
        # Verify employee properties
        expected_properties = {
            "is_8h_service": True,
            "breakfast_balance": 0.0,
            "drinks_sweets_balance": 0.0
        }
        
        verification_issues = []
        for prop, expected_value in expected_properties.items():
            actual_value = response.get(prop)
            if actual_value != expected_value:
                verification_issues.append(f"{prop}: expected {expected_value}, got {actual_value}")
            else:
                print(f"   ✅ {prop} = {actual_value}")
        
        # Check subaccount balances initialization
        subaccount_balances = response.get('subaccount_balances', {})
        if not subaccount_balances:
            verification_issues.append("subaccount_balances not initialized")
        else:
            # Check all 4 departments have 0.0 balances
            expected_departments = ["fw4abteilung1", "fw4abteilung2", "fw4abteilung3", "fw4abteilung4"]
            for dept in expected_departments:
                if dept not in subaccount_balances:
                    verification_issues.append(f"Missing subaccount for {dept}")
                else:
                    dept_balances = subaccount_balances[dept]
                    if dept_balances.get('breakfast', -1) != 0.0 or dept_balances.get('drinks', -1) != 0.0:
                        verification_issues.append(f"{dept} subaccount not initialized to 0.0: {dept_balances}")
                    else:
                        print(f"   ✅ {dept} subaccount balances initialized to 0.0")
        
        success = len(verification_issues) == 0
        if success:
            print(f"   ✅ All 8H-service employee properties verified correctly")
        else:
            print(f"   ❌ Verification issues: {verification_issues}")
        
        return {
            "test": "8H-Service Employee Creation",
            "success": success,
            "employee_id": employee_id,
            "verification_issues": verification_issues,
            "created_employee": response
        }
    
    async def test_8h_service_employee_listing(self):
        """Test 3: 8H-Service Employee Listing"""
        print("\n🧪 TEST 3: 8H-SERVICE EMPLOYEE LISTING")
        print("=" * 60)
        
        # First create a few 8H-service employees in different departments
        test_employees = []
        
        for i, dept_id in enumerate(["fw4abteilung1", "fw4abteilung2"]):
            employee_data = {
                "name": f"8H_ListTest_{i+1}",
                "department_id": dept_id,
                "is_8h_service": True
            }
            
            response, status = await self.make_request('POST', '/employees', employee_data)
            if status == 200:
                test_employees.append((response, dept_id))
                print(f"   ✅ Created 8H-service employee in {dept_id}")
        
        if not test_employees:
            return {"test": "8H-Service Employee Listing", "success": False, "error": "Failed to create test employees"}
        
        # Test the 8H-service employee listing endpoint for each department
        listing_results = {}
        
        for dept_id in ["fw4abteilung1", "fw4abteilung2"]:
            response, status = await self.make_request('GET', f'/departments/{dept_id}/8h-employees')
            
            if status != 200:
                listing_results[dept_id] = {"success": False, "error": f"Endpoint failed: {response}"}
                continue
            
            # Verify response structure and content
            if not isinstance(response, list):
                listing_results[dept_id] = {"success": False, "error": "Response is not a list"}
                continue
            
            # Check if our test employees are in the list
            found_8h_employees = []
            for emp in response:
                if emp.get('is_8h_service') == True:
                    found_8h_employees.append(emp)
            
            # Verify subaccount balance is included for the requested department
            subaccount_balance_included = True
            for emp in found_8h_employees:
                subaccount_balances = emp.get('subaccount_balances', {})
                if dept_id not in subaccount_balances:
                    subaccount_balance_included = False
                    break
            
            listing_results[dept_id] = {
                "success": True,
                "total_employees": len(response),
                "8h_service_employees": len(found_8h_employees),
                "subaccount_balance_included": subaccount_balance_included,
                "employees": found_8h_employees
            }
            
            print(f"   ✅ {dept_id}: Found {len(found_8h_employees)} 8H-service employees")
            print(f"   ✅ {dept_id}: Subaccount balance included: {subaccount_balance_included}")
        
        # Overall success check
        all_success = all(result.get("success", False) for result in listing_results.values())
        
        return {
            "test": "8H-Service Employee Listing",
            "success": all_success,
            "listing_results": listing_results,
            "test_employees_created": len(test_employees)
        }
    
    async def test_8h_service_employee_ordering_workflow(self):
        """Test 2.3 & 2.4: 8H-Service Employee Ordering Workflow"""
        print("\n🧪 TEST 2.3 & 2.4: 8H-SERVICE EMPLOYEE ORDERING WORKFLOW")
        print("=" * 60)
        
        # Create 8H-service employee
        employee_data = {
            "name": "Test 8H Mitarbeiter",
            "department_id": "fw4abteilung1",
            "is_8h_service": True
        }
        
        emp_response, emp_status = await self.make_request('POST', '/employees', employee_data)
        if emp_status != 200:
            return {"test": "8H-Service Employee Ordering Workflow", "success": False, "error": f"Failed to create employee: {emp_response}"}
        
        employee_id = emp_response['id']
        print(f"   ✅ Created 8H-service employee: {employee_id[:8]}...")
        
        # Verify initial properties
        expected_properties = {
            "is_8h_service": True,
            "breakfast_balance": 0.0,
            "drinks_sweets_balance": 0.0
        }
        
        verification_issues = []
        for prop, expected_value in expected_properties.items():
            actual_value = emp_response.get(prop)
            if actual_value != expected_value:
                verification_issues.append(f"{prop}: expected {expected_value}, got {actual_value}")
            else:
                print(f"   ✅ {prop} = {actual_value}")
        
        if verification_issues:
            return {"test": "8H-Service Employee Ordering Workflow", "success": False, "error": f"Property verification failed: {verification_issues}"}
        
        # Get initial balances
        initial_balances = await self.get_employee_all_balances(employee_id)
        if not initial_balances:
            return {"test": "8H-Service Employee Ordering Workflow", "success": False, "error": "Failed to get initial balances"}
        
        print(f"   📊 Initial main balances: breakfast={initial_balances['main_balances']['breakfast']}, drinks={initial_balances['main_balances']['drinks_sweets']}")
        
        # Test 2.3: Create breakfast order for 8H employee in Department 1
        print(f"\n   🔸 Test 2.3: Order for 8H Employee in Department 1")
        
        order_data_dept1 = {
            "employee_id": employee_id,
            "department_id": "fw4abteilung1",
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 2,
                "white_halves": 1,
                "seeded_halves": 1,
                "toppings": ["ruehrei", "kaese"],  # 2 toppings for 2 halves
                "has_lunch": False,
                "boiled_eggs": 0,
                "fried_eggs": 0,
                "has_coffee": True
            }]
        }
        
        order_response_dept1, order_status_dept1 = await self.make_request('POST', '/orders', order_data_dept1)
        if order_status_dept1 != 200:
            return {"test": "8H-Service Employee Ordering Workflow", "success": False, "error": f"Failed to create order in dept1: {order_response_dept1}"}
        
        print(f"   ✅ Created breakfast order in fw4abteilung1")
        
        # Get balances after dept1 order
        balances_after_dept1 = await self.get_employee_all_balances(employee_id)
        if not balances_after_dept1:
            return {"test": "8H-Service Employee Ordering Workflow", "success": False, "error": "Failed to get balances after dept1 order"}
        
        # Verify main balances STILL 0.0
        main_balances_still_zero_dept1 = (
            balances_after_dept1['main_balances']['breakfast'] == 0.0 and
            balances_after_dept1['main_balances']['drinks_sweets'] == 0.0
        )
        
        # Verify subaccount for fw4abteilung1 updated (negative)
        fw1_subaccount_after = balances_after_dept1['subaccount_balances']['fw4abteilung1']
        fw1_subaccount_updated = (fw1_subaccount_after['breakfast'] < 0 or fw1_subaccount_after['drinks'] < 0)
        
        print(f"   📊 After dept1 order - Main balances still 0.0: {main_balances_still_zero_dept1}")
        print(f"   📊 fw4abteilung1 subaccount: {fw1_subaccount_after}")
        print(f"   📊 fw4abteilung1 subaccount updated (negative): {fw1_subaccount_updated}")
        
        # Test 2.4: Create drinks order for 8H employee in Department 2
        print(f"\n   🔸 Test 2.4: Order for 8H Employee in Department 2")
        
        order_data_dept2 = {
            "employee_id": employee_id,
            "department_id": "fw4abteilung2",
            "order_type": "drinks",
            "drink_items": {"cola_id": 2}  # Assuming cola exists in menu
        }
        
        order_response_dept2, order_status_dept2 = await self.make_request('POST', '/orders', order_data_dept2)
        if order_status_dept2 != 200:
            return {"test": "8H-Service Employee Ordering Workflow", "success": False, "error": f"Failed to create order in dept2: {order_response_dept2}"}
        
        print(f"   ✅ Created drinks order in fw4abteilung2")
        
        # Get final balances
        final_balances = await self.get_employee_all_balances(employee_id)
        if not final_balances:
            return {"test": "8H-Service Employee Ordering Workflow", "success": False, "error": "Failed to get final balances"}
        
        # Verify main balances STILL 0.0
        main_balances_still_zero_final = (
            final_balances['main_balances']['breakfast'] == 0.0 and
            final_balances['main_balances']['drinks_sweets'] == 0.0
        )
        
        # Verify subaccount balances
        fw1_subaccount_final = final_balances['subaccount_balances']['fw4abteilung1']
        fw2_subaccount_final = final_balances['subaccount_balances']['fw4abteilung2']
        
        # fw4abteilung1 should be unchanged from dept1 order
        fw1_unchanged = (fw1_subaccount_final == fw1_subaccount_after)
        
        # fw4abteilung2 should be updated (negative) from dept2 order
        fw2_updated = (fw2_subaccount_final['drinks'] < 0)
        
        print(f"   📊 Final main balances still 0.0: {main_balances_still_zero_final}")
        print(f"   📊 fw4abteilung1 subaccount unchanged: {fw1_unchanged}")
        print(f"   📊 fw4abteilung2 subaccount: {fw2_subaccount_final}")
        print(f"   📊 fw4abteilung2 subaccount updated (negative): {fw2_updated}")
        
        success = (main_balances_still_zero_dept1 and main_balances_still_zero_final and 
                  fw1_subaccount_updated and fw1_unchanged and fw2_updated)
        
        if success:
            print(f"   ✅ All tests passed - 8H-service employee ordering workflow working correctly")
        else:
            print(f"   ❌ Some tests failed:")
            print(f"      Main balances 0.0 after dept1: {main_balances_still_zero_dept1}")
            print(f"      Main balances 0.0 final: {main_balances_still_zero_final}")
            print(f"      fw4abteilung1 updated: {fw1_subaccount_updated}")
            print(f"      fw4abteilung1 unchanged after dept2: {fw1_unchanged}")
            print(f"      fw4abteilung2 updated: {fw2_updated}")
        
        return {
            "test": "8H-Service Employee Ordering Workflow",
            "success": success,
            "employee_id": employee_id,
            "main_balances_zero_dept1": main_balances_still_zero_dept1,
            "main_balances_zero_final": main_balances_still_zero_final,
            "fw1_subaccount_updated": fw1_subaccount_updated,
            "fw1_unchanged_after_dept2": fw1_unchanged,
            "fw2_updated": fw2_updated,
            "initial_balances": initial_balances,
            "balances_after_dept1": balances_after_dept1,
            "final_balances": final_balances
        }
    
    async def test_8h_service_employee_deletion_protection(self):
        """Test 5: 8H-Service Employee Deletion Protection"""
        print("\n🧪 TEST 5: 8H-SERVICE EMPLOYEE DELETION PROTECTION")
        print("=" * 60)
        
        # Test Case A: Employee with non-zero subaccount balance (should be protected)
        print("\n   🔸 Test Case A: Deletion protection with non-zero balance")
        
        # Create 8H-service employee
        employee_data = {
            "name": "8H_DeleteProtectionTest",
            "department_id": "fw4abteilung1", 
            "is_8h_service": True
        }
        
        emp_response, emp_status = await self.make_request('POST', '/employees', employee_data)
        if emp_status != 200:
            return {"test": "8H-Service Employee Deletion Protection", "success": False, "error": f"Failed to create employee: {emp_response}"}
        
        employee_id_protected = emp_response['id']
        
        # Create an order to give non-zero balance
        order_data = {
            "employee_id": employee_id_protected,
            "department_id": "fw4abteilung1",
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 2,
                "white_halves": 1,
                "seeded_halves": 1,
                "toppings": ["ruehrei", "kaese"],  # 2 toppings for 2 halves
                "has_lunch": False,
                "boiled_eggs": 0,
                "fried_eggs": 0,
                "has_coffee": True
            }]
        }
        
        order_response, order_status = await self.make_request('POST', '/orders', order_data)
        if order_status != 200:
            return {"test": "8H-Service Employee Deletion Protection", "success": False, "error": f"Failed to create order: {order_response}"}
        
        print(f"   ✅ Created order to establish non-zero balance")
        
        # Try to delete employee (should fail with 400 error)
        delete_response, delete_status = await self.make_request('DELETE', f'/department-admin/employees/{employee_id_protected}')
        
        deletion_protected = delete_status == 400
        german_error_message = False
        
        if deletion_protected and isinstance(delete_response, dict):
            error_detail = delete_response.get('detail', '')
            # Check for German error message
            german_error_message = any(word in error_detail.lower() for word in ['saldo', 'balance', 'nicht', 'löschen'])
        
        print(f"   {'✅' if deletion_protected else '❌'} Deletion protection active (HTTP {delete_status})")
        print(f"   {'✅' if german_error_message else '❌'} German error message present")
        if delete_response and isinstance(delete_response, dict):
            print(f"   📝 Error message: {delete_response.get('detail', 'No detail')}")
        
        # Test Case B: Employee with zero subaccount balances (should allow deletion)
        print("\n   🔸 Test Case B: Deletion allowed with zero balances")
        
        # Create another 8H-service employee
        employee_data_zero = {
            "name": "8H_DeleteAllowedTest",
            "department_id": "fw4abteilung2",
            "is_8h_service": True
        }
        
        emp_response_zero, emp_status_zero = await self.make_request('POST', '/employees', employee_data_zero)
        if emp_status_zero != 200:
            return {"test": "8H-Service Employee Deletion Protection", "success": False, "error": f"Failed to create second employee: {emp_response_zero}"}
        
        employee_id_zero = emp_response_zero['id']
        
        # Verify all subaccounts are at 0€ (should be by default)
        balances = await self.get_employee_all_balances(employee_id_zero)
        all_zero = True
        if balances:
            for dept_id, dept_balances in balances['subaccount_balances'].items():
                if dept_balances['breakfast'] != 0.0 or dept_balances['drinks'] != 0.0:
                    all_zero = False
                    break
        
        print(f"   📊 All subaccount balances at 0€: {all_zero}")
        
        # Try to delete employee (should succeed)
        delete_response_zero, delete_status_zero = await self.make_request('DELETE', f'/department-admin/employees/{employee_id_zero}')
        
        deletion_allowed = delete_status_zero == 200
        print(f"   {'✅' if deletion_allowed else '❌'} Deletion allowed for zero balance (HTTP {delete_status_zero})")
        
        success = deletion_protected and german_error_message and deletion_allowed and all_zero
        
        return {
            "test": "8H-Service Employee Deletion Protection",
            "success": success,
            "test_case_a": {
                "employee_id": employee_id_protected,
                "deletion_protected": deletion_protected,
                "german_error_message": german_error_message,
                "delete_status": delete_status,
                "delete_response": delete_response
            },
            "test_case_b": {
                "employee_id": employee_id_zero,
                "all_balances_zero": all_zero,
                "deletion_allowed": deletion_allowed,
                "delete_status": delete_status_zero,
                "delete_response": delete_response_zero
            }
        }

    async def test_8h_service_employee_creation_critical(self):
        """Test 1: Create 8H Employee - Critical Test"""
        print("\n🧪 TEST 1: CREATE 8H EMPLOYEE")
        print("=" * 60)
        
        # Create a NEW 8H-service employee (fresh start)
        employee_data = {
            "name": "Test 8H Final",
            "department_id": "fw4abteilung1",
            "is_8h_service": True
        }
        
        print(f"   📝 Creating 8H-service employee: {employee_data}")
        
        response, status = await self.make_request('POST', '/employees', employee_data)
        if status != 200:
            return {
                "test": "Create 8H Employee",
                "success": False,
                "error": f"Failed to create employee: {response}",
                "employee_id": None
            }
        
        employee_id = response['id']
        print(f"   ✅ Created 8H-service employee: {employee_id[:8]}...")
        
        # Verify critical properties
        verification_results = {}
        
        # Check is_8h_service=true
        is_8h_service = response.get('is_8h_service')
        verification_results['is_8h_service'] = is_8h_service == True
        print(f"   {'✅' if verification_results['is_8h_service'] else '❌'} is_8h_service = {is_8h_service} (expected: True)")
        
        # Check main balances=0.0
        breakfast_balance = response.get('breakfast_balance')
        drinks_balance = response.get('drinks_sweets_balance')
        verification_results['main_balances_zero'] = (breakfast_balance == 0.0 and drinks_balance == 0.0)
        print(f"   {'✅' if verification_results['main_balances_zero'] else '❌'} Main balances = breakfast:{breakfast_balance}, drinks:{drinks_balance} (expected: 0.0, 0.0)")
        
        # Check subaccount initialization
        subaccount_balances = response.get('subaccount_balances', {})
        subaccounts_initialized = True
        expected_departments = ["fw4abteilung1", "fw4abteilung2", "fw4abteilung3", "fw4abteilung4"]
        
        for dept in expected_departments:
            if dept not in subaccount_balances:
                subaccounts_initialized = False
                break
            dept_balances = subaccount_balances[dept]
            if dept_balances.get('breakfast', -1) != 0.0 or dept_balances.get('drinks', -1) != 0.0:
                subaccounts_initialized = False
                break
        
        verification_results['subaccounts_initialized'] = subaccounts_initialized
        print(f"   {'✅' if verification_results['subaccounts_initialized'] else '❌'} All subaccount balances initialized to 0.0")
        
        success = all(verification_results.values())
        
        if success:
            print(f"   🎉 TEST 1 PASSED: 8H Employee created with correct properties")
        else:
            print(f"   ❌ TEST 1 FAILED: Property verification issues")
            for prop, result in verification_results.items():
                if not result:
                    print(f"      - {prop}: FAILED")
        
        return {
            "test": "Create 8H Employee",
            "success": success,
            "employee_id": employee_id,
            "verification_results": verification_results,
            "created_employee": response
        }

    async def test_8h_service_order_department_1(self):
        """Test 2: Order in Department 1 - Critical Test"""
        print("\n🧪 TEST 2: ORDER IN DEPARTMENT 1")
        print("=" * 60)
        
        # First create the 8H employee if not already done
        employee_data = {
            "name": "Test 8H Final",
            "department_id": "fw4abteilung1", 
            "is_8h_service": True
        }
        
        emp_response, emp_status = await self.make_request('POST', '/employees', employee_data)
        if emp_status != 200:
            return {
                "test": "Order in Department 1",
                "success": False,
                "error": f"Failed to create employee: {emp_response}",
                "employee_id": None
            }
        
        employee_id = emp_response['id']
        print(f"   📝 Using 8H employee: {employee_id[:8]}...")
        
        # Get initial balances
        initial_balances = await self.get_employee_all_balances(employee_id)
        if not initial_balances:
            return {
                "test": "Order in Department 1",
                "success": False,
                "error": "Failed to get initial balances",
                "employee_id": employee_id
            }
        
        print(f"   📊 Initial main balances:")
        print(f"      breakfast_balance: {initial_balances['main_balances']['breakfast']}")
        print(f"      drinks_sweets_balance: {initial_balances['main_balances']['drinks_sweets']}")
        print(f"   📊 Initial fw4abteilung1 subaccount:")
        print(f"      breakfast: {initial_balances['subaccount_balances']['fw4abteilung1']['breakfast']}")
        print(f"      drinks: {initial_balances['subaccount_balances']['fw4abteilung1']['drinks']}")
        
        # Create breakfast order in fw4abteilung1
        order_data = {
            "employee_id": employee_id,
            "department_id": "fw4abteilung1",
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 2,
                "white_halves": 1,
                "seeded_halves": 1,
                "toppings": ["ruehrei", "kaese"],
                "has_lunch": False,
                "boiled_eggs": 0,
                "fried_eggs": 0,
                "has_coffee": True
            }]
        }
        
        print(f"   📝 Creating breakfast order in fw4abteilung1...")
        
        order_response, order_status = await self.make_request('POST', '/orders', order_data)
        if order_status != 200:
            return {
                "test": "Order in Department 1",
                "success": False,
                "error": f"Failed to create order: {order_response}",
                "employee_id": employee_id
            }
        
        print(f"   ✅ Created breakfast order: {order_response.get('id', 'unknown')[:8]}...")
        
        # Get balances after order
        after_balances = await self.get_employee_all_balances(employee_id)
        if not after_balances:
            return {
                "test": "Order in Department 1",
                "success": False,
                "error": "Failed to get balances after order",
                "employee_id": employee_id
            }
        
        print(f"   📊 After order main balances:")
        print(f"      breakfast_balance: {after_balances['main_balances']['breakfast']}")
        print(f"      drinks_sweets_balance: {after_balances['main_balances']['drinks_sweets']}")
        print(f"   📊 After order fw4abteilung1 subaccount:")
        print(f"      breakfast: {after_balances['subaccount_balances']['fw4abteilung1']['breakfast']}")
        print(f"      drinks: {after_balances['subaccount_balances']['fw4abteilung1']['drinks']}")
        
        # Verify critical requirements
        verification_results = {}
        
        # ✅ breakfast_balance REMAINS 0.0 (main balance NOT updated)
        breakfast_remains_zero = after_balances['main_balances']['breakfast'] == 0.0
        verification_results['breakfast_balance_remains_zero'] = breakfast_remains_zero
        print(f"   {'✅' if breakfast_remains_zero else '❌'} breakfast_balance REMAINS 0.0: {after_balances['main_balances']['breakfast']}")
        
        # ✅ drinks_sweets_balance REMAINS 0.0 (main balance NOT updated)
        drinks_remains_zero = after_balances['main_balances']['drinks_sweets'] == 0.0
        verification_results['drinks_balance_remains_zero'] = drinks_remains_zero
        print(f"   {'✅' if drinks_remains_zero else '❌'} drinks_sweets_balance REMAINS 0.0: {after_balances['main_balances']['drinks_sweets']}")
        
        # ✅ subaccount_balances.fw4abteilung1.breakfast is NEGATIVE (subaccount WAS updated)
        fw1_breakfast_negative = after_balances['subaccount_balances']['fw4abteilung1']['breakfast'] < 0
        verification_results['fw1_breakfast_negative'] = fw1_breakfast_negative
        print(f"   {'✅' if fw1_breakfast_negative else '❌'} fw4abteilung1.breakfast is NEGATIVE: {after_balances['subaccount_balances']['fw4abteilung1']['breakfast']}")
        
        success = all(verification_results.values())
        
        if success:
            print(f"   🎉 TEST 2 PASSED: Order in Department 1 - Main balances remain 0.0, subaccount updated")
        else:
            print(f"   ❌ TEST 2 FAILED: Critical requirements not met")
            for req, result in verification_results.items():
                if not result:
                    print(f"      - {req}: FAILED")
        
        return {
            "test": "Order in Department 1",
            "success": success,
            "employee_id": employee_id,
            "verification_results": verification_results,
            "initial_balances": initial_balances,
            "after_balances": after_balances,
            "order_id": order_response.get('id')
        }

    async def test_8h_service_order_department_2(self, employee_id):
        """Test 3: Order in Department 2 - Critical Test"""
        print("\n🧪 TEST 3: ORDER IN DEPARTMENT 2")
        print("=" * 60)
        
        if not employee_id:
            return {
                "test": "Order in Department 2",
                "success": False,
                "error": "No employee_id provided from previous test",
                "employee_id": None
            }
        
        print(f"   📝 Using 8H employee: {employee_id[:8]}...")
        
        # Get balances before department 2 order
        before_balances = await self.get_employee_all_balances(employee_id)
        if not before_balances:
            return {
                "test": "Order in Department 2",
                "success": False,
                "error": "Failed to get balances before order",
                "employee_id": employee_id
            }
        
        print(f"   📊 Before dept2 order main balances:")
        print(f"      breakfast_balance: {before_balances['main_balances']['breakfast']}")
        print(f"      drinks_sweets_balance: {before_balances['main_balances']['drinks_sweets']}")
        print(f"   📊 Before dept2 order subaccounts:")
        print(f"      fw4abteilung1.breakfast: {before_balances['subaccount_balances']['fw4abteilung1']['breakfast']}")
        print(f"      fw4abteilung2.drinks: {before_balances['subaccount_balances']['fw4abteilung2']['drinks']}")
        
        # Get menu items for fw4abteilung2 to create valid drinks order
        drinks_menu, menu_status = await self.make_request('GET', '/menu/drinks/fw4abteilung2')
        if menu_status != 200 or not drinks_menu:
            # Fallback: create order with generic drink item structure
            drink_items = {"cola": 1}  # Generic structure
        else:
            # Use first available drink
            first_drink = drinks_menu[0] if drinks_menu else None
            if first_drink:
                drink_items = {first_drink['id']: 1}
            else:
                drink_items = {"cola": 1}  # Fallback
        
        # Create drinks order in fw4abteilung2
        order_data = {
            "employee_id": employee_id,
            "department_id": "fw4abteilung2",
            "order_type": "drinks",
            "drink_items": drink_items
        }
        
        print(f"   📝 Creating drinks order in fw4abteilung2...")
        
        order_response, order_status = await self.make_request('POST', '/orders', order_data)
        if order_status != 200:
            return {
                "test": "Order in Department 2",
                "success": False,
                "error": f"Failed to create order: {order_response}",
                "employee_id": employee_id
            }
        
        print(f"   ✅ Created drinks order: {order_response.get('id', 'unknown')[:8]}...")
        
        # Get balances after department 2 order
        after_balances = await self.get_employee_all_balances(employee_id)
        if not after_balances:
            return {
                "test": "Order in Department 2",
                "success": False,
                "error": "Failed to get balances after order",
                "employee_id": employee_id
            }
        
        print(f"   📊 After dept2 order main balances:")
        print(f"      breakfast_balance: {after_balances['main_balances']['breakfast']}")
        print(f"      drinks_sweets_balance: {after_balances['main_balances']['drinks_sweets']}")
        print(f"   📊 After dept2 order subaccounts:")
        print(f"      fw4abteilung1.breakfast: {after_balances['subaccount_balances']['fw4abteilung1']['breakfast']}")
        print(f"      fw4abteilung2.drinks: {after_balances['subaccount_balances']['fw4abteilung2']['drinks']}")
        
        # Verify critical requirements
        verification_results = {}
        
        # ✅ breakfast_balance STILL 0.0
        breakfast_still_zero = after_balances['main_balances']['breakfast'] == 0.0
        verification_results['breakfast_balance_still_zero'] = breakfast_still_zero
        print(f"   {'✅' if breakfast_still_zero else '❌'} breakfast_balance STILL 0.0: {after_balances['main_balances']['breakfast']}")
        
        # ✅ drinks_sweets_balance STILL 0.0
        drinks_still_zero = after_balances['main_balances']['drinks_sweets'] == 0.0
        verification_results['drinks_balance_still_zero'] = drinks_still_zero
        print(f"   {'✅' if drinks_still_zero else '❌'} drinks_sweets_balance STILL 0.0: {after_balances['main_balances']['drinks_sweets']}")
        
        # ✅ subaccount_balances.fw4abteilung1.breakfast UNCHANGED (same negative value)
        fw1_breakfast_unchanged = (before_balances['subaccount_balances']['fw4abteilung1']['breakfast'] == 
                                  after_balances['subaccount_balances']['fw4abteilung1']['breakfast'])
        verification_results['fw1_breakfast_unchanged'] = fw1_breakfast_unchanged
        print(f"   {'✅' if fw1_breakfast_unchanged else '❌'} fw4abteilung1.breakfast UNCHANGED: {after_balances['subaccount_balances']['fw4abteilung1']['breakfast']}")
        
        # ✅ subaccount_balances.fw4abteilung2.drinks is NEGATIVE (drinks order adds to balance)
        fw2_drinks_negative = after_balances['subaccount_balances']['fw4abteilung2']['drinks'] < 0
        verification_results['fw2_drinks_negative'] = fw2_drinks_negative
        print(f"   {'✅' if fw2_drinks_negative else '❌'} fw4abteilung2.drinks is NEGATIVE: {after_balances['subaccount_balances']['fw4abteilung2']['drinks']}")
        
        success = all(verification_results.values())
        
        if success:
            print(f"   🎉 TEST 3 PASSED: Order in Department 2 - Main balances still 0.0, different subaccount updated")
        else:
            print(f"   ❌ TEST 3 FAILED: Critical requirements not met")
            for req, result in verification_results.items():
                if not result:
                    print(f"      - {req}: FAILED")
        
        return {
            "test": "Order in Department 2",
            "success": success,
            "employee_id": employee_id,
            "verification_results": verification_results,
            "before_balances": before_balances,
            "after_balances": after_balances,
            "order_id": order_response.get('id')
        }

    async def test_8h_service_deletion_protection_critical(self, employee_id):
        """Test 4: Deletion Protection - Critical Test"""
        print("\n🧪 TEST 4: DELETION PROTECTION")
        print("=" * 60)
        
        if not employee_id:
            return {
                "test": "Deletion Protection",
                "success": False,
                "error": "No employee_id provided from previous test",
                "employee_id": None
            }
        
        print(f"   📝 Testing deletion protection for 8H employee: {employee_id[:8]}...")
        
        # Get current balances to verify non-zero state
        current_balances = await self.get_employee_all_balances(employee_id)
        if not current_balances:
            return {
                "test": "Deletion Protection",
                "success": False,
                "error": "Failed to get current balances",
                "employee_id": employee_id
            }
        
        # Check if employee has outstanding balances in any subaccount
        has_outstanding_balances = False
        outstanding_details = []
        
        for dept_id, dept_balances in current_balances['subaccount_balances'].items():
            breakfast_balance = dept_balances.get('breakfast', 0.0)
            drinks_balance = dept_balances.get('drinks', 0.0)
            
            if breakfast_balance != 0.0 or drinks_balance != 0.0:
                has_outstanding_balances = True
                outstanding_details.append(f"{dept_id}: breakfast={breakfast_balance}, drinks={drinks_balance}")
        
        print(f"   📊 Outstanding balances check:")
        print(f"      Has outstanding balances: {has_outstanding_balances}")
        if outstanding_details:
            for detail in outstanding_details:
                print(f"      - {detail}")
        
        # Try to delete the 8H employee
        print(f"   📝 Attempting to delete 8H employee...")
        
        delete_response, delete_status = await self.make_request('DELETE', f'/department-admin/employees/{employee_id}')
        
        print(f"   📊 Deletion attempt result:")
        print(f"      HTTP Status: {delete_status}")
        print(f"      Response: {delete_response}")
        
        # Verify critical requirements
        verification_results = {}
        
        # ✅ Returns HTTP 400 (deletion blocked)
        deletion_blocked = delete_status == 400
        verification_results['deletion_blocked_http_400'] = deletion_blocked
        print(f"   {'✅' if deletion_blocked else '❌'} Returns HTTP 400 (deletion blocked): {delete_status}")
        
        # ✅ German error message about outstanding balances
        german_error_message = False
        if isinstance(delete_response, dict) and 'detail' in delete_response:
            error_detail = delete_response['detail'].lower()
            german_keywords = ['saldo', 'balance', 'nicht', 'löschen', 'ausstehend', 'schulden']
            german_error_message = any(keyword in error_detail for keyword in german_keywords)
        
        verification_results['german_error_message'] = german_error_message
        print(f"   {'✅' if german_error_message else '❌'} German error message about outstanding balances: {german_error_message}")
        if delete_response and isinstance(delete_response, dict):
            print(f"      Error message: {delete_response.get('detail', 'No detail')}")
        
        # ✅ Employee NOT deleted (verify employee still exists)
        employee_still_exists = False
        if deletion_blocked:
            # Check if employee still exists by trying to get balances
            check_balances = await self.get_employee_all_balances(employee_id)
            employee_still_exists = check_balances is not None
        
        verification_results['employee_not_deleted'] = employee_still_exists
        print(f"   {'✅' if employee_still_exists else '❌'} Employee NOT deleted (still exists): {employee_still_exists}")
        
        success = all(verification_results.values())
        
        if success:
            print(f"   🎉 TEST 4 PASSED: Deletion Protection - HTTP 400, German error, employee preserved")
        else:
            print(f"   ❌ TEST 4 FAILED: Deletion protection requirements not met")
            for req, result in verification_results.items():
                if not result:
                    print(f"      - {req}: FAILED")
        
        return {
            "test": "Deletion Protection",
            "success": success,
            "employee_id": employee_id,
            "verification_results": verification_results,
            "has_outstanding_balances": has_outstanding_balances,
            "outstanding_details": outstanding_details,
            "delete_status": delete_status,
            "delete_response": delete_response,
            "current_balances": current_balances
        }

    async def run_8h_service_retest(self):
        """RE-TEST the 8H-Service Employee Ordering Fix as requested"""
        print("🚀 RE-TESTING 8H-SERVICE EMPLOYEE ORDERING FIX")
        print("=" * 80)
        print("CRITICAL TEST: Verify 8H-Service Employee Uses Subaccounts Only")
        print("")
        print("Test Setup:")
        print("- Create a NEW 8H-service employee (fresh start, no previous test data)")
        print("- Create orders in DIFFERENT departments")
        print("")
        print("Test 1: Create 8H Employee")
        print("- POST /api/employees with is_8h_service=true")
        print("- Verify is_8h_service=true, main balances=0.0")
        print("")
        print("Test 2: Order in Department 1")
        print("- Create a breakfast order for 8H employee in fw4abteilung1")
        print("- Verify main balances REMAIN 0.0, subaccount updated")
        print("")
        print("Test 3: Order in Department 2")
        print("- Create a drinks order for same 8H employee in fw4abteilung2")
        print("- Verify main balances STILL 0.0, different subaccount updated")
        print("")
        print("Test 4: Deletion Protection")
        print("- Try DELETE /api/department-admin/employees/{8h_employee_id}")
        print("- Verify deletion blocked with HTTP 400 and German error message")
        print("=" * 80)
        
        # Run the critical 8H-Service Employee tests
        test_results = []
        
        # Test 1: Create 8H Employee
        print(f"\n{'='*80}")
        result_1 = await self.test_8h_service_employee_creation_critical()
        test_results.append(result_1)
        
        # Test 2: Order in Department 1 (breakfast)
        print(f"\n{'='*80}")
        result_2 = await self.test_8h_service_order_department_1()
        test_results.append(result_2)
        
        # Test 3: Order in Department 2 (drinks)
        print(f"\n{'='*80}")
        result_3 = await self.test_8h_service_order_department_2(result_1.get('employee_id') if result_1.get('success') else None)
        test_results.append(result_3)
        
        # Test 4: Deletion Protection
        print(f"\n{'='*80}")
        result_4 = await self.test_8h_service_deletion_protection_critical(result_1.get('employee_id') if result_1.get('success') else None)
        test_results.append(result_4)
        
        # Analyze results
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results if result.get('success', False))
        failed_tests = [result for result in test_results if not result.get('success', False)]
        
        print(f"\n{'='*80}")
        print(f"🎯 8H-SERVICE EMPLOYEE ORDERING FIX - TEST RESULTS")
        print(f"{'='*80}")
        
        for i, result in enumerate(test_results, 1):
            test_name = result['test']
            success = result.get('success', False)
            
            print(f"\n📋 TEST {i}: {test_name}")
            print(f"   Result: {'✅ PASSED' if success else '❌ FAILED'}")
            
            if success:
                # Show key verification details
                if 'verification_results' in result:
                    for req, req_result in result['verification_results'].items():
                        print(f"   {'✅' if req_result else '❌'} {req}")
                
                # Show employee ID for tracking
                if 'employee_id' in result and result['employee_id']:
                    print(f"   Employee ID: {result['employee_id'][:8]}...")
            else:
                # Show error details
                if 'error' in result:
                    print(f"   🚨 ERROR: {result['error']}")
        
        # Final analysis
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL ANALYSIS - 8H-SERVICE EMPLOYEE ORDERING FIX")
        print(f"{'='*80}")
        print(f"Total Test Cases: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Failed Tests: {len(failed_tests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if successful_tests == total_tests:
            print(f"\n🎉 ALL 8H-SERVICE EMPLOYEE TESTS PASSED!")
            print(f"✅ Test 1: Create 8H Employee - is_8h_service=true, main balances=0.0")
            print(f"✅ Test 2: Order in Department 1 - main balances REMAIN 0.0, subaccount updated")
            print(f"✅ Test 3: Order in Department 2 - main balances STILL 0.0, different subaccount updated")
            print(f"✅ Test 4: Deletion Protection - HTTP 400, German error, employee preserved")
            print(f"")
            print(f"🎯 CRITICAL VERIFICATION COMPLETE:")
            print(f"   ✅ 8H-Service employees use SUBACCOUNTS ONLY")
            print(f"   ✅ Main balances (breakfast_balance, drinks_sweets_balance) NEVER updated")
            print(f"   ✅ Subaccount balances updated correctly per department")
            print(f"   ✅ Deletion protection works for outstanding subaccount balances")
            print(f"")
            print(f"🎉 THE 8H-SERVICE EMPLOYEE ORDERING FIX IS FULLY FUNCTIONAL!")
        else:
            print(f"\n🚨 8H-SERVICE EMPLOYEE ORDERING FIX ISSUES DETECTED!")
            print(f"❌ {len(failed_tests)} test cases failed")
            print(f"❌ The fix may not be working correctly")
            
            # Identify specific failures
            print(f"\n🔍 FAILURE ANALYSIS:")
            for result in failed_tests:
                test_name = result['test']
                error = result.get('error', 'Unknown error')
                print(f"   ❌ {test_name}: {error}")
                
                # Show specific verification failures
                if 'verification_results' in result:
                    for req, req_result in result['verification_results'].items():
                        if not req_result:
                            print(f"      - {req}: FAILED")
            
            print(f"\n💡 CRITICAL ISSUES TO INVESTIGATE:")
            print(f"   1. Check if order creation logic properly handles is_8h_service flag")
            print(f"   2. Verify update_employee_balance() function uses subaccounts for 8H employees")
            print(f"   3. Confirm deletion protection checks all subaccount balances")
            print(f"   4. Test with different order types (breakfast, drinks, sweets)")
        
        return successful_tests == total_tests

async def main():
    """Main test execution"""
    async with EmployeeProfileTester() as tester:
        success = await tester.run_8h_service_retest()
        return success

if __name__ == "__main__":
    print("Backend Test Suite: 8H-Service Employee Ordering Fix RE-TEST")
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