"""Aggregator - combines results from multiple agents into a unified response."""

from __future__ import annotations
from groq import AsyncGroq
from common.config import get_settings
from common.models import AgentResult, OrchestratorResponse
from common.logging import get_logger

logger = get_logger(__name__)

AGGREGATION_PROMPT = """You are an AI orchestrator. You have received results from multiple specialized agents.
Your job is to synthesize these results into a single, coherent, helpful response for the user.

Guidelines:
- Combine information naturally and avoid repetition
- If some agents failed, acknowledge it briefly but focus on what succeeded
- Keep the response clear and well-structured
- Do not mention "agents" or system internals - present it as a unified answer
"""


class Aggregator:
    def __init__(self):
        self.settings = get_settings()
        self.llm = AsyncGroq(api_key=self.settings.groq_api_key)

    async def aggregate(
        self, query: str, intent: str, results: list[AgentResult]
    ) -> str:
        """Aggregate agent results into a coherent summary."""
        if not results:
            return "No results were returned from the agents."

        # Build context from successful results
        context_parts = []
        for result in results:
            if result.success and result.data:
                text = result.data.get("text", "")
                if text:
                    context_parts.append(f"[{result.agent.replace('_', ' ').title()}]\n{text}")

        if not context_parts:
            # All agents failed
            errors = [f"{r.agent}: {r.error}" for r in results if r.error]
            return f"All agents encountered errors:\n" + "\n".join(errors)

        context = "\n\n---\n\n".join(context_parts)

        user_message = (
            f"User query: {query}\n\n"
            f"Agent responses:\n\n{context}\n\n"
            "Please synthesize a unified, helpful response."
        )

        try:
            response = await self.llm.chat.completions.create(
                model=self.settings.groq_model,
                messages=[
                    {"role": "system", "content": AGGREGATION_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=1024,
                temperature=0.3,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error("aggregation_llm_failed", error=str(e))
            return context  # Fall back to raw concatenation

    def build_context_string(self, results: list[AgentResult]) -> str:
        """Build a context string from agent results for the report agent."""
        parts = []
        for result in results:
            if result.success and result.data:
                text = result.data.get("text", "")
                structured = result.data.get("structured")
                if text:
                    parts.append(f"=== {result.agent.replace('_', ' ').title()} ===\n{text}")
                if structured:
                    import json
                    parts.append(f"[Structured data: {json.dumps(structured, indent=2)[:1000]}]")
        return "\n\n".join(parts)
