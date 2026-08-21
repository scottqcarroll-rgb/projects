#!/usr/bin/env python3
"""Dashboard web interface with LLM metrics support.

This Flask app provides a real-time dashboard showing:
- Drive reports (AM/PM)
- Weather status
- System health (Linux server, Mac Studio)
- LLM call metrics and usage data
- Camera status and snapshots
- OpenRoute usage statistics
- Quick links to related services
- TrueNAS server monitoring
"""
from flask import Flask, render_template, jsonify, request, Response
import pytz
from datetime import datetime, timedelta
from data_fetcher import (
    get_drive_report, get_pm_drive_report, get_weather, get_sam_hunter,
    get_gmail_summary, get_ollama_status, get_linux_server_status,
    get_mac_studio_status, get_camera_snapshots, get_openrouter_usage,
    get_mac_studio_ollama_status, get_truenas_status, get_stocks,
    get_ollama_call_metrics
)
import os
import json
import subprocess

# Load .env file for environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, will rely on system env vars

app = Flask(__name__)

@app.after_request
def add_cache_control(response):
    """Add cache control headers to prevent iPad Safari aggressive caching"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/drive')
def api_drive():
    return jsonify(get_drive_report())

@app.route('/api/weather')
def api_weather():
    return jsonify(get_weather())

@app.route('/api/links')
def api_links():
    return jsonify({
        'status': 'ok',
        'links': [
            {'name': 'Email Summary', 'url': 'http://100.124.71.12:5050/daily_summary.html'},
            {'name': 'Sam Hunter', 'url': 'http://100.124.71.12:5002'},
            {'name': 'Documenso', 'url': 'http://100.124.71.12:3000'},
            {'name': 'Coolify', 'url': 'http://100.124.71.12:8080'},
            {'name': 'AppFlowy', 'url': 'http://100.124.71.12:3001'},
            {'name': 'TrueNAS', 'url': 'http://192.168.1.68'},
            {'name': 'Immich', 'url': 'http://100.124.71.12:2283'},
            {'name': 'Jellyfin', 'url': 'http://100.79.220.32:30013'},
            {'name': 'Actual Budget', 'url': 'http://100.79.220.32:31012'},
            {'name': 'Gateway Logs', 'url': 'http://100.124.71.12:5001/api/gateway-logs?limit=50'},
            {'name': 'Gateway Errors', 'url': 'http://100.124.71.12:5001/api/gateway-errors?limit=20'},
        ]
    })

@app.route('/api/pm-drive')
def api_pm_drive():
    return jsonify(get_pm_drive_report())

@app.route('/api/samhunter')
def api_samhunter():
    return jsonify(get_sam_hunter())

@app.route('/api/gmail')
def api_gmail():
    return jsonify(get_gmail_summary())

@app.route('/api/ollama')
def api_ollama():
    return jsonify(get_ollama_status())

@app.route('/api/linux-server')
def api_linux_server():
    return jsonify(get_linux_server_status())

@app.route('/api/mac-studio')
def api_mac_studio():
    return jsonify(get_mac_studio_status())


@app.route('/api/mac-studio/ollama')
def api_mac_studio_ollama():
    return jsonify(get_mac_studio_ollama_status())


@app.route('/api/cameras')
def api_cameras():
    return jsonify(get_camera_snapshots())

@app.route('/api/camera-image')
def api_camera_image():
    url = request.args.get('url')
    if not url:
        return Response('Missing url parameter', status=400)
    try:
        import requests as req
        r = req.get(url, timeout=10)
        return Response(r.content, mimetype=r.headers.get('Content-Type', 'image/jpeg'))
    except Exception as e:
        return Response(f'Failed to fetch image: {str(e)}', status=500)

@app.route('/api/server-time')
def api_server_time():
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)
    return jsonify({
        'status': 'ok',
        'datetime': now.strftime('%A, %B %d • %I:%M %p'),
        'timestamp': now.isoformat()
    })

@app.route('/api/usage')
def api_usage():
    return jsonify(get_openrouter_usage())


@app.route('/api/truenas')
def api_truenas():
    return jsonify(get_truenas_status())


@app.route('/api/stocks')
def api_stocks():
    return jsonify(get_stocks())


import requests
OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://100.75.240.39:11434')
DEFAULT_OLLAMA_MODEL = 'hermes-4-14b:latest'

@app.route('/api/ollama-chat', methods=['POST'])
def api_ollama_chat():
    """Proxy chat requests to Mac Studio Ollama API."""
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        model = data.get('model', DEFAULT_OLLAMA_MODEL)
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        tools = data.get('tools', None)
        
        # Forward to Ollama API
        payload = {'model': model, 'messages': messages, 'stream': stream}
        if tools is not None:
            payload['tools'] = tools
        
        resp = requests.post(
            f'{OLLAMA_BASE_URL}/api/chat',
            json=payload,
            timeout=120,
            stream=stream
        )
        
        if stream:
            def generate():
                for line in resp.iter_lines():
                    if line:
                        yield line.decode('utf-8') + '\n'
            return Response(generate(), mimetype='application/x-ndjson')
        else:
            result = resp.json()
            # Log the call for metrics
            try:
                log_file = '/home/scott/projects/llm_call_log.txt'
                with open(log_file, 'a') as f:
                    f.write(f'[{datetime.now().isoformat()}] ollama-chat model={model} status=ok\n')
            except Exception as log_err:
                print(f"Failed to log LLM call: {log_err}")
            return jsonify(result)
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to Ollama at ' + OLLAMA_BASE_URL}), 503
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Ollama request timed out'}), 504
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/ollama-models')
def api_ollama_models():
    """Get available models from Ollama."""
    try:
        resp = requests.get(f'{OLLAMA_BASE_URL}/api/tags', timeout=10)
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/llm-metrics')
def api_llm_metrics():
    return jsonify(get_ollama_call_metrics())


@app.route('/api/gateway-logs')
def api_gateway_logs():
    """API endpoint for recent gateway logs."""
    try:
        log_file = '/home/scott/.hermes/logs/gateway.log'
        limit = int(request.args.get('limit', 100))
        level = request.args.get('level')  # DEBUG, INFO, WARNING, ERROR
        search = request.args.get('search')
        
        if not os.path.exists(log_file):
            return jsonify({'status': 'ok', 'logs': [], 'total_lines': 0})
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        # Filter from end (most recent first)
        filtered = []
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            if level and level.upper() not in line:
                continue
            if search and search.lower() not in line.lower():
                continue
            filtered.append(line)
            if len(filtered) >= limit:
                break
        
        return jsonify({
            'status': 'ok',
            'logs': filtered,
            'total_lines': len(lines),
            'returned': len(filtered)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/api/gateway-errors')
def api_gateway_errors():
    """API endpoint for gateway errors only."""
    try:
        log_file = '/home/scott/.hermes/logs/errors.log'
        limit = int(request.args.get('limit', 50))
        
        if not os.path.exists(log_file):
            return jsonify({'status': 'ok', 'errors': [], 'total_lines': 0})
        
        with open(log_file, 'r') as f:
            lines = f.readlines()
        
        errors = [line.strip() for line in reversed(lines) if line.strip()][:limit]
        
        return jsonify({
            'status': 'ok',
            'errors': errors,
            'total_lines': len(lines),
            'returned': len(errors)
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)