"""Report Agent entry point."""

import uvicorn
from common.config import get_settings
from common.logging import setup_logging, get_logger
from common.tracing import init_tracing
from common.a2a_types import AgentCard, AgentCapabilities
from agents.report_agent.handler import ReportAgentHandler
from agents.report_agent.skills import SKILLS
from agents.base_agent.base_a2a_server import create_agent_app


def main():
    setup_logging()
    logger = get_logger("report_agent")
    settings = get_settings()
    init_tracing("report-agent")

    agent_card = AgentCard(
        name="Report Agent",
        description="Compiles data from multiple sources into structured markdown reports.",
        url=f"http://{settings.report_agent_host}:{settings.report_agent_port}",
        version="1.0.0",
        capabilities=AgentCapabilities(streaming=False),
        skills=SKILLS,
    )

    handler = ReportAgentHandler()
    app = create_agent_app(handler, agent_card)

    logger.info("report_agent_starting", port=settings.report_agent_port)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.report_agent_port,
        log_config=None,
    )


if __name__ == "__main__":
    main()
