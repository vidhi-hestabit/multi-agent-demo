#!/usr/bin/env bash
# Quick end-to-end test script
# Usage: ./scripts/test_query.sh "your query here"
# Example: ./scripts/test_query.sh "weather in London"

set -euo pipefail

# Use uv run if available, else fall back to bare python/pytest
UV_RUN=""
if command -v uv &> /dev/null; then
  UV_RUN="uv run"
fi

QUERY="${1:-What is the latest AI news?}"
ORCHESTRATOR_URL="${ORCHESTRATOR_URL:-http://localhost:8004}"
MCP_URL="${MCP_URL:-http://localhost:8000}"

echo "=== Multi-Agent AI System Test ==="
echo ""

# Colours
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check() {
  local name="$1"
  local url="$2"
  if curl -sf "$url" > /dev/null 2>&1; then
    echo -e "${GREEN}[OK]${NC}  $name ($url)"
  else
    echo -e "${RED}[FAIL]${NC} $name ($url)"
  fi
}

echo "--- Health Checks ---"
check "MCP Server"    "$MCP_URL/health"
check "News Agent"    "http://localhost:8001/health"
check "Weather Agent" "http://localhost:8002/health"
check "Report Agent"  "http://localhost:8003/health"
check "Orchestrator"  "$ORCHESTRATOR_URL/health"
echo ""

echo "--- MCP Tools ---"
curl -sf "$MCP_URL/tools" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for t in data.get('tools', []):
    print(f\"  {t['name']}: {t['description'][:60]}\")
"
echo ""

echo "--- Agent Cards ---"
for port in 8001 8002 8003; do
  echo -n "  Port $port: "
  curl -sf "http://localhost:$port/agent-card" | python3 -c "
import json, sys
try:
    card = json.load(sys.stdin)
    print(card.get('name', 'unknown'))
except:
    print('(unreachable)')
" 2>/dev/null || echo "(unreachable)"
done
echo ""

echo "--- Orchestrator Query ---"
echo -e "${YELLOW}Query:${NC} $QUERY"
echo ""

RESPONSE=$(curl -sf -X POST "$ORCHESTRATOR_URL/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\", \"stream\": false}" 2>&1) || {
  echo -e "${RED}ERROR:${NC} Orchestrator query failed. Is it running?"
  exit 1
}

echo "$RESPONSE" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print('Intent:', data.get('intent', 'N/A'))
print('Agents used:', [r['agent'] for r in data.get('results', [])])
print()
print('--- Summary ---')
print(data.get('summary', 'No summary'))
print()
results = data.get('results', [])
for r in results:
    status = 'OK' if r.get('success') else 'FAIL'
    duration = f\"{r.get('duration_ms', 0):.0f}ms\" if r.get('duration_ms') else ''
    print(f\"Agent: {r['agent']} [{status}] {duration}\")
    if r.get('error'):
        print(f\"  Error: {r['error']}\")
"

echo ""
echo "=== Test complete ==="
