"""Profile Blueprint

This module contains all customer profile-related endpoints including:
- Customer profile display with ratings and sales statistics
"""

from flask import Blueprint, render_template, session
from flask_login import login_required, current_user
from modules import storage
from modules.Products.product import Product
from modules.Review.review import Review
from modules.Order.order_item import OrderItem
from modules.Cart.cart import Cart

# Create profile blueprint
profile_bp = Blueprint('profile', __name__)

@profile_bp.route('/customer_profile', methods=['GET'])
@profile_bp.route('/profile', methods=['GET'])
@login_required
def customer_profile():
    """
    Display customer profile with calculated rating and sales statistics.
    
    Rating is calculated from all reviews of the user's products.
    Sales count is calculated from all order items of the user's products.
    """
    print(current_user)

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
                         total_sales=total_sales,
                         cart_item_count=cart_item_count)