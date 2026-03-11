"""Router - coordinates intent parsing, task dispatch, and aggregation."""

from __future__ import annotations
from common.models import AgentResult, OrchestratorResponse
from common.logging import get_logger
from orchestrator.intent_parser import IntentParser
from orchestrator.agent_discovery import AgentDiscovery
from orchestrator.task_manager import TaskManager
from orchestrator.aggregator import Aggregator

logger = get_logger(__name__)


class Router:
    def __init__(self, discovery: AgentDiscovery):
        self.intent_parser = IntentParser()
        self.task_manager = TaskManager(discovery)
        self.aggregator = Aggregator()

    async def route(self, query: str) -> OrchestratorResponse:
        """Main routing logic: parse intent -> dispatch -> aggregate."""

        # 1. Parse intent
        intent_data = await self.intent_parser.parse(query)
        intent = intent_data.get("intent", "general query")
        agents = intent_data.get("agents", ["news_agent"])
        wants_report = intent_data.get("entities", {}).get("wants_report", False)

        logger.info("routing", query=query[:80], agents=agents, intent=intent)

        # 2. Dispatch to primary agents (not report_agent yet)
        primary_agents = [a for a in agents if a != "report_agent"]
        if not primary_agents:
            primary_agents = ["news_agent"]

        results = await self.task_manager.dispatch(primary_agents, query)

        # 3. If report is wanted, dispatch to report agent with aggregated context
        if wants_report or "report_agent" in agents:
            context_str = self.aggregator.build_context_string(results)
            report_result = await self.task_manager.dispatch_report(query, context_str)
            results.append(report_result)

        # 4. Aggregate results
        summary = await self.aggregator.aggregate(query, intent, results)

        return OrchestratorResponse(
            query=query,
            intent=intent,
            results=results,
            summary=summary,
        )
