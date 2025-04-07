from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from db_conn import db   
from models import User, Folder, Email, EmailFolder
import logging
folders_bp = Blueprint('folders', __name__)
logging.basicConfig(level=logging.INFO)  
logger = logging.getLogger(__name__)

@folders_bp.route('/folders/add', methods=['GET', 'POST'])
@login_required
def add_folder():
    if request.method == 'POST':
        folder_name = request.form.get('folder_name')
        user_id = request.form.get('user_id')
        email_ids = request.form.getlist('email_ids')

        if not folder_name:
            flash("Folder name is required.", "error")
            return redirect(url_for('folders.add_folder'))
        if not user_id:
            flash("User ID is required.", "error")
            return redirect(url_for('folders.add_folder'))
        existing_folder = Folder.query.filter_by(folder_name=folder_name, user_id=user_id).first()
        if existing_folder:
            flash("A folder with this name already exists for the user.", "error")
            return redirect(url_for('folders.add_folder'))
        try:
            user = User.query.get(user_id)
            if not user:
                flash("User not found.", "error")
                return redirect(url_for('folders.add_folder'))

            new_folder = Folder(folder_name=folder_name, user_id=user_id)
            db.session.add(new_folder)
            db.session.commit()

            for email_id in email_ids:
                email = Email.query.get(email_id)
                if email:
                    email_folder = EmailFolder(email_id=email.id, folder_id=new_folder.id)
                    db.session.add(email_folder)

            db.session.commit()
            flash("Folder added and emails associated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", "error")
            print(f"Error: {e}")

        return redirect(url_for('folders.list_folders'))

    emails = Email.query.all()
    return render_template('folders/add.html', emails=emails)


@folders_bp.route('/folders/list')
def list_folders():
    folders = Folder.query.all()  
    return render_template('folders/list.html', folders=folders)

@folders_bp.route('/folders/update/<int:folder_id>', methods=['GET', 'POST'])
def update_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)
    users = User.query.all()

    if request.method == 'POST':
        folder_name = request.form['folder_name']
        user_id = request.form['user_id']
        email_folder_id = request.form.get('email_folder_id') 

        try:
            folder.folder_name = folder_name
            folder.user_id = user_id
            if email_folder_id:
                folder.email_folder_id = email_folder_id
            db.session.commit()
            flash("Folder updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating folder: {e}")
            flash("An error occurred while updating the folder.", "error")
        return redirect(url_for('folders.list_folders'))

    return render_template('folders/update.html', folder=folder, users=users)


@folders_bp.route('/folders/delete/<int:folder_id>', methods=['POST'])
def delete_folder(folder_id):
    folder = Folder.query.get_or_404(folder_id)

    try:
        db.session.delete(folder)
        db.session.commit()
        flash("Folder deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the folder.", "error")
        print(f"Error: {e}")

    return redirect(url_for('folders.list_folders'))

@folders_bp.route('/folders/search_by_name', methods=['GET', 'POST'])
def search_by_name():
    folders = []
    if request.method == 'POST':
        folder_name = request.form['folder_name']
        folders = Folder.query.filter(Folder.folder_name.like(f"%{folder_name}%")).all()
        if not folders:
            flash("No folders found with that name.", "info")
    return render_template('folders/search_by_name.html', folders=folders)

@folders_bp.route('/folders/search_by_user_id', methods=['GET', 'POST'])
def search_by_user_id():
    folders = []
    if request.method == 'POST':
        user_id = request.form['user_id']
        folders = Folder.query.filter_by(user_id=user_id).all()
        if not folders:
            flash("No folders found for this user.", "info")
    return render_template('folders/search_by_user_id.html', folders=folders)

@folders_bp.route('/folders/search_with_user_info', methods=['GET', 'POST'])
def search_with_user_info():
    folders = []
    if request.method == 'POST':
        folder_name = request.form['folder_name']
        folders = db.session.query(Folder, User.username, User.email) \
            .join(User, Folder.user_id == User.id) \
            .filter(Folder.folder_name.like(f"%{folder_name}%")) \
            .all()
        if not folders:
            flash("No folders found with that name.", "info")
    return render_template('folders/search_with_user_info.html', folders=folders)

@folders_bp.route('/folders/search_by_email_folder', methods=['GET', 'POST'])
def search_by_email_folder():
    folders = Folder.query.all()  
    emails = []

    if request.method == 'POST':
        folder_id = request.form['folder_id']
        folder = Folder.query.get(folder_id)
        if folder:
            emails = [email_folder.email for email_folder in folder.email_folders]
        else:
            flash("Folder not found.", "error")

    return render_template('folders/search_by_email_folder.html', folders=folders, emails=emails)



@folders_bp.route('/folders/search_with_emails', methods=['GET', 'POST'])
def search_with_emails():
    folders = []
    if request.method == 'POST':
        folder_name = request.form['folder_name']
        folders = db.session.query(Folder, Email.subject).join(Email, Folder.email_folder_id == Email.id).filter(Folder.folder_name.like(f"%{folder_name}%")).all()
        if not folders:
            flash("No folders found with that name and email info.", "info")
    return render_template('folders/search_with_emails.html', folders=folders)

