#!/usr/bin/python3
"""
Review API endpoints for TechOnline e-commerce platform.

This module provides comprehensive review management functionality including:
- Review submission with validation
- Review retrieval with filtering and pagination
- Review moderation and approval
- Rating calculations and statistics
"""

from modules.Review.review import Review
from modules.Products.product import Product
from modules.Customer.customer import Customer
from modules.Order.order import Order
from modules.Order.order_item import OrderItem
from modules import storage
from api.v1.views import app_views
from api.v1.auth import require_auth, require_admin, optional_auth, get_current_user_id
from flask import jsonify, abort, make_response, request
from datetime import datetime


@app_views.route('/reviews', methods=['GET'], strict_slashes=False)
@optional_auth()
def get_reviews():
    """
    Get all reviews with optional filtering and pagination.
    
    Query Parameters:
        - product_id: Filter reviews by product ID
        - customer_id: Filter reviews by customer ID
        - rating: Filter by specific rating (1-5)
        - min_rating: Filter by minimum rating
        - approved_only: Only return approved reviews (true/false)
        - verified_only: Only return verified purchase reviews (true/false)
        - limit: Maximum number of results (default: 20)
        - offset: Number of results to skip (default: 0)
        - sort_by: Sort by 'date', 'rating', 'helpful' (default: 'date')
        - order: 'asc' or 'desc' (default: 'desc')
    
    Returns:
        JSON response with reviews list and pagination info
    """
    try:
        # Get query parameters
        product_id = request.args.get('product_id')
        customer_id = request.args.get('customer_id')
        rating = request.args.get('rating', type=int)
        min_rating = request.args.get('min_rating', type=float)
        approved_only = request.args.get('approved_only', 'true').lower() == 'true'
        verified_only = request.args.get('verified_only', 'false').lower() == 'true'
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        sort_by = request.args.get('sort_by', 'date')
        order = request.args.get('order', 'desc')
        
        # Get all reviews
        all_reviews = list(storage.all(Review).values())
        
        # Apply filters
        filtered_reviews = []
        for review in all_reviews:
            # Filter by product
            if product_id and review.product_id != product_id:
                continue
            
            # Filter by customer
            if customer_id and review.customer_id != customer_id:
                continue
            
            # Filter by specific rating
            if rating and int(round(review.rate)) != rating:
                continue
            
            # Filter by minimum rating
            if min_rating and review.rate < min_rating:
                continue
            
            # Filter by approval status
            if approved_only and review.is_approved != 1:
                continue
            
            # Filter by verified purchase
            if verified_only and review.is_verified != 1:
                continue
            
            filtered_reviews.append(review)
        
        # Sort reviews
        if sort_by == 'rating':
            filtered_reviews.sort(key=lambda x: x.rate, reverse=(order == 'desc'))
        elif sort_by == 'helpful':
            filtered_reviews.sort(key=lambda x: x.helpful_count, reverse=(order == 'desc'))
        else:  # sort by date
            filtered_reviews.sort(key=lambda x: x.created_at, reverse=(order == 'desc'))
        
        # Apply pagination
        total_reviews = len(filtered_reviews)
        paginated_reviews = filtered_reviews[offset:offset + limit]
        
        # Convert to dict
        reviews_list = [review.to_dict() for review in paginated_reviews]
        
        return jsonify({
            'reviews': reviews_list,
            'pagination': {
                'total': total_reviews,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_reviews
            }
        })
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to get reviews: {str(e)}"}), 500)


@app_views.route('/reviews/<review_id>', methods=['GET'], strict_slashes=False)
@optional_auth()
def get_review(review_id):
    """
    Get a specific review by ID.
    
    Args:
        review_id (str): The review ID
        
    Returns:
        JSON response with review details or error message
    """
    try:
        review = storage.get(Review, review_id)
        if not review:
            return make_response(jsonify({"error": "Review not found"}), 404)
        
        return jsonify(review.to_dict())
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to get review: {str(e)}"}), 500)


