#!/usr/bin/env python3
"""
Authentication API endpoints for TechOnline e-commerce platform.

This module provides authentication endpoints including:
- Customer login and token generation
- Token refresh and validation
- API key generation and management
- Password reset functionality
"""

from api.v1.views import app_views
from api.v1.auth import (
    generate_jwt_token, 
    authenticate_customer, 
    generate_api_key,
    verify_jwt_token,
    require_auth,
    require_admin,
    AuthenticationError
)
from modules.Customer.customer import Customer
from modules import storage
from modules.utils.file_handler import save_uploaded_file, delete_uploaded_file
from modules.utils.error_handler import error_handler
from modules.utils.validators import BusinessRuleValidator
from flask import request, jsonify, make_response
from flask_bcrypt import generate_password_hash
import datetime


@app_views.route('/auth/login', methods=['POST'], strict_slashes=False)
def api_login():
    """
    Authenticate a customer and return a JWT token.
    
    Expected JSON payload:
        {
            "email": "customer@example.com",
            "password": "password123"
        }
    
    Returns:
        JSON response with JWT token and customer info or error message
    """
    try:
        if not request.get_json():
            return error_handler.validation_error_response(
                message="Invalid request format",
                errors=["Request must contain JSON data"]
            )
        
        data = request.get_json()
        
        # Validate required fields
        if 'email' not in data or 'password' not in data:
            missing_fields = []
            if 'email' not in data:
                missing_fields.append('email')
            if 'password' not in data:
                missing_fields.append('password')
            
            return error_handler.validation_error_response(
                message="Missing required fields",
                field_errors={field: [f"{field} is required"] for field in missing_fields}
            )
        
        # Validate email format
        validator = BusinessRuleValidator()
        if not validator.validate_email(data['email']):
            return error_handler.validation_error_response(
                message="Invalid email format",
                field_errors={'email': ['Please provide a valid email address']}
            )
        
        email = data['email'].strip().lower()
        password = data['password']
        
        # Authenticate customer
        customer = authenticate_customer(email, password)
        
        # Generate JWT token
        token = generate_jwt_token(customer.id, customer.email)
        
        return error_handler.success_response(
            data={
                "token": token,
                "token_type": "Bearer",
                "expires_in": 24 * 3600,  # 24 hours in seconds
                "customer": {
                    "id": customer.id,
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name
                }
            },
            message="Login successful"
        )
        
    except AuthenticationError as e:
        return error_handler.authentication_error_response(
            message=str(e)
        )
    except Exception as e:
        return error_handler.system_error_response(
            message="Login failed",
            error_details=str(e)
        )


@app_views.route('/auth/register', methods=['POST'], strict_slashes=False)
def api_register():
    """
    Register a new customer and return a JWT token.
    
    Expected JSON payload:
        {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password": "password123",
            "address": "123 Main St"
        }
    
    Returns:
        JSON response with JWT token and customer info or error message
    """
    try:
        if not request.get_json():
            return error_handler.validation_error_response(
                message="Invalid request format",
                errors=["Request must contain JSON data"]
            )
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email', 'password', 'address']
        missing_fields = []
        for field in required_fields:
            if field not in data or not data[field].strip():
                missing_fields.append(field)
        
        if missing_fields:
            return error_handler.validation_error_response(
                message="Missing required fields",
                field_errors={field: [f"{field} is required"] for field in missing_fields}
            )
        
        # Validate customer data using BusinessRuleValidator
        validator = BusinessRuleValidator()
        validation_result = validator.validate_customer_data(data)
        if not validation_result['is_valid']:
            return error_handler.validation_error_response(
                message="Invalid customer data",
                field_errors=validation_result['errors']
            )
        
        email = data['email'].strip().lower()
        
        # Check if customer already exists
        customers = storage.all(Customer).values()
        for customer in customers:
            if customer.email == email:
                return error_handler.validation_error_response(
                    message="Registration failed",
                    field_errors={'email': ['Email address is already registered']}
                )
        
        # Hash password
        from app import bcrypt
        hashed_password = bcrypt.generate_password_hash(data['password'])
        
        # Create new customer
        new_customer = Customer(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            email=email,
            password=hashed_password,
            address=data['address'].strip()
        )
        
        new_customer.save()
        
        # Generate JWT token
        token = generate_jwt_token(new_customer.id, new_customer.email)
        
        return error_handler.success_response(
            data={
                "token": token,
                "token_type": "Bearer",
                "expires_in": 24 * 3600,  # 24 hours in seconds
                "customer": {
                    "id": new_customer.id,
                    "email": new_customer.email,
                    "first_name": new_customer.first_name,
                    "last_name": new_customer.last_name
                }
            },
            message="Registration successful",
            status_code=201
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Registration failed",
            error_details=str(e)
        )


