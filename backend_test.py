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
    
    async def test_department(self, dept_info):
        """Test all payment functions for a specific department"""
        dept_id = dept_info["id"]
        dept_name = dept_info["name"]
        admin_password = dept_info["admin_password"]
        
        print(f"\n{'='*60}")
        print(f"🏢 TESTING DEPARTMENT: {dept_name} ({dept_id})")
        print(f"{'='*60}")
        
        # Authenticate as admin
        auth_result = await self.authenticate_admin(dept_name, admin_password)
        if not auth_result:
            print(f"❌ Cannot test {dept_name} - authentication failed")
            return False
        
        # Create test employee for this department
        test_employee_name = f"TestEmployee_{dept_id}"
        employee = await self.create_test_employee(dept_id, test_employee_name)
        if not employee:
            print(f"❌ Cannot test {dept_name} - employee creation failed")
            return False
        
        employee_id = employee["id"]
        self.test_employees[dept_id] = employee_id
        
        # Test all 4 payment functions
        test_results = []
        
        # 1. Test subaccount_flexible_payment
        result1 = await self.test_subaccount_flexible_payment(employee_id, dept_id, dept_name)
        test_results.append(result1)
        
        # 2. Test flexible_payment
        result2 = await self.test_flexible_payment(employee_id, dept_id, dept_name)
        test_results.append(result2)
        
        # 3. Test mark_payment
        result3 = await self.test_mark_payment(employee_id, dept_id, dept_name)
        test_results.append(result3)
        
        # 4. Test reset_subaccount_balance (after creating some balance)
        result4 = await self.test_reset_subaccount_balance(employee_id, dept_id, dept_name)
        test_results.append(result4)
        
        # Verify admin display in payment logs
        admin_display_correct = await self.verify_admin_display_in_logs(employee_id, dept_name)
        
        # Summary for this department
        successful_tests = sum(test_results)
        total_tests = len(test_results)
        
        print(f"\n📊 DEPARTMENT {dept_name} SUMMARY:")
        print(f"   Payment Functions: {successful_tests}/{total_tests} successful")
        print(f"   Admin Display: {'✅ CORRECT' if admin_display_correct else '❌ INCORRECT'}")
        
        return successful_tests == total_tests and admin_display_correct
    
    async def run_comprehensive_test(self):
        """Run comprehensive test of admin display fix across all departments"""
        print("🚀 STARTING COMPREHENSIVE ADMIN DISPLAY TEST")
        print("=" * 80)
        print("Testing corrected admin display in payment_logs:")
        print("- BEFORE: Admin: fw4abteilung1 (technical ID)")
        print("- AFTER:  Admin: 1. Wachabteilung (user-friendly name)")
        print("=" * 80)
        
        department_results = []
        
        # Test each department
        for dept_info in self.departments:
            dept_result = await self.test_department(dept_info)
            department_results.append(dept_result)
        
        # Final summary
        successful_depts = sum(department_results)
        total_depts = len(department_results)
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL TEST RESULTS")
        print(f"{'='*80}")
        print(f"Departments Tested: {total_depts}")
        print(f"Departments Passed: {successful_depts}")
        print(f"Success Rate: {(successful_depts/total_depts)*100:.1f}%")
        
        if successful_depts == total_depts:
            print(f"\n🎉 ALL TESTS PASSED!")
            print(f"✅ Admin display fix is working correctly across all departments")
            print(f"✅ Admin field shows user-friendly names like '1. Wachabteilung'")
            print(f"✅ Notes field shows 'Zahlung in X. Wachabteilung'")
            print(f"✅ System is ready for live testing!")
        else:
            failed_depts = total_depts - successful_depts
            print(f"\n❌ {failed_depts} DEPARTMENT(S) FAILED")
            print(f"❌ Admin display fix needs attention")
        
        return successful_depts == total_depts

async def main():
    """Main test execution"""
    async with PaymentLogTester() as tester:
        success = await tester.run_comprehensive_test()
        return success

if __name__ == "__main__":
    print("Backend Test Suite: Admin Display Fix in Payment Logs")
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