@app_views.route('/reviews', methods=['POST'], strict_slashes=False)
@require_auth(['write'])
def create_review():
    """
    Create a new product review.
    
    Required JSON fields:
        - product_id: ID of the product being reviewed
        - text: Review text content
        - rate: Rating (1.0 to 5.0)
        
    Optional JSON fields:
        - title: Review title
        
    Note:
        - customer_id is automatically determined from authentication token
        
    Returns:
        JSON response with created review or error message
    """
    try:
        # Validate JSON request
        if not request.get_json():
            return make_response(jsonify({"error": "Not a JSON request"}), 400)
        
        data = request.get_json()
        
        # Get authenticated customer ID
        customer_id = get_current_user_id()
        if not customer_id:
            return make_response(jsonify({"error": "Authentication required"}), 401)
        
        # Validate required fields
        required_fields = ['product_id', 'text', 'rate']
        for field in required_fields:
            if field not in data:
                return make_response(jsonify({"error": f"Missing required field: {field}"}), 400)
        
        # Validate product exists
        product = storage.get(Product, data['product_id'])
        if not product:
            return make_response(jsonify({"error": "Product not found"}), 404)
        
        # Validate customer exists
        customer = storage.get(Customer, customer_id)
        if not customer:
            return make_response(jsonify({"error": "Customer not found"}), 404)
        
        # Check if customer has already reviewed this product
        if product.has_customer_reviewed(customer_id):
            return make_response(jsonify({"error": "Customer has already reviewed this product"}), 400)
        
        # Create review instance
        review = Review(
            product_id=data['product_id'],
            customer_id=customer_id,
            text=data['text'],
            rate=float(data['rate']),
            title=data.get('title')
        )
        
        # Validate review
        is_valid, error_message = review.is_valid_review()
        if not is_valid:
            return make_response(jsonify({"error": error_message}), 400)
        
        # Check if this is a verified purchase
        is_verified = check_verified_purchase(customer_id, data['product_id'])
        if is_verified:
            review.mark_as_verified()
        
        # Save review
        review.save()
        
        # Update product's average rating
        product.calculate_average_rating()
        
        return make_response(jsonify(review.to_dict()), 201)
        
    except ValueError as e:
        return make_response(jsonify({"error": f"Invalid data format: {str(e)}"}), 400)
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to create review: {str(e)}"}), 500)


@app_views.route('/reviews/<review_id>', methods=['PUT'], strict_slashes=False)
@require_auth(['write'])
def update_review(review_id):
    """
    Update an existing review.
    
    Args:
        review_id (str): The review ID to update
        
    Allowed JSON fields:
        - text: Updated review text
        - title: Updated review title
        - rate: Updated rating (1.0 to 5.0)
        
    Returns:
        JSON response with updated review or error message
    """
    try:
        review = storage.get(Review, review_id)
        if not review:
            return make_response(jsonify({"error": "Review not found"}), 404)
        
        # Check if user owns this review
        current_user_id = get_current_user_id()
        if review.customer_id != current_user_id:
            return make_response(jsonify({"error": "You can only update your own reviews"}), 403)
        
        if not request.get_json():
            return make_response(jsonify({"error": "Not a JSON request"}), 400)
        
        data = request.get_json()
        
        # Update allowed fields
        if 'text' in data:
            if not review.validate_text(data['text']):
                return make_response(jsonify({"error": "Invalid review text"}), 400)
            review.text = data['text']
        
        if 'title' in data:
            if not review.validate_title(data['title']):
                return make_response(jsonify({"error": "Invalid review title"}), 400)
            review.title = data['title']
        
        if 'rate' in data:
            if not review.validate_rating(data['rate']):
                return make_response(jsonify({"error": "Invalid rating"}), 400)
            review.rate = float(data['rate'])
        
        # Validate updated review
        is_valid, error_message = review.is_valid_review()
        if not is_valid:
            return make_response(jsonify({"error": error_message}), 400)
        
        # Save changes
        review.save()
        
        # Update product's average rating if rating changed
        if 'rate' in data:
            product = storage.get(Product, review.product_id)
            if product:
                product.calculate_average_rating()
        
        return jsonify(review.to_dict())
        
    except ValueError as e:
        return make_response(jsonify({"error": f"Invalid data format: {str(e)}"}), 400)
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to update review: {str(e)}"}), 500)


