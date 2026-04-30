# API Documentation

MailIQ integrates deeply with the Google Cloud ecosystem, relying specifically on the Gmail API and the Gemini API.

---

## 1. Google Gmail API (`services/gmail_service.py`)

The Gmail API is responsible for two-way communication: fetching new unread customer emails and sending replies out from the agent.

### Authentication (`get_gmail_service`)
*   **Method:** OAuth 2.0 via `google-auth` and `google-auth-oauthlib`.
*   **Scope:** `https://mail.google.com/`
*   **Storage:** The service checks for `GMAIL_TOKEN_JSON` and `GMAIL_CREDENTIALS_JSON` environment variables to support serverless deployment. If present, it writes them to temporary files at runtime.

### Fetching Emails (`fetch_unread_emails`)
*   **Endpoint:** `users().messages().list`
*   **Query:** `q="is:unread"`
*   **Action:** Fetches the ID and ThreadID of unread emails. It then immediately removes the `UNREAD` label via the `users().messages().modify` endpoint so the email is not ingested twice.
*   **Parsing:** Uses a recursive function to parse `multipart/alternative` payloads and base64-decode the raw text. It also runs regex cleanup to strip lengthy quoted replies.

### Sending Replies (`send_reply`)
*   **Action:** Constructs an RFC 2822 formatted email using Python's `email.message.EmailMessage` module. 
*   **Threading:** Critical to the integration, it sets the `In-Reply-To` and `References` headers and passes the `threadId` to Google, ensuring the customer sees the response grouped correctly in their inbox.

---

## 2. Google Gemini API (`services/ai_service.py`)

The Gemini API handles all natural language processing tasks.

### Authentication & Initialization
*   **Library:** `google-genai`
*   **Credentials:** Authenticates directly via the `GEMINI_API_KEY` environment variable.

### Content Generation (`analyse_email`)
*   **Model:** `gemini-2.5-flash-lite`
*   **Endpoint:** `client.models.generate_content`
*   **Input:** System prompt containing classification rules and the raw customer email.
*   **Output:** Returns a strictly formatted JSON string containing the extracted intent, sentiment, priority, and an auto-drafted reply.
