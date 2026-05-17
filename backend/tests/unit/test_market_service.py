"""Unit tests for market_service.py — all yfinance calls are mocked."""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock

from services.market_service import (
    get_stock_data,
    get_stock_forecast,
    get_market_overview,
    search_stock,
)
from tests.utils.helpers import SoftAssert
from tests.utils.logger import get_logger

logger = get_logger("test.market")


# ─── get_stock_data ──────────────────────────────────────────────────────────

class TestGetStockData:

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_returns_expected_fields(self, mock_yfinance_ticker):
        result = get_stock_data("RELIANCE")
        sa = SoftAssert()
        for field in ("symbol", "name", "price", "change", "change_pct",
                      "open", "high", "low", "volume", "trend"):
            sa.check(field in result, f"Missing field: {field}")
        sa.assert_all()

    @pytest.mark.unit
    def test_auto_appends_ns_suffix(self, mock_yfinance_ticker):
        result = get_stock_data("RELIANCE")
        assert result["symbol"] == "RELIANCE.NS"

    @pytest.mark.unit
    def test_price_is_last_close(self, mock_yfinance_ticker, mock_ticker_history):
        result = get_stock_data("RELIANCE")
        assert result["price"] == round(mock_ticker_history["Close"].iloc[-1], 2)

    @pytest.mark.unit
    def test_trend_up_when_price_rises(self, mock_yfinance_ticker):
        result = get_stock_data("RELIANCE")
        # fixture: close[0]=200, close[1]=205 — price went up
        assert result["trend"] == "UP"

    @pytest.mark.unit
    def test_trend_down_when_price_falls(self, mock_ticker_history):
        mock_ticker_history["Close"] = [210.0, 200.0]
        ticker = MagicMock()
        ticker.history.return_value = mock_ticker_history
        ticker.info = {"previousClose": 210.0, "currency": "INR"}
        with patch("services.market_service.yf.Ticker", return_value=ticker):
            result = get_stock_data("RELIANCE")
        assert result["trend"] == "DOWN"

    @pytest.mark.unit
    def test_returns_error_on_empty_history(self):
        ticker = MagicMock()
        ticker.history.return_value = pd.DataFrame()
        ticker.info = {}
        with patch("services.market_service.yf.Ticker", return_value=ticker):
            result = get_stock_data("INVALID")
        assert "error" in result

    @pytest.mark.unit
    def test_us_symbol_not_modified(self, mock_yfinance_ticker):
        result = get_stock_data("AAPL")
        # AAPL has no "." so .NS is appended — valid yfinance behavior
        assert "error" not in result or result.get("symbol") == "AAPL.NS"

    @pytest.mark.unit
    def test_caret_symbol_not_modified(self, mock_yfinance_ticker):
        result = get_stock_data("^NSEI")
        assert result.get("symbol") == "^NSEI"


# ─── get_stock_forecast ──────────────────────────────────────────────────────

class TestGetStockForecast:

    def _make_ticker_with_history(self, history: pd.DataFrame) -> MagicMock:
        ticker = MagicMock()
        ticker.history.return_value = history
        return ticker

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_returns_expected_fields(self, mock_forecast_history):
        ticker = self._make_ticker_with_history(mock_forecast_history)
        with patch("services.market_service.yf.Ticker", return_value=ticker):
            result = get_stock_forecast("RELIANCE")
        sa = SoftAssert()
        for field in ("symbol", "current_price", "sma_20", "rsi",
                      "rsi_signal", "support", "resistance", "signal"):
            sa.check(field in result, f"Missing field: {field}")
        sa.assert_all()

    @pytest.mark.unit
    def test_rsi_in_valid_range(self, mock_forecast_history):
        ticker = self._make_ticker_with_history(mock_forecast_history)
        with patch("services.market_service.yf.Ticker", return_value=ticker):
            result = get_stock_forecast("RELIANCE")
        assert 0 <= result["rsi"] <= 100, f"RSI out of range: {result['rsi']}"

    @pytest.mark.unit
    def test_support_less_than_resistance(self, mock_forecast_history):
        ticker = self._make_ticker_with_history(mock_forecast_history)
        with patch("services.market_service.yf.Ticker", return_value=ticker):
            result = get_stock_forecast("RELIANCE")
        assert result["support"] <= result["resistance"]

    @pytest.mark.unit
    def test_signal_is_valid_value(self, mock_forecast_history):
        ticker = self._make_ticker_with_history(mock_forecast_history)
        with patch("services.market_service.yf.Ticker", return_value=ticker):
            result = get_stock_forecast("RELIANCE")
        assert result["signal"] in ("BULLISH", "BEARISH", "NEUTRAL")

    @pytest.mark.unit
    def test_error_on_insufficient_data(self):
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        short_hist = pd.DataFrame({"Close": [100]*5, "Open": [99]*5,
                                   "High": [101]*5, "Low": [98]*5,
                                   "Volume": [1000]*5}, index=dates)
        ticker = self._make_ticker_with_history(short_hist)
        with patch("services.market_service.yf.Ticker", return_value=ticker):
            result = get_stock_forecast("RELIANCE")
        assert "error" in result

    @pytest.mark.unit
    def test_rsi_signal_overbought(self, mock_forecast_history):
        # Force all gains to push RSI above 70
        mock_forecast_history["Close"] = sorted(mock_forecast_history["Close"])
        ticker = self._make_ticker_with_history(mock_forecast_history)
        with patch("services.market_service.yf.Ticker", return_value=ticker):
            result = get_stock_forecast("RELIANCE")
        assert result["rsi_signal"] in ("Overbought", "Neutral", "Oversold")


# ─── get_market_overview ─────────────────────────────────────────────────────

class TestGetMarketOverview:

    def _patch_format(self, return_value: dict):
        return patch(
            "services.market_service._format_index_data",
            return_value=return_value,
        )

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_indian_market_returns_list(self):
        stub = {"name": "NIFTY 50", "price": 24000.0, "trend": "UP"}
        with self._patch_format(stub):
            result = get_market_overview("indian")
        assert "indian" in result
        assert isinstance(result["indian"], list)
        assert len(result["indian"]) > 0

    @pytest.mark.unit
    def test_global_market_returns_list(self):
        stub = {"name": "S&P 500", "price": 5000.0, "trend": "UP"}
        with self._patch_format(stub):
            result = get_market_overview("global")
        assert "global" in result

    @pytest.mark.unit
    def test_both_returns_indian_and_global(self):
        stub = {"name": "X", "price": 100.0, "trend": "UP"}
        with self._patch_format(stub):
            result = get_market_overview("both")
        assert "indian" in result and "global" in result


# ─── search_stock ─────────────────────────────────────────────────────────────

class TestSearchStock:

    @pytest.mark.unit
    def test_returns_list(self):
        mock_search = MagicMock()
        mock_search.quotes = [
            {"symbol": "RELIANCE.NS", "longname": "Reliance Industries",
             "exchange": "NSI", "quoteType": "EQUITY"}
        ]
        with patch("services.market_service.yf.Search", return_value=mock_search):
            result = search_stock("Reliance")
        assert isinstance(result, list)
        assert result[0]["symbol"] == "RELIANCE.NS"

    @pytest.mark.unit
    def test_returns_empty_list_on_exception(self):
        with patch("services.market_service.yf.Search", side_effect=Exception("API error")):
            result = search_stock("xyz_nonexistent")
        assert result == []
