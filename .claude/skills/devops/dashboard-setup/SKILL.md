---
name: dashboard-setup
description: Complete recreation guide for Scott's Dashboard — all conventions, code, endpoints, file contents, and deployment steps
category: devops
---

# Dashboard Setup — Complete Recreation Guide

## Overview
Flask-based personal dashboard served at **http://100.124.71.12:5001** (Tailscale) / **192.168.1.222:5001** (LAN). Managed via systemd service `dashboard` on `clawz840` (user: scott).

## Project Structure
```
/home/scott/projects/dashboard/
├── app.py                    # Flask entry point (72 lines, port 5001, host 0.0.0.0)
├── data_fetcher.py           # All backend fetchers (701 lines)
├── templates/
│   └── dashboard.html        # Full HTML/CSS/JS template (927 lines)
├── static/                   # Empty directory (reserved)
├── credentials.json          # Gmail API credentials (gitignored, required for email tile)
├── token.json                # Gmail OAuth token (gitignored, auto-generated)
├── .git/                     # Git repo → github.com:scottqcarroll-rgb/projects
└── .claude/skills/devops/dashboard-setup/  # THIS skill (backed up to GitHub)
```

## Systemd Service (dashboard.service)
**Location:** `/etc/systemd/system/dashboard.service`
```ini
[Unit]
Description=Scott's Dashboard
After=network.target

[Service]
Type=simple
User=scott
WorkingDirectory=/home/scott/projects/dashboard
Environment=FLASK_ENV=production
ExecStart=/usr/bin/python3 /home/scott/projects/dashboard/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```
**Commands:**
- `sudo systemctl restart dashboard` — restart after changes
- `sudo systemctl status dashboard` — verify running
- `sudo journalctl -u dashboard -f` — follow logs

---

## app.py — Complete Flask App (227 lines)

