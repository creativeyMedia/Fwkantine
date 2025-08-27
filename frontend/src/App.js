import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

// Use environment variable for backend URL
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

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

// NumberSelector Component - Replaces number inputs with - and + buttons
const NumberSelector = ({ 
  value, 
  onChange, 
  min = 0, 
  max = 99, 
  label = "",
  unit = "",
  className = "" 
}) => {
  const handleDecrement = () => {
    if (value > min) {
      onChange(value - 1);
    }
  };

  const handleIncrement = () => {
    if (value < max) {
      onChange(value + 1);
    }
  };

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      {label && <span className="text-sm font-medium mr-2">{label}:</span>}
      <button
        type="button"
        onClick={handleDecrement}
        disabled={value <= min}
        className="w-8 h-8 flex items-center justify-center bg-red-500 text-white rounded-lg hover:bg-red-600 disabled:bg-gray-300 disabled:cursor-not-allowed font-bold text-lg"
      >
        −
      </button>
      <span className="min-w-[3rem] text-center font-medium text-lg">
        {value}
      </span>
      <button
        type="button"
        onClick={handleIncrement}
        disabled={value >= max}
        className="w-8 h-8 flex items-center justify-center bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:bg-gray-300 disabled:cursor-not-allowed font-bold text-lg"
      >
        +
      </button>
      {unit && <span className="text-sm text-gray-600 ml-1">{unit}</span>}
    </div>
  );
};

// Success Notification Component
const SuccessNotification = ({ message, onClose }) => {
  const [hasPlayed, setHasPlayed] = useState(false);

  useEffect(() => {
    // Play sound only once
    if (!hasPlayed) {
      playSucessSound();
      setHasPlayed(true);
    }
    
    // Auto-close after 1.5 seconds
    const timer = setTimeout(() => {
      if (onClose) {
        onClose();
      }
    }, 1500);
    
    // Cleanup timer on unmount
    return () => {
      clearTimeout(timer);
    };
  }, []); // Empty dependency array to run only once

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-2xl p-6 mx-4 max-w-md w-full border-2 border-green-200">
        <div className="text-center">
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-green-100 mb-4">
            <svg className="h-8 w-8 text-green-600 animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Erfolgreich!</h3>
          <p className="text-gray-700">{message}</p>
          <div className="mt-4">
            <div className="bg-green-500 h-2 rounded-full animate-pulse"></div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Sound Utility Functions
const playSucessSound = () => {
  try {
    // Check if audio is enabled in localStorage (default: true)
    const isAudioEnabled = localStorage.getItem('canteenAudioEnabled') !== 'false';
    if (!isAudioEnabled) return;

    // Create success sound with two ascending tones (do-re pattern)
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    
    // First tone (lower)
    const oscillator1 = audioContext.createOscillator();
    const gainNode1 = audioContext.createGain();
    oscillator1.connect(gainNode1);
    gainNode1.connect(audioContext.destination);
    
    oscillator1.frequency.setValueAtTime(523, audioContext.currentTime); // C5 note
    gainNode1.gain.setValueAtTime(0.3, audioContext.currentTime);
    gainNode1.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
    
    oscillator1.start(audioContext.currentTime);
    oscillator1.stop(audioContext.currentTime + 0.15);
    
    // Second tone (higher) - starts slightly overlapped
    const oscillator2 = audioContext.createOscillator();
    const gainNode2 = audioContext.createGain();
    oscillator2.connect(gainNode2);
    gainNode2.connect(audioContext.destination);
    
    oscillator2.frequency.setValueAtTime(659, audioContext.currentTime + 0.08); // E5 note
    gainNode2.gain.setValueAtTime(0.3, audioContext.currentTime + 0.08);
    gainNode2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.25);
    
    oscillator2.start(audioContext.currentTime + 0.08);
    oscillator2.stop(audioContext.currentTime + 0.25);
  } catch (error) {
    console.log('Audio not supported or blocked:', error);
  }
};

