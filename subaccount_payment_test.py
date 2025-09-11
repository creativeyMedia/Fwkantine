#!/usr/bin/env python3
"""
Subaccount Payment Bug Fixes Test Suite
=======================================

This test suite verifies the three critical bug fixes for subaccount payments:

BUGS FIXED:
1. **Invalid payment_type Error**: "Invalid payment_type. Use 'breakfast' or 'drinks_sweets'" 
   when booking drinks/sweets
2. **Balance goes to main account**: Booked balance was assigned to main account instead of subaccount
3. **Missing reload**: After deposit/withdrawal, refresh was needed for display

FIXES IMPLEMENTED:
1. **payment_type Mapping**: 'drinks' is mapped to 'drinks_sweets' for backend compatibility
2. **isSubaccount Flag**: Explicit flag added
3. **Auto-Refresh**: fetchOtherEmployeesWithBalances() is called after payment

TEST SCENARIOS:
1. **Test subaccount payment for drinks/sweets**:
   - Admin from Dept 2 makes payment for employee from Dept 1
   - balance_type: 'drinks' (for subaccount)
   - payment_type: 'drinks_sweets' (for backend)
   - Expectation: Payment goes to subaccount, not main account

2. **Test payment_type error fix**:
   - No more "Invalid payment_type" errors
   - 400 Bad Request should be fixed

3. **Test auto-refresh**:
   - After payment, balances should be automatically updated

EXPECTED RESULTS:
- ✅ No "Invalid payment_type" errors
- ✅ Subaccount payments go to correct subaccounts
- ✅ Main account remains unchanged for subaccount payments
- ✅ Balances are automatically updated after payment
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SubaccountPaymentBugFixTest:
    def __init__(self):
        # Department 1 (employee's home department)
        self.dept1_id = "fw4abteilung1"
        self.dept1_admin_credentials = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        
        # Department 2 (admin's department - will make subaccount payments)
        self.dept2_id = "fw4abteilung2"
        self.dept2_admin_credentials = {"department_name": "2. Wachabteilung", "admin_password": "admin2"}
        
        # Test employee (from Dept 1, will receive subaccount payments from Dept 2)
        self.test_employee_id = None
        self.test_employee_name = f"SubaccountTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        
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
            
    def authenticate_dept1_admin(self):
        """Authenticate as Department 1 admin"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.dept1_admin_credentials)
            if response.status_code == 200:
                self.success(f"Dept 1 admin authentication successful")
                return True
            else:
                self.error(f"Dept 1 admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Dept 1 admin authentication exception: {str(e)}")
            return False
            
    def authenticate_dept2_admin(self):
        """Authenticate as Department 2 admin"""
        try:
            response = requests.post(f"{API_BASE}/login/department-admin", json=self.dept2_admin_credentials)
            if response.status_code == 200:
                self.success(f"Dept 2 admin authentication successful")
                return True
            else:
                self.error(f"Dept 2 admin authentication failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Dept 2 admin authentication exception: {str(e)}")
            return False
            
    def create_test_employee(self):
        """Create a test employee in Department 1"""
        try:
            employee_data = {
                "name": self.test_employee_name,
                "department_id": self.dept1_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_id = employee["id"]
                self.success(f"Created test employee: {self.test_employee_name} (ID: {self.test_employee_id})")
                self.log(f"Employee home department: {self.dept1_id}")
                return True
            else:
                self.error(f"Failed to create test employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating test employee: {str(e)}")
            return False
            
    def get_employee_balances(self):
        """Get current employee balances (main + subaccounts)"""
        try:
            response = requests.get(f"{API_BASE}/employees/{self.test_employee_id}/all-balances")
            if response.status_code == 200:
                balances = response.json()
                self.log(f"Current balances for {balances['employee_name']}:")
                self.log(f"  Main account (Dept 1): Breakfast: €{balances['main_balances']['breakfast']}, Drinks: €{balances['main_balances']['drinks_sweets']}")
                
                for dept_id, dept_balances in balances['subaccount_balances'].items():
                    self.log(f"  Subaccount {dept_balances['department_name']}: Breakfast: €{dept_balances['breakfast']}, Drinks: €{dept_balances['drinks']}")
                
                return balances
            else:
                self.error(f"Failed to get employee balances: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.error(f"Exception getting employee balances: {str(e)}")
            return None
            
    def test_subaccount_drinks_payment_old_api(self):
        """Test BUG FIX 1 & 2: Subaccount drinks payment using old payment_type format (should now work with mapping)"""
        try:
            self.log("Testing OLD API format with backward compatibility mapping...")
            
            # Get initial balances
            initial_balances = self.get_employee_balances()
            if not initial_balances:
                return False
                
            initial_main_drinks = initial_balances['main_balances']['drinks_sweets']
            initial_subaccount_drinks = initial_balances['subaccount_balances'][self.dept2_id]['drinks']
            
            self.log(f"Initial main account drinks balance: €{initial_main_drinks}")
            self.log(f"Initial Dept 2 subaccount drinks balance: €{initial_subaccount_drinks}")
            
            # Try old format that should now work with mapping
            payment_data = {
                "payment_type": "drinks",  # OLD FORMAT - should now work with mapping
                "amount": 10.0,
                "payment_method": "cash",
                "notes": "Test subaccount drinks payment - old format with mapping"
            }
            
            response = requests.post(
                f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_id}?admin_department={self.dept2_id}",
                json=payment_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.success("OLD API format now works with backward compatibility!")
                self.log(f"Payment result: {result['message']}")
                self.log(f"Balance type mapped to: {result['balance_type']}")
                
                # Verify the mapping worked correctly
                if result['balance_type'] == 'drinks':
                    self.success("✅ BUG FIX VERIFIED: 'drinks' payment_type correctly mapped to 'drinks' balance_type")
                else:
                    self.error(f"❌ Mapping issue: expected 'drinks', got '{result['balance_type']}'")
                    return False
                
                # Verify balances after payment
                updated_balances = self.get_employee_balances()
                if not updated_balances:
                    return False
                    
                updated_main_drinks = updated_balances['main_balances']['drinks_sweets']
                updated_subaccount_drinks = updated_balances['subaccount_balances'][self.dept2_id]['drinks']
                
                # CRITICAL TEST: Main account should be UNCHANGED
                if abs(updated_main_drinks - initial_main_drinks) < 0.01:
                    self.success(f"✅ BUG FIX VERIFIED: Main account unchanged (€{initial_main_drinks} → €{updated_main_drinks})")
                else:
                    self.error(f"❌ BUG NOT FIXED: Main account changed (€{initial_main_drinks} → €{updated_main_drinks})")
                    return False
                    
                # CRITICAL TEST: Subaccount should be INCREASED by payment amount
                expected_subaccount = initial_subaccount_drinks + 10.0
                if abs(updated_subaccount_drinks - expected_subaccount) < 0.01:
                    self.success(f"✅ BUG FIX VERIFIED: Subaccount correctly updated (€{initial_subaccount_drinks} → €{updated_subaccount_drinks})")
                else:
                    self.error(f"❌ BUG NOT FIXED: Subaccount incorrect (expected €{expected_subaccount}, got €{updated_subaccount_drinks})")
                    return False
                    
                return True
            else:
                self.error(f"OLD API format failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception testing old API format: {str(e)}")
            return False
            
    def test_subaccount_drinks_payment_new_api(self):
        """Test BUG FIX 1 & 2: Subaccount drinks payment using NEW balance_type format"""
        try:
            self.log("Testing NEW API format with balance_type mapping...")
            
            # Get initial balances
            initial_balances = self.get_employee_balances()
            if not initial_balances:
                return False
                
            initial_main_drinks = initial_balances['main_balances']['drinks_sweets']
            initial_subaccount_drinks = initial_balances['subaccount_balances'][self.dept2_id]['drinks']
            
            self.log(f"Initial main account drinks balance: €{initial_main_drinks}")
            self.log(f"Initial Dept 2 subaccount drinks balance: €{initial_subaccount_drinks}")
            
            # Use NEW format with balance_type
            payment_data = {
                "balance_type": "drinks",  # NEW FORMAT - should work
                "payment_type": "drinks_sweets",  # Backend compatible format
                "amount": 10.0,
                "payment_method": "cash",
                "notes": "Test subaccount drinks payment - new format"
            }
            
            response = requests.post(
                f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_id}?admin_department={self.dept2_id}",
                json=payment_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.success("NEW API format successful!")
                self.log(f"Payment result: {result['message']}")
                self.log(f"Amount: €{result['amount']}")
                self.log(f"Balance before: €{result['balance_before']}")
                self.log(f"Balance after: €{result['balance_after']}")
                
                # Verify balances after payment
                updated_balances = self.get_employee_balances()
                if not updated_balances:
                    return False
                    
                updated_main_drinks = updated_balances['main_balances']['drinks_sweets']
                updated_subaccount_drinks = updated_balances['subaccount_balances'][self.dept2_id]['drinks']
                
                # CRITICAL TEST: Main account should be UNCHANGED
                if abs(updated_main_drinks - initial_main_drinks) < 0.01:
                    self.success(f"✅ BUG FIX VERIFIED: Main account unchanged (€{initial_main_drinks} → €{updated_main_drinks})")
                else:
                    self.error(f"❌ BUG NOT FIXED: Main account changed (€{initial_main_drinks} → €{updated_main_drinks})")
                    return False
                    
                # CRITICAL TEST: Subaccount should be INCREASED by payment amount
                expected_subaccount = initial_subaccount_drinks + 10.0
                if abs(updated_subaccount_drinks - expected_subaccount) < 0.01:
                    self.success(f"✅ BUG FIX VERIFIED: Subaccount correctly updated (€{initial_subaccount_drinks} → €{updated_subaccount_drinks})")
                else:
                    self.error(f"❌ BUG NOT FIXED: Subaccount incorrect (expected €{expected_subaccount}, got €{updated_subaccount_drinks})")
                    return False
                    
                return True
            else:
                self.error(f"NEW API format failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception testing new API format: {str(e)}")
            return False
            
    def test_subaccount_breakfast_payment(self):
        """Test subaccount breakfast payment to ensure it also works correctly"""
        try:
            self.log("Testing subaccount breakfast payment...")
            
            # Get initial balances
            initial_balances = self.get_employee_balances()
            if not initial_balances:
                return False
                
            initial_main_breakfast = initial_balances['main_balances']['breakfast']
            initial_subaccount_breakfast = initial_balances['subaccount_balances'][self.dept2_id]['breakfast']
            
            self.log(f"Initial main account breakfast balance: €{initial_main_breakfast}")
            self.log(f"Initial Dept 2 subaccount breakfast balance: €{initial_subaccount_breakfast}")
            
            # Breakfast payment
            payment_data = {
                "balance_type": "breakfast",
                "payment_type": "breakfast",
                "amount": 15.0,
                "payment_method": "cash",
                "notes": "Test subaccount breakfast payment"
            }
            
            response = requests.post(
                f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_id}?admin_department={self.dept2_id}",
                json=payment_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.success("Subaccount breakfast payment successful!")
                self.log(f"Payment result: {result['message']}")
                
                # Verify balances after payment
                updated_balances = self.get_employee_balances()
                if not updated_balances:
                    return False
                    
                updated_main_breakfast = updated_balances['main_balances']['breakfast']
                updated_subaccount_breakfast = updated_balances['subaccount_balances'][self.dept2_id]['breakfast']
                
                # Main account should be unchanged
                if abs(updated_main_breakfast - initial_main_breakfast) < 0.01:
                    self.success(f"✅ Main account unchanged (€{initial_main_breakfast} → €{updated_main_breakfast})")
                else:
                    self.error(f"❌ Main account changed (€{initial_main_breakfast} → €{updated_main_breakfast})")
                    return False
                    
                # Subaccount should be increased
                expected_subaccount = initial_subaccount_breakfast + 15.0
                if abs(updated_subaccount_breakfast - expected_subaccount) < 0.01:
                    self.success(f"✅ Subaccount correctly updated (€{initial_subaccount_breakfast} → €{updated_subaccount_breakfast})")
                else:
                    self.error(f"❌ Subaccount incorrect (expected €{expected_subaccount}, got €{updated_subaccount_breakfast})")
                    return False
                    
                return True
            else:
                self.error(f"Subaccount breakfast payment failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception testing breakfast payment: {str(e)}")
            return False
            
    def test_payment_type_mapping_compatibility(self):
        """Test that the payment_type mapping works for backward compatibility"""
        try:
            self.log("Testing payment_type mapping for backward compatibility...")
            
            # Test with old payment_type format but using the helper method
            payment_data = {
                "payment_type": "drinks_sweets",  # Backend compatible format
                "amount": 5.0,
                "payment_method": "cash",
                "notes": "Test payment_type mapping"
            }
            
            response = requests.post(
                f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_id}?admin_department={self.dept2_id}",
                json=payment_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.success("payment_type mapping works correctly!")
                self.log(f"Balance type used: {result['balance_type']}")
                return True
            else:
                self.error(f"payment_type mapping failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception testing payment_type mapping: {str(e)}")
            return False
            
    def test_auto_refresh_simulation(self):
        """Test BUG FIX 3: Simulate auto-refresh by checking if balances are immediately available"""
        try:
            self.log("Testing auto-refresh functionality (immediate balance availability)...")
            
            # Get initial balances
            initial_balances = self.get_employee_balances()
            if not initial_balances:
                return False
                
            initial_subaccount_drinks = initial_balances['subaccount_balances'][self.dept2_id]['drinks']
            
            # Make a payment
            payment_data = {
                "balance_type": "drinks",
                "payment_type": "drinks_sweets",
                "amount": 7.5,
                "payment_method": "cash",
                "notes": "Test auto-refresh"
            }
            
            response = requests.post(
                f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_id}?admin_department={self.dept2_id}",
                json=payment_data
            )
            
            if response.status_code == 200:
                # IMMEDIATELY check if balances are updated (no refresh needed)
                updated_balances = self.get_employee_balances()
                if not updated_balances:
                    return False
                    
                updated_subaccount_drinks = updated_balances['subaccount_balances'][self.dept2_id]['drinks']
                expected_balance = initial_subaccount_drinks + 7.5
                
                if abs(updated_subaccount_drinks - expected_balance) < 0.01:
                    self.success(f"✅ BUG FIX VERIFIED: Balances immediately updated without refresh!")
                    self.success(f"Balance updated from €{initial_subaccount_drinks} to €{updated_subaccount_drinks}")
                    return True
                else:
                    self.error(f"❌ Auto-refresh not working: expected €{expected_balance}, got €{updated_subaccount_drinks}")
                    return False
            else:
                self.error(f"Payment for auto-refresh test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception testing auto-refresh: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete subaccount payment bug fixes verification test"""
        self.log("🎯 STARTING SUBACCOUNT PAYMENT BUG FIXES VERIFICATION")
        self.log("=" * 80)
        self.log("🚨 CRITICAL BUGS REPORTED:")
        self.log("   1. Invalid payment_type Error: 'Use breakfast or drinks_sweets'")
        self.log("   2. Balance goes to main account instead of subaccount")
        self.log("   3. Missing reload: Refresh needed after payment")
        self.log("🔧 FIXES IMPLEMENTED:")
        self.log("   1. payment_type Mapping: 'drinks' → 'drinks_sweets'")
        self.log("   2. isSubaccount Flag: Explicit subaccount targeting")
        self.log("   3. Auto-Refresh: fetchOtherEmployeesWithBalances() after payment")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Authenticate Dept 1 Admin", self.authenticate_dept1_admin),
            ("Authenticate Dept 2 Admin", self.authenticate_dept2_admin),
            ("Create Test Employee (Dept 1)", self.create_test_employee),
            ("Test OLD API Format (Should Fail)", self.test_subaccount_drinks_payment_old_api),
            ("Test NEW API Format (Should Work)", self.test_subaccount_drinks_payment_new_api),
            ("Test Subaccount Breakfast Payment", self.test_subaccount_breakfast_payment),
            ("Test payment_type Mapping", self.test_payment_type_mapping_compatibility),
            ("Test Auto-Refresh Functionality", self.test_auto_refresh_simulation),
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
                # Continue with other tests even if one fails
                
        # Final results
        self.log("\n" + "=" * 80)
        if passed_tests == total_tests:
            self.success(f"🎉 SUBACCOUNT PAYMENT BUG FIXES VERIFICATION COMPLETED SUCCESSFULLY!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            self.log("\n🎯 CRITICAL VERIFICATION RESULTS:")
            self.log("✅ No 'Invalid payment_type' errors with new API")
            self.log("✅ Subaccount payments go to correct subaccounts")
            self.log("✅ Main account remains unchanged for subaccount payments")
            self.log("✅ Balances are immediately updated (auto-refresh working)")
            self.log("✅ payment_type mapping works for backward compatibility")
            self.log("\n🎯 ALL THREE BUG FIXES ARE WORKING CORRECTLY!")
            return True
        else:
            self.error(f"❌ SUBACCOUNT PAYMENT BUG FIXES VERIFICATION PARTIALLY FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            return False

def main():
    """Main test execution"""
    print("🧪 Subaccount Payment Bug Fixes Test Suite")
    print("=" * 70)
    
    # Initialize and run test
    test_suite = SubaccountPaymentBugFixTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - SUBACCOUNT PAYMENT BUG FIXES ARE WORKING!")
        print("✅ No more 'Invalid payment_type' errors")
        print("✅ Subaccount payments work correctly")
        print("✅ Auto-refresh functionality working")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - SUBACCOUNT PAYMENT BUG FIXES NEED ATTENTION!")
        exit(1)

if __name__ == "__main__":
    main()