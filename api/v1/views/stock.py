#!/usr/bin/python3
"""
Stock Management API endpoints for TechOnline e-commerce platform.

This module provides comprehensive stock management functionality including:
- Stock level monitoring and alerts
- Stock reservations and releases
- Inventory adjustments and tracking
- Low stock and out-of-stock reporting
"""

from modules.Products.product import Product
from modules.utils.stock_manager import StockManager
from modules.utils.error_handler import error_handler
from modules.utils.validators import BusinessRuleValidator
from modules import storage
from api.v1.views import app_views
from api.v1.auth import require_auth, require_admin, optional_auth, get_current_user_id, is_admin
from flask import jsonify, abort, make_response, request


@app_views.route('/stock/check/<product_id>', methods=['GET'], strict_slashes=False)  # type: ignore
@optional_auth
def check_product_stock(product_id):
    """
    Check stock availability for a specific product.
    
    Args:
        product_id (str): Product ID to check stock for
        
    Query Parameters:
        quantity (int, optional): Quantity to check availability for (default: 1)
        
    Returns:
        JSON response with stock information
    """
    try:
        # Get requested quantity from query parameters
        requested_quantity = request.args.get('quantity', 1, type=int)
        
        if requested_quantity <= 0:
            return error_handler.validation_error_response(
                "Quantity must be a positive integer"
            )
        
        # Initialize stock manager
        stock_manager = StockManager(storage.get_session())
        
        # Check stock availability
        stock_info = stock_manager.check_stock_availability(product_id, requested_quantity)
        
        return error_handler.success_response(
            data=stock_info,
            message="Stock information retrieved successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            f"Failed to check stock: {str(e)}"
        )


@app_views.route('/stock/check/bulk', methods=['POST'], strict_slashes=False)  # type: ignore
@optional_auth
def check_multiple_products_stock():
    """
    Check stock availability for multiple products.
    
    Request Body:
        {
            "products": [
                {"product_id": "string", "quantity": int},
                ...
            ]
        }
        
    Returns:
        JSON response with bulk stock check results
    """
    try:
        # Validate request format
        if not request.is_json:
            return error_handler.validation_error_response(
                "Request must be in JSON format"
            )
        
        data = request.get_json()
        
        # Validate required fields
        if 'products' not in data:
            return error_handler.validation_error_response(
                "Missing required field: products"
            )
        
        products = data['products']
        
        if not isinstance(products, list) or not products:
            return error_handler.validation_error_response(
                "Products must be a non-empty list"
            )
        
        # Validate product entries
        for i, product in enumerate(products):
            if not isinstance(product, dict):
                return error_handler.validation_error_response(
                    f"Product at index {i} must be an object"
                )
            
            if 'product_id' not in product or 'quantity' not in product:
                return error_handler.validation_error_response(
                    f"Product at index {i} missing required fields: product_id, quantity"
                )
            
            if not isinstance(product['quantity'], int) or product['quantity'] <= 0:
                return error_handler.validation_error_response(
                    f"Product at index {i} quantity must be a positive integer"
                )
        
        # Initialize stock manager
        stock_manager = StockManager(storage.get_session())
        
        # Check stock for all products
        stock_results = stock_manager.check_multiple_products_stock(products)
        
        return error_handler.success_response(
            data=stock_results,
            message="Bulk stock check completed successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            f"Failed to check bulk stock: {str(e)}"
        )


@app_views.route('/stock/reserve', methods=['POST'], strict_slashes=False)  # type: ignore
@require_admin
def reserve_stock():
    """
    Reserve stock for a product (admin only).
    
    Request Body:
        {
            "product_id": "string",
            "quantity": int,
            "order_id": "string" (optional),
            "reason": "string" (optional)
        }
        
    Returns:
        JSON response with reservation result
    """
    try:
        # Validate request format
        if not request.is_json:
            return error_handler.validation_error_response(
                "Request must be in JSON format"
            )
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return error_handler.validation_error_response(
                    f"Missing required field: {field}"
                )
        
        product_id = data['product_id']
        quantity = data['quantity']
        order_id = data.get('order_id')
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity <= 0:
            return error_handler.validation_error_response(
                "Quantity must be a positive integer"
            )
        
        # Initialize stock manager
        stock_manager = StockManager(storage.get_session())
        
        # Reserve stock
        reservation_result = stock_manager.reserve_stock(product_id, quantity, order_id)
        
        if reservation_result['success']:
            return error_handler.success_response(
                data=reservation_result,
                message="Stock reserved successfully"
            )
        else:
            return error_handler.validation_error_response(
                reservation_result['message']
            )
        
    except Exception as e:
        return error_handler.system_error_response(
            f"Failed to reserve stock: {str(e)}"
        )


@app_views.route('/stock/release', methods=['POST'], strict_slashes=False)  # type: ignore
@require_admin
def release_stock():
    """
    Release previously reserved stock (admin only).
    
    Request Body:
        {
            "product_id": "string",
            "quantity": int,
            "order_id": "string" (optional),
            "reason": "string" (optional)
        }
        
    Returns:
        JSON response with release result
    """
    try:
        # Validate request format
        if not request.is_json:
            return error_handler.validation_error_response(
                "Request must be in JSON format"
            )
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_id', 'quantity']
        for field in required_fields:
            if field not in data:
                return error_handler.validation_error_response(
                    f"Missing required field: {field}"
                )
        
        product_id = data['product_id']
        quantity = data['quantity']
        order_id = data.get('order_id')
        
        # Validate quantity
        if not isinstance(quantity, int) or quantity <= 0:
            return error_handler.validation_error_response(
                "Quantity must be a positive integer"
            )
        
        # Initialize stock manager
        stock_manager = StockManager(storage.get_session())
        
        # Release stock
        release_result = stock_manager.release_stock(product_id, quantity, order_id)
        
        if release_result['success']:
            return error_handler.success_response(
                data=release_result,
                message="Stock released successfully"
            )
        else:
            return error_handler.validation_error_response(
                release_result['message']
            )
        
    except Exception as e:
        return error_handler.system_error_response(
            f"Failed to release stock: {str(e)}"
        )


