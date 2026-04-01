#!/usr/bin/env bash

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${GREEN}[setup]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC}  $*"; }
error() { echo -e "${RED}[error]${NC} $*"; exit 1; }

if [ "$1" == "--clean" ]; then

    info "Installing poetry"
    python -m pip install poetry

    info "Installing libraries"
    python -m poetry install --no-cache

fi

if [ ! -f ".env" ]; then
    cp .env.example .env
    warn ".env created — set your ANTHROPIC_API_KEY in backend/.env before continuing"
    exit 1
fi

info "Starting server"
source .venv/Scripts/activate
pre-commit install
uvicorn main:app --reload --port 8000
