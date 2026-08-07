# Email Agent — Yahoo Bellsouth Automated Junk Cleanup

Automated daily email cleanup for `sqc@bellsouth.net` using Yahoo OAuth2 IMAP.

## Quick Start

### 1. Create Yahoo Developer App (One-time)

1. Go to https://developer.yahoo.com/apps/create/
2. Create new app:
   - **Application Name**: Email Agent
   - **Application Type**: Server-side App
   - **Home Page URL**: http://localhost
   - **Redirect URI**: oob (out of band)
   - **Scopes**: Select `mail-r` and `mail-w` (Mail Read/Write)
3. Save → Get **Client ID** and **Client Secret**

### 2. Configure Credentials

```bash
cd /home/scott/projects/email-agent
cp .env.example .env
# Edit .env and add:
# YAHOO_CLIENT_ID=your-client-id
# YAHOO_CLIENT_SECRET=your-client-secret
```

### 3. Initial OAuth2 Authorization (One-time)

```bash
python3 setup_yahoo_oauth2.py
```

This will:
1. Show a URL and user code
2. You visit the URL on your computer/phone
3. Enter the code
4. Sign in as `sqc@bellsouth.net`
4. Approve permissions
5. Tokens saved to `yahoo_tokens.json` (auto-refreshed thereafter)

### 4. Test the Cleanup

```bash
python3 daily_cleanup.py
```

This will:
- Fetch last 24h emails from Yahoo (and Gmail if configured)
- Classify using rule-based keywords
- Delete "not_important" (junk) emails
- Send Telegram summary

### 5. Install as Daily Systemd Timer

```bash
python3 setup_cron.py
```

This creates:
- `email-cleanup.service` — runs the cleanup
- `email-cleanup.timer` — triggers daily at 6 AM

**Manage the timer:**
```bash
sudo systemctl status email-cleanup.timer     # Check status
sudo systemctl start email-cleanup.service    # Run manually now
sudo journalctl -u email-cleanup.service -f   # View live logs
sudo systemctl stop email-cleanup.timer       # Disable
```

## Architecture

```
daily_cleanup.py (main entry)
    ├── yahoo_client.py (OAuth2 IMAP wrapper)
    │     └── yahoo_oauth2.py (OAuth2: device flow + XOAUTH2 SASL)
    ├── gmail_client.py (Gmail API - optional)
    ├── email_classifier.py (Rule-based: keywords + senders)
    └── email_api.py (Flask API on :5050 for delete operations)
```

## Customizing Junk Rules

Edit `email_classifier.py`:

```python
# Add your spam keywords
NOT_IMPORTANT_KEYWORDS = [
    'unsubscribe', 'newsletter', 'promotion', 'sale', 'discount',
    'your custom spam keyword', 'another spam phrase',
]

# Add spam sender patterns
NOT_IMPORTANT_SENDERS = [
    'noreply@', 'no-reply@', 'marketing@', 'promo@', 'deals@',
    'spammy-sender', '@spamdomain.com',
]
```

## Files

| File | Purpose |
|------|---------|
| `yahoo_oauth2.py` | OAuth2 device flow + XOAUTH2 IMAP auth |
| `yahoo_client.py` | Wrapper using OAuth2 for email fetch/delete |
| `email_classifier.py` | Rule-based email importance classification |
| `email_api.py` | Flask API server for delete operations |
| `daily_cleanup.py` | Main cron job: fetch → classify → delete → notify |
| `setup_yahoo_oauth2.py` | One-time OAuth2 setup wizard |
| `setup_cron.py` | Install systemd timer |
| `.env` | Credentials (not in git) |
| `yahoo_tokens.json` | OAuth2 tokens (auto-managed) |

## Troubleshooting

**OAuth2 fails?**
- Verify Yahoo app has `mail-r` and `mail-w` scopes approved
- Check `.env` has correct `YAHOO_CLIENT_ID` and `YAHOO_CLIENT_SECRET`
- Delete `yahoo_tokens.json` and re-run `setup_yahoo_oauth2.py`

**IMAP auth fails?**
- Yahoo may take a few minutes to propagate new app credentials
- Ensure you're signing in as `sqc@bellsouth.net` during device flow

**Emails not deleting?**
- Check API server is running: `curl http://localhost:5050/status`
- Check logs: `sudo journalctl -u email-cleanup.service -f`

**Telegram not sending?**
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Test: `curl -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" -d "chat_id=$CHAT_ID&text=test"`

## Requirements

- Python 3.8+
- `requests`, `requests-oauthlib`, `flask`, `flask-cors`, `google-api-python-client`, `anthropic` (optional)

Install:
```bash
pip install -r requirements.txt
```