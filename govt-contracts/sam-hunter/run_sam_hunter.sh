#!/bin/bash
# Persistent launcher — kills any existing instance, then starts fresh
# Run at boot: add to crontab with @reboot
cd /home/scott/projects/govt-contracts/sam-hunter
source /home/scott/projects/email-agent/venv/bin/activate

# Kill any existing instance
pkill -f "sam-hunter/app.py" 2>/dev/null
sleep 1

# Start detached, log to sam-hunter.log
nohup python3 app.py >> /home/scott/projects/govt-contracts/sam-hunter/sam-hunter.log 2>&1 &
echo "[$(date)] Sam Hunter started on port 5001 (PID $!)"
