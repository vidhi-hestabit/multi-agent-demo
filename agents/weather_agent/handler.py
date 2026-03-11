"""Weather agent task handler."""

from __future__ import annotations
import re
from groq import AsyncGroq

from common.config import get_settings
from common.a2a_types import Task
from common.logging import get_logger
from agents.base_agent.base_handler import BaseTaskHandler
from agents.base_agent.base_mcp_client import BaseMCPClient

logger = get_logger(__name__)

SYSTEM_PROMPT = """You are a Weather Agent. Your job is to:
1. Interpret the user's weather query (city, conditions they want to know)
2. Present weather data in a clear, friendly way
3. Include temperature, humidity, wind speed, and general conditions
4. Use natural language - avoid raw JSON

Always mention if data is mock/placeholder when applicable.
"""

# Simple city coordinate lookup for map generation
CITY_COORDS: dict[str, tuple[float, float]] = {
    "london": (51.5074, -0.1278),
    "new york": (40.7128, -74.0060),
    "tokyo": (35.6762, 139.6503),
    "paris": (48.8566, 2.3522),
    "sydney": (-33.8688, 151.2093),
    "dubai": (25.2048, 55.2708),
    "berlin": (52.5200, 13.4050),
    "mumbai": (19.0760, 72.8777),
    "delhi": (28.6139, 77.2090),
    "singapore": (1.3521, 103.8198),
}


class WeatherAgentHandler(BaseTaskHandler):
    def __init__(self):
        self.settings = get_settings()
        self.mcp = BaseMCPClient()
        self.llm = AsyncGroq(api_key=self.settings.groq_api_key)

    async def process(self, task: Task) -> Task:
        query = task.history[-1].text() if task.history else ""
        logger.info("weather_agent_process", query=query[:100])

        city = self._extract_city(query)

        # Fetch weather
        weather_data = await self.mcp.call_tool("fetch_weather", {"city": city, "units": "metric"})
        is_mock = weather_data.get("_mock", False)

        # Try to generate a map
        map_data = None
        city_lower = city.lower()
        coords = CITY_COORDS.get(city_lower)
        if coords:
            try:
                map_data = await self.mcp.call_tool(
                    "weather_map",
                    {"lat": coords[0], "lon": coords[1], "layer": "precipitation_new"},
                )
            except Exception:
                pass

        # Build LLM prompt
        weather_summary = (
            f"City: {weather_data.get('city')}, {weather_data.get('country')}\n"
            f"Temperature: {weather_data.get('temperature')}°{weather_data.get('unit_symbol', 'C')}\n"
            f"Feels like: {weather_data.get('feels_like')}°{weather_data.get('unit_symbol', 'C')}\n"
            f"Humidity: {weather_data.get('humidity')}%\n"
            f"Wind speed: {weather_data.get('wind_speed')} m/s\n"
            f"Conditions: {weather_data.get('description')}"
        )

        if is_mock:
            weather_summary = "[NOTE: Mock data - set OPENWEATHER_API_KEY for real weather]\n\n" + weather_summary

        user_message = (
            f"User query: {query}\n\n"
            f"Weather data:\n{weather_summary}\n\n"
            "Please present this weather information in a friendly, natural way."
        )

        chat_response = await self.llm.chat.completions.create(
            model=self.settings.groq_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=512,
            temperature=0.3,
        )

        summary = chat_response.choices[0].message.content

        result_data = {"city": city, "weather": weather_data, "is_mock": is_mock}
        if map_data:
            result_data["map"] = map_data

        return self._complete(task, text=summary, data=result_data)

    def _extract_city(self, query: str) -> str:
        """Extract city name from a weather query."""
        patterns = [
            r"weather (?:in|for|at)\s+([A-Za-z\s]+?)(?:\s+today|\s+tomorrow|\s+forecast|$|\?)",
            r"(?:temperature|forecast|conditions?) (?:in|for|at)\s+([A-Za-z\s]+?)(?:\s+today|$|\?)",
            r"(?:is it|what(?:'s| is) it like) (?:in|at)\s+([A-Za-z\s]+?)(?:\s+today|$|\?)",
            r"([A-Za-z\s]+?) weather",
        ]
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                city = match.group(1).strip().rstrip("?.,")
                if city and len(city) > 1:
                    return city
        # Last resort: return first proper noun or default
        words = [w for w in query.split() if w[0].isupper()] if query else []
        return words[0] if words else "London"
