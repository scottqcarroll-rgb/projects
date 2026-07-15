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
"""
from flask import Flask, render_template, jsonify, request, Response
import pytz
from datetime import datetime, timedelta
from data_fetcher import (
    get_drive_report, get_pm_drive_report, get_weather, get_sam_hunter,
    get_gmail_summary, get_ollama_status, get_linux_server_status,
    get_mac_studio_status, get_camera_snapshots, get_openrouter_usage,
    get_mac_studio_ollama_status
)
import os
import json
import subprocess

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
        'sam_url': 'http://100.124.71.12:5002',
        'sam_name': 'Sam Hunter'
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

import requests

OLLAMA_BASE_URL = os.environ.get('OLLAMA_BASE_URL', 'http://192.168.1.174:11434')

@app.route('/api/ollama-chat', methods=['POST'])
def api_ollama_chat():
    """Proxy chat requests to Mac Studio Ollama API."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        model = data.get('model', 'hermes-4-14b')
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        
        # Forward to Ollama API
        resp = requests.post(
            f'{OLLAMA_BASE_URL}/api/chat',
            json={'model': model, 'messages': messages, 'stream': stream},
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
            return jsonify(resp.json())
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot connect to Ollama at ' + OLLAMA_BASE_URL}), 503
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Ollama request timed out'}), 504
    except Exception as e:
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
    """API endpoint for LLM call metrics - reads from log files."""
    try:
        log_file = '/home/scott/projects/llm_call_log.txt'
        if not os.path.exists(log_file):
            return jsonify({
                'status': 'ok',
                'total_calls': 0,
                'today_calls': 0,
                'share_of_total': 0,
                'avg_30_day': 0,
                'hourly_rate': 0,
                'calls_today': []
            })
        with open(log_file, 'r') as f:
            lines = f.readlines()
        calls = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            try:
                timestamp_str = line.split(']')[0][1:]
                timestamp = datetime.fromisoformat(timestamp_str)
                calls.append(timestamp)
            except (ValueError, IndexError):
                continue
        total_calls = len(calls)
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_calls = sum(1 for c in calls if c >= today_start)
        calls_today = [c.strftime('%H:%M') for c in calls if c >= today_start]
        thirty_days_ago = now - timedelta(days=30)
        recent_calls = [c for c in calls if c >= thirty_days_ago]
        avg_30_day = len(recent_calls) / 30 if recent_calls else 0
        one_day_ago = now - timedelta(hours=24)
        recent_24h = [c for c in calls if c >= one_day_ago]
        hourly_rate = len(recent_24h) / 24 if recent_24h else 0
        share_of_total = round((today_calls / total_calls * 100), 1) if total_calls > 0 else 0
        return jsonify({
            'status': 'ok',
            'total_calls': total_calls,
            'today_calls': today_calls,
            'share_of_total': share_of_total,
            'avg_30_day': round(avg_30_day, 1),
            'hourly_rate': round(hourly_rate, 2),
            'calls_today': calls_today
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)