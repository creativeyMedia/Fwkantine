#!/usr/bin/env python3
"""
Timezone Debug Test - Understanding the Berlin Timezone Issue

This test investigates the timezone boundary issue that's causing the breakfast day deletion to fail.
"""

import requests
import json
from datetime import datetime, timezone
import pytz
import os

# Configuration
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'https://canteenio.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"
DEPARTMENT_ID = "fw4abteilung2"
ADMIN_PASSWORD = "admin2"
DEPARTMENT_NAME = "2. Wachabteilung"

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

def get_berlin_now():
    """Get current time in Berlin timezone"""
    return datetime.now(BERLIN_TZ)

def get_berlin_date():
    """Get current date in Berlin timezone"""
    return get_berlin_now().date()

def get_berlin_day_bounds(date_obj):
    """Get start and end of day in Berlin timezone for a given date"""
    if isinstance(date_obj, str):
        date_obj = datetime.strptime(date_obj, '%Y-%m-%d').date()
    
    # Create datetime objects for start and end of day in Berlin timezone
    start_of_day = BERLIN_TZ.localize(datetime.combine(date_obj, datetime.min.time()))
    end_of_day = BERLIN_TZ.localize(datetime.combine(date_obj, datetime.max.time()))
    
    # Convert to UTC for database storage
    start_of_day_utc = start_of_day.astimezone(timezone.utc)
    end_of_day_utc = end_of_day.astimezone(timezone.utc)
    
    return start_of_day_utc, end_of_day_utc

def debug_timezone_boundaries():
    """Debug timezone boundaries"""
    print("🕐 TIMEZONE BOUNDARY ANALYSIS")
    print("=" * 50)
    
    # Current times
    utc_now = datetime.now(timezone.utc)
    berlin_now = get_berlin_now()
    berlin_date = get_berlin_date()
    
    print(f"UTC Now:    {utc_now}")
    print(f"Berlin Now: {berlin_now}")
    print(f"Berlin Date: {berlin_date}")
    
    # Today's boundaries
    start_utc, end_utc = get_berlin_day_bounds(berlin_date)
    print(f"\nToday's Berlin Day Bounds (in UTC):")
    print(f"Start: {start_utc}")
    print(f"End:   {end_utc}")
    
    # Check if current UTC time falls within today's Berlin boundaries
    in_bounds = start_utc <= utc_now <= end_utc
    print(f"\nCurrent UTC time in today's Berlin bounds: {in_bounds}")
    
    if not in_bounds:
        print("⚠️ TIMEZONE ISSUE DETECTED!")
        if utc_now < start_utc:
            print("   Current UTC time is BEFORE today's Berlin day start")
        else:
            print("   Current UTC time is AFTER today's Berlin day end")

def test_order_timestamps():
    """Test order creation and timestamp analysis"""
    print("\n📋 ORDER TIMESTAMP ANALYSIS")
    print("=" * 50)
    
    session = requests.Session()
    
    # Authenticate
    response = session.post(f"{API_BASE}/login/department-admin", json={
        "department_name": DEPARTMENT_NAME,
        "admin_password": ADMIN_PASSWORD
    })
    
    if response.status_code != 200:
        print("❌ Authentication failed")
        return
    
    print("✅ Authenticated successfully")
    
    # Get breakfast history to see existing orders
    response = session.get(f"{API_BASE}/orders/breakfast-history/{DEPARTMENT_ID}")
    
    if response.status_code == 200:
        history_data = response.json()
        
        if isinstance(history_data, dict) and "history" in history_data:
            print(f"\nFound {len(history_data['history'])} days in history:")
            
            for day_data in history_data["history"]:
                date = day_data.get("date")
                orders_count = len(day_data.get("employee_orders", []))
                print(f"  {date}: {orders_count} orders")
                
                # Check if this is today
                berlin_date_str = get_berlin_date().isoformat()
                if date == berlin_date_str:
                    print(f"    ✅ This is today's date in Berlin timezone")
                else:
                    print(f"    📅 This is not today ({berlin_date_str})")

def main():
    """Main debug execution"""
    print("🚨 TIMEZONE DEBUG TEST: Berlin Timezone Boundary Analysis")
    print("=" * 80)
    
    debug_timezone_boundaries()
    test_order_timestamps()
    
    print(f"\n🔍 ANALYSIS COMPLETE")

if __name__ == "__main__":
    main()