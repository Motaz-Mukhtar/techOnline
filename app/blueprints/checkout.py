"""Checkout Blueprint

This module contains the route for checkout includes:
- Creating an order and include all the cart info
"""

from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from modules import storage
from modules.Products.product import Product
from modules.Review.review import Review
from modules.Order.order_item import OrderItem
from modules.Cart.cart import Cart

# Create profile blueprint
checkout_bp = Blueprint('profile', __name__)
