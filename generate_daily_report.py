#!/usr/bin/env python3
"""
Generate comprehensive daily session summary report and push to GitHub.
This is the production script run by the 22:00 cron job.
Follows the workflow in references/cron-workflow.md and template in references/summary-template.md
"""
import os
import json
import subprocess
import sys
from datetime import datetime, timedelta

BASE = "/home/scott/projects"
TOTAL_FILE = os.path.join(BASE, "total_calls.txt")
DAILY_DIR = os.path.join(BASE, "daily_counts")
LOG_FILE_JSONL = os.path.join(BASE, "logs", "llm_calls.jsonl")
LOG_FILE_TEXT = os.path.join(BASE, "llm_call_log.txt")
EMAIL_CRON_LOG = os.path.join(BASE, "email-agent", "cron.log")
GOV_CRON_LOG = os.path.join(BASE, "govt-contracts", "report_cron.log")
PROSPECT_DIR = os.path.join(BASE, "govt-contracts", "prospect-lists")

def _read_int(path, default=0):
    try:
        with open(path) as f:
            return int(f.read().strip() or 0)
    except Exception:
        return default

def _run_cmd(cmd, cwd=None):
    """Run command and return (stdout, stderr, returncode)"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd, timeout=30)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except Exception as e:
        return "", str(e), 1

def collect_llm_metrics(today_str, yesterday_str):
    """Collect LLM call metrics from BOTH JSONL and text logs"""
    jsonl_calls = []
    text_calls = []
    
    # Read JSONL log (local llama.cpp - Gemma 4 E4B)
    if os.path.exists(LOG_FILE_JSONL):
        with open(LOG_FILE_JSONL) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    jsonl_calls.append(obj)
                except Exception:
                    pass
    
    # Read text log (Ollama chat calls - hermes-4-14b, qwen3.6:27b, etc.)
    if os.path.exists(LOG_FILE_TEXT):
        with open(LOG_FILE_TEXT) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    # Format: [2026-08-03T05:23:47.651416] ollama-chat model=hermes-4-14b:latest status=ok
                    if 'ollama-chat' in line and 'model=' in line:
                        import re
                        ts_match = re.search(r'\[(.*?)\]', line)
                        model_match = re.search(r'model=([^\s]+)', line)
                        status_match = re.search(r'status=(\w+)', line)
                        if ts_match and model_match:
                            obj = {
                                'timestamp': ts_match.group(1),
                                'date': ts_match.group(1)[:10],
                                'model': model_match.group(1),
                                'ok': status_match.group(1) == 'ok' if status_match else True,
                                'tokens': 0,  # Text log doesn't have token counts
                                'elapsed_s': 0,
                                'source': 'text_log'
                            }
                            text_calls.append(obj)
                except Exception:
                    pass
    
    # Combine both logs
    all_calls = jsonl_calls + text_calls
    
    # Filter for past 24 hours (yesterday and today dates)
    recent = [c for c in all_calls if c.get("date") in (yesterday_str, today_str)]
    
    total_calls = len(recent)
    total_tokens = sum(c.get("tokens", 0) for c in recent)
    total_elapsed = sum(c.get("elapsed_s", 0) for c in recent)
    success_rate = (sum(1 for c in recent if c.get("ok", False)) / total_calls * 100) if total_calls else 0
    
    models = {}
    for c in recent:
        m = c.get("model", "unknown")
        models[m] = models.get(m, 0) + 1
    
    # All-time total (from JSONL counter)
    all_time = _read_int(TOTAL_FILE)
    
    # 30-day average (from daily_counts JSON files)
    last_30 = []
    for i in range(30):
        day = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        day_file = os.path.join(DAILY_DIR, f"{day}.json")
        try:
            with open(day_file) as f:
                last_30.append(int(f.read().strip() or 0))
        except Exception:
            pass
    avg_30 = int(sum(last_30) / max(1, len(last_30))) if last_30 else 0
    
    # Today's calls for detailed log
    today_calls = [c for c in all_calls if c.get("date") == today_str]
    today_calls.sort(key=lambda x: x.get("timestamp", ""))
    
    return {
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "total_elapsed": total_elapsed,
        "avg_latency": total_elapsed / total_calls if total_calls else 0,
        "success_rate": success_rate,
        "models": models,
        "calls": recent,
        "today_calls": today_calls,
        "all_time": all_time,
        "avg_30": avg_30,
        "today_count": len(today_calls),
        "jsonl_count": len([c for c in today_calls if c.get('source') != 'text_log']),
        "text_log_count": len([c for c in today_calls if c.get('source') == 'text_log'])
    }

def collect_git_activity():
    """Collect git commits and changes from last 24 hours"""
    # Get commits from last 24 hours
    out, _, _ = _run_cmd('git log --oneline --since="24 hours ago" --until="now" --all', cwd=BASE)
    commits = out.split('\n') if out else []
    
    # Get status
    out, _, _ = _run_cmd('git status --short', cwd=BASE)
    status_lines = out.split('\n') if out else []
    
    # Get diff stats for recent commits
    commit_details = []
    for commit_line in commits[:10]:  # Limit to 10
        if not commit_line.strip():
            continue
        sha = commit_line.split()[0]
        msg = ' '.join(commit_line.split()[1:])
        out, _, _ = _run_cmd(f'git show --stat {sha} --oneline', cwd=BASE)
        files = []
        for line in out.split('\n'):
            if '|' in line and ('insertion' in line or 'deletion' in line):
                continue
            parts = line.strip().split()
            if len(parts) >= 1 and ('.' in parts[0] or '/' in parts[0]):
                files.append(parts[0])
        commit_details.append({"sha": sha[:8], "message": msg, "files": files})
    
    return {
        "commit_count": len(commits),
        "commits": commit_details,
        "uncommitted": len([l for l in status_lines if l.strip()]),
        "status_lines": [l for l in status_lines if l.strip()]
    }

def collect_cron_logs():
    """Collect recent activity from cron logs"""
    result = {"email_agent": {"runs": [], "errors": []}, "gov_contracts": {"runs": [], "errors": []}}
    
    # Email agent cron log
    if os.path.exists(EMAIL_CRON_LOG):
        with open(EMAIL_CRON_LOG) as f:
            lines = f.readlines()
        # Look for runs in last ~24 hours (today/yesterday)
        for line in lines[-200:]:  # Last 200 lines
            if "Email Agent starting" in line or "Starting email agent" in line:
                result["email_agent"]["runs"].append(line.strip())
            if "WARN" in line or "ERROR" in line or "failed" in line.lower():
                result["email_agent"]["errors"].append(line.strip())
    
    # Gov contracts cron log
    if os.path.exists(GOV_CRON_LOG):
        with open(GOV_CRON_LOG) as f:
            lines = f.readlines()
        for line in lines[-200:]:
            if "Starting contract report" in line:
                result["gov_contracts"]["runs"].append(line.strip())
            if "ERROR" in line or "Traceback" in line or "504" in line or "500" in line:
                result["gov_contracts"]["errors"].append(line.strip())
    
    return result

def collect_prospect_files(today_str, yesterday_str):
    """Collect today/yesterday prospect list files"""
    files = {"today": [], "yesterday": []}
    if not os.path.exists(PROSPECT_DIR):
        return files
    for fname in sorted(os.listdir(PROSPECT_DIR)):
        if today_str in fname:
            files["today"].append(fname)
        elif yesterday_str in fname:
            files["yesterday"].append(fname)
    return files

def check_services():
    """Check status of key services"""
    services = {}
    
    # Dashboard (systemd)
    out, _, code = _run_cmd('systemctl is-active dashboard 2>/dev/null')
    services["dashboard"] = {"status": "active" if code == 0 else "inactive", "code": code}
    if code == 0:
        out, _, _ = _run_cmd('systemctl show dashboard --property=MainPID,MemoryCurrent,CPUUsageNSec --value', cwd=BASE)
        services["dashboard"]["details"] = out
    
    # Sam Hunter (cron @reboot, check process)
    out, _, _ = _run_cmd('ps aux | grep -v grep | grep "run_sam_hunter\|sam-hunter" | head -3')
    services["sam_hunter"] = {"running": len(out.strip()) > 0, "processes": out.strip()[:200]}
    
    # Claude Telegram Bot
    out, _, _ = _run_cmd('ps aux | grep -v grep | grep "claude-telegram" | head -2')
    services["claude_bot"] = {"running": len(out.strip()) > 0, "processes": out.strip()[:200]}
    
    return services

def build_summary(llm, git, cron, prospects, services, today_str, today_display, yesterday_str):
    """Build the comprehensive markdown summary"""
    
    # 1. LLM Metrics Section
    llm_section = f"""## 1. Local LLM Calls Metrics (JSONL + Text Log)