// Individual Employee Profile Component with Combined Chronological History
const IndividualEmployeeProfile = ({ employee, onClose }) => {
  const [employeeProfile, setEmployeeProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

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

  // Combine and sort orders and payments chronologically
  const getCombinedHistory = () => {
    if (!employeeProfile) return [];
    
    const orders = (employeeProfile.order_history || []).map(order => ({
      ...order,
      type: 'order',
      timestamp: order.timestamp
    }));
    
    const payments = (employeeProfile.payment_history || []).map(payment => ({
      ...payment,
      type: 'payment',
      timestamp: payment.timestamp
    }));
    
    // Combine and sort by timestamp (newest first)
    const combined = [...orders, ...payments];
    combined.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
    
    return combined;
  };

  // Pagination logic
  const combinedHistory = getCombinedHistory();
  const totalPages = Math.ceil(combinedHistory.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentItems = combinedHistory.slice(startIndex, endIndex);

  const goToPage = (page) => {
    setCurrentPage(page);
  };

  const goToFirstPage = () => {
    setCurrentPage(1);
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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
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
              <p className="text-2xl font-bold text-blue-600">{employeeProfile.breakfast_total.toFixed(2)} €</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800">Getränke/Süßes Saldo</h3>
              <p className="text-2xl font-bold text-green-600">{employeeProfile.drinks_sweets_total.toFixed(2)} €</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="font-semibold text-purple-800">Gesamt Bestellungen</h3>
              <p className="text-2xl font-bold text-purple-600">{employeeProfile.total_orders}</p>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h3 className="font-semibold text-orange-800">Gesamt Schulden</h3>
              <p className="text-2xl font-bold text-orange-600">{(employeeProfile.breakfast_total + employeeProfile.drinks_sweets_total).toFixed(2)} €</p>
            </div>
          </div>

          {/* Combined Chronological History */}
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-semibold">Chronologischer Verlauf</h3>
              <span className="text-sm text-gray-600">
                Seite {currentPage} von {totalPages} ({combinedHistory.length} Einträge gesamt)
              </span>
            </div>
            
            {combinedHistory.length === 0 ? (
              <p className="text-gray-600 text-center py-8">Keine Einträge vorhanden</p>
            ) : (
              <div className="space-y-4">
                {currentItems.map((item, index) => {
                  if (item.type === 'order') {
                    // Render Order
                    return (
                      <div key={`order-${item.id || index}`} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <span className="inline-block bg-blue-100 text-blue-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded">
                              {getOrderTypeLabel(item.order_type)}
                            </span>
                            <span className="text-sm text-gray-600">{formatDate(item.timestamp)}</span>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold">{item.total_price.toFixed(2)} €</p>
                          </div>
                        </div>
                        
                        {item.readable_items && item.readable_items.length > 0 && (
                          <div className="space-y-1">
                            {item.readable_items.map((orderItem, idx) => (
                              <div key={idx} className="text-sm flex justify-between items-start">
                                <div className="flex-1">
                                  <span className="font-medium">{orderItem.description}</span>
                                  {orderItem.toppings && <span className="text-gray-600 block text-xs">mit {orderItem.toppings}</span>}
                                  {orderItem.unit_price && <span className="text-gray-500 block text-xs">({orderItem.unit_price})</span>}
                                </div>
                                {orderItem.total_price && (
                                  <span className="text-sm font-medium text-right ml-2">{orderItem.total_price}</span>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  } else {
                    // Render Payment (Green styling)
                    return (
                      <div key={`payment-${item.id || index}`} className="bg-green-50 border border-green-200 rounded-lg p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <span className="inline-block bg-green-100 text-green-800 text-xs font-semibold mr-2 px-2.5 py-0.5 rounded">
                              Zahlung
                            </span>
                            <span className="text-sm text-gray-600">{formatDate(item.timestamp)}</span>
                          </div>
                          <div className="text-right">
                            <p className="font-semibold text-green-600">{item.amount.toFixed(2)} €</p>
                          </div>
                        </div>
                        
                        <div className="text-sm text-gray-700">
                          <p><strong>Art:</strong> {item.payment_type === 'breakfast' ? 'Frühstück' : 'Getränke/Süßes'}</p>
                          <p><strong>Admin:</strong> {item.admin_user}</p>
                          {item.notes && <p><strong>Hinweise:</strong> {item.notes}</p>}
                        </div>
                      </div>
                    );
                  }
                })}
              </div>
            )}
          </div>

          {/* Pagination Navigation */}
          {totalPages > 1 && (
            <div className="mt-6 flex justify-center items-center space-x-2">
              <button
                onClick={() => goToPage(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                ← Zurück
              </button>
              
              {currentPage > 1 && (
                <button
                  onClick={goToFirstPage}
                  className="px-4 py-2 bg-blue-100 text-blue-700 rounded hover:bg-blue-200"
                >
                  Zur ersten Seite
                </button>
              )}
              
              <span className="px-4 py-2 bg-blue-600 text-white rounded">
                {currentPage}
              </span>
              
              <button
                onClick={() => goToPage(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-3 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Vor →
              </button>
            </div>
          )}
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
    // ⚠️ SICHERHEITSFIX: init-data Aufruf entfernt! 
    // Verursachte Datenbank-Löschung bei jedem Frontend-Reload
    // initializeData(); // ← DEAKTIVIERT - GEFÄHRLICH FÜR PRODUCTION
    fetchDepartments();
  }, []);

  const initializeData = async () => {
    // ⚠️ DEAKTIVIERT: Diese Funktion löschte die Datenbank bei jedem Aufruf!
    // Nur für Development verwenden, niemals in Production!
    console.warn('🚨 initializeData() deaktiviert - gefährlich für Production-Daten!');
    return;
    
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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg p-8 max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
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
    // This function opens employee profile/history
    setSelectedEmployeeForProfile(employee);
    setShowEmployeeProfile(true);
  };

  const handleEmployeeProfileClick = async (employee, event) => {
    // This function handles the "Bestellen" button click - should open order menu
    try {
      event.stopPropagation(); // Prevent the employee profile from opening
      setSelectedEmployee(employee); // Open order menu (correct!)
    } catch (error) {
      console.error('Error opening employee order menu:', error);
      alert('Fehler beim Öffnen des Bestellmenüs');
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
              <h3 className="text-lg sm:text-xl font-semibold mb-4 sm:mb-6 text-gray-800">{employee.name}</h3>
              <div className="flex gap-2 sm:gap-3">
                <div className="flex-1 text-center text-xs sm:text-sm text-gray-700 py-2 sm:py-3 cursor-pointer hover:text-gray-900 verlauf-text rounded-lg hover:bg-gray-100 transition-colors"
                     onClick={(event) => handleEmployeeClick(employee, event)}>
                  Verlauf
                </div>
                <button
                  onClick={(event) => handleEmployeeProfileClick(employee, event)}
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
  const [lunchSettings, setLunchSettings] = useState({ price: 0.0, enabled: true, boiled_eggs_price: 0.50, coffee_price: 1.50 });
  const [order, setOrder] = useState({
    breakfast_items: [],
    drink_items: {},
    sweet_items: {}
  });
  const [breakfastFormData, setBreakfastFormData] = useState(null);
  const [isLoadingExistingOrders, setIsLoadingExistingOrders] = useState(true);
  const [breakfastStatus, setBreakfastStatus] = useState({ is_closed: false });
  const [showSuccessNotification, setShowSuccessNotification] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');

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
    fetchLunchSettings();
    fetchBreakfastStatus();
  }, [currentDepartment]);

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

  const fetchLunchSettings = async () => {
    try {
      const response = await axios.get(`${API}/lunch-settings`);
      setLunchSettings(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Lunch-Einstellungen:', error);
    }
  };

  const fetchBreakfastStatus = async () => {
    try {
      if (!currentDepartment?.department_id) {
        return;
      }
      const response = await axios.get(`${API}/breakfast-status/${currentDepartment.department_id}`);
      setBreakfastStatus(response.data);
    } catch (error) {
      console.error('Fehler beim Laden des Frühstück-Status:', error);
    }
  };

  // Create dynamic labels from menu data
  const rollTypeLabels = {
    'weiss': 'Helles Brötchen',
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
      boiled_eggs: 0,
      has_coffee: false
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
      
      // For breakfast category, check if breakfast is closed first
      if (activeCategory === 'breakfast' && breakfastStatus.is_closed) {
        alert('Frühstück ist für heute geschlossen. Nur Getränke und Süßigkeiten können bestellt werden.');
        return;
      }
      
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
            
            setSuccessMessage('Bestellung erfolgreich aktualisiert!');
            setShowSuccessNotification(true);
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
            
            setSuccessMessage('Bestellung erfolgreich gespeichert!');
            setShowSuccessNotification(true);
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
          
          setSuccessMessage('Bestellung erfolgreich gespeichert!');
          setShowSuccessNotification(true);
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
        setSuccessMessage('Bestellung erfolgreich gespeichert!');
        setShowSuccessNotification(true);
        playSucessSound();
      }
      
      // Note: Employee data refresh and modal closing is now handled by SuccessNotification onClose
      
    } catch (error) {
      console.error('Fehler beim Speichern der Bestellung:', error);
      alert('Fehler beim Speichern der Bestellung. Bitte versuchen Sie es erneut.');
    }
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
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
            breakfastStatus.is_closed ? (
              <div className="text-center py-8">
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-6">
                  <div className="text-orange-800 mb-4">
                    <svg className="mx-auto h-16 w-16 text-orange-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-orange-800 mb-2">Frühstück ist für heute geschlossen</h3>
                  <p className="text-orange-600">Die Frühstücksbestellung wurde vom Administrator beendet.</p>
                  <p className="text-orange-600">Getränke und Süßigkeiten können weiterhin bestellt werden.</p>
                </div>
              </div>
            ) : (
              <BreakfastOrderForm
                breakfastMenu={breakfastMenu}
                toppingsMenu={toppingsMenu}
                onAddItem={addBreakfastItem}
                rollTypeLabels={rollTypeLabels}
                toppingLabels={finalToppingLabels}
                existingOrderData={breakfastFormData}
                boiledEggsPrice={lunchSettings.boiled_eggs_price || 0.50}
                coffeePrice={lunchSettings.coffee_price || 1.50}
                onDirectSubmit={(breakfastData) => {
                  // This will be called directly when breakfast form is submitted
                  setBreakfastFormData(breakfastData);
                }}
              />
            )
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

      {/* Success Notification */}
      {showSuccessNotification && (
        <SuccessNotification
          message={successMessage}
          onClose={() => {
            setShowSuccessNotification(false);
            setSuccessMessage('');
            
            // Refresh employee data and close after success notification
            if (fetchEmployees) {
              fetchEmployees();
            }
            
            if (onOrderComplete) {
              onOrderComplete();
            }
          }}
        />
      )}
    </div>
  );
};

// Simplified Breakfast Order Form with Memo to prevent unnecessary re-renders - Direct Roll Selection with Topping Assignment
const BreakfastOrderForm = ({ breakfastMenu, toppingsMenu, onAddItem, rollTypeLabels, toppingLabels, onDirectSubmit, existingOrderData, boiledEggsPrice = 0.50, coffeePrice = 1.50 }) => {
  const [whiteRolls, setWhiteRolls] = useState(0);
  const [seededRolls, setSeededRolls] = useState(0);
  const [toppingAssignments, setToppingAssignments] = useState([]);
  const [hasLunch, setHasLunch] = useState(false);
  const [boiledEggs, setBoiledEggs] = useState(0);
  const [hasCoffee, setHasCoffee] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);

  // Initialize form with existing order data if available (only once)
  useEffect(() => {
    if (existingOrderData && Object.keys(existingOrderData).length > 0 && !isInitialized) {
      setWhiteRolls(existingOrderData.white_halves || 0);
      setSeededRolls(existingOrderData.seeded_halves || 0);
      setHasLunch(existingOrderData.has_lunch || false);
      setBoiledEggs(existingOrderData.boiled_eggs || 0);
      setHasCoffee(existingOrderData.has_coffee || false);
      
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
      setIsInitialized(true);
    } else if (!existingOrderData || Object.keys(existingOrderData).length === 0) {
      // Allow re-initialization if existingOrderData becomes empty (form reset)
      setIsInitialized(false);
    }
  }, [existingOrderData, isInitialized]);

  // Get actual prices from menu (use admin-set prices directly)
  const getBreakfastPrice = (rollType) => {
    const menuItem = breakfastMenu.find(item => item.roll_type === rollType);
    return menuItem ? menuItem.price : 0;
  };

  const whiteRollPrice = getBreakfastPrice('weiss');
  const seededRollPrice = getBreakfastPrice('koerner');

  const totalHalves = whiteRolls + seededRolls;
  
  // Get boiled eggs price from props (passed from lunch settings)
  const boiledEggsCost = boiledEggs * boiledEggsPrice;
  const coffeeCost = hasCoffee ? coffeePrice : 0;
  
  // Calculate separate cost components for better display
  const rollsCost = (whiteRolls * whiteRollPrice) + (seededRolls * seededRollPrice);
  const totalCost = rollsCost + boiledEggsCost + coffeeCost; // Lunch is handled separately by backend

  // Event handlers - defined as stable functions
  const handleLunchChange = (e) => {
    setHasLunch(e.target.checked);
  };

  const handleCoffeeChange = (e) => {
    setHasCoffee(e.target.checked);
  };

  // Update topping assignments when roll counts change
  useEffect(() => {
    const newAssignments = [];
    const oldAssignmentsByLabel = {};
    
    // Create lookup of existing assignments by label to preserve selections
    toppingAssignments.forEach(assignment => {
      oldAssignmentsByLabel[assignment.rollLabel] = assignment.topping;
    });
    
    // Add white roll topping slots
    for (let i = 0; i < whiteRolls; i++) {
      const rollLabel = `Helles Brötchen ${i + 1}`;
      newAssignments.push({
        id: `white_${i}`,
        rollType: 'weiss',
        rollLabel: rollLabel,
        topping: oldAssignmentsByLabel[rollLabel] || ''
      });
    }
    // Add seeded roll topping slots
    for (let i = 0; i < seededRolls; i++) {
      const rollLabel = `Körnerbrötchen ${i + 1}`;
      newAssignments.push({
        id: `seeded_${i}`,
        rollType: 'koerner',
        rollLabel: rollLabel,
        topping: oldAssignmentsByLabel[rollLabel] || ''
      });
    }
    setToppingAssignments(newAssignments);
  }, [whiteRolls, seededRolls]); // Removed toppingAssignments from dependencies to avoid infinite loop

  // Update form data when any valid combination is selected
  useEffect(() => {
    const hasRolls = totalHalves > 0;
    const hasValidRollOrder = hasRolls && toppingAssignments.length === totalHalves && 
                              !toppingAssignments.some(a => !a.topping);
    const hasExtras = boiledEggs > 0 || hasLunch || hasCoffee;
    
    // Allow submission if user has:
    // 1. Valid roll order (rolls + toppings), OR
    // 2. Just extras (eggs, lunch, coffee) without rolls, OR  
    // 3. Any combination of rolls and extras
    if ((hasValidRollOrder || (hasExtras && !hasRolls) || (hasRolls && hasExtras)) && onDirectSubmit) {
      const toppings = hasRolls ? toppingAssignments.map(assignment => assignment.topping) : [];
      const breakfastData = {
        total_halves: totalHalves,
        white_halves: whiteRolls,
        seeded_halves: seededRolls,
        toppings: toppings,
        has_lunch: hasLunch,
        boiled_eggs: boiledEggs,
        has_coffee: hasCoffee
      };
      onDirectSubmit(breakfastData);
    } else if (onDirectSubmit && totalHalves === 0 && !hasExtras) {
      onDirectSubmit(null); // Clear data if nothing selected
    }
  }, [toppingAssignments, totalHalves, hasLunch, boiledEggs, hasCoffee, totalCost, onDirectSubmit]); // Include all form fields that affect submission

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
    const hasRolls = totalHalves > 0;
    const hasEggsOrLunch = boiledEggs > 0 || hasLunch;
    
    // Validate that user has selected something
    if (!hasRolls && !hasEggsOrLunch) {
      alert('Bitte wählen Sie mindestens ein Brötchen, Frühstückseier oder Mittagessen.');
      return;
    }

    // If user selected rolls, check if all toppings are assigned  
    if (hasRolls) {
      const unassignedCount = toppingAssignments.filter(assignment => !assignment.topping).length;
      if (unassignedCount > 0) {
        alert(`Bitte weisen Sie allen ${totalHalves} Brötchenhälften einen Belag zu. ${unassignedCount} fehlen noch.`);
        return;
      }
    }

    // Convert assignments to the expected format (empty array if no rolls)
    const toppings = hasRolls ? toppingAssignments.map(assignment => assignment.topping) : [];
    
    onAddItem(totalHalves, whiteRolls, seededRolls, toppings, hasLunch, boiledEggs, totalCost);
    
    // Reset form
    setWhiteRolls(0);
    setSeededRolls(0);
    setToppingAssignments([]);
    setHasLunch(false);
    setBoiledEggs(0);
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
              <label className="block text-sm font-medium mb-3">Helle Brötchen (Hälften)</label>
              <div className="flex flex-col gap-2">
                <NumberSelector
                  value={whiteRolls}
                  onChange={setWhiteRolls}
                  min={0}
                  max={20}
                  unit="Hälften"
                />
                <span className="text-sm text-gray-600">
                  à {whiteRollPrice.toFixed(2)} € = {(whiteRolls * whiteRollPrice).toFixed(2)} €
                </span>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium mb-3">Körner Brötchen (Hälften)</label>
              <div className="flex flex-col gap-2">
                <NumberSelector
                  value={seededRolls}
                  onChange={setSeededRolls}
                  min={0}
                  max={20}
                  unit="Hälften"
                />
                <span className="text-sm text-gray-600">
                  à {seededRollPrice.toFixed(2)} € = {(seededRolls * seededRollPrice).toFixed(2)} €
                </span>
              </div>
            </div>
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
      </div>
    )}

    {/* Boiled Eggs and Coffee Options - Side by Side */}
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* Boiled Eggs Option */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
        <label className="block text-sm font-medium mb-3">🥚 Gekochte Frühstückseier</label>
        <div className="flex flex-col gap-2">
          <NumberSelector
            value={boiledEggs}
            onChange={setBoiledEggs}
            min={0}
            max={10}
            unit="Stück"
          />
          <span className="text-sm text-gray-600">
            {boiledEggsPrice.toFixed(2)} € pro Ei = {boiledEggsCost.toFixed(2)} €
          </span>
        </div>
      </div>

      {/* Coffee Option */}
      <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
        <label className="flex items-center cursor-pointer">
          <input
            type="checkbox"
            checked={hasCoffee}
            onChange={handleCoffeeChange}
            className="mr-3 w-4 h-4 text-amber-600 bg-gray-100 border-gray-300 rounded focus:ring-amber-500 focus:ring-2"
          />
          <div>
            <span className="text-sm font-medium block">☕ Kaffee</span>
            <span className="text-sm text-gray-600">
              {coffeePrice.toFixed(2)} € pro Tag{hasCoffee ? ` = ${coffeeCost.toFixed(2)} €` : ''}
            </span>
          </div>
        </label>
      </div>
    </div>

    {/* Mittagessen Option */}
    <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
      <label className="flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={hasLunch}
          onChange={handleLunchChange}
          className="mr-3 w-4 h-4 text-purple-600 bg-gray-100 border-gray-300 rounded focus:ring-purple-500 focus:ring-2"
        />
        <span className="text-sm font-medium">🍽️ Mittagessen hinzufügen (Preis wird vom Admin festgelegt)</span>
      </label>
    </div>

    {/* Gesamtrechnung nach unten verschoben */}
    <div className="mt-4 p-4 bg-gray-50 border border-gray-300 rounded-lg">
      <h4 className="font-semibold mb-3 text-gray-800">📋 Bestellzusammenfassung</h4>
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-sm font-medium">Brötchen ({totalHalves} Hälften):</span>
          <span className="text-sm font-medium">{rollsCost.toFixed(2)} €</span>
        </div>
        {boiledEggs > 0 && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600">Gekochte Eier ({boiledEggs} Stück):</span>
            <span className="text-sm text-gray-600">{boiledEggsCost.toFixed(2)} €</span>
          </div>
        )}
        {hasCoffee && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-amber-600">☕ Kaffee:</span>
            <span className="text-sm text-amber-600">{coffeeCost.toFixed(2)} €</span>
          </div>
        )}
        {hasLunch && (
          <div className="flex justify-between items-center">
            <span className="text-sm text-purple-600">🍽️ Mittagessen:</span>
            <span className="text-sm text-purple-600">wird vom Admin berechnet</span>
          </div>
        )}
        <div className="border-t pt-2 mt-2">
          <div className="flex justify-between items-center">
            <span className="font-bold">Brötchen + Eier + Kaffee Gesamt:</span>
            <span className="font-bold">{totalCost.toFixed(2)} €</span>
          </div>
          {hasLunch && (
            <p className="text-xs text-gray-500 mt-1">+ Mittagessen-Preis wird automatisch hinzugefügt</p>
          )}
        </div>
      </div>
    </div>
  </div>
</div>
  );
};

// Drinks Order Form
const DrinksOrderForm = ({ drinksMenu, onUpdateQuantity }) => {
  const [quantities, setQuantities] = useState({});

  const handleQuantityChange = (drinkId, newQuantity) => {
    setQuantities(prev => ({ ...prev, [drinkId]: newQuantity }));
    onUpdateQuantity(drinkId, newQuantity);
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Getränke auswählen</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {drinksMenu.map((drink) => (
          <div key={drink.id} className="flex items-center justify-between p-3 border border-gray-300 rounded-lg">
            <div>
              <span className="font-medium">{drink.name}</span>
              <span className="text-gray-600 ml-2">({drink.price.toFixed(2)} €)</span>
            </div>
            <NumberSelector
              value={quantities[drink.id] || 0}
              onChange={(value) => handleQuantityChange(drink.id, value)}
              min={0}
              max={50}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

// Sweets Order Form
const SweetsOrderForm = ({ sweetsMenu, onUpdateQuantity }) => {
  const [quantities, setQuantities] = useState({});

  const handleQuantityChange = (sweetId, newQuantity) => {
    setQuantities(prev => ({ ...prev, [sweetId]: newQuantity }));
    onUpdateQuantity(sweetId, newQuantity);
  };

  return (
    <div>
      <h3 className="text-lg font-semibold mb-4">Süßes auswählen</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sweetsMenu.map((sweet) => (
          <div key={sweet.id} className="flex items-center justify-between p-3 border border-gray-300 rounded-lg">
            <div>
              <span className="font-medium">{sweet.name}</span>
              <span className="text-gray-600 ml-2">({sweet.price.toFixed(2)} €)</span>
            </div>
            <NumberSelector
              value={quantities[sweet.id] || 0}
              onChange={(value) => handleQuantityChange(sweet.id, value)}
              min={0}
              max={50}
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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg p-6 max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
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
                  <p>Frühstück: {employee.breakfast_balance.toFixed(2)} €</p>
                  <p>Getränke/Süßes: {employee.drinks_sweets_balance.toFixed(2)} €</p>
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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
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
              <p className="text-2xl font-bold text-blue-600">{profile.breakfast_total.toFixed(2)} €</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800">Getränke/Süßes Saldo</h3>
              <p className="text-2xl font-bold text-green-600">{profile.drinks_sweets_total.toFixed(2)} €</p>
            </div>
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="font-semibold text-purple-800">Gesamt Bestellungen</h3>
              <p className="text-2xl font-bold text-purple-600">{profile.total_orders}</p>
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
              <h3 className="font-semibold text-orange-800">Gesamt Schulden</h3>
              <p className="text-2xl font-bold text-orange-600">{(profile.breakfast_total + profile.drinks_sweets_total).toFixed(2)} €</p>
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
                        <p className="font-semibold">{order.total_price.toFixed(2)} €</p>
                      </div>
                    </div>
                    
                    {order.readable_items && order.readable_items.length > 0 && (
                      <div className="space-y-1">
                        {order.readable_items.map((item, idx) => (
                          <div key={idx} className="text-sm flex justify-between items-start">
                            <div className="flex-1">
                              <span className="font-medium">{item.description}</span>
                              {item.toppings && <span className="text-gray-600 block text-xs">mit {item.toppings}</span>}
                              {item.unit_price && <span className="text-gray-500 block text-xs">({item.unit_price})</span>}
                            </div>
                            {item.total_price && (
                              <span className="text-sm font-medium text-right ml-2">{item.total_price}</span>
                            )}
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
      if (!currentDepartment?.department_id) {
        console.error('No department ID available for admin menu fetch');
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
        console.error('Fallback admin menu loading also failed:', fallbackError);
      }
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

  const createMenuItem = async (category, nameOrType, nameOrPrice, priceOrNull) => {
    try {
      if (!currentDepartment?.department_id) {
        alert('Fehler: Keine Abteilungs-ID verfügbar');
        return;
      }

      let requestData;
      const departmentId = currentDepartment.department_id;
      
      if (category === 'breakfast') {
        requestData = { roll_type: nameOrType, price: parseFloat(nameOrPrice), department_id: departmentId };
      } else if (category === 'toppings') {
        // New format: toppingId, toppingName, price
        requestData = { 
          topping_id: nameOrType, 
          topping_name: nameOrPrice, 
          price: parseFloat(priceOrNull), 
          department_id: departmentId 
        };
      } else {
        // For drinks and sweets
        requestData = { name: nameOrType, price: parseFloat(nameOrPrice), department_id: departmentId };
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
            { id: 'breakfast-history', label: 'Bestellverlauf' },
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
              currentDepartment={currentDepartment}
            />
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
  const [drinksMenu, setDrinksMenu] = useState([]);
  const [sweetsMenu, setSweetsMenu] = useState([]);

  useEffect(() => {
    fetchEmployeeOrders();
    fetchMenus();
  }, [employee.id]);

  const fetchMenus = async () => {
    try {
      if (!currentDepartment?.department_id) {
        return;
      }
      const departmentId = currentDepartment.department_id;
      const [drinks, sweets] = await Promise.all([
        axios.get(`${API}/menu/drinks/${departmentId}`),
        axios.get(`${API}/menu/sweets/${departmentId}`)
      ]);
      setDrinksMenu(drinks.data);
      setSweetsMenu(sweets.data);
    } catch (error) {
      console.error('Fehler beim Laden der Menüs:', error);
      // Fallback to old endpoints if department-specific ones fail
      try {
        const [drinks, sweets] = await Promise.all([
          axios.get(`${API}/menu/drinks`),
          axios.get(`${API}/menu/sweets`)
        ]);
        setDrinksMenu(drinks.data);
        setSweetsMenu(sweets.data);
      } catch (fallbackError) {
        console.error('Fallback menu loading also failed:', fallbackError);
      }
    }
  };

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
        const boiledEggs = item.boiled_eggs || 0;
        const hasLunch = item.has_lunch ? ' + 🍽️ Mittagessen' : '';
        const hasCoffee = item.has_coffee ? ' + ☕ Kaffee' : '';
        
        // Handle toppings that might be objects or strings
        const toppingsText = toppings.length > 0 ? 
          ', Beläge: ' + toppings.map(topping => {
            if (typeof topping === 'string') {
              return topping;
            } else if (topping && typeof topping === 'object') {
              return topping.name || topping.topping_type || 'Unknown';
            }
            return 'Unknown';
          }).join(', ') : '';
        
        const rollsText = `${whiteHalves} Hell + ${seededHalves} Körner`;
        const eggsText = boiledEggs > 0 ? ` + 🥚 ${boiledEggs} Eier` : '';
        
        return `${rollsText}${eggsText}${toppingsText}${hasCoffee}${hasLunch}`;
      }).join('; ');
    } else if (order.order_type === 'drinks') {
      return Object.entries(order.drink_items || {}).map(([drinkId, qty]) => {
        // Find drink name by ID
        const drink = drinksMenu.find(d => d.id === drinkId);
        const drinkName = drink ? drink.name : drinkId;
        return `${qty}x ${drinkName}`;
      }).join(', ');
    } else if (order.order_type === 'sweets') {
      return Object.entries(order.sweet_items || {}).map(([sweetId, qty]) => {
        // Find sweet name by ID  
        const sweet = sweetsMenu.find(s => s.id === sweetId);
        const sweetName = sweet ? sweet.name : sweetId;
        return `${qty}x ${sweetName}`;
      }).join(', ');
    }
    return 'Unbekannte Bestellung';
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
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
                            {order.total_price.toFixed(2)} €
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
  const [sortedEmployees, setSortedEmployees] = useState([]);
  const [draggedIndex, setDraggedIndex] = useState(null);
  
  // Initialize sorted employees when employees prop changes
  useEffect(() => {
    setSortedEmployees([...employees]);
  }, [employees]);

  // Drag and Drop handlers
  const handleDragStart = (e, index) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', e.target.outerHTML);
    e.target.style.opacity = '0.5';
  };

  const handleDragEnd = (e) => {
    e.target.style.opacity = '1';
    setDraggedIndex(null);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  };

  const handleDrop = (e, dropIndex) => {
    e.preventDefault();
    
    if (draggedIndex === null || draggedIndex === dropIndex) {
      return;
    }

    const newSortedEmployees = [...sortedEmployees];
    const draggedEmployee = newSortedEmployees[draggedIndex];
    
    // Remove dragged employee from current position
    newSortedEmployees.splice(draggedIndex, 1);
    
    // Insert at new position
    newSortedEmployees.splice(dropIndex, 0, draggedEmployee);
    
    setSortedEmployees(newSortedEmployees);
    setDraggedIndex(null);
    
    // Save the new order to backend
    saveSortOrder(newSortedEmployees);
  };
  
  const saveSortOrder = async (sortedEmployees) => {
    try {
      const employeeIds = sortedEmployees.map(emp => emp.id);
      await axios.put(`${API}/departments/${currentDepartment.department_id}/employees/sort-order`, employeeIds);
      console.log('Sortierung erfolgreich gespeichert');
    } catch (error) {
      console.error('Fehler beim Speichern der Sortierung:', error);
      alert('Fehler beim Speichern der Sortierung. Die Änderungen gehen beim Neuladen verloren.');
    }
  };
  
  const markAsPaid = async (employee, balanceType) => {
    const balanceAmount = balanceType === 'breakfast' ? employee.breakfast_balance : employee.drinks_sweets_balance;
    const balanceLabel = balanceType === 'breakfast' ? 'Frühstück' : 'Getränke/Süßes';
    
    if (balanceAmount <= 0) {
      alert('Kein Saldo zum Zurücksetzen vorhanden');
      return;
    }
    
    if (window.confirm(`${balanceLabel}-Saldo von ${balanceAmount.toFixed(2)} € für ${employee.name} als bezahlt markieren?`)) {
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
        <div>
          <h3 className="text-lg font-semibold">Mitarbeiter verwalten</h3>
          <p className="text-sm text-gray-600 mt-1">
            <svg className="inline w-4 h-4 mr-1" viewBox="0 0 24 24" fill="currentColor">
              <path d="M8,18H11V15H8V18M8,14H11V10H8V14M8,9H11V6H8V9M13,18H16V15H13V18M13,14H16V10H13V14M13,9H16V6H13V9Z" />
            </svg>
            Mitarbeiter per Drag & Drop sortieren
          </p>
        </div>
        <button
          onClick={() => setShowNewEmployee(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
        >
          Neuer Mitarbeiter
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedEmployees.map((employee, index) => (
          <div 
            key={employee.id} 
            className={`bg-gray-50 border border-gray-200 rounded-lg p-4 transition-all duration-200 ${
              draggedIndex === index ? 'shadow-lg border-blue-400 bg-blue-50' : 'hover:shadow-md'
            }`}
            draggable
            onDragStart={(e) => handleDragStart(e, index)}
            onDragEnd={handleDragEnd}
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, index)}
          >
            {/* Drag Handle */}
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-lg">{employee.name}</h4>
              <div className="flex items-center space-x-2">
                <div 
                  className="cursor-move text-gray-400 hover:text-gray-600"
                  title="Zum Sortieren ziehen"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8,18H11V15H8V18M8,14H11V10H8V14M8,9H11V6H8V9M13,18H16V15H13V18M13,14H16V10H13V14M13,9H16V6H13V9Z" />
                  </svg>
                </div>
                <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded">
                  #{index + 1}
                </span>
              </div>
            </div>
            
            {/* Breakfast Balance */}
            <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium">Frühstück:</span>
                <span className="font-bold text-blue-600">{employee.breakfast_balance.toFixed(2)} €</span>
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
                <span className="font-bold text-green-600">{employee.drinks_sweets_balance.toFixed(2)} €</span>
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
    'weiss': 'Helles Brötchen',
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

        {/* Eier & Kaffee */}
        <CoffeeAndEggsManagement />

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
    { value: 'weiss', label: 'Helles Brötchen' },
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
  const [toppingName, setToppingName] = useState('');
  const [price, setPrice] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (toppingName.trim() && price && !isNaN(parseFloat(price))) {
      // Create a unique ID from the name
      const toppingId = toppingName.toLowerCase().replace(/[^a-z0-9]/g, '_').replace(/_+/g, '_').replace(/^_|_$/g, '');
      onCreateItem(toppingId, toppingName, price);
      setToppingName('');
      setPrice('');
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h2 className="text-xl font-bold mb-4">{title}</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium mb-2">Belag-Name</label>
            <input
              type="text"
              value={toppingName}
              onChange={(e) => setToppingName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500"
              placeholder="z.B. Rührei, Käse, Salami..."
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
      alert('Mittagessen-Preis erfolgreich aktualisiert');
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
          <h2 className="text-xl font-semibold mb-4">Mittagessen-Preis Verwaltung</h2>
          <div className="flex items-center gap-4">
            <span>Aktueller Preis: €{lunchSettings.price.toFixed(2)}</span>
            <button
              onClick={() => {
                const newPrice = prompt('Neuer Mittagessen-Preis (€):', lunchSettings.price.toFixed(2));
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
                  <p>Frühstück: {employee.breakfast_balance.toFixed(2)} €</p>
                  <p>Getränke/Süßes: {employee.drinks_sweets_balance.toFixed(2)} €</p>
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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
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
              <p className="text-2xl font-bold text-blue-600">{employeeProfile.breakfast_total.toFixed(2)} €</p>
              <button
                onClick={() => resetBalance('breakfast')}
                className="mt-2 text-sm bg-blue-600 text-white px-2 py-1 rounded hover:bg-blue-700"
              >
                Zurücksetzen
              </button>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <h3 className="font-semibold text-green-800">Getränke/Süßes Saldo</h3>
              <p className="text-2xl font-bold text-green-600">{employeeProfile.drinks_sweets_total.toFixed(2)} €</p>
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
              <p className="text-2xl font-bold text-orange-600">{(employeeProfile.breakfast_total + employeeProfile.drinks_sweets_total).toFixed(2)} €</p>
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
                        <p className="font-semibold">{order.total_price.toFixed(2)} €</p>
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
                          <div key={idx} className="text-sm flex justify-between items-start">
                            <div className="flex-1">
                              <span className="font-medium">{item.description}</span>
                              {item.toppings && <span className="text-gray-600 block text-xs">mit {item.toppings}</span>}
                              {item.unit_price && <span className="text-gray-500 block text-xs">({item.unit_price})</span>}
                            </div>
                            {item.total_price && (
                              <span className="text-sm font-medium text-right ml-2">{item.total_price}</span>
                            )}
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
      if (!departmentId) {
        console.error('No department ID available for toppings fetch');
        return;
      }
      
      const response = await axios.get(`${API}/menu/toppings/${departmentId}`);
      setToppingsMenu(response.data);
    } catch (error) {
      console.error('Fehler beim Laden der Beläge:', error);
      // Fallback to old endpoint
      try {
        const response = await axios.get(`${API}/menu/toppings`);
        setToppingsMenu(response.data);
      } catch (fallbackError) {
        console.error('Fallback toppings loading failed:', fallbackError);
      }
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
    'weiss': 'Helles Brötchen',
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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-lg max-w-6xl w-full mx-4 max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
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
              {/* Combined Shopping List with Lunch Box */}
              <div className="mb-8 flex gap-4">
                {/* Main Shopping List Box */}
                <div className="flex-1 bg-green-50 border border-green-200 rounded-lg p-6">
                  <h3 className="text-xl font-semibold mb-4 text-green-800">🛒 Einkaufsliste</h3>
                  
                  <div className="bg-white border border-green-300 rounded-lg p-4">
                    <div className="space-y-3">
                      {/* Bread Rolls */}
                      <div className="pb-2 border-b border-gray-200">
                        <div className="font-semibold text-gray-700 mb-2">Brötchen gesamt:</div>
                        <div className="ml-4">
                          {Object.entries(dailySummary.shopping_list).map(([rollType, data]) => {
                            const rollLabel = rollTypeLabels[rollType] || rollType;
                            const wholeRolls = data.whole_rolls || 0;
                            return (
                              <div key={rollType} className="text-lg font-bold text-green-700">
                                {wholeRolls} {rollLabel.replace(' Brötchen', '')}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                      
                      {/* Boiled Eggs */}
                      {dailySummary.total_boiled_eggs > 0 && (
                        <div className="pb-2 border-b border-gray-200">
                          <div className="font-semibold text-gray-700 mb-2">Gekochte Eier:</div>
                          <div className="ml-4 text-lg font-bold text-yellow-700">{dailySummary.total_boiled_eggs} Stück</div>
                        </div>
                      )}
                      
                      {/* Toppings with Roll Type Detail */}
                      {(() => {
                        // Check if we have employee orders data
                        if (!dailySummary.employee_orders || Object.keys(dailySummary.employee_orders).length === 0) {
                          return null;
                        }
                        
                        // Calculate toppings from employee orders
                        const toppingBreakdown = {};
                        
                        try {
                          Object.values(dailySummary.employee_orders).forEach(employeeData => {
                            if (employeeData && employeeData.toppings) {
                              Object.entries(employeeData.toppings).forEach(([topping, count]) => {
                                if (!toppingBreakdown[topping]) {
                                  toppingBreakdown[topping] = { white: 0, seeded: 0 };
                                }
                                
                                const whiteHalves = employeeData.white_halves || 0;
                                const seededHalves = employeeData.seeded_halves || 0;
                                const totalHalves = whiteHalves + seededHalves;
                                
                                if (totalHalves > 0) {
                                  const whiteRatio = whiteHalves / totalHalves;
                                  const seededRatio = seededHalves / totalHalves;
                                  toppingBreakdown[topping].white += Math.round(count * whiteRatio);
                                  toppingBreakdown[topping].seeded += Math.round(count * seededRatio);
                                }
                              });
                            }
                          });
                        } catch (error) {
                          console.error('Error processing toppings:', error);
                          return (
                            <div>
                              <div className="font-semibold text-gray-700 mb-2">Beläge:</div>
                              <div className="ml-4 text-red-500 text-sm">Fehler beim Laden der Beläge</div>
                            </div>
                          );
                        }
                        
                        if (Object.keys(toppingBreakdown).length === 0) {
                          return null;
                        }
                        
                        const toppingItems = [];
                        Object.entries(toppingBreakdown).forEach(([topping, counts]) => {
                          const toppingName = finalToppingLabels[topping] || topping;
                          
                          // Create parts array for Hell and Korn counts
                          const parts = [];
                          if (counts.white > 0) {
                            parts.push(`${counts.white}x Hell`);
                          }
                          if (counts.seeded > 0) {
                            parts.push(`${counts.seeded}x Korn`);
                          }
                          
                          // Only add if there are actual counts
                          if (parts.length > 0) {
                            toppingItems.push(
                              <div key={topping} className="flex items-center gap-4">
                                <span className="text-gray-600 font-medium min-w-[100px]">{toppingName}:</span>
                                <span className="text-gray-600">{parts.join(' | ')}</span>
                              </div>
                            );
                          }
                        });
                        
                        if (toppingItems.length === 0) {
                          return null;
                        }
                        
                        return (
                          <div>
                            <div className="font-semibold text-gray-700 mb-2">Beläge:</div>
                            <div className="ml-4 space-y-1">
                              {toppingItems}
                            </div>
                          </div>
                        );
                      })()}
                    </div>
                  </div>
                </div>
                
                {/* Lunch Summary Box */}
                {(() => {
                  const lunchCount = dailySummary.employee_orders ? 
                    Object.values(dailySummary.employee_orders).filter(emp => emp.has_lunch).length : 0;
                  
                  if (lunchCount > 0) {
                    return (
                      <div className="w-48 bg-orange-50 border border-orange-200 rounded-lg p-4">
                        <h4 className="text-lg font-semibold text-orange-800 mb-3">🍽️ Mittagessen</h4>
                        <div className="text-center">
                          <div className="text-3xl font-bold text-orange-700 mb-1">{lunchCount}</div>
                          <div className="text-sm text-orange-600">Bestellungen</div>
                        </div>
                      </div>
                    );
                  }
                  return null;
                })()}
              </div>

              {/* Matrix-Style Employee Orders Table */}
              <div className="mb-8">
                <h3 className="text-lg font-semibold mb-4">Detaillierte Mitarbeiter-Bestellungen</h3>
                
                {dailySummary && dailySummary.employee_orders && Object.keys(dailySummary.employee_orders).length > 0 ? (
                  (() => {
                    try {
                      // Filter employees who have any breakfast bookings
                      const employeesWithBookings = Object.entries(dailySummary.employee_orders).filter(([employeeName, employeeData]) => {
                        if (!employeeData) return false;
                        const hasRolls = (employeeData.white_halves || 0) > 0 || (employeeData.seeded_halves || 0) > 0;
                        const hasEggs = (employeeData.boiled_eggs || 0) > 0;
                        const hasToppings = employeeData.toppings && Object.keys(employeeData.toppings).length > 0;
                        const hasLunch = employeeData.has_lunch;
                        return hasRolls || hasEggs || hasToppings || hasLunch;
                      });
                      
                      if (employeesWithBookings.length === 0) {
                        return (
                          <div className="text-center py-4 text-gray-500">
                            Keine Mitarbeiter-Bestellungen für heute
                          </div>
                        );
                      }
                      
                      // Get all unique toppings
                      const allToppings = new Set();
                      employeesWithBookings.forEach(([employeeName, employeeData]) => {
                        if (employeeData && employeeData.toppings) {
                          Object.keys(employeeData.toppings).forEach(topping => {
                            allToppings.add(topping);
                          });
                        }
                      });
                      const toppingsList = Array.from(allToppings);
                      
                      // Count lunch selections
                      const totalLunchCount = employeesWithBookings.filter(([name, data]) => data && data.has_lunch).length;
                      
                      return (
                        <div className="overflow-x-auto">
                          <table className="w-full border-collapse border border-gray-300">
                            <thead>
                              <tr className="bg-blue-100">
                                <th className="border border-gray-300 px-3 py-2 text-left font-semibold">Mitarbeiter</th>
                                {toppingsList.map(topping => (
                                  <th key={topping} className="border border-gray-300 px-2 py-2 text-center font-semibold text-sm">
                                    {String(finalToppingLabels[topping] || topping)}
                                  </th>
                                ))}
                                <th className="border border-gray-300 px-2 py-2 text-center font-semibold text-sm bg-yellow-50">
                                  🥚 Eier
                                </th>
                                <th className="border border-gray-300 px-2 py-2 text-center font-semibold text-sm bg-purple-50">
                                  🍽️ Mittagessen
                                </th>
                              </tr>
                            </thead>
                            <tbody>
                              {employeesWithBookings.map(([employeeName, employeeData]) => (
                                <tr key={employeeName} className="hover:bg-gray-50">
                                  <td className="border border-gray-300 px-3 py-2 font-semibold">
                                    {String(employeeName)}
                                  </td>
                                  {toppingsList.map(topping => {
                                    const toppingCount = (employeeData && employeeData.toppings && employeeData.toppings[topping]) || 0;
                                    
                                    if (toppingCount === 0) {
                                      return (
                                        <td key={topping} className="border border-gray-300 px-2 py-2 text-center text-sm text-gray-400">
                                          -
                                        </td>
                                      );
                                    }
                                    
                                    const whiteHalves = (employeeData && employeeData.white_halves) || 0;
                                    const seededHalves = (employeeData && employeeData.seeded_halves) || 0;
                                    const totalHalves = whiteHalves + seededHalves;
                                    
                                    if (totalHalves === 0) {
                                      return (
                                        <td key={topping} className="border border-gray-300 px-2 py-2 text-center text-sm font-semibold">
                                          {toppingCount}
                                        </td>
                                      );
                                    }
                                    
                                    // Calculate proportional distribution
                                    const whiteRatio = whiteHalves / totalHalves;
                                    const seededRatio = seededHalves / totalHalves;
                                    const whiteCount = Math.round(toppingCount * whiteRatio);
                                    const seededCount = Math.round(toppingCount * seededRatio);
                                    
                                    // Format with abbreviations
                                    const parts = [];
                                    if (seededCount > 0) parts.push(`${seededCount}xK`);
                                    if (whiteCount > 0) parts.push(`${whiteCount}x`);
                                    
                                    return (
                                      <td key={topping} className="border border-gray-300 px-2 py-2 text-center text-sm font-semibold">
                                        {parts.join(' ') || toppingCount.toString()}
                                      </td>
                                    );
                                  })}
                                  <td className="border border-gray-300 px-2 py-2 text-center text-sm bg-yellow-50 font-semibold">
                                    {(employeeData && employeeData.boiled_eggs) || 0}
                                  </td>
                                  <td className="border border-gray-300 px-2 py-2 text-center text-sm bg-purple-50 font-semibold">
                                    {(employeeData && employeeData.has_lunch) ? 'X' : '-'}
                                  </td>
                                </tr>
                              ))}
                              
                              {/* Totals Row */}
                              <tr className="bg-gray-100 font-bold">
                                <td className="border border-gray-300 px-3 py-2">
                                  <strong>Gesamt</strong>
                                </td>
                                {toppingsList.map(topping => {
                                  let totalWhite = 0;
                                  let totalSeeded = 0;
                                  
                                  employeesWithBookings.forEach(([name, employeeData]) => {
                                    if (employeeData && employeeData.toppings && employeeData.toppings[topping]) {
                                      const count = employeeData.toppings[topping];
                                      const whiteHalves = employeeData.white_halves || 0;
                                      const seededHalves = employeeData.seeded_halves || 0;
                                      const totalHalves = whiteHalves + seededHalves;
                                      
                                      if (totalHalves > 0) {
                                        totalWhite += Math.round(count * (whiteHalves / totalHalves));
                                        totalSeeded += Math.round(count * (seededHalves / totalHalves));
                                      }
                                    }
                                  });
                                  
                                  const parts = [];
                                  if (totalSeeded > 0) parts.push(`${totalSeeded}xK`);
                                  if (totalWhite > 0) parts.push(`${totalWhite}x`);
                                  
                                  return (
                                    <td key={topping} className="border border-gray-300 px-2 py-2 text-center text-sm font-bold">
                                      {parts.join(' ') || '-'}
                                    </td>
                                  );
                                })}
                                <td className="border border-gray-300 px-2 py-2 text-center text-sm bg-yellow-100 font-bold">
                                  {dailySummary.total_boiled_eggs || 0}
                                </td>
                                <td className="border border-gray-300 px-2 py-2 text-center text-sm bg-purple-100 font-bold">
                                  {totalLunchCount}
                                </td>
                              </tr>
                            </tbody>
                          </table>
                          
                          {/* Legend */}
                          <div className="mt-4 text-sm text-gray-600 bg-gray-50 p-3 rounded">
                            <strong>Legende:</strong> K = Körnerbrötchen, ohne K = Helle Brötchen (z.B. "2xK 1x" = 2x auf Körnern + 1x auf Hell), X = Mittagessen bestellt
                          </div>
                        </div>
                      );
                    } catch (error) {
                      console.error('Error rendering employee table:', error);
                      return (
                        <div className="text-center py-4 text-red-500">
                          Fehler beim Laden der Mitarbeiter-Tabelle
                        </div>
                      );
                    }
                  })()
                ) : (
                  <div className="text-center py-4 text-gray-500">
                    Keine Mitarbeiter-Bestellungen für heute
                  </div>
                )}
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


// Unified Menu & Price Management Tab Component
const UnifiedMenuManagementTab = ({ breakfastMenu, toppingsMenu, drinksMenu, sweetsMenu, onUpdatePrice, onCreateMenuItem, onDeleteMenuItem, fetchMenus, currentDepartment }) => {
  const [showNewDrink, setShowNewDrink] = useState(false);
  const [showNewSweet, setShowNewSweet] = useState(false);
  const [showNewBreakfast, setShowNewBreakfast] = useState(false);
  const [showNewTopping, setShowNewTopping] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  const [editForm, setEditForm] = useState({ name: '', price: '' });

  const rollTypeLabels = {
    'weiss': 'Helles Brötchen',
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
      if (!currentDepartment?.department_id) {
        alert('Fehler: Keine Abteilungs-ID verfügbar');
        return;
      }

      const updateData = {
        name: editForm.name,
        price: parseFloat(editForm.price)
      };
      
      const departmentId = currentDepartment.department_id;
      await axios.put(`${API}/department-admin/menu/${editingItem.category}/${editingItem.id}?department_id=${departmentId}`, updateData);
      
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

        {/* Eier & Kaffee */}
        <CoffeeAndEggsManagement />

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
          onCreateItem={(toppingId, toppingName, price) => onCreateMenuItem('toppings', toppingId, toppingName, price)}
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
  const [deleting, setDeleting] = useState(null);
  const [editingLunchPrice, setEditingLunchPrice] = useState(null); // date being edited
  const [lunchPriceInput, setLunchPriceInput] = useState(''); // temporary input value
  const [updatingLunchPrice, setUpdatingLunchPrice] = useState(null); // date being updated

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

  const deleteBreakfastDay = async (date) => {
    if (window.confirm(`Alle Frühstücks-Bestellungen für ${formatDate(date)} wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden und wird die Mitarbeiter-Salden entsprechend anpassen.`)) {
      try {
        setDeleting(date);
        await axios.delete(`${API}/department-admin/breakfast-day/${currentDepartment.department_id}/${date}`);
        alert('Frühstücks-Tag erfolgreich gelöscht');
        // Refresh the history
        await fetchBreakfastHistory();
      } catch (error) {
        console.error('Fehler beim Löschen des Frühstücks-Tags:', error);
        alert('Fehler beim Löschen des Frühstücks-Tags');
      } finally {
        setDeleting(null);
      }
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

  const startEditingLunchPrice = (date, currentPrice) => {
    setEditingLunchPrice(date);
    setLunchPriceInput(currentPrice.toFixed(2));
  };

  const cancelEditingLunchPrice = () => {
    setEditingLunchPrice(null);
    setLunchPriceInput('');
  };

  const updateLunchPrice = async (date) => {
    const newPrice = parseFloat(lunchPriceInput);
    if (isNaN(newPrice) || newPrice < 0) {
      alert('Bitte gültigen Preis eingeben');
      return;
    }

    try {
      setUpdatingLunchPrice(date);
      await axios.put(`${API}/daily-lunch-settings/${currentDepartment.department_id}/${date}?lunch_price=${newPrice}`);
      
      // Refresh the history to show updated prices
      await fetchBreakfastHistory();
      
      // Clear editing state
      setEditingLunchPrice(null);
      setLunchPriceInput('');
      
      alert(`Mittagessen-Preis für ${formatDate(date)} erfolgreich auf €${newPrice.toFixed(2)} aktualisiert`);
    } catch (error) {
      console.error('Fehler beim Aktualisieren des Mittagessen-Preises:', error);
      alert('Fehler beim Aktualisieren des Mittagessen-Preises');
    } finally {
      setUpdatingLunchPrice(null);
    }
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
      <h3 className="text-lg font-semibold mb-6">Bestellverlauf - {currentDepartment.department_name}</h3>

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
                  className={`p-6 hover:bg-gray-50 ${
                    selectedDate === day.date ? 'bg-blue-50' : ''
                  }`}
                >
                  {/* Day Summary Header */}
                  <div className="flex justify-between items-center">
                    <div 
                      className="flex-1 cursor-pointer"
                      onClick={() => setSelectedDate(selectedDate === day.date ? null : day.date)}
                    >
                      <h5 className="font-semibold text-lg">{formatDate(day.date)}</h5>
                      <p className="text-sm text-gray-600">
                        {day.total_orders} Bestellungen • €{day.total_amount.toFixed(2)} • 
                        {Object.values(day.employee_orders || {}).filter(emp => emp.has_lunch).length} × 🍽️ Mittag
                      </p>
                    </div>
                    <div className="flex items-center space-x-4 text-sm text-gray-500">
                      <span>Helle: {day.shopping_list.weiss?.whole_rolls || 0} Brötchen</span>
                      <span>Körner: {day.shopping_list.koerner?.whole_rolls || 0} Brötchen</span>
                      
                      {/* Lunch Price Management */}
                      <div className="flex items-center space-x-2 bg-orange-50 px-3 py-1 rounded border border-orange-200">
                        <span className="font-medium text-orange-800">Mittagessen:</span>
                        {editingLunchPrice === day.date ? (
                          <div className="flex items-center space-x-1">
                            <input
                              type="number"
                              step="0.01"
                              min="0"
                              value={lunchPriceInput}
                              onChange={(e) => setLunchPriceInput(e.target.value)}
                              className="w-16 px-2 py-1 text-xs border border-orange-300 rounded focus:outline-none focus:border-orange-500"
                              onKeyPress={(e) => {
                                if (e.key === 'Enter') {
                                  updateLunchPrice(day.date);
                                } else if (e.key === 'Escape') {
                                  cancelEditingLunchPrice();
                                }
                              }}
                              autoFocus
                            />
                            <span className="text-orange-600">€</span>
                            <button
                              onClick={() => updateLunchPrice(day.date)}
                              disabled={updatingLunchPrice === day.date}
                              className="px-2 py-1 bg-green-600 text-white text-xs rounded hover:bg-green-700 disabled:bg-gray-400"
                            >
                              {updatingLunchPrice === day.date ? '...' : '✓'}
                            </button>
                            <button
                              onClick={cancelEditingLunchPrice}
                              className="px-2 py-1 bg-gray-400 text-white text-xs rounded hover:bg-gray-500"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center space-x-1">
                            <span className="font-semibold text-orange-600">
                              €{(day.daily_lunch_price || 0).toFixed(2)}
                            </span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                startEditingLunchPrice(day.date, day.daily_lunch_price || 0);
                              }}
                              className="px-2 py-1 bg-orange-600 text-white text-xs rounded hover:bg-orange-700"
                              title="Mittagessen-Preis bearbeiten"
                            >
                              ✏️
                            </button>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex items-center space-x-2 ml-4">
                        {/* Delete Button */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation(); // Prevent expanding/collapsing
                            deleteBreakfastDay(day.date);
                          }}
                          disabled={deleting === day.date}
                          className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                            deleting === day.date 
                              ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                              : 'bg-red-600 text-white hover:bg-red-700'
                          }`}
                          title="Tag löschen"
                        >
                          {deleting === day.date ? 'Wird gelöscht...' : '🗑️ Löschen'}
                        </button>
                        {/* Expand/Collapse Indicator */}
                        <button
                          onClick={() => setSelectedDate(selectedDate === day.date ? null : day.date)}
                          className="px-2 py-1 text-gray-400 hover:text-gray-600"
                        >
                          {selectedDate === day.date ? '▲' : '▼'}
                        </button>
                      </div>
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
                                <span>Helle Brötchen:</span>
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
                                <div>Helle Hälften: {employeeData.white_halves}</div>
                                <div>Körner Hälften: {employeeData.seeded_halves}</div>
                                {employeeData.boiled_eggs > 0 && (
                                  <div>🥚 Gekochte Eier: {employeeData.boiled_eggs}</div>
                                )}
                                {employeeData.has_coffee && (
                                  <div>☕ Kaffee: Ja</div>
                                )}
                                {employeeData.has_lunch && (
                                  <div>🍽️ Mittagessen: Ja</div>
                                )}
                                <div className="pt-1 border-t">
                                  <strong>Total: €{employeeData.total_amount.toFixed(2)}</strong>
                                </div>
                                {Object.keys(employeeData.toppings).length > 0 && (
                                  <div className="pt-1 text-xs">
                                    Beläge: {Object.entries(employeeData.toppings).map(([topping, count]) => {
                                      // Handle both string and object toppings
                                      const toppingName = typeof topping === 'string' ? topping : (topping.name || topping.topping_type || 'Unknown');
                                      return `${count}x ${toppingName}`;
                                    }).join(', ')}
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
  const [audioEnabled, setAudioEnabled] = useState(
    localStorage.getItem('canteenAudioEnabled') !== 'false'
  );

  useEffect(() => {
    fetchBreakfastStatus();
  }, [currentDepartment]);

  const toggleAudio = () => {
    const newAudioState = !audioEnabled;
    setAudioEnabled(newAudioState);
    localStorage.setItem('canteenAudioEnabled', newAudioState.toString());
    
    // Play test sound if enabling
    if (newAudioState) {
      playSucessSound();
    }
  };

  const fetchBreakfastStatus = async () => {
    try {
      const response = await axios.get(`${API}/breakfast-status/${currentDepartment.department_id}`);
      setBreakfastStatus(response.data);
    } catch (error) {
      console.error('Fehler beim Laden des Frühstück-Status:', error);
    }
  };

  const changeEmployeePassword = async () => {
    if (!newEmployeePassword) {
      alert('Bitte neues Mitarbeiter-Passwort eingeben');
      return;
    }

    if (newAdminPassword && newEmployeePassword === newAdminPassword) {
      alert('Mitarbeiter- und Admin-Passwort müssen unterschiedlich sein');
      return;
    }

    try {
      await axios.put(`${API}/department-admin/change-employee-password/${currentDepartment.department_id}?new_password=${newEmployeePassword}`);
      alert('Mitarbeiter-Passwort erfolgreich geändert');
      setNewEmployeePassword('');
    } catch (error) {
      console.error('Fehler beim Ändern des Mitarbeiter-Passworts:', error);
      alert('Fehler beim Ändern des Mitarbeiter-Passworts');
    }
  };

  const changeAdminPassword = async () => {
    if (!newAdminPassword) {
      alert('Bitte neues Admin-Passwort eingeben');
      return;
    }

    if (newEmployeePassword && newEmployeePassword === newAdminPassword) {
      alert('Mitarbeiter- und Admin-Passwort müssen unterschiedlich sein');
      return;
    }

    try {
      await axios.put(`${API}/department-admin/change-admin-password/${currentDepartment.department_id}?new_password=${newAdminPassword}`);
      alert('Admin-Passwort erfolgreich geändert');
      setNewAdminPassword('');
    } catch (error) {
      console.error('Fehler beim Ändern des Admin-Passworts:', error);
      alert('Fehler beim Ändern des Admin-Passworts');
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
              <div className="mt-2">
                <button
                  onClick={changeEmployeePassword}
                  disabled={!newEmployeePassword}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                >
                  Mitarbeiter-Passwort ändern
                </button>
              </div>
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
              <div className="mt-2">
                <button
                  onClick={changeAdminPassword}
                  disabled={!newAdminPassword}
                  className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-sm"
                >
                  Admin-Passwort ändern
                </button>
              </div>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            <p><strong>Hinweis:</strong></p>
            <ul className="list-disc list-inside space-y-1">
              <li>Passwörter können unabhängig voneinander geändert werden</li>
              <li>Beide Passwörter müssen unterschiedlich sein</li>
              <li>Nach der Änderung müssen sich betroffene Benutzer neu anmelden</li>
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

        {/* Sound Settings */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-6">
          <h4 className="text-md font-semibold mb-4 text-green-800">🔊 Sound-Einstellungen</h4>
          
          <div className="flex items-center justify-between p-4 bg-white border border-green-300 rounded">
            <div>
              <div className="font-medium">Bestätigungs-Sound bei Bestellungen</div>
              <div className="text-sm text-gray-600 mt-1">
                Kurzer Bestätigungston wenn eine Bestellung erfolgreich gespeichert wird
              </div>
            </div>
            <button
              onClick={toggleAudio}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 ${
                audioEnabled ? 'bg-green-600' : 'bg-gray-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  audioEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
          
          <div className="mt-4 text-sm text-gray-600">
            <p><strong>Info:</strong></p>
            <ul className="list-disc list-inside space-y-1">
              <li>Diese Einstellung gilt für alle Benutzer dieses Browsers</li>
              <li>Sound wird nur bei erfolgreich gespeicherten Bestellungen abgespielt</li>
              <li>Beim Aktivieren wird ein Test-Sound abgespielt</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

// Coffee and Eggs Management Component
const CoffeeAndEggsManagement = () => {
  const [lunchSettings, setLunchSettings] = useState({ boiled_eggs_price: 0.50, coffee_price: 1.50 });
  const [newBoiledEggsPrice, setNewBoiledEggsPrice] = useState('');
  const [newCoffeePrice, setNewCoffeePrice] = useState('');

  const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  useEffect(() => {
    fetchLunchSettings();
  }, []);

  const fetchLunchSettings = async () => {
    try {
      const response = await axios.get(`${API}/api/lunch-settings`);
      setLunchSettings(response.data);
      setNewBoiledEggsPrice((response.data.boiled_eggs_price || 0.50).toFixed(2));
      setNewCoffeePrice((response.data.coffee_price || 1.50).toFixed(2));
    } catch (error) {
      console.error('Fehler beim Laden der Lunch-Einstellungen:', error);
    }
  };

  const updateBoiledEggsPrice = async () => {
    if (!newBoiledEggsPrice || isNaN(parseFloat(newBoiledEggsPrice))) {
      alert('Bitte gültigen Kochei-Preis eingeben');
      return;
    }

    try {
      await axios.put(`${API}/api/lunch-settings/boiled-eggs-price?price=${parseFloat(newBoiledEggsPrice)}`);
      await fetchLunchSettings();
      alert('Kochei-Preis erfolgreich aktualisiert');
    } catch (error) {
      console.error('Fehler beim Aktualisieren des Kochei-Preises:', error);
      alert('Fehler beim Aktualisieren des Kochei-Preises');
    }
  };

  const updateCoffeePrice = async () => {
    if (!newCoffeePrice || isNaN(parseFloat(newCoffeePrice))) {
      alert('Bitte gültigen Kaffee-Preis eingeben');
      return;
    }

    try {
      await axios.put(`${API}/api/lunch-settings/coffee-price?price=${parseFloat(newCoffeePrice)}`);
      await fetchLunchSettings();
      alert('Kaffee-Preis erfolgreich aktualisiert');
    } catch (error) {
      console.error('Fehler beim Aktualisieren des Kaffee-Preises:', error);
      alert('Fehler beim Aktualisieren des Kaffee-Preises');
    }
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h4 className="text-md font-semibold text-gray-700 border-b pb-2">🥚☕ Eier & Kaffee</h4>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Gekochte Eier */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="mb-4">
            <h5 className="text-sm font-semibold mb-2 text-yellow-800">🥚 Gekochte Eier</h5>
            <div className="text-lg font-bold text-yellow-600 mb-2">
              {(lunchSettings.boiled_eggs_price || 0.50).toFixed(2)} € <span className="text-sm text-gray-500">pro Ei</span>
            </div>
          </div>

          <div className="border-t border-yellow-300 pt-4">
            <h6 className="text-xs font-semibold mb-2 text-gray-700">Preis ändern</h6>
            <div className="flex items-center gap-2">
              <input
                type="number"
                step="0.01"
                min="0"
                value={newBoiledEggsPrice}
                onChange={(e) => setNewBoiledEggsPrice(e.target.value)}
                className="w-20 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:border-yellow-500 text-sm"
                placeholder="0.50"
              />
              <span className="text-yellow-600 text-sm">€</span>
              <button
                onClick={updateBoiledEggsPrice}
                className="bg-yellow-600 text-white px-2 py-1 rounded hover:bg-yellow-700 transition-colors text-xs"
              >
                Update
              </button>
            </div>
          </div>
        </div>

        {/* Kaffee */}
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="mb-4">
            <h5 className="text-sm font-semibold mb-2 text-amber-800">☕ Kaffee</h5>
            <div className="text-lg font-bold text-amber-600 mb-2">
              {(lunchSettings.coffee_price || 1.50).toFixed(2)} € <span className="text-sm text-gray-500">pro Tag</span>
            </div>
          </div>

          <div className="border-t border-amber-300 pt-4">
            <h6 className="text-xs font-semibold mb-2 text-gray-700">Preis ändern</h6>
            <div className="flex items-center gap-2">
              <input
                type="number"
                step="0.01"
                min="0"
                value={newCoffeePrice}
                onChange={(e) => setNewCoffeePrice(e.target.value)}
                className="w-20 px-2 py-1 border border-gray-300 rounded focus:outline-none focus:border-amber-500 text-sm"
                placeholder="1.50"
              />
              <span className="text-amber-600 text-sm">€</span>
              <button
                onClick={updateCoffeePrice}
                className="bg-amber-600 text-white px-2 py-1 rounded hover:bg-amber-700 transition-colors text-xs"
              >
                Update
              </button>
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