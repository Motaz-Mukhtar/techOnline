#!/usr/bin/env python3
from flask import Flask, make_response, jsonify, abort
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from modules import storage


app = Flask(__name__)
app.config['SECRET_KEY']='dsierjsdfksdofip'

bcrypt = Bcrypt(app)


from app.auth import *
from app.layout import *
from app.app import *