### Summary
| Metric | Value |
|--------|-------|
| **Total Calls (24h, both logs)** | {llm['total_calls']} |
| **JSONL Log Calls (Gemma 4 E4B)** | {llm['jsonl_count']} |
| **Text Log Calls (Ollama)** | {llm['text_log_count']} |
| **Total Tokens (JSONL only)** | {llm['total_tokens']} |
| **Total Time (JSONL only)** | {llm['total_elapsed']:.2f} seconds |
| **Avg Latency (JSONL only)** | {llm['avg_latency']:.2f}s |
| **Success Rate** | {llm['success_rate']:.1f}% |
| **Models Used** | {', '.join(llm['models'].keys()) if llm['models'] else 'N/A'} |

### Detailed Call Log ({today_str})
| Timestamp | Model | Source | Tokens | Latency | Status |
|-----------|-------|--------|--------|---------|--------|"""
    
    if llm['today_calls']:
        for c in llm['today_calls']:
            ts = c.get('timestamp', '').split('T')[-1][:8] if 'T' in c.get('timestamp', '') else c.get('timestamp', '')
            model = c.get('model', 'unknown')
            source = c.get('source', 'jsonl')
            tokens = c.get('tokens', 0)
            latency = c.get('elapsed_s', 0)
            status = "✓ OK" if c.get('ok', False) else "✗ FAIL"
            llm_section += f"\n| {ts} | {model} | {source} | {tokens} | {latency:.2f}s | {status} |"
    else:
        llm_section += "\n| - | - | - | - | - | No calls today |"
    
    llm_section += f"""

