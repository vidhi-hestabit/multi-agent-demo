"""
Base A2A FastAPI server factory.
Each agent calls create_agent_app() with its handler and agent card.
"""

from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from common.a2a_types import AgentCard, TaskSendRequest, TaskSendResponse, TaskGetResponse
from common.logging import get_logger
from agents.base_agent.base_handler import BaseTaskHandler

logger = get_logger(__name__)

# In-memory task store (sufficient for local/dev; replace with Redis for prod)
_task_store: dict[str, TaskSendResponse] = {}


def create_agent_app(handler: BaseTaskHandler, agent_card: AgentCard) -> FastAPI:
    app = FastAPI(title=agent_card.name, version=agent_card.version)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "agent": agent_card.name}

    @app.get("/agent-card")
    async def get_agent_card():
        return agent_card.model_dump()

    @app.post("/tasks/send", response_model=TaskSendResponse)
    async def send_task(request: TaskSendRequest):
        response = await handler.handle_send(request)
        _task_store[response.id] = response
        return response

    @app.get("/tasks/{task_id}")
    async def get_task(task_id: str):
        if task_id not in _task_store:
            raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")
        stored = _task_store[task_id]
        return TaskGetResponse(
            id=stored.id,
            status=stored.status,
            artifacts=stored.artifacts,
        )

    return app
