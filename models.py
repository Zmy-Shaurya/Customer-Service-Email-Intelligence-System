from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class EmailTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_email = db.Column(db.String(120))
    subject = db.Column(db.String(255))
    body = db.Column(db.Text)
    intent = db.Column(db.String(100))
    sentiment = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    ai_draft_reply = db.Column(db.Text)
    status = db.Column(db.String(20), default="New")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    gmail_id = db.Column(db.String(200), unique=True, nullable=True)