from typing import Any
import httpx
import logging

from mcp.server.fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware

# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"

# Initialize FastMCP server
mcp = FastMCP("weather")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def make_nws_request(url: str) -> dict[str, Any] | None:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"NWS request failed: {e}")
            return None


def format_alert(feature: dict) -> str:
    props = feature["properties"]
    return f"""
Event: {props.get("event", "Unknown")}
Area: {props.get("areaDesc", "Unknown")}
Severity: {props.get("severity", "Unknown")}
Description: {props.get("description", "No description available")}
Instructions: {props.get("instruction", "No specific instructions provided")}
"""


@mcp.tool()
async def get_alerts(state: str) -> str:
    """Get weather alerts for a US state."""
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    if not data or "features" not in data:
        return "Unable to fetch alerts or no alerts found."
    return "\n---\n".join([format_alert(f) for f in data["features"]])


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location."""
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    f_data = await make_nws_request(points_url)
    if not f_data or "properties" not in f_data:
        return "Unable to fetch forecast data."
    periods = f_data["properties"]["periods"][:5]
    forecasts = []
    for p in periods:
        forecasts.append(
            f"{p['name']}:\n"
            f"Temperature: {p['temperature']}°{p['temperatureUnit']}\n"
            f"Wind: {p['windSpeed']} {p['windDirection']}\n"
            f"Forecast: {p['detailedForecast']}"
        )
    return "\n---\n".join(forecasts)


if __name__ == "__main__":
    # Get the Starlette app
    app = mcp.streamable_http_app()

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Run with uvicorn
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000, access_log=True)