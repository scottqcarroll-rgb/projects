#!/usr/bin/env python3
"""
Local Flask API server for email dashboard operations.
Runs on localhost:5050 and handles delete requests from the dashboard.
Auto-shuts down after 2 hours of operation.
"""

import threading
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import gmail_client
import yahoo_client

app = Flask(__name__)
CORS(app)

# Global references to services
gmail_service = None
shutdown_timer = None
SHUTDOWN_SECONDS = 7200  # 2 hours


def schedule_shutdown():
    """Schedule server shutdown after SHUTDOWN_SECONDS."""
    global shutdown_timer
    def shutdown():
        import os
        os._exit(0)
    shutdown_timer = threading.Timer(SHUTDOWN_SECONDS, shutdown)


@app.route('/status', methods=['GET'])
def status():
    """Health check endpoint."""
    return jsonify({'alive': True}), 200


@app.route('/delete', methods=['POST'])
def delete_email():
    """Delete an email from Gmail or Yahoo."""
    try:
        data = request.get_json()
        email_id = data.get('id')
        source = data.get('source')

        if not email_id or not source:
            return jsonify({'error': 'Missing id or source'}), 400

        if source == 'Gmail':
            if not gmail_service:
                return jsonify({'error': 'Gmail service not available'}), 500
            gmail_client.delete_email(gmail_service, email_id)
            return jsonify({'success': True, 'message': f'Email deleted from Gmail'}), 200

        elif source == 'Yahoo':
            try:
                conn = yahoo_client.get_authenticated_service()
                yahoo_client.delete_email(conn, email_id.encode() if isinstance(email_id, str) else email_id)
                conn.close()
                return jsonify({'success': True, 'message': f'Email deleted from Yahoo'}), 200
            except Exception as e:
                return jsonify({'error': f'Yahoo delete failed: {str(e)}'}), 500

        else:
            return jsonify({'error': f'Unknown email source: {source}'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def start_server(gmail_svc=None):
    """Start the Flask server in a background thread."""
    global gmail_service
    gmail_service = gmail_svc

    # Schedule shutdown timer
    schedule_shutdown()

    # Run server in background thread
    thread = threading.Thread(target=lambda: app.run(host='localhost', port=5050, debug=False, use_reloader=False))
    thread.daemon = True
    thread.start()

    print("[*] Email API server started on http://localhost:5050")
    return thread


if __name__ == '__main__':
    app.run(host='localhost', port=5050, debug=False)
