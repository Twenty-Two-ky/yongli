#!/usr/bin/env bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "Starting local environment on :8001..."
python "$SCRIPT_DIR/server.py" --env-name local --port 8001 &
PID1=$!
echo "Starting staging environment on :8002..."
python "$SCRIPT_DIR/server.py" --env-name staging --port 8002 &
PID2=$!
echo "Both environments running."
echo "  Local:   http://localhost:8001 (admin/123456)"
echo "  Staging: http://localhost:8002 (admin/staging123)"
echo "Press Ctrl+C to stop both."
trap "kill $PID1 $PID2 2>/dev/null; exit" INT TERM
wait
