const axios = require('axios');

const BACKEND_URL = 'http://localhost:8001';
const API = `${BACKEND_URL}/api`;

async function testAuthentication() {
    console.log('=== TESTING AUTHENTICATION ===');
    
    try {
        // Test 1: Get departments
        console.log('\n1. Testing departments endpoint...');
        const deptResponse = await axios.get(`${API}/departments`);
        console.log(`✅ Found ${deptResponse.data.length} departments`);
        console.log('Departments:', deptResponse.data.map(d => d.name));
        
        // Test 2: Department admin login
        console.log('\n2. Testing department admin login...');
        const loginResponse = await axios.post(`${API}/login/department-admin`, {
            department_name: '1. Wachabteilung',
            admin_password: 'admin1'
        });
        console.log('✅ Admin login successful:', loginResponse.data);
        
        // Test 3: Get menu items
        console.log('\n3. Testing menu endpoints...');
        const [breakfast, toppings] = await Promise.all([
            axios.get(`${API}/menu/breakfast`),
            axios.get(`${API}/menu/toppings`)
        ]);
        console.log(`✅ Found ${breakfast.data.length} breakfast items`);
        console.log(`✅ Found ${toppings.data.length} topping items`);
        
        // Test 4: Create new breakfast item
        console.log('\n4. Testing new breakfast item creation...');
        const newBreakfast = await axios.post(`${API}/department-admin/menu/breakfast`, {
            roll_type: 'weiss',
            price: 0.55
        });
        console.log('✅ New breakfast item created:', newBreakfast.data);
        
        // Test 5: Create new topping item
        console.log('\n5. Testing new topping item creation...');
        const newTopping = await axios.post(`${API}/department-admin/menu/toppings`, {
            topping_type: 'ruehrei',
            price: 0.00
        });
        console.log('✅ New topping item created:', newTopping.data);
        
        // Test 6: Delete the created items
        console.log('\n6. Testing item deletion...');
        await axios.delete(`${API}/department-admin/menu/breakfast/${newBreakfast.data.id}`);
        console.log('✅ Breakfast item deleted');
        
        await axios.delete(`${API}/department-admin/menu/toppings/${newTopping.data.id}`);
        console.log('✅ Topping item deleted');
        
        console.log('\n=== ALL BACKEND TESTS PASSED ===');
        
    } catch (error) {
        console.error('❌ Test failed:', error.response?.data || error.message);
    }
}

testAuthentication();