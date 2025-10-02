#!/usr/bin/python3
from modules.Cart.cart import Cart
from modules.Cart.cart_item import CartItem
from modules.Products.product import Product
from modules.Customer.customer import Customer
from modules import storage
from api.v1.views import app_views
from api.v1.auth import require_auth, require_admin, optional_auth, get_current_user_id, is_admin
from flask import jsonify, abort, make_response, request


@app_views.route('/carts', methods=['GET', 'POST'], strict_slashes=False) # type: ignore
@require_auth(['read'])
def get_carts():
    """
    Handle cart operations.
    
    GET: Retrieve all carts (admin) or user's own carts
    POST: Create a new cart for authenticated user
    
    Returns:
        JSON response with cart data or error message
    """
    if request.method == 'GET':
        current_user_id = get_current_user_id()
        carts = storage.all(Cart).values()
        
        # Admin can see all carts, regular users only their own
        if is_admin():
            carts_list = [cart.to_dict() for cart in carts]
        else:
            carts_list = [cart.to_dict() for cart in carts if cart.customer_id == current_user_id]
        
        return jsonify(carts_list)
    
    elif request.method == 'POST':
        if not request.get_json():
            return make_response(jsonify({"error": "Not a JSON"}), 400)
        
        data = request.get_json()
        
        # Get authenticated customer ID
        customer_id = get_current_user_id()
        if not customer_id:
            return make_response(jsonify({"error": "Authentication required"}), 401)
        
        # Validate customer exists
        customer = storage.get(Customer, customer_id)
        if not customer:
            return make_response(jsonify({"error": "Customer not found"}), 404)
        
        # Check if customer already has a cart
        existing_carts = storage.all(Cart).values()
        for cart in existing_carts:
            if cart.customer_id == customer_id:
                return make_response(jsonify({"error": "Customer already has a cart", "cart": cart.to_dict()}), 409)
        
        # Create new cart
        new_cart = Cart(customer_id=customer_id)
        new_cart.save()
        
        return make_response(jsonify(new_cart.to_dict()), 201)

@app_views.route('/carts/<cart_id>', methods=['GET', 'PUT', 'DELETE'], strict_slashes=False) # type: ignore
@require_auth(['read'])
def cart(cart_id):
    cart = storage.get(Cart, cart_id)

    if not cart:
        return make_response(jsonify({"error": "customer cart is empty"}), 404)
    
    # Check if user can access this cart
    current_user_id = get_current_user_id()
    if not is_admin() and cart.customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only access your own cart"}), 403)

    if request.method == 'GET':
        return jsonify(cart.to_dict())

    if request.method == 'PUT' or request.method == 'DELETE':
        if not request.get_json():
            abort(400, "Not a JSON")

        if request.method == 'PUT':
            ignore = ['id', 'created_at', 'updated_at']
            data = request.get_json()

            for key, value in data.items():
                if key not in ignore:
                    setattr(cart, key, value)
            storage.save()
            return make_response(jsonify(cart.to_dict()), 200)

        elif request.method == 'DELETE':
            storage.delete(cart)
            storage.save()
            return make_response(jsonify({}), 200)


@app_views.route('/carts/<cart_id>/add_product', methods=['POST'], strict_slashes=False) # type: ignore
@require_auth(['write'])
def add_product_to_cart(cart_id):
    """
    Add a product to the specified cart.
    
    Args:
        cart_id (str): ID of the cart to add product to
        
    Expected JSON payload:
        {
            "product_id": "string",
            "quantity": int (optional, default: 1)
        }
    
    Returns:
        JSON response with updated cart data or error message
    """
    cart = storage.get(Cart, cart_id)
    
    if not cart:
        return make_response(jsonify({"error": "Cart not found"}), 404)
    
    # Check if user can modify this cart
    current_user_id = get_current_user_id()
    if not is_admin() and cart.customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only modify your own cart"}), 403)
    
    if not request.get_json():
        return make_response(jsonify({"error": "Not a JSON"}), 400)
    
    data = request.get_json()
    
    # Validate required fields
    if 'product_id' not in data:
        return make_response(jsonify({"error": "Missing product_id"}), 400)
    
    product_id = data['product_id']
    quantity = data.get('quantity', 1)
    
    # Validate quantity
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return make_response(jsonify({"error": "Quantity must be greater than 0"}), 400)
    except (ValueError, TypeError):
        return make_response(jsonify({"error": "Invalid quantity format"}), 400)
    
    try:
        # Add product to cart
        cart_item = cart.add_product(product_id, quantity)
        cart.save()
        
        return make_response(jsonify({
            "message": "Product added to cart successfully",
            "cart": cart.to_dict(),
            "cart_item": cart_item.to_dict()
        }), 200)
        
    except ValueError as e:
        return make_response(jsonify({"error": str(e)}), 400)
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to add product to cart: {str(e)}"}), 500)


