"""
conftest.py — Pytest fixtures for TradeBot backend.
Adapted from Testing COE greenfield_framework/pytest/conftest.py.
Replaces Selenium driver fixture with FastAPI TestClient + market/IPO mocks.
"""

import os
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Set fake API key before app import so the startup guard doesn't raise
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-placeholder")

from main import app  # noqa: E402  (must come after env var is set)
from tests.utils.logger import get_logger


# ─── Core fixtures ───────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def client() -> TestClient:
    """FastAPI TestClient — replaces COE's Selenium driver fixture."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def logger():
    """Structured test logger from COE logger utility."""
    return get_logger("tradebot-tests")


# ─── Market service mock fixtures ────────────────────────────────────────────

@pytest.fixture
def mock_ticker_history() -> pd.DataFrame:
    """Two-day price history DataFrame that mimics a yfinance Ticker.history() response."""
    dates = pd.date_range("2024-01-01", periods=2, freq="D")
    return pd.DataFrame(
        {
            "Open":   [195.0, 200.0],
            "High":   [210.0, 215.0],
            "Low":    [190.0, 195.0],
            "Close":  [200.0, 205.0],
            "Volume": [1_000_000, 1_200_000],
        },
        index=dates,
    )


@pytest.fixture
def mock_forecast_history() -> pd.DataFrame:
    """Six months of daily close prices for technical indicator calculations."""
    import numpy as np
    dates = pd.date_range("2023-07-01", periods=180, freq="D")
    prices = 200 + np.cumsum(np.random.default_rng(42).normal(0, 2, 180))
    return pd.DataFrame(
        {
            "Open":   prices - 1,
            "High":   prices + 3,
            "Low":    prices - 3,
            "Close":  prices,
            "Volume": [500_000] * 180,
        },
        index=dates,
    )


@pytest.fixture
def mock_yfinance_ticker(mock_ticker_history):
    """Patched yfinance.Ticker with stubbed history() and info."""
    ticker = MagicMock()
    ticker.history.return_value = mock_ticker_history
    ticker.info = {
        "longName": "Reliance Industries Limited",
        "previousClose": 200.0,
        "fiftyTwoWeekHigh": 250.0,
        "fiftyTwoWeekLow": 150.0,
        "marketCap": 1_500_000_000_000,
        "trailingPE": 22.5,
        "sector": "Energy",
        "industry": "Oil & Gas Refining",
        "currency": "INR",
    }
    with patch("services.market_service.yf.Ticker", return_value=ticker):
        yield ticker


# ─── IPO service mock fixtures ────────────────────────────────────────────────

@pytest.fixture
def mock_ipo_html() -> str:
    """Minimal HTML table matching the investorgain.com GMP page structure."""
    return """
    <html><body>
    <table id="mainTable">
      <thead><tr><th>IPO Name</th><th>Price</th><th>GMP</th><th>Est Listing</th><th>Updated</th></tr></thead>
      <tbody>
        <tr><td>Alpha Corp IPO</td><td>200</td><td>50</td><td>250 (25%)</td><td>Today</td></tr>
        <tr><td>Beta Ltd IPO</td><td>150</td><td>-10</td><td>140 (-6.67%)</td><td>Today</td></tr>
      </tbody>
    </table>
    </body></html>
    """


@pytest.fixture
def mock_requests_get(mock_ipo_html):
    """Patched requests.get returning fake IPO HTML."""
    response = MagicMock()
    response.status_code = 200
    response.text = mock_ipo_html
    response.raise_for_status = MagicMock()
    with patch("services.ipo_service.requests.get", return_value=response):
        yield response
