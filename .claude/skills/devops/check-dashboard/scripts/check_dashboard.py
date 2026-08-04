#!/usr/bin/env python3
"""Check Dashboard - Regression detection for Flask dashboard."""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

DASHBOARD_DIR = Path("/home/scott/projects/dashboard")
BASELINE_DIR = DASHBOARD_DIR / ".dashboard-baseline"
TEMPLATE_PATH = DASHBOARD_DIR / "templates" / "dashboard.html"
DATA_FETCHER_PATH = DASHBOARD_DIR / "data_fetcher.py"
APP_PATH = DASHBOARD_DIR / "app.py"

# Known-good baseline commit (last with full Linux/Mac Studio cards)
DEFAULT_BASELINE_COMMIT = "0457814"

# Expected template fields per tile function
EXPECTED_TEMPLATE_FIELDS = {
    "loadLinuxServer": [
        "hostname", "cpu_model", "load_1m", "load_5m", "load_15m",
        "memory_used_pct", "memory_avail_gb", "memory_total_gb",
        "disk_pct", "disk_used", "disk_total", "uptime", "cpu_temp", "ip"
    ],
    "loadMacStudio": [
        "hostname", "model", "chip", "os", "ram", "storage",
        "load_1m", "load_5m", "load_15m",
        "memory_used_pct", "memory_used_gb", "memory_total_gb",
        "disk_pct", "disk_used", "disk_total"
    ],
    "loadTrueNAS": ["version", "uptime", "cpu_physical_cores", "memory_total_gb", "apps_running", "apps_total"],
    "loadCameras": [],  # Uses data.cameras array iterated, not individual fields
    "loadWeather": ["temperature", "condition", "feels_like", "humidity", "wind_speed"],
    "loadDriveReport": ["distance_miles", "duration_minutes", "departure_time", "arrival_time"],
    "loadPMDriveReport": ["distance_miles", "duration_minutes", "departure_time", "arrival_time"],
    "loadLLMMetrics": ["total_calls", "today_calls", "avg_30_day", "hourly_rate", "share_of_total"],
    "loadGmail": ["unread_count", "total_count", "latest"],
    "loadLinks": [],  # Uses data.links array iterated
    "loadServerTime": ["datetime"],
    "loadOpenRoute": ["usage_total", "usage_daily", "usage_weekly", "usage_monthly", "limit", "limit_remaining", "is_free_tier"],
    "loadGemma": ["ollama_running", "models", "running"],
}

# Expected API endpoint -> data_fetcher function mapping
API_ENDPOINTS = {
    "/api/linux-server": "get_linux_server_status",
    "/api/mac-studio": "get_mac_studio_status",
    "/api/truenas": "get_truenas_status",
    "/api/weather": "get_weather",
    "/api/drive": "get_drive_report",
    "/api/pm-drive": "get_pm_drive_report",
    "/api/llm-metrics": "get_llm_metrics",  # special - reads log file
    "/api/ollama": "get_ollama_status",
    "/api/mac-studio/ollama": "get_mac_studio_ollama_status",
    "/api/cameras": "get_camera_snapshots",
    "/api/samhunter": "get_sam_hunter",
    "/api/gmail": "get_gmail_summary",
    "/api/usage": "get_openrouter_usage",
}


def run_cmd(cmd: List[str], cwd: Path = None) -> subprocess.CompletedProcess:
    """Run command and return result."""
    return subprocess.run(cmd, cwd=cwd or DASHBOARD_DIR, capture_output=True, text=True)


def get_git_commit() -> str:
    """Get current git commit hash."""
    result = run_cmd(["git", "rev-parse", "HEAD"])
    return result.stdout.strip()


def extract_template_functions(html: str) -> Dict[str, str]:
    """Extract JavaScript load functions from dashboard template."""
    functions = {}
    # Pattern to match async function loadX() { ... }
    pattern = r'(async function (load\w+)\(\) \{[\s\S]*?\n        \})'
    matches = re.findall(pattern, html)
    for full_func, func_name in matches:
        functions[func_name] = full_func
    return functions


