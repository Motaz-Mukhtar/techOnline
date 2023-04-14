#!/usr/bin/env python3
from modules.Customer.customer import Customer
from modules.Products.product import Product
from flask import render_template, request
from flask_login import login_required
from app import app
from app.auth import current_user
from modules import storage
import requests
import json
from requests import HTTPError
from flask import Response


def img_url(product_id):
    return f'http://127.0.0.1:5000/product_img/{product_id}'


@app.route('/shop', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def shop():

    if request.method == 'POST':
        product_name = request.form.get('product_name')
        product = None
        customers_list = storage.all(Customer).values()

        for customer in customers_list:
            if product_name == customer.first_name: 
                product = customer
        return render_template('layout.html', name=product)

    return render_template('layout.html')


@app.route('/shop/product_form', methods=['GET', 'POST'], strict_slashes=False)
@login_required
def product_form():
    
    if request.method == 'POST':
        pass
    return render_template('product_form.html', user=current_user.to_dict()) # type: ignore



@app.route('/profile', strict_slashes=False)
@login_required
def customer_profile():
    print(current_user)
    return render_template('customer_profile.html', user=current_user) # type: ignore



@app.route('/test', methods=['GET'], strict_slashes=False)
@login_required
def tdddest():
    data = []
    try:
        products_list = requests.get('http://127.0.0.1:5001/api/v1/products')
        for i in json.loads(products_list.text):
            data.append(i)
    except HTTPError:
        products_list = []
    return render_template('test.html', data=data)


@app.route('/product_img/<id>', methods=['GET'], strict_slashes=False) #type: ignore
def get_img(id):
    imges = storage.all(Product).values()
    storage.reload()
    for img in imges:
        if id == img.id:
            return Response(img.product_image, mimetype='Text')

