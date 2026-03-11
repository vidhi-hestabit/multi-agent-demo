"""Custom exception hierarchy for the multi-agent system."""

from typing import Optional


class AgentError(Exception):
    """Base exception for all agent errors."""

    def __init__(self, message: str, code: str = "AGENT_ERROR", details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}

    def to_dict(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


class MCPError(AgentError):
    """Raised when MCP tool execution fails."""

    def __init__(self, message: str, tool: str = "", details: Optional[dict] = None):
        super().__init__(message, code="MCP_ERROR", details={"tool": tool, **(details or {})})


class ToolNotFoundError(MCPError):
    """Raised when a requested MCP tool does not exist."""

    def __init__(self, tool: str):
        super().__init__(f"Tool '{tool}' not found", tool=tool)
        self.code = "TOOL_NOT_FOUND"


class AgentNotFoundError(AgentError):
    """Raised when a requested agent cannot be found."""

    def __init__(self, agent: str):
        super().__init__(f"Agent '{agent}' not found or unreachable", code="AGENT_NOT_FOUND")


class OrchestratorError(AgentError):
    """Raised for orchestrator-level failures."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code="ORCHESTRATOR_ERROR", details=details)


class TaskTimeoutError(AgentError):
    """Raised when a task exceeds its timeout."""

    def __init__(self, task_id: str, timeout: int):
        super().__init__(
            f"Task '{task_id}' timed out after {timeout}s",
            code="TASK_TIMEOUT",
            details={"task_id": task_id, "timeout": timeout},
        )


class LLMError(AgentError):
    """Raised when LLM call fails."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, code="LLM_ERROR", details=details)


class ConfigurationError(AgentError):
    """Raised when required configuration is missing or invalid."""

    def __init__(self, field: str):
        super().__init__(
            f"Configuration error: '{field}' is missing or invalid",
            code="CONFIG_ERROR",
            details={"field": field},
        )
