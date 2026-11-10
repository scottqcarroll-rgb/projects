# Daily Session Summary — 2026-11-09

## 📊 Local LLM Activity

| Metric | Value |
|--------|-------|
| **Total Calls** | 0 |
| **Total Tokens** | 0 |
| **Total Latency** | 0.0 s |
| **Proxy (llm-proxy:11435)** | 0 |
| **OpenWebUI Sync** | 0 |
| **Success Rate** | 0.0% |

> **Note**: No local LLM calls recorded for 2026-11-08 (the 24h period covered by this report) in `llm_calls.jsonl`. Data file exists but contains no entries for this date.

## ⚙️ Service Status (as of 22:00 EDT)

| Service | Status | Uptime | Notes |
|---------|--------|--------|-------|
| **Dashboard** (port 5001) | 🟢 Active | 1 week 5 days | systemd: `dashboard.service` |
| **Sam Hunter** (port 5002) | ❓ Not monitored | — | Service status unknown |
| **Odoo** (port 8069) | 🟢 Active | 3 weeks 5 days | systemd: `odoo.service` |
| **Frigate** | ⏹️ Stopped | — | Intentionally stopped; not monitored |
| **Immich** (port 2283) | 🚫 Decommissioned | — | No longer exists on this host |
| **Email Agent API** (port 5050) | 🟢 Active | Since 08:00 | Manual execution; automated cron failing |
| **LLM Proxy** (port 11435) | ❌ Not Running | Since 09:00 | Failed: Service not found |
| **Ollama (Mac Studio)** | 🟢 Available | — | 7 models installed, 0 currently loaded |

## 🤖 Cron Jobs (Last 24h)

### 22:00 — Daily Session Summary (`generate_daily_summary.py`)
- **Status**: ❓ Not executed
- **Note**: No cron output file found for this period (daily-session-summary-2026-11-09.md did not exist)

### 23:00 — Daily Session Reset (`reset_session.py`)
- **Status**: ❓ Not executed
- **Note**: No cron output file found for this period

### 08:00 — Email Agent (`run_email_agent.sh`)
- **Status**: ❌ FAILED
- **Error**: Automated execution failed (missing Flask dependency)
- **Impact**: Email sending functionality remains unavailable

### 05:xx (hourly) — LLM WebUI Sync (`llm_webui_sync.py`)
- **Status**: Running hourly at minute 5
- **Syncs OpenWebUI usage**: Continues (last seen: 2026-10-28)

### 00:00 — Midnight GitHub Backup (`git_backup.sh`)
- **Status**: ❓ Not executed
- **Note**: No cron output file found for this period

## 📈 System Health

### LLM Calls Data Availability
- **File**: `/home/scott/projects/logs/llm_calls.jsonl`
- **Status**: File exists (21,201 bytes) but contains no entries for the current 24-hour period
- **Most recent entry**: 2026-10-28T09: leto: active (overdue for update)

### Automated Monitoring
- **LLM Proxy Service**: Not running (systemctl status shows service not found)
- **Scheduled Activities**: Daily session summary cron job appears to have missed today's execution

## 📈 Summary

No local LLM activity recorded for 2026-11-08. System services operational with minor issues:

- **Dashboard** and **Odoo** services remain healthy
- **Email Agent** continues to fail due to missing Flask dependency in automated execution
- **LLM Proxy** service appears to be unavailable or not properly configured
- **Frigate** intentionally stopped; **Immich** decommissioned as per policy

**Note**: The `llm_calls.jsonl` file shows no activity for the current 24-hour period, which may indicate either:
1. The LLM proxy service is not running
2. The proxy is running but not recording calls
3. The service is intermittent and not capturing recent activity

---

*Generated 2026-11-09 22:00 EDT by cron job*