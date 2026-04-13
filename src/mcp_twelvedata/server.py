import logging
import os
import sys
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("mcp-twelvedata")

# Initialize FastMCP server
mcp = FastMCP("TwelveData")


def get_client() -> TDClient:
    """Helper to initialize the TwelveData client."""
    key = os.getenv("TWELVE_DATA_API_KEY")
    if not key:
        logger.error("TWELVE_DATA_API_KEY not found in environment")
        raise ValueError("TWELVE_DATA_API_KEY environment variable is not set")
    try:
        td = TDClient(apikey=key)
        return td
    except Exception as e:
        logger.exception("Failed to initialize TwelveData client")
        raise ValueError(f"Failed to initialize TwelveData client: {e}") from e


def verify_api_key() -> bool:
    """Verify the API key on startup to ensure fail-fast behavior."""
    logger.info("Verifying TwelveData API key...")
    try:
        td = get_client()
        # Use a lightweight call to check validity
        usage = td.api_usage().as_json()
        current = usage.get("current_usage", 0)
        limit = usage.get("plan_limit", "N/A")
        logger.info(f"API key verified. Usage: {current}/{limit}")
        return True
    except InvalidApiKeyError:
        logger.critical("CRITICAL: The provided TwelveData API key is invalid.")
        return False
    except TwelveDataError as e:
        if "rate limit" in str(e).lower():
            logger.warning("Startup check hit rate limit, but assuming key is valid.")
            return True
        logger.error(f"TwelveData verification error: {e}")
        return False
    except Exception as e:
        logger.exception(f"Unexpected verification failure: {e}")
        return False


def handle_api_error(e: Exception, symbol: str | None = None) -> dict[str, Any]:
    """Centralized error handling for TwelveData API calls."""
    if isinstance(e, BadRequestError):
        logger.warning(f"Bad request for symbol {symbol}: {e}")
        return {"error": f"Invalid request parameters: {e}", "symbol": symbol}
    if isinstance(e, InvalidApiKeyError):
        logger.error("Invalid API key")
        return {"error": "The provided TwelveData API key is invalid."}
    if isinstance(e, TwelveDataError):
        error_str = str(e).lower()
        if "rate limit" in error_str:
            logger.warning("Rate limit exceeded")
            return {
                "error": (
                    "TwelveData Rate Limit Exceeded (Free tier: 8 credits/min). "
                    "Please wait 60 seconds."
                ),
                "code": 429,
            }
        logger.error(f"TwelveData API error: {e}")
        return {"error": str(e), "symbol": symbol}

    logger.exception(f"Unexpected error for symbol {symbol}")
    return {"error": f"An unexpected error occurred: {e}", "symbol": symbol}


@mcp.tool()
def get_price(symbol: str) -> dict[str, Any]:
    """
    Get the real-time price of one or more financial instruments.

    Args:
        symbol: Single ticker or comma-separated list.
    """
    try:
        logger.info(f"Fetching price for {symbol}")
        td = get_client()
        result = td.price(symbol=symbol).as_json()
        return result
    except Exception as e:
        return handle_api_error(e, symbol)


