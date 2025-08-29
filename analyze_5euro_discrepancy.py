#!/usr/bin/env python3
"""
ANALYZE 5€ DISCREPANCY IN EXISTING DATA

FOCUS: Analyze the existing sponsored meal data to identify the source of the 5€ discrepancy
in the daily summary total_amount calculation.

This script will:
1. Examine the current breakfast history data
2. Analyze individual employee orders vs total_amount
3. Identify where the extra money is coming from
4. Check the calculation logic in the breakfast-history endpoint
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "https://meal-tracker-49.preview.emergentagent.com/api"
DEPARTMENT_NAME = "3. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung3"
ADMIN_PASSWORD = "admin3"

class AnalyzeFiveEuroDiscrepancy:
    def __init__(self):
        self.session = requests.Session()
        
    def authenticate_admin(self):
        """Authenticate as department admin"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                print("✅ Authenticated successfully as admin")
                return True
            else:
                print(f"❌ Authentication failed: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def analyze_breakfast_history(self):
        """Analyze the breakfast history to identify discrepancies"""
        try:
            print("\n🔍 ANALYZING BREAKFAST HISTORY FOR 5€ DISCREPANCY")
            print("=" * 60)
            
            # Get breakfast history for today
            response = self.session.get(f"{BASE_URL}/orders/breakfast-history/{DEPARTMENT_ID}?days_back=1")
            
            if response.status_code != 200:
                print(f"❌ Could not fetch breakfast history: HTTP {response.status_code}: {response.text}")
                return False
            
            breakfast_history = response.json()
            history_entries = breakfast_history.get("history", [])
            
            if not history_entries:
                print("❌ No history entries found for today")
                return False
            
            # Analyze today's entry
            today_entry = history_entries[0]
            today_date = today_entry.get("date", "")
            total_amount = today_entry.get("total_amount", 0)
            total_orders = today_entry.get("total_orders", 0)
            employee_orders = today_entry.get("employee_orders", {})
            
            print(f"📅 Date: {today_date}")
            print(f"📊 Total Orders: {total_orders}")
            print(f"💰 Total Amount: €{total_amount:.2f}")
            print(f"👥 Employee Count: {len(employee_orders)}")
            
            # Calculate sum of individual employee amounts
            individual_sum = 0
            sponsored_employees = []
            sponsor_employees = []
            regular_employees = []
            
            print(f"\n👤 INDIVIDUAL EMPLOYEE ANALYSIS:")
            for employee_name, order_data in employee_orders.items():
                employee_total = order_data.get("total_amount", 0)
                individual_sum += employee_total
                has_lunch = order_data.get("has_lunch", False)
                boiled_eggs = order_data.get("boiled_eggs", 0)
                has_coffee = order_data.get("has_coffee", False)
                white_halves = order_data.get("white_halves", 0)
                seeded_halves = order_data.get("seeded_halves", 0)
                total_halves = white_halves + seeded_halves
                
                # Categorize employees based on their amounts
                if employee_total == 0:
                    sponsored_employees.append(employee_name)
                    category = "SPONSORED"
                elif employee_total > 20:  # Likely sponsor (high amount)
                    sponsor_employees.append(employee_name)
                    category = "SPONSOR"
                else:
                    regular_employees.append(employee_name)
                    category = "REGULAR"
                
                print(f"   {category:8} | {employee_name:25} | €{employee_total:6.2f} | L:{has_lunch} E:{boiled_eggs} C:{has_coffee} R:{total_halves}")
            
            print(f"\n📈 CALCULATION ANALYSIS:")
            print(f"   Sum of individual amounts: €{individual_sum:.2f}")
            print(f"   Daily summary total_amount: €{total_amount:.2f}")
            print(f"   Difference: €{abs(total_amount - individual_sum):.2f}")
            
            if abs(total_amount - individual_sum) > 0.01:
                print(f"   ❌ DISCREPANCY DETECTED: Individual sum ≠ Total amount")
            else:
                print(f"   ✅ Individual sum matches total amount")
            
            print(f"\n🏷️  EMPLOYEE CATEGORIES:")
            print(f"   Sponsored employees (€0.00): {len(sponsored_employees)}")
            print(f"   Sponsor employees (>€20.00): {len(sponsor_employees)}")
            print(f"   Regular employees: {len(regular_employees)}")
            
            # Analyze potential 5€ discrepancy patterns
            print(f"\n🔍 5€ DISCREPANCY ANALYSIS:")
            
            # Check if there are employees with exactly 5€ extra
            five_euro_candidates = []
            for employee_name, order_data in employee_orders.items():
                employee_total = order_data.get("total_amount", 0)
                has_lunch = order_data.get("has_lunch", False)
                boiled_eggs = order_data.get("boiled_eggs", 0)
                has_coffee = order_data.get("has_coffee", False)
                
                # Expected cost calculation
                expected_cost = 0
                if boiled_eggs > 0:
                    expected_cost += boiled_eggs * 0.50  # Assume €0.50 per egg
                if has_coffee:
                    expected_cost += 1.50  # Assume €1.50 for coffee
                if has_lunch:
                    expected_cost += 5.00  # Assume €5.00 for lunch
                
                # Check for 5€ discrepancy
                discrepancy = employee_total - expected_cost
                if abs(discrepancy - 5.0) < 0.01:
                    five_euro_candidates.append({
                        "name": employee_name,
                        "actual": employee_total,
                        "expected": expected_cost,
                        "discrepancy": discrepancy
                    })
            
            if five_euro_candidates:
                print(f"   🎯 FOUND {len(five_euro_candidates)} EMPLOYEES WITH ~5€ DISCREPANCY:")
                for candidate in five_euro_candidates:
                    print(f"      {candidate['name']}: €{candidate['actual']:.2f} (expected: €{candidate['expected']:.2f}, extra: €{candidate['discrepancy']:.2f})")
            else:
                print(f"   ℹ️  No employees found with exactly 5€ discrepancy")
            
            # Check for sponsor order patterns
            print(f"\n🍽️  SPONSOR ORDER ANALYSIS:")
            for sponsor_name in sponsor_employees:
                sponsor_data = employee_orders[sponsor_name]
                sponsor_total = sponsor_data.get("total_amount", 0)
                
                # Try to break down sponsor cost
                print(f"   Sponsor: {sponsor_name}")
                print(f"   Total: €{sponsor_total:.2f}")
                
                # Estimate sponsor breakdown
                # Sponsor typically pays: own meal + sponsored meals for others
                sponsored_count = len(sponsored_employees)
                if sponsored_count > 0:
                    estimated_sponsored_cost = sponsored_count * 5.0  # Assume €5 per lunch
                    estimated_own_cost = sponsor_total - estimated_sponsored_cost
                    print(f"   Estimated own cost: €{estimated_own_cost:.2f}")
                    print(f"   Estimated sponsored cost: €{estimated_sponsored_cost:.2f} ({sponsored_count} × €5.00)")
                    
                    # Check for 5€ discrepancy in sponsor calculation
                    if abs(estimated_own_cost - 5.0) < 0.01:
                        print(f"   🎯 POTENTIAL 5€ DISCREPANCY: Sponsor's own cost might be inflated by €5.00")
            
            return True
                
        except Exception as e:
            print(f"❌ Analysis error: {str(e)}")
            return False
    
    def check_daily_summary_endpoint(self):
        """Check the daily summary endpoint for comparison"""
        try:
            print(f"\n🔍 COMPARING WITH DAILY SUMMARY ENDPOINT")
            print("=" * 50)
            
            # Get daily summary
            response = self.session.get(f"{BASE_URL}/orders/daily-summary/{DEPARTMENT_ID}")
            
            if response.status_code != 200:
                print(f"❌ Could not fetch daily summary: HTTP {response.status_code}: {response.text}")
                return False
            
            daily_summary = response.json()
            employee_orders = daily_summary.get("employee_orders", {})
            
            print(f"📊 Daily Summary Employee Count: {len(employee_orders)}")
            
            # Calculate total from daily summary
            daily_sum = 0
            for employee_name, order_data in employee_orders.items():
                # Note: daily summary doesn't have total_amount field, need to calculate
                # This is a simplified calculation
                has_lunch = order_data.get("has_lunch", False)
                boiled_eggs = order_data.get("boiled_eggs", 0)
                has_coffee = order_data.get("has_coffee", False)
                white_halves = order_data.get("white_halves", 0)
                seeded_halves = order_data.get("seeded_halves", 0)
                
                # Estimate cost (simplified)
                estimated_cost = 0
                estimated_cost += (white_halves + seeded_halves) * 0.50  # Assume €0.50 per half
                estimated_cost += boiled_eggs * 0.50
                if has_coffee:
                    estimated_cost += 1.50
                if has_lunch:
                    estimated_cost += 5.00
                
                daily_sum += estimated_cost
                
                print(f"   {employee_name:25} | L:{has_lunch} E:{boiled_eggs} C:{has_coffee} R:{white_halves + seeded_halves} | ~€{estimated_cost:.2f}")
            
            print(f"\n📈 Daily Summary Estimated Total: €{daily_sum:.2f}")
            
            return True
                
        except Exception as e:
            print(f"❌ Daily summary check error: {str(e)}")
            return False
    
    def run_analysis(self):
        """Run the complete analysis"""
        print("🎯 ANALYZING 5€ DISCREPANCY IN SPONSORED MEALS")
        print("=" * 80)
        print("GOAL: Identify the source of the 5€ extra in daily summary calculations")
        print("FOCUS: /api/orders/breakfast-history/{department_id} endpoint")
        print("=" * 80)
        
        if not self.authenticate_admin():
            return False
        
        success = True
        
        if not self.analyze_breakfast_history():
            success = False
        
        if not self.check_daily_summary_endpoint():
            success = False
        
        print(f"\n" + "=" * 80)
        print("🎯 ANALYSIS SUMMARY")
        print("=" * 80)
        
        if success:
            print("✅ Analysis completed successfully")
            print("📋 Key findings should be visible above")
            print("🔍 Look for employees with 5€ discrepancies or sponsor calculation issues")
        else:
            print("❌ Analysis encountered errors")
        
        return success

if __name__ == "__main__":
    analyzer = AnalyzeFiveEuroDiscrepancy()
    success = analyzer.run_analysis()
    sys.exit(0 if success else 1)