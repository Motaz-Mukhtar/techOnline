#!/usr/bin/env python3
""" Blueprint for API """
from flask import Blueprint

app_views = Blueprint('app_views', __name__, url_prefix='/api/v1/')

from app.api.v1.views.products import *
from app.api.v1.views.carts import *
from app.api.v1.views.customers import *
from app.api.v1.views.reviews import *
from app.api.v1.views.orders import *
