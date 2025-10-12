#!/usr/bin/env python3
import requests
import re

def test_signup_and_form():
    base_url = 'http://127.0.0.1:5000'
    session = requests.Session()
    
    print("Testing user signup and product form functionality...")
    
    # Step 1: Get signup page and extract CSRF token
    print("\n1. Getting signup page...")
    signup_response = session.get(f'{base_url}/signup')
    print(f"Signup page status: {signup_response.status_code}")
    
    if signup_response.status_code != 200:
        print(f"Failed to access signup page: {signup_response.status_code}")
        return False
    
    # Extract CSRF token using regex
    csrf_pattern = r'<input[^>]*name=["\']csrf_token["\'][^>]*value=["\']([^"\'>]+)["\']'
    csrf_match = re.search(csrf_pattern, signup_response.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"Found CSRF token: {csrf_token[:20]}...")
    else:
        print("No CSRF token found on signup page")
        return False
    
    # Step 2: Register a new user
    print("\n2. Registering new user...")
    signup_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'testuser@example.com',
        'password': 'password123',
        'confirm_password': 'password123',
        'address': '123 Test Street',
        'csrf_token': csrf_token,
        'submit': 'Register'
    }
    
    signup_submit_response = session.post(f'{base_url}/signup', data=signup_data)
    print(f"Signup submission status: {signup_submit_response.status_code}")
    print(f"Signup response URL: {signup_submit_response.url}")
    
    # Check if redirected to login page (successful registration)
    if 'login' in signup_submit_response.url:
        print("✓ User registration successful - redirected to login")
    else:
        print("Registration may have failed or user already exists")
        # Continue anyway to test login
    
    # Step 3: Get login page and extract CSRF token
    print("\n3. Getting login page...")
    login_response = session.get(f'{base_url}/login')
    print(f"Login page status: {login_response.status_code}")
    
    if login_response.status_code != 200:
        print(f"Failed to access login page: {login_response.status_code}")
        return False
    
    # Extract CSRF token from login form
    csrf_match = re.search(csrf_pattern, login_response.text)
    if csrf_match:
        csrf_token = csrf_match.group(1)
        print(f"Found login CSRF token: {csrf_token[:20]}...")
    else:
        print("No CSRF token found on login page")
        return False
    
    # Step 4: Login with the registered user
    print("\n4. Logging in...")
    login_data = {
        'email': 'testuser@example.com',
        'password': 'password123',
        'csrf_token': csrf_token
    }
    
    login_submit_response = session.post(f'{base_url}/login', data=login_data)
    print(f"Login submission status: {login_submit_response.status_code}")
    print(f"Login response URL: {login_submit_response.url}")
    
    # Check if redirected to shop (successful login)
    if 'shop' in login_submit_response.url or login_submit_response.url.endswith('/'):
        print("✓ Login successful")
    else:
        print("Login failed")
        return False
    
    # Step 5: Access product form page
    print("\n5. Accessing product form...")
    product_form_response = session.get(f'{base_url}/product_form')
    print(f"Product form status: {product_form_response.status_code}")
    
    if product_form_response.status_code != 200:
        print(f"Failed to access product form: {product_form_response.status_code}")
        return False
    
    # Check for _method field in the form
    method_pattern = r'<input[^>]*name=["\']_method["\'][^>]*value=["\']([^"\'>]+)["\']'
    method_match = re.search(method_pattern, product_form_response.text)
    if method_match:
        print(f"✓ Found _method field with value: {method_match.group(1)}")
    else:
        print("✓ No _method field found (expected for new product creation)")
    
    # Check for form action
    form_pattern = r'<form[^>]*id=["\']productForm["\'][^>]*action=["\']([^"\'>]+)["\']'
    form_match = re.search(form_pattern, product_form_response.text)
    if form_match:
        action = form_match.group(1)
        print(f"✓ Product form found with action: {action}")
    else:
        print("✗ Product form not found")
        return False
    
    print("\n✓ All tests passed! Product form is accessible and properly configured.")
    return True

if __name__ == '__main__':
    test_signup_and_form()