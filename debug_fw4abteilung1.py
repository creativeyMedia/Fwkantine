#!/usr/bin/env python3
"""
Debug script to investigate fw4abteilung1 employee data corruption
"""

import asyncio
import os
import json
import math
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment
load_dotenv('/app/backend/.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

async def check_employee_data():
    """Check for corrupted float values in fw4abteilung1 employees"""
    print("🔍 DEBUGGING FW4ABTEILUNG1 EMPLOYEE DATA CORRUPTION")
    print("=" * 60)
    
    # Get all employees from fw4abteilung1
    employees = await db.employees.find({"department_id": "fw4abteilung1"}).to_list(1000)
    
    print(f"📊 Found {len(employees)} employees in fw4abteilung1")
    
    corrupted_employees = []
    
    for emp in employees:
        emp_id = emp.get('id', 'NO_ID')[:8]
        emp_name = emp.get('name', 'NO_NAME')
        
        print(f"\n👤 Checking employee: {emp_name} ({emp_id})")
        
        # Check all float fields for corruption
        float_fields = [
            'breakfast_balance', 
            'drinks_sweets_balance',
            'sort_order'
        ]
        
        corruption_found = False
        corruption_details = []
        
        for field in float_fields:
            value = emp.get(field)
            if value is not None:
                try:
                    # Check if value is a valid JSON-serializable float
                    if isinstance(value, (int, float)):
                        if math.isnan(value) or math.isinf(value):
                            corruption_found = True
                            corruption_details.append(f"{field}: {value} (NaN/Inf)")
                            print(f"   ❌ {field}: {value} (NaN/Infinity detected)")
                        else:
                            print(f"   ✅ {field}: {value}")
                    else:
                        print(f"   ⚠️  {field}: {value} (type: {type(value)})")
                except Exception as e:
                    corruption_found = True
                    corruption_details.append(f"{field}: {value} (error: {str(e)})")
                    print(f"   ❌ {field}: {value} (error: {str(e)})")
        
        # Check subaccount_balances
        subaccounts = emp.get('subaccount_balances', {})
        if subaccounts:
            print(f"   📊 Checking subaccount_balances...")
            for dept_id, balances in subaccounts.items():
                if isinstance(balances, dict):
                    for balance_type, balance_value in balances.items():
                        if balance_value is not None and isinstance(balance_value, (int, float)):
                            if math.isnan(balance_value) or math.isinf(balance_value):
                                corruption_found = True
                                corruption_details.append(f"subaccount_balances.{dept_id}.{balance_type}: {balance_value} (NaN/Inf)")
                                print(f"   ❌ subaccount_balances.{dept_id}.{balance_type}: {balance_value} (NaN/Infinity)")
                            else:
                                print(f"   ✅ subaccount_balances.{dept_id}.{balance_type}: {balance_value}")
        
        # Test JSON serialization
        try:
            json.dumps(emp, default=str)
            print(f"   ✅ JSON serialization: OK")
        except Exception as e:
            corruption_found = True
            corruption_details.append(f"JSON serialization failed: {str(e)}")
            print(f"   ❌ JSON serialization failed: {str(e)}")
        
        if corruption_found:
            corrupted_employees.append({
                'id': emp_id,
                'name': emp_name,
                'issues': corruption_details,
                'full_record': emp
            })
    
    print(f"\n" + "=" * 60)
    print(f"🎯 CORRUPTION ANALYSIS SUMMARY")
    print(f"=" * 60)
    print(f"Total employees checked: {len(employees)}")
    print(f"Corrupted employees found: {len(corrupted_employees)}")
    
    if corrupted_employees:
        print(f"\n🚨 CORRUPTED EMPLOYEES:")
        for corrupt in corrupted_employees:
            print(f"   - {corrupt['name']} ({corrupt['id']})")
            for issue in corrupt['issues']:
                print(f"     * {issue}")
    else:
        print(f"\n✅ No corruption detected in employee data")
    
    return corrupted_employees

async def fix_corrupted_data(corrupted_employees):
    """Fix corrupted float values"""
    if not corrupted_employees:
        print("No corrupted data to fix")
        return
    
    print(f"\n🔧 FIXING CORRUPTED DATA")
    print(f"=" * 60)
    
    for corrupt in corrupted_employees:
        emp_id = corrupt['id']
        emp_name = corrupt['name']
        
        print(f"\n🔧 Fixing employee: {emp_name} ({emp_id})")
        
        # Get the full employee record
        employee = await db.employees.find_one({"id": emp_id})
        if not employee:
            print(f"   ❌ Employee not found in database")
            continue
        
        update_fields = {}
        
        # Fix main balance fields
        for field in ['breakfast_balance', 'drinks_sweets_balance']:
            value = employee.get(field)
            if value is not None and isinstance(value, (int, float)):
                if math.isnan(value) or math.isinf(value):
                    update_fields[field] = 0.0
                    print(f"   🔧 Fixed {field}: {value} → 0.0")
        
        # Fix subaccount balances
        subaccounts = employee.get('subaccount_balances', {})
        if subaccounts:
            fixed_subaccounts = {}
            for dept_id, balances in subaccounts.items():
                if isinstance(balances, dict):
                    fixed_balances = {}
                    for balance_type, balance_value in balances.items():
                        if balance_value is not None and isinstance(balance_value, (int, float)):
                            if math.isnan(balance_value) or math.isinf(balance_value):
                                fixed_balances[balance_type] = 0.0
                                print(f"   🔧 Fixed subaccount_balances.{dept_id}.{balance_type}: {balance_value} → 0.0")
                            else:
                                fixed_balances[balance_type] = balance_value
                        else:
                            fixed_balances[balance_type] = balance_value
                    fixed_subaccounts[dept_id] = fixed_balances
                else:
                    fixed_subaccounts[dept_id] = balances
            
            if fixed_subaccounts != subaccounts:
                update_fields['subaccount_balances'] = fixed_subaccounts
        
        # Apply fixes
        if update_fields:
            result = await db.employees.update_one(
                {"id": emp_id},
                {"$set": update_fields}
            )
            
            if result.modified_count > 0:
                print(f"   ✅ Successfully updated employee {emp_name}")
            else:
                print(f"   ❌ Failed to update employee {emp_name}")
        else:
            print(f"   ℹ️  No fixes needed for {emp_name}")

async def main():
    """Main debug function"""
    try:
        # Check for corruption
        corrupted_employees = await check_employee_data()
        
        # Fix corruption if found
        if corrupted_employees:
            print(f"\n❓ Fix corrupted data? (y/n): ", end="")
            response = input().strip().lower()
            if response == 'y':
                await fix_corrupted_data(corrupted_employees)
                
                # Verify fix
                print(f"\n🔍 VERIFYING FIXES...")
                await check_employee_data()
        
        # Test the endpoint after fixes
        print(f"\n🧪 TESTING ENDPOINT AFTER FIXES...")
        employees = await db.employees.find({"department_id": "fw4abteilung1"}).to_list(1000)
        
        try:
            json_data = json.dumps(employees, default=str)
            print(f"   ✅ Endpoint should work now - JSON serialization successful")
            print(f"   📊 Total employees: {len(employees)}")
        except Exception as e:
            print(f"   ❌ Endpoint still broken: {str(e)}")
        
    except Exception as e:
        print(f"💥 Debug script failed: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())