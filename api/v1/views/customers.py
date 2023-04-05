#!/usr/bin/python3
from modules.Customer.customer import Customer
from api.v1.views import app_views
from modules import storage
from flask import request, jsonify, make_response, abort, render_template


@app_views.route('/customers', methods=['GET'], strict_slashes=False)
def get_customers():
    """"""
    my_dict = storage.all(Customer)
    customers_list = []
    for customers in my_dict.values():
        customers_list.append(customers.to_dict())
    return jsonify(customers_list)

@app_views.route('/customers/<customer_id>', methods=['GET'], strict_slashes=False)
def get_customer(customer_id):
    """"""
    customer = storage.get(Customer, customer_id)

    return jsonify(customer.to_dict()) # type: ignore

@app_views.route('/customers/<customer_id>', methods=['PUT', 'DELETE'], strict_slashes=False) # type: ignore
def modify_customer(customer_id):
    """
        Update Customer data in the database.
    """
    customer = storage.get(Customer, customer_id)

    if not customer:
        abort(404)
    
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











