"""Agent discovery - fetches and caches agent cards."""

from __future__ import annotations
import asyncio
from common.config import get_settings
from common.a2a_types import AgentCard
from common.logging import get_logger
from agents.base_agent.base_a2a_client import BaseA2AClient

logger = get_logger(__name__)


class AgentDiscovery:
    def __init__(self):
        self.settings = get_settings()
        self._cards: dict[str, AgentCard] = {}
        self._clients: dict[str, BaseA2AClient] = {}
        self._setup_clients()

    def _setup_clients(self):
        agents = {
            "news_agent": self.settings.news_agent_url,
            "weather_agent": self.settings.weather_agent_url,
            "report_agent": self.settings.report_agent_url,
        }
        for name, url in agents.items():
            self._clients[name] = BaseA2AClient(url, timeout=self.settings.request_timeout)

    async def discover_all(self) -> dict[str, AgentCard]:
        """Discover all agents and cache their cards."""
        tasks = {
            name: asyncio.create_task(self._discover_agent(name, client))
            for name, client in self._clients.items()
        }
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        for name, result in zip(tasks.keys(), results):
            if isinstance(result, AgentCard):
                self._cards[name] = result
                logger.info("agent_discovered", agent=name, url=self._clients[name].agent_url)
            else:
                logger.warning("agent_discovery_failed", agent=name, error=str(result))
        return self._cards

    async def _discover_agent(self, name: str, client: BaseA2AClient) -> AgentCard:
        return await client.get_agent_card()

    def get_client(self, agent_name: str) -> BaseA2AClient | None:
        return self._clients.get(agent_name)

    async def health_check(self) -> dict[str, bool]:
        results = {}
        for name, client in self._clients.items():
            results[name] = await client.health()
        return results
