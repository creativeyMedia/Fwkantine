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
from datetime import datetime, timezone, timedelta
from enum import Enum
import pytz

# Berlin timezone
BERLIN_TZ = pytz.timezone('Europe/Berlin')

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

# Berlin timezone helper functions
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

# Enums
class OrderType(str, Enum):
    BREAKFAST = "breakfast"
    DRINKS = "drinks" 
    SWEETS = "sweets"

class RollType(str, Enum):
    WHITE = "weiss"  # White roll
    SEEDED = "koerner"  # Seeded roll

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
    id: str  # KEINE automatischen UUIDs mehr - manuell setzen
    name: str
    password_hash: str = os.environ.get('DEPARTMENT_PASSWORD_DEFAULT', 'password1')
    admin_password_hash: str = os.environ.get('ADMIN_PASSWORD_DEFAULT', 'admin1')
    
class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    department_id: str
    breakfast_balance: float = 0.0
    drinks_sweets_balance: float = 0.0
    sort_order: int = 0  # For drag & drop sorting
    
class MenuItemBreakfast(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str  # Department-specific menu items
    roll_type: RollType
    name: Optional[str] = None  # Custom name, if None use default from roll_type
    price: float
    
class MenuItemToppings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str  # Department-specific menu items
    topping_type: Optional[str] = None  # Allow custom topping types for simplified creation
    name: Optional[str] = None  # Custom name, if None use default from topping_type
    price: float
    
class MenuItemDrink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str  # Department-specific menu items
    name: str
    price: float
    
class MenuItemSweet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str  # Department-specific menu items
    name: str
    price: float

class LunchSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    price: float = 0.0
    enabled: bool = True
    boiled_eggs_price: float = 0.50  # Default price per boiled egg

class DailyLunchPrice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str
    date: str  # YYYY-MM-DD format
    lunch_price: float

class BreakfastSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str
    date: str  # YYYY-MM-DD format
    is_closed: bool = False
    closed_by: str = ""  # Admin who closed it
    closed_at: Optional[datetime] = None

class PaymentLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    department_id: str
    amount: float
    payment_type: str  # "breakfast" or "drinks_sweets"
    action: str  # "payment" or "reset"
    admin_user: str  # department name who performed action
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""

class BreakfastOrder(BaseModel):
    total_halves: int  # Total number of roll halves
    white_halves: int  # Number of white roll halves
    seeded_halves: int  # Number of seeded roll halves
    toppings: List[ToppingType]  # Exactly matches total_halves count
    has_lunch: bool = False
    boiled_eggs: int = 0  # Number of boiled breakfast eggs
    
class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str
    department_id: str
    order_type: OrderType
    breakfast_items: Optional[List[BreakfastOrder]] = []
    drink_items: Optional[Dict[str, int]] = {}  # drink_id -> quantity
    sweet_items: Optional[Dict[str, int]] = {}  # sweet_id -> quantity
    total_price: float
    has_lunch: bool = False  # Whether this order includes lunch
    lunch_price: Optional[float] = None  # The specific lunch price used for this order
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Request/Response Models
class DepartmentLogin(BaseModel):
    department_name: str
    password: str
    
class DepartmentAdminLogin(BaseModel):
    department_name: str
    admin_password: str
    
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

class MenuItemUpdate(BaseModel):
    price: Optional[float] = None
    name: Optional[str] = None

class MenuItemCreate(BaseModel):
    name: str
    price: float
    department_id: str

class MenuItemCreateBreakfast(BaseModel):
    roll_type: RollType
    price: float
    department_id: str

class MenuItemCreateToppings(BaseModel):
    topping_id: str
    topping_name: str
    price: float
    department_id: str

# Initialize default data
def get_department_data():
    """Generate department data using environment variables for passwords"""
    departments_data = []
    for i in range(1, 5):
        dept_password = os.environ.get(f'DEPT_{i}_PASSWORD', f'password{i}')
        admin_password = os.environ.get(f'DEPT_{i}_ADMIN_PASSWORD', f'admin{i}')
        
        departments_data.append(Department(
            name=f"{i}. Wachabteilung", 
            password_hash=dept_password, 
            admin_password_hash=admin_password
        ))
    return departments_data

@api_router.post("/cleanup-departments-final")
async def cleanup_departments_final():
    """Final cleanup - keep only 4 Wachabteilung departments, remove all others"""
    
    # Delete ALL existing departments
    await db.departments.delete_many({})
    
    # Create exactly 4 clean Wachabteilung departments
    departments_data = get_department_data()
    
    # Insert new departments
    for dept in departments_data:
        await db.departments.insert_one(dept.dict())
    
    return {"message": "Final cleanup complete - only 4 Wachabteilung cards", "count": 4}

@api_router.post("/cleanup-departments")
async def cleanup_departments():
    """Clean up duplicate and old departments, keep only the 4 new ones"""
    
    # Delete all existing departments
    await db.departments.delete_many({})
    
    # Create exactly 4 new departments
    departments_data = get_department_data()
    
    # Create new departments
    for dept in departments_data:
        await db.departments.insert_one(dept.dict())
    
    return {"message": "Departments cleaned up successfully", "count": 4}

@api_router.post("/init-data")
async def initialize_default_data():
    """Initialize the database with default departments and menu items
    
    CRITICAL: This function NEVER updates existing department passwords.
    It only creates new departments if they don't exist.
    This preserves user-changed passwords permanently.
    """
    
    print("🔧 DEBUG: Starting initialize_default_data...")
    
    # Check current departments
    existing_depts = await db.departments.find().to_list(100)
    print(f"🔧 DEBUG: Found {len(existing_depts)} existing departments")
    
    # CRITICAL FIX: Only create departments that don't exist
    # NEVER update existing department passwords to preserve user changes
    departments_created = 0
    departments_preserved = 0
    
    for i in range(1, 5):
        dept_name = f"{i}. Wachabteilung"
        dept_id = f"fw4abteilung{i}"  # FESTE, LESBARE ID!
        
        # Check if department already exists BY ID
        existing_dept = await db.departments.find_one({"id": dept_id})
        
        if existing_dept:
            # Department exists - DO NOT UPDATE PASSWORDS
            # This preserves user-changed passwords
            print(f"🔧 DEBUG: Department '{dept_name}' (ID: {dept_id}) exists - preserving passwords")
            departments_preserved += 1
            continue
        
        # Department doesn't exist - create it with FIXED ID
        dept_password = os.environ.get(f'DEPT_{i}_PASSWORD', f'password{i}')
        admin_password = os.environ.get(f'DEPT_{i}_ADMIN_PASSWORD', f'admin{i}')
        
        print(f"🔧 DEBUG: Creating department '{dept_name}' with FIXED ID: {dept_id}")
        
        new_department = Department(
            id=dept_id,  # FESTE ID VERWENDEN!
            name=dept_name,
            password_hash=dept_password,
            admin_password_hash=admin_password
        )
        
        result = await db.departments.insert_one(new_department.dict())
        print(f"🔧 DEBUG: Inserted department with ID: {result.inserted_id}")
        departments_created += 1
    
    print(f"🔧 DEBUG: Summary - Created: {departments_created}, Preserved: {departments_preserved}")
    
    # Check final departments
    final_depts = await db.departments.find().to_list(100)
    print(f"🔧 DEBUG: Final count: {len(final_depts)} departments")
    for dept in final_depts:
        print(f"🔧 DEBUG: Final dept: {dept['name']} - emp_pass: {dept['password_hash']}, admin_pass: {dept['admin_password_hash']}")
    
    # Check if menu items already exist (check for department-specific items)
    existing_breakfast = await db.menu_breakfast.find().to_list(1)
    if existing_breakfast:
        # Check if items have department_id (new format)
        if any("department_id" in item for item in existing_breakfast):
            return {"message": "Daten erfolgreich aktualisiert (Abteilungsspezifische Menüs bereits vorhanden)"}
        else:
            # Old global items exist, suggest migration
            return {"message": "Daten aktualisiert. Führen Sie /api/migrate-to-department-specific für abteilungsspezifische Menüs aus."}
    
    # Create department-specific default menu items for each department
    departments = await db.departments.find().to_list(100)
    
    for dept in departments:
        # Create default menu items for this department
        breakfast_items = [
            MenuItemBreakfast(department_id=dept["id"], roll_type=RollType.WHITE, price=0.50),
            MenuItemBreakfast(department_id=dept["id"], roll_type=RollType.SEEDED, price=0.60)
        ]
        
        toppings = [
            MenuItemToppings(department_id=dept["id"], topping_type=ToppingType.SCRAMBLED_EGG, price=0.00),  # Free
            MenuItemToppings(department_id=dept["id"], topping_type=ToppingType.FRIED_EGG, price=0.00),     # Free
            MenuItemToppings(department_id=dept["id"], topping_type=ToppingType.EGG_SALAD, price=0.00),     # Free
            MenuItemToppings(department_id=dept["id"], topping_type=ToppingType.SALAMI, price=0.00),        # Free
            MenuItemToppings(department_id=dept["id"], topping_type=ToppingType.HAM, price=0.00),           # Free
            MenuItemToppings(department_id=dept["id"], topping_type=ToppingType.CHEESE, price=0.00),        # Free
            MenuItemToppings(department_id=dept["id"], topping_type=ToppingType.BUTTER, price=0.00)         # Free
        ]
        
        drinks = [
            MenuItemDrink(department_id=dept["id"], name="Kaffee", price=1.00),
            MenuItemDrink(department_id=dept["id"], name="Tee", price=0.80),
            MenuItemDrink(department_id=dept["id"], name="Wasser", price=0.50),
            MenuItemDrink(department_id=dept["id"], name="Orangensaft", price=1.50),
            MenuItemDrink(department_id=dept["id"], name="Apfelsaft", price=1.50),
            MenuItemDrink(department_id=dept["id"], name="Cola", price=1.20)
        ]
        
        sweets = [
            MenuItemSweet(department_id=dept["id"], name="Schokoriegel", price=1.50),
            MenuItemSweet(department_id=dept["id"], name="Keks", price=0.80),
            MenuItemSweet(department_id=dept["id"], name="Apfel", price=0.60),
            MenuItemSweet(department_id=dept["id"], name="Banane", price=0.50),
            MenuItemSweet(department_id=dept["id"], name="Kuchen", price=2.00)
        ]
        
        # Insert menu items for this department
        for item in breakfast_items:
            await db.menu_breakfast.insert_one(item.dict())
        for item in toppings:
            await db.menu_toppings.insert_one(item.dict())
        for item in drinks:
            await db.menu_drinks.insert_one(item.dict())
        for item in sweets:
            await db.menu_sweets.insert_one(item.dict())
    
    # Create default lunch settings with explicit boiled eggs price
    lunch_settings = LunchSettings(price=0.0, enabled=True, boiled_eggs_price=0.50)
    
    # Insert lunch settings
    await db.lunch_settings.insert_one(lunch_settings.dict())
    
    return {"message": "Daten erfolgreich initialisiert"}

@api_router.post("/migrate-to-department-specific")
async def migrate_to_department_specific():
    """Migrate existing global menu items to department-specific items"""
    
    # Get all departments
    departments = await db.departments.find().to_list(100)
    if not departments:
        raise HTTPException(status_code=400, detail="Keine Abteilungen gefunden. Bitte zuerst /api/init-data aufrufen.")
    
    migration_results = {
        "breakfast_items": 0,
        "topping_items": 0, 
        "drink_items": 0,
        "sweet_items": 0,
        "departments_processed": len(departments)
    }
    
    # Migrate breakfast items
    existing_breakfast = await db.menu_breakfast.find({"department_id": {"$exists": False}}).to_list(100)
    for breakfast_item in existing_breakfast:
        # Remove MongoDB _id and create department-specific copies
        clean_item = {k: v for k, v in breakfast_item.items() if k != '_id'}
        for dept in departments:
            new_item = MenuItemBreakfast(**clean_item, department_id=dept["id"])
            await db.menu_breakfast.insert_one(new_item.dict())
            migration_results["breakfast_items"] += 1
    
    # Migrate topping items
    existing_toppings = await db.menu_toppings.find({"department_id": {"$exists": False}}).to_list(100)
    for topping_item in existing_toppings:
        clean_item = {k: v for k, v in topping_item.items() if k != '_id'}
        for dept in departments:
            new_item = MenuItemToppings(**clean_item, department_id=dept["id"])
            await db.menu_toppings.insert_one(new_item.dict())
            migration_results["topping_items"] += 1
    
    # Migrate drink items
    existing_drinks = await db.menu_drinks.find({"department_id": {"$exists": False}}).to_list(100)
    for drink_item in existing_drinks:
        clean_item = {k: v for k, v in drink_item.items() if k != '_id'}
        for dept in departments:
            new_item = MenuItemDrink(**clean_item, department_id=dept["id"])
            await db.menu_drinks.insert_one(new_item.dict())
            migration_results["drink_items"] += 1
    
    # Migrate sweet items
    existing_sweets = await db.menu_sweets.find({"department_id": {"$exists": False}}).to_list(100)
    for sweet_item in existing_sweets:
        clean_item = {k: v for k, v in sweet_item.items() if k != '_id'}
        for dept in departments:
            new_item = MenuItemSweet(**clean_item, department_id=dept["id"])
            await db.menu_sweets.insert_one(new_item.dict())
            migration_results["sweet_items"] += 1
    
    # Remove old global items (optional - comment out if you want to keep them)
    await db.menu_breakfast.delete_many({"department_id": {"$exists": False}})
    await db.menu_toppings.delete_many({"department_id": {"$exists": False}})
    await db.menu_drinks.delete_many({"department_id": {"$exists": False}})
    await db.menu_sweets.delete_many({"department_id": {"$exists": False}})
    
    return {
        "message": "Migration zu abteilungsspezifischen Menüs erfolgreich abgeschlossen",
        "results": migration_results
    }

# Authentication routes
@api_router.post("/login/department")
async def department_login(login_data: DepartmentLogin):
    """Login for department with password"""
    dept = await db.departments.find_one({"name": login_data.department_name})
    if not dept or dept["password_hash"] != login_data.password:
        raise HTTPException(status_code=401, detail="Ungültiger Name oder Passwort")
    
    return {"department_id": dept["id"], "department_name": dept["name"]}

@api_router.post("/login/master")
async def master_login(department_name: str, master_password: str):
    """Master password login for developer access to any department"""
    master_password_env = os.environ.get('MASTER_PASSWORD', 'master123dev')
    if master_password != master_password_env:  # Developer master password
        raise HTTPException(status_code=401, detail="Ungültiges Master-Passwort")
    
    # Find the department
    dept = await db.departments.find_one({"name": department_name})
    if not dept:
        raise HTTPException(status_code=404, detail="Abteilung nicht gefunden")
    
    return {
        "department_id": dept["id"], 
        "department_name": dept["name"], 
        "role": "master_admin",
        "access_level": "master"
    }

@api_router.post("/login/department-admin")
async def department_admin_login(login_data: DepartmentAdminLogin):
    """Login for department admin with admin password"""
    dept = await db.departments.find_one({"name": login_data.department_name})
    if not dept or dept["admin_password_hash"] != login_data.admin_password:
        raise HTTPException(status_code=401, detail="Ungültiger Name oder Admin-Passwort")
    
    return {"department_id": dept["id"], "department_name": dept["name"], "role": "department_admin"}

@api_router.post("/login/admin") 
async def admin_login(login_data: AdminLogin):
    """Central admin login"""
    admin_password = os.environ.get('CENTRAL_ADMIN_PASSWORD', 'admin123')
    if login_data.password != admin_password:
        raise HTTPException(status_code=401, detail="Ungültiges Admin-Passwort")
    
    return {"message": "Admin erfolgreich angemeldet", "role": "admin"}

# Department routes
@api_router.get("/departments", response_model=List[Department])
async def get_departments():
    """Get all departments for homepage display - ONLY Wachabteilung"""
    # Only return departments with "Wachabteilung" in name
    departments = await db.departments.find({"name": {"$regex": "Wachabteilung"}}).to_list(100)
    return [Department(**dept) for dept in departments]

# Employee routes
@api_router.get("/departments/{department_id}/employees", response_model=List[Employee])
async def get_department_employees(department_id: str):
    """Get all employees for a specific department, sorted by sort_order"""
    employees = await db.employees.find({"department_id": department_id}).sort("sort_order", 1).to_list(100)
    return [Employee(**emp) for emp in employees]

@api_router.put("/departments/{department_id}/employees/sort-order")
async def update_employees_sort_order(department_id: str, employee_ids: List[str]):
    """Update sort order for employees based on drag & drop"""
    try:
        # Update each employee's sort_order based on their position in the list
        for index, employee_id in enumerate(employee_ids):
            await db.employees.update_one(
                {"id": employee_id, "department_id": department_id},
                {"$set": {"sort_order": index}}
            )
        
        return {
            "message": "Mitarbeiter-Sortierung erfolgreich gespeichert",
            "updated_count": len(employee_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Sortierung: {str(e)}")

@api_router.post("/employees", response_model=Employee)
async def create_employee(employee_data: EmployeeCreate):
    """Create a new employee"""
    employee = Employee(**employee_data.dict())
    await db.employees.insert_one(employee.dict())
    return employee

@api_router.get("/lunch-settings")
async def get_lunch_settings():
    """Get current lunch settings"""
    lunch_settings = await db.lunch_settings.find_one()
    if not lunch_settings:
        # Create default if none exists
        default_settings = LunchSettings()
        await db.lunch_settings.insert_one(default_settings.dict())
        return default_settings
    
    # Clean the document by removing MongoDB _id field
    clean_settings = {k: v for k, v in lunch_settings.items() if k != '_id'}
    return clean_settings

@api_router.put("/lunch-settings")
async def update_lunch_settings(price: float):
    """Update lunch price and retroactively apply to all today's lunch orders"""
    lunch_settings = await db.lunch_settings.find_one()
    if lunch_settings:
        await db.lunch_settings.update_one(
            {"id": lunch_settings["id"]},
            {"$set": {"price": price}}
        )
    else:
        new_settings = LunchSettings(price=price)
        await db.lunch_settings.insert_one(new_settings.dict())
    
    # Retroactively update all today's breakfast orders with lunch
    today = datetime.now(timezone.utc).date()
    start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    # Find all today's breakfast orders with lunch
    todays_orders = await db.orders.find({
        "order_type": "breakfast",
        "timestamp": {
            "$gte": start_of_day.isoformat(),
            "$lte": end_of_day.isoformat()
        }
    }).to_list(1000)
    
    updated_orders = 0
    for order in todays_orders:
        if order.get("breakfast_items"):
            # Check if any breakfast item has lunch
            has_lunch_items = any(item.get("has_lunch", False) for item in order["breakfast_items"])
            if has_lunch_items:
                # Recalculate total price with new lunch price
                new_total = 0.0
                
                # Get current menu prices (department-specific)
                breakfast_menu = await db.menu_breakfast.find({"department_id": order["department_id"]}).to_list(100)
                toppings_menu = await db.menu_toppings.find({"department_id": order["department_id"]}).to_list(100)
                breakfast_prices = {item["roll_type"]: item["price"] for item in breakfast_menu}
                topping_prices = {item["topping_type"]: item["price"] for item in toppings_menu}
                
                for item in order["breakfast_items"]:
                    # Handle both old and new breakfast item formats
                    if "roll_type" in item:
                        # Old format
                        roll_price = breakfast_prices.get(item["roll_type"], 0.0)
                        roll_halves = item.get("roll_halves", item.get("roll_count", 1))
                        new_total += roll_price * roll_halves
                    else:
                        # New format with white_halves and seeded_halves
                        white_halves = item.get("white_halves", 0)
                        seeded_halves = item.get("seeded_halves", 0)
                        
                        white_price = breakfast_prices.get("weiss", 0.0)
                        seeded_price = breakfast_prices.get("koerner", 0.0)
                        
                        # Prices are per-half (NOT divided by 2)
                        new_total += (white_price * white_halves) + (seeded_price * seeded_halves)
                    
                    # Toppings price
                    for topping in item.get("toppings", []):
                        topping_price = topping_prices.get(topping, 0.0)
                        new_total += topping_price
                    
                    # Add boiled eggs price if applicable
                    boiled_eggs = item.get("boiled_eggs", 0)
                    if boiled_eggs > 0:
                        # Get boiled eggs price from lunch settings
                        lunch_settings_obj = await db.lunch_settings.find_one({}) or {}
                        boiled_eggs_price = lunch_settings_obj.get("boiled_eggs_price", 0.50)
                        new_total += boiled_eggs * boiled_eggs_price
                    
                    # New lunch price (FIXED: lunch price should be per order, not per roll halves)
                    if item.get("has_lunch"):
                        # Add lunch price once per order, regardless of roll count
                        new_total += price
                
                # Update order with new total price
                old_total = order["total_price"]
                await db.orders.update_one(
                    {"id": order["id"]},
                    {"$set": {"total_price": new_total}}
                )
                
                # Update employee balance with the difference
                balance_diff = new_total - old_total
                if balance_diff != 0:
                    await db.employees.update_one(
                        {"id": order["employee_id"]},
                        {"$inc": {"breakfast_balance": balance_diff}}
                    )
                
                updated_orders += 1
    
    return {
        "message": "Lunch-Preis erfolgreich aktualisiert", 
        "price": price,
        "updated_orders": updated_orders
    }

@api_router.put("/lunch-settings/boiled-eggs-price")
async def update_boiled_eggs_price(price: float):
    """Update boiled eggs price"""
    lunch_settings = await db.lunch_settings.find_one()
    if lunch_settings:
        await db.lunch_settings.update_one(
            {"id": lunch_settings["id"]},
            {"$set": {"boiled_eggs_price": price}}
        )
    else:
        new_settings = LunchSettings(boiled_eggs_price=price)
        await db.lunch_settings.insert_one(new_settings.dict())
    
    return {"message": "Kochei-Preis erfolgreich aktualisiert", "price": price}

@api_router.get("/daily-lunch-settings/{department_id}")
async def get_daily_lunch_settings(department_id: str):
    """Get daily lunch prices for a department (last 30 days)"""
    end_date = get_berlin_date()
    start_date = end_date - timedelta(days=30)
    
    daily_prices = []
    current_date = start_date
    
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Check if we have a specific price for this day
        daily_price = await db.daily_lunch_prices.find_one({
            "department_id": department_id,
            "date": date_str
        })
        
        if daily_price:
            daily_prices.append({
                "date": date_str,
                "lunch_price": daily_price["lunch_price"]
            })
        else:
            # Fall back to global lunch settings
            lunch_settings = await db.lunch_settings.find_one()
            default_price = lunch_settings["price"] if lunch_settings else 0.0
            daily_prices.append({
                "date": date_str,
                "lunch_price": default_price
            })
        
        current_date += timedelta(days=1)
    
    return {"daily_prices": daily_prices}

@api_router.put("/daily-lunch-settings/{department_id}/{date}")
async def set_daily_lunch_price(department_id: str, date: str, lunch_price: float):
    """Set lunch price for a specific day and department"""
    
    # Validate date format
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    
    # Check if daily price already exists
    existing_price = await db.daily_lunch_prices.find_one({
        "department_id": department_id,
        "date": date
    })
    
    if existing_price:
        # Update existing
        await db.daily_lunch_prices.update_one(
            {"department_id": department_id, "date": date},
            {"$set": {"lunch_price": lunch_price}}
        )
    else:
        # Create new
        daily_price = DailyLunchPrice(
            department_id=department_id,
            date=date,
            lunch_price=lunch_price
        )
        await db.daily_lunch_prices.insert_one(daily_price.dict())
    
    # Now retroactively update all lunch orders from that specific day (Berlin timezone)
    start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(date)
    
    updated_orders = 0
    
    # Find all breakfast orders with lunch from that day
    orders_cursor = db.orders.find({
        "department_id": department_id,
        "order_type": "breakfast",
        "has_lunch": True,
        "timestamp": {
            "$gte": start_of_day_utc.isoformat(),
            "$lte": end_of_day_utc.isoformat()
        }
    })
    
    async for order in orders_cursor:
        # Get current lunch price from order
        current_lunch_price = order.get("lunch_price", 0.0)
        price_difference = lunch_price - current_lunch_price
        
        if abs(price_difference) > 0.01:  # Only update if significant difference
            # Update order
            new_total = order["total_price"] + price_difference
            await db.orders.update_one(
                {"id": order["id"]},
                {
                    "$set": {
                        "lunch_price": lunch_price,
                        "total_price": new_total
                    }
                }
            )
            
            # Update employee balance (lunch goes to breakfast_balance)
            await db.employees.update_one(
                {"id": order["employee_id"]},
                {"$inc": {"breakfast_balance": price_difference}}
            )
            
            updated_orders += 1
    
    return {
        "message": "Tages-Mittagessen-Preis erfolgreich gesetzt",
        "date": date,
        "lunch_price": lunch_price,
        "updated_orders": updated_orders
    }

@api_router.get("/daily-lunch-price/{department_id}/{date}")
async def get_daily_lunch_price(department_id: str, date: str):
    """Get lunch price for a specific day"""
    
    # Check if we have a specific price for this day
    daily_price = await db.daily_lunch_prices.find_one({
        "department_id": department_id,
        "date": date
    })
    
    if daily_price:
        return {"date": date, "lunch_price": daily_price["lunch_price"]}
    else:
        # Fall back to global lunch settings
        lunch_settings = await db.lunch_settings.find_one()
        default_price = lunch_settings["price"] if lunch_settings else 0.0
        return {"date": date, "lunch_price": default_price}

# Menu routes
@api_router.get("/menu/breakfast/{department_id}", response_model=List[MenuItemBreakfast])
async def get_breakfast_menu(department_id: str):
    """Get breakfast menu items for a specific department"""
    items = await db.menu_breakfast.find({"department_id": department_id}).to_list(100)
    return [MenuItemBreakfast(**item) for item in items]

@api_router.get("/menu/toppings/{department_id}", response_model=List[MenuItemToppings])
async def get_toppings_menu(department_id: str):
    """Get topping menu items for a specific department"""
    items = await db.menu_toppings.find({"department_id": department_id}).to_list(100)
    return [MenuItemToppings(**item) for item in items]

@api_router.get("/menu/drinks/{department_id}", response_model=List[MenuItemDrink])
async def get_drinks_menu(department_id: str):
    """Get drink menu items for a specific department"""
    items = await db.menu_drinks.find({"department_id": department_id}).to_list(100)
    return [MenuItemDrink(**item) for item in items]

@api_router.get("/menu/sweets/{department_id}", response_model=List[MenuItemSweet])
async def get_sweets_menu(department_id: str):
    """Get sweet menu items for a specific department"""
    items = await db.menu_sweets.find({"department_id": department_id}).to_list(100)
    return [MenuItemSweet(**item) for item in items]

# Backward compatibility endpoints (will use first department if no department specified)
@api_router.get("/menu/breakfast", response_model=List[MenuItemBreakfast])
async def get_breakfast_menu_compat():
    """Backward compatibility - get breakfast menu for first department"""
    # Get first department
    dept = await db.departments.find_one()
    if not dept:
        return []
    items = await db.menu_breakfast.find({"department_id": dept["id"]}).to_list(100)
    return [MenuItemBreakfast(**item) for item in items]

@api_router.get("/menu/toppings", response_model=List[MenuItemToppings])
async def get_toppings_menu_compat():
    """Backward compatibility - get toppings menu for first department"""
    dept = await db.departments.find_one()
    if not dept:
        return []
    items = await db.menu_toppings.find({"department_id": dept["id"]}).to_list(100)
    return [MenuItemToppings(**item) for item in items]

@api_router.get("/menu/drinks", response_model=List[MenuItemDrink])
async def get_drinks_menu_compat():
    """Backward compatibility - get drinks menu for first department"""
    dept = await db.departments.find_one()
    if not dept:
        return []
    items = await db.menu_drinks.find({"department_id": dept["id"]}).to_list(100)
    return [MenuItemDrink(**item) for item in items]

@api_router.get("/menu/sweets", response_model=List[MenuItemSweet])
async def get_sweets_menu_compat():
    """Backward compatibility - get sweets menu for first department"""
    dept = await db.departments.find_one()
    if not dept:
        return []
    items = await db.menu_sweets.find({"department_id": dept["id"]}).to_list(100)
    return [MenuItemSweet(**item) for item in items]

# Order routes
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate):
    """Create a new order and update employee balance"""
    
    # For breakfast orders, check if breakfast is closed
    if order_data.order_type == OrderType.BREAKFAST:
        # Use Berlin timezone for date calculation
        today = get_berlin_date().isoformat()
        breakfast_status = await db.breakfast_settings.find_one({
            "department_id": order_data.department_id,
            "date": today
        })
        
        # Auto-reopen breakfast if it's a new day (Berlin time)
        if breakfast_status and breakfast_status["is_closed"]:
            # Check if the breakfast was closed on a previous day
            closed_date = breakfast_status.get("date", today)
            if closed_date != today:
                # New day - automatically reopen breakfast
                await db.breakfast_settings.update_one(
                    {"department_id": order_data.department_id, "date": closed_date},
                    {"$set": {"is_closed": False, "closed_by": "", "closed_at": None}}
                )
                breakfast_status = None  # Treat as open
        
        if breakfast_status and breakfast_status["is_closed"]:
            raise HTTPException(
                status_code=403, 
                detail="Frühstücksbestellungen sind für heute geschlossen. Nur Admins können noch Änderungen vornehmen."
            )
        
        # Check for existing breakfast order today (single breakfast order constraint)
        # Use Berlin timezone for day boundaries
        start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(today)
        
        existing_breakfast = await db.orders.find_one({
            "employee_id": order_data.employee_id,
            "order_type": "breakfast",
            "timestamp": {
                "$gte": start_of_day_utc.isoformat(),
                "$lte": end_of_day_utc.isoformat()
            }
        })
        
        if existing_breakfast:
            raise HTTPException(
                status_code=400,
                detail="Sie haben bereits eine Frühstücksbestellung für heute. Bitte bearbeiten Sie Ihre bestehende Bestellung."
            )
    
    # Calculate total price (rest of the existing logic...)
    total_price = 0.0
    
    if order_data.order_type == OrderType.BREAKFAST and order_data.breakfast_items:
        # Get department-specific breakfast menu prices and lunch settings
        breakfast_menu = await db.menu_breakfast.find({"department_id": order_data.department_id}).to_list(100)
        toppings_menu = await db.menu_toppings.find({"department_id": order_data.department_id}).to_list(100)
        lunch_settings = await db.lunch_settings.find_one()
        
        breakfast_prices = {item["roll_type"]: item["price"] for item in breakfast_menu}
        topping_prices = {item["topping_type"]: item["price"] for item in toppings_menu}
        
        # Get daily lunch price for today (Berlin timezone)
        today = get_berlin_date().strftime('%Y-%m-%d')
        daily_price = await db.daily_lunch_prices.find_one({
            "department_id": order_data.department_id,
            "date": today
        })
        
        if daily_price:
            lunch_price = daily_price["lunch_price"]
        else:
            # Fall back to global lunch settings
            lunch_price = lunch_settings["price"] if lunch_settings and lunch_settings["enabled"] else 0.0
        
        boiled_eggs_price = lunch_settings.get("boiled_eggs_price", 0.50) if lunch_settings else 0.50  # Default €0.50 per egg
        
        for breakfast_item in order_data.breakfast_items:
            # Allow orders without rolls (just eggs and/or lunch)
            has_rolls = breakfast_item.total_halves > 0
            has_eggs_or_lunch = breakfast_item.boiled_eggs > 0 or breakfast_item.has_lunch
            
            if not has_rolls and not has_eggs_or_lunch:
                raise HTTPException(
                    status_code=400, 
                    detail="Bitte wählen Sie mindestens Brötchen, Frühstückseier oder Mittagessen"
                )
            
            # Validate roll calculation only if rolls are selected
            if has_rolls:
                if breakfast_item.white_halves + breakfast_item.seeded_halves != breakfast_item.total_halves:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Weiße ({breakfast_item.white_halves}) + Körner ({breakfast_item.seeded_halves}) Hälften müssen der Gesamtzahl ({breakfast_item.total_halves}) entsprechen"
                    )
                
                # Validate that toppings count matches total halves only if rolls are selected
                if len(breakfast_item.toppings) != breakfast_item.total_halves:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Anzahl der Beläge ({len(breakfast_item.toppings)}) muss der Anzahl der Brötchenhälften ({breakfast_item.total_halves}) entsprechen"
                    )
            
            # Calculate roll prices only if rolls are selected
            if has_rolls:
                white_price = breakfast_prices.get("weiss", 0.0)
                seeded_price = breakfast_prices.get("koerner", 0.0)
                total_price += (white_price * breakfast_item.white_halves) + (seeded_price * breakfast_item.seeded_halves)
                
                # Toppings price (free but keep structure)
                for topping in breakfast_item.toppings:
                    topping_price = topping_prices.get(topping, 0.0)
                    total_price += topping_price
            
            # Lunch price calculation (can be without rolls now)
            if breakfast_item.has_lunch:
                # Lunch price should be added once per order, not multiplied by roll halves
                total_price += lunch_price
            
            # Boiled eggs price
            if breakfast_item.boiled_eggs > 0:
                total_price += boiled_eggs_price * breakfast_item.boiled_eggs
    
    elif order_data.order_type == OrderType.DRINKS and order_data.drink_items:
        drinks_menu = await db.menu_drinks.find({"department_id": order_data.department_id}).to_list(100)
        drink_prices = {item["id"]: item["price"] for item in drinks_menu}
        
        for drink_id, quantity in order_data.drink_items.items():
            drink_price = drink_prices.get(drink_id, 0.0)
            total_price += drink_price * quantity
            
    elif order_data.order_type == OrderType.SWEETS and order_data.sweet_items:
        sweets_menu = await db.menu_sweets.find({"department_id": order_data.department_id}).to_list(100)
        sweet_prices = {item["id"]: item["price"] for item in sweets_menu}
        
        for sweet_id, quantity in order_data.sweet_items.items():
            sweet_price = sweet_prices.get(sweet_id, 0.0)
            total_price += sweet_price * quantity
    
    # Create order
    order_has_lunch = False
    order_lunch_price = None
    
    # Check if this is a breakfast order with lunch
    if order_data.order_type == OrderType.BREAKFAST and order_data.breakfast_items:
        for breakfast_item in order_data.breakfast_items:
            if breakfast_item.has_lunch:
                order_has_lunch = True
                order_lunch_price = lunch_price  # Use the daily lunch price we calculated above
                break
    
    order = Order(
        **order_data.dict(), 
        total_price=total_price,
        has_lunch=order_has_lunch,
        lunch_price=order_lunch_price
    )
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

