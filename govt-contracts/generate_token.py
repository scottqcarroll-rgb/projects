#!/usr/bin/env python3
"""
Fresh token generator for Gmail API.
Creates a new token.json with full offline access.
"""

import json
import os
import sys
from pathlib import Path

# Force re-auth even if token exists
TOKEN_FILE = '/home/scott/projects/email-agent/token.json'
CREDENTIALS_FILE = '/home/scott/projects/email-agent/credentials.json'

# Remove any existing token
if os.path.exists(TOKEN_FILE):
    os.remove(TOKEN_FILE)

# Import Google auth flows
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

try:
    # Try device flow - prints URL and waits for code
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    
    print('1. Opening browser...')
    creds = flow.run_local_server(port=0)
    
except Exception as e:
    print(f'Browser flow failed: {e}')
    print('2. Falling back to device flow...')
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE,
        SCOPES,
        redirect_uri='urn:ietf:wg:oauth:2.0:oob'
    )
    
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    print(f'Please open this URL and authorize access:')
    print(auth_url)
    code = input('Paste authorization code here: ').strip()
    creds = flow.fetch_token(code=code)

# Save the credentials
with open(TOKEN_FILE, 'w') as token_file:
    token_file.write(creds.to_json())

print(f'Success! Token saved to {TOKEN_FILE}')
print('You can now run the email agent:')
print('  python3 /home/scott/projects/govt-contracts/send_contract_report.py')