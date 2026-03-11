"""
Intent parser - uses Groq to classify user query intent
and determine which agents should handle it.
"""

from __future__ import annotations
import json
from groq import AsyncGroq
from common.config import get_settings
from common.logging import get_logger

logger = get_logger(__name__)

INTENT_SYSTEM_PROMPT = """You are an intent classifier for a multi-agent AI system.
Given a user query, you must determine which agents should handle it.

Available agents:
- news_agent: Handles news fetching, current events, topic news searches
- weather_agent: Handles weather queries, temperature, forecasts, climate conditions
- report_agent: Handles requests for reports, summaries, or comprehensive documents

Rules:
1. A query can require one or more agents
2. If the query asks for a report or document combining multiple sources, include report_agent
3. For simple single-domain queries, use only the relevant agent
4. Extract any specific entities (cities, topics) from the query

Respond ONLY with a JSON object:
{
  "intent": "brief description of user intent",
  "agents": ["agent_name1", "agent_name2"],
  "entities": {
    "city": "extracted city if any",
    "topic": "extracted topic if any",
    "wants_report": true or false
  }
}
"""


class IntentParser:
    def __init__(self):
        self.settings = get_settings()
        self.llm = AsyncGroq(api_key=self.settings.groq_api_key)

    async def parse(self, query: str) -> dict:
        """Parse a user query into intent and agent routing."""
        try:
            response = await self.llm.chat.completions.create(
                model=self.settings.groq_model,
                messages=[
                    {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Query: {query}"},
                ],
                max_tokens=256,
                temperature=0.1,
            )

            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            parsed = json.loads(raw)
            logger.info("intent_parsed", query=query[:80], intent=parsed)
            return parsed

        except (json.JSONDecodeError, Exception) as e:
            logger.warning("intent_parse_fallback", error=str(e))
            return self._fallback_parse(query)

    def _fallback_parse(self, query: str) -> dict:
        """Rule-based fallback intent parsing."""
        query_lower = query.lower()
        agents = []

        weather_keywords = ["weather", "temperature", "forecast", "rain", "sunny", "cloudy", "wind", "humid"]
        news_keywords = ["news", "latest", "current events", "happening", "articles", "headlines"]
        report_keywords = ["report", "summary", "document", "compile", "comprehensive"]

        if any(k in query_lower for k in weather_keywords):
            agents.append("weather_agent")
        if any(k in query_lower for k in news_keywords):
            agents.append("news_agent")
        if any(k in query_lower for k in report_keywords):
            agents.append("report_agent")

        if not agents:
            agents = ["news_agent"]

        return {
            "intent": "User query requiring " + ", ".join(agents),
            "agents": agents,
            "entities": {"wants_report": "report_agent" in agents},
        }
