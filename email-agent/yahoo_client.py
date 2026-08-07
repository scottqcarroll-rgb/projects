import os
import imaplib
import email
from datetime import datetime, timedelta
from pathlib import Path

# Import OAuth2 implementation
from yahoo_oauth2 import (
    get_yahoo_imap_connection,
    fetch_recent_emails_oauth2 as fetch_recent_emails_impl,
    delete_email_oauth2 as delete_email_impl,
)

YAHOO_IMAP_HOST = 'imap.mail.yahoo.com'
YAHOO_IMAP_PORT = 993


def load_yahoo_credentials():
    """Load Yahoo email and password from .env file (kept for backward compat)."""
    yahoo_email = os.environ.get('YAHOO_EMAIL')
    yahoo_password = os.environ.get('YAHOO_PASSWORD')

    if not yahoo_email or not yahoo_password:
        # Try reading from .env file
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    if line.startswith('YAHOO_EMAIL='):
                        yahoo_email = line.split('=', 1)[1].strip()
                    elif line.startswith('YAHOO_PASSWORD='):
                        yahoo_password = line.split('=', 1)[1].strip()

    if not yahoo_email or not yahoo_password:
        raise ValueError(
            "[ERROR] Yahoo credentials not found.\n"
            "Set YAHOO_EMAIL and YAHOO_PASSWORD in .env:\n"
            "YAHOO_EMAIL=youremail@bellsouth.net\n"
            "YAHOO_PASSWORD=your-regular-password"
        )

    return yahoo_email, yahoo_password


def get_authenticated_service():
    """Authenticate with Yahoo IMAP using OAuth2 and return connection."""
    try:
        yahoo_email, _ = load_yahoo_credentials()
        # Use OAuth2 connection
        return get_yahoo_imap_connection(yahoo_email)

    except Exception as e:
        raise ValueError(f"[ERROR] Yahoo OAuth2 auth failed: {e}")


def fetch_recent_emails(service, hours=24, max_results=50):
    """Fetch recent emails from Yahoo IMAP."""
    return fetch_recent_emails_impl(service, hours, max_results)


def delete_email(conn, msg_id):
    """Delete an email from Yahoo IMAP by marking it as deleted and expunging."""
    return delete_email_impl(conn, msg_id)


if __name__ == '__main__':
    try:
        conn = get_authenticated_service()
        emails = fetch_recent_emails(conn, hours=24, max_results=10)
        print(f"[OK] Fetched {len(emails)} Yahoo emails")
        for email_data in emails[:3]:
            print(f"  - {email_data['from']}: {email_data['subject']}")
        conn.close()
    except Exception as e:
        print(f"[ERROR] Error: {e}")
