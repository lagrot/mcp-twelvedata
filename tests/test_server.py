import os
import sys
from unittest.mock import MagicMock

import pytest
from twelvedata import TDClient
from twelvedata.exceptions import (
    BadRequestError,
    TwelveDataError,
)

# Ensure the src directory is in the Python path for imports
current_dir = os.path.dirname(__file__)
src_path = os.path.abspath(os.path.join(current_dir, "..", "src"))
sys.path.insert(0, src_path)

from mcp_twelvedata.server import (  # noqa: E402
    get_price,
    get_quote,
    get_technical_indicator,
    get_time_series,
    list_cryptocurrencies,
    list_forex,
    list_stocks,
)


# Mock the TDClient and its methods
@pytest.fixture
def mock_td_client(mocker):
    """Fixture to mock the TDClient and its methods."""
    mock_client = MagicMock(spec=TDClient)

    # Mock the get_client function to return our mocked client
    mocker.patch("mcp_twelvedata.server.load_dotenv")
    mocker.patch.dict(os.environ, {"TWELVE_DATA_API_KEY": "test_api_key"})
    mocker.patch("mcp_twelvedata.server.get_client", return_value=mock_client)

    return mock_client


# --- Tests for get_price tool ---
def test_get_price_success(mock_td_client):
    """Test successful retrieval of real-time price."""
    mock_price_method = MagicMock()
    mock_price_method.as_json.return_value = {
        "symbol": "AAPL",
        "price": "170.50",
        "timestamp": 1678886400,
    }
    mock_td_client.price.return_value = mock_price_method

    symbol = "AAPL"
    result = get_price(symbol=symbol)

    mock_td_client.price.assert_called_once_with(symbol=symbol)
    mock_price_method.as_json.assert_called_once()
    assert result == {"symbol": "AAPL", "price": "170.50", "timestamp": 1678886400}


def test_get_price_invalid_symbol(mock_td_client):
    """Test get_price with an invalid symbol."""
    mock_td_client.price.side_effect = BadRequestError("Invalid symbol")

    symbol = "INVALID_SYMBOL"
    result = get_price(symbol=symbol)

    mock_td_client.price.assert_called_once_with(symbol=symbol)
    assert "error" in result
    assert "Bad request" in result["error"]


def test_get_price_rate_limit(mock_td_client):
    """Test get_price when rate limit is exceeded."""
    mock_td_client.price.side_effect = TwelveDataError("Rate limit exceeded")

    symbol = "TSLA"
    result = get_price(symbol=symbol)

    mock_td_client.price.assert_called_once_with(symbol=symbol)
    assert result["code"] == 429
    assert "Rate limit exceeded" in result["error"]


def test_get_price_api_key_error(mocker):
    """Test get_price when API key is missing."""
    mocker.patch(
        "mcp_twelvedata.server.get_client",
        side_effect=ValueError("TWELVE_DATA_API_KEY environment variable is not set"),
    )

    symbol = "AAPL"
    result = get_price(symbol=symbol)

    assert result == {"error": "TWELVE_DATA_API_KEY environment variable is not set"}


# --- Tests for get_quote tool ---
def test_get_quote_success(mock_td_client):
    """Test successful retrieval of quote."""
    mock_quote_method = MagicMock()
    mock_quote_method.as_json.return_value = {
        "symbol": "AAPL",
        "open": "175.00",
        "high": "176.00",
        "low": "174.00",
        "close": "175.50",
        "volume": 10000000,
    }
    mock_td_client.quote.return_value = mock_quote_method

    symbol = "AAPL"
    result = get_quote(symbol=symbol)

    mock_td_client.quote.assert_called_once_with(symbol=symbol)
    mock_quote_method.as_json.assert_called_once()
    assert result["symbol"] == "AAPL"


