#!/bin/bash
# Mac Studio Chrome Remote Desktop - Quick Commands
# Run these on Mac Studio via SSH AFTER dummy HDMI plug is installed

set -e

echo "=== Mac Studio Chrome Remote Desktop Setup ==="
echo ""

# 1. Install Chrome & Chrome Remote Desktop Host
echo "[1/6] Installing Chrome & Chrome Remote Desktop Host..."
brew install --cask google-chrome
brew install --cask chrome-remote-desktop-host

# 2. Verify installation
echo "[2/6] Verifying installation..."
/opt/homebrew/bin/chrome-remote-desktop-headless --version

# 3. Instructions for authorization
echo ""
echo "[3/6] AUTHORIZATION REQUIRED - Do this on YOUR LOCAL COMPUTER:"
echo "    1. Open: https://remotedesktop.google.com/headless"
echo "    2. Sign in with Google account"
echo "    3. Click 'Begin' -> 'Next' -> 'Authorize'"
echo "    4. COPY the generated command (starts with /opt/homebrew/bin/chrome-remote-desktop-headless --code=...)"
echo ""
read -p "    Paste the FULL command here: " AUTH_CMD

if [[ -z "$AUTH_CMD" ]]; then
    echo "ERROR: No command provided. Exiting."
    exit 1
fi

# 4. Run authorization
echo "[4/6] Running authorization..."
eval "$AUTH_CMD"

# 5. Create persistent LaunchAgent
echo "[5/6] Creating persistent LaunchAgent..."
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

launchctl load ~/Library/LaunchAgents/com.google.chrome-remote-desktop.plist

# 6. Verify
echo "[6/6] Verifying service..."
sleep 2
/opt/homebrew/bin/chrome-remote-desktop-headless --status

echo ""
echo "=== SETUP COMPLETE ==="
echo ""
echo "Access from anywhere:"
echo "  1. Go to: https://remotedesktop.google.com/access"
echo "  2. Click 'MacStudio'"
echo "  3. Enter your 6-digit PIN"
echo ""
echo "Useful commands:"
echo "  Status:  /opt/homebrew/bin/chrome-remote-desktop-headless --status"
echo "  Stop:    /opt/homebrew/bin/chrome-remote-desktop-headless --stop"
echo "  Start:   /opt/homebrew/bin/chrome-remote-desktop-headless --start"
echo "  Logs:    tail -f /tmp/chrome-remote-desktop.log"