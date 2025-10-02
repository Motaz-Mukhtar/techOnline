#!/usr/bin/python3
"""
Search API endpoints for TechOnline e-commerce platform.

This module provides comprehensive search functionality including:
- Product search with various filters
- Search suggestions and autocomplete
- Category-based search
- Advanced filtering options
"""

from modules.engine.SEARCH_ENGINE import Search
from modules.Products.product import Product
from modules.Category.category import Category
from modules import storage
from api.v1.views import app_views
from api.v1.auth import require_auth, require_admin, optional_auth, get_current_user_id, is_admin
from flask import jsonify, make_response, request


@app_views.route('/search/products', methods=['GET'], strict_slashes=False) # type: ignore
@optional_auth()
def search_products():
    """
    Search for products with various filters.
    
    Query Parameters:
        - q: Search term for product name/description
        - category_id: Filter by category ID
        - category_name: Filter by category name
        - min_price: Minimum price filter
        - max_price: Maximum price filter
        - in_stock: Only return products in stock (true/false)
        - limit: Maximum number of results (default: 20)
        - sort_by: Sort results by 'name', 'price', 'created_at' (default: 'name')
    
    Returns:
        JSON response with search results or error message
    """
    try:
        # Get query parameters
        search_term = request.args.get('q', '').strip()
        category_id = request.args.get('category_id')
        category_name = request.args.get('category_name')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        in_stock_only = request.args.get('in_stock', 'true').lower() == 'true'
        limit = request.args.get('limit', type=int, default=20)
        sort_by = request.args.get('sort_by', 'name')
        
        # Validate sort_by parameter
        if sort_by not in ['name', 'price', 'created_at']:
            sort_by = 'name'
        
        # If category_name is provided, get category_id
        if category_name and not category_id:
            categories = storage.all(Category).values()
            for category in categories:
                if category_name.lower() in category.name.lower():
                    category_id = category.id
                    break
        
        # Perform search
        if search_term or category_id or min_price is not None or max_price is not None:
            # Use advanced search
            results = Search.search_products_advanced(
                search_term=search_term,
                category_id=category_id,
                min_price=min_price,
                max_price=max_price,
                in_stock_only=in_stock_only,
                limit=limit,
                sort_by=sort_by
            )
        else:
            # Return all products if no filters
            all_products = list(storage.all(Product).values())
            if in_stock_only:
                all_products = [p for p in all_products if p.stock_quantity > 0 and p.is_available]
            
            # Apply sorting
            if sort_by == 'price':
                all_products.sort(key=lambda x: x.price)
            elif sort_by == 'created_at':
                all_products.sort(key=lambda x: x.created_at, reverse=True)
            else:
                all_products.sort(key=lambda x: x.product_name)
            
            # Apply limit
            results = all_products[:limit] if limit else all_products
        
        # Convert to dict format
        products_data = [product.to_dict() for product in results]
        
        return make_response(jsonify({
            "query": search_term,
            "filters": {
                "category_id": category_id,
                "category_name": category_name,
                "min_price": min_price,
                "max_price": max_price,
                "in_stock_only": in_stock_only,
                "sort_by": sort_by
            },
            "total_results": len(products_data),
            "products": products_data
        }), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Search failed: {str(e)}"}), 500)


@app_views.route('/search/suggestions', methods=['GET'], strict_slashes=False) # type: ignore
@optional_auth()
def get_search_suggestions():
    """
    Get search suggestions for autocomplete functionality.
    
    Query Parameters:
        - q: Partial search term (minimum 2 characters)
        - limit: Maximum number of suggestions (default: 5)
    
    Returns:
        JSON response with search suggestions or error message
    """
    try:
        search_term = request.args.get('q', '').strip()
        limit = request.args.get('limit', type=int, default=5)
        
        if len(search_term) < 2:
            return make_response(jsonify({
                "error": "Search term must be at least 2 characters long"
            }), 400)
        
        suggestions = Search.get_search_suggestions(search_term, limit)
        
        return make_response(jsonify({
            "query": search_term,
            "suggestions": suggestions
        }), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to get suggestions: {str(e)}"}), 500)


@app_views.route('/search/categories', methods=['GET'], strict_slashes=False) # type: ignore
@optional_auth()
def search_categories():
    """
    Search for categories by name.
    
    Query Parameters:
        - q: Search term for category name
        - limit: Maximum number of results (default: 10)
    
    Returns:
        JSON response with matching categories or error message
    """
    try:
        search_term = request.args.get('q', '').strip()
        limit = request.args.get('limit', type=int, default=10)
        
        if not search_term:
            # Return all active categories if no search term
            all_categories = list(storage.all(Category).values())
            active_categories = [cat for cat in all_categories if cat.is_active]
            categories_data = [cat.to_dict() for cat in active_categories[:limit]]
        else:
            # Search categories by name
            all_categories = list(storage.all(Category).values())
            matching_categories = []
            
            for category in all_categories:
                if search_term.lower() in category.name.lower() and category.is_active:
                    matching_categories.append(category)
            
            categories_data = [cat.to_dict() for cat in matching_categories[:limit]]
        
        return make_response(jsonify({
            "query": search_term,
            "total_results": len(categories_data),
            "categories": categories_data
        }), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Category search failed: {str(e)}"}), 500)


@app_views.route('/search/categories/<category_id>/products', methods=['GET'], strict_slashes=False) # type: ignore
@optional_auth()
def get_products_by_category(category_id):
    """
    Get all products in a specific category.
    
    Args:
        category_id (str): ID of the category
    
    Query Parameters:
        - in_stock: Only return products in stock (true/false)
        - limit: Maximum number of results
        - sort_by: Sort results by 'name', 'price', 'created_at'
    
    Returns:
        JSON response with products in the category or error message
    """
    try:
        # Validate category exists
        category = storage.get(Category, category_id)
        if not category:
            return make_response(jsonify({"error": "Category not found"}), 404)
        
        # Get query parameters
        in_stock_only = request.args.get('in_stock', 'true').lower() == 'true'
        limit = request.args.get('limit', type=int)
        sort_by = request.args.get('sort_by', 'name')
        
        # Validate sort_by parameter
        if sort_by not in ['name', 'price', 'created_at']:
            sort_by = 'name'
        
        # Get products in category
        all_products = list(storage.all(Product).values())
        category_products = [p for p in all_products if p.category_id == category_id]
        
        # Apply stock filter
        if in_stock_only:
            category_products = [p for p in category_products if p.stock_quantity > 0 and p.is_available]
        
        # Apply sorting
        if sort_by == 'price':
            category_products.sort(key=lambda x: x.price)
        elif sort_by == 'created_at':
            category_products.sort(key=lambda x: x.created_at, reverse=True)
        else:
            category_products.sort(key=lambda x: x.product_name)
        
        # Apply limit
        if limit:
            category_products = category_products[:limit]
        
        # Convert to dict format
        products_data = [product.to_dict() for product in category_products]
        
        return make_response(jsonify({
            "category": category.to_dict(),
            "total_products": len(products_data),
            "products": products_data
        }), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to get category products: {str(e)}"}), 500)


@app_views.route('/search/filters', methods=['GET'], strict_slashes=False) # type: ignore
@optional_auth()
def get_search_filters():
    """
    Get available search filters and their options.
    
    Returns:
        JSON response with available filter options
    """
    try:
        # Get all categories
        categories = list(storage.all(Category).values())
        active_categories = [cat.to_dict() for cat in categories if cat.is_active]
        
        # Get price range from products
        products = list(storage.all(Product).values())
        if products:
            prices = [p.price for p in products if p.price is not None]
            min_price = min(prices) if prices else 0
            max_price = max(prices) if prices else 0
        else:
            min_price = max_price = 0
        
        return make_response(jsonify({
            "categories": active_categories,
            "price_range": {
                "min": min_price,
                "max": max_price
            },
            "sort_options": [
                {"value": "name", "label": "Name (A-Z)"},
                {"value": "price", "label": "Price (Low to High)"},
                {"value": "created_at", "label": "Newest First"}
            ],
            "availability_options": [
                {"value": "true", "label": "In Stock Only"},
                {"value": "false", "label": "All Products"}
            ]
        }), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to get filters: {str(e)}"}), 500)