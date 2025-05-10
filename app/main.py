from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, Response, jsonify
from flask_login import login_required, current_user
from app.forms import DonationForm
from app.models import Donation
from io import BytesIO
from . import db
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from flask_paginate import Pagination
from datetime import datetime, timezone
import stripe

import psycopg2
from dotenv import load_dotenv
import os

## Load environment variables from .env file
load_dotenv()

def connect_to_db():
    try:
        # Establish a connection to the PostgreSQL database
        conn = psycopg2.connect(
            user=os.getenv('user'),
            password=os.getenv('password'),
            database=os.getenv('dbname'),
            host=os.getenv('host'),
            port=os.getenv('port')
        )

        # Create a cursor object to interact with the database
        cursor = conn.cursor()

        # Execute a simple query to check connection
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("✅ Connection successful!")
        print("🕒 Current time:", result)

        # Close the cursor and connection
        cursor.close()
        conn.close()
        print("🔌 Connection closed.")

    except Exception as e:
        print("Error: Unable to connect to the database")
        print(e)

# Just call the DB function normally in the application lifecycle
connect_to_db()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
endpoint_secret = os.getenv("STRIPE_WEBHOOK_SECRET")


main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')  

@main_bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = DonationForm()

    # When the donation form is submitted
    if form.validate_on_submit():
        donation = Donation(
            user_id=current_user.id,
            amount=form.amount.data,
            donation_type=form.donation_type.data,
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(donation)
        db.session.commit()

        flash('Your donation was successfully recorded!', 'success')
        return redirect(url_for('main.dashboard'))
    
     # Get donation status from query string for modal popup
    donation_status = request.args.get('donation_status')
    donation_amount = request.args.get('donation_amount')

    # Get all donations for current user (used for stats)
    all_donations = Donation.query.filter_by(user_id=current_user.id).all()

    # Normalize donation_type to lowercase for consistent stats
    total_donated = sum(d.amount for d in all_donations)
    total_tithe = sum(d.amount for d in all_donations if d.donation_type.strip().lower() == 'tithe')
    total_offering = sum(d.amount for d in all_donations if d.donation_type.strip().lower() == 'offering')

    # Paginate for current page
    page = request.args.get('page', 1, type=int)
    donations_query = Donation.query.filter_by(user_id=current_user.id).order_by(Donation.timestamp.desc())
    donations_paginated = db.paginate(donations_query, page=page, per_page=10, error_out=False)

    return render_template('dashboard.html',
                           form=form,
                           donations=donations_paginated.items,
                           pagination=donations_paginated,
                           total_donated=total_donated,
                           total_tithe=total_tithe,
                           total_offering=total_offering,
                           breakdown={
                               'Tithe': total_tithe,
                               'Offering': total_offering
                           },
                           donation_status=donation_status,
                           donation_amount=donation_amount
                           )



@main_bp.route('/donate', methods=['GET', 'POST'])
@login_required  # Ensure the user is logged in to donate
def donate():
    form = DonationForm()

    if form.validate_on_submit():
        # Retrieve form data
        amount = form.amount.data
        donation_type = form.donation_type.data

        # Here you would typically save the donation to the database
        # Example: db.session.add(Donation(user_id=current_user.id, amount=amount, donation_type=donation_type))
        # db.session.commit()

        flash(f"Thank you for your {donation_type} donation of ${amount}!", 'success')
        return redirect(url_for('main.dashboard'))  # Redirect to the dashboard or a thank you page

    return render_template('donate.html', form=form)


@main_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    amount = int(float(request.form['amount']) * 100)  # Convert Naira to kobo
    donation_type = request.form['donation_type']

    if not amount or not donation_type:
        flash("Invalid donation details", "error")
        return redirect(url_for('main.dashboard'))

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'ngn',
                    'product_data': {
                        'name': f'{donation_type} by {current_user.email}',
                    },
                    'unit_amount': amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('main.payment_success', _external=True) + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=url_for('main.dashboard', _external=True),
            metadata={
                "user_id": current_user.id,
                "donation_type": donation_type
            }
        )
        return redirect(checkout_session.url)
    except Exception as e:
        print("Stripe error:", e)
        flash("Error creating Stripe session", "error")
        return redirect(url_for('main.dashboard'))
    
@main_bp.route('/payment-success')
@login_required
def payment_success():
    session_id = request.args.get('session_id')
    if not session_id:
        flash("Missing session ID", "error")
        return redirect(url_for('main.dashboard'))

    session = stripe.checkout.Session.retrieve(session_id)
    # email = session['customer_details']['email']
    amount = session['amount_total'] / 100  # Convert back from kobo
    donation_type = session['metadata'].get('donation_type')
    user_id = session['metadata'].get('user_id')
    charge_id = session.get('payment_intent')
    status = session.get('payment_status')

    # Record in DB
    donation = Donation(
        user_id=user_id,
        amount=amount,
        donation_type=donation_type,
        stripe_charge_id=charge_id,
        stripe_status=status,
        timestamp=datetime.now(timezone.utc)
    )
    db.session.add(donation)
    db.session.commit()

    flash(f"Donation of ₦{amount} was successful! Status: {status}", "success")

    # Redirect to the dashboard with donation details to display the modal
    return redirect(url_for('main.dashboard', donation_status=status, donation_amount=amount))

@main_bp.route('/payment-cancel')
@login_required
def payment_cancel():
    # Redirect back to dashboard with cancellation flag
    return redirect(url_for('main.dashboard', donation_status='cancelled'))

@main_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('stripe-signature')
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError as e:
        print('⚠️ Invalid payload')
        return jsonify(success=False), 400
    except stripe.error.SignatureVerificationError as e:
        print('⚠️ Invalid signature')
        return jsonify(success=False), 400

    # ✅ Handle checkout.session.completed
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        user_id = session['metadata'].get('user_id')
        donation_type = session['metadata'].get('donation_type')
        amount = session['amount_total'] / 100
        charge_id = session.get('payment_intent')
        status = session.get('payment_status')
        # customer_email = session.get('customer_details', {}).get('email')

        # Prevent duplicates
        existing = Donation.query.filter_by(stripe_charge_id=charge_id).first()
        if not existing:
            donation = Donation(
                user_id=user_id,
                amount=amount,
                donation_type=donation_type,
                stripe_charge_id=charge_id,
                stripe_status=status,
                timestamp=datetime.now(timezone.utc),
                # email=customer_email
            )
            db.session.add(donation)
            db.session.commit()

    return jsonify(success=True), 200

@main_bp.route('/contact')
def contact():
    return render_template('contact.html')

@main_bp.route('/mandate')
def mandate():
    return render_template('mandate.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')
