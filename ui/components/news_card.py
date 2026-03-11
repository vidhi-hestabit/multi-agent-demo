"""Format news articles as HTML cards."""

from __future__ import annotations


def format_news_card(article: dict) -> str:
    title = article.get("title", "No title")
    description = article.get("description", "")
    url = article.get("url", "#")
    source = article.get("source", "Unknown")
    published = article.get("published_at", "")

    return f"""
<div style="border:1px solid #e0e0e0; border-radius:8px; padding:12px; margin:8px 0; background:#fafafa;">
  <h4 style="margin:0 0 6px 0;"><a href="{url}" target="_blank" style="color:#1a73e8; text-decoration:none;">{title}</a></h4>
  <p style="margin:0 0 6px 0; color:#555; font-size:14px;">{description}</p>
  <small style="color:#888;">{source} &bull; {published[:10] if published else 'N/A'}</small>
</div>
"""


def format_news_section(articles: list[dict]) -> str:
    if not articles:
        return "<p>No news articles found.</p>"
    return "".join(format_news_card(a) for a in articles[:5])
