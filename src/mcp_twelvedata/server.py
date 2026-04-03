import os
from typing import Any
from dotenv import load_dotenv
from fastmcp import FastMCP
from twelvedata import TDClient

# Load environment variables from .env file
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("TwelveData")

# Initialize TwelveData client
# Note: The API key is retrieved from the TWELVE_DATA_API_KEY environment variable
api_key = os.getenv("TWELVE_DATA_API_KEY")

def get_client() -> TDClient:
    """Helper to initialize the TwelveData client."""
    if not api_key:
        raise ValueError("TWELVE_DATA_API_KEY environment variable is not set")
    return TDClient(apikey=api_key)

@mcp.tool()
def get_price(symbol: str) -> dict[str, Any]:
    """
    Get the real-time price of a financial instrument.
    
    Args:
        symbol: The ticker symbol (e.g., "AAPL", "BTC/USD", "EUR/USD").
    """
    td = get_client()
    try:
        # Fetch price and convert to JSON
        result = td.price(symbol=symbol).as_json()
        return result
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

def main():
    """Entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
