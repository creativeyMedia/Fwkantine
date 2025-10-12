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
    async with DeveloperDashboardTester() as tester:
        success = await tester.run_comprehensive_test()
        return success

if __name__ == "__main__":
    print("Backend Test Suite: Developer Dashboard Employee Management")
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