@app_views.route('/auth/refresh', methods=['POST'], strict_slashes=False)
@require_auth()
def refresh_token():
    """
    Refresh a JWT token.
    
    Requires:
        Authorization header with valid Bearer token
    
    Returns:
        JSON response with new JWT token or error message
    """
    try:
        auth_info = request.auth_info
        
        if auth_info['type'] != 'jwt':
            return error_handler.authentication_error_response(
                message="JWT token required for refresh"
            )
        
        customer = auth_info['customer']
        
        # Generate new token
        new_token = generate_jwt_token(customer.id, customer.email)
        
        return error_handler.success_response(
            data={
                "token": new_token,
                "token_type": "Bearer",
                "expires_in": 24 * 3600  # 24 hours in seconds
            },
            message="Token refreshed successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Token refresh failed",
            error_details=str(e)
        )


@app_views.route('/auth/validate', methods=['GET'], strict_slashes=False)
@require_auth()
def validate_token():
    """
    Validate the current authentication token.
    
    Requires:
        Authorization header with valid Bearer token or API key
    
    Returns:
        JSON response with token validation info
    """
    try:
        auth_info = request.auth_info
        
        response_data = {
            "valid": True,
            "auth_type": auth_info['type'],
            "permissions": auth_info.get('permissions', [])
        }
        
        if auth_info['type'] == 'jwt':
            customer = auth_info['customer']
            response_data.update({
                "customer": {
                    "id": customer.id,
                    "email": customer.email,
                    "first_name": customer.first_name,
                    "last_name": customer.last_name
                }
            })
        elif auth_info['type'] == 'api_key':
            response_data.update({
                "user_type": auth_info.get('user_type')
            })
        
        return error_handler.success_response(
            data=response_data,
            message="Token validation successful"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Token validation failed",
            error_details=str(e)
        )


@app_views.route('/auth/profile', methods=['GET'], strict_slashes=False)
@require_auth()
def get_profile():
    """
    Get the current authenticated customer's profile.
    
    Requires:
        Authorization header with valid Bearer token
    
    Returns:
        JSON response with customer profile or error message
    """
    try:
        auth_info = request.auth_info
        
        if auth_info['type'] != 'jwt':
            return error_handler.authentication_error_response(
                message="Customer authentication required"
            )
        
        customer = auth_info['customer']
        
        return error_handler.success_response(
            data={
                "customer": customer.to_dict()
            },
            message="Profile retrieved successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to get profile",
            error_details=str(e)
        )


@app_views.route('/auth/profile', methods=['PUT'], strict_slashes=False)
@require_auth()
def update_profile():
    """
    Update the current authenticated customer's profile.
    
    Supports both JSON data and multipart form data for profile image uploads.
    
    Requires:
        Authorization header with valid Bearer token
    
    Expected form data or JSON payload (all fields optional):
        {
            "first_name": "John",
            "last_name": "Doe",
            "address": "123 New St"
        }
        
    For file upload, use multipart form data with:
        - profile_avatar: Image file
        - Other profile fields as form data
    
    Returns:
        JSON response with updated customer profile or error message
    """
    try:
        auth_info = request.auth_info
        
        if auth_info['type'] != 'jwt':
            return error_handler.authentication_error_response(
                message="Customer authentication required"
            )
        
        customer = auth_info['customer']
        
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            if not data:
                return error_handler.validation_error_response(
                    message="Invalid request format",
                    errors=["Request must contain JSON data"]
                )
        else:
            # Handle form data (for file uploads)
            data = request.form.to_dict()
        
        # Update allowed fields
        updatable_fields = ['first_name', 'last_name', 'address']
        updated = False
        
        for field in updatable_fields:
            if field in data and data[field] and data[field].strip():
                setattr(customer, field, data[field].strip())
                updated = True
        
        # Handle profile image upload if present
        if 'profile_avatar' in request.files:
            file = request.files['profile_avatar']
            if file and file.filename:
                # Delete old profile image if exists
                if customer.profile_avatar_filename:
                    delete_uploaded_file(customer.profile_avatar_filename, 'profile')
                
                # Save new profile image
                result = save_uploaded_file(file, 'profile', customer.id)
                
                if result['success']:
                    customer.profile_avatar = result['url']
                    customer.profile_avatar_filename = result['filename']
                    updated = True
                else:
                    return error_handler.file_upload_error_response(
                        message="Profile image upload failed",
                        error_details=result['error']
                    )
        
        if updated:
            customer.save()
            return error_handler.success_response(
                data={
                    "customer": customer.to_dict()
                },
                message="Profile updated successfully"
            )
        else:
            return error_handler.validation_error_response(
                message="No valid fields to update",
                errors=["At least one field must be provided for update"]
            )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to update profile",
            error_details=str(e)
        )


