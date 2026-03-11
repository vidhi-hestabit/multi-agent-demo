"""Unit tests for MCP tool handlers (using mock data paths)."""

import pytest
from mcp_server.tools import fetch_news, fetch_weather, generate_report


@pytest.mark.asyncio
async def test_fetch_news_mock():
    """fetch_news returns mock data when API key is not set."""
    result = await fetch_news.handle(query="artificial intelligence")
    assert "articles" in result
    assert len(result["articles"]) > 0
    assert result["_mock"] is True


@pytest.mark.asyncio
async def test_fetch_weather_mock():
    """fetch_weather returns mock data when API key is not set."""
    result = await fetch_weather.handle(city="London")
    assert "city" in result
    assert "temperature" in result
    assert result["_mock"] is True


@pytest.mark.asyncio
async def test_generate_report():
    """generate_report produces valid markdown."""
    result = await generate_report.handle(
        title="Test Report",
        summary="This is a test summary.",
        sections=[
            {"heading": "Introduction", "content": "Test content."},
            {"heading": "Conclusion", "content": "Test conclusion."},
        ],
    )
    assert "markdown" in result
    assert "# Test Report" in result["markdown"]
    assert "## Introduction" in result["markdown"]
    assert result["sections_count"] == 2


@pytest.mark.asyncio
async def test_generate_report_with_metadata():
    result = await generate_report.handle(
        title="Report",
        summary="Summary",
        sections=[],
        metadata={"author": "Test", "topic": "AI"},
    )
    assert "Author: Test" in result["markdown"]
