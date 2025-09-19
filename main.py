"""
FastMCP Echo + Exchange + Weather Server
"""
from typing import Optional, Union, List
import httpx
from fastmcp import FastMCP
from supabase import create_client
from fastmcp import Client
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


SUPABASE_URL = "https://wanmahanxxzwpopilhrl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indhbm1haGFueHh6d3BvcGlsaHJsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc0OTMzMDksImV4cCI6MjA3MzA2OTMwOX0.fyX3pVNXWzKlMFmRwyABq-r4FtwDkC4oqBNr2C21qPg"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@mcp.tool
async def get_product_info(user_id: str, name: Optional[str] = None) -> List[dict]:
    """
    Fetch product information (with images and videos) for a specific user.

    Args:
        user_id (str): ID of the user/merchant to filter their products.
        name (Optional[str]): Optional name filter for the product (case-insensitive).

    Returns:
        List[dict]: List of product info dicts with name, description, price, images, and videos.
    """
    try:
        query = supabase.table("products").select("*").eq("user_id", user_id)

        if name:
            query = query.ilike("name", f"%{name}%")

        products_response = query.execute()

        if not products_response.data:
            return []

        results = []
        for product in products_response.data:
            product_id = product["id"]

            try:
                media_response = supabase.table("product_media") \
                    .select("path, type") \
                    .eq("product_id", product_id) \
                    .execute()

                images = []
                videos = []
                if media_response.data:
                    for media in media_response.data:
                        if media["type"] == 0:
                            images.append(media["path"])
                        elif media["type"] == 1:
                            videos.append(media["path"])
            except Exception as media_err:
                print(f"Error retrieving media for product {product_id}: {media_err}")
                images = []
                videos = []

            product_info = {
                "name": product["name"],
                "description": product.get("description", "No description"),
                "price": product.get("price", "N/A"),
                "images": images,
                "videos": videos
            }
            results.append(product_info)

        return results

    except Exception as e:
        print(f"Error retrieving product info: {e}")
        return []
