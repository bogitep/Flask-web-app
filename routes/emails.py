from flask import Blueprint, request, flash, redirect, url_for, render_template
from flask_login import login_required  
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from flask_login import login_required, current_user
from db_conn import db
from models import Email, User, Folder, Recipient, RecipientType, EmailFolder
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)  
file_handler = logging.FileHandler('error_log.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

email_bp = Blueprint('email', __name__)

@email_bp.route('/list')
def list_emails():
    emails = Email.query.all()
    return render_template('emails/list.html', emails=emails)

@email_bp.route('/emails/add', methods=['GET', 'POST'])
@login_required
def add_email():
    if request.method == 'POST':
        try:
            subject = request.form.get('subject')
            body = request.form.get('body')
            sender_id = current_user.id  
            sent_at = request.form.get('sent_at')
            folder_id = request.form.get('folder_id') 

            if not subject or not body:
                flash("Subject and body are required.", "error")
                return redirect(url_for('emails.add_email'))

            new_email = Email(subject=subject, body=body, sender_id=sender_id, sent_at=sent_at)
            db.session.add(new_email)
            db.session.commit()

            if folder_id:
                folder = Folder.query.get(folder_id)
                if folder:
                    email_folder = EmailFolder(email_id=new_email.id, folder_id=folder.id)
                    db.session.add(email_folder)
                    db.session.commit()

            flash("Email added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred while adding the email: {e}", "error")
            print(f"Error: {e}")

        return redirect(url_for('emails.list_emails'))
    
    folders = Folder.query.all()
    return render_template('emails/add.html', folders=folders)


@email_bp.route('/update/<int:id>', methods=['GET', 'POST'])
def update_email(id):
    email = Email.query.get_or_404(id)
    
    if not email:
        flash("Email not found", "error")
        return redirect(url_for('emails/list.htm'))

    if request.method == 'POST':
        email.subject = request.form['subject']
        email.body = request.form['body']
    
        try:
            db.session.commit()
            flash("Email updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating email ID {id}: {str(e)}")
            flash("An error occurred while updating the email.", "error")
        return redirect(url_for('email.list_emails'))
    return render_template('emails/update.html', email=email)

@email_bp.route('/delete/<int:id>', methods=['POST'])
def delete_email(id):
    email = Email.query.get_or_404(id)
    try:
        db.session.delete(email)
        db.session.commit()
        flash("Email deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting email ID {id}: {str(e)}")
        flash("An error occurred while deleting the email.", "error")
    return redirect(url_for('email.list_emails'))

@email_bp.route('/search_by_sender', methods=['GET', 'POST'])
def search_by_sender():
    emails = []
    if request.method == 'POST':
        sender_query = request.form['sender'].strip()
        if not sender_query:
            flash("Please enter a sender name to search.", "info")
        else:
            try:
                user = User.query.filter(User.username.ilike(f"%{sender_query}%")).first()
                if user:
                    emails = Email.query.filter_by(sender_id=user.id).all()
                    if not emails:
                        flash("No emails found for the provided sender.", "warning")
                else:
                    flash("No user found with the provided sender name.", "warning")
            except Exception as e:
                logger.error(f"Error searching by sender '{sender_query}': {str(e)}")
                flash("An error occurred while searching by sender.", "error")
    
    return render_template('emails/search_by_sender.html', emails=emails)


@email_bp.route('/search_by_keywords', methods=['GET', 'POST'])
def search_by_keywords():
    emails = []
    if request.method == 'POST':
        keywords = request.form['keywords']
        try:
            emails = Email.query.filter(Email.body.like(f"%{keywords}%")).all()
        except Exception as e:
            logger.error(f"Error searching by keywords '{keywords}': {str(e)}")
            flash("An error occurred while searching by keywords.", "error")
    return render_template('emails/search_by_keywords.html', emails=emails)

@email_bp.route('/search_by_date_range', methods=['GET', 'POST'])
def search_by_date_range():
    emails = []
    if request.method == 'POST':
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        
        if not start_date or not end_date:
            flash("Please provide both start and end dates.", "info")
        else:
            try:
                emails = Email.query.filter(Email.sent_at.between(start_date, end_date)).all()
                if not emails:
                    flash("No emails found within the provided date range.", "warning")
            except Exception as e:
                logger.error(f"Error searching by date range '{start_date} to {end_date}': {str(e)}")
                flash("An error occurred while searching by date range.", "error")
    
    return render_template('emails/search_by_date_range.html', emails=emails)

@email_bp.route('/search_by_subject_sender', methods=['GET', 'POST'])
def search_by_subject_and_sender():
    emails = []
    if request.method == 'POST':
        subject = request.form.get('subject', '').strip()
        sender_input = request.form.get('sender', '').strip()

        if not subject and not sender_input:
            flash("Please enter at least one search criteria (subject or sender).", "info")
        else:
            try:
                sender_query = sender_input.lower().strip()
                sender_user_by_username = User.query.filter(User.username.ilike(f"%{sender_query}%")).first()
                sender_user_by_email = User.query.filter(User.email.ilike(f"%{sender_query}%")).first()

                if sender_user_by_username:
                    sender_id = sender_user_by_username.id
                elif sender_user_by_email:
                    sender_id = sender_user_by_email.id
                else:
                    sender_id = None  

                if sender_id:
                    emails = Email.query.filter(
                        Email.subject.ilike(f"%{subject}%"),
                        Email.sender_id == sender_id
                    ).all()
                else:
                    emails = Email.query.filter(Email.subject.ilike(f"%{subject}%")).all()

                if not emails:
                    flash("No emails found for the provided subject and sender.", "warning")
            except Exception as e:
                logger.error(f"Error searching by subject '{subject}' and sender '{sender_input}': {str(e)}")
                flash("An error occurred while searching by subject and sender.", "error")
    
    return render_template('emails/search_by_subject_sender.html', emails=emails)

@email_bp.route('/search_emails_with_sender', methods=['GET', 'POST'])
def search_emails_with_sender():
    emails = []
    if request.method == 'POST':
        keywords = request.form['keywords']
        try:
            emails = (
                db.session.query(Email, User)
                .join(User, Email.sender_id == User.id) 
                .filter(Email.body.like(f"%{keywords}%")) 
                .all() 
            )
        except Exception as e:
            logger.error(f"Error searching emails with sender info and keywords '{keywords}': {str(e)}")
            flash("An error occurred while searching emails with sender info.", "error")
    return render_template('emails/search_emails_with_sender.html', emails=emails)

@email_bp.route('/search_by_recipient', methods=['GET', 'POST'])
def search_by_recipient():
    emails = []
    if request.method == 'POST':
        recipient_name_or_email = request.form.get('recipient', '').strip()
        try:
            emails = (
                db.session.query(Email, Recipient)
                .join(Recipient, Email.id == Recipient.email_id)
                .filter(
                    Recipient.name.ilike(f"%{recipient_name_or_email}%") |
                    Recipient.email_id.ilike(f"%{recipient_name_or_email}%")
                )
                .options(joinedload(Recipient))
                .all()
            )
            if not emails:
                flash("No emails found for the provided recipient.", "warning")
        except Exception as e:
            logger.error(f"Error searching by receiver '{recipient_name_or_email}': {str(e)}")
            flash("An error occurred while searching emails by receiver.", "error")
    return render_template('emails/search_by_recipient.html', emails=emails)


@email_bp.route('/search_by_domain', methods=['GET', 'POST'])
def search_by_domain():
    emails = []
    if request.method == 'POST':
        domain = request.form['domain']
        try:
            emails = User.query.filter(User.email.like(f"%@{domain}")).all()
        except Exception as e:
            logger.error(f"Error searching by domain '{domain}': {str(e)}")
            flash("An error occurred while searching by domain.", "error")
    return render_template('emails/search_by_domain.html', emails=emails)


@email_bp.route('/search_full_email_info', methods=['GET', 'POST'])
def search_full_email_info():
    emails = []
    if request.method == 'POST':
        keywords = request.form.get('keywords')
        if keywords:
            emails = Email.query.options(
                joinedload(Email.sender),  
                joinedload(Email.recipients)  
            ).filter(
                (Email.subject.like(f'%{keywords}%')) |
                (Email.body.like(f'%{keywords}%'))
            ).all() 
    
    return render_template('emails/search_full_email_info.html', emails=emails)

