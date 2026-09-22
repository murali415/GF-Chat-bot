#!/bin/bash
# Run Aria GF chatbot on localhost:8000
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR/backend"
pip install -q --break-system-packages -r requirements.txt 2>/dev/null || pip install -q -r requirements.txt 2>/dev/null || true
# preload the local brain so first replies are fast too (best-effort, silent)
MODEL="${PRIYA_MODEL:-qwen2.5:0.5b}"
curl -s -m 60 -X POST http://localhost:11434/api/chat -H "Content-Type: application/json" \
  -d "{\"model\":\"$MODEL\",\"messages\":[{\"role\":\"user\",\"content\":\"hi\"}],\"stream\":false,\"keep_alive\":\"2h\",\"options\":{\"num_predict\":1}}" \
  >/dev/null 2>&1 &
echo "💖 Starting Aria on http://localhost:8000 ..."
uvicorn app:app --host 0.0.0.0 --port 8000
