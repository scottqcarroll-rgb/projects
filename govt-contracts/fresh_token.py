#!/usr/bin/env python3
"""
Minimal token refresh script for Gmail API.
Run this script and follow the prompts to refresh your token.
"""

import json
import os
import sys
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOKEN_FILE = '/home/scott/projects/email-agent/token.json'
CREDENTIALS_FILE = '/home/scott/projects/email-agent/credentials.json'

# Remove any existing token file
if os.path.exists(TOKEN_FILE):
    os.remove(TOKEN_FILE)

flow = InstalledAppFlow.from_client_secrets_file(
    CREDENTIALS_FILE,
    SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)

print("Opening browser for authorization...")
try:
    creds = flow.run_local_server(port=0)
except Exception as e:
    print("Browser flow failed: {}".format(e))
    print("Please go to this URL and authorize access:")
    auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
    print(auth_url)
    code = input("Paste the authorization code here: ").strip()
    creds = flow.fetch_token(code=code)

# Save the new credentials
with open(TOKEN_FILE, 'w') as token_file:
    token_file.write(creds.to_json())

print("Success! Token saved to {}".format(TOKEN_FILE))
print("You can now run the email agent:", file=sys.stderr)
print("  python3 /home/scott/projects/govt-contracts/send_contract_report.py", file=sys.stderr)