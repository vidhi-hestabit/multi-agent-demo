"""News agent task handler - uses Groq LLM + MCP news tool."""

from __future__ import annotations
import re
from groq import AsyncGroq

from common.config import get_settings
from common.a2a_types import Task
from common.logging import get_logger
from agents.base_agent.base_handler import BaseTaskHandler
from agents.base_agent.base_mcp_client import BaseMCPClient

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a News Research Agent. Your job is to:
1. Understand what news topic the user is asking about
2. Use the provided news data to give a clear, concise summary
3. Highlight the most important and relevant articles
4. Present findings in a structured, readable format

Always be factual and cite the sources of news articles.
If no real news data is available, clearly indicate that mock/placeholder data is being shown.
"""


class NewsAgentHandler(BaseTaskHandler):
    def __init__(self):
        self.settings = get_settings()
        self.mcp = BaseMCPClient()
        self.llm = AsyncGroq(api_key=self.settings.groq_api_key)

    async def process(self, task: Task) -> Task:
        query = task.history[-1].text() if task.history else ""
        logger.info("news_agent_process", query=query[:100])

        # Extract search topic from query
        topic = self._extract_topic(query)

        # Fetch news via MCP
        news_data = await self.mcp.call_tool("fetch_news", {"query": topic, "page_size": 5})

        # Build context for LLM
        articles = news_data.get("articles", [])
        is_mock = news_data.get("_mock", False)

        articles_text = "\n\n".join(
            f"Title: {a['title']}\n"
            f"Source: {a['source']}\n"
            f"Published: {a.get('published_at', 'N/A')}\n"
            f"Description: {a.get('description', 'N/A')}\n"
            f"URL: {a['url']}"
            for a in articles
        )

        if is_mock:
            articles_text = "[NOTE: Using mock data. Set NEWS_API_KEY in .env for real articles.]\n\n" + articles_text

        user_message = (
            f"User query: {query}\n\n"
            f"News articles fetched for topic '{topic}':\n\n"
            f"{articles_text}\n\n"
            f"Please summarize these news articles for the user."
        )

        # Call Groq LLM
        chat_response = await self.llm.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=1024,
            temperature=0.3,
        )

        summary = chat_response.choices[0].message.content

        return self._complete(
            task,
            text=summary,
            data={
                "topic": topic,
                "articles": articles,
                "total": news_data.get("total", len(articles)),
                "is_mock": is_mock,
            },
        )

    def _extract_topic(self, query: str) -> str:
        """Extract the main news topic from the user query."""
        # Remove common question words to get the core topic
        patterns = [
            r"(?:get|fetch|find|show|tell me about|what(?:'s| is) (?:happening with|the latest|the news about)?)\s+(.+?)(?:\s+news|\s+articles?|$)",
            r"(?:latest|recent|current)\s+(.+?)(?:\s+news|\s+articles?|$)",
            r"news (?:about|on|for)\s+(.+?)$",
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return match.group(1).strip()
        # Fallback: use first 50 chars of query
        return query[:50].strip()