@mcp.tool()
def get_quote(symbol: str) -> dict[str, Any]:
    """
    Get detailed quote information for a financial instrument.

    Args:
        symbol: The ticker symbol (e.g., "AAPL").
    """
    try:
        logger.info(f"Fetching quote for {symbol}")
        td = get_client()
        result = td.quote(symbol=symbol).as_json()
        return result
    except Exception as e:
        return handle_api_error(e, symbol)


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
    """
    try:
        logger.info(f"Fetching time series for {symbol} ({interval})")
        td = get_client()
        max_outputsize = 5000
        safe_outputsize = min(outputsize, max_outputsize)

        result = td.time_series(
            symbol=symbol,
            interval=interval,
            outputsize=safe_outputsize,
            start_date=start_date,
            end_date=end_date,
        ).as_json()
        return result
    except Exception as e:
        return handle_api_error(e, symbol)


@mcp.tool()
def get_correlation(
    symbol1: str,
    symbol2: str,
    interval: str = "1day",
    time_period: int = 20,
    outputsize: int = 10,
) -> dict[str, Any]:
    """
    Calculate the statistical correlation between two financial instruments.
    A value close to 1 implies positive correlation, -1 negative, and 0 no correlation.

    Args:
        symbol1: The first ticker symbol (e.g., "AAPL").
        symbol2: The second ticker symbol to compare against (e.g., "MSFT", "QQQ").
        interval: Data interval (e.g., "1day", "1h").
        time_period: Number of periods for correlation calculation. Defaults to 20.
        outputsize: Number of data points to return.
    """
    try:
        logger.info(f"Calculating correlation between {symbol1} and {symbol2}")
        td = get_client()
        # Correlation is a technical indicator that requires symbol and symbol2
        result = td.custom_endpoint(
            "correlation",
            symbol=symbol1,
            symbol2=symbol2,
            interval=interval,
            time_period=time_period,
            outputsize=outputsize,
        ).as_json()
        return result
    except Exception as e:
        return handle_api_error(e, f"{symbol1}/{symbol2}")


@mcp.tool()
def get_beta(
    symbol: str,
    interval: str = "1day",
    time_period: int = 20,
    outputsize: int = 10,
) -> dict[str, Any]:
    """
    Calculate the Beta of an instrument (usually vs the S&P 500).
    Beta measures volatility relative to the market.

    Args:
        symbol: The ticker symbol (e.g., "AAPL").
        interval: Data interval (e.g., "1day").
        time_period: Number of periods. Defaults to 20.
        outputsize: Number of data points to return.
    """
    try:
        logger.info(f"Calculating Beta for {symbol}")
        td = get_client()
        result = (
            td.time_series(symbol=symbol, interval=interval, outputsize=outputsize)
            .with_beta(time_period=time_period)
            .as_json()
        )
        return result
    except Exception as e:
        return handle_api_error(e, symbol)


@mcp.tool()
def get_rsi(
    symbol: str,
    interval: str = "1day",
    time_period: int = 14,
    series: str = "close",
    outputsize: int = 100,
) -> dict[str, Any]:
    """
    Calculate the Relative Strength Index (RSI) for a financial instrument.

    Args:
        symbol: The ticker symbol (e.g., "AAPL").
        interval: The data interval (e.g., "1day", "1h").
        time_period: The number of periods to use for calculation. Defaults to 14.
        series: Price type ("open", "high", "low", "close"). Defaults to "close".
        outputsize: Number of data points to return. Max 5000.
    """
    try:
        logger.info(f"Calculating RSI for {symbol}")
        td = get_client()
        result = (
            td.time_series(symbol=symbol, interval=interval, outputsize=outputsize)
            .with_rsi(time_period=time_period, series=series)
            .as_json()
        )
        return result
    except Exception as e:
        return handle_api_error(e, symbol)


@mcp.tool()
def get_macd(
    symbol: str,
    interval: str = "1day",
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    series: str = "close",
    outputsize: int = 100,
) -> dict[str, Any]:
    """
    Calculate Moving Average Convergence Divergence (MACD) for a financial instrument.

    Args:
        symbol: The ticker symbol (e.g., "AAPL").
        interval: The data interval (e.g., "1day", "1h").
        fast_period: Fast EMA period. Defaults to 12.
        slow_period: Slow EMA period. Defaults to 26.
        signal_period: Signal line period. Defaults to 9.
        series: Price type to use. Defaults to "close".
        outputsize: Number of data points to return.
    """
    try:
        logger.info(f"Calculating MACD for {symbol}")
        td = get_client()
        result = (
            td.time_series(symbol=symbol, interval=interval, outputsize=outputsize)
            .with_macd(
                fast_period=fast_period,
                slow_period=slow_period,
                signal_period=signal_period,
                series=series,
            )
            .as_json()
        )
        return result
    except Exception as e:
        return handle_api_error(e, symbol)


@mcp.tool()
def list_technical_indicators() -> dict[str, Any]:
    """
    Discover all technical indicators supported by TwelveData and their parameters.
    """
    try:
        logger.info("Fetching supported technical indicators list")
        td = get_client()
        return td.get_technical_indicators_list().as_json()
    except Exception as e:
        return handle_api_error(e)


@mcp.tool()
def get_technical_indicator(
    symbol: str,
    indicator_name: str,
    interval: str = "1day",
    outputsize: int = 100,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Generic tool to calculate any technical indicator supported by TwelveData.
    Use list_technical_indicators to see all available indicator names and parameters.

    Args:
        symbol: The ticker symbol (e.g., "AAPL").
        indicator_name: The name of the indicator (e.g., "ema", "stoch").
        interval: The data interval.
        outputsize: Number of data points to retrieve.
        params: Dictionary of parameters specific to the indicator.
    """
    try:
        logger.info(f"Generic call for indicator {indicator_name} on {symbol}")
        if params is None:
            params = {}
        td = get_client()

        # Mapping for generic method calling
        method_name = f"with_{indicator_name.lower()}"
        ts_data = td.time_series(
            symbol=symbol, interval=interval, outputsize=outputsize
        )

        if not hasattr(ts_data, method_name):
            return {
                "error": (
                    f"Indicator '{indicator_name}' is not supported. "
                    "Try dedicated tools or check the name."
                )
            }

        indicator_method = getattr(ts_data, method_name)
        result = indicator_method(**params).as_json()
        return result
    except Exception as e:
        return handle_api_error(e, symbol)