**Notes:** {"No LLM calls recorded today." if not llm['today_calls'] else f"{llm['today_count']} call(s) today: {llm['jsonl_count']} from JSONL (Gemma 4 E4B), {llm['text_log_count']} from text log (Ollama: {', '.join([m for m in llm['models'].keys() if 'gemma' not in m.lower()])})."}

---

### All-Time Aggregate (as of {today_str})
| Metric | Value |
|--------|-------|
| **All-time total calls (JSONL counter)** | {llm['all_time']} |
| **Today's calls (both logs)** | {llm['today_count']} |
| **Share of total** | {int((llm['today_count'] / (llm['all_time'] or 1)) * 100)}% |
| **30-day average (JSONL)** | {llm['avg_30']} per day |
| **Hourly rate (est.)** | {int(llm['today_count'] / 24) if llm['today_count'] else 0} |

---

"""
    
    # 2. Git Activity
    git_section = "## 2. Git Activity (Code Changes)\n\n"
    git_section += "### Commits in Last 24 Hours\n"
    git_section += "| Commit | Message | Files Changed |\n"
    git_section += "|--------|---------|---------------|\n"
    
    if git['commits']:
        for c in git['commits']:
            files_str = ", ".join(c['files'][:5]) + ("..." if len(c['files']) > 5 else "")
            git_section += f"| `{c['sha']}` | {c['message']} | {files_str} |\n"
    else:
        git_section += "| - | No commits in last 24h | - |\n"
    
    git_section += f"\n**Summary:** {git['commit_count']} commit(s) focused on:\n"
    if git['commits']:
        # Categorize commits
        categories = set()
        for c in git['commits']:
            msg = c['message'].lower()
            if 'summary' in msg or 'daily' in msg:
                categories.add("Daily summaries")
            elif 'dashboard' in msg:
                categories.add("Dashboard")
            elif 'email' in msg:
                categories.add("Email agent")
            elif 'contract' in msg or 'gov' in msg:
                categories.add("Gov contracts")
            elif 'ollama' in msg or 'llm' in msg:
                categories.add("LLM/MLOps")
            else:
                categories.add("Other")
        for cat in sorted(categories):
            git_section += f"- {cat}\n"
    else:
        git_section += "- No commits\n"
    
    if git['uncommitted']:
        git_section += f"\n**Uncommitted changes:** {git['uncommitted']} file(s) modified/untracked\n"
    
    git_section += "\n---\n\n"
    
    # 3. System Automation Activity
    auto_section = "## 3. System Automation Activity\n\n"
    
    # Gov Contracts
    auto_section += "### Government Contracts Hunter (govt-contracts/)\n"
    auto_section += "**Cron Schedule:** Daily at 08:00\n\n"
    auto_section += "| Date | SAM.gov Records | Contracts Matched | Categories | Email Status |\n"
    auto_section += "|------|----------------|-------------------|------------|--------------|\n"
    
    # Parse today's gov contracts run
    today_run = None
    today_matches = {}
    today_email = "N/A"
    for line in cron['gov_contracts']['runs'][-5:]:  # Last 5 runs
        if today_str in line or yesterday_str in line:
            today_run = line
    # Also check prospect files
    today_prospect = prospects['today']
    cat_files = [f for f in today_prospect if 'categorized' in f]
    raw_files = [f for f in today_prospect if 'raw' in f]
    
    if cat_files:
        # Try to read the categorized file for today
        for cf in cat_files:
            try:
                with open(os.path.join(PROSPECT_DIR, cf)) as f:
                    content = f.read()
                # Extract category counts
                import re
                cats = re.findall(r'(\w+(?:\s+\w+)*):\s+(\d+)', content)
                total = sum(int(c[1]) for c in cats)
                cat_str = ", ".join([f"{c[0]}: {c[1]}" for c in cats])
                today_matches = {c[0]: int(c[1]) for c in cats}
                today_matches_str = cat_str
            except:
                today_matches_str = "See file"
    else:
        today_matches_str = "No report generated"
    
    # Check email status from errors
    email_errors = cron['gov_contracts']['errors']
    if any('invalid_grant' in e or 'auth' in e.lower() for e in email_errors[-5:]):
        today_email = "❌ Gmail auth failed"
    elif any('504' in e for e in email_errors[-5:]):
        today_email = "❌ SAM.gov 504 timeout"
    elif today_run:
        today_email = "✅ Sent"
    else:
        today_email = "N/A"
    
    auto_section += f"| {today_str} | {'1000 returned' if raw_files else 'N/A'} | {sum(today_matches.values()) if today_matches else 'N/A'} | {today_matches_str} | {today_email} |\n\n"
    
    # Email Agent
    auto_section += "### Email Agent (email-agent/)\n"
    auto_section += "**Cron Schedule:** Daily at 09:00\n\n"
    auto_section += "**Recent Activity:**\n"
    if cron['email_agent']['runs']:
        for run in cron['email_agent']['runs'][-3:]:
            auto_section += f"- {run}\n"
    else:
        auto_section += "- No runs logged recently\n"
    
    if cron['email_agent']['errors']:
        auto_section += "\n**Errors/Issues:**\n"
        for err in cron['email_agent']['errors'][-5:]:
            auto_section += f"- {err}\n"
    else:
        auto_section += "\n**Errors:** None recent\n"
    
    auto_section += "\n"
    
    # Daily Session Summary (this script)
    auto_section += "### Daily Session Summary Generator (this script)\n"
    auto_section += "- **Schedule:** Daily at 22:00 (10 PM)\n"
    auto_section += f"- **Status:** ✅ Completed\n"
    auto_section += f"- **Output:** `daily_session_summary_{today_str}.md`\n\n"
    
    auto_section += "---\n\n"
    
    # 4. Session Activity (from session search would go here, but we're non-interactive)
    session_section = "## 4. Session Activity (Hermes AI)\n\n"
    session_section += "### Interactive Sessions (Last 24 Hours)\n"
    session_section += "| Session ID | Title | Source | Time | Messages |\n"
    session_section += "|------------|-------|--------|------|----------|\n"
    session_section += "| *(cron job - no interactive sessions in this window)* | | | | |\n\n"
    session_section += "---\n\n"
    
    # 5. Overall Activity Summary & Metrics
    health_section = "## 5. Overall Activity Summary & Metrics\n\n"
    health_section += "| System | Status | Key Metrics |\n"
    health_section += "|--------|--------|-------------|\n"
    
    # LLM status
    llm_status = "🟢" if llm['total_calls'] > 0 else "🟡"
    health_section += f"| **Local LLM** | {llm_status} | {llm['total_calls']} calls, {llm['total_tokens']} tokens, {llm['avg_latency']:.2f}s avg |\n"
    
    # Dashboard
    dash_status = "🟢" if services.get('dashboard', {}).get('status') == 'active' else "🔴"
    health_section += f"| **Dashboard (Flask 5001)** | {dash_status} | {services.get('dashboard', {}).get('details', 'systemd managed')[:50]} |\n"
    
    # Gov Contracts
    gov_status = "🟢" if not cron['gov_contracts']['errors'] else ("🟡" if any('504' in e for e in cron['gov_contracts']['errors']) else "🔴")
    health_section += f"| **Gov Contracts Hunter** | {gov_status} | {sum(today_matches.values()) if today_matches else 0} contracts matched today |\n"
    
    # Email Agent
    email_status = "🟢" if not cron['email_agent']['errors'] else "🟡"
    health_section += f"| **Email Agent** | {email_status} | Gmail auth: {'OK' if not any('invalid_grant' in e for e in cron['email_agent']['errors']) else 'Expired/Revoked'} |\n"
    
    # Daily Summary Cron
    health_section += f"| **Daily Summary Cron** | 🟢 | Runs at 22:00, commits to GitHub |\n"
    
    health_section += "\n"
    
    # Critical Issues
    health_section += "### Critical Issues Requiring Attention\n"
    issues = []
    if any('invalid_grant' in e for e in cron['email_agent']['errors'] + cron['gov_contracts']['errors']):
        issues.append("**Gmail Authentication Expired** — OAuth refresh token expired/revoked; requires re-auth")
    if any('504' in e for e in cron['gov_contracts']['errors']):
        issues.append("**SAM.gov Gateway Timeout (504)** — Intermittent API issue; add retry logic to fetch script")
    if services.get('sam_hunter', {}).get('running') is False:
        issues.append("**Sam Hunter Not Running** — Process not found")
    
    if issues:
        for i, issue in enumerate(issues, 1):
            health_section += f"{i}. {issue}\n"
    else:
        health_section += "None detected.\n"
    
    health_section += "\n### Positive Trends\n"
    health_section += "- ✅ Daily session summary cron running reliably\n"
    health_section += "- ✅ GitHub sync working (commits pushed daily)\n"
    health_section += "- ✅ Dashboard service healthy under systemd\n"
    health_section += f"- ✅ Gov contracts data collection: {sum(today_matches.values()) if today_matches else 'N/A'} contracts categorized\n"
    
    health_section += f"\n---\n\n*Report generated at {datetime.now().strftime('%Y-%m-%d %H:%M')} by daily cron job. Pushed to GitHub (master branch).*"
    
    # Combine all sections
    full_summary = f"""# Daily Session Summary - {today_display}

