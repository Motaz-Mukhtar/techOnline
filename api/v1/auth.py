#!/usr/bin/env python3
"""
API Authentication module for TechOnline e-commerce platform.

This module provides JWT-based authentication for API endpoints including:
- JWT token generation and validation
- API key authentication
- Authentication decorators for API endpoints
- User authentication and authorization
"""

import jwt
import datetime
from functools import wraps
from flask import request, jsonify, current_app, make_response
from modules.Customer.customer import Customer
from modules import storage
from flask_bcrypt import check_password_hash
import secrets
import hashlib

# Secret key for JWT encoding (should be in environment variables in production)
JWT_SECRET_KEY = 'your-secret-key-change-in-production'
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

# API Keys storage (in production, this should be in a database)
API_KEYS = {
    'admin_key_123': {'user_type': 'admin', 'permissions': ['read', 'write', 'delete']},
    'customer_key_456': {'user_type': 'customer', 'permissions': ['read', 'write']}
}

class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    pass

class AuthorizationError(Exception):
    """Custom exception for authorization errors."""
    pass

def generate_jwt_token(customer_id, email, expires_in_hours=JWT_EXPIRATION_HOURS):
    """
    Generate a JWT token for a customer.
    
    Args:
        customer_id (str): The customer's ID
        email (str): The customer's email
        expires_in_hours (int): Token expiration time in hours
        
    Returns:
        str: JWT token
    """
    try:
        payload = {
            'customer_id': customer_id,
            'email': email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=expires_in_hours),
            'iat': datetime.datetime.utcnow(),
            'type': 'access_token'
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
        
    except Exception as e:
        raise AuthenticationError(f"Failed to generate token: {str(e)}")

def verify_jwt_token(token):
    """
    Verify and decode a JWT token.
    
    Args:
        token (str): JWT token to verify
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token")
    except Exception as e:
        raise AuthenticationError(f"Token verification failed: {str(e)}")

def generate_api_key(user_type='customer'):
    """
    Generate a new API key.
    
    Args:
        user_type (str): Type of user ('admin' or 'customer')
        
    Returns:
        str: Generated API key
    """
    # Generate a secure random key
    random_bytes = secrets.token_bytes(32)
    api_key = hashlib.sha256(random_bytes).hexdigest()[:32]
    
    # Set permissions based on user type
    permissions = ['read', 'write', 'delete'] if user_type == 'admin' else ['read', 'write']
    
    # Store the key (in production, save to database)
    API_KEYS[api_key] = {
        'user_type': user_type,
        'permissions': permissions,
        'created_at': datetime.datetime.utcnow().isoformat()
    }
    
    return api_key

def verify_api_key(api_key):
    """
    Verify an API key.
    
    Args:
        api_key (str): API key to verify
        
    Returns:
        dict: API key information
        
    Raises:
        AuthenticationError: If API key is invalid
    """
    if api_key not in API_KEYS:
        raise AuthenticationError("Invalid API key")
    
    return API_KEYS[api_key]

def get_auth_token_from_header():
    """
    Extract authentication token from request headers.
    
    Returns:
        tuple: (token_type, token) or (None, None) if no token found
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None, None
    
    try:
        # Support both "Bearer <token>" and "API-Key <key>" formats
        parts = auth_header.split(' ', 1)
        if len(parts) != 2:
            return None, None
        
        token_type, token = parts
        return token_type.lower(), token
        
    except Exception:
        return None, None

def authenticate_request():
    """
    Authenticate the current request using JWT or API key.
    
    Returns:
        dict: Authentication information containing user details
        
    Raises:
        AuthenticationError: If authentication fails
    """
    token_type, token = get_auth_token_from_header()
    
    if not token_type or not token:
        raise AuthenticationError("Missing authentication token")
    
    if token_type == 'bearer':
        # JWT token authentication
        payload = verify_jwt_token(token)
        customer = storage.get(Customer, payload['customer_id'])
        
        if not customer:
            raise AuthenticationError("Customer not found")
        
        return {
            'type': 'jwt',
            'customer': customer,
            'customer_id': customer.id,
            'email': customer.email,
            'permissions': ['read', 'write']  # Default customer permissions
        }
    
    elif token_type == 'api-key':
        # API key authentication
        key_info = verify_api_key(token)
        
        return {
            'type': 'api_key',
            'user_type': key_info['user_type'],
            'permissions': key_info['permissions'],
            'api_key': token
        }
    
    else:
        raise AuthenticationError(f"Unsupported authentication type: {token_type}")

