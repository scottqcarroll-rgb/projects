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

### 4. Deprecated Cleanup (removed 2026-11-23)

`daily_cleanup.py` and its `setup_cron.py` installer were decommissioned.
The installer is now a stub that refuses to run, and nothing creates an
`email-cleanup.timer` any more.

The live mailbox services are:
- `sqc@bellsouth.net` — `/home/scott/inbox-cleanup/run_inbox_cleanup.sh` (cron 08:00)
- `scottqcarroll@gmail.com` — `run_email_agent.sh` (cron 09:00)

## Architecture

```
email_agent.py (active, cron 09:00 — Gmail summary only)
    ├── gmail_imap_client.py (IMAP + SMTP app-password client)
    ├── llm_classifier.py (LLM classification, falls back to email_classifier.py)
    ├── dashboard.py (HTML summary)
    └── email_api.py (Flask API on :5050 for dashboard actions)
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
| `setup_yahoo_oauth2.py` | Legacy OAuth2 setup wizard (no active consumer) |
| `setup_cron.py` | Disabled stub — installer for the retired cleanup agent |
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