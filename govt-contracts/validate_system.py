#!/usr/bin/env python3
"""
Test script to validate email delivery with fresh token
"""

import os
import sys
import json
from datetime import datetime

# Add email-agent to path
sys.path.insert(0, '/home/scott/projects/email-agent')
os.chdir('/home/scott/projects/email-agent')

def test_token_validity():
    """Test if we can load a valid token"""
    print("🔍 Testing token validity...")
    
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    
    TOKEN_FILE = 'token.json'
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    
    if not os.path.exists(TOKEN_FILE):
        print("❌ No token.json found")
        return False
        
    try:
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        print(f"   Token loaded: {creds.token[:20] if creds.token else 'None'}...")
        print(f"   Token valid: {creds.valid}")
        print(f"   Token expired: {creds.expired}")
        if creds.expired and creds.refresh_token:
            print("   Attempting refresh...")
            creds.refresh(Request())
            print(f"   After refresh - valid: {creds.valid}")
            # Save refreshed token
            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())
            print("   Token refreshed and saved")
        return creds.valid
    except Exception as e:
        print(f"❌ Error loading token: {e}")
        return False

def test_gmail_service():
    """Test if we can build a valid Gmail service"""
    print("\n📧 Testing Gmail service creation...")
    try:
        from gmail_client import get_authenticated_service
        service = get_authenticated_service()
        profile = service.users().getProfile(userId='me').execute()
        print(f"✅ Gmail service connected!")
        print(f"   Email: {profile.get('emailAddress')}")
        print(f"   Messages total: {profile.get('messagesTotal')}")
        return True
    except Exception as e:
        print(f"❌ Gmail service failed: {e}")
        return False

def test_send_contract_report():
    """Test sending a minimal contract report"""
    print("\n📋 Testing contract report generation...")
    try:
        # Import the contract report script
        sys.path.insert(0, '/home/scott/projects/govt-contracts')
        os.chdir('/home/scott/projects/govt-contracts')
        
        # Try a dry run first
        import subprocess
        result = subprocess.run([
            sys.executable, 'send_contract_report.py', '--dry-run'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Contract report generation successful (dry-run)")
            print(f"   Output: {result.stdout[:200]}...")
            return True
        else:
            print(f"❌ Contract report failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing contract report: {e}")
        return False

def main():
    print("🧪 Brisar Contract Report System Validation")
    print("=" * 50)
    
    # Test 1: Token validity
    token_ok = test_token_validity()
    
    # Test 2: Gmail service
    gmail_ok = False
    if token_ok:
        gmail_ok = test_gmail_service()
    
    # Test 3: Contract report (only if auth works)
    report_ok = False
    if gmail_ok:
        report_ok = test_send_contract_report()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VALIDATION RESULTS:")
    print(f"   Token Validity:     {'✅ PASS' if token_ok else '❌ FAIL'}")
    print(f"   Gmail Service:      {'✅ PASS' if gmail_ok else '❌ FAIL'}")
    print(f"   Report Generation:  {'✅ PASS' if report_ok else '❌ FAIL'}")
    
    overall = token_ok and gmail_ok and report_ok
    print(f"\n🎯 Overall Status:     {'✅ SYSTEM READY' if overall else '❌ SYSTEM ISSUES'}")
    
    if not overall:
        print("\n🔧 RECOMMENDED ACTIONS:")
        if not token_ok:
            print("   1. Regenerate OAuth token using device flow")
        if not gmail_ok:
            print("   2. Check Gmail API permissions and quota")
        if not report_ok:
            print("   3. Verify SAM.gov API key and network connectivity")
    
    return 0 if overall else 1

if __name__ == '__main__':
    sys.exit(main())