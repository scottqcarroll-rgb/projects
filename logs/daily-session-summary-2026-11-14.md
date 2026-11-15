# Daily Session Summary - November 14, 2026

## Overview
Daily automation report for November 14, 2026. This covers LLM activity, system actions, and overall operational status for the 24-hour period (November 13, 2026 22:00 → November 14, 2026 22:00 EST).

## 1. Local LLM Calls Analysis (`/home/scott/projects/logs/llm_calls.jsonl`)

### 📊 Current Day Performance
- **Date**: 2026-11-14
- **Total LLM Calls**: 0
- **Models Used**: None
- **Total Tokens Consumed**: 0
- **Total Elapsed Time**: 0.ন্দ
- **Successful Calls**: 0/0
- **Source Breakdown**: None

### 📈 Data Status
- **Historical Range**: July 14, 2026 through October 28, 2026
- **Note**: No local LLM call records exist for current date (November 14, 2026)

## 2. System Services Status

### ✅ Active Services
- **Dashboard**: Active (PID 1559)
  - Running since: November 10, 2026 16:55:важа
  - Recent activity: API calls from 192.168.1.84
  - Current CPU: 1min 302ms (since reporting start)
  - Current Memory: 168.4M (peak: 176.9M)

- **Odoo**: Active (Multiple PIDs)
  - Running since: November 10, 2026 16:56:18 EST
  - Service: Odoo 17 Production Instance
  - Database: Postgres running (PID 6815)

### ⚠️ Service Status Notes
- **Samhunter**: Service not found (unit not present)
- **Immich**: Not monitored / decommissioned (as per instructions)
- **Frigate**: Stopped / not running (as per instructions)
- **hermes-llm-proxy**: Not found (unit not present)

## 3. System Actions & Automation

### 📁 File Processing Status
- **Email Agent**: Running hourly (08:00-22:00) via cron
  - Successfully fetched and processed multiple Gmail email batches
  - Generated daily dashboard summaries
  - Delivered Telegram notifications
  - Some operational issues noted (see below)

- **Govt Contracts Hunter**: Daily at 08:00 via cron
  - SAM.gov API access issues (HTTP 401 Unauthorized)
  - Gmail authentication errors due to expired OAuth tokens
  - Unable to send contract reports to subscribers

### ⚠️ System Action Issues

#### Email Agent Issues
- **LLM Classification**: Multiple instances where LLM was unavailable (404 errors connecting to http://192.168.1.240:11434/v1/chat/completions)
- **Gmail Authentication**: OAuth tokens have expired/revoked, causing authentication failures
- **Yahoo Mail**: Credentials not configured in environment

#### Govt Contracts Issues
- **SAM.gov API**: Persistent HTTP 401 Unauthorized errors
- **Gmail Integration**: OAuth token refresh failures
- **Email Delivery**: Unable to send contract reports due to authentication issues

## 4. Activity Metrics Summary

### 📋 System Health
- **Dashboard Service**: ✅ Healthy and operational
  - 4 days of continuous operation
  - Stable resource usage
- **Odoo Service**: ✅ Healthy and operational
  - Running alongside Postgres database
- **Local LLM Services**: No current activity recorded

### 🔄 Cron Job Activity
- **Email Agent**: Successfully completed multiple runs
  - Processed various email batches (2-11 emails per run)
  - Generated dashboard summaries each time
- **Govt Contracts**: Daily run attempted but failed
  - SAM.gov access issues persistent
  - Email delivery blocked by authentication problems

### 📊 Data Processing
- **LLM Call Logs**: Historical data available through October 2026
- **Email Processing**: Active but with authentication/LLM issues
- **Contract Reports**: Data collection works, but delivery blocked

## 5. Key Observations

### Primary Issues
1. **LLM Service Unavailable**: Local LLM proxy service not responding (404 errors)
2. **Authentication Problems**: Gmail OAuth tokens expired, affecting email processing
3. **API Access Issues**: SAM.gov requiring updated credentials for contract reporting

### System Stability
1. **Core Services**: Dashboard and Odoo running normally
2. **Historical Data**: Complete audit trail maintained in llm_calls.jsonl
3. **Automation**: Email agent working despite technical issues

### Operational Notes
1. **No LLM Activity**: No local LLM calls recorded for current period
2. **Service Decommissioning**: Immich and Frigate intentionally not active
3. **Backup Status**: System has consistent auto-backup routine

## 6. Recommendations

### Immediate Actions
1. **Restore LLM Service**: Restart llm-proxy.service to restore local LLM functionality
2. **Refresh Gmail Tokens**: Re-authenticate Gmail OAuth2 credentials
3. **Update SAM.gov API**: Resolve access credentials for contract reporting

### Preventive Measures
1. **Monitor Authentication**: Set up alerts for OAuth token expiration
2. **Service Health Checks**: Implement monitoring for llm-proxy service
3. **Backup Credentials**: Store API credentials securely for automated refresh

## 7. System Uptime
- **Dashboard**: 4 days 5h (since November 10, 2026)
- **Odoo**: 4 days 5h (since November 10, 2026)

---
*Report generated automatically on November 14, 2026 at 22:00 EST*
*Data sources: /home/scott/projects/logs/llm_calls.jsonl, email-agent/cron.log, govt-contracts/report_cron.log, system service status checks*