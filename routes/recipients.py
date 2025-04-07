from flask import Blueprint, render_template, request, redirect, url_for, flash
from db_conn import db
from models import Recipient, RecipientType, User, Email

recipients_bp = Blueprint('recipients', __name__, url_prefix='/recipients')

@recipients_bp.route('/add', methods=['GET', 'POST'])
def add_recipient():
    if request.method == 'POST':
        recipient_type_id = request.form.get('recipient_type')
        email_id = request.form.get('email_id')
        user_id = request.form.get('user_id')
        recipient_name = request.form.get('recipient_name')

        print(f"Form data: recipient_type_id={recipient_type_id}, email_id={email_id}, user_id={user_id}, recipient_name={recipient_name}")

        if not recipient_type_id or not email_id or not recipient_name or not user_id:  
            flash('All fields are required. Please check the inputs.', 'error')
            return redirect(url_for('recipients.add_recipient'))
        
        recipient_type = RecipientType.query.get(recipient_type_id)
        if not recipient_type:
            flash('Invalid recipient type. Please check the inputs.', 'error')
            return redirect(url_for('recipients.add_recipient'))

        email = Email.query.get(email_id)
        if not email:
            flash('Invalid email ID. Please check the inputs.', 'error')
            return redirect(url_for('recipients.add_recipient'))
        
        user = User.query.get(user_id)
        if not user:
            flash('Invalid user ID. Please check the inputs.', 'error')
            return redirect(url_for('recipients.add_recipient'))

        existing_recipient = Recipient.query.filter_by(
            recipient_type_id=recipient_type.id,
            email_id=email_id,
            user_id=user_id
        ).first()
        if existing_recipient:
            flash('This recipient already exists.', 'error')
            return redirect(url_for('recipients.add_recipient'))

        new_recipient = Recipient(
            recipient_type_id=recipient_type.id,
            email_id=email_id,
            user_id=user_id,
            name=recipient_name
        )
        db.session.add(new_recipient)
        db.session.commit()

        flash('Recipient added successfully!', 'success')
        return redirect(url_for('recipients.list_recipients'))

    recipient_types = RecipientType.query.all()
    emails = Email.query.all()
    users = User.query.all()

    return render_template('recipients/add.html', recipient_types=recipient_types, emails=emails, users=users)

@recipients_bp.route('/list')
def list_recipients():
    recipients = (
        db.session.query(Recipient.id, Recipient.email_id, RecipientType.name.label("recipient_type"), 
                         User.username.label("user"), Recipient.name)
        .join(RecipientType, Recipient.recipient_type_id == RecipientType.id)
        .join(User, Recipient.user_id == User.id)
        .all()
    )
    return render_template('recipients/list.html', recipients=recipients)

@recipients_bp.route('/update_recipient/<int:recipient_id>', methods=['GET', 'POST'])
def update_recipient(recipient_id):
    recipient = Recipient.query.get(recipient_id)

    if request.method == 'POST':
        recipient_type_id = request.form['recipient_type']
        email_id = request.form['email_id']
        user_id = request.form['user_id']
        recipient_name = request.form['recipient_name']

        try:
            recipient.recipient_type_id = recipient_type_id
            recipient.email_id = email_id
            recipient.user_id = user_id
            recipient.name = recipient_name

            db.session.commit()
            flash("Recipient updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the recipient.", "error")
        return redirect(url_for('recipients.list_recipients'))

    recipient_types = RecipientType.query.all()
    emails = Email.query.all()
    users = User.query.all()

    return render_template('recipients/update.html', recipient=recipient, recipient_types=recipient_types, 
                           emails=emails, users=users)

@recipients_bp.route('/delete_recipient/<int:recipient_id>', methods=['POST'])
def delete_recipient(recipient_id):
    try:
        recipient = Recipient.query.get(recipient_id)
        db.session.delete(recipient)
        db.session.commit()
        flash("Recipient deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the recipient.", "error")
        print(f"Error: {e}")
    return redirect(url_for('recipients.list_recipients'))

@recipients_bp.route('/search_by_type', methods=['GET', 'POST'])
def search_recipients_by_type():
    type_name = request.form.get('type_name')  
    recipients = db.session.query(
        Recipient.id,
        Recipient.email_id,
        RecipientType.name,  
    ).join(RecipientType, Recipient.recipient_type_id == RecipientType.id).filter(
        RecipientType.name.ilike(f'%{type_name}%') 
    ).all()

    return render_template('recipients/search_recipients_by_type.html', recipients=recipients)

@recipients_bp.route('/search_recipients_with_emails', methods=['GET', 'POST'])
def search_recipients_with_emails():
    recipients = []
    
    if request.method == 'POST':
        email_subject = request.form.get('email_subject', '').strip()

        if not email_subject:
            flash("Please enter an email subject to search.", "warning")
            return render_template('recipients/search_with_emails.html', recipients=[])

        try:
            recipients = (
                db.session.query(Recipient.name, Recipient.email_id, Email.subject, Email.body, User.username)
                .join(Email, Recipient.email_id == Email.id)
                .join(User, Recipient.user_id == User.id)
                .filter(Email.subject.ilike(f"%{email_subject}%"))
                .all()
            )

            if not recipients:
                flash("No recipients found for the given email subject.", "info")
        except Exception as e:
            flash("An error occurred while searching recipients with emails.", "danger")
    return render_template('recipients/search_with_emails.html', recipients=recipients)


