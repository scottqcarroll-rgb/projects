---
name: check-dashboard
description: Compare dashboard against baseline to catch regressions.
category: devops
---

# Check Dashboard Skill

Automated regression detection for the Flask dashboard. Compares current state against a saved baseline (git commit/tag) to catch:
- Missing template fields (like the Linux Server/Mac Studio card simplification)
- API response field changes
- Broken endpoints
- JavaScript errors in rendered HTML

## Baseline Strategy

The skill saves a **baseline snapshot** from a known-good commit (default: `0457814` - last commit with full Linux/Mac Studio cards). Run `check-dashboard capture` to update baseline after intentional changes.

## Usage

```bash
# Quick check against saved baseline
check-dashboard check

# Full check with API validation (requires running dashboard)
check-dashboard check --full

# Update baseline to current state (after verified good changes)
check-dashboard capture

# Compare specific commit against baseline
check-dashboard diff 6bc5a07

# List available baselines
check-dashboard list-baselines
```

## What Gets Checked

### 1. Template Field Coverage (`templates/dashboard.html`)
- `loadLinuxServer()` renders all expected fields: `hostname`, `cpu_model`, `load_1m`, `load_5m`, `load_15m`, `memory_used_pct`, `memory_avail_gb`, `memory_total_gb`, `disk_pct`, `disk_used`, `disk_total`, `uptime`, `cpu_temp`, `ip`
- `loadMacStudio()` renders all expected fields: `hostname`, `model`, `chip`, `os`, `ram`, `storage`, `load_1m`, `load_5m`, `load_15m`, `memory_used_pct`, `memory_used_gb`, `memory_total_gb`, `disk_pct`, `disk_used`, `disk_total`
- All other tile load functions (`loadTrueNAS`, `loadCameras`, `loadWeather`, `loadDriveReport`, `loadPMDriveReport`, `loadLLMMetrics`, `loadOllamaModels`, `loadGmail`, `loadLinks`, `loadServerTime`, `loadOpenRoute`, `loadGemma`, `loadSamHunter`)

### 2. API Response Fields (`data_fetcher.py` return dicts)
- `/api/linux-server` → `get_linux_server_status()` keys
- `/api/mac-studio` → `get_mac_studio_status()` keys
- `/api/truenas` → `get_truenas_status()` keys
- `/api/weather` → `get_weather()` keys
- `/api/drive` → `get_drive_report()` keys
- `/api/pm-drive` → `get_pm_drive_report()` keys
- `/api/llm-metrics` → log parsing structure
- `/api/ollama` → `get_ollama_status()` keys
- `/api/mac-studio/ollama` → `get_mac_studio_ollama_status()` keys
- `/api/cameras` → `get_camera_snapshots()` keys
- `/api/samhunter` → `get_sam_hunter()` keys
- `/api/gmail` → `get_gmail_summary()` keys
- `/api/usage` → `get_openrouter_usage()` keys

### 3. Live Endpoint Validation (with `--full`)
- All `/api/*` endpoints return `status: "ok"` (or expected structure)
- Response time < 5s
- No 500 errors

### 4. JavaScript Console Errors (with `--full` via headless browser)
- No uncaught exceptions on page load
- All `fetch()` calls succeed
- No "Loading..." stuck states after 10s

## Configuration

Baseline stored in `.dashboard-baseline/`:
```
.dashboard-baseline/
├── commit.txt           # Git commit hash of baseline
├── template-fields.json # Expected fields per tile function
├── api-fields.json      # Expected keys per API endpoint
└── package.json         # For headless browser deps (playwright)
```

## Integration

Add to cron for daily regression checks:
```bash
# Daily at 6 AM - full check with live endpoints
0 6 * * * /home/scott/.hermes/scripts/check-dashboard.sh --full
```

Or as a pre-deploy gate in CI/CD.

## Exit Codes
- `0` = All checks pass
- `1` = Template field regression detected
- `2` = API field regression detected
- `3` = Live endpoint failure (--full only)
- `4` = JavaScript errors detected (--full only)
- `10` = Baseline not found (run `capture` first)