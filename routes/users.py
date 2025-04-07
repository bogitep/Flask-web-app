from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash
from db_conn import db
import re
from forms import UpdateUserForm 
from email_validator import validate_email, EmailNotValidError
from flask_login import login_required, current_user
from models import User, Folder, Email, Recipient

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/list', methods=['GET'], endpoint='list_users')
def list_user():
    users = User.query.all()
    return render_template('users/list.html', users=users)

@user_bp.route('/add', methods=['GET', 'POST'])
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        is_admin = request.form.get('is_admin', '0') == '1'

        existing_user = User.query.filter_by(username=username, email=email, password=password, is_admin=is_admin).first()
        if existing_user:
            flash("A user with this name already exist.", "error")
            return redirect(url_for('users.add_user'))
        try:
            new_user = User(username=username, email=email, password=password, is_admin=is_admin)
            db.session.add(new_user)
            db.session.commit()
            flash("User added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding user: {e}", "danger")
        return redirect(url_for('user.list_users'))
    
    return render_template('users/add.html')

def is_valid_username(username):
    return bool(re.match(r'^[a-zA-Z0-9_]{3,30}$', username))

def is_valid_email(email):
    return bool(re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email))

def is_valid_email(email):
    try:
        validate_email(email)  
        return True
    except EmailNotValidError:
        return False

@user_bp.route('/update/<int:user_id>', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    user = User.query.get(user_id)

    if not user:
        flash("User not found.", "error")
        return redirect(url_for('user.list_users'))
    
    if user.id != current_user.id and not current_user.is_admin:
        flash("You are not authorized to edit this user.", "error")
        return redirect(url_for('user.list_users'))

    # Instantiate the form and prepopulate fields with the user's current data
    form = UpdateUserForm(obj=user)

    if form.validate_on_submit():  # Automatically handles POST method
        try:
            # Update user fields with form data
            form.populate_obj(user)

            # Additional admin-only fields
            if current_user.is_admin:
                user.is_admin = form.is_admin.data
                user.is_banned = form.is_banned.data
                user.is_flagged = form.is_flagged.data

            # Save changes to the database
            db.session.commit()
            flash("User updated successfully!", "success")
            return redirect(url_for('user.list_users'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while updating the user: {e}", "error")
            return redirect(url_for('user.update_user', user_id=user_id))

    # Render the form for GET requests
    return render_template('users/update.html', form=form, user=user)

@user_bp.route('/delete/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting user: {e}", "danger")
    return redirect(url_for('user.list_users'))


@user_bp.route('/search_users_with_folders', methods=['GET', 'POST'])
def search_users_with_folders():
    folders = Folder.query.all()

    users_with_folders = []  
    if request.method == 'POST':
        folder_name = request.form.get('folder_name')  
        if folder_name:
            try:
                users_with_folders = User.query.filter(
                    User.folders.any(Folder.folder_name == folder_name)
                ).all()
                if not users_with_folders:
                    flash("No users found with the specified folder name.", "warning")
            except Exception as e:
                flash("An error occurred while searching users with folders.", "error")
                print(f"Error: {e}")
        else:
            flash("Please select a folder.", "warning")

    return render_template('users/search_users_with_folders.html',folders=folders, users=users_with_folders 
    )


@user_bp.route('/search_users_with_recipients', methods=['GET', 'POST'])
def search_users_with_recipients():
    if request.method == 'POST':
        recipient_name = request.form.get('recipient_name')  
        if not recipient_name:
            flash("Please provide a recipient name.", "error")
            return render_template('users/search_users_with_recipients.html', users=[])

        try:
            users_with_recipients = (
                db.session.query(User)
                .join(Recipient, Recipient.user_id == User.id)  
                .filter(Recipient.name.ilike(f"%{recipient_name}%"))
                .all()
            )

            if not users_with_recipients:
                flash("No users found with the specified recipient name.", "warning")

            return render_template(
                'users/search_users_with_recipients.html',
                users=users_with_recipients
            )
        except Exception as e:
            flash("An error occurred while searching users with recipients.", "error")
            print(f"Error: {e}")
            return render_template('users/search_users_with_recipients.html', users=[])

    return render_template('users/search_users_with_recipients.html', users=[])

@user_bp.route('/search_users_with_email_details', methods=['GET', 'POST'])
def search_users_with_email_details():
    users = []  
    
    if request.method == 'POST':
        email_query = request.form.get('email_query', '').strip()  
        

        if email_query:
            users = User.query.join(Email).filter(Email.subject.ilike(f"%{email_query}%")).all()
            
            if not users:
                flash('No users found matching the email details.', 'warning')
        else:
            flash('Please enter a valid search query.', 'danger')
    
    
    return render_template('users/search_users_with_email_details.html', users=users)

@user_bp.route('/search_users_with_folders_emails', methods=['GET', 'POST'])
def search_users_with_folders_emails():
    users = None  
    if request.method == 'POST':
        search_query = request.form.get('username', '').strip()
        if search_query:
            try:
                users = (
                    db.session.query(
                        User.username.label('username'),
                        Folder.folder_name.label('folder_name'),
                        Email.subject.label('email_subject'),
                        Email.sent_at.label('email_sent_at')
                    )
                    .join(Folder, User.id == Folder.user_id) 
                    .join(Email, Folder.id == Email.folder_id, isouter=True) 
                    .filter(User.username.ilike(f"%{search_query}%")) 
                    .order_by(User.username, Folder.folder_name, Email.sent_at)
                    .all()
                )
                if not users:
                    flash("No users found with the given username.", "warning")
            except Exception as e:
                flash("An error occurred while searching users.", "error")
                print(f"Error: {e}")

    return render_template('users/search_users_with_folders_emails.html', users=users)
