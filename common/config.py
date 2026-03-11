"""Pydantic settings loaded from environment / .env file."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM
    groq_api_key: str = ""
    groq_model: str = "llama3-70b-8192"

    # External APIs
    news_api_key: str = ""
    openweather_api_key: str = ""

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""

    # Service ports
    mcp_server_port: int = 8000
    news_agent_port: int = 8001
    weather_agent_port: int = 8002
    report_agent_port: int = 8003
    orchestrator_port: int = 8004
    ui_port: int = 7860

    # Service hosts
    mcp_server_host: str = "localhost"
    news_agent_host: str = "localhost"
    weather_agent_host: str = "localhost"
    report_agent_host: str = "localhost"
    orchestrator_host: str = "localhost"

    # MCP transport
    mcp_transport: str = "sse"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # Tracing
    otel_enabled: bool = False
    otel_endpoint: str = "http://localhost:4317"

    # App
    app_env: str = "development"
    request_timeout: int = 30
    max_retries: int = 3

    # Derived URLs
    @property
    def mcp_server_url(self) -> str:
        return f"http://{self.mcp_server_host}:{self.mcp_server_port}"

    @property
    def news_agent_url(self) -> str:
        return f"http://{self.news_agent_host}:{self.news_agent_port}"

    @property
    def weather_agent_url(self) -> str:
        return f"http://{self.weather_agent_host}:{self.weather_agent_port}"

    @property
    def report_agent_url(self) -> str:
        return f"http://{self.report_agent_host}:{self.report_agent_port}"

    @property
    def orchestrator_url(self) -> str:
        return f"http://{self.orchestrator_host}:{self.orchestrator_port}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
