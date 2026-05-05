#!/bin/bash
cd ~/email-agent
source venv/bin/activate
python3 email_agent.py --force >> ~/email-agent/cron.log 2>&1
