# 🚀 CANTEEN MANAGEMENT - DEPLOYMENT GUIDE

## 📋 CLEAN DEPLOYMENT PROCEDURE

### 1. **Server Preparation**
```bash
# Stop services
sudo systemctl stop [ihr-backend-service]
sudo systemctl stop [ihr-frontend-service]

# Backup current database (optional)
mongodump --uri="mongodb://canteen_user:bnp.ABW2fbq4gad5hge@127.0.0.1:27017/canteen_db" --out=/tmp/backup_$(date +%Y%m%d)
```

### 2. **Clean Database** 
```bash
# Connect to MongoDB
mongo mongodb://canteen_user:bnp.ABW2fbq4gad5hge@127.0.0.1:27017/canteen_db

# Clean all collections for fresh start
db.departments.deleteMany({})
db.employees.deleteMany({}) 
db.menu_breakfast.deleteMany({})
db.menu_toppings.deleteMany({})
db.menu_drinks.deleteMany({})
db.menu_sweets.deleteMany({})
db.lunch_settings.deleteMany({})
db.breakfast_orders.deleteMany({})
db.drink_orders.deleteMany({})
db.sweet_orders.deleteMany({})

exit
```

### 3. **Deploy Code**
```bash
# Pull latest code
git pull

# Copy production environment files
cp frontend/.env.production frontend/.env
cp backend/.env.production backend/.env
```

### 4. **Build Frontend**
```bash
cd frontend
npm install
npm run build
cd ..
```

### 5. **Start Services**
```bash
sudo systemctl start [ihr-backend-service]
sudo systemctl start [ihr-frontend-service]

# Verify services are running
sudo systemctl status [ihr-backend-service]
sudo systemctl status [ihr-frontend-service]
```

### 6. **Initialize Fresh Data**
```bash
# Initialize departments and menu with FIXED IDs
curl -X POST https://kantine.dev-creativey.de/api/init-data

# Verify departments
curl -s https://kantine.dev-creativey.de/api/departments
# Should show: fw4abteilung1, fw4abteilung2, fw4abteilung3, fw4abteilung4
```

### 7. **Verify Complete Functionality**
```bash
# Test menu data
curl -s https://kantine.dev-creativey.de/api/menu/toppings/fw4abteilung1

# Test drinks
curl -s https://kantine.dev-creativey.de/api/menu/drinks/fw4abteilung1

# Test employee creation
curl -X POST https://kantine.dev-creativey.de/api/employees \
-H "Content-Type: application/json" \
-d '{"name": "Test Employee", "department_id": "fw4abteilung1"}'
```

## ✅ **FIXED DEPARTMENT IDs**

The system now uses **stable, fixed department IDs**:
- `fw4abteilung1` = 1. Wachabteilung
- `fw4abteilung2` = 2. Wachabteilung  
- `fw4abteilung3` = 3. Wachabteilung
- `fw4abteilung4` = 4. Wachabteilung

**Benefits:**
- ✅ No more UUID chaos
- ✅ Data consistency across updates
- ✅ Menu items stay connected to departments
- ✅ Password changes persist
- ✅ Employee data remains stable

## 🔧 **TROUBLESHOOTING**

**If departments show duplicates:**
- Clean database and re-initialize as above

**If menu items are empty:**
- Check department IDs match fixed format
- Re-run init-data endpoint

**If frontend shows errors:**
- Verify .env contains correct REACT_APP_BACKEND_URL
- Rebuild frontend with `npm run build`