@app_views.route('/carts/<cart_id>/remove_product/<product_id>', methods=['DELETE'], strict_slashes=False) # type: ignore
@require_auth(['write'])
def remove_product_from_cart(cart_id, product_id):
    """
    Remove a product completely from the specified cart.
    
    Args:
        cart_id (str): ID of the cart to remove product from
        product_id (str): ID of the product to remove
    
    Returns:
        JSON response with updated cart data or error message
    """
    cart = storage.get(Cart, cart_id)
    
    if not cart:
        return make_response(jsonify({"error": "Cart not found"}), 404)
    
    # Check if user can modify this cart
    current_user_id = get_current_user_id()
    if not is_admin() and cart.customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only modify your own cart"}), 403)
    
    try:
        success = cart.remove_product(product_id)
        
        if success:
            cart.save()
            return make_response(jsonify({
                "message": "Product removed from cart successfully",
                "cart": cart.to_dict()
            }), 200)
        else:
            return make_response(jsonify({"error": "Product not found in cart"}), 404)
            
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to remove product from cart: {str(e)}"}), 500)


@app_views.route('/carts/<cart_id>/update_quantity', methods=['PUT'], strict_slashes=False) # type: ignore
@require_auth(['write'])
def update_cart_item_quantity(cart_id):
    """
    Update the quantity of a specific product in the cart.
    
    Args:
        cart_id (str): ID of the cart to update
        
    Expected JSON payload:
        {
            "product_id": "string",
            "quantity": int
        }
    
    Returns:
        JSON response with updated cart data or error message
    """
    cart = storage.get(Cart, cart_id)
    
    if not cart:
        return make_response(jsonify({"error": "Cart not found"}), 404)
    
    # Check if user can modify this cart
    current_user_id = get_current_user_id()
    if not is_admin() and cart.customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only modify your own cart"}), 403)
    
    if not request.get_json():
        return make_response(jsonify({"error": "Not a JSON"}), 400)
    
    data = request.get_json()
    
    # Validate required fields
    if 'product_id' not in data or 'quantity' not in data:
        return make_response(jsonify({"error": "Missing product_id or quantity"}), 400)
    
    product_id = data['product_id']
    quantity = data['quantity']
    
    # Validate quantity
    try:
        quantity = int(quantity)
        if quantity <= 0:
            return make_response(jsonify({"error": "Quantity must be greater than 0"}), 400)
    except (ValueError, TypeError):
        return make_response(jsonify({"error": "Invalid quantity format"}), 400)
    
    try:
        # Update product quantity in cart
        cart_item = cart.update_product_quantity(product_id, quantity)
        cart.save()
        
        return make_response(jsonify({
            "message": "Cart item quantity updated successfully",
            "cart": cart.to_dict(),
            "cart_item": cart_item.to_dict()
        }), 200)
        
    except ValueError as e:
        return make_response(jsonify({"error": str(e)}), 400)
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to update cart item quantity: {str(e)}"}), 500)


@app_views.route('/carts/<cart_id>/clear', methods=['DELETE'], strict_slashes=False) # type: ignore
@require_auth(['write'])
def clear_cart(cart_id):
    """
    Clear all items from the specified cart.
    
    Args:
        cart_id (str): ID of the cart to clear
    
    Returns:
        JSON response with cleared cart data or error message
    """
    cart = storage.get(Cart, cart_id)
    
    if not cart:
        return make_response(jsonify({"error": "Cart not found"}), 404)
    
    # Check if user can modify this cart
    current_user_id = get_current_user_id()
    if not is_admin() and cart.customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only modify your own cart"}), 403)
    
    try:
        cart.clear_cart()
        cart.save()
        
        return make_response(jsonify({
            "message": "Cart cleared successfully",
            "cart": cart.to_dict()
        }), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to clear cart: {str(e)}"}), 500)


@app_views.route('/customers/<customer_id>/cart', methods=['GET'], strict_slashes=False) # type: ignore
@require_auth(['read'])
def get_customer_cart(customer_id):
    """
    Get the cart for a specific customer.
    
    Args:
        customer_id (str): ID of the customer
    
    Returns:
        JSON response with customer's cart data or error message
    """
    # Check if user can access this customer's cart
    current_user_id = get_current_user_id()
    if not is_admin() and customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only access your own cart"}), 403)
    
    # Validate customer exists
    customer = storage.get(Customer, customer_id)
    if not customer:
        return make_response(jsonify({"error": "Customer not found"}), 404)
    
    # Find customer's cart
    carts = storage.all(Cart).values()
    customer_cart = None
    
    for cart in carts:
        if cart.customer_id == customer_id:
            customer_cart = cart
            break
    
    if not customer_cart:
        return make_response(jsonify({"error": "Customer has no cart"}), 404)
    
    return make_response(jsonify(customer_cart.to_dict()), 200)