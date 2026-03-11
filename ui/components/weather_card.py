"""Format weather data as an HTML card."""

from __future__ import annotations


def format_weather_card(weather: dict) -> str:
    city = weather.get("city", "Unknown")
    country = weather.get("country", "")
    temp = weather.get("temperature", "N/A")
    feels = weather.get("feels_like", "N/A")
    humidity = weather.get("humidity", "N/A")
    wind = weather.get("wind_speed", "N/A")
    desc = weather.get("description", "N/A").title()
    unit = weather.get("unit_symbol", "C")
    is_mock = weather.get("_mock", False)

    mock_badge = '<span style="background:#ff9800; color:#fff; padding:2px 6px; border-radius:4px; font-size:11px;">MOCK DATA</span>' if is_mock else ""

    return f"""
<div style="border:1px solid #e0e0e0; border-radius:8px; padding:16px; margin:8px 0; background:linear-gradient(135deg,#e3f2fd,#fafafa);">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <h3 style="margin:0;">{city}, {country} {mock_badge}</h3>
    <span style="font-size:32px; font-weight:bold; color:#1a73e8;">{temp}&deg;{unit}</span>
  </div>
  <p style="color:#555; margin:6px 0 0 0;">{desc}</p>
  <div style="display:flex; gap:16px; margin-top:8px; font-size:13px; color:#666;">
    <span>Feels like: {feels}&deg;{unit}</span>
    <span>Humidity: {humidity}%</span>
    <span>Wind: {wind} m/s</span>
  </div>
</div>
"""
