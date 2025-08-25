#!/usr/bin/env python3
"""
CRITICAL BUG INVESTIGATION: Employee-specific breakfast order failure
Testing Jonas Parlow vs Julian Takke breakfast ordering issue

LIVE SYSTEM: https://canteen-keeper.preview.emergentagent.com
CREDENTIALS: 2. Wachabteilung (password: costa, admin: lenny)
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "https://canteen-keeper.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_PASSWORD = "password2"
ADMIN_PASSWORD = "admin2"

class CanteenTester:
    def __init__(self):
        self.session = requests.Session()
        self.department_id = None
        self.julian_id = None
        self.jonas_id = None
        self.test_results = []
        
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
    
    def authenticate_department(self):
        """Authenticate with department credentials"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department", json={
                "department_name": DEPARTMENT_NAME,
                "password": DEPARTMENT_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.department_id = data.get("department_id")
                self.log_result(
                    "Department Authentication", 
                    True, 
                    f"Authenticated as {DEPARTMENT_NAME}, ID: {self.department_id}"
                )
                return True
            else:
                self.log_result(
                    "Department Authentication", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Department Authentication", False, error=str(e))
            return False
    
    def authenticate_admin(self):
        """Authenticate with admin credentials for employee creation"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                self.log_result(
                    "Admin Authentication", 
                    True, 
                    f"Authenticated as admin for {DEPARTMENT_NAME}"
                )
                return True
            else:
                self.log_result(
                    "Admin Authentication", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, error=str(e))
            return False
    
    def create_julian_takke(self):
        """Create Julian Takke employee for testing"""
        try:
            response = self.session.post(f"{BASE_URL}/employees", json={
                "name": "Julian Takke",
                "department_id": self.department_id
            })
            
            if response.status_code == 200:
                employee_data = response.json()
                self.julian_id = employee_data.get("id")
                self.log_result(
                    "Julian Takke Creation", 
                    True, 
                    f"Created Julian Takke (ID: {self.julian_id})"
                )
                return True
            else:
                self.log_result(
                    "Julian Takke Creation", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Julian Takke Creation", False, error=str(e))
            return False
    
    def get_employees(self):
        """Get all employees and find Julian Takke and Jonas Parlow"""
        try:
            response = self.session.get(f"{BASE_URL}/departments/{self.department_id}/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                # Find Julian Takke and Jonas Parlow
                for emp in employees:
                    if "Julian Takke" in emp.get("name", ""):
                        self.julian_id = emp["id"]
                    elif "Jonas Parlow" in emp.get("name", ""):
                        self.jonas_id = emp["id"]
                
                found_employees = []
                if self.julian_id:
                    found_employees.append(f"Julian Takke (ID: {self.julian_id})")
                if self.jonas_id:
                    found_employees.append(f"Jonas Parlow (ID: {self.jonas_id})")
                
                self.log_result(
                    "Employee Discovery", 
                    bool(found_employees),
                    f"Found {len(employees)} total employees. Target employees: {', '.join(found_employees) if found_employees else 'NONE FOUND'}"
                )
                
                # Log all employees for debugging
                employee_names = [emp.get("name", "Unknown") for emp in employees]
                print(f"   All employees: {employee_names}")
                
                return len(found_employees) > 0
                
            else:
                self.log_result(
                    "Employee Discovery", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Employee Discovery", False, error=str(e))
            return False
    
    def compare_employee_data(self):
        """Compare employee data between Julian and Jonas"""
        if not self.julian_id or not self.jonas_id:
            self.log_result(
                "Employee Data Comparison", 
                False, 
                error="Both employees not found - cannot compare"
            )
            return False
        
        try:
            # Get Julian's data
            julian_response = self.session.get(f"{BASE_URL}/employees/{self.julian_id}/orders")
            jonas_response = self.session.get(f"{BASE_URL}/employees/{self.jonas_id}/orders")
            
            julian_success = julian_response.status_code == 200
            jonas_success = jonas_response.status_code == 200
            
            details = []
            if julian_success:
                julian_orders = julian_response.json()
                details.append(f"Julian: {len(julian_orders.get('orders', []))} orders")
            else:
                details.append(f"Julian: ERROR {julian_response.status_code}")
            
            if jonas_success:
                jonas_orders = jonas_response.json()
                details.append(f"Jonas: {len(jonas_orders.get('orders', []))} orders")
            else:
                details.append(f"Jonas: ERROR {jonas_response.status_code}")
            
            self.log_result(
                "Employee Data Comparison",
                julian_success and jonas_success,
                "; ".join(details)
            )
            
            return julian_success and jonas_success
            
        except Exception as e:
            self.log_result("Employee Data Comparison", False, error=str(e))
            return False
    
    def get_breakfast_menu(self):
        """Get breakfast menu items for the department"""
        try:
            response = self.session.get(f"{BASE_URL}/menu/breakfast/{self.department_id}")
            
            if response.status_code == 200:
                menu_items = response.json()
                self.log_result(
                    "Breakfast Menu Retrieval",
                    True,
                    f"Found {len(menu_items)} breakfast items"
                )
                
                # Store menu items for order testing
                self.breakfast_menu = menu_items
                return True
            else:
                self.log_result(
                    "Breakfast Menu Retrieval",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Breakfast Menu Retrieval", False, error=str(e))
            return False
    
    def get_toppings_menu(self):
        """Get toppings menu items for the department"""
        try:
            response = self.session.get(f"{BASE_URL}/menu/toppings/{self.department_id}")
            
            if response.status_code == 200:
                menu_items = response.json()
                self.log_result(
                    "Toppings Menu Retrieval",
                    True,
                    f"Found {len(menu_items)} topping items"
                )
                
                # Store toppings for order testing
                self.toppings_menu = menu_items
                return True
            else:
                self.log_result(
                    "Toppings Menu Retrieval",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Toppings Menu Retrieval", False, error=str(e))
            return False
    
    def test_breakfast_order_creation(self, employee_id, employee_name):
        """Test breakfast order creation for a specific employee"""
        if not hasattr(self, 'breakfast_menu') or not hasattr(self, 'toppings_menu'):
            self.log_result(
                f"Breakfast Order Test - {employee_name}",
                False,
                error="Menu data not available"
            )
            return False
        
        try:
            # Create a simple breakfast order
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
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            success = response.status_code == 200
            if success:
                order_result = response.json()
                self.log_result(
                    f"Breakfast Order Test - {employee_name}",
                    True,
                    f"Order created successfully. Total: €{order_result.get('total_price', 'N/A')}"
                )
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_detail)
                except:
                    pass
                
                self.log_result(
                    f"Breakfast Order Test - {employee_name}",
                    False,
                    error=f"HTTP {response.status_code}: {error_detail}"
                )
            
            return success
            
        except Exception as e:
            self.log_result(f"Breakfast Order Test - {employee_name}", False, error=str(e))
            return False
    
    def check_employee_balances(self):
        """Check employee balance data for both employees"""
        if not self.julian_id or not self.jonas_id:
            self.log_result(
                "Employee Balance Check", 
                False, 
                error="Both employees not found"
            )
            return False
        
        try:
            # Get department employees to check balances
            response = self.session.get(f"{BASE_URL}/departments/{self.department_id}/employees")
            
            if response.status_code == 200:
                employees = response.json()
                
                julian_balance = None
                jonas_balance = None
                
                for emp in employees:
                    if emp["id"] == self.julian_id:
                        julian_balance = {
                            "breakfast": emp.get("breakfast_balance", 0),
                            "drinks_sweets": emp.get("drinks_sweets_balance", 0)
                        }
                    elif emp["id"] == self.jonas_id:
                        jonas_balance = {
                            "breakfast": emp.get("breakfast_balance", 0),
                            "drinks_sweets": emp.get("drinks_sweets_balance", 0)
                        }
                
                details = []
                if julian_balance:
                    details.append(f"Julian: Breakfast €{julian_balance['breakfast']}, Drinks/Sweets €{julian_balance['drinks_sweets']}")
                if jonas_balance:
                    details.append(f"Jonas: Breakfast €{jonas_balance['breakfast']}, Drinks/Sweets €{jonas_balance['drinks_sweets']}")
                
                self.log_result(
                    "Employee Balance Check",
                    bool(julian_balance and jonas_balance),
                    "; ".join(details)
                )
                
                return bool(julian_balance and jonas_balance)
                
            else:
                self.log_result(
                    "Employee Balance Check",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Employee Balance Check", False, error=str(e))
            return False
    
    def test_drinks_order_for_jonas(self):
        """Test drinks order for Jonas (should work according to issue description)"""
        if not self.jonas_id:
            self.log_result(
                "Jonas Drinks Order Test",
                False,
                error="Jonas not found"
            )
            return False
        
        try:
            # Get drinks menu first
            drinks_response = self.session.get(f"{BASE_URL}/menu/drinks/{self.department_id}")
            if drinks_response.status_code != 200:
                self.log_result(
                    "Jonas Drinks Order Test",
                    False,
                    error="Could not get drinks menu"
                )
                return False
            
            drinks_menu = drinks_response.json()
            if not drinks_menu:
                self.log_result(
                    "Jonas Drinks Order Test",
                    False,
                    error="No drinks available"
                )
                return False
            
            # Create a drinks order
            first_drink = drinks_menu[0]
            order_data = {
                "employee_id": self.jonas_id,
                "department_id": self.department_id,
                "order_type": "drinks",
                "drink_items": {
                    first_drink["id"]: 1
                }
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            success = response.status_code == 200
            if success:
                order_result = response.json()
                self.log_result(
                    "Jonas Drinks Order Test",
                    True,
                    f"Drinks order created successfully. Total: €{order_result.get('total_price', 'N/A')}"
                )
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_detail)
                except:
                    pass
                
                self.log_result(
                    "Jonas Drinks Order Test",
                    False,
                    error=f"HTTP {response.status_code}: {error_detail}"
                )
            
            return success
            
        except Exception as e:
            self.log_result("Jonas Drinks Order Test", False, error=str(e))
            return False
    
    def run_investigation(self):
        """Run the complete investigation"""
        print("🔍 CRITICAL BUG INVESTIGATION: Employee-specific breakfast order failure")
        print("=" * 80)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME}")
        print(f"Issue: Jonas Parlow cannot place breakfast orders, Julian Takke can")
        print("=" * 80)
        print()
        
        # Step 1: Authenticate
        if not self.authenticate_department():
            print("❌ CRITICAL: Cannot authenticate - stopping investigation")
            return False
        
        # Step 2: Find employees
        if not self.get_employees():
            print("❌ CRITICAL: Cannot find target employees - stopping investigation")
            return False
        
        # Step 3: Get menu data
        menu_success = self.get_breakfast_menu() and self.get_toppings_menu()
        if not menu_success:
            print("⚠️ WARNING: Menu data incomplete - some tests may fail")
        
        # Step 4: Compare employee data
        self.compare_employee_data()
        
        # Step 5: Check employee balances
        self.check_employee_balances()
        
        # Step 6: Test drinks order for Jonas (should work)
        self.test_drinks_order_for_jonas()
        
        # Step 7: Test breakfast orders for both employees
        if self.julian_id:
            self.test_breakfast_order_creation(self.julian_id, "Julian Takke")
        
        if self.jonas_id:
            self.test_breakfast_order_creation(self.jonas_id, "Jonas Parlow")
        
        # Summary
        self.print_summary()
        
        return True
    
    def print_summary(self):
        """Print investigation summary"""
        print("\n" + "=" * 80)
        print("🔍 INVESTIGATION SUMMARY")
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
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        if self.julian_id and self.jonas_id:
            print("   • Both target employees found in system")
        elif self.julian_id:
            print("   • Only Julian Takke found - Jonas Parlow missing!")
        elif self.jonas_id:
            print("   • Only Jonas Parlow found - Julian Takke missing!")
        else:
            print("   • Neither target employee found - data integrity issue!")
        
        # Check for breakfast order results
        julian_breakfast = next((r for r in self.test_results if "Julian Takke" in r["test"] and "Breakfast Order" in r["test"]), None)
        jonas_breakfast = next((r for r in self.test_results if "Jonas Parlow" in r["test"] and "Breakfast Order" in r["test"]), None)
        
        if julian_breakfast and jonas_breakfast:
            julian_works = "✅ PASS" in julian_breakfast["status"]
            jonas_works = "✅ PASS" in jonas_breakfast["status"]
            
            if julian_works and not jonas_works:
                print("   • ⚠️ CONFIRMED BUG: Julian can order breakfast, Jonas cannot!")
                print(f"   • Jonas error: {jonas_breakfast.get('error', 'Unknown')}")
            elif not julian_works and jonas_works:
                print("   • 🔄 REVERSED ISSUE: Jonas can order breakfast, Julian cannot!")
            elif not julian_works and not jonas_works:
                print("   • 🚨 SYSTEM WIDE ISSUE: Neither employee can order breakfast!")
            else:
                print("   • ✅ NO ISSUE DETECTED: Both employees can order breakfast")
        
        print("\n" + "=" * 80)

def main():
    """Main function"""
    tester = CanteenTester()
    
    try:
        success = tester.run_investigation()
        
        # Exit with appropriate code
        failed_tests = [r for r in tester.test_results if "❌ FAIL" in r["status"]]
        if failed_tests:
            sys.exit(1)  # Indicate test failures
        else:
            sys.exit(0)  # All tests passed
            
    except KeyboardInterrupt:
        print("\n⚠️ Investigation interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()