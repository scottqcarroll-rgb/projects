#!/usr/bin/env python3
from flask import Flask, render_template, jsonify
from data_fetcher import get_drive_report, get_pm_drive_report, get_weather, get_sam_hunter, get_gmail_summary, get_gemma_status, get_linux_server_status, get_mac_studio_status, get_camera_snapshots
import pytz
from datetime import datetime

app = Flask(__name__)

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

@app.route('/api/gemma')
def api_gemma():
    return jsonify(get_gemma_status())

@app.route('/api/linux-server')
def api_linux_server():
    return jsonify(get_linux_server_status())

@app.route('/api/mac-studio')
def api_mac_studio():
    return jsonify(get_mac_studio_status())

@app.route('/api/cameras')
def api_cameras():
    return jsonify(get_camera_snapshots())

@app.route('/api/camera-image')
def api_camera_image():
    from flask import request, Response
    import requests as req
    url = request.args.get('url')
    if not url:
        return Response('Missing url parameter', status=400)
    try:
        r = req.get(url, timeout=10)
        return Response(r.content, mimetype=r.headers.get('Content-Type', 'image/jpeg'))
    except Exception as e:
        return Response(f'Failed to fetch image: {str(e)}', status=500)

@app.route('/api/server-time')
def api_server_time():
    # Get current time in Atlanta/Eastern timezone with 12-hour a.m./p.m. format
    eastern = pytz.timezone('America/New_York')
    now = datetime.now(eastern)
    return jsonify({
        'status': 'ok',
        'datetime': now.strftime('%A, %B %d • %I:%M %p'),
        'timestamp': now.isoformat()
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=False)