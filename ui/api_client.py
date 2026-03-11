"""HTTP client for communicating with the orchestrator."""

from __future__ import annotations
import httpx
from common.config import get_settings
from common.logging import get_logger

logger = get_logger(__name__)


class OrchestratorClient:
    def __init__(self):
        settings = get_settings()
        self.base_url = settings.orchestrator_url
        self.timeout = settings.request_timeout

    async def query(self, user_query: str) -> dict:
        """Send a query to the orchestrator and return the full response."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/query",
                json={"query": user_query, "stream": False},
            )
            response.raise_for_status()
            return response.json()

    async def health(self) -> dict:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

    async def list_agents(self) -> dict:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{self.base_url}/agents")
            response.raise_for_status()
            return response.json()
