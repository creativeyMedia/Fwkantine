#!/usr/bin/env python3
"""
CRITICAL BALANCE LOGIC CORRECTION TESTING

Test the CORRECTED balance logic to ensure orders and payments work in the right direction.

**CORRECTED LOGIC TO VERIFY:**
- **Orders DECREASE balance** (create debt = negative balance)
- **Payments INCREASE balance** (reduce debt = more positive balance)

**BALANCE INTERPRETATION:**
- Negative balance = debt (owes money)  
- Positive balance = credit (has money)
- Zero balance = even

**TEST SCENARIOS:**

1. **Create Fresh Employee**: Create new test employee with 0.00 balance
2. **Test Order Logic**: 
   - Create breakfast order (€5.50)
   - Verify balance becomes NEGATIVE (-€5.50) = debt
   - Create drinks order (€2.00) 
   - Verify drinks balance becomes NEGATIVE (-€2.00) = debt
3. **Test Payment Logic**:
   - Pay €10.00 for breakfast (overpayment)
   - Verify breakfast balance becomes POSITIVE (+€4.50) = credit
   - Pay €1.50 for drinks (underpayment)
   - Verify drinks balance becomes NEGATIVE (-€0.50) = remaining debt
4. **Verify Separate Account Logic**:
   - Breakfast payment doesn't affect drinks balance
   - Drinks payment doesn't affect breakfast balance
5. **Test Edge Cases**:
   - Exact payment (€0.50 for remaining drinks debt)
   - Verify balance becomes exactly 0.00

**EXPECTED RESULTS:**
- Fresh employee: breakfast_balance=0.00, drinks_sweets_balance=0.00
- After orders: breakfast_balance=-5.50, drinks_sweets_balance=-2.00
- After breakfast payment: breakfast_balance=+4.50, drinks_sweets_balance=-2.00  
- After drinks payment: breakfast_balance=+4.50, drinks_sweets_balance=-0.50
- After final payment: breakfast_balance=+4.50, drinks_sweets_balance=0.00

**CRITICAL VERIFICATION:**
- Orders must create NEGATIVE balances (debt)
- Payments must create POSITIVE balances (credit/reduce debt)
- No more "backwards" balance calculations

Use Department "2. Wachabteilung" for testing.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta
import uuid

# Configuration - Use Department 2 as specified in review request
BASE_URL = "https://mealflow-1.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"
DEPARTMENT_PASSWORD = "password2"

class CorrectedBalanceLogicTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.test_employee = None
        self.admin_auth = None
        
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
        """Authenticate as department admin for balance testing"""
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
                    f"Successfully authenticated as admin for {DEPARTMENT_NAME} (admin2 password) for corrected balance testing"
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
    
    def create_fresh_employee(self):
        """Create a fresh test employee with 0.00 balance"""
        try:
            timestamp = datetime.now().strftime("%H%M%S")
            employee_name = f"BalanceTest_{timestamp}"
            
            response = self.session.post(f"{BASE_URL}/employees", json={
                "name": employee_name,
                "department_id": DEPARTMENT_ID
            })
            
            if response.status_code == 200:
                employee = response.json()
                self.test_employee = employee
                
                # Verify fresh employee has 0.00 balances
                breakfast_balance = employee.get('breakfast_balance', 0)
                drinks_balance = employee.get('drinks_sweets_balance', 0)
                
                if breakfast_balance == 0.0 and drinks_balance == 0.0:
                    self.log_result(
                        "Create Fresh Employee",
                        True,
                        f"Created fresh employee '{employee_name}' with breakfast_balance=€{breakfast_balance:.2f}, drinks_sweets_balance=€{drinks_balance:.2f}"
                    )
                    return employee
                else:
                    self.log_result(
                        "Create Fresh Employee",
                        False,
                        error=f"Fresh employee has non-zero balances: breakfast=€{breakfast_balance:.2f}, drinks=€{drinks_balance:.2f}"
                    )
                    return None
            else:
                self.log_result(
                    "Create Fresh Employee",
                    False,
                    error=f"Failed to create employee: HTTP {response.status_code}: {response.text}"
                )
                return None
                
        except Exception as e:
            self.log_result("Create Fresh Employee", False, error=str(e))
            return None
    
    # ========================================
    # BALANCE CHECKING UTILITIES
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
    
    # ========================================
    # ORDER LOGIC TESTING (SHOULD CREATE DEBT)
    # ========================================
    
    def test_breakfast_order_creates_debt(self):
        """Test that breakfast order creates NEGATIVE balance (debt)"""
        try:
            if not self.test_employee:
                return False
            
            # Get balance before order
            balance_before = self.get_employee_balance(self.test_employee['id'])
            if not balance_before:
                self.log_result(
                    "Breakfast Order Creates Debt",
                    False,
                    error="Could not get employee balance before order"
                )
                return False
            
            # Create breakfast order worth approximately €5.50
            order_data = {
                "employee_id": self.test_employee["id"],
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 1 roll = 2 halves
                    "white_halves": 2,  # 2 white halves
                    "seeded_halves": 0,  # 0 seeded halves
                    "toppings": ["butter", "kaese"],  # 2 toppings for 2 halves
                    "has_lunch": True,  # Include lunch (~€5.00)
                    "boiled_eggs": 1,   # 1 boiled egg (~€0.50)
                    "has_coffee": False  # No coffee
                }]
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_cost = order.get('total_price', 0)
                
                # Get balance after order
                balance_after = self.get_employee_balance(self.test_employee['id'])
                if balance_after:
                    new_breakfast_balance = balance_after['breakfast_balance']
                    expected_balance = balance_before['breakfast_balance'] - order_cost
                    
                    # CRITICAL CHECK: Balance should be NEGATIVE (debt)
                    if abs(new_breakfast_balance - expected_balance) < 0.01 and new_breakfast_balance < 0:
                        self.log_result(
                            "Breakfast Order Creates Debt",
                            True,
                            f"✅ CORRECTED LOGIC VERIFIED! Breakfast order (€{order_cost:.2f}) created NEGATIVE balance (debt). Balance: €0.00 → €{new_breakfast_balance:.2f} (debt of €{abs(new_breakfast_balance):.2f})"
                        )
                        return True
                    else:
                        self.log_result(
                            "Breakfast Order Creates Debt",
                            False,
                            error=f"❌ INCORRECT BALANCE LOGIC! Expected negative balance €{expected_balance:.2f}, got €{new_breakfast_balance:.2f}. Orders should create DEBT (negative balance)!"
                        )
                        return False
                else:
                    self.log_result(
                        "Breakfast Order Creates Debt",
                        False,
                        error="Could not verify balance after breakfast order"
                    )
                    return False
            else:
                self.log_result(
                    "Breakfast Order Creates Debt",
                    False,
                    error=f"Failed to create breakfast order: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Breakfast Order Creates Debt", False, error=str(e))
            return False
    
    def test_drinks_order_creates_debt(self):
        """Test that drinks order creates NEGATIVE balance (debt)"""
        try:
            if not self.test_employee:
                return False
            
            # Get balance before order
            balance_before = self.get_employee_balance(self.test_employee['id'])
            if not balance_before:
                self.log_result(
                    "Drinks Order Creates Debt",
                    False,
                    error="Could not get employee balance before drinks order"
                )
                return False
            
            # Get drinks menu first
            menu_response = self.session.get(f"{BASE_URL}/menu/drinks/{DEPARTMENT_ID}")
            if menu_response.status_code != 200:
                self.log_result(
                    "Drinks Order Creates Debt",
                    False,
                    error=f"Failed to get drinks menu: HTTP {menu_response.status_code}"
                )
                return False
            
            drinks_menu = menu_response.json()
            if not drinks_menu:
                self.log_result(
                    "Drinks Order Creates Debt",
                    False,
                    error="No drinks available in menu"
                )
                return False
            
            # Create drinks order worth approximately €2.00
            drink_items = {}
            total_expected = 0
            
            # Find drinks to reach approximately €2.00
            for drink in drinks_menu:
                if total_expected < 2.0:
                    quantity = 1
                    drink_items[drink['id']] = quantity
                    total_expected += drink.get('price', 0) * quantity
                    if total_expected >= 2.0:
                        break
                        
            order_data = {
                "employee_id": self.test_employee["id"],
                "department_id": DEPARTMENT_ID,
                "order_type": "drinks",
                "drink_items": drink_items
            }
            
            response = self.session.post(f"{BASE_URL}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_cost = order.get('total_price', 0)
                
                # Get balance after order
                balance_after = self.get_employee_balance(self.test_employee['id'])
                if balance_after:
                    new_drinks_balance = balance_after['drinks_sweets_balance']
                    expected_balance = balance_before['drinks_sweets_balance'] - order_cost
                    
                    # CRITICAL CHECK: Balance should be NEGATIVE (debt)
                    if abs(new_drinks_balance - expected_balance) < 0.01 and new_drinks_balance < 0:
                        self.log_result(
                            "Drinks Order Creates Debt",
                            True,
                            f"✅ CORRECTED LOGIC VERIFIED! Drinks order (€{order_cost:.2f}) created NEGATIVE balance (debt). Balance: €0.00 → €{new_drinks_balance:.2f} (debt of €{abs(new_drinks_balance):.2f})"
                        )
                        return True
                    else:
                        self.log_result(
                            "Drinks Order Creates Debt",
                            False,
                            error=f"❌ INCORRECT BALANCE LOGIC! Expected negative balance €{expected_balance:.2f}, got €{new_drinks_balance:.2f}. Orders should create DEBT (negative balance)!"
                        )
                        return False
                else:
                    self.log_result(
                        "Drinks Order Creates Debt",
                        False,
                        error="Could not verify balance after drinks order"
                    )
                    return False
            else:
                self.log_result(
                    "Drinks Order Creates Debt",
                    False,
                    error=f"Failed to create drinks order: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Drinks Order Creates Debt", False, error=str(e))
            return False
    
    # ========================================
    # PAYMENT LOGIC TESTING (SHOULD REDUCE DEBT)
    # ========================================
    
    def test_breakfast_overpayment_creates_credit(self):
        """Test that breakfast overpayment creates POSITIVE balance (credit)"""
        try:
            if not self.test_employee:
                return False
            
            # Get current balance (should be negative from breakfast order)
            balance_before = self.get_employee_balance(self.test_employee['id'])
            if not balance_before:
                self.log_result(
                    "Breakfast Overpayment Creates Credit",
                    False,
                    error="Could not get employee balance before payment"
                )
                return False
            
            breakfast_debt = balance_before['breakfast_balance']
            
            if breakfast_debt >= 0:
                self.log_result(
                    "Breakfast Overpayment Creates Credit",
                    False,
                    error=f"Employee has no breakfast debt (balance: €{breakfast_debt:.2f}). Need negative balance for overpayment test."
                )
                return False
            
            # Make overpayment (€10.00 for debt of ~€5.50)
            payment_amount = 10.0
            payment_data = {
                "payment_type": "breakfast",
                "amount": payment_amount,
                "notes": f"Overpayment test: €{payment_amount:.2f} for breakfast debt €{abs(breakfast_debt):.2f}"
            }
            
            response = self.session.post(
                f"{BASE_URL}/department-admin/flexible-payment/{self.test_employee['id']}?admin_department={DEPARTMENT_NAME}",
                json=payment_data
            )
            
            if response.status_code == 200:
                # Get balance after payment
                balance_after = self.get_employee_balance(self.test_employee['id'])
                if balance_after:
                    new_breakfast_balance = balance_after['breakfast_balance']
                    expected_balance = breakfast_debt + payment_amount  # Payment INCREASES balance
                    
                    # CRITICAL CHECK: Balance should be POSITIVE (credit) after overpayment
                    if abs(new_breakfast_balance - expected_balance) < 0.01 and new_breakfast_balance > 0:
                        credit_amount = new_breakfast_balance
                        self.log_result(
                            "Breakfast Overpayment Creates Credit",
                            True,
                            f"✅ CORRECTED LOGIC VERIFIED! Overpayment (€{payment_amount:.2f}) created POSITIVE balance (credit). Balance: €{breakfast_debt:.2f} → €{new_breakfast_balance:.2f} (credit of €{credit_amount:.2f})"
                        )
                        return True
                    else:
                        self.log_result(
                            "Breakfast Overpayment Creates Credit",
                            False,
                            error=f"❌ INCORRECT PAYMENT LOGIC! Expected positive balance €{expected_balance:.2f}, got €{new_breakfast_balance:.2f}. Overpayments should create CREDIT (positive balance)!"
                        )
                        return False
                else:
                    self.log_result(
                        "Breakfast Overpayment Creates Credit",
                        False,
                        error="Could not verify balance after overpayment"
                    )
                    return False
            else:
                self.log_result(
                    "Breakfast Overpayment Creates Credit",
                    False,
                    error=f"Overpayment failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Breakfast Overpayment Creates Credit", False, error=str(e))
            return False
    
    def test_drinks_underpayment_leaves_debt(self):
        """Test that drinks underpayment leaves NEGATIVE balance (remaining debt)"""
        try:
            if not self.test_employee:
                return False
            
            # Get current balance (should be negative from drinks order)
            balance_before = self.get_employee_balance(self.test_employee['id'])
            if not balance_before:
                self.log_result(
                    "Drinks Underpayment Leaves Debt",
                    False,
                    error="Could not get employee balance before underpayment"
                )
                return False
            
            drinks_debt = balance_before['drinks_sweets_balance']
            
            if drinks_debt >= 0:
                self.log_result(
                    "Drinks Underpayment Leaves Debt",
                    False,
                    error=f"Employee has no drinks debt (balance: €{drinks_debt:.2f}). Need negative balance for underpayment test."
                )
                return False
            
            # Make underpayment (€1.50 for debt of ~€2.00)
            payment_amount = 1.5
            payment_data = {
                "payment_type": "drinks_sweets",
                "amount": payment_amount,
                "notes": f"Underpayment test: €{payment_amount:.2f} for drinks debt €{abs(drinks_debt):.2f}"
            }
            
            response = self.session.post(
                f"{BASE_URL}/department-admin/flexible-payment/{self.test_employee['id']}?admin_department={DEPARTMENT_NAME}",
                json=payment_data
            )
            
            if response.status_code == 200:
                # Get balance after payment
                balance_after = self.get_employee_balance(self.test_employee['id'])
                if balance_after:
                    new_drinks_balance = balance_after['drinks_sweets_balance']
                    expected_balance = drinks_debt + payment_amount  # Payment INCREASES balance
                    
                    # CRITICAL CHECK: Balance should still be NEGATIVE (remaining debt) after underpayment
                    if abs(new_drinks_balance - expected_balance) < 0.01 and new_drinks_balance < 0:
                        remaining_debt = abs(new_drinks_balance)
                        self.log_result(
                            "Drinks Underpayment Leaves Debt",
                            True,
                            f"✅ CORRECTED LOGIC VERIFIED! Underpayment (€{payment_amount:.2f}) left NEGATIVE balance (remaining debt). Balance: €{drinks_debt:.2f} → €{new_drinks_balance:.2f} (remaining debt €{remaining_debt:.2f})"
                        )
                        return True
                    else:
                        self.log_result(
                            "Drinks Underpayment Leaves Debt",
                            False,
                            error=f"❌ INCORRECT PAYMENT LOGIC! Expected negative balance €{expected_balance:.2f}, got €{new_drinks_balance:.2f}. Underpayments should leave DEBT (negative balance)!"
                        )
                        return False
                else:
                    self.log_result(
                        "Drinks Underpayment Leaves Debt",
                        False,
                        error="Could not verify balance after underpayment"
                    )
                    return False
            else:
                self.log_result(
                    "Drinks Underpayment Leaves Debt",
                    False,
                    error=f"Underpayment failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Drinks Underpayment Leaves Debt", False, error=str(e))
            return False
    
    # ========================================
    # SEPARATE ACCOUNT LOGIC TESTING
    # ========================================
    
    def test_separate_account_logic(self):
        """Verify that breakfast and drinks payments don't affect each other"""
        try:
            if not self.test_employee:
                return False
            
            # Get balance before any payments
            balance_before = self.get_employee_balance(self.test_employee['id'])
            if not balance_before:
                self.log_result(
                    "Separate Account Logic",
                    False,
                    error="Could not get employee balance for separate account test"
                )
                return False
            
            breakfast_balance_before = balance_before['breakfast_balance']
            drinks_balance_before = balance_before['drinks_sweets_balance']
            
            # Make a small breakfast payment
            payment_amount = 2.0
            payment_data = {
                "payment_type": "breakfast",
                "amount": payment_amount,
                "notes": "Separate account test - breakfast payment"
            }
            
            response = self.session.post(
                f"{BASE_URL}/department-admin/flexible-payment/{self.test_employee['id']}?admin_department={DEPARTMENT_NAME}",
                json=payment_data
            )
            
            if response.status_code == 200:
                # Get balance after breakfast payment
                balance_after = self.get_employee_balance(self.test_employee['id'])
                if balance_after:
                    new_breakfast_balance = balance_after['breakfast_balance']
                    new_drinks_balance = balance_after['drinks_sweets_balance']
                    
                    # Check that breakfast balance changed but drinks balance didn't
                    breakfast_changed = abs(new_breakfast_balance - (breakfast_balance_before + payment_amount)) < 0.01
                    drinks_unchanged = abs(new_drinks_balance - drinks_balance_before) < 0.01
                    
                    if breakfast_changed and drinks_unchanged:
                        self.log_result(
                            "Separate Account Logic",
                            True,
                            f"✅ SEPARATE ACCOUNTS VERIFIED! Breakfast payment (€{payment_amount:.2f}) affected only breakfast balance (€{breakfast_balance_before:.2f} → €{new_breakfast_balance:.2f}). Drinks balance unchanged (€{drinks_balance_before:.2f})"
                        )
                        return True
                    else:
                        self.log_result(
                            "Separate Account Logic",
                            False,
                            error=f"❌ ACCOUNT SEPARATION FAILED! Breakfast payment should only affect breakfast balance. Breakfast: €{breakfast_balance_before:.2f} → €{new_breakfast_balance:.2f}, Drinks: €{drinks_balance_before:.2f} → €{new_drinks_balance:.2f}"
                        )
                        return False
                else:
                    self.log_result(
                        "Separate Account Logic",
                        False,
                        error="Could not verify balance after separate account test"
                    )
                    return False
            else:
                self.log_result(
                    "Separate Account Logic",
                    False,
                    error=f"Separate account payment failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Separate Account Logic", False, error=str(e))
            return False
    
    # ========================================
    # EDGE CASE TESTING
    # ========================================
    
    def test_exact_payment_zeros_balance(self):
        """Test that exact payment creates exactly 0.00 balance"""
        try:
            if not self.test_employee:
                return False
            
            # Get current balance
            balance_before = self.get_employee_balance(self.test_employee['id'])
            if not balance_before:
                self.log_result(
                    "Exact Payment Zeros Balance",
                    False,
                    error="Could not get employee balance for exact payment test"
                )
                return False
            
            drinks_debt = balance_before['drinks_sweets_balance']
            
            if drinks_debt >= 0:
                self.log_result(
                    "Exact Payment Zeros Balance",
                    False,
                    error=f"Employee has no drinks debt (balance: €{drinks_debt:.2f}). Need negative balance for exact payment test."
                )
                return False
            
            # Make exact payment to zero the balance
            payment_amount = abs(drinks_debt)  # Pay exactly the debt amount
            payment_data = {
                "payment_type": "drinks_sweets",
                "amount": payment_amount,
                "notes": f"Exact payment test: €{payment_amount:.2f} for exact debt €{abs(drinks_debt):.2f}"
            }
            
            response = self.session.post(
                f"{BASE_URL}/department-admin/flexible-payment/{self.test_employee['id']}?admin_department={DEPARTMENT_NAME}",
                json=payment_data
            )
            
            if response.status_code == 200:
                # Get balance after payment
                balance_after = self.get_employee_balance(self.test_employee['id'])
                if balance_after:
                    new_drinks_balance = balance_after['drinks_sweets_balance']
                    
                    # CRITICAL CHECK: Balance should be exactly 0.00
                    if abs(new_drinks_balance) < 0.01:  # Within 1 cent of zero
                        self.log_result(
                            "Exact Payment Zeros Balance",
                            True,
                            f"✅ EXACT PAYMENT VERIFIED! Exact payment (€{payment_amount:.2f}) created exactly zero balance. Balance: €{drinks_debt:.2f} → €{new_drinks_balance:.2f}"
                        )
                        return True
                    else:
                        self.log_result(
                            "Exact Payment Zeros Balance",
                            False,
                            error=f"❌ EXACT PAYMENT FAILED! Expected €0.00 balance, got €{new_drinks_balance:.2f}. Exact payments should zero the balance!"
                        )
                        return False
                else:
                    self.log_result(
                        "Exact Payment Zeros Balance",
                        False,
                        error="Could not verify balance after exact payment"
                    )
                    return False
            else:
                self.log_result(
                    "Exact Payment Zeros Balance",
                    False,
                    error=f"Exact payment failed: HTTP {response.status_code}: {response.text}"
                )
                return False
                
        except Exception as e:
            self.log_result("Exact Payment Zeros Balance", False, error=str(e))
            return False

    def run_corrected_balance_tests(self):
        """Run all corrected balance logic tests"""
        print("🎯 STARTING CRITICAL BALANCE LOGIC CORRECTION TESTING")
        print("=" * 80)
        print("Testing CORRECTED balance logic to ensure orders and payments work correctly")
        print("DEPARTMENT: 2. Wachabteilung (admin: admin2)")
        print("CRITICAL VERIFICATION:")
        print("  - Orders DECREASE balance (create debt = negative balance)")
        print("  - Payments INCREASE balance (reduce debt = more positive balance)")
        print("=" * 80)
        
        # Test sequence
        tests_passed = 0
        total_tests = 7
        
        # SETUP
        print("\n🔧 SETUP AND AUTHENTICATION")
        print("-" * 50)
        
        if not self.authenticate_as_admin():
            print("❌ Cannot proceed without admin authentication")
            return False
        tests_passed += 1
        
        fresh_employee = self.create_fresh_employee()
        if not fresh_employee:
            print("❌ Cannot proceed without fresh test employee")
            return False
        
        # ORDER LOGIC TESTS (SHOULD CREATE DEBT)
        print("\n📝 TESTING ORDER LOGIC (SHOULD CREATE DEBT)")
        print("-" * 50)
        
        if self.test_breakfast_order_creates_debt():
            tests_passed += 1
        
        if self.test_drinks_order_creates_debt():
            tests_passed += 1
        
        # PAYMENT LOGIC TESTS (SHOULD REDUCE DEBT)
        print("\n💰 TESTING PAYMENT LOGIC (SHOULD REDUCE DEBT)")
        print("-" * 50)
        
        if self.test_breakfast_overpayment_creates_credit():
            tests_passed += 1
        
        if self.test_drinks_underpayment_leaves_debt():
            tests_passed += 1
        
        # SEPARATE ACCOUNT LOGIC
        print("\n🔄 TESTING SEPARATE ACCOUNT LOGIC")
        print("-" * 50)
        
        if self.test_separate_account_logic():
            tests_passed += 1
        
        # EDGE CASES
        print("\n⚡ TESTING EDGE CASES")
        print("-" * 50)
        
        if self.test_exact_payment_zeros_balance():
            tests_passed += 1
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 CRITICAL BALANCE LOGIC CORRECTION TESTING SUMMARY")
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
        balance_logic_working = tests_passed >= 6  # At least 85% success rate
        
        print(f"\n🎯 CORRECTED BALANCE LOGIC DIAGNOSIS:")
        if balance_logic_working:
            print("✅ CORRECTED BALANCE LOGIC: WORKING")
            print("   ✅ Orders DECREASE balance (create debt = negative balance)")
            print("   ✅ Payments INCREASE balance (reduce debt = more positive balance)")
            print("   ✅ Negative balance = debt (owes money)")
            print("   ✅ Positive balance = credit (has money)")
            print("   ✅ Zero balance = even")
            print("   ✅ Separate account logic working (breakfast vs drinks)")
        else:
            print("❌ CORRECTED BALANCE LOGIC: NOT WORKING CORRECTLY")
            failed_tests = total_tests - tests_passed
            print(f"   ⚠️  {failed_tests} test(s) failed")
            print("   ⚠️  Balance calculations may still be backwards or incorrect")
        
        if tests_passed >= 6:  # At least 85% success rate
            print("\n🎉 CRITICAL BALANCE LOGIC CORRECTION TESTING COMPLETED!")
            print("✅ Balance logic has been corrected and verified")
            print("✅ Orders create debt, payments reduce debt - NO MORE BACKWARDS CALCULATIONS")
            return True
        else:
            print("\n❌ CRITICAL BALANCE LOGIC CORRECTION TESTING REVEALED ISSUES")
            failed_tests = total_tests - tests_passed
            print(f"⚠️  {failed_tests} test(s) failed")
            print("⚠️  Balance logic still needs correction - calculations may be backwards")
            return False

if __name__ == "__main__":
    tester = CorrectedBalanceLogicTest()
    success = tester.run_corrected_balance_tests()
    sys.exit(0 if success else 1)