```python
#!/usr/bin/env python3
from flask import Flask, render_template, jsonify, request, Response
from data_fetcher import (
    get_drive_report, get_pm_drive_report, get_weather, get_sam_hunter,
    get_gmail_summary, get_openrouter_usage, get_ollama_status,
    get_linux_server_status, get_mac_studio_status, get_mac_studio_ollama_status,
    get_camera_snapshots
)
import os
import pytz
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/time')
def api_time():
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)
    return jsonify({
        'status': 'ok',
        'datetime': now.strftime('%A, %B %d • %I:%M %p'),
        'timezone': 'America/New_York'
    })

@app.route('/api/drive')
def api_drive():
    return jsonify(get_drive_report())

@app.route('/api/pm-drive')
def api_pm_drive():
    return jsonify(get_pm_drive_report())

@app.route('/api/weather')
def api_weather():
    return jsonify(get_weather())

@app.route('/api/links')
def api_links():
    sam = get_sam_hunter()
    return jsonify({
        'status': 'ok',
        'links': [
            {'name': sam['name'], 'url': sam['url']}
        ] if sam['status'] == 'ok' else []
    })

@app.route('/api/gmail')
def api_gmail():
    return jsonify(get_gmail_summary())

@app.route('/api/usage')
def api_usage():
    return jsonify(get_openrouter_usage())

@app.route('/api/ollama')
def api_ollama():
    return jsonify(get_ollama_status())

@app.route('/api/linux-server')
def api_linux_server():
    return jsonify(get_linux_server_status())

@app.route('/api/mac-studio')
def api_mac_studio():
    return jsonify(get_mac_studio_status())

@app.route('/api/mac-studio/ollama')
def api_mac_studio_ollama():
    return jsonify(get_mac_studio_ollama_status())

@app.route('/api/cameras')
def api_cameras():
    return jsonify(get_camera_snapshots())

@app.route('/api/camera-image')
def api_camera_image():
    url = request.args.get('url')
    if not url:
        return Response('Missing url parameter', status=400)
    try:
        import requests
        r = requests.get(url, timeout=10)
        return Response(r.content, mimetype=r.headers.get('Content-Type', 'image/jpeg'))
    except Exception as e:
        return Response(f'Failed to fetch image: {str(e)}', status=500)

# --- Chat proxy to Mac Studio Ollama ---
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://192.168.1.174:11434')
DEFAULT_OLLAMA_MODEL = 'hermes-4-14b:latest'

@app.route('/api/ollama-chat', methods=['POST'])
def api_ollama_chat():
    import requests
    try:
        data = request.get_json(force=True)
        model = data.get('model', DEFAULT_OLLAMA_MODEL)
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        tools = data.get('tools', None)
        payload = {'model': model, 'messages': messages, 'stream': stream}
        if tools is not None:
            payload['tools'] = tools
        resp = requests.post(
            f'{OLLAMA_BASE_URL}/api/chat',
            json=payload,
            timeout=120,
            stream=stream
        )
        if stream:
            def generate():
                for line in resp.iter_lines():
                    if line:
                        yield line.decode('utf-8') + '\n'
            return Response(generate(), mimetype='application/x-ndjson')
        else:
            return jsonify(resp.json())
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to Ollama at ' + OLLAMA_BASE_URL}), 503
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Ollama request timed out'}), 504
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/ollama-models')
def api_ollama_models():
    import requests
    try:
        resp = requests.get(f'{OLLAMA_BASE_URL}/api/tags', timeout=10)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/llm-metrics')
def api_llm_metrics():
    log_file = '/home/scott/projects/llm_call_log.txt'
    if not os.path.exists(log_file):
        return jsonify({
            'status': 'ok', 'total_calls': 0, 'today_calls': 0,
            'share_of_total': 0, 'avg_30_day': 0, 'hourly_rate': 0, 'calls_today': []
        })
    with open(log_file, 'r') as f:
        lines = f.readlines()
    calls = []
    for line in lines:
        line = line.strip()
        if not line: continue
        try:
            timestamp_str = line.split(']')[0][1:]
            timestamp = datetime.fromisoformat(timestamp_str)
            calls.append(timestamp)
        except (ValueError, IndexError):
            continue
    total_calls = len(calls)
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_calls = sum(1 for c in calls if c >= today_start)
    calls_today = [c.strftime('%H:%M') for c in calls if c >= today_start]
    thirty_days_ago = now - timedelta(days=30)
    recent_calls = [c for c in calls if c >= thirty_days_ago]
    avg_30_day = len(recent_calls) / 30 if recent_calls else 0
    one_day_ago = now - timedelta(hours=24)
    recent_24h = [c for c in calls if c >= one_day_ago]
    hourly_rate = len(recent_24h) / 24 if recent_24h else 0
    share_of_total = round((today_calls / total_calls * 100), 1) if total_calls > 0 else 0
    return jsonify({
        'status': 'ok',
        'total_calls': total_calls,
        'today_calls': today_calls,
        'share_of_total': share_of_total,
        'avg_30_day': round(avg_30_day, 1),
        'hourly_rate': round(hourly_rate, 2),
        'calls_today': calls_today
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)
```

---

## data_fetcher.py — Complete (701 lines)

### Key Functions & Signatures

| Function | Returns | Notes |
|----------|---------|-------|
| `get_drive_routes(origin, destination)` | `{'status', 'routes[]'}` | Google Maps Directions API, `departure_time=now`, alternatives=true |
| `get_drive_report()` (AM) | `{'status', 'origin', 'destination', 'departure_time', 'arrival_time', 'distance_miles', 'duration_minutes', 'routes'}` | Home → Work: `616 Huntwood Cir, Temple GA 30179` → `5303 New Peachtree Rd, Chamblee GA 30341` |
| `get_pm_drive_report()` (PM) | Same structure | Work → Home (swapped), **uses `datetime.now()` for departure (synced with dashboard)** |
| `parse_duration_to_minutes(str)` | `int` | Parses "1 hour 15 mins" or "45 mins" |
| `get_weather()` | `{'status', 'temperature', 'condition', 'humidity', 'wind_speed', 'feels_like', 'high', 'low', 'precip'}` | Open-Meteo API, Temple GA (33.7353, -85.0308), no key needed |
| `get_sam_hunter()` | `{'status', 'url', 'name'}` | Returns `http://100.124.71.12:5002` |
| `get_gmail_summary()` | `{'status', 'email_address', 'unread_count', 'total_count', 'starred_count', 'message'}` | Uses `email-agent/gmail_client.py` |
| `get_openrouter_usage()` | `{'status', 'usage_total', 'usage_daily', 'usage_weekly', 'usage_monthly', 'limit', 'limit_remaining', 'is_free_tier', 'label'}` | OpenRouter `/api/v1/key` |
| `get_ollama_status()` | `{'status', 'model', 'params', 'context', 'size_gb', 'host'}` | Local llama.cpp server |
| `get_linux_server_status()` | `{'status', 'hostname', 'cpu_model', 'load_1m', 'load_5m', 'load_15m', 'memory_total_gb', 'memory_used_pct', 'memory_avail_gb', 'disk_used', 'disk_total', 'disk_pct', 'uptime', 'cpu_temp', 'ip'}` | Reads `/proc/*`, `df -h /` |
| `get_mac_studio_status()` | `{'status', 'hostname', 'model', 'chip', 'ram', 'os', 'storage', 'load_1m', 'load_5m', 'load_15m', 'memory_total_gb', 'memory_used_gb', 'memory_free_gb', 'memory_used_pct', 'disk_used', 'disk_total', 'disk_pct', 'ip'}` | SSH to `macstudio`, runs `system_profiler`, `top`, `df` |
| `get_mac_studio_ollama_status()` | `{'status', 'ollama_running', 'models_installed', 'models[]', 'running_models[]'}` | SSH to Mac Studio, `ollama list` + `curl localhost:11434/api/ps` |
| `get_camera_snapshots()` | `{'status', 'cameras[{id, name, ip, snapshot_url}]'}` | Returns metadata; browser loads images via `/api/camera-image?url=...` |

