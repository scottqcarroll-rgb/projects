---
name: dashboard-setup
description: Dashboard conventions, icons, and formatting rules
category: devops
---

# Dashboard Setup & Format Rules

## Project Location
- **Repo**: `/home/scott/projects/dashboard`
- **URL**: http://100.124.71.12:5001
- **Service**: `systemctl restart dashboard`

## Icon Conventions (CRITICAL - DO NOT CHANGE)

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

**PM Drive icon implementation**: Uses same 🚗 emoji as AM, but flipped with CSS:
```html
<div class="card-icon drive-icon" style="transform: scaleX(-1);">🚗</div>
```

## Drive Report Time Rules

### AM Drive Report
- **Departure**: Current dashboard time (synced via JS `updateDriveTimes()`)
- **Arrival**: Departure + traffic duration

### PM Drive Report  
- **Departure**: Current dashboard time (synced like AM) — **NOT fixed 5:00 PM**
- **Arrival**: Departure + traffic duration
- **Endpoint**: `/api/drive-times` returns both AM and PM with current time

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/api/drive-times` | Both AM & PM drive reports (current time synced) |
| `/api/weather` | Weather for Temple, GA |
| `/api/email` | Gmail summary |
| `/api/ollama` | Local Ollama status |
| `/api/mac-studio/ollama` | Mac Studio Ollama (running model, installed models) |
| `/api/linux` | Linux server stats |
| `/api/mac-studio` | Mac Studio specs |
| `/api/cameras` | Camera list |
| `/api/camera-image?url=...` | Camera image proxy |

## JS Time Sync (dashboard.html)
```javascript
function updateDriveTimes() {
    fetch('/api/drive-times')
        .then(r => r.json())
        .then(data => {
            // Updates BOTH #drive-data (AM) and #pm-drive-data (PM)
            // Departure time comes from backend (current time)
        });
}
setInterval(updateDriveTimes, 60000); // Every minute
```

## Data Fetcher (data_fetcher.py)
- `get_am_drive_report()` - Home → Work
- `get_pm_drive_report()` - Work → Home (uses current time, NOT fixed 5 PM)
- Both use `get_drive_routes()` with Google Maps API (`departure_time=now`)

## Git Workflow
- After EVERY change: `git add ... && git commit -m "..." && git push`
- Commit messages: verb-first, under 70 chars
- Service restart: `sudo systemctl restart dashboard && sleep 3`

## Verification
- Always verify with browser snapshot after restart
- Check both icons show correctly (AM left, PM right)
- Check both departure times match dashboard clock