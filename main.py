"""
FastMCP Echo + Exchange + Weather Server
"""

import httpx
from fastmcp import FastMCP
from supabase import create_client

# Create server
mcp = FastMCP("Echo + Exchange + Weather Server")


# ------------------------
# Echo Tools
# ------------------------

@mcp.tool
def echo_tool(text: str) -> str:
    """Echo the input text"""
    return text


@mcp.resource("echo://static")
def echo_resource() -> str:
    return "Echo!"


@mcp.resource("echo://{text}")
def echo_template(text: str) -> str:
    """Echo the input text"""
    return f"Echo: {text}"


@mcp.prompt("echo")
def echo_prompt(text: str) -> str:
    return text


# ------------------------
# Exchange Rate Tool
# ------------------------

FRANKFURTER_URL = "https://api.frankfurter.app/latest"

@mcp.tool
async def get_exchange_rate(source_currency: str, destination_currency: str, amount: float = 1.0) -> dict:
    """
    Convert amount from source_currency to destination_currency using Frankfurter API.
    """
    params = {
        "from": source_currency.upper(),
        "to": destination_currency.upper()
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(FRANKFURTER_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            rate = data["rates"].get(destination_currency.upper())
            if rate is None:
                return {"error": "Invalid currency code or unsupported conversion."}

            converted = round(rate * amount, 4)

            return {
                "from": source_currency.upper(),
                "to": destination_currency.upper(),
                "amount": amount,
                "rate": rate,
                "converted": converted,
                "date": data.get("date")
            }

        except Exception as e:
            return {"error": f"API request failed: {e}"}


# ------------------------
# Weather Tool (Open-Meteo)
# ------------------------

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

@mcp.tool
async def get_weather(latitude: float, longitude: float) -> dict:
    """
    Get current weather for a given latitude and longitude using Open-Meteo API.
    """
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current_weather": True
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPEN_METEO_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "current_weather" not in data:
                return {"error": "No weather data available."}

            current = data["current_weather"]

            return {
                "temperature": current.get("temperature"),
                "windspeed": current.get("windspeed"),
                "winddirection": current.get("winddirection"),
                "weathercode": current.get("weathercode"),
                "time": current.get("time")
            }

        except Exception as e:
            return {"error": f"Failed to fetch weather: {e}"}
