"""Products Blueprint

This module contains all product-related endpoints including:
- Product form (create/edit products)
- Product details view
- Product reviews (GET/POST)
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
import requests
import os
from werkzeug.utils import secure_filename
from modules import storage
from modules.Products.product import Product
from modules.Category.category import Category
from modules.Customer.customer import Customer
from modules.Cart.cart import Cart
from modules.Review.review import Review

# Create products blueprint
products_bp = Blueprint('products', __name__)

# Helper functions
def get_admin_api_key():
    """Get admin API key from session."""
    return session.get('access_token')

def img_url(filename):
    """Generate image URL for uploaded files."""
    if filename:
        return f'/static/uploads/{filename}'
    return '/static/images/default-product.jpg'

@products_bp.route('/product_form', methods=['GET', 'POST'])
@products_bp.route('/product_form/<product_id>', methods=['GET', 'POST'])
@login_required
def product_form(product_id=None):
    """
    Handle product creation and editing.
    
    GET: Display the product form (empty for new, populated for edit)
    POST: Process form submission to create or update product
    """
    if request.method == 'POST':
        # Check for method override (for PUT requests via POST)
        method_override = request.form.get('_method', 'POST').upper()
        is_update = method_override == 'PUT' or product_id is not None
        
        # Get form data
        product_name = request.form.get('product_name')
        description = request.form.get('description')
        price_str = request.form.get('price')
        category_id = request.form.get('category_id')
        
        # Validate required fields
        if not all([product_name, description, price_str, category_id]):
            flash('All fields are required', 'error')
            return redirect(request.url)
        
        # Validate price
        try:
            price = float(price_str)
            if price <= 0:
                flash('Price must be greater than 0', 'error')
                return redirect(request.url)
        except ValueError:
            flash('Invalid price format', 'error')
            return redirect(request.url)
        
        # Prepare form data
        form_data = {
            'product_name': product_name,
            'description': description,
            'price': price,
            'category_id': category_id,
            'customer_id': current_user.id
        }
        
        # Handle file upload
        uploaded_file = None
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename:
                filename = secure_filename(file.filename)
                upload_folder = os.path.join('app', 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)
                uploaded_file = filename
                form_data['product_image'] = filename
        
        # API request setup
        api_key = get_admin_api_key()
        headers = {'Authorization': f'Bearer {api_key}'} if api_key else {}
        
        try:
            if is_update and product_id:
                # Update existing product
                api_url = f'http://127.0.0.1:5001/api/v1/products/{product_id}'
                
                if uploaded_file:
                    # Send file with form data
                    with open(os.path.join('app', 'static', 'uploads', uploaded_file), 'rb') as f:
                        files = {'product_image': (uploaded_file, f, 'image/jpeg')}
                        response = requests.put(api_url, data=form_data, files=files, headers=headers, timeout=10)
                else:
                    # Send only form data
                    response = requests.put(api_url, data=form_data, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    flash('Product updated successfully!', 'success')
                    return redirect(url_for('shop.shop'))
                else:
                    flash(f'Failed to update product: {response.text}', 'error')
            else:
                # Create new product
                api_url = 'http://127.0.0.1:5001/api/v1/products'
                
                if uploaded_file:
                    # Send file with form data
                    with open(os.path.join('app', 'static', 'uploads', uploaded_file), 'rb') as f:
                        files = {'product_image': (uploaded_file, f, 'image/jpeg')}
                        response = requests.post(api_url, data=form_data, files=files, headers=headers, timeout=10)
                else:
                    # Send only form data
                    response = requests.post(api_url, data=form_data, headers=headers, timeout=10)
                
                if response.status_code == 201:
                    flash('Product created successfully!', 'success')
                    return redirect(url_for('shop.shop'))
                else:
                    flash(f'Failed to create product: {response.text}', 'error')
        
        except requests.exceptions.RequestException:
            # Fallback: create product locally if API is unavailable
            try:
                if product_id:
                    # Update existing product in storage
                    product = storage.get(Product, product_id)
                    if product and product.customer_id == current_user.id:
                        product.product_name = product_name
                        product.description = description
                        product.price = price
                        product.category_id = category_id
                        if uploaded_file:
                            product.product_image = uploaded_file
                        product.save()
                        flash('Product updated successfully (offline mode)!', 'success')
                        return redirect(url_for('shop.shop'))
                    else:
                        flash('Product not found or access denied', 'error')
                else:
                    # Create new product in storage
                    product = Product(
                        product_name=product_name,
                        description=description,
                        price=price,
                        category_id=category_id,
                        customer_id=current_user.id,
                        product_image=uploaded_file
                    )
                    product.save()
                    flash('Product created successfully (offline mode)!', 'success')
                    return redirect(url_for('shop.shop'))
            except Exception as e:
                flash(f'Failed to save product: {str(e)}', 'error')
    
    # GET request: render form
    product_data = None
    
    # Check for product_id from URL path or query parameter
    edit_product_id = product_id or request.args.get('edit')
    
    if edit_product_id:
        # Try to get product from API first
        try:
            api_url = f'http://127.0.0.1:5001/api/v1/products/{edit_product_id}'
            response = requests.get(api_url, timeout=10)
            if response.status_code == 200:
                api_json = response.json()
                product_data = api_json.get('data') if isinstance(api_json, dict) else None
        except requests.exceptions.RequestException:
            pass
        
        # Fallback to storage
        if not product_data:
            product = storage.get(Product, edit_product_id)
            if product and product.customer_id == current_user.id:
                product_data = product.to_dict()
            else:
                flash('Product not found or access denied', 'error')
                return redirect(url_for('shop.shop'))
    
    # Get categories for dropdown
    categories = list(storage.all(Category).values())
    
    # Determine if we're editing an existing product
    is_editing = product_data is not None
    
    return render_template('product_form.html', 
                         existing_product=product_data, 
                         is_editing=is_editing,
                         categories=categories,
                         user=current_user)

@products_bp.route('/product/<product_id>', methods=['GET'])
@login_required
def product_details(product_id):
    """
    Render product details page.
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

        # Try fetching product from API
        api_url = f'http://127.0.0.1:5001/api/v1/products/{product_id}'
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
            return redirect(url_for('shop.shop'))

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

        return render_template('product_details.html', product=product_data,
                                                       cart_item_count=cart_item_count,
                                                       seller=seller_info,
                                                       category_name=category_name,
                                                       reviews=reviews,
                                                       has_reviewed=has_reviewed)

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
        return redirect(url_for('shop.shop'))
    except Exception as e:
        flash(f'Unexpected error: {str(e)}', 'error')
        return redirect(url_for('shop.shop'))

