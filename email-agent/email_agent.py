#!/usr/bin/env python3
"""
Unified Email Agent
Fetches emails from Gmail and/or Yahoo Mail, classifies them with Claude,
and generates an HTML dashboard. Flexible provider support via --gmail and --yahoo flags.
"""

import os
import json
import re
import sys
import requests
from datetime import datetime

from gmail_imap_client import get_authenticated_service as get_gmail_service, fetch_recent_emails as fetch_gmail_emails
try:
    from llm_classifier import classify_emails
    USE_LLM = True
except ImportError:
    from email_classifier import classify_emails
    USE_LLM = False
from dashboard import generate_dashboard
import email_api

# Telegram Bot credentials
TELEGRAM_BOT_TOKEN = "8773175847:***"
TELEGRAM_CHAT_ID = "7542619200"

LAST_RUN_FILE = 'last_run.json'

# Gmail only mode
CHECK_GMAIL = True
CHECK_YAHOO = False


def load_last_run_date():
    """Load the last run date from last_run.json."""
    if not os.path.exists(LAST_RUN_FILE):
        return None

    try:
        with open(LAST_RUN_FILE, 'r') as f:
            data = json.load(f)
            return data.get('date')
    except:
        return None


def save_run_date():
    """Save today's date to last_run.json."""
    today = datetime.now().date().isoformat()
    with open(LAST_RUN_FILE, 'w') as f:
        json.dump({'date': today}, f)


def has_already_run_today():
    """Check if the agent has already run today."""
    last_run = load_last_run_date()
    today = datetime.now().date().isoformat()
    return last_run == today


def send_telegram_notification(important_emails, not_important_count, total_count, title="Morning Email Summary"):
    """Telegram disabled - invalid bot token."""
    print("[*] Telegram notification skipped (no valid bot token)")
    return True


def _extract_name(sender_str):
    """Extract a clean name from sender string like 'Name <email@example.com>'."""
    if not sender_str or sender_str == 'Unknown':
        return 'Unknown'
    # Try to extract name before < bracket
    m = re.match(r'^([^<]+)', sender_str)
    if m:
        name = m.group(1).strip().strip('"')
        if name and name != sender_str:
            return name[:30]
    # Fallback: extract email user
    m = re.search(r'[\w.+-]+@([\w.-]+)', sender_str)
    if m:
        return m.group(1).split('.')[0].title()
    return sender_str[:30]


def _get_priority_icon(reason):
    """Return priority icon based on reason keywords."""
    reason_lower = reason.lower()
    if any(w in reason_lower for w in ['deadline', 'urgent', 'action required', 'payment']):
        return "🔴"
    if any(w in reason_lower for w in ['meeting', 'schedule', 'appointment', 'call']):
        return "🟠"
    return "🟡"


def main():
    """Main orchestration flow."""
    print("[*] Email Agent starting...")

    # Parse CLI flags
    force_run = '--force' in sys.argv

    # Determine title
    title = "Gmail Morning Summary"

    if has_already_run_today() and not force_run:
        print("[OK] Already ran today. Use --force to run again.")
        return

    all_emails = []
    gmail_service = None

    # Fetch from Gmail
    if CHECK_GMAIL:
        try:
            print("[*] Authenticating with Gmail...")
            gmail_service = get_gmail_service()
            print("[*] Fetching Gmail emails...")
            gmail_emails = fetch_gmail_emails(gmail_service, hours=24, max_results=50)
            print(f"[*] Fetched {len(gmail_emails)} Gmail emails")
            all_emails.extend(gmail_emails)
        except Exception as e:
            print(f"[WARN] Gmail fetch failed: {e}")
            print("[*] Continuing with empty email list...")
            gmail_service = None

    if not all_emails:
        print("[OK] No emails to classify. Generating empty dashboard...")
        html = generate_dashboard([], title=title)
        dashboard_path = os.path.abspath('daily_summary.html')
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f"[*] Dashboard written to {dashboard_path}")

        # Start Flask API server
        print("[*] Starting email API server...")
        if CHECK_GMAIL and gmail_service:
            email_api.start_server(gmail_service)
        else:
            email_api.start_server(None)

        # (browser output disabled - Telegram digest is the primary output)
        send_telegram_notification([], 0, 0, title=title)
        save_run_date()
        print("[OK] Done!")
        return

    print(f"[*] Classifying {len(all_emails)} emails...")
    classifications = classify_emails(all_emails)

    print("[*] Merging classifications with email data...")
    emails_with_classification = []
    for email in all_emails:
        classification = next((c for c in classifications if c.get('id') == email['id']), None)
        if classification:
            email.update(classification)
        else:
            email['importance'] = 'not_important'
            email['reason'] = 'Classification unavailable'
        emails_with_classification.append(email)

    print("[*] Generating dashboard...")

    # Count important vs not important
    important_emails = [e for e in emails_with_classification if e.get('importance', 'not_important') == 'important']
    not_important_count = len(emails_with_classification) - len(important_emails)

    html = generate_dashboard(emails_with_classification, title=title)

    dashboard_path = os.path.abspath('daily_summary.html')
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"[*] Dashboard written to {dashboard_path}")

    # Start Flask API server for delete operations
    print("[*] Starting email API server...")
    email_api.start_server(gmail_service)

    # (browser output disabled - Telegram digest is the primary output)

    # Send rich Telegram notification
    send_telegram_notification(important_emails, not_important_count, len(all_emails), title=title)

    save_run_date()
    print("[OK] Done! Dashboard generated and digest sent.")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
