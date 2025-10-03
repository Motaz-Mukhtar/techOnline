#!/usr/bin/env python3
"""
Script to test product creation using admin API key.
"""

import requests
import json

def test_product_creation():
    """
    Test creating a product using the admin API key.
    """
    # Admin API key from the API server
    admin_api_key = 'admin_key_123'
    
    # API endpoint
    api_url = 'http://127.0.0.1:5001/api/v1/products'
    
    # Test product data
    product_data = {
        'product_name': 'Test Gaming Laptop - Admin',
        'description': 'High-performance gaming laptop for testing admin API access',
        'price': 1299.99,
        'category_id': '1',  # Assuming category 1 exists
        'stock_quantity': 10,
        'min_stock_level': 2
    }
    
    # Headers with admin API key
    headers = {
        'Authorization': f'API-Key {admin_api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("Testing product creation with admin API key...")
        print(f"API URL: {api_url}")
        print(f"Product: {product_data['product_name']}")
        print(f"API Key: {admin_api_key}")
        print("\nSending request...")
        
        # Send POST request
        response = requests.post(api_url, json=product_data, headers=headers, timeout=30)
        
        print(f"\nResponse Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"Response Data: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
        
        if response.status_code == 201:
            print("\n✅ SUCCESS: Product created successfully!")
            return True
        else:
            print(f"\n❌ FAILED: Product creation failed with status {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_product_creation()
    if success:
        print("\n🎉 Product creation test completed successfully!")
    else:
        print("\n💥 Product creation test failed!")