#!/usr/bin/env python3
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_wtf .csrf import CSRFProtect


app = Flask(__name__)
app.config['SECRET_KEY']='dsierjsdfksdofip'

app.secret_key = "lskdjflkdsjf_sldkfjlksdjf"

csrf = CSRFProtect(app)

bcrypt = Bcrypt(app)


from app.auth import *
from app.layout import *
from app.app import *
