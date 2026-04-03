import pytest
from unittest.mock import MagicMock, patch
import os
import sys

# Ensure the src directory is in the Python path for imports
# This is a common setup for projects structured with a src directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the server module and relevant exceptions
from mcp_twelvedata.server import get_price, get_quote, get_time_series, get_technical_indicator, list_stocks, list_forex, list_cryptocurrencies, get_client
from twelvedata.errors import InvalidSymbolError, InvalidIntervalError, RateLimitExceededError

# Mock the TDClient and its methods
@pytest.fixture
def mock_td_client(mocker):
    """Fixture to mock the TDClient and its methods."""
    mock_client = MagicMock(spec=TDClient)
    
    # Mock the get_client function to return our mocked client
    # We also need to ensure the API key is set for load_dotenv to work correctly in the server context
    mocker.patch('mcp_twelvedata.server.load_dotenv') # Prevent loading .env during tests
    mocker.patch.dict(os.environ, {"TWELVE_DATA_API_KEY": "test_api_key"})
    mocker.patch('mcp_twelvedata.server.get_client', return_value=mock_client)
    
    return mock_client

# --- Tests for get_price tool ---
def test_get_price_success(mock_td_client):
    """Test successful retrieval of real-time price."""
    mock_price_method = MagicMock()
    mock_price_method.as_json.return_value = {"symbol": "AAPL", "price": "170.50", "timestamp": 1678886400}
    mock_td_client.price.return_value = mock_price_method

    symbol = "AAPL"
    result = get_price(symbol=symbol)

    mock_td_client.price.assert_called_once_with(symbol=symbol)
    mock_price_method.as_json.assert_called_once()
    assert result == {"symbol": "AAPL", "price": "170.50", "timestamp": 1678886400}

def test_get_price_invalid_symbol(mock_td_client):
    """Test get_price with an invalid symbol."""
    mock_td_client.price.side_effect = InvalidSymbolError("Invalid symbol provided")

    symbol = "INVALID_SYMBOL"
    result = get_price(symbol=symbol)

    mock_td_client.price.assert_called_once_with(symbol=symbol)
    assert result == {"error": f"Invalid symbol: {symbol}"}

def test_get_price_rate_limit(mock_td_client):
    """Test get_price when rate limit is exceeded."""
    mock_td_client.price.side_effect = RateLimitExceededError("Rate limit exceeded")

    symbol = "TSLA"
    result = get_price(symbol=symbol)

    mock_td_client.price.assert_called_once_with(symbol=symbol)
    assert result == {"error": "Rate limit exceeded. Please check your API usage.", "code": 429}

def test_get_price_api_key_error(mocker):
    """Test get_price when API key is missing."""
    # Mock get_client to raise ValueError (simulating missing API key)
    mocker.patch('mcp_twelvedata.server.get_client', side_effect=ValueError("TWELVE_DATA_API_KEY environment variable is not set"))
    
    symbol = "AAPL"
    result = get_price(symbol=symbol)

    assert result == {"error": "TWELVE_DATA_API_KEY environment variable is not set"}

# --- Tests for get_quote tool ---
def test_get_quote_success(mock_td_client):
    """Test successful retrieval of quote."""
    mock_quote_method = MagicMock()
    mock_quote_method.as_json.return_value = {"symbol": "AAPL", "open": "175.00", "high": "176.00", "low": "174.00", "close": "175.50", "volume": 10000000}
    mock_td_client.quote.return_value = mock_quote_method

    symbol = "AAPL"
    result = get_quote(symbol=symbol)

    mock_td_client.quote.assert_called_once_with(symbol=symbol)
    mock_quote_method.as_json.assert_called_once()
    assert result == {"symbol": "AAPL", "open": "175.00", "high": "176.00", "low": "174.00", "close": "175.50", "volume": 10000000}

def test_get_quote_invalid_symbol(mock_td_client):
    """Test get_quote with an invalid symbol."""
    mock_td_client.quote.side_effect = InvalidSymbolError("Invalid symbol provided")

    symbol = "INVALID_QUOTE_SYMBOL"
    result = get_quote(symbol=symbol)

    mock_td_client.quote.assert_called_once_with(symbol=symbol)
    assert result == {"error": f"Invalid symbol: {symbol}"}

