"""
Integration tests for the MCP server.
Requires: MCP server running at http://localhost:8000
Run with: pytest tests/integration/test_mcp_server.py -v
"""

import pytest
import httpx

BASE_URL = "http://localhost:8000"


@pytest.fixture(autouse=True)
async def check_server():
    """Skip tests if MCP server is not running."""
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{BASE_URL}/health")
            r.raise_for_status()
    except Exception:
        pytest.skip("MCP server is not running at http://localhost:8000")


@pytest.mark.asyncio
async def test_health():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_list_tools():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/tools")
        assert r.status_code == 200
        tools = r.json()["tools"]
        tool_names = [t["name"] for t in tools]
        assert "fetch_news" in tool_names
        assert "fetch_weather" in tool_names
        assert "generate_report" in tool_names


@pytest.mark.asyncio
async def test_call_fetch_news():
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{BASE_URL}/tools/call", json={
            "tool": "fetch_news",
            "arguments": {"query": "test"}
        })
        assert r.status_code == 200
        result = r.json()["result"]
        assert "articles" in result


@pytest.mark.asyncio
async def test_call_fetch_weather():
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{BASE_URL}/tools/call", json={
            "tool": "fetch_weather",
            "arguments": {"city": "London"}
        })
        assert r.status_code == 200
        result = r.json()["result"]
        assert "temperature" in result


@pytest.mark.asyncio
async def test_call_nonexistent_tool():
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/tools/call", json={
            "tool": "does_not_exist",
            "arguments": {}
        })
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_sse_endpoint():
    """Test that SSE endpoint streams tool definitions."""
    async with httpx.AsyncClient(timeout=5) as client:
        async with client.stream("GET", f"{BASE_URL}/sse") as r:
            assert r.status_code == 200
            assert "text/event-stream" in r.headers.get("content-type", "")
            # Read first event
            async for line in r.aiter_lines():
                if line.startswith("data:"):
                    import json
                    data = json.loads(line[5:].strip())
                    assert data["type"] == "tools"
                    break
