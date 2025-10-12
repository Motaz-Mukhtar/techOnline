import requests
import re

def test_registration_and_form():
    print("Testing user registration and form method override...")
    
    session = requests.Session()
    
    # Step 1: Register a new user
    print("1. Registering a new user...")
    register_page = session.get('http://127.0.0.1:5000/register')
    print(f"   Register page status: {register_page.status_code}")
    
    # Extract CSRF token from registration form
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', register_page.text)
    csrf_token = csrf_match.group(1) if csrf_match else None
    print(f"   CSRF token: {csrf_token[:20]}..." if csrf_token else "   No CSRF token found")
    
    # Register new user
    register_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'testuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'phone_number': '1234567890',
        'csrf_token': csrf_token
    }
    
    register_response = session.post('http://127.0.0.1:5000/register', data=register_data)
    print(f"   Registration response status: {register_response.status_code}")
    print(f"   Registration response URL: {register_response.url}")
    
    if 'register' in register_response.url:
        print("   ❌ Registration failed")
        return False
    
    print("   ✅ Registration successful")
    
    # Step 2: Login with the new user
    print("2. Logging in with new user...")
    login_page = session.get('http://127.0.0.1:5000/login')
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', login_page.text)
    csrf_token = csrf_match.group(1) if csrf_match else None
    
    login_data = {
        'email': 'testuser@example.com',
        'password': 'password123',
        'csrf_token': csrf_token
    }
    
    login_response = session.post('http://127.0.0.1:5000/login', data=login_data)
    print(f"   Login response status: {login_response.status_code}")
    print(f"   Login response URL: {login_response.url}")
    
    if 'login' in login_response.url:
        print("   ❌ Login failed")
        return False
    
    print("   ✅ Login successful")
    
    # Step 3: Test product form access
    print("3. Testing product form access...")
    form_page = session.get('http://127.0.0.1:5000/product_form')
    print(f"   Product form page status: {form_page.status_code}")
    
    if form_page.status_code == 200:
        print("   ✅ Product form accessible")
        
        # Check if form contains method override field
        if '_method' in form_page.text:
            print("   ✅ Form contains _method field for method override")
        else:
            print("   ❌ Form does not contain _method field")
            
        # Check form method attribute
        method_match = re.search(r'<form[^>]*method="([^"]+)"', form_page.text)
        if method_match:
            print(f"   Form method: {method_match.group(1)}")
        
        # Check form action attribute
        action_match = re.search(r'<form[^>]*action="([^"]+)"', form_page.text)
        if action_match:
            print(f"   Form action: {action_match.group(1)}")
        
        # Step 4: Test creating a product
        print("4. Testing product creation...")
        csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', form_page.text)
        csrf_token = csrf_match.group(1) if csrf_match else None
        
        product_data = {
            'product_name': 'Test Product Method Override',
            'description': 'Testing method override functionality',
            'price': '99.99',
            'category_id': '1',
            'stock_quantity': '10',
            'min_stock_level': '2',
            'csrf_token': csrf_token
        }
        
        create_response = session.post('http://127.0.0.1:5000/product_form', data=product_data)
        print(f"   Create response status: {create_response.status_code}")
        print(f"   Create response URL: {create_response.url}")
        
        if create_response.status_code == 200 and 'shop' in create_response.url:
            print("   ✅ Product created successfully")
            return True
        else:
            print("   ❌ Product creation failed")
            return False
    else:
        print("   ❌ Cannot access product form")
        return False

if __name__ == "__main__":
    success = test_registration_and_form()
    if success:
        print("\n🎉 Registration and form test PASSED!")
        print("✅ User registration works")
        print("✅ Login works")
        print("✅ Product form is accessible")
        print("✅ Product creation works")
    else:
        print("\n❌ Registration and form test FAILED!")