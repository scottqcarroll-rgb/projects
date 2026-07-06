import imaplib
import socket
socket.setdefaulttimeout(15)

# AT&T's own IMAP server
host = 'imap.mail.att.net'
port = 993
user = 'sqc@bellsouth.net'
password = 'Blackwater2025##'

try:
    m = imaplib.IMAP4_SSL(host, port)
    print(f'Connected to {host}:{port}')
    m.login(user, password)
    print('Login successful!')
    m.select('INBOX')
    status, data = m.search(None, 'ALL')
    msg_ids = data[0].split()
    print(f'Inbox: {len(msg_ids)} messages')
    if msg_ids:
        status, msg_data = m.fetch(msg_ids[-1], '(BODY[HEADER.FROM (SUBJECT)])')
        print(f'Latest: {msg_data[0][1].decode()[:200]}')
    m.logout()
except imaplib.IMAP4.error as e:
    print(f'IMAP error: {e}')
except Exception as e:
    print(f'Error: {e}')
