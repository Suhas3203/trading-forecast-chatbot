"""Unit tests for ipo_service.py — all HTTP calls are mocked."""

import pytest
import requests
from unittest.mock import patch, MagicMock

from services.ipo_service import get_ipo_gmp, get_upcoming_ipos
from tests.utils.helpers import SoftAssert
from tests.utils.logger import get_logger

logger = get_logger("test.ipo")


# ─── get_ipo_gmp ─────────────────────────────────────────────────────────────

class TestGetIpoGmp:

    @pytest.mark.smoke
    @pytest.mark.unit
    def test_returns_expected_shape(self, mock_requests_get):
        result = get_ipo_gmp()
        sa = SoftAssert()
        sa.check("data" in result, "Missing 'data' key")
        sa.check("count" in result, "Missing 'count' key")
        sa.check("source" in result, "Missing 'source' key")
        sa.check("fetched_at" in result, "Missing 'fetched_at' key")
        sa.assert_all()

    @pytest.mark.unit
    def test_parses_ipo_rows(self, mock_requests_get):
        result = get_ipo_gmp()
        assert result["count"] == 2
        assert result["data"][0]["name"] == "Alpha Corp IPO"
        assert result["data"][1]["name"] == "Beta Ltd IPO"

    @pytest.mark.unit
    def test_ipo_row_fields(self, mock_requests_get):
        result = get_ipo_gmp()
        row = result["data"][0]
        sa = SoftAssert()
        for field in ("name", "price", "gmp", "estimated_listing"):
            sa.check(field in row, f"IPO row missing field: {field}")
        sa.assert_all()

    @pytest.mark.unit
    def test_returns_error_on_timeout(self):
        with patch("services.ipo_service.requests.get",
                   side_effect=requests.exceptions.Timeout):
            result = get_ipo_gmp()
        assert "error" in result
        assert "timed out" in result["error"].lower()
        assert result["data"] == []

    @pytest.mark.unit
    def test_returns_error_on_network_failure(self):
        with patch("services.ipo_service.requests.get",
                   side_effect=requests.exceptions.ConnectionError("no route")):
            result = get_ipo_gmp()
        assert "error" in result
        assert result["data"] == []

    @pytest.mark.unit
    def test_returns_error_when_table_missing(self):
        response = MagicMock()
        response.status_code = 200
        response.text = "<html><body><p>No table here</p></body></html>"
        response.raise_for_status = MagicMock()
        with patch("services.ipo_service.requests.get", return_value=response):
            result = get_ipo_gmp()
        assert "error" in result

    @pytest.mark.unit
    def test_caps_results_at_20(self):
        rows = "".join(
            f"<tr><td>IPO {i}</td><td>100</td><td>20</td><td>120</td><td>Today</td></tr>"
            for i in range(30)
        )
        html = f"<html><body><table id='mainTable'><tbody>{rows}</tbody></table></body></html>"
        response = MagicMock()
        response.status_code = 200
        response.text = html
        response.raise_for_status = MagicMock()
        with patch("services.ipo_service.requests.get", return_value=response):
            result = get_ipo_gmp()
        assert len(result["data"]) <= 20


# ─── get_upcoming_ipos ───────────────────────────────────────────────────────

class TestGetUpcomingIpos:

    def _make_response(self, html: str) -> MagicMock:
        response = MagicMock()
        response.status_code = 200
        response.text = html
        response.raise_for_status = MagicMock()
        return response

    @pytest.mark.unit
    def test_returns_expected_shape(self):
        html = """
        <html><body>
        <table id="mainTable">
          <tbody>
            <tr>
              <td>Gamma IPO</td><td>10 Jan</td><td>12 Jan</td>
              <td>100-120</td><td>120</td><td>100 Cr</td>
            </tr>
          </tbody>
        </table>
        </body></html>"""
        with patch("services.ipo_service.requests.get",
                   return_value=self._make_response(html)):
            result = get_upcoming_ipos()
        sa = SoftAssert()
        sa.check("data" in result, "Missing 'data' key")
        sa.check("count" in result, "Missing 'count' key")
        sa.assert_all()

    @pytest.mark.unit
    def test_parses_ipo_row_fields(self):
        html = """
        <html><body>
        <table id="mainTable">
          <tbody>
            <tr>
              <td>Gamma IPO</td><td>10 Jan</td><td>12 Jan</td>
              <td>100-120</td><td>120</td><td>100 Cr</td>
            </tr>
          </tbody>
        </table>
        </body></html>"""
        with patch("services.ipo_service.requests.get",
                   return_value=self._make_response(html)):
            result = get_upcoming_ipos()
        row = result["data"][0]
        assert row["name"] == "Gamma IPO"
        assert row["price_band"] == "100-120"

    @pytest.mark.unit
    def test_returns_error_on_exception(self):
        with patch("services.ipo_service.requests.get",
                   side_effect=Exception("unexpected")):
            result = get_upcoming_ipos()
        assert "error" in result
        assert result["data"] == []
