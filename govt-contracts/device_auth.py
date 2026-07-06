#!/usr/bin/env python3
"""
Device Authorization Flow for Remote OAuth Authentication
This works without a local server - perfect for remote/headless environments.
"""

import json
import urllib.request
import urllib.parse
import time
import sys

# Load credentials
with open('/home/scott/projects/email-agent/credentials.json') as f:
    creds = json.load(f)

client_id = creds['installed']['client_id']
client_secret = creds['installed']['client_secret']
redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

print("=" * 60)
print("DEVICE AUTHORIZATION FLOW - Remote OAuth Authentication")
print("=" * 60)
print(f"Client ID: {client_id}")
print(f"Redirect URI: {redirect_uri}")
print()

# Step 1: Request device code
device_url = "https://oauth2.googleapis.com/device/code"
data = urllib.parse.urlencode({
    'client_id': client_id,
    'scope': 'https://www.googleapis.com/auth/gmail.modify'
}).encode()

req = urllib.request.Request(device_url, data=data)
req.add_header('Content-Type', 'application/x-www-form-urlencoded')

try:
    with urllib.request.urlopen(req) as response:
        device_data = json.load(response)
except Exception as e:
    print(f"Failed to get device code: {e}")
    sys.exit(1)

device_code = device_data.get('device_code')
user_code = device_data.get('user_code')
verification_url = device_data.get('verification_url', 'https://www.google.com/device')
expires_in = device_data.get('expires_in', 1800)
interval = device_data.get('interval', 5)

print("🔐 AUTHORIZATION REQUIRED")
print("-" * 40)
print(f"1. Go to: {verification_url}")
print(f"2. Enter code: {user_code}")
print(f"3. Complete Google authentication")
print(f"4. Wait for token exchange (auto-polls)")
print()
print(f"⏱️  Code expires in: {expires_in} seconds ({expires_in//60} minutes)")
print(f"🔄 Polling every: {interval} seconds")
print()

# Step 2: Poll for token
token_url = "https://oauth2.googleapis.com/token"
start_time = time.time()

while time.time() - start_time < expires_in:
    time.sleep(interval)
    
    poll_data = urllib.parse.urlencode({
        'client_id': client_id,
        'client_secret': client_secret,
        'device_code': device_code,
        'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
    }).encode()
    
    poll_req = urllib.request.Request(token_url, data=poll_data)
    poll_req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    
    try:
        with urllib.request.urlopen(poll_req) as response:
            token_data = json.load(response)
            
        # Success!
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_in_token = token_data.get('expires_in')
        token_type = token_data.get('token_type', 'Bearer')
        
        print("✅ AUTHENTICATION SUCCESSFUL!")
        print(f"   Access Token: {access_token[:30]}...")
        print(f"   Refresh Token: {refresh_token[:30] if refresh_token else 'NONE'}...")
        print(f"   Expires In: {expires_in_token} seconds")
        print(f"   Token Type: {token_type}")
        
        # Save token.json
        with open('/home/scott/projects/email-agent/token.json', 'w') as f:
            json.dump(token_data, f)
        
        print(f"\n💾 Token saved to: /home/scott/projects/email-agent/token.json")
        print("\n" + "=" * 60)
        print("🎉 COMPLETE - Gmail API is now authenticated!")
        print("   Daily contract reports will be sent automatically.")
        print("=" * 60)
        sys.exit(0)
        
    except urllib.error.HTTPError as e:
        if e.code == 400:
            error_body = json.loads(e.read().decode())
            error = error_body.get('error', 'unknown')
            
            if error == 'authorization_pending':
                print(f"⏳ Waiting for authorization... (code: {user_code})")
                continue
            elif error == 'slow_down':
                interval += 5
                print(f"⏳ Slowing down, polling every {interval}s...")
                continue
            elif error == 'expired_token':
                print("❌ Device code expired. Please restart.")
                break
            elif error == 'access_denied':
                print("❌ Access denied by user.")
                break
            else:
                print(f"❌ Error: {error} - {error_body.get('error_description', '')}")
                break
        else:
            print(f"❌ HTTP Error {e.code}: {e.reason}")
            break
    except Exception as e:
        print(f"❌ Polling error: {e}")
        break

print("\n❌ Authorization timed out or failed.")
print("   Please restart the script to try again.")
sys.exit(1)