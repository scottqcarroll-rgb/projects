#!/usr/bin/env python3
"""Generate a detailed daily LLM‑call report and update the Daily Session Summary.

This script:
1. Reads the log file `logs/llm_calls.jsonl`.
2. Aggregates:
   - Total calls (all‑time via `total_calls.txt`).
   - Today's calls.
   - % of today's calls vs total.
   - 30‑day average.
   - Hourly rate (est.)
   - Every call timestamp.
3. Appends a formatted block to `daily_session_summary_<today>.md`.
4. Adds, commits, and pushes the markdown file to GitHub.

The cron job set-up will run this script at 22:00 (10 pm) each day.
"""

import os
import json
from datetime import datetime, timedelta
import subprocess

BASE = "/home/scott/projects"
TOTAL_FILE = os.path.join(BASE, "total_calls.txt")
DAILY_DIR = os.path.join(BASE, "daily_counts")
LOG_FILE = os.path.join(BASE, "logs", "llm_calls.jsonl")
SUMMARY_DIR = BASE
def _read_int(path, default=0):
    try:
        with open(path) as f:
            return int(f.read().strip() or 0)
    except Exception:
        return default

def _write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

# 1. totals
all_time = _read_int(TOTAL_FILE)

yesterday = datetime.now() - timedelta(days=1)
# compute 30‑day average
last_30_days = []
for i in range(30):
    day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
    day_file = os.path.join(DAILY_DIR, f"{day}.json")
    try:
        with open(day_file) as f:
            last_30_days.append(int(f.read().strip() or 0))
    except Exception:
        pass
avg_30 = int(sum(last_30_days) / max(1, len(last_30_days))) if last_30_days else 0

today_str = datetime.now().strftime("%Y-%m-%d")
today_file = os.path.join(DAILY_DIR, f"{today_str}.json")
today_calls = _read_int(today_file)
%share = int((today_calls / (all_time or 1)) * 100)
hourly_rate = int((today_calls / 24) if today_calls else 0)

# 2. timestamps list
calls = []
if os.path.exists(LOG_FILE):
    with open(LOG_FILE) as f:
        for line in f:
            try:
                obj = json.loads(line)
                if obj.get("date") == today_str:
                    calls.append(obj.get("timestamp"))
            except Exception:
                pass
calls.sort()

# 3. build block
block = f"\n### 📊 LLM‑Call Metrics (as of {today_str})\n"
block += f"- **All‑time total**: {all_time}\n"
block += f"- **Today's calls**: {today_calls}\n"
block += f"- **Share of total**: {pct}%\n"
block += f"- **30‑day average**: {avg_30} per day\n"
block += f"- **Hourly rate** (est.): {hourly_rate}\n"
if calls:
    block += "- **Timestamps**:\n"
    for ts in calls:
        block += f"  - {ts}\n"
else:
    block += "- **No calls today**\n"

# 4. Append to summary file
summary_path = os.path.join(SUMMARY_DIR, f"daily_session_summary_{today_str}.md")
with open(summary_path, "a") as f:
    f.write(block)

# 5. Git add/commit/push
subprocess.run(["git", "add", summary_path], check=False)
commit_msg = f"Update LLM metrics for {today_str}"
subprocess.run(["git", "commit", "-m", commit_msg], check=False)
subprocess.run(["git", "push", "origin", "main"], check=False)

print("Daily LLM report generated and pushed.")
