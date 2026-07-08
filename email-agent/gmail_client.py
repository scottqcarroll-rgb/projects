import os
import json
import base64
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.api_core.client_options import ClientOptions
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOKEN_FILE = 'token.json'
CREDENTIALS_FILE = 'credentials.json'


def _load_client_config():
    """Load client_id/client_secret/token_uri from credentials.json."""
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(
            f"[ERROR] {CREDENTIALS_FILE} not found.\n"
            "Please download it from Google Cloud Console:\n"
            "1. Go to https://console.cloud.google.com\n"
            "2. Create a project and enable Gmail API\n"
            "3. Create OAuth 2.0 credentials (Desktop app)\n"
            "4. Download and save as credentials.json in this directory"
        )
    with open(CREDENTIALS_FILE) as f:
        cfg = json.load(f)
    info = cfg.get('installed') or cfg.get('web') or {}
    return {
        'client_id': info.get('client_id'),
        'client_secret': info.get('client_secret'),
        'token_uri': info.get('token_uri', 'https://oauth2.googleapis.com/token'),
    }


def get_authenticated_service():
    """Authenticate and return Gmail API service.

    Works headless: loads the refresh token from token.json and the
    client secrets from credentials.json, then refreshes the access
    token without a browser. Falls back to interactive flow only when
    no token.json exists (run once locally to bootstrap).
    """
    client = _load_client_config()

    creds = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            token_data = json.load(f)
        # Force expiry into the past so a refresh is always attempted,
        # avoiding use of a long-stale access token.
        creds = Credentials(
            token=token_data.get('access_token') or token_data.get('token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=client['token_uri'],
            client_id=client['client_id'],
            client_secret=client['client_secret'],
            scopes=SCOPES,
            expiry=datetime.utcnow() - timedelta(days=1),
        )

    if creds and creds.refresh_token:
        # Remove forced past expiry that causes invalid_grant errors
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    elif creds is None:
        # No token yet — bootstrap interactively (needs a browser locally).
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    else:
        raise RuntimeError(
            "Gmail token.json has no refresh_token; delete it and re-run "
            "the interactive OAuth flow locally to regenerate."
        )

    return build('gmail', 'v1', credentials=creds)


def fetch_recent_emails(service, hours=24, max_results=50):
    """Fetch emails from the last N hours."""
    try:
        query = f'newer_than:{hours}h in:inbox'
        results = service.users().messages().list(
            userId='me',
            q=query,
            maxResults=max_results
        ).execute()

        messages = results.get('messages', [])

        if not messages:
            return []

        emails = []
        for msg in messages:
            try:
                msg_data = service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='full'
                ).execute()

                headers = msg_data['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

                snippet = msg_data.get('snippet', '')[:200]

                emails.append({
                    'id': msg['id'],
                    'from': sender,
                    'subject': subject,
                    'snippet': snippet,
                    'date': date,
                    'source': 'Gmail',
                    'is_unread': 'UNREAD' in msg_data.get('labelIds', [])
                })
            except Exception as e:
                print(f"[WARN] Error processing message {msg['id']}: {e}")
                continue

        return emails

    except Exception as e:
        print(f"[ERROR] Error fetching emails: {e}")
        raise


def delete_email(service, message_id):
    """Delete (trash) an email from Gmail."""
    try:
        service.users().messages().trash(userId='me', id=message_id).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete email {message_id}: {e}")
        raise


if __name__ == '__main__':
    try:
        service = get_authenticated_service()
        emails = fetch_recent_emails(service)
        print(f"[OK] Fetched {len(emails)} emails")
        for email in emails[:3]:
            print(f"  - {email['from']}: {email['subject']}")
    except Exception as e:
        print(f"[ERROR] Error: {e}")