def extract_fields_from_function(func_code: str) -> List[str]:
    """Extract data.field references from a load function."""
    # Match ${data.field_name} patterns including ${data.field || ...} and ${(data.field * 100)...}
    # Also catch ${variable.length} and ${m.field} patterns for array iterations
    fields = set()
    
    # Pattern 1: ${data.field} or ${data.field || ...} (simple case)
    pattern1 = r'\$\{data\.(\w+)(?:\s*\|\|)?'
    fields.update(re.findall(pattern1, func_code))
    
    # Pattern 2: ${(data.field || 0).toFixed(2)} - parenthesized with default
    pattern2 = r'\$\{\(data\.(\w+)\s*\|\|'
    fields.update(re.findall(pattern2, func_code))
    
    # Pattern 3: ${(data.field * 100)...} - math expressions
    pattern3 = r'\$\{\(data\.(\w+)\s*[*/+-]'
    fields.update(re.findall(pattern3, func_code))
    
    # Pattern 4: ${variable.length} - for array length access
    pattern4 = r'\$\{(\w+)\.length\}'
    fields.update(re.findall(pattern4, func_code))
    
    # Pattern 5: ${m.field} - for array element access
    pattern5 = r'\$\{m\.(\w+)\}'
    fields.update(re.findall(pattern5, func_code))
    
    # Pattern 6: ${pool.field} - for array element access
    pattern6 = r'\$\{pool\.(\w+)\}'
    fields.update(re.findall(pattern6, func_code))
    
    # Pattern 7: ${alerts.FIELD} - for alert counts
    pattern7 = r'\$\{alerts\.(\w+)(?:\s*\|\|)?'
    fields.update(re.findall(pattern7, func_code))
    
    return list(fields)


def extract_api_fields_from_data_fetcher() -> Dict[str, List[str]]:
    """Extract return dict keys from data_fetcher functions."""
    content = DATA_FETCHER_PATH.read_text()
    api_fields = {}
    
    for endpoint, func_name in API_ENDPOINTS.items():
        if func_name == "get_llm_metrics":
            continue  # special case
        
        # Find function definition and its return dict
        pattern = rf'def {func_name}\(.*?\):[\s\S]*?return\s+\{{([\s\S]*?)\n\}}'
        match = re.search(pattern, content)
        if match:
            return_dict = match.group(1)
            # Extract keys from return dict
            keys = re.findall(r'["\'](\w+)["\']\s*:', return_dict)
            api_fields[endpoint] = keys
        else:
            api_fields[endpoint] = []
    
    return api_fields


def capture_baseline(commit: str = None) -> None:
    """Capture current state as baseline."""
    commit = commit or get_git_commit()
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save commit
    (BASELINE_DIR / "commit.txt").write_text(commit)
    
    # Save template fields
    html = TEMPLATE_PATH.read_text()
    functions = extract_template_functions(html)
    template_fields = {}
    for func_name, func_code in functions.items():
        if func_name in EXPECTED_TEMPLATE_FIELDS:
            template_fields[func_name] = extract_fields_from_function(func_code)
    (BASELINE_DIR / "template-fields.json").write_text(json.dumps(template_fields, indent=2))
    
    # Save API fields
    api_fields = extract_api_fields_from_data_fetcher()
    (BASELINE_DIR / "api-fields.json").write_text(json.dumps(api_fields, indent=2))
    
    print(f"✅ Baseline captured at commit {commit}")
    print(f"   Template functions: {len(template_fields)}")
    print(f"   API endpoints: {len(api_fields)}")


