#!/usr/bin/env python3
"""Weather MCP server wrapping Open-Meteo (free, no API key).

Defaults to Scott's saved location: Temple, GA (lat 33.7353, lon -85.0308),
matching projects/dashboard/data_fetcher.py. Two tools: current conditions and
a multi-day forecast for any lat/lon.
"""
from __future__ import annotations

import httpx
from typing import Annotated
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("weather_mcp")

API_BASE = "https://api.open-meteo.com/v1/forecast"
DEFAULT_LAT = 33.7353
DEFAULT_LON = -85.0308
DEFAULT_TZ = "America/New_York"
DEFAULT_NAME = "Temple, GA"

WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def c_to_f(c: float | None) -> str:
    return "N/A" if c in (None, "N/A") else f"{round(c * 9 / 5 + 32)}°F"


async def fetch_open_meteo(
    lat: float,
    lon: float,
    tz: str = DEFAULT_TZ,
    hourly: str | None = None,
    daily: str | None = None,
    forecast_days: int | None = None,
) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": (
            "temperature_2m,relative_humidity_2m,apparent_temperature,"
            "weather_code,wind_speed_10m,wind_direction_10m,pressure_msl"
        ),
        "timezone": tz,
    }
    if hourly:
        params["hourly"] = hourly
    if daily:
        params["daily"] = daily
    if forecast_days:
        params["forecast_days"] = forecast_days
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(API_BASE, params=params)
        r.raise_for_status()
        return r.json()


async def geocode(name: str) -> tuple[float, float]:
    url = "https://api.open-meteo.com/v1/search"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, params={"name": name, "count": 1})
        r.raise_for_status()
        results = r.json().get("results") or []
        if not results:
            raise ValueError(f"Location '{name}' not found.")
    return float(results[0]["latitude"]), float(results[0]["longitude"])


class LocationInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Annotated[
        str,
        Field(
            description=(
                "City/place name to look up (e.g. 'Austin TX', 'Temple GA'). "
                 "Leave empty or pass empty string to use Scott's default home in Temple, GA."
              ),
           )
      ] = ""


class ForecastInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    name: Annotated[str, Field(description="City/place name. Empty uses Scott's default home (Temple, GA).")] = ""
    days: Annotated[int, Field(description="Number of forecast days starting today (1-16).", ge=1, le=16)] = 5


@mcp.tool()
async def weather_current(location: LocationInput) -> dict:
    """Get current weather conditions for a place.

    Free via Open-Meteo (no API key). Defaults to Scott's home in Temple, GA.
    Returns temperature (°F), feels-like, condition, humidity, wind, and whether
    it is currently raining/snowing — good for "should I bring an umbrella?".
    """
    if not location.name:
        lat, lon = DEFAULT_LAT, DEFAULT_LON
    else:
        lat, lon = await geocode(location.name)

    data = await fetch_open_meteo(lat, lon)
    cur = data.get("current", {})
    code = cur.get("weather_code")
    return {
        "location": location.name or DEFAULT_NAME,
        "temperature_f": c_to_f(cur.get("temperature_2m")),
        "feels_like_f": c_to_f(cur.get("apparent_temperature")),
        "condition": WMO_CODES.get(code, f"Unknown ({code})"),
        "humidity_pct": cur.get("relative_humidity_2m"),
        "wind_mph": round(
            (cur.get("wind_speed_10m") or 0) * 0.621371, 1
        ),
        "pressure_hpa": cur.get("pressure_msl"),
    }


@mcp.tool()
async def weather_forecast(location: ForecastInput) -> list[dict]:
    """Get a multi-day high/low forecast for a place.

    Free via Open-Meteo (no API key). Defaults to Scott's home in Temple, GA.
    Returns one entry per day: date, high/low (°F), condition, and rainfall mm.
    """
    if not location.name:
        lat, lon = DEFAULT_LAT, DEFAULT_LON
    else:
        lat, lon = await geocode(location.name)

    data = await fetch_open_meteo(
        lat,
        lon,
        daily="temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
        forecast_days=location.days,
    )
    d = data.get("daily", {})
    times = d.get("time", [])
    out = []
    for i, day in enumerate(times):
        code = d["weather_code"][i] if "weather_code" in d else -1
        out.append(
            {
                "date": day,
                "high_f": c_to_f(d.get("temperature_2m_max", [None])[i]),
                "low_f": c_to_f(d.get("temperature_2m_min", [None])[i]),
                "condition": WMO_CODES.get(code, f"Unknown ({code})"),
                "precip_mm": d.get("precipitation_sum", [None])[i],
            }
        )
    return out


if __name__ == "__main__":
    mcp.run()
