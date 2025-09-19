#!/usr/bin/env python3
"""
Check Department 2 Pricing to understand the calculation difference
"""

import asyncio
import aiohttp
import json
import os

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://fire-meals.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class PricingChecker:
    def __init__(self):
        self.session = None
        
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
        except Exception as e:
            print(f"❌ Request failed: {method} {url} - {str(e)}")
            return None, 500
    
    async def check_department_pricing(self, department_id, department_name):
        """Check pricing for a specific department"""
        print(f"\n🔍 Checking pricing for {department_name} ({department_id}):")
        
        # Get breakfast menu
        breakfast_response, status = await self.make_request('GET', f'/menu/breakfast/{department_id}')
        if status == 200:
            print(f"   Breakfast Menu:")
            white_price = 0.0
            seeded_price = 0.0
            for item in breakfast_response:
                roll_type = item.get('roll_type', 'Unknown')
                price = item.get('price', 0.0)
                print(f"      {roll_type}: €{price}")
                if roll_type == 'weiss':
                    white_price = price
                elif roll_type == 'koerner':
                    seeded_price = price
        else:
            print(f"   ❌ Failed to get breakfast menu: {breakfast_response}")
            return
        
        # Get department settings
        dept_settings_response, status = await self.make_request('GET', f'/department-settings/{department_id}')
        if status == 200:
            boiled_eggs_price = dept_settings_response.get('boiled_eggs_price', 0.0)
            fried_eggs_price = dept_settings_response.get('fried_eggs_price', 0.0)
            coffee_price = dept_settings_response.get('coffee_price', 0.0)
            
            print(f"   Department Settings:")
            print(f"      Boiled Eggs: €{boiled_eggs_price}")
            print(f"      Fried Eggs: €{fried_eggs_price}")
            print(f"      Coffee: €{coffee_price}")
        else:
            print(f"   ❌ Failed to get department settings: {dept_settings_response}")
            return
        
        # Calculate expected costs for standard order
        print(f"   Expected Costs for Standard Order:")
        print(f"      1 white roll: €{white_price}")
        print(f"      1 seeded roll: €{seeded_price}")
        print(f"      1 boiled egg: €{boiled_eggs_price}")
        print(f"      1 coffee: €{coffee_price}")
        
        breakfast_portion = white_price + seeded_price + boiled_eggs_price
        total_with_coffee = breakfast_portion + coffee_price
        
        print(f"      Breakfast portion (rolls + eggs): €{breakfast_portion}")
        print(f"      Total with coffee: €{total_with_coffee}")
        
        return {
            'white_price': white_price,
            'seeded_price': seeded_price,
            'boiled_eggs_price': boiled_eggs_price,
            'coffee_price': coffee_price,
            'breakfast_portion': breakfast_portion,
            'total_with_coffee': total_with_coffee
        }
    
    async def compare_departments(self):
        """Compare pricing between departments"""
        print("🔍 DEPARTMENT PRICING COMPARISON")
        print("=" * 40)
        
        departments = [
            ("fw4abteilung1", "1. Wachabteilung"),
            ("fw4abteilung2", "2. Wachabteilung")
        ]
        
        pricing_data = {}
        
        for dept_id, dept_name in departments:
            pricing = await self.check_department_pricing(dept_id, dept_name)
            if pricing:
                pricing_data[dept_id] = pricing
        
        # Compare the results
        if len(pricing_data) >= 2:
            print(f"\n📊 COMPARISON ANALYSIS:")
            dept1_data = pricing_data.get('fw4abteilung1', {})
            dept2_data = pricing_data.get('fw4abteilung2', {})
            
            print(f"   Department 1 breakfast portion: €{dept1_data.get('breakfast_portion', 0.0)}")
            print(f"   Department 2 breakfast portion: €{dept2_data.get('breakfast_portion', 0.0)}")
            
            dept1_breakfast = dept1_data.get('breakfast_portion', 0.0)
            dept2_breakfast = dept2_data.get('breakfast_portion', 0.0)
            
            if abs(dept1_breakfast - dept2_breakfast) > 0.01:
                print(f"   ⚠️  PRICING DIFFERENCE DETECTED!")
                print(f"   Difference: €{abs(dept1_breakfast - dept2_breakfast):.2f}")
            else:
                print(f"   ✅ Breakfast portions are the same")
            
            # Check if department 2's breakfast portion matches the observed €2.25
            if abs(dept2_breakfast - 2.25) < 0.01:
                print(f"   🎯 FOUND THE ISSUE: Department 2 breakfast portion (€{dept2_breakfast}) matches observed sponsoring amount (€2.25)")
                print(f"   This suggests coffee is being incorrectly included in breakfast sponsoring")
            elif abs(dept2_data.get('total_with_coffee', 0.0) - 2.25) < 0.01:
                print(f"   🎯 FOUND THE ISSUE: Department 2 total with coffee (€{dept2_data.get('total_with_coffee', 0.0)}) matches observed sponsoring amount (€2.25)")
                print(f"   This confirms coffee is being incorrectly included in breakfast sponsoring")

async def main():
    """Main execution"""
    async with PricingChecker() as checker:
        await checker.compare_departments()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n💥 Check failed with exception: {str(e)}")
        exit(1)