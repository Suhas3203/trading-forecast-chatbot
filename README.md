# TradeBot — Market Intelligence Chatbot

AI-powered chatbot for Indian & global market data, IPO GMP, and stock forecasts.

## Stack

| Layer | Tech |
|---|---|
| Frontend | React 18 + Vite + Tailwind CSS |
| Backend | Python FastAPI |
| AI | Claude Sonnet 4.6 (Anthropic) with tool use |
| Data | yfinance (free, no key) + web scraping for IPO GMP |
| Package manager | Poetry (venv isolated per project) |

## Prerequisites

- Python 3.11+
- Node.js 18+
- Anthropic API key — get one at https://console.anthropic.com

## Getting Started

### 1. Backend

```bash
cd backend

# Copy env file and set your API key
cp .env.example .env
# Edit .env → set ANTHROPIC_API_KEY=your_key_here

# First time: installs Poetry + all dependencies, then starts server
bash setup.sh --clean

# Subsequent runs: activates .venv and starts server
bash setup.sh
```

Or from the project root:

```bash
# Auto-runs --clean if .venv is missing, otherwise just starts
bash start-backend.sh
```

Server runs at http://localhost:8000

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Or from the project root:

```bash
bash start-frontend.sh
```

Open http://localhost:5173

## Project Structure

```
trading-chatbot/
├── backend/
│   ├── services/
│   │   ├── claude_service.py   # Claude API + tool use orchestration
│   │   ├── market_service.py   # yfinance — indices & stock data
│   │   └── ipo_service.py      # IPO GMP scraping
│   ├── main.py                 # FastAPI app + routes
│   ├── pyproject.toml          # Poetry dependencies
│   ├── poetry.toml             # Forces .venv inside backend/
│   ├── setup.sh                # Setup & start script
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/         # Header, ChatWindow, MessageBubble, QuickActions
│   │   ├── api/chat.ts         # API client
│   │   └── types/index.ts
│   └── package.json
└── start-backend.sh            # Root-level convenience start script
```

## Features

- **Indian indices** — NIFTY 50, SENSEX, BANK NIFTY + 7 sector indices (live)
- **Global indices** — S&P 500, NASDAQ, Dow Jones, FTSE 100, Nikkei, DAX, Hang Seng, etc.
- **IPO GMP** — Grey Market Premium scraped live from investorgain.com
- **Upcoming IPOs** — price band, open/close dates, lot size
- **Stock analysis** — price, volume, 52W high/low, PE ratio, sector (NSE/BSE + US)
- **Technical forecast** — SMA 20/50, RSI, support/resistance, BULLISH/BEARISH signal
- **Stock search** — find any stock by company name
- **Content filtering** — off-topic or inappropriate queries are declined by Claude

## Backend Scripts

| Command | What it does |
|---|---|
| `bash setup.sh --clean` | Installs Poetry, installs all packages, starts server |
| `bash setup.sh` | Activates `.venv`, runs pre-commit, starts server |
| `bash start-backend.sh` | From project root — runs `--clean` if needed, else `setup.sh` |

## Useful Poetry Commands

```bash
poetry add <package>            # add a dependency
poetry add --group dev <pkg>    # add a dev-only dependency
poetry show --tree              # view dependency tree
poetry env info                 # show venv path
```
