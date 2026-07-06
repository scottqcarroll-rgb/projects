#!/usr/bin/env python3
"""
Automated Gmail token refresh for headless environments.
Uses OAuth device flow or manual code injection.
"""
import os
import json
import sys
from pathlib import Path

# Add email-agent to path
sys.path.insert(0, '/home/scott/projects/email-agent')
os.chdir('/home/scott/projects/email-agent')

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
TOKEN_FILE = '/home/scott/projects/email-agent/token.json'
CREDENTIALS_FILE = '/home/scott/projects/email-agent/credentials.json'

def refresh_token():
    """Attempt to refresh token using device flow or re-auth."""
    creds = None
    
    # Load existing token if it exists
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Try to refresh if expired
    if creds and creds.expired and creds.refresh_token:
        try:
            print("[*] Attempting to refresh expired token...")
            creds.refresh(Request())
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            print("[OK] Token refreshed successfully!")
            return True
        except Exception as e:
            print(f"[WARN] Refresh failed: {e}")
            creds = None
    
    # Need full re-authentication
    print("[*] Starting OAuth re-authentication...")
    flow = InstalledAppFlow.from_client_secrets_file(
        CREDENTIALS_FILE, 
        SCOPES,
        redirect_uri='http://localhost:8080'
    )
    
    try:
        # Try local server flow (works if port 8080 is available)
        creds = flow.run_local_server(port=8080, open_browser=True)
    except Exception as e:
        print(f"[WARN] Local server flow failed: {e}")
        print("[*] Falling back to console-based device flow...")
        
        # Device flow - prints URL and waits for code
        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
        print(f"\n{'='*60}")
        print("OPEN THIS URL IN YOUR BROWSER:")
        print(f"{'='*60}")
        print(auth_url)
        print(f"{'='*60}\n")
        
        code = input("Paste the authorization code: ").strip()
        flow.fetch_token(code=code)
        creds = flow.credentials
    
    # Save new token
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print(f"[OK] New token saved to {TOKEN_FILE}")
    return True

if __name__ == '__main__':
    try:
        if refresh_token():
            print("\n[SUCCESS] Gmail authentication ready!")
            print("You can now run: python3 /home/scott/projects/govt-contracts/send_contract_report.py")
    except Exception as e:
        print(f"[ERROR] Failed: {e}")
        sys.exit(1)