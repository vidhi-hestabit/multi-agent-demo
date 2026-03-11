"""
Base A2A client.
Used by the orchestrator to send tasks to agents.
"""

from __future__ import annotations
import httpx
from common.a2a_types import (
    TaskSendRequest,
    TaskSendResponse,
    TaskGetResponse,
    Message,
    TextPart,
    AgentCard,
)
from common.errors import AgentError, AgentNotFoundError
from common.logging import get_logger
from common.utils import retry_async

logger = get_logger(__name__)


class BaseA2AClient:
    def __init__(self, agent_url: str, timeout: int = 30):
        self.agent_url = agent_url.rstrip("/")
        self.timeout = timeout

    @retry_async(max_attempts=2)
    async def send_task(self, text: str, session_id: str | None = None) -> TaskSendResponse:
        """Send a text task to the agent and return the response."""
        request = TaskSendRequest(
            session_id=session_id,
            message=Message(
                role="user",
                parts=[TextPart(text=text)],
            ),
        )

        url = f"{self.agent_url}/tasks/send"
        logger.debug("a2a_send_task", url=url, text=text[:100])

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=request.model_dump())
                if response.status_code in (404, 503):
                    raise AgentNotFoundError(self.agent_url)
                response.raise_for_status()
                return TaskSendResponse(**response.json())
            except AgentNotFoundError:
                raise
            except httpx.HTTPError as e:
                raise AgentError(f"HTTP error sending task to {self.agent_url}: {e}")

    async def get_task(self, task_id: str) -> TaskGetResponse:
        """Poll a task by ID."""
        url = f"{self.agent_url}/tasks/{task_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return TaskGetResponse(**response.json())

    async def get_agent_card(self) -> AgentCard:
        """Fetch the agent's capability card."""
        url = f"{self.agent_url}/agent-card"
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url)
            response.raise_for_status()
            return AgentCard(**response.json())

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self.agent_url}/health")
                return r.status_code == 200
        except Exception:
            return False
