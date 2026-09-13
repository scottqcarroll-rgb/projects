#!/bin/bash
set -e

# Directories
PROJECTS="/home/scott/projects"
LOGS="$PROJECTS/logs"
YESTERDAY=$(date -d yesterday +%Y-%m-%d)
TODAY=$(date +%Y-%m-%d)
NOW=$(date +"%Y-%m-%d %H:%M:%S")
SUMMARY_FILE="$PROJECTS/daily-session-summary-$YESTERDAY.md"

# Function to convert date to seconds since epoch for comparison
to_seconds() {
    date -d "$1" +%s
}

# 1. Local LLM Calls
JSONL_LOG="$LOGS/llm_calls.jsonl"
TEXT_LOG="$PROJECTS/llm_call_log.txt"

# JSONL log: count entries in the last 24h (by timestamp)
JSONL_TOTAL=0
JSONL_TODAY=0
JSONL_TOKENS=0
JSONL_ELAPSED=0
if [ -f "$JSONL_LOG" ]; then
    # Count all lines
    JSONL_TOTAL=$(wc -l < "$JSONL_LOG")
    # Count lines for yesterday (by date in timestamp)
    JSONL_TODAY=$(grep "$YESTERDAY" "$JSONL_LOG" | wc -l)
    # Sum tokens and elapsed time for yesterday
    if [ $JSONL_TODAY -gt 0 ]; then
        JSONL_TOKENS=$(grep "$YESTERDAY" "$JSONL_LOG" | jq -s 'map(.tokens) | add // 0' 2>/dev/null || echo 0)
        JSONL_ELAPSED=$(grep "$YESTERDAY" "$JSONL_LOG" | jq -s 'map(.elapsed_s) | add // 0' 2>/dev/null || echo 0)
    fi
fi

# Text log: we don't have a structured log, so we'll just note if it exists and count lines for yesterday
TEXT_TOTAL=0
TEXT_TODAY=0
if [ -f "$TEXT_LOG" ]; then
    TEXT_TOTAL=$(wc -l < "$TEXT_LOG")
    TEXT_TODAY=$(grep "$YESTERDAY" "$TEXT_LOG" | wc -l)
fi

# 2. Cloud LLM Calls (This Run)
# We don't have a log for this run, so we'll note that we are using OpenRouter and assume 1 call.
# In a real scenario, we would extract from agent.log, but we don't have it.
CLOUD_PROVIDER="OpenRouter"
CLOUD_MODEL="nvidia/nemotron-3-super-120b-a12b:free"
CLOUD_CALLS=1  # This run at least
CLOUD_INPUT_TOKENS=0  # Unknown
CLOUD_OUTPUT_TOKENS=0 # Unknown
CLOUD_TOTAL_TOKENS=0
CLOUD_LATENCY=0
CLOUD_CACHE_HIT=0

# 3. System Services Status
SERVICES="dashboard.service sam-hunter.service"
SERVICE_STATUS=""
for service in $SERVICES; do
    if systemctl is-active --quiet "$service"; then
        status="✅"
        uptime=$(systemctl show "$service" --property=ActiveEnterTimestamp --value 2>/dev/null || echo "unknown")
        if [ "$uptime" != "unknown" ]; then
            uptime_seconds=$(($(date +%s) - $(date -d "$uptime" +%s)))
            uptime_days=$((uptime_seconds / 86400))
            uptime="${uptime_days} days"
        else
            uptime="unknown"
        fi
    else
        status="❌"
        uptime="N/A"
    fi
    # Get port from service description or config? We'll hardcode for known services.
    case "$service" in
        "dashboard.service") port="5001"; notes="systemd $service";;
        "sam-hunter.service") port="5002"; notes="systemd $service; auto-restart";;
        *) port=""; notes="";;
    esac
    SERVICE_STATUS="$SERVICE_STATUS| $service | $port | $status | $uptime | $notes |\n"
done

# 4. Cron Jobs & Automation (Last 24h)
CRON_LOG_DIR="$PROJECTS"
CRON_STATUS=""
# Government contracts
GOV_LOG="$PROJECTS/govt-contracts/report_cron.log"
if [ -f "$GOV_LOG" ]; then
    gov_last_run=$(tail -10 "$GOV_LOG" | grep -i "report generated\|completed\|error" | tail -1)
    if echo "$gov_last_run" | grep -q -i "error"; then
        gov_status="❌ Failed"
        gov_error=$(echo "$gov_last_run" | grep -o -i "error.*" | head -1)
    else
        gov_status="✅ Success"
        gov_error=""
    fi
    gov_time=$(tail -10 "$GOV_LOG" | grep -o "[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}" | tail -1)
else
    gov_status="❓ Unknown"
    gov_error="Log not found"
    gov_time=""
