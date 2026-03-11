"""Report agent task handler."""

from __future__ import annotations
import json
from groq import AsyncGroq

from common.config import get_settings
from common.a2a_types import Task
from common.logging import get_logger
from agents.base_agent.base_handler import BaseTaskHandler
from agents.base_agent.base_mcp_client import BaseMCPClient

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a Report Generation Agent. Your task is to:
1. Analyze the provided query and context data
2. Structure it into a professional, well-formatted report
3. Include an executive summary, key findings, and relevant sections
4. Use clear headings, bullet points where appropriate
5. The report should be comprehensive yet concise

Return ONLY a JSON object with this exact structure:
{
  "title": "Report Title",
  "summary": "Executive summary paragraph",
  "sections": [
    {"heading": "Section Name", "content": "Section content"}
  ],
  "metadata": {"topic": "...", "data_sources": [...]}
}
Do not include any text outside the JSON object.
"""


class ReportAgentHandler(BaseTaskHandler):
    def __init__(self):
        self.settings = get_settings()
        self.mcp = BaseMCPClient()
        self.llm = AsyncGroq(api_key=self.settings.groq_api_key)

    async def process(self, task: Task) -> Task:
        query = task.history[-1].text() if task.history else ""
        context = task.metadata.get("context", "")
        logger.info("report_agent_process", query=query[:100])

        user_message = f"Query: {query}"
        if context:
            user_message += f"\n\nContext data:\n{context}"

        # Ask LLM to structure the report
        chat_response = await self.llm.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=2048,
            temperature=0.2,
        )

        raw = chat_response.choices[0].message.content.strip()

        # Parse JSON response
        try:
            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            report_spec = json.loads(raw)
        except json.JSONDecodeError:
            # Fallback: create a basic report structure
            report_spec = {
                "title": f"Report: {query[:60]}",
                "summary": raw[:500] if raw else "No summary available.",
                "sections": [],
                "metadata": {},
            }

        # Use MCP generate_report tool to produce the final markdown
        report_result = await self.mcp.call_tool("generate_report", {
            "title": report_spec.get("title", "Report"),
            "summary": report_spec.get("summary", ""),
            "sections": report_spec.get("sections", []),
            "metadata": report_spec.get("metadata", {}),
        })

        markdown = report_result.get("markdown", "")

        return self._complete(
            task,
            text=markdown,
            data={
                "title": report_spec.get("title"),
                "markdown": markdown,
                "sections_count": report_result.get("sections_count", 0),
                "generated_at": report_result.get("generated_at"),
            },
        )