def load_baseline() -> Dict:
    """Load baseline from disk."""
    if not BASELINE_DIR.exists():
        return None
    
    commit = (BASELINE_DIR / "commit.txt").read_text().strip()
    template_fields = json.loads((BASELINE_DIR / "template-fields.json").read_text())
    api_fields = json.loads((BASELINE_DIR / "api-fields.json").read_text())
    
    return {
        "commit": commit,
        "template_fields": template_fields,
        "api_fields": api_fields,
    }


def check_template_fields(baseline: Dict) -> List[str]:
    """Check current template against baseline."""
    errors = []
    html = TEMPLATE_PATH.read_text()
    functions = extract_template_functions(html)
    
    for func_name, expected_fields in EXPECTED_TEMPLATE_FIELDS.items():
        if func_name not in functions:
            errors.append(f"❌ Missing template function: {func_name}")
            continue
        
        current_fields = extract_fields_from_function(functions[func_name])
        baseline_fields = baseline["template_fields"].get(func_name, [])
        
        # Check against expected (not just baseline, in case baseline was captured at bad state)
        missing_expected = set(expected_fields) - set(current_fields)
        if missing_expected:
            errors.append(f"❌ {func_name}: Missing expected fields: {sorted(missing_expected)}")
        
        # Also check against baseline for any regression
        missing_baseline = set(baseline_fields) - set(current_fields)
        if missing_baseline:
            errors.append(f"⚠️  {func_name}: Regression vs baseline (missing): {sorted(missing_baseline)}")
    
    return errors


def check_api_fields(baseline: Dict) -> List[str]:
    """Check current data_fetcher API fields against baseline."""
    errors = []
    current_api_fields = extract_api_fields_from_data_fetcher()
    
    for endpoint, baseline_fields in baseline["api_fields"].items():
        current_fields = current_api_fields.get(endpoint, [])
        missing = set(baseline_fields) - set(current_fields)
        if missing:
            errors.append(f"❌ {endpoint}: Missing API fields vs baseline: {sorted(missing)}")
    
    return errors


def check_live_endpoints() -> List[str]:
    """Check live API endpoints (requires running dashboard)."""
    errors = []
    import requests
    import time
    
    base_url = "http://localhost:5001"
    endpoints = list(API_ENDPOINTS.keys()) + ["/api/server-time", "/api/links"]
    
    for endpoint in endpoints:
        try:
            start = time.time()
            resp = requests.get(f"{base_url}{endpoint}", timeout=5)
            elapsed = time.time() - start
            
            if resp.status_code != 200:
                errors.append(f"❌ {endpoint}: HTTP {resp.status_code}")
            elif elapsed > 5:
                errors.append(f"⚠️  {endpoint}: Slow response ({elapsed:.1f}s)")
            else:
                data = resp.json()
                if data.get("status") == "error":
                    errors.append(f"❌ {endpoint}: API error - {data.get('message')}")
        except requests.exceptions.ConnectionError:
            errors.append(f"❌ {endpoint}: Connection refused (dashboard not running?)")
        except Exception as e:
            errors.append(f"❌ {endpoint}: {type(e).__name__}: {e}")
    
    return errors


