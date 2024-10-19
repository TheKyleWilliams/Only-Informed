from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
import os  # Import os for accessing environment variables
from dotenv import load_dotenv  # Import load_dotenv

# Load environment variables from .env file
load_dotenv() 

# Initialize Flask app
app = Flask(__name__)

# configure secret key and database URI from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Access SECRET_KEY from environment
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')  # Access DB URI

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bcrypt = Bcrypt(app) # provides password hashing utilites
login_manager = LoginManager(app) # manages user sessions
login_manager.login_view = 'login' # redirects unauthorized users to login page
login_manager.login_message_category = 'info'

from app import routes, models