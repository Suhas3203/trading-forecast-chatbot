import anthropic
import json
import time
from services.market_service import (
    get_market_overview,
    get_stock_data,
    get_stock_forecast,
    search_stock,
)
from services.ipo_service import get_ipo_gmp, get_upcoming_ipos

client = anthropic.Anthropic()

_RETRY_DELAYS = [2, 5, 10]  # seconds between attempts for rate limit errors


def _create_with_retry(**kwargs) -> anthropic.types.Message:
    for attempt, delay in enumerate(_RETRY_DELAYS, start=1):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            if attempt == len(_RETRY_DELAYS):
                raise
            time.sleep(delay)
    # unreachable, but satisfies type checker
    return client.messages.create(**kwargs)

SYSTEM_PROMPT = """You are TradeBot — a specialized financial assistant focused exclusively on Indian and global stock markets.

You ONLY help with:
- Indian market indices: NIFTY 50, SENSEX, BANK NIFTY, sector indices
- Global market indices: S&P 500, NASDAQ, Dow Jones, FTSE 100, Nikkei, DAX, etc.
- IPO Grey Market Premium (GMP) and upcoming IPOs
- Individual stock data and analysis (NSE/BSE and US markets)
- Technical analysis and trading forecasts
- Market trends, sector performance, basic trading concepts

STRICT RULES:
1. If a query is NOT related to finance, trading, stocks, markets, or economics — politely decline and say: "I'm TradeBot, specialized for market queries only. I can't help with that, but feel free to ask me about stocks, indices, or IPOs!"
2. NEVER engage with inappropriate, offensive, or harmful content — respond: "I can't respond to that. Please keep queries focused on market and trading topics."
3. Always use available tools to fetch real-time data before answering data-specific questions.
4. Present numbers with proper formatting (commas for thousands, 2 decimal places).
5. For UP moves use ▲, for DOWN moves use ▼.
6. Always add this disclaimer after providing stock/index data or forecasts: "⚠️ Disclaimer: Information is for educational purposes only and not financial advice. Consult a SEBI-registered advisor before investing."
7. Be concise, clear, and structured. Use bullet points and tables when helpful.
8. When data fetch fails, acknowledge it honestly and suggest the user check NSE/BSE websites directly."""

TOOLS = [
    {
        "name": "get_market_overview",
        "description": "Fetch live data for Indian indices (NIFTY 50, SENSEX, BANK NIFTY, sector indices) and/or global indices (S&P 500, NASDAQ, etc.)",
        "input_schema": {
            "type": "object",
            "properties": {
                "market": {
                    "type": "string",
                    "enum": ["indian", "global", "both"],
                    "description": "Which markets to fetch: 'indian', 'global', or 'both'",
                }
            },
            "required": ["market"],
        },
    },
    {
        "name": "get_stock_data",
        "description": "Fetch live stock price and details for a specific stock or index. For Indian stocks use NSE symbol (e.g. RELIANCE, TCS, INFY). For US stocks use ticker (e.g. AAPL, TSLA).",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g. RELIANCE, TCS, AAPL, ^NSEI)",
                },
                "period": {
                    "type": "string",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
                    "description": "Historical period to fetch",
                },
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_stock_forecast",
        "description": "Get technical analysis forecast for a stock including SMA, RSI, support/resistance levels, and trend signal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol",
                }
            },
            "required": ["symbol"],
        },
    },
    {
        "name": "get_ipo_gmp",
        "description": "Fetch current IPO Grey Market Premium (GMP) data — shows estimated listing gains/losses for upcoming IPOs.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_upcoming_ipos",
        "description": "Fetch list of upcoming IPOs with open/close dates, price band, and lot size.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "search_stock",
        "description": "Search for a stock by company name or partial ticker to find the correct symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Company name or partial stock symbol to search",
                }
            },
            "required": ["query"],
        },
    },
]


def _execute_tool(tool_name: str, tool_input: dict) -> str:
    try:
        if tool_name == "get_market_overview":
            result = get_market_overview(tool_input.get("market", "both"))
        elif tool_name == "get_stock_data":
            result = get_stock_data(
                tool_input["symbol"], tool_input.get("period", "1mo")
            )
        elif tool_name == "get_stock_forecast":
            result = get_stock_forecast(tool_input["symbol"])
        elif tool_name == "get_ipo_gmp":
            result = get_ipo_gmp()
        elif tool_name == "get_upcoming_ipos":
            result = get_upcoming_ipos()
        elif tool_name == "search_stock":
            result = search_stock(tool_input["query"])
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        return json.dumps(result)
    except Exception as e:
        return json.dumps({"error": str(e)})


def process_chat(messages: list[dict]) -> str:
    """
    Run an agentic loop: let Claude call tools until it produces a final text response.
    messages: list of {"role": "user"|"assistant", "content": str}
    """
    api_messages = [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]

    while True:
        response = _create_with_retry(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=api_messages,
        )

        if response.stop_reason == "end_turn":
            # Extract text content
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return "I couldn't generate a response. Please try again."

        if response.stop_reason == "tool_use":
            # Add assistant's tool-use response to history
            api_messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_output = _execute_tool(block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": tool_output,
                    })

            # Add tool results and continue loop
            api_messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop reason
        return "An unexpected error occurred. Please try again."
