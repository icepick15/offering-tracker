from . import db
from flask_login import UserMixin
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash




class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    # Method to set the password with hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Method to check if the given password matches the hashed password
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # Update timestamp on record update
    def update_timestamp(self):
        self.updated_at = datetime.now(timezone.utc)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    donation_type = db.Column(db.String(10), nullable=False)  # 'tithe' or 'offering'
    timestamp = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    user = db.relationship('User', backref=db.backref('donations', lazy=True))
    stripe_charge_id = db.Column(db.String(100))
    stripe_status = db.Column(db.String(50))
    # email = db.Column(db.String(255), nullable=True)