@app_views.route('/stock/adjust', methods=['PUT'], strict_slashes=False)  # type: ignore
@require_admin
def adjust_stock():
    """
    Adjust stock quantity for a product (admin only).
    
    Request Body:
        {
            "product_id": "string",
            "new_quantity": int,
            "reason": "string" (optional)
        }
        
    Returns:
        JSON response with adjustment result
    """
    try:
        # Validate request format
        if not request.is_json:
            return error_handler.validation_error_response(
                "Request must be in JSON format"
            )
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['product_id', 'new_quantity']
        for field in required_fields:
            if field not in data:
                return error_handler.validation_error_response(
                    f"Missing required field: {field}"
                )
        
        product_id = data['product_id']
        new_quantity = data['new_quantity']
        reason = data.get('reason', 'Manual adjustment via API')
        
        # Validate new_quantity
        if not isinstance(new_quantity, int) or new_quantity < 0:
            return error_handler.validation_error_response(
                "New quantity must be a non-negative integer"
            )
        
        # Initialize stock manager
        stock_manager = StockManager(storage.get_session())
        
        # Update stock quantity
        adjustment_result = stock_manager.update_stock_quantity(product_id, new_quantity, reason)
        
        if adjustment_result['success']:
            return error_handler.success_response(
                data=adjustment_result,
                message="Stock adjusted successfully"
            )
        else:
            return error_handler.validation_error_response(
                adjustment_result['message']
            )
        
    except Exception as e:
        return error_handler.system_error_response(
            f"Failed to adjust stock: {str(e)}"
        )


@app_views.route('/stock/low-stock', methods=['GET'], strict_slashes=False)  # type: ignore
@require_admin
def get_low_stock_products():
    """
    Get products with low stock levels (admin only).
    
    Query Parameters:
        threshold (int, optional): Custom low stock threshold
        
    Returns:
        JSON response with low stock products
    """
    try:
        # Get threshold from query parameters
        threshold = request.args.get('threshold', type=int)
        
        # Initialize stock manager
        stock_manager = StockManager(storage.get_session())
        
        # Get low stock products
        low_stock_products = stock_manager.get_low_stock_products(threshold)
        
        return error_handler.success_response(
            data={
                'products': low_stock_products,
                'count': len(low_stock_products),
                'threshold_used': threshold or stock_manager.LOW_STOCK_THRESHOLD
            },
            message="Low stock products retrieved successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            f"Failed to get low stock products: {str(e)}"
        )


@app_views.route('/stock/out-of-stock', methods=['GET'], strict_slashes=False)  # type: ignore
@require_admin
def get_out_of_stock_products():
    """
    Get products that are out of stock (admin only).
    
    Returns:
        JSON response with out of stock products
    """
    try:
        # Initialize stock manager
        stock_manager = StockManager(storage.get_session())
        
        # Get out of stock products
        out_of_stock_products = stock_manager.get_out_of_stock_products()
        
        return error_handler.success_response(
            data={
                'products': out_of_stock_products,
                'count': len(out_of_stock_products)
            },
            message="Out of stock products retrieved successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            f"Failed to get out of stock products: {str(e)}"
        )


@app_views.route('/stock/summary', methods=['GET'], strict_slashes=False)  # type: ignore
@require_admin
def get_stock_summary():
    """
    Get overall stock summary and statistics (admin only).
    
    Returns:
        JSON response with stock summary
    """
    try:
        # Initialize stock manager
        stock_manager = StockManager(storage.get_session())
        
        # Get stock data
        low_stock_products = stock_manager.get_low_stock_products()
        out_of_stock_products = stock_manager.get_out_of_stock_products()
        
        # Get all products for total count
        all_products = storage.all(Product).values()
        total_products = len(all_products)
        
        # Calculate stock statistics
        total_stock_value = 0
        normal_stock_count = 0
        critical_stock_count = 0
        
        for product in all_products:
            if product.stock_quantity and product.price:
                total_stock_value += product.stock_quantity * float(product.price)
            
            stock_level = stock_manager._get_stock_level_status(product.stock_quantity or 0)
            if stock_level == 'normal':
                normal_stock_count += 1
            elif stock_level == 'critical':
                critical_stock_count += 1
        
        summary = {
            'total_products': total_products,
            'normal_stock': normal_stock_count,
            'low_stock': len(low_stock_products),
            'critical_stock': critical_stock_count,
            'out_of_stock': len(out_of_stock_products),
            'total_stock_value': round(total_stock_value, 2),
            'thresholds': {
                'low_stock': stock_manager.LOW_STOCK_THRESHOLD,
                'critical_stock': stock_manager.CRITICAL_STOCK_THRESHOLD
            }
        }
        
        return error_handler.success_response(
            data=summary,
            message="Stock summary retrieved successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            f"Failed to get stock summary: {str(e)}"
        )