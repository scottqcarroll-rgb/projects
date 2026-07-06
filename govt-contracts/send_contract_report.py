#!/usr/bin/env python3
"""
Daily Government Contract Report — Brisar Investments LLC
Pulls from SAM.gov, categorizes by NAICS, sends HTML report to Gmail.
"""

import os
import sys
import json
import base64
from datetime import datetime, date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_AGENT_DIR = '/home/scott/projects/email-agent'
sys.path.insert(0, EMAIL_AGENT_DIR)
os.chdir(EMAIL_AGENT_DIR)

from gmail_client import get_authenticated_service

SAM_KEY_FILE = '/home/scott/projects/.env.samgov'
RECIPIENT    = 'scottqcarroll@gmail.com'
PROSPECT_DIR = '/home/scott/projects/govt-contracts/prospect-lists'

WINDOW_DAYS   = 30
RECORD_LIMIT  = 1000
AWARD_CEILING = 350000

CATEGORIES = {
    'Facility & Grounds Services': {
        'codes':  ['561210', '561720', '561730', '561740', '238910'],
        'bg':     '#f0fdf4',
        'border': '#22c55e',
        'accent': '#16a34a',
        'icon':   '🏗️',
    },
    'Security & Pest Control': {
        'codes':  ['561612', '561710'],
        'bg':     '#fef2f2',
        'border': '#ef4444',
        'accent': '#dc2626',
        'icon':   '🛡️',
    },
    'Waste & Environmental Services': {
        'codes':  ['562111', '562112', '562211', '562998'],
        'bg':     '#fff7ed',
        'border': '#f97316',
        'accent': '#ea580c',
        'icon':   '♻️',
    },
    'Textile & Linen Services': {
        'codes':  ['812331', '812332'],
        'bg':     '#eff6ff',
        'border': '#3b82f6',
        'accent': '#2563eb',
        'icon':   '🧺',
    },
}

SERVICE_KEYWORDS = [
    'maintenance', 'service', 'repair', 'support', 'cleaning', 'disposal',
    'grounds', 'inspection', 'installation', 'management',
]


def load_api_key():
    with open(SAM_KEY_FILE) as f:
        for line in f:
            if line.startswith('SAM_API_KEY='):
                return line.strip().split('=', 1)[1]
    raise ValueError("SAM_API_KEY not found in .env.samgov")


