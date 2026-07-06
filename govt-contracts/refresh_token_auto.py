import json
import urllib.request
import urllib.parse
import os

# Google OAuth token endpoint
token_url = "https://oauth2.googleapis.com/token"

# Load client credentials from credentials.json
with open('/home/scott/projects/email-agent/credentials.json') as f:
    creds = json.load(f)
client_id = creds['installed']['client_id']
client_secret = creds['installed']['client_secret']

# Load existing refresh token
with open('/home/scott/projects/email-agent/token.json') as f:
    token_data = json.load(f)
refresh_token = token_data['refresh_token']

# Request new access token
data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "refresh_token": refresh_token,
    "grant_type": "refresh_token",
    "scope": "https://www.googleapis.com/auth/gmail.modify"
}

req = urllib.request.Request(
    token_url,
    data=urllib.parse.urlencode(data).encode()
)

try:
    with urllib.request.urlopen(req) as response:
        new_tokens = json.load(response)
        
        # Save updated token file
        with open('/home/scott/projects/email-agent/token.json', 'w') as f:
            json.dump(new_tokens, f)
        
        print("Token refreshed successfully!")
        print(f"New token expires at: {new_tokens.get('expiry')}")
        
except Exception as e:
    print(f"Token refresh failed: {e}")
    raise