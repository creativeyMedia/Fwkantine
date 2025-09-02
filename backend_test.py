#!/usr/bin/env python3
"""
🔍 FRONTEND DEBUG: Analysiere exakte Backend-Datenstruktur für Frontend-Verarbeitung

KRITISCHE FRONTEND-DATEN-ANALYSE:

1. **Create exact scenario from User screenshot:**
   - Test1: Eigene Bestellung (Brötchen, Eier, Kaffee, Mittag)
   - Test1 sponsert Frühstück für andere (daher die Message "Frühstück wurde von dir ausgegeben")
   - Test4 sponsert Mittag für Test1 (daher "Dieses Mittagessen wurde von Test4 ausgegeben")

2. **KRITISCHE DATENSTRUKTUR-ANALYSE für Test1:**
   - Hol Test1's individual employee profile
   - Analysiere EXACT die Order-Struktur die das Frontend bekommt
   - WICHTIG: `sponsored_meal_type`, `is_sponsored`, `readable_items` Struktur
   - WICHTIG: Prüfe ob `sponsored_meal_type = "lunch"` gesetzt ist (für Mittag-Sponsoring)

3. **DETAILLIERTE ORDER-FELDER:**
   - Zeige komplette Order mit allen Feldern
   - Speziell: `breakfast_items`, `readable_items`, `sponsored_meal_type`, `sponsored_message`
   - Prüfe ob die Daten so strukturiert sind, wie die Frontend-Logik erwartet

4. **FRONTEND-LOGIK VERIFICATION:**
   - Test1 sollte have: `is_sponsored=True`, `sponsored_meal_type="lunch"` (weil Mittag gesponsert)
   - readable_items sollten korrekte Preise haben für calculateDisplayPrice
   - sponsored_meal_type sollte "lunch" enthalten für Durchstreichungslogik

Department: fw1abteilung1 (1. Wachabteilung)
Login: admin1/password1

ZIEL: Finde heraus warum Frontend die Backend-Daten nicht korrekt verarbeitet!
"""

import requests
import json
from datetime import datetime, timedelta
import pytz
import os
from typing import Dict, List, Any

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteen-fire.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

# Test Configuration - EXACT from review request
DEPARTMENT_ID = "fw1abteilung1"  # Department 1 (1. Wachabteilung)
ADMIN_PASSWORD = "admin1"
DEPARTMENT_NAME = "1. Wachabteilung"

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

