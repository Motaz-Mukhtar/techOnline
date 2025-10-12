#!/usr/bin/env python3
"""
Script to test product form method override functionality
"""

import sys
import os
import requests
import json

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_product_form_method_override():
    """Test that the product form correctly handles method override for updates"""
    
    # Test credentials
    email = "testuser@example.com"
    password = "testpass123"
    
    print("Testing product form method override functionality...")
    
    # Step 1: Login to get session
    session = requests.Session()
    
    print("1. Logging in...")
    login_page = session.get('http://127.0.0.1:5000/login')
    print(f"   Login page status: {login_page.status_code}")
    
    login_data = {
        'email': email,
        'password': password
    }
    
    login_response = session.post('http://127.0.0.1:5000/login', data=login_data)
    print(f"   Login response status: {login_response.status_code}")
    
    if login_response.status_code != 200 or '/shop' not in login_response.url:
        print("   ❌ Login failed!")
        return False
    
    print("   ✅ Login successful")
    
    # Step 2: Get JWT token
    print("2. Getting JWT token...")
    token_response = session.get('http://127.0.0.1:5000/api/token')
    print(f"   Token endpoint status: {token_response.status_code}")
    
    if token_response.status_code != 200:
        print(f"   ❌ Token endpoint failed with status {token_response.status_code}")
        return False
    
    token_data = token_response.json()
    jwt_token = token_data.get('access_token')
    
    if not jwt_token:
        print("   ❌ No JWT token received!")
        return False
    
    print(f"   ✅ JWT token received: {jwt_token[:50]}...")
    
    # Step 3: Create a product via form submission
    print("3. Creating a product via form submission...")
    
    create_form_data = {
        'product_name': 'Test Product for Method Override',
        'description': 'This product will be updated to test method override',
        'price': '149.99',
        'category_id': '1',
        'stock_quantity': '15',
        'min_stock_level': '3'
    }
    
    # Submit form to create product
    create_response = session.post('http://127.0.0.1:5000/product_form', data=create_form_data)
    print(f"   Create form response status: {create_response.status_code}")
    print(f"   Create form response URL: {create_response.url}")
    
    if create_response.status_code != 200 or 'shop' not in create_response.url:
        print("   ❌ Product creation via form failed!")
        return False
    
    print("   ✅ Product created via form")
    
    # Step 4: Get the created product ID from API
    print("4. Finding the created product...")
    
    headers = {'Authorization': f'Bearer {jwt_token}'}
    products_response = requests.get('http://127.0.0.1:5001/api/v1/products', headers=headers)
    
    if products_response.status_code != 200:
        print(f"   ❌ Failed to get products: {products_response.status_code}")
        return False
    
    products_data = products_response.json()
    products = products_data.get('data', [])
    
    # Find our test product
    test_product = None
    for product in products:
        if product.get('product_name') == 'Test Product for Method Override':
            test_product = product
            break
    
    if not test_product:
        print("   ❌ Created product not found!")
        return False
    
    product_id = test_product['id']
    print(f"   ✅ Found created product with ID: {product_id}")
    
    # Step 5: Update the product via form submission with method override
    print("5. Updating product via form with method override...")
    
    update_form_data = {
        '_method': 'PUT',  # Method override
        'product_id': product_id,
        'product_name': 'Updated Test Product',
        'description': 'This product was updated using method override',
        'price': '199.99',
        'category_id': '1',
        'stock_quantity': '20',
        'min_stock_level': '5'
    }
    
    # Submit form to update product
    update_response = session.post(f'http://127.0.0.1:5000/product_form/{product_id}', data=update_form_data)
    print(f"   Update form response status: {update_response.status_code}")
    print(f"   Update form response URL: {update_response.url}")
    
    if update_response.status_code != 200 or 'shop' not in update_response.url:
        print("   ❌ Product update via form failed!")
        return False
    
    print("   ✅ Product updated via form")
    
    # Step 6: Verify the update worked
    print("6. Verifying product update...")
    
    verify_response = requests.get(f'http://127.0.0.1:5001/api/v1/products/{product_id}', headers=headers)
    
    if verify_response.status_code != 200:
        print(f"   ❌ Failed to verify product: {verify_response.status_code}")
        return False
    
    verify_data = verify_response.json()
    updated_product = verify_data.get('data', {})
    
    if updated_product.get('product_name') != 'Updated Test Product':
        print(f"   ❌ Product name not updated! Expected: 'Updated Test Product', Got: '{updated_product.get('product_name')}'")
        return False
    
    if float(updated_product.get('price', 0)) != 199.99:
        print(f"   ❌ Product price not updated! Expected: 199.99, Got: {updated_product.get('price')}")
        return False
    
    print("   ✅ Product successfully updated with correct values")
    
    # Step 7: Clean up - delete the test product
    print("7. Cleaning up test product...")
    
    delete_response = requests.delete(f'http://127.0.0.1:5001/api/v1/products/{product_id}', headers=headers)
    print(f"   Delete response status: {delete_response.status_code}")
    
    if delete_response.status_code == 200:
        print("   ✅ Test product cleaned up successfully")
    else:
        print(f"   ⚠️ Failed to clean up test product: {delete_response.status_code}")
    
    return True

if __name__ == "__main__":
    success = test_product_form_method_override()
    if success:
        print("\n🎉 Product form method override test PASSED!")
        print("✅ Form correctly handles POST for creation")
        print("✅ Form correctly handles POST with _method=PUT for updates")
        print("✅ Backend properly processes method override")
    else:
        print("\n❌ Product form method override test FAILED!")