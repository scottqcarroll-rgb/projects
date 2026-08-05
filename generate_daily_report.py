#!/usr/bin/env python3
"""
Generate daily session summary report with LLM call metrics and push to GitHub.
"""
import os
import json
import subprocess
from datetime import datetime, timedelta

BASE = "/home/scott/projects"
TOTAL_FILE = os.path.join(BASE, "total_calls.txt")
DAILY_DIR = os.path.join(BASE, "daily_counts")
LOG_FILE = os.path.join(BASE, "logs", "llm_calls.jsonl")

def _read_int(path, default=0):
    try:
        with open(path) as f:
            return int(f.read().strip() or 0)
    except Exception:
        return default

def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_display = datetime.now().strftime("%A, %B %d, %Y")
    
    # 1. totals
    all_time = _read_int(TOTAL_FILE)

    # compute 30-day average
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

    today_file = os.path.join(DAILY_DIR, f"{today_str}.json")
    today_calls = _read_int(today_file)
    pct = int((today_calls / (all_time or 1)) * 100)
    hourly_rate = int((today_calls / 24) if today_calls else 0)

    # 2. timestamps list for today
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

    # 3. build metrics block
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

    # 4. Generate comprehensive daily session summary
    summary_path = os.path.join(BASE, f"daily_session_summary_{today_str}.md")

    summary_content = f"""# Daily Session Summary - {today_display}

## 🗓️ Session Date
{today_display}

## ✅ Major Tasks Completed
*   **Scheduled cron job execution**: Daily LLM call metrics report generation and daily session summary generation
*   **LLM call metrics aggregation**: Aggregated LLM call metrics from logs

## 🧠 Major Decisions / Established Workflows
*   Continued automated daily session summary generation via cron job
*   LLM call metrics tracking continues via automated logging

## 📊 LLM-Call Metrics Summary
{block.strip()}

## ➡️ Next Steps / Ongoing Items
*   Continue daily cron job execution for metrics collection
*   Monitor LLM usage patterns and optimize as needed
*   Continue automated daily session summary generation

---
*Summary generated autonomously by scheduled cron job.*
"""

    with open(summary_path, "w") as f:
        f.write(summary_content)

    print(f"=== Summary written to {summary_path} ===")

    # 5. Git add/commit/push
    subprocess.run(["git", "add", summary_path], cwd=BASE, check=False)
    commit_msg = f"Update daily session summary for {today_str}"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE, check=False)
    subprocess.run(["git", "push", "origin", "master"], cwd=BASE, check=False)

    print("Git push completed.")

if __name__ == "__main__":
    main()