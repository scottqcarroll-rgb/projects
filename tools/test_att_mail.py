#!/usr/bin/env python3
"""IMAP connectivity check for the AT&T mailbox.

Credentials come from /home/scott/inbox-cleanup/.env, not from this file.
"""

import imaplib
import socket
import sys

sys.path.insert(0, "/home/scott/inbox-cleanup")
from inbox_cleanup import EMAIL_USER, IMAP_SERVER, IMAP_PORT, get_mail_password

socket.setdefaulttimeout(15)


def main():
    password = get_mail_password()
    if not password:
        print("[-] Set INBOX_CLEANUP_PASS in /home/scott/inbox-cleanup/.env")
        return 1

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        print(f"Connected to {IMAP_SERVER}:{IMAP_PORT}")
        mail.login(EMAIL_USER, password)
        print("Login successful!")
        mail.select("INBOX")
        status, data = mail.search(None, "ALL")
        msg_ids = data[0].split()
        print(f"Inbox: {len(msg_ids)} messages")
        if msg_ids:
            status, msg_data = mail.fetch(msg_ids[-1], "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
            print(f"Latest: {msg_data[0][1].decode()[:200]}")
        mail.logout()
        return 0
    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
