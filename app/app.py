#!/usr/bin/env python3
from modules import storage
from app import app
from flask import redirect, url_for, make_response, jsonify

@app.teardown_appcontext
def close_db(error):
    """ Close session """
    storage.close()


@app.errorhandler(401)
def unauthorized(error):
    """ 401 Error

    responses:
        401:
            description: redirect to the login page (unauthorized)
    """
    return redirect(url_for('login'))

@app.errorhandler(404) # type: ignore
def not_found(error):
    """ 404 Error
    ---
    responses:
      404:
        description: a resource was not found
    """
    return make_response(jsonify({'error': "Page Not Found"}), 404)
