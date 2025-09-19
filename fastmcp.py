"""
FastMCP Cloud: Echo + Exchange + Weather + Product Info Server
"""

import os
import httpx
from typing import List, Optional
from fastmcp import FastMCP
from supabase import create_client, Client

# ------------------------
# Initialize FastMCP
# ------------------------
mcp = FastMCP("Echo + Exchange + Weather Server")

# ------------------------
# Supabase Configuration (From FastMCP Cloud Env Vars)
# ------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ------------------------
# Product Info Tool
# ------------------------

@mcp.tool
async def get_product_info(user_id: str, name: Optional[str] = None) -> List[dict]:
    """
    Fetch product information (with images and videos) for a specific user.
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
                images = [m["path"] for m in media_response.data if m["type"] == 0]
                videos = [m["path"] for m in media_response.data if m["type"] == 1]
            except Exception:
                images, videos = [], []

            results.append({
                "name": product["name"],
                "description": product.get("description", "No description"),
                "price": product.get("price", "N/A"),
                "images": images,
                "videos": videos
            })

        return results

    except Exception as e:
        return [{"error": f"Error retrieving product info: {str(e)}"}]

# ------------------------
# Currency Exchange Tool
# ------------------------

FRANKFURTER_URL = "https://api.frankfurter.app/latest"

@mcp.tool
async def get_exchange_rate(source_currency: str, destination_currency: str, amount: float = 1.0) -> dict:
    """
    Convert amount from one currency to another using Frankfurter API.
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
                return {"error": "Invalid or unsupported currency code."}

            return {
                "from": source_currency.upper(),
                "to": destination_currency.upper(),
                "amount": amount,
                "rate": rate,
                "converted": round(rate * amount, 4),
                "date": data.get("date")
            }

        except Exception as e:
            return {"error": f"Currency conversion failed: {e}"}

# ------------------------
# Weather Tool
# ------------------------

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

@mcp.tool
async def get_weather(latitude: float, longitude: float) -> dict:
    """
    Get current weather for a given latitude and longitude.
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

            weather = data["current_weather"]
            return {
                "temperature": weather.get("temperature"),
                "windspeed": weather.get("windspeed"),
                "winddirection": weather.get("winddirection"),
                "weathercode": weather.get("weathercode"),
                "time": weather.get("time")
            }

        except Exception as e:
            return {"error": f"Weather fetch failed: {e}"}
