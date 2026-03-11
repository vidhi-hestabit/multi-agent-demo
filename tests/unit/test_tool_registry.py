"""Unit tests for the MCP tool registry."""

import pytest
from mcp_server.tool_registry import ToolRegistry, ToolDefinition


async def dummy_handler(**kwargs):
    return {"ok": True}


@pytest.fixture
def registry():
    r = ToolRegistry()
    r.register(ToolDefinition(
        name="test_tool",
        description="A test tool",
        input_schema={"type": "object", "properties": {"x": {"type": "string"}}, "required": ["x"]},
        handler=dummy_handler,
        tags=["test"],
    ))
    return r


def test_register_and_get(registry):
    tool = registry.get("test_tool")
    assert tool is not None
    assert tool.name == "test_tool"


def test_get_missing(registry):
    assert registry.get("nonexistent") is None


def test_list_tools(registry):
    tools = registry.list_tools()
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"


def test_all_names(registry):
    assert "test_tool" in registry.all_names()


@pytest.mark.asyncio
async def test_handler_callable(registry):
    tool = registry.get("test_tool")
    result = await tool.handler(x="hello")
    assert result == {"ok": True}
