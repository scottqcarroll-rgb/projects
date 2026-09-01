#!/usr/bin/env python3
"""
Daily Email Cleanup Cron Job
- Fetches emails from Yahoo (and Gmail)
- Classifies them using rule-based classifier
- Deletes emails classified as 'not_important' (junk)
- Sends Telegram summary of what was deleted
"""

import os
import sys
import json
import requests
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yahoo_client import get_authenticated_service as get_yahoo_service, fetch_recent_emails as fetch_yahoo_emails
from gmail_imap_client import get_authenticated_service as get_gmail_service, fetch_recent_emails as fetch_gmail_emails, delete_email as delete_gmail_email
from email_classifier import classify_emails


# Telegram Bot credentials
TELEGRAM_BOT_TOKEN = "8773175847:***"
TELEGRAM_CHAT_ID = "7542619200"

# API server endpoint
API_BASE = "http://localhost:5050"


def send_telegram(message: str):
    """Send message to Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
        response = requests.post(url, json=data, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"[WARN] Telegram send failed: {e}")
        return False


def delete_via_api(email_id: str, source: str) -> bool:
    """Delete email via API server"""
    try:
        response = requests.post(
            f"{API_BASE}/delete",
            json={"id": email_id, "source": source},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] Delete API call failed for {source} {email_id}: {e}")
        return False


def main():
    print(f"[{datetime.now()}] Starting daily email cleanup...")
    
    all_emails = []
    
    # Fetch Yahoo emails
    try:
        print("[*] Fetching Yahoo emails...")
        yahoo_service = get_yahoo_service()
        yahoo_emails = fetch_yahoo_emails(yahoo_service, hours=24, max_results=100)
        print(f"[*] Fetched {len(yahoo_emails)} Yahoo emails")
        all_emails.extend(yahoo_emails)
        yahoo_service.close()
    except Exception as e:
        print(f"[WARN] Yahoo fetch failed: {e}")
    
    # Fetch Gmail emails
    gmail_service = None
    try:
        print("[*] Fetching Gmail emails...")
        gmail_service = get_gmail_service()
        gmail_emails = fetch_gmail_emails(gmail_service, hours=24, max_results=100)
        print(f"[*] Fetched {len(gmail_emails)} Gmail emails")
        all_emails.extend(gmail_emails)
    except Exception as e:
        print(f"[WARN] Gmail fetch failed: {e}")
    
    if not all_emails:
        print("[OK] No emails to process")
        send_telegram("📧 Daily Email Cleanup — No emails found today")
        return
    
    # Classify all emails
    print(f"[*] Classifying {len(all_emails)} emails...")
    classifications = classify_emails(all_emails)
    
    # Merge classifications
    emails_with_class = []
    for email in all_emails:
        classification = next((c for c in classifications if c.get('id') == email['id']), None)
        if classification:
            email.update(classification)
        else:
            email['importance'] = 'not_important'
            email['reason'] = 'Classification unavailable'
        emails_with_class.append(email)
    
    # Separate junk (not_important) from important
    junk_emails = [e for e in emails_with_class if e.get('importance') == 'not_important']
    important_emails = [e for e in emails_with_class if e.get('importance') == 'important']
    
    print(f"[*] Found {len(junk_emails)} junk emails, {len(important_emails)} important emails")
    
    # Delete junk emails
    deleted_count = 0
    failed_deletes = []

    for email in junk_emails:
        email_id = email['id']
        source = email['source']

        # Convert email_id to string if bytes
        if isinstance(email_id, bytes):
            email_id = email_id.decode()

        print(f"[*] Deleting junk: {email.get('from', 'Unknown')} - {email.get('subject', 'No Subject')[:50]}")

        if source == 'Gmail':
            try:
                delete_gmail_email(gmail_service, email_id)
                deleted_count += 1
            except Exception as e:
                print(f"[ERROR] Delete failed for Gmail {email_id}: {e}")
                failed_deletes.append(f"{source}: {email.get('subject', 'Unknown')[:40]}")
        else:
            # Yahoo - still use API (would need yahoo_client to support delete)
            if delete_via_api(email_id, source):
                deleted_count += 1
            else:
                failed_deletes.append(f"{source}: {email.get('subject', 'Unknown')[:40]}")
    
    # Send summary
    today = datetime.now().strftime("%B %d, %Y")
    
    message = f"🧹 **Daily Email Cleanup — {today}**\n\n"
    message += f"📊 **Processed:** {len(all_emails)} emails\n"
    message += f"✅ **Important kept:** {len(important_emails)}\n"
    message += f"🗑️ **Junk deleted:** {deleted_count}/{len(junk_emails)}"
    
    if failed_deletes:
        message += f"\n⚠️ **Failed ({len(failed_deletes)}):**\n"
        for f in failed_deletes[:5]:
            message += f"  • {f}\n"
    
    if important_emails:
        message += "\n\n⭐ **Important emails kept:**\n"
        for e in important_emails[:5]:
            sender = e.get('from', 'Unknown')
            subject = e.get('subject', 'No Subject')
            message += f"  • {sender}: {subject[:50]}\n"
    
    send_telegram(message)
    print(f"[OK] Cleanup complete. Deleted {deleted_count} junk emails.")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        send_telegram(f"❌ Daily Email Cleanup FAILED: {e}")
        sys.exit(1)