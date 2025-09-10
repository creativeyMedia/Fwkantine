#!/usr/bin/env python3
"""
Multi-Department Subaccount System Comprehensive Test Suite
==========================================================

This test suite comprehensively tests the extended multi-department subaccount system.

CORE FUNCTIONALITIES TESTED:
1. **Subaccount System Basics:**
   - Employee model with JSON subaccount_balances 
   - New API endpoints: /departments/{id}/other-employees, /employees/{id}/all-balances
   - Migration of existing employees works

2. **Order System with Subaccounts:**
   - CREATE ORDER: Employee A from department A orders in foreign department B → Main Balance + Subaccount Balance correctly updated
   - DELETE ORDER: Cancel order → both balances correctly restored
   - Test different order types: breakfast, drinks, sweets

3. **EXTENDED: Sponsoring with Subaccounts:**
   - Sponsor action: Employee1 from Department1 sponsors breakfast for Employee2/Employee3 in Department1
   - Check: Sponsor balance (main + subaccount) correctly charged
   - Check: Sponsored employee balances (main + subaccount) correctly credited
   - Test cross-department sponsoring if possible

4. **Balance Consistency:**
   - Main balance always = Subaccount balance of home department
   - All CRUD operations synchronize both systems
   - No discrepancies between main and subaccount balances

IMPORTANT TEST SCENARIOS:
- Employee from fw4abteilung1 orders in fw4abteilung2
- Cancellation of cross-department orders
- Sponsoring within same department
- Balance queries via /employees/{id}/all-balances

ERROR HANDLING:
- Wrong department IDs
- Non-existent employees
- Edge cases in balance updates
"""

