#!/usr/bin/env python3
"""
🚨 CRITICAL DUPLICATION BUG FIX TEST: Test employee duplication fix in daily overview

CRITICAL DUPLICATION BUG TEST:

1. **Create Test Scenario:**
   - Create 3 employees: Employee1, Employee2, Employee3
   - Employee1: Create breakfast order (rolls, eggs, coffee, lunch)
   - Employee2: Create breakfast order (rolls, eggs, coffee, lunch)  
   - Employee3: Create NO ORDERS (will be sponsor only)

2. **Test Mixed Sponsoring:**
   - Employee1 sponsors breakfast for Employee2 (Employee1 has both own orders AND sponsors)
   - Employee3 sponsors lunch for Employee2 (Employee3 has no own orders, only sponsors)

3. **CRITICAL Bug Test - Check for Duplicates:**
   - Call GET /api/orders/breakfast-history/{department_id}
   - CRITICAL: Each employee should appear ONLY ONCE in employee_orders
   - Employee1: Should show own orders + sponsored_breakfast info (NO DUPLICATE)
   - Employee2: Should show own orders with sponsored meal adjustments (NO DUPLICATE)
   - Employee3: Should show empty orders + sponsored_lunch info (NO DUPLICATE)

4. **Verify Correct Structure:**
   - Employee1: Has own order items + sponsored_breakfast data + correct total_amount
   - Employee2: Has own order items + correct remaining total_amount after sponsoring
   - Employee3: Has zero order items + sponsored_lunch data + sponsored total_amount

5. **Count Verification:**
   - Total employees in employee_orders should equal 3 (not 4, 5, or 6)
   - No employee names should be duplicated
   - All sponsoring information should be correctly assigned

EXPECTED RESULT: 
- NO employee duplicates in daily overview
- Each employee appears exactly once with correct sponsoring information
- Sponsor totals calculated correctly without duplication

Use Department 2 (fw4abteilung2) with admin2 credentials.
"""

import requests
import json
from datetime import datetime, timedelta
import pytz
import os
from typing import Dict, List, Any

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteenio.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test Configuration
DEPARTMENT_ID = "fw4abteilung2"  # Department 2
ADMIN_PASSWORD = "admin2"
DEPARTMENT_NAME = "2. Wachabteilung"

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

