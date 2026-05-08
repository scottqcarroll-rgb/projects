#!/bin/bash
cd ~/projects/email-agent
source venv/bin/activate
python3 email_agent.py --gmail --force >> ~/projects/email-agent/cron.log 2>&1
