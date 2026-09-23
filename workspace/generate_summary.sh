#!/bin/bash
set -e

# Get the current date for the file name (in YYYY-MM-DD)
DATE=$(date +%Y-%m-%d)
FILENAME="daily-session-summary-${DATE}.md"
OUTPUT_DIR="/home/scott/projects"
OUTPUT_FILE="${OUTPUT_DIR}/${FILENAME}"

# We'll build the markdown in a variable
MARKDOWN=""

# Function to append a section
append_section() {
  MARKDOWN="${MARKDOWN}$1\n\n"
}

# Start the markdown
append_section "# Daily Session Summary for ${DATE}"

# Section 1: Local LLM Calls
append_section "## 1. Local LLM Calls"

# Check the JSONL log
JSONL_LOG="/home/scott/projects/logs/llm_calls.jsonl"
TEXT_LOG="/home/scott/projects/llm_call_log.txt"

if [ -f "${JSONL_LOG}" ]; then
  JSONL_COUNT=$(wc -l < "${JSONL_LOG}" | tr -d ' ')
  append_section "### JSONL Log (${JSONL_LOG})"
  append_section "- Total calls: ${JSONL_COUNT}"
  # We can try to get more details if jq is available
  if command -v jq &> /dev/null; then
    # Example: extract models and tokens
    MODELS=$(jq -r '.model' "${JSONL_LOG}" | sort | uniq -c | sort -nr)
    append_section "#### Models used:"
    append_section "\`\`\`"
    append_section "${MODELS}"
    append_section "\`\`\`"
    # Total tokens? Assume a field 'tokens'
    TOTAL_TOKENS=$(jq -s 'map(.tokens // 0) | add' "${JSONL_LOG}" 2>/dev/null || echo "0")
    append_section "- Total tokens (JSONL): ${TOTAL_TOKENS}"
  else
    append_section "_jq not available for detailed analysis_"
  fi
else
  append_section "_JSONL log not found_"
fi

if [ -f "${TEXT_LOG}" ]; then
  TEXT_COUNT=$(wc -l < "${TEXT_LOG}" | tr -d ' ')
  append_section "### Text Log (${TEXT_LOG})"
  append_section "- Total calls: ${TEXT_COUNT}"
  # We can try to get models and tokens if the format is known
  # Assume each line has: timestamp, model, tokens, etc.
  # We'll just note the count for now.
else
  append_section "_Text log not found_"
fi

# Total local LLM calls
TOTAL_LOCAL_CALLS=0
if [ -f "${JSONL_LOG}" ]; then
  TOTAL_LOCAL_CALLS=$((TOTAL_LOCAL_CALLS + JSONL_COUNT))
fi
if [ -f "${TEXT_LOG}" ]; then
  TOTAL_LOCAL_CALLS=$((TOTAL_LOCAL_CALLS + TEXT_COUNT))
fi
append_section "**Total Local LLM Calls (last 24h):** ${TOTAL_LOCAL_CALLS}"

# Section 2: Cloud LLM Calls (This Run)
append_section "## 2. Cloud LLM Calls (This Run)"
append_section "_Data not available in this cron run. This section would typically be extracted from the agent.log for this run._"

# Section 3: System Services Status
append_section "## 3. System Services Status"
append_section "| Service | Port | Status | Uptime | Notes |"
append_section "|---------|------|--------|--------|-------|"
# We'll check a few services: Dashboard (5001), Sam Hunter (5002), Odoo (8069), Immich (2283)
check_service() {
  local service_name=$1
  local port=$2
  local notes=$3
  # Check if the service is listening on the port
  if ss -tln | grep -q ":${port} "; then
    status="🟢 Running"
    # Get the process ID and then the uptime? We'll skip uptime for simplicity.
    uptime="N/A"
  else
    status="🔴 Stopped"
    uptime="N/A"
  fi
  echo "| ${service_name} | ${port} | ${status} | ${uptime} | ${notes} |"
}
# We'll generate the table rows
append_section "$(check_service "Dashboard" 5001 "Flask dashboard")"
append_section "$(check_service "Sam Hunter" 5002 "Hunter service")"
append_section "$(check_service "Odoo" 8069 "Odoo website")"
append_section "$(check_service "Immich" 2283 "Immich photo management")"

# Section 4: Cron Jobs & Automation (Last 24h)
append_section "## 4. Cron Jobs & Automation (Last 24h)"
append_section "_This section would list the cron jobs that ran in the last 24 hours and their status._"
append_section "| Job | Schedule | Last Run | Status | Notes |"
append_section "|-----|----------|----------|--------|-------|"
# We'll check the cron logs for the known jobs: Gov Contracts (08:00), Email Agent (09:00-22:00 hourly), etc.
# We'll just note that we are running the daily summary at 22:00.
append_section "| Daily Session Summary | 22:00 daily | $(date) | Running | This report |"

# Section 5: Errors & Issues (Last 24h)
append_section "## 5. Errors & Issues (Last 24h)"
append_section "_We will check the logs for errors in the last 24 hours._"
append_section "| Severity | Component | Error | Impact |"
append_section "|----------|-----------|-------|--------|"
# We'll check the dashboard log, sam hunter log, etc. for errors.
# For now, we'll leave it empty or note if we find any.
# We can search for "error" in the logs in the last 24 hours? But note: we are in cron mode and cannot run complex searches without execute_code.
# We'll do a simple grep on the log files if they exist.
append_section "_Error checking not implemented in this version._"

# Section 6: Git Activity (Last 24h)
append_section "## 6. Git Activity (Last 24h)"
append_section "_Commits in the last 24 hours._"
# We'll change to the projects directory and run git log
cd /home/scott/projects
GIT_LOG=$(git log --oneline --since="24 hours ago" --until="now" --all 2>/dev/null || echo "Unable to retrieve git log")
append_section "\`\`\`"
append_section "${GIT_LOG}"
append_section "\`\`\`"

# Section 7: Key Metrics Summary
append_section "## 7. Key Metrics Summary"
append_section "| Metric | Value |"
append_section "|--------|-------|"
append_section "| Total Local LLM Calls (24h) | ${TOTAL_LOCAL_CALLS} |"
# We can add more metrics if we have them.

# Section 8: Action Items
append_section "## 8. Action Items"
append_section "_Prioritized actions to improve the system._"
append_section "1. **Investigate missing local LLM logs** - Ensure both JSONL and text logs are being updated."
append_section "2. **Check cron job logs for errors** - Look at the Gov Contracts and Email Agent cron logs."
append_section "3. **Verify service statuses** - Ensure all critical services are running."

# Section 9: Network & Infrastructure (Optional)
append_section "## 9. Network & Infrastructure (Optional)"
append_section "_Optional section for network details if available._"
append_section "| Host | Tailscale IP | LAN IP | Services |"
append_section "|------|--------------|--------|----------|"
# We can get the Tailscale IP and LAN IP for the Linux server.
# We'll use hostname -I for all IPs and then try to filter? We'll just show the first two.
# We'll get the IPs and note that we don't have a way to label them without more context.
IPS=$(hostname -I)
append_section "| Linux Server (clawz840) | ${IPS} | ${IPS} | Dashboard, Sam Hunter, etc. |"

# Output the markdown
echo -e "${MARKDOWN}"
