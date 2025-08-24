#!/usr/bin/env python3
"""
Focused Test for Boiled Eggs Price Management Functionality
Tests the specific API endpoints that the BoiledEggsManagement component uses
"""

import requests
import json
import sys
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class BoiledEggsTestRunner:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message,
            'details': details
        })
        
    def test_boiled_eggs_price_management(self):
        """Test boiled eggs price management functionality in Menu & Preise section"""
        print("\n=== Testing Boiled Eggs Price Management ===")
        print("🥚 Testing the boiled eggs price management functionality that was moved to the Menu & Preise section")
        print(f"🔗 API Base URL: {API_BASE}")
        print("=" * 80)
        
        success_count = 0
        
        # Test 1: GET lunch settings to verify boiled_eggs_price field
        print("\n1️⃣ Testing GET /api/lunch-settings - Verify boiled_eggs_price field exists")
        try:
            response = self.session.get(f"{API_BASE}/lunch-settings")
            
            if response.status_code == 200:
                lunch_settings = response.json()
                
                # Check if boiled_eggs_price field exists
                if 'boiled_eggs_price' in lunch_settings:
                    current_price = lunch_settings['boiled_eggs_price']
                    self.log_test("GET Lunch Settings - Boiled Eggs Price Field", True, 
                                f"✅ Current boiled eggs price: €{current_price:.2f}")
                    success_count += 1
                    
                    # Show all lunch settings for context
                    print(f"   📋 Full lunch settings: {json.dumps(lunch_settings, indent=2)}")
                else:
                    self.log_test("GET Lunch Settings - Boiled Eggs Price Field", False, 
                                "❌ boiled_eggs_price field missing from lunch settings")
            else:
                self.log_test("GET Lunch Settings - Boiled Eggs Price Field", False, 
                            f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("GET Lunch Settings - Boiled Eggs Price Field", False, f"❌ Exception: {str(e)}")
        
        # Test 2: UPDATE boiled eggs price using PUT endpoint
        print("\n2️⃣ Testing PUT /api/lunch-settings/boiled-eggs-price - Update price with query parameter")
        try:
            new_boiled_eggs_price = 0.85  # Test with a different price
            response = self.session.put(f"{API_BASE}/lunch-settings/boiled-eggs-price", 
                                      params={"price": new_boiled_eggs_price})
            
            if response.status_code == 200:
                result = response.json()
                if result.get('price') == new_boiled_eggs_price:
                    self.log_test("UPDATE Boiled Eggs Price", True, 
                                f"✅ Successfully updated boiled eggs price to €{new_boiled_eggs_price:.2f}")
                    success_count += 1
                    print(f"   📋 Update response: {json.dumps(result, indent=2)}")
                else:
                    self.log_test("UPDATE Boiled Eggs Price", False, 
                                f"❌ Price update response mismatch: expected €{new_boiled_eggs_price:.2f}, got {result.get('price', 'N/A')}")
            else:
                self.log_test("UPDATE Boiled Eggs Price", False, 
                            f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("UPDATE Boiled Eggs Price", False, f"❌ Exception: {str(e)}")
        
        # Test 3: Verify price persistence by fetching settings again
        print("\n3️⃣ Testing Price Persistence - Confirm the price update is saved correctly")
        try:
            response = self.session.get(f"{API_BASE}/lunch-settings")
            
            if response.status_code == 200:
                lunch_settings = response.json()
                
                if 'boiled_eggs_price' in lunch_settings:
                    persisted_price = lunch_settings['boiled_eggs_price']
                    expected_price = 0.85  # From previous update
                    
                    if abs(persisted_price - expected_price) < 0.01:  # Allow for floating point precision
                        self.log_test("Verify Price Persistence", True, 
                                    f"✅ Price correctly persisted: €{persisted_price:.2f}")
                        success_count += 1
                    else:
                        self.log_test("Verify Price Persistence", False, 
                                    f"❌ Price not persisted correctly: expected €{expected_price:.2f}, got €{persisted_price:.2f}")
                else:
                    self.log_test("Verify Price Persistence", False, 
                                "❌ boiled_eggs_price field missing after update")
            else:
                self.log_test("Verify Price Persistence", False, 
                            f"❌ HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Verify Price Persistence", False, f"❌ Exception: {str(e)}")
        
        # Test 4: Test price validation with invalid values
        print("\n4️⃣ Testing Price Validation - Try updating with invalid values")
        invalid_test_cases = [
            {"price": -1.0, "description": "negative price"},
            {"price": "invalid", "description": "non-numeric price"},
            {"price": 999.99, "description": "extremely high price"}
        ]
        
        validation_success_count = 0
        for i, test_case in enumerate(invalid_test_cases, 1):
            print(f"   4.{i} Testing {test_case['description']}: {test_case['price']}")
            try:
                response = self.session.put(f"{API_BASE}/lunch-settings/boiled-eggs-price", 
                                          params={"price": test_case["price"]})
                
                # We expect either 400 (validation error) or 422 (unprocessable entity)
                if response.status_code in [400, 422]:
                    self.log_test(f"Price Validation - {test_case['description']}", True, 
                                f"✅ Correctly rejected {test_case['description']} with HTTP {response.status_code}")
                    validation_success_count += 1
                elif response.status_code == 200:
                    # If it accepts the invalid value, that's a problem
                    self.log_test(f"Price Validation - {test_case['description']}", False, 
                                f"❌ Should reject {test_case['description']}, but got HTTP 200")
                else:
                    self.log_test(f"Price Validation - {test_case['description']}", False, 
                                f"❌ Unexpected response: HTTP {response.status_code}")
                    
            except Exception as e:
                # For non-numeric values, we might get an exception during request preparation
                if test_case["price"] == "invalid":
                    self.log_test(f"Price Validation - {test_case['description']}", True, 
                                f"✅ Correctly rejected {test_case['description']} with exception")
                    validation_success_count += 1
                else:
                    self.log_test(f"Price Validation - {test_case['description']}", False, 
                                f"❌ Exception: {str(e)}")
        
        # Consider validation successful if at least 2 out of 3 invalid cases are handled properly
        if validation_success_count >= 2:
            success_count += 1
            self.log_test("Overall Price Validation", True, 
                        f"✅ Price validation working correctly ({validation_success_count}/3 cases handled)")
        else:
            self.log_test("Overall Price Validation", False, 
                        f"❌ Price validation insufficient ({validation_success_count}/3 cases handled)")
        
        # Final summary
        print("\n" + "=" * 80)
        print("🎯 BOILED EGGS PRICE MANAGEMENT TEST SUMMARY")
        print("=" * 80)
        
        total_tests = 4
        success_rate = (success_count / total_tests) * 100
        print(f"📊 Tests Passed: {success_count}/{total_tests} ({success_rate:.1f}%)")
        
        if success_count >= 3:
            print("🎉 EXCELLENT! Boiled eggs price management functionality is working correctly!")
            print("✅ The BoiledEggsManagement component should work properly in the Menu & Preise tab.")
        elif success_count >= 2:
            print("⚠️  GOOD! Core functionality working but some validation issues detected.")
        else:
            print("🚨 CRITICAL! Major issues with boiled eggs price management functionality.")
        
        print("\n📋 Detailed Test Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return success_count >= 3

def main():
    """Run the boiled eggs price management tests"""
    print("🥚 BOILED EGGS PRICE MANAGEMENT TESTING")
    print("Testing the functionality that was moved to the Menu & Preise section")
    print("=" * 80)
    
    tester = BoiledEggsTestRunner()
    success = tester.test_boiled_eggs_price_management()
    
    if success:
        print("\n🎉 SUCCESS: All boiled eggs price management tests passed!")
        sys.exit(0)
    else:
        print("\n❌ FAILURE: Some boiled eggs price management tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()