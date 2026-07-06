#!/usr/bin/env python3
"""
Simplified Remote OAuth Test Script for Gmail
"""

import os
import json
import requests

# Load credentials
with open('/home/scott/projects/email-agent/credentials.json') as f:
    creds = json.load(f)

client_id = creds['installed']['client_id']
client_secret = creds['installed']['client_secret']
redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

# Device code request
url = 'https://accounts.google.com/o/oauth2/device/code'
data = {
    'client_id': client_id,
    'scope': 'https://www.googleapis.com/auth/gmail.modify',
    'redirect_uri': redirect_uri
}

try:
    response = requests.post(url, data=data)
    response.raise_for_status()
    data = response.json()

    print("\n✅ Device code received!")
    print(f"Device Code: {data['device_code']}")
    print(f"User Code: {data['user_code']}")
    print(f"Verification URL: {data['verification_uri']}")
    print(f"Expires in {data['expires_in']//60} minutes")

    # Manual verification step requires browser access
    print("\n\u23f0 Please:")
    print(f"1. Visit: {data['verification_uri']}")
    print(f"2. Enter code: {data['user_code']}")
    print(f"3. Press Enter here after completion\n")

    input("Auth complete? (y/n): ").strip().lower() == 'y'

    # Token exchange would follow here if automated
except Exception as e:
    print(f"\n❌ Error: {e}")
    input("Check credentials and try again (y/n): ").strip()