@app_views.route('/auth/change-password', methods=['PUT'], strict_slashes=False)
@require_auth()
def change_password():
    """
    Change the current authenticated customer's password.
    
    Requires:
        Authorization header with valid Bearer token
    
    Expected JSON payload:
        {
            "current_password": "oldpassword",
            "new_password": "newpassword"
        }
    
    Returns:
        JSON response confirming password change or error message
    """
    try:
        auth_info = request.auth_info
        
        if auth_info['type'] != 'jwt':
            return error_handler.authentication_error_response(
                message="Customer authentication required"
            )
        
        if not request.get_json():
            return error_handler.validation_error_response(
                message="Invalid request format",
                errors=["Request must contain JSON data"]
            )
        
        data = request.get_json()
        
        # Validate required fields
        missing_fields = []
        if 'current_password' not in data:
            missing_fields.append('current_password')
        if 'new_password' not in data:
            missing_fields.append('new_password')
        
        if missing_fields:
            return error_handler.validation_error_response(
                message="Missing required fields",
                field_errors={field: [f"{field} is required"] for field in missing_fields}
            )
        
        # Validate new password strength
        validator = BusinessRuleValidator()
        if not validator.validate_password(data['new_password']):
            return error_handler.validation_error_response(
                message="Invalid password",
                field_errors={'new_password': ['Password must be at least 8 characters long and contain letters and numbers']}
            )
        
        customer = auth_info['customer']
        
        # Verify current password
        from flask_bcrypt import check_password_hash
        if not check_password_hash(customer.password, data['current_password']):
            return error_handler.authentication_error_response(
                message="Current password is incorrect"
            )
        
        # Hash new password
        from app import bcrypt
        new_hashed_password = bcrypt.generate_password_hash(data['new_password'])
        
        # Update password
        customer.password = new_hashed_password
        customer.save()
        
        return error_handler.success_response(
            message="Password changed successfully"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to change password",
            error_details=str(e)
        )


@app_views.route('/auth/api-keys', methods=['POST'], strict_slashes=False)
@require_admin()
def create_api_key():
    """
    Generate a new API key (admin only).
    
    Requires:
        Authorization header with valid admin API key
    
    Expected JSON payload:
        {
            "user_type": "admin" | "customer"
        }
    
    Returns:
        JSON response with new API key or error message
    """
    try:
        if not request.get_json():
            return error_handler.validation_error_response(
                message="Invalid request format",
                errors=["Request must contain JSON data"]
            )
        
        data = request.get_json()
        user_type = data.get('user_type', 'customer')
        
        if user_type not in ['admin', 'customer']:
            return error_handler.validation_error_response(
                message="Invalid user type",
                field_errors={'user_type': ["Must be 'admin' or 'customer'"]}
            )
        
        # Generate new API key
        api_key = generate_api_key(user_type)
        
        return error_handler.success_response(
            data={
                "api_key": api_key,
                "user_type": user_type,
                "usage": "Include in Authorization header as 'API-Key <key>'"
            },
            message="API key created successfully",
            status_code=201
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Failed to create API key",
            error_details=str(e)
        )


@app_views.route('/auth/logout', methods=['POST'], strict_slashes=False)
@require_auth()
def api_logout():
    """
    Logout endpoint (mainly for consistency, JWT tokens are stateless).
    
    Requires:
        Authorization header with valid Bearer token
    
    Returns:
        JSON response confirming logout
    
    Note:
        Since JWT tokens are stateless, this endpoint mainly serves as a 
        confirmation. In a production environment, you might want to 
        implement a token blacklist.
    """
    try:
        return error_handler.success_response(
            data={
                "note": "JWT tokens are stateless. For security, delete the token from client storage."
            },
            message="Logout successful"
        )
        
    except Exception as e:
        return error_handler.system_error_response(
            message="Logout failed",
            error_details=str(e)
        )