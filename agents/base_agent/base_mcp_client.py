"""
Base MCP client.
Agents use this to call tools on the MCP server via HTTP (SSE transport).
"""

from __future__ import annotations
import httpx
from common.config import get_settings
from common.errors import MCPError, ToolNotFoundError
from common.logging import get_logger
from common.utils import retry_async

logger = get_logger(__name__)


class BaseMCPClient:
    def __init__(self, base_url: str | None = None):
        settings = get_settings()
        self.base_url = base_url or settings.mcp_server_url
        self.timeout = settings.request_timeout

    @retry_async(max_attempts=3)
    async def call_tool(self, tool: str, arguments: dict) -> dict:
        """Call a tool on the MCP server and return the result."""
        url = f"{self.base_url}/tools/call"
        payload = {"tool": tool, "arguments": arguments}

        logger.debug("mcp_call", tool=tool, arguments=arguments)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                if response.status_code == 404:
                    raise ToolNotFoundError(tool)
                if response.status_code == 422:
                    error_data = response.json().get("detail", {})
                    raise MCPError(
                        error_data.get("message", "Tool call failed"),
                        tool=tool,
                        details=error_data,
                    )
                response.raise_for_status()
                data = response.json()
                return data.get("result", data)
            except (ToolNotFoundError, MCPError):
                raise
            except httpx.HTTPError as e:
                raise MCPError(f"HTTP error calling tool '{tool}': {e}", tool=tool)

    async def list_tools(self) -> list[dict]:
        """Retrieve all available tools from the MCP server."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/tools")
            response.raise_for_status()
            return response.json().get("tools", [])

    async def health(self) -> bool:
        """Check if the MCP server is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
