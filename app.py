from flask import Flask, render_template, request, redirect, url_for, flash
from models import db, EmailTicket, User, TicketMessage
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
        body = request.form.get("email_body", "").strip()

        if not customer_email or not subject or not body:
            logging.error("Missing form data in new-ticket POST request")
            return redirect(url_for("new_ticket"))

        ticket = EmailTicket(
            customer_email=customer_email,
            subject=subject
        )
        db.session.add(ticket)
        db.session.flush() # get ticket.id
        
        msg = TicketMessage(ticket_id=ticket.id, sender="customer", body=body)
        db.session.add(msg)
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
                EmailTicket.customer_email.contains(search),
                EmailTicket.messages.any(TicketMessage.body.contains(search))
            )
        )

    tickets = query.order_by(EmailTicket.created_at.desc()).all()

    # Stats for the dashboard header cards (case-insensitive to match AI output)
    total = EmailTicket.query.count()
    high_priority = EmailTicket.query.filter(EmailTicket.priority.ilike("high")).count()
    negative = EmailTicket.query.filter(EmailTicket.sentiment.ilike("negative")).count()

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
        
        # Send via Gmail
        send_response = send_reply(ticket.customer_email, subject, reply_body, ticket.gmail_id)
        
        # If we got a threadId back and we didn't have one, save it
        if send_response and send_response.get("threadId") and not ticket.gmail_thread_id:
            ticket.gmail_thread_id = send_response.get("threadId")
            
        # Append message to thread
        msg = TicketMessage(ticket_id=ticket.id, sender="agent", body=reply_body)
        db.session.add(msg)
        
        send_action = request.form.get("send_action", "resolve")
        ticket.status = "Pending Customer" if send_action == "pending" else "Resolved"
        ticket.ai_draft_reply = "" # clear draft since sent
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
    high_priority = EmailTicket.query.filter(EmailTicket.priority.ilike("high")).count()
    negative = EmailTicket.query.filter(EmailTicket.sentiment.ilike("negative")).count()

    # Status breakdown
    status_new = EmailTicket.query.filter(EmailTicket.status.ilike("new")).count()
    status_in_progress = EmailTicket.query.filter(EmailTicket.status.ilike("in progress")).count()
    status_pending = EmailTicket.query.filter(EmailTicket.status.ilike("pending customer")).count()
    status_resolved = EmailTicket.query.filter(EmailTicket.status.ilike("resolved")).count()

    # Priority breakdown
    priority_high = high_priority
    priority_medium = EmailTicket.query.filter(EmailTicket.priority.ilike("medium")).count()
    priority_low = EmailTicket.query.filter(EmailTicket.priority.ilike("low")).count()

    # Sentiment breakdown
    sentiment_positive = EmailTicket.query.filter(EmailTicket.sentiment.ilike("positive")).count()
    sentiment_neutral = EmailTicket.query.filter(EmailTicket.sentiment.ilike("neutral")).count()
    sentiment_negative = negative

    # Intent breakdown — top intents
    all_tickets = EmailTicket.query.all()
    intent_counts = {}
    for t in all_tickets:
        intent_key = (t.intent or "Unknown").strip().title()
        intent_counts[intent_key] = intent_counts.get(intent_key, 0) + 1
    # Sort by count descending, take top 6
    top_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:6]
    intent_labels = [i[0] for i in top_intents]
    intent_values = [i[1] for i in top_intents]

    # Resolution rate
    resolution_rate = round((status_resolved / total * 100), 1) if total > 0 else 0

    # Unique customers
    unique_customers = db.session.query(EmailTicket.customer_email).distinct().count()

    return render_template(
        "analytics.html",
        total=total,
        high_priority=high_priority,
        negative=negative,
        status_new=status_new,
        status_in_progress=status_in_progress,
        status_pending=status_pending,
        status_resolved=status_resolved,
        priority_high=priority_high,
        priority_medium=priority_medium,
        priority_low=priority_low,
        sentiment_positive=sentiment_positive,
        sentiment_neutral=sentiment_neutral,
        sentiment_negative=sentiment_negative,
        intent_labels=intent_labels,
        intent_values=intent_values,
        resolution_rate=resolution_rate,
        unique_customers=unique_customers
    )

# --------------------------------------------------------------------------------
def process_ticket_ai(ticket_id):
    with app.app_context():
        ticket = EmailTicket.query.get(ticket_id)

        if not ticket:
            return

        try:
            # We analyse the latest message from the customer
            latest_msg = TicketMessage.query.filter_by(ticket_id=ticket.id, sender="customer").order_by(TicketMessage.created_at.desc()).first()
            if not latest_msg:
                return
            
            result = analyse_email(latest_msg.body)

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
    updated_tickets = []

    for email_data in emails:
        if not email_data.get("body"):
            continue

        existing_gmail_msg = EmailTicket.query.filter_by(
            gmail_id=email_data["gmail_id"]
        ).first()
        if existing_gmail_msg:
            continue

        # Try to find existing thread
        existing_thread = None
        if email_data.get("thread_id"):
            existing_thread = EmailTicket.query.filter_by(gmail_thread_id=email_data["thread_id"]).first()
            
        if existing_thread:
            # Append to existing thread
            msg = TicketMessage(ticket_id=existing_thread.id, sender="customer", body=email_data["body"])
            db.session.add(msg)
            # Re-open the ticket if it was resolved
            existing_thread.status = "In Progress"
            # We don't have the message ID yet, flush to get it if needed, but not strictly necessary here.
            updated_tickets.append(existing_thread)
        else:
            # Create new ticket
            new_ticket = EmailTicket(
                gmail_id=email_data["gmail_id"],
                gmail_thread_id=email_data.get("thread_id"),
                customer_email=email_data.get("from") or email_data.get("sender", "Unknown"),
                subject=email_data.get("subject", "(No Subject)")
            )
            db.session.add(new_ticket)
            db.session.flush() # get ID
            
            msg = TicketMessage(ticket_id=new_ticket.id, sender="customer", body=email_data["body"])
            db.session.add(msg)
            new_tickets.append(new_ticket)

    db.session.commit()

    # Process AI for totally new tickets
    for ticket in new_tickets[:MAX_AI_THREADS_PER_SYNC]:
        thread = threading.Thread(
            target=process_ticket_ai,
            args=(ticket.id,),
            daemon=True
        )
        thread.start()
        
    # Also re-process AI for updated tickets to get a new draft based on newest message
    for ticket in updated_tickets[:MAX_AI_THREADS_PER_SYNC]:
        thread = threading.Thread(
            target=process_ticket_ai,
            args=(ticket.id,),
            daemon=True
        )
        thread.start()

    logging.info(f"Synced {len(new_tickets)} new tickets and updated {len(updated_tickets)} threads")
    return redirect(url_for("dashboard"))

# --------------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)