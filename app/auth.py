#!/usr/bin/env python3
from flask import render_template, request, url_for, flash, redirect, session
from wtforms import Form, StringField, TextAreaField, PasswordField,SubmitField,validators, ValidationError
from flask_wtf.file import FileRequired, FileAllowed, FileField
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from modules.Customer.customer import Customer
from app import app, bcrypt
from modules import storage

login_manager = LoginManager()
login_manager.init_app(app)

# form to add customer to database
class CustomerSignupForm(FlaskForm):
    first_name = StringField('first_name: ')
    last_name = StringField('last_name: ', [validators.DataRequired()])
    email = StringField('Email: ', [validators.Email(), validators.DataRequired()])
    password = PasswordField('Password: ', [validators.DataRequired(), validators.EqualTo('confirm', message=' Both password must match! ')])
    confirm = PasswordField('Repeat Password: ', [validators.DataRequired()])
    address = StringField('Address: ', [validators.DataRequired()])
    profile = FileField('Profile', validators=[FileAllowed(['jpg','png','jpeg','gif'], 'Image only please')])
    submit = SubmitField('Register')

    def validate_email(self, email):
        customers = storage.all(Customer).values()
        for customer in customers:
            if customer.email == email.data:
                raise ValidationError("This email address is already in use!")

# login form
class CustomerLoginForm(FlaskForm):
    email = StringField('Email: ', [validators.Email(), validators.DataRequired()])
    password = PasswordField('Password: ', [validators.DataRequired()])


@login_manager.user_loader
def load_user(user_id):
    return storage.get(Customer, user_id)

@app.route('/login', methods=['POST']) # type: ignore
def login():
    form = CustomerLoginForm()
    if request.method == 'POST':
        user_pass = form.password.data
        user_email= form.email.data

        users_list = storage.all(Customer).values()

        for user in users_list:
            if user.email == user_email and bcrypt.check_password_hash(user.password, user_pass):
                login_user(user)
                load_user(user.id)
                return redirect(url_for('shop'))

        flash(f'Wrong Email or Password', 'error')
        return redirect(url_for('login'))
        

@app.route('/login', methods=['GET'], strict_slashes=False)
def get_login():
    form = CustomerLoginForm()
    return render_template('admin/login.html', form=form)
    

@app.route('/home') # type: ignore
def test():
    return render_template('home.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = CustomerSignupForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        user = Customer(first_name=form.first_name.data,last_name=form.last_name.data, email=form.email.data, address=form.address.data,
                    password=hash_password)
        storage.new(user)
        flash(f'welcome {form.first_name.data} Thanks for registering','success')
        storage.save()
        return redirect(url_for('login'))
    return render_template('admin/signup.html',title='Register user', form=form)

@app.route('/home')
def home():
    return render_template('home.html')