@mcp.tool()
def list_stocks(country: str = "USA") -> list[dict[str, Any]]:
    """
    List available stock symbols.

    Args:
        country: The country to list stocks from. Defaults to "USA".
    """
    try:
        logger.info(f"Listing stocks for country: {country}")
        td = get_client()
        result = td.get_stocks_list(country=country).as_json()
        return result.get("symbols", result.get("data", []))
    except Exception as e:
        err = handle_api_error(e)
        return [err] if isinstance(err, dict) else [{"error": str(e)}]


@mcp.tool()
def list_exchanges(exchange_type: str = "stock") -> list[dict[str, Any]]:
    """
    List all supported exchanges.

    Args:
        exchange_type: Exchange type ("stock", "forex", "cryptocurrency").
    """
    try:
        logger.info(f"Listing exchanges for type: {exchange_type}")
        td = get_client()
        result = td.get_exchanges_list(type=exchange_type).as_json()
        return result.get("data", [])
    except Exception as e:
        err = handle_api_error(e)
        return [err] if isinstance(err, dict) else [{"error": str(e)}]


@mcp.tool()
def list_forex() -> list[dict[str, Any]]:
    """List available forex symbols."""
    try:
        logger.info("Listing forex pairs")
        td = get_client()
        result = td.get_forex_pairs_list().as_json()
        return result.get("symbols", result.get("data", []))
    except Exception as e:
        err = handle_api_error(e)
        return [err] if isinstance(err, dict) else [{"error": str(e)}]


@mcp.tool()
def list_cryptocurrencies() -> list[dict[str, Any]]:
    """List available cryptocurrency symbols."""
    try:
        logger.info("Listing cryptocurrencies")
        td = get_client()
        result = td.get_cryptocurrencies_list().as_json()
        return result.get("symbols", result.get("data", []))
    except Exception as e:
        err = handle_api_error(e)
        return [err] if isinstance(err, dict) else [{"error": str(e)}]


def main():
    """Entry point for the MCP server."""
    logger.info("Starting TwelveData MCP Server")

    # Verify API key on startup
    if not verify_api_key():
        logger.critical("Startup failed: Invalid or non-functional API key.")
        sys.exit(1)

    mcp.run()


if __name__ == "__main__":
    main()
