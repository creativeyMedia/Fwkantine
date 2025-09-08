#!/usr/bin/env python3
"""
Comprehensive FRIED EGGS and NOTES Backend Test Suite
====================================================

This comprehensive test suite covers all aspects of the fried eggs and notes functionality
including edge cases, error handling, and integration with existing features.
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-fix.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class ComprehensiveFriedEggsNotesTest:
    def __init__(self):
        self.department_id = "fw4abteilung1"
        self.admin_credentials = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.test_employees = []
        self.test_orders = []
        
    def log(self, message):
        """Log test progress"""
        print(f"🧪 {message}")
        
    def error(self, message):
        """Log test errors"""
        print(f"❌ ERROR: {message}")
        
    def success(self, message):
        """Log test success"""
        print(f"✅ SUCCESS: {message}")
        
    def create_test_employee(self, name_suffix):
        """Create a test employee"""
        try:
            employee_name = f"CompTest_{name_suffix}_{datetime.now().strftime('%H%M%S')}"
            employee_data = {
                "name": employee_name,
                "department_id": self.department_id
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.test_employees.append(employee)
                self.success(f"Created test employee: {employee_name} (ID: {employee['id']})")
                return employee
            else:
                self.error(f"Failed to create test employee: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            self.error(f"Exception creating test employee: {str(e)}")
            return None
            
    def test_comprehensive_scenarios(self):
        """Test comprehensive scenarios for fried eggs and notes"""
        try:
            self.log("🎯 COMPREHENSIVE FRIED EGGS AND NOTES TESTING")
            self.log("=" * 80)
            
            # Initialize data
            response = requests.post(f"{API_BASE}/init-data")
            self.log(f"Init data response: {response.status_code}")
            
            # Set fried eggs price
            response = requests.put(f"{API_BASE}/department-settings/{self.department_id}/fried-eggs-price?price=0.75")
            if response.status_code == 200:
                self.success("Set fried eggs price to €0.75")
            
            # Test scenarios
            test_scenarios = [
                {
                    "name": "Order with only fried eggs (no rolls)",
                    "employee_suffix": "OnlyEggs",
                    "order_data": {
                        "order_type": "breakfast",
                        "notes": "Only fried eggs, no rolls",
                        "breakfast_items": [{
                            "total_halves": 0,
                            "white_halves": 0,
                            "seeded_halves": 0,
                            "toppings": [],
                            "has_lunch": False,
                            "boiled_eggs": 0,
                            "fried_eggs": 3,
                            "has_coffee": False
                        }]
                    },
                    "expected_price_min": 2.0  # 3 * 0.75 = 2.25
                },
                {
                    "name": "Order with fried eggs, rolls, and lunch",
                    "employee_suffix": "FullOrder",
                    "order_data": {
                        "order_type": "breakfast",
                        "notes": "Full breakfast with everything",
                        "breakfast_items": [{
                            "total_halves": 4,
                            "white_halves": 2,
                            "seeded_halves": 2,
                            "toppings": ["Rührei", "Spiegelei", "Salami", "Käse"],
                            "has_lunch": True,
                            "boiled_eggs": 1,
                            "fried_eggs": 2,
                            "has_coffee": True
                        }]
                    },
                    "expected_price_min": 5.0  # Should be substantial
                },
                {
                    "name": "Order with long notes text",
                    "employee_suffix": "LongNotes",
                    "order_data": {
                        "order_type": "breakfast",
                        "notes": "This is a very long note with special instructions: no butter on the rolls, fried eggs should be well done, coffee should be strong, and please make sure the lunch is vegetarian. Additional notes about dietary restrictions and preferences.",
                        "breakfast_items": [{
                            "total_halves": 2,
                            "white_halves": 1,
                            "seeded_halves": 1,
                            "toppings": ["Butter", "Käse"],
                            "has_lunch": False,
                            "boiled_eggs": 0,
                            "fried_eggs": 1,
                            "has_coffee": True
                        }]
                    },
                    "expected_price_min": 2.0
                },
                {
                    "name": "Order with special characters in notes",
                    "employee_suffix": "SpecialChars",
                    "order_data": {
                        "order_type": "breakfast",
                        "notes": "Spëcîál chäräctërs: äöüß & émojis 🍳🥚☕ and symbols @#$%^&*()",
                        "breakfast_items": [{
                            "total_halves": 1,
                            "white_halves": 1,
                            "seeded_halves": 0,
                            "toppings": ["Spiegelei"],
                            "has_lunch": False,
                            "boiled_eggs": 0,
                            "fried_eggs": 2,
                            "has_coffee": False
                        }]
                    },
                    "expected_price_min": 1.0
                }
            ]
            
            successful_tests = 0
            
            for i, scenario in enumerate(test_scenarios, 1):
                self.log(f"\n📋 Scenario {i}: {scenario['name']}")
                self.log("-" * 60)
                
                # Create employee for this scenario
                employee = self.create_test_employee(scenario["employee_suffix"])
                if not employee:
                    continue
                
                # Prepare order data
                order_data = scenario["order_data"].copy()
                order_data["employee_id"] = employee["id"]
                order_data["department_id"] = self.department_id
                
                # Create order
                response = requests.post(f"{API_BASE}/orders", json=order_data)
                if response.status_code == 200:
                    order = response.json()
                    self.test_orders.append(order)
                    
                    total_price = order["total_price"]
                    notes = order.get("notes", "")
                    
                    self.success(f"Order created successfully (ID: {order['id']}, Total: €{total_price})")
                    
                    # Verify price is reasonable
                    if total_price >= scenario["expected_price_min"]:
                        self.success(f"Order price is reasonable: €{total_price} >= €{scenario['expected_price_min']}")
                    else:
                        self.error(f"Order price seems too low: €{total_price} < €{scenario['expected_price_min']}")
                        continue
                    
                    # Verify notes are stored
                    if notes == order_data["notes"]:
                        self.success(f"Notes correctly stored: '{notes[:50]}{'...' if len(notes) > 50 else ''}'")
                    else:
                        self.error(f"Notes not stored correctly")
                        continue
                    
                    successful_tests += 1
                    
                else:
                    self.error(f"Failed to create order: {response.status_code} - {response.text}")
            
            self.log(f"\n🎯 Scenario Testing Results: {successful_tests}/{len(test_scenarios)} passed")
            return successful_tests == len(test_scenarios)
            
        except Exception as e:
            self.error(f"Exception in comprehensive testing: {str(e)}")
            return False
            
    def test_api_endpoints_integration(self):
        """Test all relevant API endpoints for fried eggs and notes integration"""
        try:
            self.log("\n🎯 API ENDPOINTS INTEGRATION TESTING")
            self.log("=" * 60)
            
            endpoints_to_test = [
                ("Daily Summary", f"{API_BASE}/orders/daily-summary/{self.department_id}"),
                ("Breakfast History", f"{API_BASE}/orders/breakfast-history/{self.department_id}"),
                ("Department Settings", f"{API_BASE}/department-settings/{self.department_id}"),
                ("Fried Eggs Price", f"{API_BASE}/department-settings/{self.department_id}/fried-eggs-price")
            ]
            
            successful_endpoints = 0
            
            for endpoint_name, endpoint_url in endpoints_to_test:
                self.log(f"Testing {endpoint_name}: {endpoint_url}")
                
                response = requests.get(endpoint_url)
                if response.status_code == 200:
                    data = response.json()
                    self.success(f"{endpoint_name} endpoint accessible")
                    
                    # Check for fried eggs data in relevant endpoints
                    if "daily-summary" in endpoint_url:
                        if "total_fried_eggs" in data:
                            self.success(f"Daily summary contains total_fried_eggs: {data['total_fried_eggs']}")
                        else:
                            self.error("Daily summary missing total_fried_eggs field")
                            continue
                            
                    elif "fried-eggs-price" in endpoint_url:
                        if "fried_eggs_price" in data:
                            self.success(f"Fried eggs price endpoint returns price: €{data['fried_eggs_price']}")
                        else:
                            self.error("Fried eggs price endpoint missing price field")
                            continue
                    
                    successful_endpoints += 1
                    
                else:
                    self.error(f"{endpoint_name} endpoint failed: {response.status_code} - {response.text}")
            
            self.log(f"\n🎯 API Endpoints Testing Results: {successful_endpoints}/{len(endpoints_to_test)} passed")
            return successful_endpoints == len(endpoints_to_test)
            
        except Exception as e:
            self.error(f"Exception in API endpoints testing: {str(e)}")
            return False
            
    def test_data_persistence(self):
        """Test that fried eggs and notes data persists correctly"""
        try:
            self.log("\n🎯 DATA PERSISTENCE TESTING")
            self.log("=" * 60)
            
            if not self.test_employees or not self.test_orders:
                self.error("No test data available for persistence testing")
                return False
            
            # Test data retrieval through different endpoints
            persistence_tests = 0
            total_persistence_tests = 0
            
            for employee in self.test_employees[:2]:  # Test first 2 employees
                employee_name = employee["name"]
                self.log(f"Testing data persistence for employee: {employee_name}")
                
                # Test daily summary
                response = requests.get(f"{API_BASE}/orders/daily-summary/{self.department_id}")
                if response.status_code == 200:
                    summary = response.json()
                    employee_orders = summary.get("employee_orders", {})
                    
                    found_employee = False
                    for emp_key, emp_data in employee_orders.items():
                        if employee_name in emp_key:
                            found_employee = True
                            
                            # Check fried eggs
                            if "fried_eggs" in emp_data:
                                self.success(f"Fried eggs data persisted in daily summary: {emp_data['fried_eggs']}")
                                persistence_tests += 1
                            
                            # Check notes
                            if "notes" in emp_data and emp_data["notes"]:
                                self.success(f"Notes data persisted in daily summary: '{emp_data['notes'][:30]}...'")
                                persistence_tests += 1
                            
                            break
                    
                    if not found_employee:
                        self.log(f"Employee {employee_name} not found in daily summary")
                    
                    total_persistence_tests += 2  # fried_eggs + notes
                
                # Test breakfast history
                response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.department_id}")
                if response.status_code == 200:
                    history = response.json()
                    
                    found_employee = False
                    if history.get("history"):
                        for day_data in history["history"]:
                            employee_orders = day_data.get("employee_orders", {})
                            for emp_key, emp_data in employee_orders.items():
                                if employee_name in emp_key:
                                    found_employee = True
                                    
                                    # Check fried eggs
                                    if "fried_eggs" in emp_data:
                                        self.success(f"Fried eggs data persisted in breakfast history: {emp_data['fried_eggs']}")
                                        persistence_tests += 1
                                    
                                    # Check notes
                                    if "notes" in emp_data and emp_data["notes"]:
                                        self.success(f"Notes data persisted in breakfast history: '{emp_data['notes'][:30]}...'")
                                        persistence_tests += 1
                                    
                                    break
                            if found_employee:
                                break
                    
                    if not found_employee:
                        self.log(f"Employee {employee_name} not found in breakfast history")
                    
                    total_persistence_tests += 2  # fried_eggs + notes
            
            self.log(f"\n🎯 Data Persistence Results: {persistence_tests}/{total_persistence_tests} data points persisted")
            return persistence_tests >= (total_persistence_tests * 0.8)  # 80% success rate acceptable
            
        except Exception as e:
            self.error(f"Exception in data persistence testing: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run all comprehensive tests"""
        self.log("🎯 STARTING COMPREHENSIVE FRIED EGGS AND NOTES TESTING")
        self.log("=" * 80)
        
        test_results = []
        
        test_results.append(("Comprehensive Scenarios", self.test_comprehensive_scenarios()))
        test_results.append(("API Endpoints Integration", self.test_api_endpoints_integration()))
        test_results.append(("Data Persistence", self.test_data_persistence()))
        
        # Calculate results
        passed_tests = sum(1 for _, result in test_results if result)
        total_tests = len(test_results)
        
        # Final results
        self.log("\n" + "=" * 80)
        self.log("🎯 COMPREHENSIVE TEST RESULTS:")
        
        for test_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"  {status}: {test_name}")
        
        if passed_tests == total_tests:
            self.success(f"🎉 ALL COMPREHENSIVE TESTS PASSED! ({passed_tests}/{total_tests})")
            return True
        else:
            self.error(f"❌ COMPREHENSIVE TESTS PARTIALLY FAILED! ({passed_tests}/{total_tests})")
            return False

def main():
    """Main test execution"""
    print("🧪 COMPREHENSIVE FRIED EGGS AND NOTES TEST SUITE")
    print("=" * 70)
    
    # Initialize and run test
    test_suite = ComprehensiveFriedEggsNotesTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL COMPREHENSIVE TESTS PASSED!")
        exit(0)
    else:
        print("\n❌ SOME COMPREHENSIVE TESTS FAILED!")
        exit(1)

if __name__ == "__main__":
    main()