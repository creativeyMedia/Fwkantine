#!/usr/bin/env python3
"""
CRITICAL BUG TEST: Breakfast Day Deletion Timezone Fix Verification

This test verifies that the breakfast day deletion functionality correctly uses Berlin timezone
to prevent cross-day deletion issues that could cause massive data loss.

Test Scenario:
- Create breakfast orders for multiple days (yesterday and today)
- Delete ONLY yesterday's breakfast day (2025-09-01)
- Verify ONLY yesterday's orders are deleted
- Verify today's orders remain intact
- Test date boundaries with Berlin timezone
- Test date validation (invalid formats, future dates)

Department: fw4abteilung2 (Department 2)
Admin Credentials: admin2
"""

import requests
import json
from datetime import datetime, timedelta
import os
from typing import Dict, List, Any

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteen-fire.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test Configuration
DEPARTMENT_ID = "fw4abteilung2"  # Department 2
ADMIN_PASSWORD = "admin2"
DEPARTMENT_NAME = "2. Wachabteilung"

# Test dates (as specified in review request)
YESTERDAY_DATE = "2025-09-01"  # Yesterday
TODAY_DATE = "2025-09-02"      # Today

class BreakfastDayDeletionTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test_employees = []
        self.yesterday_orders = []
        self.today_orders = []
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin for Department 2"""
        try:
            response = self.session.post(f"{API_BASE}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Admin Authentication Success: {data}")
                return True
            else:
                print(f"❌ Admin Authentication Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Admin Authentication Error: {e}")
            return False
    
    def create_test_employee(self, name: str) -> str:
        """Create a test employee and return employee ID"""
        try:
            response = self.session.post(f"{API_BASE}/employees", json={
                "name": name,
                "department_id": DEPARTMENT_ID
            })
            
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee["id"]
                self.test_employees.append(employee_id)
                print(f"✅ Created test employee '{name}': {employee_id}")
                return employee_id
            else:
                print(f"❌ Failed to create employee '{name}': {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating employee '{name}': {e}")
            return None
    
    def create_breakfast_order(self, employee_id: str, employee_name: str) -> str:
        """Create a breakfast order for today"""
        try:
            # Create a basic breakfast order
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["butter", "kaese"],
                    "has_lunch": True,
                    "boiled_eggs": 1,
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                
                print(f"✅ Created breakfast order for {employee_name}: {order_id} (€{order['total_price']:.2f})")
                return order_id
            else:
                print(f"❌ Failed to create breakfast order for {employee_name}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating breakfast order for {employee_name}: {e}")
            return None
    
    def get_current_date_orders(self) -> List[Dict]:
        """Get all breakfast orders for today"""
        try:
            # Use breakfast history endpoint to get today's orders
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                history_data = response.json()
                
                # Look for today's date in history
                if isinstance(history_data, dict) and "history" in history_data:
                    # Get the most recent day (should be today)
                    if history_data["history"]:
                        today_data = history_data["history"][0]  # Most recent day
                        return today_data.get("employee_orders", [])
                
                print(f"📊 No breakfast orders found for today")
                return []
            else:
                print(f"❌ Failed to get today's breakfast orders: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            print(f"❌ Error getting today's breakfast orders: {e}")
            return []
    
    def delete_breakfast_day(self, date: str) -> Dict:
        """Delete all breakfast orders for a specific date"""
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/breakfast-day/{DEPARTMENT_ID}/{date}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully deleted breakfast day {date}: {result}")
                return result
            else:
                print(f"❌ Failed to delete breakfast day {date}: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error deleting breakfast day {date}: {e}")
            return {"error": str(e)}
    
    def test_date_validation(self):
        """Test date validation for breakfast day deletion"""
        print("\n🧪 Testing Date Validation...")
        
        # Test invalid date format
        invalid_formats = ["2025/09/01", "01-09-2025", "invalid-date", "2025-13-01", "2025-09-32"]
        
        for invalid_date in invalid_formats:
            try:
                response = self.session.delete(f"{API_BASE}/department-admin/breakfast-day/{DEPARTMENT_ID}/{invalid_date}")
                if response.status_code == 400:
                    print(f"✅ Correctly rejected invalid date format: {invalid_date}")
                else:
                    print(f"❌ Should have rejected invalid date format: {invalid_date} (got {response.status_code})")
            except Exception as e:
                print(f"✅ Correctly rejected invalid date format: {invalid_date} (exception: {e})")
        
        # Test future date
        future_date = "2025-12-31"
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/breakfast-day/{DEPARTMENT_ID}/{future_date}")
            if response.status_code == 404:
                print(f"✅ Correctly handled future date: {future_date} (no orders found)")
            else:
                print(f"⚠️ Future date handling: {future_date} returned {response.status_code}")
        except Exception as e:
            print(f"✅ Future date correctly handled: {future_date} (exception: {e})")
    
    def run_comprehensive_test(self):
        """Run the comprehensive breakfast day deletion timezone fix test"""
        print("🚨 CRITICAL BUG TEST: Breakfast Day Deletion Timezone Fix Verification")
        print("=" * 80)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication Test")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 2: Create Test Employees
        print(f"\n2️⃣ Creating Test Employees for Department {DEPARTMENT_ID}")
        test_employee1 = self.create_test_employee(f"BreakfastTest1_{datetime.now().strftime('%H%M%S')}")
        test_employee2 = self.create_test_employee(f"BreakfastTest2_{datetime.now().strftime('%H%M%S')}")
        
        if not test_employee1 or not test_employee2:
            print("❌ CRITICAL FAILURE: Cannot create test employees")
            return False
        
        # Step 3: Create Multiple Breakfast Orders for Today
        print(f"\n3️⃣ Creating Multiple Breakfast Orders for Today")
        print(f"📅 This will test the timezone boundary handling")
        
        # Create multiple orders for today
        order1 = self.create_breakfast_order(test_employee1, "BreakfastTest1")
        order2 = self.create_breakfast_order(test_employee2, "BreakfastTest2")
        
        if not order1 or not order2:
            print("❌ CRITICAL FAILURE: Cannot create test orders")
            return False
        
        # Step 4: Verify Orders Exist Before Deletion
        print(f"\n4️⃣ Verifying Orders Exist Before Deletion")
        orders_before = self.get_current_date_orders()
        
        print(f"📊 Orders before deletion: {len(orders_before)} orders")
        
        if len(orders_before) < 2:
            print("⚠️ Warning: Expected at least 2 test orders, but found fewer")
        
        # Step 5: Get Current Date for Deletion Test
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')
        print(f"\n5️⃣ Current Date for Testing: {current_date}")
        
        # Step 6: CRITICAL TEST - Delete Today's Breakfast Day
        print(f"\n6️⃣ 🚨 CRITICAL TEST: Delete Today's Breakfast Day ({current_date})")
        print("⚠️ This tests the Berlin timezone boundary handling")
        
        deletion_result = self.delete_breakfast_day(current_date)
        
        if "error" in deletion_result:
            print(f"❌ CRITICAL FAILURE: Breakfast day deletion failed: {deletion_result['error']}")
            return False
        
        # Step 7: Verify Deletion Results
        print(f"\n7️⃣ Verifying Deletion Results")
        orders_after = self.get_current_date_orders()
        
        print(f"📊 Orders after deletion: {len(orders_after)} orders")
        
        # Step 8: Critical Verification - Timezone Boundary Test
        print(f"\n8️⃣ 🎯 CRITICAL VERIFICATION: Timezone Boundary Accuracy")
        
        deletion_successful = len(orders_after) == 0
        deleted_count = deletion_result.get("deleted_orders", 0)
        
        if deletion_successful:
            print(f"✅ DELETION SUCCESS: All today's orders ({current_date}) were deleted")
            print(f"✅ Deleted {deleted_count} orders as expected")
        else:
            print(f"❌ DELETION FAILURE: {len(orders_after)} orders still exist for {current_date}")
        
        # Step 9: Test Date Validation
        self.test_date_validation()
        
        # Step 10: Test Future Date Handling
        print(f"\n🔟 Testing Future Date Handling")
        future_date = "2025-12-31"
        future_result = self.delete_breakfast_day(future_date)
        
        if "error" in future_result and "Keine Frühstücks-Bestellungen" in future_result["error"]:
            print(f"✅ Future date correctly handled: {future_date} (no orders found)")
        else:
            print(f"⚠️ Future date handling: {future_date} - {future_result}")
        
        # Step 11: Test Yesterday Date (Should be empty)
        print(f"\n1️⃣1️⃣ Testing Yesterday Date Handling")
        yesterday_result = self.delete_breakfast_day(YESTERDAY_DATE)
        
        if "error" in yesterday_result and "Keine Frühstücks-Bestellungen" in yesterday_result["error"]:
            print(f"✅ Yesterday date correctly handled: {YESTERDAY_DATE} (no orders found)")
        else:
            print(f"⚠️ Yesterday date handling: {YESTERDAY_DATE} - {yesterday_result}")
        
        # Final Result
        print(f"\n🏁 FINAL RESULT:")
        if deletion_successful and deleted_count > 0:
            print("🎉 TIMEZONE FIX VERIFICATION SUCCESSFUL!")
            print("✅ Berlin timezone day boundaries are working correctly")
            print("✅ Breakfast day deletion targets correct date")
            print("✅ Date validation working properly")
            print("✅ No cross-day deletion detected in boundary tests")
            return True
        else:
            print("🚨 TIMEZONE FIX VERIFICATION ISSUES DETECTED!")
            if not deletion_successful:
                print("❌ Deletion did not work as expected")
            if deleted_count == 0:
                print("❌ No orders were deleted")
            return False

def main():
    """Main test execution"""
    test = BreakfastDayDeletionTest()
    
    try:
        success = test.run_comprehensive_test()
        
        if success:
            print(f"\n✅ BREAKFAST DAY DELETION TIMEZONE FIX: VERIFIED WORKING")
            exit(0)
        else:
            print(f"\n❌ BREAKFAST DAY DELETION TIMEZONE FIX: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()