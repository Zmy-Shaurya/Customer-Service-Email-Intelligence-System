from flask import Flask, render_template, request, redirect, url_for
from models import db, EmailTicket

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/', method=["GET","POST"])
def home():
    if request.method=="POST":
        customer_email = request.form["customer_email"]
        subject = request.form["subject"]
        body = request.form["body"]

        new_ticket = EmailTicket(
            customer_email=customer_email,
            subject=subject,
            body=body
        )
        db.session.add(new_ticket)
        db.session.commit()
        return redirect(url_for("dashboard"))
    
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)