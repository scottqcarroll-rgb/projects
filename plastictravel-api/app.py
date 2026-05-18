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
NOTIFY_TO = os.getenv('NOTIFY_TO', 'scottqcarroll@gmail.com')


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

    return jsonify({'success': True, 'lead_id': lead_id})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5051)