@app_views.route('/reviews/<review_id>', methods=['DELETE'], strict_slashes=False)
@require_auth(['write'])
def delete_review(review_id):
    """
    Delete a review.
    
    Args:
        review_id (str): The review ID to delete
        
    Returns:
        JSON response confirming deletion or error message
    """
    try:
        review = storage.get(Review, review_id)
        if not review:
            return make_response(jsonify({"error": "Review not found"}), 404)
        
        # Check if user owns this review
        current_user_id = get_current_user_id()
        if review.customer_id != current_user_id:
            return make_response(jsonify({"error": "You can only delete your own reviews"}), 403)
        
        product_id = review.product_id
        
        # Delete review
        storage.delete(review)
        storage.save()
        
        # Update product's average rating
        product = storage.get(Product, product_id)
        if product:
            product.calculate_average_rating()
        
        return make_response(jsonify({"message": "Review deleted successfully"}), 200)
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to delete review: {str(e)}"}), 500)


@app_views.route('/products/<product_id>/reviews', methods=['GET'], strict_slashes=False)
@optional_auth()
def get_product_reviews(product_id):
    """
    Get all reviews for a specific product.
    
    Args:
        product_id (str): The product ID
        
    Query Parameters:
        - approved_only: Only return approved reviews (default: true)
        - limit: Maximum number of results (default: 10)
        - offset: Number of results to skip (default: 0)
        - sort_by: Sort by 'date', 'rating', 'helpful' (default: 'date')
        
    Returns:
        JSON response with product reviews and statistics
    """
    try:
        # Validate product exists
        product = storage.get(Product, product_id)
        if not product:
            return make_response(jsonify({"error": "Product not found"}), 404)
        
        # Get query parameters
        approved_only = request.args.get('approved_only', 'true').lower() == 'true'
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        sort_by = request.args.get('sort_by', 'date')
        
        # Get product reviews
        all_reviews = storage.all(Review)
        product_reviews = [
            review for review in all_reviews.values()
            if review.product_id == product_id and (not approved_only or review.is_approved == 1)
        ]
        
        # Sort reviews
        if sort_by == 'rating':
            product_reviews.sort(key=lambda x: x.rate, reverse=True)
        elif sort_by == 'helpful':
            product_reviews.sort(key=lambda x: x.helpful_count, reverse=True)
        else:  # sort by date
            product_reviews.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total_reviews = len(product_reviews)
        paginated_reviews = product_reviews[offset:offset + limit]
        
        # Get review statistics
        review_summary = product.get_review_summary()
        
        return jsonify({
            'product_id': product_id,
            'product_name': product.product_name,
            'reviews': [review.to_dict() for review in paginated_reviews],
            'statistics': review_summary,
            'pagination': {
                'total': total_reviews,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_reviews
            }
        })
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to get product reviews: {str(e)}"}), 500)