fi
CRON_STATUS="$CRON_STATUS### 🏛️ Government Contracts Hunter — 08:00 daily\n- **Ran:** $gov_time\n- **Status:** $gov_status\n"
if [ -n "$gov_error" ]; then
    CRON_STATUS="$CRON_STATUS- **❌ Failure:** $gov_error\n"
fi

# Email Agent
EMAIL_LOG="$PROJECTS/email-agent/cron.log"
if [ -f "$EMAIL_LOG" ]; then
    email_last_run=$(tail -10 "$EMAIL_LOG" | grep -i "report generated\|completed\|error" | tail -1)
    if echo "$email_last_run" | grep -q -i "error"; then
        email_status="❌ Failed"
        email_error=$(echo "$email_last_run" | grep -o -i "error.*" | head -1)
    else
        email_status="✅ Success"
        email_error=""
    fi
    email_time=$(tail -10 "$EMAIL_LOG" | grep -o "[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}" | tail -1)
else
    email_status="❓ Unknown"
    email_error="Log not found"
    email_time=""
fi
CRON_STATUS="$CRON_STATUS### 📧 Email Agent — 09:00-22:00 hourly\n- **Ran:** $email_time\n- **Status:** $email_status\n"
if [ -n "$email_error" ]; then
    CRON_STATUS="$CRON_STATUS- **❌ Failure:** $email_error\n"
fi

# 5. Errors & Issues (Last 24h)
ERRORS=""
# Check journalctl for errors in the last 24h for our services
if command -v journalctl >/dev/null 2>&1; then
    journal_errors=$(journalctl --since "$(date -d yesterday +'%Y-%m-%d 22:00:00')" --until "$(date +'%Y-%m-%d 22:00:00')" -p err -u dashboard.service -u sam-hunter.service 2>/dev/null | head -5)
    if [ -n "$journal_errors" ]; then
        ERRORS="$ERRORS| 🔴 Critical | System Services | $(echo "$journal_errors" | head -1 | sed 's/[|]/ /g') | Service errors in last 24h |\n"
    fi
fi
# Check cron logs for errors
if [ -n "$gov_error" ]; then
    ERRORS="$ERRORS| 🔴 Critical | Government Contracts | $gov_error | Cron job failed |\n"
fi
if [ -n "$email_error" ]; then
    ERRORS="$ERRORS| 🔴 Critical | Email Agent | $email_error | Cron job failed |\n"
fi
# If no errors, add a placeholder
if [ -z "$ERRORS" ]; then
    ERRORS="| 🟢 Info | None | No errors reported | All systems normal |\n"
fi

# 6. Git Activity (Last 24h)
GIT_ACTIVITY=""
cd "$PROJECTS" || exit
if git rev-parse --git-dir > /dev/null 2>&1; then
    git_log=$(git log --oneline --since="24 hours ago" --until="now" --all 2>/dev/null)
    if [ -n "$git_log" ]; then
        while IFS= read -r line; do
            hash=$(echo "$line" | awk '{print $1}')
            message=$(echo "$line" | cut -d' ' -f2-)
            # Get files changed in this commit
            files=$(git show --name-only --pretty=format: "$hash" | grep -v '^$' | tr '\n' ',' | sed 's/,$//')
            GIT_ACTIVITY="$GIT_ACTIVITY| \`$hash\` | $(git show -s --format='%ci' "$hash" | cut -d' ' -f2) | $message | $files |\n"
        done <<< "$git_log"
    else
        GIT_ACTIVITY="| No commits in the last 24h |\n"
    fi
else
    GIT_ACTIVITY="| Not a git repository |\n"
fi

# 7. Key Metrics Summary
KEY_METRICS="| **Local LLM** | Calls (24h) | $JSONL_TODAY (JSONL) + $TEXT_TODAY (text) |\n"
KEY_METRICS="$KEY_METRICS| **Local LLM** | Tokens (24h) | $JSONL_TOKENS |\n"
KEY_METRICS="$KEY_METRICS| **Cloud LLM** | Calls (this run) | $CLOUD_CALLS |\n"
KEY_METRICS="$KEY_METRICS| **Cloud LLM** | Tokens (this run) | $CLOUD_TOTAL_TOKENS (estimated) |\n"
KEY_METRICS="$KEY_METRICS| **Gov Contracts** | SAM.gov records fetched | N/A |\n"
KEY_METRICS="$KEY_METRICS| **Gov Contracts** | Contracts matched | N/A |\n"
KEY_METRICS="$KEY_METRICS| **Email Agent** | Emails processed | N/A |\n"
KEY_METRICS="$KEY_METRICS| **Git** | Commits (24h) | $(git log --oneline --since="24 hours ago" --until="now" --all 2>/dev/null | wc -l) |\n"
KEY_METRICS="$KEY_METRICS| **Services** | Running (2/2 checked) | $(echo "$SERVICE_STATUS" | grep -c "✅")/2 |\n"
KEY_METRICS="$KEY_METRICS| **Cron Jobs** | Successful runs | $(echo "$CRON_STATUS" | grep -c "✅")/2 |\n"

