#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "=== AI API Testing Platform — Start All ==="
trap 'kill 0; exit' INT TERM EXIT

echo "[1/5] Starting demo service (local :8001)..."
(cd "$SCRIPT_DIR/demo-service" && python server.py --env-name local --port 8001) &
echo "[2/5] Starting demo service (staging :8002)..."
(cd "$SCRIPT_DIR/demo-service" && python server.py --env-name staging --port 8002) &
sleep 2

echo "[3/5] Starting backend Master (:8080)..."
(cd "$SCRIPT_DIR/backend" && python main.py) &
sleep 3

echo "[4/5] Starting 3 Worker instances..."
(cd "$SCRIPT_DIR/worker" && WORKER_NAME=worker-1 python worker.py) &
(cd "$SCRIPT_DIR/worker" && WORKER_NAME=worker-2 python worker.py) &
(cd "$SCRIPT_DIR/worker" && WORKER_NAME=worker-3 python worker.py) &

echo "[5/5] Starting frontend dev server (:5173)..."
(cd "$SCRIPT_DIR/frontend" && npm run dev) &

echo ""
echo "All services started!"
echo "  Demo (local):     http://localhost:8001"
echo "  Demo (staging):   http://localhost:8002"
echo "  Backend API:      http://localhost:8080"
echo "  Frontend:         http://localhost:5173"
echo "  Press Ctrl+C to stop all."
wait
