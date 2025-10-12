#!/usr/bin/env python3
import requests
import re

def test_method_override_direct():
    """Test the method override functionality by directly accessing the product form endpoints"""
    base_url = 'http://127.0.0.1:5000'
    session = requests.Session()
    
    print("Testing method override functionality directly...")
    
    # Test 1: Access product form for new product (should not have _method field)
    print("\n1. Testing new product form...")
    new_product_response = session.get(f'{base_url}/product_form')
    print(f"New product form status: {new_product_response.status_code}")
    
    if new_product_response.status_code == 200:
        # Check for _method field (should not exist for new products)
        method_pattern = r'<input[^>]*name=["\']_method["\'][^>]*value=["\']([^"\'>]+)["\']'
        method_match = re.search(method_pattern, new_product_response.text)
        if method_match:
            print(f"✗ Unexpected _method field found: {method_match.group(1)}")
        else:
            print("✓ No _method field found (correct for new product)")
        
        # Check form action
        form_pattern = r'<form[^>]*id=["\']productForm["\'][^>]*action=["\']([^"\'>]+)["\']'
        form_match = re.search(form_pattern, new_product_response.text)
        if form_match:
            action = form_match.group(1)
            print(f"✓ Form action: {action}")
        else:
            print("✗ Product form not found")
    else:
        print(f"✗ Failed to access new product form: {new_product_response.status_code}")
        if new_product_response.status_code == 302:
            print(f"Redirected to: {new_product_response.headers.get('Location', 'Unknown')}")
    
    # Test 2: Access product form for editing (with a dummy product ID)
    print("\n2. Testing edit product form...")
    edit_product_response = session.get(f'{base_url}/product_form/123')
    print(f"Edit product form status: {edit_product_response.status_code}")
    
    if edit_product_response.status_code == 200:
        # Check for _method field (should exist for editing)
        method_match = re.search(method_pattern, edit_product_response.text)
        if method_match:
            method_value = method_match.group(1)
            print(f"✓ Found _method field with value: {method_value}")
            if method_value == 'PUT':
                print("✓ Correct method override value (PUT)")
            else:
                print(f"✗ Incorrect method override value, expected PUT, got {method_value}")
        else:
            print("✗ No _method field found (should exist for editing)")
        
        # Check for product_id hidden field
        product_id_pattern = r'<input[^>]*name=["\']product_id["\'][^>]*value=["\']([^"\'>]+)["\']'
        product_id_match = re.search(product_id_pattern, edit_product_response.text)
        if product_id_match:
            product_id = product_id_match.group(1)
            print(f"✓ Found product_id field with value: {product_id}")
        else:
            print("✗ No product_id field found (should exist for editing)")
        
        # Check form action
        form_match = re.search(form_pattern, edit_product_response.text)
        if form_match:
            action = form_match.group(1)
            print(f"✓ Edit form action: {action}")
        else:
            print("✗ Edit product form not found")
    else:
        print(f"Edit product form status: {edit_product_response.status_code}")
        if edit_product_response.status_code == 302:
            print(f"Redirected to: {edit_product_response.headers.get('Location', 'Unknown')}")
        elif edit_product_response.status_code == 404:
            print("✓ 404 expected for non-existent product ID")
    
    # Test 3: Check if the form template contains the method override logic
    print("\n3. Checking template logic...")
    if new_product_response.status_code == 200:
        template_content = new_product_response.text
        
        # Check for conditional _method field logic
        if 'existing_product and is_editing' in template_content:
            print("✓ Template contains conditional logic for method override")
        else:
            print("✗ Template missing conditional logic for method override")
        
        # Check for PUT method value
        if 'value="PUT"' in template_content:
            print("✓ Template contains PUT method override")
        else:
            print("✗ Template missing PUT method override")
        
        # Check for product_id field logic
        if 'name="product_id"' in template_content:
            print("✓ Template contains product_id field")
        else:
            print("✗ Template missing product_id field")
    
    print("\n=== Method Override Test Summary ===")
    print("The form template should:")
    print("- Show no _method field for new products")
    print("- Show _method='PUT' field for editing existing products")
    print("- Include product_id field when editing")
    print("- Have conditional form action based on editing state")
    
    return True

if __name__ == '__main__':
    test_method_override_direct()