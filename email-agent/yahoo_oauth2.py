#!/usr/bin/env python3
"""
Yahoo OAuth2 IMAP Client - Authorization Code Flow with Local Callback
Handles full OAuth2 flow: browser auth → callback → token → IMAP XOAUTH2 auth
Based on Yahoo's official documentation at https://developer.yahoo.com/oauth2/guide/
"""

import os
import json
import time
import base64
import imaplib
import requests
import threading
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from urllib.parse import urlencode, parse_qs
from http.server import HTTPServer, BaseHTTPRequestHandler

# Yahoo OAuth2 endpoints (from https://api.login.yahoo.com/.well-known/openid-configuration)
YAHOO_AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
YAHOO_TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
YAHOO_REVOKE_URL = "https://api.login.yahoo.com/oauth2/revoke"

# Local callback server
CALLBACK_HOST = "localhost"
CALLBACK_PORT = 8090
CALLBACK_PATH = "/callback"
REDIRECT_URI = f"http://{CALLBACK_HOST}:{CALLBACK_PORT}{CALLBACK_PATH}"

# Scopes needed for IMAP/SMTP access
YAHOO_SCOPES = ["mail-r", "mail-w", "openid", "email", "profile"]

# Token storage
TOKEN_FILE = Path(__file__).parent / "yahoo_tokens.json"

# Global to store auth code from callback
_auth_code = None
_auth_state = None
_callback_server = None


def load_client_credentials() -> Tuple[str, str]:
    """Load Yahoo OAuth2 client credentials from .env"""
    env_file = Path(__file__).parent / ".env"
    client_id = os.environ.get("YAHOO_CLIENT_ID")
    client_secret = os.environ.get("YAHOO_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        if env_file.exists():
            with open(env_file) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("YAHOO_CLIENT_ID="):
                        client_id = line.split("=", 1)[1].strip()
                    elif line.startswith("YAHOO_CLIENT_SECRET="):
                        client_secret = line.split("=", 1)[1].strip()
    
    if not client_id or not client_secret:
        raise ValueError(
            "[ERROR] Yahoo OAuth2 credentials not found.\n"
            "Set YAHOO_CLIENT_ID and YAHOO_CLIENT_SECRET in .env:\n"
            "YAHOO_CLIENT_ID=your-client-id\n"
            "YAHOO_CLIENT_SECRET=your-client-secret\n\n"
            "Get these from: https://developer.yahoo.com/apps/create/\n"
            "Requires 'mail-r' and 'mail-w' scopes approved by Yahoo.\n"
            f"Redirect URI must be: {REDIRECT_URI}"
        )
    
    return client_id, client_secret


def load_tokens() -> Optional[dict]:
    """Load stored tokens from file"""
    if TOKEN_FILE.exists():
        try:
            with open(TOKEN_FILE) as f:
                return json.load(f)
        except Exception:
            return None
    return None


def save_tokens(tokens: dict):
    """Save tokens to file"""
    if "expires_at" not in tokens and "expires_in" in tokens:
        tokens["expires_at"] = time.time() + tokens["expires_in"]
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)


def is_token_expired(tokens: dict) -> bool:
    """Check if access token is expired or expiring soon (5 min buffer)"""
    if "expires_at" not in tokens:
        return True
    return time.time() >= (tokens["expires_at"] - 300)


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict:
    """Refresh access token using refresh token"""
    data = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    response = requests.post(YAHOO_TOKEN_URL, data=data, timeout=30)
    response.raise_for_status()
    return response.json()


class CallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    def do_GET(self):
        global _auth_code, _auth_state
        if self.path.startswith(CALLBACK_PATH):
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
                <p>You can close this window and return to the terminal.</p>
                <script>setTimeout(() => window.close(), 3000);</script>
                </body></html>
                """
            else:
                error = query.get("error", ["Unknown error"])[0]
                html = f"""
                <html><body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1>❌ Authorization Failed</h1>
                <p>Error: {error}</p>
                <p>You can close this window.</p>
                </body></html>
                """
            self.wfile.write(html.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Suppress default log messages


def start_callback_server() -> HTTPServer:
    """Start local HTTP server to receive OAuth callback"""
    global _callback_server
    _callback_server = HTTPServer((CALLBACK_HOST, CALLBACK_PORT), CallbackHandler)
    thread = threading.Thread(target=_callback_server.serve_forever, daemon=True)
    thread.start()
    return _callback_server


def stop_callback_server():
    """Stop the callback server"""
    global _callback_server
    if _callback_server:
        _callback_server.shutdown()
        _callback_server.server_close()
        _callback_server = None


def authorization_code_flow(client_id: str, client_secret: str) -> dict:
    """
    Perform Authorization Code flow with local callback server.
    User visits URL in browser, authorizes, and is redirected to localhost:8080/callback
    """
    global _auth_code, _auth_state
    
    # Generate secure state parameter
    state = secrets.token_urlsafe(32)
    
    # Build authorization URL
    auth_params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(YAHOO_SCOPES),
        "state": state,
        "access_type": "offline",  # Request refresh token
    }
    auth_url = f"{YAHOO_AUTH_URL}?{urlencode(auth_params)}"
    
    # Start callback server
    start_callback_server()
    
    print(f"\n{'='*60}")
    print(f"YAHOO OAUTH2 AUTHORIZATION CODE FLOW")
    print(f"{'='*60}")
    print(f"\n1. Opening browser to authorize...")
    print(f"2. Sign in as sqc@bellsouth.net")
    print(f"3. Approve the requested permissions")
    print(f"4. You'll be redirected back automatically")
    print(f"\nIf browser doesn't open, visit manually:")
    print(f"\n  {auth_url}")
    print(f"\nWaiting for callback on {REDIRECT_URI}...")
    print(f"{'='*60}\n")
    
    # Try to open browser
    import webbrowser
    webbrowser.open(auth_url)
    
    # Wait for callback (with timeout)
    timeout = 300  # 5 minutes
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        if _auth_code is not None:
            break
        if _auth_state is not None and _auth_code is None:
            # Error occurred
            raise ValueError(f"Authorization failed: {_auth_state}")
        time.sleep(1)
    
    stop_callback_server()
    
    if not _auth_code:
        raise ValueError("Authorization timed out. Please try again.")
    
    # Verify state
    if _auth_state != state:
        raise ValueError("Invalid state parameter - possible CSRF attack")
    
    print(f"\n[OK] Authorization code received. Exchanging for tokens...")
    
    # Exchange code for tokens
    token_data = {
        "grant_type": "authorization_code",
        "code": _auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    
    response = requests.post(YAHOO_TOKEN_URL, data=token_data, timeout=30)
    response.raise_for_status()
    tokens = response.json()
    
    save_tokens(tokens)
    print(f"\n[OK] Tokens received and saved!")
    print(f"  Access token: {tokens.get('access_token', 'N/A')[:20]}...")
    print(f"  Refresh token: {'YES' if tokens.get('refresh_token') else 'NO'}")
    print(f"  Expires in: {tokens.get('expires_in', 'N/A')} seconds")
    
    return tokens


def get_valid_tokens() -> dict:
    """Get valid access token, refreshing if needed"""
    client_id, client_secret = load_client_credentials()
    tokens = load_tokens()
    
    if not tokens:
        print("[*] No stored tokens found. Starting authorization code flow...")
        return authorization_code_flow(client_id, client_secret)
    
    if is_token_expired(tokens):
        if "refresh_token" not in tokens:
            print("[*] No refresh token. Starting authorization code flow...")
            return authorization_code_flow(client_id, client_secret)
        
        print("[*] Access token expired. Refreshing...")
        try:
            new_tokens = refresh_access_token(client_id, client_secret, tokens["refresh_token"])
            tokens.update(new_tokens)
            save_tokens(tokens)
            print("[OK] Token refreshed successfully.")
            return tokens
        except Exception as e:
            print(f"[WARN] Token refresh failed: {e}")
            print("[*] Starting fresh authorization...")
            TOKEN_FILE.unlink(missing_ok=True)
            return authorization_code_flow(client_id, client_secret)
    
    return tokens


def build_xoauth2_string(email: str, access_token: str, host: str = "imap.mail.yahoo.com", port: int = 993) -> str:
    """
    Build XOAUTH2 SASL initial client response per RFC 7628
    Format: n,a=<email>\x01host=<host>\x01port=<port>\x01auth=Bearer <token>\x01\x01
    Then base64 encoded
    """
    ctrl_a = "\x01"
    auth_string = f"n,a={email}{ctrl_a}host={host}{ctrl_a}port={port}{ctrl_a}auth=Bearer {access_token}{ctrl_a}{ctrl_a}"
    return base64.b64encode(auth_string.encode("utf-8")).decode("ascii")


def get_yahoo_imap_connection(email: str = None) -> imaplib.IMAP4_SSL:
    """
    Get authenticated IMAP connection using OAuth2 XOAUTH2
    Returns connected and authenticated IMAP4_SSL object
    """
    tokens = get_valid_tokens()
    access_token = tokens["access_token"]
    
    if not email:
        email = "sqc@bellsouth.net"
    
    xoauth2_string = build_xoauth2_string(email, access_token)
    
    conn = imaplib.IMAP4_SSL("imap.mail.yahoo.com", 993)
    
    # Send IMAP ID command (recommended by Yahoo)
    conn.send(b'A001 ID ("name" "EmailAgent" "version" "1.0" "os" "Linux" "vendor" "Custom")\r\n')
    conn.readline()
    
    # Authenticate with XOAUTH2
    auth_cmd = f'A002 AUTHENTICATE XOAUTH2 {xoauth2_string}\r\n'.encode()
    conn.send(auth_cmd)
    response = conn.readline()
    
    if not response.startswith(b"A002 OK"):
        raise ValueError(f"XOAUTH2 authentication failed: {response.decode()}")
    
    print(f"[OK] Yahoo IMAP authenticated as {email} via OAuth2")
    return conn


def fetch_recent_emails_oauth2(service: imaplib.IMAP4_SSL, hours: int = 24, max_results: int = 50) -> list:
    """Fetch recent emails using existing authenticated connection"""
    try:
        service.select("INBOX")
        
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.strftime("%d-%b-%Y")
        
        status, msg_ids = service.search(None, f"SINCE {cutoff_str}")
        if status != "OK":
            return []
        
        msg_list = msg_ids[0].split()[-max_results:]
        if not msg_list:
            return []
        
        emails = []
        for msg_id in msg_list:
            try:
                status, msg_data = service.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue
                
                import email
                msg_bytes = msg_data[0][1]
                msg_obj = email.message_from_bytes(msg_bytes)
                
                subject = msg_obj.get("Subject", "No Subject")
                from_addr = msg_obj.get("From", "Unknown")
                date = msg_obj.get("Date", "")
                message_id = msg_obj.get("Message-ID", "")
                
                # Extract snippet
                snippet = ""
                if msg_obj.is_multipart():
                    for part in msg_obj.walk():
                        if part.get_content_type() == "text/plain":
                            try:
                                payload = part.get_payload(decode=True)
                                if isinstance(payload, bytes):
                                    snippet = payload.decode("utf-8", errors="ignore")
                                else:
                                    snippet = str(payload)
                                break
                            except:
                                continue
                else:
                    try:
                        payload = msg_obj.get_payload(decode=True)
                        if isinstance(payload, bytes):
                            snippet = payload.decode("utf-8", errors="ignore")
                        else:
                            snippet = str(payload)
                    except:
                        snippet = str(msg_obj.get_payload())
                
                snippet = snippet.replace("\r\n", " ").replace("\n", " ").strip()[:200]
                
                # Check unread
                status, flags = service.fetch(msg_id, "(FLAGS)")
                is_unread = False
                if status == "OK" and flags:
                    flag_data = flags[0]
                    if isinstance(flag_data, bytes):
                        is_unread = b"\\Seen" not in flag_data
                    else:
                        is_unread = "\\Seen" not in str(flag_data)
                
                emails.append({
                    "id": msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                    "from": from_addr,
                    "subject": subject,
                    "snippet": snippet,
                    "date": date,
                    "message_id": message_id,
                    "is_unread": is_unread,
                    "source": "Yahoo",
                })
            except Exception as e:
                print(f"[WARN] Error processing message {msg_id}: {e}")
                continue
        
        return emails
    
    except Exception as e:
        print(f"[ERROR] Error fetching Yahoo emails: {e}")
        raise


def delete_email_oauth2(service: imaplib.IMAP4_SSL, msg_id) -> bool:
    """Delete email using existing authenticated connection"""
    try:
        msg_id_str = msg_id.decode() if isinstance(msg_id, bytes) else str(msg_id)
        status = service.store(msg_id_str, "+FLAGS", "\\Deleted")
        if status[0] != "OK":
            raise ValueError(f"Failed to mark for deletion: {status}")
        service.expunge()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to delete email {msg_id}: {e}")
        raise


if __name__ == "__main__":
    # Test the OAuth2 flow
    try:
        print("[*] Testing Yahoo OAuth2 IMAP connection...")
        conn = get_yahoo_imap_connection()
        emails = fetch_recent_emails_oauth2(conn, hours=24, max_results=5)
        print(f"[OK] Fetched {len(emails)} emails")
        for e in emails[:3]:
            print(f"  - {e['from']}: {e['subject'][:60]}")
        conn.close()
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()