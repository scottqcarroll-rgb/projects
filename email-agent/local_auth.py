#!/usr/bin/env python3
"""
Yahoo OAuth2 Authorization - Run THIS on YOUR LOCAL MACHINE (with browser)
Then copy the generated yahoo_tokens.json to the server at /home/scott/projects/email-agent/yahoo_tokens.json
"""

import json
import os
import secrets
import threading
import time
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, parse_qs
import requests

# ========== CONFIG - UPDATE THESE ==========
CLIENT_ID = "dj0yJmk9SmhaWGNFVE1XajM5JmQ9WVdrOWJUUnZZblZ1UzA0bWNHbzlNQT09JnM9Y29uc3VtZXJzZWNyZXQmc3Y9MCZ4PTdh"
CLIENT_SECRET = "e1bcff1def87649f2c6b8a5313029606acc7ce0c"
REDIRECT_URI = "http://localhost:8090/callback"
SCOPES = ["mail-r", "mail-w", "openid", "email", "profile"]
# ===========================================

YAHOO_AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
YAHOO_TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"

_auth_code = None
_auth_state = None
_callback_server = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code, _auth_state
        if self.path.startswith("/callback"):
            query = parse_qs(self.path.split("?", 1)[1] if "?" in self.path else "")
            _auth_code = query.get("code", [None])[0]
            _auth_state = query.get("state", [None])[0]
            
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            if _auth_code:
                html = """
                <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>✅ Authorization Successful</h1>
                <p>Tokens are being saved. You can close this window.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
                </body></html>
                """
            else:
                error = query.get("error", ["Unknown error"])[0]
                html = f"""
                <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>❌ Authorization Failed</h1>
                <p>Error: {error}</p>
                </body></html>
                """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass


def start_callback_server():
    global _callback_server
    _callback_server = HTTPServer(("localhost", 8090), CallbackHandler)
    thread = threading.Thread(target=_callback_server.serve_forever, daemon=True)
    thread.start()
    return _callback_server


def stop_callback_server():
    global _callback_server
    if _callback_server:
        _callback_server.shutdown()
        _callback_server.server_close()
        _callback_server = None


def main():
    print("=" * 60)
    print("YAHOO OAUTH2 AUTHORIZATION - RUN ON LOCAL MACHINE")
    print("=" * 60)
    print(f"\nClient ID: {CLIENT_ID[:30]}...")
    print(f"Redirect URI: {REDIRECT_URI}")
    print(f"Scopes: {' '.join(SCOPES)}")
    
    state = secrets.token_urlsafe(32)
    
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "state": state,
        "access_type": "offline",
    }
    auth_url = f"{YAHOO_AUTH_URL}?{urlencode(auth_params)}"
    
    print(f"\n[*] Starting callback server on {REDIRECT_URI}...")
    start_callback_server()
    
    print(f"\n[*] Opening browser for authorization...")
    print(f"    If browser doesn't open, visit manually:")
    print(f"\n    {auth_url}\n")
    
    webbrowser.open(auth_url)
    
    print(f"[*] Waiting for callback (5 min timeout)...")
    
    timeout = 300
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if _auth_code is not None:
            break
        if _auth_state is not None and _auth_code is None:
            print(f"[ERROR] Authorization failed: {_auth_state}")
            stop_callback_server()
            return 1
        time.sleep(1)
    
    stop_callback_server()
    
    if not _auth_code:
        print("[ERROR] Timeout - no authorization received")
        return 1
    
    if _auth_state != state:
        print("[ERROR] Invalid state - possible CSRF")
        return 1
    
    print(f"\n[OK] Authorization code received!")
    print(f"[*] Exchanging for tokens...")
    
    token_data = {
        "grant_type": "authorization_code",
        "code": _auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
    }
    
    response = requests.post(YAHOO_TOKEN_URL, data=token_data, timeout=30)
    
    if response.status_code != 200:
        print(f"[ERROR] Token exchange failed: {response.status_code}")
        print(f"        {response.text}")
        return 1
    
    tokens = response.json()
    
    # Add expiry timestamp
    if "expires_in" in tokens:
        tokens["expires_at"] = time.time() + tokens["expires_in"]
    
    # Save to current directory
    output_file = "yahoo_tokens.json"
    with open(output_file, "w") as f:
        json.dump(tokens, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✅ SUCCESS! Tokens saved to {output_file}")
    print(f"{'='*60}")
    print(f"\nAccess token: {tokens.get('access_token', 'N/A')[:30]}...")
    print(f"Refresh token: {'YES' if tokens.get('refresh_token') else 'NO'}")
    print(f"Expires in: {tokens.get('expires_in', 'N/A')} seconds")
    print(f"\n📋 NEXT STEP:")
    print(f"   Copy {output_file} to the server:")
    print(f"   scp {output_file} clawz840:/home/scott/projects/email-agent/yahoo_tokens.json")
    print(f"\n   Or copy the file contents manually.")
    
    return 0


if __name__ == "__main__":
    exit(main())