#!/usr/bin/env python3
from modules.Products.product import Product
from modules import storage
from flask import jsonify, abort, make_response, request, url_for, Response
from werkzeug.utils import secure_filename
from app.api.v1.views import app_views
from flask import Response
import json


@app_views.route('/products', methods=['GET'], strict_slashes=False)
def get_products():
    products = storage.all(Product).values()

    product_list = []
    for product in products:
        product_dict = product.to_dict()
        product_dict['product_image'] = f'http://localhost:5000/product_img/{product.id}'
        product_list.append(product_dict)

    return jsonify(product_list)

@app_views.route('/products/<product_id>', methods=['GET'], strict_slashes=False)
def get_product(product_id):
    """"""
    product = storage.get(Product, product_id)
    return jsonify(product.to_dict()) # type: ignore

@app_views.route('/products/<product_id>', methods=['PUT', 'DELETE'], strict_slashes=False) # type: ignore
def modify_product(product_id):
    """"""
    product = storage.get(Product, product_id)

    if not request.get_json():
        abort(400, "Not a JSON")
    elif not product:
        abort(404)
    
    if request.method == 'PUT':
        ignore = ['id', 'created_at', 'updated_at']

        data = request.get_json()

        for key, value in data.items():
            if key not in ignore:
                setattr(product, key, value)
        storage.save()

        return make_response(jsonify(product.to_dict()), 200)

    if request.method == 'DELETE':
        storage.delete(product)
        storage.save()
        return make_response(jsonify({}), 200)

@app_views.route('/products', methods=['POST'], strict_slashes=False) # type: ignore
def add_product():
    """
        Create new Product instnace, and add it to the database
    """
    # if not request.get_json():
    #     abort(400, "NOT JSON")
    print(request.files)
    data = request.form.to_dict()
    img = request.files.get('product_image')
    img_name = secure_filename(img.filename) #type: ignore
    data['product_image'] = img.read() #type: ignore
    # print(data)
    product_instance = Product(**data)
    product_instance.save()

    return make_response(jsonify(product_instance.to_dict()), 201)


# /product/reivews
