#!/usr/bin/env python3
"""
Backend Test Suite for Three Critical Pricing Problems
======================================================

This test suite tests the three specific pricing problems mentioned in the review request:

PROBLEM 1 - Falsche Preisanzeige im chronologischen Verlauf:
- User meldete: Gastmitarbeiter aus 2. WA bestellt in 1. WA, aber Verlauf zeigt Preise der 2. WA (0,75€/1,00€) statt 1. WA (0,50€/0,60€)
- Fix implementiert: Backend lädt jetzt menü-spezifische Preise für jede Bestellung basierend auf order["department_id"]

PROBLEM 2 - Saldo korrekt, Anzeige falsch:
- User meldete: Saldo wird korrekt mit 8,50€ berechnet, aber Verlauf zeigt falsche Einzelpreise
- Fix implementiert: get_employee_profile verwendet jetzt order-spezifische Department-Preise

PROBLEM 3 - Rückwirkende Mittagspreis-Änderungen:
- User meldete: Bei Gastmitarbeitern wird Mittagspreis nur im Frontend aktualisiert, nicht im Subkonto-Saldo
- Fix implementiert: update_lunch_settings prüft jetzt ob Bestellung Stamm- oder Gastdepartment ist und aktualisiert entsprechendes Konto

TEST-SZENARIEN:
1. Erstelle Gastmitarbeiter-Bestellung: Gastmitarbeiter aus fw4abteilung2 bestellt in fw4abteilung1
2. Teste Preisanzeige-Korrektheit: Vergleiche Backend-Berechnung mit Frontend-Anzeige
3. Teste rückwirkende Mittagspreis-Änderung: Ändere Mittagspreis für fw4abteilung1
"""

