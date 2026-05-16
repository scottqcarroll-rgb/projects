#!/bin/bash
# Called on reboot by cron — starts Claude+Telegram in a detached tmux session

export PATH="$HOME/.bun/bin:$PATH"
export TELEGRAM_BOT_TOKEN="$(grep TELEGRAM_BOT_TOKEN ~/.claude/channels/telegram/.env | cut -d= -f2)"

PLUGIN_DIR="$HOME/.claude/plugins/telegram@claude-plugins-official"
SESSION="claude-telegram"

sleep 15

if tmux has-session -t "$SESSION" 2>/dev/null; then
    exit 0
fi

tmux new-session -d -s "$SESSION" -x 220 -y 50 \
    "export PATH=$HOME/.bun/bin:\$PATH; \
     export TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN; \
     /home/scott/.vscode-server/extensions/anthropic.claude-code-2.1.142-linux-x64/resources/native-binary/claude \
     --dangerously-load-development-channels server:telegram"

# Auto-answer the two confirmation prompts (trust folder + dev channels warning)
sleep 8 && tmux send-keys -t "$SESSION" "" Enter
sleep 3 && tmux send-keys -t "$SESSION" "" Enter
