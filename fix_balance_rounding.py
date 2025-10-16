#!/usr/bin/env python3
"""
BALANCE ROUNDING FIX SCRIPT

Behebt Fließkomma-Rundungsfehler in bestehenden Mitarbeiter-Salden.
Rundet alle Salden auf genau 2 Dezimalstellen und verhindert -0.00 Anzeigen.
"""

import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/backend/.env')

def round_to_cents(amount):
    """Round amount to exactly 2 decimal places and avoid -0.00"""
    if amount is None:
        return 0.0
    rounded = round(float(amount), 2)
    return 0.0 if rounded == -0.0 else rounded

async def fix_balance_rounding():
    """Fix rounding issues in employee balances"""
    
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'fw_kantine_production')
    
    print(f"🔄 Connecting to MongoDB: {mongo_url}")
    print(f"🔄 Database: {db_name}")
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        employees = await db.employees.find({}).to_list(1000)
        print(f"\n📊 Found {len(employees)} employees to process")
        
        fixed_count = 0
        
        for employee in employees:
            updates = {}
            needs_update = False
            
            # Fix main balances
            breakfast_balance = employee.get('breakfast_balance', 0.0)
            drinks_balance = employee.get('drinks_sweets_balance', 0.0)
            
            rounded_breakfast = round_to_cents(breakfast_balance)
            rounded_drinks = round_to_cents(drinks_balance)
            
            if breakfast_balance != rounded_breakfast:
                updates['breakfast_balance'] = rounded_breakfast
                needs_update = True
                print(f"  {employee['name']}: Breakfast {breakfast_balance} → {rounded_breakfast}")
            
            if drinks_balance != rounded_drinks:
                updates['drinks_sweets_balance'] = rounded_drinks
                needs_update = True
                print(f"  {employee['name']}: Drinks {drinks_balance} → {rounded_drinks}")
            
            # Fix subaccount balances
            subaccounts = employee.get('subaccount_balances', {})
            if subaccounts:
                fixed_subaccounts = {}
                for dept_id, balances in subaccounts.items():
                    fixed_subaccounts[dept_id] = {
                        'breakfast': round_to_cents(balances.get('breakfast', 0.0)),
                        'drinks': round_to_cents(balances.get('drinks', 0.0))
                    }
                    
                    # Check if subaccounts changed
                    if (balances.get('breakfast', 0.0) != fixed_subaccounts[dept_id]['breakfast'] or
                        balances.get('drinks', 0.0) != fixed_subaccounts[dept_id]['drinks']):
                        needs_update = True
                        print(f"  {employee['name']}: Fixed subaccount {dept_id}")
                
                if needs_update and 'subaccount_balances' not in updates:
                    updates['subaccount_balances'] = fixed_subaccounts
            
            # Update employee if needed
            if needs_update:
                await db.employees.update_one(
                    {"id": employee["id"]},
                    {"$set": updates}
                )
                fixed_count += 1
        
        print(f"\n✅ Fixed balance rounding for {fixed_count} employees")
        print("🎉 Balance rounding fix completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during balance rounding fix: {str(e)}")
        return False
    finally:
        client.close()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(fix_balance_rounding())
    if not success:
        exit(1)