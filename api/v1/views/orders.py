#!/usr/bin/python3
"""
Order API endpoints for TechOnline e-commerce platform.

This module provides comprehensive order management functionality including:
- Order creation from carts
- Order status management
- Order history retrieval
- Inventory management integration
"""

from modules.Order.order import Order
from modules.Order.order_item import OrderItem
from modules.Cart.cart import Cart
from modules.Cart.cart_item import CartItem
from modules.Products.product import Product
from modules.Customer.customer import Customer
from modules.utils.stock_manager import StockManager
from modules.utils.error_handler import error_handler
from modules.utils.order_workflow import OrderWorkflowManager, OrderStatus
from modules.utils.validators import BusinessRuleValidator
from modules import storage
from api.v1.views import app_views
from api.v1.auth import require_auth, require_admin, optional_auth, get_current_user_id, is_admin
from flask import jsonify, abort, make_response, request


@app_views.route('/orders', methods=['GET', 'POST'], strict_slashes=False) # type: ignore
@optional_auth()
def handle_orders():
    """
    Handle order operations.
    
    GET: Retrieve all orders with filtering and pagination
    POST: Create a new order from a cart
    
    Query Parameters (GET):
        - customer_id: Filter by customer ID
        - status: Filter by order status
        - min_amount: Filter by minimum order amount
        - max_amount: Filter by maximum order amount
        - limit: Maximum number of results (default: 50)
        - offset: Number of results to skip (default: 0)
        - sort_by: Sort by 'date', 'amount', 'status' (default: 'date')
        - order: 'asc' or 'desc' (default: 'desc')
    
    Returns:
        JSON response with order data or error message
    """
    if request.method == 'GET':
        try:
            # Get query parameters
            customer_id = request.args.get('customer_id')
            status_filter = request.args.get('status')
            min_amount = request.args.get('min_amount', type=float)
            max_amount = request.args.get('max_amount', type=float)
            limit = request.args.get('limit', 50, type=int)
            offset = request.args.get('offset', 0, type=int)
            sort_by = request.args.get('sort_by', 'date')
            order_direction = request.args.get('order', 'desc')
            
            # Get all orders
            all_orders = list(storage.all(Order).values())
            
            # Get all orders
            all_orders = list(storage.all(Order).values())
            
            # Apply customer filter and authorization check first
            if customer_id:
                try:
                    customer = storage.get(Customer, customer_id)
                    if not customer:
                        return make_response(jsonify({"error": "Customer not found"}), 404)
                    # Non-admin users can only view their own orders
                    current_user_id = get_current_user_id()
                    if current_user_id and not is_admin() and customer_id != current_user_id:
                        return make_response(jsonify({"error": "Access denied: You can only view your own orders"}), 403)
                    filtered_orders = [order for order in all_orders if order.customer_id == customer_id]
                except Exception as e:
                    return make_response(jsonify({"error": "Invalid customer_id format"}), 400)
            else:
                # If no customer_id specified and user is authenticated but not admin, show only their orders
                current_user_id = get_current_user_id()
                if current_user_id and not is_admin():
                    filtered_orders = [order for order in all_orders if order.customer_id == current_user_id]
                else:
                    filtered_orders = all_orders
            
            # Apply other filters
            if status_filter:
                filtered_orders = [order for order in filtered_orders if order.order_status == status_filter]
            
            if min_amount is not None:
                filtered_orders = [order for order in filtered_orders if order.total_amount >= min_amount]
            
            if max_amount is not None:
                filtered_orders = [order for order in filtered_orders if order.total_amount <= max_amount]
            
            # Sort orders
            if sort_by == 'amount':
                filtered_orders.sort(key=lambda x: x.total_amount, reverse=(order_direction == 'desc'))
            elif sort_by == 'status':
                filtered_orders.sort(key=lambda x: x.order_status, reverse=(order_direction == 'desc'))
            else:  # sort by date
                filtered_orders.sort(key=lambda x: x.created_at, reverse=(order_direction == 'desc'))
            
            # Apply pagination
            total_orders = len(filtered_orders)
            paginated_orders = filtered_orders[offset:offset + limit]
            
            # Convert to dict
            orders_list = [order.to_dict() for order in paginated_orders]
            
            return jsonify({
                'orders': orders_list,
                'pagination': {
                    'total': total_orders,
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_orders
                }
            })
            
        except Exception as e:
            return make_response(jsonify({"error": f"Failed to get orders: {str(e)}"}), 500)
    
    elif request.method == 'POST':
        # POST requires authentication
        current_user_id = get_current_user_id()
        if not current_user_id:
            return make_response(jsonify({"error": "Authentication required to create orders"}), 401)
        
        if not request.get_json():
            return make_response(jsonify({"error": "Not a JSON"}), 400)
        
        data = request.get_json()
        
        # Validate required fields
        if 'cart_id' not in data:
            return make_response(jsonify({"error": "Missing cart_id"}), 400)
        
        cart_id = data['cart_id']
        
        try:
            # Create order from cart
            order = create_order_from_cart(cart_id, current_user_id)
            return make_response(jsonify({
                "message": "Order created successfully",
                "order": order.to_dict()
            }), 201)
            
        except ValueError as e:
            return make_response(jsonify({"error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({"error": f"Failed to create order: {str(e)}"}), 500)


def create_order_from_cart(cart_id, customer_id=None):
    """
    Create an order from a cart with comprehensive inventory validation and stock management.
    
    Args:
        cart_id (str): ID of the cart to convert to order
        customer_id (str, optional): ID of the customer (for validation)
        
    Returns:
        Order: The created order object
        
    Raises:
        ValueError: If cart is invalid or has insufficient stock
    """
    from modules.utils.validators import BusinessRuleValidator
    
    # Initialize stock manager and validator
    stock_manager = StockManager(storage.get_session())
    validator = BusinessRuleValidator(db_session=storage.get_session())
    
    # Validate cart exists
    cart = storage.get(Cart, cart_id)
    if not cart:
        raise ValueError(f"Cart with ID {cart_id} not found")
    
    # Validate cart belongs to customer if customer_id is provided
    if customer_id and cart.customer_id != customer_id:
        raise ValueError("Cart does not belong to the specified customer")
    
    # Check if cart has items
    if not cart.cart_items:
        raise ValueError("Cannot create order from empty cart")
    
    # Prepare product quantities for bulk stock check
    product_quantities = []
    order_items_data = []
    for cart_item in cart.cart_items:
        product_quantities.append({
            'product_id': cart_item.product_id,
            'quantity': cart_item.quantity
        })
        order_items_data.append({
            'product_id': cart_item.product_id,
            'quantity': cart_item.quantity
        })
    
    # Calculate preliminary order total for validation
    preliminary_total = sum(
        cart_item.quantity * cart_item.product.price 
        for cart_item in cart.cart_items
    )
    
    # Validate customer order limits
    if customer_id:
        customer_limits_validation = validator.validate_customer_order_limits(
            customer_id=customer_id,
            order_total=preliminary_total
        )
        
        if not customer_limits_validation['valid']:
            raise ValueError(f"Customer order limits exceeded: {'; '.join(customer_limits_validation['errors'])}")
    
    # Validate order items business rules
    order_items_validation = validator.validate_order_items(order_items_data)
    if not order_items_validation['valid']:
        raise ValueError(f"Order items validation failed: {'; '.join(order_items_validation['errors'])}")
    
    # Validate inventory constraints
    inventory_validation = validator.validate_inventory_constraints(order_items_data)
    if not inventory_validation['valid']:
        raise ValueError(f"Inventory constraints violated: {'; '.join(inventory_validation['errors'])}")
    
    # Validate stock availability for all items using StockManager
    stock_check_result = stock_manager.check_multiple_products_stock(product_quantities)
    
    if not stock_check_result['all_available']:
        unavailable_items = stock_check_result['unavailable_items']
        error_messages = []
        for item in unavailable_items:
            product = storage.get(Product, item.get('product_id', 'unknown'))
            product_name = product.product_name if product else 'Unknown Product'
            error_messages.append(
                f"{product_name}: {item['reason']} (Available: {item['current_stock']}, Requested: {item['requested_quantity']})"
            )
        raise ValueError(f"Insufficient stock for items: {'; '.join(error_messages)}")
    
    # Create order
    order = Order(
        customer_id=cart.customer_id,
        cart_id=cart_id,
        order_status='pending'
    )
    order.save()
    
    # Create order items and reserve stock
    reserved_items = []
    try:
        for cart_item in cart.cart_items:
            # Create order item
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                unit_price=cart_item.unit_price
            )
            order_item.save()
            
            # Reserve stock using StockManager
            reservation_result = stock_manager.reserve_stock(
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                order_id=order.id
            )
            
            if not reservation_result['success']:
                raise ValueError(f"Failed to reserve stock for product {cart_item.product_id}: {reservation_result['message']}")
            
            reserved_items.append({
                'product_id': cart_item.product_id,
                'quantity': cart_item.quantity
            })
        
        # Calculate and save order total
        order.calculate_total_amount()
        order.save()
        
        # Clear the cart after successful order creation
        cart.clear_cart()
        
    except Exception as e:
        # If anything fails, release all reserved stock
        for reserved_item in reserved_items:
            stock_manager.release_stock(
                product_id=reserved_item['product_id'],
                quantity=reserved_item['quantity'],
                order_id=order.id
            )
        # Re-raise the exception
        raise e
    cart.save()
    
    return order


@app_views.route('/orders/<order_id>', methods=['GET', 'PUT', 'DELETE'], strict_slashes=False) # type: ignore
@require_auth()
def handle_order(order_id):
    """
    Handle individual order operations.
    
    GET: Retrieve specific order details
    PUT: Update order information (mainly status)
    DELETE: Cancel/delete an order
    
    Args:
        order_id (str): ID of the order to handle
        
    Returns:
        JSON response with order data or error message
    """
    order = storage.get(Order, order_id)
    
    if not order:
        return make_response(jsonify({"error": "Order not found"}), 404)
    
    if request.method == 'GET':
        # Check if user can access this order
        current_user_id = get_current_user_id()
        if not is_admin() and order.customer_id != current_user_id:
            return make_response(jsonify({"error": "Access denied: You can only view your own orders"}), 403)
        return jsonify(order.to_dict())
    
    elif request.method == 'PUT':
        # Check if user can modify this order
        current_user_id = get_current_user_id()
        if not is_admin() and order.customer_id != current_user_id:
            return make_response(jsonify({"error": "Access denied: You can only modify your own orders"}), 403)
        
        if not request.get_json():
            return make_response(jsonify({"error": "Not a JSON"}), 400)
        
        data = request.get_json()
        
        try:
            # Update order status if provided
            if 'order_status' in data:
                order.update_order_status(data['order_status'])
            
            # Update other fields if provided
            if 'total_amount' in data:
                order.total_amount = float(data['total_amount'])
            
            order.save()
            
            return make_response(jsonify({
                "message": "Order updated successfully",
                "order": order.to_dict()
            }), 200)
            
        except ValueError as e:
            return make_response(jsonify({"error": str(e)}), 400)
        except Exception as e:
            return make_response(jsonify({"error": f"Failed to update order: {str(e)}"}), 500)
    
    elif request.method == 'DELETE':
        # Check if user can delete this order
        current_user_id = get_current_user_id()
        if not is_admin() and order.customer_id != current_user_id:
            return make_response(jsonify({"error": "Access denied: You can only delete your own orders"}), 403)
        
        try:
            # Only allow deletion of pending orders
            if order.order_status not in ['pending', 'cancelled']:
                return make_response(jsonify({"error": "Cannot delete order with status: " + order.order_status}), 400)
            
            # Restore inventory if order is being cancelled
            if order.order_status == 'pending':
                for order_item in order.order_items:
                    product = storage.get(Product, order_item.product_id)
                    if product:
                        product.update_stock(order_item.quantity)
                        product.save()
            
            storage.delete(order)
            storage.save()
            
            return make_response(jsonify({"message": "Order deleted successfully"}), 200)
            
        except Exception as e:
            return make_response(jsonify({"error": f"Failed to delete order: {str(e)}"}), 500)


@app_views.route('/orders/<order_id>/status', methods=['PUT'], strict_slashes=False) # type: ignore
@require_auth()
def update_order_status(order_id):
    """
    Update the status of a specific order with proper workflow validation.
    
    This endpoint handles order status transitions with comprehensive validation,
    stock management integration, and business rule enforcement.
    
    Args:
        order_id (str): ID of the order to update
        
    Expected JSON payload:
        {
            "status": "string" (pending, confirmed, processing, shipped, delivered, cancelled, refunded),
            "reason": "string" (optional reason for status change)
        }
    
    Returns:
        JSON response with updated order data or error message
    """
    try:
        # Check if order exists
        order = storage.get(Order, order_id)
        if not order:
            return error_handler.not_found_error_response(
                message="Order not found",
                resource_type="Order",
                resource_id=order_id
            )
        
        # Check if user can modify this order
        current_user_id = get_current_user_id()
        if not is_admin() and order.customer_id != current_user_id:
            return error_handler.access_denied_error_response(
                message="Access denied: You can only modify your own orders"
            )
        
        # Validate JSON data
        data = request.get_json()
        if not data:
            return error_handler.validation_error_response(
                message="No JSON data provided"
            )
        
        new_status = data.get('status')
        reason = data.get('reason')
        
        if not new_status:
            return error_handler.validation_error_response(
                message="status field is required",
                field_errors={'status': ['This field is required']}
            )
        
        # Validate status value
        try:
            OrderStatus(new_status)
        except ValueError:
            valid_statuses = [status.value for status in OrderStatus]
            return error_handler.validation_error_response(
                message="Invalid order status",
                field_errors={
                    'status': [f'Must be one of: {", ".join(valid_statuses)}']
                }
            )
        
        # Initialize workflow manager
        workflow_manager = OrderWorkflowManager(db_session=storage)
        
        # Perform status transition
        result = workflow_manager.transition_order_status(
            order_id=order_id,
            new_status=new_status,
            reason=reason,
            user_id=current_user_id
        )
        
        if result['success']:
            # Get updated order data
            updated_order = storage.get(Order, order_id)
            return error_handler.success_response(
                data={
                    'order': updated_order.to_dict() if updated_order else None,
                    'previous_status': result['previous_status'],
                    'current_status': result['current_status'],
                    'actions_performed': result.get('post_transition_actions', {}).get('actions_performed', [])
                },
                message=result['message']
            )
        else:
            return error_handler.business_rule_error_response(
                message=result['message'],
                details={
                    'current_status': result.get('current_status'),
                    'valid_transitions': result.get('valid_transitions', [])
                }
            )
    
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to update order status",
            error_details=str(e)
        )


@app_views.route('/customers/<customer_id>/orders', methods=['GET'], strict_slashes=False) # type: ignore
@require_auth()
def get_customer_orders(customer_id):
    """
    Get order history for a specific customer.
    
    Args:
        customer_id (str): ID of the customer
        
    Query Parameters:
        - status: Filter by order status
        - limit: Limit number of results
        - offset: Offset for pagination
    
    Returns:
        JSON response with customer's order history or error message
    """
    # Check if user can access this customer's orders
    current_user_id = get_current_user_id()
    if not is_admin() and customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only view your own orders"}), 403)
    
    # Validate customer exists
    customer = storage.get(Customer, customer_id)
    if not customer:
        return make_response(jsonify({"error": "Customer not found"}), 404)
    
    # Get query parameters
    status_filter = request.args.get('status')
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', type=int, default=0)
    
    # Get all orders for the customer
    all_orders = storage.all(Order).values()
    customer_orders = [order for order in all_orders if order.customer_id == customer_id]
    
    # Apply status filter if provided
    if status_filter:
        customer_orders = [order for order in customer_orders if order.order_status == status_filter]
    
    # Sort by creation date (newest first)
    customer_orders.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply pagination
    if limit:
        customer_orders = customer_orders[offset:offset + limit]
    
    # Convert to dict format
    orders_data = [order.to_dict() for order in customer_orders]
    
    return make_response(jsonify({
        "customer_id": customer_id,
        "total_orders": len(orders_data),
        "orders": orders_data
    }), 200)


@app_views.route('/orders/<order_id>/items', methods=['GET'], strict_slashes=False) # type: ignore
@require_auth()
def get_order_items(order_id):
    """
    Get all items in a specific order.
    
    Args:
        order_id (str): ID of the order
        
    Returns:
        JSON response with order items or error message
    """
    order = storage.get(Order, order_id)
    
    if not order:
        return make_response(jsonify({"error": "Order not found"}), 404)
    
    # Check if user can access this order
    current_user_id = get_current_user_id()
    if not is_admin() and order.customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only view your own orders"}), 403)
    
    items_data = [item.to_dict() for item in order.order_items]
    
    return make_response(jsonify({
        "order_id": order_id,
        "total_items": len(items_data),
        "items": items_data
    }), 200)


@app_views.route('/orders/stats', methods=['GET'], strict_slashes=False) # type: ignore
@require_admin()
def get_order_statistics():
    """
    Get order statistics and analytics.
    
    Query Parameters:
        - customer_id: Get stats for specific customer
        - date_from: Start date for filtering (YYYY-MM-DD)
        - date_to: End date for filtering (YYYY-MM-DD)
    
    Returns:
        JSON response with order statistics
    """
    try:
        # Get query parameters
        customer_id = request.args.get('customer_id')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        all_orders = list(storage.all(Order).values())
        
        # Apply filters
        filtered_orders = all_orders
        if customer_id:
            filtered_orders = [order for order in filtered_orders if order.customer_id == customer_id]
        
        # Calculate statistics
        total_orders = len(filtered_orders)
        total_revenue = sum(order.total_amount for order in filtered_orders if order.total_amount)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        # Count by status
        status_counts = {}
        for order in filtered_orders:
            status = order.order_status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Recent orders (last 10)
        recent_orders = sorted(filtered_orders, key=lambda x: x.created_at, reverse=True)[:10]
        
        # Top customers by order count
        customer_order_counts = {}
        for order in filtered_orders:
            customer_id_key = order.customer_id
            customer_order_counts[customer_id_key] = customer_order_counts.get(customer_id_key, 0) + 1
        
        top_customers = sorted(customer_order_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return make_response(jsonify({
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "average_order_value": round(average_order_value, 2),
            "status_breakdown": status_counts,
            "recent_orders": [order.to_dict() for order in recent_orders],
            "top_customers": [{"customer_id": cid, "order_count": count} for cid, count in top_customers]
        }), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to get order statistics: {str(e)}"}), 500)


@app_views.route('/orders/search', methods=['GET'], strict_slashes=False) # type: ignore
@require_auth()
def search_orders():
    """
    Search orders by various criteria.
    
    Query Parameters:
        - q: Search query (searches in order ID, customer name, product names)
        - limit: Maximum number of results (default: 20)
        - offset: Number of results to skip (default: 0)
    
    Returns:
        JSON response with matching orders
    """
    try:
        query = request.args.get('q', '').lower().strip()
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if not query:
            return make_response(jsonify({"error": "Search query is required"}), 400)
        
        all_orders = list(storage.all(Order).values())
        matching_orders = []
        
        for order in all_orders:
            # Search in order ID
            if query in order.id.lower():
                matching_orders.append(order)
                continue
            
            # Search in customer information
            customer = storage.get(Customer, order.customer_id)
            if customer:
                customer_name = f"{customer.first_name} {customer.last_name}".lower()
                if query in customer_name or query in customer.email.lower():
                    matching_orders.append(order)
                    continue
            
            # Search in order items/products
            for order_item in order.order_items:
                product = storage.get(Product, order_item.product_id)
                if product and query in product.product_name.lower():
                    matching_orders.append(order)
                    break
        
        # Remove duplicates and sort by date
        unique_orders = list({order.id: order for order in matching_orders}.values())
        unique_orders.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total_results = len(unique_orders)
        paginated_orders = unique_orders[offset:offset + limit]
        
        return jsonify({
            'query': query,
            'orders': [order.to_dict() for order in paginated_orders],
            'pagination': {
                'total': total_results,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_results
            }
        })
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to search orders: {str(e)}"}), 500)


@app_views.route('/orders/bulk', methods=['PUT'], strict_slashes=False) # type: ignore
@require_admin()
def bulk_update_orders():
    """
    Bulk update multiple orders with proper workflow validation.
    
    This endpoint allows bulk status updates with proper validation
    and workflow management for each order.
    
    Expected JSON payload:
        {
            "order_ids": ["order_id1", "order_id2", ...],
            "updates": {
                "order_status": "new_status"
            },
            "reason": "optional reason for status changes"
        }
    
    Returns:
        JSON response with bulk update results
    """
    try:
        # Validate JSON data
        data = request.get_json()
        if not data:
            return error_handler.validation_error_response(
                message="No JSON data provided"
            )
        
        order_ids = data.get('order_ids', [])
        updates = data.get('updates', {})
        reason = data.get('reason')
        
        # Validate required fields
        if not order_ids:
            return error_handler.validation_error_response(
                message="order_ids is required",
                field_errors={'order_ids': ['This field is required']}
            )
        
        if not updates:
            return error_handler.validation_error_response(
                message="updates is required",
                field_errors={'updates': ['This field is required']}
            )
        
        if not isinstance(order_ids, list) or len(order_ids) == 0:
            return error_handler.validation_error_response(
                message="order_ids must be a non-empty list",
                field_errors={'order_ids': ['Must be a non-empty list']}
            )
        
        # Validate status if provided
        new_status = updates.get('order_status')
        if new_status:
            try:
                OrderStatus(new_status)
            except ValueError:
                valid_statuses = [status.value for status in OrderStatus]
                return error_handler.validation_error_response(
                    message="Invalid order status",
                    field_errors={
                        'updates.order_status': [f'Must be one of: {", ".join(valid_statuses)}']
                    }
                )
        
        # Initialize workflow manager and validator
        workflow_manager = OrderWorkflowManager(db_session=storage)
        validator = BusinessRuleValidator(db_session=storage.get_session())
        current_user_id = get_current_user_id()
        
        # Validate bulk operation limits
        bulk_validation = validator.validate_bulk_operations(
            operation_count=len(order_ids),
            operation_type='update'
        )
        
        if not bulk_validation['valid']:
            return error_handler.validation_error_response(
                message="Bulk operation validation failed",
                errors=bulk_validation['errors']
            )
        
        updated_orders = []
        failed_updates = []
        
        for order_id in order_ids:
            try:
                # Check if order exists
                order = storage.get(Order, order_id)
                if not order:
                    failed_updates.append({
                        "order_id": order_id, 
                        "error": "Order not found"
                    })
                    continue
                
                # Apply status update if provided
                if new_status:
                    result = workflow_manager.transition_order_status(
                        order_id=order_id,
                        new_status=new_status,
                        reason=reason,
                        user_id=current_user_id
                    )
                    
                    if result['success']:
                        # Get updated order data
                        updated_order = storage.get(Order, order_id)
                        if updated_order:
                            updated_orders.append({
                                'order_id': order_id,
                                'order': updated_order.to_dict(),
                                'previous_status': result['previous_status'],
                                'current_status': result['current_status'],
                                'actions_performed': result.get('post_transition_actions', {}).get('actions_performed', [])
                            })
                    else:
                        failed_updates.append({
                            "order_id": order_id,
                            "error": result['message'],
                            "current_status": result.get('current_status'),
                            "valid_transitions": result.get('valid_transitions', [])
                        })
                
            except Exception as e:
                failed_updates.append({
                    "order_id": order_id, 
                    "error": f"Unexpected error: {str(e)}"
                })
        
        return error_handler.success_response(
            data={
                "updated_orders": updated_orders,
                "failed_updates": failed_updates,
                "summary": {
                    "total_requested": len(order_ids),
                    "successful_updates": len(updated_orders),
                    "failed_updates": len(failed_updates)
                }
            },
            message=f"Bulk update completed. {len(updated_orders)} orders updated, {len(failed_updates)} failed."
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to perform bulk update",
            error_details=str(e)
        )


@app_views.route('/orders/<order_id>/payment', methods=['POST'], strict_slashes=False) # type: ignore
@require_auth()
def process_order_payment(order_id):
    """
    Process payment for an order (mock payment processing).
    
    Args:
        order_id (str): ID of the order to process payment for
        
    Expected JSON payload:
        {
            "payment_method": "credit_card|paypal|bank_transfer",
            "payment_details": {
                "card_number": "****-****-****-1234",
                "amount": 99.99
            }
        }
    
    Returns:
        JSON response with payment processing result
    """
    try:
        order = storage.get(Order, order_id)
        if not order:
            return make_response(jsonify({"error": "Order not found"}), 404)
        
        # Check if user can process payment for this order
        current_user_id = get_current_user_id()
        if not is_admin() and order.customer_id != current_user_id:
            return make_response(jsonify({"error": "Access denied: You can only process payment for your own orders"}), 403)
        
        if order.order_status not in ['pending', 'confirmed']:
            return make_response(jsonify({"error": f"Cannot process payment for order with status: {order.order_status}"}), 400)
        
        if not request.get_json():
            return make_response(jsonify({"error": "Not a JSON request"}), 400)
        
        data = request.get_json()
        
        if 'payment_method' not in data:
            return make_response(jsonify({"error": "Missing payment_method"}), 400)
        
        payment_method = data['payment_method']
        payment_details = data.get('payment_details', {})
        
        # Validate payment method
        valid_methods = ['credit_card', 'paypal', 'bank_transfer']
        if payment_method not in valid_methods:
            return make_response(jsonify({"error": f"Invalid payment method. Must be one of: {valid_methods}"}), 400)
        
        # Mock payment processing (in real implementation, integrate with payment gateway)
        import random
        payment_success = random.choice([True, True, True, False])  # 75% success rate for demo
        
        if payment_success:
            # Update order status to confirmed/paid
            order.update_order_status('confirmed')
            order.save()
            
            return make_response(jsonify({
                "message": "Payment processed successfully",
                "payment_id": f"pay_{order_id}_{random.randint(1000, 9999)}",
                "order": order.to_dict()
            }), 200)
        else:
            return make_response(jsonify({
                "error": "Payment processing failed. Please try again.",
                "order": order.to_dict()
            }), 400)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to process payment: {str(e)}"}), 500)

