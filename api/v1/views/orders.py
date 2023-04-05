#!/usr/bin/python3
from modules.Order.order import Order
from modules import storage
from api.v1.views import app_views
from flask import jsonify, abort, make_response, request


@app_views.route('/orders', methods=['GET'], strict_slashes=False) # type: ignore
def get_orders():
    orders = storage.all(Order).values()

    orders_list = []

    for order in orders:
        orders_list.append(order)
    return jsonify(orders_list)

@app_views.route('/orders/<order_id>', methods=['GET', 'DELETE'], strict_slashes=False) # type: ignore
def get_order(order_id):
    order = storage.get(Order, order_id)
    
    if request.method == 'DELETE':
        if not request.get_json():
            abort(400, "NOT JSON")
        elif not order:
            abort(404)
        
        storage.delete(order)
        storage.save()
        
        return make_response(jsonify({}), 200)

    return jsonify(order.to_dict()) # type: ignore

# @app_views.route('/orders/<order_id>/products', methods=['GET'], strict_slashes=False) # type: ignore
# def get_order_products(order_id):
#     order = storage.get(Order, order_id)

