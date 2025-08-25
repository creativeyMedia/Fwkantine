#!/usr/bin/env python3
"""
CRITICAL BUG INVESTIGATION: Menu Items und Employees nicht abrufbar

Das System zeigt ein schwerwiegendes Problem:
- GET /api/departments → 4 departments ✅  
- GET /api/menu/toppings/{department_id} → 0 toppings ❌
- GET /api/menu/breakfast/{department_id} → 0 items ❌  
- GET /api/departments/{department_id}/employees → 0 employees ❌
- Frontend-Bestellungen schlagen mit HTTP 422 fehl ❌

ABER: safe-init API sagt: "4 employees, 1 order, 1 lunch_settings vorhanden"

VERDACHT: Department-ID Mismatch oder Menu-Items haben falsche department_id Felder nach der Migration.
"""

import requests
import json
import sys
from datetime import datetime

# Use the production backend URL from frontend/.env
BACKEND_URL = "https://canteenflow.preview.emergentagent.com/api"

class CanteenBugInvestigation:
    def __init__(self):
        self.backend_url = BACKEND_URL
        self.session = requests.Session()
        self.departments = []
        self.test_results = []
        
    def log_result(self, test_name, success, details, data=None):
        """Log test results for comprehensive reporting"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}: {details}")
        if data and not success:
            print(f"   Data: {json.dumps(data, indent=2)}")
    
    def test_departments_endpoint(self):
        """Test 1: Prüfe ob Departments abrufbar sind"""
        try:
            response = self.session.get(f"{self.backend_url}/departments")
            
            if response.status_code == 200:
                departments = response.json()
                self.departments = departments
                
                self.log_result(
                    "GET /api/departments", 
                    True, 
                    f"Found {len(departments)} departments",
                    {"count": len(departments), "departments": [{"id": d.get("id"), "name": d.get("name")} for d in departments]}
                )
                
                # Log department details for debugging
                for dept in departments:
                    print(f"   Department: {dept.get('name')} (ID: {dept.get('id')})")
                
                return True
            else:
                self.log_result("GET /api/departments", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("GET /api/departments", False, f"Exception: {str(e)}")
            return False
    
    def test_menu_endpoints_for_each_department(self):
        """Test 2: Prüfe Menu-Endpoints für jede Abteilung"""
        if not self.departments:
            self.log_result("Menu Endpoints Test", False, "No departments available for testing")
            return False
        
        menu_types = ["breakfast", "toppings", "drinks", "sweets"]
        all_success = True
        
        for dept in self.departments:
            dept_id = dept.get("id")
            dept_name = dept.get("name")
            
            print(f"\n🔍 Testing menu endpoints for {dept_name} (ID: {dept_id})")
            
            for menu_type in menu_types:
                try:
                    response = self.session.get(f"{self.backend_url}/menu/{menu_type}/{dept_id}")
                    
                    if response.status_code == 200:
                        items = response.json()
                        success = len(items) > 0
                        
                        self.log_result(
                            f"GET /api/menu/{menu_type}/{dept_id}",
                            success,
                            f"Found {len(items)} {menu_type} items for {dept_name}",
                            {"department": dept_name, "department_id": dept_id, "count": len(items), "items": items[:3] if items else []}
                        )
                        
                        if not success:
                            all_success = False
                            
                    else:
                        self.log_result(
                            f"GET /api/menu/{menu_type}/{dept_id}",
                            False,
                            f"HTTP {response.status_code} for {dept_name}: {response.text}"
                        )
                        all_success = False
                        
                except Exception as e:
                    self.log_result(
                        f"GET /api/menu/{menu_type}/{dept_id}",
                        False,
                        f"Exception for {dept_name}: {str(e)}"
                    )
                    all_success = False
        
        return all_success
    
    def test_employees_endpoints_for_each_department(self):
        """Test 3: Prüfe Employee-Endpoints für jede Abteilung"""
        if not self.departments:
            self.log_result("Employees Endpoints Test", False, "No departments available for testing")
            return False
        
        all_success = True
        
        for dept in self.departments:
            dept_id = dept.get("id")
            dept_name = dept.get("name")
            
            try:
                response = self.session.get(f"{self.backend_url}/departments/{dept_id}/employees")
                
                if response.status_code == 200:
                    employees = response.json()
                    success = len(employees) > 0
                    
                    self.log_result(
                        f"GET /api/departments/{dept_id}/employees",
                        success,
                        f"Found {len(employees)} employees for {dept_name}",
                        {"department": dept_name, "department_id": dept_id, "count": len(employees), "employees": [{"id": e.get("id"), "name": e.get("name")} for e in employees[:3]]}
                    )
                    
                    if not success:
                        all_success = False
                        
                else:
                    self.log_result(
                        f"GET /api/departments/{dept_id}/employees",
                        False,
                        f"HTTP {response.status_code} for {dept_name}: {response.text}"
                    )
                    all_success = False
                    
            except Exception as e:
                self.log_result(
                    f"GET /api/departments/{dept_id}/employees",
                    False,
                    f"Exception for {dept_name}: {str(e)}"
                )
                all_success = False
        
        return all_success
    
    def test_backward_compatibility_endpoints(self):
        """Test 4: Prüfe Backward Compatibility Endpoints (ohne department_id)"""
        menu_types = ["breakfast", "toppings", "drinks", "sweets"]
        all_success = True
        
        print(f"\n🔍 Testing backward compatibility menu endpoints")
        
        for menu_type in menu_types:
            try:
                response = self.session.get(f"{self.backend_url}/menu/{menu_type}")
                
                if response.status_code == 200:
                    items = response.json()
                    success = len(items) > 0
                    
                    self.log_result(
                        f"GET /api/menu/{menu_type} (backward compatibility)",
                        success,
                        f"Found {len(items)} {menu_type} items (should use first department)",
                        {"count": len(items), "items": items[:3] if items else []}
                    )
                    
                    if not success:
                        all_success = False
                        
                else:
                    self.log_result(
                        f"GET /api/menu/{menu_type} (backward compatibility)",
                        False,
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    all_success = False
                    
            except Exception as e:
                self.log_result(
                    f"GET /api/menu/{menu_type} (backward compatibility)",
                    False,
                    f"Exception: {str(e)}"
                )
                all_success = False
        
        return all_success
    
    def test_safe_init_status(self):
        """Test 5: Prüfe safe-init Status um zu sehen was wirklich in der DB ist"""
        try:
            # First try to call safe-init to see what it reports
            response = self.session.post(f"{self.backend_url}/safe-init-empty-database")
            
            if response.status_code == 409:  # Expected - database not empty
                error_data = response.json()
                self.log_result(
                    "POST /api/safe-init-empty-database",
                    True,
                    "Database not empty (expected)",
                    error_data
                )
                return True
            elif response.status_code == 200:
                # Database was empty and got initialized
                init_data = response.json()
                self.log_result(
                    "POST /api/safe-init-empty-database",
                    True,
                    "Database was empty and got initialized",
                    init_data
                )
                return True
            else:
                self.log_result(
                    "POST /api/safe-init-empty-database",
                    False,
                    f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "POST /api/safe-init-empty-database",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def test_department_authentication(self):
        """Test 6: Prüfe Department Authentication um sicherzustellen dass IDs korrekt sind"""
        if not self.departments:
            self.log_result("Department Authentication Test", False, "No departments available for testing")
            return False
        
        all_success = True
        
        for dept in self.departments:
            dept_name = dept.get("name")
            
            # Try to authenticate with default password pattern
            # Based on the backend code, passwords should be password1, password2, etc.
            dept_number = dept_name.split(".")[0] if "." in dept_name else "1"
            test_password = f"password{dept_number}"
            
            try:
                auth_data = {
                    "department_name": dept_name,
                    "password": test_password
                }
                
                response = self.session.post(f"{self.backend_url}/login/department", json=auth_data)
                
                if response.status_code == 200:
                    auth_result = response.json()
                    self.log_result(
                        f"Department Auth: {dept_name}",
                        True,
                        f"Authentication successful with {test_password}",
                        {"department_id": auth_result.get("department_id"), "department_name": auth_result.get("department_name")}
                    )
                else:
                    self.log_result(
                        f"Department Auth: {dept_name}",
                        False,
                        f"Authentication failed with {test_password}: HTTP {response.status_code}"
                    )
                    all_success = False
                    
            except Exception as e:
                self.log_result(
                    f"Department Auth: {dept_name}",
                    False,
                    f"Exception: {str(e)}"
                )
                all_success = False
        
        return all_success
    
    def test_order_creation_simulation(self):
        """Test 7: Simuliere Order Creation um HTTP 422 Fehler zu reproduzieren"""
        if not self.departments:
            self.log_result("Order Creation Test", False, "No departments available for testing")
            return False
        
        # Use first department for testing
        dept = self.departments[0]
        dept_id = dept.get("id")
        dept_name = dept.get("name")
        
        print(f"\n🔍 Testing order creation for {dept_name} (ID: {dept_id})")
        
        # First, we need to create a test employee
        try:
            employee_data = {
                "name": "Test Employee Bug Investigation",
                "department_id": dept_id
            }
            
            response = self.session.post(f"{self.backend_url}/employees", json=employee_data)
            
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee.get("id")
                
                self.log_result(
                    "Create Test Employee",
                    True,
                    f"Created test employee: {employee.get('name')}",
                    {"employee_id": employee_id}
                )
                
                # Now try to create a breakfast order
                order_data = {
                    "employee_id": employee_id,
                    "department_id": dept_id,
                    "order_type": "breakfast",
                    "breakfast_items": [
                        {
                            "total_halves": 2,
                            "white_halves": 1,
                            "seeded_halves": 1,
                            "toppings": ["ruehrei", "kaese"],
                            "has_lunch": False,
                            "boiled_eggs": 0,
                            "has_coffee": False
                        }
                    ]
                }
                
                response = self.session.post(f"{self.backend_url}/orders", json=order_data)
                
                if response.status_code == 200:
                    order = response.json()
                    self.log_result(
                        "Create Test Order",
                        True,
                        f"Order created successfully: €{order.get('total_price', 0):.2f}",
                        {"order_id": order.get("id"), "total_price": order.get("total_price")}
                    )
                    return True
                else:
                    self.log_result(
                        "Create Test Order",
                        False,
                        f"Order creation failed: HTTP {response.status_code} - {response.text}",
                        {"status_code": response.status_code, "error": response.text}
                    )
                    return False
                    
            else:
                self.log_result(
                    "Create Test Employee",
                    False,
                    f"Employee creation failed: HTTP {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result(
                "Order Creation Test",
                False,
                f"Exception: {str(e)}"
            )
            return False
    
    def run_comprehensive_investigation(self):
        """Run all tests to investigate the critical bug"""
        print("🚨 STARTING CRITICAL BUG INVESTIGATION")
        print("=" * 60)
        print("PROBLEM: Menu Items und Employees nicht abrufbar")
        print("EXPECTED: 4 departments, menu items, employees should be accessible")
        print("ACTUAL: APIs return 0 results despite data existing")
        print("=" * 60)
        
        # Run all tests
        tests = [
            ("Departments Endpoint", self.test_departments_endpoint),
            ("Menu Endpoints", self.test_menu_endpoints_for_each_department),
            ("Employees Endpoints", self.test_employees_endpoints_for_each_department),
            ("Backward Compatibility", self.test_backward_compatibility_endpoints),
            ("Safe Init Status", self.test_safe_init_status),
            ("Department Authentication", self.test_department_authentication),
            ("Order Creation", self.test_order_creation_simulation)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n{'='*20} {test_name} {'='*20}")
            try:
                success = test_func()
                if success:
                    passed_tests += 1
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {str(e)}")
        
        # Final summary
        print(f"\n{'='*60}")
        print("🔍 INVESTIGATION SUMMARY")
        print(f"{'='*60}")
        print(f"Tests Passed: {passed_tests}/{total_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Analyze results for root cause
        self.analyze_root_cause()
        
        return passed_tests, total_tests
    
    def analyze_root_cause(self):
        """Analyze test results to identify root cause"""
        print(f"\n🔬 ROOT CAUSE ANALYSIS")
        print("-" * 40)
        
        # Check if departments are accessible
        dept_test = next((r for r in self.test_results if "departments" in r["test"].lower() and "GET" in r["test"]), None)
        if dept_test and dept_test["success"]:
            print("✅ Departments are accessible")
            dept_count = dept_test["data"]["count"] if dept_test["data"] else 0
            print(f"   Found {dept_count} departments")
        else:
            print("❌ Departments are NOT accessible - this is the root cause!")
            return
        
        # Check menu endpoints
        menu_failures = [r for r in self.test_results if "menu" in r["test"].lower() and not r["success"]]
        if menu_failures:
            print(f"❌ Menu endpoints failing: {len(menu_failures)} failures")
            for failure in menu_failures[:3]:  # Show first 3 failures
                print(f"   - {failure['test']}: {failure['details']}")
        else:
            print("✅ Menu endpoints working")
        
        # Check employee endpoints
        employee_failures = [r for r in self.test_results if "employee" in r["test"].lower() and not r["success"]]
        if employee_failures:
            print(f"❌ Employee endpoints failing: {len(employee_failures)} failures")
            for failure in employee_failures[:3]:
                print(f"   - {failure['test']}: {failure['details']}")
        else:
            print("✅ Employee endpoints working")
        
        # Check authentication
        auth_failures = [r for r in self.test_results if "auth" in r["test"].lower() and not r["success"]]
        if auth_failures:
            print(f"❌ Authentication failing: {len(auth_failures)} failures")
            print("   This could indicate department ID mismatch!")
        else:
            print("✅ Authentication working")
        
        # Provide recommendations
        print(f"\n💡 RECOMMENDATIONS")
        print("-" * 40)
        
        if menu_failures and employee_failures:
            print("🔧 LIKELY CAUSE: Department ID mismatch after migration")
            print("   - Menu items may have wrong department_id values")
            print("   - Employees may have wrong department_id values")
            print("   - Check if migration from development_database → canteen_db corrupted IDs")
            print("\n🛠️  SUGGESTED FIXES:")
            print("   1. Run database migration script to fix department_id fields")
            print("   2. Re-run /api/init-data to recreate menu items with correct IDs")
            print("   3. Check if department IDs changed during migration")
        elif menu_failures:
            print("🔧 LIKELY CAUSE: Menu items have wrong department_id values")
            print("   - Run /api/migrate-to-department-specific to fix menu items")
        elif employee_failures:
            print("🔧 LIKELY CAUSE: Employees have wrong department_id values")
            print("   - Check employee records in database")
            print("   - Update employee department_id fields to match current departments")
        else:
            print("✅ All systems appear to be working correctly")

def main():
    """Main function to run the investigation"""
    investigator = CanteenBugInvestigation()
    
    try:
        passed, total = investigator.run_comprehensive_investigation()
        
        # Exit with appropriate code
        if passed == total:
            print(f"\n🎉 ALL TESTS PASSED - No critical bugs found!")
            sys.exit(0)
        else:
            print(f"\n🚨 CRITICAL BUGS FOUND - {total - passed} tests failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Investigation interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\n💥 Investigation failed with exception: {str(e)}")
        sys.exit(3)

if __name__ == "__main__":
    main()