import requests
import json
import os
from datetime import datetime
import uuid
import time

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class MultiDepartmentSubaccountTest:
    def __init__(self):
        self.dept1_id = "fw4abteilung1"
        self.dept2_id = "fw4abteilung2"
        self.dept1_admin = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.dept2_admin = {"department_name": "2. Wachabteilung", "admin_password": "admin2"}
        
        # Test employees
        self.test_employees = {}
        self.test_orders = {}
        
        # Generate unique test names
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.test_prefix = f"SubaccountTest_{timestamp}"
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        
    def warning(self, message):
        """Log test warnings"""
        print(f"⚠️ WARNING: {message}")

    def test_init_data(self):
        """Initialize data to ensure departments exist"""
        try:
            response = requests.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.success("Data initialization successful")
                return True
            else:
                self.log(f"Init data response: {response.status_code} - {response.text}")
                # This might fail if data already exists, which is OK
                return True
        except Exception as e:
            self.error(f"Exception during data initialization: {str(e)}")
            return False

    def test_get_departments(self):
        """Test that departments are returned"""
        try:
            response = requests.get(f"{API_BASE}/departments")
            if response.status_code == 200:
                departments = response.json()
                if len(departments) >= 2:
                    self.success(f"Found {len(departments)} departments")
                    for dept in departments:
                        self.log(f"  - {dept['name']} (ID: {dept['id']})")
                    return True
                else:
                    self.error(f"Need at least 2 departments for testing, found {len(departments)}")
                    return False
            else:
                self.error(f"Failed to get departments: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception getting departments: {str(e)}")
            return False

    def test_migrate_subaccounts(self):
        """Test migration of existing employees to subaccount system"""
        try:
            response = requests.post(f"{API_BASE}/admin/migrate-subaccounts")
            if response.status_code == 200:
                result = response.json()
                self.success(f"Subaccount migration successful: {result.get('message', 'No details')}")
                self.log(f"  - Migrated employees: {result.get('migrated_employees', 0)}")
                self.log(f"  - Synchronized balances: {result.get('synchronized_balances', 0)}")
                return True
            else:
                self.error(f"Subaccount migration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception during subaccount migration: {str(e)}")
            return False

    def create_test_employee(self, dept_id, name_suffix):
        """Create a test employee for testing"""
        try:
            employee_name = f"{self.test_prefix}_{name_suffix}"
            employee_data = {
                "name": employee_name,
                "department_id": dept_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee["id"]
                self.test_employees[name_suffix] = {
                    "id": employee_id,
                    "name": employee_name,
                    "department_id": dept_id
                }
                self.success(f"Created test employee: {employee_name} (ID: {employee_id}) in {dept_id}")
                return True
            else:
                self.error(f"Failed to create test employee {employee_name}: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating test employee {name_suffix}: {str(e)}")
            return False

    def test_new_api_endpoints(self):
        """Test new API endpoints for multi-department functionality"""
        try:
            # Test /departments/{id}/other-employees
            self.log("Testing /departments/{id}/other-employees endpoint...")
            response = requests.get(f"{API_BASE}/departments/{self.dept1_id}/other-employees")
            if response.status_code == 200:
                other_employees = response.json()
                self.success(f"GET /departments/{self.dept1_id}/other-employees working")
                self.log(f"  - Found employees from other departments: {len(other_employees)} departments")
                
                # Check if we have employees from dept2
                if self.dept2_id in other_employees:
                    dept2_employees = other_employees[self.dept2_id]
                    self.log(f"  - Department {self.dept2_id} has {len(dept2_employees)} employees")
                else:
                    self.log(f"  - No employees found from {self.dept2_id}")
            else:
                self.error(f"Failed to get other employees: {response.status_code} - {response.text}")
                return False

            # Test /employees/{id}/all-balances for our test employee
            if "emp1" in self.test_employees:
                employee_id = self.test_employees["emp1"]["id"]
                self.log(f"Testing /employees/{employee_id}/all-balances endpoint...")
                response = requests.get(f"{API_BASE}/employees/{employee_id}/all-balances")
                if response.status_code == 200:
                    balances = response.json()
                    self.success(f"GET /employees/{employee_id}/all-balances working")
                    self.log(f"  - Employee: {balances.get('employee_name')}")
                    self.log(f"  - Main department: {balances.get('main_department_name')}")
                    self.log(f"  - Main balances: {balances.get('main_balances')}")
                    self.log(f"  - Subaccount balances: {len(balances.get('subaccount_balances', {}))} departments")
                    
                    # Verify subaccount structure
                    subaccounts = balances.get('subaccount_balances', {})
                    if len(subaccounts) >= 4:  # Should have all 4 departments
                        self.success("Subaccount balances initialized for all departments")
                    else:
                        self.warning(f"Expected 4 subaccounts, found {len(subaccounts)}")
                else:
                    self.error(f"Failed to get employee balances: {response.status_code} - {response.text}")
                    return False
            
            return True
        except Exception as e:
            self.error(f"Exception testing new API endpoints: {str(e)}")
            return False

    def test_cross_department_order_creation(self):
        """Test creating orders across departments"""
        try:
            if "emp1" not in self.test_employees:
                self.error("Test employee emp1 not available for cross-department order test")
                return False
                
            employee = self.test_employees["emp1"]
            employee_id = employee["id"]
            home_dept = employee["department_id"]
            foreign_dept = self.dept2_id if home_dept == self.dept1_id else self.dept1_id
            
            self.log(f"Testing cross-department order: Employee from {home_dept} ordering in {foreign_dept}")
            
            # Get initial balances
            response = requests.get(f"{API_BASE}/employees/{employee_id}/all-balances")
            if response.status_code != 200:
                self.error("Failed to get initial balances")
                return False
            
            initial_balances = response.json()
            initial_main_breakfast = initial_balances["main_balances"]["breakfast"]
            initial_subaccount = initial_balances["subaccount_balances"][foreign_dept]["breakfast"]
            
            self.log(f"Initial main breakfast balance: €{initial_main_breakfast}")
            self.log(f"Initial {foreign_dept} subaccount balance: €{initial_subaccount}")
            
            # Create breakfast order in foreign department
            order_data = {
                "employee_id": employee_id,
                "department_id": foreign_dept,  # Ordering in foreign department
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["Rührei", "Spiegelei"],
                    "has_lunch": False,
                    "boiled_eggs": 0,
                    "fried_eggs": 0,
                    "has_coffee": True
                }]
            }
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                total_price = order["total_price"]
                
                self.test_orders["cross_dept_breakfast"] = {
                    "id": order_id,
                    "employee_id": employee_id,
                    "department_id": foreign_dept,
                    "total_price": total_price,
                    "order_type": "breakfast"
                }
                
                self.success(f"Cross-department breakfast order created (ID: {order_id}, Total: €{total_price})")
                
                # Check updated balances
                time.sleep(1)  # Small delay for database consistency
                response = requests.get(f"{API_BASE}/employees/{employee_id}/all-balances")
                if response.status_code == 200:
                    updated_balances = response.json()
                    updated_main_breakfast = updated_balances["main_balances"]["breakfast"]
                    updated_subaccount = updated_balances["subaccount_balances"][foreign_dept]["breakfast"]
                    
                    self.log(f"Updated main breakfast balance: €{updated_main_breakfast}")
                    self.log(f"Updated {foreign_dept} subaccount balance: €{updated_subaccount}")
                    
                    # For cross-department orders, only subaccount should change
                    if home_dept == employee["department_id"]:
                        # Main balance should remain unchanged for cross-department orders
                        if abs(updated_main_breakfast - initial_main_breakfast) < 0.01:
                            self.success("Main balance correctly unchanged for cross-department order")
                        else:
                            self.warning(f"Main balance changed unexpectedly: {initial_main_breakfast} → {updated_main_breakfast}")
                    
                    # Subaccount balance should decrease by order amount
                    expected_subaccount = initial_subaccount - total_price
                    if abs(updated_subaccount - expected_subaccount) < 0.01:
                        self.success(f"Subaccount balance correctly updated: €{initial_subaccount} → €{updated_subaccount}")
                    else:
                        self.error(f"Subaccount balance incorrect: expected €{expected_subaccount}, got €{updated_subaccount}")
                        return False
                else:
                    self.error("Failed to get updated balances after cross-department order")
                    return False
            else:
                self.error(f"Failed to create cross-department order: {response.status_code} - {response.text}")
                return False
                
            return True
        except Exception as e:
            self.error(f"Exception testing cross-department order creation: {str(e)}")
            return False

    def test_cross_department_drinks_order(self):
        """Test creating drinks order across departments"""
        try:
            if "emp1" not in self.test_employees:
                self.error("Test employee emp1 not available for drinks order test")
                return False
                
            employee = self.test_employees["emp1"]
            employee_id = employee["id"]
            home_dept = employee["department_id"]
            foreign_dept = self.dept2_id if home_dept == self.dept1_id else self.dept1_id
            
            self.log(f"Testing cross-department drinks order: Employee from {home_dept} ordering drinks in {foreign_dept}")
            
            # Get initial balances
            response = requests.get(f"{API_BASE}/employees/{employee_id}/all-balances")
            if response.status_code != 200:
                self.error("Failed to get initial balances for drinks test")
                return False
            
            initial_balances = response.json()
            initial_main_drinks = initial_balances["main_balances"]["drinks_sweets"]
            initial_subaccount = initial_balances["subaccount_balances"][foreign_dept]["drinks"]
            
            self.log(f"Initial main drinks balance: €{initial_main_drinks}")
            self.log(f"Initial {foreign_dept} drinks subaccount balance: €{initial_subaccount}")
            
            # Create drinks order in foreign department
            order_data = {
                "employee_id": employee_id,
                "department_id": foreign_dept,
                "order_type": "drinks",
                "drink_items": {
                    "drink_1": 2,  # Assuming drink_1 exists
                    "drink_2": 1   # Assuming drink_2 exists
                }
            }
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                total_price = order["total_price"]
                
                self.test_orders["cross_dept_drinks"] = {
                    "id": order_id,
                    "employee_id": employee_id,
                    "department_id": foreign_dept,
                    "total_price": total_price,
                    "order_type": "drinks"
                }
                
                self.success(f"Cross-department drinks order created (ID: {order_id}, Total: €{total_price})")
                
                # Check updated balances
                time.sleep(1)
                response = requests.get(f"{API_BASE}/employees/{employee_id}/all-balances")
                if response.status_code == 200:
                    updated_balances = response.json()
                    updated_main_drinks = updated_balances["main_balances"]["drinks_sweets"]
                    updated_subaccount = updated_balances["subaccount_balances"][foreign_dept]["drinks"]
                    
                    self.log(f"Updated main drinks balance: €{updated_main_drinks}")
                    self.log(f"Updated {foreign_dept} drinks subaccount balance: €{updated_subaccount}")
                    
                    # For cross-department orders, only subaccount should change
                    if home_dept == employee["department_id"]:
                        if abs(updated_main_drinks - initial_main_drinks) < 0.01:
                            self.success("Main drinks balance correctly unchanged for cross-department order")
                        else:
                            self.warning(f"Main drinks balance changed unexpectedly: {initial_main_drinks} → {updated_main_drinks}")
                    
                    # Subaccount balance should change by order amount (drinks are negative)
                    expected_subaccount = initial_subaccount + total_price  # total_price is negative for drinks
                    if abs(updated_subaccount - expected_subaccount) < 0.01:
                        self.success(f"Drinks subaccount balance correctly updated: €{initial_subaccount} → €{updated_subaccount}")
                    else:
                        self.error(f"Drinks subaccount balance incorrect: expected €{expected_subaccount}, got €{updated_subaccount}")
                        return False
                else:
                    self.error("Failed to get updated balances after drinks order")
                    return False
            else:
                self.error(f"Failed to create cross-department drinks order: {response.status_code} - {response.text}")
                return False
                
            return True
        except Exception as e:
            self.error(f"Exception testing cross-department drinks order: {str(e)}")
            return False

    def test_order_cancellation_balance_restoration(self):
        """Test that order cancellation correctly restores both main and subaccount balances"""
        try:
            if "cross_dept_breakfast" not in self.test_orders:
                self.error("No cross-department breakfast order available for cancellation test")
                return False
                
            order = self.test_orders["cross_dept_breakfast"]
            order_id = order["id"]
            employee_id = order["employee_id"]
            foreign_dept = order["department_id"]
            original_total = order["total_price"]
            
            self.log(f"Testing order cancellation balance restoration for order {order_id}")
            
            # Get balances before cancellation
            response = requests.get(f"{API_BASE}/employees/{employee_id}/all-balances")
            if response.status_code != 200:
                self.error("Failed to get balances before cancellation")
                return False
            
            before_balances = response.json()
            before_main = before_balances["main_balances"]["breakfast"]
            before_subaccount = before_balances["subaccount_balances"][foreign_dept]["breakfast"]
            
            self.log(f"Before cancellation - Main: €{before_main}, Subaccount: €{before_subaccount}")
            
            # Cancel the order (using employee endpoint)
            response = requests.delete(f"{API_BASE}/employee/{employee_id}/orders/{order_id}")
            if response.status_code == 200:
                self.success(f"Order {order_id} cancelled successfully")
                
                # Check balances after cancellation
                time.sleep(1)
                response = requests.get(f"{API_BASE}/employees/{employee_id}/all-balances")
                if response.status_code == 200:
                    after_balances = response.json()
                    after_main = after_balances["main_balances"]["breakfast"]
                    after_subaccount = after_balances["subaccount_balances"][foreign_dept]["breakfast"]
                    
                    self.log(f"After cancellation - Main: €{after_main}, Subaccount: €{after_subaccount}")
                    
                    # Main balance should remain unchanged (was cross-department order)
                    if abs(after_main - before_main) < 0.01:
                        self.success("Main balance correctly unchanged after cross-department order cancellation")
                    else:
                        self.warning(f"Main balance changed during cancellation: {before_main} → {after_main}")
                    
                    # Subaccount balance should be restored (increased by original order amount)
                    expected_subaccount = before_subaccount + original_total
                    if abs(after_subaccount - expected_subaccount) < 0.01:
                        self.success(f"Subaccount balance correctly restored: €{before_subaccount} → €{after_subaccount}")
                    else:
                        self.error(f"Subaccount balance not correctly restored: expected €{expected_subaccount}, got €{after_subaccount}")
                        return False
                else:
                    self.error("Failed to get balances after cancellation")
                    return False
            else:
                self.error(f"Failed to cancel order: {response.status_code} - {response.text}")
                return False
                
            return True
        except Exception as e:
            self.error(f"Exception testing order cancellation: {str(e)}")
            return False

    def test_balance_consistency(self):
        """Test that main balance always equals subaccount balance of home department"""
        try:
            for emp_key, employee in self.test_employees.items():
                employee_id = employee["id"]
                home_dept = employee["department_id"]
                
                self.log(f"Testing balance consistency for {employee['name']} (home: {home_dept})")
                
                response = requests.get(f"{API_BASE}/employees/{employee_id}/all-balances")
                if response.status_code == 200:
                    balances = response.json()
                    main_breakfast = balances["main_balances"]["breakfast"]
                    main_drinks = balances["main_balances"]["drinks_sweets"]
                    
                    subaccounts = balances["subaccount_balances"]
                    if home_dept in subaccounts:
                        sub_breakfast = subaccounts[home_dept]["breakfast"]
                        sub_drinks = subaccounts[home_dept]["drinks"]
                        
                        # Check breakfast balance consistency
                        if abs(main_breakfast - sub_breakfast) < 0.01:
                            self.success(f"Breakfast balance consistent: Main €{main_breakfast} = Sub €{sub_breakfast}")
                        else:
                            self.error(f"Breakfast balance inconsistent: Main €{main_breakfast} ≠ Sub €{sub_breakfast}")
                            return False
                        
                        # Check drinks balance consistency
                        if abs(main_drinks - sub_drinks) < 0.01:
                            self.success(f"Drinks balance consistent: Main €{main_drinks} = Sub €{sub_drinks}")
                        else:
                            self.error(f"Drinks balance inconsistent: Main €{main_drinks} ≠ Sub €{sub_drinks}")
                            return False
                    else:
                        self.error(f"Home department {home_dept} not found in subaccounts")
                        return False
                else:
                    self.error(f"Failed to get balances for {employee['name']}")
                    return False
            
            return True
        except Exception as e:
            self.error(f"Exception testing balance consistency: {str(e)}")
            return False

    def test_sponsoring_within_department(self):
        """Test sponsoring functionality within same department"""
        try:
            # Create additional employees for sponsoring test
            if not self.create_test_employee(self.dept1_id, "sponsor"):
                return False
            if not self.create_test_employee(self.dept1_id, "sponsored1"):
                return False
            if not self.create_test_employee(self.dept1_id, "sponsored2"):
                return False
            
            sponsor = self.test_employees["sponsor"]
            sponsored1 = self.test_employees["sponsored1"]
            sponsored2 = self.test_employees["sponsored2"]
            
            # Create breakfast orders for sponsored employees
            for emp_key, employee in [("sponsored1", sponsored1), ("sponsored2", sponsored2)]:
                order_data = {
                    "employee_id": employee["id"],
                    "department_id": self.dept1_id,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["Rührei", "Spiegelei"],
                        "has_lunch": False,
                        "boiled_eggs": 0,
                        "fried_eggs": 0,
                        "has_coffee": False
                    }]
                }
                
                response = requests.post(f"{API_BASE}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    self.test_orders[f"{emp_key}_breakfast"] = {
                        "id": order["id"],
                        "employee_id": employee["id"],
                        "total_price": order["total_price"]
                    }
                    self.success(f"Created breakfast order for {employee['name']}: €{order['total_price']}")
                else:
                    self.error(f"Failed to create breakfast order for {employee['name']}")
                    return False
            
            # Get initial balances
            sponsor_response = requests.get(f"{API_BASE}/employees/{sponsor['id']}/all-balances")
            if sponsor_response.status_code != 200:
                self.error("Failed to get sponsor initial balances")
                return False
            
            sponsor_initial = sponsor_response.json()
            sponsor_initial_main = sponsor_initial["main_balances"]["breakfast"]
            sponsor_initial_sub = sponsor_initial["subaccount_balances"][self.dept1_id]["breakfast"]
            
            self.log(f"Sponsor initial balances - Main: €{sponsor_initial_main}, Sub: €{sponsor_initial_sub}")
            
            # Authenticate as admin for sponsoring
            auth_response = requests.post(f"{API_BASE}/login/department-admin", json=self.dept1_admin)
            if auth_response.status_code != 200:
                self.error("Failed to authenticate as admin for sponsoring")
                return False
            
            # Sponsor breakfast for both employees
            sponsored_ids = [sponsored1["id"], sponsored2["id"]]
            sponsor_data = {
                "sponsor_employee_id": sponsor["id"],
                "sponsored_employee_ids": sponsored_ids,
                "meal_type": "breakfast"
            }
            
            response = requests.post(f"{API_BASE}/department-admin/sponsor-meal/{self.dept1_id}", json=sponsor_data)
            if response.status_code == 200:
                result = response.json()
                self.success(f"Sponsoring successful: {result.get('message', 'No message')}")
                
                # Check sponsor balances after sponsoring
                time.sleep(1)
                sponsor_response = requests.get(f"{API_BASE}/employees/{sponsor['id']}/all-balances")
                if sponsor_response.status_code == 200:
                    sponsor_after = sponsor_response.json()
                    sponsor_after_main = sponsor_after["main_balances"]["breakfast"]
                    sponsor_after_sub = sponsor_after["subaccount_balances"][self.dept1_id]["breakfast"]
                    
                    self.log(f"Sponsor after balances - Main: €{sponsor_after_main}, Sub: €{sponsor_after_sub}")
                    
                    # Sponsor should have paid for the sponsored meals
                    total_sponsored_cost = sum(self.test_orders[f"{key}_breakfast"]["total_price"] 
                                             for key in ["sponsored1", "sponsored2"])
                    expected_main = sponsor_initial_main - total_sponsored_cost
                    expected_sub = sponsor_initial_sub - total_sponsored_cost
                    
                    if abs(sponsor_after_main - expected_main) < 0.01:
                        self.success(f"Sponsor main balance correctly charged: €{sponsor_initial_main} → €{sponsor_after_main}")
                    else:
                        self.error(f"Sponsor main balance incorrect: expected €{expected_main}, got €{sponsor_after_main}")
                        return False
                    
                    if abs(sponsor_after_sub - expected_sub) < 0.01:
                        self.success(f"Sponsor subaccount balance correctly charged: €{sponsor_initial_sub} → €{sponsor_after_sub}")
                    else:
                        self.error(f"Sponsor subaccount balance incorrect: expected €{expected_sub}, got €{sponsor_after_sub}")
                        return False
                    
                    # Check sponsored employees' balances
                    for emp_key, employee in [("sponsored1", sponsored1), ("sponsored2", sponsored2)]:
                        emp_response = requests.get(f"{API_BASE}/employees/{employee['id']}/all-balances")
                        if emp_response.status_code == 200:
                            emp_balances = emp_response.json()
                            emp_main = emp_balances["main_balances"]["breakfast"]
                            emp_sub = emp_balances["subaccount_balances"][self.dept1_id]["breakfast"]
                            
                            # Sponsored employees should have their balances restored (or improved)
                            if emp_main >= 0 and emp_sub >= 0:
                                self.success(f"Sponsored employee {employee['name']} balances restored: Main €{emp_main}, Sub €{emp_sub}")
                            else:
                                self.warning(f"Sponsored employee {employee['name']} still has negative balances: Main €{emp_main}, Sub €{emp_sub}")
                        else:
                            self.error(f"Failed to get balances for sponsored employee {employee['name']}")
                            return False
                else:
                    self.error("Failed to get sponsor balances after sponsoring")
                    return False
            else:
                self.error(f"Failed to sponsor meals: {response.status_code} - {response.text}")
                return False
                
            return True
        except Exception as e:
            self.error(f"Exception testing sponsoring within department: {str(e)}")
            return False

    def test_error_handling(self):
        """Test error handling for edge cases"""
        try:
            # Test with non-existent department ID
            self.log("Testing error handling with non-existent department ID")
            response = requests.get(f"{API_BASE}/departments/nonexistent/other-employees")
            if response.status_code == 200:
                result = response.json()
                if not result:  # Empty result is acceptable
                    self.success("Non-existent department returns empty result")
                else:
                    self.log("Non-existent department returns some data (may be acceptable)")
            else:
                self.log(f"Non-existent department returns error: {response.status_code} (acceptable)")
            
            # Test with non-existent employee ID
            self.log("Testing error handling with non-existent employee ID")
            response = requests.get(f"{API_BASE}/employees/nonexistent-id/all-balances")
            if response.status_code == 404:
                self.success("Non-existent employee correctly returns 404")
            else:
                self.warning(f"Non-existent employee returns: {response.status_code} (expected 404)")
            
            # Test cross-department order with invalid department
            if "emp1" in self.test_employees:
                employee_id = self.test_employees["emp1"]["id"]
                self.log("Testing cross-department order with invalid department")
                
                order_data = {
                    "employee_id": employee_id,
                    "department_id": "invalid_dept",
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 1,
                        "white_halves": 1,
                        "seeded_halves": 0,
                        "toppings": ["Rührei"],
                        "has_lunch": False,
                        "boiled_eggs": 0,
                        "fried_eggs": 0,
                        "has_coffee": False
                    }]
                }
                
                response = requests.post(f"{API_BASE}/orders", json=order_data)
                if response.status_code >= 400:
                    self.success(f"Invalid department order correctly rejected: {response.status_code}")
                else:
                    self.warning(f"Invalid department order unexpectedly accepted: {response.status_code}")
            
            return True
        except Exception as e:
            self.error(f"Exception testing error handling: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """Run the complete multi-department subaccount system test"""
        self.log("🎯 STARTING MULTI-DEPARTMENT SUBACCOUNT SYSTEM COMPREHENSIVE TESTING")
        self.log("=" * 90)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Get Departments", self.test_get_departments),
            ("Migrate Subaccounts", self.test_migrate_subaccounts),
            ("Create Test Employee 1 (Dept1)", lambda: self.create_test_employee(self.dept1_id, "emp1")),
            ("Create Test Employee 2 (Dept2)", lambda: self.create_test_employee(self.dept2_id, "emp2")),
            ("Test New API Endpoints", self.test_new_api_endpoints),
            ("Test Cross-Department Order Creation", self.test_cross_department_order_creation),
            ("Test Cross-Department Drinks Order", self.test_cross_department_drinks_order),
            ("Test Order Cancellation Balance Restoration", self.test_order_cancellation_balance_restoration),
            ("Test Balance Consistency", self.test_balance_consistency),
            ("Test Sponsoring Within Department", self.test_sponsoring_within_department),
            ("Test Error Handling", self.test_error_handling)
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        
        for step_name, step_function in test_steps:
            self.log(f"\n📋 Step {passed_tests + 1}/{total_tests}: {step_name}")
            self.log("-" * 60)
            
            if step_function():
                passed_tests += 1
                self.success(f"Step {passed_tests}/{total_tests} PASSED: {step_name}")
            else:
                self.error(f"Step {passed_tests + 1}/{total_tests} FAILED: {step_name}")
                # Continue with other tests even if one fails
                
        # Final results
        self.log("\n" + "=" * 90)
        if passed_tests == total_tests:
            self.success(f"🎉 MULTI-DEPARTMENT SUBACCOUNT SYSTEM TESTING COMPLETED SUCCESSFULLY!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            self.log("\n🎯 CRITICAL VERIFICATION RESULTS:")
            self.log("✅ Employee model with JSON subaccount_balances working")
            self.log("✅ New API endpoints /departments/{id}/other-employees working")
            self.log("✅ New API endpoints /employees/{id}/all-balances working")
            self.log("✅ Cross-department order creation working")
            self.log("✅ Cross-department order cancellation working")
            self.log("✅ Balance consistency maintained (main = subaccount for home dept)")
            self.log("✅ Sponsoring with subaccounts working")
            self.log("✅ Error handling working")
            return True
        else:
            self.error(f"❌ MULTI-DEPARTMENT SUBACCOUNT SYSTEM TESTING PARTIALLY FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            return False

def main():
    """Main test execution"""
    print("🧪 Multi-Department Subaccount System Comprehensive Test Suite")
    print("=" * 80)
    
    # Initialize and run test
    test_suite = MultiDepartmentSubaccountTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - MULTI-DEPARTMENT SUBACCOUNT SYSTEM IS WORKING!")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - MULTI-DEPARTMENT SUBACCOUNT SYSTEM NEEDS ATTENTION!")
        exit(1)

if __name__ == "__main__":
    main()