# --- Tests for get_time_series tool ---
def test_get_time_series_success(mock_td_client):
    """Test successful retrieval of time series data."""
    mock_ts_method = MagicMock()
    mock_ts_method.as_json.return_value = {
        "symbol": "AAPL",
        "interval": "1day",
        "historical": [
            {"date": "2023-01-01", "open": "130.00", "high": "132.00", "low": "129.50", "close": "131.50", "volume": 50000000},
            {"date": "2023-01-02", "open": "131.50", "high": "133.00", "low": "131.00", "close": "132.50", "volume": 52000000}
        ]
    }
    mock_td_client.time_series.return_value = mock_ts_method

    symbol = "AAPL"
    interval = "1day"
    outputsize = 2
    result = get_time_series(symbol=symbol, interval=interval, outputsize=outputsize)

    mock_td_client.time_series.assert_called_once_with(
        symbol=symbol,
        interval=interval,
        outputsize=outputsize,
        start_date=None,
        end_date=None
    )
    mock_ts_method.as_json.assert_called_once()
    assert result["symbol"] == "AAPL"
    assert len(result["historical"]) == 2

def test_get_time_series_invalid_interval(mock_td_client):
    """Test get_time_series with an invalid interval."""
    mock_td_client.time_series.side_effect = InvalidIntervalError("Invalid interval")
    
    symbol = "AAPL"
    interval = "invalid_interval"
    result = get_time_series(symbol=symbol, interval=interval)

    mock_td_client.time_series.assert_called_once_with(
        symbol=symbol,
        interval=interval,
        outputsize=100, # Default outputsize
        start_date=None,
        end_date=None
    )
    assert result == {"error": f"Invalid interval: {interval}"}

def test_get_time_series_outputsize_limit(mock_td_client):
    """Test get_time_series outputsize capping."""
    mock_ts_method = MagicMock()
    # Assume the API call actually received the capped outputsize
    mock_ts_method.as_json.return_value = {"symbol": "AAPL", "interval": "1day", "historical": [{"date": "2023-01-01", "close": "131.50"}]}
    mock_td_client.time_series.return_value = mock_ts_method

    symbol = "AAPL"
    interval = "1day"
    large_outputsize = 6000 # Exceeds limit
    
    result = get_time_series(symbol=symbol, interval=interval, outputsize=large_outputsize)

    # Verify that time_series was called with the capped outputsize
    mock_td_client.time_series.assert_called_once_with(
        symbol=symbol,
        interval=interval,
        outputsize=5000, # Capped value
        start_date=None,
        end_date=None
    )
    assert "outputsize" in result and result["outputsize"] == 5000


# --- Tests for get_technical_indicator tool ---
def test_get_technical_indicator_success_rsi(mock_td_client):
    """Test successful calculation of RSI indicator."""
    mock_indicator_method = MagicMock()
    mock_indicator_method.as_json.return_value = {
        "symbol": "AAPL", "indicator": "RSI", "interval": "1day", "time_period": 14,
        "values": [{"datetime": "2023-01-01", "RSI": 65.5}, {"datetime": "2023-01-02", "RSI": 67.2}]
    }
    # Mock the time_series call and the subsequent with_rsi call
    mock_ts_base = MagicMock()
    mock_ts_base.with_rsi.return_value = mock_indicator_method
    mock_td_client.time_series.return_value = mock_ts_base

    symbol = "AAPL"
    indicator_name = "rsi"
    interval = "1day"
    outputsize = 2
    result = get_technical_indicator(symbol=symbol, indicator_name=indicator_name, interval=interval, outputsize=outputsize)

    # Check that time_series was called correctly
    mock_td_client.time_series.assert_called_once_with(
        symbol=symbol,
        interval=interval,
        outputsize=outputsize,
        start_date=None,
        end_date=None
    )
    # Check that the correct indicator method was called on the time_series result
    mock_ts_base.with_rsi.assert_called_once_with(time_period=14, series="close")
    mock_indicator_method.as_json.assert_called_once()
    assert result["symbol"] == "AAPL"
    assert result["indicator"] == "RSI"
    assert len(result["values"]) == 2

