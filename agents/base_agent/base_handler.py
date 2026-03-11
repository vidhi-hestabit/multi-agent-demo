"""
Base task handler.
All agent handlers inherit from this and implement `process`.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime

from common.a2a_types import (
    Task,
    TaskState,
    TaskStatus,
    Message,
    TextPart,
    DataPart,
    Artifact,
    TaskSendRequest,
    TaskSendResponse,
)
from common.logging import get_logger

logger = get_logger(__name__)


class BaseTaskHandler(ABC):
    """Abstract base class for agent task handlers."""

    @abstractmethod
    async def process(self, task: Task) -> Task:
        """Process a task and return the updated task with result."""
        ...

    async def handle_send(self, request: TaskSendRequest) -> TaskSendResponse:
        """Entry point called by the A2A server route."""
        task = Task(
            id=request.id,
            session_id=request.session_id,
            status=TaskStatus(state=TaskState.WORKING),
            history=[request.message],
            metadata=request.metadata,
        )

        logger.info("task_started", task_id=task.id, agent=self.__class__.__name__)

        try:
            task = await self.process(task)
            logger.info(
                "task_completed",
                task_id=task.id,
                state=task.status.state,
            )
        except Exception as e:
            logger.exception("task_failed", task_id=task.id)
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=Message(
                    role="agent",
                    parts=[TextPart(text=f"Task failed: {e}")],
                ),
            )

        return TaskSendResponse(
            id=task.id,
            status=task.status,
            artifacts=task.artifacts,
        )

    def _complete(self, task: Task, text: str, data: dict | None = None) -> Task:
        """Helper to mark a task as completed with a text response."""
        parts = [TextPart(text=text)]
        task.status = TaskStatus(
            state=TaskState.COMPLETED,
            message=Message(role="agent", parts=parts),
        )
        if data:
            task.artifacts.append(
                Artifact(
                    name="result",
                    parts=[DataPart(data=data)],
                )
            )
        return task

    def _fail(self, task: Task, reason: str) -> Task:
        task.status = TaskStatus(
            state=TaskState.FAILED,
            message=Message(role="agent", parts=[TextPart(text=reason)]),
        )
        return task
