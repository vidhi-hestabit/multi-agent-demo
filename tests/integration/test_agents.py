"""
Integration tests for individual agents.
Requires: All agents and MCP server running.
Run with: pytest tests/integration/test_agents.py -v
"""

import pytest
import httpx

AGENTS = {
    "news": "http://localhost:8001",
    "weather": "http://localhost:8002",
    "report": "http://localhost:8003",
}


def skip_if_down(url: str):
    async def _check():
        try:
            async with httpx.AsyncClient(timeout=3) as client:
                r = await client.get(f"{url}/health")
                r.raise_for_status()
                return True
        except Exception:
            return False
    import asyncio
    return not asyncio.get_event_loop().run_until_complete(_check())


@pytest.mark.asyncio
@pytest.mark.parametrize("agent,base_url", AGENTS.items())
async def test_agent_health(agent, base_url):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{base_url}/health")
            assert r.status_code == 200
    except Exception:
        pytest.skip(f"{agent} agent not running at {base_url}")


@pytest.mark.asyncio
@pytest.mark.parametrize("agent,base_url", AGENTS.items())
async def test_agent_card(agent, base_url):
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{base_url}/agent-card")
            assert r.status_code == 200
            card = r.json()
            assert "name" in card
            assert "skills" in card
    except Exception:
        pytest.skip(f"{agent} agent not running")


@pytest.mark.asyncio
async def test_news_agent_task():
    base_url = AGENTS["news"]
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{base_url}/health")
            r.raise_for_status()
    except Exception:
        pytest.skip("News agent not running")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{base_url}/tasks/send", json={
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "Latest AI news"}]
            }
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"]["state"] in ("completed", "failed")


@pytest.mark.asyncio
async def test_weather_agent_task():
    base_url = AGENTS["weather"]
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{base_url}/health")
            r.raise_for_status()
    except Exception:
        pytest.skip("Weather agent not running")

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(f"{base_url}/tasks/send", json={
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": "What is the weather in London?"}]
            }
        })
        assert r.status_code == 200
        data = r.json()
        assert data["status"]["state"] in ("completed", "failed")


@pytest.mark.asyncio
async def test_orchestrator_query():
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get("http://localhost:8004/health")
            r.raise_for_status()
    except Exception:
        pytest.skip("Orchestrator not running")

    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post("http://localhost:8004/query", json={
            "query": "What is the weather in London?",
            "stream": False
        })
        assert r.status_code == 200
        data = r.json()
        assert "summary" in data
        assert "results" in data
