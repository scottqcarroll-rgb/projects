#!/usr/bin/env python3
"""
Gmail OAuth re-auth - simple code paste approach.
1. Prints the authorization URL
2. Waits for you to paste the auth code
3. Saves the token
"""
import os
import sys
import subprocess

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

cred_file = os.path.join(script_dir, 'credentials.json')
if not os.path.exists(cred_file):
    print("[ERROR] credentials.json not found in", script_dir)
    sys.exit(1)

# Use a redirect URI that doesn't need a server (urn:ietf:wg:oauth:2.0:oob)
# This makes Google show the code on-screen instead of redirecting
flow = InstalledAppFlow.from_client_secrets_file(
    cred_file, SCOPES,
    redirect_uri='urn:ietf:wg:oauth:2.0:oob'
)
auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

print()
print("=" * 60)
print("GMAIL RE-AUTHENTICATION - STEP 1: AUTHORIZE")
print("=" * 60)
print()
print("Open this URL in your browser:")
print()
print(auth_url)
print()
print("If you see a security warning, click 'Advanced' → 'Go to ... (unsafe)'")
print("Sign in and click 'Allow'")
print()
print("Google will display a code on the page (not redirect).")
print()

# Read code from stdin
code = input("Paste the code here: ").strip()
if not code:
    print("[ERROR] No code provided.")
    sys.exit(1)

print(f"[*] Exchanging code for token...")

flow.fetch_token(code=code)
creds = flow.credentials

token_file = os.path.join(script_dir, 'token.json')
with open(token_file, 'w') as token:
    token.write(creds.to_json())

print(f"[OK] Token saved to {token_file}")
print("[OK] Gmail re-authentication complete!")