def test_get_technical_indicator_unknown_indicator(mock_td_client):
    """Test get_technical_indicator with an unsupported indicator name."""
    symbol = "AAPL"
    indicator_name = "unknown_indicator"
    result = get_technical_indicator(symbol=symbol, indicator_name=indicator_name)

    assert "error" in result
    assert f"Indicator '{indicator_name}' is not supported or recognized." in result["error"]
    # Ensure no API calls were made
    mock_td_client.time_series.assert_not_called()

def test_get_technical_indicator_with_custom_params(mock_td_client):
    """Test get_technical_indicator with custom parameters like time_period."""
    mock_indicator_method = MagicMock()
    mock_indicator_method.as_json.return_value = {
        "symbol": "MSFT", "indicator": "SMA", "interval": "1h", "time_period": 50,
        "values": [{"datetime": "2023-01-01T10:00:00", "SMA": 150.0}]
    }
    mock_ts_base = MagicMock()
    mock_ts_base.with_sma.return_value = mock_indicator_method
    mock_td_client.time_series.return_value = mock_ts_base

    symbol = "MSFT"
    indicator_name = "sma"
    interval = "1h"
    outputsize = 1
    custom_time_period = 50
    
    result = get_technical_indicator(
        symbol=symbol,
        indicator_name=indicator_name,
        interval=interval,
        outputsize=outputsize,
        time_period=custom_time_period # Custom parameter
    )

    mock_td_client.time_series.assert_called_once_with(
        symbol=symbol,
        interval=interval,
        outputsize=outputsize,
        start_date=None,
        end_date=None
    )
    mock_ts_base.with_sma.assert_called_once_with(time_period=custom_time_period, series="close") # Ensure custom param is used
    assert result["symbol"] == "MSFT"
    assert result["indicator"] == "SMA"


# --- Tests for list_* tools ---
def test_list_stocks_success(mock_td_client):
    """Test successful listing of US stocks."""
    mock_stocks_method = MagicMock()
    mock_stocks_method.as_json.return_value = {"symbols": [{"symbol": "AAPL", "name": "Apple Inc."}, {"symbol": "MSFT", "name": "Microsoft Corp."}]}
    mock_td_client.stocks.return_value = mock_stocks_method

    country = "USA"
    result = list_stocks(country=country)

    mock_td_client.stocks.assert_called_once_with(country=country)
    mock_stocks_method.as_json.assert_called_once()
    assert len(result) == 2
    assert result[0]["symbol"] == "AAPL"

def test_list_stocks_no_symbols_returned(mock_td_client):
    """Test list_stocks when API returns an empty list or no 'symbols' key."""
    mock_stocks_method = MagicMock()
    mock_stocks_method.as_json.return_value = {} # Simulate empty response
    mock_td_client.stocks.return_value = mock_stocks_method

    country = "USA"
    result = list_stocks(country=country)

    mock_td_client.stocks.assert_called_once_with(country=country)
    assert result == [] # Should default to empty list if 'symbols' key is missing

def test_list_forex_success(mock_td_client):
    """Test successful listing of forex symbols."""
    mock_forex_method = MagicMock()
    mock_forex_method.as_json.return_value = {"symbols": [{"symbol": "EUR/USD"}, {"symbol": "GBP/USD"}]}
    mock_td_client.forex.return_value = mock_forex_method

    result = list_forex()

    mock_td_client.forex.assert_called_once()
    mock_forex_method.as_json.assert_called_once()
    assert len(result) == 2
    assert result[0]["symbol"] == "EUR/USD"

def test_list_cryptocurrencies_success(mock_td_client):
    """Test successful listing of crypto symbols."""
    mock_crypto_method = MagicMock()
    mock_crypto_method.as_json.return_value = {"symbols": [{"symbol": "BTC/USD"}, {"symbol": "ETH/USD"}]}
    mock_td_client.cryptocurrencies.return_value = mock_crypto_method

    result = list_cryptocurrencies()

    mock_td_client.cryptocurrencies.assert_called_once()
    mock_crypto_method.as_json.assert_called_once()
    assert len(result) == 2
    assert result[0]["symbol"] == "BTC/USD"

def test_tool_error_handling(mock_td_client):
    """Test generic exception handling in tools."""
    # Example for get_price, but could be generalized
    mock_td_client.price.side_effect = Exception("A generic API error occurred")
    
    symbol = "ANY_SYMBOL"
    result = get_price(symbol=symbol)
    
    assert result == {"error": "A generic API error occurred", "symbol": symbol}
