# Mac Studio Ollama Setup (Port 8080 + 11434)

## Overview
- **Mac Studio IP**: 192.168.1.174 (LAN) / 100.75.240.39 (Tailscale)
- **Ollama API**: `http://192.168.1.174:11434` (with CORS enabled)
- **Chat UI**: `http://192.168.1.174:8080/ollama-chat.html`
- **Dashboard proxy**: Linux server (clawz840:5001) → `/api/ollama-*` via Tailscale

---

## 1. Ollama LaunchDaemon (System Domain — Always On)

**File**: `/Library/LaunchDaemons/com.ollama.server.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.server</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Applications/Ollama.app/Contents/Resources/ollama</string>
        <string>serve</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OLLAMA_ORIGINS</key>
        <string>*</string>
        <key>OLLAMA_HOST</key>
        <string>0.0.0.0:11434</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/var/log/ollama.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ollama.error.log</string>
</dict>
</plist>
```

**Load it**:
```bash
sudo launchctl load /Library/LaunchDaemons/com.ollama.server.plist
sudo launchctl start com.ollama.server
```

**Verify**:
```bash
launchctl list | grep ollama
curl -H "Origin: http://192.168.1.174:8080" -X OPTIONS http://192.168.1.174:11434/api/chat -v
# Should show: Access-Control-Allow-Origin: *
```

---

## 2. Web UI Server (Port 8080)

**Option A: Simple HTTP Server (for static files only)**
```bash
cd ~/projects/ollama-chat
python3 -m http.server 8080 --bind 0.0.0.0
```

**Option B: Combined Proxy + Static Server (recommended)**
File: `~/projects/ollama-chat/proxy.py`
```python
#!/usr/bin/env python3
"""Serves ollama-chat.html on / and proxies /api/* to Ollama with CORS."""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import urllib.request
import json
import os

class ProxyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(__file__), **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path.startswith('/api/'):
            self.proxy_request('GET')
        else:
            if self.path == '/':
                self.path = '/ollama-chat.html'
            super().do_GET()

    def do_POST(self):
        if self.path.startswith('/api/'):
            self.proxy_request('POST')
        else:
            self.send_error(404)

    def proxy_request(self, method):
        url = f'http://127.0.0.1:11434{self.path}'
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else None

        req = urllib.request.Request(url, data=body, method=method)
        for k, v in self.headers.items():
            if k.lower() not in ('host', 'content-length'):
                req.add_header(k, v)

        try:
            with urllib.request.urlopen(req) as resp:
                self.send_response(resp.status)
                for k, v in resp.headers.items():
                    if k.lower() != 'transfer-encoding':
                        self.send_header(k, v)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(resp.read())
        except Exception as e:
            self.send_error(502, str(e))

if __name__ == '__main__':
    os.chdir(os.path.dirname(__file__))
    HTTPServer(('0.0.0.0', 8080), ProxyHandler).serve_forever()
```

**Run it**:
```bash
cd ~/projects/ollama-chat
python3 proxy.py
```

**Or as a LaunchDaemon** (`/Library/LaunchDaemons/com.ollama.webui.plist`):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ollama.webui</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/scott/projects/ollama-chat/proxy.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>WorkingDirectory</key>
    <string>/Users/scott/projects/ollama-chat</string>
    <key>StandardOutPath</key>
    <string>/var/log/ollama-webui.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ollama-webui.error.log</string>
</dict>
</plist>
```

---

## 3. Chat HTML (`~/projects/ollama-chat/ollama-chat.html`)

Key points:
- Calls `const OLLAMA_URL = 'http://192.168.1.174:11434'` directly
- Works because Ollama sends `Access-Control-Allow-Origin: *`
- No proxy needed in browser — Ollama handles CORS

---

## 4. Linux Server Dashboard Integration

**File**: `/home/scott/projects/dashboard/app.py`

```python
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://100.75.240.39:11434')  # Tailscale IP

@app.route('/api/ollama-chat', methods=['POST'])
def api_ollama_chat():
    # Proxies to Mac Studio Ollama via Tailscale
    ...
```

**Dashboard URL**: `http://100.124.71.12:5001` (or `http://192.168.1.222:5001`)

---

## 5. Installed Models (via `ollama list`)

| Model | Size | Capabilities |
|-------|------|--------------|
| `qwen3.6:27b` | 17.4 GB | vision, completion, tools, thinking |
| `qwen3-coder:30b` | 18.6 GB | completion, tools |
| `hermes-4-14b:latest` | 9.0 GB | completion |
| `qwen3:14b` | 9.3 GB | completion, tools, thinking |

---

## 6. Verification Commands

```bash
# Check Ollama is running with CORS
curl -s http://192.168.1.174:11434/api/tags | jq '.models[].name'

# Test CORS from browser origin
curl -H "Origin: http://192.168.1.174:8080" -X OPTIONS http://192.168.1.174:11434/api/chat -v

# Test chat endpoint
curl -X POST http://192.168.1.174:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3:14b","messages":[{"role":"user","content":"Hello"}],"stream":false}'

# Check web UI
curl -s http://192.168.1.174:8080/ollama-chat.html | head -5

# Check LaunchDaemons
launchctl list | grep -E '(ollama|webui)'
sudo launchctl print system/com.ollama.server
sudo launchctl print system/com.ollama.webui
```

---

## 7. File Locations Summary

| Component | Location |
|-----------|----------|
| Ollama LaunchDaemon | `/Library/LaunchDaemons/com.ollama.server.plist` |
| Web UI LaunchDaemon | `/Library/LaunchDaemons/com.ollama.webui.plist` |
| Chat HTML | `~/projects/ollama-chat/ollama-chat.html` |
| Proxy server | `~/projects/ollama-chat/proxy.py` |
| Dashboard app | `~/projects/dashboard/app.py` (on Linux server) |
| Ollama binary | `/Applications/Ollama.app/Contents/Resources/ollama` |
| Ollama CLI symlink | `/usr/local/bin/ollama` → app bundle |
| Logs | `/var/log/ollama*.log`, `/var/log/ollama-webui*.log` |

---

## 8. Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS error in browser | Verify `OLLAMA_ORIGINS=*` in LaunchDaemon, restart: `sudo launchctl kickstart -k system/com.ollama.server` |
| Port 8080 not responding | Check web UI daemon: `sudo launchctl kickstart -k system/com.ollama.webui` |
| Models not loading | `curl http://127.0.0.1:11434/api/tags` from Mac Studio |
| Dashboard can't reach Ollama | Check Tailscale connectivity: `curl http://100.75.240.39:11434/api/tags` from Linux server |
| CLI `ollama` not found | `sudo ln -s /Applications/Ollama.app/Contents/Resources/ollama /usr/local/bin/ollama` |