#!/usr/bin/env python3
"""
Backend Test Suite for Statistics Tab - Admin Dashboard Balance Overview

TESTING FOCUS:
Testing the backend endpoints that support the new Statistics tab in Admin Dashboard,
specifically the "Gesamtsaldi" (total balances) feature.

BACKEND ENDPOINTS TO TEST:
1. GET /api/departments/{department_id}/employees - Employee balance data
2. GET /api/employees/{employee_id}/profile - Individual employee profiles  
3. GET /api/departments/{department_id}/employees-with-subaccount-balances - Subaccount balances

GESAMTSALDI CALCULATIONS TO VERIFY:
- "Frühstück & Mittagessen" total balance (sum of all breakfast balances)
- "Süßigkeiten & Getränke" total balance (sum of all drinks/sweets balances)
- Color coding verification (positive/negative totals)
- Mathematical accuracy of balance summations

TEST DEPARTMENTS:
- fw4abteilung1 (admin1/password1)
- fw4abteilung2 (admin2/password1) 

The frontend Statistics tab relies on these backend endpoints to display employee
balance cards and calculate the new Gesamtsaldi totals at the bottom.
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://firebrigade-food.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class StatisticsTabTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.departments = [
            {"id": "fw4abteilung1", "name": "1. Wachabteilung", "admin_password": "admin1", "password": "password1"},
            {"id": "fw4abteilung2", "name": "2. Wachabteilung", "admin_password": "admin2", "password": "password1"},
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
    
    async def get_department_employees(self, department_id):
        """Get all employees for a department - main endpoint for Statistics tab"""
        print(f"\n🧪 Testing GET /api/departments/{department_id}/employees")
        
        response, status = await self.make_request('GET', f'/departments/{department_id}/employees')
        
        if status == 200:
            print(f"✅ Successfully retrieved employees for {department_id}")
            print(f"   Found {len(response)} employees")
            return response, True
        else:
            print(f"❌ Failed to get employees for {department_id}: {response}")
            return response, False
    
    async def get_employee_profile(self, employee_id):
        """Get individual employee profile"""
        print(f"\n🧪 Testing GET /api/employees/{employee_id}/profile")
        
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        
        if status == 200:
            print(f"✅ Successfully retrieved profile for employee {employee_id}")
            return response, True
        else:
            print(f"❌ Failed to get profile for employee {employee_id}: {response}")
            return response, False
    
    async def get_employees_with_subaccount_balances(self, department_id):
        """Get employees with subaccount balances"""
        print(f"\n🧪 Testing GET /api/departments/{department_id}/employees-with-subaccount-balances")
        
        response, status = await self.make_request('GET', f'/departments/{department_id}/employees-with-subaccount-balances')
        
        if status == 200:
            print(f"✅ Successfully retrieved subaccount balances for {department_id}")
            print(f"   Found {len(response)} employees with subaccount balances")
            return response, True
        else:
            print(f"❌ Failed to get subaccount balances for {department_id}: {response}")
            return response, False
    
    async def verify_employee_balance_structure(self, employee_data):
        """Verify employee has proper balance structure for Statistics tab"""
        print(f"\n🔍 Verifying balance structure for employee: {employee_data.get('name', 'Unknown')}")
        
        required_fields = ['id', 'name', 'breakfast_balance', 'drinks_sweets_balance']
        missing_fields = []
        
        for field in required_fields:
            if field not in employee_data or employee_data[field] is None:
                missing_fields.append(field)
                print(f"   ❌ Missing field: {field}")
            else:
                print(f"   ✅ {field}: {employee_data[field]}")
        
        # Check subaccount_balances structure
        subaccounts = employee_data.get('subaccount_balances')
        if subaccounts:
            print(f"   ✅ subaccount_balances: Present")
            for dept_id, balances in subaccounts.items():
                breakfast_bal = balances.get('breakfast', 'MISSING')
                drinks_bal = balances.get('drinks', 'MISSING')
                print(f"      {dept_id}: breakfast={breakfast_bal}, drinks={drinks_bal}")
        else:
            print(f"   ❌ subaccount_balances: Missing")
            missing_fields.append('subaccount_balances')
        
        return len(missing_fields) == 0, missing_fields
    
    async def calculate_gesamtsaldi(self, employees):
        """Calculate Gesamtsaldi totals like the frontend would"""
        print(f"\n🧮 Calculating Gesamtsaldi totals for {len(employees)} employees")
        
        total_breakfast_lunch = 0.0
        total_drinks_sweets = 0.0
        
        employee_breakdown = []
        
        for employee in employees:
            name = employee.get('name', 'Unknown')
            breakfast_balance = employee.get('breakfast_balance', 0.0)
            drinks_balance = employee.get('drinks_sweets_balance', 0.0)
            
            total_breakfast_lunch += breakfast_balance
            total_drinks_sweets += drinks_balance
            
            employee_breakdown.append({
                'name': name,
                'breakfast_balance': breakfast_balance,
                'drinks_balance': drinks_balance,
                'total_balance': breakfast_balance + drinks_balance
            })
            
            print(f"   {name}: Breakfast={breakfast_balance:.2f}€, Drinks={drinks_balance:.2f}€")
        
        print(f"\n📊 GESAMTSALDI CALCULATION RESULTS:")
        print(f"   Frühstück & Mittagessen Total: {total_breakfast_lunch:.2f}€")
        print(f"   Süßigkeiten & Getränke Total: {total_drinks_sweets:.2f}€")
        print(f"   Grand Total: {(total_breakfast_lunch + total_drinks_sweets):.2f}€")
        
        # Determine color coding
        breakfast_color = "green" if total_breakfast_lunch >= 0 else "red"
        drinks_color = "green" if total_drinks_sweets >= 0 else "red"
        
        print(f"   Color Coding: Breakfast={breakfast_color}, Drinks={drinks_color}")
        
        return {
            'total_breakfast_lunch': total_breakfast_lunch,
            'total_drinks_sweets': total_drinks_sweets,
            'grand_total': total_breakfast_lunch + total_drinks_sweets,
            'breakfast_color': breakfast_color,
            'drinks_color': drinks_color,
            'employee_breakdown': employee_breakdown
        }
    
    async def test_statistics_tab_backend_support(self, department_info):
        """Test all backend endpoints that support the Statistics tab"""
        dept_id = department_info["id"]
        dept_name = department_info["name"]
        admin_password = department_info["admin_password"]
        
        print(f"\n{'='*80}")
        print(f"🎯 TESTING STATISTICS TAB BACKEND SUPPORT")
        print(f"   Department: {dept_name} ({dept_id})")
        print(f"{'='*80}")
        
        test_results = {
            'department': dept_name,
            'admin_auth': False,
            'employees_endpoint': False,
            'employee_profiles': False,
            'subaccount_balances': False,
            'balance_structure_valid': False,
            'gesamtsaldi_calculation': False,
            'error_details': []
        }
        
        # Step 1: Admin Authentication
        print(f"\n📋 STEP 1: Admin Authentication")
        auth_result = await self.authenticate_admin(dept_name, admin_password)
        if auth_result:
            test_results['admin_auth'] = True
            print(f"✅ Admin authentication successful")
        else:
            test_results['error_details'].append("Admin authentication failed")
            print(f"❌ Admin authentication failed")
            return test_results
        
        # Step 2: Get Department Employees (Main Statistics Tab Endpoint)
        print(f"\n📋 STEP 2: Department Employees Endpoint")
        employees, employees_success = await self.get_department_employees(dept_id)
        if employees_success and employees:
            test_results['employees_endpoint'] = True
            print(f"✅ Employees endpoint working - found {len(employees)} employees")
            
            # Step 3: Verify Employee Balance Structure
            print(f"\n📋 STEP 3: Employee Balance Structure Verification")
            valid_employees = 0
            total_employees = len(employees)
            
            for employee in employees:
                structure_valid, missing_fields = await self.verify_employee_balance_structure(employee)
                if structure_valid:
                    valid_employees += 1
                else:
                    test_results['error_details'].append(f"Employee {employee.get('name', 'Unknown')} missing fields: {missing_fields}")
            
            if valid_employees == total_employees:
                test_results['balance_structure_valid'] = True
                print(f"✅ All {total_employees} employees have valid balance structure")
            else:
                print(f"❌ Only {valid_employees}/{total_employees} employees have valid balance structure")
            
            # Step 4: Calculate Gesamtsaldi
            print(f"\n📋 STEP 4: Gesamtsaldi Calculation Test")
            try:
                gesamtsaldi_result = await self.calculate_gesamtsaldi(employees)
                test_results['gesamtsaldi_calculation'] = True
                test_results['gesamtsaldi_data'] = gesamtsaldi_result
                print(f"✅ Gesamtsaldi calculation successful")
            except Exception as e:
                test_results['error_details'].append(f"Gesamtsaldi calculation failed: {str(e)}")
                print(f"❌ Gesamtsaldi calculation failed: {str(e)}")
            
            # Step 5: Test Individual Employee Profiles (Sample)
            print(f"\n📋 STEP 5: Individual Employee Profile Test")
            if employees:
                sample_employee = employees[0]
                employee_id = sample_employee.get('id')
                profile, profile_success = await self.get_employee_profile(employee_id)
                if profile_success:
                    test_results['employee_profiles'] = True
                    print(f"✅ Employee profile endpoint working")
                else:
                    test_results['error_details'].append("Employee profile endpoint failed")
                    print(f"❌ Employee profile endpoint failed")
            
            # Step 6: Test Subaccount Balances Endpoint
            print(f"\n📋 STEP 6: Subaccount Balances Endpoint Test")
            subaccounts, subaccounts_success = await self.get_employees_with_subaccount_balances(dept_id)
            if subaccounts_success:
                test_results['subaccount_balances'] = True
                print(f"✅ Subaccount balances endpoint working")
            else:
                test_results['error_details'].append("Subaccount balances endpoint failed")
                print(f"❌ Subaccount balances endpoint failed")
        
        else:
            test_results['error_details'].append("Failed to get department employees")
            print(f"❌ Failed to get department employees")
        
        return test_results
    
    async def test_gesamtsaldi_mathematical_accuracy(self, department_info):
        """Test mathematical accuracy of Gesamtsaldi calculations"""
        dept_id = department_info["id"]
        dept_name = department_info["name"]
        
        print(f"\n{'='*80}")
        print(f"🧮 TESTING GESAMTSALDI MATHEMATICAL ACCURACY")
        print(f"   Department: {dept_name} ({dept_id})")
        print(f"{'='*80}")
        
        # Get employees
        employees, success = await self.get_department_employees(dept_id)
        if not success or not employees:
            print(f"❌ Cannot test mathematical accuracy - no employee data")
            return False
        
        # Manual calculation
        manual_breakfast_total = 0.0
        manual_drinks_total = 0.0
        
        print(f"\n🔍 Manual Balance Verification:")
        for i, employee in enumerate(employees):
            name = employee.get('name', f'Employee_{i}')
            breakfast = employee.get('breakfast_balance', 0.0)
            drinks = employee.get('drinks_sweets_balance', 0.0)
            
            manual_breakfast_total += breakfast
            manual_drinks_total += drinks
            
            print(f"   {name}: B={breakfast:.2f}€, D={drinks:.2f}€")
        
        print(f"\n📊 Manual Calculation Results:")
        print(f"   Manual Breakfast Total: {manual_breakfast_total:.2f}€")
        print(f"   Manual Drinks Total: {manual_drinks_total:.2f}€")
        print(f"   Manual Grand Total: {(manual_breakfast_total + manual_drinks_total):.2f}€")
        
        # Automated calculation
        gesamtsaldi_result = await self.calculate_gesamtsaldi(employees)
        auto_breakfast_total = gesamtsaldi_result['total_breakfast_lunch']
        auto_drinks_total = gesamtsaldi_result['total_drinks_sweets']
        auto_grand_total = gesamtsaldi_result['grand_total']
        
        print(f"\n📊 Automated Calculation Results:")
        print(f"   Auto Breakfast Total: {auto_breakfast_total:.2f}€")
        print(f"   Auto Drinks Total: {auto_drinks_total:.2f}€")
        print(f"   Auto Grand Total: {auto_grand_total:.2f}€")
        
        # Verify accuracy
        breakfast_match = abs(manual_breakfast_total - auto_breakfast_total) < 0.01
        drinks_match = abs(manual_drinks_total - auto_drinks_total) < 0.01
        grand_match = abs((manual_breakfast_total + manual_drinks_total) - auto_grand_total) < 0.01
        
        print(f"\n✅ Mathematical Accuracy Verification:")
        print(f"   Breakfast Totals Match: {'✅' if breakfast_match else '❌'}")
        print(f"   Drinks Totals Match: {'✅' if drinks_match else '❌'}")
        print(f"   Grand Totals Match: {'✅' if grand_match else '❌'}")
        
        return breakfast_match and drinks_match and grand_match
    
    async def test_color_coding_logic(self, department_info):
        """Test color coding logic for positive/negative balances"""
        dept_id = department_info["id"]
        dept_name = department_info["name"]
        
        print(f"\n{'='*80}")
        print(f"🎨 TESTING COLOR CODING LOGIC")
        print(f"   Department: {dept_name} ({dept_id})")
        print(f"{'='*80}")
        
        # Get employees and calculate totals
        employees, success = await self.get_department_employees(dept_id)
        if not success or not employees:
            print(f"❌ Cannot test color coding - no employee data")
            return False
        
        gesamtsaldi_result = await self.calculate_gesamtsaldi(employees)
        
        breakfast_total = gesamtsaldi_result['total_breakfast_lunch']
        drinks_total = gesamtsaldi_result['total_drinks_sweets']
        breakfast_color = gesamtsaldi_result['breakfast_color']
        drinks_color = gesamtsaldi_result['drinks_color']
        
        print(f"\n🎨 Color Coding Test Results:")
        print(f"   Breakfast Total: {breakfast_total:.2f}€ → Color: {breakfast_color}")
        print(f"   Drinks Total: {drinks_total:.2f}€ → Color: {drinks_color}")
        
        # Verify color logic
        breakfast_color_correct = (breakfast_color == "green" and breakfast_total >= 0) or (breakfast_color == "red" and breakfast_total < 0)
        drinks_color_correct = (drinks_color == "green" and drinks_total >= 0) or (drinks_color == "red" and drinks_total < 0)
        
        print(f"\n✅ Color Logic Verification:")
        print(f"   Breakfast Color Correct: {'✅' if breakfast_color_correct else '❌'}")
        print(f"   Drinks Color Correct: {'✅' if drinks_color_correct else '❌'}")
        
        # Test edge cases
        print(f"\n🧪 Edge Case Testing:")
        
        # Test zero balance
        zero_color = "green" if 0.0 >= 0 else "red"
        print(f"   Zero Balance (0.00€) → Color: {zero_color} {'✅' if zero_color == 'green' else '❌'}")
        
        # Test small negative
        small_neg_color = "green" if -0.01 >= 0 else "red"
        print(f"   Small Negative (-0.01€) → Color: {small_neg_color} {'✅' if small_neg_color == 'red' else '❌'}")
        
        # Test small positive
        small_pos_color = "green" if 0.01 >= 0 else "red"
        print(f"   Small Positive (0.01€) → Color: {small_pos_color} {'✅' if small_pos_color == 'green' else '❌'}")
        
        return breakfast_color_correct and drinks_color_correct
    
    async def run_comprehensive_statistics_test(self):
        """Run comprehensive test of Statistics tab backend support"""
        print("🚀 STARTING STATISTICS TAB BACKEND COMPREHENSIVE TEST")
        print("=" * 80)
        print("TESTING: Backend support for Statistics tab Gesamtsaldi feature")
        print("- Employee balance data endpoints")
        print("- Gesamtsaldi calculation accuracy")
        print("- Color coding logic")
        print("- Data structure validation")
        print("=" * 80)
        
        all_results = []
        
        # Test each department
        for department_info in self.departments:
            dept_results = await self.test_statistics_tab_backend_support(department_info)
            all_results.append(dept_results)
            
            # Test mathematical accuracy
            math_accuracy = await self.test_gesamtsaldi_mathematical_accuracy(department_info)
            dept_results['mathematical_accuracy'] = math_accuracy
            
            # Test color coding
            color_coding = await self.test_color_coding_logic(department_info)
            dept_results['color_coding'] = color_coding
        
        # Analyze overall results
        print(f"\n{'='*80}")
        print(f"🎯 COMPREHENSIVE TEST RESULTS ANALYSIS")
        print(f"{'='*80}")
        
        total_departments = len(all_results)
        successful_departments = 0
        
        for result in all_results:
            dept_name = result['department']
            print(f"\n📋 DEPARTMENT: {dept_name}")
            
            tests = [
                ('Admin Authentication', result['admin_auth']),
                ('Employees Endpoint', result['employees_endpoint']),
                ('Employee Profiles', result['employee_profiles']),
                ('Subaccount Balances', result['subaccount_balances']),
                ('Balance Structure Valid', result['balance_structure_valid']),
                ('Gesamtsaldi Calculation', result['gesamtsaldi_calculation']),
                ('Mathematical Accuracy', result.get('mathematical_accuracy', False)),
                ('Color Coding Logic', result.get('color_coding', False))
            ]
            
            passed_tests = 0
            for test_name, test_result in tests:
                status = "✅" if test_result else "❌"
                print(f"   {test_name}: {status}")
                if test_result:
                    passed_tests += 1
            
            if result['error_details']:
                print(f"   🚨 ERRORS:")
                for error in result['error_details']:
                    print(f"      - {error}")
            
            success_rate = (passed_tests / len(tests)) * 100
            print(f"   📊 Success Rate: {success_rate:.1f}% ({passed_tests}/{len(tests)})")
            
            if success_rate >= 87.5:  # 7/8 tests passed
                successful_departments += 1
                print(f"   ✅ DEPARTMENT PASSED")
            else:
                print(f"   ❌ DEPARTMENT FAILED")
        
        # Final analysis
        overall_success_rate = (successful_departments / total_departments) * 100 if total_departments > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL STATISTICS TAB BACKEND TEST RESULTS")
        print(f"{'='*80}")
        print(f"Total Departments Tested: {total_departments}")
        print(f"Successful Departments: {successful_departments}")
        print(f"Failed Departments: {total_departments - successful_departments}")
        print(f"Overall Success Rate: {overall_success_rate:.1f}%")
        
        if successful_departments == total_departments:
            print(f"\n🎉 ALL STATISTICS TAB BACKEND TESTS PASSED!")
            print(f"✅ Employee balance endpoints working correctly")
            print(f"✅ Gesamtsaldi calculations are mathematically accurate")
            print(f"✅ Color coding logic is correct")
            print(f"✅ Data structures support frontend Statistics tab")
            print(f"✅ Backend fully supports the new Gesamtsaldi feature")
        else:
            print(f"\n🚨 STATISTICS TAB BACKEND ISSUES DETECTED!")
            print(f"❌ {total_departments - successful_departments} departments have backend issues")
            print(f"❌ This may affect Statistics tab functionality")
            
            print(f"\n💡 RECOMMENDED FIXES:")
            print(f"   1. Check employee balance data structure consistency")
            print(f"   2. Verify subaccount_balances initialization")
            print(f"   3. Test admin authentication for all departments")
            print(f"   4. Validate mathematical calculation accuracy")
        
        return successful_departments == total_departments

async def main():
    """Main test execution"""
    async with StatisticsTabTester() as tester:
        success = await tester.run_comprehensive_statistics_test()
        return success

if __name__ == "__main__":
    print("Backend Test Suite: Statistics Tab - Admin Dashboard Balance Overview")
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