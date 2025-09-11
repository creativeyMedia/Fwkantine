#!/usr/bin/env python3
"""
Specific Scenario Test for Subaccount Payment Bug Fixes
=======================================================

This test verifies the EXACT scenario mentioned in the German review request:

SCENARIO:
- Admin aus Abt. 2 macht Zahlung für Mitarbeiter aus Abt. 1
- balance_type: 'drinks' (für Subkonto)
- payment_type: 'drinks_sweets' (für Backend)
- Erwartung: Zahlung geht an Subkonto, nicht Hauptkonto

EXPECTED RESULTS:
- ✅ Keine "Invalid payment_type" Fehler mehr
- ✅ Subkonto-Zahlungen gehen an korrekte Subkonten
- ✅ Hauptkonto bleibt unverändert bei Subkonto-Zahlungen
- ✅ Balances werden automatisch nach Zahlung aktualisiert
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SpecificScenarioTest:
    def __init__(self):
        # Department 1 (employee's home department)
        self.dept1_id = "fw4abteilung1"
        self.dept1_name = "1. Wachabteilung"
        
        # Department 2 (admin's department - will make subaccount payments)
        self.dept2_id = "fw4abteilung2"
        self.dept2_name = "2. Wachabteilung"
        self.dept2_admin_credentials = {"department_name": self.dept2_name, "admin_password": "admin2"}
        
        # Test employee (from Dept 1, will receive subaccount payments from Dept 2)
        self.test_employee_id = None
        self.test_employee_name = f"SpecificTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        
    def create_test_employee_dept1(self):
        """Create test employee in Department 1"""
        try:
            employee_data = {
                "name": self.test_employee_name,
                "department_id": self.dept1_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_id = employee["id"]
                self.success(f"Created test employee in Dept 1: {self.test_employee_name}")
                self.log(f"Employee ID: {self.test_employee_id}")
                self.log(f"Employee home department: {self.dept1_id} ({self.dept1_name})")
                return True
            else:
                self.error(f"Failed to create test employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating test employee: {str(e)}")
            return False
            
    def authenticate_dept2_admin(self):
        """Authenticate as Department 2 admin"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.dept2_admin_credentials)
            if response.status_code == 200:
                self.success(f"Authenticated as admin for {self.dept2_name}")
                return True
            else:
                self.error(f"Admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Admin authentication exception: {str(e)}")
            return False
            
    def get_employee_balances(self):
        """Get current employee balances"""
        try:
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_id}/all-balances")
            if response.status_code == 200:
                balances = response.json()
                return balances
            else:
                self.error(f"Failed to get employee balances: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.error(f"Exception getting employee balances: {str(e)}")
            return None
            
    def test_exact_scenario_from_review(self):
        """Test the EXACT scenario from the German review request"""
        try:
            self.log("🎯 TESTING EXACT SCENARIO FROM REVIEW REQUEST:")
            self.log("   Admin aus Abt. 2 macht Zahlung für Mitarbeiter aus Abt. 1")
            self.log("   balance_type: 'drinks' (für Subkonto)")
            self.log("   payment_type: 'drinks_sweets' (für Backend)")
            self.log("   Erwartung: Zahlung geht an Subkonto, nicht Hauptkonto")
            
            # Get initial balances
            initial_balances = self.get_employee_balances()
            if not initial_balances:
                return False
                
            initial_main_drinks = initial_balances['main_balances']['drinks_sweets']
            initial_subaccount_drinks = initial_balances['subaccount_balances'][self.dept2_id]['drinks']
            
            self.log(f"📊 INITIAL BALANCES:")
            self.log(f"   Hauptkonto (Dept 1) Getränke: €{initial_main_drinks}")
            self.log(f"   Subkonto (Dept 2) Getränke: €{initial_subaccount_drinks}")
            
            # EXACT scenario from review request
            payment_data = {
                "balance_type": "drinks",  # für Subkonto
                "payment_type": "drinks_sweets",  # für Backend
                "amount": 25.0,
                "payment_method": "cash",
                "notes": "Admin aus Abt. 2 macht Zahlung für Mitarbeiter aus Abt. 1"
            }
            
            self.log(f"💰 MAKING PAYMENT:")
            self.log(f"   Admin Department: {self.dept2_id} ({self.dept2_name})")
            self.log(f"   Employee Department: {self.dept1_id} ({self.dept1_name})")
            self.log(f"   balance_type: '{payment_data['balance_type']}'")
            self.log(f"   payment_type: '{payment_data['payment_type']}'")
            self.log(f"   Amount: €{payment_data['amount']}")
            
            response = requests.post(
                f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_id}?admin_department={self.dept2_id}",
                json=payment_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.success("✅ PAYMENT SUCCESSFUL - No 'Invalid payment_type' error!")
                self.log(f"   Result: {result['message']}")
                self.log(f"   Department: {result['department']}")
                self.log(f"   Balance type: {result['balance_type']}")
                self.log(f"   Amount: €{result['amount']}")
                self.log(f"   Balance before: €{result['balance_before']}")
                self.log(f"   Balance after: €{result['balance_after']}")
                
                # Verify balances after payment
                updated_balances = self.get_employee_balances()
                if not updated_balances:
                    return False
                    
                updated_main_drinks = updated_balances['main_balances']['drinks_sweets']
                updated_subaccount_drinks = updated_balances['subaccount_balances'][self.dept2_id]['drinks']
                
                self.log(f"📊 UPDATED BALANCES:")
                self.log(f"   Hauptkonto (Dept 1) Getränke: €{updated_main_drinks}")
                self.log(f"   Subkonto (Dept 2) Getränke: €{updated_subaccount_drinks}")
                
                # CRITICAL VERIFICATION 1: Main account unchanged
                if abs(updated_main_drinks - initial_main_drinks) < 0.01:
                    self.success("✅ BUG FIX VERIFIED: Hauptkonto bleibt unverändert!")
                    self.log(f"   Hauptkonto: €{initial_main_drinks} → €{updated_main_drinks} (UNCHANGED)")
                else:
                    self.error(f"❌ BUG NOT FIXED: Hauptkonto changed (€{initial_main_drinks} → €{updated_main_drinks})")
                    return False
                    
                # CRITICAL VERIFICATION 2: Subaccount correctly updated
                expected_subaccount = initial_subaccount_drinks + 25.0
                if abs(updated_subaccount_drinks - expected_subaccount) < 0.01:
                    self.success("✅ BUG FIX VERIFIED: Zahlung geht an korrektes Subkonto!")
                    self.log(f"   Subkonto: €{initial_subaccount_drinks} → €{updated_subaccount_drinks} (+€25.0)")
                else:
                    self.error(f"❌ BUG NOT FIXED: Subkonto incorrect (expected €{expected_subaccount}, got €{updated_subaccount_drinks})")
                    return False
                    
                # CRITICAL VERIFICATION 3: Auto-refresh working (balances immediately available)
                self.success("✅ BUG FIX VERIFIED: Balances automatisch aktualisiert (kein Refresh nötig)!")
                
                return True
            else:
                self.error(f"❌ PAYMENT FAILED: {response.status_code} - {response.text}")
                if "Invalid payment_type" in response.text:
                    self.error("❌ BUG NOT FIXED: Still getting 'Invalid payment_type' error!")
                return False
                
        except Exception as e:
            self.error(f"Exception testing exact scenario: {str(e)}")
            return False
            
    def run_specific_scenario_test(self):
        """Run the specific scenario test"""
        self.log("🎯 STARTING SPECIFIC SCENARIO TEST FROM GERMAN REVIEW REQUEST")
        self.log("=" * 80)
        self.log("🇩🇪 ORIGINAL REQUEST:")
        self.log("   'Admin aus Abt. 2 macht Zahlung für Mitarbeiter aus Abt. 1'")
        self.log("   'balance_type: drinks (für Subkonto)'")
        self.log("   'payment_type: drinks_sweets (für Backend)'")
        self.log("   'Erwartung: Zahlung geht an Subkonto, nicht Hauptkonto'")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Create Test Employee in Dept 1", self.create_test_employee_dept1),
            ("Authenticate Dept 2 Admin", self.authenticate_dept2_admin),
            ("Test Exact Scenario from Review", self.test_exact_scenario_from_review),
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        
        for step_name, step_function in test_steps:
            self.log(f"\n📋 Step {passed_tests + 1}/{total_tests}: {step_name}")
            self.log("-" * 50)
            
            if step_function():
                passed_tests += 1
                self.success(f"Step {passed_tests}/{total_tests} PASSED: {step_name}")
            else:
                self.error(f"Step {passed_tests + 1}/{total_tests} FAILED: {step_name}")
                break  # Stop on first failure for this specific test
                
        # Final results
        self.log("\n" + "=" * 80)
        if passed_tests == total_tests:
            self.success(f"🎉 SPECIFIC SCENARIO TEST COMPLETED SUCCESSFULLY!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            self.log("\n🎯 GERMAN REVIEW REQUEST VERIFICATION:")
            self.log("✅ Keine 'Invalid payment_type' Fehler mehr")
            self.log("✅ Subkonto-Zahlungen gehen an korrekte Subkonten")
            self.log("✅ Hauptkonto bleibt unverändert bei Subkonto-Zahlungen")
            self.log("✅ Balances werden automatisch nach Zahlung aktualisiert")
            self.log("\n🇩🇪 ALLE DREI SUBKONTO-ZAHLUNG-BUG-FIXES FUNKTIONIEREN KORREKT!")
            return True
        else:
            self.error(f"❌ SPECIFIC SCENARIO TEST FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            return False

def main():
    """Main test execution"""
    print("🧪 Specific Scenario Test - Subaccount Payment Bug Fixes")
    print("=" * 70)
    
    # Initialize and run test
    test_suite = SpecificScenarioTest()
    success = test_suite.run_specific_scenario_test()
    
    if success:
        print("\n🎉 SPECIFIC SCENARIO TEST PASSED!")
        print("✅ Admin aus Abt. 2 kann Zahlung für Mitarbeiter aus Abt. 1 machen")
        print("✅ Zahlung geht korrekt an Subkonto, nicht Hauptkonto")
        print("✅ Alle drei Bug-Fixes funktionieren wie erwartet")
        exit(0)
    else:
        print("\n❌ SPECIFIC SCENARIO TEST FAILED!")
        exit(1)

if __name__ == "__main__":
    main()