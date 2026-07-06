import os
import json
import xmlrpc.client
import smtplib
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

ODOO_URL  = 'http://localhost:8069'
ODOO_DB   = 'odoo17_production'
ODOO_USER = os.getenv('ODOO_USER', 'Admin')
ODOO_PASS = os.getenv('ODOO_PASS', 'admin123')

SMTP_HOST = os.getenv('SMTP_HOST', 'smtp.turbify.net')
SMTP_PORT = int(os.getenv('SMTP_PORT', '465'))
SMTP_USER = os.getenv('SMTP_USER', '')
SMTP_PASS = os.getenv('SMTP_PASS', '')
NOTIFY_TO = os.getenv('NOTIFY_TO', 'sqc@bellsouth.net')

TELEGRAM_BOT_TOKEN = "8773175847:AAGE_xLobOi7pKZUaww7XTZKpg20YltgJjc"
TELEGRAM_CHAT_ID   = "7542619200"

FOLLOWUP_DIR  = os.path.join(os.path.dirname(__file__), 'pending-followups')
AGREEMENT_URL = os.getenv('AGREEMENT_URL', '[AGREEMENT LINK — ADD PANDADOC URL HERE]')


def queue_followup(lead_id, first_name, last_name, email):
    os.makedirs(FOLLOWUP_DIR, exist_ok=True)
    draft = {
        'lead_id':    lead_id,
        'first_name': first_name,
        'last_name':  last_name,
        'email':      email,
        'queued_at':  datetime.now().isoformat(),
        'sent':       False
    }
    path = os.path.join(FOLLOWUP_DIR, f'{lead_id}.json')
    with open(path, 'w') as f:
        json.dump(draft, f, indent=2)

    telegram_msg = (
        f"📋 Follow-up Queued — {first_name} {last_name}\n"
        f"📧 {email}\n"
        f"🔖 Lead #{lead_id}\n\n"
        f"Review, then tell me:\n"
        f"send plastic travel followup {lead_id}"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": telegram_msg},
            timeout=10
        )
    except Exception as e:
        app.logger.warning(f"Telegram followup queue alert failed: {e}")