@products_bp.route('/product/<product_id>/reviews', methods=['GET'])
@login_required
def get_product_reviews(product_id):
    """
    Get all approved reviews for a product (JSON endpoint).
    """
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

@products_bp.route('/product/<product_id>/reviews', methods=['POST'])
@login_required
def create_product_review(product_id):
    """
    Create a new review for a product.
    """
    try:
        prod = storage.get(Product, product_id)
        if not prod:
            flash('Product not found', 'error')
            return redirect(url_for('products.product_details', product_id=product_id))

        if prod.has_customer_reviewed(current_user.id):
            flash('You already reviewed this product.', 'error')
            return redirect(url_for('products.product_details', product_id=product_id))

        rating = request.form.get('rating')
        title = request.form.get('title')
        text = request.form.get('text')

        if not text or not rating:
            flash('Rating and review text are required.', 'error')
            return redirect(url_for('products.product_details', product_id=product_id))

        try:
            rating_float = float(rating)
            if rating_float < 1 or rating_float > 5:
                flash('Rating must be between 1 and 5.', 'error')
                return redirect(url_for('products.product_details', product_id=product_id))
        except ValueError:
            flash('Invalid rating value.', 'error')
            return redirect(url_for('products.product_details', product_id=product_id))

        review = Review(
            product_id=product_id,
            customer_id=current_user.id,
            text=text,
            rate=rating_float,
            title=title
        )
        review.save()

        flash('Review submitted successfully!', 'success')
        return redirect(url_for('products.product_details', product_id=product_id))
    except Exception as e:
        flash(f'Failed to submit review: {str(e)}', 'error')
        return redirect(url_for('products.product_details', product_id=product_id))