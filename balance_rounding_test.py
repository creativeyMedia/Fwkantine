#!/usr/bin/env python3
"""
Balance Rounding Fix Test Suite

TESTING FOCUS:
Testing the balance rounding fix to ensure floating-point precision issues are resolved.

BACKEND FUNCTIONS TO TEST:
- round_to_cents() function for various scenarios
- Balance calculations in order processing using proper rounding
- Edge cases like -0.00, 8.999999, 0.000001, etc.
- Verify balances are consistently rounded to 2 decimal places
- Test that negative zero (-0.00) is converted to positive zero (0.00)

TEST SCENARIOS:
1. Test the new round_to_cents() function for various scenarios
2. Verify balance calculations in order processing now use proper rounding
3. Test edge cases like -0.00, 8.999999, 0.000001, etc.
4. Verify that balances are consistently rounded to 2 decimal places
5. Test that negative zero (-0.00) is converted to positive zero (0.00)
6. Order creation with balance deduction
7. Payment processing with balance addition
8. Balance display formatting
9. Edge case handling for very small amounts

EXPECTED RESULTS:
- All balance calculations should be rounded to exactly 2 decimal places
- No more floating-point precision errors like 8.999999 → 9.00
- Negative zero (-0.00) should display as 0.00
- Balance updates through order processing should use rounding
- Mathematical consistency maintained across all operations
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime, timezone
import sys
import traceback

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://firebrigade-food.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class BalanceRoundingTester:
    def __init__(self):
        self.session = None
        self.test_results = []
        self.departments = [
            {"id": "fw4abteilung1", "name": "1. Wachabteilung", "admin_password": "admin1", "password": "password1"},
            {"id": "fw4abteilung2", "name": "2. Wachabteilung", "admin_password": "admin2", "password": "password2"}
        ]
        self.test_employees = []  # Track created test employees for cleanup
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method, endpoint, data=None, params=None):
        """Make HTTP request to backend API"""
        url = f"{API_BASE}{endpoint}"
        try:
            if method.upper() == 'GET':
                async with self.session.get(url, params=params) as response:
                    return await response.json(), response.status
            elif method.upper() == 'POST':
                async with self.session.post(url, json=data, params=params) as response:
                    return await response.json(), response.status
            elif method.upper() == 'PUT':
                async with self.session.put(url, json=data, params=params) as response:
                    return await response.json(), response.status
            elif method.upper() == 'DELETE':
                async with self.session.delete(url, params=params) as response:
                    return await response.json(), response.status
        except Exception as e:
            print(f"❌ Request failed: {method} {url} - {str(e)}")
            return None, 500
    
    async def authenticate_admin(self, department_name, admin_password):
        """Authenticate as department admin"""
        auth_data = {
            "department_name": department_name,
            "admin_password": admin_password
        }
        
        response, status = await self.make_request('POST', '/login/department-admin', auth_data)
        if status == 200:
            print(f"✅ Admin authentication successful for {department_name}")
            return response
        else:
            print(f"❌ Admin authentication failed for {department_name}: {response}")
            return None
    
    async def create_test_employee(self, department_id, name, is_guest=False):
        """Create a test employee for testing"""
        employee_data = {
            "name": name,
            "department_id": department_id,
            "is_guest": is_guest
        }
        
        response, status = await self.make_request('POST', '/employees', employee_data)
        if status == 200:
            print(f"✅ Created test employee: {name} in {department_id}")
            self.test_employees.append(response['id'])  # Track for cleanup
            return response
        else:
            print(f"❌ Failed to create employee {name}: {response}")
            return None
    
    async def get_employee_balance(self, employee_id):
        """Get current employee balance"""
        response, status = await self.make_request('GET', f'/employees/{employee_id}/profile')
        if status == 200:
            employee = response.get('employee', {})
            return {
                'breakfast_balance': employee.get('breakfast_balance', 0.0),
                'drinks_sweets_balance': employee.get('drinks_sweets_balance', 0.0)
            }
        else:
            print(f"❌ Failed to get employee balance: {response}")
            return None
    
    async def make_flexible_payment(self, employee_id, department_id, balance_type, amount, notes="Test payment"):
        """Make a flexible payment to set specific balance"""
        payment_data = {
            "payment_type": balance_type if balance_type != "drinks" else "drinks_sweets",
            "balance_type": balance_type,
            "amount": amount,
            "payment_method": "adjustment",
            "notes": notes
        }
        
        params = {"admin_department": department_id}
        
        response, status = await self.make_request('POST', f'/department-admin/flexible-payment/{employee_id}', payment_data, params)
        if status == 200:
            return response
        else:
            print(f"❌ Failed to make payment: {response}")
            return None
    
    async def create_breakfast_order(self, employee_id, department_id, total_price_target=None):
        """Create a breakfast order with specific pricing to test rounding"""
        # Create a simple breakfast order
        order_data = {
            "employee_id": employee_id,
            "department_id": department_id,
            "order_type": "breakfast",
            "breakfast_items": [{
                "total_halves": 2,
                "white_halves": 1,
                "seeded_halves": 1,
                "toppings": ["butter", "kaese"],
                "has_lunch": False,
                "boiled_eggs": 0,
                "fried_eggs": 0,
                "has_coffee": True
            }],
            "notes": "Balance rounding test order"
        }
        
        response, status = await self.make_request('POST', '/orders', order_data)
        if status == 200:
            return response
        else:
            print(f"❌ Failed to create breakfast order: {response}")
            return None
    
    async def create_drinks_order(self, employee_id, department_id, drink_price_target=None):
        """Create a drinks order to test rounding"""
        # Get available drinks
        drinks_response, status = await self.make_request('GET', f'/menu/drinks/{department_id}')
        if status != 200 or not drinks_response:
            print(f"❌ Failed to get drinks menu: {drinks_response}")
            return None
        
        # Use first available drink
        drink = drinks_response[0]
        
        order_data = {
            "employee_id": employee_id,
            "department_id": department_id,
            "order_type": "drinks",
            "drink_items": {
                drink['id']: 1
            },
            "notes": "Balance rounding test drinks order"
        }
        
        response, status = await self.make_request('POST', '/orders', order_data)
        if status == 200:
            return response
        else:
            print(f"❌ Failed to create drinks order: {response}")
            return None
    
    async def test_round_to_cents_function(self):
        """Test Case 1: Test the round_to_cents function directly through balance operations"""
        print(f"\n🧪 TEST CASE 1: round_to_cents Function Testing")
        
        # Create test employee
        test_emp = await self.create_test_employee("fw4abteilung1", "RoundingTestEmployee")
        if not test_emp:
            return {"test": "round_to_cents function", "success": False, "error": "Failed to create test employee"}
        
        employee_id = test_emp['id']
        department_id = "fw4abteilung1"
        
        test_cases = [
            # (amount, expected_result, description)
            (8.999999, 9.00, "Floating point precision error case"),
            (0.000001, 0.00, "Very small positive amount"),
            (-0.000001, 0.00, "Very small negative amount"),
            (1.999, 2.00, "Rounding up case"),
            (1.001, 1.00, "Rounding down case"),
            (0.005, 0.01, "Exact half rounding"),
            (-0.005, -0.01, "Negative half rounding"),
            (123.456789, 123.46, "Multiple decimal places"),
            (-123.456789, -123.46, "Negative multiple decimal places"),
            (0.0, 0.00, "Exact zero"),
            (-0.0, 0.00, "Negative zero should become positive zero")
        ]
        
        results = []
        
        for amount, expected, description in test_cases:
            print(f"   Testing: {description} - Input: {amount}, Expected: {expected}")
            
            # Reset balance to 0
            current_balance = await self.get_employee_balance(employee_id)
            if current_balance and current_balance['breakfast_balance'] != 0:
                reset_amount = -current_balance['breakfast_balance']
                await self.make_flexible_payment(employee_id, department_id, "breakfast", reset_amount, "Reset for test")
            
            # Make payment with test amount
            payment_result = await self.make_flexible_payment(employee_id, department_id, "breakfast", amount, f"Test: {description}")
            if not payment_result:
                results.append({"amount": amount, "expected": expected, "actual": None, "success": False, "description": description})
                continue
            
            # Get resulting balance
            new_balance = await self.get_employee_balance(employee_id)
            if not new_balance:
                results.append({"amount": amount, "expected": expected, "actual": None, "success": False, "description": description})
                continue
            
            actual = new_balance['breakfast_balance']
            success = abs(actual - expected) < 0.001  # Allow tiny floating point differences
            
            # Special check for negative zero
            if amount == -0.0:
                success = actual == 0.0 and str(actual) != "-0.0"
            
            results.append({
                "amount": amount,
                "expected": expected,
                "actual": actual,
                "success": success,
                "description": description
            })
            
            print(f"      Result: {actual} - {'✅ PASS' if success else '❌ FAIL'}")
        
        # Summary
        passed = sum(1 for r in results if r['success'])
        total = len(results)
        
        return {
            "test": "round_to_cents function",
            "success": passed == total,
            "passed": passed,
            "total": total,
            "results": results,
            "employee_id": employee_id
        }
    
    async def test_order_balance_rounding(self):
        """Test Case 2: Test balance rounding in order processing"""
        print(f"\n🧪 TEST CASE 2: Order Processing Balance Rounding")
        
        # Create test employee
        test_emp = await self.create_test_employee("fw4abteilung1", "OrderRoundingTestEmployee")
        if not test_emp:
            return {"test": "order balance rounding", "success": False, "error": "Failed to create test employee"}
        
        employee_id = test_emp['id']
        department_id = "fw4abteilung1"
        
        # Test scenarios with orders that might cause rounding issues
        test_scenarios = []
        
        # Scenario 1: Multiple small orders that could accumulate rounding errors
        print(f"   Scenario 1: Multiple small orders accumulation test")
        
        initial_balance = await self.get_employee_balance(employee_id)
        if not initial_balance:
            return {"test": "order balance rounding", "success": False, "error": "Failed to get initial balance"}
        
        # Create multiple small orders
        orders_created = []
        for i in range(3):
            order = await self.create_breakfast_order(employee_id, department_id)
            if order:
                orders_created.append(order)
        
        final_balance = await self.get_employee_balance(employee_id)
        if not final_balance:
            return {"test": "order balance rounding", "success": False, "error": "Failed to get final balance"}
        
        # Check that balance is properly rounded
        balance_change = final_balance['breakfast_balance'] - initial_balance['breakfast_balance']
        is_properly_rounded = abs(balance_change - round(balance_change, 2)) < 0.001
        
        test_scenarios.append({
            "scenario": "Multiple breakfast orders",
            "orders_count": len(orders_created),
            "initial_balance": initial_balance['breakfast_balance'],
            "final_balance": final_balance['breakfast_balance'],
            "balance_change": balance_change,
            "properly_rounded": is_properly_rounded,
            "success": is_properly_rounded and len(orders_created) > 0
        })
        
        print(f"      Orders created: {len(orders_created)}")
        print(f"      Balance change: {balance_change}")
        print(f"      Properly rounded: {'✅' if is_properly_rounded else '❌'}")
        
        # Scenario 2: Drinks orders (negative amounts)
        print(f"   Scenario 2: Drinks orders (negative amounts) test")
        
        initial_drinks_balance = final_balance['drinks_sweets_balance']
        
        # Create drinks order
        drinks_order = await self.create_drinks_order(employee_id, department_id)
        
        final_drinks_balance = await self.get_employee_balance(employee_id)
        if not final_drinks_balance:
            return {"test": "order balance rounding", "success": False, "error": "Failed to get drinks balance"}
        
        drinks_balance_change = final_drinks_balance['drinks_sweets_balance'] - initial_drinks_balance
        drinks_properly_rounded = abs(drinks_balance_change - round(drinks_balance_change, 2)) < 0.001
        
        test_scenarios.append({
            "scenario": "Drinks order (negative amount)",
            "order_created": drinks_order is not None,
            "initial_balance": initial_drinks_balance,
            "final_balance": final_drinks_balance['drinks_sweets_balance'],
            "balance_change": drinks_balance_change,
            "properly_rounded": drinks_properly_rounded,
            "success": drinks_properly_rounded and drinks_order is not None
        })
        
        print(f"      Drinks order created: {'✅' if drinks_order else '❌'}")
        print(f"      Balance change: {drinks_balance_change}")
        print(f"      Properly rounded: {'✅' if drinks_properly_rounded else '❌'}")
        
        # Summary
        passed = sum(1 for s in test_scenarios if s['success'])
        total = len(test_scenarios)
        
        return {
            "test": "order balance rounding",
            "success": passed == total,
            "passed": passed,
            "total": total,
            "scenarios": test_scenarios,
            "employee_id": employee_id
        }
    
    async def test_payment_balance_rounding(self):
        """Test Case 3: Test balance rounding in payment processing"""
        print(f"\n🧪 TEST CASE 3: Payment Processing Balance Rounding")
        
        # Create test employee
        test_emp = await self.create_test_employee("fw4abteilung1", "PaymentRoundingTestEmployee")
        if not test_emp:
            return {"test": "payment balance rounding", "success": False, "error": "Failed to create test employee"}
        
        employee_id = test_emp['id']
        department_id = "fw4abteilung1"
        
        # Test payments with amounts that could cause rounding issues
        payment_test_cases = [
            (8.999999, "Floating point precision payment"),
            (0.001, "Very small payment"),
            (123.456789, "Multiple decimal places payment"),
            (-5.333333, "Negative payment (withdrawal)"),
            (0.005, "Exact half cent payment")
        ]
        
        results = []
        
        for amount, description in payment_test_cases:
            print(f"   Testing: {description} - Amount: {amount}")
            
            # Get initial balance
            initial_balance = await self.get_employee_balance(employee_id)
            if not initial_balance:
                results.append({"amount": amount, "success": False, "error": "Failed to get initial balance", "description": description})
                continue
            
            # Make payment
            payment_result = await self.make_flexible_payment(employee_id, department_id, "breakfast", amount, description)
            if not payment_result:
                results.append({"amount": amount, "success": False, "error": "Payment failed", "description": description})
                continue
            
            # Get final balance
            final_balance = await self.get_employee_balance(employee_id)
            if not final_balance:
                results.append({"amount": amount, "success": False, "error": "Failed to get final balance", "description": description})
                continue
            
            # Check rounding - use our improved rounding function logic
            from decimal import Decimal, ROUND_HALF_UP
            decimal_amount = Decimal(str(float(amount)))
            expected_change = float(decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            balance_change = final_balance['breakfast_balance'] - initial_balance['breakfast_balance']
            is_properly_rounded = abs(balance_change - expected_change) < 0.001
            
            # Check that final balance has exactly 2 decimal places
            final_balance_str = f"{final_balance['breakfast_balance']:.2f}"
            has_two_decimals = len(final_balance_str.split('.')[-1]) == 2
            
            results.append({
                "amount": amount,
                "expected_change": expected_change,
                "actual_change": balance_change,
                "initial_balance": initial_balance['breakfast_balance'],
                "final_balance": final_balance['breakfast_balance'],
                "properly_rounded": is_properly_rounded,
                "has_two_decimals": has_two_decimals,
                "success": is_properly_rounded and has_two_decimals,
                "description": description
            })
            
            print(f"      Expected change: {expected_change}, Actual: {balance_change}")
            print(f"      Final balance: {final_balance['breakfast_balance']}")
            print(f"      Result: {'✅ PASS' if is_properly_rounded and has_two_decimals else '❌ FAIL'}")
        
        # Summary
        passed = sum(1 for r in results if r['success'])
        total = len(results)
        
        return {
            "test": "payment balance rounding",
            "success": passed == total,
            "passed": passed,
            "total": total,
            "results": results,
            "employee_id": employee_id
        }
    
    async def test_negative_zero_handling(self):
        """Test Case 4: Test that negative zero (-0.00) is converted to positive zero (0.00)"""
        print(f"\n🧪 TEST CASE 4: Negative Zero Handling")
        
        # Create test employee
        test_emp = await self.create_test_employee("fw4abteilung1", "NegativeZeroTestEmployee")
        if not test_emp:
            return {"test": "negative zero handling", "success": False, "error": "Failed to create test employee"}
        
        employee_id = test_emp['id']
        department_id = "fw4abteilung1"
        
        # Test scenarios that could result in negative zero
        test_scenarios = []
        
        # Scenario 1: Payment that exactly cancels out a debt
        print(f"   Scenario 1: Payment exactly canceling debt")
        
        # Create a small debt
        debt_amount = -5.00
        await self.make_flexible_payment(employee_id, department_id, "breakfast", debt_amount, "Create debt")
        
        # Pay exact amount to cancel debt
        payment_amount = 5.00
        await self.make_flexible_payment(employee_id, department_id, "breakfast", payment_amount, "Cancel debt")
        
        balance_after_cancel = await self.get_employee_balance(employee_id)
        if balance_after_cancel:
            final_balance = balance_after_cancel['breakfast_balance']
            is_positive_zero = final_balance == 0.0 and str(final_balance) != "-0.0"
            
            test_scenarios.append({
                "scenario": "Debt cancellation",
                "final_balance": final_balance,
                "is_positive_zero": is_positive_zero,
                "balance_str": str(final_balance),
                "success": is_positive_zero
            })
            
            print(f"      Final balance: {final_balance}")
            print(f"      Balance string: '{str(final_balance)}'")
            print(f"      Is positive zero: {'✅' if is_positive_zero else '❌'}")
        
        # Scenario 2: Very small negative amount that rounds to zero
        print(f"   Scenario 2: Very small negative amount rounding to zero")
        
        # Reset balance
        current_balance = await self.get_employee_balance(employee_id)
        if current_balance and current_balance['breakfast_balance'] != 0:
            reset_amount = -current_balance['breakfast_balance']
            await self.make_flexible_payment(employee_id, department_id, "breakfast", reset_amount, "Reset")
        
        # Apply very small negative amount
        tiny_negative = -0.001
        await self.make_flexible_payment(employee_id, department_id, "breakfast", tiny_negative, "Tiny negative")
        
        balance_after_tiny = await self.get_employee_balance(employee_id)
        if balance_after_tiny:
            final_balance = balance_after_tiny['breakfast_balance']
            is_positive_zero = final_balance == 0.0 and str(final_balance) != "-0.0"
            
            test_scenarios.append({
                "scenario": "Tiny negative amount",
                "input_amount": tiny_negative,
                "final_balance": final_balance,
                "is_positive_zero": is_positive_zero,
                "balance_str": str(final_balance),
                "success": is_positive_zero
            })
            
            print(f"      Input amount: {tiny_negative}")
            print(f"      Final balance: {final_balance}")
            print(f"      Is positive zero: {'✅' if is_positive_zero else '❌'}")
        
        # Summary
        passed = sum(1 for s in test_scenarios if s['success'])
        total = len(test_scenarios)
        
        return {
            "test": "negative zero handling",
            "success": passed == total,
            "passed": passed,
            "total": total,
            "scenarios": test_scenarios,
            "employee_id": employee_id
        }
    
    async def test_edge_cases(self):
        """Test Case 5: Test edge cases for balance rounding"""
        print(f"\n🧪 TEST CASE 5: Edge Cases Testing")
        
        # Create test employee
        test_emp = await self.create_test_employee("fw4abteilung1", "EdgeCaseTestEmployee")
        if not test_emp:
            return {"test": "edge cases", "success": False, "error": "Failed to create test employee"}
        
        employee_id = test_emp['id']
        department_id = "fw4abteilung1"
        
        # Edge case scenarios
        edge_cases = [
            (999999.999999, 1000000.00, "Very large amount with precision"),
            (-999999.999999, -1000000.00, "Very large negative amount"),
            (0.994, 0.99, "Rounding down at 0.994"),
            (0.995, 1.00, "Rounding up at 0.995"),
            (0.996, 1.00, "Rounding up at 0.996"),
            (-0.994, -0.99, "Negative rounding down"),
            (-0.995, -1.00, "Negative rounding up"),
            (1e-10, 0.00, "Scientific notation small positive"),
            (-1e-10, 0.00, "Scientific notation small negative"),
            (float('inf'), None, "Infinity handling"),
            (float('-inf'), None, "Negative infinity handling")
        ]
        
        results = []
        
        for amount, expected, description in edge_cases:
            print(f"   Testing: {description} - Input: {amount}")
            
            # Reset balance
            current_balance = await self.get_employee_balance(employee_id)
            if current_balance and current_balance['breakfast_balance'] != 0:
                reset_amount = -current_balance['breakfast_balance']
                await self.make_flexible_payment(employee_id, department_id, "breakfast", reset_amount, "Reset")
            
            # Handle infinity cases
            if amount in [float('inf'), float('-inf')]:
                # These should be rejected or handled gracefully
                payment_result = await self.make_flexible_payment(employee_id, department_id, "breakfast", amount, description)
                success = payment_result is None  # Should fail gracefully
                
                results.append({
                    "amount": amount,
                    "expected": expected,
                    "actual": None,
                    "success": success,
                    "description": description,
                    "note": "Should be rejected gracefully"
                })
                
                print(f"      Result: {'✅ PASS (rejected)' if success else '❌ FAIL (not rejected)'}")
                continue
            
            # Normal cases
            payment_result = await self.make_flexible_payment(employee_id, department_id, "breakfast", amount, description)
            if not payment_result:
                results.append({
                    "amount": amount,
                    "expected": expected,
                    "actual": None,
                    "success": False,
                    "description": description,
                    "error": "Payment failed"
                })
                continue
            
            # Get resulting balance
            new_balance = await self.get_employee_balance(employee_id)
            if not new_balance:
                results.append({
                    "amount": amount,
                    "expected": expected,
                    "actual": None,
                    "success": False,
                    "description": description,
                    "error": "Failed to get balance"
                })
                continue
            
            actual = new_balance['breakfast_balance']
            success = abs(actual - expected) < 0.001 if expected is not None else False
            
            results.append({
                "amount": amount,
                "expected": expected,
                "actual": actual,
                "success": success,
                "description": description
            })
            
            print(f"      Expected: {expected}, Actual: {actual}")
            print(f"      Result: {'✅ PASS' if success else '❌ FAIL'}")
        
        # Summary
        passed = sum(1 for r in results if r['success'])
        total = len(results)
        
        return {
            "test": "edge cases",
            "success": passed == total,
            "passed": passed,
            "total": total,
            "results": results,
            "employee_id": employee_id
        }
    
    async def test_mathematical_consistency(self):
        """Test Case 6: Test mathematical consistency across operations"""
        print(f"\n🧪 TEST CASE 6: Mathematical Consistency Testing")
        
        # Create test employee
        test_emp = await self.create_test_employee("fw4abteilung1", "ConsistencyTestEmployee")
        if not test_emp:
            return {"test": "mathematical consistency", "success": False, "error": "Failed to create test employee"}
        
        employee_id = test_emp['id']
        department_id = "fw4abteilung1"
        
        # Test mathematical operations consistency
        test_operations = []
        
        # Operation 1: Multiple small payments vs one large payment (expect small difference due to individual rounding)
        print(f"   Operation 1: Multiple small vs single large payment (individual rounding expected)")
        
        # Reset balance
        current_balance = await self.get_employee_balance(employee_id)
        if current_balance and current_balance['breakfast_balance'] != 0:
            reset_amount = -current_balance['breakfast_balance']
            await self.make_flexible_payment(employee_id, department_id, "breakfast", reset_amount, "Reset")
        
        # Make multiple small payments
        small_amounts = [1.111, 2.222, 3.333]
        for amount in small_amounts:
            await self.make_flexible_payment(employee_id, department_id, "breakfast", amount, f"Small payment {amount}")
        
        balance_after_small = await self.get_employee_balance(employee_id)
        
        # Reset and make one large payment
        if balance_after_small:
            reset_amount = -balance_after_small['breakfast_balance']
            await self.make_flexible_payment(employee_id, department_id, "breakfast", reset_amount, "Reset")
        
        large_amount = sum(small_amounts)
        await self.make_flexible_payment(employee_id, department_id, "breakfast", large_amount, f"Large payment {large_amount}")
        
        balance_after_large = await self.get_employee_balance(employee_id)
        
        if balance_after_small and balance_after_large:
            small_total = balance_after_small['breakfast_balance']
            large_total = balance_after_large['breakfast_balance']
            # Allow for small differences due to individual rounding of each payment
            consistency_check = abs(small_total - large_total) < 0.02  # Allow up to 2 cents difference
            
            test_operations.append({
                "operation": "Multiple small vs single large payment",
                "small_payments": small_amounts,
                "small_total": small_total,
                "large_payment": large_amount,
                "large_total": large_total,
                "consistent": consistency_check,
                "success": consistency_check
            })
            
            print(f"      Small payments total: {small_total}")
            print(f"      Large payment total: {large_total}")
            print(f"      Consistent: {'✅' if consistency_check else '❌'}")
        
        # Operation 2: Addition and subtraction should be inverse operations
        print(f"   Operation 2: Addition/subtraction inverse operations")
        
        # Reset balance
        current_balance = await self.get_employee_balance(employee_id)
        if current_balance and current_balance['breakfast_balance'] != 0:
            reset_amount = -current_balance['breakfast_balance']
            await self.make_flexible_payment(employee_id, department_id, "breakfast", reset_amount, "Reset")
        
        # Add amount
        test_amount = 12.345
        await self.make_flexible_payment(employee_id, department_id, "breakfast", test_amount, "Add amount")
        
        # Subtract same amount
        await self.make_flexible_payment(employee_id, department_id, "breakfast", -test_amount, "Subtract amount")
        
        final_balance = await self.get_employee_balance(employee_id)
        if final_balance:
            is_zero = abs(final_balance['breakfast_balance']) < 0.001
            
            test_operations.append({
                "operation": "Addition/subtraction inverse",
                "test_amount": test_amount,
                "final_balance": final_balance['breakfast_balance'],
                "is_zero": is_zero,
                "success": is_zero
            })
            
            print(f"      Test amount: ±{test_amount}")
            print(f"      Final balance: {final_balance['breakfast_balance']}")
            print(f"      Is zero: {'✅' if is_zero else '❌'}")
        
        # Summary
        passed = sum(1 for op in test_operations if op['success'])
        total = len(test_operations)
        
        return {
            "test": "mathematical consistency",
            "success": passed == total,
            "passed": passed,
            "total": total,
            "operations": test_operations,
            "employee_id": employee_id
        }
    
    async def run_comprehensive_balance_rounding_test(self):
        """Run comprehensive balance rounding test suite"""
        print("🚀 STARTING BALANCE ROUNDING FIX COMPREHENSIVE TEST")
        print("=" * 80)
        print("TESTING: Balance rounding fix to ensure floating-point precision issues are resolved")
        print("- Function: round_to_cents() for various scenarios")
        print("- Balance calculations in order processing using proper rounding")
        print("- Edge cases like -0.00, 8.999999, 0.000001, etc.")
        print("- Verify balances are consistently rounded to 2 decimal places")
        print("- Test that negative zero (-0.00) is converted to positive zero (0.00)")
        print("=" * 80)
        
        # Authenticate as admin for test operations
        auth_result = await self.authenticate_admin("1. Wachabteilung", "admin1")
        if not auth_result:
            print("❌ Failed to authenticate as admin")
            return False
        
        # Run all test cases
        test_results = []
        
        try:
            # Test Case 1: round_to_cents function
            result_1 = await self.test_round_to_cents_function()
            test_results.append(result_1)
            
            # Test Case 2: Order balance rounding
            result_2 = await self.test_order_balance_rounding()
            test_results.append(result_2)
            
            # Test Case 3: Payment balance rounding
            result_3 = await self.test_payment_balance_rounding()
            test_results.append(result_3)
            
            # Test Case 4: Negative zero handling
            result_4 = await self.test_negative_zero_handling()
            test_results.append(result_4)
            
            # Test Case 5: Edge cases
            result_5 = await self.test_edge_cases()
            test_results.append(result_5)
            
            # Test Case 6: Mathematical consistency
            result_6 = await self.test_mathematical_consistency()
            test_results.append(result_6)
            
        except Exception as e:
            print(f"❌ Test execution failed: {str(e)}")
            traceback.print_exc()
            return False
        
        # Analyze results
        total_tests = len(test_results)
        successful_tests = sum(1 for result in test_results if result.get('success', False))
        failed_tests = [result for result in test_results if not result.get('success', False)]
        
        print(f"\n{'='*80}")
        print(f"🎯 BALANCE ROUNDING TEST RESULTS ANALYSIS")
        print(f"{'='*80}")
        
        for result in test_results:
            test_name = result['test']
            success = result.get('success', False)
            passed = result.get('passed', 0)
            total = result.get('total', 0)
            
            print(f"\n📋 TEST: {test_name}")
            print(f"   Result: {'✅ PASSED' if success else '❌ FAILED'}")
            if 'passed' in result and 'total' in result:
                print(f"   Sub-tests: {passed}/{total} passed")
            
            if not success and 'error' in result:
                print(f"   🚨 ERROR: {result['error']}")
        
        # Final analysis
        success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL ANALYSIS - BALANCE ROUNDING FIX")
        print(f"{'='*80}")
        print(f"Total Test Cases: {total_tests}")
        print(f"Successful Tests: {successful_tests}")
        print(f"Failed Tests: {len(failed_tests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if successful_tests == total_tests:
            print(f"\n🎉 ALL BALANCE ROUNDING TESTS PASSED!")
            print(f"✅ The round_to_cents() function is working correctly")
            print(f"✅ Balance calculations in order processing use proper rounding")
            print(f"✅ Edge cases like -0.00, 8.999999, 0.000001 are handled correctly")
            print(f"✅ Balances are consistently rounded to 2 decimal places")
            print(f"✅ Negative zero (-0.00) is converted to positive zero (0.00)")
            print(f"✅ Order creation with balance deduction uses rounding")
            print(f"✅ Payment processing with balance addition uses rounding")
            print(f"✅ Mathematical consistency is maintained across all operations")
            print(f"✅ Balance rounding fix is FULLY FUNCTIONAL")
        else:
            print(f"\n🚨 BALANCE ROUNDING ISSUES DETECTED!")
            print(f"❌ {len(failed_tests)} test cases failed")
            print(f"❌ This may cause floating-point precision errors")
            
            # Identify patterns in failures
            print(f"\n🔍 FAILURE PATTERN ANALYSIS:")
            for result in failed_tests:
                test_name = result['test']
                error = result.get('error', 'Test failed')
                print(f"   - {test_name}: {error}")
            
            print(f"\n💡 RECOMMENDED INVESTIGATION:")
            print(f"   1. Check round_to_cents() function implementation")
            print(f"   2. Verify all balance update operations use round_to_cents()")
            print(f"   3. Test floating-point precision handling")
            print(f"   4. Confirm negative zero handling")
            print(f"   5. Validate mathematical consistency in operations")
        
        return successful_tests == total_tests

async def main():
    """Main test execution"""
    async with BalanceRoundingTester() as tester:
        success = await tester.run_comprehensive_balance_rounding_test()
        return success

if __name__ == "__main__":
    print("Balance Rounding Fix Test Suite")
    print("=" * 50)
    
    try:
        result = asyncio.run(main())
        exit_code = 0 if result else 1
        print(f"\nTest completed with exit code: {exit_code}")
        exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️ Test interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n💥 Test failed with exception: {str(e)}")
        traceback.print_exc()
        exit(1)