def send_followup_email(lead_id):
    path = os.path.join(FOLLOWUP_DIR, f'{lead_id}.json')
    if not os.path.exists(path):
        return False, "No queued follow-up found for that lead ID"

    with open(path) as f:
        draft = json.load(f)

    if draft.get('sent'):
        return False, "Follow-up already sent"

    if not SMTP_USER or not SMTP_PASS:
        return False, "SMTP not configured"

    first_name = draft['first_name']
    email      = draft['email']

    plain = f"""Hi {first_name},

Thanks for reaching out to Plastic Travel. I've reviewed your inquiry and I'd love to help you start getting more out of every dollar your business spends.

Here's exactly what working together looks like:

━━━━━━━━━━━━━━━━━━━━━━
WHAT WE DO
━━━━━━━━━━━━━━━━━━━━━━

We build credit card reward strategies for business owners — identifying the right cards for your specific spend categories, stacking them for maximum points per dollar, and then showing you how to redeem those points through airline transfer partners at 2–5x the value of a standard portal booking.

Most clients are leaving 3–5x points on the table every month. We fix that.

━━━━━━━━━━━━━━━━━━━━━━
SERVICES & INVESTMENT
━━━━━━━━━━━━━━━━━━━━━━

Strategy Deep Dive                   $875
  A full audit of your cards, spend categories, and travel goals.
  You walk away with a complete, custom points strategy.

Trip Research Deposit                 $50
  We research real award availability for your specific trip.
  Credited toward the success fee when you book.

Trip Planning Success Fee             $450
  Paid only after we find the trip and you decide to book.
  Based on complexity and savings delivered.

━━━━━━━━━━━━━━━━━━━━━━
NEXT STEP — REVIEW THE AGREEMENT
━━━━━━━━━━━━━━━━━━━━━━

Before we schedule anything, I ask every client to sign a short consulting agreement. It takes about 2 minutes and makes sure we're aligned on scope and expectations.

Sign here: {AGREEMENT_URL}

Once signed, I'll send your payment link and we'll get your strategy session on the calendar.

Talk soon,
Scott
Plastic Travel
plastictravel.com
"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:6px;overflow:hidden;max-width:600px;width:100%;">

        <tr>
          <td style="background:#152638;padding:32px 48px;">
            <p style="margin:0;font-size:13px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#c9a84c;">PLASTIC TRAVEL</p>
          </td>
        </tr>

        <tr>
          <td style="padding:48px 48px 32px;">
            <p style="margin:0 0 24px;font-size:22px;font-weight:700;color:#152638;line-height:1.3;">Hi {first_name}, here&rsquo;s what working together looks like.</p>
            <p style="margin:0 0 20px;font-size:16px;color:#444;line-height:1.75;">Thanks for your inquiry. I&rsquo;ve reviewed it and I&rsquo;d love to help you start getting more out of every dollar your business spends.</p>

            <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:#c9a84c;">What We Do</p>
            <p style="margin:0 0 28px;font-size:16px;color:#444;line-height:1.75;">We build credit card reward strategies for business owners &mdash; identifying the right cards for your specific spend, stacking them for maximum points per dollar, and showing you how to redeem through airline transfer partners at <strong>2&ndash;5x the value</strong> of a standard portal booking.</p>

            <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:#c9a84c;">Services &amp; Investment</p>
            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom:28px;border-collapse:collapse;">
              <tr style="border-bottom:1px solid #eee;">
                <td style="padding:14px 0;font-size:15px;color:#152638;font-weight:600;">Strategy Deep Dive</td>
                <td style="padding:14px 0;font-size:15px;color:#c9a84c;font-weight:700;text-align:right;">$875</td>
              </tr>
              <tr style="border-bottom:1px solid #eee;">
                <td style="padding:14px 0;font-size:15px;color:#152638;font-weight:600;">Trip Research Deposit</td>
                <td style="padding:14px 0;font-size:15px;color:#c9a84c;font-weight:700;text-align:right;">$50</td>
              </tr>
              <tr>
                <td style="padding:14px 0;font-size:15px;color:#152638;font-weight:600;">Trip Planning Success Fee</td>
                <td style="padding:14px 0;font-size:15px;color:#c9a84c;font-weight:700;text-align:right;">$450</td>
              </tr>
            </table>

            <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:0.2em;text-transform:uppercase;color:#c9a84c;">Next Step &mdash; Review the Agreement</p>
            <p style="margin:0 0 24px;font-size:16px;color:#444;line-height:1.75;">Before we schedule anything, I ask every client to sign a short consulting agreement. It takes about 2 minutes and makes sure we&rsquo;re aligned on scope and expectations.</p>

            <table cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
              <tr>
                <td style="background:#c9a84c;border-radius:2px;padding:16px 36px;">
                  <a href="{AGREEMENT_URL}" style="color:#152638;font-size:13px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;text-decoration:none;">Review &amp; Sign the Agreement &rarr;</a>
                </td>
              </tr>
            </table>

            <p style="margin:0 0 4px;font-size:16px;color:#444;">Once signed, I&rsquo;ll send your payment link and we&rsquo;ll get your strategy session on the calendar.</p>
            <p style="margin:24px 0 4px;font-size:16px;color:#444;">Talk soon,</p>
            <p style="margin:4px 0 0;font-size:16px;font-weight:600;color:#152638;">Scott</p>
            <p style="margin:2px 0 0;font-size:14px;color:#888;">Plastic Travel</p>
          </td>
        </tr>

        <tr>
          <td style="background:#f9f7f4;border-top:1px solid #eee;padding:24px 48px;">
            <p style="margin:0;font-size:12px;color:#aaa;line-height:1.6;">You received this because you submitted a contact form at <a href="https://plastictravel.com" style="color:#c9a84c;text-decoration:none;">plastictravel.com</a>. Questions? Reply to this email.</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Your Plastic Travel Strategy — Next Steps, {first_name}"
    msg['From']    = f'Scott at Plastic Travel <{SMTP_USER}>'
    msg['To']      = email

    msg.attach(MIMEText(plain, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, email, msg.as_string())

    draft['sent'] = True
    draft['sent_at'] = datetime.now().isoformat()
    with open(path, 'w') as f:
        json.dump(draft, f, indent=2)

    return True, "Sent"


def send_telegram_alert(first_name, last_name, email, notes):
    message = (
        f"🔔 New Plastic Travel Lead\n\n"
        f"👤 {first_name} {last_name}\n"
        f"📧 {email}\n"
        f"📝 {notes or '(no notes)'}"
    )
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message},
            timeout=10
        )
    except Exception as e:
        app.logger.warning(f"Telegram alert failed: {e}")


def create_odoo_lead(first_name, last_name, email, notes):
    common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
    uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
    if not uid:
        raise Exception('Odoo authentication failed')

    models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
    lead_id = models.execute_kw(ODOO_DB, uid, ODOO_PASS, 'crm.lead', 'create', [{
        'name':         f'Website Inquiry — {first_name} {last_name}',
        'partner_name': f'{first_name} {last_name}',
        'email_from':   email,
        'description':  notes or '(no notes provided)',
        'type':         'lead',
        'source_id':    False,
    }])
    return lead_id


def send_notification(first_name, last_name, email, notes, lead_id=None):
    if not SMTP_USER or not SMTP_PASS:
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'New Plastic Travel Lead #{lead_id}: {first_name} {last_name}'
    msg['From']    = SMTP_USER
    msg['To']      = NOTIFY_TO

    body = f"""New contact form submission on plastictravel.com

