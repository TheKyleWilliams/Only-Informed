from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_apscheduler import APScheduler
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
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
migrate = Migrate(app, db)
bcrypt = Bcrypt(app) # provides password hashing utilites
login_manager = LoginManager(app) # manages user sessions
login_manager.login_view = 'login' # redirects unauthorized users to login page
login_manager.login_message_category = 'info' # flash message category



from app.news_fetcher import fetch_articles

# Runs fetch articles script every hour
@scheduler.task('interval', id='fetch_articles_job', hours=1)
def scheduled_fetch_articles():
    with app.app_context():
        fetch_articles()

# if not app.debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
#     scheduler.init_app(app)
#     scheduler.start()

from app import routes, models