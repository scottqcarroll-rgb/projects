#!/usr/bin/env python3
"""
Test script for token exchange
"""

import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOKEN_FILE = '/home/scott/projects/email-agent/token.json'
CREDENTIALS_FILE = '/home/scott/projects/email-agent/credentials.json'

print("==== CKP: Initiating OAuth Refresh ====")
print(f"Client ID: {CREDENTIALS_FILE}")

flow = InstalledAppFlow.from_client_secrets_file(
    CREDENTIALS_FILE,
    SCOPES,
    redirect_uri='http://localhost:8080'
)

# Generate URL for manual auth
auth_url = flow.authorization_url(prompt='force')
print("==== CKP: Visit URL Below ====")
print(auth_url)
print("""
Please:
1. Go to this URL in your browser
2. Complete OAuth authentication
3. Return here with the authorization code
====
""")

# Manual code sequence
code = input("Enter authorization code: ")
creds = flow.fetch_token(code=code)

# Save fresh token
with open(TOKEN_FILE, 'w') as f:
    f.write(creds.to_json())

print("==== CKP: Token Refresh Complete ====")