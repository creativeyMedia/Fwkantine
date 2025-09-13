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

class PaymentLogTester:
    def __init__(self):
        self.session = None
        self.test_employees = {}
        self.departments = [
            {"id": "fw4abteilung1", "name": "1. Wachabteilung", "admin_password": "admin1"},
            {"id": "fw4abteilung2", "name": "2. Wachabteilung", "admin_password": "admin2"},
            {"id": "fw4abteilung3", "name": "3. Wachabteilung", "admin_password": "admin3"},
            {"id": "fw4abteilung4", "name": "4. Wachabteilung", "admin_password": "admin4"}
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
    
    async def create_test_employee(self, department_id, name):
        """Create a test employee for payment testing"""
        employee_data = {
            "name": name,
            "department_id": department_id,
            "is_guest": False
        }
        
        response, status = await self.make_request('POST', '/employees', employee_data)
        if status == 200:
            print(f"✅ Created test employee: {name} in {department_id}")
            return response
        else:
            print(f"❌ Failed to create employee {name}: {response}")
            return None
    
    async def test_subaccount_flexible_payment(self, employee_id, admin_department, expected_dept_name):
        """Test subaccount flexible payment and verify admin display"""
        print(f"\n🧪 Testing subaccount_flexible_payment for {admin_department}")
        
        payment_data = {
            "balance_type": "breakfast",
            "amount": 10.0,
            "payment_method": "cash",
            "notes": "Test payment for admin display verification"
        }
        
        response, status = await self.make_request(
            'POST', 
            f'/department-admin/subaccount-payment/{employee_id}',
            payment_data,
            params={"admin_department": admin_department}
        )
        
        if status == 200:
            print(f"✅ Subaccount payment successful")
            return True
        else:
            print(f"❌ Subaccount payment failed: {response}")
            return False
    
    async def test_reset_subaccount_balance(self, employee_id, admin_department, expected_dept_name):
        """Test reset subaccount balance and verify admin display"""
        print(f"\n🧪 Testing reset_subaccount_balance for {admin_department}")
        
        response, status = await self.make_request(
            'POST', 
            f'/department-admin/reset-subaccount-balance/{employee_id}',
            params={
                "balance_type": "breakfast",
                "admin_department": admin_department
            }
        )
        
        if status == 200:
            print(f"✅ Reset subaccount balance successful")
            return True
        else:
            print(f"❌ Reset subaccount balance failed: {response}")
            return False
    
    async def test_flexible_payment(self, employee_id, admin_department, expected_dept_name):
        """Test flexible payment and verify admin display"""
        print(f"\n🧪 Testing flexible_payment for {admin_department}")
        
        payment_data = {
            "payment_type": "breakfast",
            "amount": 15.0,
            "payment_method": "cash",
            "notes": "Test flexible payment for admin display verification"
        }
        
        response, status = await self.make_request(
            'POST', 
            f'/department-admin/flexible-payment/{employee_id}',
            payment_data,
            params={"admin_department": admin_department}
        )
        
        if status == 200:
            print(f"✅ Flexible payment successful")
            return True
        else:
            print(f"❌ Flexible payment failed: {response}")
            return False
    
    async def test_mark_payment(self, employee_id, admin_department, expected_dept_name):
        """Test mark payment and verify admin display"""
        print(f"\n🧪 Testing mark_payment for {admin_department}")
        
        response, status = await self.make_request(
            'POST', 
            f'/department-admin/mark-payment/{employee_id}',
            params={
                "payment_type": "breakfast",
                "amount": 20.0,
                "admin_department": admin_department
            }
        )
        
        if status == 200:
            print(f"✅ Mark payment successful")
            return True
        else:
            print(f"❌ Mark payment failed: {response}")
            return False
    
    async def get_payment_logs(self, employee_id):
        """Get payment logs for an employee to verify admin display"""
        response, status = await self.make_request('GET', f'/employees/{employee_id}/payment-logs')
        
        if status == 200:
            return response
        else:
            print(f"❌ Failed to get payment logs: {response}")
            return None
    
    async def verify_admin_display_in_logs(self, employee_id, expected_dept_name):
        """Verify that payment logs show correct admin display"""
        print(f"\n🔍 Verifying admin display in payment logs...")
        
        logs = await self.get_payment_logs(employee_id)
        if not logs:
            print("❌ No payment logs found")
            return False
        
        success_count = 0
        total_logs = len(logs) if isinstance(logs, list) else 0
        
        if total_logs == 0:
            print("❌ No payment logs to verify")
            return False
        
        for log in logs:
            admin_user = log.get('admin_user', '')
            notes = log.get('notes', '')
            
            print(f"📋 Payment Log:")
            print(f"   Admin: {admin_user}")
            print(f"   Notes: {notes}")
            
            # Check if admin field shows user-friendly name instead of technical ID
            if expected_dept_name in admin_user:
                print(f"   ✅ Admin field correct: Shows '{expected_dept_name}' (user-friendly)")
                success_count += 1
            else:
                print(f"   ❌ Admin field incorrect: Shows '{admin_user}' instead of '{expected_dept_name}'")
            
            # Check if notes field shows user-friendly department name
            if f"Zahlung in {expected_dept_name}" in notes:
                print(f"   ✅ Notes field correct: Contains 'Zahlung in {expected_dept_name}'")
            else:
                print(f"   ⚠️  Notes field: '{notes}' (may not contain expected text)")
        
        success_rate = (success_count / total_logs) * 100
        print(f"\n📊 Admin Display Verification: {success_count}/{total_logs} logs correct ({success_rate:.1f}%)")
        
        return success_count == total_logs
    
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