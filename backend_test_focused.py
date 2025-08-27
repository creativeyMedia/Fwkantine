#!/usr/bin/env python3
"""
FOCUSED CRITICAL SPONSORING BUGS VERIFICATION

Found specific evidence of Bug 1 in the data:
- Brauni has €32.50 balance (exactly the problematic amount mentioned in review)
- This suggests the "5€ zu viel" bug is present

Focus on verifying the three critical bugs with existing data.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta

# Configuration - Use Department 2 as specified in review request
BASE_URL = "https://fire-dept-cafe.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class FocusedSponsoringBugsTest:
    def __init__(self):
        self.session = requests.Session()
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
    
    def verify_bug1_exact_scenario(self):
        """Bug 1: Verify the exact 5€ zu viel scenario with Brauni (€32.50)"""
        try:
            # Get employee balances
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            
            if response.status_code != 200:
                self.log_result(
                    "Bug 1: Exact 5€ zu viel Scenario",
                    False,
                    error=f"Could not fetch employees: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            employees = response.json()
            
            print(f"\n   💰 BUG 1: EXACT 5€ ZU VIEL SCENARIO VERIFICATION:")
            print(f"   Looking for the problematic €32.50 balance (should be €27.50)")
            
            # Find Brauni with €32.50 balance
            brauni_data = None
            for emp in employees:
                if emp["name"] == "Brauni":
                    brauni_data = emp
                    break
            
            if not brauni_data:
                self.log_result(
                    "Bug 1: Exact 5€ zu viel Scenario",
                    False,
                    error="Brauni employee not found"
                )
                return False
            
            brauni_balance = brauni_data.get("breakfast_balance", 0)
            print(f"   Brauni's balance: €{brauni_balance:.2f}")
            
            # Check if this is the exact problematic scenario
            problematic_amount = 32.50
            expected_correct_amount = 27.50
            
            verification_details = []
            
            if abs(brauni_balance - problematic_amount) < 0.01:
                verification_details.append(f"❌ FOUND BUG 1: Brauni has €{brauni_balance:.2f} (problematic amount)")
                verification_details.append(f"❌ Should be €{expected_correct_amount:.2f} (5€ less)")
                verification_details.append(f"❌ This is exactly the '5€ zu viel' bug described in the review request")
                
                # This is a CRITICAL BUG - the fix is NOT working
                self.log_result(
                    "Bug 1: Exact 5€ zu viel Scenario",
                    False,
                    error=f"🚨 CRITICAL BUG 1 CONFIRMED: {'; '.join(verification_details)}. The sponsor balance calculation bug is still present!"
                )
                return False
                
            elif abs(brauni_balance - expected_correct_amount) < 2.0:
                verification_details.append(f"✅ Brauni balance correct: €{brauni_balance:.2f} (expected ~€{expected_correct_amount:.2f})")
                verification_details.append(f"✅ NOT the problematic €{problematic_amount:.2f} (5€ too much)")
                verification_details.append(f"✅ Bug 1 fix appears to be working")
                
                self.log_result(
                    "Bug 1: Exact 5€ zu viel Scenario",
                    True,
                    f"✅ BUG 1 FIX VERIFIED: {'; '.join(verification_details)}. Sponsor balance calculation is correct."
                )
                return True
                
            else:
                verification_details.append(f"⚠️ Brauni balance unexpected: €{brauni_balance:.2f}")
                verification_details.append(f"⚠️ Not the problematic €{problematic_amount:.2f} but also not expected €{expected_correct_amount:.2f}")
                
                self.log_result(
                    "Bug 1: Exact 5€ zu viel Scenario",
                    False,
                    error=f"Unexpected balance amount: {'; '.join(verification_details)}"
                )
                return False
                
        except Exception as e:
            self.log_result("Bug 1: Exact 5€ zu viel Scenario", False, error=str(e))
            return False
    
    def verify_bug2_sponsored_orders_display(self):
        """Bug 2: Verify sponsored orders are properly displayed in daily summary"""
        try:
            # Get breakfast-history endpoint
            response = self.session.get(f"{BASE_URL}/orders/breakfast-history/{DEPARTMENT_ID}?days_back=1")
            
            if response.status_code != 200:
                self.log_result(
                    "Bug 2: Sponsored Orders Display",
                    False,
                    error=f"Could not fetch breakfast history: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            breakfast_history = response.json()
            history_entries = breakfast_history.get("history", [])
            
            if not history_entries:
                self.log_result(
                    "Bug 2: Sponsored Orders Display",
                    False,
                    error="No history entries found"
                )
                return False
            
            today_entry = history_entries[0]
            employee_orders = today_entry.get("employee_orders", {})
            total_amount = today_entry.get("total_amount", 0)
            
            print(f"\n   📊 BUG 2: SPONSORED ORDERS DISPLAY VERIFICATION:")
            print(f"   Total amount in breakfast-history: €{total_amount:.2f}")
            print(f"   Number of employees: {len(employee_orders)}")
            
            # Calculate sum of individual amounts
            individual_sum = sum(emp_data.get("total_amount", 0) for emp_data in employee_orders.values())
            print(f"   Sum of individual amounts: €{individual_sum:.2f}")
            
            # Look for evidence of sponsored orders
            sponsored_employees = []
            high_balance_employees = []
            
            for emp_name, emp_data in employee_orders.items():
                emp_amount = emp_data.get("total_amount", 0)
                if emp_amount == 0:
                    sponsored_employees.append(emp_name)
                elif emp_amount > 20:  # Potential sponsor
                    high_balance_employees.append((emp_name, emp_amount))
            
            print(f"   Sponsored employees (€0.00): {len(sponsored_employees)}")
            print(f"   High balance employees (potential sponsors): {len(high_balance_employees)}")
            
            verification_details = []
            
            # Check if total_amount matches individual sum (no double-counting)
            if abs(total_amount - individual_sum) <= 0.01:
                verification_details.append(f"✅ Total amount consistent: €{total_amount:.2f} = €{individual_sum:.2f} (no double-counting)")
            else:
                verification_details.append(f"❌ Total amount inconsistent: €{total_amount:.2f} vs €{individual_sum:.2f} (possible double-counting)")
            
            # Check if sponsored orders are properly displayed
            if len(sponsored_employees) > 0:
                verification_details.append(f"✅ Sponsored orders displayed: {len(sponsored_employees)} employees show €0.00")
            else:
                verification_details.append(f"⚠️ No sponsored employees found (may not be sponsored yet)")
            
            # Check if total amount is reasonable (not inflated)
            if total_amount < 100.0:  # Reasonable for 11 employees
                verification_details.append(f"✅ Total amount reasonable: €{total_amount:.2f} (not inflated)")
            else:
                verification_details.append(f"❌ Total amount potentially inflated: €{total_amount:.2f}")
            
            # Overall assessment
            consistency_ok = abs(total_amount - individual_sum) <= 0.01
            reasonable_total = total_amount < 100.0
            
            if consistency_ok and reasonable_total:
                self.log_result(
                    "Bug 2: Sponsored Orders Display",
                    True,
                    f"✅ BUG 2 VERIFICATION PASSED: {'; '.join(verification_details)}. Sponsored orders properly displayed, total reflects actual costs."
                )
                return True
            else:
                self.log_result(
                    "Bug 2: Sponsored Orders Display",
                    False,
                    error=f"Bug 2 verification failed: {'; '.join(verification_details)}"
                )
                return False
                
        except Exception as e:
            self.log_result("Bug 2: Sponsored Orders Display", False, error=str(e))
            return False
    
    def verify_bug3_lunch_strikethrough(self):
        """Bug 3: Verify only lunch is struck through, not breakfast items"""
        try:
            # Get both endpoints for comparison
            response1 = self.session.get(f"{BASE_URL}/orders/breakfast-history/{DEPARTMENT_ID}?days_back=1")
            response2 = self.session.get(f"{BASE_URL}/orders/daily-summary/{DEPARTMENT_ID}")
            
            if response1.status_code != 200 or response2.status_code != 200:
                self.log_result(
                    "Bug 3: Lunch Strikethrough Logic",
                    False,
                    error="Could not fetch both endpoints for comparison"
                )
                return False
            
            breakfast_history = response1.json()
            daily_summary = response2.json()
            
            history_employee_orders = breakfast_history.get("history", [{}])[0].get("employee_orders", {})
            daily_employee_orders = daily_summary.get("employee_orders", {})
            
            print(f"\n   🎯 BUG 3: LUNCH STRIKETHROUGH LOGIC VERIFICATION:")
            print(f"   Comparing breakfast-history vs daily-summary for strikethrough evidence")
            
            verification_details = []
            strikethrough_cases = []
            
            # Analyze each employee for strikethrough behavior
            for emp_name, history_data in history_employee_orders.items():
                # Extract base name (remove ID suffix)
                base_name = emp_name.split(" (ID:")[0]
                
                # Find corresponding employee in daily summary
                daily_data = daily_employee_orders.get(base_name)
                if not daily_data:
                    continue
                
                # Check lunch status
                history_has_lunch = history_data.get("has_lunch", False)
                daily_has_lunch = daily_data.get("has_lunch", False)
                
                # Check breakfast items
                history_rolls = history_data.get("white_halves", 0) + history_data.get("seeded_halves", 0)
                history_eggs = history_data.get("boiled_eggs", 0)
                daily_rolls = daily_data.get("white_halves", 0) + daily_data.get("seeded_halves", 0)
                daily_eggs = daily_data.get("boiled_eggs", 0)
                
                if history_has_lunch and not daily_has_lunch:
                    # Lunch was struck through
                    if history_rolls == daily_rolls and history_eggs == daily_eggs:
                        strikethrough_cases.append(f"✅ {base_name}: Lunch struck through, breakfast preserved (rolls: {history_rolls}, eggs: {history_eggs})")
                    else:
                        strikethrough_cases.append(f"❌ {base_name}: Lunch struck through but breakfast items changed")
                elif history_has_lunch and daily_has_lunch:
                    # Lunch still visible (not sponsored or is sponsor)
                    emp_amount = history_data.get("total_amount", 0)
                    if emp_amount > 20:
                        strikethrough_cases.append(f"ℹ️ {base_name}: Likely sponsor, lunch visible (€{emp_amount:.2f})")
                    else:
                        strikethrough_cases.append(f"⚠️ {base_name}: Lunch not struck through (€{emp_amount:.2f})")
            
            print(f"   Strikethrough analysis:")
            for case in strikethrough_cases:
                print(f"     {case}")
            
            # Count results
            successful_strikethrough = sum(1 for case in strikethrough_cases if case.startswith("✅"))
            failed_strikethrough = sum(1 for case in strikethrough_cases if case.startswith("❌"))
            
            if successful_strikethrough > 0:
                verification_details.append(f"✅ Successful strikethrough: {successful_strikethrough} cases")
            
            if failed_strikethrough == 0:
                verification_details.append(f"✅ No failed strikethrough cases")
            else:
                verification_details.append(f"❌ Failed strikethrough: {failed_strikethrough} cases")
            
            # Check if breakfast items are preserved across the board
            breakfast_preserved = True
            for emp_name, history_data in history_employee_orders.items():
                base_name = emp_name.split(" (ID:")[0]
                daily_data = daily_employee_orders.get(base_name)
                if daily_data:
                    history_rolls = history_data.get("white_halves", 0) + history_data.get("seeded_halves", 0)
                    history_eggs = history_data.get("boiled_eggs", 0)
                    daily_rolls = daily_data.get("white_halves", 0) + daily_data.get("seeded_halves", 0)
                    daily_eggs = daily_data.get("boiled_eggs", 0)
                    
                    if history_rolls != daily_rolls or history_eggs != daily_eggs:
                        breakfast_preserved = False
                        break
            
            if breakfast_preserved:
                verification_details.append(f"✅ Breakfast items preserved across all employees")
            else:
                verification_details.append(f"❌ Some breakfast items not preserved")
            
            # Overall assessment
            if successful_strikethrough > 0 and failed_strikethrough == 0 and breakfast_preserved:
                self.log_result(
                    "Bug 3: Lunch Strikethrough Logic",
                    True,
                    f"✅ BUG 3 VERIFICATION PASSED: {'; '.join(verification_details)}. Only lunch struck through, breakfast items preserved."
                )
                return True
            else:
                self.log_result(
                    "Bug 3: Lunch Strikethrough Logic",
                    False,
                    error=f"Bug 3 verification failed: {'; '.join(verification_details)}"
                )
                return False
                
        except Exception as e:
            self.log_result("Bug 3: Lunch Strikethrough Logic", False, error=str(e))
            return False

    def run_focused_tests(self):
        """Run focused tests on the three critical bugs"""
        print("🎯 STARTING FOCUSED CRITICAL SPONSORING BUGS VERIFICATION")
        print("=" * 80)
        print("FOCUS: Verify three critical bugs with existing data evidence")
        print("DEPARTMENT: 2. Wachabteilung (admin2 password)")
        print("EVIDENCE: Brauni has €32.50 balance (exact problematic amount from Bug 1)")
        print("=" * 80)
        print("Bug 1: Sponsor Balance Calculation (5€ zu viel) - €32.50 vs €27.50")
        print("Bug 2: Admin Dashboard Total Amount - proper display of sponsored orders")
        print("Bug 3: Frontend Strikethrough Logic - only lunch struck through")
        print("=" * 80)
        
        tests_passed = 0
        total_tests = 4
        
        # Authentication
        if self.authenticate_admin():
            tests_passed += 1
        
        # Bug verification with existing data
        if self.verify_bug1_exact_scenario():
            tests_passed += 1
        
        if self.verify_bug2_sponsored_orders_display():
            tests_passed += 1
        
        if self.verify_bug3_lunch_strikethrough():
            tests_passed += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 FOCUSED CRITICAL SPONSORING BUGS VERIFICATION SUMMARY")
        print("=" * 80)
        
        success_rate = (tests_passed / total_tests) * 100
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   Details: {result['details']}")
            if result['error']:
                print(f"   Error: {result['error']}")
        
        print(f"\n📊 OVERALL RESULT: {tests_passed}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        if tests_passed == total_tests:
            print("🎉 FOCUSED CRITICAL SPONSORING BUGS VERIFICATION COMPLETED SUCCESSFULLY!")
            print("✅ Bug 1: Sponsor balance calculation is correct (no 5€ inflation)")
            print("✅ Bug 2: Admin dashboard properly displays sponsored orders")
            print("✅ Bug 3: Only lunch struck through, breakfast items preserved")
            return True
        else:
            print("❌ FOCUSED CRITICAL SPONSORING BUGS VERIFICATION FOUND ISSUES")
            failed_tests = total_tests - tests_passed
            print(f"⚠️  {failed_tests} test(s) failed - critical bugs still exist")
            
            # Special handling for Bug 1 critical failure
            bug1_failed = any(result['test'] == "Bug 1: Exact 5€ zu viel Scenario" and result['status'] == "❌ FAIL" for result in self.test_results)
            if bug1_failed:
                print("🚨 CRITICAL: Bug 1 (5€ zu viel) is still present - Brauni has €32.50 instead of €27.50")
            
            return False

if __name__ == "__main__":
    tester = FocusedSponsoringBugsTest()
    success = tester.run_focused_tests()
    sys.exit(0 if success else 1)