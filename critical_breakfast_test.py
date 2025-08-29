#!/usr/bin/env python3
"""
CRITICAL BACKEND BUG INVESTIGATION: Breakfast order creation completely failing

LIVE SYSTEM: https://fw-kantine.de
DEPARTMENT: fw4abteilung2 (2. Wachabteilung)
CREDENTIALS: password: costa, admin: lenny

CRITICAL ISSUES TO INVESTIGATE:
1. ALL breakfast orders fail with "Fehler beim Speichern der Bestellung"
2. Drinks orders save but with total_price: 0 (should have actual price)
3. Sweets orders work correctly with proper pricing (total_price: 1.5)

SUSPECTED ROOT CAUSES:
- Menu item ID mismatch after database cleanup
- Price calculation logic broken for breakfast items
- Department-specific menu items have incorrect IDs
- Order validation failing for breakfast category
"""

import requests
import json
import sys
from datetime import datetime

# Configuration from review request
BASE_URL = "https://meal-tracker-49.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
DEPARTMENT_PASSWORD = "costa"
ADMIN_PASSWORD = "lenny"

class CriticalBreakfastTester:
    def __init__(self):
        self.session = requests.Session()
        self.department_id = DEPARTMENT_ID
        self.test_results = []
        self.test_employee_id = None
        
    def log_result(self, test_name, success, details="", error="", critical=False):
        """Log test result"""
        status = "✅ PASS" if success else ("🚨 CRITICAL FAIL" if critical else "❌ FAIL")
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "error": error,
            "critical": critical,
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
                self.department_id = data.get("department_id", DEPARTMENT_ID)
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
                    error=f"HTTP {response.status_code}: {response.text}",
                    critical=True
                )
                return False
                
        except Exception as e:
            self.log_result("Department Authentication", False, error=str(e), critical=True)
            return False
    
    def authenticate_admin(self):
        """Authenticate with admin credentials"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
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
    
    def test_breakfast_menu_retrieval(self):
        """Test breakfast menu retrieval for fw4abteilung2"""
        try:
            response = self.session.get(f"{BASE_URL}/menu/breakfast/{self.department_id}")
            
            if response.status_code == 200:
                menu_items = response.json()
                self.breakfast_menu = menu_items
                
                # Analyze menu structure
                details = f"Found {len(menu_items)} breakfast items"
                if menu_items:
                    first_item = menu_items[0]
                    details += f". Sample item: {first_item.get('roll_type', 'N/A')} - €{first_item.get('price', 'N/A')}"
                    details += f", ID: {first_item.get('id', 'N/A')}"
                    details += f", Dept ID: {first_item.get('department_id', 'N/A')}"
                
                self.log_result(
                    "Breakfast Menu Retrieval",
                    True,
                    details
                )
                return True
            else:
                self.log_result(
                    "Breakfast Menu Retrieval",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    critical=True
                )
                return False
                
        except Exception as e:
            self.log_result("Breakfast Menu Retrieval", False, error=str(e), critical=True)
            return False
    
    def test_toppings_menu_retrieval(self):
        """Test toppings menu retrieval for fw4abteilung2"""
        try:
            response = self.session.get(f"{BASE_URL}/menu/toppings/{self.department_id}")
            
            if response.status_code == 200:
                menu_items = response.json()
                self.toppings_menu = menu_items
                
                details = f"Found {len(menu_items)} topping items"
                if menu_items:
                    first_item = menu_items[0]
                    details += f". Sample item: {first_item.get('topping_type', 'N/A')} - €{first_item.get('price', 'N/A')}"
                    details += f", ID: {first_item.get('id', 'N/A')}"
                
                self.log_result(
                    "Toppings Menu Retrieval",
                    True,
                    details
                )
                return True
            else:
                self.log_result(
                    "Toppings Menu Retrieval",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}",
                    critical=True
                )
                return False
                
        except Exception as e:
            self.log_result("Toppings Menu Retrieval", False, error=str(e), critical=True)
            return False
    
    def test_drinks_menu_retrieval(self):
        """Test drinks menu retrieval for fw4abteilung2"""
        try:
            response = self.session.get(f"{BASE_URL}/menu/drinks/{self.department_id}")
            
            if response.status_code == 200:
                menu_items = response.json()
                self.drinks_menu = menu_items
                
                details = f"Found {len(menu_items)} drink items"
                if menu_items:
                    first_item = menu_items[0]
                    details += f". Sample item: {first_item.get('name', 'N/A')} - €{first_item.get('price', 'N/A')}"
                    details += f", ID: {first_item.get('id', 'N/A')}"
                
                self.log_result(
                    "Drinks Menu Retrieval",
                    True,
                    details
                )
                return True
            else:
                self.log_result(
                    "Drinks Menu Retrieval",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Drinks Menu Retrieval", False, error=str(e))
            return False
    
    def test_sweets_menu_retrieval(self):
        """Test sweets menu retrieval for fw4abteilung2"""
        try:
            response = self.session.get(f"{BASE_URL}/menu/sweets/{self.department_id}")
            
            if response.status_code == 200:
                menu_items = response.json()
                self.sweets_menu = menu_items
                
                details = f"Found {len(menu_items)} sweet items"
                if menu_items:
                    first_item = menu_items[0]
                    details += f". Sample item: {first_item.get('name', 'N/A')} - €{first_item.get('price', 'N/A')}"
                    details += f", ID: {first_item.get('id', 'N/A')}"
                
                self.log_result(
                    "Sweets Menu Retrieval",
                    True,
                    details
                )
                return True
            else:
                self.log_result(
                    "Sweets Menu Retrieval",
                    False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Sweets Menu Retrieval", False, error=str(e))
            return False
    
    def create_test_employee(self):
        """Create a test employee for order testing"""
        try:
            response = self.session.post(f"{BASE_URL}/employees", json={
                "name": "Test Employee Critical Bug",
                "department_id": self.department_id
            })
            
            if response.status_code == 200:
                employee_data = response.json()
                self.test_employee_id = employee_data.get("id")
                self.log_result(
                    "Test Employee Creation", 
                    True, 
                    f"Created test employee (ID: {self.test_employee_id})"
                )
                return True
            else:
                self.log_result(
                    "Test Employee Creation", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Test Employee Creation", False, error=str(e))
            return False
    
    def get_existing_employee(self):
        """Get an existing employee from the department"""
        try:
            response = self.session.get(f"{BASE_URL}/departments/{self.department_id}/employees")
            
            if response.status_code == 200:
                employees = response.json()
                if employees:
                    self.test_employee_id = employees[0]["id"]
                    self.log_result(
                        "Existing Employee Found", 
                        True, 
                        f"Using existing employee: {employees[0]['name']} (ID: {self.test_employee_id})"
                    )
                    return True
                else:
                    self.log_result(
                        "Existing Employee Found", 
                        False, 
                        error="No employees found in department"
                    )
                    return False
            else:
                self.log_result(
                    "Existing Employee Found", 
                    False, 
                    error=f"HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Existing Employee Found", False, error=str(e))
            return False
    
    def test_breakfast_order_creation(self):
        """CRITICAL TEST: Test breakfast order creation - this should be failing"""
        if not self.test_employee_id:
            self.log_result(
                "Breakfast Order Creation",
                False,
                error="No test employee available",
                critical=True
            )
            return False
        
        if not hasattr(self, 'breakfast_menu') or not hasattr(self, 'toppings_menu'):
            self.log_result(
                "Breakfast Order Creation",
                False,
                error="Menu data not available",
                critical=True
            )
            return False
        
        try:
            # Create a realistic breakfast order
            order_data = {
                "employee_id": self.test_employee_id,
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
            
            print(f"   Attempting breakfast order with data: {json.dumps(order_data, indent=2)}")
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            success = response.status_code == 200
            if success:
                order_result = response.json()
                total_price = order_result.get('total_price', 0)
                self.log_result(
                    "Breakfast Order Creation",
                    True,
                    f"Order created successfully! Total: €{total_price}. Order ID: {order_result.get('id', 'N/A')}"
                )
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_detail)
                except:
                    pass
                
                self.log_result(
                    "Breakfast Order Creation",
                    False,
                    error=f"HTTP {response.status_code}: {error_detail}",
                    critical=True
                )
            
            return success
            
        except Exception as e:
            self.log_result("Breakfast Order Creation", False, error=str(e), critical=True)
            return False
    
    def test_drinks_order_creation(self):
        """Test drinks order creation - should work but with total_price: 0 bug"""
        if not self.test_employee_id:
            self.log_result(
                "Drinks Order Creation",
                False,
                error="No test employee available"
            )
            return False
        
        if not hasattr(self, 'drinks_menu') or not self.drinks_menu:
            self.log_result(
                "Drinks Order Creation",
                False,
                error="Drinks menu not available"
            )
            return False
        
        try:
            # Create a drinks order
            first_drink = self.drinks_menu[0]
            order_data = {
                "employee_id": self.test_employee_id,
                "department_id": self.department_id,
                "order_type": "drinks",
                "drink_items": {
                    first_drink["id"]: 2  # Order 2 of the first drink
                }
            }
            
            print(f"   Attempting drinks order: 2x {first_drink['name']} (€{first_drink['price']} each)")
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            success = response.status_code == 200
            if success:
                order_result = response.json()
                total_price = order_result.get('total_price', 0)
                expected_price = first_drink['price'] * 2
                
                # Check for the reported bug: total_price should be > 0
                if total_price == 0:
                    self.log_result(
                        "Drinks Order Creation",
                        False,
                        error=f"BUG CONFIRMED: Drinks order saved with total_price: 0 (expected: €{expected_price})",
                        critical=True
                    )
                else:
                    self.log_result(
                        "Drinks Order Creation",
                        True,
                        f"Order created with correct pricing. Total: €{total_price} (expected: €{expected_price})"
                    )
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_detail)
                except:
                    pass
                
                self.log_result(
                    "Drinks Order Creation",
                    False,
                    error=f"HTTP {response.status_code}: {error_detail}"
                )
            
            return success
            
        except Exception as e:
            self.log_result("Drinks Order Creation", False, error=str(e))
            return False
    
    def test_sweets_order_creation(self):
        """Test sweets order creation - should work correctly with proper pricing"""
        if not self.test_employee_id:
            self.log_result(
                "Sweets Order Creation",
                False,
                error="No test employee available"
            )
            return False
        
        if not hasattr(self, 'sweets_menu') or not self.sweets_menu:
            self.log_result(
                "Sweets Order Creation",
                False,
                error="Sweets menu not available"
            )
            return False
        
        try:
            # Create a sweets order
            first_sweet = self.sweets_menu[0]
            order_data = {
                "employee_id": self.test_employee_id,
                "department_id": self.department_id,
                "order_type": "sweets",
                "sweet_items": {
                    first_sweet["id"]: 1  # Order 1 of the first sweet
                }
            }
            
            print(f"   Attempting sweets order: 1x {first_sweet['name']} (€{first_sweet['price']})")
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            success = response.status_code == 200
            if success:
                order_result = response.json()
                total_price = order_result.get('total_price', 0)
                expected_price = first_sweet['price']
                
                if abs(total_price - expected_price) < 0.01:  # Allow for floating point precision
                    self.log_result(
                        "Sweets Order Creation",
                        True,
                        f"Order created with correct pricing. Total: €{total_price} (expected: €{expected_price})"
                    )
                else:
                    self.log_result(
                        "Sweets Order Creation",
                        False,
                        error=f"Price mismatch: got €{total_price}, expected €{expected_price}"
                    )
            else:
                error_detail = response.text
                try:
                    error_json = response.json()
                    error_detail = error_json.get('detail', error_detail)
                except:
                    pass
                
                self.log_result(
                    "Sweets Order Creation",
                    False,
                    error=f"HTTP {response.status_code}: {error_detail}"
                )
            
            return success
            
        except Exception as e:
            self.log_result("Sweets Order Creation", False, error=str(e))
            return False
    
    def test_menu_id_consistency(self):
        """Test menu item ID consistency across categories"""
        try:
            all_ids = []
            categories = []
            
            if hasattr(self, 'breakfast_menu'):
                breakfast_ids = [item['id'] for item in self.breakfast_menu]
                all_ids.extend(breakfast_ids)
                categories.append(f"Breakfast: {len(breakfast_ids)} items")
            
            if hasattr(self, 'toppings_menu'):
                topping_ids = [item['id'] for item in self.toppings_menu]
                all_ids.extend(topping_ids)
                categories.append(f"Toppings: {len(topping_ids)} items")
            
            if hasattr(self, 'drinks_menu'):
                drink_ids = [item['id'] for item in self.drinks_menu]
                all_ids.extend(drink_ids)
                categories.append(f"Drinks: {len(drink_ids)} items")
            
            if hasattr(self, 'sweets_menu'):
                sweet_ids = [item['id'] for item in self.sweets_menu]
                all_ids.extend(sweet_ids)
                categories.append(f"Sweets: {len(sweet_ids)} items")
            
            # Check for duplicate IDs
            unique_ids = set(all_ids)
            has_duplicates = len(all_ids) != len(unique_ids)
            
            # Check ID format consistency
            valid_uuid_format = all(len(id_str) > 10 for id_str in all_ids)  # Basic UUID length check
            
            details = f"Total IDs: {len(all_ids)}, Unique: {len(unique_ids)}. Categories: {', '.join(categories)}"
            
            if has_duplicates:
                self.log_result(
                    "Menu ID Consistency",
                    False,
                    error=f"Duplicate IDs found! {details}",
                    critical=True
                )
            elif not valid_uuid_format:
                self.log_result(
                    "Menu ID Consistency",
                    False,
                    error=f"Invalid ID format detected! {details}"
                )
            else:
                self.log_result(
                    "Menu ID Consistency",
                    True,
                    details
                )
            
            return not has_duplicates and valid_uuid_format
            
        except Exception as e:
            self.log_result("Menu ID Consistency", False, error=str(e))
            return False
    
    def test_department_id_consistency(self):
        """Test that all menu items have correct department_id"""
        try:
            issues = []
            
            # Check breakfast menu
            if hasattr(self, 'breakfast_menu'):
                for item in self.breakfast_menu:
                    if item.get('department_id') != self.department_id:
                        issues.append(f"Breakfast item {item.get('id', 'N/A')} has wrong dept_id: {item.get('department_id')}")
            
            # Check toppings menu
            if hasattr(self, 'toppings_menu'):
                for item in self.toppings_menu:
                    if item.get('department_id') != self.department_id:
                        issues.append(f"Topping item {item.get('id', 'N/A')} has wrong dept_id: {item.get('department_id')}")
            
            # Check drinks menu
            if hasattr(self, 'drinks_menu'):
                for item in self.drinks_menu:
                    if item.get('department_id') != self.department_id:
                        issues.append(f"Drink item {item.get('id', 'N/A')} has wrong dept_id: {item.get('department_id')}")
            
            # Check sweets menu
            if hasattr(self, 'sweets_menu'):
                for item in self.sweets_menu:
                    if item.get('department_id') != self.department_id:
                        issues.append(f"Sweet item {item.get('id', 'N/A')} has wrong dept_id: {item.get('department_id')}")
            
            if issues:
                self.log_result(
                    "Department ID Consistency",
                    False,
                    error=f"Found {len(issues)} department ID mismatches: {'; '.join(issues[:3])}{'...' if len(issues) > 3 else ''}",
                    critical=True
                )
                return False
            else:
                self.log_result(
                    "Department ID Consistency",
                    True,
                    f"All menu items have correct department_id: {self.department_id}"
                )
                return True
            
        except Exception as e:
            self.log_result("Department ID Consistency", False, error=str(e))
            return False
    
    def run_critical_investigation(self):
        """Run the complete critical bug investigation"""
        print("🚨 CRITICAL BACKEND BUG INVESTIGATION: Breakfast order creation completely failing")
        print("=" * 90)
        print(f"Target System: {BASE_URL}")
        print(f"Department: {DEPARTMENT_NAME} (ID: {DEPARTMENT_ID})")
        print(f"Credentials: password: {DEPARTMENT_PASSWORD}, admin: {ADMIN_PASSWORD}")
        print()
        print("CRITICAL ISSUES TO INVESTIGATE:")
        print("1. ALL breakfast orders fail with 'Fehler beim Speichern der Bestellung'")
        print("2. Drinks orders save but with total_price: 0 (should have actual price)")
        print("3. Sweets orders work correctly with proper pricing (total_price: 1.5)")
        print("=" * 90)
        print()
        
        # Step 1: Authenticate
        if not self.authenticate_department():
            print("🚨 CRITICAL: Cannot authenticate - stopping investigation")
            return False
        
        # Step 2: Test all menu retrievals
        print("📋 TESTING MENU RETRIEVALS...")
        breakfast_menu_ok = self.test_breakfast_menu_retrieval()
        toppings_menu_ok = self.test_toppings_menu_retrieval()
        drinks_menu_ok = self.test_drinks_menu_retrieval()
        sweets_menu_ok = self.test_sweets_menu_retrieval()
        
        # Step 3: Test menu consistency
        print("🔍 TESTING MENU CONSISTENCY...")
        self.test_menu_id_consistency()
        self.test_department_id_consistency()
        
        # Step 4: Get test employee
        print("👤 SETTING UP TEST EMPLOYEE...")
        if not self.get_existing_employee():
            # Try to authenticate as admin and create employee
            if self.authenticate_admin():
                self.create_test_employee()
        
        # Step 5: Test order creation for all categories
        print("🛒 TESTING ORDER CREATION...")
        if breakfast_menu_ok and toppings_menu_ok:
            self.test_breakfast_order_creation()  # CRITICAL TEST
        
        if drinks_menu_ok:
            self.test_drinks_order_creation()
        
        if sweets_menu_ok:
            self.test_sweets_order_creation()
        
        # Summary
        self.print_critical_summary()
        
        return True
    
    def print_critical_summary(self):
        """Print critical investigation summary"""
        print("\n" + "=" * 90)
        print("🚨 CRITICAL BUG INVESTIGATION SUMMARY")
        print("=" * 90)
        
        passed = sum(1 for result in self.test_results if "✅ PASS" in result["status"])
        failed = sum(1 for result in self.test_results if "❌ FAIL" in result["status"] or "🚨 CRITICAL FAIL" in result["status"])
        critical_failed = sum(1 for result in self.test_results if result.get("critical", False) and "FAIL" in result["status"])
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Critical Failures: {critical_failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%" if self.test_results else "0%")
        print()
        
        # Show critical failures first
        critical_failures = [r for r in self.test_results if r.get("critical", False) and "FAIL" in r["status"]]
        if critical_failures:
            print("🚨 CRITICAL FAILURES:")
            for test in critical_failures:
                print(f"   • {test['test']}: {test['error']}")
            print()
        
        # Show other failures
        other_failures = [r for r in self.test_results if not r.get("critical", False) and "FAIL" in r["status"]]
        if other_failures:
            print("❌ OTHER FAILURES:")
            for test in other_failures:
                print(f"   • {test['test']}: {test['error']}")
            print()
        
        # Key findings
        print("🔍 KEY FINDINGS:")
        
        # Check breakfast order result
        breakfast_test = next((r for r in self.test_results if "Breakfast Order Creation" in r["test"]), None)
        if breakfast_test:
            if "FAIL" in breakfast_test["status"]:
                print("   • 🚨 CONFIRMED: Breakfast orders are failing!")
                print(f"     Error: {breakfast_test.get('error', 'Unknown')}")
            else:
                print("   • ✅ UNEXPECTED: Breakfast orders are working (bug may be intermittent)")
        
        # Check drinks order result
        drinks_test = next((r for r in self.test_results if "Drinks Order Creation" in r["test"]), None)
        if drinks_test:
            if "total_price: 0" in drinks_test.get("error", ""):
                print("   • 🚨 CONFIRMED: Drinks orders save with total_price: 0 bug!")
            elif "PASS" in drinks_test["status"]:
                print("   • ✅ Drinks orders working with correct pricing")
        
        # Check sweets order result
        sweets_test = next((r for r in self.test_results if "Sweets Order Creation" in r["test"]), None)
        if sweets_test:
            if "PASS" in sweets_test["status"]:
                print("   • ✅ CONFIRMED: Sweets orders work correctly")
            else:
                print("   • ⚠️ UNEXPECTED: Sweets orders also having issues")
        
        # Check menu consistency
        menu_id_test = next((r for r in self.test_results if "Menu ID Consistency" in r["test"]), None)
        dept_id_test = next((r for r in self.test_results if "Department ID Consistency" in r["test"]), None)
        
        if menu_id_test and "FAIL" in menu_id_test["status"]:
            print("   • 🚨 MENU ISSUE: Menu item ID problems detected!")
        
        if dept_id_test and "FAIL" in dept_id_test["status"]:
            print("   • 🚨 DEPARTMENT ISSUE: Department ID mismatches detected!")
        
        print("\n" + "=" * 90)

def main():
    """Main function"""
    tester = CriticalBreakfastTester()
    
    try:
        success = tester.run_critical_investigation()
        
        # Exit with appropriate code
        critical_failures = [r for r in tester.test_results if r.get("critical", False) and "FAIL" in r["status"]]
        if critical_failures:
            sys.exit(2)  # Critical failures
        
        failed_tests = [r for r in tester.test_results if "FAIL" in r["status"]]
        if failed_tests:
            sys.exit(1)  # Regular test failures
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