from flask import Blueprint, render_template, request, redirect, url_for, flash
from db_conn import db
from models import RecipientType, Recipient, Email

recipient_types_bp = Blueprint('recipient_types', __name__, url_prefix='/recipient_types')

@recipient_types_bp.route('/add', methods=['GET', 'POST'])
def add_recipient_type():
    if request.method == 'POST':
        name = request.form.get('name')

        if not name:
            flash("Recipient type name is required.", "error")
            return redirect(url_for('recipient_types.add_recipient_type'))
        
        try:
            recipient_type = RecipientType.query.filter_by(name=name).first()
            if recipient_type:
                flash("Recipient type already exists.", "error")
                return redirect(url_for('recipient_types.add_recipient_type'))

            new_recipient_type = RecipientType(name=name)
            db.session.add(new_recipient_type)
            db.session.commit()
            flash("Recipient type added successfully!", "success")

        except Exception as e:
            db.session.rollback()
            flash("An error occurred while adding the recipient type.", "error")
            print(f"Error: {e}")

        return redirect(url_for('recipient_types.list_recipient_types'))

    return render_template('recipient_type/add.html')


@recipient_types_bp.route('/list', methods=['GET'])
def list_recipient_types():
    recipient_types = RecipientType.query.all()
    return render_template('recipient_type/list.html', recipient_types=recipient_types)

@recipient_types_bp.route('/update/<int:recipient_type_id>', methods=['GET', 'POST'])
def update_recipient_type(recipient_type_id):
    recipient_type = RecipientType.query.get(recipient_type_id)

    if not recipient_type:
        flash("Recipient type not found.", "error")
        return redirect(url_for('recipient_types.list_recipient_types'))

    if request.method == 'POST':
        name = request.form['name']
        try:
            recipient_type.name = name
            db.session.commit()
            flash("Recipient type updated successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash("An error occurred while updating the recipient type.", "error")
        return redirect(url_for('recipient_types.list_recipient_types'))
    return render_template('recipient_type/update.html', recipient_type=recipient_type)

@recipient_types_bp.route('/delete/<int:recipient_type_id>', methods=['POST'])
def delete_recipient_type(recipient_type_id):
    try:
        recipient_type = RecipientType.query.get(recipient_type_id)
        db.session.delete(recipient_type)
        db.session.commit()
        flash("Recipient type deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the recipient type.", "error")
        print(f"Error: {e}")
    return redirect(url_for('recipient_types.list_recipient_types'))

@recipient_types_bp.route('/search_by_name', methods=['GET', 'POST'])
def search_by_name():
    recipient_types = []
    if request.method == 'POST':
        name = request.form['name']
        recipient_types = RecipientType.query.filter(RecipientType.name.ilike(f"%{name}%")).all()
    return render_template('recipient_type/search_by_name.html', recipient_types=recipient_types)

@recipient_types_bp.route('/search_with_recipients', methods=['GET', 'POST'])
def search_with_recipients():
    recipient_data = []
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not name:
            flash("Please provide a name to search.", "info")
            return render_template('recipient_type/search_with_recipients.html', recipient_data=[])

        try:
            recipient_data = db.session.query(
                RecipientType.id.label('recipient_type_id'),
                RecipientType.name.label('recipient_type_name'),
                Recipient.name.label('recipient_name')
            ).join(Recipient, RecipientType.id == Recipient.recipient_type_id)\
             .filter(RecipientType.name.ilike(f"%{name}%"))\
             .all()

            print("Query Results:", recipient_data)

            if not recipient_data:
                flash("No matching recipient types found.", "warning")

        except Exception as e:
            flash("An error occurred while searching with recipients.", "error")
            print(f"Error during query execution: {e}")

    return render_template('recipient_type/search_with_recipients.html', recipient_data=recipient_data)



@recipient_types_bp.route('/search_with_emails', methods=['GET', 'POST'])
def search_with_emails():
    results = []
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash("Please provide a recipient name to search.", "info")
            return render_template('recipient_type/search_with_emails.html', results=[])

        try:
            results = db.session.query(
                RecipientType.id.label('recipient_type_id'),
                RecipientType.name.label('recipient_type_name'),
                Email.subject.label('email_subject'),
                Recipient.name.label('recipient_name')
            ).join(Recipient, RecipientType.id == Recipient.recipient_type_id)\
             .join(Email, Recipient.email_id == Email.id)\
             .filter(Recipient.name.ilike(f"%{name}%"))\
             .all()

            if not results:
                flash("No results found for the provided recipient name.", "warning")

        except Exception as e:
            flash("An error occurred while searching with emails.", "error")
            print(f"Error during query execution: {e}")

    return render_template('recipient_type/search_with_emails.html', results=results)
