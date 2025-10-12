# Changelog - Canteen Management System

## Version 1.3.0 - Developer Dashboard & UI Enhancements (October 2025)

### 🔧 **NEW: Developer Dashboard**
- **Developer Access**: New Dev login button with master password authentication
- **Enhanced Employee Management**: View all employees across departments with department grouping
- **Employee Migration**: Move employees between departments with automatic balance migration
- **Extended History Access**: View complete order/payment history with developer deletion controls
- **Saldo-Neutral Deletions**: Remove history entries without affecting balances

### ✅ **Security & Safety Features**
- **Balance Warning Modal**: Prevents employee deletion with open balances (main + subaccounts)
- **Dangerous Scripts Removed**: Cleanup scripts moved to backup folder for production safety
- **Balance Migration**: Automatic main↔subaccount balance transfer when moving employees

### 🎨 **UI/UX Improvements**
- **Statistics Enhancement**: Added total balance overview (Frühstück+Mittag, Snacks+Getränke)
- **Search Functionality**: Employee search in "Andere WA" guest employee modal
- **Department Grouping**: "Andere WA" tab now groups employees by home department
- **Responsive Design**: Improved tablet display (1024px) for homepage and admin dashboard
- **Terminology Update**: "Süßes/Süßware" → "Snacks" throughout application

### 🐛 **Bug Fixes**
- **Timezone Display**: Fixed German timezone (Europe/Berlin) in order history
- **NaN Error**: Fixed balance display showing "NaN€" in developer profiles
- **Sponsoring Display**: Corrected sponsoring calculation messages
- **Employee Deletion**: Enhanced deletion prevention with detailed balance breakdown

## Version 2.0 - Bug Fixes & Enhancements (August 2025)

### 🐛 Critical Bug Fixes

#### 1. **Sponsoring Calculation Logic Fixed**
- **Problem**: Sponsored employees' balances were incorrectly debited instead of credited
- **Solution**: Corrected balance calculation in `POST /api/department-admin/sponsor-meal` endpoint
- **Impact**: Sponsored meals now correctly set employee balance to 0€, sponsor pays full amount

#### 2. **Department-Specific Egg/Coffee Prices**
- **Problem**: Egg and coffee prices were global across all departments
- **Solution**: 
  - Created new `DepartmentSettings` model with department-specific pricing
  - Added endpoints: `GET/PUT /api/department-settings/{department_id}/boiled-eggs-price` and `coffee-price`
  - Frontend now loads department-specific prices instead of global settings
- **Impact**: Each department can now set their own egg and coffee prices independently

#### 3. **Admin Dashboard Calculation Errors After Sponsoring**
- **Problem**: Daily summaries showed incorrect calculations after breakfast sponsoring
- **Solution**: Fixed breakfast-history endpoint to only sponsor relevant items (rolls + eggs), keeping coffee and lunch with employee
- **Impact**: Tagesübersichten now show accurate remaining costs after sponsoring

#### 4. **Lunch Price Changes Affecting Cancelled Orders**
- **Problem**: Retroactive lunch price changes incorrectly modified cancelled orders and their balances
- **Solution**: 
  - Added `"is_cancelled": {"$ne": True}` filter to price update queries
  - Fixed balance calculation direction (price increase = balance decrease)
- **Impact**: Cancelled orders are now immune to price changes, preventing balance corruption

#### 5. **Order Creation After Cancellation**
- **Problem**: Employees couldn't create new breakfast orders after cancelling existing ones
- **Solution**: 
  - Updated existing order checks to ignore cancelled orders
  - Fixed frontend filtering to exclude cancelled orders from form pre-filling
- **Impact**: Users can now create fresh orders after cancellation

### 🎨 UI/UX Improvements

#### 1. **Consistent Color Coding**
- **Changed**: Employee balance displays now show positive amounts in GREEN (instead of blue)
- **Impact**: Better visual consistency across admin and employee dashboards

#### 2. **Updated Labels**
- **Changed**: "Frühstück Saldo" → "Frühstück/Mittag Saldo" 
- **Impact**: Clearer understanding that lunch costs are included in breakfast balance

#### 3. **Simplified Admin Views**
- **Removed**: "Gesamt Schulden" and "Gesamt Bestellungen" from admin dashboard
- **Impact**: Cleaner 50/50 layout focusing on the two main balance types

#### 4. **Success Notification System**
- **Added**: Modern notification modals for price changes and payments
- **Replaced**: Browser alerts with styled success notifications
- **Features**: Auto-close after 1 second, sound effects, consistent design
- **Coverage**: Egg/coffee price changes, payment processing, menu updates

### 🔧 Technical Improvements

#### 1. **Robust Order Cancellation Logic**
- **Enhanced**: Proper handling of cancelled orders throughout the system
- **Separation**: Clear distinction between active and cancelled orders in all operations
- **Data Integrity**: Cancelled orders no longer interfere with new order creation

#### 2. **Department-Specific Data Architecture**
- **New Models**: `DepartmentSettings` for per-department configuration
- **API Endpoints**: Full CRUD operations for department-specific pricing
- **Fallback Logic**: Graceful degradation to global settings when department settings unavailable

#### 3. **Balance Calculation Accuracy**
- **Fixed**: Retroactive price change calculations
- **Improved**: Sponsoring cost distribution logic
- **Protected**: Balance integrity against edge cases

### 📋 Database Schema Changes

#### New Collections:
- `department_settings`: Stores department-specific egg and coffee prices
  ```json
  {
    "id": "uuid",
    "department_id": "fw4abteilung2", 
    "boiled_eggs_price": 1.0,
    "coffee_price": 2.1
  }
  ```

#### Enhanced Order Model:
- Improved cancellation fields with proper audit trail
- Better timestamp handling for Berlin timezone

### 🚀 Deployment Notes

#### Environment Variables (Unchanged):
- `REACT_APP_BACKEND_URL`: Frontend API endpoint
- `MONGO_URL`: MongoDB connection string  
- `DB_NAME`: Database name (supports multi-tenant setup)

#### Migration Steps:
1. **No breaking changes** - existing data remains compatible
2. **Department settings** will be created automatically when first accessed
3. **Price changes** are backward compatible with existing orders

### 🧪 Testing Coverage

#### Verified Functionality:
- ✅ Sponsoring system (breakfast and lunch)
- ✅ Department-specific pricing
- ✅ Order cancellation and recreation
- ✅ Balance calculations and integrity
- ✅ UI consistency across all dashboards
- ✅ Multi-tenant deployment compatibility

#### Test Scenarios:
- Order creation → cancellation → new order creation
- Price changes on active vs cancelled orders  
- Cross-department price independence
- Sponsoring cost distribution accuracy
- Balance protection mechanisms

---

## Previous Versions

### Version 1.x - Core System
- Basic canteen management functionality
- Multi-department support
- Order management and employee dashboards
- Payment tracking and sponsoring features

---

**Developed by**: AI Engineering Team  
**Last Updated**: August 2025  
**Status**: Production Ready ✅