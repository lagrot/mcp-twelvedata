import os
from typing import Any, Optional, Dict, List
from dotenv import load_dotenv
from fastmcp import FastMCP
from twelvedata import TDClient
from twelvedata.errors import InvalidSymbolError, InvalidIntervalError, RateLimitExceededError

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
    try:
        td = TDClient(apikey=api_key)
        # Ping to check API key validity and connection early
        td.api_usage() 
        return td
    except RateLimitExceededError:
        return {"error": "Rate limit exceeded. Please check your API usage.", "code": 429}
    except Exception as e:
        raise ValueError(f"Failed to initialize TwelveData client: {e}") from e


@mcp.tool()
def get_price(symbol: str) -> dict[str, Any]:
    """
    Get the real-time price of a financial instrument.
    
    Args:
        symbol: The ticker symbol (e.g., "AAPL", "BTC/USD", "EUR/USD").
    """
    try:
        td = get_client()
        # Fetch price and convert to JSON
        result = td.price(symbol=symbol).as_json()
        return result
    except ValueError as e: # Handles API key/init errors
        return {"error": str(e)}
    except InvalidSymbolError:
        return {"error": f"Invalid symbol: {symbol}"}
    except RateLimitExceededError:
        return {"error": "Rate limit exceeded. Please check your API usage.", "code": 429}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}

@mcp.tool()
def get_quote(symbol: str) -> dict[str, Any]:
    """
    Get detailed quote information for a financial instrument.
    
    Args:
        symbol: The ticker symbol (e.g., "AAPL", "BTC/USD", "EUR/USD").
    """
    try:
        td = get_client()
        result = td.quote(symbol=symbol).as_json()
        return result
    except ValueError as e:
        return {"error": str(e)}
    except InvalidSymbolError:
        return {"error": f"Invalid symbol: {symbol}"}
    except RateLimitExceededError:
        return {"error": "Rate limit exceeded. Please check your API usage.", "code": 429}
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
    except ValueError as e:
        return {"error": str(e)}
    except InvalidSymbolError:
        return {"error": f"Invalid symbol: {symbol}"}
    except InvalidIntervalError:
        return {"error": f"Invalid interval: {interval}"}
    except RateLimitExceededError:
        return {"error": "Rate limit exceeded. Please check your API usage.", "code": 429}
    except Exception as e:
        return {"error": str(e), "symbol": symbol, "interval": interval, "outputsize": outputsize}

# Mapping of common indicator names to TwelveData's with_ methods and their parameters
# This allows dynamic calling of indicator methods.
# Parameters are specified as tuples of (parameter_name, default_value, type_hint)
INDICATOR_MAP: Dict[str, Dict[str, Any]] = {
    "rsi": {"method": "with_rsi", "params": [("time_period", 14, int), ("series", "close", str)]},
    "macd": {"method": "with_macd", "params": [("slow_period", 26, int), ("fast_period", 12, int), ("signal_period", 9, int), ("series", "close", str)]},
    "sma": {"method": "with_sma", "params": [("time_period", 20, int), ("series", "close", str)]},
    "ema": {"method": "with_ema", "params": [("time_period", 20, int), ("series", "close", str)]},
    "bbands": {"method": "with_bbands", "params": [("time_period", 20, int), ("nb_std", 2, int), ("series", "close", str)]},
    # Add more indicators as needed
}

