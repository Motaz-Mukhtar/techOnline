#!/usr/bin/env python3
from modules.Customer.customer import Customer
from modules.Products.product import Product
from modules.utils.file_handler import save_uploaded_file
from flask import render_template, request, flash, redirect, url_for
from flask_login import login_required
from app import app
from app.auth import current_user
from modules import storage
import requests
import json
from requests import HTTPError
from flask import Response
import os
import uuid
from werkzeug.utils import secure_filename
import mimetypes


def get_admin_api_key():
    """
    Get the admin API key for making administrative API calls.
    
    Returns:
        str: Admin API key
    """
    # Use the hardcoded admin API key from the API server
    return 'admin_key_123'


def img_url(product_id):
    """
    Generate URL for product image by ID.
    
    Args:
        product_id (str): Product ID to generate image URL for
    
    Returns:
        str: URL path to product image or default image if not found
    """
    try:
        product = storage.get(Product, product_id)
        if product and product.product_image:
            return product.product_image
        else:
            return '/static/images/default-product.jpg'
    except Exception:
        return '/static/images/default-product.jpg'


@app.route('/shop', methods=['GET', 'POST'], strict_slashes=False)
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
                    
                    return render_template('layout.html', products=matching_products, search_query=product_name)
                else:
                    flash(f'Error fetching search results: {response.status_code}', 'error')
                    # Fallback to empty results
                    return render_template('layout.html', products=[], search_query=product_name)
            else:
                # If no search query, get all products from API
                api_url = 'http://127.0.0.1:5001/api/v1/products'
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    api_data = response.json()
                    products_data = api_data.get('data', [])
                    
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
                    
                    return render_template('layout.html', products=products_list)
                else:
                    flash(f'Error fetching products: {response.status_code}', 'error')
                    return render_template('layout.html', products=[])
        
        # GET request - get all products from API
        api_url = 'http://127.0.0.1:5001/api/v1/products'
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            api_data = response.json()
            products_data = api_data.get('data', [])
            
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
            
            return render_template('layout.html', products=products_list)
        else:
            flash(f'Error fetching products: {response.status_code}', 'error')
            return render_template('layout.html', products=[])
            
    except requests.exceptions.RequestException as e:
        flash(f'API connection error: {str(e)}', 'error')
        # Fallback to direct database access if API is unavailable
        products_list = list(storage.all(Product).values())
        return render_template('layout.html', products=products_list)
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        return render_template('layout.html', products=[])


@app.route('/shop/product_form', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def product_form():
    """
    Handle product form submission and display using API endpoints.
    
    GET: Display the product creation form
    POST: Process form data, validate inputs, handle image upload, and create new product via API
    
    Returns:
        GET: Rendered product form template
        POST: Redirect to shop page on success, or form with errors on failure
    """
    if request.method == 'POST':
        try:
            # Extract form data
            product_name = request.form.get('product_name', '').strip()
            price = request.form.get('price', '').strip()
            description = request.form.get('description', '').strip()
            customer_id = request.form.get('customer_id')
            category_id = request.form.get('category_id', '1')  # Default category
            stock_quantity = request.form.get('stock_quantity', '10')  # Default stock
            min_stock_level = request.form.get('min_stock_level', '5')  # Default min stock
            
            # Validate required fields
            if not all([product_name, price, description, customer_id]):
                flash('All fields are required!', 'error')
                return render_template('product_form.html', user=current_user.to_dict())
            
            # Validate price is numeric
            try:
                price_float = float(price)
                if price_float <= 0:
                    flash('Price must be a positive number!', 'error')
                    return render_template('product_form.html', user=current_user.to_dict())
            except ValueError:
                flash('Price must be a valid number!', 'error')
                return render_template('product_form.html', user=current_user.to_dict())
            
            # Prepare form data for API
            form_data = {
                'product_name': product_name,
                'description': description,
                'price': str(price_float),
                'customer_id': customer_id,
                'category_id': category_id,
                'stock_quantity': stock_quantity,
                'min_stock_level': min_stock_level
            }
            
            # Handle file upload
            files = {}
            if 'product_image' in request.files:
                file = request.files['product_image']
                if file and file.filename:
                    files['product_image'] = (file.filename, file.stream, file.content_type)
            
            # Get admin API key for API authentication
            api_key = get_admin_api_key()
            if not api_key:
                flash('Authentication failed. Please try again.', 'error')
                return redirect(url_for('product_form'))
            
            # Create product via API
            api_url = 'http://127.0.0.1:5001/api/v1/products'
            headers = {'Authorization': f'API-Key {api_key}'}
            
            if files:
                # Send multipart form data with file
                response = requests.post(api_url, data=form_data, files=files, headers=headers, timeout=30)
            else:
                # Send JSON data
                headers['Content-Type'] = 'application/json'
                response = requests.post(api_url, json=form_data, headers=headers, timeout=30)
            
            if response.status_code == 201:
                api_data = response.json()
                flash(f'Product "{product_name}" created successfully!', 'success')
                return redirect(url_for('shop'))
            else:
                # Handle API errors
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', f'API Error: {response.status_code}')
                    if 'field_errors' in error_data:
                        for field, errors in error_data['field_errors'].items():
                            for error in errors:
                                flash(f'{field}: {error}', 'error')
                    else:
                        flash(f'Error creating product: {error_message}', 'error')
                except:
                    flash(f'Error creating product: HTTP {response.status_code}', 'error')
                
                return render_template('product_form.html', user=current_user.to_dict())
            
        except requests.exceptions.RequestException as e:
            flash(f'Error connecting to API: {str(e)}', 'error')
            return render_template('product_form.html', user=current_user.to_dict())
        except Exception as e:
            flash(f'Error creating product: {str(e)}', 'error')
            return render_template('product_form.html', user=current_user.to_dict())
    
    return render_template('product_form.html', user=current_user.to_dict())



@app.route('/profile', strict_slashes=False)
@login_required
def customer_profile():
    print(current_user)
    return render_template('customer_profile.html', user=current_user) # type: ignore



@app.route('/test', methods=['GET'], strict_slashes=False)
@login_required
def tdddest():
    data = []
    try:
        products_list = requests.get('http://127.0.0.1:5001/api/v1/products')
        for i in json.loads(products_list.text):
            data.append(i)
    except HTTPError:
        products_list = []
    return render_template('test.html', data=data)


# Old Base64 image serving endpoint removed - now using direct file serving

