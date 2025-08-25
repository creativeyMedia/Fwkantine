#!/usr/bin/env python3
"""
MENU RESTORATION TEST: Fix missing menu items causing HTTP 422 errors

ROOT CAUSE IDENTIFIED: All menu items are missing from the database, causing order validation to fail.
This test will attempt to restore menu items and then test order creation.
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "https://fw-kantine.de/api"

class MenuRestorationTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        self.department_id = None
        self.admin_authenticated = False
        
    def authenticate_as_admin(self):
        """Authenticate as department admin to create menu items"""
        try:
            # Try to authenticate as admin for department 1
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": "1. Wachabteilung",
                "admin_password": "admin1"
            })
            
            if response.status_code == 200:
                data = response.json()
                self.department_id = data.get("department_id")
                self.admin_authenticated = True
                print(f"✅ Admin authentication successful for department: {self.department_id}")
                return True
            else:
                print(f"❌ Admin authentication failed: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Admin authentication error: {str(e)}")
            return False
    
    def create_breakfast_items(self):
        """Create basic breakfast menu items"""
        if not self.admin_authenticated:
            print("❌ Cannot create breakfast items - not authenticated as admin")
            return False
        
        breakfast_items = [
            {"roll_type": "weiss", "price": 0.50, "department_id": self.department_id},
            {"roll_type": "koerner", "price": 0.60, "department_id": self.department_id}
        ]
        
        success_count = 0
        
        for item in breakfast_items:
            try:
                response = self.session.post(f"{BASE_URL}/department-admin/menu/breakfast", json=item)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Created breakfast item: {item['roll_type']} - €{item['price']}")
                    success_count += 1
                else:
                    print(f"❌ Failed to create breakfast item {item['roll_type']}: HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error creating breakfast item {item['roll_type']}: {str(e)}")
        
        return success_count > 0
    
    def create_topping_items(self):
        """Create basic topping menu items"""
        if not self.admin_authenticated:
            print("❌ Cannot create topping items - not authenticated as admin")
            return False
        
        topping_items = [
            {"topping_id": "ruehrei", "topping_name": "Rührei", "price": 0.00, "department_id": self.department_id},
            {"topping_id": "kaese", "topping_name": "Käse", "price": 0.00, "department_id": self.department_id},
            {"topping_id": "schinken", "topping_name": "Schinken", "price": 0.00, "department_id": self.department_id},
            {"topping_id": "butter", "topping_name": "Butter", "price": 0.00, "department_id": self.department_id}
        ]
        
        success_count = 0
        
        for item in topping_items:
            try:
                response = self.session.post(f"{BASE_URL}/department-admin/menu/toppings", json=item)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Created topping item: {item['topping_name']} - €{item['price']}")
                    success_count += 1
                else:
                    print(f"❌ Failed to create topping item {item['topping_name']}: HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"❌ Error creating topping item {item['topping_name']}: {str(e)}")
        
        return success_count > 0
    
    def verify_menu_items_created(self):
        """Verify that menu items were successfully created"""
        try:
            # Check breakfast items
            breakfast_response = self.session.get(f"{BASE_URL}/menu/breakfast/{self.department_id}")
            if breakfast_response.status_code == 200:
                breakfast_items = breakfast_response.json()
                print(f"✅ Breakfast menu now has {len(breakfast_items)} items")
                
                # Check toppings items
                toppings_response = self.session.get(f"{BASE_URL}/menu/toppings/{self.department_id}")
                if toppings_response.status_code == 200:
                    toppings_items = toppings_response.json()
                    print(f"✅ Toppings menu now has {len(toppings_items)} items")
                    
                    return len(breakfast_items) > 0 and len(toppings_items) > 0
                else:
                    print(f"❌ Failed to verify toppings: HTTP {toppings_response.status_code}")
                    return False
            else:
                print(f"❌ Failed to verify breakfast items: HTTP {breakfast_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying menu items: {str(e)}")
            return False
    
    def test_order_creation_after_fix(self):
        """Test order creation after menu items are restored"""
        try:
            # First authenticate as regular user
            user_response = self.session.post(f"{BASE_URL}/login/department", json={
                "department_name": "1. Wachabteilung",
                "password": "password1"
            })
            
            if user_response.status_code != 200:
                print(f"❌ User authentication failed: HTTP {user_response.status_code}")
                return False
            
            # Create a test employee
            employee_data = {
                "name": "Test Employee for Fixed Order",
                "department_id": self.department_id
            }
            
            employee_response = self.session.post(f"{BASE_URL}/employees", json=employee_data)
            
            if employee_response.status_code == 200:
                employee = employee_response.json()
                employee_id = employee.get("id")
                print(f"✅ Created test employee: {employee_id}")
                
                # Now test order creation
                order_data = {
                    "employee_id": employee_id,
                    "department_id": self.department_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["ruehrei", "kaese"],
                        "has_lunch": False,
                        "boiled_eggs": 0,
                        "has_coffee": False
                    }]
                }
                
                print(f"Testing order creation with data: {json.dumps(order_data, indent=2)}")
                
                order_response = self.session.post(f"{BASE_URL}/orders", json=order_data)
                
                if order_response.status_code == 200:
                    order_result = order_response.json()
                    print(f"🎉 SUCCESS! Order created successfully!")
                    print(f"   Order ID: {order_result.get('id')}")
                    print(f"   Total Price: €{order_result.get('total_price')}")
                    print(f"   ✅ HTTP 422 ERROR FIXED!")
                    return True
                elif order_response.status_code == 422:
                    error_data = order_response.json()
                    print(f"❌ Still getting HTTP 422 error: {error_data}")
                    return False
                else:
                    print(f"❌ Order creation failed: HTTP {order_response.status_code}: {order_response.text}")
                    return False
                    
            else:
                print(f"❌ Failed to create test employee: HTTP {employee_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing order creation: {str(e)}")
            return False
    
    def run_menu_restoration_test(self):
        """Run the complete menu restoration test"""
        print("🔧 MENU RESTORATION TEST")
        print("=" * 60)
        print("Goal: Fix missing menu items causing HTTP 422 errors")
        print("=" * 60)
        
        # Step 1: Authenticate as admin
        print("\n🔍 STEP 1: Authenticate as Department Admin")
        if not self.authenticate_as_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Step 2: Create breakfast items
        print("\n🔍 STEP 2: Create Breakfast Menu Items")
        breakfast_success = self.create_breakfast_items()
        
        # Step 3: Create topping items
        print("\n🔍 STEP 3: Create Topping Menu Items")
        toppings_success = self.create_topping_items()
        
        # Step 4: Verify items were created
        print("\n🔍 STEP 4: Verify Menu Items Created")
        verification_success = self.verify_menu_items_created()
        
        # Step 5: Test order creation
        print("\n🔍 STEP 5: Test Order Creation After Fix")
        if verification_success:
            order_success = self.test_order_creation_after_fix()
        else:
            print("❌ Skipping order test - menu items not properly created")
            order_success = False
        
        # Summary
        print("\n" + "=" * 60)
        print("🔧 MENU RESTORATION TEST SUMMARY")
        print("=" * 60)
        
        if order_success:
            print("🎉 SUCCESS! Menu restoration completed successfully!")
            print("✅ HTTP 422 errors should now be fixed")
            print("✅ Order creation is working")
        else:
            print("❌ Menu restoration failed or incomplete")
            print("❌ HTTP 422 errors may persist")
        
        return order_success

def main():
    """Main function"""
    tester = MenuRestorationTester()
    
    try:
        success = tester.run_menu_restoration_test()
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()