import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("exchange_rate")

BASE_URL = "https://api.frankfurter.app/latest"

@mcp.tool()
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
            response = await client.get(BASE_URL, params=params, timeout=10)
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

if __name__ == "__main__":
    mcp.run(transport="stdio")
