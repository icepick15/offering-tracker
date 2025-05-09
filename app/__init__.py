from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from datetime import timedelta
from dotenv import load_dotenv
import os
import stripe

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    # Load environment variables
    load_dotenv()

    app = Flask(__name__)

    # App configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or 'dev-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DB_URI') or 'sqlite:///app.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.permanent_session_lifetime = timedelta(days=7)

     # Load Stripe keys from .env
    # app.config['STRIPE_PUBLIC_KEY'] = os.getenv('STRIPE_PUBLIC_KEY')
    app.config['STRIPE_SECRET_KEY'] = os.getenv('STRIPE_SECRET_KEY')


    # Set Stripe API key
    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Flask-Login settings
    login_manager.login_view = 'auth.login'  # redirect view for @login_required
    login_manager.login_message_category = 'info'

    # Register models (make sure to import models here)
    from .models import User, Donation  # Import all models, including Donation
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register Blueprints
    from .main import main_bp
    from .auth import auth_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)

    # Create tables (only call once or manually in shell)
    with app.app_context():
        # Create tables only on the first run
        try:
            db.create_all()  # This will create the tables if they don't already exist
        except Exception as e:
            print("Error creating tables:", e)

    return app
