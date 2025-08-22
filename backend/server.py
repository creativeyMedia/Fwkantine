from fastapi import FastAPI, APIRouter, HTTPException, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timezone
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Helper functions for MongoDB date serialization
def prepare_for_mongo(data):
    """Convert date/time objects to ISO strings for MongoDB storage"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    """Parse ISO strings back to datetime objects from MongoDB"""
    if isinstance(item, dict) and 'timestamp' in item:
        if isinstance(item['timestamp'], str):
            item['timestamp'] = datetime.fromisoformat(item['timestamp'])
    return item

# Enums
class OrderType(str, Enum):
    BREAKFAST = "breakfast"
    DRINKS = "drinks" 
    SWEETS = "sweets"

class RollType(str, Enum):
    LIGHT = "hell"  # Light roll
    DARK = "dunkel"  # Dark roll
    WHOLEMEAL = "vollkorn"  # Wholemeal roll

class ToppingType(str, Enum):
    SCRAMBLED_EGG = "ruehrei"
    FRIED_EGG = "spiegelei"
    EGG_SALAD = "eiersalat"
    SALAMI = "salami"
    HAM = "schinken"
    CHEESE = "kaese"
    BUTTER = "butter"

# Models
class Department(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    password_hash: str  # In production, this should be properly hashed
    admin_password_hash: str = "admin123"  # Department admin password
    
class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    department_id: str
    breakfast_balance: float = 0.0
    drinks_sweets_balance: float = 0.0
    
class MenuItemBreakfast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    roll_type: RollType
    price: float
    
class MenuItemToppings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topping_type: ToppingType
    price: float
    
class MenuItemDrink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: float
    
class MenuItemSweet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    price: float

class BreakfastOrder(BaseModel):
    roll_type: RollType
    roll_count: int
    toppings: List[ToppingType]
    
class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    department_id: str
    order_type: OrderType
    breakfast_items: Optional[List[BreakfastOrder]] = []
    drink_items: Optional[Dict[str, int]] = {}  # drink_id -> quantity
    sweet_items: Optional[Dict[str, int]] = {}  # sweet_id -> quantity
    total_price: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request/Response Models
class DepartmentLogin(BaseModel):
    department_name: str
    password: str
    
class AdminLogin(BaseModel):
    password: str
    
class EmployeeCreate(BaseModel):
    name: str
    department_id: str

class OrderCreate(BaseModel):
    employee_id: str
    department_id: str
    order_type: OrderType
    breakfast_items: Optional[List[BreakfastOrder]] = []
    drink_items: Optional[Dict[str, int]] = {}
    sweet_items: Optional[Dict[str, int]] = {}

# Initialize default data
@api_router.post("/init-data")
async def initialize_default_data():
    """Initialize the database with default departments and menu items"""
    
    # Check if data already exists
    existing_depts = await db.departments.find().to_list(1)
    if existing_depts:
        return {"message": "Data already initialized"}
    
    # Create 4 watch departments
    departments = [
        Department(name="Wachabteilung A", password_hash="passwordA"),
        Department(name="Wachabteilung B", password_hash="passwordB"),
        Department(name="Wachabteilung C", password_hash="passwordC"),
        Department(name="Wachabteilung D", password_hash="passwordD")
    ]
    
    for dept in departments:
        await db.departments.insert_one(dept.dict())
    
    # Create default menu items
    breakfast_items = [
        MenuItemBreakfast(roll_type=RollType.LIGHT, price=0.50),
        MenuItemBreakfast(roll_type=RollType.DARK, price=0.55),
        MenuItemBreakfast(roll_type=RollType.WHOLEMEAL, price=0.60)
    ]
    
    toppings = [
        MenuItemToppings(topping_type=ToppingType.SCRAMBLED_EGG, price=1.20),
        MenuItemToppings(topping_type=ToppingType.FRIED_EGG, price=1.00),
        MenuItemToppings(topping_type=ToppingType.EGG_SALAD, price=0.80),
        MenuItemToppings(topping_type=ToppingType.SALAMI, price=1.50),
        MenuItemToppings(topping_type=ToppingType.HAM, price=1.30),
        MenuItemToppings(topping_type=ToppingType.CHEESE, price=0.70),
        MenuItemToppings(topping_type=ToppingType.BUTTER, price=0.30)
    ]
    
    drinks = [
        MenuItemDrink(name="Kaffee", price=1.00),
        MenuItemDrink(name="Tee", price=0.80),
        MenuItemDrink(name="Wasser", price=0.50),
        MenuItemDrink(name="Orangensaft", price=1.50),
        MenuItemDrink(name="Apfelsaft", price=1.50),
        MenuItemDrink(name="Cola", price=1.20)
    ]
    
    sweets = [
        MenuItemSweet(name="Schokoriegel", price=1.50),
        MenuItemSweet(name="Keks", price=0.80),
        MenuItemSweet(name="Apfel", price=0.60),
        MenuItemSweet(name="Banane", price=0.50),
        MenuItemSweet(name="Kuchen", price=2.00)
    ]
    
    # Insert menu items
    for item in breakfast_items:
        await db.menu_breakfast.insert_one(item.dict())
    for item in toppings:
        await db.menu_toppings.insert_one(item.dict())
    for item in drinks:
        await db.menu_drinks.insert_one(item.dict())
    for item in sweets:
        await db.menu_sweets.insert_one(item.dict())
    
    return {"message": "Daten erfolgreich initialisiert"}

# Authentication routes
@api_router.post("/login/department")
async def department_login(login_data: DepartmentLogin):
    """Login for department with password"""
    dept = await db.departments.find_one({"name": login_data.department_name})
    if not dept or dept["password_hash"] != login_data.password:
        raise HTTPException(status_code=401, detail="Ungültiger Name oder Passwort")
    
    return {"department_id": dept["id"], "department_name": dept["name"]}

@api_router.post("/login/admin") 
async def admin_login(login_data: AdminLogin):
    """Admin login"""
    if login_data.password != "admin123":  # In production, use proper authentication
        raise HTTPException(status_code=401, detail="Ungültiges Admin-Passwort")
    
    return {"message": "Admin erfolgreich angemeldet", "role": "admin"}

# Department routes
@api_router.get("/departments", response_model=List[Department])
async def get_departments():
    """Get all departments for homepage display"""
    departments = await db.departments.find().to_list(100)
    return [Department(**dept) for dept in departments]

# Employee routes
@api_router.get("/departments/{department_id}/employees", response_model=List[Employee])
async def get_department_employees(department_id: str):
    """Get all employees for a specific department"""
    employees = await db.employees.find({"department_id": department_id}).to_list(100)
    return [Employee(**emp) for emp in employees]

@api_router.post("/employees", response_model=Employee)
async def create_employee(employee_data: EmployeeCreate):
    """Create a new employee"""
    employee = Employee(**employee_data.dict())
    await db.employees.insert_one(employee.dict())
    return employee

# Menu routes
@api_router.get("/menu/breakfast", response_model=List[MenuItemBreakfast])
async def get_breakfast_menu():
    items = await db.menu_breakfast.find().to_list(100)
    return [MenuItemBreakfast(**item) for item in items]

@api_router.get("/menu/toppings", response_model=List[MenuItemToppings])
async def get_toppings_menu():
    items = await db.menu_toppings.find().to_list(100)
    return [MenuItemToppings(**item) for item in items]

@api_router.get("/menu/drinks", response_model=List[MenuItemDrink])
async def get_drinks_menu():
    items = await db.menu_drinks.find().to_list(100)
    return [MenuItemDrink(**item) for item in items]

@api_router.get("/menu/sweets", response_model=List[MenuItemSweet])
async def get_sweets_menu():
    items = await db.menu_sweets.find().to_list(100)
    return [MenuItemSweet(**item) for item in items]

# Order routes
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate):
    """Create a new order and update employee balance"""
    
    # Calculate total price
    total_price = 0.0
    
    if order_data.order_type == OrderType.BREAKFAST and order_data.breakfast_items:
        # Get breakfast menu prices
        breakfast_menu = await db.menu_breakfast.find().to_list(100)
        toppings_menu = await db.menu_toppings.find().to_list(100)
        
        breakfast_prices = {item["roll_type"]: item["price"] for item in breakfast_menu}
        topping_prices = {item["topping_type"]: item["price"] for item in toppings_menu}
        
        for breakfast_item in order_data.breakfast_items:
            # Roll price
            roll_price = breakfast_prices.get(breakfast_item.roll_type, 0.0)
            total_price += roll_price * breakfast_item.roll_count
            
            # Toppings price
            for topping in breakfast_item.toppings:
                topping_price = topping_prices.get(topping, 0.0)
                total_price += topping_price * breakfast_item.roll_count
    
    elif order_data.order_type == OrderType.DRINKS and order_data.drink_items:
        drinks_menu = await db.menu_drinks.find().to_list(100)
        drink_prices = {item["id"]: item["price"] for item in drinks_menu}
        
        for drink_id, quantity in order_data.drink_items.items():
            drink_price = drink_prices.get(drink_id, 0.0)
            total_price += drink_price * quantity
            
    elif order_data.order_type == OrderType.SWEETS and order_data.sweet_items:
        sweets_menu = await db.menu_sweets.find().to_list(100)
        sweet_prices = {item["id"]: item["price"] for item in sweets_menu}
        
        for sweet_id, quantity in order_data.sweet_items.items():
            sweet_price = sweet_prices.get(sweet_id, 0.0)
            total_price += sweet_price * quantity
    
    # Create order
    order = Order(**order_data.dict(), total_price=total_price)
    order_dict = prepare_for_mongo(order.dict())
    await db.orders.insert_one(order_dict)
    
    # Update employee balance
    employee = await db.employees.find_one({"id": order_data.employee_id})
    if employee:
        if order_data.order_type == OrderType.BREAKFAST:
            new_breakfast_balance = employee["breakfast_balance"] + total_price
            await db.employees.update_one(
                {"id": order_data.employee_id},
                {"$set": {"breakfast_balance": new_breakfast_balance}}
            )
        else:  # DRINKS or SWEETS
            new_drinks_sweets_balance = employee["drinks_sweets_balance"] + total_price
            await db.employees.update_one(
                {"id": order_data.employee_id},
                {"$set": {"drinks_sweets_balance": new_drinks_sweets_balance}}
            )
    
    return order

@api_router.get("/orders/daily-summary/{department_id}")
async def get_daily_summary(department_id: str):
    """Get daily summary of all orders for a department"""
    today = datetime.now(timezone.utc).date()
    start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    # Get today's orders
    orders = await db.orders.find({
        "department_id": department_id,
        "timestamp": {
            "$gte": start_of_day.isoformat(),
            "$lte": end_of_day.isoformat()
        }
    }).to_list(1000)
    
    # Aggregate breakfast orders
    breakfast_summary = {}
    drinks_summary = {}
    sweets_summary = {}
    
    for order in orders:
        if order["order_type"] == "breakfast" and order.get("breakfast_items"):
            for item in order["breakfast_items"]:
                roll_type = item["roll_type"]
                if roll_type not in breakfast_summary:
                    breakfast_summary[roll_type] = {"count": 0, "toppings": {}}
                
                breakfast_summary[roll_type]["count"] += item["roll_count"]
                
                for topping in item["toppings"]:
                    if topping not in breakfast_summary[roll_type]["toppings"]:
                        breakfast_summary[roll_type]["toppings"][topping] = 0
                    breakfast_summary[roll_type]["toppings"][topping] += item["roll_count"]
        
        elif order["order_type"] == "drinks" and order.get("drink_items"):
            for drink_id, quantity in order["drink_items"].items():
                if drink_id not in drinks_summary:
                    drinks_summary[drink_id] = 0
                drinks_summary[drink_id] += quantity
                
        elif order["order_type"] == "sweets" and order.get("sweet_items"):
            for sweet_id, quantity in order["sweet_items"].items():
                if sweet_id not in sweets_summary:
                    sweets_summary[sweet_id] = 0
                sweets_summary[sweet_id] += quantity
    
    return {
        "date": today.isoformat(),
        "breakfast_summary": breakfast_summary,
        "drinks_summary": drinks_summary,
        "sweets_summary": sweets_summary
    }

@api_router.get("/orders/employee/{employee_id}")
async def get_employee_orders(employee_id: str):
    """Get all orders for a specific employee"""
    orders = await db.orders.find({"employee_id": employee_id}).to_list(1000)
    return [parse_from_mongo(order) for order in orders]

# Admin routes
@api_router.delete("/orders/{order_id}")
async def delete_order(order_id: str):
    """Admin: Delete an order and adjust employee balance"""
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
    
    # Adjust employee balance
    employee = await db.employees.find_one({"id": order["employee_id"]})
    if employee:
        if order["order_type"] == "breakfast":
            new_breakfast_balance = employee["breakfast_balance"] - order["total_price"]
            await db.employees.update_one(
                {"id": order["employee_id"]},
                {"$set": {"breakfast_balance": max(0, new_breakfast_balance)}}
            )
        else:
            new_drinks_sweets_balance = employee["drinks_sweets_balance"] - order["total_price"]
            await db.employees.update_one(
                {"id": order["employee_id"]},
                {"$set": {"drinks_sweets_balance": max(0, new_drinks_sweets_balance)}}
            )
    
    # Delete order
    await db.orders.delete_one({"id": order_id})
    return {"message": "Bestellung erfolgreich gelöscht"}

@api_router.post("/admin/reset-balance/{employee_id}")
async def reset_employee_balance(employee_id: str, balance_type: str):
    """Admin: Reset employee balance (breakfast or drinks_sweets)"""
    if balance_type == "breakfast":
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": {"breakfast_balance": 0.0}}
        )
    elif balance_type == "drinks_sweets":
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": {"drinks_sweets_balance": 0.0}}
        )
    else:
        raise HTTPException(status_code=400, detail="Ungültiger Saldo-Typ")
    
    return {"message": f"Saldo erfolgreich zurückgesetzt"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()