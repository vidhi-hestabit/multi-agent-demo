"""Task manager - dispatches tasks to agents and collects results."""

from __future__ import annotations
import asyncio
import time
from common.a2a_types import TaskSendResponse
from common.models import AgentResult
from common.logging import get_logger
from orchestrator.agent_discovery import AgentDiscovery

logger = get_logger(__name__)


class TaskManager:
    def __init__(self, discovery: AgentDiscovery):
        self.discovery = discovery

    async def dispatch(
        self,
        agent_names: list[str],
        query: str,
        context: dict | None = None,
        metadata: dict | None = None,
    ) -> list[AgentResult]:
        """Dispatch a query to multiple agents concurrently."""
        tasks = [
            self._dispatch_single(agent_name, query, context, metadata)
            for agent_name in agent_names
            if agent_name != "report_agent"  # report_agent is handled separately after aggregation
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        agent_results = []
        for agent_name, result in zip(
            [a for a in agent_names if a != "report_agent"], results
        ):
            if isinstance(result, AgentResult):
                agent_results.append(result)
            else:
                agent_results.append(AgentResult(
                    agent=agent_name,
                    success=False,
                    error=str(result),
                ))
        return agent_results

    async def dispatch_report(
        self,
        query: str,
        context: str,
    ) -> AgentResult:
        """Dispatch to the report agent with aggregated context."""
        return await self._dispatch_single(
            "report_agent",
            query,
            metadata={"context": context},
        )

    async def _dispatch_single(
        self,
        agent_name: str,
        query: str,
        context: dict | None = None,
        metadata: dict | None = None,
    ) -> AgentResult:
        client = self.discovery.get_client(agent_name)
        if client is None:
            return AgentResult(agent=agent_name, success=False, error="Agent not found")

        start = time.perf_counter()
        try:
            response: TaskSendResponse = await client.send_task(
                text=query,
                session_id=None,
            )
            elapsed_ms = (time.perf_counter() - start) * 1000

            # Extract text from response
            text = ""
            data = None
            if response.status.message:
                text = response.status.message.text()
            if response.artifacts:
                from common.a2a_types import DataPart
                for artifact in response.artifacts:
                    for part in artifact.parts:
                        if isinstance(part, DataPart):
                            data = part.data
                            break

            return AgentResult(
                agent=agent_name,
                success=True,
                data={"text": text, "structured": data},
                duration_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error("agent_dispatch_failed", agent=agent_name, error=str(e))
            return AgentResult(
                agent=agent_name,
                success=False,
                error=str(e),
                duration_ms=elapsed_ms,
            )
