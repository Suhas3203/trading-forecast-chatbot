from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise RuntimeError("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and add your key.")

from services.claude_service import process_chat
from services.market_service import get_market_overview, get_stock_data, get_stock_forecast
from services.ipo_service import get_ipo_gmp, get_upcoming_ipos

app = FastAPI(title="TradeBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]


class ChatResponse(BaseModel):
    reply: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="Messages cannot be empty")
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    try:
        reply = process_chat(messages)
        return ChatResponse(reply=reply)
    except Exception as e:
        err = str(e)
        if "rate_limit" in err or "429" in err:
            raise HTTPException(
                status_code=429,
                detail="Anthropic API rate limit reached. Please wait a moment and try again.",
            )
        raise HTTPException(status_code=500, detail=err)


@app.get("/api/market/overview")
async def market_overview(market: str = "both"):
    return get_market_overview(market)


@app.get("/api/market/stock/{symbol}")
async def stock_data(symbol: str, period: str = "1mo"):
    return get_stock_data(symbol, period)


@app.get("/api/market/forecast/{symbol}")
async def stock_forecast(symbol: str):
    return get_stock_forecast(symbol)


@app.get("/api/ipo/gmp")
async def ipo_gmp():
    return get_ipo_gmp()


@app.get("/api/ipo/upcoming")
async def upcoming_ipos():
    return get_upcoming_ipos()


@app.get("/health")
async def health():
    return {"status": "ok", "service": "TradeBot API"}