@api_router.get("/orders/breakfast-history/{department_id}")
async def get_breakfast_history(department_id: str, days_back: int = 30):
    """Get historical breakfast summaries for a department"""
    
    # Get date range (Berlin timezone)
    end_date = get_berlin_date()
    start_date = end_date - timedelta(days=days_back)
    
    history = []
    current_date = start_date
    
    while current_date <= end_date:
        # Get orders for this specific date using Berlin timezone boundaries
        start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(current_date)
        
        orders = await db.orders.find({
            "department_id": department_id,
            "order_type": "breakfast",
            "timestamp": {
                "$gte": start_of_day_utc.isoformat(),
                "$lte": end_of_day_utc.isoformat()
            }
        }).to_list(1000)
        
        if orders:  # Only include dates with orders
            # Calculate daily summary
            breakfast_summary = {}
            employee_orders = {}
            total_orders = len(orders)
            total_amount = sum(order.get("total_price", 0) for order in orders)
            
            for order in orders:
                if order.get("breakfast_items"):
                    # Get employee info
                    employee = await db.employees.find_one({"id": order["employee_id"]})
                    employee_name = employee["name"] if employee else "Unknown"
                    
                    if employee_name not in employee_orders:
                        employee_orders[employee_name] = {"white_halves": 0, "seeded_halves": 0, "toppings": {}, "total_amount": 0}
                    
                    employee_orders[employee_name]["total_amount"] += order.get("total_price", 0)
                    
                    for item in order["breakfast_items"]:
                        # Handle new format (total_halves, white_halves, seeded_halves)
                        if "total_halves" in item:
                            white_halves = item.get("white_halves", 0)
                            seeded_halves = item.get("seeded_halves", 0)
                        else:
                            # Handle old format (roll_type, roll_halves)
                            roll_type = item.get("roll_type", "weiss")
                            roll_halves = item.get("roll_halves", item.get("roll_count", 1))
                            if roll_type == "weiss":
                                white_halves = roll_halves
                                seeded_halves = 0
                            else:
                                white_halves = 0
                                seeded_halves = roll_halves
                        
                        # Update employee totals
                        employee_orders[employee_name]["white_halves"] += white_halves
                        employee_orders[employee_name]["seeded_halves"] += seeded_halves
                        
                        # Update overall summary
                        if "weiss" not in breakfast_summary:
                            breakfast_summary["weiss"] = {"halves": 0, "toppings": {}}
                        if "koerner" not in breakfast_summary:
                            breakfast_summary["koerner"] = {"halves": 0, "toppings": {}}
                        
                        breakfast_summary["weiss"]["halves"] += white_halves
                        breakfast_summary["koerner"]["halves"] += seeded_halves
                        
                        # Count toppings
                        for topping in item["toppings"]:
                            if topping not in employee_orders[employee_name]["toppings"]:
                                employee_orders[employee_name]["toppings"][topping] = 0
                            employee_orders[employee_name]["toppings"][topping] += 1
            
            # Calculate shopping list
            shopping_list = {}
            for roll_type, data in breakfast_summary.items():
                whole_rolls = (data["halves"] + 1) // 2
                shopping_list[roll_type] = {"halves": data["halves"], "whole_rolls": whole_rolls}
            
            # Get daily lunch price for this date
            date_str = current_date.isoformat()
            daily_price = await db.daily_lunch_prices.find_one({
                "department_id": department_id,
                "date": date_str
            })
            
            daily_lunch_price = daily_price["lunch_price"] if daily_price else 0.0
            
            # If no daily price set, fall back to global lunch settings
            if daily_lunch_price == 0.0:
                lunch_settings = await db.lunch_settings.find_one()
                daily_lunch_price = lunch_settings["price"] if lunch_settings else 0.0
            
            history.append({
                "date": current_date.isoformat(),
                "total_orders": total_orders,
                "total_amount": total_amount,
                "breakfast_summary": breakfast_summary,
                "employee_orders": employee_orders,
                "shopping_list": shopping_list,
                "daily_lunch_price": daily_lunch_price  # Add daily lunch price
            })
        
        current_date += timedelta(days=1)
    
    # Return history in reverse chronological order (newest first)
    return {"history": list(reversed(history))}


