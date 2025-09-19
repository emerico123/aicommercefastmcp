import asyncio
from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("weather")

# Base URL for Open‑Meteo API
OPENMETEO_API_BASE = "https://api.open-meteo.com/v1/forecast"

async def fetch_weather(lat: float, lon: float) -> dict[str, Any] | None:
    """
    Fetch current weather data using Open-Meteo API.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True
    }
    headers = {
        "User-Agent": "weather-mcp/1.0",
        "Accept": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPENMETEO_API_BASE, params=params, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to fetch weather: {e}"}

@mcp.tool()
async def get_weather(lat: float, lon: float) -> dict[str, Any]:
    """
    Tool: Given latitude and longitude, return current weather data.
    """
    result = await fetch_weather(lat, lon)
    if result is None or "current_weather" not in result:
        return {"error": "No weather data available."}
    cw = result["current_weather"]
    return {
        "temperature": cw.get("temperature"),
        "windspeed": cw.get("windspeed"),
        "winddirection": cw.get("winddirection"),
        "weathercode": cw.get("weathercode")
    }

if __name__ == "__main__":
    # Run the MCP server via stdio (or choose transport='sse' if preferred)
    mcp.run(transport="stdio")
