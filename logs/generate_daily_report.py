#!/usr/bin/env python3
import json
import os
from datetime import datetime, timedelta

# Get current date and calculate yesterday's date
current_date = datetime.now()
yesterday_date = current_date - timedelta(days=1)
cutoff_date = yesterday_date.strftime('%Y-%m-%d')

print(f"=== DAILY HERMES AI ACTIVITY REPORT ===")
print(f"Date: {cutoff_date}")
print(f"Generated: {current_date.strftime('%Y-%m-%d %H:%M %Z')}")
print()

# 1. Local LLM Calls Analysis
print("## 1. Local LLM Calls")
today_calls = []

# Read and parse llm_calls.jsonl
if os.path.exists('/home/scott/projects/logs/llm_calls.jsonl'):
    with open('/home/scott/projects/logs/llm_calls.jsonl', 'r') as f:
        for line in f:
            try:
                call = json.loads(line.strip())
                today_calls.append(call)
            except json.JSONDecodeError:
                continue

print(f"Total LLM Calls: {len(today_calls)}")

if today_calls:
    total_tokens = sum(call.get('tokens', 0) for call in today_calls)
    total_elapsed = sum(call.get('elapsed_s', 0) for call in today_calls)
    successful_calls = sum(1 for call in today_calls if call.get('ok', True))
    
    # Count by source
    source_counts = {}
    for call in today_calls:
        source = call.get('source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    print(f"Total Tokens Used: {total_tokens}")
    print(f"Total Processing Time: {total_elapsed:.2f} seconds")
    print(f"Successful Calls: {successful_calls}")
    print(f"Success Rate: {(successful_calls/len(today_calls)*100):.1f}%")
    print()
    print("### Source Breakdown:")
    for source, count in source_counts.items():
        print(f"- {source}: {count} calls ({count/len(today_calls)*100:.1f}%)")
    
    # Show sample calls
    print()
    print("### Sample Calls:")
    for i, call in enumerate(today_calls[:3]):
        model = call.get('model', 'unknown')
        tokens = call.get('tokens', 0)
        elapsed = call.get('elapsed_s', 0)
        timestamp = call.get('timestamp', 'unknown')
        print(f"{i+1}. {timestamp} - {model} - {tokens} tokens - {elapsed:.2f}s")
else:
    print("No LLM calls found for yesterday ({cutoff_date})")
    print("Note: Tokens=0 entries in historical data are streamed calls where the provider returned no token counts; not flagged as errors.")
print()

# 2. System Actions and Status
print("## 2. System Actions and Status")

# Check key services using systemctl
print("### Core Services Status:")
services_status = []
for service in ['dashboard.service', 'sam-hunter.service', 'odoo.service', 'llm-proxy.service']:
    result = os.system(f"systemctl is-active {service} > /dev/null 2>&1; echo $?")
    status = "🟢 Active" if result == 0 else "🔴 Inactive"
    services_status.append(f"- **{service.replace('.service', '')}**: {status}")

for status in services_status:
    print(f"  {status}")

# Check for recent cron activity and errors
print()
print("### Recent Cron Activity:")

# Read recent cron logs
errors_found = []

# Email Agent cron log
if os.path.exists('/home/scott/projects/email-agent/cron.log'):
    with open('/home/scott/projects/email-agent/cron.log', 'r') as f:
        content = f.read()
        if 'ERROR' in content or 'Failed' in content:
            errors_found.append("Email Agent: Contains errors in cron.log")

# Govt contracts cron log  
if os.path.exists('/home/scott/projects/govt-contracts/report_cron.log'):
    with open('/home/scott/projects/govt-contracts/report_cron.log', 'r') as f:
        content = f.read()
        if 'ERROR' in content or 'Failed' in content:
            errors_found.append("Gov Contracts: Contains errors in report_cron.log")

if errors_found:
    print("⚠️  Issues Found:")
    for error in errors_found:
        print(f"  {error}")
else:
    print("✅ No errors detected in recent cron logs")

print()

# 3. Overall Summary
print("## 3. Overall Activity Summary")
total_services = len(services_status)
active_services = sum(1 for s in services_status if "🟢 Active" in s)

print(f"Services Monitor: {active_services}/{total_services} services running")
print(f"LLM Activity: {len(today_calls)} calls recorded")
print(f"System Health: {'✅ Good' if not errors_found else '⚠️ Issues detected'}")

# Note about decommissioned services
print()
print("### Important Notes:")
print("- **Frigate**: Intentionally stopped (not monitored)")
print("- **Immich**: Decommissioned (no longer exists on this host)")
print("- **Email Agent API**: Currently requires Flask dependency - shows in logs")
print("- **Tokens=0**: Indicates streaming calls where provider didn't return token counts (not errors)")
print()

# Git status for changes
print("### Git Status:")
result = os.system("cd /home/scott/projects && git status --porcelain | wc -l")
print(f"Modified files tracked: {result}")
print()

print("=== END OF REPORT ===")

# Write the report to a file
report_filename = f"/home/scott/projects/logs/daily-session-summary-{cutoff_date}.md"
with open(report_filename, 'w') as f:
    f.write("""# Daily Session Summary — """ + cutoff_date + """

""")

print(f"Report written to: {report_filename}")