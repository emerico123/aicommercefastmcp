"""
FastMCP Echo + Exchange + Weather Server
"""

import os
import httpx
from typing import List, Optional
from fastmcp import FastMCP
from supabase import create_client, Client

# ------------------------
# Load Environment Variables
# ------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# ------------------------
# Validate Supabase Credentials
# ------------------------
if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY in environment variables.")

# ------------------------
# Initialize FastMCP and Supabase
# ------------------------
mcp = FastMCP("Echo + Exchange + Weather Server")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------
# Product Info Tool
# ------------------------

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
            data = await response.json()

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
            data = await response.json()

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
