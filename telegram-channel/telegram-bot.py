#!/usr/bin/env python3
"""
Telegram bot for Claude — replaces defunct --dangerously-load-development-channels.
Uses long polling (free) + Anthropic API with bash tool for full server access.
"""

import os
import subprocess
import requests
import anthropic
from datetime import datetime

def _load_env(path):
    vals = {}
    try:
        with open(os.path.expanduser(path)) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    vals[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return vals


def _load_bot_token():
    import json
    try:
        with open(os.path.expanduser("~/.mcp.json")) as f:
            d = json.load(f)
        return d["mcpServers"]["telegram"]["env"]["TELEGRAM_BOT_TOKEN"]
    except Exception:
        return ""


_email_env = _load_env("~/projects/email-agent/.env")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN") or _load_bot_token()
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY") or _email_env.get("ANTHROPIC_API_KEY", "")
ALLOWED_USERS = {7542619200}
BASE_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are Claude, running on Scott's Linux server (clawz840) via Telegram.

Scott Carroll is a 30-year IT/maintenance professional. His active projects:
- Government contracts under Brisar Investments LLC (GA) — bidding USDA/federal work as prime
- AI Assessment Agency — voice bot audits using Retell AI + Claude
- Email agent — automated Gmail monitoring with Telegram alerts
- Various Claude Code skills and automation tools

You have a bash tool to run commands on the server. Use it freely to help Scott with tasks.
Default working directory: /home/scott/projects

Keep responses concise — this is a mobile chat interface.
Use /clear to reset conversation history."""

TOOLS = [
    {
        "name": "bash",
        "description": "Run a bash command on clawz840 (Scott's Linux server). Use for file ops, git, logs, scripts, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to run"}
            },
            "required": ["command"]
        }
    }
]

conversations = {}


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_bash(command):
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            timeout=60, cwd="/home/scott/projects",
            env={**os.environ, "PATH": f"/home/scott/.bun/bin:/home/scott/.local/bin:{os.environ.get('PATH', '')}"}
        )
        output = (result.stdout + result.stderr).strip()
        return output[:4000] if output else "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out after 60 seconds"
    except Exception as e:
        return f"Error: {e}"


def send_message(chat_id, text):
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]
        try:
            resp = requests.post(f"{BASE_URL}/sendMessage", json={
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "Markdown"
            }, timeout=10)
            if not resp.json().get("ok"):
                # Retry without markdown if parse fails
                requests.post(f"{BASE_URL}/sendMessage", json={
                    "chat_id": chat_id,
                    "text": chunk
                }, timeout=10)
        except Exception as e:
            log(f"send_message error: {e}")


def send_typing(chat_id):
    try:
        requests.post(f"{BASE_URL}/sendChatAction", json={
            "chat_id": chat_id, "action": "typing"
        }, timeout=5)
    except Exception:
        pass


def process_message(chat_id, user_id, text):
    if user_id not in ALLOWED_USERS:
        send_message(chat_id, "Unauthorized.")
        return

    if text.strip().lower() in ("/clear", "/reset"):
        conversations.pop(chat_id, None)
        send_message(chat_id, "Conversation cleared.")
        return

    send_typing(chat_id)

    if chat_id not in conversations:
        conversations[chat_id] = []

    conversations[chat_id].append({"role": "user", "content": text})

    # Keep last 30 messages to avoid token bloat
    if len(conversations[chat_id]) > 30:
        conversations[chat_id] = conversations[chat_id][-30:]

    messages = list(conversations[chat_id])

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        text_parts = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append(block)

        if text_parts:
            send_message(chat_id, "\n".join(text_parts))

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn" or not tool_calls:
            conversations[chat_id] = messages
            break

        tool_results = []
        for tc in tool_calls:
            if tc.name == "bash":
                cmd = tc.input["command"]
                log(f"bash: {cmd[:60]}")
                send_typing(chat_id)
                result = run_bash(cmd)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tc.id,
                    "content": result
                })

        messages.append({"role": "user", "content": tool_results})


def get_updates(offset=None):
    params = {"timeout": 30, "allowed_updates": ["message"]}
    if offset is not None:
        params["offset"] = offset
    try:
        resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
        return resp.json()
    except Exception as e:
        log(f"getUpdates error: {e}")
        return {"ok": False}


def main():
    log("Telegram bot starting...")
    offset = None

    # Clear pending updates on startup so old messages don't replay
    data = get_updates(-1)
    if data.get("ok") and data.get("result"):
        offset = data["result"][-1]["update_id"] + 1

    log("Ready. Listening for messages (long polling)...")

    while True:
        data = get_updates(offset)
        if not data.get("ok"):
            import time; time.sleep(5)
            continue

        for update in data.get("result", []):
            offset = update["update_id"] + 1
            msg = update.get("message")
            if not msg or "text" not in msg:
                continue

            chat_id = msg["chat"]["id"]
            user_id = msg["from"]["id"]
            text = msg["text"]
            log(f"msg from {user_id}: {text[:60]}")

            try:
                process_message(chat_id, user_id, text)
            except Exception as e:
                log(f"Error: {e}")
                send_message(chat_id, f"Error: {e}")


if __name__ == "__main__":
    main()
