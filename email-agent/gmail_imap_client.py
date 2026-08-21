#!/usr/bin/env python3
"""
Gmail IMAP Client using App Password
Simple, no OAuth2 - uses IMAP with Gmail App Password directly.
"""

import os
import imaplib
import email
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

GMAIL_IMAP_HOST = 'imap.gmail.com'
GMAIL_IMAP_PORT = 993


def load_gmail_credentials() -> tuple[str, str]:
    """Load Gmail email and app password from .env file."""
    gmail_email = os.environ.get('GMAIL_EMAIL')
    gmail_app_password = os.environ.get('GMAIL_APP_PASSWORD')

    if not gmail_email or not gmail_app_password:
        # Try reading from .env file
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('GMAIL_EMAIL='):
                        gmail_email = line.split('=', 1)[1].strip()
                    elif line.startswith('GMAIL_APP_PASSWORD='):
                        gmail_app_password = line.split('=', 1)[1].strip()

    if not gmail_email or not gmail_app_password:
        raise ValueError(
            "[ERROR] Gmail credentials not found.\n"
            "Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env:\n"
            "GMAIL_EMAIL=your_email@gmail.com\n"
            "GMAIL_APP_PASSWORD=your-16-char-app-password\n\n"
            "To create an App Password:\n"
            "1. Enable 2FA on your Google Account\n"
            "2. Go to https://myaccount.google.com/apppasswords\n"
            "3. Create app password for 'Mail'\n"
            "4. Use the 16-character password (no spaces)"
        )

    return gmail_email, gmail_app_password


def get_authenticated_service() -> imaplib.IMAP4_SSL:
    """
    Authenticate with Gmail IMAP using App Password.
    Returns connected and authenticated IMAP4_SSL object.
    """
    gmail_email, gmail_app_password = load_gmail_credentials()

    conn = imaplib.IMAP4_SSL(GMAIL_IMAP_HOST, GMAIL_IMAP_PORT)

    # Login with app password
    try:
        conn.login(gmail_email, gmail_app_password)
    except imaplib.IMAP4.error as e:
        raise ValueError(f"[ERROR] Gmail IMAP login failed: {e}\n"
                         "Verify your App Password is correct (16 chars, no spaces).")

    print(f"[OK] Gmail IMAP authenticated as {gmail_email} via App Password")
    return conn


def fetch_recent_emails(service: imaplib.IMAP4_SSL, hours: int = 24, max_results: int = 50) -> list:
    """Fetch recent emails using existing authenticated connection."""
    try:
        service.select("INBOX")

        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.strftime("%d-%b-%Y")

        status, msg_ids = service.search(None, f"SINCE {cutoff_str}")
        if status != "OK":
            return []

        msg_list = msg_ids[0].split()[-max_results:]
        if not msg_list:
            return []

        emails = []
        for msg_id in msg_list:
            try:
                status, msg_data = service.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                msg_bytes = msg_data[0][1]
                msg_obj = email.message_from_bytes(msg_bytes)

                subject = msg_obj.get("Subject", "No Subject")
                from_addr = msg_obj.get("From", "Unknown")
                date = msg_obj.get("Date", "")
                message_id = msg_obj.get("Message-ID", "")

                # Extract snippet
                snippet = ""
                if msg_obj.is_multipart():
                    for part in msg_obj.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                payload = part.get_payload(decode=True)
                                if isinstance(payload, bytes):
                                    snippet = payload.decode("utf-8", errors="ignore")
                                else:
                                    snippet = str(payload)
                                break
                            except:
                                continue
                else:
                    try:
                        payload = msg_obj.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            snippet = payload.decode("utf-8", errors="ignore")
                        else:
                            snippet = str(payload)
                    except:
                        snippet = str(msg_obj.get_payload())

                snippet = snippet.replace("\r\n", " ").replace("\n", " ").strip()[:200]

                # Check unread
                status, flags = service.fetch(msg_id, "(FLAGS)")
                is_unread = False
                if status == "OK" and flags:
                    flag_data = flags[0]
                    if isinstance(flag_data, bytes):
                        is_unread = b"\\Seen" not in flag_data
                    else:
                        is_unread = "\\Seen" not in str(flag_data)

                emails.append({
                    "id": msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                    "from": from_addr,
                    "subject": subject,
                    "snippet": snippet,
                    "date": date,
                    "message_id": message_id,
                    "is_unread": is_unread,
                    "source": "Gmail",
                })
            except Exception as e:
                print(f"[WARN] Error processing message {msg_id}: {e}")
                continue

        return emails

    except Exception as e:
        print(f"[ERROR] Error fetching Gmail emails: {e}")
        raise


def delete_email(service: imaplib.IMAP4_SSL, msg_id) -> bool:
    """Delete email using existing authenticated connection."""
    try:
        msg_id_str = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
        status = service.store(msg_id_str, "+FLAGS", "\\Deleted")
        if status[0] != "OK":
            raise ValueError(f"Failed to mark for deletion: {status}")
        service.expunge()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete email {msg_id}: {e}")
        raise


if __name__ == "__main__":
    # Test the IMAP connection
    try:
        print("[*] Testing Gmail IMAP connection with App Password...")
        conn = get_authenticated_service()
        emails = fetch_recent_emails(conn, hours=24, max_results=5)
        print(f"[OK] Fetched {len(emails)} emails")
        for e in emails[:3]:
            print(f"  - {e['from']}: {e['subject'][:60]}")
        conn.close()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()