# Mac Studio Chrome Remote Desktop Setup

## Prerequisites (One-time Physical Access Required)

**The Mac Studio is headless (no monitor). Chrome Remote Desktop requires a virtual display.**

### Option A: Dummy HDMI Plug (Recommended - $10-15)
- Plug into HDMI port on Mac Studio
- Creates a "virtual monitor" that macOS detects
- Works reliably for headless servers
- Search Amazon: "HDMI dummy plug 4K" or "headless ghost display adapter"

### Option B: BetterDisplay (Free Software Alternative)
- Requires initial GUI access to install/configure
- Creates virtual displays via software
- Less reliable after reboots than hardware dummy

---

## Setup Steps (Run on Mac Studio via SSH After Dummy Plug Installed)

### 1. Install Chrome & Chrome Remote Desktop Host

```bash
# Install Google Chrome (if not already)
brew install --cask google-chrome

# Install Chrome Remote Desktop host
brew install --cask chrome-remote-desktop-host
```

### 2. Configure Chrome Remote Desktop

```bash
# Start the setup (generates command for your Google account)
/opt/homebrew/bin/chrome-remote-desktop-headless --help
```

### 3. Get Authorization Command

1. On **your local computer**, go to: https://remotedesktop.google.com/headless
2. Sign in with your Google account
3. Click "Begin" → "Next" → "Authorize"
4. Copy the **generated command** (looks like):
   ```
   /opt/homebrew/bin/chrome-remote-desktop-headless --code=4/xxxxxxxx --redirect-url=https://remotedesktop.google.com/_/oauthredirect --name=MacStudio
   ```

### 4. Run Authorization on Mac Studio

```bash
# Paste the command from step 3 here:
/opt/homebrew/bin/chrome-remote-desktop-headless --code=YOUR_CODE --redirect-url=https://remotedesktop.google.com/_/oauthredirect --name=MacStudio
```

### 5. Set PIN (Required for Access)

When prompted, enter a **6-digit PIN** twice. This secures your remote access.

### 6. Verify It's Running

```bash
# Check service status
/opt/homebrew/bin/chrome-remote-desktop-headless --status

# Should show: "Chrome Remote Desktop is running"
```

---

## Persistent Auto-Start (Survives Reboot)

### Create LaunchAgent

```bash
cat > ~/Library/LaunchAgents/com.google.chrome-remote-desktop.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.google.chrome-remote-desktop</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/chrome-remote-desktop-headless</string>
        <string>--start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/chrome-remote-desktop.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/chrome-remote-desktop-error.log</string>
</dict>
</plist>
EOF

# Load it
launchctl load ~/Library/LaunchAgents/com.google.chrome-remote-desktop.plist
```

---

## Access from Anywhere

### Via Browser (Any Device)
1. Go to: https://remotedesktop.google.com/access
2. Click "MacStudio" (or your chosen name)
3. Enter your 6-digit PIN
4. Full macOS desktop in browser tab

### Via Chrome Remote Desktop App
- Install "Chrome Remote Desktop" extension/app on your local Chrome
- Access from the Apps page (chrome://apps)

---

## Network Access

| Method | Address |
|--------|---------|
| **Tailscale (Remote)** | Works automatically via Google's relay servers |
| **LAN (Local)** | Works automatically |
| **No port forwarding needed** | Google handles NAT traversal |

---

## Troubleshooting

### "No display found" / Black Screen
- Dummy HDMI plug not detected → Try different port or replug
- Run: `system_profiler SPDisplaysDataType` — should show a display

### Service Won't Start
```bash
# Check logs
cat /tmp/chrome-remote-desktop-error.log

# Restart service
launchctl unload ~/Library/LaunchAgents/com.google.chrome-remote-desktop.plist
launchctl load ~/Library/LaunchAgents/com.google.chrome-remote-desktop.plist
```

### Forgot PIN
```bash
# Re-run setup to set new PIN
/opt/homebrew/bin/chrome-remote-desktop-headless --uninstall
# Then re-run authorization command from step 3
```

### Update Chrome Remote Desktop
```bash
brew upgrade --cask chrome-remote-desktop-host
# Re-run authorization if needed
```

---

## Quick Reference Card

```bash
# Status
/opt/homebrew/bin/chrome-remote-desktop-headless --status

# Stop
/opt/homebrew/bin/chrome-remote-desktop-headless --stop

# Start
/opt/homebrew/bin/chrome-remote-desktop-headless --start

# Uninstall (removes PIN too)
/opt/homebrew/bin/chrome-remote-desktop-headless --uninstall

# Logs
tail -f /tmp/chrome-remote-desktop.log
tail -f /tmp/chrome-remote-desktop-error.log
```

---

## Next Steps for You

1. **Order dummy HDMI plug** (if not already have one)
2. **Plug into Mac Studio HDMI port**
3. **Run steps 1-6 above** via SSH
4. **Test at** https://remotedesktop.google.com/access

The dummy plug is the only hardware needed. Once set up, Chrome Remote Desktop works reliably over Tailscale from anywhere — phone, tablet, laptop, any browser.