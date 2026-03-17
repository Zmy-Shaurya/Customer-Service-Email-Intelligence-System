from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class EmailTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_email = db.Column(db.String(120))
    subject = db.Column(db.String(255))
    body = db.Column(db.Text)
    intent = db.Column(db.String(100))
    sentiment = db.Column(db.String(50))
    priority = db.Column(db.String(20))
    ai_draft_reply = db.Column(db.Text)
    status = db.Column(db.String(20), default="Open")
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    gmail_id = db.Column(db.String(200), unique=True, nullable=True)