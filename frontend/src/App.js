import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Context for authentication
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [currentDepartment, setCurrentDepartment] = useState(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [isDepartmentAdmin, setIsDepartmentAdmin] = useState(false);

  const loginDepartment = (departmentData) => {
    setCurrentDepartment(departmentData);
    setIsAdmin(false);
    setIsDepartmentAdmin(false);
  };

  const loginAdmin = () => {
    setIsAdmin(true);
    setCurrentDepartment(null);
    setIsDepartmentAdmin(false);
  };

  const loginDepartmentAdmin = (departmentData) => {
    setCurrentDepartment(departmentData);
    setIsDepartmentAdmin(true);
    setIsAdmin(false);
  };

  const logout = () => {
    setCurrentDepartment(null);
    setIsAdmin(false);
    setIsDepartmentAdmin(false);
  };

  return (
    <AuthContext.Provider value={{
      currentDepartment,
      isAdmin,
      isDepartmentAdmin,
      loginDepartment,
      loginAdmin,
      loginDepartmentAdmin,
      logout
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Homepage with department cards
const Homepage = () => {
  const [departments, setDepartments] = useState([]);
  const [showDepartmentLogin, setShowDepartmentLogin] = useState(false);
  const [showDepartmentAdminLogin, setShowDepartmentAdminLogin] = useState(false);
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState(null);
  const { loginDepartment, loginAdmin, loginDepartmentAdmin } = React.useContext(AuthContext);

  useEffect(() => {
    initializeData();
    fetchDepartments();
  }, []);

  const initializeData = async () => {
    try {
      await axios.post(`${API}/init-data`);
    } catch (error) {
      console.error('Fehler beim Initialisieren der Daten:', error);
    }
  };

  const fetchDepartments = async () => {
    try {
      const response = await axios.get(`${API}/departments`);
      setDepartments(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Abteilungen:', error);
    }
  };

  const handleDepartmentClick = (department) => {
    setSelectedDepartment(department);
    setShowDepartmentLogin(true);
  };

  const handleDepartmentAdminClick = (department) => {
    setSelectedDepartment(department);
    setShowDepartmentAdminLogin(true);
  };

  const handleDepartmentLogin = async (password) => {
    try {
      const response = await axios.post(`${API}/login/department`, {
        department_name: selectedDepartment.name,
        password: password
      });
      loginDepartment(response.data);
      setShowDepartmentLogin(false);
    } catch (error) {
      alert('Ungültiges Passwort');
    }
  };

  const handleDepartmentAdminLogin = async (password) => {
    try {
      const response = await axios.post(`${API}/login/department-admin`, {
        department_name: selectedDepartment.name,
        admin_password: password
      });
      loginDepartmentAdmin(response.data);
      setShowDepartmentAdminLogin(false);
    } catch (error) {
      alert('Ungültiges Admin-Passwort');
    }
  };

  const handleAdminLogin = async (password) => {
    try {
      await axios.post(`${API}/login/admin`, { password });
      loginAdmin();
      setShowAdminLogin(false);
    } catch (error) {
      alert('Ungültiges Admin-Passwort');
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold text-center mb-12 text-gray-800">
          Kantine Verwaltungssystem
        </h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {departments.map((department) => (
            <div
              key={department.id}
              className="bg-white rounded-lg shadow-lg p-6 border-l-4 border-blue-500"
            >
              <h2 className="text-xl font-semibold text-gray-800 mb-4">
                {department.name}
              </h2>
              <div className="space-y-2">
                <button
                  onClick={() => handleDepartmentClick(department)}
                  className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors duration-300"
                >
                  Mitarbeiter Anmeldung
                </button>
                <button
                  onClick={() => handleDepartmentAdminClick(department)}
                  className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors duration-300"
                >
                  Admin Anmeldung
                </button>
              </div>
            </div>
          ))}
        </div>

        <div className="text-center">
          <button
            onClick={() => setShowAdminLogin(true)}
            className="bg-red-600 text-white px-6 py-3 rounded-lg hover:bg-red-700 transition-colors duration-300"
          >
            Admin Anmeldung
          </button>
        </div>

        {/* Department Login Modal */}
        {showDepartmentLogin && (
          <LoginModal
            title={`Anmeldung für ${selectedDepartment?.name}`}
            onLogin={handleDepartmentLogin}
            onClose={() => setShowDepartmentLogin(false)}
          />
        )}

        {/* Department Admin Login Modal */}
        {showDepartmentAdminLogin && (
          <LoginModal
            title={`Admin Anmeldung für ${selectedDepartment?.name}`}
            onLogin={handleDepartmentAdminLogin}
            onClose={() => setShowDepartmentAdminLogin(false)}
          />
        )}

        {/* Admin Login Modal */}
        {showAdminLogin && (
          <LoginModal
            title="Admin Anmeldung"
            onLogin={handleAdminLogin}
            onClose={() => setShowAdminLogin(false)}
          />
        )}
      </div>
    </div>
  );
};

// Login Modal Component
const LoginModal = ({ title, onLogin, onClose }) => {
  const [password, setPassword] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onLogin(password);
    setPassword('');
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
        <h2 className="text-2xl font-bold mb-6 text-center">{title}</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 text-sm font-bold mb-2">
              Passwort
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          <div className="flex gap-4">
            <button
              type="submit"
              className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Anmelden
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-500 text-white py-2 rounded-lg hover:bg-gray-600 transition-colors"
            >
              Abbrechen
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Department Dashboard
const DepartmentDashboard = () => {
  const [employees, setEmployees] = useState([]);
  const [showNewEmployee, setShowNewEmployee] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showEmployeeProfile, setShowEmployeeProfile] = useState(false);
  const { currentDepartment, logout } = React.useContext(AuthContext);

  useEffect(() => {
    if (currentDepartment) {
      fetchEmployees();
    }
  }, [currentDepartment]);

  const fetchEmployees = async () => {
    try {
      const response = await axios.get(
        `${API}/departments/${currentDepartment.department_id}/employees`
      );
      setEmployees(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Mitarbeiter:', error);
    }
  };

  const handleCreateEmployee = async (name) => {
    try {
      await axios.post(`${API}/employees`, {
        name,
        department_id: currentDepartment.department_id
      });
      fetchEmployees();
      setShowNewEmployee(false);
    } catch (error) {
      console.error('Fehler beim Erstellen des Mitarbeiters:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">
            {currentDepartment.department_name}
          </h1>
          <button
            onClick={logout}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors"
          >
            Abmelden
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {employees.map((employee) => (
            <div
              key={employee.id}
              onClick={() => setSelectedEmployee(employee)}
              className="bg-white rounded-lg shadow-lg p-6 cursor-pointer hover:shadow-xl transition-shadow duration-300"
            >
              <h3 className="text-lg font-semibold mb-2">{employee.name}</h3>
              <div className="text-sm text-gray-600">
                <p>Frühstück: €{employee.breakfast_balance.toFixed(2)}</p>
                <p>Getränke/Süßes: €{employee.drinks_sweets_balance.toFixed(2)}</p>
              </div>
            </div>
          ))}
          
          <div
            onClick={() => setShowNewEmployee(true)}
            className="bg-white rounded-lg shadow-lg p-6 cursor-pointer hover:shadow-xl transition-shadow duration-300 border-2 border-dashed border-gray-300 flex items-center justify-center"
          >
            <div className="text-center text-gray-500">
              <div className="text-4xl mb-2">+</div>
              <p>Neuer Mitarbeiter</p>
            </div>
          </div>
        </div>

        {/* Employee Menu Modal */}
        {selectedEmployee && (
          <EmployeeMenu
            employee={selectedEmployee}
            onClose={() => setSelectedEmployee(null)}
            onOrderComplete={() => {
              fetchEmployees();
              setSelectedEmployee(null);
            }}
          />
        )}

        {/* New Employee Modal */}
        {showNewEmployee && (
          <NewEmployeeModal
            onCreate={handleCreateEmployee}
            onClose={() => setShowNewEmployee(false)}
          />
        )}
      </div>
    </div>
  );
};

// Employee Menu Component
const EmployeeMenu = ({ employee, onClose, onOrderComplete }) => {
  const [activeCategory, setActiveCategory] = useState('breakfast');
  const [breakfastMenu, setBreakfastMenu] = useState([]);
  const [toppingsMenu, setToppingsMenu] = useState([]);
  const [drinksMenu, setDrinksMenu] = useState([]);
  const [sweetsMenu, setSweetsMenu] = useState([]);
  const [order, setOrder] = useState({
    breakfast_items: [],
    drink_items: {},
    sweet_items: {}
  });

  const { currentDepartment } = React.useContext(AuthContext);

  useEffect(() => {
    fetchMenus();
  }, []);

  const fetchMenus = async () => {
    try {
      const [breakfast, toppings, drinks, sweets] = await Promise.all([
        axios.get(`${API}/menu/breakfast`),
        axios.get(`${API}/menu/toppings`),
        axios.get(`${API}/menu/drinks`),
        axios.get(`${API}/menu/sweets`)
      ]);
      setBreakfastMenu(breakfast.data);
      setToppingsMenu(toppings.data);
      setDrinksMenu(drinks.data);
      setSweetsMenu(sweets.data);
    } catch (error) {
      console.error('Fehler beim Laden der Menüs:', error);
    }
  };

  const rollTypeLabels = {
    'hell': 'Helles Brötchen',
    'dunkel': 'Dunkles Brötchen',
    'vollkorn': 'Vollkornbrötchen'
  };

  const toppingLabels = {
    'ruehrei': 'Rührei',
    'spiegelei': 'Spiegelei',
    'eiersalat': 'Eiersalat',
    'salami': 'Salami',
    'schinken': 'Schinken',
    'kaese': 'Käse',
    'butter': 'Butter'
  };

  const addBreakfastItem = (rollType, rollCount, selectedToppings) => {
    const newItem = {
      roll_type: rollType,
      roll_count: parseInt(rollCount),
      toppings: selectedToppings
    };
    setOrder(prev => ({
      ...prev,
      breakfast_items: [...prev.breakfast_items, newItem]
    }));
  };

  const updateDrinkQuantity = (drinkId, quantity) => {
    setOrder(prev => ({
      ...prev,
      drink_items: {
        ...prev.drink_items,
        [drinkId]: parseInt(quantity) || 0
      }
    }));
  };

  const updateSweetQuantity = (sweetId, quantity) => {
    setOrder(prev => ({
      ...prev,
      sweet_items: {
        ...prev.sweet_items,
        [sweetId]: parseInt(quantity) || 0
      }
    }));
  };

  const submitOrder = async () => {
    try {
      await axios.post(`${API}/orders`, {
        employee_id: employee.id,
        department_id: currentDepartment.department_id,
        order_type: activeCategory,
        breakfast_items: activeCategory === 'breakfast' ? order.breakfast_items : [],
        drink_items: activeCategory === 'drinks' ? order.drink_items : {},
        sweet_items: activeCategory === 'sweets' ? order.sweet_items : {}
      });
      onOrderComplete();
    } catch (error) {
      console.error('Fehler beim Erstellen der Bestellung:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Bestellung für {employee.name}</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          </div>
          
          {/* Category Tabs */}
          <div className="flex mt-4 space-x-1">
            {['breakfast', 'drinks', 'sweets'].map((category) => (
              <button
                key={category}
                onClick={() => setActiveCategory(category)}
                className={`px-4 py-2 rounded-t-lg ${
                  activeCategory === category
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {category === 'breakfast' && 'Frühstück'}
                {category === 'drinks' && 'Getränke'}
                {category === 'sweets' && 'Süßes'}
              </button>
            ))}
          </div>
        </div>

        <div className="p-6">
          {activeCategory === 'breakfast' && (
            <BreakfastOrderForm
              breakfastMenu={breakfastMenu}
              toppingsMenu={toppingsMenu}
              onAddItem={addBreakfastItem}
              rollTypeLabels={rollTypeLabels}
              toppingLabels={toppingLabels}
            />
          )}

          {activeCategory === 'drinks' && (
            <DrinksOrderForm
              drinksMenu={drinksMenu}
              onUpdateQuantity={updateDrinkQuantity}
            />
          )}

          {activeCategory === 'sweets' && (
            <SweetsOrderForm
              sweetsMenu={sweetsMenu}
              onUpdateQuantity={updateSweetQuantity}
            />
          )}

          <div className="mt-6 flex justify-end space-x-4">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              Abbrechen
            </button>
            <button
              onClick={submitOrder}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Bestellung aufgeben
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Breakfast Order Form
const BreakfastOrderForm = ({ breakfastMenu, toppingsMenu, onAddItem, rollTypeLabels, toppingLabels }) => {
  const [selectedRollType, setSelectedRollType] = useState('');
  const [rollCount, setRollCount] = useState(1);
  const [selectedToppings, setSelectedToppings] = useState([]);

  const handleToppingChange = (toppingType) => {
    setSelectedToppings(prev => 
      prev.includes(toppingType)
        ? prev.filter(t => t !== toppingType)
        : [...prev, toppingType]
    );
  };

  const handleAddItem = () => {
    if (selectedRollType && rollCount > 0) {
      onAddItem(selectedRollType, rollCount, selectedToppings);
      setSelectedRollType('');
      setRollCount(1);
      setSelectedToppings([]);
    }
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Frühstück zusammenstellen</h3>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium mb-2">Brötchenart</label>
          {breakfastMenu.map((item) => (
            <label key={item.id} className="flex items-center mb-2">
              <input
                type="radio"
                name="rollType"
                value={item.roll_type}
                onChange={(e) => setSelectedRollType(e.target.value)}
                className="mr-2"
              />
              {rollTypeLabels[item.roll_type]} (€{item.price.toFixed(2)})
            </label>
          ))}
          
          <div className="mt-4">
            <label className="block text-sm font-medium mb-2">Anzahl</label>
            <input
              type="number"
              min="1"
              value={rollCount}
              onChange={(e) => setRollCount(e.target.value)}
              className="w-20 px-2 py-1 border border-gray-300 rounded"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">Belag</label>
          {toppingsMenu.map((item) => (
            <label key={item.id} className="flex items-center mb-2">
              <input
                type="checkbox"
                checked={selectedToppings.includes(item.topping_type)}
                onChange={() => handleToppingChange(item.topping_type)}
                className="mr-2"
              />
              {toppingLabels[item.topping_type]} (€{item.price.toFixed(2)})
            </label>
          ))}
        </div>
      </div>

      <button
        onClick={handleAddItem}
        disabled={!selectedRollType}
        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
      >
        Hinzufügen
      </button>
    </div>
  );
};

// Drinks Order Form
const DrinksOrderForm = ({ drinksMenu, onUpdateQuantity }) => {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Getränke auswählen</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {drinksMenu.map((drink) => (
          <div key={drink.id} className="flex items-center justify-between p-3 border border-gray-300 rounded-lg">
            <div>
              <span className="font-medium">{drink.name}</span>
              <span className="text-gray-600 ml-2">(€{drink.price.toFixed(2)})</span>
            </div>
            <input
              type="number"
              min="0"
              placeholder="0"
              onChange={(e) => onUpdateQuantity(drink.id, e.target.value)}
              className="w-16 px-2 py-1 border border-gray-300 rounded text-center"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

// Sweets Order Form
const SweetsOrderForm = ({ sweetsMenu, onUpdateQuantity }) => {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Süßes auswählen</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sweetsMenu.map((sweet) => (
          <div key={sweet.id} className="flex items-center justify-between p-3 border border-gray-300 rounded-lg">
            <div>
              <span className="font-medium">{sweet.name}</span>
              <span className="text-gray-600 ml-2">(€{sweet.price.toFixed(2)})</span>
            </div>
            <input
              type="number"
              min="0"
              placeholder="0"
              onChange={(e) => onUpdateQuantity(sweet.id, e.target.value)}
              className="w-16 px-2 py-1 border border-gray-300 rounded text-center"
            />
          </div>
        ))}
      </div>
    </div>
  );
};

// New Employee Modal
const NewEmployeeModal = ({ onCreate, onClose }) => {
  const [name, setName] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (name.trim()) {
      onCreate(name.trim());
      setName('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">Neuen Mitarbeiter hinzufügen</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Name</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          <div className="flex gap-4">
            <button
              type="submit"
              className="flex-1 bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
            >
              Erstellen
            </button>
            <button
              type="button"
              onClick={onClose}
              className="flex-1 bg-gray-500 text-white py-2 rounded-lg hover:bg-gray-600"
            >
              Abbrechen
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Admin Dashboard (placeholder for now)
const AdminDashboard = () => {
  const { logout } = React.useContext(AuthContext);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Admin Dashboard</h1>
          <button
            onClick={logout}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
          >
            Abmelden
          </button>
        </div>
        
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-4">Verwaltungsfunktionen</h2>
          <p className="text-gray-600">
            Admin-Funktionen werden in der nächsten Phase implementiert:
            <br />• Bestellungen bearbeiten/löschen
            <br />• Guthaben zurücksetzen
            <br />• Inventar verwalten
            <br />• Tagesberichte anzeigen
          </p>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const { currentDepartment, isAdmin } = React.useContext(AuthContext);

  if (isAdmin) {
    return <AdminDashboard />;
  }

  if (currentDepartment) {
    return <DepartmentDashboard />;
  }

  return <Homepage />;
}

// App with Context Provider
export default function AppWithProvider() {
  return (
    <AuthProvider>
      <App />
    </AuthProvider>
  );
}