import requests
import json

def test_put_request():
    print("Testing PUT request to API...")
    
    # First, login to get a token
    login_data = {
        'email': 'test@example.com',
        'password': 'password123'
    }
    
    session = requests.Session()
    
    # Login
    login_response = session.post('http://127.0.0.1:5000/login', data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    # Get JWT token
    token_response = session.get('http://127.0.0.1:5000/api/token')
    print(f"Token status: {token_response.status_code}")
    print(f"Token response text: {token_response.text}")
    
    if token_response.status_code == 200:
        try:
            token_data = token_response.json()
            jwt_token = token_data.get('token')
            print(f"JWT token: {jwt_token[:50]}...")
        except:
            print("Failed to parse token response as JSON")
            return
        
        # Get products to find one to update
        headers = {'Authorization': f'Bearer {jwt_token}'}
        products_response = requests.get('http://127.0.0.1:5001/api/v1/products', headers=headers)
        print(f"Products status: {products_response.status_code}")
        
        if products_response.status_code == 200:
            products_data = products_response.json()
            products = products_data.get('data', [])
            
            if products:
                product_id = products[0]['id']
                print(f"Testing PUT on product: {product_id}")
                
                # Test PUT request
                update_data = {
                    'product_name': 'Updated via PUT Test',
                    'description': 'This was updated via direct PUT',
                    'price': '299.99',
                    'category_id': '1',
                    'stock_quantity': '15',
                    'min_stock_level': '3'
                }
                
                put_response = requests.put(
                    f'http://127.0.0.1:5001/api/v1/products/{product_id}',
                    data=update_data,
                    headers=headers
                )
                
                print(f"PUT response status: {put_response.status_code}")
                print(f"PUT response text: {put_response.text}")
                
                if put_response.status_code == 200:
                    print("✅ PUT request successful!")
                else:
                    print("❌ PUT request failed!")
            else:
                print("No products found to test PUT")
        else:
            print(f"Failed to get products: {products_response.text}")
    else:
        print(f"Failed to get token: {token_response.text}")

if __name__ == "__main__":
    test_put_request()