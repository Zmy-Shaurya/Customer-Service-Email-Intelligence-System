from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, EmailTicket, User
import threading
from services.ai_service import analyse_email
import logging
from dotenv import load_dotenv
from services.gmail_service import fetch_unread_emails, send_reply
from sqlalchemy import or_
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

MAX_AI_THREADS_PER_SYNC = 10

load_dotenv()

logging.basicConfig(
    filename="logs.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "super-secret-key-change-in-production"

db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    # Seed a default employee account if none exists
    if not User.query.first():
        default_user = User(username="admin")
        default_user.set_password("admin123")
        db.session.add(default_user)
        db.session.commit()

# --------------------------------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.")
    return render_template("login.html")

# --------------------------------------------------------------------------------
@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# --------------------------------------------------------------------------------
@app.route('/')
@login_required
def home():
    return redirect(url_for("dashboard"))

# --------------------------------------------------------------------------------
@app.route('/new-ticket', methods=["GET","POST"])
@login_required
def new_ticket():
    if request.method == "POST":
        customer_email = request.form.get("customer_email", "").strip()
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not customer_email or not subject or not body:
            logging.error("Missing form data in new-ticket POST request")
            return redirect(url_for("new_ticket"))

        ticket = EmailTicket(
            customer_email=customer_email,
            subject=subject,
            body=body
        )
        db.session.add(ticket)
        db.session.commit()

        thread = threading.Thread(
            target=process_ticket_ai,
            args=(ticket.id,),
            daemon=True
        )
        thread.start()

        logging.info(f"New ticket created with ID: {ticket.id}")
        return redirect(url_for("dashboard"))

    return render_template("index.html")

# --------------------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    query = EmailTicket.query

    priority = request.args.get("priority")
    if priority:
        query = query.filter(EmailTicket.priority.ilike(priority))

    status = request.args.get("status")
    if status:
        query = query.filter(EmailTicket.status.ilike(status))
        
    sentiment = request.args.get("sentiment")
    if sentiment:
        query = query.filter(EmailTicket.sentiment.ilike(sentiment))
        
    intent = request.args.get("intent")
    if intent:
        query = query.filter(EmailTicket.intent.ilike(f"%{intent}%"))

    search = request.args.get("search")
    if search:
        query = query.filter(
            or_(
                EmailTicket.subject.contains(search),
                EmailTicket.body.contains(search),
                EmailTicket.customer_email.contains(search)
            )
        )

    tickets = query.order_by(EmailTicket.created_at.desc()).all()

    # Stats for the dashboard header cards
    total = EmailTicket.query.count()
    high_priority = EmailTicket.query.filter_by(priority="High").count()
    negative = EmailTicket.query.filter_by(sentiment="Negative").count()

    return render_template("dashboard.html", tickets=tickets,
                           total=total, high_priority=high_priority, negative=negative)

# --------------------------------------------------------------------------------
@app.route("/ticket/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def ticket_detail(ticket_id):
    ticket = EmailTicket.query.get_or_404(ticket_id)
    
    if request.method == "POST":
        ticket.ai_draft_reply = request.form.get("draft_reply", ticket.ai_draft_reply)
        ticket.status = request.form.get("status", ticket.status)
        db.session.commit()
        return redirect(url_for("ticket_detail", ticket_id=ticket.id))
        
    return render_template("ticket.html", ticket=ticket)

# --------------------------------------------------------------------------------
@app.route("/ticket/<int:ticket_id>/send", methods=["POST"])
@login_required
def send_ticket_reply(ticket_id):
    ticket = EmailTicket.query.get_or_404(ticket_id)
    
    try:
        reply_body = request.form.get("draft_reply", ticket.ai_draft_reply)
        # Prevent double 'Re:' tracking
        subject = f"Re: {ticket.subject}" if not ticket.subject.startswith("Re:") else ticket.subject
        
        send_reply(ticket.customer_email, subject, reply_body, ticket.gmail_id)
        
        send_action = request.form.get("send_action", "resolve")
        ticket.status = "Pending Customer" if send_action == "pending" else "Resolved"
        ticket.ai_draft_reply = reply_body
        db.session.commit()
    except Exception as e:
        logging.error(f"Send Reply Error: {e}")
        
    return redirect(url_for("ticket_detail", ticket_id=ticket.id))

# --------------------------------------------------------------------------------
@app.route("/ticket/<int:ticket_id>/delete", methods=["POST"])
@login_required
def delete_ticket(ticket_id):
    ticket = EmailTicket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    return redirect(url_for("dashboard"))

# --------------------------------------------------------------------------------
@app.route("/analytics")
@login_required
def analytics():

    total = EmailTicket.query.count()

    high_priority = EmailTicket.query.filter_by(priority="High").count()

    negative = EmailTicket.query.filter_by(sentiment="Negative").count()

    return render_template(
        "analytics.html",
        total=total,
        high_priority=high_priority,
        negative=negative
    )

# --------------------------------------------------------------------------------
def process_ticket_ai(ticket_id):
    with app.app_context():
        ticket = EmailTicket.query.get(ticket_id)

        if not ticket:
            return

        try:
            result = analyse_email(ticket.body)

            ticket.intent = result["intent"]
            ticket.sentiment = result["sentiment"]
            ticket.priority = result["priority"]
            ticket.ai_draft_reply = result["draft_reply"]

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            logging.error(f"AI Processing Error: {e}")

# --------------------------------------------------------------------------------
@app.route("/sync")
@app.route("/sync-gmail")
@login_required
def sync_emails():
    try:
        emails = fetch_unread_emails()
    except Exception as e:
        logging.error(f"Gmail fetch error: {e}")
        return redirect(url_for("dashboard"))

    new_tickets = []

    for email_data in emails:
        if not email_data.get("body"):
            continue

        existing = EmailTicket.query.filter_by(
            gmail_id=email_data["gmail_id"]
        ).first()
        if existing:
            continue

        new_ticket = EmailTicket(
            gmail_id=email_data["gmail_id"],
            customer_email=email_data.get("from") or email_data.get("sender", "Unknown"),
            subject=email_data.get("subject", "(No Subject)"),
            body=email_data["body"]
        )
        db.session.add(new_ticket)
        new_tickets.append(new_ticket)

    db.session.commit()

    for ticket in new_tickets[:MAX_AI_THREADS_PER_SYNC]:
        thread = threading.Thread(
            target=process_ticket_ai,
            args=(ticket.id,),
            daemon=True
        )
        thread.start()

    logging.info(f"Synced {len(new_tickets)} new tickets")
    return redirect(url_for("dashboard"))

# --------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)