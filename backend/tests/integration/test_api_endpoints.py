"""Integration tests for TradeBot FastAPI endpoints.
These tests use a real TestClient but mock external services (yfinance, requests)
so they don't require network access.
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from tests.utils.helpers import SoftAssert
from tests.utils.logger import get_logger

logger = get_logger("test.api")

_INDEX_STUB = {"name": "NIFTY 50", "symbol": "^NSEI", "price": 24000.0,
               "change": 50.0, "change_pct": 0.21, "trend": "UP"}

_STOCK_STUB = {
    "symbol": "RELIANCE.NS", "name": "Reliance Industries",
    "price": 2850.50, "change": 30.0, "change_pct": 1.06,
    "open": 2820.0, "high": 2870.0, "low": 2810.0,
    "volume": 5_000_000, "trend": "UP", "currency": "INR",
}

_FORECAST_STUB = {
    "symbol": "RELIANCE.NS", "current_price": 2850.50,
    "sma_20": 2800.0, "sma_50": 2750.0, "rsi": 58.3,
    "rsi_signal": "Neutral", "support": 2700.0, "resistance": 2950.0,
    "signal": "BULLISH",
}

_IPO_STUB = {
    "source": "investorgain.com", "fetched_at": "2024-01-01 10:00 IST",
    "count": 1, "data": [{"name": "Test IPO", "price": "100",
                           "gmp": "20", "estimated_listing": "120 (20%)",
                           "last_updated": "Today"}],
}


# ─── Health ──────────────────────────────────────────────────────────────────

class TestHealthEndpoint:

    @pytest.mark.smoke
    @pytest.mark.integration
    def test_health_returns_200(self, client, logger):
        logger.info("GET /health")
        resp = client.get("/health")
        assert resp.status_code == 200

    @pytest.mark.smoke
    @pytest.mark.integration
    def test_health_response_shape(self, client):
        resp = client.get("/health")
        body = resp.json()
        sa = SoftAssert()
        sa.check(body.get("status") == "ok", f"status != ok: {body}")
        sa.check("service" in body, "Missing 'service' key")
        sa.assert_all()


# ─── Market overview ─────────────────────────────────────────────────────────

class TestMarketOverviewEndpoint:

    @pytest.mark.smoke
    @pytest.mark.integration
    def test_both_markets_returns_200(self, client):
        with patch("main.get_market_overview",
                   return_value={"indian": [_INDEX_STUB], "global": [_INDEX_STUB]}):
            resp = client.get("/api/market/overview")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_response_contains_indian_and_global(self, client):
        with patch("main.get_market_overview",
                   return_value={"indian": [_INDEX_STUB], "global": [_INDEX_STUB]}):
            body = client.get("/api/market/overview").json()
        assert "indian" in body and "global" in body

    @pytest.mark.integration
    def test_indian_only(self, client):
        with patch("main.get_market_overview",
                   return_value={"indian": [_INDEX_STUB]}):
            resp = client.get("/api/market/overview?market=indian")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_global_only(self, client):
        with patch("main.get_market_overview",
                   return_value={"global": [_INDEX_STUB]}):
            resp = client.get("/api/market/overview?market=global")
        assert resp.status_code == 200


# ─── Stock data ──────────────────────────────────────────────────────────────

class TestStockDataEndpoint:

    @pytest.mark.smoke
    @pytest.mark.integration
    def test_returns_200_for_valid_symbol(self, client):
        with patch("main.get_stock_data", return_value=_STOCK_STUB):
            resp = client.get("/api/market/stock/RELIANCE")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_response_has_price_and_trend(self, client):
        with patch("main.get_stock_data", return_value=_STOCK_STUB):
            body = client.get("/api/market/stock/RELIANCE").json()
        sa = SoftAssert()
        sa.check("price" in body, "Missing 'price'")
        sa.check("trend" in body, "Missing 'trend'")
        sa.assert_all()

    @pytest.mark.integration
    def test_accepts_period_param(self, client):
        with patch("main.get_stock_data", return_value=_STOCK_STUB) as mock:
            client.get("/api/market/stock/RELIANCE?period=3mo")
        mock.assert_called_once_with("RELIANCE", "3mo")


# ─── Forecast ────────────────────────────────────────────────────────────────

class TestForecastEndpoint:

    @pytest.mark.integration
    def test_returns_200(self, client):
        with patch("main.get_stock_forecast", return_value=_FORECAST_STUB):
            resp = client.get("/api/market/forecast/RELIANCE")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_response_has_signal_and_rsi(self, client):
        with patch("main.get_stock_forecast", return_value=_FORECAST_STUB):
            body = client.get("/api/market/forecast/RELIANCE").json()
        sa = SoftAssert()
        sa.check("signal" in body, "Missing 'signal'")
        sa.check("rsi" in body, "Missing 'rsi'")
        sa.assert_all()


# ─── IPO GMP ─────────────────────────────────────────────────────────────────

class TestIpoGmpEndpoint:

    @pytest.mark.smoke
    @pytest.mark.integration
    def test_returns_200(self, client):
        with patch("main.get_ipo_gmp", return_value=_IPO_STUB):
            resp = client.get("/api/ipo/gmp")
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_response_has_data_list(self, client):
        with patch("main.get_ipo_gmp", return_value=_IPO_STUB):
            body = client.get("/api/ipo/gmp").json()
        assert "data" in body
        assert isinstance(body["data"], list)


# ─── Chat endpoint ───────────────────────────────────────────────────────────

class TestChatEndpoint:

    @pytest.mark.smoke
    @pytest.mark.integration
    def test_returns_200_with_valid_payload(self, client):
        with patch("main.process_chat", return_value="NIFTY 50 is at 24,000."):
            resp = client.post("/api/chat",
                               json={"messages": [{"role": "user",
                                                   "content": "What is NIFTY?"}]})
        assert resp.status_code == 200

    @pytest.mark.integration
    def test_reply_field_in_response(self, client):
        with patch("main.process_chat", return_value="NIFTY 50 is at 24,000."):
            body = client.post("/api/chat",
                               json={"messages": [{"role": "user",
                                                   "content": "What is NIFTY?"}]}).json()
        assert "reply" in body
        assert isinstance(body["reply"], str)

    @pytest.mark.integration
    def test_empty_messages_returns_422(self, client):
        resp = client.post("/api/chat", json={"messages": []})
        assert resp.status_code == 400

    @pytest.mark.integration
    def test_rate_limit_returns_429(self, client):
        import anthropic
        with patch("main.process_chat",
                   side_effect=anthropic.RateLimitError(
                       "rate_limit", response=MagicMock(), body={})):
            resp = client.post("/api/chat",
                               json={"messages": [{"role": "user",
                                                   "content": "Show NIFTY"}]})
        assert resp.status_code == 429
