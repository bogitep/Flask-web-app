from db_conn import db
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_banned = db.Column(db.Boolean, default=False)
    is_flagged = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    failed_login_attempts = db.Column(db.Integer, default=0)  # Track failed attempts
    last_failed_login = db.Column(db.DateTime)
    lock_time = db.Column(db.DateTime, nullable=True)
    mfa_secret = db.Column(db.String(255), nullable=True)

    emails_sent = db.relationship(
        'Email', foreign_keys='Email.sender_id', backref='user_sender', lazy='joined', cascade='all, delete-orphan'
    )
    folders = db.relationship('Folder', backref='user', lazy='joined', cascade='all, delete-orphan')

    def get_id(self):
        return str(self.id)

    @property
    def is_active(self):
        return True  

    @property
    def is_authenticated(self):
        return True  

    @property
    def is_anonymous(self):
        return False  
    
    def is_admin_user(self):
        return self.is_admin
    
    def is_regular_user(self):
        return not self.is_admin

    def reset_failed_login(self):
        self.failed_login_attempts = 0
        self.last_failed_login = None
        db.session.commit()

    def is_locked(self):
        if self.failed_login_attempts >= 5:
            if self.lock_time:
                lock_time_limit = self.lock_time + timedelta(minutes=15)
                if datetime.now() < lock_time_limit:
                    return True  
                else:
                    self.failed_login_attempts = 0
                    self.lock_time = None 
                    db.session.commit()
            else:
                return False
        return False


class Email(db.Model):
    __tablename__ = 'emails'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    sent_at = db.Column(db.DateTime, default=datetime.now)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=True)

    folder = db.relationship('Folder', backref='emails', lazy='joined')
    sender = db.relationship('User', backref='sent_emails', lazy='joined', foreign_keys=[sender_id])
    recipients = db.relationship('Recipient', backref='email', lazy='joined', cascade='all, delete-orphan')
    attachments = db.relationship('Attachment', backref='email', lazy='joined', cascade='all, delete-orphan')
    email_folders = db.relationship('EmailFolder', backref='email_folder', lazy='joined', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Email {self.subject}>"
    

class Folder(db.Model):
    __tablename__ = 'folders'
    id = db.Column(db.Integer, primary_key=True)
    folder_name = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    email_folders = db.relationship('EmailFolder', backref='folder_email', lazy='joined', cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Folder {self.folder_name}>"


class EmailFolder(db.Model):
    __tablename__ = 'email_folders'
    id = db.Column(db.Integer, primary_key=True)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folders.id'), nullable=False)

    email = db.relationship('Email', back_populates='email_folders', lazy='joined')
    folder = db.relationship('Folder', back_populates='email_folders', lazy='joined')

    def __repr__(self):
        return f"<EmailFolder Email ID: {self.email_id}, Folder ID: {self.folder_id}>"


class Recipient(db.Model):
    __tablename__ = 'recipients'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False)
    recipient_type_id = db.Column(db.Integer, db.ForeignKey('recipient_types.id'), nullable=True)  
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    recipient_type = db.relationship('RecipientType', back_populates='recipients', lazy='joined', uselist=False)
    user = db.relationship('User', foreign_keys=[user_id], backref='received_emails', lazy='joined')

    def __repr__(self):
        return f"<Recipient Email ID: {self.email_id}, User ID: {self.user_id}>"

    @property
    def type_name(self):
        return self.recipient_type.name if self.recipient_type else 'No Type'


class RecipientType(db.Model):
    __tablename__ = 'recipient_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    recipients = db.relationship('Recipient', back_populates='recipient_type', lazy='joined')

    def __repr__(self):
        return f"<RecipientType {self.name}>"


class Attachment(db.Model):
    __tablename__ = 'attachments'

    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    email_id = db.Column(db.Integer, db.ForeignKey('emails.id'), nullable=False)

    def __repr__(self):
        return f"<Attachment {self.file_name} ({self.file_type}, {self.file_size} bytes)>"
