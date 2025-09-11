#!/usr/bin/env python3
"""
Subaccount Payment Notes Test Suite - User-Friendly Hint Display
================================================================

This test suite verifies the user-friendly hint display for subaccount payments.

FEATURE TESTED:
- Backend loads department_name from database
- payment_log notes format: "Zahlung in [Department Name] ([Payment Method]) - [User Notes]"

EXPECTED BEHAVIOR:
- User wanted: "Zahlung in 1. Wachabteilung" instead of "fw4abteilung1" in payment_log notes
- Backend should load readable department names from database
- Notes should be formatted with user-friendly department names

TEST SCENARIOS:
1. Create subaccount payment for fw4abteilung1
2. Check if notes contain "Zahlung in 1. Wachabteilung (cash)"
3. Compare with old version "fw4abteilung1" (should NOT appear)
4. Test different payment methods and user notes
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SubaccountPaymentNotesTest:
    def __init__(self):
        self.test_employee_id = None
        self.test_employee_name = f"SubaccountNotesTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.payment_log_ids = []
        
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
                return True  # May fail if data exists, which is OK
        except Exception as e:
            self.error(f"Exception during data initialization: {str(e)}")
            return False
            
    def create_test_employee(self):
        """Create a test employee in fw4abteilung2 (different from payment department)"""
        try:
            employee_data = {
                "name": self.test_employee_name,
                "department_id": "fw4abteilung2"  # Employee from dept 2
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_id = employee["id"]
                self.success(f"Created test employee: {self.test_employee_name} (ID: {self.test_employee_id}) in fw4abteilung2")
                return True
            else:
                self.error(f"Failed to create test employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating test employee: {str(e)}")
            return False
            
    def test_subaccount_payment_with_user_friendly_notes(self):
        """Test subaccount payment and verify user-friendly department names in notes"""
        try:
            # Admin from fw4abteilung1 makes payment for employee from fw4abteilung2
            admin_department = "fw4abteilung1"
            payment_data = {
                "balance_type": "breakfast",
                "payment_type": "breakfast", 
                "amount": 10.0,
                "payment_method": "cash",
                "notes": "Test payment for user-friendly notes"
            }
            
            self.log(f"Making subaccount payment: Admin from {admin_department} pays for employee from fw4abteilung2")
            
            response = requests.post(
                f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_id}?admin_department={admin_department}",
                json=payment_data
            )
            
            if response.status_code == 200:
                result = response.json()
                self.success(f"Subaccount payment successful: €{result['amount']}")
                
                # Now check the payment log for user-friendly notes
                return self.verify_payment_log_notes(admin_department, payment_data)
            else:
                self.error(f"Failed to make subaccount payment: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception making subaccount payment: {str(e)}")
            return False
            
    def verify_payment_log_notes(self, admin_department, payment_data):
        """Verify that payment log contains user-friendly department names"""
        try:
            # Get payment logs for the test employee
            response = requests.get(f"{API_BASE}/department-admin/payment-logs/{self.test_employee_id}")
            
            if response.status_code == 200:
                payment_logs = response.json()
                
                if not payment_logs:
                    self.error("No payment logs found for test employee")
                    return False
                
                # Find the most recent payment log
                latest_log = payment_logs[0]  # Assuming logs are sorted by timestamp desc
                notes = latest_log.get("notes", "")
                
                self.log(f"Payment log notes: '{notes}'")
                
                # Check for user-friendly department name
                expected_dept_name = "1. Wachabteilung"  # fw4abteilung1 should be "1. Wachabteilung"
                expected_payment_method = payment_data["payment_method"]
                expected_user_notes = payment_data["notes"]
                
                # Expected format: "Zahlung in [Department Name] ([Payment Method]) - [User Notes]"
                expected_pattern = f"Zahlung in {expected_dept_name} ({expected_payment_method})"
                
                if expected_pattern in notes:
                    self.success(f"✅ USER-FRIENDLY DEPARTMENT NAME FOUND: '{expected_pattern}' in notes")
                    
                    # Check that technical ID is NOT present
                    if admin_department not in notes:
                        self.success(f"✅ TECHNICAL ID REMOVED: '{admin_department}' not found in notes")
                    else:
                        self.error(f"❌ TECHNICAL ID STILL PRESENT: '{admin_department}' found in notes")
                        return False
                        
                    # Check user notes are included
                    if expected_user_notes in notes:
                        self.success(f"✅ USER NOTES INCLUDED: '{expected_user_notes}' found in notes")
                    else:
                        self.error(f"❌ USER NOTES MISSING: '{expected_user_notes}' not found in notes")
                        return False
                        
                    return True
                else:
                    self.error(f"❌ USER-FRIENDLY DEPARTMENT NAME NOT FOUND: Expected '{expected_pattern}' in notes")
                    self.error(f"   Actual notes: '{notes}'")
                    return False
                    
            else:
                self.error(f"Failed to get payment logs: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception verifying payment log notes: {str(e)}")
            return False
            
    def test_multiple_departments_and_payment_methods(self):
        """Test different departments and payment methods for comprehensive verification"""
        try:
            test_cases = [
                {
                    "admin_dept": "fw4abteilung2",
                    "expected_name": "2. Wachabteilung",
                    "payment_method": "bank_transfer",
                    "user_notes": "Bank transfer test"
                },
                {
                    "admin_dept": "fw4abteilung3", 
                    "expected_name": "3. Wachabteilung",
                    "payment_method": "adjustment",
                    "user_notes": "Balance adjustment"
                },
                {
                    "admin_dept": "fw4abteilung4",
                    "expected_name": "4. Wachabteilung", 
                    "payment_method": "other",
                    "user_notes": "Other payment method"
                }
            ]
            
            all_passed = True
            
            for i, test_case in enumerate(test_cases):
                self.log(f"\n--- Test Case {i+1}: {test_case['admin_dept']} ---")
                
                payment_data = {
                    "balance_type": "drinks",
                    "payment_type": "drinks_sweets",
                    "amount": 5.0 + i,  # Different amounts
                    "payment_method": test_case["payment_method"],
                    "notes": test_case["user_notes"]
                }
                
                # Make payment
                response = requests.post(
                    f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_id}?admin_department={test_case['admin_dept']}",
                    json=payment_data
                )
                
                if response.status_code == 200:
                    self.success(f"Payment successful for {test_case['admin_dept']}")
                    
                    # Verify notes
                    logs_response = requests.get(f"{API_BASE}/employees/{self.test_employee_id}/payment-logs")
                    if logs_response.status_code == 200:
                        payment_logs = logs_response.json()
                        latest_log = payment_logs[0]
                        notes = latest_log.get("notes", "")
                        
                        expected_pattern = f"Zahlung in {test_case['expected_name']} ({test_case['payment_method']})"
                        
                        if expected_pattern in notes and test_case["user_notes"] in notes:
                            self.success(f"✅ Notes correct for {test_case['admin_dept']}: '{notes}'")
                        else:
                            self.error(f"❌ Notes incorrect for {test_case['admin_dept']}: '{notes}'")
                            all_passed = False
                    else:
                        self.error(f"Failed to get payment logs for {test_case['admin_dept']}")
                        all_passed = False
                else:
                    self.error(f"Payment failed for {test_case['admin_dept']}: {response.status_code}")
                    all_passed = False
                    
            return all_passed
            
        except Exception as e:
            self.error(f"Exception in multiple departments test: {str(e)}")
            return False
            
    def test_edge_cases(self):
        """Test edge cases for payment notes formatting"""
        try:
            # Test with empty user notes
            payment_data = {
                "balance_type": "breakfast",
                "payment_type": "breakfast",
                "amount": 15.0,
                "payment_method": "cash",
                "notes": ""  # Empty notes
            }
            
            response = requests.post(
                f"{API_BASE}/department-admin/subaccount-payment/{self.test_employee_id}?admin_department=fw4abteilung1",
                json=payment_data
            )
            
            if response.status_code == 200:
                # Check notes formatting with empty user notes
                logs_response = requests.get(f"{API_BASE}/employees/{self.test_employee_id}/payment-logs")
                if logs_response.status_code == 200:
                    payment_logs = logs_response.json()
                    latest_log = payment_logs[0]
                    notes = latest_log.get("notes", "")
                    
                    # Should not end with " - " when user notes are empty
                    if notes.endswith(" - "):
                        self.error(f"❌ Notes formatting issue with empty user notes: '{notes}'")
                        return False
                    else:
                        self.success(f"✅ Notes formatting correct with empty user notes: '{notes}'")
                        return True
                else:
                    self.error("Failed to get payment logs for edge case test")
                    return False
            else:
                self.error(f"Payment failed for edge case test: {response.status_code}")
                return False
                
        except Exception as e:
            self.error(f"Exception in edge cases test: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete user-friendly payment notes test"""
        self.log("🎯 STARTING USER-FRIENDLY SUBACCOUNT PAYMENT NOTES TEST")
        self.log("=" * 80)
        self.log("🚨 FEATURE BEING TESTED:")
        self.log("   User wanted: 'Zahlung in 1. Wachabteilung' instead of 'fw4abteilung1'")
        self.log("🔧 IMPLEMENTATION:")
        self.log("   - Backend loads department_name from database")
        self.log("   - payment_log notes format: 'Zahlung in [Department Name] ([Payment Method]) - [User Notes]'")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Create Test Employee", self.create_test_employee),
            ("Test Subaccount Payment with User-Friendly Notes", self.test_subaccount_payment_with_user_friendly_notes),
            ("Test Multiple Departments and Payment Methods", self.test_multiple_departments_and_payment_methods),
            ("Test Edge Cases", self.test_edge_cases),
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
                
        # Final results
        self.log("\n" + "=" * 80)
        if passed_tests == total_tests:
            self.success(f"🎉 USER-FRIENDLY SUBACCOUNT PAYMENT NOTES TEST COMPLETED SUCCESSFULLY!")
            self.success(f"All {total_tests}/{total_tests} tests passed")
            self.log("\n🎯 CRITICAL VERIFICATION RESULTS:")
            self.log("✅ Backend loads department_name from database")
            self.log("✅ Payment log notes use user-friendly department names")
            self.log("✅ Format: 'Zahlung in [Department Name] ([Payment Method]) - [User Notes]'")
            self.log("✅ Technical IDs (fw4abteilung1) are replaced with readable names")
            self.log("✅ Multiple departments and payment methods work correctly")
            self.log("✅ Edge cases handled properly")
            return True
        else:
            self.error(f"❌ USER-FRIENDLY SUBACCOUNT PAYMENT NOTES TEST PARTIALLY FAILED!")
            self.error(f"Only {passed_tests}/{total_tests} tests passed")
            return False

def main():
    """Main test execution"""
    print("🧪 Subaccount Payment Notes Test Suite - User-Friendly Hint Display")
    print("=" * 70)
    
    # Initialize and run test
    test_suite = SubaccountPaymentNotesTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL TESTS PASSED - USER-FRIENDLY PAYMENT NOTES ARE WORKING!")
        print("✅ Payment logs now show readable department names")
        print("✅ Technical IDs are replaced with user-friendly names")
        exit(0)
    else:
        print("\n❌ SOME TESTS FAILED - USER-FRIENDLY PAYMENT NOTES NEED ATTENTION!")
        exit(1)

if __name__ == "__main__":
    main()