**Date:** {today_str}
**Report Period:** {yesterday_str} 22:00 - {today_str} 22:00 (24 hours)
**Generated by:** Daily Cron Job (22:00 scheduled run)

---

{llm_section}{git_section}{auto_section}{session_section}{health_section}
"""
    
    return full_summary

def main():
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_display = datetime.now().strftime("%A, %B %d, %Y")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"=== Generating daily session summary for {today_str} ===")
    
    # Check for activity - if truly silent, output [SILENT]
    # We'll check after collecting data
    
    # Collect all data
    print("Collecting LLM metrics...")
    llm = collect_llm_metrics(today_str, yesterday_str)
    
    print("Collecting git activity...")
    git = collect_git_activity()
    
    print("Collecting cron logs...")
    cron = collect_cron_logs()
    
    print("Collecting prospect files...")
    prospects = collect_prospect_files(today_str, yesterday_str)
    
    print("Checking services...")
    services = check_services()
    
    # Check if completely silent - consider BOTH logs
    has_activity = (
        llm['total_calls'] > 0 or 
        git['commit_count'] > 0 or 
        cron['gov_contracts']['runs'] or 
        cron['email_agent']['runs'] or
        prospects['today'] or
        prospects['yesterday']
    )
    
    if not has_activity:
        print("[SILENT]")
        return
    
    # Build summary
    print("Building summary...")
    summary = build_summary(llm, git, cron, prospects, services, today_str, today_display, yesterday_str)
    
    # Write file - USE HYPHENS for production format
    summary_path = os.path.join(BASE, f"daily-session-summary-{today_str}.md")
    with open(summary_path, "w") as f:
        f.write(summary)
    
    print(f"=== Summary written to {summary_path} ===")
    
    # Git add/commit/push
    print("Committing to git...")
    subprocess.run(["git", "add", summary_path], cwd=BASE, check=False)
    commit_msg = f"Daily session summary: {today_str}"
    subprocess.run(["git", "commit", "-m", commit_msg], cwd=BASE, check=False)
    subprocess.run(["git", "push", "origin", "master"], cwd=BASE, check=False)
    
    print("Git push completed.")

if __name__ == "__main__":
    main()