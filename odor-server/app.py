#!/usr/bin/env python3
"""
Odor Server — Environmental/Odor Monitoring Dashboard
Port 5003
"""
from flask import Flask, render_template, jsonify
from flask_cors import CORS
import random
from datetime import datetime

app = Flask(__name__)
CORS(app, origins=["http://127.0.0.1:5001", "http://100.124.71.12:5001", "http://192.168.1.222:5001"])  # Allow cross-origin requests from dashboard

# Simulated sensor data
SENSORS = {
    "sensor_1": {"name": "Gun Room", "location": "192.168.1.158", "type": "VOC/NH3"},
    "sensor_2": {"name": "Office", "location": "192.168.1.163", "type": "VOC/H2S"},
    "sensor_3": {"name": "Garage", "location": "192.168.1.160", "type": "VOC/CH4"},
    "sensor_4": {"name": "HVAC Return", "location": "192.168.1.161", "type": "VOC/CO2"},
}

def generate_reading(sensor_type):
    """Generate simulated sensor readings based on type"""
    base = {"VOC": random.uniform(0.05, 2.5), "NH3": random.uniform(0, 50), 
            "H2S": random.uniform(0, 10), "CH4": random.uniform(0, 100), "CO2": random.uniform(400, 2000)}
    return {k: round(v, 2) for k, v in base.items() if k in sensor_type}

@app.route('/')
def index():
    return render_template('index.html', sensors=SENSORS)

@app.route('/api/sensors')
def api_sensors():
    data = {}
    for sid, info in SENSORS.items():
        data[sid] = {
            "name": info["name"],
            "location": info["location"],
            "type": info["type"],
            "readings": generate_reading(info["type"]),
            "status": "online" if random.random() > 0.1 else "offline",
            "timestamp": datetime.now().isoformat()
        }
    return jsonify({"status": "ok", "sensors": data, "updated": datetime.now().isoformat()})

@app.route('/api/health')
def api_health():
    return jsonify({"status": "ok", "service": "    return jsonify({"status": "ok", "service": "odoo", "port": 5003, "time": datetime.now().isoformat()})", "port": 5003, "time": datetime.now().isoformat()})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=False)