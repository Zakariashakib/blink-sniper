#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "========================================="
echo "   Starting BLINK SNIPER (Hands-Free)    "
echo "========================================="
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif command -v python3 >/dev/null 2>&1; then
    echo "Creating virtual environment and installing dependencies..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi
python3 main.py
