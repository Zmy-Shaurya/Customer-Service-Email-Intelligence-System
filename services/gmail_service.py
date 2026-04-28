import base64
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from email.message import EmailMessage

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send"
]


def get_gmail_service():
    creds = None
    token_path = Path("token.json")
    credentials_path = Path("credentials.json")

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except RefreshError:
                flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
                creds = flow.run_local_server(port=0)
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def fetch_unread_emails():
    try:
        service = get_gmail_service()

        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            q="is:unread"
        ).execute()

        messages = results.get("messages", [])
        
        if not messages:
            print("No unread emails found.")
            return []  # return empty list, not None

        emails = []

        for msg in messages[:10]:
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full"
            ).execute()

            headers = msg_data["payload"]["headers"]
            subject = next((h["value"] for h in headers if h["name"] == "Subject"), "No Subject")
            sender = next((h["value"] for h in headers if h["name"] == "From"), "Unknown")

            def extract_body(payload_part):
                if "parts" in payload_part:
                    for part in payload_part["parts"]:
                        if part["mimeType"] == "text/plain":
                            data = part["body"].get("data", "")
                            return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                        elif "parts" in part:
                            nested_body = extract_body(part)
                            if nested_body:
                                return nested_body
                elif "body" in payload_part and payload_part["body"].get("data"):
                    data = payload_part["body"].get("data", "")
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                return ""

            body = extract_body(payload)
            
            # Strip out quoted replies (e.g., "On Mon, 27 Apr... wrote:")
            def strip_quoted_text(text):
                import re
                pattern1 = r"(?i)(?:\r?\n)?On\s.*?wrote:\s*(?:\r?\n)?"
                pattern2 = r"(?i)(?:\r?\n)?-----Original Message-----"
                pattern3 = r"(?i)(?:\r?\n)?From:\s"
                
                for pattern in [pattern1, pattern2, pattern3]:
                    parts = re.split(pattern, text, maxsplit=1)
                    if len(parts) > 1:
                        text = parts[0]
                return text.strip()
                
            body = strip_quoted_text(body)

            emails.append({
                "gmail_id": msg["id"],
                "thread_id": msg_data.get("threadId"),
                "sender": sender,
                "subject": subject,
                "body": body
            })

            service.users().messages().modify(
                userId="me",
                id=msg["id"],
                body={"removeLabelIds": ["UNREAD"]}
            ).execute()

        return emails

    except Exception as e:
        print("Gmail fetch error:", e)
        return []  # always return a list, never None

def send_reply(to_email, subject, body, gmail_id=None):
    try:
        service = get_gmail_service()
        message = EmailMessage()
        message.set_content(body)
        message["To"] = to_email
        message["Subject"] = subject

        thread_id = None
        if gmail_id:
            try:
                original_msg = service.users().messages().get(userId='me', id=gmail_id, format='metadata', metadataHeaders=['Message-ID']).execute()
                thread_id = original_msg.get('threadId')
                headers = original_msg.get('payload', {}).get('headers', [])
                message_id = next((h['value'] for h in headers if h['name'].upper() == 'MESSAGE-ID'), None)
                
                if message_id:
                    message["In-Reply-To"] = message_id
                    message["References"] = message_id
            except Exception as e:
                print("Failed to fetch original metadata for threading:", e)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        
        if thread_id:
            create_message["threadId"] = thread_id

        send_message = service.users().messages().send(userId="me", body=create_message).execute()
        return send_message
    except Exception as e:
        print("Gmail send error:", e)
        raise e