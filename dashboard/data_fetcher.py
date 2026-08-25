#!/usr/bin/env python3
import urllib.request
import json
import re
import os
from datetime import datetime, timedelta

# --- Google Maps API Key ---
import glob

def get_maps_key():
    files = glob.glob('/home/scott/.hermes/scripts/*.py')
    if not files:
        raise FileNotFoundError("No API key file found in /home/scott/.hermes/scripts/")
    # Find the file that contains API_KEY=
    for f in files:
        raw = open(f).read()
        idx = raw.find('API_KEY="')
        if idx >= 0:
            rest = raw[idx + 9:]
            return rest.split('"')[0]
    raise ValueError("No file in /home/scott/.hermes/scripts/ contains API_KEY=")

# --- Helper: Get drive routes ---
def get_drive_routes(origin, destination):
    try:
        key = get_maps_key()
        url = 'https://maps.googleapis.com/maps/api/directions/json?origin=' + origin.replace(' ', '+') + '&destination=' + destination.replace(' ', '+') + '&departure_time=now&alternatives=true&key=' + key
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))

        if data.get('status') == 'OK':
            routes = []
            for route in data.get('routes', []):
                leg = route['legs'][0]
                duration_in_traffic = leg.get('duration_in_traffic', {}).get('text', 'N/A')
                traffic_val = leg.get('duration_in_traffic', {}).get('value', 0)
                dur_val = leg.get('duration', {}).get('value', 0)
                delay = ''
                if traffic_val > dur_val:
                    delay = f"+{int((traffic_val - dur_val) / 60)} min traffic"
                routes.append({
                    'summary': route.get('summary', 'N/A'),
                    'distance': leg.get('distance', {}).get('text', 'N/A'),
                    'duration': leg.get('duration', {}).get('text', 'N/A'),
                    'traffic': duration_in_traffic,
                    'delay': delay
                })
            return {'status': 'ok', 'routes': routes}
        else:
            return {'status': 'error', 'message': data.get('status', 'Unknown error')}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_drive_report():
    ORIGIN = '616 Huntwood Cir, Temple GA 30179'
    DESTINATION = '5303 New Peachtree Rd, Chamblee GA 30341'
    result = get_drive_routes(ORIGIN, DESTINATION)
    if result.get('status') == 'ok' and result.get('routes'):
        # Use first route as primary
        route = result['routes'][0]
        # Use TRAFFIC duration (with traffic) for arrival time calculation
        traffic_duration = route.get('traffic', route.get('duration', '0'))
        duration_minutes = parse_duration_to_minutes(traffic_duration)
        departure_time = datetime.now().strftime('%-I:%M %p')
        arrival_time = (datetime.now() + timedelta(minutes=duration_minutes)).strftime('%-I:%M %p')
        return {
            'status': 'ok',
            'origin': ORIGIN.split(',')[0],  # "616 Huntwood Cir"
            'destination': DESTINATION.split(',')[0],  # "5303 New Peachtree Rd"
            'departure_time': departure_time,
            'arrival_time': arrival_time,
            'distance_miles': route.get('distance', 'N/A').replace(' mi', '').replace(',', ''),
            'duration_minutes': duration_minutes,
            'routes': result['routes']
        }
    return result

# --- PM Drive Report (Work → Home) ---
def get_pm_drive_report():
    ORIGIN = '5303 New Peachtree Rd, Chamblee GA 30341'
    DESTINATION = '616 Huntwood Cir, Temple GA 30179'
    result = get_drive_routes(ORIGIN, DESTINATION)
    if result.get('status') == 'ok' and result.get('routes'):
        route = result['routes'][0]
        # Use TRAFFIC duration (with traffic) for arrival time calculation
        traffic_duration = route.get('traffic', route.get('duration', '0'))
        duration_minutes = parse_duration_to_minutes(traffic_duration)
        # Use current time (synced with dashboard) like AM report
        departure_time = datetime.now().strftime('%-I:%M %p')
        departure_dt = datetime.now()
        arrival_time = (departure_dt + timedelta(minutes=duration_minutes)).strftime('%-I:%M %p')
        return {
            'status': 'ok',
            'origin': ORIGIN.split(',')[0],
            'destination': DESTINATION.split(',')[0],
            'departure_time': departure_time,
            'arrival_time': arrival_time,
            'distance_miles': route.get('distance', 'N/A').replace(' mi', '').replace(',', ''),
            'duration_minutes': duration_minutes,
            'routes': result['routes']
        }
    return result

