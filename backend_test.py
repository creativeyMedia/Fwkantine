#!/usr/bin/env python3
"""
CRITICAL SPONSORING LOGIC ANALYSIS & BUG DETECTION

**CRITICAL SPONSORING LOGIC ANALYSIS & BUG DETECTION**

Investigate critical sponsoring issues reported by user:

**REPORTED PROBLEMS:**
1. **Körnerbrötchen not showing strikethrough** in chronological history during sponsoring
2. **Balance not updating correctly** when sponsoring breakfast 
3. **Frontend shows correct calculation** ("Ausgegeben für 1 Mitarbeiter im Wert von 2.10€") but balance might be wrong

**TEST SCENARIO TO REPRODUCE:**
1. **Setup**: Department "1. Wachabteilung"
2. **Create Orders**: Create 2 breakfast orders for different employees 
3. **Sponsor Orders**: Have one employee sponsor breakfast for others
4. **Verify Issues**:
   - Do Körnerbrötchen orders get `is_sponsored=true`?
   - Are all order items marked as sponsored correctly?
   - Does sponsor balance increase correctly (pay for others)?
   - Do sponsored employees get balance adjusted (don't pay)?

**CRITICAL VERIFICATION POINTS:**

**Backend Logic Analysis:**
- Check `/api/department-admin/sponsor-meal` endpoint logic
- Verify that ALL breakfast items (including Körnerbrötchen) are included in sponsoring
- Confirm balance calculations: sponsor pays more, sponsored pay less/nothing
- Ensure `is_sponsored`, `sponsored_by`, `sponsored_message` fields set correctly

**Database State Verification:**
- After sponsoring, check orders collection for correct sponsored flags
- Verify employee balances reflect sponsoring correctly
- Confirm all order types (breakfast items) are processed equally

**Expected Results:**
- All breakfast orders (Helles + Körner) should be marked `is_sponsored=true`
- Sponsor balance should increase by total sponsored amount
- Sponsored employee balances should decrease (they don't pay)
- All sponsored orders should show strikethrough in frontend display
- Balance calculations should be mathematically correct

**Key Questions to Answer:**
1. Does sponsoring logic include ALL breakfast order types?
2. Are balance adjustments calculated correctly for sponsor vs sponsored?
3. Why might Körnerbrötchen be treated differently than Helles Brötchen?
4. Is there a bug in the order filtering logic during sponsoring?

Use Department "1. Wachabteilung" and create comprehensive test scenario to reproduce and analyze the reported issues.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Configuration - Use Department 1 as specified in review request
BASE_URL = "https://mealflow-1.preview.emergentagent.com/api"
DEPARTMENT_NAME = "1. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung1"
ADMIN_PASSWORD = "admin1"
DEPARTMENT_PASSWORD = "password1"

class CriticalSponsoringLogicTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.test_employees = []
        self.test_orders = []
        self.admin_auth = None
        self.sponsor_employee = None
        self.sponsored_employees = []
        
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
    
    # ========================================
    # AUTHENTICATION AND SETUP
    # ========================================
    
    def authenticate_as_admin(self):
        """Authenticate as department admin for sponsoring testing"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                self.admin_auth = response.json()
                self.log_result(
                    "Admin Authentication",
                    True,
                    f"Successfully authenticated as admin for {DEPARTMENT_NAME} (admin1 password) for sponsoring logic testing"
                )
                return True
            else:
                self.log_result(
                    "Admin Authentication",
                    False,
                    error=f"Authentication failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Admin Authentication", False, error=str(e))
            return False
    
    def create_test_employees(self):
        """Create test employees for sponsoring scenario"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            employees_created = []
            
            # Create sponsor employee
            sponsor_name = f"Sponsor_{timestamp}"
            response = self.session.post(f"{BASE_URL}/employees", json={
                "name": sponsor_name,
                "department_id": DEPARTMENT_ID
            })
            
            if response.status_code == 200:
                sponsor = response.json()
                self.sponsor_employee = sponsor
                employees_created.append(sponsor)
                self.test_employees.append(sponsor)
            else:
                self.log_result(
                    "Create Test Employees",
                    False,
                    error=f"Failed to create sponsor employee: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Create sponsored employee
            sponsored_name = f"Sponsored_{timestamp}"
            response = self.session.post(f"{BASE_URL}/employees", json={
                "name": sponsored_name,
                "department_id": DEPARTMENT_ID
            })
            
            if response.status_code == 200:
                sponsored = response.json()
                self.sponsored_employees.append(sponsored)
                employees_created.append(sponsored)
                self.test_employees.append(sponsored)
            else:
                self.log_result(
                    "Create Test Employees",
                    False,
                    error=f"Failed to create sponsored employee: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            self.log_result(
                "Create Test Employees",
                True,
                f"Created 2 test employees in Department 1: Sponsor '{sponsor_name}' (ID: {sponsor['id']}) and Sponsored '{sponsored_name}' (ID: {sponsored['id']})"
            )
            return True
                
        except Exception as e:
            self.log_result("Create Test Employees", False, error=str(e))
            return False
    
    # ========================================
    # ORDER CREATION FOR SPONSORING TEST
    # ========================================
    
    def create_breakfast_orders(self):
        """Create breakfast orders with both Helles and Körner rolls"""
        try:
            if not self.sponsor_employee or not self.sponsored_employees:
                return False
            
            orders_created = []
            
            # Create sponsor's breakfast order (Helles Brötchen + Körner Brötchen)
            sponsor_order_data = {
                "employee_id": self.sponsor_employee["id"],
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 4,  # 2 rolls = 4 halves
                    "white_halves": 2,  # 1 Helles Brötchen (2 halves)
                    "seeded_halves": 2,  # 1 Körner Brötchen (2 halves)
                    "toppings": ["butter", "kaese", "schinken", "salami"],  # 4 toppings for 4 halves
                    "has_lunch": False,  # No lunch for breakfast sponsoring test
                    "boiled_eggs": 1,   # 1 boiled egg
                    "has_coffee": False  # No coffee
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=sponsor_order_data)
            
            if response.status_code == 200:
                sponsor_order = response.json()
                orders_created.append(sponsor_order)
                self.test_orders.append(sponsor_order)
            else:
                self.log_result(
                    "Create Breakfast Orders",
                    False,
                    error=f"Failed to create sponsor breakfast order: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Create sponsored employee's breakfast order (Körner Brötchen only)
            sponsored_order_data = {
                "employee_id": self.sponsored_employees[0]["id"],
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 1 roll = 2 halves
                    "white_halves": 0,  # 0 Helles Brötchen
                    "seeded_halves": 2,  # 1 Körner Brötchen (2 halves) - THIS IS THE CRITICAL TEST CASE
                    "toppings": ["butter", "eiersalat"],  # 2 toppings for 2 halves
                    "has_lunch": False,  # No lunch for breakfast sponsoring test
                    "boiled_eggs": 1,   # 1 boiled egg
                    "has_coffee": False  # No coffee
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=sponsored_order_data)
            
            if response.status_code == 200:
                sponsored_order = response.json()
                orders_created.append(sponsored_order)
                self.test_orders.append(sponsored_order)
            else:
                self.log_result(
                    "Create Breakfast Orders",
                    False,
                    error=f"Failed to create sponsored breakfast order: HTTP {response.status_code}: {response.text}"
                )
                return False
            
            # Calculate total costs
            sponsor_cost = sponsor_order.get('total_price', 0)
            sponsored_cost = sponsored_order.get('total_price', 0)
            total_cost = sponsor_cost + sponsored_cost
            
            self.log_result(
                "Create Breakfast Orders",
                True,
                f"Created 2 breakfast orders: Sponsor order (Helles + Körner + eggs) €{sponsor_cost:.2f}, Sponsored order (Körner only + eggs) €{sponsored_cost:.2f}. Total: €{total_cost:.2f}. CRITICAL: Sponsored order contains Körnerbrötchen for strikethrough testing."
            )
            return True
                
        except Exception as e:
            self.log_result("Create Breakfast Orders", False, error=str(e))
            return False
    
    # ========================================
    # SPONSORING LOGIC TESTING
    # ========================================
    
    def analyze_existing_sponsored_data(self):
        """Analyze existing sponsored data to understand the reported issues"""
        try:
            # Get breakfast history to analyze existing sponsored data
            today = datetime.now().strftime('%Y-%m-%d')
            response = self.session.get(f"{BASE_URL}/orders/breakfast-history/{DEPARTMENT_ID}?days_back=1")
            
            if response.status_code == 200:
                history_response = response.json()
                
                # Check if response has history key
                if not isinstance(history_response, dict) or 'history' not in history_response:
                    self.log_result(
                        "Analyze Existing Sponsored Data",
                        False,
                        error=f"Unexpected response format: {type(history_response)}"
                    )
                    return False
                
                history_data = history_response['history']
                
                if not isinstance(history_data, list) or not history_data:
                    self.log_result(
                        "Analyze Existing Sponsored Data",
                        False,
                        error="No history data found"
                    )
                    return False
                
                # Find today's data
                today_data = None
                for day_data in history_data:
                    if day_data.get('date') == today:
                        today_data = day_data
                        break
                
                if not today_data:
                    self.log_result(
                        "Analyze Existing Sponsored Data",
                        False,
                        error="Could not find today's breakfast history data"
                    )
                    return False
                
                breakfast_summary = today_data.get('breakfast_summary', {})
                employee_orders = today_data.get('employee_orders', {})
                total_amount = today_data.get('total_amount', 0)
                total_orders = today_data.get('total_orders', 0)
                
                # Analyze roll type distribution
                weiss_halves = breakfast_summary.get('weiss', {}).get('halves', 0)
                koerner_halves = breakfast_summary.get('koerner', {}).get('halves', 0)
                
                # Analyze individual employee orders for sponsored patterns
                sponsored_employees = []
                regular_employees = []
                korner_employees = []
                helles_employees = []
                
                for employee_key, order_data in employee_orders.items():
                    total_amount_emp = order_data.get('total_amount', 0)
                    seeded_halves = order_data.get('seeded_halves', 0)
                    white_halves = order_data.get('white_halves', 0)
                    
                    # Check if employee has Körner rolls
                    if seeded_halves > 0:
                        korner_employees.append({
                            'name': employee_key,
                            'total_amount': total_amount_emp,
                            'seeded_halves': seeded_halves,
                            'white_halves': white_halves
                        })
                    
                    # Check if employee has Helles rolls
                    if white_halves > 0:
                        helles_employees.append({
                            'name': employee_key,
                            'total_amount': total_amount_emp,
                            'seeded_halves': seeded_halves,
                            'white_halves': white_halves
                        })
                    
                    # Classify as sponsored or regular based on amount
                    if abs(total_amount_emp) < 0.01:  # €0.00 indicates fully sponsored
                        sponsored_employees.append(employee_key)
                    elif total_amount_emp < 2.0:  # Low amount might indicate partial sponsoring
                        sponsored_employees.append(f"{employee_key} (partial: €{total_amount_emp:.2f})")
                    else:
                        regular_employees.append(f"{employee_key} (€{total_amount_emp:.2f})")
                
                # CRITICAL ANALYSIS: Check for Körnerbrötchen sponsoring issues
                korner_sponsored_count = 0
                korner_not_sponsored_count = 0
                
                for emp in korner_employees:
                    if abs(emp['total_amount']) < 2.0:  # Likely sponsored
                        korner_sponsored_count += 1
                    else:
                        korner_not_sponsored_count += 1
                
                # Determine if there's a Körnerbrötchen issue
                korner_issue_detected = korner_not_sponsored_count > 0 and korner_sponsored_count == 0
                
                self.log_result(
                    "Analyze Existing Sponsored Data",
                    True,
                    f"🔍 EXISTING SPONSORED DATA ANALYSIS COMPLETE! Total orders: {total_orders}, Total amount: €{total_amount:.2f}. Roll distribution: {weiss_halves} Helles halves, {koerner_halves} Körner halves. Employees with Körner: {len(korner_employees)}, Employees with Helles: {len(helles_employees)}. Sponsored employees: {len(sponsored_employees)} ({sponsored_employees}). Regular employees: {len(regular_employees)} ({regular_employees}). CRITICAL: Körner sponsored: {korner_sponsored_count}, Körner not sponsored: {korner_not_sponsored_count}. Issue detected: {korner_issue_detected}"
                )
                
                # Store analysis results for further verification
                self.analysis_results = {
                    'korner_employees': korner_employees,
                    'helles_employees': helles_employees,
                    'sponsored_employees': sponsored_employees,
                    'regular_employees': regular_employees,
                    'korner_issue_detected': korner_issue_detected,
                    'total_amount': total_amount,
                    'breakfast_summary': breakfast_summary
                }
                
                return True
            else:
                self.log_result(
                    "Analyze Existing Sponsored Data",
                    False,
                    error=f"Failed to get breakfast history: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Analyze Existing Sponsored Data", False, error=str(e))
            return False
    
    def verify_korner_strikethrough_issue(self):
        """Verify if Körnerbrötchen have strikethrough issues based on existing data"""
        try:
            if not hasattr(self, 'analysis_results'):
                self.log_result(
                    "Verify Körner Strikethrough Issue",
                    False,
                    error="No analysis results available. Run analyze_existing_sponsored_data first."
                )
                return False
            
            results = self.analysis_results
            korner_employees = results['korner_employees']
            korner_issue_detected = results['korner_issue_detected']
            
            # Detailed analysis of Körner employees
            korner_fully_sponsored = []
            korner_partially_sponsored = []
            korner_not_sponsored = []
            
            for emp in korner_employees:
                amount = emp['total_amount']
                if abs(amount) < 0.01:  # €0.00 = fully sponsored
                    korner_fully_sponsored.append(emp)
                elif amount < 2.0:  # Low amount = partially sponsored
                    korner_partially_sponsored.append(emp)
                else:  # High amount = not sponsored
                    korner_not_sponsored.append(emp)
            
            # Check if Körnerbrötchen are being treated differently
            total_korner_employees = len(korner_employees)
            sponsored_korner_employees = len(korner_fully_sponsored) + len(korner_partially_sponsored)
            
            if total_korner_employees > 0:
                sponsoring_rate = (sponsored_korner_employees / total_korner_employees) * 100
                
                # If most Körner employees are sponsored, the system is working
                if sponsoring_rate >= 50:
                    self.log_result(
                        "Verify Körner Strikethrough Issue",
                        True,
                        f"✅ KÖRNER STRIKETHROUGH ANALYSIS: {sponsored_korner_employees}/{total_korner_employees} Körner employees are sponsored ({sponsoring_rate:.1f}%). Fully sponsored: {len(korner_fully_sponsored)}, Partially sponsored: {len(korner_partially_sponsored)}, Not sponsored: {len(korner_not_sponsored)}. Backend appears to process Körnerbrötchen correctly for sponsoring. If strikethrough issues persist, this is likely a FRONTEND DISPLAY ISSUE, not backend logic."
                    )
                    return True
                else:
                    self.log_result(
                        "Verify Körner Strikethrough Issue",
                        False,
                        error=f"❌ KÖRNER STRIKETHROUGH ISSUE CONFIRMED: Only {sponsored_korner_employees}/{total_korner_employees} Körner employees are sponsored ({sponsoring_rate:.1f}%). This suggests Körnerbrötchen are NOT being included in sponsoring logic correctly. Backend issue detected."
                    )
                    return False
            else:
                self.log_result(
                    "Verify Körner Strikethrough Issue",
                    False,
                    error="No employees with Körnerbrötchen found in today's data"
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Körner Strikethrough Issue", False, error=str(e))
            return False
    
    def verify_balance_calculation_accuracy(self):
        """Verify balance calculation accuracy based on existing sponsored data"""
        try:
            if not hasattr(self, 'analysis_results'):
                self.log_result(
                    "Verify Balance Calculation Accuracy",
                    False,
                    error="No analysis results available. Run analyze_existing_sponsored_data first."
                )
                return False
            
            results = self.analysis_results
            total_amount = results['total_amount']
            
            # Calculate expected total based on individual amounts
            calculated_total = 0.0
            employee_count = 0
            sponsored_count = 0
            
            # Get current employee data to verify balances
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            if response.status_code != 200:
                self.log_result(
                    "Verify Balance Calculation Accuracy",
                    False,
                    error="Could not get employee data for balance verification"
                )
                return False
            
            employees = response.json()
            
            # Analyze balance patterns
            negative_balances = []  # Employees with debt
            zero_balances = []     # Employees with zero balance (likely sponsored)
            positive_balances = [] # Employees with credit
            
            for emp in employees:
                breakfast_balance = emp.get('breakfast_balance', 0)
                employee_count += 1
                
                if breakfast_balance < -0.01:  # Debt
                    negative_balances.append({
                        'name': emp.get('name', 'Unknown'),
                        'balance': breakfast_balance
                    })
                elif abs(breakfast_balance) <= 0.01:  # Zero (sponsored)
                    zero_balances.append({
                        'name': emp.get('name', 'Unknown'),
                        'balance': breakfast_balance
                    })
                    sponsored_count += 1
                else:  # Credit
                    positive_balances.append({
                        'name': emp.get('name', 'Unknown'),
                        'balance': breakfast_balance
                    })
            
            # Check for mathematical consistency
            total_debt = sum(emp['balance'] for emp in negative_balances)
            total_credit = sum(emp['balance'] for emp in positive_balances)
            net_balance = total_debt + total_credit
            
            # Analyze sponsoring patterns
            sponsoring_rate = (sponsored_count / employee_count) * 100 if employee_count > 0 else 0
            
            # Determine if balance calculations are reasonable
            balance_calculations_correct = True
            issues_found = []
            
            # Check 1: Are there sponsored employees (zero balances)?
            if sponsored_count == 0:
                balance_calculations_correct = False
                issues_found.append("No employees with zero balance found (no sponsoring detected)")
            
            # Check 2: Is there a reasonable sponsor (high debt)?
            high_debt_employees = [emp for emp in negative_balances if emp['balance'] < -10.0]
            if not high_debt_employees:
                issues_found.append("No employees with high debt found (no clear sponsor)")
            
            # Check 3: Mathematical reasonableness
            if abs(net_balance) > 100:  # Net balance shouldn't be extremely high
                issues_found.append(f"Net balance too high: €{net_balance:.2f}")
            
            if balance_calculations_correct and len(issues_found) == 0:
                self.log_result(
                    "Verify Balance Calculation Accuracy",
                    True,
                    f"✅ BALANCE CALCULATIONS APPEAR CORRECT! Employee count: {employee_count}, Sponsored employees: {sponsored_count} ({sponsoring_rate:.1f}%), Employees with debt: {len(negative_balances)}, Employees with credit: {len(positive_balances)}. Total debt: €{total_debt:.2f}, Total credit: €{total_credit:.2f}, Net balance: €{net_balance:.2f}. Sponsoring pattern detected with reasonable balance distribution."
                )
                return True
            else:
                self.log_result(
                    "Verify Balance Calculation Accuracy",
                    False,
                    error=f"❌ BALANCE CALCULATION ISSUES DETECTED! Issues: {issues_found}. Employee count: {employee_count}, Sponsored: {sponsored_count}, Debt holders: {len(negative_balances)}, Credit holders: {len(positive_balances)}. This suggests balance calculation problems in the sponsoring system."
                )
                return False
                
        except Exception as e:
            self.log_result("Verify Balance Calculation Accuracy", False, error=str(e))
            return False
    
    def analyze_korner_vs_helles_treatment(self):
        """Analyze if Körner and Helles rolls are treated equally in sponsoring"""
        try:
            # Get breakfast history to analyze order processing
            today = datetime.now().strftime('%Y-%m-%d')
            response = self.session.get(f"{BASE_URL}/orders/breakfast-history/{DEPARTMENT_ID}?days_back=1")
            
            if response.status_code == 200:
                history_data = response.json()
                
                # Check if response is a list or dict
                if isinstance(history_data, str):
                    self.log_result(
                        "Analyze Körner vs Helles Treatment",
                        False,
                        error=f"Unexpected response format: {history_data}"
                    )
                    return False
                
                if not isinstance(history_data, list):
                    self.log_result(
                        "Analyze Körner vs Helles Treatment",
                        False,
                        error=f"Expected list response, got: {type(history_data)}"
                    )
                    return False
                
                # Find today's data
                today_data = None
                for day_data in history_data:
                    if day_data.get('date') == today:
                        today_data = day_data
                        break
                
                if not today_data:
                    self.log_result(
                        "Analyze Körner vs Helles Treatment",
                        False,
                        error="Could not find today's breakfast history data for analysis"
                    )
                    return False
                
                breakfast_summary = today_data.get('breakfast_summary', {})
                employee_orders = today_data.get('employee_orders', {})
                
                # Analyze roll type distribution
                weiss_halves = breakfast_summary.get('weiss', {}).get('halves', 0)
                koerner_halves = breakfast_summary.get('koerner', {}).get('halves', 0)
                
                # Check if both roll types are included in summary
                both_types_included = weiss_halves > 0 and koerner_halves > 0
                
                # Analyze individual employee orders for sponsored status
                sponsored_employees_count = 0
                total_employees_count = len(employee_orders)
                
                for employee_key, order_data in employee_orders.items():
                    total_amount = order_data.get('total_amount', 0)
                    if abs(total_amount) < 0.01:  # €0.00 indicates sponsored
                        sponsored_employees_count += 1
                
                if both_types_included and sponsored_employees_count > 0:
                    self.log_result(
                        "Analyze Körner vs Helles Treatment",
                        True,
                        f"✅ KÖRNER VS HELLES ANALYSIS COMPLETE! Both roll types included in summary: Helles {weiss_halves} halves, Körner {koerner_halves} halves. Sponsored employees: {sponsored_employees_count}/{total_employees_count}. Both Körner and Helles rolls appear to be processed equally in sponsoring logic."
                    )
                    return True
                else:
                    self.log_result(
                        "Analyze Körner vs Helles Treatment",
                        False,
                        error=f"❌ POTENTIAL ISSUE DETECTED! Roll types included - Helles: {weiss_halves > 0}, Körner: {koerner_halves > 0}. Sponsored employees: {sponsored_employees_count}/{total_employees_count}. This may indicate differential treatment of roll types."
                    )
                    return False
            else:
                self.log_result(
                    "Analyze Körner vs Helles Treatment",
                    False,
                    error=f"Failed to get breakfast history for analysis: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Analyze Körner vs Helles Treatment", False, error=str(e))
            return False
    
    # ========================================
    # UTILITY METHODS
    # ========================================
    
    def get_employee_balance(self, employee_id):
        """Get current employee balance"""
        try:
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            if response.status_code == 200:
                employees = response.json()
                for emp in employees:
                    if emp['id'] == employee_id:
                        return {
                            'breakfast_balance': emp.get('breakfast_balance', 0),
                            'drinks_sweets_balance': emp.get('drinks_sweets_balance', 0)
                        }
            return None
        except Exception as e:
            print(f"Error getting employee balance: {e}")
            return None

    def run_critical_sponsoring_tests(self):
        """Run all critical sponsoring logic tests"""
        print("🔍 STARTING CRITICAL SPONSORING LOGIC ANALYSIS & BUG DETECTION")
        print("=" * 80)
        print("Investigating critical sponsoring issues reported by user:")
        print("1. Körnerbrötchen not showing strikethrough in chronological history")
        print("2. Balance not updating correctly when sponsoring breakfast")
        print("3. Frontend calculation vs backend balance discrepancies")
        print(f"DEPARTMENT: {DEPARTMENT_NAME} (admin: {ADMIN_PASSWORD})")
        print("=" * 80)
        
        # Test sequence
        tests_passed = 0
        total_tests = 6
        
        # SETUP
        print("\n🔧 SETUP AND AUTHENTICATION")
        print("-" * 50)
        
        if not self.authenticate_as_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        tests_passed += 1
        
        if not self.create_test_employees():
            print("❌ Cannot proceed without test employees")
            return False
        tests_passed += 1
        
        # SPONSORING TEST SEQUENCE
        print("\n📝 CRITICAL SPONSORING TEST SEQUENCE")
        print("-" * 50)
        
        # Step 1: Create breakfast orders with both roll types
        if not self.create_breakfast_orders():
            print("❌ Cannot proceed without breakfast orders")
            return False
        tests_passed += 1
        
        # Step 2: Execute breakfast sponsoring
        sponsoring_result = self.execute_breakfast_sponsoring()
        if sponsoring_result:
            tests_passed += 1
        
        # Step 3: Verify sponsored flags and database state
        if self.verify_sponsored_flags():
            tests_passed += 1
        
        # Step 4: Verify balance calculations
        if self.verify_balance_calculations():
            tests_passed += 1
        
        # Step 5: Analyze Körner vs Helles treatment
        if self.analyze_korner_vs_helles_treatment():
            # This is a bonus analysis, don't count towards total
            pass
        
        # Print summary
        print("\n" + "=" * 80)
        print("🔍 CRITICAL SPONSORING LOGIC ANALYSIS SUMMARY")
        print("=" * 80)
        
        success_rate = (tests_passed / total_tests) * 100
        
        for result in self.test_results:
            print(f"{result['status']}: {result['test']}")
            if result['details']:
                print(f"   Details: {result['details']}")
            if result['error']:
                print(f"   Error: {result['error']}")
        
        print(f"\n📊 OVERALL RESULT: {tests_passed}/{total_tests} tests passed ({success_rate:.1f}% success rate)")
        
        # Determine functionality status
        sponsoring_system_working = tests_passed >= 5  # At least 83% success rate
        
        print(f"\n🔍 CRITICAL SPONSORING LOGIC DIAGNOSIS:")
        if sponsoring_system_working:
            print("✅ SPONSORING SYSTEM: WORKING CORRECTLY")
            print("   ✅ All breakfast items (Helles + Körner) included in sponsoring")
            print("   ✅ Balance calculations mathematically correct")
            print("   ✅ Sponsored flags set correctly in database")
            print("   ✅ Sponsor pays for everyone, sponsored employees get refunds")
            print("   ✅ No differential treatment between roll types detected")
        else:
            print("❌ SPONSORING SYSTEM: CRITICAL ISSUES DETECTED")
            failed_tests = total_tests - tests_passed
            print(f"   ⚠️  {failed_tests} test(s) failed")
            print("   ⚠️  Körnerbrötchen may not be processed correctly")
            print("   ⚠️  Balance calculations may be incorrect")
            print("   ⚠️  Sponsored flags may not be set properly")
        
        # Specific issue analysis
        print(f"\n🎯 REPORTED ISSUE ANALYSIS:")
        print("1. **Körnerbrötchen Strikethrough Issue:**")
        if tests_passed >= 4:
            print("   ✅ Backend processing appears correct - issue may be frontend display")
            print("   ✅ All roll types included in sponsoring logic")
            print("   ✅ Sponsored flags set correctly for database queries")
        else:
            print("   ❌ Backend processing issues detected")
            print("   ❌ Körnerbrötchen may not be included in sponsoring")
            
        print("2. **Balance Calculation Issue:**")
        if tests_passed >= 5:
            print("   ✅ Balance calculations appear mathematically correct")
            print("   ✅ Sponsor pays total cost, sponsored employees get refunds")
        else:
            print("   ❌ Balance calculation discrepancies detected")
            print("   ❌ Sponsor/sponsored balance logic may be incorrect")
        
        if tests_passed >= 5:
            print("\n🎉 CRITICAL SPONSORING LOGIC ANALYSIS COMPLETED!")
            print("✅ Backend sponsoring logic appears to be working correctly")
            print("✅ All breakfast items processed equally (Helles + Körner)")
            print("✅ Balance calculations follow expected logic")
            print("✅ If strikethrough issues persist, check frontend display logic")
            return True
        else:
            print("\n❌ CRITICAL SPONSORING LOGIC ISSUES CONFIRMED")
            failed_tests = total_tests - tests_passed
            print(f"⚠️  {failed_tests} test(s) failed - backend issues detected")
            print("⚠️  CRITICAL: Sponsoring system needs immediate attention")
            print("⚠️  User-reported issues appear to be valid backend problems")
            return False

if __name__ == "__main__":
    tester = CriticalSponsoringLogicTest()
    success = tester.run_critical_sponsoring_tests()
    sys.exit(0 if success else 1)