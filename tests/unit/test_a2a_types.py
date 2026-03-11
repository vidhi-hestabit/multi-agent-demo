"""Unit tests for A2A protocol types."""

import pytest
from common.a2a_types import (
    Message, TextPart, DataPart, Task, TaskState, TaskStatus,
    TaskSendRequest, AgentCard, AgentSkill, AgentCapabilities
)


def test_message_text_extraction():
    msg = Message(role="user", parts=[TextPart(text="Hello"), TextPart(text="World")])
    assert msg.text() == "Hello World"


def test_task_defaults():
    task = Task()
    assert task.status.state == TaskState.SUBMITTED
    assert task.history == []
    assert task.artifacts == []


def test_task_send_request_auto_id():
    req1 = TaskSendRequest(message=Message(role="user", parts=[TextPart(text="test")]))
    req2 = TaskSendRequest(message=Message(role="user", parts=[TextPart(text="test")]))
    assert req1.id != req2.id


def test_agent_card_serialization():
    card = AgentCard(
        name="Test Agent",
        description="A test agent",
        url="http://localhost:9999",
        skills=[
            AgentSkill(
                id="test_skill",
                name="Test Skill",
                description="Does testing",
            )
        ],
    )
    data = card.model_dump()
    assert data["name"] == "Test Agent"
    assert len(data["skills"]) == 1
