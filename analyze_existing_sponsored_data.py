#!/usr/bin/env python3
"""
ANALYZE EXISTING SPONSORED DATA FOR NEGATIVE BALANCE ISSUE

Since lunch sponsoring has already been completed today, let's analyze the existing 
sponsored data to understand where the negative balance issue (-17.50€) is coming from.

This will help us identify the root cause of the problem in the sponsor balance calculation.
"""

import requests
import json
import sys
from datetime import datetime, date, timedelta

# Configuration
BASE_URL = "https://fire-dept-cafe.preview.emergentagent.com/api"
DEPARTMENT_NAME = "2. Wachabteilung"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"

class AnalyzeExistingSponsoredData:
    def __init__(self):
        self.session = requests.Session()
        self.admin_auth = None
        
    def authenticate_admin(self):
        """Authenticate as department admin"""
        try:
            response = self.session.post(f"{BASE_URL}/login/department-admin", json={
                "department_name": DEPARTMENT_NAME,
                "admin_password": ADMIN_PASSWORD
            })
            
            if response.status_code == 200:
                self.admin_auth = response.json()
                print(f"✅ Successfully authenticated as admin for {DEPARTMENT_NAME}")
                return True
            else:
                print(f"❌ Authentication failed: HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Authentication error: {str(e)}")
            return False
    
    def analyze_employee_balances(self):
        """Analyze all employee balances to find negative balances"""
        try:
            print(f"\n🔍 ANALYZING EMPLOYEE BALANCES IN DEPARTMENT 2:")
            print("=" * 60)
            
            # Get all employees in department
            response = self.session.get(f"{BASE_URL}/departments/{DEPARTMENT_ID}/employees")
            if response.status_code != 200:
                print(f"❌ Could not fetch employees: {response.status_code} - {response.text}")
                return False
            
            employees = response.json()
            
            negative_balances = []
            positive_balances = []
            zero_balances = []
            
            for employee in employees:
                name = employee.get("name", "Unknown")
                balance = employee.get("breakfast_balance", 0)
                employee_id = employee.get("id", "")
                
                print(f"- {name}: €{balance:.2f} (ID: {employee_id[-8:]})")
                
                if balance < -0.01:
                    negative_balances.append((name, balance, employee_id))
                elif balance > 0.01:
                    positive_balances.append((name, balance, employee_id))
                else:
                    zero_balances.append((name, balance, employee_id))
            
            print(f"\n📊 BALANCE SUMMARY:")
            print(f"- Negative balances: {len(negative_balances)}")
            print(f"- Positive balances: {len(positive_balances)}")
            print(f"- Zero balances: {len(zero_balances)}")
            
            # Focus on negative balances
            if negative_balances:
                print(f"\n🚨 NEGATIVE BALANCES FOUND:")
                for name, balance, emp_id in negative_balances:
                    print(f"- {name}: €{balance:.2f}")
                    
                    # Check if this matches the -17.50€ issue
                    if abs(balance + 17.50) < 1.0:
                        print(f"  🎯 EXACT MATCH: This is the -17.50€ issue mentioned in review request!")
                        return emp_id, balance
                    elif balance < -10.0:
                        print(f"  ⚠️ SIGNIFICANT NEGATIVE BALANCE: This could be related to the issue")
                        return emp_id, balance
            
            return None, None
                
        except Exception as e:
            print(f"❌ Error analyzing balances: {str(e)}")
            return None, None
    
    def analyze_breakfast_history(self):
        """Analyze breakfast history to understand sponsored orders"""
        try:
            print(f"\n🔍 ANALYZING BREAKFAST HISTORY FOR SPONSORED ORDERS:")
            print("=" * 60)
            
            # Get breakfast history for today
            response = self.session.get(f"{BASE_URL}/orders/breakfast-history/{DEPARTMENT_ID}?days_back=1")
            if response.status_code != 200:
                print(f"❌ Could not fetch breakfast history: {response.status_code} - {response.text}")
                return False
            
            history_data = response.json()
            history_entries = history_data.get("history", [])
            
            if not history_entries:
                print("❌ No history entries found")
                return False
            
            # Get today's entry
            today_entry = history_entries[0]
            today_date = date.today().isoformat()
            
            print(f"📅 Date: {today_entry.get('date', 'Unknown')}")
            print(f"📊 Total orders: {today_entry.get('total_orders', 0)}")
            print(f"💰 Total amount: €{today_entry.get('total_amount', 0):.2f}")
            
            # Analyze employee orders
            employee_orders = today_entry.get("employee_orders", {})
            
            print(f"\n👥 INDIVIDUAL EMPLOYEE ORDERS:")
            sponsored_employees = []
            sponsor_employees = []
            
            for emp_name, emp_data in employee_orders.items():
                amount = emp_data.get("total_amount", 0)
                white_halves = emp_data.get("white_halves", 0)
                seeded_halves = emp_data.get("seeded_halves", 0)
                has_lunch = emp_data.get("has_lunch", False)
                boiled_eggs = emp_data.get("boiled_eggs", 0)
                
                print(f"- {emp_name}: €{amount:.2f}")
                print(f"  - Rolls: {white_halves} white + {seeded_halves} seeded halves")
                print(f"  - Lunch: {'Yes' if has_lunch else 'No'}")
                print(f"  - Eggs: {boiled_eggs}")
                
                if abs(amount) < 0.01:
                    sponsored_employees.append(emp_name)
                    print(f"  🎯 SPONSORED EMPLOYEE (€0.00)")
                elif amount < -0.01:
                    print(f"  🚨 NEGATIVE BALANCE: €{amount:.2f}")
                elif amount > 20.0:  # Likely sponsor
                    sponsor_employees.append((emp_name, amount))
                    print(f"  💰 POTENTIAL SPONSOR (high balance)")
            
            print(f"\n📋 SPONSORED DATA SUMMARY:")
            print(f"- Sponsored employees (€0.00): {len(sponsored_employees)}")
            print(f"- Potential sponsors (high balance): {len(sponsor_employees)}")
            
            if sponsor_employees:
                print(f"\n💰 SPONSOR ANALYSIS:")
                for sponsor_name, sponsor_amount in sponsor_employees:
                    print(f"- {sponsor_name}: €{sponsor_amount:.2f}")
                    
                    # Check if this is a negative sponsor balance
                    if sponsor_amount < 0:
                        print(f"  🚨 NEGATIVE SPONSOR BALANCE FOUND!")
                        if abs(sponsor_amount + 17.50) < 1.0:
                            print(f"  🎯 EXACT MATCH: This is the -17.50€ issue!")
                        return sponsor_name, sponsor_amount
            
            return None, None
                
        except Exception as e:
            print(f"❌ Error analyzing breakfast history: {str(e)}")
            return None, None
    
    def examine_sponsor_meal_endpoint_logic(self):
        """Examine what might be causing the negative balance in sponsor calculations"""
        try:
            print(f"\n🔍 EXAMINING SPONSOR MEAL CALCULATION LOGIC:")
            print("=" * 60)
            
            # Try to understand the current state by checking if we can get more details
            # about the sponsoring that happened today
            
            print("Based on the expected logic:")
            print("1. Sponsor initial balance: 7.50€ (from own order)")
            print("2. Total sponsored cost: 25€ (5 employees × 5€ lunch each)")
            print("3. Sponsor contributed amount: 5€ (sponsor's own lunch)")
            print("4. Sponsor additional cost: 25€ - 5€ = 20€")
            print("5. Final sponsor balance: 7.50€ + 20€ = 27.50€")
            print()
            print("But we're getting -17.50€ instead.")
            print()
            print("🚨 POSSIBLE CAUSES:")
            print("1. Sign error: -27.50€ instead of +27.50€")
            print("2. Wrong calculation: subtracting instead of adding")
            print("3. Double subtraction: subtracting both own cost and total cost")
            print("4. Incorrect formula in sponsor_additional_cost calculation")
            
            # The difference between expected (27.50€) and actual (-17.50€) is 45€
            difference = 27.50 - (-17.50)
            print(f"\n📊 CALCULATION ANALYSIS:")
            print(f"- Expected: €27.50")
            print(f"- Actual: €-17.50")
            print(f"- Difference: €{difference:.2f}")
            print(f"- This suggests the calculation is off by €45.00")
            print(f"- Possible issue: Adding/subtracting €45.00 incorrectly")
            
            return True
                
        except Exception as e:
            print(f"❌ Error examining logic: {str(e)}")
            return False

    def run_analysis(self):
        """Run complete analysis of existing sponsored data"""
        print("🔍 ANALYZING EXISTING SPONSORED DATA FOR NEGATIVE BALANCE ISSUE")
        print("=" * 80)
        print("GOAL: Find and analyze the -17.50€ negative balance issue")
        print("DEPARTMENT: 2. Wachabteilung")
        print("=" * 80)
        
        # Authenticate
        if not self.authenticate_admin():
            return False
        
        # Analyze employee balances
        problem_employee_id, problem_balance = self.analyze_employee_balances()
        
        # Analyze breakfast history
        sponsor_name, sponsor_balance = self.analyze_breakfast_history()
        
        # Examine the logic
        self.examine_sponsor_meal_endpoint_logic()
        
        # Summary
        print(f"\n" + "=" * 80)
        print("🔍 ANALYSIS SUMMARY")
        print("=" * 80)
        
        if problem_employee_id or sponsor_name:
            print("🎯 NEGATIVE BALANCE ISSUE IDENTIFIED!")
            if problem_employee_id:
                print(f"- Found employee with negative balance: €{problem_balance:.2f}")
            if sponsor_name:
                print(f"- Found sponsor with negative balance: {sponsor_name} = €{sponsor_balance:.2f}")
            
            print("\n🚨 ROOT CAUSE ANALYSIS:")
            print("The negative balance suggests an error in the sponsor balance calculation logic.")
            print("This is likely in the /api/department-admin/sponsor-meal endpoint.")
            print("The calculation should be: initial_balance + additional_cost")
            print("But it might be: initial_balance - additional_cost (wrong sign)")
            print("Or: initial_balance - total_cost (wrong formula)")
            
            return True
        else:
            print("❌ Could not identify the specific negative balance issue in current data.")
            print("The issue might have been resolved or the data might have been cleaned up.")
            return False

if __name__ == "__main__":
    analyzer = AnalyzeExistingSponsoredData()
    success = analyzer.run_analysis()
    sys.exit(0 if success else 1)