@app_views.route('/customers/<customer_id>/reviews', methods=['GET'], strict_slashes=False)
@require_auth(['read'])
def get_customer_reviews(customer_id):
    """
    Get all reviews by a specific customer.
    
    Args:
        customer_id (str): The customer ID
        
    Query Parameters:
        - limit: Maximum number of results (default: 10)
        - offset: Number of results to skip (default: 0)
        
    Returns:
        JSON response with customer reviews
    """
    try:
        # Validate customer exists
        customer = storage.get(Customer, customer_id)
        if not customer:
            return make_response(jsonify({"error": "Customer not found"}), 404)
        
        # Get query parameters
        limit = request.args.get('limit', 10, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Get customer reviews
        all_reviews = storage.all(Review)
        customer_reviews = [
            review for review in all_reviews.values()
            if review.customer_id == customer_id
        ]
        
        # Sort by date (most recent first)
        customer_reviews.sort(key=lambda x: x.created_at, reverse=True)
        
        # Apply pagination
        total_reviews = len(customer_reviews)
        paginated_reviews = customer_reviews[offset:offset + limit]
        
        return jsonify({
            'customer_id': customer_id,
            'customer_name': f"{customer.first_name} {customer.last_name}",
            'reviews': [review.to_dict() for review in paginated_reviews],
            'total_reviews': total_reviews,
            'pagination': {
                'total': total_reviews,
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_reviews
            }
        })
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to get customer reviews: {str(e)}"}), 500)


@app_views.route('/reviews/<review_id>/approve', methods=['PUT'], strict_slashes=False)
@require_admin()
def approve_review(review_id):
    """
    Approve a review for public display (admin function).
    
    Args:
        review_id (str): The review ID to approve
        
    Returns:
        JSON response confirming approval or error message
    """
    try:
        review = storage.get(Review, review_id)
        if not review:
            return make_response(jsonify({"error": "Review not found"}), 404)
        
        review.approve_review()
        
        # Update product's average rating
        product = storage.get(Product, review.product_id)
        if product:
            product.calculate_average_rating()
        
        return jsonify({"message": "Review approved successfully", "review": review.to_dict()})
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to approve review: {str(e)}"}), 500)


@app_views.route('/reviews/<review_id>/reject', methods=['PUT'], strict_slashes=False)
@require_admin()
def reject_review(review_id):
    """
    Reject a review (hide from public display).
    
    Args:
        review_id (str): The review ID to reject
        
    Returns:
        JSON response confirming rejection or error message
    """
    try:
        review = storage.get(Review, review_id)
        if not review:
            return make_response(jsonify({"error": "Review not found"}), 404)
        
        review.reject_review()
        
        # Update product's average rating
        product = storage.get(Product, review.product_id)
        if product:
            product.calculate_average_rating()
        
        return jsonify({"message": "Review rejected successfully", "review": review.to_dict()})
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to reject review: {str(e)}"}), 500)


@app_views.route('/reviews/<review_id>/helpful', methods=['PUT'], strict_slashes=False)
@require_auth(['write'])
def mark_review_helpful(review_id):
    """
    Mark a review as helpful (increment helpful count).
    
    Args:
        review_id (str): The review ID to mark as helpful
        
    Returns:
        JSON response with updated helpful count or error message
    """
    try:
        review = storage.get(Review, review_id)
        if not review:
            return make_response(jsonify({"error": "Review not found"}), 404)
        
        review.add_helpful_vote()
        
        return jsonify({
            "message": "Review marked as helpful",
            "helpful_count": review.helpful_count
        })
        
    except Exception as e:
        return make_response(jsonify({"error": f"Failed to mark review as helpful: {str(e)}"}), 500)


def check_verified_purchase(customer_id, product_id):
    """
    Check if a customer has purchased a specific product (verified purchase).
    
    Args:
        customer_id (str): The customer ID
        product_id (str): The product ID
        
    Returns:
        bool: True if customer has purchased the product, False otherwise
    """
    try:
        # Get all orders for the customer
        all_orders = storage.all(Order)
        customer_orders = [
            order for order in all_orders.values()
            if order.customer_id == customer_id and order.status in ['completed', 'delivered']
        ]
        
        # Check if any order contains the product
        all_order_items = storage.all(OrderItem)
        for order in customer_orders:
            order_items = [
                item for item in all_order_items.values()
                if item.order_id == order.id and item.product_id == product_id
            ]
            if order_items:
                return True
        
        return False
        
    except Exception:
        return False