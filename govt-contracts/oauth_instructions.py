#!/usr/bin/env python3
"""
Explanation of OAuth process for remote authentication
"""

import os
import json

print("=" * 60)
print("REMOTE OAUTH AUTHENTICATION GUIDE")
print("=" * 60)

print("\n1. CURRENT CREDENTIALS STATUS:")
with open('/home/scott/projects/email-agent/credentials.json') as f:
    creds = json.load(f)
    print(f"   Client ID: {creds['installed']['client_id'][:20]}...")
    print(f"   Redirect URIs: {creds['installed']['redirect_uris']}")

print("\n2. AUTHORIZATION URL TO VISIT:")
auth_url = "https://accounts.google.com/o/oauth2/auth?" + "&".join([
    "response_type=code",
    f"client_id={creds['installed']['client_id']}",
    "redirect_uri=urn:ietf:wg:oauth:2.0:oob",
    "scope=https://www.googleapis.com/auth/gmail.modify",
    "access_type=offline",
    "prompt=consent"
])
print(f"   {auth_url}")

print("\n3. STEPS TO COMPLETE:")
print("   a. Copy the above URL")
print("   b. Paste it into your browser address bar")
print("   c. Sign in with your Google account (if needed)")
print("   d. Click 'Allow' to grant Gmail API permissions")
print("   e. You will see an authorization code (starts with 4/)")
print("   f. Copy that entire code")
print("   g. Return here and paste it")

print("\n4. WHAT HAPPENS NEXT:")
print("   - I will exchange the code for a fresh token")
print("   - The token will be saved to token.json")
print("   - Your email agent will be authenticated")
print("   - Daily contract reports will resume")

print("\n" + "=" * 60)
print("READY WHEN YOU ARE - JUST PROVIDE THE AUTHORIZATION CODE")
print("=" * 60)