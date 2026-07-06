#!/usr/bin/env python3
"""
Token exchange with proper error handling and device flow authentication.
"""

import json
import urllib.request
import urllib.parse
import time

# Load client credentials
with open('/home/scott/projects/email-agent/credentials.json') as f:
    creds = json.load(f)

client_id = creds['installed']['client_id']
client_secret = creds['installed']['client_secret']
redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

# Use the authorization code provided by the user
auth_code = '4/1AdkVLPziS1lOSEHHYXYypyJ5MyREQPoVT1CjUtrIlrBk5tn8BogY4vc'

print("Exchanging authorization code for token...")
print(f"Client ID: {client_id}")
print(f"Redirect URI: {redirect_uri}")
print(f"Auth Code: {auth_code[:20]}... (truncated)")

# Prepare token request
token_url = 'https://oauth2.googleapis.com/token'
data = urllib.parse.urlencode({
    'client_id': client_id,
    'client_secret': client_secret,
    'code': auth_code,
    'grant_type': 'authorization_code',
    'redirect_uri': redirect_uri
}).encode()

# Create request with proper headers
req = urllib.request.Request(token_url, data=data)
req.add_header('Content-Type', 'application/x-www-form-urlencoded')
req.add_header('User-Agent', 'Brisar-Contract-Agent/1.0')

# Send request with timeout
req_timeout = 30
success = False

try:
    with urllib.request.urlopen(req, timeout=req_timeout) as response:
        token_data = json.load(response)
        
        # Validate response
        if 'access_token' not in token_data:
            print(f"Token exchange failed: missing access_token")
            print(f"Response: {token_data}")
            success = False
        else:
            # Save the new token
            with open('/home/scott/projects/email-agent/token.json', 'w') as f:
                json.dump(token_data, f)
            
            print("\n✅ Token exchange successful!")
            print(f"✅ Access token: {token_data.get('access_token', 'NOT FOUND')[:30]}...")
            print(f"✅ Expires in: {token_data.get('expires_in', 'NOT FOUND')} seconds")
            if 'refresh_token' in token_data:
                print(f"✅ Refresh token: {token_data['refresh_token'][:30]}...")
            print(f"✅ Scope: {token_data.get('scope', 'NOT FOUND')}")
            
            # Verify token structure
            required_fields = ['access_token', 'expires_in', 'token_type']
            for field in required_fields:
                if field not in token_data:
                    print(f"⚠️ Missing field: {field}")
            
            success = True
        
except urllib.error.HTTPError as e:
    print(f"\n❌ HTTP Error {e.code}: {e.reason}")
    try:
        error_body = json.loads(e.read().decode())
        print(f"Error details: {error_body}")
    except:
        print(f"Response body: {e.read().decode()}")
    success = False
except Exception as e:
    print(f"\n❌ Token exchange failed: {e}")
    success = False

if success:
    print("\n🎉 Token exchange completed successfully!")
else:
    print("\n💥 Token exchange failed - contact support if issues persist")