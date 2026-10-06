#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .local
export API_SECRET_KEY="${API_SECRET_KEY:-local-demo-only-token}"
export CANARY_API_TOKEN="$API_SECRET_KEY"
export CANARY_API_URL=http://127.0.0.1:8001
export AUTH_REQUIRED=false
export NODE_ENV=development
export ALLOW_PRIVATE_TARGETS=true
export DB_PATH="$PWD/.local/canary.db"
export REPORT_OUTPUT_DIR="$PWD/.local/reports"
export LOG_FILE="$PWD/.local/backend.log"
export PYTHONPATH="$PWD/cyber-redteam-foundry/src:$PWD/demo-agent/src${PYTHONPATH:+:$PYTHONPATH}"
backend_python="${CANARY_BACKEND_PYTHON:-$PWD/cyber-redteam-foundry/.venv/bin/python}"
pids=()
cleanup() { for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM
(cd cyber-redteam-foundry && exec "$backend_python" -m uvicorn cyberredteam.api:app --host 127.0.0.1 --port 8001) > .local/api.log 2>&1 &
pids+=("$!")
(cd demo-agent && exec .venv/bin/uvicorn companybot.fixture:app --host 127.0.0.1 --port 9000) > .local/target.log 2>&1 &
pids+=("$!")
(cd canary && exec node node_modules/vite/bin/vite.js --port 5173 --strictPort) > .local/dashboard.log 2>&1 &
pids+=("$!")
echo 'Dashboard: http://127.0.0.1:5173 — integration fixture, no provider calls.'
wait