### Critical Implementation Details

- **Google Maps API Key:** Read from first `*.py` file in `/home/scott/.hermes/scripts/` containing `API_KEY="..."`
- **AM Drive:** Origin=`616 Huntwood Cir, Temple GA 30179`, Dest=`5303 New Peachtree Rd, Chamblee GA 30341`
- **PM Drive:** Origin/Dest swapped, `departure_time = datetime.now().strftime('%-I:%M %p')` (current time, synced)
- **Weather:** Open-Meteo, WMO code mapping to condition text
- **Mac Studio SSH:** Uses `macstudio` SSH alias (configured in `~/.ssh/config`)
- **Cameras:** Two FLIR cameras at `192.168.1.158` (Gun Room) and `192.168.1.163` (Office), snapshot endpoint `/cgi-bin/snapshot.cgi?chn=0`

---

## templates/dashboard.html — Complete (927 lines)

### HTML Structure
- **Header:** `Scott's Dashboard` + `#datetime` (server time from `/api/time`)
- **Grid:** 11 cards (AM Drive, PM Drive, Weather, Links, Gmail, OpenRouter, Ollama, Linux Server, Mac Studio, Cameras, LLM Metrics)
- **Chat Container:** Ollama chat interface (bottom)

### CSS Classes (Key)
| Class | Purpose |
|-------|---------|
| `.card-icon.drive-icon` | Teal gradient for drive cards |
| `.card-icon.weather-icon` | Orange/yellow gradient |
| `.card-icon.gemma-icon` | Orange/pink gradient (Ollama tile) |
| `.card-icon.linux-icon` | Teal/cyan gradient |
| `.card-icon.mac-icon` | Pink/red gradient |
| `.weather-icon-large` | 2.5rem weather emoji |
| `.metric-row` | Flex row: label + value |
| `.camera-grid` | Grid for camera images |
| `.camera-item img` | 100% width, 16:9 aspect-ratio |

### PM Drive Icon (CRITICAL — DO NOT CHANGE)
```html
<div class="card-icon drive-icon" style="transform: scaleX(-1);">🚗</div>
```
Same 🚗 emoji as AM, flipped horizontally via CSS to face RIGHT (returning home).

### JavaScript Functions
| Function | Interval | Endpoint |
|----------|----------|----------|
| `loadServerTime()` | 30s | `/api/time` |
| `loadDriveReport()` | 5min | `/api/drive` |
| `loadPMDriveReport()` | 5min | `/api/pm-drive` |
| `loadWeather()` | 5min | `/api/weather` |
| `loadLinks()` | 5min | `/api/links` |
| `loadGmail()` | 5min | `/api/gmail` |
| `loadOpenRoute()` | 5min | `/api/usage` |
| `loadOllamaModelStatus()` | 5min | `/api/mac-studio/ollama` |
| `loadLinuxServer()` | 5min | `/api/linux-server` |
| `loadMacStudio()` | 5min | `/api/mac-studio` |
| `loadCameras()` | 30s | `/api/cameras` |
| `loadLLMMetrics()` | 5min | `/api/llm-metrics` |
| `updateDriveTimes()` | 60s | `/api/drive-times` |

