#!/usr/bin/env python3
"""
Debug script to check orders directly in database
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from datetime import datetime, timezone, timedelta
import pytz

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

def get_berlin_date():
    """Get current date in Berlin timezone"""
    return datetime.now(BERLIN_TZ).date()

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

async def debug_database_orders():
    """Debug orders directly in database"""
    department_id = "fw4abteilung1"
    today = get_berlin_date()
    start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(today)
    
    print(f"🔍 DEBUGGING DATABASE ORDERS FOR {today}")
    print(f"   Department: {department_id}")
    print(f"   Time range: {start_of_day_utc} to {end_of_day_utc}")
    print("=" * 80)
    
    # Get all orders for today
    orders = await db.orders.find({
        "department_id": department_id,
        "timestamp": {
            "$gte": start_of_day_utc.isoformat(),
            "$lte": end_of_day_utc.isoformat()
        }
    }).to_list(1000)
    
    print(f"\n📊 Found {len(orders)} total orders:")
    
    sponsor_orders = []
    regular_orders = []
    
    for order in orders:
        employee_id = order.get("employee_id", "Unknown")
        is_sponsor_order = order.get("is_sponsor_order", False)
        is_sponsored = order.get("is_sponsored", False)
        sponsored_meal_type = order.get("sponsored_meal_type", "")
        total_price = order.get("total_price", 0)
        
        print(f"\n📋 Order ID: {order.get('id', 'No ID')}")
        print(f"   Employee ID: {employee_id}")
        print(f"   Total Price: €{total_price:.2f}")
        print(f"   is_sponsor_order: {is_sponsor_order}")
        print(f"   is_sponsored: {is_sponsored}")
        print(f"   sponsored_meal_type: '{sponsored_meal_type}'")
        
        if is_sponsor_order:
            sponsor_orders.append(order)
            print(f"   🎯 SPONSOR ORDER DETAILS:")
            print(f"      - sponsor_employee_count: {order.get('sponsor_employee_count', 'N/A')}")
            print(f"      - sponsor_total_cost: {order.get('sponsor_total_cost', 'N/A')}")
            print(f"      - sponsor_message: {order.get('sponsor_message', 'N/A')}")
        else:
            regular_orders.append(order)
            if is_sponsored:
                print(f"   🎁 SPONSORED ORDER DETAILS:")
                print(f"      - sponsored_by_employee_id: {order.get('sponsored_by_employee_id', 'N/A')}")
                print(f"      - sponsored_by_name: {order.get('sponsored_by_name', 'N/A')}")
                print(f"      - sponsored_message: {order.get('sponsored_message', 'N/A')}")
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total orders: {len(orders)}")
    print(f"   Sponsor orders: {len(sponsor_orders)}")
    print(f"   Regular orders: {len(regular_orders)}")
    
    # Get employees to match IDs to names
    employees = await db.employees.find({"department_id": department_id}).to_list(100)
    employee_map = {emp["id"]: emp["name"] for emp in employees}
    
    print(f"\n👥 EMPLOYEE MAPPING:")
    for emp_id, emp_name in employee_map.items():
        print(f"   {emp_name}: {emp_id}")
    
    # Now test the sponsor order lookup logic
    print(f"\n🔍 TESTING SPONSOR ORDER LOOKUP LOGIC:")
    print("=" * 80)
    
    for emp_id, emp_name in employee_map.items():
        print(f"\n👤 Testing {emp_name} (ID: {emp_id}):")
        
        # This is the exact query from the breakfast-history endpoint
        sponsor_orders_for_employee = await db.orders.find({
            "department_id": department_id,
            "employee_id": emp_id,  # Orders belonging to this employee
            "is_sponsor_order": True,    # This employee sponsored someone
            "timestamp": {
                "$gte": start_of_day_utc.isoformat(),
                "$lte": end_of_day_utc.isoformat()
            }
        }).to_list(1000)
        
        print(f"   Found {len(sponsor_orders_for_employee)} sponsor orders")
        
        breakfast_sponsored_info = None
        lunch_sponsored_info = None
        
        if sponsor_orders_for_employee:
            for sponsor_order in sponsor_orders_for_employee:
                sponsor_meal_type = sponsor_order.get("sponsored_meal_type", "")
                sponsor_count = sponsor_order.get("sponsor_employee_count", 0)
                sponsor_cost = sponsor_order.get("sponsor_total_cost", 0.0)
                
                print(f"      Sponsor order: meal_type='{sponsor_meal_type}', count={sponsor_count}, cost=€{sponsor_cost:.2f}")
                
                # Extract meal type from sponsor order
                if "breakfast" in sponsor_meal_type.lower():
                    breakfast_sponsored_info = {
                        "count": sponsor_count,
                        "amount": round(sponsor_cost, 2)
                    }
                elif "lunch" in sponsor_meal_type.lower() or "mittag" in sponsor_meal_type.lower():
                    lunch_sponsored_info = {
                        "count": sponsor_count,
                        "amount": round(sponsor_cost, 2)
                    }
        
        print(f"   Result - sponsored_breakfast: {breakfast_sponsored_info}")
        print(f"   Result - sponsored_lunch: {lunch_sponsored_info}")

if __name__ == "__main__":
    asyncio.run(debug_database_orders())