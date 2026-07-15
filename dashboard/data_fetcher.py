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
    raw = open(files[0]).read()
    idx = raw.find('API_KEY="') + 9
    rest = raw[idx:]
    return rest.split('"')[0]

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
        # Use fixed PM departure time (5:00 PM) instead of current time
        departure_time = '5:00 PM'
        departure_dt = datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
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
        lat, lon = 33.7353, -85.0308
        url = f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code&timezone=America%2FNew_York&forecast_days=1'
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

        return {
            'status': 'ok',
            'temperature': c_to_f(temp_c),
            'condition': wmo.get(code, f'Unknown ({code})'),
            'humidity': current.get('relative_humidity_2m', 'N/A'),
            'wind_speed': round(current.get('wind_speed_10m', 0) * 2.237, 1) if current.get('wind_speed_10m') else 'N/A',  # m/s to mph
            'feels_like': c_to_f(feels_c),
            'high': c_to_f(high_c),
            'low': c_to_f(low_c),
            'precip': daily.get('precipitation_sum', ['N/A'])[0]
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_sam_hunter():
    return {
        'status': 'ok',
        'url': 'http://100.124.71.12:5002',
        'name': 'Sam Hunter'
    }

# --- 4. Gmail Summary (placeholder for now) ---
def get_gmail_summary():
    return {
        'status': 'ok',
        'unread_count': 0,
        'message': 'Gmail integration pending'
    }

# --- 5. Ollama Model Status (Mac Studio) ---
def get_ollama_status():
    try:
        import urllib.request
        import json
        # Check Mac Studio Ollama API (port 11434) - more reliable than dynamic llama.cpp port
        url = 'http://192.168.1.174:11434/api/ps'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        models = data.get('models', [])
        if models:
            model = models[0]
            details = model.get('details', {})
            n_params = model.get('size', 0)  # Ollama returns size in bytes
            n_ctx = model.get('context_length', 0)
            size_gb = round(n_params / (1024**3), 1) if n_params else 'N/A'
            
            # Determine model name from details
            family = details.get('family', '')
            param_size = details.get('parameter_size', '')
            model_name = model.get('name', 'Unknown')
            
            if 'hermes' in model_name.lower():
                model_name = 'Hermes 4 14B'
            elif 'gemma' in model_name.lower():
                model_name = 'Gemma'
            elif 'qwen' in family.lower():
                model_name = f'Qwen {param_size}' if param_size else 'Qwen'
            
            return {
                'status': 'ok',
                'model': model_name,
                'params': param_size if param_size else f'{n_params/1e9:.1f}B',
                'context': f'{n_ctx//1000}K',
                'size_gb': size_gb,
                'host': 'Mac Studio (192.168.1.174:11434)'
            }
        return {'status': 'error', 'message': 'No model loaded'}
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
            capture_output=True, text=True, timeout=15
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
            capture_output=True, text=True, timeout=15
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
                # Parse: "PhysMem: 31G used (1606M wired, 2136M compressor), 452M unused."
                import re
                used_match = re.search(r'(\d+)[GM]i? used', line)
                unused_match = re.search(r'(\d+)M unused', line)
                if used_match:
                    mem_used_gb = int(used_match.group(1))
                if unused_match:
                    mem_free_gb = round(int(unused_match.group(1)) / 1024, 1)
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
            'ip': '192.168.1.174 (LAN)'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# --- 7b. Mac Studio Ollama Status ---
def get_mac_studio_ollama_status():
    try:
        import subprocess
        import json
        
        # Get Ollama models and running status
        result = subprocess.run(
            ['ssh', 'macstudio', '/Applications/Ollama.app/Contents/Resources/ollama list'],
            capture_output=True, text=True, timeout=10
        )
        
        models = []
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            for line in lines[1:]:  # Skip header
                parts = line.split()
                if len(parts) >= 3:
                    models.append({
                        'name': parts[0],
                        'id': parts[1],
                        'size': ' '.join(parts[2:4]) if len(parts) >= 4 else parts[2],
                        'modified': ' '.join(parts[4:]) if len(parts) > 4 else 'N/A'
                    })
        
        # Check if Ollama is running and what's loaded
        result2 = subprocess.run(
            ['ssh', 'macstudio', 'curl -s http://localhost:11434/api/ps 2>/dev/null'],
            capture_output=True, text=True, timeout=10, shell=True
        )
        
        running_models = []
        if result2.returncode == 0:
            try:
                data = json.loads(result2.stdout)
                running_models = data.get('models', [])
            except:
                pass
        
        return {
            'status': 'ok',
            'models': models,
            'running_models': running_models,
            'ollama_running': len(running_models) > 0 or len(models) > 0
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


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
                'url': 'http://192.168.1.158/cgi-bin/snapshot.cgi?chn=0'
            },
            {
                'status': 'ok',
                'id': 'flir_163',
                'name': 'Office (163)',
                'ip': '192.168.1.163',
                'url': 'http://192.168.1.163/cgi-bin/snapshot.cgi?chn=0'
            }
        ]
    }


