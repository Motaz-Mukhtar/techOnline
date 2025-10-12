"""API Blueprint

This module contains API-related endpoints including:
- JWT token retrieval endpoint
- Other internal API functionality
"""

from flask import Blueprint, jsonify, session
from flask_login import login_required

# Create API blueprint
api_bp = Blueprint('api', __name__)

@api_bp.route('/token', methods=['GET'])
@login_required
def get_jwt_token():
    """
    Retrieve the JWT token from the session.
    
    This endpoint allows frontend JavaScript to access the stored JWT token
    for making authenticated API requests.
    
    Returns:
        JSON response containing the access token or error message
    """
    access_token = session.get('access_token')
    if access_token:
        return jsonify({
            'success': True,
            'access_token': access_token
        }), 200
    else:
        return jsonify({
            'success': False,
            'error': 'No access token found'
        }), 404