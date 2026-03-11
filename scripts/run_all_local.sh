#!/usr/bin/env bash
# Run all services locally using uv run (no manual venv activation needed).
# Usage:  ./scripts/run_all_local.sh
# Stop:   kill $(cat .pids) && rm .pids

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

# ---- Preflight checks ----

if ! command -v uv &> /dev/null; then
  echo "ERROR: uv is not installed."
  echo "Install it with:  curl -LsSf https://astral.sh/uv/install.sh | sh"
  exit 1
fi

if [ ! -f ".env" ]; then
  echo "ERROR: .env file not found."
  echo "Run:  cp .env.example .env  and fill in your API keys."
  exit 1
fi

# Sync dependencies (creates .venv if missing)
echo "Syncing dependencies with uv..."
uv sync --dev
echo ""

LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"
PID_FILE="$ROOT_DIR/.pids"
> "$PID_FILE"

start_service() {
  local name="$1"
  local module="$2"
  local log="$LOG_DIR/${name}.log"

  echo "Starting $name..."
  uv run python -m "$module" > "$log" 2>&1 &
  local pid=$!
  echo "$pid" >> "$PID_FILE"
  echo "  $name  PID=$pid  log=$log"
}

echo "=== Starting Multi-Agent AI System ==="
echo ""

start_service "mcp-server"     "mcp_server.main"
sleep 2

start_service "news-agent"     "agents.news_agent.main"
start_service "weather-agent"  "agents.weather_agent.main"
start_service "report-agent"   "agents.report_agent.main"
sleep 3

start_service "orchestrator"   "orchestrator.main"
sleep 2

start_service "ui"             "ui.app"

echo ""
echo "=== All services started ==="
echo ""
echo "Service URLs:"
echo "  MCP Server:    http://localhost:8000"
echo "  News Agent:    http://localhost:8001"
echo "  Weather Agent: http://localhost:8002"
echo "  Report Agent:  http://localhost:8003"
echo "  Orchestrator:  http://localhost:8004"
echo "  UI:            http://localhost:7860"
echo ""
echo "Logs:  $LOG_DIR"
echo "PIDs:  $PID_FILE"
echo ""
echo "To stop all:  kill \$(cat .pids) && rm .pids"
echo ""
echo "Press Ctrl+C to stop watching logs. Services keep running."
echo ""

tail -f "$LOG_DIR"/*.log
