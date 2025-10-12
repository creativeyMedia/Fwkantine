#!/usr/bin/env python3
"""
Backend Test Suite for Employee Department Moving with Balance Migration

TESTING FOCUS:
Testing the improved employee department moving with proper balance migration logic.

BACKEND ENDPOINT TO TEST:
PUT /api/developer/move-employee/{employee_id} - Move employee between departments with balance migration

TEST SCENARIOS TO VERIFY:
1. Test employee moving with balance migration from department A to department B
2. Verify that main balances become subaccount balances for old department
3. Verify that subaccount balances (if any) for target department become new main balances
4. Test complex scenarios with multiple moves and existing subaccount balances
5. Verify balance consistency and data integrity after moves

EXPECTED BALANCE MIGRATION LOGIC:
- Move A→B: Main balances of A become subaccount A, subaccount B becomes main balances
- Multiple moves: Previous department balances preserved in subaccounts
- Balance totals: Total balance across all accounts remains constant (no money created/lost)

TEST SCENARIOS:
1. Simple Move: Employee with €10 main balance (breakfast) moves A→B
2. Complex Move: Employee with existing subaccount balances moves between departments  
3. Multiple Moves: Employee moves A→B→C to test subaccount accumulation
4. Zero Balance Move: Employee with €0 balances moves departments
5. Negative Balance Move: Employee with negative balances moves departments

VERIFICATION POINTS:
- Balance migration response includes old and new balance details
- Database reflects correct main and subaccount balance updates
- Total employee balance remains mathematically consistent
- No balance duplication or loss during migration
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://feuerwehr-kantine.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BalanceMigrationTester:
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
        
        # Use flexible payment to adjust balance
        payment_data = {
            "payment_type": balance_type if balance_type != "drinks" else "drinks_sweets",
            "amount": payment_amount,
            "payment_method": "adjustment",
            "notes": f"Test balance adjustment to {amount}"
        }
        
        response, status = await self.make_request('POST', f'/department-admin/flexible-payment/{employee_id}', payment_data)
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
    
    async def test_simple_balance_migration(self):
        """Test Case 1: Simple Move - Employee with €10 main balance (breakfast) moves A→B"""
        print(f"\n🧪 TEST CASE 1: Simple Balance Migration (A→B)")
        
        # Create test employee in department 1
        employee = await self.create_test_employee("fw4abteilung1", "TestSimpleMigration")
        if not employee:
            return {"test": "Simple balance migration", "success": False, "error": "Failed to create test employee"}
        
        employee_id = employee['id']
        original_dept = "fw4abteilung1"
        target_dept = "fw4abteilung2"
        
        print(f"   Employee ID: {employee_id}")
        print(f"   Original Department: {original_dept}")
        print(f"   Target Department: {target_dept}")
        
        # Set initial balance: €10 breakfast balance
        if not await self.set_employee_balance(employee_id, original_dept, "breakfast", 10.0):
            return {"test": "Simple balance migration", "success": False, "error": "Failed to set initial balance"}
        
        # Get initial balances
        initial_balances = await self.get_employee_all_balances(employee_id)
        if not initial_balances:
            return {"test": "Simple balance migration", "success": False, "error": "Failed to get initial balances"}
        
        print(f"   Initial breakfast balance: €{initial_balances['main_balances']['breakfast']}")
        print(f"   Initial drinks balance: €{initial_balances['main_balances']['drinks_sweets']}")
        
        # Move employee to department 2
        move_response, move_status = await self.move_employee_to_department(employee_id, target_dept)
        
        if move_status != 200:
            return {
                "test": "Simple balance migration", 
                "success": False, 
                "error": f"Move failed with status {move_status}: {move_response}"
            }
        
        print(f"   ✅ Move API response: {move_response}")
        
        # Verify balance migration in response
        balance_migration = move_response.get('balance_migration', {})
        old_balances = balance_migration.get('old_main_balances_moved_to_subaccount', {})
        new_balances = balance_migration.get('new_main_balances_from_subaccount', {})
        
        if old_balances.get('breakfast') != 10.0:
            return {
                "test": "Simple balance migration",
                "success": False,
                "error": f"Expected old breakfast balance 10.0, got {old_balances.get('breakfast')}"
            }
        
        # Get final balances
        final_balances = await self.get_employee_all_balances(employee_id)
        if not final_balances:
            return {"test": "Simple balance migration", "success": False, "error": "Failed to get final balances"}
        
        print(f"   Final main breakfast balance: €{final_balances['main_balances']['breakfast']}")
        print(f"   Final main drinks balance: €{final_balances['main_balances']['drinks_sweets']}")
        
        # Verify main balances are now 0 (moved to subaccount)
        if final_balances['main_balances']['breakfast'] != 0.0:
            return {
                "test": "Simple balance migration",
                "success": False,
                "error": f"Expected new main breakfast balance 0.0, got {final_balances['main_balances']['breakfast']}"
            }
        
        # Verify old department subaccount has the migrated balance
        old_dept_subaccount = final_balances['subaccount_balances'].get(original_dept, {})
        if old_dept_subaccount.get('breakfast') != 10.0:
            return {
                "test": "Simple balance migration",
                "success": False,
                "error": f"Expected subaccount breakfast balance 10.0, got {old_dept_subaccount.get('breakfast')}"
            }
        
        print(f"   ✅ Old department subaccount breakfast: €{old_dept_subaccount.get('breakfast')}")
        print(f"   ✅ Balance migration successful: Main €10 → Subaccount €10")
        
        return {
            "test": "Simple balance migration",
            "success": True,
            "employee_id": employee_id,
            "original_department": original_dept,
            "target_department": target_dept,
            "initial_balance": 10.0,
            "migrated_to_subaccount": old_dept_subaccount.get('breakfast'),
            "new_main_balance": final_balances['main_balances']['breakfast']
        }
    
    async def test_complex_balance_migration(self):
        """Test Case 2: Complex Move - Employee with existing subaccount balances moves between departments"""
        print(f"\n🧪 TEST CASE 2: Complex Balance Migration with Existing Subaccounts")
        
        # Create test employee in department 1
        employee = await self.create_test_employee("fw4abteilung1", "TestComplexMigration")
        if not employee:
            return {"test": "Complex balance migration", "success": False, "error": "Failed to create test employee"}
        
        employee_id = employee['id']
        
        print(f"   Employee ID: {employee_id}")
        print(f"   Testing: Dept1 → Dept2 → Dept3 with balance accumulation")
        
        # Set initial balance: €15 breakfast, €5 drinks
        if not await self.set_employee_balance(employee_id, "fw4abteilung1", "breakfast", 15.0):
            return {"test": "Complex balance migration", "success": False, "error": "Failed to set initial breakfast balance"}
        if not await self.set_employee_balance(employee_id, "fw4abteilung1", "drinks", 5.0):
            return {"test": "Complex balance migration", "success": False, "error": "Failed to set initial drinks balance"}
        
        # Get initial balances
        initial_balances = await self.get_employee_all_balances(employee_id)
        print(f"   Initial: Breakfast €{initial_balances['main_balances']['breakfast']}, Drinks €{initial_balances['main_balances']['drinks_sweets']}")
        
        # MOVE 1: Dept1 → Dept2
        print(f"   🔄 MOVE 1: fw4abteilung1 → fw4abteilung2")
        move1_response, move1_status = await self.move_employee_to_department(employee_id, "fw4abteilung2")
        if move1_status != 200:
            return {"test": "Complex balance migration", "success": False, "error": f"Move 1 failed: {move1_response}"}
        
        # Check balances after move 1
        balances_after_move1 = await self.get_employee_all_balances(employee_id)
        dept1_subaccount = balances_after_move1['subaccount_balances'].get('fw4abteilung1', {})
        print(f"   After Move 1 - Dept1 subaccount: Breakfast €{dept1_subaccount.get('breakfast')}, Drinks €{dept1_subaccount.get('drinks')}")
        print(f"   After Move 1 - Main balances: Breakfast €{balances_after_move1['main_balances']['breakfast']}, Drinks €{balances_after_move1['main_balances']['drinks_sweets']}")
        
        # Set some balance in dept2 (simulate orders)
        if not await self.set_employee_balance(employee_id, "fw4abteilung2", "breakfast", -8.0):
            return {"test": "Complex balance migration", "success": False, "error": "Failed to set dept2 balance"}
        
        # MOVE 2: Dept2 → Dept3  
        print(f"   🔄 MOVE 2: fw4abteilung2 → fw4abteilung3")
        move2_response, move2_status = await self.move_employee_to_department(employee_id, "fw4abteilung3")
        if move2_status != 200:
            return {"test": "Complex balance migration", "success": False, "error": f"Move 2 failed: {move2_response}"}
        
        # Get final balances
        final_balances = await self.get_employee_all_balances(employee_id)
        
        # Verify balance preservation
        dept1_final = final_balances['subaccount_balances'].get('fw4abteilung1', {})
        dept2_final = final_balances['subaccount_balances'].get('fw4abteilung2', {})
        
        print(f"   Final - Dept1 subaccount: Breakfast €{dept1_final.get('breakfast')}, Drinks €{dept1_final.get('drinks')}")
        print(f"   Final - Dept2 subaccount: Breakfast €{dept2_final.get('breakfast')}, Drinks €{dept2_final.get('drinks')}")
        print(f"   Final - Main balances: Breakfast €{final_balances['main_balances']['breakfast']}, Drinks €{final_balances['main_balances']['drinks_sweets']}")
        
        # Verify dept1 balances are preserved
        if dept1_final.get('breakfast') != 15.0 or dept1_final.get('drinks') != 5.0:
            return {
                "test": "Complex balance migration",
                "success": False,
                "error": f"Dept1 balances not preserved. Expected: B€15, D€5. Got: B€{dept1_final.get('breakfast')}, D€{dept1_final.get('drinks')}"
            }
        
        # Verify dept2 balances are preserved
        if dept2_final.get('breakfast') != -8.0:
            return {
                "test": "Complex balance migration",
                "success": False,
                "error": f"Dept2 breakfast balance not preserved. Expected: €-8, Got: €{dept2_final.get('breakfast')}"
            }
        
        print(f"   ✅ All balances preserved across multiple moves")
        
        return {
            "test": "Complex balance migration",
            "success": True,
            "employee_id": employee_id,
            "moves_completed": 2,
            "dept1_preserved": {"breakfast": dept1_final.get('breakfast'), "drinks": dept1_final.get('drinks')},
            "dept2_preserved": {"breakfast": dept2_final.get('breakfast'), "drinks": dept2_final.get('drinks')},
            "final_department": "fw4abteilung3"
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