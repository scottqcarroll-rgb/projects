# Multi-Machine Development Setup — Complete Summary

**Setup Date:** May 5, 2026  
**Status:** ✓ Fully Operational

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    LINUX SERVER                             │
│              (ClawZ840 - 192.168.1.222)                     │
│         Tailscale IP: 100.124.71.12 (clawz840)              │
│                                                              │
│  • ALL Projects and Code                                    │
│  • Git Repository (Primary)                                 │
│  • Email Agent (Cron: 9 AM daily)                           │
│  • Python Virtual Environment                               │
│  • Tailscale Connected                                      │
└─────────────────────────────────────────────────────────────┘
         ▲                    ▲                    ▲
         │ SSH                │ SSH                │ SSH
         │ via                │ via                │ via
    Tailscale            Tailscale            Tailscale
         │                    │                    │
    ┌────────────┐    ┌──────────────┐    ┌──────────────┐
    │  Windows   │    │   Mac        │    │   Mac        │
    │  Desktop   │    │   Laptop     │    │   Studio     │
    │            │    │              │    │              │
    │ SSH Client │    │ SSH Client   │    │ SSH Client   │
    │ Tailscale  │    │ Tailscale    │    │ Tailscale    │
    └────────────┘    └──────────────┘    └──────────────┘
```

---

## System Details

### Linux Server
- **Hostname:** ClawZ840
- **Internal IP:** 192.168.1.222
- **Tailscale IP:** 100.124.71.12
- **OS:** Ubuntu (Noble)
- **SSH Port:** 22
- **Username:** scott
- **Sudo Password:** admin (all lowercase)

**Installed Tools:**
- Python 3.12.3
- Git 2.43.0
- Node.js v18.19.1
- npm 9.2.0
- Tailscale v1.96.4

### VPN Access
- **Service:** Tailscale
- **Purpose:** Secure mesh VPN connecting all machines
- **Status:** All machines connected

---

## Projects on Linux

### Location: `~/projects/`

```
~/projects/
│
├── email-agent/                    Email processing automation
│   ├── email_agent.py             Main script
│   ├── gmail_client.py            Gmail API integration
│   ├── yahoo_client.py            Yahoo IMAP integration
│   ├── email_classifier.py        Claude AI classification
│   ├── dashboard.py               HTML dashboard generation
│   ├── email_api.py               Flask API server (localhost:5050)
│   ├── venv/                      Python virtual environment
│   ├── run_email_agent.sh         Cron wrapper script
│   ├── cron.log                   Daily execution logs
│   ├── daily_summary.html         Generated email dashboard
│   ├── credentials.json           Gmail OAuth credentials
│   ├── token.json                 Gmail OAuth token
│   └── .env                       Email credentials
│
├── games/                          Game projects
│   ├── tic-tac-toe.html           Tic-tac-toe game
│   └── top-down-shooter/          Top-down shooter game
│
├── venue-research/                Venue dossier research
│   ├── nc_distressed_wedding_venues.csv
│   ├── nc_venues_scorecard.csv
│   ├── venue_dossier.html
│   ├── greater_atlanta_metro_venue_dossier.html
│   └── greater_atlanta_metro_venues_scorecard.csv
│
├── .claude/                        Claude Code configuration
│   ├── CLAUDE.md                  Project guidelines
│   ├── settings.json              VS Code settings
│   └── skills/                    Custom skills
│       ├── email-agent.md
│       ├── gmail-agent.md
│       └── venue-dossier.md
│
├── CLAUDE.md                       Documentation
├── .gitignore                      Git ignore rules
└── .git/                           Git repository (Primary)
```

---

## Daily Automated Tasks

### Email Agent Cron Job
- **Schedule:** Every day at 9:00 AM UTC
- **Command:** `0 9 * * * ~/projects/email-agent/run_email_agent.sh`
- **Process:**
  1. Fetches Gmail emails (last 24 hours, max 50)
  2. Classifies with Claude API
  3. Generates HTML dashboard
  4. Starts Flask API server for delete operations
  5. Sends Telegram notification with summary
  6. Logs execution to `~/projects/email-agent/cron.log`

**Monitor Execution:**
```bash
ssh clawz840 "tail -f ~/projects/email-agent/cron.log"
```

---

## Quick Start Commands

### From Windows or Mac Terminal

#### 1. Connect to Linux Server
```bash
ssh clawz840
# or
ssh scott@100.124.71.12
```

#### 2. Navigate to Projects
```bash
cd ~/projects                 # Main projects directory
cd ~/projects/email-agent     # Email automation
cd ~/projects/games           # Game projects
cd ~/projects/venue-research  # Venue research
```

#### 3. Git Operations
```bash
cd ~/projects
git status                    # Check status
git log --oneline            # View commits
git add .                    # Stage changes
git commit -m "message"      # Commit
git push                     # Push to remote (if configured)
```

#### 4. Email Agent Management
```bash
# Run manually (overrides 9 AM schedule)
~/projects/email-agent/run_email_agent.sh

# View last execution log
tail ~/projects/email-agent/cron.log

# View generated dashboard
cat ~/projects/email-agent/daily_summary.html

# Test Python environment
source ~/projects/email-agent/venv/bin/activate
python3 email_agent.py --force
deactivate
```

#### 5. Check System Status
```bash
# Verify cron job
crontab -l

# Check Tailscale status
sudo tailscale status

# Verify disk space
df -h

# Check system time
date
```

---

## SSH Configuration

### Windows/Mac SSH Config (`~/.ssh/config`)

```
Host clawz840
    HostName 100.124.71.12
    User scott
    IdentityFile ~/.ssh/id_ed25519_linux
    AddKeysToAgent yes
    IdentitiesOnly yes