def fetch_contracts(api_key):
    import urllib.request
    today     = date.today()
    from_date = (today - timedelta(days=WINDOW_DAYS)).strftime('%m/%d/%Y')
    to_date   = today.strftime('%m/%d/%Y')
    url = (
        f'https://api.sam.gov/opportunities/v2/search'
        f'?api_key={api_key}'
        f'&ptype=o,k'
        f'&awardCeiling={AWARD_CEILING}'
        f'&postedFrom={from_date}'
        f'&postedTo={to_date}'
        f'&limit={RECORD_LIMIT}'
        f'&offset=0'
    )
    req = urllib.request.Request(url, headers={'User-Agent': 'BrisarInvestments/1.0'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())


def score_contract(h):
    title    = h.get('title', '').lower()
    setaside = h.get('typeOfSetAsideDescription', '') or ''
    deadline = h.get('responseDeadLine', '') or h.get('archiveDate', '')
    ceiling  = h.get('awardCeiling')
    perf     = h.get('placeOfPerformance') or {}
    city     = perf.get('city', {}).get('name', '') if perf else ''
    state    = perf.get('state', {}).get('code', '') if perf else ''

    pts = 0
    if any(k in title for k in SERVICE_KEYWORDS): pts += 3
    if 'small business' in setaside.lower():       pts += 2
    if city or state:                              pts += 1

    try:
        val = float(str(ceiling).replace(',', '')) if ceiling else None
        if val and val < 25000:     pts += 2
        elif val and val <= 100000: pts += 1
    except Exception:
        val = None

    days_away = None
    if deadline:
        try:
            dl = datetime.strptime(deadline[:10], '%Y-%m-%d').date()
            days_away = (dl - date.today()).days
            if days_away >= 21:   pts += 3   # comfortable window
            elif days_away >= 14: pts += 1   # tight but workable
            elif days_away >= 7:  pts -= 2   # too tight to find a sub
            else:                 pts -= 5   # not actionable
        except Exception:
            pass

    return pts, days_away


def build_contract(h):
    pts, days_away = score_contract(h)
    title    = h.get('title', 'Untitled')
    agency   = (h.get('fullParentPathName') or '').split('.')[0].title() or 'Unknown'
    perf     = h.get('placeOfPerformance') or {}
    city     = perf.get('city', {}).get('name', '') if perf else ''
    state    = perf.get('state', {}).get('code', '') if perf else ''
    location = f'{city}, {state}'.strip(', ') or 'Not listed'
    setaside = h.get('typeOfSetAsideDescription', '') or 'None'
    naics    = h.get('naicsCode', '') or 'N/A'
    notice   = h.get('noticeId', '')
    link     = f'https://sam.gov/opp/{notice}/view' if notice else '#'

    contacts = h.get('pointOfContact') or []
    poc_parts = []
    for poc in contacts[:2]:
        name  = poc.get('fullName', '')
        email = poc.get('email', '')
        phone = poc.get('phone', '')
        if name or email:
            poc_parts.append({'name': name, 'email': email, 'phone': phone})
    poc = poc_parts
    deadline = h.get('responseDeadLine', '') or h.get('archiveDate', '')
    ceiling  = h.get('awardCeiling')

    if deadline:
        try:
            dl     = datetime.strptime(deadline[:10], '%Y-%m-%d').date()
            dl_str = f'{dl.strftime("%m/%d/%Y")} ({days_away} days away)'
        except Exception:
            dl_str = deadline[:10]
    else:
        dl_str = 'Not listed'

    try:
        val_str = f'${float(str(ceiling).replace(",", "")):,.0f}' if ceiling else 'Not listed'
    except Exception:
        val_str = 'Not listed'

    return dict(
        title=title, agency=agency, location=location,
        setaside=setaside, naics=str(naics), link=link,
        deadline=dl_str, value=val_str, poc=poc,
        score=pts, days_away=days_away,
        urgent=(days_away is not None and days_away <= 14),
    )


def bucket_contracts(raw):
    all_codes = {code for cat in CATEGORIES.values() for code in cat['codes']}
    bucketed  = {name: [] for name in CATEGORIES}

    for h in raw.get('opportunitiesData', []):
        naics = str(h.get('naicsCode', ''))
        if naics not in all_codes:
            continue
        c = build_contract(h)
        for cat_name, cat in CATEGORIES.items():
            if naics in cat['codes']:
                bucketed[cat_name].append(c)

    for cat_name in bucketed:
        bucketed[cat_name].sort(key=lambda x: -x['score'])

    return bucketed


def make_table(contracts):
    if not contracts:
        return '''<div style="padding:20px;text-align:center;color:#6b7280;border:2px dashed #d1d5db;
                              border-radius:8px;background:#f9fafb;margin-bottom:4px">
            No contracts found in this category for the current 30-day window.<br>
            <span style="font-size:12px">This category will populate as matching solicitations are posted.</span>
        </div>'''

    rows = ''
    for i, c in enumerate(contracts, 1):
        urgent_flag  = ' <span style="color:#dc2626;font-size:11px;font-weight:bold">⚠️ UNDER 14 DAYS</span>' if c['urgent'] else ''
        score_color  = '#16a34a' if c['score'] >= 7 else '#2563eb' if c['score'] >= 5 else '#6b7280'
        row_bg       = '#fff7f7' if c['urgent'] else '#ffffff'
        poc_html = ''
        for p in c.get('poc', []):
            name  = p.get('name','')
            email = p.get('email','')
            phone = p.get('phone','')
            if email:
                poc_html += f'<a href="mailto:{email}" style="color:#2563eb;font-size:11px">{name or email}</a>'
                if phone: poc_html += f' &nbsp;·&nbsp; <span style="color:#6b7280;font-size:11px">{phone}</span>'
                poc_html += '<br>'
        rows += f'''
        <tr style="background:{row_bg};border-bottom:1px solid #e5e7eb">
          <td style="padding:12px 14px;vertical-align:top">
            <span style="color:#9ca3af;font-size:12px">#{i}&nbsp;</span>
            <strong style="color:#111827">{c["title"]}</strong>{urgent_flag}<br>
            <span style="color:#6b7280;font-size:12px">{c["agency"]}</span>
          </td>
          <td style="padding:12px 8px;color:#374151;font-size:13px;white-space:nowrap;vertical-align:top">{c["location"]}</td>
          <td style="padding:12px 8px;color:#374151;font-size:13px;white-space:nowrap;vertical-align:top">{c["value"]}</td>
          <td style="padding:12px 8px;color:#374151;font-size:13px;white-space:nowrap;vertical-align:top">{c["deadline"]}</td>
          <td style="padding:12px 8px;font-size:11px;vertical-align:top">
            <span style="background:#f3f4f6;color:#374151;padding:2px 8px;border-radius:10px;border:1px solid #e5e7eb">{c["setaside"][:40]}</span>
          </td>
          <td style="padding:12px 8px;vertical-align:top;font-size:11px">{poc_html or '<span style="color:#9ca3af">Not listed</span>'}</td>
          <td style="padding:12px 8px;text-align:center;vertical-align:top">
            <strong style="color:{score_color};font-size:15px">{c["score"]}/10</strong>
          </td>
          <td style="padding:12px 8px;vertical-align:top">
            <a href="{c["link"]}" style="color:#2563eb;font-size:13px;font-weight:500">View →</a>
          </td>
        </tr>'''

    return f'''<table width="100%" cellpadding="0" cellspacing="0"
        style="border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;margin-bottom:4px">
      <tr style="background:#f9fafb;color:#6b7280;font-size:11px;text-transform:uppercase;letter-spacing:.05em">
        <th style="padding:9px 14px;text-align:left;border-bottom:1px solid #e5e7eb">Contract</th>
        <th style="padding:9px 8px;text-align:left;border-bottom:1px solid #e5e7eb">Location</th>
        <th style="padding:9px 8px;text-align:left;border-bottom:1px solid #e5e7eb">Value</th>
        <th style="padding:9px 8px;text-align:left;border-bottom:1px solid #e5e7eb">Deadline</th>
        <th style="padding:9px 8px;text-align:left;border-bottom:1px solid #e5e7eb">Set-Aside</th>
        <th style="padding:9px 8px;text-align:left;border-bottom:1px solid #e5e7eb">Contact</th>
        <th style="padding:9px 8px;text-align:center;border-bottom:1px solid #e5e7eb">Score</th>
        <th style="padding:9px 8px;text-align:left;border-bottom:1px solid #e5e7eb">Link</th>
      </tr>
      {rows}
    </table>'''


def build_html(bucketed, run_date):
    total_matched = sum(len(v) for v in bucketed.values())
    urgent_total  = sum(1 for v in bucketed.values() for c in v if c['urgent'])

    cat_sections = ''
    for cat_name, cat in CATEGORIES.items():
        contracts  = bucketed[cat_name]
        count_str  = f'{len(contracts)} contract{"s" if len(contracts) != 1 else ""}' if contracts else 'No matches today'
        naics_list = ' &nbsp;·&nbsp; '.join(cat['codes'])
        cat_sections += f'''
        <div style="margin-bottom:36px">
          <div style="background:{cat["bg"]};border-left:5px solid {cat["border"]};
                      border-radius:8px 8px 0 0;padding:16px 20px;margin-bottom:2px;
                      display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap">
            <div>
              <span style="font-size:20px">{cat["icon"]}</span>
              <strong style="color:#111827;font-size:17px;margin-left:8px">{cat_name}</strong><br>
              <span style="color:#6b7280;font-size:12px;margin-left:30px">NAICS: {naics_list}</span>
            </div>
            <span style="color:{cat["accent"]};font-weight:bold;font-size:15px">{count_str}</span>
          </div>
          {make_table(contracts)}
        </div>'''

    return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="margin:0;padding:24px;background:#f3f4f6;color:#111827;
             font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif">
<div style="max-width:1100px;margin:0 auto">

  <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;
              padding:28px;margin-bottom:28px;box-shadow:0 1px 3px rgba(0,0,0,.06)">
    <h1 style="margin:0 0 4px;font-size:24px;color:#111827">
      📋 Brisar Investments — Government Contract Report
    </h1>
    <p style="margin:0 0 20px;color:#6b7280">
      Under $350,000 &nbsp;|&nbsp; Nationwide &nbsp;|&nbsp; Posted last {WINDOW_DAYS} days &nbsp;|&nbsp; {run_date}
    </p>
    <div style="display:flex;gap:20px;flex-wrap:wrap">
      <div style="text-align:center;background:#f0fdf4;border-radius:8px;padding:12px 20px;min-width:90px">
        <div style="font-size:28px;font-weight:bold;color:#16a34a">{total_matched}</div>
        <div style="font-size:12px;color:#6b7280">Matched</div>
      </div>
      <div style="text-align:center;background:#fff7ed;border-radius:8px;padding:12px 20px;min-width:90px">
        <div style="font-size:28px;font-weight:bold;color:#ea580c">{urgent_total}</div>
        <div style="font-size:12px;color:#6b7280">Closing ≤7 Days</div>
      </div>
      <div style="text-align:center;background:#faf5ff;border-radius:8px;padding:12px 20px;min-width:90px">
        <div style="font-size:28px;font-weight:bold;color:#7c3aed">4</div>
        <div style="font-size:12px;color:#6b7280">Categories</div>
      </div>
      <div style="text-align:center;background:#eff6ff;border-radius:8px;padding:12px 20px;min-width:90px">
        <div style="font-size:28px;font-weight:bold;color:#2563eb">8</div>
        <div style="font-size:12px;color:#6b7280">NAICS Tracked</div>
      </div>
    </div>
  </div>

  <!-- Scoring Legend -->
  <div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;
              padding:24px 28px;margin-bottom:28px;box-shadow:0 1px 3px rgba(0,0,0,.06)">
    <h2 style="margin:0 0 16px;font-size:16px;color:#111827">📊 Score Legend (1–10)</h2>
    <p style="margin:0 0 12px;font-size:13px;color:#6b7280">
      Each contract is scored on factors that make it easier to win and more actionable for Brisar.
    </p>
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-bottom:16px">
      <div style="background:#f0fdf4;border:1px solid #22c55e;border-radius:8px;padding:10px 16px;min-width:100px;text-align:center">
        <div style="font-size:20px;font-weight:bold;color:#16a34a">8–10</div>
        <div style="font-size:12px;color:#16a34a;font-weight:600">Strong</div>
        <div style="font-size:11px;color:#6b7280">Bid this</div>
      </div>
      <div style="background:#eff6ff;border:1px solid #3b82f6;border-radius:8px;padding:10px 16px;min-width:100px;text-align:center">
        <div style="font-size:20px;font-weight:bold;color:#2563eb">5–7</div>
        <div style="font-size:12px;color:#2563eb;font-weight:600">Decent</div>
        <div style="font-size:11px;color:#6b7280">Review it</div>
      </div>
      <div style="background:#fff7ed;border:1px solid #f97316;border-radius:8px;padding:10px 16px;min-width:100px;text-align:center">
        <div style="font-size:20px;font-weight:bold;color:#ea580c">3–4</div>
        <div style="font-size:12px;color:#ea580c;font-weight:600">Marginal</div>
        <div style="font-size:11px;color:#6b7280">Low priority</div>
      </div>
      <div style="background:#faf5ff;border:1px solid #a855f7;border-radius:8px;padding:10px 16px;min-width:100px;text-align:center">
        <div style="font-size:20px;font-weight:bold;color:#7c3aed">1–2</div>
        <div style="font-size:12px;color:#7c3aed;font-weight:600">Skip</div>
        <div style="font-size:11px;color:#6b7280">Too risky</div>
      </div>
    </div>
    <table width="100%" cellpadding="0" cellspacing="0"
           style="border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;font-size:13px">
      <tr style="background:#f9fafb">
        <th style="padding:8px 14px;text-align:left;color:#6b7280;font-size:11px;text-transform:uppercase;border-bottom:1px solid #e5e7eb">Factor</th>
        <th style="padding:8px 14px;text-align:center;color:#6b7280;font-size:11px;text-transform:uppercase;border-bottom:1px solid #e5e7eb">Points</th>
      </tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 14px;color:#111827">Service-type title (maintenance, cleaning, repair, grounds, inspection, etc.)</td><td style="padding:8px 14px;text-align:center;color:#16a34a;font-weight:bold">+3</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6;background:#f9fafb"><td style="padding:8px 14px;color:#111827">Deadline 21+ days away (comfortable — time to find sub, review scope, submit bid)</td><td style="padding:8px 14px;text-align:center;color:#16a34a;font-weight:bold">+3</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 14px;color:#111827">Small Business Set-Aside (reserved for small businesses only)</td><td style="padding:8px 14px;text-align:center;color:#16a34a;font-weight:bold">+2</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6;background:#f9fafb"><td style="padding:8px 14px;color:#111827">Contract value under $25,000 (smallest, easiest to win)</td><td style="padding:8px 14px;text-align:center;color:#16a34a;font-weight:bold">+2</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 14px;color:#111827">Contract value $25,000–$100,000</td><td style="padding:8px 14px;text-align:center;color:#16a34a;font-weight:bold">+1</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6;background:#f9fafb"><td style="padding:8px 14px;color:#111827">Deadline 14–20 days away (tight but workable)</td><td style="padding:8px 14px;text-align:center;color:#16a34a;font-weight:bold">+1</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6"><td style="padding:8px 14px;color:#111827">Has a listed location (city/state)</td><td style="padding:8px 14px;text-align:center;color:#16a34a;font-weight:bold">+1</td></tr>
      <tr style="border-bottom:1px solid #f3f4f6;background:#fff7f7"><td style="padding:8px 14px;color:#111827">Deadline 7–13 days away (too tight to find a subcontractor)</td><td style="padding:8px 14px;text-align:center;color:#dc2626;font-weight:bold">−2</td></tr>
      <tr style="background:#fff7f7"><td style="padding:8px 14px;color:#111827">Deadline under 7 days (not actionable — not enough time to bid)</td><td style="padding:8px 14px;text-align:center;color:#dc2626;font-weight:bold">−5</td></tr>
    </table>
    <p style="margin:10px 0 0;font-size:12px;color:#9ca3af">
      The score ranks contract terms — not whether Brisar can perform the work. That decision is always yours.
    </p>
  </div>

  {cat_sections}

  <p style="margin-top:24px;color:#9ca3af;font-size:12px;text-align:center">
    Brisar Investments LLC &nbsp;|&nbsp; Automated Daily Report &nbsp;|&nbsp; {run_date}
  </p>
</div>
</body></html>'''


def save_report(bucketed, run_date):
    date_slug = date.today().strftime('%Y-%m-%d')
    path      = os.path.join(PROSPECT_DIR, f'{date_slug}-categorized.md')
    lines     = [f'# Brisar Contract Report — {run_date}\n']
    for cat_name, contracts in bucketed.items():
        lines.append(f'\n## {cat_name} ({len(contracts)} contracts)')
        for i, c in enumerate(contracts, 1):
            lines.append(f'\n### #{i} — Score {c["score"]}/10 — {c["title"]}')
            lines.append(f'- Agency: {c["agency"]}')
            lines.append(f'- Location: {c["location"]}')
            lines.append(f'- Value: {c["value"]}')
            lines.append(f'- Deadline: {c["deadline"]}')
            lines.append(f'- Set-Aside: {c["setaside"]}')
            lines.append(f'- NAICS: {c["naics"]}')
            lines.append(f'- Link: {c["link"]}')
    with open(path, 'w') as f:
        f.write('\n'.join(lines))
    print(f'[OK] Report saved: {path}')


def send_email(service, subject, html_body):
    msg            = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = RECIPIENT
    msg['To']      = RECIPIENT
    msg.attach(MIMEText(html_body, 'html'))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId='me', body={'raw': raw}).execute()
    print(f'[OK] Email sent to {RECIPIENT}')


def main():
    run_date = date.today().strftime('%B %d, %Y')
    print(f'[{datetime.now().strftime("%H:%M:%S")}] Starting contract report — {run_date}')

    api_key  = load_api_key()
    print(f'[...] Fetching up to {RECORD_LIMIT} records from SAM.gov (last {WINDOW_DAYS} days)...')
    raw      = fetch_contracts(api_key)
    total    = raw.get('totalRecords', 0)
    returned  = len(raw.get('opportunitiesData', []))
    print(f'[OK] SAM.gov: {total} total available, {returned} returned')

    raw_path  = os.path.join(PROSPECT_DIR, f'{date.today().strftime("%Y-%m-%d")}-raw.json')
    with open(raw_path, 'w') as f:
        json.dump(raw, f)
    print(f'[OK] Raw data saved: {raw_path}')

    bucketed      = bucket_contracts(raw)
    total_matched = sum(len(v) for v in bucketed.values())
    print(f'[OK] Matched {total_matched} contracts across 4 categories')
    for cat_name, contracts in bucketed.items():
        print(f'     {cat_name}: {len(contracts)}')

    save_report(bucketed, run_date)

    html         = build_html(bucketed, run_date)
    gmail        = get_authenticated_service()
    urgent_total = sum(1 for v in bucketed.values() for c in v if c['urgent'])
    subject      = f'📋 Brisar Contracts {run_date} — {total_matched} matched (under $350K), {urgent_total} closing soon'
    send_email(gmail, subject, html)


if __name__ == '__main__':
    main()
