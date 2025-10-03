from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from modules import storage

app = Flask(__name__)
app.config['SECRET_KEY']='dsierjsdfksdofip'
db = storage

bcrypt = Bcrypt(app)