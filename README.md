# Multi-Agent AI System

A production-ready multi-agent AI system using the A2A (Agent-to-Agent) protocol and MCP (Model Context Protocol) with Groq as the LLM provider.

## Architecture

```
User -> UI (Gradio) -> Orchestrator -> Agents -> MCP Tools -> Agents -> Orchestrator -> UI
```

### Services

| Service | Port | Description |
|---|---|---|
| MCP Server (SSE) | 8000 | Tool server exposing news, weather, report, email tools |
| News Agent | 8001 | Fetches and summarizes news |
| Weather Agent | 8002 | Fetches weather data and maps |
| Report Agent | 8003 | Generates structured reports |
| Orchestrator | 8004 | Routes requests, aggregates results |
| UI | 7860 | Gradio web interface |

## Quick Start (Local)

### 1. Prerequisites

- Python 3.11+
- uv (install: `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Docker + Docker Compose (optional, for containerized run)
- Groq API key (free at https://console.groq.com)
- NewsAPI key (free at https://newsapi.org)
- OpenWeatherMap key (free at https://openweathermap.org/api)

### 2. Install dependencies

```bash
# uv creates .venv and installs everything from pyproject.toml
uv sync

# Include dev/test tools
uv sync --dev
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your API keys
```

### 4. Run everything locally

```bash
chmod +x scripts/run_all_local.sh
./scripts/run_all_local.sh
```

Or start services individually (each in its own terminal):

```bash
# Terminal 1 - MCP Server
uv run python -m mcp_server.main

# Terminal 2 - News Agent
uv run python -m agents.news_agent.main

# Terminal 3 - Weather Agent
uv run python -m agents.weather_agent.main

# Terminal 4 - Report Agent
uv run python -m agents.report_agent.main

# Terminal 5 - Orchestrator
uv run python -m orchestrator.main

# Terminal 6 - UI
uv run python -m ui.app
```

### 5. Run with Docker Compose

```bash
docker-compose up --build
```

### 6. Access the UI

Open http://localhost:7860 in your browser.

## Testing

### Test the MCP Server (SSE mode)

```bash
# Check server is up
curl http://localhost:8000/health

# List available tools
curl http://localhost:8000/tools

# Call a tool directly
curl -X POST http://localhost:8000/tools/call \
  -H "Content-Type: application/json" \
  -d '{"tool": "fetch_weather", "arguments": {"city": "London"}}'

# Test SSE stream
curl -N http://localhost:8000/sse
```

### Test an Agent directly

```bash
# Check agent card
curl http://localhost:8001/agent-card

# Send a task
curl -X POST http://localhost:8001/tasks/send \
  -H "Content-Type: application/json" \
  -d '{
    "id": "test-001",
    "message": {
      "role": "user",
      "parts": [{"type": "text", "text": "Get me the latest AI news"}]
    }
  }'
```

### Test the Orchestrator

```bash
curl -X POST http://localhost:8004/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Paris and any related news?"}'
```

### Run unit tests

```bash
uv run pytest tests/unit/ -v
```

### Run integration tests (requires all services running)

```bash
uv run pytest tests/integration/ -v
```

### Quick end-to-end test

```bash
chmod +x scripts/test_query.sh
./scripts/test_query.sh "weather in Tokyo"
```

### Adding or upgrading a dependency

```bash
uv add <package>           # add to pyproject.toml and lock file
uv add --dev <package>     # add as dev-only dependency
uv remove <package>        # remove a dependency
uv lock --upgrade          # upgrade all deps within constraints
```

## MCP Server Modes

This project uses SSE (Server-Sent Events) mode for the MCP server, which means:
- The server runs as a persistent HTTP service
- Clients connect via HTTP and receive streaming responses
- No subprocess spawning required (unlike stdio mode)

To switch to stdio mode (for local Claude Desktop integration), see `mcp_server/main.py` and set `MCP_TRANSPORT=stdio` in `.env`.

## Environment Variables

See `.env.example` for all available configuration options.

## Project Structure

```
common/          Shared schemas, config, logging, tracing
mcp_server/      MCP tool server (SSE transport)
agents/          Individual AI agents (A2A protocol)
orchestrator/    Request routing and aggregation
ui/              Gradio web interface
scripts/         Local dev and test scripts
tests/           Unit, integration, load tests
```
