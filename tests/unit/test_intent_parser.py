"""Unit tests for the intent parser fallback logic."""

import pytest
from orchestrator.intent_parser import IntentParser


@pytest.fixture
def parser():
    return IntentParser()


def test_fallback_weather_query(parser):
    result = parser._fallback_parse("What is the weather in London?")
    assert "weather_agent" in result["agents"]


def test_fallback_news_query(parser):
    result = parser._fallback_parse("Latest news about AI")
    assert "news_agent" in result["agents"]


def test_fallback_report_query(parser):
    result = parser._fallback_parse("Generate a report about climate change")
    assert "report_agent" in result["agents"]


def test_fallback_combined_query(parser):
    result = parser._fallback_parse("Weather and news in Tokyo report")
    agents = result["agents"]
    assert "weather_agent" in agents
    assert "news_agent" in agents
    assert "report_agent" in agents


def test_fallback_unknown_defaults_to_news(parser):
    result = parser._fallback_parse("Hello world random text")
    assert result["agents"] == ["news_agent"]
