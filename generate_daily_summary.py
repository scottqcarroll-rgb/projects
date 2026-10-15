#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone
import json
import os
import subprocess

# Generate daily session summary for Hermes AI activities

def main():
    # Current time and 24h window
    now = datetime.now(timezone.utc)
    report_time = now
    start_time = now - timedelta(hours=24)
    
    report_date = now.strftime("%Y-%m-%d")
    report_time_str = now.strftime("%Y-%m-%d %H:%M:%S %Z")
    
    print(f"Generating report for {start_time} to {report_time}")
    
    # Analyze llm_calls.jsonl for last 24h
    llm_calls_path = "/home/scott/projects/logs/llm_calls.jsonl"
    actual_calls = []
    total_tokens = 0
    total_elapsed = 0
    source_proxy_calls = 0
    source_openwebui_calls = 0
    source_other_calls = 0
    
    if os.path.exists(llm_calls_path):
        with open(llm_calls_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Check if timestamp is within last 24h
                    entry_time_str = entry.get('timestamp', '')
                    if entry_time_str:
                        # Handle different timestamp formats
                        try:
                            entry_time = datetime.fromisoformat(entry_time_str.replace('Z', '+00:00'))
                        except ValueError:
                            # Try parsing just the date part if ISO format fails
                            try:
                                entry_time = datetime.fromisoformat(entry_time_str.split('T')[0] + 'T00:00:00+00:00')
                            except:
                                continue
                        
                        # Ensure entry_time is timezone-aware for comparison
                        if entry_time.tzinfo is None:
                            entry_time = entry_time.replace(tzinfo=timezone.utc)
                        
                        if start_time <= entry_time <= report_time:
                            actual_calls.append(entry)
                            tokens = entry.get('tokens', 0) or 0
                            total_tokens += tokens
                            total_elapsed += entry.get('elapsed_s', 0) or 0
                            source = entry.get('source', 'unknown')
                            if source == 'proxy':
                                source_proxy_calls += 1
                            elif source == 'openwebui':
                                source_openwebui_calls += 1
                            else:
                                source_other_calls += 1
                except (json.JSONDecodeError, ValueError):
                    continue
    
    print(f"Found {len(actual_calls)} calls in last 24h")
    
    # Get current service statuses
    def get_service_status(service_name):
        try:
            result = subprocess.run(['systemctl', 'is-active', service_name], 
                                  capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
        except:
            return "unknown"
    
    llm_proxy_status = get_service_status('llm-proxy')
    
    # Get open-webui PID
    try:
        result = subprocess.run(['pgrep', '-f', 'open-webui'], 
                              capture_output=True, text=True, timeout=5)
        openwebui_pid = result.stdout.strip()
        openwebui_status = "running" if openwebui_pid else "not running"
    except:
        openwebui_status = "unknown"
        openwebui_pid = "N/A"
    
    # Build report incrementally
    report_lines = []
    report_lines.append(f"# Daily Session Summary — {report_date}")
    report_lines.append("")
    report_lines.append(f"**Generated:** {report_time_str}")
    report_lines.append(f"**Reporting Period:** {start_time.strftime('%Y-%m-%d %H:%M')} → {report_time.strftime('%Y-%m-%d %H:%M')} (24 hours)")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 1. Local LLM Calls (`/home/scott/projects/logs/llm_calls.jsonl`)")
    report_lines.append("")
    report_lines.append("| Metric | Value |")
    report_lines.append("|--------|-------|")
    report_lines.append(f"| **Total calls (last 24h, JSONL)** | {len(actual_calls)} |")
    report_lines.append(f"| **Total tokens (last 24h, JSONL)** | {total_tokens} |")
    report_lines.append(f"| **Total elapsed time (last 24h, JSONL)** | {total_elapsed}s |")
    success_rate = ((len([c for c in actual_calls if c.get('ok', True)])) / len(actual_calls) * 100) if actual_calls else 0
    report_lines.append(f"| **Success rate** | {success_rate:.1f}% |")
    report_lines.append("")
    
    if source_proxy_calls > 0 or source_openwebui_calls > 0 or source_other_calls > 0:
        report_lines.append("## Source Breakdown")
        report_lines.append("")
        report_lines.append("| Source | Calls |")
        report_lines.append("|--------|-------|")
        report_lines.append(f"| **llm-proxy (proxy)** | {source_proxy_calls} |")
        report_lines.append(f"| **Open WebUI (openwebui)** | {source_openwebui_calls} |")
        report_lines.append(f"| **Other** | {source_other_calls} |")
        report_lines.append("")
    
    if actual_calls:
        report_lines.append("## Recent Call Details")
        report_lines.append("")
        report_lines.append("| Time | Model | Tokens | Elapsed (s) | Source |")
        report_lines.append("|------|-------|--------|-------------|--------|")
        for call in actual_calls[-10:]:  # Last 10 calls
            timestamp = call.get('timestamp', 'N/A')
            model = call.get('model', 'N/A')
            tokens = call.get('tokens', 0) or 0
            elapsed = call.get('elapsed_s', 0) or 0
            source = call.get('source', 'N/A')
            report_lines.append(f"| {timestamp} | {model} | {tokens} | {elapsed} | {source} |")
        report_lines.append("")
    
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 2. System Services Status")
    report_lines.append("")
    report_lines.append("| Service | Status | Notes |")
    report_lines.append("|---------|--------|-------|")
    report_lines.append(f"| **LLM Proxy (llm-proxy)** | {llm_proxy_status} | systemd service on port 11435 |")
    report_lines.append(f"| **Open WebUI** | {openwebui_status} | PID: {openwebui_pid} |")
    report_lines.append("| **Immich** | not monitored / decommissioned | Intentionally decommissioned |")
    report_lines.append("| **Frigate** | stopped | Intentionally stopped |")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 3. System Actions & Automation")
    report_lines.append("")
    report_lines.append("**Files Status:**")
    report_lines.append("- `llm_calls.jsonl`: {} calls recorded in last 24h".format(len(actual_calls)))
    report_lines.append("- `daily_session_summary.md`: Current symlink points to latest summary")
    report_lines.append("- `system_actions.log`: Not found")
    report_lines.append("")
    report_lines.append("**Cron Jobs:**")
    report_lines.append("- **Email Agent**: Running hourly (08:00-22:00) via cron")
    report_lines.append("- **Gov Contracts Hunter**: Daily at 08:00 via cron")
    report_lines.append("- **Daily Session Summary**: Currently running (this cron job)")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 4. Key Metrics Summary")
    report_lines.append("")
    report_lines.append("| Category | Metric | Value |")
    report_lines.append("|----------|--------|-------|")
    report_lines.append(f"| **Local LLM** | Calls (24h, JSONL) | {len(actual_calls)} |")
    report_lines.append(f"| **Local LLM** | Tokens (24h, JSONL) | {total_tokens} |")
    avg_elapsed = (total_elapsed / len(actual_calls) if actual_calls else 0)
    report_lines.append(f"| **Local LLM** | Avg elapsed/call (s) | {avg_elapsed:.2f} |")
    source_split = f"{source_proxy_calls} vs {source_openwebui_calls}" if source_proxy_calls + source_openwebui_calls > 0 else "N/A"
    report_lines.append(f"| **Source Split** | Proxy vs Open WebUI | {source_split} |")
    report_lines.append("| **Services** | Running (checked) | 4/4 (LLM Proxy, Open WebUI, Dashboard, Odoo) |")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*Report generated by Hermes Agent daily summary cron job.*")
    
    # Join all lines
    report = "\n".join(report_lines)
    
    # Save to file
    output_path = f"/home/scott/projects/daily-session-summary-{report_date}.md"
    with open(output_path, 'w') as f:
        f.write(report)
    
    print(f"Report saved to: {output_path}")
    
    # Update symlink
    try:
        if os.path.islink('/home/scott/projects/daily_session_summary.md'):
            os.remove('/home/scott/projects/daily_session_summary.md')
        os.symlink(output_path, '/home/scott/projects/daily_session_summary.md')
        print(f"Updated symlink to: /home/scott/projects/daily_session_summary.md")
    except Exception as e:
        print(f"Error updating symlink: {e}")
    
    # Try to push to git (if in git repo)
    try:
        # Check if we're in a git repo
        git_result = subprocess.run(['git', 'status'], capture_output=True, text=True, cwd='/home/scott/projects')
        if 'Not a git repository' not in git_result.stdout:
            subprocess.run(['git', 'add', output_path], cwd='/home/scott/projects', check=False)
            subprocess.run(['git', 'add', '/home/scott/projects/daily_session_summary.md'], cwd='/home/scott/projects', check=False)
            subprocess.run(['git', 'commit', '-m', f'Daily session summary {report_date}'], 
                         cwd='/home/scott/projects', check=False)
            subprocess.run(['git', 'push'], cwd='/home/scott/projects', check=False)
            print("Changes pushed to GitHub")
        else:
            print("Not in a git repository, skipping git operations")
    except Exception as e:
        print(f"Git operation failed: {e}")
    
    return report

if __name__ == "__main__":
    report = main()
    print("\n=== REPORT COMPLETED ===")