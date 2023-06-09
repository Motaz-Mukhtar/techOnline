#!/usr/bin/python3
""" Blueprint for API """
from flask import Blueprint

app_views = Blueprint('app_views', __name__, url_prefix='/api/v1/')

from api.v1.views.products import *
from api.v1.views.carts import *
from api.v1.views.customers import *
from api.v1.views.reviews import *
from api.v1.views.orders import *