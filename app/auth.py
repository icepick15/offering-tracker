from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db
from .forms import LoginForm, RegistrationForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask import request



auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Registration route
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth/register.html", form=form)
# Login route
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            flash('Login successful', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password', 'danger')  
    else:
        if request.method == 'POST':
            flash('Please fill in all fields correctly', 'warning')

    return render_template('auth/login.html', title='Login', form=form)

# Logout route
@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out!', 'info')
    return redirect(url_for('main.index'))
