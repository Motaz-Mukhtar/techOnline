"""Cart Blueprint

This module contains all cart-related endpoints including:
- Cart page display
- Add items to cart
- Update cart item quantities
- Remove items from cart
"""

from flask import Blueprint, render_template, request, jsonify, flash
from flask_login import login_required, current_user
from modules import storage
from modules.Cart.cart import Cart
from modules.Products.product import Product

# Create cart blueprint
cart_bp = Blueprint('cart', __name__)

@cart_bp.route('/cart', methods=['GET'])
@login_required
def cart():
    """
    Cart page rendered with server-side data from database.
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

        return render_template('cart.html', cart=cart_obj,
                                            items=items,
                                            total=total,
                                            cart_item_count=cart_item_count)
    except Exception as e:
        flash(f'Failed to load cart: {str(e)}', 'error')
        return render_template('cart.html', cart=None, items=[], total=0.0)

@cart_bp.route('/cart/add', methods=['POST'])
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

@cart_bp.route('/cart/update_item', methods=['POST'])
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

@cart_bp.route('/cart/remove_item', methods=['POST'])
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