import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

// Detect environment and set appropriate backend URL
const isProduction = window.location.hostname !== 'localhost';
const BACKEND_URL = isProduction ? '' : (process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001');
const API = BACKEND_URL ? `${BACKEND_URL}/api` : '/api';

// Context for authentication
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [currentDepartment, setCurrentDepartment] = useState(null);
  const [isDepartmentAdmin, setIsDepartmentAdmin] = useState(false);
  const [isMasterAdmin, setIsMasterAdmin] = useState(false);

  const loginDepartment = (departmentData) => {
    setCurrentDepartment(departmentData);
    setIsDepartmentAdmin(false);
    setIsMasterAdmin(false);
  };

  const loginDepartmentAdmin = (departmentData) => {
    setCurrentDepartment(departmentData);
    setIsDepartmentAdmin(true);
    setIsMasterAdmin(departmentData.access_level === "master");
  };

  const logout = () => {
    setCurrentDepartment(null);
    setIsDepartmentAdmin(false);
    setIsMasterAdmin(false);
  };

  const setAuthState = (state) => {
    if (state.currentDepartment) {
      setCurrentDepartment(state.currentDepartment);
    }
    if (state.hasOwnProperty('isDepartmentAdmin')) {
      setIsDepartmentAdmin(state.isDepartmentAdmin);
    }
    if (state.hasOwnProperty('isMasterAdmin')) {
      setIsMasterAdmin(state.isMasterAdmin);
    }
  };

  return (
    <AuthContext.Provider value={{
      currentDepartment,
      isDepartmentAdmin,
      isMasterAdmin,
      loginDepartment,
      loginDepartmentAdmin,
      logout,
      setAuthState
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// Individual Employee Profile Component
const IndividualEmployeeProfile = ({ employee, onClose }) => {
  const [employeeProfile, setEmployeeProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchEmployeeProfile();
  }, [employee.id]);

  const fetchEmployeeProfile = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/employees/${employee.id}/profile`);
      setEmployeeProfile(response.data);
    } catch (error) {
      console.error('Fehler beim Laden des Mitarbeiterprofils:', error);
      alert('Fehler beim Laden des Profils');
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getOrderTypeLabel = (orderType) => {
    switch (orderType) {
      case 'breakfast': return 'Frühstück';
      case 'drinks': return 'Getränke';
      case 'sweets': return 'Süßes';
      default: return orderType;
    }
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Lade Profile...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!employeeProfile) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <p>Fehler beim Laden des Profils</p>
          <button onClick={onClose} className="mt-4 bg-red-600 text-white px-4 py-2 rounded">
            Schließen
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">{employeeProfile.employee.name} - Verlauf</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800">Frühstück Saldo</h3>
              <p className="text-2xl font-bold text-blue-600">€{employeeProfile.breakfast_total.toFixed(2)}</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800">Getränke/Süßes Saldo</h3>
              <p className="text-2xl font-bold text-green-600">€{employeeProfile.drinks_sweets_total.toFixed(2)}</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="font-semibold text-purple-800">Gesamt Bestellungen</h3>
              <p className="text-2xl font-bold text-purple-600">{employeeProfile.total_orders}</p>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h3 className="font-semibold text-orange-800">Gesamt Schulden</h3>
              <p className="text-2xl font-bold text-orange-600">€{(employeeProfile.breakfast_total + employeeProfile.drinks_sweets_total).toFixed(2)}</p>
            </div>
          </div>

          {/* Order History */}
          <div>
            <h3 className="text-xl font-semibold mb-4">Bestellverlauf</h3>
            {employeeProfile.order_history.length === 0 ? (
              <p className="text-gray-600 text-center py-8">Keine Bestellungen vorhanden</p>
            ) : (
              <div className="space-y-4">
                {employeeProfile.order_history.map((order, index) => (
                  <div key={order.id || index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <span className="inline-block bg-blue-100 text-blue-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded">
                          {getOrderTypeLabel(order.order_type)}
                        </span>
                        <span className="text-sm text-gray-600">{formatDate(order.timestamp)}</span>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">€{order.total_price.toFixed(2)}</p>
                      </div>
                    </div>
                    
                    {order.readable_items && order.readable_items.length > 0 && (
                      <div className="space-y-1">
                        {order.readable_items.map((item, idx) => (
                          <div key={idx} className="text-sm">
                            <span className="font-medium">{item.description}</span>
                            {item.toppings && <span className="text-gray-600"> mit {item.toppings}</span>}
                            {item.unit_price && <span className="text-gray-600"> ({item.unit_price} pro Stück)</span>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Homepage with department cards - Password Required
const Homepage = () => {
  const [departments, setDepartments] = useState([]);
  const [showDepartmentLogin, setShowDepartmentLogin] = useState(false);
  const [selectedDepartment, setSelectedDepartment] = useState(null);
  const { loginDepartment } = React.useContext(AuthContext);

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

  return (
    <div className="min-h-screen bg-gray-100 p-4 sm:p-6 md:p-8 lg:p-12">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-center mb-8 sm:mb-12 lg:mb-16 text-gray-800 px-4">
          Feuerwache Lichterfelde Kantine
        </h1>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 lg:gap-8 mb-8 px-4">
          {departments.map((department) => (
            <div
              key={department.id}
              onClick={() => handleDepartmentClick(department)}
              className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:scale-105 p-6 sm:p-8 lg:p-10 flex items-center justify-center"
            >
              <h2 className="text-xl sm:text-2xl lg:text-3xl font-semibold text-center text-blue-800">
                {department.name}
              </h2>
            </div>
          ))}
        </div>

        <div className="text-center">
          <p className="text-gray-600">Wählen Sie Ihre Wachabteilung aus</p>
        </div>

        {/* Department Login Modal */}
        {showDepartmentLogin && (
          <LoginModal
            title={`Passwort für ${selectedDepartment?.name}`}
            onLogin={handleDepartmentLogin}
            onClose={() => setShowDepartmentLogin(false)}
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

// Department Dashboard with Admin Login Inside
const DepartmentDashboard = () => {
  const [employees, setEmployees] = useState([]);
  const [showNewEmployee, setShowNewEmployee] = useState(false);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showEmployeeProfile, setShowEmployeeProfile] = useState(false);
  const [selectedEmployeeForProfile, setSelectedEmployeeForProfile] = useState(null);
  const [showBreakfastSummary, setShowBreakfastSummary] = useState(false);
  const [showAdminLogin, setShowAdminLogin] = useState(false);
  const [showMasterLogin, setShowMasterLogin] = useState(false);
  const { currentDepartment, logout, loginDepartmentAdmin } = React.useContext(AuthContext);

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

  const handleEmployeeClick = (employee, event) => {
    // Check if the click was on the "Verlauf" text
    if (event && event.target && event.target.closest('.verlauf-text')) {
      return; // Don't open order menu if clicking on Verlauf text
    }
    setSelectedEmployee(employee);
  };

  const handleEmployeeProfileClick = async (employee, event) => {
    try {
      event.stopPropagation(); // Prevent the employee order menu from opening
      setSelectedEmployeeForProfile(employee);
      setShowEmployeeProfile(true);
    } catch (error) {
      console.error('Error opening employee profile:', error);
      alert('Fehler beim Öffnen des Mitarbeiterprofils');
    }
  };

  const handleAdminLogin = async (password) => {
    try {
      const response = await axios.post(`${API}/login/department-admin`, {
        department_name: currentDepartment.department_name,
        admin_password: password
      });
      loginDepartmentAdmin(response.data);
      setShowAdminLogin(false);
    } catch (error) {
      alert('Ungültiges Admin-Passwort');
    }
  };

  const handleMasterLogin = async (password) => {
    try {
      const response = await axios.post(`${API}/login/master?department_name=${currentDepartment.department_name}&master_password=${password}`);
      loginDepartmentAdmin(response.data);
      setShowMasterLogin(false);
    } catch (error) {
      alert('Ungültiges Master-Passwort');
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
    <div className="min-h-screen bg-gray-100 p-4 sm:p-6 md:p-8 lg:p-12">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row justify-between items-center mb-6 sm:mb-8 lg:mb-12 gap-4">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold text-gray-800 text-center sm:text-left">
            {currentDepartment.department_name}
          </h1>
          <div className="flex flex-wrap gap-2 sm:gap-4 justify-center sm:justify-end">
            <button
              onClick={() => setShowBreakfastSummary(true)}
              className="bg-green-600 text-white px-3 sm:px-4 py-2 rounded-lg hover:bg-green-700 transition-colors text-sm sm:text-base whitespace-nowrap"
            >
              Frühstück Übersicht
            </button>
            <button
              onClick={() => setShowAdminLogin(true)}
              className="bg-orange-600 text-white px-3 sm:px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors text-sm sm:text-base whitespace-nowrap"
            >
              Admin Login
            </button>
            <button
              onClick={() => setShowMasterLogin(true)}
              className="bg-purple-600 text-white px-2 sm:px-3 py-2 rounded-lg hover:bg-purple-700 transition-colors text-xs sm:text-sm whitespace-nowrap"
            >
              Master
            </button>
            <button
              onClick={logout}
              className="bg-red-600 text-white px-3 sm:px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm sm:text-base whitespace-nowrap"
            >
              Abmelden
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6 lg:gap-8 px-4">
          {employees.map((employee) => (
            <div
              key={employee.id}
              onClick={(event) => handleEmployeeClick(employee, event)}
              className="bg-white rounded-xl shadow-lg p-4 sm:p-6 lg:p-8 cursor-pointer hover:shadow-xl transition-all duration-300 transform hover:scale-105"
            >
              <h3 className="text-lg sm:text-xl font-semibold mb-3 sm:mb-4 text-gray-800">{employee.name}</h3>
              <div className="text-sm sm:text-base text-gray-600 mb-4 sm:mb-6 space-y-2">
                {employee.breakfast_balance > 0 && (
                  <p className="flex justify-between">
                    <span>Frühstück:</span> 
                    <span className="font-medium">€{employee.breakfast_balance.toFixed(2)}</span>
                  </p>
                )}
                {employee.drinks_sweets_balance > 0 && (
                  <p className="flex justify-between">
                    <span>Getränke/Süßes:</span> 
                    <span className="font-medium">€{employee.drinks_sweets_balance.toFixed(2)}</span>
                  </p>
                )}
                {employee.breakfast_balance === 0 && employee.drinks_sweets_balance === 0 && (
                  <p className="text-center text-gray-500 italic">
                    Keine offenen Bestellungen
                  </p>
                )}
              </div>
              <div className="flex gap-2 sm:gap-3">
                <div className="flex-1 text-center text-xs sm:text-sm text-gray-700 py-2 sm:py-3 cursor-pointer hover:text-gray-900 verlauf-text rounded-lg hover:bg-gray-100 transition-colors"
                     onClick={(event) => handleEmployeeProfileClick(employee, event)}>
                  Verlauf
                </div>
                <button
                  onClick={() => handleEmployeeClick(employee)}
                  className="flex-1 bg-blue-600 text-white text-xs sm:text-sm py-2 sm:py-3 px-3 sm:px-4 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  Bestellen
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Breakfast Summary Modal */}
        {showBreakfastSummary && (
          <BreakfastSummaryTable
            departmentId={currentDepartment.department_id}
            onClose={() => setShowBreakfastSummary(false)}
          />
        )}

        {/* Employee Profile Modal for Individual Employee */}
        {showEmployeeProfile && selectedEmployeeForProfile && (
          <IndividualEmployeeProfile
            employee={selectedEmployeeForProfile}
            onClose={() => {
              setShowEmployeeProfile(false);
              setSelectedEmployeeForProfile(null);
            }}
          />
        )}

        {/* Employee Menu Modal */}
        {selectedEmployee && (
          <EmployeeMenu
            employee={selectedEmployee}
            onClose={() => setSelectedEmployee(null)}
            onOrderComplete={() => {
              fetchEmployees();
              setSelectedEmployee(null);
            }}
            fetchEmployees={fetchEmployees}
          />
        )}

        {/* Admin Login Modal */}
        {showAdminLogin && (
          <LoginModal
            title={`Admin Login für ${currentDepartment.department_name}`}
            onLogin={handleAdminLogin}
            onClose={() => setShowAdminLogin(false)}
          />
        )}

        {/* Master Login Modal */}
        {showMasterLogin && (
          <LoginModal
            title={`Master Login für ${currentDepartment.department_name}`}
            onLogin={handleMasterLogin}
            onClose={() => setShowMasterLogin(false)}
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
const EmployeeMenu = ({ employee, onClose, onOrderComplete, fetchEmployees }) => {
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
  const [breakfastFormData, setBreakfastFormData] = useState(null);
  const [isLoadingExistingOrders, setIsLoadingExistingOrders] = useState(true);

  const { currentDepartment } = React.useContext(AuthContext);

  // Load existing orders for today when component mounts
  useEffect(() => {
    loadExistingOrdersForToday();
  }, [employee.id]);

  const loadExistingOrdersForToday = async () => {
    try {
      setIsLoadingExistingOrders(true);
      const response = await axios.get(`${API}/employees/${employee.id}/orders`);
      const orders = response.data.orders || [];
      
      // Filter orders for today
      const today = new Date().toDateString();
      const todaysOrders = orders.filter(order => {
        const orderDate = new Date(order.timestamp).toDateString();
        return orderDate === today;
      });

      // Populate existing order data if available
      const todaysOrder = {
        breakfast_items: [],
        drink_items: {},
        sweet_items: {}
      };

      todaysOrders.forEach(order => {
        if (order.order_type === 'breakfast' && order.breakfast_items) {
          todaysOrder.breakfast_items.push(...order.breakfast_items);
        } else if (order.order_type === 'drinks' && order.drink_items) {
          Object.assign(todaysOrder.drink_items, order.drink_items);
        } else if (order.order_type === 'sweets' && order.sweet_items) {
          Object.assign(todaysOrder.sweet_items, order.sweet_items);
        }
      });

      setOrder(todaysOrder);

      // If there's breakfast data, pre-fill the form
      if (todaysOrder.breakfast_items.length > 0) {
        const latestBreakfast = todaysOrder.breakfast_items[0];
        console.log('Loading existing breakfast data:', latestBreakfast);
        setBreakfastFormData(latestBreakfast);
      } else {
        setBreakfastFormData(null);
      }

    } catch (error) {
      console.error('Fehler beim Laden bestehender Bestellungen:', error);
      // Continue with empty order if loading fails
    } finally {
      setIsLoadingExistingOrders(false);
    }
  };

  useEffect(() => {
    fetchMenus();
  }, []);

  const fetchMenus = async () => {
    try {
      if (!currentDepartment?.department_id) {
        console.error('No department ID available for menu fetch');
        return;
      }

      const departmentId = currentDepartment.department_id;
      const [breakfast, toppings, drinks, sweets] = await Promise.all([
        axios.get(`${API}/menu/breakfast/${departmentId}`),
        axios.get(`${API}/menu/toppings/${departmentId}`),
        axios.get(`${API}/menu/drinks/${departmentId}`),
        axios.get(`${API}/menu/sweets/${departmentId}`)
      ]);
      setBreakfastMenu(breakfast.data);
      setToppingsMenu(toppings.data);
      setDrinksMenu(drinks.data);
      setSweetsMenu(sweets.data);
    } catch (error) {
      console.error('Fehler beim Laden der Menüs:', error);
      // Fallback to old endpoints if department-specific ones fail
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
      } catch (fallbackError) {
        console.error('Fallback menu loading also failed:', fallbackError);
      }
    }
  };

  // Create dynamic labels from menu data
  const rollTypeLabels = {
    'weiss': 'Weißes Brötchen',
    'koerner': 'Körnerbrötchen'
  };

  // Use custom names from menu if available, otherwise fall back to defaults
  const toppingLabels = {};
  toppingsMenu.forEach(item => {
    toppingLabels[item.topping_type] = item.name || {
      'ruehrei': 'Rührei',
      'spiegelei': 'Spiegelei', 
      'eiersalat': 'Eiersalat',
      'salami': 'Salami',
      'schinken': 'Schinken',
      'kaese': 'Käse',
      'butter': 'Butter'
    }[item.topping_type] || item.topping_type;
  });

  // Fallback toppings if menu is empty
  const defaultToppingLabels = {
    'ruehrei': 'Rührei',
    'spiegelei': 'Spiegelei',
    'eiersalat': 'Eiersalat',
    'salami': 'Salami',
    'schinken': 'Schinken',
    'kaese': 'Käse',
    'butter': 'Butter'
  };

  const finalToppingLabels = Object.keys(toppingLabels).length > 0 ? toppingLabels : defaultToppingLabels;

  const addBreakfastItem = (totalHalves, whiteHalves, seededHalves, selectedToppings, hasLunch, totalCost) => {
    const newItem = {
      total_halves: totalHalves,
      white_halves: whiteHalves,
      seeded_halves: seededHalves,
      toppings: selectedToppings,
      has_lunch: hasLunch,
      item_cost: totalCost
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
      let breakfastItems = [];
      
      // For breakfast category, use form data if available, otherwise use order array
      if (activeCategory === 'breakfast') {
        if (breakfastFormData) {
          breakfastItems = [breakfastFormData];
        } else if (order.breakfast_items.length > 0) {
          breakfastItems = order.breakfast_items;
        } else {
          alert('Bitte füllen Sie das Frühstücksformular aus.');
          return;
        }
      }
      
      // Check if employee already has an order for today (for breakfast only)
      if (activeCategory === 'breakfast') {
        try {
          const existingOrdersResponse = await axios.get(`${API}/employees/${employee.id}/orders`);
          const orders = existingOrdersResponse.data.orders || [];
          
          // Filter orders for today
          const today = new Date().toDateString();
          const todaysBreakfastOrders = orders.filter(order => {
            const orderDate = new Date(order.timestamp).toDateString();
            return orderDate === today && order.order_type === 'breakfast';
          });

          if (todaysBreakfastOrders.length > 0) {
            // Update existing order instead of creating new
            const existingOrderId = todaysBreakfastOrders[0].id;
            
            await axios.put(`${API}/orders/${existingOrderId}`, {
              breakfast_items: breakfastItems
            });
            
            alert('Bestellung erfolgreich aktualisiert!');
          } else {
            // Create new order
            await axios.post(`${API}/orders`, {
              employee_id: employee.id,
              department_id: currentDepartment.department_id,
              order_type: activeCategory,
              breakfast_items: breakfastItems,
              drink_items: {},
              sweet_items: {}
            });
            
            alert('Bestellung erfolgreich gespeichert!');
          }
        } catch (existingOrderError) {
          console.error('Fehler beim Prüfen bestehender Bestellungen:', existingOrderError);
          // Fallback: try to create new order
          await axios.post(`${API}/orders`, {
            employee_id: employee.id,
            department_id: currentDepartment.department_id,
            order_type: activeCategory,
            breakfast_items: breakfastItems,
            drink_items: {},
            sweet_items: {}
          });
          
          alert('Bestellung erfolgreich gespeichert!');
        }
      } else {
        // For drinks and sweets, create new order as usual
        const orderData = {
          employee_id: employee.id,
          department_id: currentDepartment.department_id,
          order_type: activeCategory,
          breakfast_items: [],
          drink_items: activeCategory === 'drinks' ? order.drink_items : {},
          sweet_items: activeCategory === 'sweets' ? order.sweet_items : {}
        };

        await axios.post(`${API}/orders`, orderData);
        alert('Bestellung erfolgreich gespeichert!');
      }
      
      // Refresh employee data to show updated balance
      if (fetchEmployees) {
        fetchEmployees();
      }
      
      // DON'T reset the form data or close the modal - keep it open for editing
      
    } catch (error) {
      console.error('Fehler beim Speichern der Bestellung:', error);
      alert('Fehler beim Speichern der Bestellung. Bitte versuchen Sie es erneut.');
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
              toppingLabels={finalToppingLabels}
              existingOrderData={breakfastFormData}
              onDirectSubmit={(breakfastData) => {
                // This will be called directly when breakfast form is submitted
                setBreakfastFormData(breakfastData);
              }}
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
              Bestellung speichern
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Simplified Breakfast Order Form - Direct Roll Selection with Topping Assignment
const BreakfastOrderForm = ({ breakfastMenu, toppingsMenu, onAddItem, rollTypeLabels, toppingLabels, onDirectSubmit, existingOrderData }) => {
  const [whiteRolls, setWhiteRolls] = useState(0);
  const [seededRolls, setSeededRolls] = useState(0);
  const [toppingAssignments, setToppingAssignments] = useState([]);
  const [hasLunch, setHasLunch] = useState(false);

  // Initialize form with existing order data if available
  useEffect(() => {
    if (existingOrderData) {
      setWhiteRolls(existingOrderData.white_halves || 0);
      setSeededRolls(existingOrderData.seeded_halves || 0);
      setHasLunch(existingOrderData.has_lunch || false);
      
      // Reconstruct toppings assignments
      if (existingOrderData.toppings && Array.isArray(existingOrderData.toppings)) {
        const newAssignments = [];
        existingOrderData.toppings.forEach((topping, index) => {
          newAssignments.push({
            id: `existing_${index}`,
            rollType: index < (existingOrderData.white_halves || 0) ? 'weiss' : 'koerner',
            rollLabel: `Brötchen ${index + 1}`,
            topping: topping
          });
        });
        setToppingAssignments(newAssignments);
      }
    }
  }, [existingOrderData]);

  // Get actual prices from menu (use admin-set prices directly)
  const getBreakfastPrice = (rollType) => {
    const menuItem = breakfastMenu.find(item => item.roll_type === rollType);
    return menuItem ? menuItem.price : 0;
  };

  const whiteRollPrice = getBreakfastPrice('weiss');
  const seededRollPrice = getBreakfastPrice('koerner');

  const totalHalves = whiteRolls + seededRolls;
  const totalCost = (whiteRolls * whiteRollPrice) + (seededRolls * seededRollPrice);

  // Update topping assignments when roll counts change
  useEffect(() => {
    const newAssignments = [];
    // Add white roll topping slots
    for (let i = 0; i < whiteRolls; i++) {
      newAssignments.push({
        id: `white_${i}`,
        rollType: 'weiss',
        rollLabel: `Weißes Brötchen ${i + 1}`,
        topping: toppingAssignments[newAssignments.length]?.topping || ''
      });
    }
    // Add seeded roll topping slots
    for (let i = 0; i < seededRolls; i++) {
      newAssignments.push({
        id: `seeded_${i}`,
        rollType: 'koerner',
        rollLabel: `Körnerbrötchen ${i + 1}`,
        topping: toppingAssignments[newAssignments.length]?.topping || ''
      });
    }
    setToppingAssignments(newAssignments);
  }, [whiteRolls, seededRolls]);

  // Update breakfast form data whenever form changes
  useEffect(() => {
    if (totalHalves > 0 && !toppingAssignments.some(a => !a.topping) && onDirectSubmit) {
      const toppings = toppingAssignments.map(assignment => assignment.topping);
      const breakfastData = {
        total_halves: totalHalves,
        white_halves: whiteRolls,
        seeded_halves: seededRolls,
        toppings: toppings,
        has_lunch: hasLunch,
        item_cost: totalCost
      };
      onDirectSubmit(breakfastData);
    } else if (onDirectSubmit) {
      onDirectSubmit(null); // Clear data if form is incomplete
    }
  }, [totalHalves, whiteRolls, seededRolls, toppingAssignments, hasLunch, totalCost, onDirectSubmit]);

  const handleToppingAssignment = (assignmentIndex, toppingType) => {
    setToppingAssignments(prev => {
      const newAssignments = [...prev];
      newAssignments[assignmentIndex] = {
        ...newAssignments[assignmentIndex],
        topping: toppingType
      };
      return newAssignments;
    });
  };

  const handleAddItem = () => {
    if (totalHalves === 0) {
      alert('Bitte wählen Sie mindestens ein Brötchen.');
      return;
    }

    // Check if all toppings are assigned
    const unassignedCount = toppingAssignments.filter(assignment => !assignment.topping).length;
    if (unassignedCount > 0) {
      alert(`Bitte weisen Sie allen ${totalHalves} Brötchenhälften einen Belag zu. ${unassignedCount} fehlen noch.`);
      return;
    }

    // Convert assignments to the expected format
    const toppings = toppingAssignments.map(assignment => assignment.topping);
    
    onAddItem(totalHalves, whiteRolls, seededRolls, toppings, hasLunch, totalCost);
    
    // Reset form
    setWhiteRolls(0);
    setSeededRolls(0);
    setToppingAssignments([]);
    setHasLunch(false);
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Frühstück zusammenstellen</h3>
      
      <div className="space-y-6">
        {/* Step 1: Select Roll Counts */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h4 className="font-semibold mb-4">1. Brötchen Auswahl</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium mb-2">Weiße Brötchen (Hälften)</label>
              <input
                type="number"
                min="0"
                max="20"
                value={whiteRolls}
                onChange={(e) => setWhiteRolls(parseInt(e.target.value) || 0)}
                className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                placeholder="0"
              />
              <span className="text-sm text-gray-600 ml-3">
                à €{whiteRollPrice.toFixed(2)} = €{(whiteRolls * whiteRollPrice).toFixed(2)}
              </span>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Körner Brötchen (Hälften)</label>
              <input
                type="number"
                min="0"
                max="20"
                value={seededRolls}
                onChange={(e) => setSeededRolls(parseInt(e.target.value) || 0)}
                className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                placeholder="0"
              />
              <span className="text-sm text-gray-600 ml-3">
                à €{seededRollPrice.toFixed(2)} = €{(seededRolls * seededRollPrice).toFixed(2)}
              </span>
            </div>
          </div>
          
          <div className="mt-4 p-3 bg-white border border-blue-300 rounded">
            <p className="text-sm font-medium">
              Gesamt: {totalHalves} Brötchenhälften
            </p>
            <p className="text-sm text-gray-600">
              Kosten: €{totalCost.toFixed(2)}
            </p>
          </div>
        </div>

        {/* Step 2: Assign Toppings to Each Roll */}
        {totalHalves > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <h4 className="font-semibold mb-4">2. Beläge zuweisen (kostenlos)</h4>
            <p className="text-sm text-gray-600 mb-4">
              Weisen Sie jedem Brötchen einen Belag zu. Gleiche Beläge können mehrfach verwendet werden.
            </p>
            
            <div className="space-y-3">
              {toppingAssignments.map((assignment, index) => (
                <div key={assignment.id} className="flex items-center gap-4 p-3 bg-white border border-green-300 rounded">
                  <div className="w-40">
                    <span className="text-sm font-medium">{assignment.rollLabel}</span>
                  </div>
                  <div className="flex-1">
                    <select
                      value={assignment.topping}
                      onChange={(e) => handleToppingAssignment(index, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:border-green-500"
                    >
                      <option value="">-- Belag wählen --</option>
                      {toppingsMenu.map((item) => (
                        <option key={item.id} value={item.topping_type}>
                          {toppingLabels[item.topping_type]}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-4 p-3 bg-white border border-green-300 rounded">
              <h5 className="text-sm font-medium mb-2">Belag-Übersicht:</h5>
              <div className="text-xs text-gray-700">
                {Object.entries(
                  toppingAssignments
                    .filter(a => a.topping)
                    .reduce((acc, a) => {
                      acc[a.topping] = (acc[a.topping] || 0) + 1;
                      return acc;
                    }, {})
                ).map(([topping, count]) => (
                  <span key={topping} className="inline-block bg-green-200 px-2 py-1 rounded mr-2 mb-1">
                    {count}x {toppingLabels[topping]}
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Lunch Option */}
        {totalHalves > 0 && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={hasLunch}
                onChange={(e) => setHasLunch(e.target.checked)}
                className="mr-3"
              />
              <span className="text-sm font-medium">Lunch hinzufügen (Preis wird vom Admin festgelegt)</span>
            </label>
          </div>
        )}
      </div>
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

// Employee Profile List Component
const EmployeeProfileList = ({ employees, onClose }) => {
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeProfile, setEmployeeProfile] = useState(null);

  const fetchEmployeeProfile = async (employeeId) => {
    try {
      const response = await axios.get(`${API}/employees/${employeeId}/profile`);
      setEmployeeProfile(response.data);
      setSelectedEmployee(employeeId);
    } catch (error) {
      console.error('Fehler beim Laden des Mitarbeiterprofils:', error);
    }
  };

  if (selectedEmployee && employeeProfile) {
    return (
      <EmployeeProfileDetail
        profile={employeeProfile}
        onBack={() => {
          setSelectedEmployee(null);
          setEmployeeProfile(null);
        }}
        onClose={onClose}
      />
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Mitarbeiter Profile</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {employees.map((employee) => (
              <div
                key={employee.id}
                onClick={() => fetchEmployeeProfile(employee.id)}
                className="bg-white border border-gray-300 rounded-lg p-4 cursor-pointer hover:shadow-lg transition-shadow duration-300"
              >
                <h3 className="text-lg font-semibold mb-2">{employee.name}</h3>
                <div className="text-sm text-gray-600">
                  <p>Frühstück: €{employee.breakfast_balance.toFixed(2)}</p>
                  <p>Getränke/Süßes: €{employee.drinks_sweets_balance.toFixed(2)}</p>
                  <p className="text-blue-600 mt-2">Klicken für Verlauf →</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Employee Profile Detail Component
const EmployeeProfileDetail = ({ profile, onBack, onClose }) => {
  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getOrderTypeLabel = (orderType) => {
    switch (orderType) {
      case 'breakfast': return 'Frühstück';
      case 'drinks': return 'Getränke';
      case 'sweets': return 'Süßes';
      default: return orderType;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ← Zurück
              </button>
              <h2 className="text-2xl font-bold">{profile.employee.name} - Profil</h2>
            </div>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6">
          {/* Summary Stats */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800">Frühstück Saldo</h3>
              <p className="text-2xl font-bold text-blue-600">€{profile.breakfast_total.toFixed(2)}</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800">Getränke/Süßes Saldo</h3>
              <p className="text-2xl font-bold text-green-600">€{profile.drinks_sweets_total.toFixed(2)}</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="font-semibold text-purple-800">Gesamt Bestellungen</h3>
              <p className="text-2xl font-bold text-purple-600">{profile.total_orders}</p>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h3 className="font-semibold text-orange-800">Gesamt Schulden</h3>
              <p className="text-2xl font-bold text-orange-600">€{(profile.breakfast_total + profile.drinks_sweets_total).toFixed(2)}</p>
            </div>
          </div>

          {/* Order History */}
          <div>
            <h3 className="text-xl font-semibold mb-4">Bestellverlauf</h3>
            {profile.order_history.length === 0 ? (
              <p className="text-gray-600">Keine Bestellungen vorhanden</p>
            ) : (
              <div className="space-y-4">
                {profile.order_history.map((order, index) => (
                  <div key={order.id || index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <span className="inline-block bg-blue-100 text-blue-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded">
                          {getOrderTypeLabel(order.order_type)}
                        </span>
                        <span className="text-sm text-gray-600">{formatDate(order.timestamp)}</span>
                      </div>
                      <div className="text-right">
                        <p className="font-semibold">€{order.total_price.toFixed(2)}</p>
                      </div>
                    </div>
                    
                    {order.readable_items && order.readable_items.length > 0 && (
                      <div className="space-y-1">
                        {order.readable_items.map((item, idx) => (
                          <div key={idx} className="text-sm">
                            <span className="font-medium">{item.description}</span>
                            {item.toppings && <span className="text-gray-600"> mit {item.toppings}</span>}
                            {item.unit_price && <span className="text-gray-600"> ({item.unit_price} pro Stück)</span>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Department Admin Dashboard
const DepartmentAdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('employees');
  const [employees, setEmployees] = useState([]);
  const [breakfastMenu, setBreakfastMenu] = useState([]);
  const [toppingsMenu, setToppingsMenu] = useState([]);
  const [drinksMenu, setDrinksMenu] = useState([]);
  const [sweetsMenu, setSweetsMenu] = useState([]);
  const [showNewEmployee, setShowNewEmployee] = useState(false);
  const [showNewDrink, setShowNewDrink] = useState(false);
  const [showNewSweet, setShowNewSweet] = useState(false);
  const { currentDepartment, logout, setAuthState } = React.useContext(AuthContext);

  const goBackToEmployeeDashboard = () => {
    // Set auth state to employee mode for this department
    setAuthState({
      isAuthenticated: true,
      currentDepartment: {
        department_id: currentDepartment.department_id,
        department_name: currentDepartment.department_name,
        role: 'employee'
      },
      isDepartmentAdmin: false
    });
  };

  useEffect(() => {
    if (currentDepartment) {
      fetchEmployees();
      fetchMenus();
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

  const updatePrice = async (category, itemId, newPrice) => {
    try {
      await axios.put(`${API}/department-admin/menu/${category}/${itemId}`, {
        price: parseFloat(newPrice)
      });
      fetchMenus();
      alert('Preis erfolgreich aktualisiert');
    } catch (error) {
      console.error('Fehler beim Aktualisieren des Preises:', error);
      alert('Fehler beim Aktualisieren des Preises');
    }
  };

  const createMenuItem = async (category, nameOrType, price) => {
    try {
      let requestData;
      
      if (category === 'breakfast') {
        requestData = { roll_type: nameOrType, price: parseFloat(price) };
      } else if (category === 'toppings') {
        requestData = { topping_type: nameOrType, price: parseFloat(price) };
      } else {
        // For drinks and sweets
        requestData = { name: nameOrType, price: parseFloat(price) };
      }

      await axios.post(`${API}/department-admin/menu/${category}`, requestData);
      fetchMenus();
      
      // Close appropriate modals
      if (category === 'drinks') setShowNewDrink(false);
      if (category === 'sweets') setShowNewSweet(false);
      
      alert('Artikel erfolgreich erstellt');
    } catch (error) {
      console.error('Fehler beim Erstellen des Artikels:', error);
      alert('Fehler beim Erstellen des Artikels');
    }
  };

  const deleteMenuItem = async (category, itemId) => {
    if (window.confirm('Artikel wirklich löschen?')) {
      try {
        await axios.delete(`${API}/department-admin/menu/${category}/${itemId}`);
        fetchMenus();
        alert('Artikel erfolgreich gelöscht');
      } catch (error) {
        console.error('Fehler beim Löschen des Artikels:', error);
        alert('Fehler beim Löschen des Artikels');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 sm:p-6 md:p-8 lg:p-12">
      <div className="max-w-7xl mx-auto">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 sm:mb-8 lg:mb-12 gap-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center gap-2 sm:gap-4 w-full sm:w-auto">
            <button
              onClick={goBackToEmployeeDashboard}
              className="bg-gray-600 text-white px-3 sm:px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors text-sm sm:text-base whitespace-nowrap"
            >
              ← Zurück zum Mitarbeiter-Dashboard
            </button>
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-gray-800 mt-2 sm:mt-0">
              {currentDepartment.department_name} - Admin
            </h1>
          </div>
          <button
            onClick={logout}
            className="bg-red-600 text-white px-3 sm:px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm sm:text-base whitespace-nowrap self-start sm:self-center"
          >
            Abmelden
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="flex flex-wrap mb-6 gap-1 sm:gap-2">
          {[
            { id: 'employees', label: 'Mitarbeiter' },
            { id: 'menu-management', label: 'Menü & Preise' },
            { id: 'lunch', label: 'Lunch verwalten' },
            { id: 'breakfast-history', label: 'Frühstück Verlauf' },
            { id: 'settings', label: 'Einstellungen' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 sm:px-4 lg:px-6 py-2 sm:py-3 rounded-t-lg text-xs sm:text-sm lg:text-base whitespace-nowrap ${
                activeTab === tab.id
                  ? 'bg-white border-t border-l border-r text-blue-600 font-semibold'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="bg-white rounded-lg shadow-lg p-4 sm:p-6 lg:p-8 min-h-96">
          {activeTab === 'employees' && (
            <EmployeeManagementTab 
              employees={employees}
              onCreateEmployee={handleCreateEmployee}
              showNewEmployee={showNewEmployee}
              setShowNewEmployee={setShowNewEmployee}
              currentDepartment={currentDepartment}
              onEmployeeUpdate={fetchEmployees}
            />
          )}

          {activeTab === 'menu-management' && (
            <UnifiedMenuManagementTab 
              breakfastMenu={breakfastMenu}
              toppingsMenu={toppingsMenu}
              drinksMenu={drinksMenu}
              sweetsMenu={sweetsMenu}
              onUpdatePrice={updatePrice}
              onCreateMenuItem={createMenuItem}
              onDeleteMenuItem={deleteMenuItem}
              fetchMenus={fetchMenus}
            />
          )}

          {activeTab === 'lunch' && (
            <LunchManagementTab />
          )}

          {activeTab === 'breakfast-history' && (
            <BreakfastHistoryTab currentDepartment={currentDepartment} />
          )}

          {activeTab === 'settings' && (
            <AdminSettingsTab currentDepartment={currentDepartment} />
          )}
        </div>

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

// Employee Orders Management Modal
const EmployeeOrdersModal = ({ employee, onClose, currentDepartment, onOrderUpdate }) => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEmployeeOrders();
  }, [employee.id]);

  const fetchEmployeeOrders = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/employees/${employee.id}/orders`);
      setOrders(response.data.orders || []);
    } catch (error) {
      console.error('Fehler beim Laden der Bestellungen:', error);
      setOrders([]);
    } finally {
      setLoading(false);
    }
  };

  const deleteOrder = async (orderId) => {
    if (window.confirm('Bestellung wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.')) {
      try {
        await axios.delete(`${API}/department-admin/orders/${orderId}`);
        alert('Bestellung erfolgreich gelöscht');
        fetchEmployeeOrders();
        if (onOrderUpdate) {
          onOrderUpdate();
        }
      } catch (error) {
        console.error('Fehler beim Löschen der Bestellung:', error);
        alert('Fehler beim Löschen der Bestellung');
      }
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatOrderDetails = (order) => {
    if (order.order_type === 'breakfast' && order.breakfast_items) {
      return order.breakfast_items.map(item => {
        const whiteHalves = item.white_halves || 0;
        const seededHalves = item.seeded_halves || 0;
        const toppings = item.toppings || [];
        const hasLunch = item.has_lunch ? ' + Lunch' : '';
        
        return `${whiteHalves}x Weiße, ${seededHalves}x Körner${toppings.length > 0 ? ', Beläge: ' + toppings.join(', ') : ''}${hasLunch}`;
      }).join('; ');
    } else if (order.order_type === 'drinks') {
      return Object.entries(order.drink_items || {}).map(([drink, qty]) => `${qty}x ${drink}`).join(', ');
    } else if (order.order_type === 'sweets') {
      return Object.entries(order.sweet_items || {}).map(([sweet, qty]) => `${qty}x ${sweet}`).join(', ');
    }
    return 'Unbekannte Bestellung';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Bestellungen verwalten: {employee.name}</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          </div>
        </div>
        
        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="text-lg text-gray-600">Lade Bestellungen...</div>
            </div>
          ) : orders.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <p>Keine Bestellungen für diesen Mitarbeiter gefunden.</p>
            </div>
          ) : (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold mb-4">
                Alle Bestellungen ({orders.length})
              </h3>
              
              {/* Orders List */}
              <div className="space-y-3">
                {orders.map((order) => (
                  <div key={order.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-4 mb-2">
                          <span className="font-semibold text-lg">
                            {order.order_type === 'breakfast' ? 'Frühstück' : 
                             order.order_type === 'drinks' ? 'Getränke' : 'Süßes'}
                          </span>
                          <span className="text-sm text-gray-500">
                            {formatDate(order.timestamp)}
                          </span>
                          <span className="bg-green-100 text-green-800 text-sm px-2 py-1 rounded">
                            €{order.total_price.toFixed(2)}
                          </span>
                        </div>
                        <div className="text-gray-700 mb-2">
                          <strong>Details:</strong> {formatOrderDetails(order)}
                        </div>
                      </div>
                      
                      <div className="flex gap-2 ml-4">
                        <button
                          onClick={() => deleteOrder(order.id)}
                          className="bg-red-600 text-white px-3 py-1 rounded text-sm hover:bg-red-700"
                        >
                          Löschen
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Employee Management Tab Component
const EmployeeManagementTab = ({ employees, onCreateEmployee, showNewEmployee, setShowNewEmployee, currentDepartment, onEmployeeUpdate }) => {
  const [showOrdersModal, setShowOrdersModal] = useState(false);
  const [selectedEmployeeForOrders, setSelectedEmployeeForOrders] = useState(null);
  
  const markAsPaid = async (employee, balanceType) => {
    const balanceAmount = balanceType === 'breakfast' ? employee.breakfast_balance : employee.drinks_sweets_balance;
    const balanceLabel = balanceType === 'breakfast' ? 'Frühstück' : 'Getränke/Süßes';
    
    if (balanceAmount <= 0) {
      alert('Kein Saldo zum Zurücksetzen vorhanden');
      return;
    }
    
    if (window.confirm(`${balanceLabel}-Saldo von €${balanceAmount.toFixed(2)} für ${employee.name} als bezahlt markieren?`)) {
      try {
        await axios.post(`${API}/department-admin/payment/${employee.id}?payment_type=${balanceType}&amount=${balanceAmount}&admin_department=${currentDepartment.department_name}`);
        alert('Zahlung erfolgreich verbucht');
        // Refresh employee data instead of full page reload
        if (onEmployeeUpdate) {
          onEmployeeUpdate();
        }
      } catch (error) {
        console.error('Fehler beim Verbuchen der Zahlung:', error);
        alert('Fehler beim Verbuchen der Zahlung');
      }
    }
  };

  const deleteEmployee = async (employee) => {
    if (window.confirm(`Mitarbeiter ${employee.name} wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden und löscht auch alle Bestellungen des Mitarbeiters.`)) {
      try {
        await axios.delete(`${API}/department-admin/employees/${employee.id}`);
        alert('Mitarbeiter erfolgreich gelöscht');
        // Refresh employee data instead of full page reload
        if (onEmployeeUpdate) {
          onEmployeeUpdate();
        }
      } catch (error) {
        console.error('Fehler beim Löschen des Mitarbeiters:', error);
        alert('Fehler beim Löschen des Mitarbeiters');
      }
    }
  };

  const viewEmployeeOrders = (employee) => {
    setSelectedEmployeeForOrders(employee);
    setShowOrdersModal(true);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold">Mitarbeiter verwalten</h3>
        <button
          onClick={() => setShowNewEmployee(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Neuer Mitarbeiter
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {employees.map((employee) => (
          <div key={employee.id} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-lg mb-3">{employee.name}</h4>
            
            {/* Breakfast Balance */}
            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Frühstück:</span>
                <span className="font-bold text-blue-600">€{employee.breakfast_balance.toFixed(2)}</span>
              </div>
              {employee.breakfast_balance > 0 && (
                <button
                  onClick={() => markAsPaid(employee, 'breakfast')}
                  className="w-full bg-blue-600 text-white text-xs py-1 px-2 rounded hover:bg-blue-700"
                >
                  Als bezahlt markieren
                </button>
              )}
            </div>
            
            {/* Drinks/Sweets Balance */}
            <div className="mb-3 p-3 bg-green-50 border border-green-200 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Getränke/Süßes:</span>
                <span className="font-bold text-green-600">€{employee.drinks_sweets_balance.toFixed(2)}</span>
              </div>
              {employee.drinks_sweets_balance > 0 && (
                <button
                  onClick={() => markAsPaid(employee, 'drinks_sweets')}
                  className="w-full bg-green-600 text-white text-xs py-1 px-2 rounded hover:bg-green-700"
                >
                  Als bezahlt markieren
                </button>
              )}
            </div>
            
            {/* Delete Button */}
            <div className="mt-3">
              <button
                onClick={() => deleteEmployee(employee)}
                className="w-full bg-red-600 text-white text-xs py-2 px-2 rounded hover:bg-red-700"
              >
                Mitarbeiter löschen
              </button>
            </div>

            {/* Order Management Button */}
            <div className="mt-2">
              <button
                onClick={() => viewEmployeeOrders(employee)}
                className="w-full bg-green-600 text-white text-xs py-2 px-2 rounded hover:bg-green-700"
              >
                Bestellungen verwalten
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Employee Orders Management Modal */}
      {showOrdersModal && selectedEmployeeForOrders && (
        <EmployeeOrdersModal
          employee={selectedEmployeeForOrders}
          onClose={() => {
            setShowOrdersModal(false);
            setSelectedEmployeeForOrders(null);
          }}
          currentDepartment={currentDepartment}
          onOrderUpdate={onEmployeeUpdate}
        />
      )}
    </div>
  );
};

// Price Management Tab Component
const PriceManagementTab = ({ breakfastMenu, toppingsMenu, drinksMenu, sweetsMenu, onUpdatePrice }) => {
  const rollTypeLabels = {
    'weiss': 'Weißes Brötchen',
    'koerner': 'Körnerbrötchen'
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

  const updateItemPrice = (category, itemId, currentPrice) => {
    const newPrice = prompt('Neuer Preis (€):', currentPrice.toFixed(2));
    if (newPrice && !isNaN(parseFloat(newPrice))) {
      onUpdatePrice(category, itemId, newPrice);
    }
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-6">Preise verwalten</h3>

      <div className="space-y-8">
        {/* Breakfast Items */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-700">Brötchen</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {breakfastMenu.map((item) => (
              <div key={item.id} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{rollTypeLabels[item.roll_type]}</span>
                  <button
                    onClick={() => updateItemPrice('breakfast', item.id, item.price)}
                    className="text-blue-600 hover:text-blue-800 font-semibold"
                  >
                    €{item.price.toFixed(2)}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Toppings */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-700">Beläge</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {toppingsMenu.map((item) => (
              <div key={item.id} className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{toppingLabels[item.topping_type]}</span>
                  <button
                    onClick={() => updateItemPrice('toppings', item.id, item.price)}
                    className="text-green-600 hover:text-green-800 font-semibold"
                  >
                    €{item.price.toFixed(2)}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Drinks */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-700">Getränke</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {drinksMenu.map((item) => (
              <div key={item.id} className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{item.name}</span>
                  <button
                    onClick={() => updateItemPrice('drinks', item.id, item.price)}
                    className="text-purple-600 hover:text-purple-800 font-semibold"
                  >
                    €{item.price.toFixed(2)}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sweets */}
        <div>
          <h4 className="text-md font-semibold mb-3 text-gray-700">Süßwaren</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sweetsMenu.map((item) => (
              <div key={item.id} className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{item.name}</span>
                  <button
                    onClick={() => updateItemPrice('sweets', item.id, item.price)}
                    className="text-orange-600 hover:text-orange-800 font-semibold"
                  >
                    €{item.price.toFixed(2)}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Menu Management Tab Component  
const MenuManagementTab = ({ drinksMenu, sweetsMenu, onCreateMenuItem, onDeleteMenuItem, showNewDrink, setShowNewDrink, showNewSweet, setShowNewSweet }) => {
  return (
    <div>
      <h3 className="text-lg font-semibold mb-6">Menü verwalten</h3>

      <div className="space-y-8">
        {/* Drinks Management */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-md font-semibold text-gray-700">Getränke</h4>
            <button
              onClick={() => setShowNewDrink(true)}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
            >
              Neues Getränk
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {drinksMenu.map((item) => (
              <div key={item.id} className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-medium">{item.name}</span>
                    <p className="text-sm text-gray-600">€{item.price.toFixed(2)}</p>
                  </div>
                  <button
                    onClick={() => onDeleteMenuItem('drinks', item.id)}
                    className="text-red-600 hover:text-red-800 font-semibold"
                  >
                    Löschen
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Sweets Management */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-md font-semibold text-gray-700">Süßwaren</h4>
            <button
              onClick={() => setShowNewSweet(true)}
              className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
            >
              Neue Süßware
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sweetsMenu.map((item) => (
              <div key={item.id} className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                <div className="flex justify-between items-center">
                  <div>
                    <span className="font-medium">{item.name}</span>
                    <p className="text-sm text-gray-600">€{item.price.toFixed(2)}</p>
                  </div>
                  <button
                    onClick={() => onDeleteMenuItem('sweets', item.id)}
                    className="text-red-600 hover:text-red-800 font-semibold"
                  >
                    Löschen
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* New Item Modals */}
      {showNewDrink && (
        <NewMenuItemModal
          title="Neues Getränk hinzufügen"
          onCreateItem={(name, price) => onCreateMenuItem('drinks', name, price)}
          onClose={() => setShowNewDrink(false)}
        />
      )}

      {showNewSweet && (
        <NewMenuItemModal
          title="Neue Süßware hinzufügen"
          onCreateItem={(name, price) => onCreateMenuItem('sweets', name, price)}
          onClose={() => setShowNewSweet(false)}
        />
      )}
    </div>
  );
};

// New Menu Item Modal
const NewMenuItemModal = ({ title, onCreateItem, onClose }) => {
  const [name, setName] = useState('');
  const [price, setPrice] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (name.trim() && price && !isNaN(parseFloat(price))) {
      onCreateItem(name.trim(), price);
      setName('');
      setPrice('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">{title}</h2>
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
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Preis (€)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
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

// New Breakfast Item Modal
const NewBreakfastItemModal = ({ title, onCreateItem, onClose }) => {
  const [rollType, setRollType] = useState('');
  const [price, setPrice] = useState('');

  const rollTypeOptions = [
    { value: 'weiss', label: 'Weißes Brötchen' },
    { value: 'koerner', label: 'Körnerbrötchen' }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (rollType && price && !isNaN(parseFloat(price))) {
      onCreateItem(rollType, price);
      setRollType('');
      setPrice('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">{title}</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Brötchen-Typ</label>
            <select
              value={rollType}
              onChange={(e) => setRollType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            >
              <option value="">-- Brötchen-Typ wählen --</option>
              {rollTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Preis (€)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
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

// New Topping Item Modal
const NewToppingItemModal = ({ title, onCreateItem, onClose }) => {
  const [toppingType, setToppingType] = useState('');
  const [price, setPrice] = useState('');

  const toppingTypeOptions = [
    { value: 'ruehrei', label: 'Rührei' },
    { value: 'spiegelei', label: 'Spiegelei' },
    { value: 'eiersalat', label: 'Eiersalat' },
    { value: 'salami', label: 'Salami' },
    { value: 'schinken', label: 'Schinken' },
    { value: 'kaese', label: 'Käse' },
    { value: 'butter', label: 'Butter' }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (toppingType && price && !isNaN(parseFloat(price))) {
      onCreateItem(toppingType, price);
      setToppingType('');
      setPrice('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">{title}</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Belag-Typ</label>
            <select
              value={toppingType}
              onChange={(e) => setToppingType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            >
              <option value="">-- Belag-Typ wählen --</option>
              {toppingTypeOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Preis (€)</label>
            <input
              type="number"
              step="0.01"
              min="0"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          <div className="flex gap-4">
            <button
              type="submit"
              className="flex-1 bg-green-600 text-white py-2 rounded-lg hover:bg-green-700"
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
  const [allEmployees, setAllEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showEmployeeProfile, setShowEmployeeProfile] = useState(false);
  const [lunchSettings, setLunchSettings] = useState({ price: 0.0, enabled: true });
  const { logout } = React.useContext(AuthContext);

  useEffect(() => {
    fetchAllEmployees();
    fetchLunchSettings();
  }, []);

  const fetchAllEmployees = async () => {
    try {
      // Fetch employees from all departments
      const deptResponse = await axios.get(`${API}/departments`);
      const departments = deptResponse.data;
      
      let allEmps = [];
      for (const dept of departments) {
        const empResponse = await axios.get(`${API}/departments/${dept.id}/employees`);
        const deptEmployees = empResponse.data.map(emp => ({
          ...emp,
          department_name: dept.name
        }));
        allEmps = [...allEmps, ...deptEmployees];
      }
      setAllEmployees(allEmps);
    } catch (error) {
      console.error('Fehler beim Laden der Mitarbeiter:', error);
    }
  };

  const fetchLunchSettings = async () => {
    try {
      const response = await axios.get(`${API}/lunch-settings`);
      setLunchSettings(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Lunch-Einstellungen:', error);
    }
  };

  const updateLunchPrice = async (newPrice) => {
    try {
      await axios.put(`${API}/lunch-settings?price=${newPrice}`);
      setLunchSettings(prev => ({ ...prev, price: newPrice }));
      alert('Lunch-Preis erfolgreich aktualisiert');
    } catch (error) {
      console.error('Fehler beim Aktualisieren des Lunch-Preises:', error);
      alert('Fehler beim Aktualisieren des Preises');
    }
  };

  const handleEmployeeClick = (employee) => {
    setSelectedEmployee(employee);
    setShowEmployeeProfile(true);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Admin Dashboard - Mitarbeiter Profile</h1>
          <button
            onClick={logout}
            className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700"
          >
            Abmelden
          </button>
        </div>

        {/* Lunch Price Management */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Lunch-Preis Verwaltung</h2>
          <div className="flex items-center gap-4">
            <span>Aktueller Preis: €{lunchSettings.price.toFixed(2)}</span>
            <button
              onClick={() => {
                const newPrice = prompt('Neuer Lunch-Preis (€):', lunchSettings.price.toFixed(2));
                if (newPrice && !isNaN(parseFloat(newPrice))) {
                  updateLunchPrice(parseFloat(newPrice));
                }
              }}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Preis ändern
            </button>
          </div>
        </div>
        
        {/* All Employees Overview */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-semibold mb-6">Alle Mitarbeiter</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allEmployees.map((employee) => (
              <div
                key={employee.id}
                onClick={() => handleEmployeeClick(employee)}
                className="bg-gray-50 border border-gray-200 rounded-lg p-4 cursor-pointer hover:shadow-lg transition-shadow duration-300"
              >
                <h3 className="font-semibold text-lg">{employee.name}</h3>
                <p className="text-sm text-gray-600">{employee.department_name}</p>
                <div className="text-sm text-gray-600 mt-2">
                  <p>Frühstück: €{employee.breakfast_balance.toFixed(2)}</p>
                  <p>Getränke/Süßes: €{employee.drinks_sweets_balance.toFixed(2)}</p>
                </div>
                <p className="text-blue-600 text-sm mt-2">Klicken für Verlauf →</p>
              </div>
            ))}
          </div>
        </div>

        {/* Employee Profile with Admin Controls */}
        {showEmployeeProfile && selectedEmployee && (
          <AdminEmployeeProfile
            employee={selectedEmployee}
            onClose={() => {
              setShowEmployeeProfile(false);
              setSelectedEmployee(null);
            }}
            onRefresh={fetchAllEmployees}
          />
        )}
      </div>
    </div>
  );
};

// Admin Employee Profile Component with Edit/Delete capabilities
const AdminEmployeeProfile = ({ employee, onClose, onRefresh }) => {
  const [employeeProfile, setEmployeeProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchEmployeeProfile();
  }, [employee.id]);

  const fetchEmployeeProfile = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/employees/${employee.id}/profile`);
      setEmployeeProfile(response.data);
    } catch (error) {
      console.error('Fehler beim Laden des Mitarbeiterprofils:', error);
      alert('Fehler beim Laden des Profils');
    } finally {
      setIsLoading(false);
    }
  };

  const deleteOrder = async (orderId) => {
    if (window.confirm('Bestellung wirklich löschen?')) {
      try {
        await axios.delete(`${API}/orders/${orderId}`);
        alert('Bestellung erfolgreich gelöscht');
        fetchEmployeeProfile(); // Refresh profile
        onRefresh(); // Refresh parent employee list
      } catch (error) {
        console.error('Fehler beim Löschen der Bestellung:', error);
        alert('Fehler beim Löschen der Bestellung');
      }
    }
  };

  const deleteEmployee = async () => {
    if (window.confirm(`Mitarbeiter ${employee.name} wirklich löschen? Alle Bestellungen werden ebenfalls gelöscht.`)) {
      try {
        await axios.delete(`${API}/department-admin/employees/${employee.id}`);
        alert('Mitarbeiter erfolgreich gelöscht');
        onRefresh();
        onClose();
      } catch (error) {
        console.error('Fehler beim Löschen des Mitarbeiters:', error);
        alert('Fehler beim Löschen des Mitarbeiters');
      }
    }
  };

  const resetBalance = async (balanceType) => {
    if (window.confirm(`${balanceType === 'breakfast' ? 'Frühstück' : 'Getränke/Süßes'}-Saldo wirklich zurücksetzen?`)) {
      try {
        await axios.post(`${API}/admin/reset-balance/${employee.id}?balance_type=${balanceType}`);
        alert('Saldo erfolgreich zurückgesetzt');
        fetchEmployeeProfile();
        onRefresh();
      } catch (error) {
        console.error('Fehler beim Zurücksetzen des Saldos:', error);
        alert('Fehler beim Zurücksetzen des Saldos');
      }
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getOrderTypeLabel = (orderType) => {
    switch (orderType) {
      case 'breakfast': return 'Frühstück';
      case 'drinks': return 'Getränke';
      case 'sweets': return 'Süßes';
      default: return orderType;
    }
  };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Lade Profile...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!employeeProfile) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <p>Fehler beim Laden des Profils</p>
          <button onClick={onClose} className="mt-4 bg-red-600 text-white px-4 py-2 rounded">
            Schließen
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">
              {employeeProfile.employee.name} - Admin Verlauf ({employee.department_name})
            </h2>
            <div className="flex gap-2">
              <button
                onClick={deleteEmployee}
                className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
              >
                Mitarbeiter löschen
              </button>
              <button
                onClick={onClose}
                className="text-gray-500 hover:text-gray-700 text-xl"
              >
                ×
              </button>
            </div>
          </div>
        </div>

        <div className="p-6">
          {/* Summary Stats with Admin Controls */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-semibold text-blue-800">Frühstück Saldo</h3>
              <p className="text-2xl font-bold text-blue-600">€{employeeProfile.breakfast_total.toFixed(2)}</p>
              <button
                onClick={() => resetBalance('breakfast')}
                className="mt-2 text-sm bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
              >
                Zurücksetzen
              </button>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800">Getränke/Süßes Saldo</h3>
              <p className="text-2xl font-bold text-green-600">€{employeeProfile.drinks_sweets_total.toFixed(2)}</p>
              <button
                onClick={() => resetBalance('drinks_sweets')}
                className="mt-2 text-sm bg-green-600 text-white px-2 py-1 rounded hover:bg-green-700"
              >
                Zurücksetzen
              </button>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="font-semibold text-purple-800">Gesamt Bestellungen</h3>
              <p className="text-2xl font-bold text-purple-600">{employeeProfile.total_orders}</p>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h3 className="font-semibold text-orange-800">Gesamt Schulden</h3>
              <p className="text-2xl font-bold text-orange-600">€{(employeeProfile.breakfast_total + employeeProfile.drinks_sweets_total).toFixed(2)}</p>
            </div>
          </div>

          {/* Order History with Admin Controls */}
          <div>
            <h3 className="text-xl font-semibold mb-4">Bestellverlauf (Admin kann bearbeiten)</h3>
            {employeeProfile.order_history.length === 0 ? (
              <p className="text-gray-600 text-center py-8">Keine Bestellungen vorhanden</p>
            ) : (
              <div className="space-y-4">
                {employeeProfile.order_history.map((order, index) => (
                  <div key={order.id || index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <span className="inline-block bg-blue-100 text-blue-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded">
                          {getOrderTypeLabel(order.order_type)}
                        </span>
                        <span className="text-sm text-gray-600">{formatDate(order.timestamp)}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold">€{order.total_price.toFixed(2)}</p>
                        <button
                          onClick={() => deleteOrder(order.id)}
                          className="bg-red-500 text-white px-2 py-1 text-xs rounded hover:bg-red-600"
                        >
                          Löschen
                        </button>
                      </div>
                    </div>
                    
                    {order.readable_items && order.readable_items.length > 0 && (
                      <div className="space-y-1">
                        {order.readable_items.map((item, idx) => (
                          <div key={idx} className="text-sm">
                            <span className="font-medium">{item.description}</span>
                            {item.toppings && <span className="text-gray-600"> mit {item.toppings}</span>}
                            {item.unit_price && <span className="text-gray-600"> ({item.unit_price} pro Stück)</span>}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Breakfast Summary Table Component
const BreakfastSummaryTable = ({ departmentId, onClose }) => {
  const [dailySummary, setDailySummary] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [toppingsMenu, setToppingsMenu] = useState([]);

  useEffect(() => {
    fetchDailySummary();
    fetchToppingsMenu();
  }, [departmentId]);

  const fetchToppingsMenu = async () => {
    try {
      const response = await axios.get(`${API}/menu/toppings`);
      setToppingsMenu(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Beläge:', error);
    }
  };

  const fetchDailySummary = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API}/orders/daily-summary/${departmentId}`);
      setDailySummary(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Tagesübersicht:', error);
      alert('Fehler beim Laden der Übersicht');
    } finally {
      setIsLoading(false);
    }
  };

  const rollTypeLabels = {
    'weiss': 'Weißes Brötchen',
    'koerner': 'Körnerbrötchen'
  };

  // Use dynamic labels from menu if available, otherwise fall back to defaults
  const defaultLabels = {
    'ruehrei': 'Rührei',
    'spiegelei': 'Spiegelei',
    'eiersalat': 'Eiersalat',
    'salami': 'Salami',
    'schinken': 'Schinken',
    'kaese': 'Käse',
    'butter': 'Butter'
  };
  
  const toppingLabels = {};
  toppingsMenu.forEach(item => {
    // Ensure we always get a string value
    const customName = item.name;
    const fallbackName = defaultLabels[item.topping_type];
    const finalName = customName || fallbackName || item.topping_type;
    
    // Make sure the final value is a string and not an object
    toppingLabels[item.topping_type] = typeof finalName === 'string' ? finalName : String(finalName);
  });

  // Fallback toppings if menu is empty or missing items
  const finalToppingLabels = { ...defaultLabels, ...toppingLabels };

  if (isLoading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p>Lade Frühstück Übersicht...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Frühstück Tagesübersicht - {dailySummary?.date}</h2>
            <button
              onClick={onClose}
              className="text-gray-500 hover:text-gray-700 text-xl"
            >
              ×
            </button>
          </div>
        </div>

        <div className="p-6">
          {dailySummary && dailySummary.shopping_list && Object.keys(dailySummary.shopping_list).length > 0 ? (
            <div>
              {/* Shopping List Summary */}
              <div className="mb-8 bg-green-50 border border-green-200 rounded-lg p-6">
                <h3 className="text-xl font-semibold mb-4 text-green-800">🛒 Einkaufsliste</h3>
                
                <div className="text-lg font-bold text-green-700 mb-4">
                  {Object.entries(dailySummary.shopping_list).map(([rollType, data]) => {
                    const rollLabel = String(rollTypeLabels[rollType] || rollType);
                    const wholeRolls = String(data.whole_rolls || 0);
                    return `${wholeRolls} ${rollLabel.replace(' Brötchen', '')}`;
                  }).join(', ')}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  {Object.entries(dailySummary.shopping_list).map(([rollType, data]) => (
                    <div key={rollType} className="bg-white border border-green-300 rounded p-3">
                      <div className="font-semibold">{String(rollTypeLabels[rollType] || rollType)}</div>
                      <div className="text-gray-600">
                        {String(data.halves || 0)} Hälften → {String(data.whole_rolls || 0)} ganze Brötchen
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Total Toppings Summary */}
              {dailySummary.total_toppings && Object.keys(dailySummary.total_toppings).length > 0 && (
                <div className="mb-8 bg-orange-50 border border-orange-200 rounded-lg p-6">
                  <h3 className="text-lg font-semibold mb-4 text-orange-800">🥪 Gesamt Beläge</h3>
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                    {Object.entries(dailySummary.total_toppings).map(([topping, count]) => (
                      <div key={topping} className="bg-white border border-orange-300 rounded p-3 text-center">
                        <div className="font-semibold text-orange-700">{String(count)}x</div>
                        <div className="text-sm">{String(finalToppingLabels[topping] || topping)}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Detailed Employee Orders */}
              <h3 className="text-lg font-semibold mb-4">Detaillierte Mitarbeiter-Bestellungen</h3>
              
              {/* Employee Orders Table */}
              {dailySummary.employee_orders && Object.keys(dailySummary.employee_orders).length > 0 ? (
                <div className="overflow-x-auto mb-8">
                  <table className="w-full border-collapse border border-gray-300 mb-6">
                    <thead>
                      <tr className="bg-blue-100">
                        <th className="border border-gray-300 px-4 py-2 text-left">Mitarbeiter Name</th>
                        <th className="border border-gray-300 px-4 py-2 text-center">Weiße Hälften</th>
                        <th className="border border-gray-300 px-4 py-2 text-center">Körner Hälften</th>
                        <th className="border border-gray-300 px-4 py-2 text-left">Beläge</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(dailySummary.employee_orders).map(([employeeName, employeeData]) => (
                        <tr key={employeeName} className="hover:bg-gray-50">
                          <td className="border border-gray-300 px-4 py-2 font-semibold">
                            {String(employeeName)}
                          </td>
                          <td className="border border-gray-300 px-4 py-2 text-center font-bold text-blue-600">
                            {String(employeeData.white_halves || 0)}
                          </td>
                          <td className="border border-gray-300 px-4 py-2 text-center font-bold text-orange-600">
                            {String(employeeData.seeded_halves || 0)}
                          </td>
                          <td className="border border-gray-300 px-4 py-2">
                            {Object.keys(employeeData.toppings).length > 0 ? (
                              <div className="flex flex-wrap gap-1">
                                {Object.entries(employeeData.toppings).map(([topping, count]) => (
                                  <span key={topping} className="bg-gray-100 px-2 py-1 rounded text-xs">
                                    {String(count)}x {String(finalToppingLabels[topping] || topping)}
                                  </span>
                                ))}
                              </div>
                            ) : (
                              <span className="text-gray-500 italic">Keine Beläge</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-4 mb-8 text-gray-500">
                  Keine Mitarbeiter-Bestellungen für heute
                </div>
              )}

              {/* Summary Table (only once at bottom) */}
              <h4 className="text-md font-semibold mb-4">Gesamtübersicht für Einkauf</h4>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse border border-gray-300">
                  <thead>
                    <tr className="bg-gray-100">
                      <th className="border border-gray-300 px-4 py-2 text-left">Brötchen Art</th>
                      <th className="border border-gray-300 px-4 py-2 text-center">Hälften</th>
                      <th className="border border-gray-300 px-4 py-2 text-center">Ganze Brötchen</th>
                      <th className="border border-gray-300 px-4 py-2 text-left">Beläge (Anzahl)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(dailySummary.breakfast_summary).map(([rollType, data]) => (
                      <tr key={rollType} className="hover:bg-gray-50">
                        <td className="border border-gray-300 px-4 py-2 font-semibold">
                          {String(rollTypeLabels[rollType] || rollType)}
                        </td>
                        <td className="border border-gray-300 px-4 py-2 text-center font-bold text-blue-600">
                          {String(data.halves || 0)}
                        </td>
                        <td className="border border-gray-300 px-4 py-2 text-center font-bold text-green-600">
                          {String(Math.ceil((data.halves || 0) / 2))}
                        </td>
                        <td className="border border-gray-300 px-4 py-2">
                          {Object.keys(data.toppings).length > 0 ? (
                            <div className="space-y-1">
                              {Object.entries(data.toppings).map(([topping, count]) => (
                                <div key={topping} className="flex justify-between">
                                  <span>{String(finalToppingLabels[topping] || topping)}:</span>
                                  <span className="font-semibold ml-2">{String(count)}x</span>
                                </div>
                              ))}
                            </div>
                          ) : (
                            <span className="text-gray-500 italic">Keine Beläge</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-600 text-lg">Keine Frühstück-Bestellungen für heute</p>
              <p className="text-gray-500">Bestellungen werden hier angezeigt, sobald sie eingehen.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// Lunch Management Tab Component
const LunchManagementTab = () => {
  const [lunchSettings, setLunchSettings] = useState({ price: 0.0, enabled: true });
  const [newPrice, setNewPrice] = useState('');

  useEffect(() => {
    fetchLunchSettings();
  }, []);

  const fetchLunchSettings = async () => {
    try {
      const response = await axios.get(`${API}/lunch-settings`);
      setLunchSettings(response.data);
      setNewPrice(response.data.price.toFixed(2));
    } catch (error) {
      console.error('Fehler beim Laden der Lunch-Einstellungen:', error);
    }
  };

  const updateLunchPrice = async () => {
    if (!newPrice || isNaN(parseFloat(newPrice))) {
      alert('Bitte gültigen Preis eingeben');
      return;
    }

    try {
      await axios.put(`${API}/lunch-settings?price=${parseFloat(newPrice)}`);
      await fetchLunchSettings();
      alert('Lunch-Preis erfolgreich aktualisiert');
    } catch (error) {
      console.error('Fehler beim Aktualisieren des Lunch-Preises:', error);
      alert('Fehler beim Aktualisieren des Preises');
    }
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-6">Lunch Preis verwalten</h3>

      <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
        <div className="mb-6">
          <h4 className="text-md font-semibold mb-3 text-gray-700">Aktueller Lunch-Preis</h4>
          <div className="text-3xl font-bold text-orange-600 mb-4">
            €{lunchSettings.price.toFixed(2)}
          </div>
          <p className="text-sm text-gray-600">
            Dieser Preis wird für alle Mitarbeiter angewendet, die Lunch als Zusatzoption zu ihrem Frühstück wählen.
          </p>
        </div>

        <div className="border-t pt-6">
          <h4 className="text-md font-semibold mb-3 text-gray-700">Preis ändern</h4>
          <div className="flex items-center gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Neuer Preis (€)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                value={newPrice}
                onChange={(e) => setNewPrice(e.target.value)}
                className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                placeholder="0.00"
              />
            </div>
            <div className="flex items-end">
              <button
                onClick={updateLunchPrice}
                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors"
              >
                Preis aktualisieren
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 bg-white border border-orange-300 rounded-lg p-4">
          <h4 className="font-semibold text-orange-800 mb-2">Information</h4>
          <ul className="text-sm text-gray-700 space-y-1">
            <li>• Mitarbeiter können Lunch als Zusatzoption beim Frühstück wählen</li>
            <li>• Der Lunch-Preis wird pro Brötchen berechnet</li>
            <li>• Preisänderungen wirken sich auf neue Bestellungen aus</li>
            <li>• Bereits getätigte Bestellungen behalten ihren ursprünglichen Preis</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// Unified Menu & Price Management Tab Component
const UnifiedMenuManagementTab = ({ breakfastMenu, toppingsMenu, drinksMenu, sweetsMenu, onUpdatePrice, onCreateMenuItem, onDeleteMenuItem, fetchMenus }) => {
  const [showNewDrink, setShowNewDrink] = useState(false);
  const [showNewSweet, setShowNewSweet] = useState(false);
  const [showNewBreakfast, setShowNewBreakfast] = useState(false);
  const [showNewTopping, setShowNewTopping] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', price: '' });

  const rollTypeLabels = {
    'weiss': 'Weißes Brötchen',
    'koerner': 'Körnerbrötchen'
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

  const startEditItem = (item, category) => {
    setEditingItem({ ...item, category });
    let displayName = '';
    
    if (category === 'breakfast') {
      displayName = item.name || rollTypeLabels[item.roll_type];
    } else if (category === 'toppings') {
      displayName = item.name || toppingLabels[item.topping_type];
    } else {
      displayName = item.name;
    }
    
    setEditForm({ 
      name: displayName,
      price: item.price.toString() 
    });
  };

  const saveEdit = async () => {
    if (!editingItem) return;

    try {
      const updateData = {
        name: editForm.name,
        price: parseFloat(editForm.price)
      };
      
      await axios.put(`${API}/department-admin/menu/${editingItem.category}/${editingItem.id}`, updateData);
      
      fetchMenus();
      setEditingItem(null);
      setEditForm({ name: '', price: '' });
      alert('Artikel erfolgreich aktualisiert');
    } catch (error) {
      console.error('Fehler beim Aktualisieren:', error);
      alert('Fehler beim Aktualisieren');
    }
  };

  const cancelEdit = () => {
    setEditingItem(null);
    setEditForm({ name: '', price: '' });
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-6">Menü & Preise verwalten</h3>

      <div className="space-y-8">
        {/* Breakfast Items */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-md font-semibold text-gray-700 border-b pb-2">Brötchen</h4>
            <button
              onClick={() => setShowNewBreakfast(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
            >
              Neues Brötchen
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {breakfastMenu.map((item) => (
              <div key={item.id} className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                {editingItem?.id === item.id ? (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Name</label>
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Preis (€)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={editForm.price}
                        onChange={(e) => setEditForm(prev => ({ ...prev, price: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button onClick={saveEdit} className="bg-green-600 text-white px-3 py-1 rounded text-sm">
                        Speichern
                      </button>
                      <button onClick={cancelEdit} className="bg-gray-500 text-white px-3 py-1 rounded text-sm">
                        Abbrechen
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-medium">{item.name || rollTypeLabels[item.roll_type]}</span>
                      <div className="text-sm text-gray-600">€{item.price.toFixed(2)}</div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEditItem(item, 'breakfast')}
                        className="bg-blue-600 text-white px-2 py-1 rounded text-sm hover:bg-blue-700"
                      >
                        Bearbeiten
                      </button>
                      <button
                        onClick={() => onDeleteMenuItem('breakfast', item.id)}
                        className="bg-red-600 text-white px-2 py-1 rounded text-sm hover:bg-red-700"
                      >
                        Löschen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Toppings */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-md font-semibold text-gray-700 border-b pb-2">Beläge</h4>
            <button
              onClick={() => setShowNewTopping(true)}
              className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700"
            >
              Neuer Belag
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {toppingsMenu.map((item) => (
              <div key={item.id} className="bg-green-50 border border-green-200 rounded-lg p-4">
                {editingItem?.id === item.id ? (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Name</label>
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Preis (€)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={editForm.price}
                        onChange={(e) => setEditForm(prev => ({ ...prev, price: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button onClick={saveEdit} className="bg-green-600 text-white px-3 py-1 rounded text-sm">
                        Speichern
                      </button>
                      <button onClick={cancelEdit} className="bg-gray-500 text-white px-3 py-1 rounded text-sm">
                        Abbrechen
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-medium">{item.name || toppingLabels[item.topping_type]}</span>
                      <div className="text-sm text-gray-600">€{item.price.toFixed(2)}</div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEditItem(item, 'toppings')}
                        className="bg-green-600 text-white px-2 py-1 rounded text-sm hover:bg-green-700"
                      >
                        Bearbeiten
                      </button>
                      <button
                        onClick={() => onDeleteMenuItem('toppings', item.id)}
                        className="bg-red-600 text-white px-2 py-1 rounded text-sm hover:bg-red-700"
                      >
                        Löschen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Drinks */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-md font-semibold text-gray-700 border-b pb-2">Getränke</h4>
            <button
              onClick={() => setShowNewDrink(true)}
              className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700"
            >
              Neues Getränk
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {drinksMenu.map((item) => (
              <div key={item.id} className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                {editingItem?.id === item.id ? (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Name</label>
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Preis (€)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={editForm.price}
                        onChange={(e) => setEditForm(prev => ({ ...prev, price: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button onClick={saveEdit} className="bg-green-600 text-white px-3 py-1 rounded text-sm">
                        Speichern
                      </button>
                      <button onClick={cancelEdit} className="bg-gray-500 text-white px-3 py-1 rounded text-sm">
                        Abbrechen
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-medium">{item.name}</span>
                      <div className="text-sm text-gray-600">€{item.price.toFixed(2)}</div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEditItem(item, 'drinks')}
                        className="bg-purple-600 text-white px-2 py-1 rounded text-sm hover:bg-purple-700"
                      >
                        Bearbeiten
                      </button>
                      <button
                        onClick={() => onDeleteMenuItem('drinks', item.id)}
                        className="bg-red-600 text-white px-2 py-1 rounded text-sm hover:bg-red-700"
                      >
                        Löschen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Sweets */}
        <div>
          <div className="flex justify-between items-center mb-4">
            <h4 className="text-md font-semibold text-gray-700 border-b pb-2">Süßwaren</h4>
            <button
              onClick={() => setShowNewSweet(true)}
              className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700"
            >
              Neue Süßware
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sweetsMenu.map((item) => (
              <div key={item.id} className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                {editingItem?.id === item.id ? (
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium mb-1">Name</label>
                      <input
                        type="text"
                        value={editForm.name}
                        onChange={(e) => setEditForm(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium mb-1">Preis (€)</label>
                      <input
                        type="number"
                        step="0.01"
                        value={editForm.price}
                        onChange={(e) => setEditForm(prev => ({ ...prev, price: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded"
                      />
                    </div>
                    <div className="flex gap-2">
                      <button onClick={saveEdit} className="bg-green-600 text-white px-3 py-1 rounded text-sm">
                        Speichern
                      </button>
                      <button onClick={cancelEdit} className="bg-gray-500 text-white px-3 py-1 rounded text-sm">
                        Abbrechen
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="flex justify-between items-center">
                    <div>
                      <span className="font-medium">{item.name}</span>
                      <div className="text-sm text-gray-600">€{item.price.toFixed(2)}</div>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => startEditItem(item, 'sweets')}
                        className="bg-orange-600 text-white px-2 py-1 rounded text-sm hover:bg-orange-700"
                      >
                        Bearbeiten
                      </button>
                      <button
                        onClick={() => onDeleteMenuItem('sweets', item.id)}
                        className="bg-red-600 text-white px-2 py-1 rounded text-sm hover:bg-red-700"
                      >
                        Löschen
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* New Item Modals */}
      {showNewDrink && (
        <NewMenuItemModal
          title="Neues Getränk hinzufügen"
          onCreateItem={(name, price) => onCreateMenuItem('drinks', name, price)}
          onClose={() => setShowNewDrink(false)}
        />
      )}

      {showNewSweet && (
        <NewMenuItemModal
          title="Neue Süßware hinzufügen"
          onCreateItem={(name, price) => onCreateMenuItem('sweets', name, price)}
          onClose={() => setShowNewSweet(false)}
        />
      )}

      {showNewBreakfast && (
        <NewBreakfastItemModal
          title="Neues Brötchen hinzufügen"
          onCreateItem={(rollType, price) => onCreateMenuItem('breakfast', rollType, price)}
          onClose={() => setShowNewBreakfast(false)}
        />
      )}

      {showNewTopping && (
        <NewToppingItemModal
          title="Neuer Belag hinzufügen"
          onCreateItem={(toppingType, price) => onCreateMenuItem('toppings', toppingType, price)}
          onClose={() => setShowNewTopping(false)}
        />
      )}
    </div>
  );
};

// Breakfast History Tab Component
const BreakfastHistoryTab = ({ currentDepartment }) => {
  const [breakfastHistory, setBreakfastHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(null);

  useEffect(() => {
    fetchBreakfastHistory();
  }, [currentDepartment]);

  const fetchBreakfastHistory = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/orders/breakfast-history/${currentDepartment.department_id}?days_back=30`);
      setBreakfastHistory(response.data.history || []);
    } catch (error) {
      console.error('Fehler beim Laden der Frühstück-Geschichte:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      weekday: 'long'
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-lg text-gray-600">Lade Frühstück-Verlauf...</div>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-lg font-semibold mb-6">Frühstück Verlauf - {currentDepartment.department_name}</h3>

      {breakfastHistory.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          <p>Keine Frühstücks-Bestellungen in den letzten 30 Tagen gefunden.</p>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-semibold text-blue-800">Gesamt Tage</h4>
              <p className="text-2xl font-bold text-blue-600">{breakfastHistory.length}</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h4 className="font-semibold text-green-800">Gesamt Bestellungen</h4>
              <p className="text-2xl font-bold text-green-600">
                {breakfastHistory.reduce((sum, day) => sum + day.total_orders, 0)}
              </p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h4 className="font-semibold text-purple-800">Gesamt Umsatz</h4>
              <p className="text-2xl font-bold text-purple-600">
                €{breakfastHistory.reduce((sum, day) => sum + day.total_amount, 0).toFixed(2)}
              </p>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h4 className="font-semibold text-orange-800">Ø pro Tag</h4>
              <p className="text-2xl font-bold text-orange-600">
                €{(breakfastHistory.reduce((sum, day) => sum + day.total_amount, 0) / breakfastHistory.length).toFixed(2)}
              </p>
            </div>
          </div>

          {/* Daily History List */}
          <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
            <div className="px-6 py-4 bg-gray-50 border-b">
              <h4 className="font-semibold text-gray-800">Tägliche Übersichten</h4>
            </div>
            <div className="divide-y divide-gray-200">
              {breakfastHistory.map((day, index) => (
                <div
                  key={day.date}
                  className={`p-6 hover:bg-gray-50 cursor-pointer ${
                    selectedDate === day.date ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => setSelectedDate(selectedDate === day.date ? null : day.date)}
                >
                  {/* Day Summary Header */}
                  <div className="flex justify-between items-center">
                    <div>
                      <h5 className="font-semibold text-lg">{formatDate(day.date)}</h5>
                      <p className="text-sm text-gray-600">
                        {day.total_orders} Bestellungen • €{day.total_amount.toFixed(2)}
                      </p>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>Weiße: {day.shopping_list.weiss?.whole_rolls || 0} Brötchen</span>
                      <span>Körner: {day.shopping_list.koerner?.whole_rolls || 0} Brötchen</span>
                      <span>{selectedDate === day.date ? '▲' : '▼'}</span>
                    </div>
                  </div>

                  {/* Detailed View */}
                  {selectedDate === day.date && (
                    <div className="mt-6 pt-6 border-t border-gray-200">
                      {/* Shopping List */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                          <h6 className="font-semibold text-blue-800 mb-3">Einkaufsliste</h6>
                          <div className="space-y-2 text-sm">
                            {day.shopping_list.weiss && (
                              <div className="flex justify-between">
                                <span>Weiße Brötchen:</span>
                                <span className="font-medium">{day.shopping_list.weiss.whole_rolls} Stück</span>
                              </div>
                            )}
                            {day.shopping_list.koerner && (
                              <div className="flex justify-between">
                                <span>Körnerbrötchen:</span>
                                <span className="font-medium">{day.shopping_list.koerner.whole_rolls} Stück</span>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                          <h6 className="font-semibold text-green-800 mb-3">Tagesstatistik</h6>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span>Bestellungen:</span>
                              <span className="font-medium">{day.total_orders}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Gesamtumsatz:</span>
                              <span className="font-medium">€{day.total_amount.toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Ø pro Bestellung:</span>
                              <span className="font-medium">€{(day.total_amount / day.total_orders).toFixed(2)}</span>
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Employee Details */}
                      <div>
                        <h6 className="font-semibold text-gray-800 mb-3">Mitarbeiter Bestellungen</h6>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {Object.entries(day.employee_orders).map(([employeeName, employeeData]) => (
                            <div key={employeeName} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                              <h7 className="font-medium text-gray-800">{employeeName}</h7>
                              <div className="mt-2 space-y-1 text-sm text-gray-600">
                                <div>Weiße Hälften: {employeeData.white_halves}</div>
                                <div>Körner Hälften: {employeeData.seeded_halves}</div>
                                <div className="pt-1 border-t">
                                  <strong>Total: €{employeeData.total_amount.toFixed(2)}</strong>
                                </div>
                                {Object.keys(employeeData.toppings).length > 0 && (
                                  <div className="pt-1 text-xs">
                                    Beläge: {Object.entries(employeeData.toppings).map(([topping, count]) => `${count}x ${topping}`).join(', ')}
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Admin Settings Tab Component
const AdminSettingsTab = ({ currentDepartment }) => {
  const [newEmployeePassword, setNewEmployeePassword] = useState('');
  const [newAdminPassword, setNewAdminPassword] = useState('');
  const [showBreakfastControls, setShowBreakfastControls] = useState(true);
  const [breakfastStatus, setBreakfastStatus] = useState({ is_closed: false });

  useEffect(() => {
    fetchBreakfastStatus();
  }, [currentDepartment]);

  const fetchBreakfastStatus = async () => {
    try {
      const response = await axios.get(`${API}/breakfast-status/${currentDepartment.department_id}`);
      setBreakfastStatus(response.data);
    } catch (error) {
      console.error('Fehler beim Laden des Frühstück-Status:', error);
    }
  };

  const changePasswords = async () => {
    if (!newEmployeePassword || !newAdminPassword) {
      alert('Bitte beide Passwörter eingeben');
      return;
    }

    if (newEmployeePassword === newAdminPassword) {
      alert('Mitarbeiter- und Admin-Passwort müssen unterschiedlich sein');
      return;
    }

    try {
      await axios.put(`${API}/department-admin/change-password/${currentDepartment.department_id}?new_employee_password=${newEmployeePassword}&new_admin_password=${newAdminPassword}`);
      alert('Passwörter erfolgreich geändert');
      setNewEmployeePassword('');
      setNewAdminPassword('');
    } catch (error) {
      console.error('Fehler beim Ändern der Passwörter:', error);
      alert('Fehler beim Ändern der Passwörter');
    }
  };

  const closeBreakfast = async () => {
    if (window.confirm('Frühstück für heute schließen? Mitarbeiter können dann keine neuen Bestellungen mehr aufgeben.')) {
      try {
        await axios.post(`${API}/department-admin/close-breakfast/${currentDepartment.department_id}?admin_name=${currentDepartment.department_name}`);
        fetchBreakfastStatus();
        alert('Frühstück für heute geschlossen');
      } catch (error) {
        console.error('Fehler beim Schließen des Frühstücks:', error);
        alert('Fehler beim Schließen des Frühstücks');
      }
    }
  };

  const reopenBreakfast = async () => {
    if (window.confirm('Frühstück für heute wieder öffnen?')) {
      try {
        await axios.post(`${API}/department-admin/reopen-breakfast/${currentDepartment.department_id}`);
        fetchBreakfastStatus();
        alert('Frühstück für heute wieder geöffnet');
      } catch (error) {
        console.error('Fehler beim Öffnen des Frühstücks:', error);
        alert('Fehler beim Öffnen des Frühstücks');
      }
    }
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-6">Einstellungen</h3>

      <div className="space-y-8">
        {/* Breakfast Controls */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <h4 className="text-md font-semibold mb-4 text-yellow-800">Frühstück Kontrolle</h4>
          
          <div className="mb-4 p-4 bg-white border border-yellow-300 rounded">
            <div className="flex justify-between items-center">
              <div>
                <span className="font-medium">Status: </span>
                <span className={`px-2 py-1 rounded text-sm ${
                  breakfastStatus.is_closed 
                    ? 'bg-red-100 text-red-800' 
                    : 'bg-green-100 text-green-800'
                }`}>
                  {breakfastStatus.is_closed ? 'Geschlossen' : 'Geöffnet'}
                </span>
              </div>
              
              {breakfastStatus.is_closed ? (
                <button
                  onClick={reopenBreakfast}
                  className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                >
                  Frühstück öffnen
                </button>
              ) : (
                <button
                  onClick={closeBreakfast}
                  className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
                >
                  Frühstück schließen
                </button>
              )}
            </div>
            
            {breakfastStatus.is_closed && breakfastStatus.closed_by && (
              <div className="mt-2 text-sm text-gray-600">
                Geschlossen von: {breakfastStatus.closed_by}
              </div>
            )}
          </div>

          <div className="text-sm text-gray-600">
            <p><strong>Info:</strong></p>
            <ul className="list-disc list-inside space-y-1">
              <li>Wenn geschlossen, können Mitarbeiter keine neuen Frühstücksbestellungen aufgeben</li>
              <li>Nur Admins können dann noch Bestellungen bearbeiten</li>
              <li>Status kann jederzeit wieder geändert werden</li>
            </ul>
          </div>
        </div>

        {/* Password Management */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h4 className="text-md font-semibold mb-4 text-blue-800">Passwörter ändern</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium mb-2">Neues Mitarbeiter-Passwort</label>
              <input
                type="password"
                value={newEmployeePassword}
                onChange={(e) => setNewEmployeePassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                placeholder="Neues Passwort für Mitarbeiter"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-2">Neues Admin-Passwort</label>
              <input
                type="password"
                value={newAdminPassword}
                onChange={(e) => setNewAdminPassword(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
                placeholder="Neues Passwort für Admin"
              />
            </div>
          </div>
          
          <div className="mt-4">
            <button
              onClick={changePasswords}
              disabled={!newEmployeePassword || !newAdminPassword}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              Passwörter ändern
            </button>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            <p><strong>Hinweis:</strong></p>
            <ul className="list-disc list-inside space-y-1">
              <li>Beide Passwörter müssen unterschiedlich sein</li>
              <li>Nach der Änderung müssen sich alle neu anmelden</li>
              <li>Passwörter werden sofort für diese Wachabteilung geändert</li>
            </ul>
          </div>
        </div>

        {/* Department Info */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 className="text-md font-semibold mb-4 text-gray-700">Abteilungs-Information</h4>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <span className="font-medium">Abteilung:</span>
              <span className="ml-2">{currentDepartment.department_name}</span>
            </div>
            <div>
              <span className="font-medium">Abteilungs-ID:</span>
              <span className="ml-2 text-xs text-gray-600">{currentDepartment.department_id}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Main App Component
function App() {
  const { currentDepartment, isDepartmentAdmin } = React.useContext(AuthContext);

  if (isDepartmentAdmin) {
    return <DepartmentAdminDashboard />;
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