#!/usr/bin/env python3
"""Retired installer stub.

daily_cleanup.py was decommissioned on 2026-11-23. Its live replacements are
/home/scott/inbox-cleanup/run_inbox_cleanup.sh (08:00) and
/home/scott/projects/email-agent/run_email_agent.sh (09:00).
"""

import sys


def main():
    print("[DISABLED] daily_cleanup.py was decommissioned on 2026-11-23.")
    print("[DISABLED] No systemd service or timer will be installed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
