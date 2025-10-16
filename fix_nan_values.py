#!/usr/bin/env python3
"""
Fix NaN values in fw4abteilung1 employee data
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

async def fix_nan_values():
    """Fix NaN values in employee data"""
    print("🔧 FIXING NaN VALUES IN FW4ABTEILUNG1 EMPLOYEES")
    print("=" * 60)
    
    # Find employees with NaN values
    employees = await db.employees.find({"department_id": "fw4abteilung1"}).to_list(1000)
    
    fixed_count = 0
    
    for emp in employees:
        emp_id = emp.get('id', 'NO_ID')
        emp_name = emp.get('name', 'NO_NAME')
        
        update_fields = {}
        
        # Check and fix main balance fields
        for field in ['breakfast_balance', 'drinks_sweets_balance']:
            value = emp.get(field)
            if value is not None and isinstance(value, (int, float)):
                if math.isnan(value) or math.isinf(value):
                    update_fields[field] = 0.0
                    print(f"   🔧 Fixing {emp_name} ({emp_id[:8]}): {field} = {value} → 0.0")
        
        # Check and fix subaccount balances
        subaccounts = emp.get('subaccount_balances', {})
        if subaccounts:
            fixed_subaccounts = {}
            subaccounts_changed = False
            
            for dept_id, balances in subaccounts.items():
                if isinstance(balances, dict):
                    fixed_balances = {}
                    for balance_type, balance_value in balances.items():
                        if balance_value is not None and isinstance(balance_value, (int, float)):
                            if math.isnan(balance_value) or math.isinf(balance_value):
                                fixed_balances[balance_type] = 0.0
                                subaccounts_changed = True
                                print(f"   🔧 Fixing {emp_name} ({emp_id[:8]}): subaccount_balances.{dept_id}.{balance_type} = {balance_value} → 0.0")
                            else:
                                fixed_balances[balance_type] = balance_value
                        else:
                            fixed_balances[balance_type] = balance_value
                    fixed_subaccounts[dept_id] = fixed_balances
                else:
                    fixed_subaccounts[dept_id] = balances
            
            if subaccounts_changed:
                update_fields['subaccount_balances'] = fixed_subaccounts
        
        # Apply fixes
        if update_fields:
            result = await db.employees.update_one(
                {"id": emp_id},
                {"$set": update_fields}
            )
            
            if result.modified_count > 0:
                print(f"   ✅ Successfully fixed employee {emp_name}")
                fixed_count += 1
            else:
                print(f"   ❌ Failed to fix employee {emp_name}")
    
    print(f"\n📊 SUMMARY: Fixed {fixed_count} employees")
    
    # Test JSON serialization after fixes
    print(f"\n🧪 TESTING JSON SERIALIZATION...")
    employees_after = await db.employees.find({"department_id": "fw4abteilung1"}).to_list(1000)
    
    try:
        json_data = json.dumps(employees_after, default=str)
        print(f"   ✅ JSON serialization successful - {len(employees_after)} employees")
        return True
    except Exception as e:
        print(f"   ❌ JSON serialization still failing: {str(e)}")
        return False

async def main():
    """Main function"""
    try:
        success = await fix_nan_values()
        if success:
            print(f"\n🎉 FIX COMPLETED SUCCESSFULLY!")
            print(f"The /api/departments/fw4abteilung1/employees endpoint should now work.")
        else:
            print(f"\n❌ FIX FAILED - Additional issues remain")
    except Exception as e:
        print(f"💥 Fix script failed: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())