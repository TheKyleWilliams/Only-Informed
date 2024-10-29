from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

# forms.py: deals with the logic for defining and validating registration
# and login forms

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    # Validation Methods
    def validate_username(self, username):
        # checks if username already exists
        user = User.query.filter_by(username = username.data).first()
        if user:
            raise ValidationError('Username already exists.')
        
    def validate_email(self, email):
        # checks if email already exists
        user = User.query.filter_by(email = email.data).first()
        if user:
            raise ValidationError('Email already registered')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')