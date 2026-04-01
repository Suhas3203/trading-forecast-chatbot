import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional

INDIAN_INDICES = {
    "NIFTY 50": "^NSEI",
    "SENSEX": "^BSESN",
    "BANK NIFTY": "^NSEBANK",
    "NIFTY IT": "^CNXIT",
    "NIFTY AUTO": "^CNXAUTO",
    "NIFTY PHARMA": "^CNXPHARMA",
    "NIFTY FMCG": "^CNXFMCG",
    "NIFTY METAL": "^CNXMETAL",
    "NIFTY REALTY": "^CNXREALTY",
    "NIFTY MIDCAP 50": "^NSEMDCP50",
}

GLOBAL_INDICES = {
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC",
    "Dow Jones": "^DJI",
    "FTSE 100": "^FTSE",
    "Nikkei 225": "^N225",
    "DAX": "^GDAXI",
    "Hang Seng": "^HSI",
    "Shanghai Composite": "000001.SS",
    "CAC 40": "^FCHI",
    "ASX 200": "^AXJO",
}


def _format_index_data(name: str, ticker_symbol: str) -> dict:
    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="2d", interval="1d")
        if hist.empty or len(hist) < 1:
            return {"name": name, "error": "Data unavailable"}

        current = hist["Close"].iloc[-1]
        prev = hist["Close"].iloc[-2] if len(hist) >= 2 else current
        change = current - prev
        change_pct = (change / prev) * 100 if prev != 0 else 0

        return {
            "name": name,
            "symbol": ticker_symbol,
            "price": round(current, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "trend": "UP" if change >= 0 else "DOWN",
        }
    except Exception as e:
        return {"name": name, "error": str(e)}


def get_market_overview(market: str = "both") -> dict:
    result = {}
    if market in ("indian", "both"):
        result["indian"] = [
            _format_index_data(name, sym) for name, sym in INDIAN_INDICES.items()
        ]
    if market in ("global", "both"):
        result["global"] = [
            _format_index_data(name, sym) for name, sym in GLOBAL_INDICES.items()
        ]
    return result


def get_stock_data(symbol: str, period: str = "1mo") -> dict:
    # Auto-append .NS for Indian stocks if no exchange suffix
    if "." not in symbol and "^" not in symbol:
        symbol = symbol.upper() + ".NS"

    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        hist = ticker.history(period=period)

        if hist.empty:
            return {"error": f"No data found for symbol '{symbol}'"}

        current_price = hist["Close"].iloc[-1]
        prev_close = info.get("previousClose") or hist["Close"].iloc[-2]
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100 if prev_close else 0

        return {
            "symbol": symbol,
            "name": info.get("longName") or info.get("shortName", symbol),
            "price": round(current_price, 2),
            "change": round(change, 2),
            "change_pct": round(change_pct, 2),
            "open": round(hist["Open"].iloc[-1], 2),
            "high": round(hist["High"].iloc[-1], 2),
            "low": round(hist["Low"].iloc[-1], 2),
            "volume": int(hist["Volume"].iloc[-1]),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "trend": "UP" if change >= 0 else "DOWN",
            "currency": info.get("currency", "INR"),
        }
    except Exception as e:
        return {"error": str(e)}


def get_stock_forecast(symbol: str) -> dict:
    if "." not in symbol and "^" not in symbol:
        symbol = symbol.upper() + ".NS"

    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="6mo")

        if hist.empty or len(hist) < 20:
            return {"error": f"Insufficient data for forecast of '{symbol}'"}

        close = hist["Close"]

        sma_20 = close.rolling(20).mean().iloc[-1]
        sma_50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else None
        current = close.iloc[-1]

        # RSI calculation
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = (-delta.clip(upper=0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        # Support & Resistance (last 30 days)
        recent = hist.tail(30)
        support = round(recent["Low"].min(), 2)
        resistance = round(recent["High"].max(), 2)

        # Trend signal
        if current > sma_20 and (sma_50 is None or sma_20 > sma_50):
            signal = "BULLISH"
        elif current < sma_20 and (sma_50 is None or sma_20 < sma_50):
            signal = "BEARISH"
        else:
            signal = "NEUTRAL"

        rsi_signal = "Overbought" if rsi > 70 else ("Oversold" if rsi < 30 else "Neutral")

        return {
            "symbol": symbol,
            "current_price": round(current, 2),
            "sma_20": round(sma_20, 2),
            "sma_50": round(sma_50, 2) if sma_50 else None,
            "rsi": round(rsi, 2),
            "rsi_signal": rsi_signal,
            "support": support,
            "resistance": resistance,
            "signal": signal,
            "note": "Based on technical indicators (SMA, RSI). Not financial advice.",
        }
    except Exception as e:
        return {"error": str(e)}


def search_stock(query: str) -> list[dict]:
    try:
        results = yf.Search(query, max_results=5)
        quotes = results.quotes if hasattr(results, "quotes") else []
        return [
            {
                "symbol": q.get("symbol", ""),
                "name": q.get("longname") or q.get("shortname", ""),
                "exchange": q.get("exchange", ""),
                "type": q.get("quoteType", ""),
            }
            for q in quotes[:5]
        ]
    except Exception:
        return []
