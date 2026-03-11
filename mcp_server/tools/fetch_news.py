"""Fetch news articles from NewsAPI."""

from __future__ import annotations
import httpx
from common.config import get_settings
from common.errors import MCPError


TOOL_NAME = "fetch_news"
TOOL_DESCRIPTION = "Fetch the latest news articles for a given topic or query."
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query for news articles (e.g. 'artificial intelligence', 'climate change')",
        },
        "language": {
            "type": "string",
            "description": "Language code (e.g. 'en', 'fr'). Defaults to 'en'.",
            "default": "en",
        },
        "page_size": {
            "type": "integer",
            "description": "Number of articles to return (1-10). Defaults to 5.",
            "default": 5,
            "minimum": 1,
            "maximum": 10,
        },
    },
    "required": ["query"],
}


async def handle(query: str, language: str = "en", page_size: int = 5) -> dict:
    settings = get_settings()
    api_key = settings.news_api_key

    if not api_key or api_key == "your_newsapi_key_here":
        # Return mock data when no API key is configured
        return _mock_news(query)

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": language,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "apiKey": api_key,
    }

    async with httpx.AsyncClient(timeout=15) as client:
        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "ok":
                raise MCPError(
                    f"NewsAPI error: {data.get('message', 'Unknown error')}",
                    tool=TOOL_NAME,
                )

            articles = []
            for article in data.get("articles", []):
                articles.append({
                    "title": article.get("title", ""),
                    "description": article.get("description", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", ""),
                    "published_at": article.get("publishedAt", ""),
                    "content": (article.get("content") or "")[:500],
                })

            return {"articles": articles, "total": data.get("totalResults", 0)}

        except httpx.HTTPError as e:
            raise MCPError(f"HTTP error fetching news: {e}", tool=TOOL_NAME)


def _mock_news(query: str) -> dict:
    """Return mock news data when API key is not configured."""
    return {
        "articles": [
            {
                "title": f"Breaking: Major developments in {query}",
                "description": f"Researchers and experts discuss the latest trends in {query}.",
                "url": "https://example.com/news/1",
                "source": "Mock News",
                "published_at": "2024-06-01T10:00:00Z",
                "content": f"This is mock content about {query}. Configure NEWS_API_KEY in .env for real data.",
            },
            {
                "title": f"{query.title()}: What you need to know",
                "description": f"An in-depth look at {query} and its implications.",
                "url": "https://example.com/news/2",
                "source": "Mock Daily",
                "published_at": "2024-06-01T09:00:00Z",
                "content": f"More mock content about {query}.",
            },
        ],
        "total": 2,
        "_mock": True,
    }
