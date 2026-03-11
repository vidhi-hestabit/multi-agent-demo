"""Generate a static weather map URL for a city using OpenWeatherMap tile layers."""

from __future__ import annotations
from common.config import get_settings


TOOL_NAME = "weather_map"
TOOL_DESCRIPTION = (
    "Generate a weather map URL showing precipitation or temperature for a given location."
)
TOOL_SCHEMA = {
    "type": "object",
    "properties": {
        "lat": {"type": "number", "description": "Latitude of the location"},
        "lon": {"type": "number", "description": "Longitude of the location"},
        "layer": {
            "type": "string",
            "description": "Map layer type",
            "enum": ["precipitation_new", "temp_new", "wind_new", "clouds_new"],
            "default": "precipitation_new",
        },
        "zoom": {
            "type": "integer",
            "description": "Zoom level (1-10)",
            "default": 5,
            "minimum": 1,
            "maximum": 10,
        },
    },
    "required": ["lat", "lon"],
}


async def handle(
    lat: float,
    lon: float,
    layer: str = "precipitation_new",
    zoom: int = 5,
) -> dict:
    settings = get_settings()
    api_key = settings.openweather_api_key

    # Convert lat/lon to tile coordinates
    import math

    x = int((lon + 180) / 360 * (2**zoom))
    y = int(
        (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi)
        / 2
        * (2**zoom)
    )

    if not api_key or api_key == "your_openweathermap_key_here":
        map_url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
        note = "Configure OPENWEATHER_API_KEY for weather overlay tiles."
    else:
        map_url = (
            f"https://tile.openweathermap.org/map/{layer}/{zoom}/{x}/{y}.png"
            f"?appid={api_key}"
        )
        note = None

    result = {
        "map_url": map_url,
        "layer": layer,
        "zoom": zoom,
        "tile": {"x": x, "y": y},
        "coordinates": {"lat": lat, "lon": lon},
    }
    if note:
        result["note"] = note
    return result
