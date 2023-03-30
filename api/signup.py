from flask import render_template, request, url_for, flash, redirect, session
from wtforms import Form, StringField, TextAreaField, PasswordField,SubmitField,validators, ValidationError
from flask_wtf.file import FileRequired,FileAllowed, FileField
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from modules.Customer.customer import Customer
from . import app, db, bcrypt

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

    # def validate_email(self, email):
    #     if Customer.query.filter_by(email=email.data).first():
    #         raise ValidationError("This email address is already in use!")

# login form
class CustomerLoginFrom(FlaskForm):
    email = StringField('Email: ', [validators.Email(), validators.DataRequired()])
    password = PasswordField('Password: ', [validators.DataRequired()])

@app.route('/login', methods=['GET','POST'])
def login():
    form = CustomerLoginFrom()
    if request.method == 'POST' and form.validate_on_submit():
        admin_email = ["motaz@admin.com","adel@admin.com"]
        admin_pwrd = "12345"
        if form.email.data in admin_email and form.password.data == admin_pwrd:
            return render_template('admin/dashboard.html', title='admin dashboard')
        user = Customer.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['email'] = form.email.data
            flash(f'welcome {form.email.data} you are logedin now','success')
            return redirect(url_for('home'))
        else:
            flash(f'Wrong email and password', 'error')
            return redirect(url_for('login'))
    return render_template('admin/login.html',title='Login page',form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = CustomerSignupForm()
    if form.validate_on_submit():
        hash_password = bcrypt.generate_password_hash(form.password.data)
        user = Customer(first_name=form.first_name.data,last_name=form.last_name.data, email=form.email.data, address=form.address.data,
                    password=hash_password)
        db.new(user)
        flash(f'welcome {form.first_name.data} Thanks for registering','success')
        db.save()
        return redirect(url_for('home'))
    return render_template('admin/signup.html',title='Register user', form=form)

@app.route('/home')
def home():
    return render_template('home.html')