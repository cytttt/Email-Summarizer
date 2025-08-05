import base64
from datetime import datetime
from google.cloud import storage
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import os
from utils import log_info, clean_email_text
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
# Gmail scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

GCS_BUCKET = os.getenv("GCS_BUCKET_NAME")
TOKEN_GCS = os.getenv("GOOGLE_TOKEN_PATH")
TOKEN_LOCAL = "/tmp/" + TOKEN_GCS if TOKEN_GCS else ""
MAX_EMAILS = os.getenv("MAX_EMAILS")

def decode_part(part):
    """
    Decodes base64-encoded email parts.
    """
    data = part.get("body", {}).get("data", "")
    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore") if data else ""

def extract_email_body(payload):
    """
    Extracts the body of an email from the Gmail API payload.
        Parse texts, htmls and remove images
        Since:
            1. html syntax is redundant and wasting tokens for text models.
            2. images' urls are mostly meaningless for text models.
    return:
        str, cleaned email body
    """
    body = ""
    html = ""
    
    def process_parts(parts):
        nonlocal body, html
        for part in parts:
            mime = part.get("mimeType", "")
            if part.get("parts"):  # nested parts
                process_parts(part["parts"])
            elif mime == "text/plain":
                body = decode_part(part)
            elif mime == "text/html":
                raw_html = decode_part(part)
                html = raw_html
                soup = BeautifulSoup(raw_html, "html.parser")
                body = soup.get_text(separator="\n", strip=True)

    if "parts" in payload:
        process_parts(payload["parts"])
    else:
        mime = payload.get("mimeType", "")
        raw = decode_part(payload)
        if mime == "text/html":
            html = raw
            soup = BeautifulSoup(raw, "html.parser")
            body = soup.get_text(separator="\n", strip=True)
        else:
            body = raw

    return clean_email_text(body)

def download_token():
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(TOKEN_GCS)
    blob.download_to_filename(TOKEN_LOCAL)

def upload_token():
    client = storage.Client()
    bucket = client.bucket(GCS_BUCKET)
    blob = bucket.blob(TOKEN_GCS)
    blob.upload_from_filename(TOKEN_LOCAL)

def get_gmail_service(local_mode=False):
    """
    Get Gmail service.
    """
    if local_mode:
        log_info("[GmailClient] Using local token.json and credentials.json")
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open("token.json", "w") as f:
                f.write(creds.to_json())

    else:
        log_info("[GmailClient] Using GCS token")
        if not os.path.exists(TOKEN_LOCAL):
            download_token()

        creds = Credentials.from_authorized_user_file(TOKEN_LOCAL, SCOPES)

        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(TOKEN_LOCAL, "w") as f:
                f.write(creds.to_json())
            upload_token()

    from googleapiclient.discovery import build
    return build("gmail", "v1", credentials=creds)

def fetch_recent_emails(interval: int, local_mode=False):
    """
    Fetches unread emails in given interval.

    return:
        list of dict, each dict contains email id, subject, from, body
    """
    service = get_gmail_service(local_mode)
    query = f"newer_than:{interval}h is:unread"

    results = service.users().messages().list(userId='me', q=query, maxResults=MAX_EMAILS).execute()
    messages = results.get('messages', [])

    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
        payload = msg_data['payload']

        subject = ""
        sender = ""
        for header in payload.get('headers', []):
            if header['name'].lower() == 'subject':
                subject = header['value']
            elif header['name'].lower() == 'from':
                sender = header['value']

        
        body = extract_email_body(payload)

        emails.append({
            "id": msg['id'],
            "subject": subject,
            "from": sender,
            "body": body
        })

    return emails
