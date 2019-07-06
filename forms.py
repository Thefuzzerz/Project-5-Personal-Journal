"""
Imported into main app file. This file contains all form classes
for the templates to request information.
"""

from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, ValidationError, EqualTo
from models import User


def username_exists(form, field):
    """ Function to check if user already exists. """
    if User.select().where(User.username == field.data).exists():
        raise ValidationError('User Exists')


class LoginForm(Form):
    """ Form for user to verify credentials and log in. """
    username = StringField(
        'Username',
        validators=[DataRequired()]
        )
    password = PasswordField(
        'Password',
        validators=[DataRequired()]
        )


class RegisterForm(Form):
    """ Form for user to sign up. """
    username = StringField(
        'Username',
        validators=[DataRequired(), username_exists]
        )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            EqualTo('password2', message='Passwords must match')
            ])
    password2 = PasswordField(
        'Confirm Password',
        validators=[DataRequired()]
        )
