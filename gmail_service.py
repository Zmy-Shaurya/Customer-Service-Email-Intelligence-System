import base64
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


def get_gmail_service():
    creds = None
    token_path = Path("token.json")
    credentials_path = Path("credentials.json")

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
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

            body = ""
            payload = msg_data["payload"]

            if "parts" in payload:
                for part in payload["parts"]:
                    if part["mimeType"] == "text/plain":
                        data = part["body"].get("data", "")
                        body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                        break
            elif "body" in payload:
                data = payload["body"].get("data", "")
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

            emails.append({
                "gmail_id": msg["id"],
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