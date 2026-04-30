# System Architecture

MailIQ follows a classic Model-View-Controller (MVC) architectural pattern, powered by Flask, augmented with asynchronous background processing for AI tasks.

## High-Level Architecture Flow

1.  **Ingestion Layer:**
    *   `gmail_service.py` securely polls the Gmail API for new `UNREAD` emails.
    *   Raw email data (subject, sender, threadID, body) is parsed and cleaned using regex algorithms.
2.  **Data Persistence Layer:**
    *   The `models.py` file dictates the SQLAlchemy ORM mapping.
    *   Data is stored in PostgreSQL (in production) or SQLite (locally).
    *   Emails are mapped to a One-to-Many relational structure (`EmailTicket` -> `TicketMessage`).
3.  **Intelligence Layer (AI):**
    *   `ai_service.py` is invoked asynchronously via Python `threading` so it doesn't block the main Flask thread.
    *   Google Gemini processes the raw text to determine Sentiment, Intent, Priority, and generate Draft Replies.
4.  **Presentation Layer (Frontend):**
    *   The Flask Controller (`app.py`) serves Jinja2 HTML templates (`templates/`).
    *   The UI is styled using utility classes from Tailwind CSS and interactive components from Preline.
    *   Data is pulled dynamically using SQLAlchemy ORM queries based on the user's dashboard filters.

## Directory Structure

```text
/
├── app.py                  # Main Flask application and routing controller
├── models.py               # SQLAlchemy Database schemas
├── requirements.txt        # Python dependencies
├── .env                    # Secret environment variables
├── services/
│   ├── ai_service.py       # Gemini API integration
│   └── gmail_service.py    # Gmail API integration
├── templates/              # Jinja2 HTML Templates
│   ├── base.html           # Main layout wrapper
│   ├── dashboard.html      # Main ticket queue UI
│   ├── ticket.html         # Individual thread/chat UI
│   └── analytics.html      # Data visualization UI
└── docs/                   # System Documentation
```
