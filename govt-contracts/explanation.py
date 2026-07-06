#!/usr/bin/env python3
"""
Quick Script to Extract Working OAuth Credentials
Shows all OAuth methods available for remote authentication.
"""

import os
import json
import requests
import base64
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# Test 1: Check current credentials
print("🔍 Checking current credentials...")
with open('/home/scott/projects/email-agent/credentials.json') as f:
    creds = json.load(f)
    print(f"Client ID: {creds['installed']['client_id']}")
    print(f"Redirect URIs: {creds['installed']['redirect_uris']}")

# Test 2: Try to create OAuth flow
print("\n🔐 Testing OAuth Flow...")

# Create a simple local server for OAuth callback
class OAuthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if '?' in self.path:
            query = parse_qs(self.path.split('?')[1])
            if 'code' in query:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(b'''
                <!DOCTYPE html>
                <html>
                    <head><title>Authentication Complete</title></head>
                    <body>
                        <h1>✅ Authentication Complete!</h1>
                        <p>You can close this window and return to the script.</p>
                    </body>
                </html>
                ''')
                # Extract the code and save it
                from simple_oauth import code_exchange
                return
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b'''<h1>Waiting for authorization...</h1><p>Please wait while the OAuth flow completes.</p>''')

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

    flow = InstalledAppFlow.from_client_secrets_file(
        '/home/scott/projects/email-agent/credentials.json',
        SCOPES,
        redirect_uri='http://localhost:8080'
    )

    print("✅ OAuth flow created successfully!")

    # Generate the auth URL
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )

    print(f"\n🌐 Authorization URL:")
    print(f"{auth_url}")

    print("\n📋 Instructions:")
    print(f"1. Visit: {auth_url}")
    print(f"2. Complete authentication in your browser")
    print(f"3. You'll be redirected to: http://localhost:8080")
    print(f"4. Come back here and we can extract the code")

    # Since we can't open browser, let's just print the detailed flow
    print("\n📝 Manual Copy-Paste Method:")
    print("1. Copy this authorization URL:")
    print(f"   {auth_url}")
    print("2. Open it in your browser")
    print("3. Sign in with your Google account")
    print("4. Grant permissions for Gmail API")
    print("5. You'll get redirected to http://localhost:8080")
    print("6. Look for the authorization code in the URL")
    print("7. Copy the code (it's in the URL after '?code=')")
    print("8. Return here and paste the code")

    print("\n🔄 After you get the code, I can exchange it for a token:")

except ImportError as e:
    print(f"❌ Import error: {e}")

except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "="*60)
print("🎯 Alternative: Manual Token Exchange")
print("="*60)
print("1. Authenticate manually via your browser")
print("2. Get authorization code")
print("3. Paste code back here")
print("4. I'll exchange it for a fresh token.json")
print("="*60)

# Alternative method - direct token exchange if we have a code
print("\n📝 Alternative Direct Method:")
print("If you have an authorization code from the URL...")
print("We can exchange it directly for tokens without browser.")
print("\nJust provide me with the authorization code (starts with 4/)")
print("And I'll handle the rest automatically.")

# Ask if they want to proceed
import sys
try:
    input("\nContinue? (y/n): ").strip().lower() == 'y'
except:
    print("\nManual intervention needed - run script with valid OAuth setup")