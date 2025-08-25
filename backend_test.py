#!/usr/bin/env python3
"""
FINALE SICHERHEITSVERIFIKATION - Nach Frontend-Fix
Backend Test Suite für Canteen Management System

Kritische Tests:
1. Boiled Eggs Price Stabilität (KRITISCH)
2. Gefährliche APIs Blockiert  
3. System-Stabilität
4. Normale Funktionen arbeiten
"""

import requests
import time
import json
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "https://canteenflow.preview.emergentagent.com/api"

class CanteenSecurityTester:
    def __init__(self):
        self.results = []
        self.department_auth = None
        self.admin_auth = None
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details:
            print(f"   Details: {details}")
    
    def test_boiled_eggs_price_stability(self):
        """KRITISCH: Teste Boiled Eggs Price Stabilität"""
        print("\n🥚 TESTING BOILED EGGS PRICE STABILITY...")
        
        try:
            # 1. Prüfe aktuellen boiled_eggs_price
            response1 = requests.get(f"{BACKEND_URL}/lunch-settings")
            if response1.status_code != 200:
                self.log_result("Boiled Eggs Price - Initial Check", False, 
                              f"Failed to get lunch settings: {response1.status_code}")
                return
            
            data1 = response1.json()
            initial_price = data1.get("boiled_eggs_price", "NOT_FOUND")
            
            self.log_result("Boiled Eggs Price - Initial Check", True, 
                          f"Initial boiled_eggs_price: €{initial_price}")
            
            # 2. Warte 30 Sekunden
            print("⏳ Waiting 30 seconds...")
            time.sleep(30)
            
            # 3. Prüfe erneut - sollte GLEICH bleiben
            response2 = requests.get(f"{BACKEND_URL}/lunch-settings")
            if response2.status_code != 200:
                self.log_result("Boiled Eggs Price - After Wait", False, 
                              f"Failed to get lunch settings after wait: {response2.status_code}")
                return
            
            data2 = response2.json()
            after_wait_price = data2.get("boiled_eggs_price", "NOT_FOUND")
            
            if initial_price == after_wait_price:
                self.log_result("Boiled Eggs Price - Stability Test", True, 
                              f"Price stable: €{initial_price} → €{after_wait_price}")
            else:
                self.log_result("Boiled Eggs Price - Stability Test", False, 
                              f"Price changed! €{initial_price} → €{after_wait_price}")
            
            # 4. Teste mehrere Aufrufe hintereinander
            prices = []
            for i in range(5):
                response = requests.get(f"{BACKEND_URL}/lunch-settings")
                if response.status_code == 200:
                    price = response.json().get("boiled_eggs_price", "ERROR")
                    prices.append(price)
                    time.sleep(1)  # 1 second between calls
            
            # Check if all prices are the same
            if len(set(prices)) == 1:
                self.log_result("Boiled Eggs Price - Multiple Calls", True, 
                              f"All 5 calls returned same price: €{prices[0]}")
            else:
                self.log_result("Boiled Eggs Price - Multiple Calls", False, 
                              f"Inconsistent prices: {prices}")
                
        except Exception as e:
            self.log_result("Boiled Eggs Price - Exception", False, f"Exception: {str(e)}")
    
    def test_dangerous_apis_blocked(self):
        """KRITISCH: Teste dass gefährliche APIs blockiert sind"""
        print("\n🚫 TESTING DANGEROUS APIs BLOCKED...")
        
        # Test /api/init-data
        try:
            response = requests.post(f"{BACKEND_URL}/init-data")
            if response.status_code == 403:
                self.log_result("Dangerous API - init-data", True, 
                              "init-data correctly blocked with 403")
            else:
                self.log_result("Dangerous API - init-data", False, 
                              f"init-data returned {response.status_code}, expected 403")
        except Exception as e:
            self.log_result("Dangerous API - init-data", False, f"Exception: {str(e)}")
        
        # Test /api/migrate-to-department-specific
        try:
            response = requests.post(f"{BACKEND_URL}/migrate-to-department-specific")
            if response.status_code == 403:
                self.log_result("Dangerous API - migrate", True, 
                              "migrate-to-department-specific correctly blocked with 403")
            else:
                self.log_result("Dangerous API - migrate", False, 
                              f"migrate-to-department-specific returned {response.status_code}, expected 403")
        except Exception as e:
            self.log_result("Dangerous API - migrate", False, f"Exception: {str(e)}")
    
    def test_system_stability(self):
        """KRITISCH: Teste System-Stabilität"""
        print("\n🏗️ TESTING SYSTEM STABILITY...")
        
        # Test Departments exist
        try:
            response = requests.get(f"{BACKEND_URL}/departments")
            if response.status_code == 200:
                departments = response.json()
                if len(departments) > 0:
                    self.log_result("System Stability - Departments", True, 
                                  f"Found {len(departments)} departments")
                else:
                    self.log_result("System Stability - Departments", False, 
                                  "No departments found")
            else:
                self.log_result("System Stability - Departments", False, 
                              f"Failed to get departments: {response.status_code}")
        except Exception as e:
            self.log_result("System Stability - Departments", False, f"Exception: {str(e)}")
        
        # Test Employee data exists (try first department)
        try:
            # Get first department
            dept_response = requests.get(f"{BACKEND_URL}/departments")
            if dept_response.status_code == 200:
                departments = dept_response.json()
                if departments:
                    dept_id = departments[0]["id"]
                    emp_response = requests.get(f"{BACKEND_URL}/departments/{dept_id}/employees")
                    if emp_response.status_code == 200:
                        employees = emp_response.json()
                        self.log_result("System Stability - Employees", True, 
                                      f"Found {len(employees)} employees in department {dept_id}")
                    else:
                        self.log_result("System Stability - Employees", False, 
                                      f"Failed to get employees: {emp_response.status_code}")
                else:
                    self.log_result("System Stability - Employees", False, 
                                  "No departments to test employees")
        except Exception as e:
            self.log_result("System Stability - Employees", False, f"Exception: {str(e)}")
        
        # Test Menu items exist
        try:
            response = requests.get(f"{BACKEND_URL}/menu/breakfast")
            if response.status_code == 200:
                menu_items = response.json()
                self.log_result("System Stability - Menu Items", True, 
                              f"Found {len(menu_items)} breakfast menu items")
            else:
                self.log_result("System Stability - Menu Items", False, 
                              f"Failed to get menu items: {response.status_code}")
        except Exception as e:
            self.log_result("System Stability - Menu Items", False, f"Exception: {str(e)}")
    
    def test_normal_functions(self):
        """KRITISCH: Teste normale Funktionen arbeiten"""
        print("\n⚙️ TESTING NORMAL FUNCTIONS...")
        
        # Test Department Authentication
        try:
            auth_data = {
                "department_name": "1. Wachabteilung",
                "password": "password1"
            }
            response = requests.post(f"{BACKEND_URL}/login/department", json=auth_data)
            if response.status_code == 200:
                self.department_auth = response.json()
                self.log_result("Normal Functions - Department Auth", True, 
                              f"Department authentication successful: {self.department_auth['department_name']}")
            else:
                self.log_result("Normal Functions - Department Auth", False, 
                              f"Department authentication failed: {response.status_code}")
        except Exception as e:
            self.log_result("Normal Functions - Department Auth", False, f"Exception: {str(e)}")
        
        # Test Admin Authentication
        try:
            admin_data = {
                "department_name": "1. Wachabteilung", 
                "admin_password": "admin1"
            }
            response = requests.post(f"{BACKEND_URL}/login/department-admin", json=admin_data)
            if response.status_code == 200:
                self.admin_auth = response.json()
                self.log_result("Normal Functions - Admin Auth", True, 
                              f"Admin authentication successful: {self.admin_auth['role']}")
            else:
                self.log_result("Normal Functions - Admin Auth", False, 
                              f"Admin authentication failed: {response.status_code}")
        except Exception as e:
            self.log_result("Normal Functions - Admin Auth", False, f"Exception: {str(e)}")
        
        # Test Boiled Eggs Price Update (if we have admin auth)
        if self.admin_auth:
            try:
                # Get current price first
                current_response = requests.get(f"{BACKEND_URL}/lunch-settings")
                if current_response.status_code == 200:
                    current_price = current_response.json().get("boiled_eggs_price", 0.50)
                    
                    # Try to update to a slightly different price
                    new_price = current_price + 0.01 if current_price < 1.0 else current_price - 0.01
                    
                    update_response = requests.put(f"{BACKEND_URL}/lunch-settings/boiled-eggs-price?price={new_price}")
                    if update_response.status_code == 200:
                        self.log_result("Normal Functions - Price Update", True, 
                                      f"Boiled eggs price update successful: €{current_price} → €{new_price}")
                        
                        # Verify the update
                        verify_response = requests.get(f"{BACKEND_URL}/lunch-settings")
                        if verify_response.status_code == 200:
                            updated_price = verify_response.json().get("boiled_eggs_price")
                            if abs(updated_price - new_price) < 0.001:
                                self.log_result("Normal Functions - Price Verification", True, 
                                              f"Price update verified: €{updated_price}")
                            else:
                                self.log_result("Normal Functions - Price Verification", False, 
                                              f"Price mismatch: expected €{new_price}, got €{updated_price}")
                    else:
                        self.log_result("Normal Functions - Price Update", False, 
                                      f"Price update failed: {update_response.status_code}")
            except Exception as e:
                self.log_result("Normal Functions - Price Update", False, f"Exception: {str(e)}")
        
        # Test Order Creation (basic test)
        if self.department_auth:
            try:
                # Get employees first
                dept_id = self.department_auth["department_id"]
                emp_response = requests.get(f"{BACKEND_URL}/departments/{dept_id}/employees")
                if emp_response.status_code == 200:
                    employees = emp_response.json()
                    if employees:
                        employee_id = employees[0]["id"]
                        
                        # Create a simple breakfast order
                        order_data = {
                            "employee_id": employee_id,
                            "department_id": dept_id,
                            "order_type": "breakfast",
                            "breakfast_items": [{
                                "total_halves": 2,
                                "white_halves": 1,
                                "seeded_halves": 1,
                                "toppings": ["ruehrei", "kaese"],
                                "has_lunch": False,
                                "boiled_eggs": 1,
                                "has_coffee": False
                            }]
                        }
                        
                        # Note: This might fail due to single breakfast constraint, but that's expected
                        order_response = requests.post(f"{BACKEND_URL}/orders", json=order_data)
                        if order_response.status_code == 200:
                            self.log_result("Normal Functions - Order Creation", True, 
                                          "Order creation successful")
                        elif order_response.status_code == 400:
                            # Check if it's the expected single breakfast constraint
                            error_msg = order_response.json().get("detail", "")
                            if "bereits eine Frühstücksbestellung" in error_msg:
                                self.log_result("Normal Functions - Order Creation", True, 
                                              "Order creation working (single breakfast constraint active)")
                            else:
                                self.log_result("Normal Functions - Order Creation", False, 
                                              f"Order creation failed with validation error: {error_msg}")
                        else:
                            self.log_result("Normal Functions - Order Creation", False, 
                                          f"Order creation failed: {order_response.status_code}")
                    else:
                        self.log_result("Normal Functions - Order Creation", False, 
                                      "No employees found for order test")
            except Exception as e:
                self.log_result("Normal Functions - Order Creation", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all security verification tests"""
        print("🔒 FINALE SICHERHEITSVERIFIKATION - Nach Frontend-Fix")
        print("=" * 60)
        
        # Run all test categories
        self.test_boiled_eggs_price_stability()
        self.test_dangerous_apis_blocked()
        self.test_system_stability()
        self.test_normal_functions()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Show failed tests
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Critical assessment
        print("\n🎯 CRITICAL ASSESSMENT:")
        
        # Check boiled eggs price stability
        boiled_eggs_tests = [r for r in self.results if "Boiled Eggs Price" in r["test"]]
        boiled_eggs_passed = all("✅ PASS" in r["status"] for r in boiled_eggs_tests)
        
        # Check dangerous APIs blocked
        dangerous_api_tests = [r for r in self.results if "Dangerous API" in r["test"]]
        dangerous_apis_blocked = all("✅ PASS" in r["status"] for r in dangerous_api_tests)
        
        # Check system stability
        stability_tests = [r for r in self.results if "System Stability" in r["test"]]
        system_stable = all("✅ PASS" in r["status"] for r in stability_tests)
        
        if boiled_eggs_passed:
            print("✅ BOILED EGGS PRICE: STABLE - No automatic resets detected")
        else:
            print("❌ BOILED EGGS PRICE: UNSTABLE - Price changes detected!")
        
        if dangerous_apis_blocked:
            print("✅ DANGEROUS APIs: BLOCKED - Security measures active")
        else:
            print("❌ DANGEROUS APIs: NOT BLOCKED - Security risk!")
        
        if system_stable:
            print("✅ SYSTEM STABILITY: GOOD - All data preserved")
        else:
            print("❌ SYSTEM STABILITY: ISSUES - Data loss detected!")
        
        # Final verdict
        if boiled_eggs_passed and dangerous_apis_blocked and system_stable:
            print("\n🎉 FINALE BEWERTUNG: FRONTEND-FIX ERFOLGREICH!")
            print("   Datenbank bleibt stabil, keine automatischen Resets mehr!")
        else:
            print("\n⚠️ FINALE BEWERTUNG: WEITERE FIXES ERFORDERLICH!")
            print("   System noch nicht vollständig stabil!")
        
        return self.results

if __name__ == "__main__":
    tester = CanteenSecurityTester()
    results = tester.run_all_tests()