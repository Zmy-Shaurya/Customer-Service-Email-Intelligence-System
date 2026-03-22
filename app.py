from flask import Flask, render_template, request, redirect, url_for
from models import db, EmailTicket
import threading
from services.ai_service import analyse_email
import logging
from dotenv import load_dotenv
from services.gmail_service import fetch_unread_emails

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

db.init_app(app)

with app.app_context():
    db.create_all()

# --------------------------------------------------------------------------------
@app.route('/', methods=["GET","POST"])
def home():
    if request.method == "POST":
        customer_email = request.form.get("customer_email", "").strip()
        subject = request.form.get("subject", "").strip()
        body = request.form.get("body", "").strip()

        if not customer_email or not subject or not body:
            logging.error("Missing form data in home POST request")
            return redirect(url_for("home"))

        new_ticket = EmailTicket(
            customer_email=customer_email,
            subject=subject,
            body=body
        )
        db.session.add(new_ticket)
        db.session.commit()

        thread = threading.Thread(
            target=process_ticket_ai,
            args=(new_ticket.id,),
            daemon=True
        )
        thread.start()

        logging.info(f"New ticket created with ID: {new_ticket.id}")
        return redirect(url_for("dashboard"))

    return render_template("index.html")

# --------------------------------------------------------------------------------
@app.route('/dashboard')
def dashboard():
    query = EmailTicket.query

    priority = request.args.get("priority")
    if priority:
        query = query.filter(EmailTicket.priority.ilike(priority))

    search = request.args.get("search")
    if search:
        query = query.filter(EmailTicket.subject.contains(search))

    tickets = query.order_by(EmailTicket.created_at.desc()).all()

    return render_template("dashboard.html", tickets=tickets)

# --------------------------------------------------------------------------------
@app.route("/analytics")
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