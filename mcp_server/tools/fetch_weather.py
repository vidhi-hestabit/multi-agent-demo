"""Fetch current weather data from OpenWeatherMap."""

from __future__ import annotations
import httpx
from common.config import get_settings
from common.errors import MCPError


TOOL_NAME = "fetch_weather"
TOOL_DESCRIPTION = "Fetch current weather conditions for a city."
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "city": {
            "type": "string",
            "description": "City name (e.g. 'London', 'Tokyo', 'New York')",
        },
        "units": {
            "type": "string",
            "description": "Temperature units: 'metric' (Celsius), 'imperial' (Fahrenheit), or 'standard' (Kelvin).",
            "enum": ["metric", "imperial", "standard"],
            "default": "metric",
        },
    },
    "required": ["city"],
}


async def handle(city: str, units: str = "metric") -> dict:
    settings = get_settings()
    api_key = settings.openweather_api_key

    if not api_key or api_key == "your_openweathermap_key_here":
        return _mock_weather(city, units)

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": api_key, "units": units}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(url, params=params)
            if response.status_code == 404:
                raise MCPError(f"City '{city}' not found", tool=TOOL_NAME)
            response.raise_for_status()
            data = response.json()

            unit_symbol = {"metric": "C", "imperial": "F", "standard": "K"}.get(units, "C")

            return {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temperature": data["main"]["temp"],
                "feels_like": data["main"]["feels_like"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "unit_symbol": unit_symbol,
                "timestamp": data["dt"],
            }

        except httpx.HTTPError as e:
            raise MCPError(f"HTTP error fetching weather: {e}", tool=TOOL_NAME)


def _mock_weather(city: str, units: str = "metric") -> dict:
    unit_symbol = {"metric": "C", "imperial": "F", "standard": "K"}.get(units, "C")
    return {
        "city": city.title(),
        "country": "XX",
        "temperature": 22.5,
        "feels_like": 21.0,
        "humidity": 65,
        "wind_speed": 5.2,
        "description": "partly cloudy",
        "icon": "02d",
        "unit_symbol": unit_symbol,
        "timestamp": 1717228800,
        "_mock": True,
    }
