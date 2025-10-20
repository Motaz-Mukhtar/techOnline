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

# Import and register blueprints
from app.blueprints.shop import shop_bp
from app.blueprints.products import products_bp
from app.blueprints.cart import cart_bp
from app.blueprints.profile import profile_bp
from app.blueprints.api import api_bp

# Register blueprints
app.register_blueprint(shop_bp)
app.register_blueprint(products_bp)
app.register_blueprint(cart_bp)
app.register_blueprint(profile_bp)
app.register_blueprint(api_bp, url_prefix='/api')


# Utility functions for templates and other modules
from flask import render_template, request
from flask_login import login_required
import requests
import json
from requests.exceptions import HTTPError


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


# Old Base64 image serving endpoint removed - now using direct file serving