def require_auth(permissions=None):
    """
    Decorator to require authentication for API endpoints.
    
    Args:
        permissions (list): List of required permissions (optional)
        
    Returns:
        function: Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Authenticate the request
                auth_info = authenticate_request()
                
                # Check permissions if specified
                if permissions:
                    user_permissions = auth_info.get('permissions', [])
                    for required_permission in permissions:
                        if required_permission not in user_permissions:
                            return make_response(
                                jsonify({"error": f"Insufficient permissions. Required: {required_permission}"}),
                                403
                            )
                
                # Add auth info to request context
                request.auth_info = auth_info
                
                return f(*args, **kwargs)
                
            except AuthenticationError as e:
                return make_response(
                    jsonify({"error": f"Authentication failed: {str(e)}"}),
                    401
                )
            except AuthorizationError as e:
                return make_response(
                    jsonify({"error": f"Authorization failed: {str(e)}"}),
                    403
                )
            except Exception as e:
                return make_response(
                    jsonify({"error": f"Authentication error: {str(e)}"}),
                    500
                )
        
        return decorated_function
    return decorator

def require_admin():
    """
    Decorator to require admin authentication for API endpoints.
    
    Returns:
        function: Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                auth_info = authenticate_request()
                
                # Check if user is admin
                if auth_info.get('type') == 'api_key' and auth_info.get('user_type') == 'admin':
                    request.auth_info = auth_info
                    return f(*args, **kwargs)
                else:
                    return make_response(
                        jsonify({"error": "Admin access required"}),
                        403
                    )
                    
            except AuthenticationError as e:
                return make_response(
                    jsonify({"error": f"Authentication failed: {str(e)}"}),
                    401
                )
            except Exception as e:
                return make_response(
                    jsonify({"error": f"Authentication error: {str(e)}"}),
                    500
                )
        
        return decorated_function
    return decorator

def optional_auth():
    """
    Decorator for optional authentication (doesn't fail if no auth provided).
    
    Returns:
        function: Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                auth_info = authenticate_request()
                request.auth_info = auth_info
            except AuthenticationError:
                # Authentication failed, but that's okay for optional auth
                request.auth_info = None
            except Exception:
                # Any other error, set auth_info to None
                request.auth_info = None
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_current_user():
    """
    Get the current authenticated user from request context.
    
    Returns:
        Customer or None: Current authenticated customer
    """
    auth_info = getattr(request, 'auth_info', None)
    if auth_info and auth_info.get('type') == 'jwt':
        return auth_info.get('customer')
    return None

def get_current_user_id():
    """
    Get the current authenticated user ID from request context.
    
    Returns:
        str or None: Current authenticated customer ID
    """
    auth_info = getattr(request, 'auth_info', None)
    if auth_info:
        return auth_info.get('customer_id')
    return None

def is_admin():
    """
    Check if the current user is an admin.
    
    Returns:
        bool: True if current user is admin, False otherwise
    """
    auth_info = getattr(request, 'auth_info', None)
    if auth_info and auth_info.get('type') == 'api_key':
        return auth_info.get('user_type') == 'admin'
    return False

def authenticate_customer(email, password):
    """
    Authenticate a customer with email and password.
    
    Args:
        email (str): Customer email
        password (str): Customer password
        
    Returns:
        Customer: Authenticated customer object
        
    Raises:
        AuthenticationError: If authentication fails
    """
    try:
        # Find customer by email
        customers = storage.all(Customer).values()
        customer = None
        
        for c in customers:
            if c.email == email:
                customer = c
                break
        
        if not customer:
            raise AuthenticationError("Invalid email or password")
        
        # Verify password
        if not check_password_hash(customer.password, password):
            raise AuthenticationError("Invalid email or password")
        
        return customer
        
    except Exception as e:
        if isinstance(e, AuthenticationError):
            raise
        raise AuthenticationError(f"Authentication failed: {str(e)}")