@api_router.get("/orders/daily-summary/{department_id}")
async def get_daily_summary(department_id: str):
    """Get daily summary of all orders for a department"""
    # Use Berlin timezone for current day calculation
    today = get_berlin_date()
    start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(today)
    
    # Get today's orders (Berlin time)
    orders = await db.orders.find({
        "department_id": department_id,
        "timestamp": {
            "$gte": start_of_day_utc.isoformat(),
            "$lte": end_of_day_utc.isoformat()
        }
    }).to_list(1000)
    
    # Aggregate breakfast orders with employee details
    breakfast_summary = {}
    employee_orders = {}  # Track individual employee orders
    drinks_summary = {}
    sweets_summary = {}
    
    for order in orders:
        if order["order_type"] == "breakfast" and order.get("breakfast_items"):
            # Get employee info
            employee = await db.employees.find_one({"id": order["employee_id"]})
            employee_name = employee["name"] if employee else "Unknown"
            
            if employee_name not in employee_orders:
                employee_orders[employee_name] = {
                    "white_halves": 0, 
                    "seeded_halves": 0, 
                    "boiled_eggs": 0,  # Add boiled eggs tracking
                    "has_lunch": False,  # Add lunch tracking
                    "toppings": {}
                }
            
            for item in order["breakfast_items"]:
                # Handle new format (total_halves, white_halves, seeded_halves)
                if "total_halves" in item:
                    white_halves = item.get("white_halves", 0)
                    seeded_halves = item.get("seeded_halves", 0)
                else:
                    # Handle old format (roll_type, roll_halves)
                    roll_type = item.get("roll_type", "weiss")
                    roll_halves = item.get("roll_halves", item.get("roll_count", 1))
                    if roll_type == "weiss":
                        white_halves = roll_halves
                        seeded_halves = 0
                    else:
                        white_halves = 0
                        seeded_halves = roll_halves
                
                # Update employee totals
                employee_orders[employee_name]["white_halves"] += white_halves
                employee_orders[employee_name]["seeded_halves"] += seeded_halves
                
                # Add boiled eggs if present
                boiled_eggs = item.get("boiled_eggs", 0)
                employee_orders[employee_name]["boiled_eggs"] += boiled_eggs
                
                # Add lunch if present
                if item.get("has_lunch", False):
                    employee_orders[employee_name]["has_lunch"] = True
                
                # Update overall summary
                if "weiss" not in breakfast_summary:
                    breakfast_summary["weiss"] = {"halves": 0, "toppings": {}}
                if "koerner" not in breakfast_summary:
                    breakfast_summary["koerner"] = {"halves": 0, "toppings": {}}
                
                breakfast_summary["weiss"]["halves"] += white_halves
                breakfast_summary["koerner"]["halves"] += seeded_halves
                
                # Count toppings per employee
                for topping in item["toppings"]:
                    # Employee toppings - use simple integer count for frontend display compatibility
                    if topping not in employee_orders[employee_name]["toppings"]:
                        employee_orders[employee_name]["toppings"][topping] = 0
                    
                    # Increment topping count for employee
                    employee_orders[employee_name]["toppings"][topping] += 1
                    
                    # Distribute toppings proportionally for breakfast summary (simplified: assign to roll type with more halves)
                    if white_halves >= seeded_halves:
                        if topping not in breakfast_summary["weiss"]["toppings"]:
                            breakfast_summary["weiss"]["toppings"][topping] = 0
                        breakfast_summary["weiss"]["toppings"][topping] += 1
                    else:
                        if topping not in breakfast_summary["koerner"]["toppings"]:
                            breakfast_summary["koerner"]["toppings"][topping] = 0
                        breakfast_summary["koerner"]["toppings"][topping] += 1
        
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
    
    # Calculate shopping list (convert halves to whole rolls, rounded up)
    shopping_list = {}
    total_toppings = {}
    
    for roll_type, data in breakfast_summary.items():
        # Convert halves to whole rolls (rounded up)
        whole_rolls = (data["halves"] + 1) // 2  # Round up
        shopping_list[roll_type] = {"halves": data["halves"], "whole_rolls": whole_rolls}
        
        # Aggregate all toppings
        for topping, count in data["toppings"].items():
            if topping not in total_toppings:
                total_toppings[topping] = 0
            total_toppings[topping] += count
    
    # Calculate total boiled eggs
    total_boiled_eggs = sum(data["boiled_eggs"] for data in employee_orders.values())
    
    return {
        "date": today.isoformat(),
        "breakfast_summary": breakfast_summary,
        "employee_orders": employee_orders,
        "drinks_summary": drinks_summary,
        "sweets_summary": sweets_summary,
        "shopping_list": shopping_list,
        "total_toppings": total_toppings,
        "total_boiled_eggs": total_boiled_eggs  # Add total boiled eggs
    }

