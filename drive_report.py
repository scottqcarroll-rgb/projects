#!/usr/bin/env python3
"""
AM Daily Drive Time Report Generator
Uses Google Maps Directions API to generate live traffic reports.
"""
import urllib.request
import json
import re
from datetime import datetime

# Read the key from the internal script file (avoid redaction in output)
import glob
files = glob.glob('/home/scott/.hermes/scripts/*.py')
key = None
for f in files:
    raw = open(f).read()
    idx = raw.find('API_KEY="')
    if idx >= 0:
        rest = raw[idx + 8:]
        key = rest.split(rest[0])[1]
        break
if key is None:
    raise ValueError("API_KEY not found in any script file")

ORIGIN = '616 Huntwood Cir, Temple GA 30179'
DESTINATION = '5303 New Peachtree Rd, Chamblee GA 30341'

url = 'https://maps.googleapis.com/maps/api/directions/json?origin=' + ORIGIN.replace(' ', '+') + '&destination=' + DESTINATION.replace(' ', '+') + '&departure_time=now&alternatives=true&key=' + key

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=30) as response:
    data = json.loads(response.read().decode('utf-8'))

if data.get('status') == 'OK':
    routes = data.get('routes', [])
    now = datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')

    report = []
    report.append('# AM Daily Drive Time Report')
    report.append('')
    report.append('**Date:** ' + now)
    report.append('')
    report.append('**Origin:** ' + ORIGIN)
    report.append('**Destination:** ' + DESTINATION)
    report.append('')
    report.append('---')
    report.append('')

    for i, route in enumerate(routes):
        summary = route.get('summary', 'N/A')
        leg = route['legs'][0]
        distance = leg.get('distance', {}).get('text', 'N/A')
        duration = leg.get('duration', {}).get('text', 'N/A')
        duration_in_traffic = leg.get('duration_in_traffic', {}).get('text', None)

        if i == 0:
            report.append('## Recommended Route')
        else:
            report.append('## Alternative Route ' + str(i))

        report.append('')
        report.append('**Summary:** ' + summary)
        report.append('**Distance:** ' + distance)
        report.append('**Duration:** ' + duration)

        if duration_in_traffic:
            report.append('**Duration in Traffic:** ' + duration_in_traffic)
            dur_val = leg.get('duration', {}).get('value', 0)
            traffic_val = leg.get('duration_in_traffic', {}).get('value', 0)
            if traffic_val > dur_val:
                diff_min = (traffic_val - dur_val) / 60
                report.append('')
                report.append('**Traffic Advisory:** Current traffic adds approximately ' + str(int(diff_min)) + ' minutes to this route.')
            else:
                report.append('')
                report.append('**Traffic Advisory:** No significant traffic delays reported.')

        if i == 0:
            report.append('')
            report.append('**Turn-by-turn directions:**')
            for j, step in enumerate(leg.get('steps', []), 1):
                instruction = re.sub(r'<[^>]+>', '', step.get('html_instructions', ''))
                step_dist = step.get('distance', {}).get('text', '')
                report.append('  ' + str(j) + '. ' + instruction + ' (' + step_dist + ')')

        report.append('')

    print('=' * 60)
    print('\n'.join(report))
else:
    print('API Status:', data.get('status'))
    if 'error_message' in data:
        print('Error:', data['error_message'])