def check_js_errors() -> List[str]:
    """Check for JavaScript errors using headless browser."""
    errors = []
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            console_errors = []
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
            page.on("pageerror", lambda exc: console_errors.append(str(exc)))
            
            page.goto("http://localhost:5001", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(5000)  # Wait for all async loads
            
            browser.close()
            
            if console_errors:
                for err in console_errors:
                    errors.append(f"❌ JS Error: {err}")
    except ImportError:
        errors.append("⚠️  Playwright not installed - skipping JS check (pip install playwright && playwright install chromium)")
    except Exception as e:
        errors.append(f"❌ JS check failed: {e}")
    
    return errors


def diff_commit(commit: str) -> None:
    """Show diff between baseline and a specific commit."""
    baseline = load_baseline()
    if not baseline:
        print("❌ No baseline found. Run 'check-dashboard capture' first.")
        sys.exit(10)
    
    # Get template at that commit
    result = run_cmd(["git", "show", f"{commit}:dashboard/templates/dashboard.html"])
    if result.returncode != 0:
        # Try alternate path
        result = run_cmd(["git", "show", f"{commit}:templates/dashboard.html"])
        if result.returncode != 0:
            print(f"❌ Could not read template at commit {commit}")
            sys.exit(1)
    
    old_html = result.stdout
    old_functions = extract_template_functions(old_html)
    
    print(f"\n=== Diff: Baseline ({baseline['commit'][:8]}) vs {commit[:8]} ===\n")
    
    for func_name in EXPECTED_TEMPLATE_FIELDS:
        baseline_fields = set(baseline["template_fields"].get(func_name, []))
        old_fields = set(extract_fields_from_function(old_functions.get(func_name, "")))
        
        added = old_fields - baseline_fields
        removed = baseline_fields - old_fields
        
        if added or removed:
            print(f"  {func_name}:")
            if added:
                print(f"    + Added: {sorted(added)}")
            if removed:
                print(f"    - Removed: {sorted(removed)}")


def main():
    parser = argparse.ArgumentParser(description="Check dashboard for regressions")
    parser.add_argument("command", choices=["check", "capture", "diff", "list-baselines"])
    parser.add_argument("--full", action="store_true", help="Run live endpoint and JS checks")
    parser.add_argument("commit", nargs="?", help="Commit to diff against (for diff command)")
    args = parser.parse_args()
    
    if args.command == "capture":
        capture_baseline()
        return
    
    if args.command == "list-baselines":
        if BASELINE_DIR.exists():
            commit = (BASELINE_DIR / "commit.txt").read_text().strip()
            print(f"Baseline: {commit[:8]} ({commit})")
            print(f"  Template functions: {len(json.loads((BASELINE_DIR / 'template-fields.json').read_text()))}")
            print(f"  API endpoints: {len(json.loads((BASELINE_DIR / 'api-fields.json').read_text()))}")
        else:
            print("No baseline captured yet. Run 'check-dashboard capture'")
        return
    
    if args.command == "diff":
        if not args.commit:
            print("❌ diff command requires a commit argument")
            sys.exit(1)
        diff_commit(args.commit)
        return
    
    # Check command
    baseline = load_baseline()
    if not baseline:
        print("❌ No baseline found. Run 'check-dashboard capture' first.")
        sys.exit(10)
    
    all_errors = []
    
    print(f"🔍 Checking against baseline {baseline['commit'][:8]}...")
    
    # Template fields
    template_errors = check_template_fields(baseline)
    all_errors.extend(template_errors)
    
    # API fields
    api_errors = check_api_fields(baseline)
    all_errors.extend(api_errors)
    
    # Live checks
    if args.full:
        print("🌐 Checking live endpoints...")
        live_errors = check_live_endpoints()
        all_errors.extend(live_errors)
        
        print("🌐 Checking JavaScript console...")
        js_errors = check_js_errors()
        all_errors.extend(js_errors)
    
    # Report
    if all_errors:
        print(f"\n❌ Found {len(all_errors)} issue(s):")
        for err in all_errors:
            print(f"  {err}")
        
        # Determine exit code
        has_template = any(e.startswith("❌") and "Missing template" in e or "Missing expected" in e for e in all_errors)
        has_api = any(e.startswith("❌") and "Missing API fields" in e for e in all_errors)
        has_live = any(e.startswith("❌") and ("HTTP" in e or "Connection refused" in e or "API error" in e) for e in all_errors)
        has_js = any(e.startswith("❌ JS Error") for e in all_errors)
        
        if has_template:
            sys.exit(1)
        elif has_api:
            sys.exit(2)
        elif has_live:
            sys.exit(3)
        elif has_js:
            sys.exit(4)
        else:
            sys.exit(1)
    else:
        print("✅ All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()