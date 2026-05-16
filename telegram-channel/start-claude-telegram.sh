#!/bin/bash
# Start or reattach to persistent Claude+Telegram session in tmux

export PATH="$HOME/.bun/bin:$PATH"
export TELEGRAM_BOT_TOKEN="$(grep TELEGRAM_BOT_TOKEN ~/.claude/channels/telegram/.env | cut -d= -f2)"

SESSION="claude-telegram"

if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Session already running — attaching..."
    tmux attach -t "$SESSION"
else
    echo "Starting new Claude+Telegram session..."
    tmux new-session -d -s "$SESSION" -x 220 -y 50 \
        "/home/scott/.vscode-server/extensions/anthropic.claude-code-2.1.142-linux-x64/resources/native-binary/claude --dangerously-load-development-channels server:telegram"

    # Auto-answer: "trust this folder" then "local development" prompts
    sleep 10 && tmux send-keys -t "$SESSION" "1" Enter &
    sleep 14 && tmux send-keys -t "$SESSION" "1" Enter &

    echo "Waiting for Claude to start..."
    sleep 16
    tmux attach -t "$SESSION"
fi
