from flask import Blueprint, request, redirect, url_for, flash, session, render_template, g
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
from flask_login import login_required, current_user, login_user, logout_user
import re
import dns.resolver
import logging
from email_validator import validate_email, EmailNotValidError
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from pyotp import TOTP

from models import db, User

auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')

limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])

logging.basicConfig(filename='security.log', level=logging.WARNING)


def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if current_user.role not in roles:
                flash("Access denied. You do not have the required privileges.", "error")
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper


def is_strong_password(password):
    """Check if password meets security criteria."""
    password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&|[\]\"^])[A-Za-z\d@$!%*?&|[\]\"^]{8,}$"

    return re.match(password_regex, password) is not None


def is_valid_email(email):
    """Validate email format and domain."""
    try:
        validate_email(email)
        return True
    except EmailNotValidError:
        return False


def has_mx_record(domain):
    """Check if the email domain has MX (Mail Exchange) records."""
    try:
        records = dns.resolver.resolve(domain, 'MX')
        return len(records) > 0
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, Exception):
        return False


def is_valid_username(username):
    """Validate the username format."""
    username_regex = r"^[a-zA-Z0-9_.-]{3,30}$"
    return re.match(username_regex, username) is not None


def log_suspicious_activity(activity, details):
    """Log suspicious activity."""
    logging.warning(f"{activity} - {details}")


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not username or not email or not password:
            flash("All fields are required!", "error")
            return redirect(url_for('auth.register'))

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('auth.register'))

        if not is_strong_password(password):
            flash("Password must be at least 8 characters long, include an uppercase letter, a lowercase letter, a number, and a special character.", "error")
            return redirect(url_for('auth.register'))

        if not is_valid_email(email):
            flash("Invalid email format or domain!", "error")
            return redirect(url_for('auth.register'))

        if not is_valid_username(username):
            flash("Invalid username. Only alphanumeric characters, dashes, and underscores are allowed.", "error")
            return redirect(url_for('auth.register'))

        user = User.query.filter((User.username == username) | (User.email == email)).first()
        if user:
            flash("Username or email is already registered!", "error")
            return redirect(url_for('auth.register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)
        new_user = User(
            username=username,
            password=hashed_password,
            email=email,
            created_at=datetime.now()
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in.", "info")
        return redirect(url_for('index'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user:
            if user.is_locked():
                flash("Account is locked. Try again later.", "error")
                return redirect(url_for('auth.login'))

            if check_password_hash(user.password, password):
                if user.mfa_secret:
                    session['mfa_user_id'] = user.id  
                    print(f"User requires MFA, session ID: {session.sid}")
                    return render_template('auth/login.html', mfa_required=True, email=email)  
                else:
                    user.failed_login_attempts = 0
                    db.session.commit()
                    print(f"Logging in user {user.id}")
                    login_user(user, remember=False)
                    flash("Login successful!", "success")
                    return redirect(url_for('index'))
            else:
                user.failed_login_attempts += 1
                if user.failed_login_attempts >= 5:
                    user.lock_time = datetime.now()  
                db.session.commit()
                flash("Invalid email or password!", "error")
        else:
            flash("Invalid email or password!", "error")

    return render_template('auth/login.html', mfa_required=False)
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for('auth.login'))


@auth_bp.route('/enable_mfa', methods=['GET', 'POST'])
@login_required
def enable_mfa():
    """Enable Multi-Factor Authentication (MFA) for the user."""
    if request.method == 'POST':
        totp = pyotp.TOTP(pyotp.random_base32())  
        user = current_user
        user.mfa_secret = totp.secret  

        print(f"Generated MFA secret for {user.username}: {user.mfa_secret}")

        db.session.commit() 
        qr_code_url = totp.provisioning_uri(name=user.email, issuer_name="YourAppName")

        return render_template('auth/enable_mfa.html', qr_code_url=qr_code_url)

    return render_template('auth/enable_mfa.html')




@auth_bp.route('/verify_mfa', methods=['POST'])
@login_required
def verify_mfa():
    email = request.form['email']
    mfa_token = request.form['mfa_token']

    user = User.query.filter_by(email=email).first()

    if user and user.mfa_secret:
        if verify_mfa_token(user.mfa_secret, mfa_token):
            login_user(user, remember=False)
            flash("Login successful!", "success")
            session.pop('mfa_user_id', None)  
            return redirect(url_for('index'))
        else:
            flash("Invalid MFA token!", "error")
            return redirect(url_for('auth.login')) 

    flash("No MFA required or invalid user.", "error")
    return redirect(url_for('auth.login'))

    
    
def verify_mfa_token(mfa_secret, mfa_token):
    totp = pyotp.TOTP(mfa_secret)
    return totp.verify(mfa_token)
