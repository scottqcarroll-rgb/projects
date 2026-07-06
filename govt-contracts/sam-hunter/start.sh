#!/bin/bash
# Start Sam Hunter on port 5001
cd "$(dirname "$0")"
source /home/scott/projects/email-agent/venv/bin/activate
python3 app.py
