import os
from typing import Any

from dotenv import load_dotenv
from fastmcp import FastMCP
from twelvedata import TDClient
from twelvedata.exceptions import (
    BadRequestError,
    InvalidApiKeyError,
    TwelveDataError,
)

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
    except TwelveDataError:
        # Re-raise to be handled by the caller
        raise
    except Exception as e:
        # Catch other initialization errors
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
    except ValueError as e:  # Handles API key/init errors
        return {"error": str(e)}
    except BadRequestError as e:
        return {"error": f"Bad request for {symbol}: {e}"}
    except InvalidApiKeyError:
        return {"error": "Invalid API key provided."}
    except TwelveDataError as e:
        # Generic catch for other TwelveData errors including rate limits
        if "rate limit" in str(e).lower():
            return {
                "error": "Rate limit exceeded. Please check your API usage.",
                "code": 429,
            }
        return {"error": str(e), "symbol": symbol}
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
    except BadRequestError as e:
        return {"error": f"Bad request for {symbol}: {e}"}
    except TwelveDataError as e:
        if "rate limit" in str(e).lower():
            return {
                "error": "Rate limit exceeded. Please check your API usage.",
                "code": 429,
            }
        return {"error": str(e), "symbol": symbol}
    except Exception as e:
        return {"error": str(e), "symbol": symbol}


