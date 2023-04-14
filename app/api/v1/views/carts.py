#!/usr/bin/env python3
from modules.Cart.cart import Cart
from modules import storage
from flask import jsonify, make_response, abort, request
from app.api.v1.views import app_views


@app_views.route('/carts', methods=['GET'], strict_slashes=False) # type: ignore
def get_carts():
    carts = storage.all(Cart).values()

    carts_list = []

    for cart in carts:
        carts_list.append(cart.to_dict())
    
    return jsonify(carts_list)

@app_views.route('/carts/<cart_id>', methods=['GET', 'PUT', 'DELETE'], strict_slashes=False) # type: ignore
def cart(cart_id):
    cart = storage.get(Cart, cart_id)

    if not cart:
        return make_response(jsonify({"error": "customer cart is empty"}), 404)

    if request.method == 'GET':
        return jsonify(cart.to_dict())

    if request.method == 'PUT' or request.method == 'DELETE':
        if not request.get_json():
            abort(400, "Not a JSON")

        if request.method == 'PUT':
            ignore = ['id', 'created_at', 'updated_at']
            data = request.get_json()

            for key, value in data.items():
                if key not in ignore:
                    setattr(cart, key, value)
            storage.save()
            return make_response(jsonify(cart.to_dict()), 200)

        elif request.method == 'DELETE':
            storage.delete(cart)
            storage.save()
            return make_response(jsonify({}), 200)