# --- 9. OpenRouter Usage ---
def get_openrouter_usage():
    try:
        import urllib.request
        import json
        api_key = os.environ.get('OPENROUTER_API_KEY', '')
        if not api_key:
            return {'status': 'error', 'message': 'OPENROUTER_API_KEY not set'}
        
        # OpenRouter key endpoint - returns usage and rate limit info
        url = 'https://openrouter.ai/api/v1/key'
        
        req = urllib.request.Request(
            url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'User-Agent': 'Mozilla/5.0'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Extract usage metrics from key data
        key_data = data.get('data', {})
        if key_data:
            usage = key_data.get('usage', 0)
            usage_daily = key_data.get('usage_daily', 0)
            usage_weekly = key_data.get('usage_weekly', 0)
            usage_monthly = key_data.get('usage_monthly', 0)
            limit = key_data.get('limit')
            limit_remaining = key_data.get('limit_remaining')
            is_free_tier = key_data.get('is_free_tier', True)
            
            return {
                'status': 'ok',
                'usage_total': usage,
                'usage_daily': usage_daily,
                'usage_weekly': usage_weekly,
                'usage_monthly': usage_monthly,
                'limit': limit,
                'limit_remaining': limit_remaining,
                'is_free_tier': is_free_tier,
                'label': key_data.get('label', 'N/A')
            }
        return {'status': 'error', 'message': 'No key data returned'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


# --- 10. Mac Studio Ollama Status ---
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
        
        # Also check if Ollama is running and what's loaded
        result2 = subprocess.run(
            ['ssh', 'macstudio', 'curl -s http://localhost:11434/api/tags 2>/dev/null || echo "not running"'],
            capture_output=True, text=True, timeout=10, shell=True
        )
        
        running = result2.stdout.strip() != 'not running'
        running_models = []
        if running:
            try:
                data = json.loads(result2.stdout)
                running_models = data.get('models', [])
            except:
                pass
        
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


# --- 9. OpenRouter Usage ---
def get_openrouter_usage():
    try:
        import urllib.request
        import json
        api_key = os.environ.get('OPENROUTER_API_KEY', '')
        if not api_key:
            return {'status': 'error', 'message': 'OPENROUTER_API_KEY not set'}
        
        # OpenRouter key endpoint - returns usage and rate limit info
        url = 'https://openrouter.ai/api/v1/key'
        
        req = urllib.request.Request(
            url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'User-Agent': 'Mozilla/5.0'
            }
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        
        # Extract usage metrics from key data
        key_data = data.get('data', {})
        if key_data:
            usage = key_data.get('usage', 0)
            usage_daily = key_data.get('usage_daily', 0)
            usage_weekly = key_data.get('usage_weekly', 0)
            usage_monthly = key_data.get('usage_monthly', 0)
            limit = key_data.get('limit')
            limit_remaining = key_data.get('limit_remaining')
            is_free_tier = key_data.get('is_free_tier', True)
            
            return {
                'status': 'ok',
                'usage_total': usage,
                'usage_daily': usage_daily,
                'usage_weekly': usage_weekly,
                'usage_monthly': usage_monthly,
                'limit': limit,
                'limit_remaining': limit_remaining,
                'is_free_tier': is_free_tier,
                'label': key_data.get('label', 'N/A')
            }
        else:
            return {'status': 'error', 'message': 'No key data available'}
    except urllib.error.HTTPError as e:
        return {'status': 'error', 'message': f'HTTP {e.code}: {e.reason}'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


if __name__ == '__main__':
    print("Weather:", json.dumps(get_weather(), indent=2))
    print("Sam Hunter:", json.dumps(get_sam_hunter(), indent=2))
    print("Gmail:", json.dumps(get_gmail_summary(), indent=2))
    print("Ollama:", json.dumps(get_ollama_status(), indent=2))
    print("Linux Server:", json.dumps(get_linux_server_status(), indent=2))
    print("Mac Studio:", json.dumps(get_mac_studio_status(), indent=2))
    print("OpenRouter:", json.dumps(get_openrouter_usage(), indent=2))