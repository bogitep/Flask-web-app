from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy.exc import SQLAlchemyError
from models import Attachment, Email, User, db 

attachment_bp = Blueprint('attachment', __name__)

@attachment_bp.route('/list')
def list_attachments():
    attachments = Attachment.query.all()
    return render_template('attachments/list.html', attachments=attachments)

@attachment_bp.route('/add', methods=['GET', 'POST'])
def add_attachment():
    if request.method == 'POST':
        email_id = request.form['email_id']
        file_name = request.form['file_name']
        file_type = request.form['file_type']
        file_size = request.form['file_size']
        
        new_attachment = Attachment(
            email_id=email_id,
            file_name=file_name,
            file_type=file_type,
            file_size = file_size,
        )
        
        try:
            db.session.add(new_attachment)
            db.session.commit()
            flash("Attachment added successfully!", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while adding the attachment.", "error")
            print(f"Error: {str(e)}")
        return redirect(url_for('attachment.list_attachments'))
    
    return render_template('attachments/add.html')

@attachment_bp.route('/attachments/update/<int:attachment_id>', methods=['GET', 'POST'])
def update_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    
    if request.method == 'POST':
        file_name = request.form['file_name']
        file_path = request.form['file_path']
        file_size = request.form['file_size']
        file_type = request.form['file_type']

        try:
            attachment.file_name = file_name
            attachment.file_path = file_path
            attachment.file_size = file_size
            attachment.file_type = file_type
            db.session.commit()
            flash("Attachment updated successfully!", "success")
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("An error occurred while updating the attachment.", "error")
            print(f"Error: {str(e)}")
        return redirect(url_for('attachment.list_attachments'))
    
    return render_template('attachments/update.html', attachment=attachment)

@attachment_bp.route('/attachments/delete/<int:attachment_id>', methods=['POST'])
def delete_attachment(attachment_id):
    attachment = Attachment.query.get_or_404(attachment_id)
    
    try:
        db.session.delete(attachment)
        db.session.commit()
        flash("Attachment deleted successfully!", "success")
    except SQLAlchemyError as e:
        db.session.rollback()
        flash("An error occurred while deleting the attachment.", "error")
        print(f"Error: {str(e)}")
    return redirect(url_for('attachment.list_attachments'))

@attachment_bp.route('/attachments/search_by_email_id', methods=['GET', 'POST'])
def search_by_email_id():
    attachments = []
    if request.method == 'POST':
        email_id = request.form['email_id']
        
        if not email_id:
            return render_template('attachments/search_by_email_id.html', error="Please provide an Email ID.")
        
        attachments = Attachment.query.filter_by(email_id=email_id).all()
        
        if not attachments:
            return render_template('attachments/search_by_email_id.html', attachments=[], message="No attachments found.")
        
    return render_template('attachments/search_by_email_id.html', attachments=attachments)

@attachment_bp.route('/attachments/search_by_file_name', methods=['GET', 'POST'])
def search_by_file_name():
    attachments = []
    if request.method == 'POST':
        file_name = request.form['file_name']
        attachments = Attachment.query.filter(Attachment.file_name.like(f"%{file_name}%")).all()
    return render_template('attachments/search_by_file_name.html', attachments=attachments)

@attachment_bp.route('/attachments/search_by_file_size', methods=['GET', 'POST'])
def search_by_file_size():
    attachments_with_email_user = []

    if request.method == 'POST':
        min_size = request.form.get('min_size', type=int)
        max_size = request.form.get('max_size', type=int)

        query = (
            db.session.query(Attachment, Email, User)
            .join(Email, Email.id == Attachment.email_id)
            .join(User, Email.sender_id == User.id)
        )

        if min_size is not None and min_size >= 0:
            query = query.filter(Attachment.file_size >= min_size)
        if max_size is not None and max_size >= 0:
            query = query.filter(Attachment.file_size <= max_size)

        attachments_with_email_user = query.all()

    return render_template('attachments/search_by_file_size.html', attachments_with_email_user=attachments_with_email_user)


@attachment_bp.route('/attachments/search_by_email_and_file_name', methods=['GET', 'POST'])
def search_by_email_and_file_name():
    attachments = []
    if request.method == 'POST':
        email_id = request.form['email_id']
        file_name = request.form['file_name']
        attachments = Attachment.query.filter_by(email_id=email_id).filter(
            Attachment.file_name.like(f"%{file_name}%")
        ).all()
    return render_template('attachments/search_by_email_and_file_name.html', attachments=attachments)


@attachment_bp.route('/attachments/search_with_users_info', methods=['GET', 'POST'])
def search_with_users_info():
    attachments_with_user = []
    
    if request.method == 'POST':
        search_query = request.form['search_query']
    
        attachments_with_user = (
            db.session.query(Attachment, Email, User)
            .join(Email, Email.id == Attachment.email_id)  
            .join(User, Email.sender_id == User.id)        
            .filter(
                (Attachment.file_name.like(f"%{search_query}%")) |  
                (User.username.like(f"%{search_query}%"))    
            )
            .all()  
        )
    
    return render_template('attachments/search_with_users_info.html', attachments=attachments_with_user)

