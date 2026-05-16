#!/bin/bash
# Start or reattach to persistent Claude+Telegram session in tmux

export PATH="$HOME/.bun/bin:$PATH"
export TELEGRAM_BOT_TOKEN="$(grep TELEGRAM_BOT_TOKEN ~/.claude/channels/telegram/.env | cut -d= -f2)"

PLUGIN_DIR="$HOME/.claude/plugins/telegram@claude-plugins-official"
SESSION="claude-telegram"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session already running — attaching..."
    tmux attach -t "$SESSION"
else
    echo "Starting new Claude+Telegram session..."
    tmux new-session -s "$SESSION" \
        -x 220 -y 50 \
        "/home/scott/.vscode-server/extensions/anthropic.claude-code-2.1.142-linux-x64/resources/native-binary/claude --dangerously-load-development-channels server:telegram"
fi
