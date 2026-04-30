# MailIQ: Customer Service Email Intelligence System 🚀

**🔴 Live Demo:** [https://customer-service-email-intelligence.onrender.com/](https://customer-service-email-intelligence.onrender.com/)

MailIQ is an intelligent, automated customer support helpdesk built with Python and Flask. It seamlessly integrates with the **Gmail API** to ingest customer emails and utilizes **Google Gemini 2.5 Flash** to automatically analyze sentiment, detect intent, and draft context-aware replies before a human agent even opens the ticket.

---

## ✨ Key Features

*   **✉️ Automated Gmail Ingestion:** Connects directly to a support Gmail account to pull in new unread emails and thread replies automatically.
*   **🧠 AI-Powered Triaging:** Uses Google's Gemini LLM to analyze incoming messages and assign:
    *   **Intent:** (Refund, Technical Support, Delivery Issue, General Inquiry)
    *   **Sentiment:** (Positive, Neutral, Negative)
    *   **Priority:** Auto-escalates negative or urgent tickets to High Priority.
*   **📝 Auto-Drafted Replies:** Gemini automatically generates a professional, context-aware draft reply based on the customer's email history.
*   **💬 Threaded Conversations:** Chat-like interface that groups back-and-forth emails between the customer and the support agent into a single unified ticket view.
*   **📊 Analytics Dashboard:** Visual insights into ticket volumes, customer sentiment trends, and team resolution rates.
*   **☁️ Production Ready:** Fully configured to run on serverless/ephemeral cloud platforms like Render with PostgreSQL.

---

## 🛠️ Technology Stack

*   **Backend:** Python 3, Flask, SQLAlchemy, Gunicorn
*   **Frontend:** HTML5, Tailwind CSS, Preline UI Components
*   **Database:** SQLite (Local Development) / PostgreSQL (Production)
*   **APIs & AI:** Google Gmail API (`google-api-python-client`), Google Gemini AI (`google-genai`)

---

## 🚀 Local Development Setup

### 1. Prerequisites
Ensure you have Python 3.10+ installed and a Google Cloud Console account set up with the Gmail API enabled. You will need to download your OAuth 2.0 Client ID as `credentials.json`.

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/Customer-Service-Email-Intelligence-System.git
cd Customer-Service-Email-Intelligence-System

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file in the root directory and add your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_flask_secret_key
```

### 4. Database Initialization & Run
```bash
# The application automatically initializes the SQLite database on first run.
python app.py
```
Open `http://127.0.0.1:5000` in your browser.

---

## 🌍 Cloud Deployment (Render / Vercel)

This application is fully optimized for cloud deployments requiring ephemeral storage solutions. Instead of relying on local files for Google Authentication, the system dynamically generates `token.json` from Environment Variables upon boot.

For a comprehensive step-by-step guide on deploying to Render using a free PostgreSQL database, please see our [Deployment Guide](DEPLOYMENT_GUIDE.md).

---

## 🎓 Academic / Team Reference

If you are a team member preparing for a project defense or technical examination on this system, please review the [Team Exam Prep Guide](TEAM_EXAM_PREP_GUIDE.md) for a detailed breakdown of the system architecture and designated roles.