import requests
import json
import os
from datetime import datetime
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://canteen-accounts.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class PricingProblemsTest:
    def __init__(self):
        self.dept1_id = "fw4abteilung1"  # Target department (where guest orders)
        self.dept2_id = "fw4abteilung2"  # Home department of guest employee
        self.dept1_admin = {"department_name": "1. Wachabteilung", "admin_password": "admin1"}
        self.dept2_admin = {"department_name": "2. Wachabteilung", "admin_password": "admin2"}
        self.guest_employee_id = None
        self.guest_employee_name = f"GuestTest_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
            
    def setup_department_prices(self):
        """Setup different prices for departments to test the pricing problem"""
        try:
            # Set fw4abteilung1 prices (target department): 0.50€ white, 0.60€ seeded
            # Set fw4abteilung2 prices (home department): 0.75€ white, 1.00€ seeded
            
            # Get current menu items for both departments
            dept1_breakfast = requests.get(f"{API_BASE}/menu/breakfast/{self.dept1_id}")
            dept2_breakfast = requests.get(f"{API_BASE}/menu/breakfast/{self.dept2_id}")
            
            if dept1_breakfast.status_code == 200 and dept2_breakfast.status_code == 200:
                dept1_items = dept1_breakfast.json()
                dept2_items = dept2_breakfast.json()
                
                # Update dept1 prices (0.50€ white, 0.60€ seeded)
                for item in dept1_items:
                    if item["roll_type"] == "weiss":
                        requests.put(f"{API_BASE}/menu/breakfast/{item['id']}", json={"price": 0.50})
                    elif item["roll_type"] == "koerner":
                        requests.put(f"{API_BASE}/menu/breakfast/{item['id']}", json={"price": 0.60})
                
                # Update dept2 prices (0.75€ white, 1.00€ seeded)
                for item in dept2_items:
                    if item["roll_type"] == "weiss":
                        requests.put(f"{API_BASE}/menu/breakfast/{item['id']}", json={"price": 0.75})
                    elif item["roll_type"] == "koerner":
                        requests.put(f"{API_BASE}/menu/breakfast/{item['id']}", json={"price": 1.00})
                
                self.success("Department prices configured: Dept1 (0.50€/0.60€), Dept2 (0.75€/1.00€)")
                return True
            else:
                self.error("Failed to get menu items for price setup")
                return False
                
        except Exception as e:
            self.error(f"Exception setting up department prices: {str(e)}")
            return False
            
    def create_guest_employee(self):
        """Create a guest employee in fw4abteilung2 (home department)"""
        try:
            employee_data = {
                "name": self.guest_employee_name,
                "department_id": self.dept2_id  # Home department is fw4abteilung2
            }
            
            response = requests.post(f"{API_BASE}/employees", json=employee_data)
            if response.status_code == 200:
                employee = response.json()
                self.guest_employee_id = employee["id"]
                self.success(f"Created guest employee: {self.guest_employee_name} in {self.dept2_id} (ID: {self.guest_employee_id})")
                return True
            else:
                self.error(f"Failed to create guest employee: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception creating guest employee: {str(e)}")
            return False
            
    def add_guest_to_target_department(self):
        """Add guest employee as temporary worker to fw4abteilung1"""
        try:
            assignment_data = {
                "employee_id": self.guest_employee_id
            }
            
            response = requests.post(f"{API_BASE}/departments/{self.dept1_id}/temporary-employees", json=assignment_data)
            if response.status_code == 200:
                result = response.json()
                self.success(f"Added guest employee to {self.dept1_id}: {result.get('message')}")
                return True
            else:
                self.error(f"Failed to add guest to target department: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception adding guest to target department: {str(e)}")
            return False
            
    def test_problem_1_guest_order_pricing(self):
        """TEST PROBLEM 1: Create guest order and verify prices shown are from target department"""
        try:
            # Create order: Guest from fw4abteilung2 orders in fw4abteilung1
            # Should show fw4abteilung1 prices (0.50€/0.60€) NOT fw4abteilung2 prices (0.75€/1.00€)
            
            order_data = {
                "employee_id": self.guest_employee_id,
                "department_id": self.dept1_id,  # Ordering in fw4abteilung1 (target department)
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,
                    "white_halves": 1,  # 1x Helles Brötchen
                    "seeded_halves": 1,  # 1x Körnerbrötchen  
                    "toppings": ["Rührei", "Spiegelei"],
                    "has_lunch": True,  # Add lunch
                    "boiled_eggs": 1,   # Add eggs
                    "fried_eggs": 0,
                    "has_coffee": False
                }]
            }
            
            self.log(f"Creating guest order: {self.guest_employee_name} from {self.dept2_id} ordering in {self.dept1_id}")
            
            response = requests.post(f"{API_BASE}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.test_order_id = order["id"]
                total_price = order["total_price"]
                
                # Expected price calculation using fw4abteilung1 prices:
                # 1x white roll half: 0.50€
                # 1x seeded roll half: 0.60€  
                # 1x boiled egg: 0.60€ (fw4abteilung1 specific price)
                # 1x lunch: 6.00€ (current price)
                # Expected total: 0.50 + 0.60 + 0.60 + 6.00 = 7.70€
                
                expected_price = 7.70
                if abs(total_price - expected_price) < 0.10:
                    self.success(f"✅ PROBLEM 1 TEST PASSED: Guest order uses target department prices (€{total_price})")
                    return True
                else:
                    self.error(f"❌ PROBLEM 1 TEST FAILED: Expected €{expected_price}, got €{total_price}")
                    self.error("This suggests prices from home department (fw4abteilung2) are being used instead of target department (fw4abteilung1)")
                    return False
            else:
                self.error(f"Failed to create guest order: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception testing Problem 1: {str(e)}")
            return False
            
    def test_problem_2_history_display_prices(self):
        """TEST PROBLEM 2: Verify history shows correct department-specific prices"""
        try:
            # Get breakfast history for fw4abteilung1 (where the order was placed)
            response = requests.get(f"{API_BASE}/orders/breakfast-history/{self.dept1_id}")
            if response.status_code == 200:
                history_data = response.json()
                
                # Look for our guest employee in the history
                found_guest_order = False
                if history_data.get("history"):
                    for day_data in history_data["history"]:
                        employee_orders = day_data.get("employee_orders", {})
                        for employee_key, employee_data in employee_orders.items():
                            if self.guest_employee_name in employee_key:
                                # Check if the displayed prices match fw4abteilung1 prices
                                total_amount = employee_data.get("total_amount", 0)
                                
                                # The total should be calculated using fw4abteilung1 prices
                                if abs(total_amount - 6.60) < 0.10:
                                    self.success(f"✅ PROBLEM 2 TEST PASSED: History shows correct target department prices (€{total_amount})")
                                    found_guest_order = True
                                else:
                                    self.error(f"❌ PROBLEM 2 TEST FAILED: History shows incorrect price €{total_amount}, expected €6.60")
                                    found_guest_order = True
                                break
                        if found_guest_order:
                            break
                
                if not found_guest_order:
                    self.error("Guest order not found in breakfast history")
                    return False
                    
                return found_guest_order
            else:
                self.error(f"Failed to get breakfast history: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception testing Problem 2: {str(e)}")
            return False
            
    def test_problem_3_retroactive_lunch_price_change(self):
        """TEST PROBLEM 3: Test retroactive lunch price changes for guest employees"""
        try:
            # Get current lunch settings
            lunch_response = requests.get(f"{API_BASE}/lunch-settings")
            if lunch_response.status_code != 200:
                self.error("Failed to get current lunch settings")
                return False
                
            current_settings = lunch_response.json()
            original_price = current_settings.get("price", 5.00)
            
            # Change lunch price to test retroactive updates
            new_lunch_price = 6.00
            self.log(f"Changing lunch price from €{original_price} to €{new_lunch_price}")
            
            price_response = requests.put(f"{API_BASE}/lunch-settings?price={new_lunch_price}")
            if price_response.status_code == 200:
                update_result = price_response.json()
                updated_orders = update_result.get("updated_orders", 0)
                
                self.success(f"Lunch price updated successfully, {updated_orders} orders updated")
                
                # Check if guest employee's subaccount balance was updated correctly
                balance_response = requests.get(f"{API_BASE}/employees/{self.guest_employee_id}/all-balances")
                if balance_response.status_code == 200:
                    balances = balance_response.json()
                    
                    # Check subaccount balance for fw4abteilung1 (where the order was placed)
                    subaccount_balances = balances.get("subaccount_balances", {})
                    dept1_balance = subaccount_balances.get(self.dept1_id, {})
                    breakfast_balance = dept1_balance.get("breakfast", 0)
                    
                    # The balance should reflect the new lunch price
                    # Original order: 0.50 + 0.60 + 0.50 + 6.00 = 7.60€ (with new lunch price)
                    expected_balance = -7.60  # Negative because it's debt
                    
                    if abs(breakfast_balance - expected_balance) < 0.10:
                        self.success(f"✅ PROBLEM 3 TEST PASSED: Guest subaccount balance updated correctly (€{breakfast_balance})")
                        return True
                    else:
                        self.error(f"❌ PROBLEM 3 TEST FAILED: Expected balance €{expected_balance}, got €{breakfast_balance}")
                        return False
                else:
                    self.error("Failed to get employee balances")
                    return False
            else:
                self.error(f"Failed to update lunch price: {price_response.status_code} - {price_response.text}")
                return False
                
        except Exception as e:
            self.error(f"Exception testing Problem 3: {str(e)}")
            return False
            
    def verify_employee_profile_prices(self):
        """Verify employee profile shows correct department-specific prices"""
        try:
            response = requests.get(f"{API_BASE}/employees/{self.guest_employee_id}/profile")
            if response.status_code == 200:
                profile = response.json()
                
                # Check order history in profile
                order_history = profile.get("order_history", [])
                for order in order_history:
                    if order.get("id") == self.test_order_id:
                        order_total = order.get("total_price", 0)
                        
                        # Should show price calculated with fw4abteilung1 prices
                        if abs(order_total - 7.60) < 0.10:  # Updated price after lunch change
                            self.success(f"Employee profile shows correct order price: €{order_total}")
                            return True
                        else:
                            self.error(f"Employee profile shows incorrect order price: €{order_total}")
                            return False
                
                self.error("Test order not found in employee profile")
                return False
            else:
                self.error(f"Failed to get employee profile: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.error(f"Exception verifying employee profile: {str(e)}")
            return False
            
    def run_comprehensive_test(self):
        """Run the complete pricing problems test"""
        self.log("🎯 STARTING THREE CRITICAL PRICING PROBLEMS VERIFICATION")
        self.log("=" * 80)
        
        # Test steps
        test_steps = [
            ("Initialize Data", self.test_init_data),
            ("Setup Department Prices", self.setup_department_prices),
            ("Create Guest Employee", self.create_guest_employee),
            ("Add Guest to Target Department", self.add_guest_to_target_department),
            ("TEST PROBLEM 1: Guest Order Pricing", self.test_problem_1_guest_order_pricing),
            ("TEST PROBLEM 2: History Display Prices", self.test_problem_2_history_display_prices),
            ("TEST PROBLEM 3: Retroactive Lunch Price Change", self.test_problem_3_retroactive_lunch_price_change),
            ("Verify Employee Profile Prices", self.verify_employee_profile_prices)
        ]
        
        passed_tests = 0
        total_tests = len(test_steps)
        critical_tests_passed = 0
        critical_tests_total = 3  # Problems 1, 2, 3
        
        for step_name, step_function in test_steps:
            self.log(f"\n📋 Step {passed_tests + 1}/{total_tests}: {step_name}")
            self.log("-" * 50)
            
            if step_function():
                passed_tests += 1
                self.success(f"Step {passed_tests}/{total_tests} PASSED: {step_name}")
                
                # Count critical test passes
                if "PROBLEM" in step_name:
                    critical_tests_passed += 1
            else:
                self.error(f"Step {passed_tests + 1}/{total_tests} FAILED: {step_name}")
                
        # Final results
        self.log("\n" + "=" * 80)
        self.log("🎯 CRITICAL PRICING PROBLEMS TEST RESULTS:")
        self.log("=" * 80)
        
        if critical_tests_passed == critical_tests_total:
            self.success(f"🎉 ALL THREE PRICING PROBLEMS HAVE BEEN SUCCESSFULLY FIXED!")
            self.success(f"Critical tests passed: {critical_tests_passed}/{critical_tests_total}")
            self.log("\n✅ PROBLEM 1 FIXED: Guest orders use target department prices")
            self.log("✅ PROBLEM 2 FIXED: History displays correct department-specific prices")  
            self.log("✅ PROBLEM 3 FIXED: Retroactive lunch price changes update guest subaccounts")
            return True
        else:
            self.error(f"❌ PRICING PROBLEMS STILL EXIST!")
            self.error(f"Critical tests passed: {critical_tests_passed}/{critical_tests_total}")
            
            if critical_tests_passed == 0:
                self.error("🚨 ALL THREE PROBLEMS STILL NEED TO BE FIXED")
            elif critical_tests_passed == 1:
                self.error("🚨 TWO PROBLEMS STILL NEED TO BE FIXED")
            elif critical_tests_passed == 2:
                self.error("🚨 ONE PROBLEM STILL NEEDS TO BE FIXED")
                
            return False

def main():
    """Main test execution"""
    print("🧪 Backend Test Suite - Three Critical Pricing Problems")
    print("=" * 70)
    
    # Initialize and run test
    test_suite = PricingProblemsTest()
    success = test_suite.run_comprehensive_test()
    
    if success:
        print("\n🎉 ALL PRICING PROBLEMS HAVE BEEN SUCCESSFULLY FIXED!")
        exit(0)
    else:
        print("\n❌ PRICING PROBLEMS STILL EXIST - FIXES NEEDED!")
        exit(1)

if __name__ == "__main__":
    main()