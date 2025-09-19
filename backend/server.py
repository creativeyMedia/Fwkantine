from decimal import Decimal, ROUND_HALF_UP
from fastapi import FastAPI, APIRouter, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
import zoneinfo

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

# Helper functions for Multi-Department Balance Management
def initialize_subaccount_balances(employee_data):
    """Initialize subaccount_balances for new employees or existing ones without it"""
    if not employee_data.get('subaccount_balances'):
        # Initialize with all 4 departments, all balances at 0.0
        employee_data['subaccount_balances'] = {
            "fw4abteilung1": {"breakfast": 0.0, "drinks": 0.0},
            "fw4abteilung2": {"breakfast": 0.0, "drinks": 0.0}, 
            "fw4abteilung3": {"breakfast": 0.0, "drinks": 0.0},
            "fw4abteilung4": {"breakfast": 0.0, "drinks": 0.0}
        }
    return employee_data

def get_employee_balance(employee_data, department_id, balance_type):
    """Get balance for specific department and type, with fallback to main balances"""
    # Ensure subaccount_balances exists
    employee_data = initialize_subaccount_balances(employee_data)
    
    # For main department, use main balance fields (RÜCKWÄRTSKOMPATIBILITÄT)
    if department_id == employee_data.get('department_id'):
        if balance_type == 'breakfast':
            return employee_data.get('breakfast_balance', 0.0)
        elif balance_type in ['drinks', 'drinks_sweets']:
            return employee_data.get('drinks_sweets_balance', 0.0)
    
    # For other departments, use subaccount balances
    subaccounts = employee_data.get('subaccount_balances', {})
    dept_balances = subaccounts.get(department_id, {"breakfast": 0.0, "drinks": 0.0})
    
    if balance_type == 'breakfast':
        return dept_balances.get('breakfast', 0.0)
    elif balance_type in ['drinks', 'drinks_sweets']:
        return dept_balances.get('drinks', 0.0)
    
    return 0.0

async def update_employee_balance(employee_id, department_id, balance_type, amount_change):
    """Update employee balance for specific department and type"""
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
    
    # Initialize subaccounts if not exists
    employee = initialize_subaccount_balances(employee)
    
    # For main department, update main balance fields (RÜCKWÄRTSKOMPATIBILITÄT)
    if department_id == employee.get('department_id'):
        update_fields = {}
        if balance_type == 'breakfast':
            new_balance = employee.get('breakfast_balance', 0.0) + amount_change
            update_fields['breakfast_balance'] = new_balance
            # Also update subaccount for consistency
            employee['subaccount_balances'][department_id]['breakfast'] = new_balance
        elif balance_type in ['drinks', 'drinks_sweets']:
            new_balance = employee.get('drinks_sweets_balance', 0.0) + amount_change
            update_fields['drinks_sweets_balance'] = new_balance  
            # Also update subaccount for consistency
            employee['subaccount_balances'][department_id]['drinks'] = new_balance
        
        update_fields['subaccount_balances'] = employee['subaccount_balances']
        
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": update_fields}
        )
    else:
        # For other departments, only update subaccount balances
        if balance_type == 'breakfast':
            employee['subaccount_balances'][department_id]['breakfast'] += amount_change
        elif balance_type in ['drinks', 'drinks_sweets']:
            employee['subaccount_balances'][department_id]['drinks'] += amount_change
            
        await db.employees.update_one(
            {"id": employee_id},
            {"$set": {"subaccount_balances": employee['subaccount_balances']}}
        )

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

async def get_department_prices(department_id: str):
    """Get department-specific prices with fallback to global settings"""
    dept_settings = await db.department_settings.find_one({"department_id": department_id})
    
    if dept_settings:
        return {
            "boiled_eggs_price": dept_settings.get("boiled_eggs_price", 0.50),
            "fried_eggs_price": dept_settings.get("fried_eggs_price", 0.50),
            "coffee_price": dept_settings.get("coffee_price", 1.50)
        }
    
    # Fallback to global lunch settings
    lunch_settings = await db.lunch_settings.find_one()
    if lunch_settings:
        return {
            "boiled_eggs_price": lunch_settings.get("boiled_eggs_price", 0.50),
            "fried_eggs_price": lunch_settings.get("fried_eggs_price", 0.50),
            "coffee_price": lunch_settings.get("coffee_price", 1.50)
        }
    
    # Final fallback to defaults
    return {
        "boiled_eggs_price": 0.50,
        "fried_eggs_price": 0.50,
        "coffee_price": 1.50
    }

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

async def check_order_payment_protection(employee_id: str, order: dict):
    """Check if order is protected by payment timestamp (prevents cancellation after payment)"""
    # Get the most recent payment for this employee
    recent_payment = await db.payment_logs.find_one(
        {"employee_id": employee_id},
        sort=[("timestamp", -1)]  # Most recent first
    )
    
    if not recent_payment:
        return  # No payments found, order can be cancelled
    
    # Parse timestamps for comparison
    order_timestamp = datetime.fromisoformat(order["timestamp"].replace('Z', '+00:00'))
    payment_timestamp = recent_payment["timestamp"]
    
    # If payment timestamp is a string, parse it
    if isinstance(payment_timestamp, str):
        payment_timestamp = datetime.fromisoformat(payment_timestamp.replace('Z', '+00:00'))
    
    # If order was placed BEFORE the most recent payment, it's protected
    if order_timestamp < payment_timestamp:
        raise HTTPException(
            status_code=403,
            detail="Diese Bestellung kann nicht storniert werden, da bereits eine Zahlung nach der Bestellung erfolgt ist."
        )

# Enums
class OrderType(str, Enum):
    BREAKFAST = "breakfast"
    DRINKS = "drinks" 
    SWEETS = "sweets"

class RollType(str, Enum):
    WHITE = "weiss"  # White roll
    SEEDED = "koerner"  # Seeded roll

# ToppingType Enum entfernt - verwende flexible String-Namen aus der Datenbank

# Models
class Department(BaseModel):
    id: str  # KEINE automatischen UUIDs mehr - manuell setzen
    name: str
    password_hash: str = os.environ.get('DEPARTMENT_PASSWORD_DEFAULT', 'password1')
    admin_password_hash: str = os.environ.get('ADMIN_PASSWORD_DEFAULT', 'admin1')
    
