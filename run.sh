#!/bin/bash
# Run Aria GF chatbot on localhost:8000
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/backend"
pip install -q --break-system-packages -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt 2>/dev/null || true
echo "💖 Starting Aria on http://localhost:8000 ..."
uvicorn app:app --host 0.0.0.0 --port 8000
