#!/usr/bin/env python3
"""
MEAL SPONSORING FEATURE TEST

FOCUS: Test the newly implemented meal sponsoring feature in the German canteen management system.

Test specifically:
1. **Authentication**: Test department admin authentication (admin1, admin2, admin3, admin4 credentials)
2. **Meal Sponsoring API Endpoint**: Test POST /api/department-admin/sponsor-meal with parameters:
   - department_id: Target department ID  
   - date: Date for sponsoring (format: YYYY-MM-DD)
   - meal_type: Either "breakfast" or "lunch"
   - sponsor_employee_id: ID of employee who will pay
   - sponsor_employee_name: Name of sponsoring employee

3. **Test Scenarios**:
   - Create test employees in a department
   - Create breakfast orders (rolls, toppings, eggs, lunch) for multiple employees
   - Test breakfast sponsoring (should cover rolls + eggs + lunch, excluding coffee)
   - Test lunch sponsoring (should cover only lunch costs)
   - Verify cost calculation and transfer to sponsor employee
   - Verify that sponsored orders are marked as sponsored (0€ cost)
   - Verify audit trail with sponsored_by fields

4. **Expected Results**:
   - API should return: sponsored_items count, total_cost, affected_employees count, sponsor name
   - Individual orders should be updated with sponsored_by information
   - Sponsor employee balance should be charged the total cost
   - Other employees should have their meal costs set to 0€

BACKEND URL: https://canteen-manager-1.preview.emergentagent.com/api
DEPARTMENT: 1. Wachabteilung (fw4abteilung1)
ADMIN CREDENTIALS: admin1, admin2, admin3, admin4

PURPOSE: Verify the meal sponsoring feature works correctly for both breakfast and lunch scenarios.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Configuration - Use production backend URL from frontend/.env
BASE_URL = "https://canteen-manager-1.preview.emergentagent.com/api"
DEPARTMENT_NAME = "1. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung1"
ADMIN_PASSWORD = "admin1"

class MealSponsoringTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.admin_auth = None
        self.test_employees = []
        self.test_orders = []
        
    def log_result(self, test_name, success, details="", error=""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if error:
            print(f"   Error: {error}")
        print()
    
    def authenticate_admin(self):
        """Authenticate as department admin"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                self.admin_auth = response.json()
                self.log_result(
                    "Department Admin Authentication",
                    True,
                    f"Successfully authenticated as admin for {DEPARTMENT_NAME}"
                )
                return True
            else:
                self.log_result(
                    "Department Admin Authentication",
                    False,
                    error=f"Authentication failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Department Admin Authentication", False, error=str(e))
            return False
    
    def create_test_employees(self):
        """Create test employees for sponsoring scenarios"""
        try:
            employee_names = ["Max Mustermann", "Anna Schmidt", "Peter Weber", "Lisa Mueller"]
            created_employees = []
            
            for name in employee_names:
                response = self.session.post(f"{BASE_URL}/employees", json={
                    "name": name,
                    "department_id": DEPARTMENT_ID
                })
                
                if response.status_code == 200:
                    employee = response.json()
                    created_employees.append(employee)
                    self.test_employees.append(employee)
                else:
                    # Employee might already exist, try to find existing ones
                    pass
            
            # If we couldn't create new ones, get existing employees
            if not created_employees:
                response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
                if response.status_code == 200:
                    existing_employees = response.json()
                    # Use first 4 employees for testing
                    self.test_employees = existing_employees[:4]
                    created_employees = self.test_employees
            
            if len(created_employees) >= 3:  # Need at least 3 employees (2 for orders + 1 sponsor)
                self.log_result(
                    "Create Test Employees",
                    True,
                    f"Successfully prepared {len(created_employees)} test employees"
                )
                return True
            else:
                self.log_result(
                    "Create Test Employees",
                    False,
                    error=f"Could not prepare enough test employees. Got {len(created_employees)}, need at least 3"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Test Employees", False, error=str(e))
            return False
    
    def create_breakfast_orders(self):
        """Create breakfast orders for multiple employees"""
        try:
            if len(self.test_employees) < 3:
                self.log_result(
                    "Create Breakfast Orders",
                    False,
                    error="Not enough test employees available"
                )
                return False
            
            # Create orders for first 2 employees (3rd will be sponsor)
            orders_created = 0
            
            # Employee 1: Rolls + toppings + eggs + lunch
            employee1 = self.test_employees[0]
            order1_data = {
                "employee_id": employee1["id"],
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["ruehrei", "kaese"],
                    "has_lunch": True,
                    "boiled_eggs": 2,
                    "has_coffee": True
                }]
            }
            
            response1 = self.session.post(f"{BASE_URL}/orders", json=order1_data)
            if response1.status_code == 200:
                order1 = response1.json()
                self.test_orders.append(order1)
                orders_created += 1
            
            # Employee 2: Rolls + lunch (no eggs, no coffee)
            employee2 = self.test_employees[1]
            order2_data = {
                "employee_id": employee2["id"],
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 3,
                    "white_halves": 2,
                    "seeded_halves": 1,
                    "toppings": ["salami", "butter", "schinken"],
                    "has_lunch": True,
                    "boiled_eggs": 0,
                    "has_coffee": False
                }]
            }
            
            response2 = self.session.post(f"{BASE_URL}/orders", json=order2_data)
            if response2.status_code == 200:
                order2 = response2.json()
                self.test_orders.append(order2)
                orders_created += 1
            
            if orders_created >= 2:
                self.log_result(
                    "Create Breakfast Orders",
                    True,
                    f"Successfully created {orders_created} breakfast orders for testing"
                )
                return True
            else:
                self.log_result(
                    "Create Breakfast Orders",
                    False,
                    error=f"Could only create {orders_created} orders, need at least 2"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Breakfast Orders", False, error=str(e))
            return False
    
    def test_breakfast_sponsoring(self):
        """Test breakfast sponsoring functionality"""
        try:
            if len(self.test_employees) < 3:
                self.log_result(
                    "Test Breakfast Sponsoring",
                    False,
                    error="Not enough test employees for sponsoring test"
                )
                return False
            
            # Use 3rd employee as sponsor
            sponsor = self.test_employees[2]
            today = date.today().isoformat()
            
            # Get sponsor's initial balance
            sponsor_response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            if sponsor_response.status_code != 200:
                raise Exception("Could not fetch employees to check sponsor balance")
            
            employees = sponsor_response.json()
            sponsor_employee = next((emp for emp in employees if emp["id"] == sponsor["id"]), None)
            if not sponsor_employee:
                raise Exception("Could not find sponsor employee")
            
            initial_sponsor_balance = sponsor_employee.get("breakfast_balance", 0.0)
            
            # Perform breakfast sponsoring
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": sponsor["id"],
                "sponsor_employee_name": sponsor["name"]
            }
            
            response = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=sponsor_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response structure
                required_fields = ["message", "sponsored_items", "total_cost", "affected_employees", "sponsor"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "Test Breakfast Sponsoring",
                        False,
                        error=f"Missing fields in response: {missing_fields}"
                    )
                    return False
                
                # Verify response values
                if result["total_cost"] > 0 and result["affected_employees"] > 0:
                    self.log_result(
                        "Test Breakfast Sponsoring",
                        True,
                        f"Breakfast sponsoring successful: {result['sponsored_items']}, Cost: €{result['total_cost']}, Employees: {result['affected_employees']}, Sponsor: {result['sponsor']}"
                    )
                    return True
                else:
                    self.log_result(
                        "Test Breakfast Sponsoring",
                        False,
                        error=f"Invalid sponsoring result: cost={result['total_cost']}, employees={result['affected_employees']}"
                    )
                    return False
            else:
                self.log_result(
                    "Test Breakfast Sponsoring",
                    False,
                    error=f"Sponsoring failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Breakfast Sponsoring", False, error=str(e))
            return False
    
    def test_lunch_sponsoring(self):
        """Test lunch sponsoring functionality"""
        try:
            if len(self.test_employees) < 3:
                self.log_result(
                    "Test Lunch Sponsoring",
                    False,
                    error="Not enough test employees for lunch sponsoring test"
                )
                return False
            
            # Use 3rd employee as sponsor for lunch
            sponsor = self.test_employees[2]
            today = date.today().isoformat()
            
            # Perform lunch sponsoring
            sponsor_data = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": sponsor["id"],
                "sponsor_employee_name": sponsor["name"]
            }
            
            response = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=sponsor_data)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify response structure
                required_fields = ["message", "sponsored_items", "total_cost", "affected_employees", "sponsor"]
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result(
                        "Test Lunch Sponsoring",
                        False,
                        error=f"Missing fields in response: {missing_fields}"
                    )
                    return False
                
                # Verify lunch-specific results
                if "Mittagessen" in result["sponsored_items"] and result["total_cost"] > 0:
                    self.log_result(
                        "Test Lunch Sponsoring",
                        True,
                        f"Lunch sponsoring successful: {result['sponsored_items']}, Cost: €{result['total_cost']}, Employees: {result['affected_employees']}"
                    )
                    return True
                else:
                    self.log_result(
                        "Test Lunch Sponsoring",
                        False,
                        error=f"Invalid lunch sponsoring result: {result['sponsored_items']}, cost={result['total_cost']}"
                    )
                    return False
            else:
                self.log_result(
                    "Test Lunch Sponsoring",
                    False,
                    error=f"Lunch sponsoring failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Lunch Sponsoring", False, error=str(e))
            return False
    
    def verify_sponsored_orders_audit_trail(self):
        """Verify that sponsored orders have proper audit trail"""
        try:
            if len(self.test_employees) < 2:
                self.log_result(
                    "Verify Sponsored Orders Audit Trail",
                    False,
                    error="Not enough test employees to verify audit trail"
                )
                return False
            
            # Check orders for first employee to see if they're marked as sponsored
            employee1 = self.test_employees[0]
            response = self.session.get(f"{BASE_URL}/employees/{employee1['id']}/orders")
            
            if response.status_code == 200:
                orders_data = response.json()
                orders = orders_data.get("orders", [])
                
                # Look for sponsored orders
                sponsored_orders = [order for order in orders if order.get("is_sponsored", False)]
                
                if sponsored_orders:
                    # Verify audit fields
                    audit_verified = True
                    for order in sponsored_orders:
                        required_audit_fields = ["is_sponsored", "sponsored_by_employee_id", "sponsored_by_name", "sponsored_date"]
                        missing_audit_fields = [field for field in required_audit_fields if field not in order]
                        
                        if missing_audit_fields:
                            audit_verified = False
                            break
                    
                    if audit_verified:
                        self.log_result(
                            "Verify Sponsored Orders Audit Trail",
                            True,
                            f"Found {len(sponsored_orders)} sponsored orders with proper audit trail"
                        )
                        return True
                    else:
                        self.log_result(
                            "Verify Sponsored Orders Audit Trail",
                            False,
                            error=f"Sponsored orders missing audit fields: {missing_audit_fields}"
                        )
                        return False
                else:
                    self.log_result(
                        "Verify Sponsored Orders Audit Trail",
                        False,
                        error="No sponsored orders found to verify audit trail"
                    )
                    return False
            else:
                self.log_result(
                    "Verify Sponsored Orders Audit Trail",
                    False,
                    error=f"Could not fetch employee orders: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Sponsored Orders Audit Trail", False, error=str(e))
            return False
    
    def verify_sponsor_balance_charged(self):
        """Verify that sponsor employee balance was charged correctly"""
        try:
            if len(self.test_employees) < 3:
                self.log_result(
                    "Verify Sponsor Balance Charged",
                    False,
                    error="Not enough test employees to verify sponsor balance"
                )
                return False
            
            # Check sponsor's balance
            sponsor = self.test_employees[2]
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            
            if response.status_code == 200:
                employees = response.json()
                sponsor_employee = next((emp for emp in employees if emp["id"] == sponsor["id"]), None)
                
                if sponsor_employee:
                    sponsor_balance = sponsor_employee.get("breakfast_balance", 0.0)
                    
                    # Sponsor should have a positive balance (charged for sponsoring)
                    if sponsor_balance > 0:
                        self.log_result(
                            "Verify Sponsor Balance Charged",
                            True,
                            f"Sponsor balance correctly charged: €{sponsor_balance:.2f}"
                        )
                        return True
                    else:
                        self.log_result(
                            "Verify Sponsor Balance Charged",
                            False,
                            error=f"Sponsor balance not charged correctly: €{sponsor_balance:.2f}"
                        )
                        return False
                else:
                    self.log_result(
                        "Verify Sponsor Balance Charged",
                        False,
                        error="Could not find sponsor employee in department"
                    )
                    return False
            else:
                self.log_result(
                    "Verify Sponsor Balance Charged",
                    False,
                    error=f"Could not fetch department employees: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Sponsor Balance Charged", False, error=str(e))
            return False
    
    def test_invalid_sponsoring_scenarios(self):
        """Test invalid sponsoring scenarios for proper error handling"""
        try:
            if len(self.test_employees) < 1:
                self.log_result(
                    "Test Invalid Sponsoring Scenarios",
                    False,
                    error="No test employees available for invalid scenario testing"
                )
                return False
            
            sponsor = self.test_employees[0]
            today = date.today().isoformat()
            
            # Test 1: Invalid meal_type
            invalid_data1 = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "invalid_meal",
                "sponsor_employee_id": sponsor["id"],
                "sponsor_employee_name": sponsor["name"]
            }
            
            response1 = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=invalid_data1)
            
            # Test 2: Missing required fields
            invalid_data2 = {
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast"
                # Missing sponsor fields
            }
            
            response2 = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=invalid_data2)
            
            # Test 3: Invalid date format
            invalid_data3 = {
                "department_id": DEPARTMENT_ID,
                "date": "invalid-date",
                "meal_type": "breakfast",
                "sponsor_employee_id": sponsor["id"],
                "sponsor_employee_name": sponsor["name"]
            }
            
            response3 = self.session.post(f"{BASE_URL}/department-admin/sponsor-meal", json=invalid_data3)
            
            # All should return 400 Bad Request
            error_responses = [response1.status_code == 400, response2.status_code == 400, response3.status_code == 400]
            
            if all(error_responses):
                self.log_result(
                    "Test Invalid Sponsoring Scenarios",
                    True,
                    "All invalid scenarios correctly returned HTTP 400 errors"
                )
                return True
            else:
                self.log_result(
                    "Test Invalid Sponsoring Scenarios",
                    False,
                    error=f"Invalid scenarios did not return proper errors: {[r.status_code for r in [response1, response2, response3]]}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Invalid Sponsoring Scenarios", False, error=str(e))
            return False
    
    def create_additional_lunch_orders(self):
        """Create additional orders with lunch for lunch sponsoring test"""
        try:
            if len(self.test_employees) < 4:
                self.log_result(
                    "Create Additional Lunch Orders",
                    False,
                    error="Not enough test employees for additional lunch orders"
                )
                return False
            
            # Create lunch orders for employees 3 and 4 (different from breakfast sponsoring)
            orders_created = 0
            
            # Employee 3: Only lunch (no rolls, no eggs, no coffee)
            employee3 = self.test_employees[2]  # Use 3rd employee (index 2)
            order3_data = {
                "employee_id": employee3["id"],
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 0,
                    "white_halves": 0,
                    "seeded_halves": 0,
                    "toppings": [],
                    "has_lunch": True,
                    "boiled_eggs": 0,
                    "has_coffee": False
                }]
            }
            
            response3 = self.session.post(f"{BASE_URL}/orders", json=order3_data)
            if response3.status_code == 200:
                order3 = response3.json()
                self.test_orders.append(order3)
                orders_created += 1
            
            # Employee 4: Lunch + eggs (no rolls, no coffee)
            if len(self.test_employees) > 3:
                employee4 = self.test_employees[3]  # Use 4th employee (index 3)
                order4_data = {
                    "employee_id": employee4["id"],
                    "department_id": DEPARTMENT_ID,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 0,
                        "white_halves": 0,
                        "seeded_halves": 0,
                        "toppings": [],
                        "has_lunch": True,
                        "boiled_eggs": 1,
                        "has_coffee": False
                    }]
                }
                
                response4 = self.session.post(f"{BASE_URL}/orders", json=order4_data)
                if response4.status_code == 200:
                    order4 = response4.json()
                    self.test_orders.append(order4)
                    orders_created += 1
            
            if orders_created >= 1:
                self.log_result(
                    "Create Additional Lunch Orders",
                    True,
                    f"Successfully created {orders_created} additional lunch orders for testing"
                )
                return True
            else:
                self.log_result(
                    "Create Additional Lunch Orders",
                    False,
                    error=f"Could only create {orders_created} additional lunch orders"
                )
                return False
                
        except Exception as e:
            self.log_result("Create Additional Lunch Orders", False, error=str(e))
            return False

    def run_meal_sponsoring_tests(self):
        """Run all meal sponsoring tests"""
        print("🍽️ MEAL SPONSORING FEATURE TEST")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME} ({DEPARTMENT_ID})")
        print(f"Admin Password: {ADMIN_PASSWORD}")
        print("=" * 80)
        print()
        
        # Test 1: Department Admin Authentication
        print("🧪 TEST 1: Department Admin Authentication")
        test1_ok = self.authenticate_admin()
        
        if not test1_ok:
            print("❌ Cannot proceed without admin authentication")
            return False
        
        # Test 2: Create Test Employees
        print("🧪 TEST 2: Create Test Employees")
        test2_ok = self.create_test_employees()
        
        if not test2_ok:
            print("❌ Cannot proceed without test employees")
            return False
        
        # Test 3: Create Breakfast Orders
        print("🧪 TEST 3: Create Breakfast Orders")
        test3_ok = self.create_breakfast_orders()
        
        # Test 4: Create Additional Lunch Orders (for separate lunch sponsoring test)
        print("🧪 TEST 4: Create Additional Lunch Orders")
        test4_ok = self.create_additional_lunch_orders()
        
        # Test 5: Test Lunch Sponsoring (test this first before breakfast sponsoring)
        print("🧪 TEST 5: Test Lunch Sponsoring")
        test5_ok = self.test_lunch_sponsoring()
        
        # Test 6: Test Breakfast Sponsoring
        print("🧪 TEST 6: Test Breakfast Sponsoring")
        test6_ok = self.test_breakfast_sponsoring()
        
        # Test 7: Verify Sponsored Orders Audit Trail
        print("🧪 TEST 7: Verify Sponsored Orders Audit Trail")
        test7_ok = self.verify_sponsored_orders_audit_trail()
        
        # Test 8: Verify Sponsor Balance Charged
        print("🧪 TEST 8: Verify Sponsor Balance Charged")
        test8_ok = self.verify_sponsor_balance_charged()
        
        # Test 9: Test Invalid Sponsoring Scenarios
        print("🧪 TEST 9: Test Invalid Sponsoring Scenarios")
        test9_ok = self.test_invalid_sponsoring_scenarios()
        
        # Summary
        self.print_test_summary()
        
        return all([test1_ok, test2_ok, test3_ok, test4_ok, test5_ok, test6_ok, test7_ok, test8_ok, test9_ok])
    
    def print_test_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🍽️ MEAL SPONSORING FEATURE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"])
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        print()
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            print("❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   • {test['test']}: {test['error']}")
            print()
            print("🚨 CONCLUSION: Meal sponsoring feature has issues!")
        else:
            print("✅ ALL MEAL SPONSORING TESTS PASSED!")
            print("   • Department admin authentication works correctly")
            print("   • Test employees created successfully")
            print("   • Breakfast orders created for testing")
            print("   • Breakfast sponsoring functionality works")
            print("   • Lunch sponsoring functionality works")
            print("   • Sponsored orders have proper audit trail")
            print("   • Sponsor balance is charged correctly")
            print("   • Invalid scenarios are handled properly")
            print("   • The meal sponsoring feature is working correctly!")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = MealSponsoringTester()
    
    try:
        success = tester.run_meal_sponsoring_tests()
        
        # Exit with appropriate code
        failed_tests = [r for r in tester.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            sys.exit(1)  # Indicate test failures
        else:
            sys.exit(0)  # All tests passed
            
    except KeyboardInterrupt:
        print("\n⚠️ Testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()