class Employee(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    department_id: str  # Stamm-Wachabteilung
    breakfast_balance: float = 0.0
    drinks_sweets_balance: float = 0.0
    sort_order: int = 0  # For drag & drop sorting
    is_guest: bool = False  # Guest marker for employee dashboard sorting
    # ERWEITERT: Multi-Abteilungs-Subkonten (JSON-Struktur)
    # Format: {"fw4abteilung1": {"breakfast": 0.0, "drinks": 0.0}, "fw4abteilung2": {...}, ...}
    subaccount_balances: Optional[Dict[str, Dict[str, float]]] = None
    
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

class DepartmentSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str
    boiled_eggs_price: float = 0.50  # Price per boiled egg for this department
    fried_eggs_price: float = 0.50  # Price per fried egg for this department
    coffee_price: float = 1.50  # Daily coffee price for this department

class PayPalSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str
    enabled: bool = False  # Whether PayPal payment is enabled for this department
    breakfast_enabled: bool = False  # Whether breakfast PayPal button is enabled
    drinks_enabled: bool = False  # Whether drinks PayPal button is enabled
    use_separate_links: bool = False  # True = separate links for breakfast/drinks, False = same link for both
    combined_link: Optional[str] = None  # Used when use_separate_links = False
    breakfast_link: Optional[str] = None  # Used when use_separate_links = True
    drinks_link: Optional[str] = None  # Used when use_separate_links = True

class LunchSettings(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    price: float = 0.0
    enabled: bool = True
    boiled_eggs_price: float = 0.50  # Default price per boiled egg (global fallback)
    fried_eggs_price: float = 0.50  # Default price per fried egg (global fallback)
    coffee_price: float = 1.50  # Default price for daily coffee (global fallback)

class DailyLunchPrice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    department_id: str
    date: str  # YYYY-MM-DD format
    lunch_price: float
    lunch_name: str = ""  # NEU: Name/Titel des Mittagessens

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
    # NEW: Balance tracking for flexible payments
    balance_before: Optional[float] = None  # Saldo vor Einzahlung
    balance_after: Optional[float] = None   # Saldo nach Einzahlung

class BreakfastOrder(BaseModel):
    total_halves: int  # Total number of roll halves
    white_halves: int  # Number of white roll halves
    seeded_halves: int  # Number of seeded roll halves
    toppings: List[str]  # Exactly matches total_halves count - flexible string names
    has_lunch: bool = False
    boiled_eggs: int = 0  # Number of boiled breakfast eggs
    fried_eggs: int = 0  # Number of fried breakfast eggs
    has_coffee: bool = False  # Whether daily coffee is ordered
    
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
    notes: Optional[str] = None  # Free text field for special requests/notes
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
    is_guest: bool = False  # Optional guest marker for new employees

class OrderCreate(BaseModel):
    employee_id: str
    department_id: str
    order_type: OrderType
    breakfast_items: Optional[List[BreakfastOrder]] = []
    drink_items: Optional[Dict[str, int]] = {}
    sweet_items: Optional[Dict[str, int]] = {}
    notes: Optional[str] = None  # Free text field for special requests/notes

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

# NEW: Flexible Payment Request Models
class FlexiblePaymentRequest(BaseModel):
    payment_type: str  # "breakfast" or "drinks_sweets" (legacy)
    balance_type: Optional[str] = None  # "breakfast" or "drinks" (new subaccount system)
    amount: float      # Beliebiger Einzahlungsbetrag
    payment_method: Optional[str] = "cash"  # "cash", "bank_transfer", "adjustment", "other"
    notes: Optional[str] = ""  # Optionale Notizen (z.B. "Barzahlung 50€")
    
    def get_balance_type(self):
        """Helper to get the correct balance type (backward compatibility)"""
        return self.balance_type or self.payment_type

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


@api_router.post("/init-data")
async def initialize_default_data():
    """Initialize the database with default departments and menu items
    
    ⚠️ SICHERHEITSWARNUNG: Dieser Endpoint ist für Production-Umgebungen DEAKTIVIERT!
    Er kann echte Benutzerdaten überschreiben und sollte nur in Development verwendet werden.
    
    CRITICAL: This function NEVER updates existing department passwords.
    It only creates new departments if they don't exist.
    This preserves user-changed passwords permanently.
    """
    
    # SICHERHEITSCHECK: Nur bei komplett leerer Datenbank oder mit speziellem Flag
    existing_depts = await db.departments.find().to_list(100)
    allow_init = os.getenv('ALLOW_INIT_DATA', 'false').lower() == 'true'
    
    if os.getenv('ENVIRONMENT') == 'production' and len(existing_depts) > 0 and not allow_init:
        raise HTTPException(
            status_code=403, 
            detail=f"Datenbank nicht leer ({len(existing_depts)} Departments vorhanden)! Initialisierung nur bei leerer DB erlaubt."
        )
    
    if len(existing_depts) == 0:
        print("🟢 SAFE INIT: Datenbank ist leer - Erstinitialisierung erlaubt")
    elif allow_init:
        print("🟡 ADMIN INIT: ALLOW_INIT_DATA Flag gesetzt - Initialisierung erzwungen")
    else:
        print(f"🔒 BLOCKED: {len(existing_depts)} Departments vorhanden - Initialisierung blockiert")
    
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
            MenuItemToppings(department_id=dept["id"], topping_type="ruehrei", price=0.00),  # Free
            MenuItemToppings(department_id=dept["id"], topping_type="spiegelei", price=0.00),     # Free
            MenuItemToppings(department_id=dept["id"], topping_type="eiersalat", price=0.00),     # Free
            MenuItemToppings(department_id=dept["id"], topping_type="salami", price=0.00),        # Free
            MenuItemToppings(department_id=dept["id"], topping_type="schinken", price=0.00),           # Free
            MenuItemToppings(department_id=dept["id"], topping_type="kaese", price=0.00),        # Free
            MenuItemToppings(department_id=dept["id"], topping_type="butter", price=0.00)         # Free
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
    
    # Create default lunch settings with explicit boiled eggs price and coffee price
    # NUR für Development-Umgebung - NIE in Production überschreiben!
    if os.getenv('ENVIRONMENT') != 'production':
        lunch_settings = LunchSettings(price=0.0, enabled=True, boiled_eggs_price=0.50, coffee_price=1.50)
        
        # Check if lunch settings already exist
        existing_lunch_settings = await db.lunch_settings.find_one()
        if not existing_lunch_settings:
            # Insert new lunch settings ONLY if none exist
            await db.lunch_settings.insert_one(lunch_settings.dict())
            print("🔧 DEBUG: Created new lunch settings for development")
        else:
            # KRITISCHER SICHERHEITSFIX: Nur in Development und nur bei fehlendem coffee_price
            update_fields = {}
            # NIEMALS boiled_eggs_price überschreiben - das verursacht den 999.99€ Bug!
            # if "boiled_eggs_price" not in existing_lunch_settings or existing_lunch_settings["boiled_eggs_price"] == 999.99:
            #     update_fields["boiled_eggs_price"] = 0.50  # ← DEAKTIVIERT - VERURSACHTE DEN BUG
            
            if "coffee_price" not in existing_lunch_settings:
                update_fields["coffee_price"] = 1.50
            
            if update_fields:
                await db.lunch_settings.update_one(
                    {"id": existing_lunch_settings["id"]},
                    {"$set": update_fields}
                )
                print(f"🔧 DEBUG: Updated lunch settings fields: {update_fields}")
    else:
        print("🔒 PRODUCTION: Lunch settings initialization skipped for safety")
    
    return {"message": "Daten erfolgreich initialisiert"}

@api_router.post("/safe-init-empty-database")
async def safe_init_empty_database():
    """SICHERE Initialisierung NUR für komplett leere Datenbanken
    
    Diese API prüft zuerst ob die Datenbank wirklich leer ist und 
    initialisiert nur dann. Keine Gefahr für bestehende Daten!
    """
    
    # Prüfe alle Collections auf Leere
    collections_status = {}
    collections_to_check = ['departments', 'employees', 'orders', 'lunch_settings']
    
    total_documents = 0
    for collection_name in collections_to_check:
        count = await db[collection_name].count_documents({})
        collections_status[collection_name] = count
        total_documents += count
    
    if total_documents > 0:
        raise HTTPException(
            status_code=409, 
            detail=f"Datenbank nicht leer! Gefundene Dokumente: {collections_status}. Lösche zuerst alle Daten oder verwende normale init-data API."
        )
    
    print("🟢 SAFE INIT: Alle Collections sind leer - starte sichere Initialisierung")
    
    # Rufe die normale init-data Funktion auf, aber umgehe den Production-Check
    old_env = os.environ.get('ENVIRONMENT')
    try:
        os.environ['ENVIRONMENT'] = 'development'  # Temporär auf development setzen
        result = await initialize_default_data()
        return {
            "message": "🟢 SICHERE ERSTINITIALISIERUNG ERFOLGREICH!",
            "details": result,
            "collections_initialized": collections_status
        }
    finally:
        if old_env:
            os.environ['ENVIRONMENT'] = old_env  # Environment zurücksetzen
        else:
            os.environ.pop('ENVIRONMENT', None)

async def migrate_to_department_specific():
    """Migrate existing global menu items to department-specific items
    
    ⚠️ SICHERHEITSWARNUNG: Dieser Endpoint ist für Production-Umgebungen DEAKTIVIERT!
    Er kann bestehende Menü-Daten überschreiben und sollte nur einmalig verwendet werden.
    """
    
    # SICHERHEITSCHECK: Verhindere Ausführung in Production
    if os.getenv('ENVIRONMENT') == 'production':
        raise HTTPException(
            status_code=403, 
            detail="Migration in Production-Umgebung nicht erlaubt! Gefahr von Datenverlust."
        )
    
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
    """Login for department with password or master password"""
    dept = await db.departments.find_one({"name": login_data.department_name})
    if not dept:
        raise HTTPException(status_code=401, detail="Abteilung nicht gefunden")
    
    # Check master password first (with admin rights)
    master_password_env = os.environ.get('MASTER_PASSWORD', 'master123dev')
    if login_data.password == master_password_env:
        return {
            "department_id": dept["id"], 
            "department_name": dept["name"],
            "role": "master_admin",
            "access_level": "master"
        }
    
    # Check normal department password
    if dept["password_hash"] == login_data.password:
        return {"department_id": dept["id"], "department_name": dept["name"]}
    
    # Neither password matched
    raise HTTPException(status_code=401, detail="Ungültiger Name oder Passwort")

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
    """Login for department admin with admin password or master password"""
    dept = await db.departments.find_one({"name": login_data.department_name})
    if not dept:
        raise HTTPException(status_code=404, detail="Abteilung nicht gefunden")
    
    # Check master password first (with master admin rights)
    master_password_env = os.environ.get('MASTER_PASSWORD', 'master123dev')
    if login_data.admin_password == master_password_env:
        return {
            "department_id": dept["id"], 
            "department_name": dept["name"], 
            "role": "master_admin",
            "access_level": "master"
        }
    
    # Check normal admin password
    if dept["admin_password_hash"] == login_data.admin_password:
        return {"department_id": dept["id"], "department_name": dept["name"], "role": "department_admin"}
    
    # Neither password matched
    raise HTTPException(status_code=401, detail="Ungültiger Name oder Admin-Passwort")

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
    
    # Initialize subaccount balances for existing employees that don't have them
    updated_employees = []
    for emp in employees:
        emp = initialize_subaccount_balances(emp)
        updated_employees.append(emp)
        
        # Update database if subaccount_balances was missing
        if 'subaccount_balances' not in emp or emp['subaccount_balances'] is None:
            await db.employees.update_one(
                {"id": emp["id"]},
                {"$set": {"subaccount_balances": emp['subaccount_balances']}}
            )
    
    return [Employee(**emp) for emp in updated_employees]

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
    """Create a new employee with initialized subaccount balances"""
    employee = Employee(**employee_data.dict())
    
    # Initialize subaccount balances for new employee
    employee_dict = employee.dict()
    employee_dict = initialize_subaccount_balances(employee_dict)
    
    await db.employees.insert_one(employee_dict)
    return Employee(**employee_dict)

@api_router.post("/admin/migrate-subaccounts")
async def migrate_employee_subaccounts():
    """EINMALIGE MIGRATION: Initialize subaccount_balances for all existing employees
    
    ⚠️ SICHERHEITSWARNUNG: Dieser Endpoint sollte nur einmal ausgeführt werden!
    Er initialisiert das neue Subkonto-System für bestehende Mitarbeiter.
    """
    
    try:
        # Find all employees 
        all_employees = await db.employees.find().to_list(1000)
        
        migration_count = 0
        updated_count = 0
        
        for employee in all_employees:
            needs_update = False
            
            # Initialize subaccount balances if not exists
            if not employee.get('subaccount_balances'):
                employee = initialize_subaccount_balances(employee)
                needs_update = True
                migration_count += 1
            
            # Sync main balances with subaccount balances for main department
            main_dept = employee.get('department_id')
            if main_dept and main_dept in employee['subaccount_balances']:
                main_breakfast = employee.get('breakfast_balance', 0.0)
                main_drinks = employee.get('drinks_sweets_balance', 0.0)
                
                # Update subaccount to match main balances
                if (employee['subaccount_balances'][main_dept]['breakfast'] != main_breakfast or 
                    employee['subaccount_balances'][main_dept]['drinks'] != main_drinks):
                    
                    employee['subaccount_balances'][main_dept]['breakfast'] = main_breakfast
                    employee['subaccount_balances'][main_dept]['drinks'] = main_drinks
                    needs_update = True
                    updated_count += 1
            
            # Update employee in database if needed
            if needs_update:
                await db.employees.update_one(
                    {"id": employee["id"]},
                    {"$set": {"subaccount_balances": employee['subaccount_balances']}}
                )
        
        return {
            "message": f"✅ Migration erfolgreich abgeschlossen!",
            "migrated_employees": migration_count,
            "synchronized_balances": updated_count,
            "details": f"{migration_count} neue Subkonten erstellt, {updated_count} Balances synchronisiert"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration fehlgeschlagen: {str(e)}")

@api_router.post("/admin/complete-system-reset")
async def complete_system_reset():
    """ADMIN: Complete system reset - DELETE ALL orders, payment logs and reset all balances to 0€
    
    ⚠️ WARNING: This will delete ALL data and reset ALL balances!
    Only use for testing purposes.
    """
    
    try:
        # Count current data before deletion
        orders_count = await db.orders.count_documents({})
        payment_logs_count = await db.payment_logs.count_documents({})
        employees_count = await db.employees.count_documents({})
        
        # 1. DELETE ALL ORDERS
        delete_orders_result = await db.orders.delete_many({})
        
        # 2. DELETE ALL PAYMENT LOGS  
        delete_payments_result = await db.payment_logs.delete_many({})
        
        # 3. RESET ALL EMPLOYEE BALANCES TO 0€
        reset_employees_result = await db.employees.update_many(
            {},
            {
                "$set": {
                    "breakfast_balance": 0.0,
                    "drinks_sweets_balance": 0.0,
                    "subaccount_balances": {
                        "fw4abteilung1": {"breakfast": 0.0, "drinks": 0.0},
                        "fw4abteilung2": {"breakfast": 0.0, "drinks": 0.0}, 
                        "fw4abteilung3": {"breakfast": 0.0, "drinks": 0.0},
                        "fw4abteilung4": {"breakfast": 0.0, "drinks": 0.0}
                    }
                }
            }
        )
        
        return {
            "message": "🗑️ KOMPLETTER SYSTEM-RESET ERFOLGREICH!",
            "summary": {
                "orders_deleted": delete_orders_result.deleted_count,
                "payment_logs_deleted": delete_payments_result.deleted_count,
                "employees_reset": reset_employees_result.modified_count,
                "total_employees": employees_count
            },
            "details": {
                "orders_before": orders_count,
                "payment_logs_before": payment_logs_count,
                "all_balances_set_to": "0.00€",
                "subaccounts_reset": "All 4 departments set to 0.00€"
            },
            "warning": "ALL order history and payment logs have been permanently deleted!"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset fehlgeschlagen: {str(e)}")

# ERWEITERT: Temporary Employee Assignments (Geräteübergreifend)
class TemporaryAssignment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    employee_id: str  # Mitarbeiter der temporär hinzugefügt wird
    target_department_id: str  # Ziel-Wachabteilung wo der Mitarbeiter temporär arbeitet
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str  # Läuft um 23:59 Berlin Zeit ab

@api_router.post("/departments/{department_id}/temporary-employees")
async def add_temporary_employee(department_id: str, employee_data: dict):
    """Add an employee from another department as temporary worker until 23:59 Berlin time"""
    try:
        employee_id = employee_data.get("employee_id")
        if not employee_id:
            raise HTTPException(status_code=400, detail="employee_id ist erforderlich")
        
        # Prüfe ob Mitarbeiter existiert
        employee = await db.employees.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
        
        # Prüfe ob bereits temporär hinzugefügt (heute)
        today = datetime.now(timezone.utc).date()
        existing = await db.temporary_assignments.find_one({
            "employee_id": employee_id,
            "target_department_id": department_id,
            "expires_at": {"$gte": datetime.now(timezone.utc).isoformat()}
        })
        
        if existing:
            return {"message": "Mitarbeiter bereits temporär hinzugefügt", "assignment_id": existing["id"]}
        
        # Erstelle temporäre Zuordnung bis 23:59 Berlin Zeit
        berlin_tz = zoneinfo.ZoneInfo("Europe/Berlin")
        now_berlin = datetime.now(berlin_tz)
        expires_today = now_berlin.replace(hour=23, minute=59, second=0, microsecond=0)
        expires_utc = expires_today.astimezone(timezone.utc)
        
        assignment = TemporaryAssignment(
            employee_id=employee_id,
            target_department_id=department_id,
            expires_at=expires_utc.isoformat()
        )
        
        # Speichere in Datenbank
        await db.temporary_assignments.insert_one(assignment.dict())
        
        return {
            "message": "Mitarbeiter temporär hinzugefügt",
            "assignment_id": assignment.id,
            "employee_name": employee["name"],
            "expires_at": expires_utc.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Hinzufügen: {str(e)}")

@api_router.get("/departments/{department_id}/temporary-employees")
async def get_temporary_employees(department_id: str):
    """Get all temporary employees for a department (geräteübergreifend)"""
    try:
        # Finde alle aktiven temporären Zuordnungen
        now = datetime.now(timezone.utc).isoformat()
        assignments = await db.temporary_assignments.find({
            "target_department_id": department_id,
            "expires_at": {"$gte": now}
        }).to_list(100)
        
        # Lade Mitarbeiter-Details
        temporary_employees = []
        for assignment in assignments:
            employee = await db.employees.find_one({"id": assignment["employee_id"]})
            if employee:
                # Lade Abteilungs-Details
                dept = await db.departments.find_one({"id": employee["department_id"]})
                dept_name = dept["name"] if dept else employee["department_id"]
                
                temporary_employees.append({
                    "id": employee["id"],
                    "name": employee["name"],
                    "department_id": employee["department_id"],
                    "department_name": dept_name,
                    "assignment_id": assignment["id"],
                    "expires_at": assignment["expires_at"],
                    "isTemporary": True
                })
        
        return temporary_employees
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden: {str(e)}")

@api_router.delete("/departments/{department_id}/temporary-employees/{assignment_id}")
async def remove_temporary_employee(department_id: str, assignment_id: str):
    """Remove temporary employee assignment"""
    try:
        result = await db.temporary_assignments.delete_one({
            "id": assignment_id,
            "target_department_id": department_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Temporäre Zuordnung nicht gefunden")
        
        return {"message": "Temporäre Zuordnung entfernt"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Entfernen: {str(e)}")

@api_router.post("/admin/cleanup-expired-assignments")
async def cleanup_expired_assignments():
    """Cleanup expired temporary assignments (Cron-Job)"""
    try:
        now = datetime.now(timezone.utc).isoformat()
        result = await db.temporary_assignments.delete_many({
            "expires_at": {"$lt": now}
        })
        
        return {
            "message": "Abgelaufene Zuordnungen bereinigt",
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Bereinigung: {str(e)}")

# ERWEITERT: Subaccount Balance Management für Multi-Department System

@api_router.post("/department-admin/subaccount-payment/{employee_id}")
async def subaccount_flexible_payment(employee_id: str, payment_data: FlexiblePaymentRequest, admin_department: str):
    """Department Admin: Process flexible payment for employee's subaccount in admin's department
    
    This allows admins to manage balance for employees from other departments who have
    orders/balances in the admin's department (subaccount management).
    """
    try:
        employee = await db.employees.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
        
        # Initialize subaccounts if needed
        employee = initialize_subaccount_balances(employee)
        
        # Check if employee has subaccount balance in admin's department
        if admin_department not in employee.get('subaccount_balances', {}):
            raise HTTPException(status_code=400, detail="Mitarbeiter hat kein Subkonto in dieser Abteilung")
        
        # Get current subaccount balance for this department and balance type
        balance_type = payment_data.get_balance_type()
        current_balance = get_employee_balance(employee, admin_department, balance_type)
        
        # Payment INCREASES balance (reduces debt or adds credit)
        new_balance = current_balance + payment_data.amount
        
        # Update ONLY the subaccount balance for this department
        await update_employee_balance(employee_id, admin_department, balance_type, payment_data.amount)
        
        # Get readable department name
        department_doc = await db.departments.find_one({"id": admin_department})
        department_name = department_doc["name"] if department_doc else admin_department
        
        # Create payment log with subaccount tracking
        payment_log = PaymentLog(
            employee_id=employee_id,
            department_id=admin_department,  # The admin's department (subaccount)
            amount=payment_data.amount,
            payment_type=balance_type,  # Required field
            action="payment",  # Required field  
            admin_user=department_name,  # KORRIGIERT: Benutzerfreundlicher Name statt ID
            notes=f"Zahlung in {department_name} - {payment_data.notes or ''}".strip(' -'),
            balance_before=current_balance,
            balance_after=new_balance
        )
        
        # Save payment log
        payment_dict = prepare_for_mongo(payment_log.dict())
        await db.payment_logs.insert_one(payment_dict)
        
        # Get updated employee data for response
        updated_employee = await db.employees.find_one({"id": employee_id})
        updated_employee = initialize_subaccount_balances(updated_employee)
        updated_balance = get_employee_balance(updated_employee, admin_department, balance_type)
        
        return {
            "message": f"Subkonto-Zahlung erfolgreich verbucht",
            "employee_name": employee["name"],
            "department": admin_department,
            "balance_type": balance_type,
            "amount": payment_data.amount,
            "balance_before": current_balance,
            "balance_after": updated_balance,
            "payment_method": payment_data.payment_method
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Subkonto-Zahlung: {str(e)}")

@api_router.post("/department-admin/reset-subaccount-balance/{employee_id}")
async def reset_subaccount_balance(employee_id: str, balance_type: str, admin_department: str):
    """Admin: Reset employee's subaccount balance for specific department and balance type"""
    try:
        employee = await db.employees.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
        
        # Initialize subaccounts if needed
        employee = initialize_subaccount_balances(employee)
        
        # Check if employee has subaccount balance in admin's department
        if admin_department not in employee.get('subaccount_balances', {}):
            raise HTTPException(status_code=400, detail="Mitarbeiter hat kein Subkonto in dieser Abteilung")
        
        if balance_type not in ['breakfast', 'drinks', 'drinks_sweets']:
            raise HTTPException(status_code=400, detail="Ungültiger Saldo-Typ. Verwenden Sie: breakfast, drinks, drinks_sweets")
        
        # Get current balance
        current_balance = get_employee_balance(employee, admin_department, balance_type)
        
        # Reset only the subaccount balance (set to 0)
        reset_amount = -current_balance  # Amount needed to bring balance to 0
        await update_employee_balance(employee_id, admin_department, balance_type, reset_amount)
        
        # Get readable department name
        department_doc = await db.departments.find_one({"id": admin_department})
        department_name = department_doc["name"] if department_doc else admin_department
        
        # Create payment log for the reset
        payment_log = PaymentLog(
            employee_id=employee_id,
            department_id=admin_department,
            amount=reset_amount,
            payment_type=balance_type,  # Required field
            action="reset",  # Required field
            admin_user=department_name,  # KORRIGIERT: Benutzerfreundlicher Name statt ID
            notes=f"Subkonto-Saldo zurückgesetzt in {department_name}",
            balance_before=current_balance,
            balance_after=0.0
        )
        
        # Save payment log
        payment_dict = prepare_for_mongo(payment_log.dict())
        await db.payment_logs.insert_one(payment_dict)
        
        return {
            "message": f"Subkonto-Saldo erfolgreich zurückgesetzt",
            "employee_name": employee["name"],
            "department": admin_department,
            "balance_type": balance_type,
            "balance_before": current_balance,
            "balance_after": 0.0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Zurücksetzen des Subkonto-Saldos: {str(e)}")

# NEW: Multi-Department Employee Management Endpoints

@api_router.get("/departments/{department_id}/other-employees")
async def get_other_department_employees(department_id: str):
    """Get employees from OTHER departments for temporary assignment dropdown"""
    try:
        # Get all employees NOT from this department
        other_employees = await db.employees.find({
            "department_id": {"$ne": department_id},
            "is_guest": False  # Only regular employees, not guests
        }).sort("name", 1).to_list(1000)
        
        # Group by department for easier frontend handling
        employees_by_dept = {}
        for emp in other_employees:
            dept_id = emp["department_id"]
            if dept_id not in employees_by_dept:
                employees_by_dept[dept_id] = []
            
            # Get department name for display
            dept = await db.departments.find_one({"id": dept_id})
            dept_name = dept["name"] if dept else dept_id
            
            employees_by_dept[dept_id].append({
                "id": emp["id"],
                "name": emp["name"],
                "department_id": dept_id,
                "department_name": dept_name
            })
        
        return employees_by_dept
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Mitarbeiter: {str(e)}")

@api_router.get("/employees/{employee_id}/all-balances")
async def get_employee_all_balances(employee_id: str):
    """Get all balances (main + subaccounts) for an employee"""
    try:
        employee = await db.employees.find_one({"id": employee_id})
        if not employee:
            raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
        
        # Initialize subaccounts if needed
        employee = initialize_subaccount_balances(employee)
        
        # Prepare response with all balances
        result = {
            "employee_id": employee_id,
            "employee_name": employee["name"],
            "main_department_id": employee["department_id"],
            "main_department_name": "",  # Will be filled below
            "main_balances": {
                "breakfast": employee.get("breakfast_balance", 0.0),
                "drinks_sweets": employee.get("drinks_sweets_balance", 0.0)
            },
            "subaccount_balances": {}
        }
        
        # Get all department names
        departments = await db.departments.find().to_list(100)
        dept_names = {dept["id"]: dept["name"] for dept in departments}
        
        result["main_department_name"] = dept_names.get(employee["department_id"], employee["department_id"])
        
        # Add all subaccount balances with department names
        for dept_id, balances in employee["subaccount_balances"].items():
            result["subaccount_balances"][dept_id] = {
                "department_name": dept_names.get(dept_id, dept_id),
                "breakfast": balances.get("breakfast", 0.0),
                "drinks": balances.get("drinks", 0.0),
                "total": balances.get("breakfast", 0.0) + balances.get("drinks", 0.0)
            }
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Kontostände: {str(e)}")

# Lunch settings routes (UNVERÄNDERT - bestehende Kompatibilität)
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
async def update_lunch_settings(price: float, department_id: str = None):
    """Update lunch price and retroactively apply to all today's lunch orders for specific department"""
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
    
    # Find all today's breakfast orders with lunch (optionally filtered by department)
    query = {
        "order_type": "breakfast",
        "timestamp": {
            "$gte": start_of_day.isoformat(),
            "$lte": end_of_day.isoformat()
        }
    }
    
    # If department_id is provided, only update orders from that department
    if department_id:
        query["department_id"] = department_id
    
    todays_orders = await db.orders.find(query).to_list(1000)
    
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
                print(f"DEBUG: Order {order['id'][:8]}: old_total={old_total}, new_total={new_total}, balance_diff={balance_diff}")
                if balance_diff != 0:
                    # KORRIGIERT: Invert balance_diff because when order price decreases, 
                    # employee should owe LESS money (balance improves)
                    balance_improvement = -balance_diff
                    
                    # Check if this is a home department order or guest order
                    employee = await db.employees.find_one({"id": order["employee_id"]})
                    if employee:
                        employee_home_dept = employee.get("department_id")
                        order_dept = order.get("department_id")
                        
                        print(f"DEBUG: Employee {order['employee_id'][:8]}: home_dept={employee_home_dept}, order_dept={order_dept}, balance_improvement={balance_improvement}")
                        if employee_home_dept == order_dept:
                            # HOME DEPARTMENT ORDER: Update main balance
                            print(f"DEBUG: Updating main balance for home department order")
                            await db.employees.update_one(
                                {"id": order["employee_id"]},
                                {"$inc": {"breakfast_balance": balance_improvement}}
                            )
                        else:
                            # GUEST DEPARTMENT ORDER: Update subaccount balance
                            print(f"DEBUG: Updating subaccount balance for guest department order")
                            await update_employee_balance(order["employee_id"], order_dept, 'breakfast', balance_improvement)
                
                updated_orders += 1
    
    return {
        "message": "Lunch-Preis erfolgreich aktualisiert", 
        "price": price,
        "updated_orders": updated_orders
    }

@api_router.get("/department-settings/{department_id}")
async def get_department_settings(department_id: str):
    """Get department-specific settings (eggs and coffee prices)"""
    dept_settings = await db.department_settings.find_one({"department_id": department_id})
    if not dept_settings:
        # Create default settings if none exist
        default_settings = DepartmentSettings(department_id=department_id)
        await db.department_settings.insert_one(default_settings.dict())
        return default_settings
    
    # Clean the document by removing MongoDB _id field
    clean_settings = {k: v for k, v in dept_settings.items() if k != '_id'}
    return clean_settings

@api_router.get("/department-settings/{department_id}/boiled-eggs-price")
async def get_department_boiled_eggs_price(department_id: str):
    """Get boiled eggs price for a specific department"""
    dept_settings = await db.department_settings.find_one({"department_id": department_id})
    if dept_settings:
        return {"department_id": department_id, "boiled_eggs_price": dept_settings["boiled_eggs_price"]}
    else:
        # Return default price if no department-specific settings exist
        return {"department_id": department_id, "boiled_eggs_price": 0.50}

@api_router.put("/department-settings/{department_id}/boiled-eggs-price")
async def update_department_boiled_eggs_price(department_id: str, price: float):
    """Update boiled eggs price for a specific department"""
    if price < 0:
        raise HTTPException(status_code=400, detail="Preis muss mindestens 0.00 € betragen")
    
    dept_settings = await db.department_settings.find_one({"department_id": department_id})
    if dept_settings:
        await db.department_settings.update_one(
            {"department_id": department_id},
            {"$set": {"boiled_eggs_price": price}}
        )
    else:
        new_settings = DepartmentSettings(department_id=department_id, boiled_eggs_price=price)
        await db.department_settings.insert_one(new_settings.dict())
    
    return {"message": "Abteilungsspezifischer Kochei-Preis erfolgreich aktualisiert", "department_id": department_id, "price": price}

@api_router.get("/department-settings/{department_id}/fried-eggs-price")
async def get_department_fried_eggs_price(department_id: str):
    """Get fried eggs price for a specific department"""
    dept_settings = await db.department_settings.find_one({"department_id": department_id})
    if dept_settings:
        return {"department_id": department_id, "fried_eggs_price": dept_settings.get("fried_eggs_price", 0.50)}
    else:
        # Return default price if no department-specific settings exist
        return {"department_id": department_id, "fried_eggs_price": 0.50}

@api_router.put("/department-settings/{department_id}/fried-eggs-price")
async def update_department_fried_eggs_price(department_id: str, price: float):
    """Update fried eggs price for a specific department"""
    if price < 0:
        raise HTTPException(status_code=400, detail="Preis muss mindestens 0.00 € betragen")
    
    dept_settings = await db.department_settings.find_one({"department_id": department_id})
    if dept_settings:
        await db.department_settings.update_one(
            {"department_id": department_id},
            {"$set": {"fried_eggs_price": price}}
        )
    else:
        new_settings = DepartmentSettings(department_id=department_id, fried_eggs_price=price)
        await db.department_settings.insert_one(new_settings.dict())
    
    return {"message": "Abteilungsspezifischer Spiegelei-Preis erfolgreich aktualisiert", "department_id": department_id, "price": price}

@api_router.get("/department-settings/{department_id}/coffee-price")
async def get_department_coffee_price(department_id: str):
    """Get coffee price for a specific department"""
    dept_settings = await db.department_settings.find_one({"department_id": department_id})
    if dept_settings:
        return {"department_id": department_id, "coffee_price": dept_settings["coffee_price"]}
    else:
        # Return default price if no department-specific settings exist
        return {"department_id": department_id, "coffee_price": 1.50}

@api_router.put("/department-settings/{department_id}/coffee-price")
async def update_department_coffee_price(department_id: str, price: float):
    """Update coffee price for a specific department"""
    if price < 0:
        raise HTTPException(status_code=400, detail="Preis muss mindestens 0.00 € betragen")
    
    dept_settings = await db.department_settings.find_one({"department_id": department_id})
    if dept_settings:
        await db.department_settings.update_one(
            {"department_id": department_id},
            {"$set": {"coffee_price": price}}
        )
    else:
        new_settings = DepartmentSettings(department_id=department_id, coffee_price=price)
        await db.department_settings.insert_one(new_settings.dict())
    
    return {"message": "Abteilungsspezifischer Kaffee-Preis erfolgreich aktualisiert", "department_id": department_id, "price": price}

@api_router.get("/department-paypal-settings/{department_id}")
async def get_department_paypal_settings(department_id: str):
    """Get PayPal settings for a specific department"""
    paypal_settings = await db.paypal_settings.find_one({"department_id": department_id})
    if not paypal_settings:
        # Create default settings if none exist
        default_settings = PayPalSettings(department_id=department_id)
        await db.paypal_settings.insert_one(default_settings.dict())
        return default_settings
    
    # Clean the document by removing MongoDB _id field
    clean_settings = {k: v for k, v in paypal_settings.items() if k != '_id'}
    return clean_settings

@api_router.put("/department-paypal-settings/{department_id}")
async def update_department_paypal_settings(department_id: str, settings: PayPalSettings):
    """Update PayPal settings for a specific department"""
    # Validation
    if settings.enabled:
        # Check if at least one button is enabled
        if not settings.breakfast_enabled and not settings.drinks_enabled:
            raise HTTPException(status_code=400, detail="Mindestens ein PayPal-Button muss aktiviert werden wenn PayPal aktiviert ist")
        
        if settings.use_separate_links:
            # Separate links mode - check individual links
            if settings.breakfast_enabled and not settings.breakfast_link:
                raise HTTPException(status_code=400, detail="Frühstück-Link ist erforderlich wenn Frühstück-Button aktiviert ist")
            if settings.drinks_enabled and not settings.drinks_link:
                raise HTTPException(status_code=400, detail="Getränke-Link ist erforderlich wenn Getränke-Button aktiviert ist")
        else:
            # Combined link mode - one link for all enabled buttons
            if not settings.combined_link:
                raise HTTPException(status_code=400, detail="Gemeinsamer Link ist erforderlich wenn aktivierte Buttons den gleichen Link verwenden sollen")
    
    # Set department_id to ensure consistency
    settings.department_id = department_id
    
    existing_settings = await db.paypal_settings.find_one({"department_id": department_id})
    if existing_settings:
        await db.paypal_settings.update_one(
            {"department_id": department_id},
            {"$set": settings.dict()}
        )
    else:
        await db.paypal_settings.insert_one(settings.dict())
    
    return {"message": "PayPal-Einstellungen erfolgreich aktualisiert", "department_id": department_id}

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

@api_router.put("/lunch-settings/fried-eggs-price")
async def update_fried_eggs_price(price: float):
    """Update fried eggs price"""
    if price < 0:
        raise HTTPException(status_code=400, detail="Preis muss mindestens 0.00 € betragen")
    
    lunch_settings = await db.lunch_settings.find_one()
    if lunch_settings:
        await db.lunch_settings.update_one(
            {"id": lunch_settings["id"]},
            {"$set": {"fried_eggs_price": price}}
        )
    else:
        new_settings = LunchSettings(fried_eggs_price=price)
        await db.lunch_settings.insert_one(new_settings.dict())
    
    return {"message": "Spiegelei-Preis erfolgreich aktualisiert", "price": price}

@api_router.put("/lunch-settings/coffee-price")
async def update_coffee_price(price: float):
    """Update coffee price"""
    if price < 0:
        raise HTTPException(status_code=400, detail="Preis muss mindestens 0.00 € betragen")
    
    # Get current settings
    lunch_settings = await db.lunch_settings.find_one()
    
    if lunch_settings:
        await db.lunch_settings.update_one(
            {"id": lunch_settings["id"]},
            {"$set": {"coffee_price": price}}
        )
    else:
        # Create new settings if none exist
        new_settings = LunchSettings(price=0.0, enabled=True, boiled_eggs_price=0.50, coffee_price=price)
        await db.lunch_settings.insert_one(new_settings.dict())

    return {"message": "Kaffee-Preis erfolgreich aktualisiert", "price": price}

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
async def set_daily_lunch_price(department_id: str, date: str, lunch_price: float, lunch_name: str = ""):
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
            {"$set": {"lunch_price": lunch_price, "lunch_name": lunch_name}}
        )
    else:
        # Create new
        daily_price = DailyLunchPrice(
            department_id=department_id,
            date=date,
            lunch_price=lunch_price,
            lunch_name=lunch_name
        )
        await db.daily_lunch_prices.insert_one(daily_price.dict())
    
    # Now retroactively update all lunch orders from that specific day (Berlin timezone)
    start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(date)
    
    updated_orders = 0
    
    # Find all NON-CANCELLED breakfast orders with lunch from that day
    # Use $or to handle missing is_cancelled field, null, false, and exclude true
    orders_cursor = db.orders.find({
        "department_id": department_id,
        "order_type": "breakfast", 
        "has_lunch": True,
        "$or": [
            {"is_cancelled": {"$exists": False}},  # Field doesn't exist
            {"is_cancelled": None},                # Field is null
            {"is_cancelled": False}                # Field is false
        ],
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
            # If price increases (+price_difference), balance should decrease (-price_difference)
            
            # KORRIGIERT: Check if this is a home department order or guest order
            employee = await db.employees.find_one({"id": order["employee_id"]})
            if employee:
                employee_home_dept = employee.get("department_id")
                order_dept = order.get("department_id", department_id)
                
                print(f"DEBUG DAILY: Order {order['id'][:8]}: employee_home={employee_home_dept}, order_dept={order_dept}, price_diff={price_difference}")
                
                if employee_home_dept == order_dept:
                    # HOME DEPARTMENT ORDER: Update main balance
                    print(f"DEBUG DAILY: Updating main balance by {-price_difference}")
                    await db.employees.update_one(
                        {"id": order["employee_id"]},
                        {"$inc": {"breakfast_balance": -price_difference}}
                    )
                else:
                    # GUEST DEPARTMENT ORDER: Update subaccount balance
                    print(f"DEBUG DAILY: Updating subaccount balance by {-price_difference}")
                    await update_employee_balance(order["employee_id"], order_dept, 'breakfast', -price_difference)
            
            updated_orders += 1
    
    return {
        "message": "Tages-Mittagessen-Preis erfolgreich gesetzt",
        "date": date,
        "lunch_price": lunch_price,
        "lunch_name": lunch_name,
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
        return {
            "date": date, 
            "lunch_price": daily_price["lunch_price"],
            "lunch_name": daily_price.get("lunch_name", "")
        }
    else:
        # NEW: Always return 0.0 for new days - admin must set price manually each day
        return {"date": date, "lunch_price": 0.0, "lunch_name": ""}

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

@api_router.get("/departments/{department_id}/employees-with-subaccount-balances")
async def get_employees_with_subaccount_balances(department_id: str):
    """OPTIMIERT: Get all employees with non-zero subaccount balances in the specified department in one API call"""
    try:
        # Find all employees who have non-zero subaccount balances in the specified department
        pipeline = [
            {
                "$match": {
                    f"subaccount_balances.{department_id}": {"$exists": True}
                }
            },
            {
                "$addFields": {
                    "current_dept_balance": f"$subaccount_balances.{department_id}",
                    "has_balance": {
                        "$or": [
                            {"$ne": [f"$subaccount_balances.{department_id}.breakfast", 0]},
                            {"$ne": [f"$subaccount_balances.{department_id}.drinks", 0]}
                        ]
                    }
                }
            },
            {
                "$match": {
                    "has_balance": True,
                    "department_id": {"$ne": department_id}  # Exclude employees from the same department
                }
            }
        ]
        
        employees = await db.employees.aggregate(pipeline).to_list(None)
        
        # Get department names for display
        departments = await db.departments.find({}).to_list(100)
        dept_names = {dept["id"]: dept["name"] for dept in departments}
        
        # Format response
        result = []
        for employee in employees:
            current_dept_balance = employee.get("current_dept_balance", {"breakfast": 0, "drinks": 0})
            result.append({
                "id": employee["id"],
                "name": employee["name"],
                "department_id": employee["department_id"],
                "department_name": dept_names.get(employee["department_id"], "Unbekannt"),
                "main_department_name": dept_names.get(employee["department_id"], "Unbekannt"),
                "subaccount_balance": current_dept_balance
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Mitarbeiter: {str(e)}")

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
            "is_cancelled": {"$ne": True},  # Only check non-cancelled orders
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
            # NEW: Default to 0.0 for new days - admin must set price manually each day
            lunch_price = 0.0
        
        # Get department-specific prices
        department_prices = await get_department_prices(order_data.department_id)
        boiled_eggs_price = department_prices["boiled_eggs_price"]
        fried_eggs_price = department_prices["fried_eggs_price"]
        coffee_price = department_prices["coffee_price"]
        
        for breakfast_item in order_data.breakfast_items:
            # Allow orders without rolls (just eggs, coffee and/or lunch)
            has_rolls = breakfast_item.total_halves > 0
            has_extras = breakfast_item.boiled_eggs > 0 or breakfast_item.fried_eggs > 0 or breakfast_item.has_lunch or breakfast_item.has_coffee
            
            if not has_rolls and not has_extras:
                raise HTTPException(
                    status_code=400, 
                    detail="Bitte wählen Sie mindestens Brötchen, Frühstückseier, Kaffee oder Mittagessen"
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
            
            # Fried eggs price
            if breakfast_item.fried_eggs > 0:
                total_price += fried_eggs_price * breakfast_item.fried_eggs
            
            # Coffee price (daily flat rate)
            if breakfast_item.has_coffee:
                total_price += coffee_price
    
    elif order_data.order_type == OrderType.DRINKS and order_data.drink_items:
        drinks_menu = await db.menu_drinks.find({"department_id": order_data.department_id}).to_list(100)
        drink_prices = {item["id"]: item["price"] for item in drinks_menu}
        
        for drink_id, quantity in order_data.drink_items.items():
            drink_price = drink_prices.get(drink_id, 0.0)
            total_price += drink_price * quantity
        
        # Store drinks orders as negative amounts (representing employee debt)
        total_price = -total_price
            
    elif order_data.order_type == OrderType.SWEETS and order_data.sweet_items:
        sweets_menu = await db.menu_sweets.find({"department_id": order_data.department_id}).to_list(100)
        sweet_prices = {item["id"]: item["price"] for item in sweets_menu}
        
        for sweet_id, quantity in order_data.sweet_items.items():
            sweet_price = sweet_prices.get(sweet_id, 0.0)
            total_price += sweet_price * quantity
        
        # Store sweets orders as negative amounts (representing employee debt)
        total_price = -total_price
    
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
    
    # Update employee balance (ERWEITERT für Subkonten mit korrekter Gastbestellungslogik)
    employee = await db.employees.find_one({"id": order_data.employee_id})
    if employee:
        # KORRIGIERT: Unterscheide zwischen Stammbestellung und Gastbestellung
        is_home_department = (order_data.department_id == employee.get("department_id"))
        
        if order_data.order_type == OrderType.BREAKFAST:
            if is_home_department:
                # STAMMBESTELLUNG: Update NUR main balance (subaccount wird in update_employee_balance automatisch synchronisiert)
                new_breakfast_balance = employee["breakfast_balance"] - total_price
                await db.employees.update_one(
                    {"id": order_data.employee_id},
                    {"$set": {"breakfast_balance": new_breakfast_balance}}
                )
            else:
                # GASTBESTELLUNG: Update NUR subaccount balance
                await update_employee_balance(order_data.employee_id, order_data.department_id, 'breakfast', -total_price)
                
        else:  # DRINKS or SWEETS
            if is_home_department:
                # STAMMBESTELLUNG: Update NUR main balance (subaccount wird in update_employee_balance automatisch synchronisiert)
                new_drinks_sweets_balance = employee["drinks_sweets_balance"] + total_price
                await db.employees.update_one(
                    {"id": order_data.employee_id},
                    {"$set": {"drinks_sweets_balance": new_drinks_sweets_balance}}
                )
            else:
                # GASTBESTELLUNG: Update NUR subaccount balance
                await update_employee_balance(order_data.employee_id, order_data.department_id, 'drinks', total_price)
    
    return order

@api_router.get("/orders/daily-revenue/{department_id}/{date}")
async def get_daily_revenue(department_id: str, date: str):
    """Get separated breakfast and lunch revenue for a specific day"""
    
    try:
        parsed_date = datetime.fromisoformat(date).date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Ungültiges Datumsformat. Verwenden Sie YYYY-MM-DD.")
    
    # Get orders for this specific date using Berlin timezone boundaries
    start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(parsed_date)
    
    orders = await db.orders.find({
        "department_id": department_id,
        "order_type": "breakfast",
        "timestamp": {
            "$gte": start_of_day_utc.isoformat(),
            "$lte": end_of_day_utc.isoformat()
        },
        "$or": [
            {"is_cancelled": {"$exists": False}},  # Legacy orders without is_cancelled field
            {"is_cancelled": False}                # Explicitly not cancelled
        ]
    }).to_list(1000)
    
    breakfast_revenue = 0.0
    lunch_revenue = 0.0
    total_orders = len(orders)
    
    if orders:
        # Get department prices
        try:
            white_menu = await db.menu_breakfast.find_one({"roll_type": "weiss", "department_id": department_id})
            white_roll_price = white_menu.get("price", 0.50) if white_menu else 0.50
            
            seeded_menu = await db.menu_breakfast.find_one({"roll_type": "koerner", "department_id": department_id})
            seeded_roll_price = seeded_menu.get("price", 0.60) if seeded_menu else 0.60
            
            department_prices = await get_department_prices(department_id)
            eggs_price = department_prices["boiled_eggs_price"]
            coffee_price = department_prices["coffee_price"]
        except:
            white_roll_price = 0.50
            seeded_roll_price = 0.60
            eggs_price = 0.50
            coffee_price = 1.50
        
        # Get daily lunch price
        daily_lunch_price_doc = await db.daily_lunch_prices.find_one({
            "department_id": department_id,
            "date": parsed_date.isoformat()
        })
        daily_lunch_price = daily_lunch_price_doc["lunch_price"] if daily_lunch_price_doc else 0.0
        
        for order in orders:
            # IMPORTANT: Sponsored orders should COUNT toward revenue!
            # Sponsoring is just cost redistribution, total revenue stays the same
            
            # Skip ONLY pure sponsor orders (they're not actual food orders)
            if order.get("is_sponsor_order") and not order.get("breakfast_items"):
                continue
            
            for item in order.get("breakfast_items", []):
                # Calculate breakfast revenue (rolls + eggs ONLY - coffee excluded from statistics)
                white_halves = item.get("white_halves", 0)
                seeded_halves = item.get("seeded_halves", 0)
                boiled_eggs = item.get("boiled_eggs", 0)
                
                breakfast_item_cost = (white_halves * white_roll_price) + (seeded_halves * seeded_roll_price) + (boiled_eggs * eggs_price)
                breakfast_revenue += breakfast_item_cost
                
                # Coffee is excluded from revenue statistics (but remains in employee balance)
                # Coffee is neither sponsored nor counted in statistics
                
                # Calculate lunch revenue
                if item.get("has_lunch", False):
                    lunch_revenue += daily_lunch_price
    
    return {
        "date": date,
        "breakfast_revenue": round(breakfast_revenue, 2),
        "lunch_revenue": round(lunch_revenue, 2),
        "total_revenue": round(breakfast_revenue + lunch_revenue, 2),
        "total_orders": total_orders
    }


@api_router.get("/orders/separated-revenue/{department_id}")
async def get_separated_revenue(department_id: str, days_back: int = 30):
    """Get separated breakfast and lunch revenue for a department"""
    
    # Get date range (Berlin timezone)
    end_date = get_berlin_date()
    start_date = end_date - timedelta(days=days_back)
    
    current_date = start_date
    total_breakfast_revenue = 0.0
    total_lunch_revenue = 0.0
    
    while current_date <= end_date:
        # Get orders for this specific date using Berlin timezone boundaries
        start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(current_date)
        
        orders = await db.orders.find({
            "department_id": department_id,
            "order_type": "breakfast",
            "timestamp": {
                "$gte": start_of_day_utc.isoformat(),
                "$lte": end_of_day_utc.isoformat()
            },
            "$or": [
                {"is_cancelled": {"$exists": False}},  # Legacy orders without is_cancelled field
                {"is_cancelled": False}                # Explicitly not cancelled
            ]
        }).to_list(1000)
        
        if orders:  # Only include dates with orders
            daily_breakfast_revenue = 0.0
            daily_lunch_revenue = 0.0
            
            # Get department prices
            try:
                white_menu = await db.menu_breakfast.find_one({"roll_type": "weiss", "department_id": department_id})
                white_roll_price = white_menu.get("price", 0.50) if white_menu else 0.50
                
                seeded_menu = await db.menu_breakfast.find_one({"roll_type": "koerner", "department_id": department_id})
                seeded_roll_price = seeded_menu.get("price", 0.60) if seeded_menu else 0.60
                
                department_prices = await get_department_prices(department_id)
                eggs_price = department_prices["boiled_eggs_price"]
                coffee_price = department_prices["coffee_price"]
            except:
                white_roll_price = 0.50
                seeded_roll_price = 0.60
                eggs_price = 0.50
                coffee_price = 1.50
            
            # Get daily lunch price for this date
            daily_lunch_price_doc = await db.daily_lunch_prices.find_one({
                "department_id": department_id,
                "date": current_date.isoformat()
            })
            daily_lunch_price = daily_lunch_price_doc["lunch_price"] if daily_lunch_price_doc else 0.0
            
            for order in orders:
                # IMPORTANT: Sponsored orders should COUNT toward revenue!
                # Sponsoring is just cost redistribution, total revenue stays the same
                
                # Skip ONLY pure sponsor orders (they're not actual food orders)
                if order.get("is_sponsor_order") and not order.get("breakfast_items"):
                    continue
                
                for item in order.get("breakfast_items", []):
                    # Calculate breakfast revenue (rolls + eggs ONLY - coffee excluded from statistics)
                    white_halves = item.get("white_halves", 0)
                    seeded_halves = item.get("seeded_halves", 0)
                    boiled_eggs = item.get("boiled_eggs", 0)
                    
                    breakfast_item_cost = (white_halves * white_roll_price) + (seeded_halves * seeded_roll_price) + (boiled_eggs * eggs_price)
                    daily_breakfast_revenue += breakfast_item_cost
                    
                    # Coffee is excluded from revenue statistics (but remains in employee balance)
                    # Coffee is neither sponsored nor counted in statistics
                    
                    # Calculate lunch revenue
                    if item.get("has_lunch", False):
                        daily_lunch_revenue += daily_lunch_price
            
            total_breakfast_revenue += daily_breakfast_revenue
            total_lunch_revenue += daily_lunch_revenue
        
        current_date += timedelta(days=1)
    
    return {
        "breakfast_revenue": round(total_breakfast_revenue, 2),
        "lunch_revenue": round(total_lunch_revenue, 2),
        "total_revenue": round(total_breakfast_revenue + total_lunch_revenue, 2),
        "days_back": days_back
    }


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
            },
            "$or": [
                {"is_cancelled": {"$exists": False}},  # Legacy orders without is_cancelled field
                {"is_cancelled": False}                # Explicitly not cancelled
            ]
        }).to_list(1000)
        
        if orders:  # Only include dates with orders (as originally intended)
            # Get daily lunch price and name for days WITH orders
            daily_lunch_price_doc = await db.daily_lunch_prices.find_one({
                "department_id": department_id,
                "date": current_date.isoformat()
            })
            daily_lunch_price = daily_lunch_price_doc["lunch_price"] if daily_lunch_price_doc else 0.0
            lunch_name = daily_lunch_price_doc.get("lunch_name", "") if daily_lunch_price_doc else ""
            # CORRECTED: Filter out sponsor orders from statistics (they're not real food orders)
            real_orders = [order for order in orders if not order.get("is_sponsor_order", False)]
            
            # Calculate daily summary using only real orders
            breakfast_summary = {}
            employee_orders = {}
            total_orders = len(real_orders)  # Only count real orders, not sponsor orders
            # SIMPLIFIED: Calculate total_amount from individual employee totals at the END
            # This prevents double-counting and ensures consistency
            total_amount = Decimal('0')  # Use Decimal for financial precision
            
            for order in real_orders:  # Only process real orders for employee statistics
                if order.get("breakfast_items"):
                    # Get employee info
                    employee = await db.employees.find_one({"id": order["employee_id"]})
                    employee_name = employee["name"] if employee else "Unknown"
                    
                    # Create unique key combining name and employee_id to avoid duplicate name aggregation
                    employee_key = f"{employee_name} (ID: {order['employee_id'][-8:]})"  # Show last 8 chars of ID
                    
                    if employee_key not in employee_orders:
                        employee_orders[employee_key] = {
                            "white_halves": 0, 
                            "seeded_halves": 0, 
                            "boiled_eggs": 0,  # Add boiled eggs tracking
                            "fried_eggs": 0,  # Add fried eggs tracking
                            "has_lunch": False,  # Add lunch tracking
                            "lunch_name": "",  # NEU: Name des Mittagessens
                            "has_coffee": False,  # Add coffee tracking
                            "notes": "",  # Initialize empty - will be populated during processing
                            "toppings": {}, 
                            "total_amount": 0,
                            "is_sponsored": False,  # Add sponsored status tracking
                            "sponsored_meal_type": None,  # Add sponsored meal type tracking
                            "employee_department_id": employee.get("department_id") if employee else None,  # NEU: Stammabteilung des Mitarbeiters
                            "order_department_id": order.get("department_id")  # NEU: Abteilung der Bestellung
                        }
                    
                    # Calculate individual employee total_amount considering sponsoring
                    order_amount = 0
                    if order.get("is_sponsored") and not order.get("is_sponsor_order"):
                        # For sponsored orders (not sponsor's own order), calculate only non-sponsored costs
                        # BUT KEEP THE EMPLOYEE IN THE STATISTICS FOR SHOPPING LIST!
                        
                        # CRITICAL FIX: Set sponsored status fields for frontend
                        employee_orders[employee_key]["is_sponsored"] = True
                        employee_orders[employee_key]["sponsored_meal_type"] = order.get("sponsored_meal_type", "")
                        
                        sponsored_meal_types = order.get("sponsored_meal_type", "")
                        if sponsored_meal_types:
                            # Handle comma-separated meal types (e.g., "breakfast,lunch")
                            sponsored_types_list = sponsored_meal_types.split(",")
                            order_total_cost = order.get("total_price", 0)
                            remaining_cost = order_total_cost
                            
                            # Subtract breakfast cost if sponsored
                            if "breakfast" in sponsored_types_list:
                                sponsored_breakfast_cost = 0
                                for item in order.get("breakfast_items", []):
                                    # Calculate actual breakfast items cost (rolls + eggs)
                                    white_halves = item.get("white_halves", 0)
                                    seeded_halves = item.get("seeded_halves", 0)
                                    boiled_eggs = item.get("boiled_eggs", 0)
                                    
                                    # Get menu prices (use defaults if not found)
                                    white_roll_price = 0.50  # Default
                                    seeded_roll_price = 0.60  # Default
                                    
                                    # Try to get actual department prices
                                    try:
                                        white_menu = await db.menu_breakfast.find_one({"roll_type": "weiss", "department_id": department_id})
                                        if white_menu:
                                            white_roll_price = white_menu.get("price", 0.50)
                                        
                                        seeded_menu = await db.menu_breakfast.find_one({"roll_type": "koerner", "department_id": department_id})
                                        if seeded_menu:
                                            seeded_roll_price = seeded_menu.get("price", 0.60)
                                    except:
                                        pass  # Use defaults
                                    
                                    # Calculate sponsored breakfast cost
                                    sponsored_breakfast_cost += (white_halves * white_roll_price) + (seeded_halves * seeded_roll_price)
                                    
                                    # Add boiled eggs cost
                                    if boiled_eggs > 0:
                                        department_prices = await get_department_prices(department_id)
                                        boiled_eggs_price = department_prices["boiled_eggs_price"]
                                        sponsored_breakfast_cost += boiled_eggs * boiled_eggs_price
                                    
                                    # Add fried eggs cost
                                    fried_eggs = item.get("fried_eggs", 0)
                                    if fried_eggs > 0:
                                        department_prices = await get_department_prices(department_id)
                                        fried_eggs_price = department_prices["fried_eggs_price"]
                                        sponsored_breakfast_cost += fried_eggs * fried_eggs_price
                                
                                remaining_cost -= sponsored_breakfast_cost
                            
                            # Subtract lunch cost if sponsored
                            if "lunch" in sponsored_types_list:
                                for item in order.get("breakfast_items", []):
                                    if item.get("has_lunch", False):
                                        # Get daily lunch price
                                        daily_lunch_price_doc = await db.daily_lunch_prices.find_one({
                                            "department_id": department_id,
                                            "date": current_date.isoformat()
                                        })
                                        lunch_price_to_subtract = 0.0
                                        if daily_lunch_price_doc:
                                            lunch_price_to_subtract = daily_lunch_price_doc["lunch_price"]
                                        else:
                                            # KORRIGIERT: Use original order lunch price as fallback
                                            # This ensures sponsored lunch is properly deducted even if daily price missing
                                            order_lunch_price = item.get("lunch_price", 0.0)
                                            if order_lunch_price > 0:
                                                lunch_price_to_subtract = order_lunch_price
                                            else:
                                                # Last fallback: Use global lunch settings
                                                lunch_settings = await db.lunch_settings.find_one()
                                                if lunch_settings:
                                                    lunch_price_to_subtract = lunch_settings.get("price", 0.0)
                                        
                                        print(f"DEBUG LUNCH SPONSORING: Subtracting lunch price: {lunch_price_to_subtract}")
                                        remaining_cost -= lunch_price_to_subtract
                                        break
                            
                            # Employee pays only the remaining cost (e.g., coffee)
                            order_amount = max(0, remaining_cost)
                        else:
                            # No sponsored meal types - shouldn't happen but handle gracefully
                            order_amount = order.get("total_price", 0)
                        # Round to avoid floating point errors
                        order_amount = round(order_amount, 2)
                    elif order.get("is_sponsor_order"):
                        # For sponsor orders, count full total_price 
                        order_amount = order.get("total_price", 0)
                    else:
                        # Regular orders - use full cost INCLUDING COFFEE
                        # CRITICAL: Coffee must be included in employee balance calculations
                        order_amount = order.get("total_price", 0)
                    
                    # Round to avoid floating point errors
                    order_amount = round(order_amount, 2)
                    
                    # ALWAYS add employee to statistics regardless of sponsoring status
                    # This ensures shopping list includes all employees
                    # KORRIGIERT: Use calculated order_amount (which includes sponsoring deductions)
                    employee_orders[employee_key]["total_amount"] += order_amount
                    
                    # DEBUG: Log the calculation for troubleshooting
                    print(f"DEBUG BREAKFAST HISTORY: Employee {employee_key[:20]}... adding {order_amount} (sponsored: {order.get('is_sponsored', False)}, meal_type: {order.get('sponsored_meal_type', 'None')})")
                    
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
                        employee_orders[employee_key]["white_halves"] += white_halves
                        employee_orders[employee_key]["seeded_halves"] += seeded_halves
                        
                        # FIXED: Update overall summary ALWAYS, not just when there are toppings
                        if "weiss" not in breakfast_summary:
                            breakfast_summary["weiss"] = {"halves": 0, "toppings": {}}
                        if "koerner" not in breakfast_summary:
                            breakfast_summary["koerner"] = {"halves": 0, "toppings": {}}
                        
                        breakfast_summary["weiss"]["halves"] += white_halves
                        breakfast_summary["koerner"]["halves"] += seeded_halves
                        
                        # Add boiled eggs if present
                        boiled_eggs = item.get("boiled_eggs", 0)
                        employee_orders[employee_key]["boiled_eggs"] += boiled_eggs
                        
                        # Add fried eggs if present
                        fried_eggs = item.get("fried_eggs", 0)
                        employee_orders[employee_key]["fried_eggs"] += fried_eggs
                        
                        # Add lunch if present
                        if item.get("has_lunch", False):
                            employee_orders[employee_key]["has_lunch"] = True
                            
                            # NEU: Add lunch name from daily lunch price
                            if not employee_orders[employee_key].get("lunch_name"):
                                daily_lunch = await db.daily_lunch_prices.find_one({
                                    "department_id": department_id,
                                    "date": current_date.isoformat()
                                })
                                if daily_lunch and daily_lunch.get("lunch_name"):
                                    employee_orders[employee_key]["lunch_name"] = daily_lunch["lunch_name"]
                                else:
                                    employee_orders[employee_key]["lunch_name"] = "Mittagessen"
                        
                        # Add coffee if present
                        if item.get("has_coffee", False):
                            employee_orders[employee_key]["has_coffee"] = True
                    
                    # Add notes from order level (combine multiple notes if needed, avoiding duplicates)
                    order_notes = order.get("notes", "")
                    if order_notes and order_notes.strip():
                        existing_notes = employee_orders[employee_key]["notes"]
                        if existing_notes:
                            # Split existing notes and new notes by semicolon, combine and deduplicate
                            existing_parts = [note.strip() for note in existing_notes.split(";") if note.strip()]
                            new_parts = [note.strip() for note in order_notes.split(";") if note.strip()]
                            all_parts = existing_parts + new_parts
                            # Remove duplicates while preserving order
                            unique_parts = list(dict.fromkeys(all_parts))
                            employee_orders[employee_key]["notes"] = "; ".join(unique_parts)
                        else:
                            # Clean up potential duplicates in the initial notes too
                            parts = [note.strip() for note in order_notes.split(";") if note.strip()]
                            unique_parts = list(dict.fromkeys(parts))
                            employee_orders[employee_key]["notes"] = "; ".join(unique_parts)
                        
                        # Count toppings with proper roll type assignment
                        for topping_index, topping in enumerate(item["toppings"]):
                            # Determine which roll type this topping belongs to based on position
                            if topping_index < white_halves:
                                # This topping is on a white roll
                                if topping not in employee_orders[employee_key]["toppings"]:
                                    employee_orders[employee_key]["toppings"][topping] = {"white": 0, "seeded": 0}
                                elif isinstance(employee_orders[employee_key]["toppings"][topping], int):
                                    # Convert old format to new format
                                    old_count = employee_orders[employee_key]["toppings"][topping]
                                    employee_orders[employee_key]["toppings"][topping] = {"white": old_count, "seeded": 0}
                                employee_orders[employee_key]["toppings"][topping]["white"] += 1
                                
                                # Also update breakfast_summary for overall topping counts
                                if topping not in breakfast_summary["weiss"]["toppings"]:
                                    breakfast_summary["weiss"]["toppings"][topping] = 0
                                breakfast_summary["weiss"]["toppings"][topping] += 1
                            else:
                                # This topping is on a seeded roll
                                if topping not in employee_orders[employee_key]["toppings"]:
                                    employee_orders[employee_key]["toppings"][topping] = {"white": 0, "seeded": 0}
                                elif isinstance(employee_orders[employee_key]["toppings"][topping], int):
                                    # Convert old format to new format
                                    old_count = employee_orders[employee_key]["toppings"][topping]
                                    employee_orders[employee_key]["toppings"][topping] = {"white": 0, "seeded": old_count}
                                employee_orders[employee_key]["toppings"][topping]["seeded"] += 1
                                
                                # Also update breakfast_summary for overall topping counts
                                if topping not in breakfast_summary["koerner"]["toppings"]:
                                    breakfast_summary["koerner"]["toppings"][topping] = 0
                                breakfast_summary["koerner"]["toppings"][topping] += 1
            
            # Calculate shopping list
            shopping_list = {}
            for roll_type, data in breakfast_summary.items():
                whole_rolls = (data["halves"] + 1) // 2
                shopping_list[roll_type] = {"halves": data["halves"], "whole_rolls": whole_rolls}
            
            # Daily lunch price already loaded above
            
            # Add sponsoring information for each employee
            for employee_name, employee_data in employee_orders.items():
                # Initialize sponsoring info
                employee_data["sponsored_breakfast"] = None
                employee_data["sponsored_lunch"] = None
                # Initialize sponsored status if not already set
                if "is_sponsored" not in employee_data:
                    employee_data["is_sponsored"] = False
                if "sponsored_meal_type" not in employee_data:
                    employee_data["sponsored_meal_type"] = None
            
            # CRITICAL: Also find sponsors who didn't make their own orders but sponsored others
            all_sponsors = await db.orders.find({
                "department_id": department_id,
                "sponsored_by_employee_id": {"$exists": True},
                "timestamp": {
                    "$gte": start_of_day_utc.isoformat(),
                    "$lte": end_of_day_utc.isoformat()
                }
            }).to_list(1000)
            
            # Get unique sponsor IDs and names, create correct employee_key format
            sponsor_keys_to_add = {}
            existing_employee_keys = set(employee_orders.keys())
            
            for order in all_sponsors:
                sponsor_id = order.get("sponsored_by_employee_id", "")
                sponsor_name = order.get("sponsored_by_name", "")
                if sponsor_id and sponsor_name:
                    # Create the same key format as used for regular orders
                    sponsor_key = f"{sponsor_name} (ID: {sponsor_id[-8:]})"
                    if sponsor_key not in existing_employee_keys:
                        # This sponsor has no own orders, add them
                        sponsor_keys_to_add[sponsor_key] = {
                            "sponsor_id": sponsor_id,
                            "sponsor_name": sponsor_name
                        }
            
            # Add sponsors to employee_orders if they're not already there
            for sponsor_key, sponsor_info in sponsor_keys_to_add.items():
                employee_orders[sponsor_key] = {
                    "white_halves": 0,
                    "seeded_halves": 0,
                    "boiled_eggs": 0,
                    "has_coffee": False,
                    "has_lunch": False,
                    "total_amount": 0.0,
                    "toppings": {},
                    "sponsored_breakfast": None,
                    "sponsored_lunch": None,
                    "is_sponsored": False,  # Sponsors are not sponsored
                    "sponsored_meal_type": None  # Sponsors don't have sponsored meal types
                }
            
            # Now calculate sponsoring information for ALL employees (including sponsors-only)
            for employee_key in employee_orders.keys():
                # Extract employee name and partial ID from key (format: "Name (ID: 12345678)")
                employee_id = None
                if " (ID: " in employee_key:
                    employee_name = employee_key.split(" (ID: ")[0]
                    partial_employee_id = employee_key.split(" (ID: ")[1].rstrip(")")
                    
                    # CRITICAL FIX: Find the full employee ID from database using partial ID
                    # The employee key contains only last 8 characters, but we need the full UUID
                    employee_doc = await db.employees.find_one({
                        "department_id": department_id,
                        "name": employee_name,
                        "id": {"$regex": f".*{partial_employee_id}$"}  # Match ending with partial ID
                    })
                    
                    if employee_doc:
                        employee_id = employee_doc["id"]  # Use full employee ID
                    else:
                        print(f"⚠️ Could not find full employee ID for {employee_name} with partial ID {partial_employee_id}")
                        continue
                else:
                    employee_name = employee_key  # Fallback for any edge cases
                    continue  # Skip if we can't extract ID
                
                # Check if this employee sponsored any meals today
                breakfast_sponsored_info = None
                lunch_sponsored_info = None
                
                # SIMPLIFIED CORRECT APPROACH: Find sponsor orders for this employee
                # Look for orders where this employee is marked as a sponsor (is_sponsor_order=True)
                sponsor_orders = await db.orders.find({
                    "department_id": department_id,
                    "employee_id": employee_id,  # Orders belonging to this employee (now using full ID)
                    "is_sponsor_order": True,    # This employee sponsored someone
                    "timestamp": {
                        "$gte": start_of_day_utc.isoformat(),
                        "$lte": end_of_day_utc.isoformat()
                    }
                }).to_list(1000)
                
                if sponsor_orders:
                    # Process sponsor orders to extract sponsoring info
                    for sponsor_order in sponsor_orders:
                        sponsor_meal_type = sponsor_order.get("sponsored_meal_type", "")
                        sponsor_count = sponsor_order.get("sponsor_employee_count", 0)
                        sponsor_cost = sponsor_order.get("sponsor_total_cost", 0.0)
                        
                        # CRITICAL FIX: Each sponsor order should be processed separately
                        # Don't combine meal types from different sponsor orders
                        if sponsor_meal_type.lower() == "breakfast":
                            if breakfast_sponsored_info is None:  # Only set if not already set
                                breakfast_sponsored_info = {
                                    "count": sponsor_count,
                                    "amount": round(sponsor_cost, 2)
                                }
                                # Add sponsored breakfast amount to sponsor's total_amount
                                employee_orders[employee_key]["total_amount"] += sponsor_cost
                        elif sponsor_meal_type.lower() == "lunch":
                            if lunch_sponsored_info is None:  # Only set if not already set
                                lunch_sponsored_info = {
                                    "count": sponsor_count,
                                    "amount": round(sponsor_cost, 2)
                                }
                                # Add sponsored lunch amount to sponsor's total_amount
                                employee_orders[employee_key]["total_amount"] += sponsor_cost
                
                # Add sponsoring info to employee data
                employee_orders[employee_key]["sponsored_breakfast"] = breakfast_sponsored_info
                employee_orders[employee_key]["sponsored_lunch"] = lunch_sponsored_info
                
                # Round total_amount to avoid floating point errors
                employee_orders[employee_key]["total_amount"] = round(employee_orders[employee_key]["total_amount"], 2)
            
            # CORRECTED: Calculate daily total as ACTUAL REVENUE only (exclude sponsor cost redistribution)
            # Daily total should represent actual food cost, not cost redistribution between employees
            daily_total = Decimal('0')
            
            for order in real_orders:  # Only count real orders
                # Always use the original order total_price for daily revenue calculation
                # This represents actual food costs, regardless of who pays
                daily_total += Decimal(str(order.get("total_price", 0)))
            
            # Convert back to float and round to 2 decimal places
            total_amount = float(daily_total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
            
            history.append({
                "date": current_date.isoformat(),
                "total_orders": total_orders,
                "total_amount": total_amount,
                "breakfast_summary": breakfast_summary,
                "employee_orders": employee_orders,
                "shopping_list": shopping_list,
                "daily_lunch_price": daily_lunch_price,  # Add daily lunch price
                "lunch_name": lunch_name  # NEU: Add lunch name
            })
        # KORRIGIERT: Don't add empty days - only show days with actual orders (original behavior restored)
        
        current_date += timedelta(days=1)
    
    # Return history in reverse chronological order (newest first)
    return {"history": list(reversed(history))}


@api_router.get("/orders/daily-summary/{department_id}")
async def get_daily_summary(department_id: str):
    """Get daily summary of all orders for a department"""
    # Use Berlin timezone for current day calculation
    today = get_berlin_date()
    start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(today)
    
    # Get today's orders (Berlin time) - exclude cancelled orders
    orders = await db.orders.find({
        "department_id": department_id,
        "timestamp": {
            "$gte": start_of_day_utc.isoformat(),
            "$lte": end_of_day_utc.isoformat()
        },
        "$or": [
            {"is_cancelled": {"$exists": False}},  # Legacy orders without is_cancelled field
            {"is_cancelled": False}                # Explicitly not cancelled
        ]
    }).to_list(1000)
    
    # Filter out sponsor orders from statistics (they're not real food orders)
    real_orders = [order for order in orders if not order.get("is_sponsor_order", False)]
    
    # Aggregate breakfast orders with employee details
    breakfast_summary = {}
    employee_orders = {}  # Track individual employee orders
    drinks_summary = {}
    sweets_summary = {}
    
    for order in real_orders:  # Only process real orders for employee statistics
        if order["order_type"] == "breakfast" and order.get("breakfast_items"):
            # Get employee info
            employee = await db.employees.find_one({"id": order["employee_id"]})
            employee_name = employee["name"] if employee else "Unknown"
            
            if employee_name not in employee_orders:
                employee_orders[employee_name] = {
                    "white_halves": 0, 
                    "seeded_halves": 0, 
                    "boiled_eggs": 0,  # Add boiled eggs tracking
                    "fried_eggs": 0,  # Add fried eggs tracking
                    "has_lunch": False,  # Add lunch tracking
                    "has_coffee": False,  # Add coffee tracking
                    "notes": "",  # Initialize empty - will be populated during processing
                    "toppings": {}
                }
            
            # Check if this order is sponsored and how to handle it
            is_sponsored = order.get("is_sponsored", False)
            is_sponsor_order = order.get("is_sponsor_order", False)
            sponsored_meal_type = order.get("sponsored_meal_type", "")
            
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
                
                # FIXED: Always show original orders for shopping/einkauf purposes
                # The breakfast overview is for purchasing decisions - must always show what was originally ordered
                # Sponsoring affects payments/balances, NOT the shopping list
                show_breakfast = True
                show_lunch = item.get("has_lunch", False)
                show_coffee = item.get("has_coffee", False)
                
                # NOTE: Sponsoring status does NOT affect what is shown in breakfast overview
                # The overview shows ORIGINAL orders for shopping purposes
                # Balances and payments are handled separately
                
                # Update employee totals - ALWAYS show original orders for shopping purposes
                if show_breakfast:
                    employee_orders[employee_name]["white_halves"] += white_halves
                    employee_orders[employee_name]["seeded_halves"] += seeded_halves
                    
                    # Add boiled eggs if present and breakfast is visible
                    boiled_eggs = item.get("boiled_eggs", 0)
                    employee_orders[employee_name]["boiled_eggs"] += boiled_eggs
                    
                    # Add fried eggs if present and breakfast is visible
                    fried_eggs = item.get("fried_eggs", 0)
                    employee_orders[employee_name]["fried_eggs"] += fried_eggs
                
                # Add lunch if present and visible
                if show_lunch:
                    employee_orders[employee_name]["has_lunch"] = True
                
                # Coffee is always visible
                if show_coffee:
                    employee_orders[employee_name]["has_coffee"] = True
                
                # Add notes from order level (combine multiple notes if needed)
                order_notes = order.get("notes", "")
                if order_notes and order_notes.strip():
                    existing_notes = employee_orders[employee_name]["notes"]
                    if existing_notes:
                        # Split existing notes and new notes by semicolon, combine and deduplicate
                        existing_parts = [note.strip() for note in existing_notes.split(";") if note.strip()]
                        new_parts = [note.strip() for note in order_notes.split(";") if note.strip()]
                        all_parts = existing_parts + new_parts
                        # Remove duplicates while preserving order
                        unique_parts = list(dict.fromkeys(all_parts))
                        employee_orders[employee_name]["notes"] = "; ".join(unique_parts)
                    else:
                        # Clean up potential duplicates in the initial notes too
                        parts = [note.strip() for note in order_notes.split(";") if note.strip()]
                        unique_parts = list(dict.fromkeys(parts))
                        employee_orders[employee_name]["notes"] = "; ".join(unique_parts)
                
                # Update overall summary only for visible items
                if show_breakfast:
                    if "weiss" not in breakfast_summary:
                        breakfast_summary["weiss"] = {"halves": 0, "toppings": {}}
                    if "koerner" not in breakfast_summary:
                        breakfast_summary["koerner"] = {"halves": 0, "toppings": {}}
                    
                    breakfast_summary["weiss"]["halves"] += white_halves
                    breakfast_summary["koerner"]["halves"] += seeded_halves
                
                # Count toppings per employee with proper roll type assignment
                if show_breakfast:
                    for topping_index, topping in enumerate(item["toppings"]):
                        # Employee toppings - use new format {white: X, seeded: Y} for frontend compatibility
                        if topping not in employee_orders[employee_name]["toppings"]:
                            employee_orders[employee_name]["toppings"][topping] = {"white": 0, "seeded": 0}
                        elif isinstance(employee_orders[employee_name]["toppings"][topping], int):
                            # Convert old format to new format
                            old_count = employee_orders[employee_name]["toppings"][topping]
                            employee_orders[employee_name]["toppings"][topping] = {"white": old_count, "seeded": 0}
                        
                        # Determine which roll type this topping belongs to based on position
                        if topping_index < white_halves:
                            # This topping is on a white roll
                            employee_orders[employee_name]["toppings"][topping]["white"] += 1
                            
                            # Also update breakfast_summary for overall topping counts
                            if topping not in breakfast_summary["weiss"]["toppings"]:
                                breakfast_summary["weiss"]["toppings"][topping] = 0
                            breakfast_summary["weiss"]["toppings"][topping] += 1
                        else:
                            # This topping is on a seeded roll
                            employee_orders[employee_name]["toppings"][topping]["seeded"] += 1
                            
                            # Also update breakfast_summary for overall topping counts
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
    
    # Calculate total fried eggs
    total_fried_eggs = sum(data["fried_eggs"] for data in employee_orders.values())
    
    # Collect notes summary for frontend display
    notes_summary = {}
    for employee_name, data in employee_orders.items():
        if data.get("notes") and data["notes"].strip():
            notes_summary[employee_name] = data["notes"]
    
    return {
        "date": today.isoformat(),
        "breakfast_summary": breakfast_summary,
        "employee_orders": employee_orders,
        "drinks_summary": drinks_summary,
        "sweets_summary": sweets_summary,
        "shopping_list": shopping_list,
        "total_toppings": total_toppings,
        "total_boiled_eggs": total_boiled_eggs,  # Add total boiled eggs
        "total_fried_eggs": total_fried_eggs,  # Add total fried eggs
        "notes_summary": notes_summary  # Add notes summary for frontend
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

@api_router.get("/employee/{employee_id}/orders/{order_id}/cancellable")
async def check_order_cancellable(employee_id: str, order_id: str):
    """Check if an order can be cancelled by the employee"""
    # Check if order belongs to employee
    order = await db.orders.find_one({"id": order_id, "employee_id": employee_id})
    if not order:
        raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
    
    # Check if already cancelled
    if order.get("is_cancelled"):
        return {"cancellable": False, "reason": "Bestellung bereits storniert"}
    
    # Check payment protection
    try:
        await check_order_payment_protection(employee_id, order)
    except HTTPException as e:
        return {"cancellable": False, "reason": e.detail}
    
    # Check time restriction (same day in Berlin timezone)
    order_timestamp = datetime.fromisoformat(order["timestamp"].replace('Z', '+00:00'))
    order_date_berlin = order_timestamp.astimezone(BERLIN_TZ).date()
    today_berlin = get_berlin_date()
    
    if order_date_berlin != today_berlin:
        return {
            "cancellable": False, 
            "reason": f"Bestellungen können nur am gleichen Tag bis 23:59 Uhr storniert werden. Diese Bestellung ist vom {order_date_berlin.strftime('%d.%m.%Y')}."
        }
    
    # Check if breakfast is closed (for breakfast orders)
    if order["order_type"] == "breakfast":
        today = datetime.now(timezone.utc).date().isoformat()
        breakfast_status = await db.breakfast_settings.find_one({
            "department_id": order["department_id"],
            "date": today
        })
        
        if breakfast_status and breakfast_status["is_closed"]:
            return {
                "cancellable": False, 
                "reason": "Frühstück ist geschlossen. Nur Admins können noch Änderungen vornehmen."
            }
    
    return {"cancellable": True, "reason": ""}

@api_router.delete("/employee/{employee_id}/orders/{order_id}")
async def delete_employee_order(employee_id: str, order_id: str):
    """Allow employee to cancel their own order (with payment protection)"""
    # Check if order belongs to employee
    order = await db.orders.find_one({"id": order_id, "employee_id": employee_id})
    if not order:
        raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
    
    # Check if already cancelled
    if order.get("is_cancelled"):
        raise HTTPException(status_code=400, detail="Bestellung bereits storniert")
    
    # NEW: Check if order is protected by payment timestamp
    await check_order_payment_protection(employee_id, order)
    
    # NEW: Check if employee can still cancel (only same day in Berlin timezone)
    order_timestamp = datetime.fromisoformat(order["timestamp"].replace('Z', '+00:00'))
    order_date_berlin = order_timestamp.astimezone(BERLIN_TZ).date()
    today_berlin = get_berlin_date()
    
    if order_date_berlin != today_berlin:
        raise HTTPException(
            status_code=403, 
            detail=f"Sie können diese Bestellung nicht mehr stornieren. Bestellungen können nur am gleichen Tag bis 23:59 Uhr storniert werden. Diese Bestellung ist vom {order_date_berlin.strftime('%d.%m.%Y')}."
        )
    
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
    
    # Get employee name for audit trail
    employee = await db.employees.find_one({"id": employee_id})
    employee_name = employee["name"] if employee else "Unbekannt"
    
    # CORRECTED: Adjust employee balance (add back the order amount) + ERWEITERT für Subkonten
    if employee:
        # KORRIGIERT: Unterscheide zwischen Stammbestellung und Gastbestellung bei Stornierung
        is_home_department = (order["department_id"] == employee.get("department_id"))
        
        if order["order_type"] == "breakfast":
            if is_home_department:
                # STAMMBESTELLUNG-STORNIERUNG: Restore NUR main balance
                new_breakfast_balance = employee["breakfast_balance"] + order["total_price"]
                await db.employees.update_one(
                    {"id": employee_id},
                    {"$set": {"breakfast_balance": new_breakfast_balance}}
                )
            else:
                # GASTBESTELLUNG-STORNIERUNG: Restore NUR subaccount balance
                await update_employee_balance(employee_id, order["department_id"], 'breakfast', order["total_price"])
            
        else:  # DRINKS or SWEETS
            if is_home_department:
                # STAMMBESTELLUNG-STORNIERUNG: Restore NUR main balance  
                new_drinks_sweets_balance = employee["drinks_sweets_balance"] - order["total_price"]
                await db.employees.update_one(
                    {"id": employee_id},
                    {"$set": {"drinks_sweets_balance": new_drinks_sweets_balance}}
                )
            else:
                # GASTBESTELLUNG-STORNIERUNG: Restore NUR subaccount balance
                await update_employee_balance(employee_id, order["department_id"], 'drinks', -order["total_price"])
    
    # Mark order as cancelled instead of deleting
    cancellation_data = {
        "is_cancelled": True,
        "cancelled_at": datetime.now(timezone.utc).isoformat(),
        "cancelled_by": "employee", 
        "cancelled_by_name": employee_name
    }
    
    await db.orders.update_one(
        {"id": order_id},
        {"$set": cancellation_data}
    )
    
    return {"message": "Bestellung erfolgreich storniert"}

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
    
    # KORRIGIERT: Menu items should be loaded per order department, not employee's home department
    employee_department_id = employee.get("department_id")
    
    # Get all departments for menu loading
    all_departments = await db.departments.find({}).to_list(100)
    department_menus = {}
    
    # Pre-load menus for all departments to handle cross-department orders
    for dept in all_departments:
        dept_id = dept["id"]
        breakfast_menu = await db.menu_breakfast.find({"department_id": dept_id}).to_list(100)
        toppings_menu = await db.menu_toppings.find({"department_id": dept_id}).to_list(100)
        drinks_menu = await db.menu_drinks.find({"department_id": dept_id}).to_list(100)
        sweets_menu = await db.menu_sweets.find({"department_id": dept_id}).to_list(100)
        
        department_menus[dept_id] = {
            "breakfast_prices": {item["roll_type"]: item["price"] for item in breakfast_menu},
            "topping_prices": {item["topping_type"]: item["price"] for item in toppings_menu},
            "drink_names": {item["id"]: {"name": item["name"], "price": item["price"]} for item in drinks_menu},
            "sweet_names": {item["id"]: {"name": item["name"], "price": item["price"]} for item in sweets_menu}
        }
    
    # Fallback menus (use employee's home department as default)
    default_dept_menu = department_menus.get(employee_department_id, {})
    breakfast_prices = default_dept_menu.get("breakfast_prices", {})
    topping_prices = default_dept_menu.get("topping_prices", {})
    drink_names = default_dept_menu.get("drink_names", {})
    sweet_names = default_dept_menu.get("sweet_names", {})
    
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
                    roll_name = {"weiss": "Helles Brötchen", "koerner": "Körnerbrötchen"}.get(item["roll_type"], item["roll_type"])
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
                
                # Create separate topping strings for white and seeded rolls based on position
                toppings_list = item["toppings"]
                white_toppings = []
                seeded_toppings = []
                
                for topping_index, topping in enumerate(toppings_list):
                    topping_display = topping_names_german.get(topping, topping)
                    if topping_index < white_halves:
                        # This topping is on a white roll
                        white_toppings.append(topping_display)
                    else:
                        # This topping is on a seeded roll
                        seeded_toppings.append(topping_display)
                
                white_toppings_str = ", ".join(white_toppings) if white_toppings else "Ohne Belag"
                seeded_toppings_str = ", ".join(seeded_toppings) if seeded_toppings else "Ohne Belag"
                
                # KORRIGIERT: Use order department's menu prices, not employee's home department
                order_department_id = order.get("department_id", employee_department_id)
                order_dept_menu = department_menus.get(order_department_id, default_dept_menu)
                
                # Get department-specific prices for this order
                order_breakfast_prices = order_dept_menu.get("breakfast_prices", breakfast_prices)
                department_prices = await get_department_prices(order_department_id)
                boiled_eggs_price = department_prices["boiled_eggs_price"]
                fried_eggs_price = department_prices["fried_eggs_price"]
                coffee_price = department_prices["coffee_price"]
                
                enriched_order["readable_items"] = []
                
                # Add rolls as separate items if present
                white_halves = item.get("white_halves", 0)
                seeded_halves = item.get("seeded_halves", 0)
                
                if white_halves > 0:
                    white_roll_price = order_breakfast_prices.get("weiss", 0.50)  # Use ORDER department's price
                    enriched_order["readable_items"].append({
                        "description": f"{white_halves}x Helles Brötchen (Hälften)",
                        "unit_price": f"{white_roll_price:.2f} € pro Hälfte",
                        "total_price": f"{(white_halves * white_roll_price):.2f} €",
                        "toppings": white_toppings_str
                    })
                
                if seeded_halves > 0:
                    seeded_roll_price = order_breakfast_prices.get("koerner", 0.60)  # Use ORDER department's price
                    enriched_order["readable_items"].append({
                        "description": f"{seeded_halves}x Körnerbrötchen (Hälften)", 
                        "unit_price": f"{seeded_roll_price:.2f} € pro Hälfte",
                        "total_price": f"{(seeded_halves * seeded_roll_price):.2f} €",
                        "toppings": seeded_toppings_str
                    })
                
                # Add boiled eggs as separate item if present
                boiled_eggs = item.get("boiled_eggs", 0)
                if boiled_eggs > 0:
                    enriched_order["readable_items"].append({
                        "description": f"{boiled_eggs}x Gekochte Eier",
                        "unit_price": f"{boiled_eggs_price:.2f} € pro Stück",
                        "total_price": f"{(boiled_eggs * boiled_eggs_price):.2f} €"
                    })
                
                # Add fried eggs as separate item if present
                fried_eggs = item.get("fried_eggs", 0)
                if fried_eggs > 0:
                    enriched_order["readable_items"].append({
                        "description": f"{fried_eggs}x Spiegeleier",
                        "unit_price": f"{fried_eggs_price:.2f} € pro Stück",
                        "total_price": f"{(fried_eggs * fried_eggs_price):.2f} €"
                    })
                
                # Add coffee as separate item if present
                if item.get("has_coffee"):
                    enriched_order["readable_items"].append({
                        "description": "1x Kaffee",
                        "unit_price": f"{coffee_price:.2f} € pro Tag",
                        "total_price": f"{coffee_price:.2f} €"
                    })
                
                # Add lunch as separate item if present
                if item.get("has_lunch"):
                    lunch_price = order.get("lunch_price", 0.0)  # Get actual lunch price from order level
                    
                    # NEU: Get lunch name from daily lunch price
                    lunch_name = "Mittagessen"  # Default
                    order_department_id = order.get("department_id", employee_department_id)
                    order_date = order.get("timestamp", "")[:10]  # Extract YYYY-MM-DD
                    
                    if order_date:
                        daily_lunch = await db.daily_lunch_prices.find_one({
                            "department_id": order_department_id,
                            "date": order_date
                        })
                        if daily_lunch and daily_lunch.get("lunch_name"):
                            lunch_name = daily_lunch["lunch_name"]
                    
                    enriched_order["readable_items"].append({
                        "description": f"1x {lunch_name}",
                        "unit_price": "",  # Remove price display as requested by user
                        "total_price": f"{lunch_price:.2f} €"
                    })
        
        elif order["order_type"] in ["drinks", "sweets"]:
            enriched_order["readable_items"] = []
            items_dict = order.get("drink_items", {}) if order["order_type"] == "drinks" else order.get("sweet_items", {})
            
            # KORRIGIERT: Lade Department-spezifisches Menü für jede Bestellung
            order_department_id = order.get("department_id", employee_department_id)
            if order["order_type"] == "drinks":
                # Lade Getränkemenü für das spezifische Department
                order_drinks_menu = await db.menu_drinks.find({"department_id": order_department_id}).to_list(100)
                names_dict = {item["id"]: {"name": item["name"], "price": item["price"]} for item in order_drinks_menu}
            else:  # sweets
                # Lade Süßigkeitenmenü für das spezifische Department
                order_sweets_menu = await db.menu_sweets.find({"department_id": order_department_id}).to_list(100)
                names_dict = {item["id"]: {"name": item["name"], "price": item["price"]} for item in order_sweets_menu}
            
            for item_id, quantity in items_dict.items():
                if item_id in names_dict and quantity > 0:
                    enriched_order["readable_items"].append({
                        "description": f"{quantity}x {names_dict[item_id]['name']}",
                        "unit_price": f"{names_dict[item_id]['price']:.2f} €"
                    })
                else:
                    # FALLBACK: Wenn Item nicht im Menü gefunden wird, zeige trotzdem Details
                    enriched_order["readable_items"].append({
                        "description": f"{quantity}x Unbekanntes Item (ID: {item_id})",
                        "unit_price": "N/A"
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

@api_router.get("/sponsoring-status/{department_id}")
async def get_sponsoring_status(department_id: str):
    """Check if ordering is blocked due to sponsoring for today"""
    # Use Berlin timezone for current day
    today = get_berlin_date().isoformat()
    
    setting = await db.sponsoring_settings.find_one({
        "department_id": department_id,
        "date": today
    })
    
    if setting:
        return {
            "is_blocked": setting["is_blocked"],
            "blocked_by": setting.get("blocked_by", ""),
            "blocked_at": setting.get("blocked_at", ""),
            "blocked_reason": setting.get("blocked_reason", ""),
            "date": today
        }
    
    return {"is_blocked": False, "date": today}

@api_router.post("/department-admin/unblock-ordering/{department_id}")
async def unblock_ordering_after_sponsoring(department_id: str, admin_name: str):
    """Unblock ordering after sponsoring (Admin only)"""
    # Use Berlin timezone for current day
    today = get_berlin_date().isoformat()
    
    # Remove or update the sponsoring block
    await db.sponsoring_settings.update_one(
        {"department_id": department_id, "date": today},
        {"$set": {
            "is_blocked": False,
            "blocked_by": "",
            "blocked_at": None,
            "blocked_reason": "",
            "unblocked_by": admin_name,
            "unblocked_at": datetime.now(timezone.utc).isoformat()
        }},
        upsert=True
    )
    
    return {"message": "Bestellungen nach Sponsoring wieder freigegeben", "unblocked_by": admin_name}

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

@api_router.post("/department-admin/flexible-payment/{employee_id}")
async def flexible_payment(employee_id: str, payment_data: FlexiblePaymentRequest, admin_department: str):
    """Department Admin: Process flexible payment with any amount"""
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
    
    # Validate payment_type
    if payment_data.payment_type not in ["breakfast", "drinks_sweets"]:
        raise HTTPException(status_code=400, detail="Invalid payment_type. Use 'breakfast' or 'drinks_sweets'")
    
    # Get current balance
    if payment_data.payment_type == "breakfast":
        current_balance = employee.get("breakfast_balance", 0.0)
        balance_field = "breakfast_balance"
    else:
        current_balance = employee.get("drinks_sweets_balance", 0.0) 
        balance_field = "drinks_sweets_balance"
    
    # Calculate new balance - CORRECTED LOGIC
    # Negative balance = debt (owes money), Positive balance = credit (has money)
    # Payment INCREASES balance (reduces debt or adds credit)
    new_balance = current_balance + payment_data.amount
    
    # Get readable department name
    department_doc = await db.departments.find_one({"id": admin_department})
    department_name = department_doc["name"] if department_doc else admin_department
    
    # Create payment log with balance tracking
    payment_log = PaymentLog(
        employee_id=employee_id,
        department_id=employee["department_id"],
        amount=payment_data.amount,
        payment_type=payment_data.payment_type,
        action="payment",
        admin_user=department_name,  # KORRIGIERT: Benutzerfreundlicher Name statt ID
        notes=payment_data.notes or f"{'Auszahlung' if payment_data.amount < 0 else 'Einzahlung'}: {abs(payment_data.amount):.2f} €",
        balance_before=current_balance,
        balance_after=new_balance
    )
    
    # Save payment log
    payment_dict = prepare_for_mongo(payment_log.dict())
    await db.payment_logs.insert_one(payment_dict)
    
    # Update employee balance
    await db.employees.update_one(
        {"id": employee_id},
        {"$set": {balance_field: new_balance}}
    )
    
    # Determine result type
    if new_balance < 0:
        result_description = f"Restschuld: {abs(new_balance):.2f} €"
    elif new_balance > 0:
        result_description = f"Guthaben: {new_balance:.2f} €"
    else:
        result_description = "Konto ausgeglichen"
    
    return {
        "message": "Einzahlung erfolgreich verbucht",
        "payment_amount": payment_data.amount,
        "balance_before": current_balance,
        "balance_after": new_balance,
        "result_description": result_description
    }

# LEGACY: Keep old endpoint for backward compatibility (mark as deprecated)
@api_router.post("/department-admin/payment/{employee_id}")
async def mark_payment(employee_id: str, payment_type: str, amount: float, admin_department: str):
    """DEPRECATED: Department Admin: Mark debt as paid and log the payment
    
    This endpoint is deprecated. Use /department-admin/flexible-payment/{employee_id} instead.
    """
    employee = await db.employees.find_one({"id": employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Mitarbeiter nicht gefunden")
    
    # Get readable department name
    department_doc = await db.departments.find_one({"id": admin_department})
    department_name = department_doc["name"] if department_doc else admin_department
    
    # Create payment log
    payment_log = PaymentLog(
        employee_id=employee_id,
        department_id=employee["department_id"],
        amount=amount,
        payment_type=payment_type,
        action="payment",
        admin_user=department_name,  # KORRIGIERT: Benutzerfreundlicher Name statt ID
        notes=f"Schulden als bezahlt markiert: {amount:.2f} € (LEGACY)",
        balance_before=employee.get(f"{payment_type}_balance", 0.0),
        balance_after=0.0
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
async def get_admin_breakfast_history(department_id: str, days: int = 7):
    """Get breakfast history for past days"""
    histories = []
    
    for i in range(1, days + 1):  # Start from yesterday
        target_date = datetime.now(timezone.utc).date() - timedelta(days=i)
        start_of_day = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_of_day = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # Get orders for that day - exclude cancelled orders
        orders = await db.orders.find({
            "department_id": department_id,
            "order_type": "breakfast",
            "timestamp": {
                "$gte": start_of_day.isoformat(),
                "$lte": end_of_day.isoformat()
            },
            "$or": [
                {"is_cancelled": {"$exists": False}},  # Legacy orders without is_cancelled field
                {"is_cancelled": False}                # Explicitly not cancelled
            ]
        }).to_list(1000)
        
        if orders:  # Only include days with orders
            # Process the same way as daily summary
            breakfast_summary = {}
            employee_orders = {}
            
            # Filter out sponsor orders from statistics (they're not real food orders)
            real_orders = [order for order in orders if not order.get("is_sponsor_order", False)]
            
            for order in real_orders:  # Only process real orders for employee statistics
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
async def delete_order_by_admin(order_id: str, admin_user: str = "Admin"):
    """Department Admin: Cancel an employee order"""
    try:
        # Find the order first to get employee info and price
        order = await db.orders.find_one({"id": order_id})
        if not order:
            raise HTTPException(status_code=404, detail="Bestellung nicht gefunden")
        
        # Check if already cancelled
        if order.get("is_cancelled"):
            raise HTTPException(status_code=400, detail="Bestellung bereits storniert")
        
        # Get employee name for audit trail
        employee = await db.employees.find_one({"id": order["employee_id"]})
        employee_name = employee["name"] if employee else "Unbekannt"
        
        # CORRECTED: Adjust employee balance before cancelling the order (refund) + ERWEITERT für Subkonten
        if employee:
            # KORRIGIERT: Unterscheide zwischen Stammbestellung und Gastbestellung bei Admin-Stornierung
            is_home_department = (order["department_id"] == employee.get("department_id"))
            
            if order["order_type"] == "breakfast":
                if is_home_department:
                    # STAMMBESTELLUNG-STORNIERUNG: Admin refund main balance
                    new_breakfast_balance = employee["breakfast_balance"] + order["total_price"]
                    await db.employees.update_one(
                        {"id": order["employee_id"]},
                        {"$set": {"breakfast_balance": new_breakfast_balance}}
                    )
                # IMMER: Admin refund subaccount balance (für Stamm- und Gastbestellungen)
                await update_employee_balance(order["employee_id"], order["department_id"], 'breakfast', order["total_price"])
                
            else:
                if is_home_department:
                    # STAMMBESTELLUNG-STORNIERUNG: Admin refund main balance
                    new_drinks_sweets_balance = employee["drinks_sweets_balance"] - order["total_price"]
                    await db.employees.update_one(
                        {"id": order["employee_id"]},
                        {"$set": {"drinks_sweets_balance": new_drinks_sweets_balance}}
                    )
                # IMMER: Admin refund subaccount balance (für Stamm- und Gastbestellungen)
                await update_employee_balance(order["employee_id"], order["department_id"], 'drinks', -order["total_price"])
        
        # Mark order as cancelled instead of deleting
        cancellation_data = {
            "is_cancelled": True,
            "cancelled_at": datetime.now(timezone.utc).isoformat(),
            "cancelled_by": "admin",
            "cancelled_by_name": "Admin"  # Single Admin text as requested
        }
        
        await db.orders.update_one(
            {"id": order_id},
            {"$set": cancellation_data}
        )
        
        return {"message": "Bestellung erfolgreich storniert"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelling order: {str(e)}")

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
                    department_prices = await get_department_prices(existing_order["department_id"])
                    boiled_eggs_price = department_prices["boiled_eggs_price"]
                    total_price += boiled_eggs * boiled_eggs_price
                
                # Add fried eggs price if applicable
                fried_eggs = item.get("fried_eggs", 0)
                if fried_eggs > 0:
                    department_prices = await get_department_prices(existing_order["department_id"])
                    fried_eggs_price = department_prices["fried_eggs_price"]
                    total_price += fried_eggs * fried_eggs_price
                
                # Add coffee price if applicable
                if item.get("has_coffee", False):
                    department_prices = await get_department_prices(existing_order["department_id"])
                    coffee_price = department_prices["coffee_price"]
                    total_price += coffee_price
                
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
                        # NEW: Default to 0.0 for new days - admin must set price manually each day
                        lunch_price = 0.0
                    
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
        
        if "notes" in order_update:
            update_fields["notes"] = order_update["notes"]
        
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
            
            # Update employee balance - CORRECTED LOGIC
            # Price increase = more debt (balance decreases)
            # Price decrease = less debt (balance increases)
            new_breakfast_balance = employee.get("breakfast_balance", 0.0) - price_difference
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
    """Admin: Delete all breakfast orders for a specific date and adjust employee balances
    
    ⚠️ KRITISCHE WARNUNG: Dieser Endpoint löscht ALLE Bestellungen eines Tages!
    Nur für Notfälle verwenden. Erstellt automatisch ein Backup.
    """
    
    # SICHERHEITSCHECK: Zusätzliche Bestätigung erforderlich
    print(f"🚨 KRITISCHE OPERATION: Lösche alle Frühstücksbestellungen für {date} in {department_id}")
    
    try:
        # Validate date format and use Berlin timezone like other functions
        parsed_date = datetime.fromisoformat(date).date()
        
        # CRITICAL FIX: Use Berlin timezone day bounds like all other functions
        start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(parsed_date)
        
        # Find all breakfast orders for this department and date
        breakfast_orders = await db.orders.find({
            "department_id": department_id,
            "order_type": "breakfast",
            "timestamp": {
                "$gte": start_of_day_utc.isoformat(),
                "$lte": end_of_day_utc.isoformat()
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

@api_router.get("/department-admin/sponsor-status/{department_id}/{date}")
async def get_sponsor_status(department_id: str, date: str):
    """Check if meals have already been sponsored for a specific date"""
    try:
        # Validate date format
        try:
            parsed_date = datetime.fromisoformat(date).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Ungültiges Datumsformat. Verwenden Sie YYYY-MM-DD.")
        
        # Get Berlin timezone day boundaries
        start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(parsed_date)
        
        # Get all breakfast orders for that day
        all_orders = await db.orders.find({
            "department_id": department_id,
            "order_type": "breakfast",
            "timestamp": {"$gte": start_of_day_utc.isoformat(), "$lte": end_of_day_utc.isoformat()},
            "$or": [{"is_cancelled": {"$exists": False}}, {"is_cancelled": False}]
        }).to_list(1000)
        
        # Check sponsoring status for both meal types
        breakfast_sponsored = None
        lunch_sponsored = None
        
        for order in all_orders:
            if order.get("is_sponsored") and order.get("sponsored_meal_type") == "breakfast":
                breakfast_sponsored = {
                    "sponsor_name": order.get("sponsored_by_name", "Unbekannt"),
                    "sponsor_id": order.get("sponsored_by_employee_id", "")
                }
            elif order.get("is_sponsored") and order.get("sponsored_meal_type") == "lunch":
                lunch_sponsored = {
                    "sponsor_name": order.get("sponsored_by_name", "Unbekannt"),
                    "sponsor_id": order.get("sponsored_by_employee_id", "")
                }
        
        return {
            "department_id": department_id,
            "date": date,
            "breakfast_sponsored": breakfast_sponsored,
            "lunch_sponsored": lunch_sponsored
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen des Sponsor-Status: {str(e)}")

async def get_sponsor_status(department_id: str, date: str):
    """Check if meals have already been sponsored for a specific date"""
    try:
        # Parse date and create timezone-aware range
        target_date = datetime.fromisoformat(date).date()
        berlin_tz = pytz.timezone('Europe/Berlin')
        start_of_day_berlin = berlin_tz.localize(datetime.combine(target_date, datetime.min.time()))
        end_of_day_berlin = berlin_tz.localize(datetime.combine(target_date, datetime.max.time()))
        
        # Convert to UTC for database query
        start_of_day_utc = start_of_day_berlin.astimezone(pytz.UTC)
        end_of_day_utc = end_of_day_berlin.astimezone(pytz.UTC)
        
        # Find all orders for this department and date
        all_orders = await db.orders.find({
            "department_id": department_id,
            "order_type": "breakfast",
            "timestamp": {"$gte": start_of_day_utc.isoformat(), "$lte": end_of_day_utc.isoformat()},
            "$or": [{"is_cancelled": {"$exists": False}}, {"is_cancelled": False}]
        }).to_list(1000)
        
        # Check sponsoring status for both meal types
        breakfast_sponsored = None
        lunch_sponsored = None
        
        for order in all_orders:
            if order.get("is_sponsored") and order.get("sponsored_meal_type") == "breakfast":
                if not breakfast_sponsored:  # Take the first one we find
                    breakfast_sponsored = {
                        "sponsored_by": order.get("sponsored_by_name", "Unbekannt"),
                        "sponsored_by_id": order.get("sponsored_by_employee_id")
                    }
            elif order.get("is_sponsored") and order.get("sponsored_meal_type") == "lunch":
                if not lunch_sponsored:  # Take the first one we find
                    lunch_sponsored = {
                        "sponsored_by": order.get("sponsored_by_name", "Unbekannt"),
                        "sponsored_by_id": order.get("sponsored_by_employee_id")
                    }
        
        return {
            "department_id": department_id,
            "date": date,
            "breakfast_sponsored": breakfast_sponsored,
            "lunch_sponsored": lunch_sponsored
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Ungültiges Datumsformat: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Prüfen des Sponsor-Status: {str(e)}")

@api_router.post("/department-admin/sponsor-meal")
async def sponsor_meal(meal_data: dict):
    """
    NEUE SAUBERE SPONSORING LOGIK
    
    Klare Trennung der Schritte:
    1. Validierung und Datensammlung
    2. Berechnung der Individual-Kosten
    3. Sponsor-Balance Berechnung  
    4. Refund-Berechnung für gesponserte Mitarbeiter
    5. Atomische Updates
    """
    try:
        # === PHASE 1: VALIDIERUNG ===
        department_id = meal_data.get("department_id")
        date_str = meal_data.get("date")
        meal_type = meal_data.get("meal_type")  # "breakfast" or "lunch"
        sponsor_employee_id = meal_data.get("sponsor_employee_id")
        sponsor_employee_name = meal_data.get("sponsor_employee_name")
        
        if not all([department_id, date_str, meal_type, sponsor_employee_id, sponsor_employee_name]):
            raise HTTPException(status_code=400, detail="Alle Felder sind erforderlich")
        
        if meal_type not in ["breakfast", "lunch"]:
            raise HTTPException(status_code=400, detail="meal_type muss 'breakfast' oder 'lunch' sein")
        
        try:
            parsed_date = datetime.fromisoformat(date_str).date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Ungültiges Datumsformat. Verwenden Sie YYYY-MM-DD.")
        
        # Security: Only allow today and yesterday (using Berlin timezone)
        berlin_tz = pytz.timezone('Europe/Berlin')
        today = datetime.now(berlin_tz).date()
        yesterday = today - timedelta(days=1)
        if parsed_date not in [today, yesterday]:
            raise HTTPException(status_code=400, detail=f"Sponsoring ist nur für heute ({today}) oder gestern ({yesterday}) möglich.")
        
        # === PHASE 2: DATENSAMMLUNG ===
        # Use Berlin timezone for day boundaries
        start_of_day_utc, end_of_day_utc = get_berlin_day_bounds(parsed_date)
        
        # Get all breakfast orders for that day
        all_orders = await db.orders.find({
            "department_id": department_id,
            "order_type": "breakfast",
            "timestamp": {"$gte": start_of_day_utc.isoformat(), "$lte": end_of_day_utc.isoformat()},
            "$or": [{"is_cancelled": {"$exists": False}}, {"is_cancelled": False}]
        }).to_list(1000)
        
        # Check if already sponsored (handle comma-separated meal types)
        already_sponsored = False
        for order in all_orders:
            if order.get("is_sponsored"):
                sponsored_meal_types = order.get("sponsored_meal_type", "")
                if sponsored_meal_types:
                    sponsored_types_list = sponsored_meal_types.split(",")
                    if meal_type in sponsored_types_list:
                        already_sponsored = True
                        break
        
        if already_sponsored:
            raise HTTPException(status_code=400, detail=f"{'Frühstück' if meal_type == 'breakfast' else 'Mittagessen'} für {date_str} wurde bereits gesponsert.")
        
        # Filter relevant orders and exclude already sponsored ones
        relevant_orders = []
        for order in all_orders:
            # Check if this order was already sponsored for the current meal type
            sponsored_meal_types = order.get("sponsored_meal_type", "")
            if sponsored_meal_types:
                # Handle comma-separated meal types (for orders sponsored for multiple meal types)
                already_sponsored_meal_types = sponsored_meal_types.split(",")
                if meal_type in already_sponsored_meal_types:
                    continue  # Skip already sponsored orders for this meal type
                
            if meal_type == "breakfast":
                # All breakfast orders are relevant (if not already sponsored)
                relevant_orders.append(order)
            else:  # lunch
                # Only orders with lunch are relevant (if not already sponsored)
                has_lunch = any(item.get("has_lunch", False) for item in order.get("breakfast_items", []))
                if has_lunch:
                    relevant_orders.append(order)
        
        if not relevant_orders:
            raise HTTPException(status_code=404, detail=f"Keine {'Frühstück' if meal_type == 'breakfast' else 'Mittag'}-Bestellungen für {date_str} gefunden")
        
        # === PHASE 3: KOSTENBERECHNUNG ===
        # Get menu prices once to avoid repeated DB calls
        white_roll_price = 0.50
        seeded_roll_price = 0.60
        egg_price = 0.50
        coffee_price = 1.00
        
        try:
            white_menu = await db.menu_breakfast.find_one({"roll_type": "weiss", "department_id": department_id})
            if white_menu: white_roll_price = white_menu.get("price", 0.50)
            
            seeded_menu = await db.menu_breakfast.find_one({"roll_type": "koerner", "department_id": department_id})
            if seeded_menu: seeded_roll_price = seeded_menu.get("price", 0.60)
            
            # Get department-specific egg and coffee prices
            department_prices = await get_department_prices(department_id)
            egg_price = department_prices["boiled_eggs_price"]
            fried_egg_price = department_prices["fried_eggs_price"]
            coffee_price = department_prices["coffee_price"]
        except:
            pass  # Use defaults if DB calls fail
        
        # Calculate individual costs for each order
        order_calculations = []
        total_sponsored_cost = 0.0
        
        for order in relevant_orders:
            employee_id = order["employee_id"]
            order_total = order.get("total_price", 0)
            
            # Calculate breakdown
            breakfast_cost = 0.0  # rolls + eggs
            coffee_cost = 0.0
            lunch_cost = 0.0
            
            # Check if this order was already partially sponsored
            sponsored_meal_types = order.get("sponsored_meal_type", "")
            already_sponsored_breakfast = False
            already_sponsored_lunch = False
            
            if sponsored_meal_types:
                # Handle comma-separated meal types
                sponsored_types_list = sponsored_meal_types.split(",")
                already_sponsored_breakfast = "breakfast" in sponsored_types_list
                already_sponsored_lunch = "lunch" in sponsored_types_list
            
            for item in order.get("breakfast_items", []):
                # Rolls
                white_halves = item.get("white_halves", 0)
                seeded_halves = item.get("seeded_halves", 0)
                breakfast_cost += white_halves * white_roll_price + seeded_halves * seeded_roll_price
                
                # Boiled Eggs
                boiled_eggs = item.get("boiled_eggs", 0)
                breakfast_cost += boiled_eggs * egg_price
                
                # Fried Eggs
                fried_eggs = item.get("fried_eggs", 0)
                breakfast_cost += fried_eggs * fried_egg_price
                
                # Coffee
                if item.get("has_coffee", False):
                    coffee_cost += coffee_price
                
                # Lunch - calculate from daily lunch price instead of remainder
                if item.get("has_lunch", False):
                    # Get the actual lunch price for this order (not calculated remainder)
                    lunch_price_for_order = order.get("lunch_price", 0)
                    if lunch_price_for_order > 0:
                        lunch_cost = lunch_price_for_order
                    else:
                        # Fallback to calculation if lunch_price not stored
                        lunch_cost = order_total - breakfast_cost - coffee_cost
                        lunch_cost = max(0, lunch_cost)  # Ensure non-negative
            
            # Round to avoid floating point errors
            breakfast_cost = round(breakfast_cost, 2)
            coffee_cost = round(coffee_cost, 2)
            lunch_cost = round(lunch_cost, 2)
            
            # Calculate sponsored amount for this order - only if not already sponsored
            sponsored_amount = 0.0
            if meal_type == "breakfast" and not already_sponsored_breakfast:
                sponsored_amount = breakfast_cost  # Only breakfast items (rolls + eggs)
            elif meal_type == "lunch" and not already_sponsored_lunch:
                sponsored_amount = lunch_cost  # Only lunch
            # If already sponsored, skip this order (sponsored_amount remains 0)
            
            order_calculations.append({
                "order": order,
                "employee_id": employee_id,
                "breakfast_cost": breakfast_cost,
                "coffee_cost": coffee_cost, 
                "lunch_cost": lunch_cost,
                "sponsored_amount": sponsored_amount
            })
            
            total_sponsored_cost += sponsored_amount
        
        total_sponsored_cost = round(total_sponsored_cost, 2)
        
        if total_sponsored_cost <= 0:
            raise HTTPException(status_code=400, detail="Keine kostenpflichtigen Artikel für Sponsoring gefunden")
        
        # === PHASE 4: SPONSOR BERECHNUNG ===
        # Find sponsor's order and calculate their contribution
        sponsor_calculation = None
        sponsor_contributed_amount = 0.0
        
        for calc in order_calculations:
            if calc["employee_id"] == sponsor_employee_id:
                sponsor_calculation = calc
                sponsor_contributed_amount = calc["sponsored_amount"]
                break
        
        # WICHTIG: Sponsor zahlt für ALLE (inkl. sich selbst), aber seine eigenen Kosten sind schon in seiner Bestellung
        # Also: sponsor_additional_cost = total_sponsored_cost - sponsor_contributed_amount
        sponsor_additional_cost = total_sponsored_cost - sponsor_contributed_amount
        sponsor_additional_cost = round(sponsor_additional_cost, 2)
        
        # === PHASE 5: ATOMISCHE UPDATES ===
        
        # Calculate counts for all scenarios (sponsor with or without own order)
        sponsored_count = len(order_calculations)
        others_count = sponsored_count - (1 if sponsor_calculation else 0)  # Exclude sponsor only if they have an order
        meal_name = "Frühstück" if meal_type == "breakfast" else "Mittagessen"
        
        # 1. Create sponsor order to show sponsoring details (for all sponsors)
        if sponsor_calculation:
            # Sponsor has their own order - create a SEPARATE sponsor order for this sponsoring action
            today = get_berlin_date().strftime('%Y-%m-%d')
            current_time = datetime.utcnow()
            
            # Calculate total cost for display
            total_others_cost = total_sponsored_cost - sponsor_contributed_amount
            
            if others_count > 0:
                detailed_breakdown = f"Ausgegeben {others_count}x {meal_name} für {total_others_cost:.2f}€"
                unit_price_per_person = total_others_cost / others_count
                unit_price_text = f"{others_count} × {unit_price_per_person:.2f}€"
            else:
                detailed_breakdown = f"Keine anderen Mitarbeiter gesponsert"
                unit_price_text = ""
            
            # Create a separate sponsor order (don't modify the original breakfast order)
            sponsor_order_data = {
                "id": str(uuid.uuid4()),
                "employee_id": sponsor_employee_id,
                "department_id": department_id,
                "order_type": "breakfast",  # Sponsoring always goes to breakfast account
                "total_price": total_others_cost,
                "timestamp": current_time.isoformat(),
                "breakfast_items": [],  # Empty - this is a pure sponsoring order
                "drink_items": {},
                "sweet_items": {},
                "has_lunch": False,
                "lunch_price": 0.0,
                "is_sponsored": False,  # Sponsor is not sponsored
                "is_sponsor_order": True,  # This IS a sponsor order
                "sponsored_meal_type": meal_type,  # Only the current meal type being sponsored
                "sponsor_total_cost": total_others_cost,  # CRITICAL: Cost sponsored by this sponsor (excluding their own)
                "sponsor_employee_count": others_count,  # CRITICAL: Number of other employees sponsored
                "sponsor_message": f"{meal_name} wurde von dir ausgegeben, vielen Dank! (Ausgegeben für {others_count} Mitarbeiter im Wert von {total_others_cost:.2f}€)",
                "readable_items": [{
                    "description": detailed_breakdown,
                    "unit_price": unit_price_text,
                    "total_price": f"{total_others_cost:.2f} €"
                }]
            }
            
            await db.orders.insert_one(sponsor_order_data)
        
        # 2. Update employee balances and store order updates for later
        other_order_updates = []
        
        for calc in order_calculations:
            if calc["employee_id"] == sponsor_employee_id:
                continue  # Skip sponsor
            
            order = calc["order"]
            employee_id = calc["employee_id"]
            sponsored_amount = calc["sponsored_amount"]
            
            # Only process if sponsored_amount > 0 (meaning this meal type wasn't already sponsored)
            if sponsored_amount > 0:
                # CORRECTED: Refund sponsored amount to employee balance (INCREASE balance = less debt)
                # FIXED: Use update_employee_balance() ONLY (no double counting)
                await update_employee_balance(employee_id, department_id, 'breakfast', sponsored_amount)
                
                # Store order update for later
                sponsored_message = f"Dieses {'Frühstück' if meal_type == 'breakfast' else 'Mittagessen'} wurde von {sponsor_employee_name} ausgegeben, bedanke dich bei ihm!"
                
                # Check if order already has sponsoring information
                existing_sponsored_meal_type = order.get("sponsored_meal_type", "")
                if existing_sponsored_meal_type and existing_sponsored_meal_type != meal_type:
                    # Order already sponsored for different meal type - add to existing sponsoring
                    combined_meal_type = f"{existing_sponsored_meal_type},{meal_type}"
                    combined_message = f"{order.get('sponsored_message', '')} Zusätzlich: {sponsored_message}"
                else:
                    combined_meal_type = meal_type
                    combined_message = sponsored_message
                
                other_order_updates.append({
                    "id": order["id"],
                    "updates": {
                        "is_sponsored": True,
                        "sponsored_by_employee_id": sponsor_employee_id,
                        "sponsored_by_name": sponsor_employee_name,
                        "sponsored_meal_type": combined_meal_type,
                        "sponsored_message": combined_message,
                        "sponsored_date": datetime.now(timezone.utc).isoformat()
                    }
                })
        
        # 2. Create sponsor order if they don't have one (sponsor without own order scenario)
        if not sponsor_calculation and sponsor_additional_cost > 0:
            # Create a sponsoring order for the sponsor
            today = get_berlin_date().strftime('%Y-%m-%d')
            current_time = datetime.utcnow()
            
            # Calculate total cost for display
            total_others_cost = total_sponsored_cost  # All cost since sponsor has no own order
            
            if others_count > 0:
                # Remove the incorrect "á X.XX€" calculation - just show total
                detailed_breakdown = f"Ausgegeben {others_count}x {meal_name} für {total_others_cost:.2f}€"
                unit_price_per_person = total_others_cost / others_count
                unit_price_text = f"{others_count} × {unit_price_per_person:.2f}€"
            else:
                detailed_breakdown = f"Keine Mitarbeiter gesponsert"
                unit_price_text = ""
            
            sponsor_order_data = {
                "id": str(uuid.uuid4()),
                "employee_id": sponsor_employee_id,
                "department_id": department_id,
                "order_type": "breakfast",  # Sponsoring always goes to breakfast account
                "total_price": total_others_cost,
                "timestamp": current_time.isoformat(),
                "breakfast_items": [],  # Empty - this is a pure sponsoring order
                "drink_items": {},
                "sweet_items": {},
                "has_lunch": False,
                "lunch_price": 0.0,
                "is_sponsored": False,  # Sponsor is not sponsored
                "is_sponsor_order": True,  # This IS a sponsor order
                "sponsored_meal_type": meal_type,
                "sponsored_by_employee_id": sponsor_employee_id,
                "sponsor_employee_count": others_count,  # CRITICAL: Number of employees sponsored
                "sponsor_total_cost": total_others_cost,  # CRITICAL: Total cost sponsored
                "sponsor_message": f"{meal_name} wurde von dir ausgegeben, vielen Dank! (Ausgegeben für {others_count} Mitarbeiter im Wert von {total_others_cost:.2f}€)",
                "readable_items": [{
                    "description": detailed_breakdown,
                    "unit_price": unit_price_text,
                    "total_price": f"{total_others_cost:.2f} €"
                }]
            }
            
            await db.orders.insert_one(sponsor_order_data)

        # 3. Update sponsor balance and create payment log
        sponsor_employee = await db.employees.find_one({"id": sponsor_employee_id})
        if sponsor_employee:
            # FIXED: Use update_employee_balance() ONLY to avoid double charging
            # Sponsor zahlt zusätzlich nur für die anderen, nicht für sich selbst (das ist schon in der Bestellung)
            await update_employee_balance(sponsor_employee_id, department_id, 'breakfast', -sponsor_additional_cost)
            
            # NOTE: No PaymentLog needed for sponsoring - the sponsor order serves as the record
        
        # 4. Apply all order updates (after all other operations are complete)
        # Update sponsored orders
        for order_update in other_order_updates:
            await db.orders.update_one(
                {"id": order_update["id"]},
                {"$set": order_update["updates"]}
            )
        
        # === RÜCKGABE ===
        sponsored_items_description = f"{len(order_calculations)}x {'Frühstück' if meal_type == 'breakfast' else 'Mittagessen'}"
        
        return {
            "message": f"{'Frühstück' if meal_type == 'breakfast' else 'Mittagessen'} erfolgreich gesponsert",
            "sponsored_items": sponsored_items_description,
            "total_cost": total_sponsored_cost,
            "affected_employees": len(order_calculations),
            "sponsor": sponsor_employee_name,
            "sponsor_additional_cost": sponsor_additional_cost
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Sponsoring: {str(e)}")

@api_router.post("/admin/cleanup-testing-data")
async def cleanup_testing_data():
    """Admin: Clean up all orders and reset employee balances for fresh testing"""
    try:
        # Delete all orders
        orders_result = await db.orders.delete_many({})
        
        # Reset all employee balances
        employees_result = await db.employees.update_many(
            {},
            {"$set": {
                "breakfast_balance": 0.0,
                "drinks_sweets_balance": 0.0
            }}
        )
        
        # Delete payment logs
        payment_logs_result = await db.payment_logs.delete_many({})
        
        # Get remaining counts
        remaining_orders = await db.orders.count_documents({})
        employees_count = await db.employees.count_documents({})
        departments_count = await db.departments.count_documents({})
        
        return {
            "message": "Datenbank für Tests bereinigt",
            "deleted_orders": orders_result.deleted_count,
            "reset_employee_balances": employees_result.modified_count,
            "deleted_payment_logs": payment_logs_result.deleted_count,
            "remaining_orders": remaining_orders,
            "total_employees": employees_count,
            "total_departments": departments_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler bei der Bereinigung: {str(e)}")

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

# Mount static files for landing page BEFORE other middleware
landing_page_path = Path(__file__).parent.parent / "landing-page"
if landing_page_path.exists():
    # Serve landing page index at /landing-page route
    @app.get("/landing-page")
    async def landing_page():
        return FileResponse(str(landing_page_path / "index.html"), media_type="text/html")
    
    # Mount static files under /landing-page/
    app.mount("/landing-page", StaticFiles(directory=str(landing_page_path), html=True), name="landing")

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