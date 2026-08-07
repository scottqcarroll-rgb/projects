#!/usr/bin/env python3
"""
Yahoo OAuth2 Setup Script
Run this ONCE to complete the initial device authorization flow.
After this, tokens are saved and auto-refreshed.

Usage:
    python3 setup_yahoo_oauth2.py
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from yahoo_oauth2 import get_valid_tokens, load_client_credentials


def main():
    print("=" * 60)
    print("YAHOO OAUTH2 SETUP FOR sqc@bellsouth.net")
    print("=" * 60)
    
    # Check credentials
    try:
        client_id, client_secret = load_client_credentials()
        print(f"[OK] Client ID loaded: {client_id[:8]}...")
        print(f"[OK] Client Secret loaded: {client_secret[:8]}...")
    except ValueError as e:
        print(f"[ERROR] {e}")
        print("\nPlease edit .env and add:")
        print("  YAHOO_CLIENT_ID=your-client-id")
        print("  YAHOO_CLIENT_SECRET=your-client-secret")
        print("\nGet these from: https://developer.yahoo.com/apps/create/")
        print("Select scopes: mail-r, mail-w")
        return 1
    
    print("\n[*] Starting device authorization flow...")
    print("This will open a browser on YOUR computer/phone.")
    print("You need to:")
    print("  1. Visit the URL shown")
    print("  2. Enter the user code shown")
    print("  3. Sign in as sqc@bellsouth.net")
    print("  4. Approve the permissions")
    print()
    
    try:
        tokens = get_valid_tokens()
        print(f"\n[SUCCESS] OAuth2 setup complete!")
        print(f"Access token: {tokens.get('access_token', 'N/A')[:20]}...")
        print(f"Refresh token: {tokens.get('refresh_token', 'N/A')[:20]}...")
        print(f"Expires in: {tokens.get('expires_in', 'N/A')} seconds")
        print(f"\nTokens saved to: yahoo_tokens.json")
        print("\nYou can now run the daily cleanup:")
        print("  python3 daily_cleanup.py")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Setup failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())