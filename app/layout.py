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
    Handle shop page with product search functionality.
    
    GET: Display shop page with all products
    POST: Search for products by name and display results
    
    Returns:
        Rendered shop template with products or search results
    """
    if request.method == 'POST':
        product_name = request.form.get('product_name', '').strip()
        
        if product_name:
            # Search products by name (case-insensitive)
            products_list = storage.all(Product).values()
            matching_products = []
            
            for product in products_list:
                if product_name.lower() in product.product_name.lower():
                    matching_products.append(product)
            
            return render_template('layout.html', products=matching_products, search_query=product_name)
        else:
            # If no search query, show all products
            products_list = list(storage.all(Product).values())
            return render_template('layout.html', products=products_list)
    
    # GET request - show all products
    products_list = list(storage.all(Product).values())
    return render_template('layout.html', products=products_list)


@app.route('/shop/product_form', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def product_form():
    """
    Handle product form submission and display.
    
    GET: Display the product creation form
    POST: Process form data, validate inputs, handle image upload, and create new product
    
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
            
            # Create new product first
            new_product = Product(
                product_name=product_name,
                description=description,
                price=price_float,
                customer_id=customer_id
            )
            
            # Save to database to get product ID
            new_product.save()
            
            # Handle image upload after product creation
            if 'product_image' in request.files:
                file = request.files['product_image']
                if file and file.filename:
                    # Save uploaded file using the new file handler
                    result = save_uploaded_file(file, 'product', new_product.id)
                    
                    if result['success']:
                        # Update product with image information
                        new_product.product_image = result['url']
                        new_product.product_image_filename = result['filename']
                        new_product.save()
                    else:
                        # Delete the product if image upload failed
                        new_product.delete()
                        flash(f'Product image upload failed: {result["error"]}', 'error')
                        return render_template('product_form.html', user=current_user.to_dict())
                else:
                    flash('Please select an image file!', 'error')
                    new_product.delete()
                    return render_template('product_form.html', user=current_user.to_dict())

            
            flash(f'Product "{product_name}" created successfully!', 'success')
            return redirect(url_for('shop'))
            
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