```

**SSH Key Files:**
- **Private:** `~/.ssh/id_ed25519_linux` (keep secure)
- **Public:** `~/.ssh/id_ed25519_linux.pub` (on Linux server)

---

## Tailscale Network

### Connected Devices

| Name | IP | OS | Status |
|------|----|----|--------|
| clawz840 (Linux) | 100.124.71.12 | Linux | Online |
| desktop-z8g4 | 100.94.154.56 | Windows | Online |
| scotts-27-imac | 100.111.47.89 | macOS | Online |
| scotts-mac-studio | 100.114.16.118 | macOS | Online |
| scotts-macbook-air | 100.67.66.62 | macOS | Offline |
| iphone-15-pro-max | 100.84.96.100 | iOS | Online |
| truenas-scale | 100.79.220.32 | Linux | Online |

**Access any machine:**
```bash
ssh scott@100.124.71.12      # Linux server
ssh scott@100.94.154.56      # Windows desktop (if SSH enabled)
ssh scott@100.111.47.89      # iMac (if SSH enabled)
```

---

## Common Workflows

### Daily Email Check
```bash
ssh clawz840
cat ~/projects/email-agent/daily_summary.html | less
```

### Deploy New Feature
```bash
ssh clawz840
cd ~/projects
# Make changes in your project folder
git add .
git commit -m "Add new feature: description"
# Push if remote is configured
```

### Troubleshoot Email Agent
```bash
ssh clawz840
cd ~/projects/email-agent
source venv/bin/activate
python3 -c "from gmail_client import *; print('Gmail module OK')"
python3 -c "from email_classifier import *; print('Classifier OK')"
deactivate
```

### Update Project Files on Mac
```bash
# From Mac laptop
ssh clawz840
cd ~/projects/your-project
# Edit files
git add .
git commit -m "Update from Mac"
```

---

## Troubleshooting

### SSH Connection Issues

**Problem:** `ssh: connect to host 100.124.71.12 port 22: Connection refused`

**Solutions:**
1. Check Tailscale is running: `tailscale status`
2. Verify Linux server is up: SSH to another device on Tailscale
3. Restart Tailscale on your machine

### Email Agent Not Running

**Check cron job:**
```bash
ssh clawz840 "crontab -l"
```

**Check system logs:**
```bash
ssh clawz840 "grep CRON /var/log/syslog | tail -20"
```

**Run manually:**
```bash
ssh clawz840 "~/projects/email-agent/run_email_agent.sh"
```

### Python Module Import Errors

```bash
ssh clawz840
cd ~/projects/email-agent
source venv/bin/activate
pip list  # Verify packages are installed
deactivate
```

### Cron Log Not Found

If `~/projects/email-agent/cron.log` doesn't exist, the cron job hasn't run yet. Create it:
```bash
ssh clawz840 "touch ~/projects/email-agent/cron.log"
```

---

## Important Notes

### Backup Credentials
The following files contain sensitive credentials and should be backed up:
- `~/projects/email-agent/credentials.json` (Gmail OAuth)
- `~/projects/email-agent/token.json` (Gmail OAuth token)
- `~/projects/email-agent/.env` (Email passwords)

### Python Virtual Environment
Always activate the venv before working with email agent:
```bash
source ~/projects/email-agent/venv/bin/activate
# Do work
deactivate
```

### Git Configuration
Git is configured at `~/projects/.git`. All commits go to this repository:
```bash
cd ~/projects
git config user.name    # Should be "Scott Carroll"
git config user.email   # Should be "scottqcarroll@gmail.com"
```

### Email API Server
The email API server runs on `localhost:5050` when email_agent.py is executed. It:
- Handles email delete requests from the dashboard
- Auto-shuts down after 2 hours
- Only accessible from the local machine

---

## Windows Cleanup

**Deleted from Windows:**
- `C:\Users\scarroll\OneDrive\Desktop\Claude_Code\` (old project directory)
- Windows Task Scheduler email jobs (no longer used)

**Kept on Windows:**
- `~/.ssh/` folder (SSH keys for authentication)
- Tailscale application (for VPN connectivity)

---

## Next Steps

1. **Verify Setup:** Test each quick start command above
2. **Test Email Agent:** Check tomorrow's 9 AM execution
3. **Commit First Change:** Make a small change and commit to test git workflow
4. **Remote Work Test:** Try SSHing from your Mac laptop to verify Tailscale access
5. **Backup Credentials:** Securely back up `.env` and JSON credential files

---

## Support & Reference

**File Locations:**
- Projects: `~/projects/`
- Git: `~/projects/.git/`
- Email Agent: `~/projects/email-agent/`
- Python Venv: `~/projects/email-agent/venv/`
- Logs: `~/projects/email-agent/cron.log`

**Key Commands:**
```bash
ssh clawz840              # Quick access to Linux
cd ~/projects             # Projects directory
git status                # Check changes
crontab -l                # View scheduled jobs
tailscale status          # Check VPN status
```

---

## System Architecture Summary

| Layer | Component | Status |
|-------|-----------|--------|
| **Compute** | Linux Server (ClawZ840) | ✓ Ready |
| **Storage** | ~/projects/ (all code) | ✓ Ready |
| **Version Control** | Git @ ~/projects/.git/ | ✓ Ready |
| **Automation** | Cron (9 AM daily) | ✓ Ready |
| **Email** | Gmail API + Telegram | ✓ Ready |
| **VPN** | Tailscale mesh network | ✓ Ready |
| **Access** | SSH keyless auth | ✓ Ready |
| **Clients** | Windows + Mac | ✓ Ready |

---

**Setup Verified:** May 5, 2026  
**Last Updated:** May 5, 2026  
**System Status:** ✓ OPERATIONAL
