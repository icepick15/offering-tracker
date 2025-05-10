from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import timedelta
from dotenv import load_dotenv
import os
import stripe

# Load environment variables before anything else
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

# Config class
class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://{os.getenv('user')}:{os.getenv('password')}@{os.getenv('host')}:{os.getenv('port')}/{os.getenv('dbname')}"
    )
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
    DEBUG = False
    ENV = 'production'
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    from .models import User, Donation

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from .main import main_bp
    from .auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # Create tables only in development mode (don't create in production)
    if app.config.get("ENV") == "development":
        with app.app_context():
            try:
                db.create_all()  # This will create the tables if they don't already exist
            except Exception as e:
                print("Error creating tables:", e)

    return app
