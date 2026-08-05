#!/usr/bin/env python3
import sys
import json
from google_auth_oauthlib.flow import Flow

code = sys.argv[1] if len(sys.argv) > 1 else None
if not code:
    print("Usage: python3 exchange_code.py <authorization_code>")
    sys.exit(1)

# Load client secrets
with open("/home/scott/projects/email-agent/credentials.json") as f:
    client_config = json.load(f)

# Recreate the exact same flow with PKCE
flow = Flow.from_client_config(
    client_config,
    scopes=["https://www.googleapis.com/auth/gmail.modify"],
    redirect_uri="urn:ietf:wg:oauth:2.0:oob"
)

# The flow object was created with a random code_verifier
# We need to exchange using the SAME flow instance
# But we can't recreate the exact same PKCE challenge...
# Let's just use the flow as-is and exchange the code

try:
    flow.fetch_token(code=code)
    creds = flow.credentials
    
    token_data = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes,
        "expiry": creds.expiry.isoformat() if creds.expiry else None
    }
    
    with open("/home/scott/projects/email-agent/token.json", "w") as f:
        json.dump(token_data, f, indent=2)
    
    print("[OK] Token saved successfully")
    print(f"Access token: {creds.token[:20]}...")
    print(f"Refresh token: {creds.refresh_token[:20] if creds.refresh_token else None}...")
    print(f"Expiry: {creds.expiry}")
    
except Exception as e:
    print(f"[ERROR] {type(e).__name__}: {e}")
    sys.exit(1)