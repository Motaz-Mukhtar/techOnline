from modules.Order.order import Order
from modules.utils.order_workflow import OrderWorkflowManager, OrderStatus
from modules import storage
from modules.utils.error_handler import error_handler
from flask import jsonify, request
from api.v1.views import app_views
from api.v1.auth import require_auth, require_admin, get_current_user_id


@app_views.route('/orders/<order_id>/status/transitions', methods=['GET'], strict_slashes=False)
@require_auth()
def get_order_transitions(order_id):
    """
    Get valid status transitions for an order.
    
    This endpoint returns the possible status transitions for an order
    based on its current status and business rules.
    
    Args:
        order_id (str): ID of the order
        
    Returns:
        JSON response with valid transitions or error message
    """
    try:
        order = storage.get(Order, order_id)
        
        if not order:
            return error_handler.not_found_error_response("Order")
        
        workflow_manager = OrderWorkflowManager(db_session=storage)
        valid_transitions = workflow_manager.get_valid_transitions(order.order_status)
        
        return error_handler.success_response(
            data={
                'order_id': order_id,
                'current_status': order.order_status,
                'valid_transitions': valid_transitions
            },
            message="Valid transitions retrieved successfully"
        )
    
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to get order transitions",
            error_details=str(e)
        )





@app_views.route('/orders/status-summary', methods=['GET'], strict_slashes=False)
@require_admin()
def get_order_status_summary():
    """
    Get summary of orders by status.
    
    This endpoint provides an overview of order distribution
    across different statuses for administrative purposes.
    
    Returns:
        JSON response with order status summary
    """
    try:
        workflow_manager = OrderWorkflowManager(db_session=storage)
        summary = workflow_manager.get_order_status_summary()
        
        return error_handler.success_response(
            data=summary,
            message="Order status summary retrieved successfully"
        )
    
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to get order status summary",
            error_details=str(e)
        )


@app_views.route('/orders/by-status/<status>', methods=['GET'], strict_slashes=False)
@require_admin()
def get_orders_by_status(status):
    """
    Get orders filtered by status.
    
    This endpoint retrieves orders with a specific status,
    with optional limit parameter for pagination.
    
    Args:
        status (str): Order status to filter by
        
    Query parameters:
        - limit: Maximum number of orders to return
        
    Returns:
        JSON response with filtered orders
    """
    try:
        # Validate status value
        try:
            OrderStatus(status)
        except ValueError:
            valid_statuses = [status.value for status in OrderStatus]
            return error_handler.validation_error_response(
                message="Invalid order status",
                field_errors={
                    'status': [f'Must be one of: {", ".join(valid_statuses)}']
                }
            )
        
        limit = request.args.get('limit', type=int)
        
        workflow_manager = OrderWorkflowManager(db_session=storage)
        orders = workflow_manager.get_orders_by_status(status, limit)
        
        return error_handler.success_response(
            data={
                'status': status,
                'orders': orders,
                'count': len(orders)
            },
            message=f"Retrieved {len(orders)} orders with status '{status}'"
        )
    
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to get orders by status",
            error_details=str(e)
        )


@app_views.route('/orders/<order_id>/validate', methods=['GET'], strict_slashes=False)
@require_auth()
def validate_order_business_rules(order_id):
    """
    Validate business rules for an order.
    
    This endpoint checks if an order complies with all business rules,
    including stock availability, pricing, and other constraints.
    
    Args:
        order_id (str): ID of the order to validate
        
    Returns:
        JSON response with validation results
    """
    try:
        order = storage.get(Order, order_id)
        
        if not order:
            return error_handler.not_found_error_response("Order")
        
        workflow_manager = OrderWorkflowManager(db_session=storage)
        validation_result = workflow_manager.validate_order_business_rules(order)
        
        return error_handler.success_response(
            data={
                'order_id': order_id,
                'is_valid': validation_result['is_valid'],
                'errors': validation_result['errors'],
                'warnings': validation_result['warnings']
            },
            message="Order validation completed"
        )
    
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to validate order",
            error_details=str(e)
        )