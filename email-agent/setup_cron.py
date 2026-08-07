#!/usr/bin/env python3
"""
Setup Daily Cleanup as Systemd Service + Timer
Run this once to install the daily email cleanup as a systemd timer.

Usage:
    python3 setup_cron.py
"""

import os
import sys
import subprocess
import getpass


def run_cmd(cmd, check=True):
    """Run command and return result"""
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"[ERROR] Command failed: {cmd}")
        print(f"  stdout: {result.stdout}")
        print(f"  stderr: {result.stderr}")
        return False
    return result


def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    user = getpass.getuser()
    
    print(f"[*] Setting up daily email cleanup for user: {user}")
    print(f"[*] Project directory: {project_dir}")
    
    # Service file
    service_content = f"""[Unit]
Description=Daily Email Cleanup Agent
After=network.target

[Service]
Type=oneshot
User={user}
WorkingDirectory={project_dir}
Environment=PATH={project_dir}/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart={project_dir}/venv/bin/python {project_dir}/daily_cleanup.py
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"""
    
    # Timer file
    timer_content = """[Unit]
Description=Run Daily Email Cleanup every day at 6 AM

[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true
RandomizedDelaySec=15m

[Install]
WantedBy=timers.target
"""
    
    # Write service file
    service_path = f"/etc/systemd/system/email-cleanup.service"
    timer_path = f"/etc/systemd/system/email-cleanup.timer"
    
    print(f"[*] Writing service file to {service_path}")
    try:
        with open("/tmp/email-cleanup.service", "w") as f:
            f.write(service_content)
        run_cmd(f"sudo mv /tmp/email-cleanup.service {service_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write service file: {e}")
        return 1
    
    print(f"[*] Writing timer file to {timer_path}")
    try:
        with open("/tmp/email-cleanup.timer", "w") as f:
            f.write(timer_content)
        run_cmd(f"sudo mv /tmp/email-cleanup.timer {timer_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write timer file: {e}")
        return 1
    
    # Reload systemd
    print("[*] Reloading systemd daemon...")
    run_cmd("sudo systemctl daemon-reload")
    
    # Enable and start timer
    print("[*] Enabling and starting timer...")
    run_cmd("sudo systemctl enable email-cleanup.timer")
    run_cmd("sudo systemctl start email-cleanup.timer")
    
    # Verify
    print("[*] Verifying timer...")
    result = run_cmd("systemctl list-timers email-cleanup.timer --no-pager", check=False)
    if result:
        print(result.stdout)
    
    print("\n[SUCCESS] Daily cleanup installed as systemd timer!")
    print("\nUseful commands:")
    print("  sudo systemctl status email-cleanup.timer    # Check timer status")
    print("  sudo systemctl start email-cleanup.service   # Run manually now")
    print("  sudo journalctl -u email-cleanup.service -f  # View logs")
    print("  sudo systemctl stop email-cleanup.timer      # Stop timer")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())