@mcp.tool()
def get_technical_indicator(
    symbol: str,
    indicator_name: str,
    interval: str = "1day",
    outputsize: int = 100,
    **kwargs: Any # Allows passing indicator-specific parameters like time_period, series, etc.
) -> dict[str, Any]:
    """
    Calculate a specific technical indicator for a financial instrument.

    Args:
        symbol: The ticker symbol (e.g., "AAPL", "BTC/USD").
        indicator_name: The name of the technical indicator (e.g., "rsi", "macd", "sma", "ema", "bbands").
        interval: The data interval (e.g., "1min", "5min", "1h", "1day", "1week", "1month"). Defaults to "1day".
        outputsize: The number of data points to retrieve for the indicator calculation. Max 5000. Defaults to 100.
        **kwargs: Additional parameters for the indicator, such as 'time_period', 'series', etc.
                  Consult TwelveData documentation for specific indicator parameters.

    Note: Free tier may have limitations on available indicators or credit usage.
    """
    td = get_client()
    indicator_config = INDICATOR_MAP.get(indicator_name.lower())

    if not indicator_config:
        return {"error": f"Indicator '{indicator_name}' is not supported or recognized. Supported indicators: {list(INDICATOR_MAP.keys())}"}

    method_name = indicator_config["method"]
    default_params = indicator_config["params"]
    
    # Prepare parameters for the time_series call and the indicator method call
    indicator_call_params = {}
    # Add parameters from kwargs first, then use defaults if not provided in kwargs
    for param_name, default_value, _ in default_params:
        indicator_call_params[param_name] = kwargs.get(param_name, default_value)

    try:
        # Get base time series data
        ts_data = td.time_series(
            symbol=symbol,
            interval=interval,
            outputsize=outputsize,
            # Start/end dates are generally not directly passed to indicator calls, 
            # but are implicitly handled by time_series outputsize and interval.
        )

        # Dynamically call the indicator method using getattr
        indicator_method = getattr(ts_data, method_name)
        
        # Call the indicator method with prepared parameters
        # Filter out kwargs that are not expected by the specific indicator method if necessary,
        # though get() with default values handles this.
        configured_ts_data = indicator_method(**indicator_call_params)
        
        result = configured_ts_data.as_json()
        return result
        
    except ValueError as e:
        return {"error": str(e)}
    except InvalidSymbolError:
        return {"error": f"Invalid symbol: {symbol}"}
    except InvalidIntervalError:
        return {"error": f"Invalid interval: {interval}"}
    except RateLimitExceededError:
        return {"error": "Rate limit exceeded. Please check your API usage.", "code": 429}
    except AttributeError: # Catch if method_name is not found on the object (should be caught by INDICATOR_MAP check, but for safety)
        return {"error": f"Internal error: Indicator method '{method_name}' not found for '{indicator_name}'."}
    except Exception as e:
        return {"error": str(e), "symbol": symbol, "indicator": indicator_name, "interval": interval, "outputsize": outputsize}


@mcp.tool()
def list_stocks(country: str = "USA") -> List[Dict[str, Any]]:
    """
    List available stock symbols.

    Args:
        country: The country to list stocks from (e.g., "USA", "Canada"). 
                 Defaults to "USA". Free tier primarily supports US stocks.
    """
    td = get_client()
    try:
        result = td.stocks(country=country).as_json()
        # The API might return a structure like {"symbols": [...]}
        return result.get("symbols", []) 
    except ValueError as e:
        return {"error": str(e)}
    except RateLimitExceededError:
        return {"error": "Rate limit exceeded. Please check your API usage.", "code": 429}
    except Exception as e:
        return {"error": str(e), "country": country}

@mcp.tool()
def list_forex() -> List[Dict[str, Any]]:
    """
    List available forex symbols.
    """
    td = get_client()
    try:
        result = td.forex().as_json()
        return result.get("symbols", [])
    except ValueError as e:
        return {"error": str(e)}
    except RateLimitExceededError:
        return {"error": "Rate limit exceeded. Please check your API usage.", "code": 429}
    except Exception as e:
        return {"error": str(e)}

@mcp.tool()
def list_cryptocurrencies() -> List[Dict[str, Any]]:
    """
    List available cryptocurrency symbols.
    """
    td = get_client()
    try:
        result = td.cryptocurrencies().as_json()
        return result.get("symbols", [])
    except ValueError as e:
        return {"error": str(e)}
    except RateLimitExceededError:
        return {"error": "Rate limit exceeded. Please check your API usage.", "code": 429}
    except Exception as e:
        return {"error": str(e)}

def main():
    """Entry point for the MCP server."""
    mcp.run()

if __name__ == "__main__":
    main()
