#!/usr/bin/env python3
from modules.Review.review import Review
from modules import storage
from app.api.v1.views import app_views
from flask import json, abort, make_response, request, jsonify


@app_views.route('/reviews', methods=['GET'], strict_slashes=False)
def get_reviews():
    
    reviews_list = []

    for review in storage.all(Review).values():
        reviews_list.append(review.to_dict())

    return jsonify(reviews_list)

@app_views.route('/reviews/<review_id>', methods=['GET'], strict_slashes=False)
def get_review(review_id):
    review = storage.get(Review, review_id)
    return jsonify(review)

@app_views.route('/reviews/<review_id>', methods=['DELETE'], strict_slashes=False)
def del_review(review_id):
    """
        Delete Reivew instance form the database
    """
    review = storage.get(Review, review_id)

    if not review:
        abort(404)

    storage.delete(review)
    storage.save()

    return make_response(jsonify({}), 200)

@app_views.route('/reviews', methods=['POST'], strict_slashes=False)
def new_review():
    """
        Create new review instance
    """
    if not request.get_json():
        abort(400, description="Not a JSON")
    elif 'product_id' not in request.get_json():
        abort(400, 'Product id missing')
    elif 'customer_id' not in request.get_json():
        abort(400, 'Cutomer id Missing')

    data = request.get_json()
    instnace = Review(**data)
    instnace.save()

    return make_response(jsonify(instnace.to_dict()), 201) 
