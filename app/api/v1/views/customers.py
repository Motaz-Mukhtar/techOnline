#!/usr/bin/env python3
from modules.Customer.customer import Customer
from app.api.v1.views import app_views
from app.layout import img_url
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

    if request.method == 'PUT':
        ignore = ['id', 'created_at', 'updated_at']
        data = request.form.to_dict()
        print(data)

        for key, value in data.items():
            if key not in ignore:
                setattr(customer, key, value)

        customer.save()
        storage.save()
        return make_response(jsonify(customer.to_dict()), 200)

    if request.method == 'DELETE':
        storage.delete(customer)
        storage.save()

        return make_response(jsonify({}), 200)

@app_views.route('/customers', methods=['POST'], strict_slashes=False)
def add_customer():
    """
        Add new Customer instance to the database.
    """
    if request.get_json():
        abort(400, description="Not a JSON")

    if 'email' not in request.get_json():
        abort(400, description="Missing Email")
    if 'password' not in request.get_json():
        abort(400, description="Missing Password")

    data = request.get_json()

    customer = Customer(**data)

    customer.save()

    return make_response(jsonify(customer.to_dict(), 201))

@app_views.route('/customers/<customer_id>/products', methods=['GET'], strict_slashes=False)
def get_customer_prodcuts(customer_id):
    """
        Retrive customer data by customer id.
    """
    customer = storage.get(Customer, customer_id)
    products_list = []

    if not customer:
        abort(404)
    
    for product in customer.products:
        products_list.append(product)
    
    return jsonify(products_list)
