#!/usr/bin/env python3
"""
Exchange authorization code for tokens via Google OAuth endpoint
"""

import json
import urllib.request
import urllib.parse
import sys

# Configuration
auth_code = '4/1AdkVLPy1ipEJXgBt-6Vkm7b1aNIuXfowswnlz8R303yzVVXaCns4CC7Qx1I'  # Paste your code here
TOKEN_URL = 'https://oauth2.googleapis.com/token'
# CLIENT_ID = '887491795102-s4k2tc59si6pdrjoo3p8adm1g0oh8ae9.apps.googleusercontent.com'
# CLIENT_SECRET = '***'

REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

print("🔄 Exchanging authorization code for tokens...")
print(f"Authorization Code (first 30 chars): {auth_code[:30]}...")

# Prepare request data
token_data = {
    'code': auth_code,
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'redirect_uri': REDIRECT_URI,
    'grant_type': 'authorization_code'
}

# Encode data as multipart/form-data style
encoded_data = urllib.parse.urlencode(token_data).encode('utf-8')

# Create request
request = urllib.request.Request(TOKEN_URL, data=encoded_data)
request.add_header('Content-Type', 'application/x-www-form-urlencoded')

try:
    with urllib.request.urlopen(request) as response:
        token_data = json.load(response)
        
        # Save the token
        with open('/home/scott/projects/email-agent/token.json', 'w') as f:
            json.dump(token_data, f)
        
        print("✅ SUCCESS! Token exchanged and saved to token.json")
        print("\n🔑 Token Details:")
        print(f"   Access Token: {token_data.get('access_token', 'N/A')[:30]}...")
        print(f"   Expires In: {token_data.get('expires_in', 'N/A')} seconds")
        print(f"   Refresh Token: {token_data.get('refresh_token', 'N/A')[:30] if token_data.get('refresh_token') else 'N/A'}")
        print(f"   Token Type: {token_data.get('token_type', 'N/A')}")
        print(f"   Scope: {token_data.get('scope', 'N/A')}")
        
        # Test if token works
        print("\n🧪 Testing Gmail API connection...")
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        
        creds = Credentials.from_authorized_user_file('/home/scott/projects/email-agent/token.json')
        creds.refresh(Request())
        
        if creds.valid:
            print("   ✅ Token is valid!")
            print("   🎉 Your email agent is now authenticated!")
            print("   📧 Daily contract reports will be sent automatically.")
        else:
            print("   ❌ Token validation failed")
            
except urllib.error.URLError as e:
    print(f"❌ Network error during token exchange: {e.reason}")
    print("   This may be due to missing client_secret or network issues")
except Exception as e:
    print(f"❌ Token exchange failed: {e}")