class DuplicationBugFixTest:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.employee1_id = None
        self.employee2_id = None
        self.employee3_id = None
        self.test_employees = []
        self.test_orders = []
        
    def cleanup_test_data(self) -> bool:
        """Clean up test data to create fresh scenario"""
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/debug-cleanup/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully cleaned up test data: {result}")
                return True
            else:
                print(f"⚠️ Cleanup failed (continuing anyway): {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Cleanup error (continuing anyway): {e}")
            return False
    
    def get_berlin_date(self):
        """Get current date in Berlin timezone"""
        return datetime.now(BERLIN_TZ).date().strftime('%Y-%m-%d')
        
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
    
    def create_breakfast_order(self, employee_id: str, employee_name: str) -> Dict:
        """Create a breakfast order with rolls, eggs, coffee, and lunch"""
        try:
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # 2 rolls
                    "white_halves": 2,
                    "seeded_halves": 2,
                    "toppings": ["butter", "kaese", "salami", "schinken"],
                    "has_lunch": True,
                    "boiled_eggs": 2,
                    "has_coffee": True
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                
                print(f"✅ Created breakfast order for {employee_name}: {order_id} (€{order['total_price']:.2f})")
                self.test_orders.append({
                    "employee_id": employee_id,
                    "employee_name": employee_name,
                    "order_id": order_id,
                    "total_price": order["total_price"]
                })
                return {
                    "order_id": order_id,
                    "total_price": order["total_price"]
                }
            else:
                print(f"❌ Failed to create breakfast order for {employee_name}: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating breakfast order for {employee_name}: {e}")
            return None
    
    def sponsor_breakfast_meals(self, sponsor_employee_id: str, sponsor_name: str) -> Dict:
        """Sponsor breakfast meals for employees"""
        try:
            today = self.get_berlin_date()
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": sponsor_employee_id,
                "sponsor_employee_name": sponsor_name
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully sponsored breakfast meals: {result}")
                return result
            else:
                print(f"❌ Failed to sponsor breakfast meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error sponsoring breakfast meals: {e}")
            return {"error": str(e)}
    
    def sponsor_lunch_meals(self, sponsor_employee_id: str, sponsor_name: str) -> Dict:
        """Sponsor lunch meals for employees"""
        try:
            today = self.get_berlin_date()
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": sponsor_employee_id,
                "sponsor_employee_name": sponsor_name
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully sponsored lunch meals: {result}")
                return result
            else:
                print(f"❌ Failed to sponsor lunch meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error sponsoring lunch meals: {e}")
            return {"error": str(e)}
    
    def get_breakfast_history(self) -> Dict:
        """Get breakfast history from breakfast-history endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Successfully retrieved breakfast history")
                return data
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error getting breakfast history: {e}")
            return {"error": str(e)}
    
    def verify_no_duplicates(self, employee_orders: Dict) -> Dict:
        """
        CRITICAL: Verify no employee duplicates in daily overview
        """
        results = {
            "no_duplicates": False,
            "total_employees": len(employee_orders),
            "expected_employees": 3,
            "employee_names": list(employee_orders.keys()),
            "duplicate_names": [],
            "missing_employees": [],
            "extra_employees": []
        }
        
        print(f"\n🔍 CRITICAL Duplication Test: Verify No Employee Duplicates")
        print(f"Expected: Exactly 3 employees (Employee1, Employee2, Employee3)")
        print(f"Found: {results['total_employees']} employees")
        
        # Check for exact count
        if results['total_employees'] == results['expected_employees']:
            print(f"✅ Employee count correct: {results['total_employees']} employees")
        else:
            print(f"❌ Employee count incorrect: Expected {results['expected_employees']}, found {results['total_employees']}")
        
        # Check for duplicates by name pattern
        employee_patterns = {}
        for name in results['employee_names']:
            # Extract base pattern (Employee1, Employee2, Employee3)
            if 'Employee1' in name:
                pattern = 'Employee1'
            elif 'Employee2' in name:
                pattern = 'Employee2'
            elif 'Employee3' in name:
                pattern = 'Employee3'
            else:
                pattern = 'Other'
            
            if pattern not in employee_patterns:
                employee_patterns[pattern] = []
            employee_patterns[pattern].append(name)
        
        # Check for duplicates
        for pattern, names in employee_patterns.items():
            if len(names) > 1:
                results['duplicate_names'].extend(names)
                print(f"❌ DUPLICATE DETECTED: {pattern} appears {len(names)} times: {names}")
            else:
                print(f"✅ No duplicates for {pattern}: {names}")
        
        # Verify we have all expected employees
        expected_patterns = ['Employee1', 'Employee2', 'Employee3']
        for pattern in expected_patterns:
            if pattern not in employee_patterns:
                results['missing_employees'].append(pattern)
                print(f"❌ Missing employee: {pattern}")
        
        # Check for extra employees
        for pattern in employee_patterns:
            if pattern not in expected_patterns and pattern != 'Other':
                results['extra_employees'].append(pattern)
                print(f"⚠️ Extra employee pattern: {pattern}")
        
        # Determine if test passed
        if (results['total_employees'] == results['expected_employees'] and 
            len(results['duplicate_names']) == 0 and 
            len(results['missing_employees']) == 0):
            results['no_duplicates'] = True
            print(f"✅ DUPLICATION TEST PASSED: No duplicates detected")
        else:
            print(f"❌ DUPLICATION TEST FAILED: Duplicates or count issues detected")
        
        return results
    
    def verify_sponsoring_structure(self, employee_orders: Dict) -> Dict:
        """
        Verify correct sponsoring structure for each employee
        """
        results = {
            "structure_correct": False,
            "employee1_correct": False,
            "employee2_correct": False,
            "employee3_correct": False,
            "sponsoring_details": {}
        }
        
        print(f"\n🔍 Sponsoring Structure Verification")
        
        for employee_name, employee_data in employee_orders.items():
            total_amount = employee_data.get("total_amount", 0)
            sponsored_breakfast = employee_data.get("sponsored_breakfast")
            sponsored_lunch = employee_data.get("sponsored_lunch")
            has_own_orders = any([
                employee_data.get("white_halves", 0) > 0,
                employee_data.get("seeded_halves", 0) > 0,
                employee_data.get("boiled_eggs", 0) > 0
            ])
            
            results["sponsoring_details"][employee_name] = {
                "total_amount": total_amount,
                "has_own_orders": has_own_orders,
                "sponsored_breakfast": sponsored_breakfast,
                "sponsored_lunch": sponsored_lunch
            }
            
            # Identify employee type
            if 'Employee1' in employee_name:
                # Employee1: Should have own orders + higher total (because they sponsor others, they pay more)
                # Employee1 sponsors breakfast for others, so their total should be higher than normal
                if has_own_orders and total_amount > 10.0:  # Higher due to sponsoring costs
                    results["employee1_correct"] = True
                    print(f"✅ Employee1 structure correct: Own orders + sponsors others (€{total_amount:.2f})")
                else:
                    print(f"❌ Employee1 structure incorrect: Own orders={has_own_orders}, Total amount=€{total_amount:.2f} (should be >€10)")
            
            elif 'Employee2' in employee_name:
                # Employee2: Should have own orders with sponsored meal adjustments (low total_amount)
                if has_own_orders and total_amount < 5.0:  # Should be low due to being sponsored
                    results["employee2_correct"] = True
                    print(f"✅ Employee2 structure correct: Own orders with sponsored adjustments (€{total_amount:.2f})")
                else:
                    print(f"❌ Employee2 structure incorrect: Own orders={has_own_orders}, Total amount=€{total_amount:.2f} (should be <€5)")
            
            elif 'Employee3' in employee_name:
                # Employee3: Should have no own orders + sponsored_lunch info (they sponsor lunch for others)
                if not has_own_orders and sponsored_lunch is not None:
                    results["employee3_correct"] = True
                    print(f"✅ Employee3 structure correct: No own orders + sponsors lunch (€{total_amount:.2f})")
                else:
                    print(f"❌ Employee3 structure incorrect: Own orders={has_own_orders}, Sponsors lunch={sponsored_lunch is not None}, Total=€{total_amount:.2f}")
        
        # Overall structure check
        if (results["employee1_correct"] and 
            results["employee2_correct"] and 
            results["employee3_correct"]):
            results["structure_correct"] = True
            print(f"✅ SPONSORING STRUCTURE CORRECT: All employees have correct structure")
        else:
            print(f"❌ SPONSORING STRUCTURE INCORRECT: Some employees have wrong structure")
        
        return results
    
    def run_duplication_test(self):
        """Run the comprehensive duplication bug fix test"""
        print("🚨 CRITICAL DUPLICATION BUG FIX TEST: Test employee duplication fix in daily overview")
        print("=" * 90)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication Test")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Try to cleanup existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create Test Scenario (EXACT from review request)
        print(f"\n2️⃣ Creating Test Scenario for Department {DEPARTMENT_ID}")
        
        # Create Employee1
        employee1_name = f"Employee1_{datetime.now().strftime('%H%M%S')}"
        self.employee1_id = self.create_test_employee(employee1_name)
        
        if not self.employee1_id:
            print("❌ CRITICAL FAILURE: Cannot create Employee1")
            return False
        
        # Create Employee2
        employee2_name = f"Employee2_{datetime.now().strftime('%H%M%S')}"
        self.employee2_id = self.create_test_employee(employee2_name)
        
        if not self.employee2_id:
            print("❌ CRITICAL FAILURE: Cannot create Employee2")
            return False
        
        # Create Employee3 (will be sponsor only, no orders)
        employee3_name = f"Employee3_{datetime.now().strftime('%H%M%S')}"
        self.employee3_id = self.create_test_employee(employee3_name)
        
        if not self.employee3_id:
            print("❌ CRITICAL FAILURE: Cannot create Employee3")
            return False
        
        # Step 3: Create Orders
        print(f"\n3️⃣ Creating Breakfast Orders")
        
        # Employee1: Create breakfast order (rolls, eggs, coffee, lunch)
        employee1_order = self.create_breakfast_order(self.employee1_id, employee1_name)
        if not employee1_order:
            print("❌ CRITICAL FAILURE: Cannot create Employee1's order")
            return False
        
        # Employee2: Create breakfast order (rolls, eggs, coffee, lunch)
        employee2_order = self.create_breakfast_order(self.employee2_id, employee2_name)
        if not employee2_order:
            print("❌ CRITICAL FAILURE: Cannot create Employee2's order")
            return False
        
        # Employee3: Create NO ORDERS (will be sponsor only)
        print(f"✅ Employee3 has no orders (will be sponsor only)")
        
        # Step 4: Test Mixed Sponsoring
        print(f"\n4️⃣ Testing Mixed Sponsoring Scenario")
        
        # Employee1 sponsors breakfast for Employee2 (Employee1 has both own orders AND sponsors)
        print(f"Employee1 sponsors breakfast for Employee2...")
        breakfast_result = self.sponsor_breakfast_meals(self.employee1_id, employee1_name)
        
        if "error" in breakfast_result and "bereits gesponsert" not in breakfast_result.get('error', ''):
            print(f"❌ Employee1 breakfast sponsoring failed: {breakfast_result['error']}")
            return False
        
        # Employee3 sponsors lunch for Employee2 (Employee3 has no own orders, only sponsors)
        print(f"Employee3 sponsors lunch for Employee2...")
        lunch_result = self.sponsor_lunch_meals(self.employee3_id, employee3_name)
        
        if "error" in lunch_result and "bereits gesponsert" not in lunch_result.get('error', ''):
            print(f"❌ Employee3 lunch sponsoring failed: {lunch_result['error']}")
            return False
        
        print(f"✅ Mixed sponsoring completed successfully")
        
        # Step 5: Get Breakfast History and Check for Duplicates
        print(f"\n5️⃣ Getting Breakfast History for Duplication Check")
        history_data = self.get_breakfast_history()
        
        if "error" in history_data:
            print(f"❌ CRITICAL FAILURE: Cannot get breakfast history: {history_data['error']}")
            return False
        
        # Step 6: Verify Data Structure
        print(f"\n6️⃣ Verifying Breakfast History Data Structure")
        
        if not isinstance(history_data, dict) or "history" not in history_data:
            print(f"❌ CRITICAL FAILURE: Invalid history data structure")
            return False
        
        history = history_data["history"]
        if not history or len(history) == 0:
            print(f"❌ CRITICAL FAILURE: No history data found")
            return False
        
        # Get today's data (should be first in list)
        today_data = history[0]
        employee_orders = today_data.get("employee_orders", {})
        
        if not employee_orders:
            print(f"❌ CRITICAL FAILURE: No employee orders found in today's data")
            return False
        
        print(f"✅ Found {len(employee_orders)} employees in today's breakfast history")
        
        # Step 7: CRITICAL Duplication Test
        print(f"\n7️⃣ CRITICAL Duplication Test - Check for Employee Duplicates")
        duplication_results = self.verify_no_duplicates(employee_orders)
        
        # Step 8: Verify Sponsoring Structure
        print(f"\n8️⃣ Verify Sponsoring Structure")
        structure_results = self.verify_sponsoring_structure(employee_orders)
        
        # Step 9: Detailed Employee Analysis
        print(f"\n9️⃣ Detailed Employee Analysis")
        for employee_name, employee_data in employee_orders.items():
            print(f"\n📊 {employee_name}:")
            print(f"   - Total Amount: €{employee_data.get('total_amount', 0):.2f}")
            print(f"   - White Halves: {employee_data.get('white_halves', 0)}")
            print(f"   - Seeded Halves: {employee_data.get('seeded_halves', 0)}")
            print(f"   - Boiled Eggs: {employee_data.get('boiled_eggs', 0)}")
            print(f"   - Has Coffee: {employee_data.get('has_coffee', False)}")
            print(f"   - Has Lunch: {employee_data.get('has_lunch', False)}")
            print(f"   - Sponsored Breakfast: {employee_data.get('sponsored_breakfast')}")
            print(f"   - Sponsored Lunch: {employee_data.get('sponsored_lunch')}")
        
        # Final Results
        print(f"\n🏁 FINAL RESULTS:")
        
        success_criteria = [
            (duplication_results["no_duplicates"], f"No Employee Duplicates: {duplication_results['total_employees']} employees (expected 3)"),
            (structure_results["structure_correct"], f"Correct Sponsoring Structure: Employee1={structure_results['employee1_correct']}, Employee2={structure_results['employee2_correct']}, Employee3={structure_results['employee3_correct']}"),
            (len(duplication_results["duplicate_names"]) == 0, f"No Duplicate Names: {len(duplication_results['duplicate_names'])} duplicates found"),
            (len(duplication_results["missing_employees"]) == 0, f"All Expected Employees Present: {len(duplication_results['missing_employees'])} missing"),
            (duplication_results["total_employees"] == 3, f"Correct Employee Count: {duplication_results['total_employees']} (expected 3)")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Overall Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        if success_rate == 100:
            print("🎉 CRITICAL DUPLICATION BUG FIX VERIFICATION SUCCESSFUL!")
            print("✅ NO employee duplicates detected in daily overview")
            print("✅ Each employee appears exactly once with correct sponsoring information")
            print("✅ Sponsor totals calculated correctly without duplication")
            print("✅ Mixed sponsoring scenario working correctly")
            return True
        else:
            print("🚨 CRITICAL DUPLICATION BUG DETECTED!")
            print("❌ Employee duplication or structure issues found")
            if duplication_results["duplicate_names"]:
                print(f"❌ Duplicate employees: {duplication_results['duplicate_names']}")
            return False

def main():
    """Main test execution"""
    test = DuplicationBugFixTest()
    
    try:
        success = test.run_duplication_test()
        
        if success:
            print(f"\n✅ DUPLICATION BUG FIX: VERIFIED WORKING")
            exit(0)
        else:
            print(f"\n❌ DUPLICATION BUG FIX: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()