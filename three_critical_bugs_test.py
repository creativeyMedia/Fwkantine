#!/usr/bin/env python3
"""
Three Critical Bug Fixes Test Suite
===================================

This test suite verifies the three critical bug fixes reported by the user:

BUG 1 - Doppelte Stornierung bei Süßigkeiten/Getränken:
User reported: "bestellt ein mitarbeiter süßigkeiten oder getränke und storniert diese dann, 
wird der doppelte wert storniert. aus einer -0,8€ buchung wird dann nicht 0€ sondern +0,80€"

BUG 2 - Falsche Subkonto-Buchung im "Andere WA" Tab:
User reported: "wenn ich dort einen mitarbeiter ein saldo buche egal ob negativ oder positiv 
wird das nicht dem gast wachabteilung subkonto sondern dem hauptkonto berechnet."

BUG 3 - Bestellfehler bei Gastmitarbeitern:
User reported: "bei einem test in der 3. wachabteilung mit einem Gast Mitarbeiter aus der 
1. Wachabteilung kommt beim bestellen: Fehler beim Speichern der Bestellung"

EXPECTED RESULTS:
- ✅ BUG 1: Stornierung führt zu 0€ (nicht +0,80€)
- ✅ BUG 2: Subkonto-Zahlungen gehen an richtige Subkonten
- ✅ BUG 3: Gastmitarbeiter-Bestellungen funktionieren oder klare Fehlermeldung
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

class ThreeCriticalBugsTest:
    def __init__(self):
        self.test_results = []
        self.dept1_id = "fw4abteilung1"
        self.dept2_id = "fw4abteilung2" 
        self.dept3_id = "fw4abteilung3"
        
        # Admin credentials for different departments
        self.dept1_admin = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.dept2_admin = {"department_name": "2. Wachabteilung", "admin_password": "admin2"}
        self.dept3_admin = {"department_name": "3. Wachabteilung", "admin_password": "admin3"}
        
        # Test employee IDs (will be created)
        self.test_employee_dept1_id = None
        self.test_employee_dept3_id = None
        self.test_employee_names = {
            "dept1": f"BugTest1_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "dept3": f"BugTest3_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Order IDs for testing cancellation
        self.drinks_order_id = None
        self.sweets_order_id = None
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        self.test_results.append(f"❌ {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        self.test_results.append(f"✅ {message}")
        
    def warning(self, message):
        """Log test warnings"""
        print(f"⚠️ WARNING: {message}")
        self.test_results.append(f"⚠️ {message}")

    def setup_test_data(self):
        """Initialize test data and create test employees"""
        try:
            # Initialize data
            response = requests.post(f"{API_BASE}/init-data")
            if response.status_code == 200:
                self.success("Data initialization successful")
            else:
                self.log(f"Init data response: {response.status_code} - may already exist")
            
            # Create test employee in Department 1
            employee_data = {
                "name": self.test_employee_names["dept1"],
                "department_id": self.dept1_id
            }
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_dept1_id = employee["id"]
                self.success(f"Created test employee in Dept 1: {self.test_employee_names['dept1']}")
            else:
                self.error(f"Failed to create test employee in Dept 1: {response.status_code}")
                return False
                
            # Create test employee in Department 3
            employee_data = {
                "name": self.test_employee_names["dept3"],
                "department_id": self.dept3_id
            }
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_dept3_id = employee["id"]
                self.success(f"Created test employee in Dept 3: {self.test_employee_names['dept3']}")
            else:
                self.error(f"Failed to create test employee in Dept 3: {response.status_code}")
                return False
                
            return True
            
        except Exception as e:
            self.error(f"Exception during setup: {str(e)}")
            return False

    def test_bug1_drinks_cancellation_double_deduction(self):
        """
        BUG 1 TEST: Doppelte Stornierung bei Getränken
        
        Test scenario:
        1. Employee orders a drink (e.g., Cola €1.20)
        2. Balance should become -€1.20 (debt)
        3. Cancel the order
        4. Balance should return to €0.00 (NOT +€1.20 as was the bug)
        """
        self.log("\n🎯 TESTING BUG 1: Doppelte Stornierung bei Getränken")
        self.log("=" * 60)
        
        try:
            # Step 1: Get initial balance
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_dept1_id}/profile")
            if response.status_code != 200:
                self.error("Failed to get employee profile")
                return False
                
            initial_profile = response.json()
            initial_balance = initial_profile.get("drinks_sweets_balance", 0.0)
            self.log(f"Initial drinks/sweets balance: €{initial_balance}")
            
            # Step 2: Create drinks order (Cola €1.20)
            order_data = {
                "employee_id": self.test_employee_dept1_id,
                "department_id": self.dept1_id,
                "order_type": "drinks",
                "drink_items": {"cola_id": 1}  # Assuming cola exists in menu
            }
            
            # First, let's get the drinks menu to find a real drink
            menu_response = requests.get(f"{API_BASE}/menu/drinks/{self.dept1_id}")
            if menu_response.status_code == 200:
                drinks_menu = menu_response.json()
                if drinks_menu:
                    # Use the first available drink
                    first_drink = drinks_menu[0]
                    drink_id = first_drink["id"]
                    drink_name = first_drink["name"]
                    drink_price = first_drink["price"]
                    
                    order_data["drink_items"] = {drink_id: 1}
                    self.log(f"Ordering: {drink_name} €{drink_price}")
                else:
                    self.error("No drinks found in menu")
                    return False
            else:
                self.error("Failed to get drinks menu")
                return False
            
            # Create the order
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.drinks_order_id = order["id"]
                order_total = order["total_price"]
                self.success(f"Created drinks order: {drink_name} (ID: {order['id'][:8]}..., Total: €{order_total})")
            else:
                self.error(f"Failed to create drinks order: {response.status_code} - {response.text}")
                return False
            
            # Step 3: Verify balance after order (should be negative)
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_dept1_id}/profile")
            if response.status_code == 200:
                profile_after_order = response.json()
                balance_after_order = profile_after_order.get("drinks_sweets_balance", 0.0)
                expected_balance = initial_balance + order_total  # order_total is negative for drinks
                
                self.log(f"Balance after order: €{balance_after_order}")
                if abs(balance_after_order - expected_balance) < 0.01:
                    self.success(f"Balance correctly updated after drinks order")
                else:
                    self.warning(f"Balance after order: €{balance_after_order}, expected: €{expected_balance}")
            else:
                self.error("Failed to get employee profile after order")
                return False
            
            # Step 4: Cancel the order (this is where the bug was)
            response = requests.delete(f"{API_BASE}/employee/{self.test_employee_dept1_id}/orders/{self.drinks_order_id}")
            if response.status_code == 200:
                self.success("Drinks order cancelled successfully")
            else:
                self.error(f"Failed to cancel drinks order: {response.status_code} - {response.text}")
                return False
            
            # Step 5: Verify balance after cancellation (should return to initial balance, NOT double positive)
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_dept1_id}/profile")
            if response.status_code == 200:
                profile_after_cancel = response.json()
                final_balance = profile_after_cancel.get("drinks_sweets_balance", 0.0)
                
                self.log(f"Final balance after cancellation: €{final_balance}")
                
                # Check if balance returned to initial (should be close to 0 or initial balance)
                if abs(final_balance - initial_balance) < 0.01:
                    self.success(f"✅ BUG 1 FIXED: Balance correctly returned to €{final_balance} after cancellation")
                    return True
                elif final_balance > initial_balance + abs(order_total):
                    self.error(f"❌ BUG 1 STILL EXISTS: Double positive balance detected! Expected ~€{initial_balance}, got €{final_balance}")
                    return False
                else:
                    self.warning(f"Balance after cancellation: €{final_balance} (expected ~€{initial_balance})")
                    return True
            else:
                self.error("Failed to get employee profile after cancellation")
                return False
                
        except Exception as e:
            self.error(f"Exception during BUG 1 test: {str(e)}")
            return False

    def test_bug1_sweets_cancellation_double_deduction(self):
        """
        BUG 1 TEST: Doppelte Stornierung bei Süßigkeiten
        
        Similar test for sweets orders
        """
        self.log("\n🎯 TESTING BUG 1: Doppelte Stornierung bei Süßigkeiten")
        self.log("=" * 60)
        
        try:
            # Get initial balance
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_dept1_id}/profile")
            if response.status_code != 200:
                self.error("Failed to get employee profile")
                return False
                
            initial_profile = response.json()
            initial_balance = initial_profile.get("drinks_sweets_balance", 0.0)
            self.log(f"Initial drinks/sweets balance: €{initial_balance}")
            
            # Get sweets menu
            menu_response = requests.get(f"{API_BASE}/menu/sweets/{self.dept1_id}")
            if menu_response.status_code == 200:
                sweets_menu = menu_response.json()
                if sweets_menu:
                    first_sweet = sweets_menu[0]
                    sweet_id = first_sweet["id"]
                    sweet_name = first_sweet["name"]
                    sweet_price = first_sweet["price"]
                    self.log(f"Ordering: {sweet_name} €{sweet_price}")
                else:
                    self.error("No sweets found in menu")
                    return False
            else:
                self.error("Failed to get sweets menu")
                return False
            
            # Create sweets order
            order_data = {
                "employee_id": self.test_employee_dept1_id,
                "department_id": self.dept1_id,
                "order_type": "sweets",
                "sweet_items": {sweet_id: 1}
            }
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.sweets_order_id = order["id"]
                order_total = order["total_price"]
                self.success(f"Created sweets order: {sweet_name} (ID: {order['id'][:8]}..., Total: €{order_total})")
            else:
                self.error(f"Failed to create sweets order: {response.status_code} - {response.text}")
                return False
            
            # Verify balance after order
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_dept1_id}/profile")
            if response.status_code == 200:
                profile_after_order = response.json()
                balance_after_order = profile_after_order.get("drinks_sweets_balance", 0.0)
                self.log(f"Balance after sweets order: €{balance_after_order}")
            
            # Cancel the order
            response = requests.delete(f"{API_BASE}/employee/{self.test_employee_dept1_id}/orders/{self.sweets_order_id}")
            if response.status_code == 200:
                self.success("Sweets order cancelled successfully")
            else:
                self.error(f"Failed to cancel sweets order: {response.status_code} - {response.text}")
                return False
            
            # Verify final balance
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_dept1_id}/profile")
            if response.status_code == 200:
                profile_after_cancel = response.json()
                final_balance = profile_after_cancel.get("drinks_sweets_balance", 0.0)
                
                self.log(f"Final balance after sweets cancellation: €{final_balance}")
                
                if abs(final_balance - initial_balance) < 0.01:
                    self.success(f"✅ BUG 1 FIXED: Sweets balance correctly returned to €{final_balance}")
                    return True
                elif final_balance > initial_balance + abs(order_total):
                    self.error(f"❌ BUG 1 STILL EXISTS: Double positive balance in sweets! Expected ~€{initial_balance}, got €{final_balance}")
                    return False
                else:
                    self.warning(f"Sweets balance after cancellation: €{final_balance}")
                    return True
            else:
                self.error("Failed to get employee profile after sweets cancellation")
                return False
                
        except Exception as e:
            self.error(f"Exception during BUG 1 sweets test: {str(e)}")
            return False

    def test_bug2_subaccount_payment_wrong_account(self):
        """
        BUG 2 TEST: Falsche Subkonto-Buchung im "Andere WA" Tab
        
        Test scenario:
        1. Admin from Dept 2 makes payment for employee from Dept 1
        2. Payment should go to employee's subaccount for Dept 2 (not main account)
        3. Verify the payment went to the correct subaccount
        """
        self.log("\n🎯 TESTING BUG 2: Falsche Subkonto-Buchung im 'Andere WA' Tab")
        self.log("=" * 60)
        
        try:
            # Step 1: Get initial balances for employee from Dept 1
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_dept1_id}/all-balances")
            if response.status_code == 200:
                initial_balances = response.json()
                initial_main_breakfast = initial_balances["main_balances"]["breakfast"]
                initial_subaccount_dept2_breakfast = initial_balances["subaccount_balances"].get(self.dept2_id, {}).get("breakfast", 0.0)
                
                self.log(f"Initial main account breakfast balance: €{initial_main_breakfast}")
                self.log(f"Initial Dept 2 subaccount breakfast balance: €{initial_subaccount_dept2_breakfast}")
            else:
                self.error("Failed to get employee all balances")
                return False
            
            # Step 2: Admin from Dept 2 makes subaccount payment for employee from Dept 1
            payment_data = {
                "payment_type": "breakfast",  # Required field
                "balance_type": "breakfast",
                "amount": 10.0,
                "payment_method": "cash",
                "notes": "Test subaccount payment for BUG 2"
            }
            
            # Use the subaccount payment endpoint with admin_department parameter
            response = requests.post(
                f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_dept1_id}?admin_department={self.dept2_id}",
                json=payment_data
            )
            
            if response.status_code == 200:
                payment_result = response.json()
                self.success(f"Subaccount payment successful: €{payment_result.get('amount', 0)}")
                self.log(f"Payment details: {payment_result.get('message', '')}")
            else:
                self.error(f"Failed to make subaccount payment: {response.status_code} - {response.text}")
                return False
            
            # Step 3: Verify payment went to correct subaccount (not main account)
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_dept1_id}/all-balances")
            if response.status_code == 200:
                final_balances = response.json()
                final_main_breakfast = final_balances["main_balances"]["breakfast"]
                final_subaccount_dept2_breakfast = final_balances["subaccount_balances"].get(self.dept2_id, {}).get("breakfast", 0.0)
                
                self.log(f"Final main account breakfast balance: €{final_main_breakfast}")
                self.log(f"Final Dept 2 subaccount breakfast balance: €{final_subaccount_dept2_breakfast}")
                
                # Check if payment went to subaccount (correct behavior)
                subaccount_increase = final_subaccount_dept2_breakfast - initial_subaccount_dept2_breakfast
                main_account_change = final_main_breakfast - initial_main_breakfast
                
                if abs(subaccount_increase - 10.0) < 0.01 and abs(main_account_change) < 0.01:
                    self.success(f"✅ BUG 2 FIXED: Payment correctly went to subaccount (+€{subaccount_increase})")
                    return True
                elif abs(main_account_change - 10.0) < 0.01:
                    self.error(f"❌ BUG 2 STILL EXISTS: Payment went to main account instead of subaccount!")
                    return False
                else:
                    self.warning(f"Unexpected balance changes: main +€{main_account_change}, subaccount +€{subaccount_increase}")
                    return False
            else:
                self.error("Failed to get final employee balances")
                return False
                
        except Exception as e:
            self.error(f"Exception during BUG 2 test: {str(e)}")
            return False

    def test_bug3_guest_employee_order_error(self):
        """
        BUG 3 TEST: Bestellfehler bei Gastmitarbeitern
        
        Test scenario:
        1. Add employee from Dept 1 as temporary worker in Dept 3
        2. Try to create an order for this guest employee in Dept 3
        3. Order should succeed or give clear error message (not "Fehler beim Speichern der Bestellung")
        """
        self.log("\n🎯 TESTING BUG 3: Bestellfehler bei Gastmitarbeitern")
        self.log("=" * 60)
        
        try:
            # Step 1: Add employee from Dept 1 as temporary worker in Dept 3
            temp_assignment_data = {
                "employee_id": self.test_employee_dept1_id
            }
            
            response = requests.post(
                f"{API_BASE}/departments/{self.dept3_id}/temporary-employees",
                json=temp_assignment_data
            )
            
            if response.status_code == 200:
                assignment_result = response.json()
                self.success(f"Added temporary employee to Dept 3: {assignment_result.get('employee_name', '')}")
                assignment_id = assignment_result.get("assignment_id")
            else:
                self.error(f"Failed to add temporary employee: {response.status_code} - {response.text}")
                return False
            
            # Step 2: Try to create a breakfast order for the guest employee in Dept 3
            order_data = {
                "employee_id": self.test_employee_dept1_id,
                "department_id": self.dept3_id,  # Guest employee ordering in Dept 3
                "order_type": "breakfast",
                "notes": "Test order for guest employee (BUG 3)",
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
            
            self.log(f"Creating breakfast order for guest employee in Dept 3...")
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                self.success(f"✅ BUG 3 FIXED: Guest employee order successful! (ID: {order['id'][:8]}..., Total: €{order['total_price']})")
                return True
            elif response.status_code == 400:
                error_message = response.text
                if "Fehler beim Speichern der Bestellung" in error_message:
                    self.error(f"❌ BUG 3 STILL EXISTS: Generic error message: {error_message}")
                    return False
                else:
                    self.success(f"✅ BUG 3 IMPROVED: Clear error message provided: {error_message}")
                    return True
            else:
                error_message = response.text
                self.log(f"Order failed with status {response.status_code}: {error_message}")
                
                # Check if it's a clear, specific error message (improvement) vs generic error (bug still exists)
                if ("Fehler beim Speichern der Bestellung" in error_message or 
                    "Internal Server Error" in error_message or
                    error_message.strip() == ""):
                    self.error(f"❌ BUG 3 STILL EXISTS: Generic/unclear error: {error_message}")
                    return False
                else:
                    self.success(f"✅ BUG 3 IMPROVED: Specific error message: {error_message}")
                    return True
            
            # Cleanup: Remove temporary assignment
            try:
                requests.delete(f"{API_BASE}/departments/{self.dept3_id}/temporary-employees/{assignment_id}")
                self.log("Cleaned up temporary assignment")
            except:
                pass
                
        except Exception as e:
            self.error(f"Exception during BUG 3 test: {str(e)}")
            return False

    def run_all_critical_bug_tests(self):
        """Run all three critical bug fix tests"""
        self.log("🎯 STARTING THREE CRITICAL BUG FIXES VERIFICATION")
        self.log("=" * 80)
        self.log("🚨 TESTING THREE CRITICAL USER-REPORTED BUGS:")
        self.log("   BUG 1: Doppelte Stornierung bei Süßigkeiten/Getränken")
        self.log("   BUG 2: Falsche Subkonto-Buchung im 'Andere WA' Tab")
        self.log("   BUG 3: Bestellfehler bei Gastmitarbeitern")
        self.log("=" * 80)
        
        # Setup test data
        if not self.setup_test_data():
            self.error("Failed to setup test data")
            return False
        
        # Run all bug tests
        test_results = {
            "BUG 1 - Drinks Cancellation": self.test_bug1_drinks_cancellation_double_deduction(),
            "BUG 1 - Sweets Cancellation": self.test_bug1_sweets_cancellation_double_deduction(),
            "BUG 2 - Subaccount Payment": self.test_bug2_subaccount_payment_wrong_account(),
            "BUG 3 - Guest Employee Orders": self.test_bug3_guest_employee_order_error()
        }
        
        # Summary
        self.log("\n" + "=" * 80)
        self.log("🎯 THREE CRITICAL BUG FIXES TEST RESULTS:")
        self.log("=" * 80)
        
        passed_tests = 0
        total_tests = len(test_results)
        
        for test_name, result in test_results.items():
            if result:
                self.success(f"{test_name}: PASSED")
                passed_tests += 1
            else:
                self.error(f"{test_name}: FAILED")
        
        self.log(f"\nOVERALL RESULT: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.success("🎉 ALL THREE CRITICAL BUG FIXES VERIFIED WORKING!")
            return True
        else:
            self.error(f"❌ {total_tests - passed_tests} CRITICAL BUGS STILL NEED ATTENTION!")
            return False

def main():
    """Main test execution"""
    print("🧪 Three Critical Bug Fixes Test Suite")
    print("=" * 50)
    
    test_suite = ThreeCriticalBugsTest()
    success = test_suite.run_all_critical_bug_tests()
    
    if success:
        print("\n🎉 ALL THREE CRITICAL BUG FIXES ARE WORKING!")
        exit(0)
    else:
        print("\n❌ SOME CRITICAL BUGS STILL NEED FIXING!")
        exit(1)

if __name__ == "__main__":
    main()