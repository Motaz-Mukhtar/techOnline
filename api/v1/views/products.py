#!/usr/bin/python3
"""
Product API endpoints for TechOnline e-commerce platform.

This module provides product management functionality including:
- Product CRUD operations
- Product search and filtering
- Stock management integration
"""

from modules.Products.product import Product
from modules.engine.SEARCH_ENGINE import Search
from modules.utils.stock_manager import StockManager
from modules import storage
from modules.utils.file_handler import save_uploaded_file, delete_uploaded_file
from modules.utils.error_handler import error_handler
from modules.utils.validators import BusinessRuleValidator
from flask import jsonify, abort, make_response, request
from api.v1.views import app_views
from api.v1.auth import require_auth, require_admin, optional_auth, get_current_user_id, is_admin


@app_views.route('/products', methods=['GET'], strict_slashes=False)
@optional_auth()
def get_products():
    """
    Get all products with optional filtering and search.
    
    Query Parameters:
        - search: Search term for product name/description
        - category_id: Filter by category ID
        - min_price: Minimum price filter
        - max_price: Maximum price filter
        - in_stock: Only return products in stock (true/false)
        - limit: Maximum number of results
        - sort_by: Sort results by 'name', 'price', 'created_at'
    
    Returns:
        JSON response with products list or error message
    """
    try:
        # Get query parameters
        search_term = request.args.get('search')
        category_id = request.args.get('category_id')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        in_stock_only = request.args.get('in_stock', 'false').lower() == 'true'
        limit = request.args.get('limit', type=int)
        sort_by = request.args.get('sort_by', 'name')
        
        # Validate sort_by parameter
        valid_sort_options = ['name', 'price', 'created_at']
        if sort_by not in valid_sort_options:
            return error_handler.validation_error_response(
                message="Invalid sort parameter",
                errors=[f"sort_by must be one of: {', '.join(valid_sort_options)}"]
            )
        
        # Validate price range
        if min_price is not None and max_price is not None and min_price > max_price:
            return error_handler.validation_error_response(
                message="Invalid price range",
                errors=["min_price cannot be greater than max_price"]
            )
        
        # If any filters are applied, use advanced search
        if any([search_term, category_id, min_price is not None, max_price is not None, in_stock_only]):
            products = Search.search_products_advanced(
                search_term=search_term,
                category_id=category_id,
                min_price=min_price,
                max_price=max_price,
                in_stock_only=in_stock_only,
                limit=limit,
                sort_by=sort_by
            )
        else:
            # Get all products
            products = list(storage.all(Product).values())
            
            # Apply sorting
            if sort_by == 'price':
                products.sort(key=lambda x: x.price)
            elif sort_by == 'created_at':
                products.sort(key=lambda x: x.created_at, reverse=True)
            else:
                products.sort(key=lambda x: x.product_name)
            
            # Apply limit
            if limit:
                products = products[:limit]
        
        product_list = [product.to_dict() for product in products]
        return error_handler.success_response(
            data=product_list,
            message=f"Retrieved {len(product_list)} products successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to retrieve products",
            error_details=str(e)
        )

@app_views.route('/products/<product_id>', methods=['GET'], strict_slashes=False)
@optional_auth()
def get_product(product_id):
    """
    Get a specific product by ID.
    
    Args:
        product_id (str): ID of the product to retrieve
        
    Returns:
        JSON response with product data or error message
    """
    try:
        product = storage.get(Product, product_id)
        
        if not product:
            return error_handler.not_found_error_response("Product")
        
        return error_handler.success_response(
            data=product.to_dict(),
            message="Product retrieved successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to retrieve product",
            error_details=str(e)
        )

