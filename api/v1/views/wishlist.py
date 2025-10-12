#!/usr/bin/python3
"""
Wishlist API endpoints for TechOnline e-commerce platform.

This module provides wishlist functionality including:
- Adding products to wishlist
- Removing products from wishlist
- Retrieving user's wishlist
- Checking if product is in wishlist
"""

from modules.Wishlist.wishlist import Wishlist
from modules.Products.product import Product
from modules.Customer.customer import Customer
from modules import storage
from api.v1.views import app_views
from api.v1.auth import require_auth, get_current_user_id
from flask import jsonify, make_response, request
from sqlalchemy.exc import IntegrityError


@app_views.route('/customers/<customer_id>/wishlist', methods=['GET'], strict_slashes=False)
@require_auth()
def get_customer_wishlist(customer_id):
    """
    Get all wishlist items for a specific customer.
    
    Args:
        customer_id (str): The customer ID
        
    Returns:
        JSON response with wishlist items or error message
    """
    try:
        current_user_id = get_current_user_id()
        
        # Check if user can access this wishlist (own wishlist or admin)
        if current_user_id != customer_id:
            from api.v1.auth import is_admin
            if not is_admin():
                return make_response(jsonify({
                    'error': 'Access denied. You can only view your own wishlist.'
                }), 403)
        
        # Get customer
        customer = storage.get(Customer, customer_id)
        if not customer:
            return make_response(jsonify({'error': 'Customer not found'}), 404)
        
        # Get all wishlist items for this customer
        wishlist_items = []
        for wishlist_item in storage.all(Wishlist).values():
            if wishlist_item.customer_id == customer_id:
                wishlist_items.append(wishlist_item.to_dict())
        
        # Sort by added_at date (newest first)
        wishlist_items.sort(key=lambda x: x.get('added_at', ''), reverse=True)
        
        return make_response(jsonify({
            'wishlist_items': wishlist_items,
            'total_items': len(wishlist_items)
        }), 200)
        
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)


@app_views.route('/customers/<customer_id>/wishlist', methods=['POST'], strict_slashes=False)
@require_auth()
def add_to_wishlist(customer_id):
    """
    Add a product to customer's wishlist.
    
    Args:
        customer_id (str): The customer ID
        
    Request Body:
        {
            "product_id": "string"
        }
        
    Returns:
        JSON response with success message or error
    """
    try:
        current_user_id = get_current_user_id()
        
        # Check if user can modify this wishlist (own wishlist only)
        if current_user_id != customer_id:
            return make_response(jsonify({
                'error': 'Access denied. You can only modify your own wishlist.'
            }), 403)
        
        # Get request data
        data = request.get_json()
        if not data or 'product_id' not in data:
            return make_response(jsonify({
                'error': 'Missing required field: product_id'
            }), 400)
        
        product_id = data['product_id']
        
        # Validate customer exists
        customer = storage.get(Customer, customer_id)
        if not customer:
            return make_response(jsonify({'error': 'Customer not found'}), 404)
        
        # Validate product exists
        product = storage.get(Product, product_id)
        if not product:
            return make_response(jsonify({'error': 'Product not found'}), 404)
        
        # Check if product is already in wishlist
        for wishlist_item in storage.all(Wishlist).values():
            if (wishlist_item.customer_id == customer_id and 
                wishlist_item.product_id == product_id):
                return make_response(jsonify({
                    'error': 'Product is already in your wishlist'
                }), 409)
        
        # Create new wishlist item
        new_wishlist_item = Wishlist(
            customer_id=customer_id,
            product_id=product_id
        )
        
        storage.new(new_wishlist_item)
        storage.save()
        
        return make_response(jsonify({
            'message': 'Product added to wishlist successfully',
            'wishlist_item': new_wishlist_item.to_dict()
        }), 201)
        
    except Exception as e:
        storage.rollback()
        return make_response(jsonify({'error': str(e)}), 500)


@app_views.route('/customers/<customer_id>/wishlist/<product_id>', methods=['DELETE'], strict_slashes=False)
@require_auth()
def remove_from_wishlist(customer_id, product_id):
    """
    Remove a product from customer's wishlist.
    
    Args:
        customer_id (str): The customer ID
        product_id (str): The product ID to remove
        
    Returns:
        JSON response with success message or error
    """
    try:
        current_user_id = get_current_user_id()
        
        # Check if user can modify this wishlist (own wishlist only)
        if current_user_id != customer_id:
            return make_response(jsonify({
                'error': 'Access denied. You can only modify your own wishlist.'
            }), 403)
        
        # Find the wishlist item
        wishlist_item = None
        for item in storage.all(Wishlist).values():
            if (item.customer_id == customer_id and 
                item.product_id == product_id):
                wishlist_item = item
                break
        
        if not wishlist_item:
            return make_response(jsonify({
                'error': 'Product not found in your wishlist'
            }), 404)
        
        # Remove the wishlist item
        storage.delete(wishlist_item)
        storage.save()
        
        return make_response(jsonify({
            'message': 'Product removed from wishlist successfully'
        }), 200)
        
    except Exception as e:
        storage.rollback()
        return make_response(jsonify({'error': str(e)}), 500)


@app_views.route('/customers/<customer_id>/wishlist/<product_id>/check', methods=['GET'], strict_slashes=False)
@require_auth()
def check_wishlist_status(customer_id, product_id):
    """
    Check if a product is in customer's wishlist.
    
    Args:
        customer_id (str): The customer ID
        product_id (str): The product ID to check
        
    Returns:
        JSON response with wishlist status
    """
    try:
        current_user_id = get_current_user_id()
        
        # Check if user can access this wishlist (own wishlist or admin)
        if current_user_id != customer_id:
            from api.v1.auth import is_admin
            if not is_admin():
                return make_response(jsonify({
                    'error': 'Access denied. You can only check your own wishlist.'
                }), 403)
        
        # Check if product is in wishlist
        is_in_wishlist = False
        for wishlist_item in storage.all(Wishlist).values():
            if (wishlist_item.customer_id == customer_id and 
                wishlist_item.product_id == product_id):
                is_in_wishlist = True
                break
        
        return make_response(jsonify({
            'product_id': product_id,
            'customer_id': customer_id,
            'is_in_wishlist': is_in_wishlist
        }), 200)
        
    except Exception as e:
        return make_response(jsonify({'error': str(e)}), 500)