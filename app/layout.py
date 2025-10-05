#!/usr/bin/env python3
from modules.Customer.customer import Customer
from modules.Category.category import Category
from modules.Review.review import Review
from modules.Products.product import Product
from modules.Cart.cart import Cart
from modules.Cart.cart_item import CartItem
from modules.Order.order import Order
from modules.Order.order_item import OrderItem
from modules.utils.file_handler import save_uploaded_file
from flask import render_template, request, flash, redirect, url_for, session
from flask import jsonify
from flask_login import login_required, current_user
from app import app
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
    
    GET: Display the product creation/editing form
    POST: Process form data, validate inputs, handle image upload, and create/update product via API
    
    Query Parameters:
        edit: Product ID for editing existing product
    
    Returns:
        GET: Rendered product form template
        POST: Redirect to shop page on success, or form with errors on failure
    """
    # Check if we're editing an existing product
    edit_product_id = request.args.get('edit')
    existing_product = None
    
    if edit_product_id:
        # Fetch existing product for editing
        try:
            existing_product = storage.get(Product, edit_product_id)
            if not existing_product:
                flash('Product not found!', 'error')
                return redirect(url_for('customer_profile'))
            
            # Check if user owns this product
            if existing_product.customer_id != current_user.id:
                flash('Access denied: You can only edit your own products!', 'error')
                return redirect(url_for('customer_profile'))
        except Exception as e:
            flash(f'Error loading product: {str(e)}', 'error')
            return redirect(url_for('customer_profile'))
    
    # Fetch active categories for the form (used by GET and on error cases)
    try:
        all_categories = list(storage.all(Category).values())
        categories = [c for c in all_categories if getattr(c, 'is_active', 'True') == 'True']
    except Exception:
        categories = []

    if request.method == 'POST':
        try:
            # Extract form data
            product_name = request.form.get('product_name', '').strip()
            price = request.form.get('price', '').strip()
            description = request.form.get('description', '').strip()
            customer_id = request.form.get('customer_id')
            category_id = request.form.get('category_id', '').strip()
            stock_quantity = request.form.get('stock_quantity', '10')  # Default stock
            min_stock_level = request.form.get('min_stock_level', '5')  # Default min stock
            
            # Validate required fields
            if not all([product_name, price, description, customer_id]):
                flash('All fields are required!', 'error')
                template_data = {
                    'user': current_user.to_dict(),
                    'categories': categories,
                    'existing_product': existing_product.to_dict() if existing_product else None,
                    'is_editing': existing_product is not None
                }
                return render_template('product_form.html', **template_data)

            # Validate category selection
            if not category_id:
                flash('Please select a category.', 'error')
                template_data = {
                    'user': current_user.to_dict(),
                    'categories': categories,
                    'existing_product': existing_product.to_dict() if existing_product else None,
                    'is_editing': existing_product is not None
                }
                return render_template('product_form.html', **template_data)
            # Ensure the category exists
            if not storage.get(Category, category_id):
                flash('Selected category not found.', 'error')
                template_data = {
                    'user': current_user.to_dict(),
                    'categories': categories,
                    'existing_product': existing_product.to_dict() if existing_product else None,
                    'is_editing': existing_product is not None
                }
                return render_template('product_form.html', **template_data)
            
            # Validate price is numeric
            try:
                price_float = float(price)
                if price_float <= 0:
                    flash('Price must be a positive number!', 'error')
                    template_data = {
                        'user': current_user.to_dict(),
                        'categories': categories,
                        'existing_product': existing_product.to_dict() if existing_product else None,
                        'is_editing': existing_product is not None
                    }
                    return render_template('product_form.html', **template_data)
            except ValueError:
                flash('Price must be a valid number!', 'error')
                template_data = {
                    'user': current_user.to_dict(),
                    'categories': categories,
                    'existing_product': existing_product.to_dict() if existing_product else None,
                    'is_editing': existing_product is not None
                }
                return render_template('product_form.html', **template_data)
            
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
            
            # Determine if we're creating or updating
            if existing_product:
                # Update existing product via API
                api_url = f'http://127.0.0.1:5001/api/v1/products/{existing_product.id}'
                headers = {'Authorization': f'Bearer {session.get("access_token")}'}
                
                if files:
                    # Send multipart form data with file
                    response = requests.put(api_url, data=form_data, files=files, headers=headers, timeout=30)
                else:
                    # Send JSON data
                    headers['Content-Type'] = 'application/json'
                    response = requests.put(api_url, json=form_data, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    api_data = response.json()
                    flash(f'Product "{product_name}" updated successfully!', 'success')
                    return redirect(url_for('customer_profile'))
                else:
                    # Handle API errors for update
                    try:
                        error_data = response.json()
                        error_message = error_data.get('message', f'API Error: {response.status_code}')
                        if 'field_errors' in error_data:
                            for field, errors in error_data['field_errors'].items():
                                for error in errors:
                                    flash(f'{field}: {error}', 'error')
                        else:
                            flash(f'Error updating product: {error_message}', 'error')
                    except:
                        flash(f'Error updating product: HTTP {response.status_code}', 'error')
            else:
                # Create new product via API
                api_url = 'http://127.0.0.1:5001/api/v1/products'
                headers = {'Authorization': f'Bearer {session.get("access_token")}'}
                
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
                
                template_data = {
                    'user': current_user.to_dict(),
                    'categories': categories,
                    'existing_product': existing_product.to_dict() if existing_product else None,
                    'is_editing': existing_product is not None
                }
                return render_template('product_form.html', **template_data)
            
        except requests.exceptions.RequestException as e:
            flash(f'Error connecting to API: {str(e)}', 'error')
            # Fallback: create product directly in the local database
            try:
                # Create and save product locally
                from modules.Products.product import Product
                local_product = Product(
                    product_name=product_name,
                    description=description,
                    price=price_float,
                    customer_id=customer_id,
                    category_id=category_id,
                    stock_quantity=int(stock_quantity) if str(stock_quantity).isdigit() else 0,
                    min_stock_level=int(min_stock_level) if str(min_stock_level).isdigit() else 5
                )
                local_product.save()

                # Handle image upload locally if present
                if 'product_image' in request.files:
                    file = request.files['product_image']
                    if file and file.filename:
                        result = save_uploaded_file(file, 'product', local_product.id)
                        if result.get('success'):
                            local_product.product_image = result.get('url')
                            local_product.product_image_filename = result.get('filename')
                            local_product.save()

                flash(f'Product "{product_name}" created locally (API unavailable).', 'success')
                return redirect(url_for('shop'))
            except Exception as ex:
                flash(f'Error creating product locally: {str(ex)}', 'error')
                template_data = {
                    'user': current_user.to_dict(),
                    'categories': categories,
                    'existing_product': existing_product.to_dict() if existing_product else None,
                    'is_editing': existing_product is not None
                }
                return render_template('product_form.html', **template_data)
        except Exception as e:
            flash(f'Error creating product: {str(e)}', 'error')
            template_data = {
                'user': current_user.to_dict(),
                'categories': categories,
                'existing_product': existing_product.to_dict() if existing_product else None,
                'is_editing': existing_product is not None
            }
            return render_template('product_form.html', **template_data)

    # GET request: render form with categories and existing product data (if editing)
    template_data = {
        'user': current_user.to_dict(),
        'categories': categories,
        'existing_product': existing_product.to_dict() if existing_product else None,
        'is_editing': existing_product is not None
    }
    return render_template('product_form.html', **template_data)



@app.route('/customer_profile', methods=['GET'], strict_slashes=False)
@app.route('/profile', methods=['GET'], strict_slashes=False)
@login_required
def customer_profile():
    """
    Display customer profile with calculated rating and sales statistics.
    
    Rating is calculated from all reviews of the user's products.
    Sales count is calculated from all order items of the user's products.
    """
    print(current_user)
    
    # Calculate average rating from all reviews of user's products
    user_products = storage.all(Product).values()
    user_products = [p for p in user_products if p.customer_id == current_user.id]
    
    total_rating = 0
    total_reviews = 0
    
    for product in user_products:
        product_reviews = [r for r in storage.all(Review).values() if r.product_id == product.id]
        for review in product_reviews:
            total_rating += review.rate
            total_reviews += 1
    
    average_rating = round(total_rating / total_reviews, 1) if total_reviews > 0 else 0.0
    
    # Calculate total sales from order items of user's products
    total_sales = 0
    
    for product in user_products:
        product_order_items = [oi for oi in storage.all(OrderItem).values() if oi.product_id == product.id]
        for order_item in product_order_items:
            total_sales += order_item.quantity
    
    return render_template('customer_profile.html', 
                         user=current_user, 
                         access_token=session.get('access_token'),
                         average_rating=average_rating,
                         total_sales=total_sales) # type: ignore



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

@app.route('/product/<product_id>', methods=['GET'], strict_slashes=False)
@login_required
def product_details(product_id):
    """
    Render product details page.
    """
    try:
        # Try fetching product from API
        api_url = f'http://127.0.0.1:5000/api/v1/products/{product_id}'
        response = requests.get(api_url, timeout=10)

        product_data = None
        if response.status_code == 200:
            api_json = response.json()
            # API responses use a success envelope with 'data'
            product_data = api_json.get('data') if isinstance(api_json, dict) else None
        else:
            # Fallback to storage when API returns non-200
            product_obj = storage.get(Product, product_id)
            if product_obj:
                product_data = product_obj.to_dict()

        if not product_data:
            flash('Product not found', 'error')
            return redirect(url_for('shop'))

        # Resolve seller information via storage to avoid API permission issues
        seller_info = {'first_name': '', 'last_name': ''}
        try:
            customer_id = product_data.get('customer_id') if isinstance(product_data, dict) else None
            if customer_id:
                seller = storage.get(Customer, customer_id)
                if seller:
                    seller_info = {
                        'first_name': getattr(seller, 'first_name', ''),
                        'last_name': getattr(seller, 'last_name', '')
                    }
        except Exception:
            # If seller lookup fails, continue without blocking the page
            pass

        # Resolve category name
        category_name = None
        try:
            cat_id = product_data.get('category_id') if isinstance(product_data, dict) else None
            if cat_id:
                cat = storage.get(Category, cat_id)
                if cat:
                    category_name = getattr(cat, 'name', None)
        except Exception:
            pass

        # Fetch approved reviews
        reviews = []
        try:
            all_reviews = storage.all(Review)
            product_reviews = [
                r for r in all_reviews.values()
                if r.product_id == product_id and r.is_approved == 1
            ]
            product_reviews.sort(key=lambda x: x.created_at, reverse=True)
            for r in product_reviews:
                cust = storage.get(Customer, r.customer_id)
                reviews.append({
                    'id': r.id,
                    'title': r.title,
                    'text': r.text,
                    'rate': r.rate,
                    'customer_name': f"{cust.first_name} {cust.last_name}" if cust else None,
                    'created_at': r.created_at
                })
        except Exception:
            pass

        # Determine if current user has already reviewed
        has_reviewed = False
        try:
            prod_obj = storage.get(Product, product_id)
            if prod_obj and current_user:
                has_reviewed = prod_obj.has_customer_reviewed(current_user.id)
        except Exception:
            pass

        return render_template('product_details.html', product=product_data, seller=seller_info, category_name=category_name, reviews=reviews, has_reviewed=has_reviewed)

    except requests.exceptions.RequestException:
        # Network/API error: use storage fallback
        product_obj = storage.get(Product, product_id)
        if product_obj:
            product_data = product_obj.to_dict()
            seller_info = {'first_name': '', 'last_name': ''}
            try:
                seller = storage.get(Customer, product_data.get('customer_id'))
                if seller:
                    seller_info = {
                        'first_name': getattr(seller, 'first_name', ''),
                        'last_name': getattr(seller, 'last_name', '')
                    }
            except Exception:
                pass
            # Resolve category name
            category_name = None
            try:
                cat_id = product_data.get('category_id') if isinstance(product_data, dict) else None
                if cat_id:
                    cat = storage.get(Category, cat_id)
                    if cat:
                        category_name = getattr(cat, 'name', None)
            except Exception:
                pass

            # Fetch approved reviews
            reviews = []
            try:
                all_reviews = storage.all(Review)
                product_reviews = [
                    r for r in all_reviews.values()
                    if r.product_id == product_id and r.is_approved == 1
                ]
                product_reviews.sort(key=lambda x: x.created_at, reverse=True)
                for r in product_reviews:
                    cust = storage.get(Customer, r.customer_id)
                    reviews.append({
                        'id': r.id,
                        'title': r.title,
                        'text': r.text,
                        'rate': r.rate,
                        'customer_name': f"{cust.first_name} {cust.last_name}" if cust else None,
                        'created_at': r.created_at
                    })
            except Exception:
                pass

            # Determine if current user has already reviewed
            has_reviewed = False
            try:
                if current_user and product_obj:
                    has_reviewed = product_obj.has_customer_reviewed(current_user.id)
            except Exception:
                pass

            return render_template('product_details.html', product=product_data, seller=seller_info, category_name=category_name, reviews=reviews, has_reviewed=has_reviewed)
        flash('Error fetching product details', 'error')
        return redirect(url_for('shop'))
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        return redirect(url_for('shop'))


@app.route('/product/<product_id>/reviews', methods=['GET'], strict_slashes=False)
@login_required
def get_product_reviews(product_id):
    try:
        prod = storage.get(Product, product_id)
        if not prod:
            return jsonify({'error': 'Product not found'}), 404

        all_reviews = storage.all(Review)
        product_reviews = [
            r for r in all_reviews.values()
            if r.product_id == product_id and r.is_approved == 1
        ]
        product_reviews.sort(key=lambda x: x.created_at, reverse=True)

        result = []
        for r in product_reviews:
            cust = storage.get(Customer, r.customer_id)
            result.append({
                'id': r.id,
                'title': r.title,
                'text': r.text,
                'rate': r.rate,
                'customer_name': f"{cust.first_name} {cust.last_name}" if cust else None,
                'created_at': r.created_at.isoformat()
            })

        return jsonify({'reviews': result, 'count': len(result)}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to get reviews: {str(e)}'}), 500


@app.route('/product/<product_id>/reviews', methods=['POST'], strict_slashes=False)
@login_required
def create_product_review(product_id):
    try:
        prod = storage.get(Product, product_id)
        if not prod:
            flash('Product not found', 'error')
            return redirect(url_for('product_details', product_id=product_id))

        if prod.has_customer_reviewed(current_user.id):
            flash('You already reviewed this product.', 'error')
            return redirect(url_for('product_details', product_id=product_id))

        rating = request.form.get('rating')
        title = request.form.get('title')
        text = request.form.get('text')

        if not text or not rating:
            flash('Rating and review text are required.', 'error')
            return redirect(url_for('product_details', product_id=product_id))

        try:
            rating_float = float(rating)
            if rating_float < 1 or rating_float > 5:
                flash('Rating must be between 1 and 5.', 'error')
                return redirect(url_for('product_details', product_id=product_id))
        except ValueError:
            flash('Invalid rating value.', 'error')
            return redirect(url_for('product_details', product_id=product_id))

        review = Review(
            product_id=product_id,
            customer_id=current_user.id,
            text=text,
            rate=rating_float,
            title=title
        )
        review.save()

        flash('Review submitted successfully!', 'success')
        return redirect(url_for('product_details', product_id=product_id))
    except Exception as e:
        flash(f'Failed to submit review: {str(e)}', 'error')
        return redirect(url_for('product_details', product_id=product_id))

@app.route('/cart', methods=['GET'], strict_slashes=False)
@login_required
def cart():
    """
    Cart page rendered with server-side data from database.
    """
    try:
        # Find current user's cart
        user_id = getattr(current_user, 'id', None)
        cart_obj = None
        if user_id:
            for c in storage.all(Cart).values():
                if c.customer_id == user_id:
                    cart_obj = c
                    break

        items = []
        total = 0.0
        if cart_obj:
            # Ensure totals are up to date
            try:
                cart_obj.calculate_total_price()
            except Exception:
                pass

            for ci in cart_obj.cart_items:
                prod = storage.get(Product, ci.product_id)
                items.append({
                    'product_id': ci.product_id,
                    'name': getattr(prod, 'product_name', 'Product'),
                    'price': getattr(prod, 'price', ci.unit_price),
                    'image': getattr(prod, 'product_image', None),
                    'quantity': ci.quantity,
                    'subtotal': ci.subtotal
                })
            total = cart_obj.total_price

        return render_template('cart.html', cart=cart_obj, items=items, total=total)
    except Exception as e:
        flash(f'Failed to load cart: {str(e)}', 'error')
        return render_template('cart.html', cart=None, items=[], total=0.0)


@app.route('/cart/add', methods=['POST'], strict_slashes=False)
@login_required
def add_to_cart():
    """Add a product to the current user's cart in the database."""
    try:
        data = request.get_json(silent=True) or request.form
        product_id = data.get('product_id')
        quantity = int(str(data.get('quantity', 1)))

        if not product_id:
            return jsonify({'error': 'product_id is required'}), 400

        # Validate product exists
        prod = storage.get(Product, product_id)
        if not prod:
            return jsonify({'error': 'Product not found'}), 404

        user_id = getattr(current_user, 'id', None)
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401

        # Find or create cart for user
        cart_obj = None
        for c in storage.all(Cart).values():
            if c.customer_id == user_id:
                cart_obj = c
                break
        if not cart_obj:
            cart_obj = Cart(customer_id=user_id)
            cart_obj.save()

        # Add product to cart
        try:
            cart_item = cart_obj.add_product(product_id, quantity)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400

        # Persist changes
        try:
            cart_item.save()
        except Exception:
            pass
        cart_obj.save()

        return jsonify({
            'message': 'Added to cart',
            'cart_id': cart_obj.id,
            'item': {
                'product_id': cart_item.product_id,
                'quantity': cart_item.quantity,
                'unit_price': cart_item.unit_price,
                'subtotal': cart_item.subtotal
            },
            'total': cart_obj.total_price
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to add to cart: {str(e)}'}), 500


@app.route('/cart/update_item', methods=['POST'], strict_slashes=False)
@login_required
def update_cart_item():
    """Update quantity for a product in the cart."""
    try:
        data = request.get_json(silent=True) or request.form
        product_id = data.get('product_id')
        new_quantity = int(str(data.get('quantity', 1)))

        if not product_id:
            return jsonify({'error': 'product_id is required'}), 400
        if new_quantity <= 0:
            return jsonify({'error': 'quantity must be > 0'}), 400

        user_id = getattr(current_user, 'id', None)
        cart_obj = None
        for c in storage.all(Cart).values():
            if c.customer_id == user_id:
                cart_obj = c
                break
        if not cart_obj:
            return jsonify({'error': 'Cart not found'}), 404

        # Find item
        target_item = None
        for ci in cart_obj.cart_items:
            if ci.product_id == product_id:
                target_item = ci
                break
        if not target_item:
            return jsonify({'error': 'Item not found in cart'}), 404

        # Update
        try:
            target_item.update_quantity(new_quantity)
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        try:
            target_item.save()
        except Exception:
            pass

        cart_obj.calculate_total_price()
        cart_obj.save()

        return jsonify({
            'message': 'Quantity updated',
            'item': {
                'product_id': target_item.product_id,
                'quantity': target_item.quantity,
                'subtotal': target_item.subtotal
            },
            'total': cart_obj.total_price
        }), 200
    except Exception as e:
        return jsonify({'error': f'Failed to update item: {str(e)}'}), 500


@app.route('/cart/remove_item', methods=['POST'], strict_slashes=False)
@login_required
def remove_cart_item():
    """Remove a product from the cart."""
    try:
        data = request.get_json(silent=True) or request.form
        product_id = data.get('product_id')
        if not product_id:
            return jsonify({'error': 'product_id is required'}), 400

        user_id = getattr(current_user, 'id', None)
        cart_obj = None
        for c in storage.all(Cart).values():
            if c.customer_id == user_id:
                cart_obj = c
                break
        if not cart_obj:
            return jsonify({'error': 'Cart not found'}), 404

        # Remove
        removed = cart_obj.remove_product(product_id)
        if not removed:
            return jsonify({'error': 'Item not found in cart'}), 404

        cart_obj.save()
        return jsonify({'message': 'Item removed', 'total': cart_obj.total_price}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to remove item: {str(e)}'}), 500

