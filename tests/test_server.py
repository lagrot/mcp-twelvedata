import os
import sys
from unittest.mock import MagicMock

import pytest
from twelvedata import TDClient
from twelvedata.exceptions import (
    TwelveDataError,
)

# Ensure the src directory is in the Python path for imports
current_dir = os.path.dirname(__file__)
src_path = os.path.abspath(os.path.join(current_dir, "..", "src"))
sys.path.insert(0, src_path)

from mcp_twelvedata.server import (  # noqa: E402
    get_beta,
    get_correlation,
    get_price,
    get_rsi,
    list_exchanges,
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


def test_get_price_batch(mock_td_client):
    """Test batch price retrieval."""
    mock_price_method = MagicMock()
    mock_price_method.as_json.return_value = {
        "AAPL": {"price": "170.50"},
        "MSFT": {"price": "400.10"},
    }
    mock_td_client.price.return_value = mock_price_method

    result = get_price(symbol="AAPL,MSFT")

    assert "AAPL" in result
    assert "MSFT" in result
    mock_td_client.price.assert_called_once_with(symbol="AAPL,MSFT")


# --- Tests for Analysis Tools ---


def test_get_correlation_success(mock_td_client):
    """Test correlation tool using custom_endpoint."""
    mock_custom_method = MagicMock()
    mock_custom_method.as_json.return_value = {"indicator": "Correlation", "values": []}
    mock_td_client.custom_endpoint.return_value = mock_custom_method

    result = get_correlation(symbol1="AAPL", symbol2="MSFT")

    assert result["indicator"] == "Correlation"
    mock_td_client.custom_endpoint.assert_called_once()


def test_get_beta_success(mock_td_client):
    """Test beta tool."""
    mock_indicator_method = MagicMock()
    mock_indicator_method.as_json.return_value = {"indicator": "Beta", "values": []}
    mock_ts_base = MagicMock()
    mock_ts_base.with_beta.return_value = mock_indicator_method
    mock_td_client.time_series.return_value = mock_ts_base

    result = get_beta(symbol="AAPL")

    assert result["indicator"] == "Beta"
    mock_ts_base.with_beta.assert_called_once_with(time_period=20)


# --- Existing Indicator/Listing Tests ---


def test_get_rsi_success(mock_td_client):
    """Test dedicated RSI tool."""
    mock_indicator_method = MagicMock()
    mock_indicator_method.as_json.return_value = {"indicator": "RSI", "values": []}
    mock_ts_base = MagicMock()
    mock_ts_base.with_rsi.return_value = mock_indicator_method
    mock_td_client.time_series.return_value = mock_ts_base

    result = get_rsi(symbol="AAPL", time_period=14)

    assert result["indicator"] == "RSI"


def test_list_exchanges(mock_td_client):
    """Test exchange listing."""
    mock_list_method = MagicMock()
    mock_list_method.as_json.return_value = {"data": [{"name": "NASDAQ"}]}
    mock_td_client.get_exchanges_list.return_value = mock_list_method

    result = list_exchanges(exchange_type="stock")

    assert result[0]["name"] == "NASDAQ"


def test_list_technical_indicators(mock_td_client):
    """Test discovery tool."""
    mock_list_method = MagicMock()
    mock_list_method.as_json.return_value = {"data": [{"name": "ADX"}]}
    mock_td_client.get_technical_indicators_list.return_value = mock_list_method

    result = list_technical_indicators()

    assert result["data"][0]["name"] == "ADX"


# --- Error Handling ---


def test_handle_api_error_rate_limit(mock_td_client):
    """Test centralized rate limit handler."""
    mock_td_client.price.side_effect = TwelveDataError("Rate limit exceeded")

    result = get_price(symbol="AAPL")

    assert result["code"] == 429
    assert "Rate Limit Exceeded" in result["error"]
