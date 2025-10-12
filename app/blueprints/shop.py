#!/usr/bin/env python3
"""
Shop Blueprint - Handles shop browsing and product search functionality.
"""

from flask import Blueprint, render_template, request, flash, current_app
from flask_login import login_required, current_user
from modules.Products.product import Product
from modules.Category.category import Category
from modules.Cart.cart import Cart
from modules import storage
import requests

# Create shop blueprint
shop_bp = Blueprint('shop', __name__, url_prefix='/shop')


@shop_bp.route('', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def shop():
    """
    Handle shop page with product search functionality using API endpoints.
    
    GET: Display shop page with all products from API
    POST: Search for products by name using API and display results
    
    Returns:
        Rendered shop template with products or search results from API
    """
    try:
        # Fetch the current user's cart and get item count
        cart = None
        cart_item_count = 0
        
        # Find the cart by customer_id (not by cart id)
        for c in storage.all(Cart).values():
            if c.customer_id == current_user.id:
                cart = c
                break
        
        if cart:
            # Use the built-in get_item_count method which sums all quantities
            cart_item_count = cart.get_item_count()

        if request.method == 'POST':
            product_name = request.form.get('product_name', '').strip()
            
            if product_name:
                # Search products using API with search parameter
                api_url = 'http://127.0.0.1:5001/api/v1/products'
                params = {'search': product_name}
                
                response = requests.get(api_url, params=params, timeout=10)
                
                if response.status_code == 200:
                    api_data = response.json()
                    products_data = api_data.get('data', [])
                    # Handle both flat list and nested { products: [...] } structures
                    if isinstance(products_data, dict):
                        products_data = products_data.get('products', [])
                    
                    # Convert API response to Product-like objects for template compatibility
                    matching_products = []
                    for product_dict in products_data:
                        # Create a simple object that mimics Product attributes
                        class ProductProxy:
                            def __init__(self, data):
                                self.id = data.get('id')
                                self.product_name = data.get('product_name')
                                self.description = data.get('description')
                                self.price = data.get('price')
                                self.product_image = data.get('product_image')
                                self.customer_id = data.get('customer_id')
                        
                        matching_products.append(ProductProxy(product_dict))
                    
                    return render_template('layout.html', products=matching_products, search_query=product_name, cart_item_count=cart_item_count)
                else:
                    flash(f'Error fetching search results: {response.status_code}', 'error')
                    # Fallback to empty results
                    return render_template('layout.html', products=[], search_query=product_name, cart_item_count=cart_item_count)
            else:
                # If no search query, get all products from API
                api_url = 'http://127.0.0.1:5001/api/v1/products'
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    api_data = response.json()
                    products_data = api_data.get('data', [])
                    # Handle both flat list and nested { products: [...] } structures
                    if isinstance(products_data, dict):
                        products_data = products_data.get('products', [])
                    
                    # Convert API response to Product-like objects
                    products_list = []
                    for product_dict in products_data:
                        class ProductProxy:
                            def __init__(self, data):
                                self.id = data.get('id')
                                self.product_name = data.get('product_name')
                                self.description = data.get('description')
                                self.price = data.get('price')
                                self.product_image = data.get('product_image')
                                self.customer_id = data.get('customer_id')
                        
                        products_list.append(ProductProxy(product_dict))
                    
                    return render_template('layout.html', products=products_list, cart_item_count=cart_item_count)
                else:
                    print("Error")
                    flash(f'Error fetching products: {response.status_code}', 'error')
                    return render_template('layout.html', products=[], cart_item_count=cart_item_count)
        
        # GET request - get all products from API
        api_url = 'http://127.0.0.1:5001/api/v1/products'
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            api_data = response.json()
            products_data = api_data.get('data', [])
            # Handle both flat list and nested { products: [...] } structures
            if isinstance(products_data, dict):
                products_data = products_data.get('products', [])
            
            # Convert API response to Product-like objects
            products_list = []
            for product_dict in products_data:
                class ProductProxy:
                    def __init__(self, data):
                        self.id = data.get('id')
                        self.product_name = data.get('product_name')
                        self.description = data.get('description')
                        self.price = data.get('price')
                        self.product_image = data.get('product_image')
                        self.customer_id = data.get('customer_id')
                
                products_list.append(ProductProxy(product_dict))
            
            return render_template('layout.html', products=products_list, cart_item_count=cart_item_count)
        else:
            flash(f'Error fetching products: {response.status_code}', 'error')
            return render_template('layout.html', products=[], cart_item_count=cart_item_count)
            
    except requests.exceptions.RequestException as e:
        flash(f'API connection error: {str(e)}', 'error')
        # Fallback to direct database access if API is unavailable
        products_list = list(storage.all(Product).values())
        return render_template('layout.html', products=products_list, cart_item_count=cart_item_count)
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        return render_template('layout.html', products=[], cart_item_count=cart_item_count)