@app_views.route('/products/<product_id>', methods=['PUT', 'DELETE'], strict_slashes=False) # type: ignore
@require_admin()
def modify_product(product_id):
    """
    Update or delete a product.
    
    PUT: Update product information, including image upload
    DELETE: Delete product and associated image file
    
    Args:
        product_id (str): ID of the product to modify
        
    Returns:
        JSON response with updated product data or success message
    """
    try:
        product = storage.get(Product, product_id)
        
        if not product:
            return error_handler.not_found_error_response("Product")
        
        if request.method == 'PUT':
            # Handle both JSON and form data
            if request.is_json:
                data = request.get_json()
                if not data:
                    return error_handler.validation_error_response(
                        message="No JSON data provided"
                    )
            else:
                # Handle form data (for file uploads)
                data = request.form.to_dict()
            
            # Validate product data using BusinessRuleValidator
            validator = BusinessRuleValidator()
            validation_result = validator.validate_product_data(data, db_session=storage)
            
            if not validation_result['valid']:
                field_errors = error_handler.create_field_errors_dict(validation_result)
                return error_handler.validation_error_response(
                    message="Product validation failed",
                    errors=validation_result['errors'],
                    field_errors=field_errors
                )
            
            # Fields that cannot be updated
            ignore = ['id', 'created_at', 'updated_at', 'customer_id']
            
            # Update basic fields
            updated = False
            for key, value in data.items():
                if key not in ignore and hasattr(product, key):
                    # Additional validation for specific fields
                    if key == 'price':
                        try:
                            price = float(value)
                            if price <= 0:
                                return error_handler.validation_error_response(
                                    message="Invalid price value",
                                    field_errors={'price': ['Price must be positive']}
                                )
                            setattr(product, key, price)
                            updated = True
                        except (ValueError, TypeError):
                            return error_handler.validation_error_response(
                                message="Invalid price format",
                                field_errors={'price': ['Price must be a valid number']}
                            )
                    elif key in ['stock_quantity', 'min_stock_level']:
                        try:
                            quantity = int(value)
                            if quantity < 0:
                                return error_handler.validation_error_response(
                                    message=f"Invalid {key} value",
                                    field_errors={key: [f"{key} cannot be negative"]}
                                )
                            
                            # Track stock quantity changes with StockManager
                            if key == 'stock_quantity' and quantity != product.stock_quantity:
                                stock_manager = StockManager()
                                previous_stock = product.stock_quantity
                                change = quantity - previous_stock
                                movement_type = 'stock_adjustment_increase' if change > 0 else 'stock_adjustment_decrease'
                                
                                stock_manager._log_stock_movement(
                                    product_id=product.id,
                                    movement_type=movement_type,
                                    quantity=abs(change),
                                    previous_stock=previous_stock,
                                    new_stock=quantity,
                                    notes=f'Admin stock adjustment for {product.product_name}'
                                )
                            
                            setattr(product, key, quantity)
                            updated = True
                        except (ValueError, TypeError):
                            return error_handler.validation_error_response(
                                message=f"Invalid {key} format",
                                field_errors={key: [f"{key} must be a valid integer"]}
                            )
                    elif key in ['product_name', 'description']:
                        if value and value.strip():
                            setattr(product, key, value.strip())
                            updated = True
                    else:
                        setattr(product, key, value)
                        updated = True
            
            # Handle image upload if present
            if 'product_image' in request.files:
                file = request.files['product_image']
                if file and file.filename:
                    # Delete old image if exists
                    if product.product_image_filename:
                        delete_uploaded_file(product.product_image_filename, 'product')
                    
                    # Save new image
                    result = save_uploaded_file(file, 'product', product.id)
                    
                    if result['success']:
                        product.product_image = result['url']
                        product.product_image_filename = result['filename']
                        updated = True
                    else:
                        return error_handler.file_upload_error_response(
                            message="Product image upload failed",
                            file_errors=[result['error']]
                        )
            
            if updated:
                product.save()
                return error_handler.success_response(
                    data=product.to_dict(),
                    message="Product updated successfully"
                )
            else:
                return error_handler.validation_error_response(
                    message="No valid fields to update"
                )
        
        elif request.method == 'DELETE':
            # Delete associated image file if exists
            if product.product_image_filename:
                delete_uploaded_file(product.product_image_filename, 'product')
            
            # Delete product from database
            storage.delete(product)
            storage.save()
            
            return error_handler.success_response(
                message="Product deleted successfully"
            )
    
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to modify product",
            error_details=str(e)
        )

