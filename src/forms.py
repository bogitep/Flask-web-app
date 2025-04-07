from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, IntegerField, TextAreaField 
from wtforms.validators import DataRequired, Email, Length, NumberRange, Optional

class UpdateUserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    is_admin = BooleanField('Is Admin')
    is_banned = BooleanField('Is Banned')
    is_flagged = BooleanField('Is Flagged')
    submit = SubmitField('Update User')

class EmailForm(FlaskForm):
    subject = StringField('Subject', validators=[DataRequired(), Length(min=3, max=255)])
    body = TextAreaField('Body', validators=[DataRequired()])
    sender_id = IntegerField('Sender ID', validators=[DataRequired()])
    folder_id = IntegerField('Folder ID', validators=[Optional()])
    submit = SubmitField('Submit')

class FolderForm(FlaskForm):
    folder_name = StringField('Folder Name', validators=[DataRequired(), Length(min=1, max=100)])
    user_id = IntegerField('User ID', validators=[DataRequired()])
    submit = SubmitField('Submit')

class EmailFolderForm(FlaskForm):
    email_id = IntegerField('Email ID', validators=[DataRequired()])
    folder_id = IntegerField('Folder ID', validators=[DataRequired()])
    submit = SubmitField('Submit')

class RecipientForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=255)])
    email_id = IntegerField('Email ID', validators=[DataRequired()])
    recipient_type_id = IntegerField('Recipient Type ID', validators=[Optional()])
    user_id = IntegerField('User ID', validators=[DataRequired()])
    submit = SubmitField('Submit')

class RecipientTypeForm(FlaskForm):
    name = StringField('Recipient Type Name', validators=[DataRequired(), Length(min=1, max=50)])
    submit = SubmitField('Submit')

class AttachmentForm(FlaskForm):
    file_name = StringField('File Name', validators=[DataRequired(), Length(min=1, max=255)])
    file_type = StringField('File Type', validators=[DataRequired(), Length(min=1, max=50)])
    file_size = IntegerField('File Size (bytes)', validators=[DataRequired(), NumberRange(min=1)])
    email_id = IntegerField('Email ID', validators=[DataRequired()])
    submit = SubmitField('Submit')