### Camera Loading Logic
```javascript
// In loadCameras():
camera.innerHTML = `<img src="/api/camera-image?url=${encodeURIComponent(cam.snapshot_url)}" alt="${cam.name}">`
```
Browser fetches via proxy (`/api/camera-image`) to bypass LAN/CORS restrictions.

### Ollama Status Display
```javascript
const runningModel = data.running_models && data.running_models.length > 0
    ? data.running_models[0].name
    : 'None (idle)';
el.innerHTML = `
    <div class="metric-row"><span>Status</span><span class="metric-value status-ok">${data.ollama_running ? 'Ollama Running' : 'Ollama Stopped'}</span></div>
    <div class="metric-row"><span>Running Model</span><span class="metric-value">${runningModel}</span></div>
    <div class="metric-row"><span>Models Installed</span><span class="metric-value">${data.models_installed}</span></div>
`;
```

---

## Icon Conventions (CRITICAL — DO NOT CHANGE)

| Tile | Icon | Direction | Meaning |
|------|------|-----------|---------|
| AM Drive Report | 🚗 | Left (default) | Going TO work |
| PM Drive Report | 🚗 + `transform: scaleX(-1)` | Right (flipped) | Returning HOME |
| Weather | 🌤️ | N/A | Sun behind cloud |
| Email | 📧 | N/A | Envelope |
| Ollama | 🦙 | N/A | Llama |
| Linux Server | 🐧 | N/A | Penguin |
| Mac Studio | 💻 | N/A | Laptop |
| Cameras | 📷 | N/A | Camera |
| LLM Metrics | 📊 | N/A | Chart |
| Quick Links | 🔬 | N/A | Microscope |
| OpenRouter | 🤖 | N/A | Robot |
| Chat | 💬 | N/A | Speech bubble |

---

## Drive Report Time Rules

### AM Drive Report
- **Departure:** Current dashboard time (synced via JS `updateDriveTimes()`)
- **Arrival:** Departure + traffic duration

### PM Drive Report
- **Departure:** Current dashboard time (synced like AM) — **NOT fixed 5:00 PM**
- **Arrival:** Departure + traffic duration
- **Endpoint:** `/api/drive-times` returns both AM and PM with current time

---

## API Endpoints Summary

| Endpoint | Purpose |
|----------|---------|
| `/` | Dashboard HTML |
| `/api/time` | Server time (Eastern) |
| `/api/drive` | AM drive report |
| `/api/pm-drive` | PM drive report |
| `/api/weather` | Weather for Temple, GA |
| `/api/links` | Quick links (Sam Hunter) |
| `/api/gmail` | Gmail summary |
| `/api/usage` | OpenRouter usage |
| `/api/ollama` | Local Ollama status |
| `/api/mac-studio/ollama` | Mac Studio Ollama (running model, installed models) |
| `/api/linux-server` | Linux server stats |
| `/api/mac-studio` | Mac Studio specs |
| `/api/cameras` | Camera list with snapshot URLs |
| `/api/camera-image?url=...` | Camera image proxy |
| `/api/llm-metrics` | LLM call metrics from `/home/scott/projects/llm_call_log.txt` |
| `/api/ollama-chat` | Proxy to Mac Studio Ollama `/api/chat` |
| `/api/ollama-models` | Mac Studio Ollama `/api/tags` |

---

## Git Workflow
- After EVERY change: `git add ... && git commit -m "verb-first message" && git push`
- Commit messages: verb-first, under 70 chars
- Service restart: `sudo systemctl restart dashboard && sleep 3`

---

## Verification Steps
1. `sudo systemctl restart dashboard && sleep 3`
2. Browser snapshot at `http://100.124.71.12:5001`
3. Verify:
   - AM icon 🚗 (left), PM icon 🚗 flipped (right)
   - Both departure times match dashboard clock
   - Weather shows 🌤️
   - Ollama tile shows "Running Model: None (idle)" + "Models Installed: 2"
   - Cameras load via proxy
   - LLM Metrics shows call counts