Lead #: {lead_id}
Name:   {first_name} {last_name}
Email:  {email}

Notes:
{notes or '(none)'}

To send the follow-up email, tell Claude:
send plastic travel followup {lead_id}

This lead has been added to your Odoo CRM.
"""
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, NOTIFY_TO, msg.as_string())


def send_confirmation(first_name, email):
    if not SMTP_USER or not SMTP_PASS:
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "You're on the list — Plastic Travel"
    msg['From']    = f'Scott at Plastic Travel <{SMTP_USER}>'
    msg['To']      = email

    plain = f"""Hi {first_name},

Thanks for reaching out — I got your message and I'm looking forward to connecting.

I'll be in touch within one business day to find a time that works for a quick call. We'll take a look at your current card setup, talk through where your biggest spend categories are, and give you an honest picture of what you might be leaving on the table.

No pressure, no pitch — just a real conversation.

Talk soon,
Scott
Plastic Travel
plastictravel.com
"""

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f4f4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:40px 20px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:6px;overflow:hidden;max-width:600px;width:100%;">

        <tr>
          <td style="background:#152638;padding:32px 48px;">
            <p style="margin:0;font-size:13px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#c9a84c;">PLASTIC TRAVEL</p>
          </td>
        </tr>

        <tr>
          <td style="padding:48px 48px 32px;">
            <p style="margin:0 0 24px;font-size:22px;font-weight:700;color:#152638;line-height:1.3;">Hi {first_name}, you're on the list.</p>
            <p style="margin:0 0 20px;font-size:16px;color:#444;line-height:1.75;">Thanks for reaching out — I got your message and I'm looking forward to connecting.</p>
            <p style="margin:0 0 20px;font-size:16px;color:#444;line-height:1.75;">I'll be in touch within <strong>one business day</strong> to find a time that works for a quick call. We'll take a look at your current card setup, talk through where your biggest spend categories are, and give you an honest picture of what you might be leaving on the table.</p>
            <p style="margin:0 0 32px;font-size:16px;color:#444;line-height:1.75;">No pressure, no pitch — just a real conversation.</p>

            <p style="margin:0;font-size:16px;color:#444;">Talk soon,</p>
            <p style="margin:4px 0 0;font-size:16px;font-weight:600;color:#152638;">Scott</p>
            <p style="margin:2px 0 0;font-size:14px;color:#888;">Plastic Travel</p>
          </td>
        </tr>

        <tr>
          <td style="background:#f9f7f4;border-top:1px solid #eee;padding:24px 48px;">
            <p style="margin:0;font-size:12px;color:#aaa;line-height:1.6;">You received this because you submitted a contact form at <a href="https://plastictravel.com" style="color:#c9a84c;text-decoration:none;">plastictravel.com</a>.</p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""

    msg.attach(MIMEText(plain, 'plain'))
    msg.attach(MIMEText(html, 'html'))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, email, msg.as_string())


@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.get_json(silent=True) or {}

    first_name = data.get('first_name', '').strip()
    last_name  = data.get('last_name', '').strip()
    email      = data.get('email', '').strip()
    notes      = data.get('notes', '').strip()

    if not first_name or not email:
        return jsonify({'error': 'first_name and email are required'}), 400

    try:
        lead_id = create_odoo_lead(first_name, last_name, email, notes)
    except Exception as e:
        app.logger.error(f'Odoo error: {e}')
        return jsonify({'error': 'Could not save to CRM'}), 500

    try:
        send_notification(first_name, last_name, email, notes, lead_id)
    except Exception as e:
        app.logger.warning(f'Email notification failed: {e}')

    send_telegram_alert(first_name, last_name, email, notes)
    queue_followup(lead_id, first_name, last_name, email)

    try:
        send_confirmation(first_name, email)
    except Exception as e:
        app.logger.warning(f'Confirmation email failed: {e}')

    return jsonify({'success': True, 'lead_id': lead_id})


@app.route('/api/followup/send/<int:lead_id>', methods=['POST'])
def trigger_followup(lead_id):
    success, message = send_followup_email(lead_id)
    if success:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": f"✅ Follow-up sent for Lead #{lead_id}"},
            timeout=10
        )
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'message': message}), 400


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5051)
