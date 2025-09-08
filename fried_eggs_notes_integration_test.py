#!/usr/bin/env python3
"""
FRIED EGGS and NOTES Integration Test Suite
==========================================

This test suite specifically tests the BACKEND FIXES for FRIED EGGS and NOTES integration
as requested in the review request:

1. **DAILY SUMMARY INTEGRATION TEST:**
   - Create a test order with both fried_eggs: 2 and notes: "Test notes for summary"
   - Call GET /api/orders/daily-summary/fw4abteilung1 
   - Verify response includes:
     * total_fried_eggs field
     * employee_orders contains fried_eggs per employee
     * employee_orders contains notes per employee

2. **BREAKFAST HISTORY INTEGRATION TEST:**
   - Call GET /api/orders/breakfast-history/fw4abteilung1
   - Verify response includes:
     * fried_eggs per employee in employee_orders
     * notes per employee in employee_orders

3. **OBJECT DISPLAY BUG INVESTIGATION:**
   - Check if toppings are returned in correct format
   - Verify toppings structure matches expected {white: X, seeded: Y} format
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class FriedEggsNotesIntegrationTest:
    def __init__(self):
        self.department_id = "fw4abteilung1"
        self.admin_credentials = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.test_employee_id = None
        self.test_employee_name = f"IntegrationTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_order_id = None
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        
    def setup_test_environment(self):
        """Setup test environment with employee and order"""
        try:
            # 1. Initialize data
            self.log("Setting up test environment...")
            response = requests.post(f"{API_BASE}/init-data")
            self.log(f"Init data response: {response.status_code}")
            
            # 2. Create test employee
            employee_data = {
                "name": self.test_employee_name,
                "department_id": self.department_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employee_id = employee["id"]
                self.success(f"Created test employee: {self.test_employee_name} (ID: {self.test_employee_id})")
            else:
                self.error(f"Failed to create test employee: {response.status_code} - {response.text}")
                return False
                
            # 3. Set fried eggs price to ensure consistent testing
            response = requests.put(f"{API_BASE}/department-settings/{self.department_id}/fried-eggs-price?price=0.75")
            if response.status_code == 200:
                self.success("Set fried eggs price to €0.75")
            else:
                self.log(f"Warning: Could not set fried eggs price: {response.status_code}")
                
            return True
            
        except Exception as e:
            self.error(f"Exception during setup: {str(e)}")
            return False
            
    def test_1_daily_summary_integration(self):
        """
        DAILY SUMMARY INTEGRATION TEST:
        - Create a test order with both fried_eggs: 2 and notes: "Test notes for summary"
        - Call GET /api/orders/daily-summary/fw4abteilung1 
        - Verify response includes total_fried_eggs, fried_eggs per employee, notes per employee
        """
        try:
            self.log("🎯 TEST 1: DAILY SUMMARY INTEGRATION TEST")
            self.log("=" * 60)
            
            # Create order with both fried eggs and notes
            order_data = {
                "employee_id": self.test_employee_id,
                "department_id": self.department_id,
                "order_type": "breakfast",
                "notes": "Test notes for summary",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["Rührei", "Spiegelei"],
                    "has_lunch": False,
                    "boiled_eggs": 0,
                    "fried_eggs": 2,  # Test fried eggs integration
                    "has_coffee": True
                }]
            }
            
            self.log("Creating order with fried_eggs: 2 and notes: 'Test notes for summary'")
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.test_order_id = order["id"]
                self.success(f"Created test order (ID: {order['id']}, Total: €{order['total_price']})")
            else:
                self.error(f"Failed to create test order: {response.status_code} - {response.text}")
                return False
                
            # Test daily summary endpoint
            self.log("Testing GET /api/orders/daily-summary/fw4abteilung1")
            
            response = requests.get(f"{API_BASE}/orders/daily-summary/{self.department_id}")
            if response.status_code == 200:
                summary = response.json()
                self.success("Daily summary endpoint accessible")
                
                # Verify total_fried_eggs field exists
                total_fried_eggs = summary.get("total_fried_eggs")
                if total_fried_eggs is not None:
                    self.success(f"✅ total_fried_eggs field present: {total_fried_eggs}")
                else:
                    self.error("❌ total_fried_eggs field missing from daily summary")
                    return False
                
                # Verify employee_orders contains fried_eggs per employee
                employee_orders = summary.get("employee_orders", {})
                found_employee_fried_eggs = False
                found_employee_notes = False
                
                for employee_key, employee_data in employee_orders.items():
                    if self.test_employee_name in employee_key:
                        # Check fried_eggs per employee
                        fried_eggs = employee_data.get("fried_eggs")
                        if fried_eggs is not None:
                            self.success(f"✅ employee_orders contains fried_eggs per employee: {fried_eggs}")
                            found_employee_fried_eggs = True
                        
                        # Check notes per employee
                        notes = employee_data.get("notes")
                        if notes is not None:
                            self.success(f"✅ employee_orders contains notes per employee: '{notes}'")
                            found_employee_notes = True
                        
                        break
                
                if not found_employee_fried_eggs:
                    self.error("❌ employee_orders missing fried_eggs per employee")
                    return False
                    
                if not found_employee_notes:
                    self.error("❌ employee_orders missing notes per employee")
                    return False
                
                self.success("🎉 DAILY SUMMARY INTEGRATION TEST PASSED!")
                return True
                
            else:
                self.error(f"Failed to get daily summary: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception in daily summary integration test: {str(e)}")
            return False
            
    def test_2_breakfast_history_integration(self):
        """
        BREAKFAST HISTORY INTEGRATION TEST:
        - Call GET /api/orders/breakfast-history/fw4abteilung1
        - Verify response includes fried_eggs per employee and notes per employee
        """
        try:
            self.log("\n🎯 TEST 2: BREAKFAST HISTORY INTEGRATION TEST")
            self.log("=" * 60)
            
            # Test breakfast history endpoint
            self.log("Testing GET /api/orders/breakfast-history/fw4abteilung1")
            
            response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.department_id}")
            if response.status_code == 200:
                history_data = response.json()
                self.success("Breakfast history endpoint accessible")
                
                # Look for our test employee in the history
                found_employee_fried_eggs = False
                found_employee_notes = False
                
                if history_data.get("history"):
                    for day_data in history_data["history"]:
                        employee_orders = day_data.get("employee_orders", {})
                        for employee_key, employee_data in employee_orders.items():
                            if self.test_employee_name in employee_key:
                                # Check fried_eggs per employee in breakfast history
                                fried_eggs = employee_data.get("fried_eggs")
                                if fried_eggs is not None:
                                    self.success(f"✅ breakfast-history employee_orders contains fried_eggs: {fried_eggs}")
                                    found_employee_fried_eggs = True
                                
                                # Check notes per employee in breakfast history
                                notes = employee_data.get("notes")
                                if notes is not None:
                                    self.success(f"✅ breakfast-history employee_orders contains notes: '{notes}'")
                                    found_employee_notes = True
                                
                                break
                        if found_employee_fried_eggs and found_employee_notes:
                            break
                
                if not found_employee_fried_eggs:
                    self.error("❌ breakfast-history employee_orders missing fried_eggs per employee")
                    return False
                    
                if not found_employee_notes:
                    self.error("❌ breakfast-history employee_orders missing notes per employee")
                    return False
                
                self.success("🎉 BREAKFAST HISTORY INTEGRATION TEST PASSED!")
                return True
                
            else:
                self.error(f"Failed to get breakfast history: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception in breakfast history integration test: {str(e)}")
            return False
            
    def test_3_object_display_bug_investigation(self):
        """
        OBJECT DISPLAY BUG INVESTIGATION:
        - Check if toppings are returned in correct format
        - Verify toppings structure matches expected {white: X, seeded: Y} format
        """
        try:
            self.log("\n🎯 TEST 3: OBJECT DISPLAY BUG INVESTIGATION")
            self.log("=" * 60)
            
            # Test both daily summary and breakfast history for toppings format
            endpoints_to_test = [
                ("daily-summary", f"{API_BASE}/orders/daily-summary/{self.department_id}"),
                ("breakfast-history", f"{API_BASE}/orders/breakfast-history/{self.department_id}")
            ]
            
            toppings_format_correct = True
            
            for endpoint_name, endpoint_url in endpoints_to_test:
                self.log(f"Testing toppings format in {endpoint_name}")
                
                response = requests.get(endpoint_url)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Look for toppings data in the response
                    found_toppings = False
                    
                    if endpoint_name == "daily-summary":
                        employee_orders = data.get("employee_orders", {})
                    else:  # breakfast-history
                        employee_orders = {}
                        if data.get("history"):
                            for day_data in data["history"]:
                                employee_orders.update(day_data.get("employee_orders", {}))
                    
                    for employee_key, employee_data in employee_orders.items():
                        if self.test_employee_name in employee_key:
                            # Look for toppings data
                            toppings = employee_data.get("toppings")
                            if toppings is not None:
                                found_toppings = True
                                self.log(f"Found toppings data in {endpoint_name}: {toppings}")
                                
                                # Check if toppings are in correct format
                                # Expected format: {'ToppingName': {'white': X, 'seeded': Y}, ...}
                                if isinstance(toppings, dict):
                                    format_valid = True
                                    total_white = 0
                                    total_seeded = 0
                                    
                                    for topping_name, topping_data in toppings.items():
                                        if isinstance(topping_data, dict):
                                            if "white" in topping_data and "seeded" in topping_data:
                                                white_count = topping_data.get("white", 0)
                                                seeded_count = topping_data.get("seeded", 0)
                                                total_white += white_count
                                                total_seeded += seeded_count
                                                self.log(f"  {topping_name}: white={white_count}, seeded={seeded_count}")
                                            else:
                                                format_valid = False
                                                break
                                        else:
                                            format_valid = False
                                            break
                                    
                                    if format_valid:
                                        self.success(f"✅ Toppings in correct format in {endpoint_name}: Total white={total_white}, seeded={total_seeded}")
                                    else:
                                        self.error(f"❌ Toppings format invalid in {endpoint_name}: {toppings}")
                                        toppings_format_correct = False
                                else:
                                    self.error(f"❌ Toppings not in object format in {endpoint_name}: {toppings}")
                                    toppings_format_correct = False
                            break
                    
                    if not found_toppings:
                        self.log(f"No toppings data found for test employee in {endpoint_name}")
                        
                else:
                    self.error(f"Failed to get {endpoint_name}: {response.status_code} - {response.text}")
                    return False
            
            if toppings_format_correct:
                self.success("🎉 OBJECT DISPLAY BUG INVESTIGATION PASSED!")
                return True
            else:
                self.error("❌ OBJECT DISPLAY BUG INVESTIGATION FAILED!")
                return False
                
        except Exception as e:
            self.error(f"Exception in object display bug investigation: {str(e)}")
            return False
            
    def run_integration_tests(self):
        """Run all integration tests"""
        self.log("🎯 STARTING FRIED EGGS AND NOTES INTEGRATION TESTING")
        self.log("=" * 80)
        
        # Setup test environment
        if not self.setup_test_environment():
            self.error("Failed to setup test environment")
            return False
        
        # Run integration tests
        test_results = []
        
        test_results.append(("Daily Summary Integration", self.test_1_daily_summary_integration()))
        test_results.append(("Breakfast History Integration", self.test_2_breakfast_history_integration()))
        test_results.append(("Object Display Bug Investigation", self.test_3_object_display_bug_investigation()))
        
        # Calculate results
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        # Final results
        self.log("\n" + "=" * 80)
        self.log("🎯 INTEGRATION TEST RESULTS:")
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"  {status}: {test_name}")
        
        if passed_tests == total_tests:
            self.success(f"🎉 ALL INTEGRATION TESTS PASSED! ({passed_tests}/{total_tests})")
            self.log("\n🎯 CRITICAL VERIFICATION SUMMARY:")
            self.log("✅ Daily summary includes total_fried_eggs field")
            self.log("✅ Daily summary employee_orders contains fried_eggs per employee")
            self.log("✅ Daily summary employee_orders contains notes per employee")
            self.log("✅ Breakfast history employee_orders contains fried_eggs per employee")
            self.log("✅ Breakfast history employee_orders contains notes per employee")
            self.log("✅ Toppings returned in correct {white: X, seeded: Y} format")
            return True
        else:
            self.error(f"❌ INTEGRATION TESTS PARTIALLY FAILED! ({passed_tests}/{total_tests})")
            return False

def main():
    """Main test execution"""
    print("🧪 FRIED EGGS AND NOTES INTEGRATION TEST SUITE")
    print("=" * 70)
    
    # Initialize and run test
    test_suite = FriedEggsNotesIntegrationTest()
    success = test_suite.run_integration_tests()
    
    if success:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        exit(0)
    else:
        print("\n❌ SOME INTEGRATION TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()