@api_router.get("/employee/{employee_id}/today-orders")
async def get_employee_today_orders(employee_id: str):
    """Get employee's orders for today"""
    today = datetime.now(timezone.utc).date()
    start_of_day = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_of_day = datetime.combine(today, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    orders = await db.orders.find({
        "employee_id": employee_id,
        "timestamp": {
            "$gte": start_of_day.isoformat(),
            "$lte": end_of_day.isoformat()
        }
    }).to_list(100)
    
    return [parse_from_mongo({k: v for k, v in order.items() if k != '_id'}) for order in orders]

@api_router.delete("/employee/{employee_id}/orders/{order_id}")
async def delete_employee_order(employee_id: str, order_id: str):
    """Allow employee to delete their own order (if breakfast not closed)"""
    # Check if order belongs to employee
    order = await db.orders.find_one({"id": order_id, "employee_id": employee_id})
    if not order:
        raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
    
    # For breakfast orders, check if breakfast is closed
    if order["order_type"] == "breakfast":
        today = datetime.now(timezone.utc).date().isoformat()
        breakfast_status = await db.breakfast_settings.find_one({
            "department_id": order["department_id"],
            "date": today
        })
        
        if breakfast_status and breakfast_status["is_closed"]:
            raise HTTPException(
                status_code=403, 
                detail="Frühstück ist geschlossen. Nur Admins können noch Änderungen vornehmen."
            )
    
    # Adjust employee balance
    employee = await db.employees.find_one({"id": employee_id})
    if employee:
        if order["order_type"] == "breakfast":
            new_breakfast_balance = employee["breakfast_balance"] - order["total_price"]
            await db.employees.update_one(
                {"id": employee_id},
                {"$set": {"breakfast_balance": max(0, new_breakfast_balance)}}
            )
        else:
            new_drinks_sweets_balance = employee["drinks_sweets_balance"] - order["total_price"]
            await db.employees.update_one(
                {"id": employee_id},
                {"$set": {"drinks_sweets_balance": max(0, new_drinks_sweets_balance)}}
            )
    
    # Delete order
    await db.orders.delete_one({"id": order_id})
    return {"message": "Bestellung erfolgreich gelöscht"}

@api_router.get("/orders/employee/{employee_id}")
async def get_employee_orders(employee_id: str):
    """Get all orders for a specific employee"""
    orders = await db.orders.find({"employee_id": employee_id}).sort("timestamp", -1).to_list(1000)
    return [parse_from_mongo(order) for order in orders]

@api_router.get("/employees/{employee_id}/orders")
async def get_employee_orders(employee_id: str):
    """Get all orders for a specific employee"""
    try:
        orders = await db.orders.find({"employee_id": employee_id}).sort("timestamp", -1).to_list(1000)
        # Clean orders by removing MongoDB _id and parsing timestamps
        clean_orders = []
        for order in orders:
            clean_order = {k: v for k, v in order.items() if k != '_id'}
            clean_order = parse_from_mongo(clean_order)
            clean_orders.append(clean_order)
        return {"orders": clean_orders}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")

@api_router.get("/employees/{employee_id}/profile")
async def get_employee_profile(employee_id: str):
    """Get employee profile with detailed order history"""
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
    
    # Get order history with menu details
    orders = await db.orders.find({"employee_id": employee_id}).sort("timestamp", -1).to_list(1000)
    
    # Get menu items for reference (use employee's department)
    employee_department_id = employee.get("department_id")
    if employee_department_id:
        breakfast_menu = await db.menu_breakfast.find({"department_id": employee_department_id}).to_list(100)
        toppings_menu = await db.menu_toppings.find({"department_id": employee_department_id}).to_list(100)
        drinks_menu = await db.menu_drinks.find({"department_id": employee_department_id}).to_list(100)
        sweets_menu = await db.menu_sweets.find({"department_id": employee_department_id}).to_list(100)
    else:
        # Fallback to first department's menu if employee department not found
        first_dept = await db.departments.find_one()
        dept_id = first_dept["id"] if first_dept else None
        breakfast_menu = await db.menu_breakfast.find({"department_id": dept_id}).to_list(100) if dept_id else []
        toppings_menu = await db.menu_toppings.find({"department_id": dept_id}).to_list(100) if dept_id else []
        drinks_menu = await db.menu_drinks.find({"department_id": dept_id}).to_list(100) if dept_id else []
        sweets_menu = await db.menu_sweets.find({"department_id": dept_id}).to_list(100) if dept_id else []
    
    # Create lookup dictionaries
    roll_names = {item["roll_type"]: f"€{item['price']:.2f}" for item in breakfast_menu}
    topping_names = {item["topping_type"]: f"€{item['price']:.2f}" for item in toppings_menu}
    drink_names = {item["id"]: {"name": item["name"], "price": item["price"]} for item in drinks_menu}
    sweet_names = {item["id"]: {"name": item["name"], "price": item["price"]} for item in sweets_menu}
    
    # Enrich orders with readable names
    enriched_orders = []
    for order in orders:
        # Clean the order data and remove MongoDB _id
        clean_order = {k: v for k, v in order.items() if k != '_id'}
        enriched_order = parse_from_mongo(clean_order.copy())
        
        if order["order_type"] == "breakfast" and order.get("breakfast_items"):
            enriched_order["readable_items"] = []
            for item in order["breakfast_items"]:
                # Handle both old and new breakfast order formats
                if "roll_type" in item:
                    # Old format with roll_type
                    roll_name = {"weiss": "Weißes Brötchen", "koerner": "Körnerbrötchen"}.get(item["roll_type"], item["roll_type"])
                    roll_count = item.get('roll_halves', item.get('roll_count', 1))
                    description = f"{roll_count}x {roll_name} Hälften" if 'roll_halves' in item else f"{roll_count}x {roll_name}"
                else:
                    # New format with total_halves, white_halves, seeded_halves
                    white_halves = item.get("white_halves", 0)
                    seeded_halves = item.get("seeded_halves", 0)
                    total_halves = item.get("total_halves", white_halves + seeded_halves)
                    
                    parts = []
                    if white_halves > 0:
                        parts.append(f"{white_halves}x Weiße Brötchen Hälften")
                    if seeded_halves > 0:
                        parts.append(f"{seeded_halves}x Körnerbrötchen Hälften")
                    description = ", ".join(parts) if parts else f"{total_halves} Brötchen Hälften"
                
                topping_names_german = {
                    "ruehrei": "Rührei", "spiegelei": "Spiegelei", "eiersalat": "Eiersalat",
                    "salami": "Salami", "schinken": "Schinken", "kaese": "Käse", "butter": "Butter"
                }
                toppings_str = ", ".join([topping_names_german.get(t, t) for t in item["toppings"]])
                
                if item.get("has_lunch"):
                    description += " (mit Mittagessen)"
                enriched_order["readable_items"].append({
                    "description": description,
                    "toppings": toppings_str if toppings_str else "Ohne Belag"
                })
        
        elif order["order_type"] in ["drinks", "sweets"]:
            enriched_order["readable_items"] = []
            items_dict = order.get("drink_items", {}) if order["order_type"] == "drinks" else order.get("sweet_items", {})
            names_dict = drink_names if order["order_type"] == "drinks" else sweet_names
            
            for item_id, quantity in items_dict.items():
                if item_id in names_dict and quantity > 0:
                    enriched_order["readable_items"].append({
                        "description": f"{quantity}x {names_dict[item_id]['name']}",
                        "unit_price": f"€{names_dict[item_id]['price']:.2f}"
                    })
        
        enriched_orders.append(enriched_order)
    
    # Get payment logs for this employee
    payment_logs = await db.payment_logs.find({"employee_id": employee_id}).sort("timestamp", -1).to_list(1000)
    
    # Clean payment logs
    clean_payment_logs = []
    for log in payment_logs:
        clean_log = {k: v for k, v in log.items() if k != '_id'}
        clean_payment_logs.append(clean_log)
    
    # Clean employee data and remove MongoDB _id
    clean_employee = {k: v for k, v in employee.items() if k != '_id'}
    
    return {
        "employee": clean_employee,
        "order_history": enriched_orders,
        "payment_history": clean_payment_logs,  # Add payment history
        "total_orders": len(orders),
        "breakfast_total": employee["breakfast_balance"],
        "drinks_sweets_total": employee["drinks_sweets_balance"]
    }

@api_router.post("/department-admin/close-breakfast/{department_id}")
async def close_breakfast_for_day(department_id: str, admin_name: str):
    """Close breakfast ordering for the day"""
    # Use Berlin timezone for current day
    today = get_berlin_date().isoformat()
    
    # Check if already closed
    existing_setting = await db.breakfast_settings.find_one({
        "department_id": department_id,
        "date": today
    })
    
    if existing_setting and existing_setting["is_closed"]:
        raise HTTPException(status_code=400, detail="Frühstück für heute bereits geschlossen")
    
    # Create or update breakfast settings
    breakfast_setting = BreakfastSettings(
        department_id=department_id,
        date=today,
        is_closed=True,
        closed_by=admin_name,
        closed_at=datetime.now(timezone.utc)
    )
    
    if existing_setting:
        await db.breakfast_settings.update_one(
            {"id": existing_setting["id"]},
            {"$set": {
                "is_closed": True,
                "closed_by": admin_name,
                "closed_at": breakfast_setting.closed_at.isoformat()
            }}
        )
    else:
        setting_dict = prepare_for_mongo(breakfast_setting.dict())
        await db.breakfast_settings.insert_one(setting_dict)
    
    return {"message": "Frühstück für heute geschlossen", "closed_by": admin_name}

@api_router.get("/breakfast-status/{department_id}")
async def get_breakfast_status(department_id: str):
    """Check if breakfast is closed for today"""
    # Use Berlin timezone for current day
    today = get_berlin_date().isoformat()
    
    setting = await db.breakfast_settings.find_one({
        "department_id": department_id,
        "date": today
    })
    
    if setting:
        return {
            "is_closed": setting["is_closed"],
            "closed_by": setting.get("closed_by", ""),
            "closed_at": setting.get("closed_at", ""),
            "date": today
        }
    
    return {"is_closed": False, "date": today}

@api_router.post("/department-admin/reopen-breakfast/{department_id}")
async def reopen_breakfast_for_day(department_id: str):
    """Reopen breakfast ordering for the day (admin only)"""
    # Use Berlin timezone for current day
    today = get_berlin_date().isoformat()
    
    await db.breakfast_settings.update_one(
        {"department_id": department_id, "date": today},
        {"$set": {
            "is_closed": False,
            "closed_by": "",
            "closed_at": None
        }}
    )
    
    return {"message": "Frühstück für heute wieder geöffnet"}

@api_router.put("/department-admin/change-password/{department_id}")
async def change_department_password(department_id: str, new_employee_password: str, new_admin_password: str):
    """Change department passwords (both employee and admin)"""
    result = await db.departments.update_one(
        {"id": department_id},
        {"$set": {
            "password_hash": new_employee_password,
            "admin_password_hash": new_admin_password
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Abteilung nicht gefunden")
    
    return {"message": "Passwörter erfolgreich geändert"}

@api_router.put("/department-admin/change-employee-password/{department_id}")
async def change_employee_password(department_id: str, new_password: str):
    """Change department employee password only"""
    result = await db.departments.update_one(
        {"id": department_id},
        {"$set": {"password_hash": new_password}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Abteilung nicht gefunden")
    
    return {"message": "Mitarbeiter-Passwort erfolgreich geändert"}

@api_router.put("/department-admin/change-admin-password/{department_id}")
async def change_admin_password(department_id: str, new_password: str):
    """Change department admin password only"""
    result = await db.departments.update_one(
        {"id": department_id},
        {"$set": {"admin_password_hash": new_password}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Abteilung nicht gefunden")
    
    return {"message": "Admin-Passwort erfolgreich geändert"}

# Department Admin routes
@api_router.put("/department-admin/menu/breakfast/{item_id}")
async def update_breakfast_menu_item(item_id: str, update_data: MenuItemUpdate, department_id: str):
    """Department Admin: Update breakfast menu item"""
    if not department_id:
        raise HTTPException(status_code=400, detail="Department ID is required")
        
    update_fields = {}
    if update_data.price is not None:
        update_fields["price"] = update_data.price
    if update_data.name is not None:
        update_fields["name"] = update_data.name
    
    if update_fields:
        # Query must include both id and department_id for security
        query = {"id": item_id, "department_id": department_id}
            
        result = await db.menu_breakfast.update_one(query, {"$set": update_fields})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Artikel nicht gefunden oder keine Berechtigung")
    
    return {"message": "Artikel erfolgreich aktualisiert"}

@api_router.put("/department-admin/menu/toppings/{item_id}")
async def update_toppings_menu_item(item_id: str, update_data: MenuItemUpdate, department_id: str = None):
    """Department Admin: Update toppings menu item"""
    update_fields = {}
    if update_data.price is not None:
        update_fields["price"] = update_data.price
    if update_data.name is not None:
        update_fields["name"] = update_data.name
        # BUGFIX: Also update topping_name when name is changed
        update_fields["topping_name"] = update_data.name
        # BUGFIX: Update topping_type to match the ID for consistency
        update_fields["topping_type"] = item_id
    
    if update_fields:
        query = {"id": item_id}
        if department_id:
            query["department_id"] = department_id
            
        result = await db.menu_toppings.update_one(query, {"$set": update_fields})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Belag nicht gefunden oder keine Berechtigung")
    
    return {"message": "Belag erfolgreich aktualisiert"}

@api_router.put("/department-admin/menu/drinks/{item_id}")
async def update_drinks_menu_item(item_id: str, update_data: MenuItemUpdate, department_id: str = None):
    """Department Admin: Update drinks menu item"""
    update_fields = {}
    if update_data.price is not None:
        update_fields["price"] = update_data.price
    if update_data.name is not None:
        update_fields["name"] = update_data.name
    
    if update_fields:
        query = {"id": item_id}
        if department_id:
            query["department_id"] = department_id
            
        result = await db.menu_drinks.update_one(query, {"$set": update_fields})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Getränk nicht gefunden oder keine Berechtigung")
    
    return {"message": "Getränk erfolgreich aktualisiert"}

@api_router.put("/department-admin/menu/sweets/{item_id}")
async def update_sweets_menu_item(item_id: str, update_data: MenuItemUpdate, department_id: str = None):
    """Department Admin: Update sweets menu item"""
    update_fields = {}
    if update_data.price is not None:
        update_fields["price"] = update_data.price
    if update_data.name is not None:
        update_fields["name"] = update_data.name
    
    if update_fields:
        query = {"id": item_id}
        if department_id:
            query["department_id"] = department_id
            
        result = await db.menu_sweets.update_one(query, {"$set": update_fields})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Süßware nicht gefunden oder keine Berechtigung")
    
    return {"message": "Süßware erfolgreich aktualisiert"}

@api_router.post("/department-admin/menu/drinks")
async def create_drink_item(item_data: MenuItemCreate):
    """Department Admin: Create new drink item"""
    drink_item = MenuItemDrink(**item_data.dict())
    await db.menu_drinks.insert_one(drink_item.dict())
    return drink_item

@api_router.post("/department-admin/menu/sweets")
async def create_sweet_item(item_data: MenuItemCreate):
    """Department Admin: Create new sweet item"""
    sweet_item = MenuItemSweet(**item_data.dict())
    await db.menu_sweets.insert_one(sweet_item.dict())
    return sweet_item

@api_router.delete("/department-admin/menu/drinks/{item_id}")
async def delete_drink_item(item_id: str):
    """Department Admin: Delete drink item"""
    result = await db.menu_drinks.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Getränk nicht gefunden")
    return {"message": "Getränk erfolgreich gelöscht"}

@api_router.delete("/department-admin/menu/sweets/{item_id}")
async def delete_sweet_item(item_id: str):
    """Department Admin: Delete sweet item"""
    result = await db.menu_sweets.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Süßware nicht gefunden")
    return {"message": "Süßware erfolgreich gelöscht"}

@api_router.delete("/department-admin/employees/{employee_id}")
async def delete_employee(employee_id: str):
    """Department Admin: Delete employee"""
    result = await db.employees.delete_one({"id": employee_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
    
    # Also delete all orders for this employee
    await db.orders.delete_many({"employee_id": employee_id})
    
    return {"message": "Mitarbeiter erfolgreich gelöscht"}

@api_router.post("/department-admin/menu/breakfast")
async def create_breakfast_item(item_data: MenuItemCreateBreakfast):
    """Department Admin: Create new breakfast item"""
    breakfast_item = MenuItemBreakfast(**item_data.dict())
    await db.menu_breakfast.insert_one(breakfast_item.dict())
    return breakfast_item

@api_router.delete("/department-admin/menu/breakfast/{item_id}")
async def delete_breakfast_item(item_id: str):
    """Department Admin: Delete breakfast item"""
    result = await db.menu_breakfast.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Brötchen nicht gefunden")
    return {"message": "Brötchen erfolgreich gelöscht"}

@api_router.post("/department-admin/menu/toppings")
async def create_topping_item(item_data: MenuItemCreateToppings):
    """Department Admin: Create new topping item with custom name"""
    topping_item = MenuItemToppings(
        id=item_data.topping_id,
        topping_type=item_data.topping_id,  # Use custom ID as type
        name=item_data.topping_name,  # Custom display name
        price=item_data.price,
        department_id=item_data.department_id
    )
    await db.menu_toppings.insert_one(topping_item.dict())
    return topping_item

@api_router.delete("/department-admin/menu/toppings/{item_id}")
async def delete_topping_item(item_id: str, department_id: str = None):
    """Department Admin: Delete topping item"""
    query = {"id": item_id}
    if department_id:
        query["department_id"] = department_id
    
    result = await db.menu_toppings.delete_one(query)
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Belag nicht gefunden oder keine Berechtigung")
    return {"message": "Belag erfolgreich gelöscht"}

@api_router.post("/department-admin/payment/{employee_id}")
async def mark_payment(employee_id: str, payment_type: str, amount: float, admin_department: str):
    """Department Admin: Mark debt as paid and log the payment"""
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
    
    # Create payment log
    payment_log = PaymentLog(
        employee_id=employee_id,
        department_id=employee["department_id"],
        amount=amount,
        payment_type=payment_type,
        action="payment",
        admin_user=admin_department,
        notes=f"Schulden als bezahlt markiert: €{amount:.2f}"
    )
    
    # Save payment log
    payment_dict = prepare_for_mongo(payment_log.dict())
    await db.payment_logs.insert_one(payment_dict)
    
    # Reset the balance to zero
    if payment_type == "breakfast":
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": {"breakfast_balance": 0.0}}
        )
    elif payment_type == "drinks_sweets":
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": {"drinks_sweets_balance": 0.0}}
        )
    
    return {"message": "Zahlung erfolgreich verbucht und Saldo zurückgesetzt"}

@api_router.get("/department-admin/payment-logs/{employee_id}")
async def get_payment_logs(employee_id: str):
    """Get payment history for an employee"""
    logs = await db.payment_logs.find({"employee_id": employee_id}).sort("timestamp", -1).to_list(100)
    return [parse_from_mongo({k: v for k, v in log.items() if k != '_id'}) for log in logs]

@api_router.get("/department-admin/breakfast-history/{department_id}")
async def get_breakfast_history(department_id: str, days: int = 7):
    """Get breakfast history for past days"""
    histories = []
    
    for i in range(1, days + 1):  # Start from yesterday
        target_date = datetime.now(timezone.utc).date() - timedelta(days=i)
        start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Get orders for that day
        orders = await db.orders.find({
            "department_id": department_id,
            "order_type": "breakfast",
            "timestamp": {
                "$gte": start_of_day.isoformat(),
                "$lte": end_of_day.isoformat()
            }
        }).to_list(1000)
        
        if orders:  # Only include days with orders
            # Process the same way as daily summary
            breakfast_summary = {}
            employee_orders = {}
            
            for order in orders:
                employee = await db.employees.find_one({"id": order["employee_id"]})
                employee_name = employee["name"] if employee else "Unknown"
                
                if employee_name not in employee_orders:
                    employee_orders[employee_name] = {"white_halves": 0, "seeded_halves": 0, "toppings": {}}
                
                for item in order["breakfast_items"]:
                    # Handle both old and new formats
                    if "total_halves" in item:
                        white_halves = item.get("white_halves", 0)
                        seeded_halves = item.get("seeded_halves", 0)
                    else:
                        roll_type = item.get("roll_type", "weiss")
                        roll_halves = item.get("roll_halves", item.get("roll_count", 1))
                        if roll_type == "weiss":
                            white_halves = roll_halves
                            seeded_halves = 0
                        else:
                            white_halves = 0
                            seeded_halves = roll_halves
                    
                    employee_orders[employee_name]["white_halves"] += white_halves
                    employee_orders[employee_name]["seeded_halves"] += seeded_halves
                    
                    # Count toppings
                    for topping in item["toppings"]:
                        if topping not in employee_orders[employee_name]["toppings"]:
                            employee_orders[employee_name]["toppings"][topping] = {"white": 0, "seeded": 0}
                        
                        if white_halves >= seeded_halves:
                            employee_orders[employee_name]["toppings"][topping]["white"] += 1
                        else:
                            employee_orders[employee_name]["toppings"][topping]["seeded"] += 1
            
            # Calculate shopping list
            total_white_halves = sum(emp["white_halves"] for emp in employee_orders.values())
            total_seeded_halves = sum(emp["seeded_halves"] for emp in employee_orders.values())
            
            shopping_list = {
                "weiss": {"halves": total_white_halves, "whole_rolls": (total_white_halves + 1) // 2},
                "koerner": {"halves": total_seeded_halves, "whole_rolls": (total_seeded_halves + 1) // 2}
            }
            
            histories.append({
                "date": target_date.isoformat(),
                "employee_orders": employee_orders,
                "shopping_list": shopping_list,
                "total_orders": len(orders)
            })
    
    return histories

# Admin routes
@api_router.delete("/department-admin/orders/{order_id}")
async def delete_order_by_admin(order_id: str):
    """Department Admin: Delete an employee order"""
    try:
        # Find the order first to get employee info and price
        order = await db.orders.find_one({"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
        
        # Adjust employee balance before deleting the order
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
        
        # Now delete the order
        result = await db.orders.delete_one({"id": order_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
        
        return {"message": "Bestellung erfolgreich gelöscht und Saldo aktualisiert"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting order: {str(e)}")

@api_router.put("/orders/{order_id}")
async def update_order(order_id: str, order_update: dict):
    """Update an existing order"""
    try:
        # Find the existing order
        existing_order = await db.orders.find_one({"id": order_id})
        if not existing_order:
            raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
        
        # Update the order with new data
        update_fields = {}
        if "breakfast_items" in order_update:
            update_fields["breakfast_items"] = order_update["breakfast_items"]
            
            # Recalculate total price for breakfast items
            total_price = 0.0
            
            # Get current menu prices (department-specific)
            breakfast_menu = await db.menu_breakfast.find({"department_id": existing_order["department_id"]}).to_list(100)
            toppings_menu = await db.menu_toppings.find({"department_id": existing_order["department_id"]}).to_list(100)
            
            breakfast_prices = {item["roll_type"]: item["price"] for item in breakfast_menu}
            toppings_prices = {item["topping_type"]: item["price"] for item in toppings_menu}
            
            for item in order_update["breakfast_items"]:
                # Handle new format with white_halves and seeded_halves
                white_halves = item.get("white_halves", 0)
                seeded_halves = item.get("seeded_halves", 0)
                
                # Prices are per-half roll as set by admin
                white_price = breakfast_prices.get("weiss", 0.0)
                seeded_price = breakfast_prices.get("koerner", 0.0)
                
                total_price += (white_halves * white_price) + (seeded_halves * seeded_price)
                
                # Add toppings price (toppings are free currently)
                for topping in item.get("toppings", []):
                    total_price += toppings_prices.get(topping, 0.0)
                
                # Add boiled eggs price if applicable
                boiled_eggs = item.get("boiled_eggs", 0)
                if boiled_eggs > 0:
                    lunch_settings = await db.lunch_settings.find_one({}) or {"boiled_eggs_price": 0.50}
                    boiled_eggs_price = lunch_settings.get("boiled_eggs_price", 0.50)
                    total_price += boiled_eggs * boiled_eggs_price
                
                # Add lunch price if applicable
                if item.get("has_lunch"):
                    # Get daily lunch price for today (Berlin timezone)
                    today = get_berlin_date().strftime('%Y-%m-%d')
                    daily_price = await db.daily_lunch_prices.find_one({
                        "department_id": existing_order["department_id"],
                        "date": today
                    })
                    
                    if daily_price:
                        lunch_price = daily_price["lunch_price"]
                    else:
                        # Fall back to global lunch settings
                        lunch_settings = await db.lunch_settings.find_one({}) or {"price": 0.0}
                        lunch_price = lunch_settings["price"]
                    
                    # Lunch price should be added once per order, not multiplied by roll halves
                    total_price += lunch_price
                    
                    # Update the order's lunch information
                    update_fields["has_lunch"] = True
                    update_fields["lunch_price"] = lunch_price
            
            update_fields["total_price"] = total_price
        
        if "drink_items" in order_update:
            update_fields["drink_items"] = order_update["drink_items"]
            # TODO: Calculate total price for drinks
        
        if "sweet_items" in order_update:
            update_fields["sweet_items"] = order_update["sweet_items"]
            # TODO: Calculate total price for sweets
        
        # Update the order in database
        result = await db.orders.update_one(
            {"id": order_id},
            {"$set": update_fields}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
        
        # Update employee balance
        employee = await db.employees.find_one({"id": existing_order["employee_id"]})
        if employee:
            # Calculate balance difference
            old_price = existing_order.get("total_price", 0.0)
            new_price = update_fields.get("total_price", old_price)
            price_difference = new_price - old_price
            
            # Update employee balance
            new_breakfast_balance = employee.get("breakfast_balance", 0.0) + price_difference
            await db.employees.update_one(
                {"id": existing_order["employee_id"]},
                {"$set": {"breakfast_balance": new_breakfast_balance}}
            )
        
        return {"message": "Bestellung erfolgreich aktualisiert", "order_id": order_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Aktualisieren der Bestellung: {str(e)}")

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

@api_router.delete("/department-admin/breakfast-day/{department_id}/{date}")
async def delete_breakfast_day(department_id: str, date: str):
    """Admin: Delete all breakfast orders for a specific date and adjust employee balances"""
    try:
        # Validate date format
        parsed_date = datetime.fromisoformat(date).date()
        start_of_day = datetime.combine(parsed_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(parsed_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Find all breakfast orders for this department and date
        breakfast_orders = await db.orders.find({
            "department_id": department_id,
            "order_type": "breakfast",
            "timestamp": {
                "$gte": start_of_day.isoformat(),
                "$lte": end_of_day.isoformat()
            }
        }).to_list(1000)
        
        if not breakfast_orders:
            raise HTTPException(status_code=404, detail="Keine Frühstücks-Bestellungen für dieses Datum gefunden")
        
        deleted_count = 0
        total_amount_refunded = 0.0
        
        # Process each order
        for order in breakfast_orders:
            # Adjust employee balance
            employee = await db.employees.find_one({"id": order["employee_id"]})
            if employee:
                new_breakfast_balance = employee["breakfast_balance"] - order["total_price"]
                await db.employees.update_one(
                    {"id": order["employee_id"]},
                    {"$set": {"breakfast_balance": max(0, new_breakfast_balance)}}
                )
                total_amount_refunded += order["total_price"]
            
            # Delete the order
            await db.orders.delete_one({"id": order["id"]})
            deleted_count += 1
        
        return {
            "message": f"Frühstücks-Tag erfolgreich gelöscht",
            "deleted_orders": deleted_count,
            "total_refunded": round(total_amount_refunded, 2),
            "date": date
        }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültiges Datumsformat. Verwenden Sie YYYY-MM-DD.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Löschen des Frühstücks-Tags: {str(e)}")

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