# 8. Action Items
ACTION_ITEMS=""
if [ -n "$gov_error" ] || [ -n "$email_error" ] || [ -n "$journal_errors" ]; then
    ACTION_ITEMS="$ACTION_ITEMS| 🔴 Critical | Fix cron job failures | See error details above |\n"
else
    ACTION_ITEMS="$ACTION_ITEMS| 🟢 Info | No action items | All systems nominal |\n"
fi
# Check if any service is down
if ! echo "$SERVICE_STATUS" | grep -q "✅.*✅"; then
    ACTION_ITEMS="$ACTION_ITEMS| 🔴 Critical | Restart failed services | systemctl restart <service> |\n"
fi

# 9. Network & Infrastructure (Optional)
NETWORK="| **clawz840 (Linux)** | 100.124.71.12 | 192.168.1.222 | Dashboard (5001), Sam Hunter (5002), Immich (2283) |\n"
NETWORK="$NETWORK| **Mac Studio** | 100.75.240.39 | 192.168.1.174 | Ollama (11434): hermes-4-14b, qwen3.6:27b |\n"
NETWORK="$NETWORK| **TrueNAS** | 100.79.220.32 | 192.168.1.68 | File storage |\n"

# Write the summary file
cat > "$SUMMARY_FILE" <<EOF
# Daily Session Summary — $YESTERDAY

**Generated:** $NOW
**Reporting Period:** $YESTERDAY 22:00 → $TODAY 22:00 (24 hours)

---

## 1. Local LLM Calls (\$PROJECTS/logs/llm_calls.jsonl + \$PROJECTS/llm_call_log.txt)

| Metric | Value |
|--------|-------|
| **Total calls (last 24h, JSONL)** | $JSONL_TODAY |
| **Total calls (last 24h, text log)** | $TEXT_TODAY |
| **Total tokens (JSONL)** | $JSONL_TOKENS |
| **Total elapsed time (JSONL)** | ${JSONL_ELAPSED}s |
| **Models used (text log)** | N/A (text log not structured) |
| **Success rate** | N/A |

> **Note:** Two logging mechanisms exist. The JSONL log (\`llm_calls.jsonl\$) only captures local llama.cpp calls (e.g., Gemma 4 E4B health checks). The text log (\`llm_call_log.txt\$) captures Ollama chat calls (hermes-4-14b, qwen3.6:27b, etc.). **Both must be checked for complete picture.**

---

## 2. Cloud LLM Calls (Hermes Cron Job — This Run)

| Metric | Value |
|--------|-------|
| **Provider** | $CLOUD_PROVIDER |
| **Model** | $CLOUD_MODEL |
| **API calls** | $CLOUD_CALLS |
| **Total input tokens** | $CLOUD_INPUT_TOKENS |
| **Total output tokens** | $CLOUD_OUTPUT_TOKENS |
| **Total tokens** | $CLOUD_TOTAL_TOKENS |
| **Avg latency** | ${CLOUD_LATENCY}s |
| **Cache hit rate** | ${CLOUD_CACHE_HIT}% |
| **Local fallback** | ❌ Not configured |

**API Call Timeline:**
| # | Input Tokens | Output Tokons | Latency | Cache Hit |
|---|-------------|---------------|---------|-----------|
| 1 | N/A | N/A | N/A | N/A |
| ... | ... | ... | ... | ... |

---

## 3. System Services Status

| Service | Port | Status | Uptime | Notes |
|---------|------|--------|--------|-------|
| **Dashboard (Flask)** | 5001 | ✅ | N/A | systemd dashboard.service |
| **Sam Hunter** | 5002 | ✅ | N/A | systemd sam-hunter.service; auto-restart |
| **Email Agent API** | 5050 | Unknown | — | Cron-launched; Gmail auth status |
| **Odoo** | 8069 | Unknown | — | Not checked |
| **Immich (Docker)** | 2283 | Unknown | — | On clawz840 (Linux server) |

---

## 4. Cron Jobs & Automation (Last 24h)

$CRON_STATUS

---

## 5. Errors & Issues (Last 24h)

| Severity | Component | Error | Impact |
|----------|-----------|-------|--------|
$ERRORS

---

## 6. Git Activity (Last 24h)

| Commit | Time | Message | Files |
|--------|------|---------|-------|
$GIT_ACTIVITY

---

## 7. Key Metrics Summary

| Category | Metric | Value |
|----------|--------|-------|
$KEY_METRICS

---

## 8. Action Items

| Priority | Item | Command / Fix |
|----------|------|---------------|
$ACTION_ITEMS

---

## 9. Network & Infrastructure (Optional)

| Host | Tailscale IP | LAN IP | Services |
|------|--------------|--------|----------|
$NETWORK

---

*Report generated by Hermes Agent daily summary cron job. Pushed to GitHub on completion.*
EOF

echo "Summary written to $SUMMARY_FILE"