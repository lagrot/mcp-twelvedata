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
    get_macd,
    get_price,
    get_quote,
    get_rsi,
    get_technical_indicator,
    list_cryptocurrencies,
    list_forex,
    list_stocks,
    list_technical_indicators,
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


# --- Tests for Market Data Tools ---


def test_get_price_success(mock_td_client):
    """Test successful retrieval of real-time price."""
    mock_price_method = MagicMock()
    mock_price_method.as_json.return_value = {
        "symbol": "AAPL",
        "price": "170.50",
        "timestamp": 1678886400,
    }
    mock_td_client.price.return_value = mock_price_method

    result = get_price(symbol="AAPL")

    assert result["price"] == "170.50"
    mock_td_client.price.assert_called_once_with(symbol="AAPL")


def test_get_price_rate_limit(mock_td_client):
    """Test get_price when rate limit is exceeded."""
    # Note: TwelveDataError is the base class, we simulate rate limit text
    mock_td_client.price.side_effect = TwelveDataError("Rate limit reached")

    result = get_price(symbol="AAPL")

    assert result["code"] == 429
    assert "Rate Limit Exceeded" in result["error"]


def test_get_quote_success(mock_td_client):
    """Test successful retrieval of quote."""
    mock_quote_method = MagicMock()
    mock_quote_method.as_json.return_value = {"symbol": "AAPL", "close": "175.50"}
    mock_td_client.quote.return_value = mock_quote_method

    result = get_quote(symbol="AAPL")

    assert result["symbol"] == "AAPL"
    mock_td_client.quote.assert_called_once_with(symbol="AAPL")


# --- Tests for Technical Indicator Tools ---


def test_get_rsi_success(mock_td_client):
    """Test dedicated RSI tool."""
    mock_indicator_method = MagicMock()
    mock_indicator_method.as_json.return_value = {"indicator": "RSI", "values": []}
    mock_ts_base = MagicMock()
    mock_ts_base.with_rsi.return_value = mock_indicator_method
    mock_td_client.time_series.return_value = mock_ts_base

    result = get_rsi(symbol="AAPL", time_period=14)

    assert result["indicator"] == "RSI"
    mock_ts_base.with_rsi.assert_called_once_with(time_period=14, series="close")


def test_get_macd_success(mock_td_client):
    """Test dedicated MACD tool."""
    mock_indicator_method = MagicMock()
    mock_indicator_method.as_json.return_value = {"indicator": "MACD", "values": []}
    mock_ts_base = MagicMock()
    mock_ts_base.with_macd.return_value = mock_indicator_method
    mock_td_client.time_series.return_value = mock_ts_base

    result = get_macd(symbol="AAPL", fast_period=12)

    assert result["indicator"] == "MACD"
    mock_ts_base.with_macd.assert_called_once_with(
        fast_period=12, slow_period=26, signal_period=9, series="close"
    )


def test_list_technical_indicators(mock_td_client):
    """Test discovery tool."""
    mock_list_method = MagicMock()
    mock_list_method.as_json.return_value = {"data": [{"name": "ADX"}]}
    mock_td_client.get_technical_indicators_list.return_value = mock_list_method

    result = list_technical_indicators()

    assert result["data"][0]["name"] == "ADX"


def test_get_technical_indicator_generic(mock_td_client):
    """Test generic fallback tool."""
    mock_indicator_method = MagicMock()
    mock_indicator_method.as_json.return_value = {"indicator": "EMA"}
    mock_ts_base = MagicMock()
    # Note: the generic tool calls with_<name>
    mock_ts_base.with_ema.return_value = mock_indicator_method
    mock_td_client.time_series.return_value = mock_ts_base

    result = get_technical_indicator(symbol="AAPL", indicator_name="ema")

    assert result["indicator"] == "EMA"


# --- Tests for Listing Tools ---


def test_list_stocks_success(mock_td_client):
    """Test listing stocks."""
    mock_stocks_method = MagicMock()
    mock_stocks_method.as_json.return_value = {"symbols": [{"symbol": "AAPL"}]}
    mock_td_client.get_stocks_list.return_value = mock_stocks_method

    result = list_stocks(country="USA")

    assert len(result) == 1
    assert result[0]["symbol"] == "AAPL"


def test_list_forex_success(mock_td_client):
    """Test listing forex."""
    mock_forex_method = MagicMock()
    mock_forex_method.as_json.return_value = {"symbols": [{"symbol": "EUR/USD"}]}
    mock_td_client.get_forex_pairs_list.return_value = mock_forex_method

    result = list_forex()

    assert len(result) == 1
    assert result[0]["symbol"] == "EUR/USD"


def test_list_cryptocurrencies_success(mock_td_client):
    """Test listing crypto."""
    mock_crypto_method = MagicMock()
    mock_crypto_method.as_json.return_value = {"symbols": [{"symbol": "BTC/USD"}]}
    mock_td_client.get_cryptocurrencies_list.return_value = mock_crypto_method

    result = list_cryptocurrencies()

    assert len(result) == 1
    assert result[0]["symbol"] == "BTC/USD"


# --- Generic Error Handling ---


def test_handle_api_error_bad_request(mock_td_client):
    """Test error handler for bad requests."""
    mock_td_client.price.side_effect = BadRequestError("Invalid symbol")

    result = get_price(symbol="INVALID")

    assert "Invalid request parameters" in result["error"]
