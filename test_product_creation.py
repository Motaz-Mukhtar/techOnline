#!/usr/bin/env python3
"""
Test script to verify product creation functionality through the web interface.
"""

import requests
import json

def test_product_creation():
    """Test the complete product creation flow."""
    
    # Base URLs
    web_base_url = 'http://127.0.0.1:5000'
    api_base_url = 'http://127.0.0.1:5001/api/v1'
    
    # Test data
    test_product = {
        'product_name': 'Test Gaming Laptop',
        'price': 1299.99,
        'description': 'High-performance gaming laptop with RTX graphics card and fast SSD storage.',
        'category_id': 2,  # Computers
        'stock_quantity': 15,
        'min_stock_level': 3,
        'customer_id': 'f61404cf-4c4a-4981-91f4-d9934ecb65f0'  # Existing customer ID
    }
    
    print("Testing product creation...")
    
    # First, let's test if we can create a product directly via API with a simple token
    try:
        # Create a simple JWT token for testing
        import jwt
        import datetime
        
        payload = {
            'customer_id': test_product['customer_id'],
            'email': 'motazksa2@gmail.com',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }
        
        token = jwt.encode(payload, 'your-secret-key-change-in-production', algorithm='HS256')
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
        
        print(f"Generated token: {token[:50]}...")
        
        # Test API endpoint
        response = requests.post(f'{api_base_url}/products', json=test_product, headers=headers, timeout=30)
        
        print(f"API Response Status: {response.status_code}")
        print(f"API Response: {response.text}")
        
        if response.status_code == 201:
            print("✅ Product created successfully via API!")
            
            # Now test if products are visible in the shop
            shop_response = requests.get(f'{api_base_url}/products', timeout=30)
            if shop_response.status_code == 200:
                products_data = shop_response.json()
                print(f"✅ Found {len(products_data.get('data', {}).get('products', []))} products in shop")
            else:
                print(f"❌ Error fetching products: {shop_response.status_code}")
        else:
            print(f"❌ Failed to create product: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")

if __name__ == '__main__':
    test_product_creation()