#!/usr/bin/env python3
import sys
import os
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
script_dir = "/home/scott/projects/email-agent"
os.chdir(script_dir)

cred_file = os.path.join(script_dir, "credentials.json")

if len(sys.argv) < 2:
    print("Usage: python3 exchange_code_cli.py <authorization_code>")
    sys.exit(1)

code = sys.argv[1].strip()

# Use the SAME flow pattern as reauth.py - keeps code_verifier
flow = InstalledAppFlow.from_client_secrets_file(
    cred_file, SCOPES,
    redirect_uri="urn:ietf:wg:oauth:2.0:oob"
)

flow.fetch_token(code=code)
creds = flow.credentials

token_file = os.path.join(script_dir, "token.json")
with open(token_file, "w") as token:
    token.write(creds.to_json())

print(f"[OK] Token saved to {token_file}")
print(f"Access token: {creds.token[:20]}...")
print(f"Refresh token: {creds.refresh_token[:20] if creds.refresh_token else None}...")
print(f"Expiry: {creds.expiry}")