#!/usr/bin/env python3
import requests

def debug_form_content():
    """Debug what content is actually returned by the product form endpoints"""
    base_url = 'http://127.0.0.1:5000'
    session = requests.Session()
    
    print("Debugging product form content...")
    
    # Test 1: Check new product form
    print("\n1. New product form content:")
    new_product_response = session.get(f'{base_url}/product_form')
    print(f"Status: {new_product_response.status_code}")
    print(f"URL: {new_product_response.url}")
    print(f"Content length: {len(new_product_response.text)}")
    
    # Print first 1000 characters to see what we're getting
    content = new_product_response.text
    print("\nFirst 1000 characters:")
    print(content[:1000])
    print("\n" + "="*50)
    
    # Check if it contains login form instead
    if 'login' in content.lower():
        print("⚠️  Content appears to be a login page")
    
    # Check if it contains product form
    if 'productForm' in content:
        print("✓ Contains productForm")
    else:
        print("✗ Does not contain productForm")
    
    # Check for method override elements
    if '_method' in content:
        print("✓ Contains _method")
    else:
        print("✗ Does not contain _method")
    
    if 'existing_product and is_editing' in content:
        print("✓ Contains conditional logic")
    else:
        print("✗ Does not contain conditional logic")
    
    # Test 2: Check edit product form
    print("\n\n2. Edit product form content:")
    edit_product_response = session.get(f'{base_url}/product_form/123')
    print(f"Status: {edit_product_response.status_code}")
    print(f"URL: {edit_product_response.url}")
    print(f"Content length: {len(edit_product_response.text)}")
    
    # Print first 1000 characters
    edit_content = edit_product_response.text
    print("\nFirst 1000 characters:")
    print(edit_content[:1000])
    
    # Check if it's different from new product form
    if edit_content == content:
        print("\n⚠️  Edit form content is identical to new form content")
    else:
        print("\n✓ Edit form content is different from new form content")

if __name__ == '__main__':
    debug_form_content()