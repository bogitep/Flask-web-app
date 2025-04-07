from flask import Flask, render_template, redirect, url_for, session, flash
from flask_login import LoginManager, current_user
from flask_sqlalchemy import SQLAlchemy
from routes.auth import auth_bp
from routes.recipients import recipients_bp
from routes.users import user_bp
from routes.attachments import attachment_bp
from routes.folders import folders_bp
from routes.recipient_type import recipient_types_bp
from routes.emails import email_bp
from db_conn import db, configure_db
from models import User, Email, Recipient, Attachment, Folder, RecipientType

app = Flask(__name__)

app.secret_key = "random_key"

app.config['SESSION_COOKIE_NAME'] = 'session_id'  # Custom session cookie name
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevents JavaScript from accessing the session cookie
app.config['SESSION_COOKIE_SECURE'] = True  # Ensures cookies are only sent over HTTPS (production)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection; 'Strict' for stricter protection
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session lifetime in seconds (1 hour)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

configure_db(app)

app.register_blueprint(auth_bp)
app.register_blueprint(recipients_bp, url_prefix='/recipients')
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(attachment_bp, url_prefix='/attachments')
app.register_blueprint(folders_bp, url_prefix='/folders')
app.register_blueprint(recipient_types_bp, url_prefix='/recipient_types')
app.register_blueprint(email_bp, url_prefix='/emails')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route
@app.route('/')
def index():
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    if current_user.is_admin_user():  
        return redirect(url_for('admin_dashboard')) 
    else:
        return redirect(url_for('user_dashboard'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not current_user.is_authenticated:
        flash("You must be logged in to access this page.", "error")
        return redirect(url_for('auth.login'))
    
    if not current_user.is_admin_user():
        flash("You don't have permission to access this page.", "error")
        return redirect(url_for('index'))
    
    users = User.query.all() 
    emails = Email.query.all()  
    recipients = Recipient.query.all()  
    attachments = Attachment.query.all() 
    folders = Folder.query.all()
    recipient_types = RecipientType.query.all()  

    return render_template(
        'admin_dashboard.html',
        users=users,
        emails=emails,
        recipients=recipients,
        attachments=attachments,
        folders=folders,
        recipient_types=recipient_types
    )

@app.route('/user/dashboard')
def user_dashboard():
    if current_user.is_admin_user():
        flash("Admins don't access this page.", "warning")
        return redirect(url_for('admin_dashboard'))
    return render_template('user_dashboard.html')

@app.route('/dashboard')
def dashboard():
    if not current_user.is_authenticated: 
        return redirect(url_for('auth.login'))
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  
    app.run(debug=True)
