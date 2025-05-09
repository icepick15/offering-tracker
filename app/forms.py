from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, DecimalField, SelectField 

from wtforms.validators import DataRequired, NumberRange, Email, Length, ValidationError, EqualTo

from .models import User
from wtforms import DateTimeField


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(), Length(min=3, max=150)
    ])
    email = StringField('Email', validators=[
        DataRequired(), Email(message="Invalid email address.")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(), Length(min=6)
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(), EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already taken.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(message="Invalid email address.")])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("Email not found. Please check your email address.")
    
class DonationForm(FlaskForm):
    amount = DecimalField('Amount (₦)', validators=[DataRequired(), NumberRange(min=1, message="Donation amount must be at least 1")], render_kw={'placeholder': 'Enter donation amount'})
    donation_type = SelectField('Donation Type', choices=[('tithe', 'Tithe'), ('offering', 'Offering')], validators=[DataRequired()])
    timestamp = DateTimeField('Timestamp', format='%Y-%m-%d %H:%M:%S')
    submit = SubmitField('Donate')