def parse_duration_to_minutes(duration_str):
    """Convert '1 hour 15 mins' or '45 mins' to minutes integer"""
    try:
        if 'hour' in duration_str:
            parts = duration_str.split()
            hours = int(parts[0])
            mins = int(parts[2]) if len(parts) > 2 else 0
            return hours * 60 + mins
        elif 'min' in duration_str:
            return int(duration_str.split()[0])
    except:
        pass
    return 0

# --- 2. Weather Report ---
def get_weather():
    try:
        # Open-Meteo API (free, no key needed) for Temple, GA
        # Request 6 days (today + 5 future days), we'll skip today in the forecast display
        lat, lon = 33.7353, -85.0308
        url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&timezone=America%2FNew_York&forecast_days=6'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))

        current = data.get('current', {})
        daily = data.get('daily', {})

        # WMO Weather codes to text
        wmo = {
            0: 'Clear', 1: 'Mostly Clear', 2: 'Partly Cloudy', 3: 'Overcast',
            45: 'Foggy', 48: 'Foggy', 51: 'Light Drizzle', 53: 'Drizzle',
            55: 'Heavy Drizzle', 61: 'Light Rain', 63: 'Rain', 65: 'Heavy Rain',
            71: 'Light Snow', 73: 'Snow', 75: 'Heavy Snow', 77: 'Snow Grains',
            80: 'Light Showers', 81: 'Showers', 82: 'Heavy Showers',
            85: 'Snow Showers', 86: 'Heavy Snow Showers', 95: 'Thunderstorm',
            96: 'Thunderstorm + Hail', 99: 'Thunderstorm + Heavy Hail'
        }

        code = current.get('weather_code', -1)

        def c_to_f(c):
            if c == 'N/A' or c is None:
                return 'N/A'
            return round(c * 9/5 + 32)

        temp_c = current.get('temperature_2m', 'N/A')
        feels_c = current.get('apparent_temperature', 'N/A')
        high_c = daily.get('temperature_2m_max', ['N/A'])[0]
        low_c = daily.get('temperature_2m_min', ['N/A'])[0]

        # Build 5-day forecast (skip index 0 = today, show indices 1-5 = next 5 days)
        forecast = []
        daily_times = daily.get('time', [])
        daily_max = daily.get('temperature_2m_max', [])
        daily_min = daily.get('temperature_2m_min', [])
        daily_precip = daily.get('precipitation_sum', [])
        daily_codes = daily.get('weather_code', [])
        # Start from index 1 to skip today, show next 5 days
        for i in range(1, min(6, len(daily_times))):
            day_code = daily_codes[i] if i < len(daily_codes) else -1
            forecast.append({
                'date': daily_times[i],
                'high': c_to_f(daily_max[i]) if i < len(daily_max) else 'N/A',
                'low': c_to_f(daily_min[i]) if i < len(daily_min) else 'N/A',
                'precip': daily_precip[i] if i < len(daily_precip) else 'N/A',
                'condition': wmo.get(day_code, f'Unknown ({day_code})')
            })

        return {
            'status': 'ok',
            'temperature': c_to_f(temp_c),
            'condition': wmo.get(code, f'Unknown ({code})'),
            'humidity': current.get('relative_humidity_2m', 'N/A'),
            'wind_speed': round(current.get('wind_speed_10m', 0) * 0.621371, 1) if current.get('wind_speed_10m') else 'N/A',  # km/h to mph
            'feels_like': c_to_f(feels_c),
            'high': c_to_f(high_c),
            'low': c_to_f(low_c),
            'precip': daily.get('precipitation_sum', ['N/A'])[0],
            'forecast': forecast
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_sam_hunter():
    return {
        'status': 'ok',
        'url': 'http://100.124.71.12:5002',
        'name': 'Sam Hunter'
    }

# --- 4. Gmail Summary (integrated with email-agent) ---
def get_gmail_summary():
    try:
        import sys
        sys.path.insert(0, '/home/scott/projects/email-agent')
        from gmail_client import get_authenticated_service, fetch_recent_emails
        
        service = get_authenticated_service()
        
        # Get profile to include email address
        profile = service.users().getProfile(userId='me').execute()
        email_address = profile.get('emailAddress', 'Unknown')
        
        emails = fetch_recent_emails(service, hours=24, max_results=50)
        
        unread = sum(1 for e in emails if e.get('is_unread'))
        total = len(emails)
        starred = sum(1 for e in emails if 'STARRED' in e.get('labelIds', []))
        
        return {
            'status': 'ok',
            'email_address': email_address,
            'unread_count': unread,
            'total_count': total,
            'starred_count': starred,
            'message': f'{total} emails in last 24h'
        }
    except Exception as e:
        return {
            'status': 'ok',
            'email_address': 'Unknown',
            'unread_count': 0,
            'total_count': 0,
            'starred_count': 0,
            'message': f'Gmail error: {str(e)}'
        }

# --- 5. Ollama Model Status (Mac Studio) ---
def get_ollama_status():
    try:
        import urllib.request
        import json

        # Query Ollama API directly on LAN IP (192.168.1.240:11434)
        # Get installed models via /api/tags
        req = urllib.request.Request('http://192.168.1.240:11434/api/tags', headers={'User-Agent': 'Dashboard/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        models = []
        for m in data.get('models', []):
            name = m.get('name', '')
            size_bytes = m.get('size', 0)
            size_gb = round(size_bytes / (1024**3), 1)
            modified = m.get('modified_at', '')
            # Format modified time
            if modified:
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(modified.replace('Z', '+00:00'))
                    modified = dt.strftime('%Y-%m-%d')
                except:
                    pass

            models.append({
                'name': name,
                'size': f'{size_gb} GB',
                'size_gb': size_gb,
                'modified': modified or 'N/A'
            })

        # Get running models via /api/ps
        req2 = urllib.request.Request('http://192.168.1.240:11434/api/ps', headers={'User-Agent': 'Dashboard/1.0'})
        with urllib.request.urlopen(req2, timeout=10) as resp2:
            ps_data = json.loads(resp2.read().decode())

        running_models = ps_data.get('models', [])
        running = len(running_models) > 0

        return {
            'status': 'ok',
            'ollama_running': running,
            'models_installed': len(models),
            'models': [
                {
                    'name': m['name'],
                    'size': m['size'],
                    'size_gb': m['size_gb'],
                    'modified': m['modified'],
                    'running': any(r.get('name', '') == m['name'] for r in running_models)
                }
                for m in models
            ],
            'running_models': [
                {
                    'name': m.get('name', ''),
                    'size': m.get('size', 0),
                    'size_gb': round(m.get('size', 0) / (1024**3), 1),
                }
                for m in running_models
            ]
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# --- 6. Linux Server (clawz840) System Status ---
def get_linux_server_status():
    try:
        import subprocess
        import os

        # Get CPU load
        with open('/proc/loadavg', 'r') as f:
            load = f.read().split()[:3]

        # Get memory
        with open('/proc/meminfo', 'r') as f:
            meminfo = f.read()
        mem_total = int([l for l in meminfo.split('\n') if l.startswith('MemTotal')][0].split()[1]) / 1024  # MB
        mem_avail = int([l for l in meminfo.split('\n') if l.startswith('MemAvailable')][0].split()[1]) / 1024
        mem_used_pct = round((mem_total - mem_avail) / mem_total * 100, 1)
        mem_total_gb = round(mem_total / 1024, 1)
        mem_avail_gb = round(mem_avail / 1024, 1)

        # Get CPU info
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        cpu_model = 'Unknown'
        for line in cpuinfo.split('\n'):
            if line.startswith('model name'):
                cpu_model = line.split(':')[-1].strip()
                break

        # Get disk usage for root
        disk = subprocess.check_output(['df', '-h', '/'], text=True).split('\n')[1].split()
        disk_used = disk[2]
        disk_total = disk[1]
        disk_pct = disk[4]

        # Get uptime
        with open('/proc/uptime', 'r') as f:
            uptime_sec = float(f.read().split()[0])
        uptime_days = int(uptime_sec // 86400)
        uptime_hours = int((uptime_sec % 86400) // 3600)
        uptime_str = f'{uptime_days}d {uptime_hours}h' if uptime_days else f'{uptime_hours}h'

        # Get CPU temp if available
        cpu_temp = 'N/A'
        try:
            for zone in os.listdir('/sys/class/thermal/'):
                if 'cpu' in zone.lower():
                    with open(f'/sys/class/thermal/{zone}/temp', 'r') as f:
                        cpu_temp = f'{int(f.read().strip()) / 1000}°C'
                        break
        except:
            pass

        return {
            'status': 'ok',
            'hostname': 'clawz840',
            'cpu_model': cpu_model,
            'load_1m': load[0],
            'load_5m': load[1],
            'load_15m': load[2],
            'memory_total_gb': mem_total_gb,
            'memory_used_pct': mem_used_pct,
            'memory_avail_gb': mem_avail_gb,
            'disk_used': disk_used,
            'disk_total': disk_total,
            'disk_pct': disk_pct,
            'uptime': uptime_str,
            'cpu_temp': cpu_temp,
            'ip': '100.124.71.12 (Tailscale) / 192.168.1.222 (LAN)'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

# --- 7. Mac Studio System Status ---
def get_mac_studio_status():
    try:
        import subprocess
        import json
        
        # Get hardware/software info
        result = subprocess.run(
            ['ssh', 'macstudio', 'system_profiler', 'SPHardwareDataType', 'SPMemoryDataType', 'SPSoftwareDataType', 'SPStorageDataType'],
            capture_output=True, text=True, timeout=60
        )
        
        if result.returncode != 0:
            return {'status': 'error', 'message': 'SSH to Mac Studio failed'}
        
        output = result.stdout
        
        # Parse basic info
        model = 'Mac Studio'
        chip = 'M2 Max'
        ram = '32 GB'
        os_version = 'macOS 26.5.0'
        storage = 'N/A'
        
        for line in output.split('\n'):
            if 'Model Name' in line:
                model = line.split(':')[-1].strip()
            elif 'Chip' in line:
                chip = line.split(':')[-1].strip()
            elif 'Memory' in line and 'GB' in line:
                ram = line.split(':')[-1].strip()
            elif 'System Version' in line:
                os_version = line.split(':')[-1].strip()
            elif 'Capacity' in line and ('TB' in line or 'GB' in line) and 'Available' not in line and 'File System' not in line:
                # Get the main APFS drive capacity (first one usually)
                if 'APFS' in output[max(0, output.find(line)-200):output.find(line)] or storage == 'N/A':
                    storage = line.split(':')[-1].strip()
            elif 'Available' in line and ('TB' in line or 'GB' in line):
                # This is available space, format storage nicely
                avail = line.split(':')[-1].strip()
                if storage != 'N/A':
                    storage = f"{storage} ({avail} free)"
        
        # Get load/memory/disk via SSH
        result2 = subprocess.run(
            ['ssh', 'macstudio', 'bash -c "top -l 1 -n 0 2>/dev/null | grep -E \'Load Avg|PhysMem\'; df -h / 2>/dev/null | tail -1"'],
            capture_output=True, text=True, timeout=60
        )
        
        load_1m = load_5m = load_15m = 'N/A'
        mem_total_gb = mem_used_gb = mem_free_gb = 0
        mem_used_pct = 'N/A'
        disk_used = disk_total = disk_pct = 'N/A'
        
        for line in result2.stdout.split('\n'):
            if 'Load Avg' in line:
                parts = line.split(':')[-1].strip().split(',')
                load_1m = parts[0].strip() if len(parts) > 0 else 'N/A'
                load_5m = parts[1].strip() if len(parts) > 1 else 'N/A'
                load_15m = parts[2].strip() if len(parts) > 2 else 'N/A'
            elif 'PhysMem' in line:
                # Parse: "PhysMem: 5631M used (1183M wired, 0B compressor), 26G unused."
                import re
                # Match used value with unit (M/G)
                used_match = re.search(r'(\d+)([GM]) used', line)
                # Match unused value with unit (M/G)
                unused_match = re.search(r'(\d+)([GM]) unused', line)
                
                if used_match:
                    used_val = int(used_match.group(1))
                    used_unit = used_match.group(2)
                    if used_unit == 'M':
                        mem_used_gb = round(used_val / 1024, 1)
                    else:  # G
                        mem_used_gb = float(used_val)
                
                if unused_match:
                    unused_val = int(unused_match.group(1))
                    unused_unit = unused_match.group(2)
                    if unused_unit == 'M':
                        mem_free_gb = round(unused_val / 1024, 1)
                    else:  # G
                        mem_free_gb = float(unused_val)
                
                mem_total_gb = round(mem_used_gb + mem_free_gb, 1)
                if mem_total_gb > 0:
                    mem_used_pct = round(mem_used_gb / mem_total_gb * 100, 1)
            elif line.startswith('/dev/') or line.startswith('Filesystem'):
                # df output: "/dev/disk3s1s1   460Gi    12Gi   302Gi     4%    459k  3.2G    0%   /"
                parts = line.split()
                if len(parts) >= 5:
                    disk_total = parts[1]
                    disk_used = parts[2]
                    disk_pct = parts[4]
        
        return {
            'status': 'ok',
            'hostname': 'macstudio',
            'model': model,
            'chip': chip,
            'ram': ram,
            'os': os_version,
            'storage': storage,
            'load_1m': load_1m,
            'load_5m': load_5m,
            'load_15m': load_15m,
            'memory_total_gb': mem_total_gb,
            'memory_used_gb': mem_used_gb,
            'memory_free_gb': mem_free_gb,
            'memory_used_pct': mem_used_pct,
            'disk_used': disk_used,
            'disk_total': disk_total,
            'disk_pct': disk_pct,
            'ip': '192.168.1.240 (LAN)'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# --- 7b. Mac Studio Ollama Status ---
def get_mac_studio_ollama_status():
    try:
        import subprocess
        import json
        import re
        
        # Get Ollama models (text output, no --json flag on this version)
        result = subprocess.run(
            ['ssh', 'macstudio', '/Applications/Ollama.app/Contents/Resources/ollama list'],
            capture_output=True, text=True, timeout=15
        )
        
        models = []
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 3:
                    # Parse: NAME ID SIZE MODIFIED
                    name = parts[0]
                    model_id = parts[1]
                    size_str = ' '.join(parts[2:4]) if len(parts) >= 4 else parts[2]
                    modified = ' '.join(parts[4:]) if len(parts) > 4 else 'N/A'
                    
                    # Parse size to GB
                    size_gb = 0
                    if 'GB' in size_str:
                        m = re.search(r'([\d.]+)\s*GB', size_str)
                        if m:
                            size_gb = float(m.group(1))
                    elif 'MB' in size_str:
                        m = re.search(r'([\d.]+)\s*MB', size_str)
                        if m:
                            size_gb = float(m.group(1)) / 1024
                    
                    models.append({
                        'name': name,
                        'id': model_id,
                        'size': size_str,
                        'size_gb': round(size_gb, 1),
                        'modified': modified
                    })
        
        # Also check if Ollama is running and what's loaded (use /api/ps for running models)
        # Use shell string (not list) with shell=True for proper redirection
        result2 = subprocess.run(
            'ssh macstudio "curl -s http://localhost:11434/api/ps 2>/dev/null"',
            capture_output=True, text=True, timeout=10, shell=True
        )
        
        running_models = []
        if result2.returncode == 0 and result2.stdout.strip():
            try:
                data = json.loads(result2.stdout)
                running_models = data.get('models', [])
            except:
                pass
        
        running = len(running_models) > 0
        
        return {
            'status': 'ok',
            'ollama_running': running,
            'models_installed': len(models),
            'models': [
                {
                    'name': m['name'],
                    'size': m['size'],
                    'size_gb': m['size_gb'],
                    'modified': m['modified'],
                    'running': any(r.get('name', '') == m['name'] for r in running_models)
                }
                for m in models
            ],
            'running_models': [
                {
                    'name': m.get('name', ''),
                    'size': m.get('size', 0),
                    'size_gb': round(m.get('size', 0) / (1024**3), 1),
                }
                for m in running_models
            ]
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# --- 7c. LLM Call Metrics (from Ollama GIN access logs on the Mac) ---
def get_ollama_call_metrics():
    """Count real LLM inference calls from the Mac Studio Ollama server log.

    Ollama writes GIN-formatted access log lines for every request, e.g.
        [GIN] 2026/08/20 - 15:03:12 | 200 | 1m45s | 192.168.1.222 | POST "/api/chat"
        [GIN] 2026/08/20 - 09:00:17 | 200 | 13s  | 100.124.71.12  | POST "/v1/chat/completions"
    We count only POST requests to the inference endpoints (chat/completions,
    /v1/completions, /api/chat, /api/generate) as actual LLM calls. This is the
    real usage source that replaced the abandoned llm_call_log.txt stub, which
    was only appended by a dead-end proxy and had stopped recording months ago.
    Timestamps are Ollama server-local time (= America/New_York, same as this
    host), so direct comparison with the local clock is valid.
    """
    try:
        import subprocess
        import re
        LOGS = "/tmp/ollama-serve.log /tmp/ollama.log /tmp/ollama.error.log"
        cmd = ('ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -o BatchMode=yes '
               f"macstudio 'cat {LOGS} 2>/dev/null'")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=25)

        call_re = re.compile(r'(chat/completions|/v1/completions|/api/chat|/api/generate)')
        gts_re = re.compile(r'^\[GIN\]\s+([0-9]{4}/[0-9]{2}/[0-9]{2} - [0-9]{2}:[0-9]{2}:[0-9]{2})')
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        d30 = now - timedelta(days=30)
        d1 = now - timedelta(hours=24)

        calls = []
        seen = set()
        for line in result.stdout.splitlines():
            if ' POST ' not in line:
                continue
            m = call_re.search(line)
            if not m:
                continue
            gm = gts_re.match(line)
            if not gm:
                continue
            try:
                ts = datetime.strptime(gm.group(1), '%Y/%m/%d - %H:%M:%S')
            except ValueError:
                continue
            # Dedup: the same request can appear in both ollama.log and ollama-serve.log
            key = (ts, m.group(1))
            if key in seen:
                continue
            seen.add(key)
            calls.append(ts)

        total = len(calls)
        today_calls = sum(1 for t in calls if t >= today_start)
        recent_30 = [t for t in calls if t >= d30]
        recent_24 = [t for t in calls if t >= d1]
        avg_30_day = len(recent_30) / 30.0
        hourly_rate = len(recent_24) / 24.0
        calls_today = [t.strftime('%H:%M') for t in calls if t >= today_start]

        return {
            'status': 'ok',
            'source': 'ollama-gin-log',
            'total_calls': total,
            'today_calls': today_calls,
            'share_of_total': round((today_calls / total * 100), 1) if total else 0,
            'avg_30_day': round(avg_30_day, 1),
            'hourly_rate': round(hourly_rate, 2),
            'calls_today': calls_today,
            'newest_call': max(calls).strftime('%Y-%m-%d %H:%M') if calls else None,
        }
    except Exception as e:
        return {'status': 'error', 'source': 'ollama-gin-log', 'message': str(e)}


# --- 8. Camera Snapshots ---
def get_camera_snapshots():
    # Return camera metadata - browser will attempt to load snapshots directly
    # Only works when accessing dashboard from LAN (not via Tailscale only)
    return {
        'status': 'ok',
        'cameras': [
            {
                'status': 'ok',
                'id': 'flir_158',
                'name': 'Gun Room (158)',
                'ip': '192.168.1.158',
                'snapshot_url': 'http://192.168.1.158/cgi-bin/snapshot.cgi?chn=0'
            },
            {
                'status': 'ok',
                'id': 'flir_163',
                'name': 'Office (163)',
                'ip': '192.168.1.163',
                'snapshot_url': 'http://192.168.1.163/cgi-bin/snapshot.cgi?chn=0'
            }
        ]
    }


# --- 9. TrueNAS Server Status ---
def get_truenas_status():
    """Fetch TrueNAS system info, pool status, alerts, and running apps."""
    try:
        import urllib.request
        import json
        import ssl
        
        api_key = os.environ.get('TRUENAS_API_KEY', '')
        truenas_host = os.environ.get('TRUENAS_HOST', '192.168.1.68')
        
        if not api_key:
            return {'status': 'error', 'message': 'TRUENAS_API_KEY not set'}
        
        # Disable SSL verification for self-signed certs
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Accept': 'application/json',
        }
        
        base_url = f'https://{truenas_host}/api/v2.0'
        
        def fetch_json(endpoint):
            url = f'{base_url}{endpoint}'
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, context=ssl_context, timeout=10) as response:
                return json.loads(response.read().decode('utf-8'))
        
        # Fetch all data in parallel-ish (sequential but fast)
        system_info = fetch_json('/system/info')
        pools = fetch_json('/pool')
        alerts = fetch_json('/alert/list')
        apps = fetch_json('/app')
        
        # Parse pools - extract key metrics
        pool_summary = []
        for pool in pools:
            pool_summary.append({
                'name': pool.get('name'),
                'status': pool.get('status'),
                'healthy': pool.get('healthy', False),
                'size_tb': round(pool.get('size', 0) / (1024**4), 2),
                'allocated_tb': round(pool.get('allocated', 0) / (1024**4), 2),
                'free_tb': round(pool.get('free', 0) / (1024**4), 2),
                'pct_used': round((pool.get('allocated', 0) / pool.get('size', 1)) * 100, 1) if pool.get('size', 0) > 0 else 0,
                'fragmentation': pool.get('fragmentation', '0'),
            })
        
        # Parse alerts - count by level
        alert_counts = {'CRITICAL': 0, 'WARNING': 0, 'INFO': 0}
        active_alerts = []
        for alert in alerts:
            level = alert.get('level', 'INFO')
            if level in alert_counts:
                alert_counts[level] += 1
            if not alert.get('dismissed', False):
                active_alerts.append({
                    'level': level,
                    'text': alert.get('formatted', alert.get('text', '')),
                })
        
        # Parse apps - running count and key apps
        running_apps = [a for a in apps if a.get('state') == 'RUNNING']
        key_apps = ['immich', 'jellyfin', 'tailscale', 'actual-budget']
        app_status = []
        for app in apps:
            if app.get('name') in key_apps:
                portals = app.get('portals', {})
                web_url = list(portals.values())[0] if portals else None
                app_status.append({
                    'name': app.get('name'),
                    'state': app.get('state'),
                    'version': app.get('human_version', app.get('version')),
                    'url': web_url,
                })
        
        # Memory calculation
        mem_total_gb = round(system_info.get('physmem', 0) / (1024**3), 1)
        
        return {
            'status': 'ok',
            'hostname': system_info.get('hostname'),
            'version': system_info.get('version'),
            'uptime': system_info.get('uptime'),
            'uptime_seconds': system_info.get('uptime_seconds'),
            'cpu_model': system_info.get('model'),
            'cpu_cores': system_info.get('cores'),
            'cpu_physical_cores': system_info.get('physical_cores'),
            'load_avg': system_info.get('loadavg', [0, 0, 0]),
            'memory_total_gb': mem_total_gb,
            'pools': pool_summary,
            'alerts': alert_counts,
            'active_alerts': active_alerts[:5],  # top 5
            'apps_running': len(running_apps),
            'apps_total': len(apps),
            'key_apps': app_status,
        }
    except urllib.error.HTTPError as e:
        return {'status': 'error', 'message': f'HTTP {e.code}: {e.read().decode()}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# --- 10. Stock Watcher ---
import yfinance as yf
import time

_stock_cache = {}
_stock_cache_time = {}

def get_stocks():
    symbols = ['AAPL', 'TSLA', 'NVDA', 'SPY']
    current_time = time.time()
    
    # Check if cached data is still valid (5 min cache)
    if all(symbol in _stock_cache and 
           current_time - _stock_cache_time.get(symbol, 0) < 300
           for symbol in symbols):
        return _stock_cache

    stock_data = {}
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if len(hist) >= 2:
                current_price = hist['Close'].iloc[-1]
                previous_price = hist['Close'].iloc[-2]
                change = ((current_price - previous_price) / previous_price) * 100
                change_percent = f"{change:.2f}%"
            else:
                current_price = info.get('currentPrice', 'N/A')
                change_percent = 'N/A'
                
            stock_data[symbol] = {
                'price': round(current_price, 2) if current_price != 'N/A' else 'N/A',
                'change_percent': change_percent
            }
        except Exception:
            stock_data[symbol] = {'price': 'N/A', 'change_percent': 'N/A'}
    
    # Cache the results
    for symbol in symbols:
        _stock_cache[symbol] = stock_data[symbol]
        _stock_cache_time[symbol] = current_time
    
    return stock_data


# --- 11. OpenRouter Usage ---
# --- 11. OpenRouter Usage ---
def get_openrouter_usage():
    try:
        import urllib.request
        import json
        api_key = os.environ.get('OPENROUTER_API_KEY', '')
        if not api_key:
            return {'status': 'error', 'message': 'OPENROUTER_API_KEY not set'}
        
        # OpenRouter models endpoint - returns model list and usage info
        url = 'https://openrouter.ai/api/v1/models'
        
        req = urllib.request.Request(
            url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'User-Agent': 'Mozilla/5.0',
                'Accept': 'application/json',
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Extract usage and pricing info from models response
        metadata = data.get('metadata', {})
        model_count = len(data.get('data', []))
        total_count = metadata.get('total_count', 0)
        
        # Try to get usage from first model's pricing
        pricing_info = {}
        if data.get('data'):
            first_model = data['data'][0]
            pricing = first_model.get('pricing', {})
            if pricing:
                pricing_info = {
                    'prompt_price_per_1k': pricing.get('prompt', 0),
                    'completion_price_per_1k': pricing.get('completion', 0),
                }
        
        return {
            'status': 'ok',
            'model_count': model_count,
            'total_models': total_count,
            'pricing': pricing_info,
            'api_status': 'connected',
        }
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')[:200]
        return {'status': 'error', 'message': f'HTTP Error {e.code}: {body}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