class FrontendDataStructureAnalysis:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.test1_employee_id = None
        self.test4_employee_id = None
        self.other_employees = []
        self.test_orders = []
        
    def cleanup_test_data(self) -> bool:
        """Clean up test data to create fresh scenario"""
        try:
            response = self.session.delete(f"{API_BASE}/department-admin/debug-cleanup/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully cleaned up test data: {result}")
                return True
            else:
                print(f"⚠️ Cleanup failed (continuing anyway): {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"⚠️ Cleanup error (continuing anyway): {e}")
            return False
    
    def get_berlin_date(self):
        """Get current date in Berlin timezone"""
        return datetime.now(BERLIN_TZ).date().strftime('%Y-%m-%d')
        
    def authenticate_admin(self) -> bool:
        """Authenticate as admin for Department 1"""
        try:
            response = self.session.post(f"{API_BASE}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Admin Authentication Success: {data}")
                return True
            else:
                print(f"❌ Admin Authentication Failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Admin Authentication Error: {e}")
            return False
    
    def create_test_employee(self, name: str) -> str:
        """Create a test employee and return employee ID"""
        try:
            response = self.session.post(f"{API_BASE}/employees", json={
                "name": name,
                "department_id": DEPARTMENT_ID
            })
            
            if response.status_code == 200:
                employee = response.json()
                employee_id = employee["id"]
                print(f"✅ Created test employee '{name}': {employee_id}")
                return employee_id
            else:
                print(f"❌ Failed to create employee '{name}': {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating employee '{name}': {e}")
            return None
    
    def create_test1_breakfast_order(self, employee_id: str) -> Dict:
        """Create Test1's breakfast order: Brötchen, Eier, Kaffee, Mittag"""
        try:
            # Create order matching review request: Brötchen, Eier, Kaffee, Mittag
            order_data = {
                "employee_id": employee_id,
                "department_id": DEPARTMENT_ID,
                "order_type": "breakfast",
                "breakfast_items": [{
                    "total_halves": 2,  # 1 Brötchen (2 halves)
                    "white_halves": 1,
                    "seeded_halves": 1,
                    "toppings": ["butter", "kaese"],  # Simple toppings
                    "has_lunch": True,  # Mittag
                    "boiled_eggs": 2,   # Eier
                    "has_coffee": True  # Kaffee
                }]
            }
            
            response = self.session.post(f"{API_BASE}/orders", json=order_data)
            
            if response.status_code == 200:
                order = response.json()
                order_id = order["id"]
                
                print(f"✅ Created Test1 breakfast order: {order_id} (€{order['total_price']:.2f})")
                print(f"   - Brötchen: 1 (2 halves)")
                print(f"   - Eier: 2")
                print(f"   - Kaffee: Yes")
                print(f"   - Mittag: Yes")
                
                self.test_orders.append({
                    "employee_id": employee_id,
                    "employee_name": "Test1",
                    "order_id": order_id,
                    "total_price": order["total_price"],
                    "has_lunch": True
                })
                return {
                    "order_id": order_id,
                    "total_price": order["total_price"],
                    "has_lunch": True
                }
            else:
                print(f"❌ Failed to create Test1 breakfast order: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error creating Test1 breakfast order: {e}")
            return None
    
    def create_other_employee_orders(self, employee_ids: List[str]) -> bool:
        """Create orders for other employees so Test1 can sponsor their breakfast"""
        try:
            for i, employee_id in enumerate(employee_ids):
                order_data = {
                    "employee_id": employee_id,
                    "department_id": DEPARTMENT_ID,
                    "order_type": "breakfast",
                    "breakfast_items": [{
                        "total_halves": 2,
                        "white_halves": 1,
                        "seeded_halves": 1,
                        "toppings": ["butter", "schinken"],
                        "has_lunch": False,  # No lunch for others
                        "boiled_eggs": 1,
                        "has_coffee": True
                    }]
                }
                
                response = self.session.post(f"{API_BASE}/orders", json=order_data)
                
                if response.status_code == 200:
                    order = response.json()
                    print(f"✅ Created order for Other{i+2}: €{order['total_price']:.2f}")
                else:
                    print(f"❌ Failed to create order for Other{i+2}: {response.status_code}")
                    return False
            
            return True
                
        except Exception as e:
            print(f"❌ Error creating other employee orders: {e}")
            return False
    
    def test1_sponsors_breakfast(self, test1_employee_id: str) -> Dict:
        """Test1 sponsors breakfast for others"""
        try:
            today = self.get_berlin_date()
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "breakfast",
                "sponsor_employee_id": test1_employee_id,
                "sponsor_employee_name": "Test1"
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test1 successfully sponsored breakfast meals: {result}")
                return result
            else:
                print(f"❌ Test1 failed to sponsor breakfast meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error Test1 sponsoring breakfast meals: {e}")
            return {"error": str(e)}
    
    def test4_sponsors_lunch(self, test4_employee_id: str) -> Dict:
        """Test4 sponsors lunch for Test1"""
        try:
            today = self.get_berlin_date()
            
            response = self.session.post(f"{API_BASE}/department-admin/sponsor-meal", json={
                "department_id": DEPARTMENT_ID,
                "date": today,
                "meal_type": "lunch",
                "sponsor_employee_id": test4_employee_id,
                "sponsor_employee_name": "Test4"
            })
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test4 successfully sponsored lunch meals: {result}")
                return result
            else:
                print(f"❌ Test4 failed to sponsor lunch meals: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error Test4 sponsoring lunch meals: {e}")
            return {"error": str(e)}
    
    def get_breakfast_history(self) -> Dict:
        """Get breakfast history from breakfast-history endpoint"""
        try:
            response = self.session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Successfully retrieved breakfast history")
                return data
            else:
                print(f"❌ Failed to get breakfast history: {response.status_code} - {response.text}")
                return {"error": response.text}
                
        except Exception as e:
            print(f"❌ Error getting breakfast history: {e}")
            return {"error": str(e)}
    
    def analyze_test1_data_structure(self, employee_orders: Dict) -> Dict:
        """
        KRITISCHE DATENSTRUKTUR-ANALYSE für Test1:
        - Hol Test1's individual employee profile
        - Analysiere EXACT die Order-Struktur die das Frontend bekommt
        - WICHTIG: `sponsored_meal_type`, `is_sponsored`, `readable_items` Struktur
        """
        results = {
            "test1_found": False,
            "has_sponsored_meal_type": False,
            "sponsored_meal_type_value": None,
            "is_sponsored": False,
            "total_amount": 0.0,
            "readable_items_structure": {},
            "complete_data_structure": {}
        }
        
        print(f"🔍 KRITISCHE DATENSTRUKTUR-ANALYSE für Test1")
        print(f"Expected: Test1 should have sponsored_meal_type='lunch' and is_sponsored=True")
        
        # Find Test1 in the employee orders
        test1_data = None
        for emp_name, emp_data in employee_orders.items():
            if "Test1" in emp_name or emp_name == "Test1":
                test1_data = emp_data
                results["test1_found"] = True
                results["total_amount"] = emp_data.get("total_amount", 0.0)
                results["complete_data_structure"] = emp_data
                print(f"✅ Found Test1: {emp_name}")
                break
        
        if not test1_data:
            print(f"❌ Test1 not found in employee orders")
            return results
        
        # Analyze the complete data structure
        print(f"\n🔍 COMPLETE Test1 Data Structure:")
        for key, value in test1_data.items():
            print(f"  - {key}: {value}")
        
        # Check for sponsored_meal_type
        if "sponsored_meal_type" in test1_data:
            results["has_sponsored_meal_type"] = True
            results["sponsored_meal_type_value"] = test1_data["sponsored_meal_type"]
            print(f"✅ sponsored_meal_type found: {test1_data['sponsored_meal_type']}")
            
            if "lunch" in str(test1_data["sponsored_meal_type"]).lower():
                print(f"✅ sponsored_meal_type contains 'lunch' - correct for lunch sponsoring")
            else:
                print(f"❌ sponsored_meal_type does NOT contain 'lunch': {test1_data['sponsored_meal_type']}")
        else:
            print(f"❌ sponsored_meal_type field NOT found in Test1 data")
        
        # Check for is_sponsored
        if "is_sponsored" in test1_data:
            results["is_sponsored"] = test1_data["is_sponsored"]
            print(f"✅ is_sponsored found: {test1_data['is_sponsored']}")
        else:
            print(f"❌ is_sponsored field NOT found in Test1 data")
        
        # Check for readable_items structure
        if "readable_items" in test1_data:
            results["readable_items_structure"] = test1_data["readable_items"]
            print(f"✅ readable_items found: {test1_data['readable_items']}")
        else:
            print(f"⚠️ readable_items field NOT found in Test1 data")
        
        # Check breakfast_items structure
        if "breakfast_items" in test1_data:
            print(f"✅ breakfast_items found: {test1_data['breakfast_items']}")
        else:
            print(f"⚠️ breakfast_items field NOT found in Test1 data")
        
        return results
    
    def verify_frontend_logic_expectations(self, test1_data: Dict) -> Dict:
        """
        FRONTEND-LOGIK VERIFICATION:
        - Test1 sollte have: `is_sponsored=True`, `sponsored_meal_type="lunch"` (weil Mittag gesponsert)
        - readable_items sollten korrekte Preise haben für calculateDisplayPrice
        - sponsored_meal_type sollte "lunch" enthalten für Durchstreichungslogik
        """
        results = {
            "is_sponsored_correct": False,
            "sponsored_meal_type_correct": False,
            "readable_items_correct": False,
            "strikethrough_logic_supported": False,
            "calculate_display_price_supported": False
        }
        
        print(f"\n🔍 FRONTEND-LOGIK VERIFICATION")
        
        # Check is_sponsored = True
        if test1_data.get("is_sponsored") == True:
            results["is_sponsored_correct"] = True
            print(f"✅ is_sponsored=True - correct for sponsored employee")
        else:
            print(f"❌ is_sponsored={test1_data.get('is_sponsored')} - should be True for sponsored employee")
        
        # Check sponsored_meal_type contains "lunch"
        sponsored_meal_type = test1_data.get("sponsored_meal_type")
        if sponsored_meal_type and "lunch" in str(sponsored_meal_type).lower():
            results["sponsored_meal_type_correct"] = True
            print(f"✅ sponsored_meal_type contains 'lunch': {sponsored_meal_type}")
        else:
            print(f"❌ sponsored_meal_type does NOT contain 'lunch': {sponsored_meal_type}")
        
        # Check readable_items for calculateDisplayPrice
        readable_items = test1_data.get("readable_items")
        if readable_items and isinstance(readable_items, (list, dict)):
            results["readable_items_correct"] = True
            results["calculate_display_price_supported"] = True
            print(f"✅ readable_items structure supports calculateDisplayPrice: {readable_items}")
        else:
            print(f"❌ readable_items structure NOT suitable for calculateDisplayPrice: {readable_items}")
        
        # Check if structure supports strikethrough logic
        has_breakfast_items = "breakfast_items" in test1_data or "white_halves" in test1_data
        has_lunch_info = "has_lunch" in test1_data
        has_coffee_info = "has_coffee" in test1_data
        
        if has_breakfast_items and has_lunch_info and has_coffee_info:
            results["strikethrough_logic_supported"] = True
            print(f"✅ Data structure supports strikethrough logic (breakfast items, lunch, coffee info available)")
        else:
            print(f"❌ Data structure may NOT support strikethrough logic properly")
            print(f"   - breakfast_items: {has_breakfast_items}")
            print(f"   - lunch_info: {has_lunch_info}")
            print(f"   - coffee_info: {has_coffee_info}")
        
        return results
    
    def analyze_sponsoring_messages(self, employee_orders: Dict) -> Dict:
        """
        Analyze sponsoring messages:
        - Test1 should show "Frühstück wurde von dir ausgegeben" (Test1 sponsors breakfast)
        - Test1 should show "Dieses Mittagessen wurde von Test4 ausgegeben" (Test4 sponsors Test1's lunch)
        """
        results = {
            "test1_sponsors_breakfast_message": False,
            "test4_sponsors_test1_lunch_message": False,
            "test1_sponsoring_info": None,
            "test4_sponsoring_info": None
        }
        
        print(f"\n🔍 ANALYZING SPONSORING MESSAGES")
        
        # Look for Test1's sponsoring information (Test1 sponsors breakfast for others)
        for emp_name, emp_data in employee_orders.items():
            if "Test1" in emp_name:
                sponsored_breakfast = emp_data.get("sponsored_breakfast")
                if sponsored_breakfast:
                    results["test1_sponsors_breakfast_message"] = True
                    results["test1_sponsoring_info"] = sponsored_breakfast
                    print(f"✅ Test1 sponsors breakfast info found: {sponsored_breakfast}")
                    print(f"   - This should generate message: 'Frühstück wurde von dir ausgegeben'")
        
        # Look for Test4's sponsoring information (Test4 sponsors lunch for Test1)
        for emp_name, emp_data in employee_orders.items():
            if "Test4" in emp_name:
                sponsored_lunch = emp_data.get("sponsored_lunch")
                if sponsored_lunch:
                    results["test4_sponsors_test1_lunch_message"] = True
                    results["test4_sponsoring_info"] = sponsored_lunch
                    print(f"✅ Test4 sponsors lunch info found: {sponsored_lunch}")
                    print(f"   - This should generate message: 'Dieses Mittagessen wurde von Test4 ausgegeben'")
        
        return results
    
    def run_frontend_data_analysis(self):
        """Run the frontend data structure analysis as per review request"""
        print("🔍 FRONTEND DEBUG: Analysiere exakte Backend-Datenstruktur für Frontend-Verarbeitung")
        print("=" * 80)
        
        # Step 1: Admin Authentication
        print("\n1️⃣ Admin Authentication for Department 1")
        if not self.authenticate_admin():
            print("❌ CRITICAL FAILURE: Cannot authenticate as admin")
            return False
        
        # Step 1.5: Try to cleanup existing data for fresh test
        print("\n1️⃣.5 Attempting to Clean Up Existing Data")
        self.cleanup_test_data()
        
        # Step 2: Create exact scenario from User screenshot
        print(f"\n2️⃣ Creating EXACT Scenario from User Screenshot")
        print("- Test1: Eigene Bestellung (Brötchen, Eier, Kaffee, Mittag)")
        print("- Test1 sponsert Frühstück für andere")
        print("- Test4 sponsert Mittag für Test1")
        
        # Create Test1
        self.test1_employee_id = self.create_test_employee("Test1")
        if not self.test1_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Test1")
            return False
        
        # Create Test4
        self.test4_employee_id = self.create_test_employee("Test4")
        if not self.test4_employee_id:
            print("❌ CRITICAL FAILURE: Cannot create Test4")
            return False
        
        # Create other employees for Test1 to sponsor
        other_employee_ids = []
        for i in range(2):  # Create Other2, Other3
            other_id = self.create_test_employee(f"Other{i+2}")
            if other_id:
                other_employee_ids.append(other_id)
        
        # Step 3: Create Test1's breakfast order (Brötchen, Eier, Kaffee, Mittag)
        print(f"\n3️⃣ Creating Test1's Breakfast Order")
        test1_order = self.create_test1_breakfast_order(self.test1_employee_id)
        if not test1_order:
            print("❌ CRITICAL FAILURE: Cannot create Test1's order")
            return False
        
        # Step 4: Create orders for other employees
        print(f"\n4️⃣ Creating Orders for Other Employees")
        if not self.create_other_employee_orders(other_employee_ids):
            print("❌ CRITICAL FAILURE: Cannot create other employee orders")
            return False
        
        # Step 5: Test1 sponsors breakfast for others
        print(f"\n5️⃣ Test1 Sponsors Breakfast for Others")
        breakfast_result = self.test1_sponsors_breakfast(self.test1_employee_id)
        if "error" in breakfast_result:
            print(f"❌ Test1 breakfast sponsoring failed: {breakfast_result['error']}")
            return False
        
        # Step 6: Test4 sponsors lunch for Test1
        print(f"\n6️⃣ Test4 Sponsors Lunch for Test1")
        lunch_result = self.test4_sponsors_lunch(self.test4_employee_id)
        if "error" in lunch_result:
            print(f"❌ Test4 lunch sponsoring failed: {lunch_result['error']}")
            return False
        
        # Step 7: Get breakfast history and analyze data structure
        print(f"\n7️⃣ Getting Breakfast History for Data Structure Analysis")
        history_data = self.get_breakfast_history()
        
        if "error" in history_data:
            print(f"❌ CRITICAL FAILURE: Cannot get breakfast history: {history_data['error']}")
            return False
        
        # Step 8: Analyze data structure
        print(f"\n8️⃣ Analyzing Backend Data Structure")
        
        if not isinstance(history_data, dict) or "history" not in history_data:
            print(f"❌ CRITICAL FAILURE: Invalid history data structure")
            return False
        
        history = history_data["history"]
        if not history or len(history) == 0:
            print(f"❌ CRITICAL FAILURE: No history data found")
            return False
        
        # Get today's data (should be first in list)
        today_data = history[0]
        employee_orders = today_data.get("employee_orders", {})
        
        if not employee_orders:
            print(f"❌ CRITICAL FAILURE: No employee orders found in today's data")
            return False
        
        print(f"✅ Found {len(employee_orders)} employees in today's breakfast history")
        
        # Step 9: KRITISCHE DATENSTRUKTUR-ANALYSE für Test1
        print(f"\n9️⃣ KRITISCHE DATENSTRUKTUR-ANALYSE für Test1")
        test1_analysis = self.analyze_test1_data_structure(employee_orders)
        
        # Step 10: FRONTEND-LOGIK VERIFICATION
        print(f"\n🔟 FRONTEND-LOGIK VERIFICATION")
        if test1_analysis["test1_found"]:
            frontend_logic = self.verify_frontend_logic_expectations(test1_analysis["complete_data_structure"])
        else:
            print("❌ Cannot verify frontend logic - Test1 not found")
            frontend_logic = {}
        
        # Step 11: Analyze sponsoring messages
        print(f"\n1️⃣1️⃣ ANALYZING SPONSORING MESSAGES")
        message_analysis = self.analyze_sponsoring_messages(employee_orders)
        
        # Final Results
        print(f"\n🏁 FINAL ANALYSIS RESULTS:")
        
        success_criteria = [
            (test1_analysis["test1_found"], f"Test1 Found in Data: {test1_analysis['test1_found']}"),
            (test1_analysis["has_sponsored_meal_type"], f"sponsored_meal_type Field: {test1_analysis['sponsored_meal_type_value']}"),
            (frontend_logic.get("is_sponsored_correct", False), f"is_sponsored=True: {frontend_logic.get('is_sponsored_correct', False)}"),
            (frontend_logic.get("sponsored_meal_type_correct", False), f"sponsored_meal_type contains 'lunch': {frontend_logic.get('sponsored_meal_type_correct', False)}"),
            (frontend_logic.get("readable_items_correct", False), f"readable_items Structure: {frontend_logic.get('readable_items_correct', False)}"),
            (message_analysis["test1_sponsors_breakfast_message"], f"Test1 Sponsors Breakfast Message: {message_analysis['test1_sponsors_breakfast_message']}")
        ]
        
        passed_tests = sum(1 for test, _ in success_criteria if test)
        total_tests = len(success_criteria)
        
        for test_passed, description in success_criteria:
            status = "✅" if test_passed else "❌"
            print(f"{status} {description}")
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"\n📊 Overall Analysis Success Rate: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        
        # Print detailed findings
        print(f"\n🔍 DETAILED FINDINGS:")
        print(f"Test1 Total Amount: €{test1_analysis['total_amount']:.2f}")
        print(f"Test1 Complete Data Structure Keys: {list(test1_analysis['complete_data_structure'].keys())}")
        
        if success_rate >= 70:
            print("\n✅ FRONTEND DATA STRUCTURE ANALYSIS COMPLETED!")
            print("✅ Backend provides necessary data structure for frontend processing")
            return True
        else:
            print("\n❌ CRITICAL FRONTEND DATA STRUCTURE ISSUES DETECTED!")
            print("❌ Backend may not provide correct data structure for frontend")
            return False

def main():
    """Main test execution"""
    test = FrontendDataStructureAnalysis()
    
    try:
        success = test.run_frontend_data_analysis()
        
        if success:
            print(f"\n✅ FRONTEND DATA STRUCTURE ANALYSIS: COMPLETED")
            exit(0)
        else:
            print(f"\n❌ FRONTEND DATA STRUCTURE ANALYSIS: CRITICAL ISSUES DETECTED")
            exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL TEST ERROR: {e}")
        exit(1)

if __name__ == "__main__":
    main()