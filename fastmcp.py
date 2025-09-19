"""
FastMCP Cloud: Product Info Server
"""

import os
import httpx
from typing import List, Optional
from fastmcp import FastMCP
from supabase import create_client, Client

# ------------------------
# Initialize FastMCP
# ------------------------
mcp = FastMCP("Product Info Server")

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
