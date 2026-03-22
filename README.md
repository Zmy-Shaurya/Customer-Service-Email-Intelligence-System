# 📧 Customer Service Email Intelligence System

An AI-powered customer support system that automatically fetches emails from Gmail, analyzes them using LLMs, prioritizes tickets, and generates smart response drafts — all through a clean dashboard.

---

## 🚀 Features

* 📥 **Gmail Integration (OAuth2)**

  * Fetch unread emails directly from Gmail inbox
  * Convert emails into support tickets automatically

* 🧠 **AI-Powered Email Analysis**

  * Intent classification (Refund, Complaint, Inquiry, etc.)
  * Sentiment detection (Positive, Neutral, Negative)
  * Priority assignment (Low / Medium / High)
  * Auto-generated draft replies

* 📊 **Dashboard & Ticket Management**

  * View all tickets in a centralized dashboard
  * Search and filter by priority and subject
  * Human-in-the-loop editing of AI replies

* 📈 **Analytics**

  * Total tickets
  * High priority issues
  * Negative sentiment tracking

* ⚡ **Asynchronous Processing**

  * Background AI processing using threads
  * Fast UI with non-blocking operations

---

## 🧠 System Architecture

```
Gmail API  →  Email Fetching Layer
                ↓
Flask Backend  → Ticket Creation
                ↓
Background Thread → AI Processing (Gemini)
                ↓
Database (SQLite)
                ↓
Dashboard UI (Jinja Templates)
```

---

## 🛠 Tech Stack

* **Backend:** Flask, Flask-SQLAlchemy
* **Database:** SQLite
* **AI:** Google Gemini API
* **APIs:** Gmail API (OAuth2)
* **Frontend:** HTML, CSS (Jinja Templates)

---

## 📂 Project Structure

```
customer-email-ai/
│
├── app.py
├── models.py
├── services/
│   ├── ai_service.py
│   └── gmail_service.py
│
├── templates/
├── static/
├── instance/
│   └── app.db
│
├── docs/
├── requirements.txt
├── README.md
└── .env
```

---

## ⚙️ Installation & Setup

### 1. Clone the repository

```
git clone https://github.com/Zmy-Shaurya/Customer-Service-Email-Intelligence-System
cd Customer-Service-Email-Intelligence-System
```

---

### 2. Create virtual environment

```
python -m venv .venv
source .venv/bin/activate   # Mac/Linux
.venv\Scripts\activate      # Windows
```

---

### 3. Install dependencies

```
pip install -r requirements.txt
```

---

### 4. Setup environment variables

Create a `.env` file:

```
GEMINI_API_KEY=your_api_key_here
```

---

### 5. Setup Gmail API

* Enable Gmail API in Google Cloud Console
* Download `credentials.json`
* Place it in the root directory

⚠️ **Important:** Do NOT commit `credentials.json` or `token.json`

---

### 6. Run the app

```
python app.py
```

Open:

```
http://127.0.0.1:5000
```

---

## 🔄 How It Works

1. User submits email OR clicks "Sync Gmail"
2. Emails are fetched from Gmail
3. Tickets are created in the database
4. Background thread processes email using AI
5. Dashboard updates with:

   * intent
   * sentiment
   * priority
   * draft reply

---

## 🧪 Example Use Cases

* Customer support automation
* Email triaging system
* AI-assisted helpdesk tools
* Internal support dashboards

---

## ⚠️ Known Limitations

* No user authentication (MVP)
* No real-time email sync (manual trigger)
* Basic UI (can be improved with React/Tailwind)

---

## 🚀 Future Improvements

* User authentication (Flask-Login)
* Gmail auto-reply feature
* Real-time updates using WebSockets
* Advanced analytics dashboard (charts, trends)
* Multi-user support system

---

## 👨‍💻 Contributors

* Shaurya Pratap Singh
* Sukanya Budhiraja
* Dishant Shridhar

---

## 📜 License

This project is for educational purposes.

---

## ⭐ Acknowledgements

* Google Gemini API
* Gmail API
* Flask Community

---
