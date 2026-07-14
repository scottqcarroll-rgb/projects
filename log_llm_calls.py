#!/usr/bin/env python3
"""
Local LLM Call Tracker
- Tracks total calls and daily counts
- Stores call timestamps in JSONL format for metric generation
- Writes a simple text log for the dashboard API
"""
import os
import json
from datetime import datetime

# Configuration
BASE = "/home/scott/projects"
TOTAL_COUNT_FILE = os.path.join(BASE, "total_calls.txt")
DAILY_COUNT_FILE = os.path.join(BASE, "daily_counts", f"{datetime.now().strftime('%Y-%m-%d')}.json")
LOG_FILE = os.path.join(BASE, "logs", "llm_calls.jsonl")
TEXT_LOG_FILE = os.path.join(BASE, "llm_call_log.txt")

# Ensure directories exist
os.makedirs(os.path.dirname(TOTAL_COUNT_FILE), exist_ok=True)
os.makedirs(os.path.dirname(DAILY_COUNT_FILE), exist_ok=True)
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Atomic counter increments
with open(TOTAL_COUNT_FILE, "r+") as f:
    total = int(f.read().strip() or "0") + 1
    f.seek(0)
    f.write(str(total))
    f.truncate()

with open(DAILY_COUNT_FILE, "r+") as f:
    daily = int(f.read().strip() or "0") + 1
    f.seek(0)
    f.write(str(daily))
    f.truncate()

# Log call details with timestamp (JSONL)
log_entry = {
    "timestamp": datetime.now().isoformat(timespec="seconds"),
    "date": datetime.now().strftime("%Y-%m-%d"),
    "model": "gemma-4-E4B-it-Q4_K_M.gguf",
    "tokens": 1,  # TODO: Replace with actual token count
    "elapsed_s": 0.5,  # TODO: Actual timing from LLM response
    "ok": True
}
with open(LOG_FILE, "a") as f:
    f.write(json.dumps(log_entry) + "\n")

# Also write simple text format for dashboard API: [timestamp] model=xxx prompt_tokens=xxx completion_tokens=xxx
with open(TEXT_LOG_FILE, "a") as f:
    ts = datetime.now().isoformat(timespec="seconds")
    f.write(f"[{ts}] model=gemma-4-E4B-it-Q4_K_M.gguf prompt_tokens=0 completion_tokens=0\n")

# Export current totals
def get_totals():
    return {"all_time": total, "today": daily}

if __name__ == "__main__":
    print(f"Logged LLM call: total={total}, today={daily}")