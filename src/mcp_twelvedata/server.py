import os
from typing import Any, Optional
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

@mcp.tool()
def get_quote(symbol: str) -> dict[str, Any]:
    """
    Get detailed quote information for a financial instrument.
    
    Args:
        symbol: The ticker symbol (e.g., "AAPL", "BTC/USD", "EUR/USD").
    """
    td = get_client()
    try:
        result = td.quote(symbol=symbol).as_json()
        return result
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

@mcp.tool()
def get_time_series(
    symbol: str,
    interval: str = "1day",
    outputsize: int = 100,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> dict[str, Any]:
    """
    Get historical time series data (OHLCV) for a financial instrument.

    Args:
        symbol: The ticker symbol (e.g., "AAPL", "BTC/USD", "EUR/USD").
        interval: The data interval (e.g., "1min", "5min", "1h", "1day", "1week", "1month"). 
                  Defaults to "1day".
        outputsize: The number of data points to retrieve. Max 5000. Defaults to 100.
        start_date: The start date for historical data in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' format.
        end_date: The end date for historical data in 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM:SS' format.
                  Defaults to current date if not specified.

    Note: Free tier has limits on outputsize and may incur more API credits for larger requests.
    """
    td = get_client()
    try:
        # Ensure outputsize does not exceed the typical free tier limit for a single request
        # Although the API supports up to 5000, smaller requests are safer for free tier.
        # We will cap it at 5000 as per the library's default, but advise caution.
        if outputsize > 5000:
            outputsize = 5000
            
        result = td.time_series(
            symbol=symbol,
            interval=interval,
            outputsize=outputsize,
            start_date=start_date,
            end_date=end_date
        ).as_json()
        return result
    except Exception as e:
        return {"error": str(e), "symbol": symbol, "interval": interval, "outputsize": outputsize}

def main():
    """Entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