# --- Tests for get_time_series tool ---
def test_get_time_series_success(mock_td_client):
    """Test successful retrieval of time series data."""
    mock_ts_method = MagicMock()
    mock_ts_method.as_json.return_value = {
        "symbol": "AAPL",
        "interval": "1day",
        "historical": [
            {"date": "2023-01-01", "close": "131.50"},
            {"date": "2023-01-02", "close": "132.50"},
        ],
    }
    mock_td_client.time_series.return_value = mock_ts_method

    symbol = "AAPL"
    result = get_time_series(symbol=symbol, interval="1day", outputsize=2)

    assert result["symbol"] == "AAPL"
    assert len(result["historical"]) == 2


def test_get_time_series_outputsize_limit(mock_td_client):
    """Test get_time_series outputsize capping."""
    mock_ts_method = MagicMock()
    mock_ts_method.as_json.return_value = {"symbol": "AAPL"}
    mock_td_client.time_series.return_value = mock_ts_method

    get_time_series(symbol="AAPL", outputsize=6000)

    mock_td_client.time_series.assert_called_once()
    args, kwargs = mock_td_client.time_series.call_args
    assert kwargs["outputsize"] == 5000


# --- Tests for get_technical_indicator tool ---
def test_get_technical_indicator_success_rsi(mock_td_client):
    """Test successful calculation of RSI indicator."""
    mock_indicator_method = MagicMock()
    mock_indicator_method.as_json.return_value = {
        "symbol": "AAPL",
        "indicator": "RSI",
        "values": [{"datetime": "2023-01-01", "RSI": 65.5}],
    }
    mock_ts_base = MagicMock()
    mock_ts_base.with_rsi.return_value = mock_indicator_method
    mock_td_client.time_series.return_value = mock_ts_base

    result = get_technical_indicator(symbol="AAPL", indicator_name="rsi")

    assert result["indicator"] == "RSI"
    mock_ts_base.with_rsi.assert_called_once_with(time_period=14, series="close")


def test_get_technical_indicator_unknown_indicator(mock_td_client):
    """Test get_technical_indicator with an unsupported indicator name."""
    assert mock_td_client is not None
    result = get_technical_indicator(symbol="AAPL", indicator_name="unknown")

    assert "error" in result
    assert "not supported" in result["error"]


def test_get_technical_indicator_with_params(mock_td_client):
    """Test get_technical_indicator with custom parameters in a dict."""
    mock_indicator_method = MagicMock()
    mock_indicator_method.as_json.return_value = {
        "symbol": "AAPL",
        "indicator": "SMA",
        "values": [{"datetime": "2023-01-01", "SMA": 150.5}],
    }
    mock_ts_base = MagicMock()
    mock_ts_base.with_sma.return_value = mock_indicator_method
    mock_td_client.time_series.return_value = mock_ts_base

    result = get_technical_indicator(
        symbol="AAPL", indicator_name="sma", params={"time_period": 50}
    )

    assert result["indicator"] == "SMA"
    mock_ts_base.with_sma.assert_called_once_with(time_period=50, series="close")


# --- Tests for list_* tools ---
def test_list_stocks_success(mock_td_client):
    """Test successful listing of US stocks."""
    mock_stocks_method = MagicMock()
    mock_stocks_method.as_json.return_value = {"symbols": [{"symbol": "AAPL"}]}
    mock_td_client.get_stocks_list.return_value = mock_stocks_method

    result = list_stocks(country="USA")

    assert len(result) == 1
    assert result[0]["symbol"] == "AAPL"


def test_list_forex_success(mock_td_client):
    """Test successful listing of forex symbols."""
    mock_forex_method = MagicMock()
    mock_forex_method.as_json.return_value = {"symbols": [{"symbol": "EUR/USD"}]}
    mock_td_client.get_forex_pairs_list.return_value = mock_forex_method

    result = list_forex()

    assert len(result) == 1
    assert result[0]["symbol"] == "EUR/USD"


def test_list_cryptocurrencies_success(mock_td_client):
    """Test successful listing of crypto symbols."""
    mock_crypto_method = MagicMock()
    mock_crypto_method.as_json.return_value = {"symbols": [{"symbol": "BTC/USD"}]}
    mock_td_client.get_cryptocurrencies_list.return_value = mock_crypto_method

    result = list_cryptocurrencies()

    assert len(result) == 1
    assert result[0]["symbol"] == "BTC/USD"
