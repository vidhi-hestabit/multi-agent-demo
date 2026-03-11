"""SSE streaming support for the orchestrator."""

from __future__ import annotations
import json
import asyncio
from typing import AsyncGenerator
from common.models import AgentResult, OrchestratorResponse


async def stream_response(response: OrchestratorResponse) -> AsyncGenerator[str, None]:
    """
    Stream an orchestrator response as SSE events.
    Yields events in order: intent -> results -> summary -> done
    """
    # Event: intent
    yield _event("intent", {"intent": response.intent, "query": response.query})
    await asyncio.sleep(0)

    # Event: per-agent result
    for result in response.results:
        yield _event("agent_result", {
            "agent": result.agent,
            "success": result.success,
            "duration_ms": result.duration_ms,
            "text": result.data.get("text", "") if result.success and result.data else "",
            "error": result.error,
        })
        await asyncio.sleep(0)

    # Event: summary
    yield _event("summary", {"text": response.summary})
    await asyncio.sleep(0)

    # Event: done
    yield _event("done", {"generated_at": response.generated_at.isoformat()})


def _event(event_type: str, data: dict) -> str:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