@mcp.tool()
def get_time_series(
    symbol: str,
    interval: str = "1day",
    outputsize: int = 100,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """
    Get historical time series data (OHLCV) for a financial instrument.

    Args:
        symbol: The ticker symbol (e.g., "AAPL", "BTC/USD", "EUR/USD").
        interval: The data interval (e.g., "1min", "5min", "1h", "1day", "1week").
                  Defaults to "1day".
        outputsize: The number of data points to retrieve. Max 5000. Defaults to 100.
        start_date: The start date for historical data in 'YYYY-MM-DD' format.
        end_date: The end date for historical data in 'YYYY-MM-DD' format.
                  Defaults to current date if not specified.

    Note: Free tier has limits on outputsize.
    """
    td = get_client()
    try:
        # Ensure outputsize does not exceed the maximum supported by the API
        max_outputsize = 5000
        if outputsize > max_outputsize:
            outputsize = max_outputsize

        result = td.time_series(
            symbol=symbol,
            interval=interval,
            outputsize=outputsize,
            start_date=start_date,
            end_date=end_date,
        ).as_json()
        return result
    except ValueError as e:
        return {"error": str(e)}
    except BadRequestError as e:
        return {"error": f"Bad request for {symbol}: {e}"}
    except TwelveDataError as e:
        if "rate limit" in str(e).lower():
            return {
                "error": "Rate limit exceeded. Please check your API usage.",
                "code": 429,
            }
        return {
            "error": str(e),
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
        }
    except Exception as e:
        return {
            "error": str(e),
            "symbol": symbol,
            "interval": interval,
            "outputsize": outputsize,
        }


# Mapping of common indicator names to TwelveData's with_ methods
# Parameters are specified as tuples of (parameter_name, default_value, type_hint)
INDICATOR_MAP: dict[str, dict[str, Any]] = {
    "rsi": {
        "method": "with_rsi",
        "params": [("time_period", 14, int), ("series", "close", str)],
    },
    "macd": {
        "method": "with_macd",
        "params": [
            ("slow_period", 26, int),
            ("fast_period", 12, int),
            ("signal_period", 9, int),
            ("series", "close", str),
        ],
    },
    "sma": {
        "method": "with_sma",
        "params": [("time_period", 20, int), ("series", "close", str)],
    },
    "ema": {
        "method": "with_ema",
        "params": [("time_period", 20, int), ("series", "close", str)],
    },
    "bbands": {
        "method": "with_bbands",
        "params": [
            ("time_period", 20, int),
            ("nb_std", 2, int),
            ("series", "close", str),
        ],
    },
    "stoch": {
        "method": "with_stoch",
        "params": [
            ("time_period", 14, int),
            ("k_period", 3, int),
            ("d_period", 3, int),
        ],
    },
    "adx": {"method": "with_adx", "params": [("time_period", 14, int)]},
    "cci": {"method": "with_cci", "params": [("time_period", 20, int)]},
    "roc": {"method": "with_roc", "params": [("time_period", 14, int)]},
    "rsi_ema": {
        "method": "with_rsi_ema",
        "params": [
            ("time_period", 14, int),
            ("ema_period", 14, int),
            ("series", "close", str),
        ],
    },
}


@mcp.tool()
def get_technical_indicator(
    symbol: str,
    indicator_name: str,
    interval: str = "1day",
    outputsize: int = 100,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate a specific technical indicator for a financial instrument.

    Args:
        symbol: The ticker symbol (e.g., "AAPL", "BTC/USD").
        indicator_name: The name of the technical indicator (e.g., "rsi", "macd").
        interval: The data interval (e.g., "1h", "1day"). Defaults to "1day".
        outputsize: Number of data points to retrieve. Max 5000. Defaults to 100.
        params: Additional parameters for the indicator (e.g., {"time_period": 14}).
    """
    if params is None:
        params = {}
    td = get_client()
    indicator_config = INDICATOR_MAP.get(indicator_name.lower())

    if not indicator_config:
        supported_indicators = sorted(INDICATOR_MAP.keys())
        return {
            "error": f"Indicator '{indicator_name}' is not supported. "
            f"Supported indicators: {supported_indicators}"
        }

    method_name = indicator_config["method"]
    default_params_info = indicator_config["params"]

    indicator_call_params = {}
    for param_name, default_value, _ in default_params_info:
        indicator_call_params[param_name] = params.get(param_name, default_value)

    try:
        ts_data = td.time_series(
            symbol=symbol,
            interval=interval,
            outputsize=outputsize,
            start_date=params.get("start_date"),
            end_date=params.get("end_date"),
        )

        indicator_method = getattr(ts_data, method_name)
        configured_ts_data = indicator_method(**indicator_call_params)

        result = configured_ts_data.as_json()
        return result

    except ValueError as e:
        return {"error": str(e)}
    except BadRequestError as e:
        return {"error": f"Bad request for {symbol}: {e}"}
    except TwelveDataError as e:
        if "rate limit" in str(e).lower():
            return {
                "error": "Rate limit exceeded. Please check your API usage.",
                "code": 429,
            }
        return {"error": str(e), "symbol": symbol}
    except AttributeError:
        return {"error": f"Internal error: Method '{method_name}' not found."}
    except Exception as e:
        return {
            "error": str(e),
            "symbol": symbol,
            "indicator": indicator_name,
            "interval": interval,
            "outputsize": outputsize,
        }


@mcp.tool()
def list_stocks(country: str = "USA") -> list[dict[str, Any]]:
    """
    List available stock symbols.

    Args:
        country: The country to list stocks from. Defaults to "USA".
    """
    td = get_client()
    try:
        result = td.get_stocks_list(country=country).as_json()
        symbols_list = result.get("symbols", result.get("data", []))
        return symbols_list if isinstance(symbols_list, list) else []
    except ValueError as e:
        return [{"error": str(e)}]
    except TwelveDataError as e:
        if "rate limit" in str(e).lower():
            return [{"error": "Rate limit exceeded.", "code": 429}]
        return [{"error": str(e)}]
    except Exception as e:
        return [{"error": str(e), "country": country}]


@mcp.tool()
def list_forex() -> list[dict[str, Any]]:
    """
    List available forex symbols.
    """
    td = get_client()
    try:
        result = td.get_forex_pairs_list().as_json()
        symbols_list = result.get("symbols", result.get("data", []))
        return symbols_list if isinstance(symbols_list, list) else []
    except ValueError as e:
        return [{"error": str(e)}]
    except TwelveDataError as e:
        if "rate limit" in str(e).lower():
            return [{"error": "Rate limit exceeded.", "code": 429}]
        return [{"error": str(e)}]
    except Exception as e:
        return [{"error": str(e)}]


@mcp.tool()
def list_cryptocurrencies() -> list[dict[str, Any]]:
    """
    List available cryptocurrency symbols.
    """
    td = get_client()
    try:
        result = td.get_cryptocurrencies_list().as_json()
        symbols_list = result.get("symbols", result.get("data", []))
        return symbols_list if isinstance(symbols_list, list) else []
    except ValueError as e:
        return [{"error": str(e)}]
    except TwelveDataError as e:
        if "rate limit" in str(e).lower():
            return [{"error": "Rate limit exceeded.", "code": 429}]
        return [{"error": str(e)}]
    except Exception as e:
        return [{"error": str(e)}]


def main():
    """Entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
