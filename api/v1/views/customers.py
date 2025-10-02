#!/usr/bin/python3
from modules.Customer.customer import Customer
from api.v1.views import app_views
from modules import storage
from api.v1.auth import require_auth, require_admin, optional_auth, get_current_user_id, is_admin
from flask import request, jsonify, make_response, abort, render_template


@app_views.route('/customers', methods=['GET'], strict_slashes=False)
@require_admin()
def get_customers():
    """Get all customers (Admin only)"""
    my_dict = storage.all(Customer)
    customers_list = []
    for customers in my_dict.values():
        customers_list.append(customers.to_dict())
    return jsonify(customers_list)

@app_views.route('/customers/<customer_id>', methods=['GET'], strict_slashes=False)
@require_auth(['read'])
def get_customer(customer_id):
    """Get a specific customer"""
    customer = storage.get(Customer, customer_id)
    if not customer:
        abort(404)
    
    # Check if user can access this customer's data
    current_user_id = get_current_user_id()
    if not is_admin() and customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only access your own profile"}), 403)

    return jsonify(customer.to_dict()) # type: ignore

@app_views.route('/customers/<customer_id>', methods=['PUT', 'DELETE'], strict_slashes=False) # type: ignore
@require_auth(['read'])
def modify_customer(customer_id):
    """
        Update Customer data in the database.
    """
    customer = storage.get(Customer, customer_id)

    if not customer:
        abort(404)
    
    # Check if user can access this customer's data
    current_user_id = get_current_user_id()
    if not is_admin() and customer_id != current_user_id:
        return make_response(jsonify({"error": "Access denied: You can only access your own profile"}), 403)
    
    if not request.get_json():
        abort(400, description="Not a JSON")


    if request.method == 'PUT':
        ignore = ['id', 'created_at', 'updated_at']
        data = request.get_json()

        for key, value in data.items():
            if key not in ignore:
                setattr(customer, key, value)
        storage.save()
        return make_response(jsonify(customer.to_dict()), 200)

    if request.method == 'DELETE':
        storage.delete(customer)
        storage.save()

        return make_response(jsonify({}), 200)

# /customer/products











