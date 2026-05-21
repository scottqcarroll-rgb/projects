import os
import xmlrpc.client
import smtplib
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
NOTIFY_TO = os.getenv('NOTIFY_TO', 'scott@plastictravel.com')


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


def send_notification(first_name, last_name, email, notes):
    if not SMTP_USER or not SMTP_PASS:
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'New Plastic Travel Lead: {first_name} {last_name}'
    msg['From']    = SMTP_USER
    msg['To']      = NOTIFY_TO

    body = f"""New contact form submission on plastictravel.com

Name:   {first_name} {last_name}
Email:  {email}

Notes:
{notes or '(none)'}

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
        send_notification(first_name, last_name, email, notes)
    except Exception as e:
        app.logger.warning(f'Email notification failed: {e}')

    try:
        send_confirmation(first_name, email)
    except Exception as e:
        app.logger.warning(f'Confirmation email failed: {e}')

    return jsonify({'success': True, 'lead_id': lead_id})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5051)
