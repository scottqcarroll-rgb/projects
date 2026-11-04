#!/usr/bin/env python3
import json
from datetime import datetime, timedelta

# Load LLM calls data
calls = []
with open('/home/scott/projects/logs/llm_calls.jsonl', 'r') as f:
    for line in f:
        try:
            calls.append(json.loads(line.strip()))
        except:
            continue

print(f"Total LLM calls: {len(calls)}")
print(f"OpenWebUI calls: {len([c for c in calls if c.get('source') == 'openwebui'])}")
print(f"Proxy calls: {len([c for c in calls if c.get('source') == 'proxy'])}")
print(f"Models: {set(c.get('model') for c in calls)}")

# Find recent dates
for call in calls:
    if 'timestamp' in call:
        try:
            call_date = datetime.fromisoformat(call['timestamp'].replace('Z', '+00:00'))
            print(f"Call at {call['timestamp']} date: {call_date.strftime('%Y-%m-%d')}")
        except:
            pass

# Calculate summary
total_tokens = sum(c.get('tokens', 0) for c in calls)
total_ok = sum(1 for c in calls if c.get('ok') == True)
print(f"\nSummary:")
print(f"Total tokens: {total_tokens}")
print(f"Successful calls: {total_ok}/{len(calls)}")

# Today's calls (using current date from system)
import subprocess
result = subprocess.run(['date'], capture_output=True, text=True)
print(f"\nSystem date: {result.stdout.strip()}")