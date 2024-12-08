from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_apscheduler import APScheduler
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
import logging
from logging.handlers import RotatingFileHandler
import os  # Import os for accessing environment variables
from dotenv import load_dotenv  # Import load_dotenv

# Load environment variables from .env file
load_dotenv() 

# Initialize Flask app
app = Flask(__name__)

# configure secret key and database URI from environment variables
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # Access SECRET_KEY from environment
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')  # Access DB URI
app.config['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
app.config['WTF_CSRF_HEADERS'] = ['X-CSRFToken', 'X-CSRF-Token']

# Initialize extensions
db = SQLAlchemy(app)
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
migrate = Migrate(app, db)
bcrypt = Bcrypt(app) # provides password hashing utilites
login_manager = LoginManager(app) # manages user sessions
login_manager.login_view = 'login' # redirects unauthorized users to login page
login_manager.login_message_category = 'info' # flash message category
csrf = CSRFProtect(app)


from app.news_fetcher import fetch_articles

# Runs fetch articles script every hour
@scheduler.task('interval', id='fetch_articles_job', hours=1)
def scheduled_fetch_articles():
    with app.app_context():
        fetch_articles()

# if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
#     scheduler.init_app(app)
#     scheduler.start()

from app.helpers import user_has_passed_quiz
@app.context_processor
def utility_processor():
    return dict(user_has_passed_quiz=user_has_passed_quiz)

def create_app():
    app = Flask(__name__)

    # Logging configuration
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('App startup')

    return app

from app import routes, models