@app_views.route('/products', methods=['POST'], strict_slashes=False) # type: ignore
@require_admin()
def add_product():
    """
    Create new Product instance and add it to the database.
    
    Supports both JSON data and multipart form data for file uploads.
    
    Expected form data:
        - product_name: Name of the product
        - description: Product description
        - price: Product price
        - category_id: Category ID
        - stock_quantity: Initial stock quantity
        - min_stock_level: Minimum stock level
        - product_image: Image file (optional)
    
    Returns:
        JSON response with created product data or error message
    """
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            if not data:
                return error_handler.validation_error_response(
                    message="No JSON data provided"
                )
        else:
            # Handle form data (for file uploads)
            data = request.form.to_dict()
        
        # Validate product data using BusinessRuleValidator
        validator = BusinessRuleValidator(db_session=None)
        validation_result = validator.validate_product_data(data)
        
        if not validation_result['valid']:
            field_errors = error_handler.create_field_errors_dict(validation_result)
            return error_handler.validation_error_response(
                message="Product validation failed",
                errors=validation_result['errors'],
                field_errors=field_errors
            )
        
        # Additional business rule validation
        business_rules_validation = validator.validate_product_business_rules(data)
        if not business_rules_validation['valid']:
            return error_handler.validation_error_response(
                message="Product business rules validation failed",
                errors=business_rules_validation['errors'],
                field_errors=error_handler.create_field_errors_dict({
                    'errors': business_rules_validation['errors'],
                    'warnings': business_rules_validation['warnings']
                })
            )
        
        # Additional validation for required fields
        required_fields = ['product_name', 'description', 'price', 'category_id']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return error_handler.validation_error_response(
                message="Missing required fields",
                field_errors={field: [f"{field} is required"] for field in missing_fields}
            )
        
        # Validate price
        try:
            price = float(data['price'])
            if price <= 0:
                return error_handler.validation_error_response(
                    message="Invalid price value",
                    field_errors={'price': ['Price must be positive']}
                )
        except (ValueError, TypeError):
            return error_handler.validation_error_response(
                message="Invalid price format",
                field_errors={'price': ['Price must be a valid number']}
            )
        
        # Validate stock quantity
        try:
            stock_quantity = int(data.get('stock_quantity', 0))
            min_stock_level = int(data.get('min_stock_level', 5))
            
            if stock_quantity < 0:
                return error_handler.validation_error_response(
                    message="Invalid stock quantity",
                    field_errors={'stock_quantity': ['Stock quantity cannot be negative']}
                )
        except (ValueError, TypeError):
            return error_handler.validation_error_response(
                message="Invalid stock quantity format",
                field_errors={'stock_quantity': ['Stock quantity must be a valid integer']}
            )
        
        # Create product instance
        # For admin users, we'll use a special admin customer_id or allow NULL
        current_user_id = get_current_user_id()
        if current_user_id is None and is_admin():
            # For admin API key users, use a special admin customer ID
            current_user_id = 'admin_user'
        
        product_data = {
            'product_name': data['product_name'].strip(),
            'description': data['description'].strip(),
            'price': price,
            'category_id': data['category_id'],
            'stock_quantity': stock_quantity,
            'min_stock_level': min_stock_level,
            'customer_id': current_user_id
        }
        
        product_instance = Product(**product_data)
        product_instance.save()
        
        # Log initial stock using StockManager
        if stock_quantity > 0:
            stock_manager = StockManager()
            stock_manager._log_stock_movement(
                product_id=product_instance.id,
                movement_type='initial_stock',
                quantity=stock_quantity,
                previous_stock=0,
                new_stock=stock_quantity,
                notes=f'Initial stock for new product: {product_instance.product_name}'
            )
        
        # Handle image upload if present
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file and file.filename:
                # Save the uploaded file
                result = save_uploaded_file(file, 'product', product_instance.id)
                
                if result['success']:
                    # Update product with image information
                    product_instance.product_image = result['url']
                    product_instance.product_image_filename = result['filename']
                    product_instance.save()
                else:
                    # Delete the product if image upload failed
                    product_instance.delete()
                    return error_handler.file_upload_error_response(
                        message="Product image upload failed",
                        file_errors=[result['error']]
                    )
        
        return error_handler.success_response(
            data=product_instance.to_dict(),
            message="Product created successfully",
            status_code=error_handler.HTTP_201_CREATED
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to create product",
            error_details=str(e)
        )





# /product/reivews