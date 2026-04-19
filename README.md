# Finance API

A personal portfolio analytics API built with FastAPI, providing factor model analysis, portfolio monitoring, and stock screening capabilities.

## Overview

REST API that serves as the backend for portfolio management tools. Provides endpoints for factor model regression, portfolio drift detection, rebalancing recommendations, and universe screening.

---

## Features

- **Factor Models** — Fama-French 5-factor + momentum regression for individual assets and portfolios across multiple regions (US, Europe, Japan, APAC, Emerging Markets, Global)
- **Portfolio Monitoring** — detect factor drift, check if rebalancing is sufficient, identify sell/buy candidates
- **Stock Screening** — dynamically generate candidate universes from factor gaps and fundamental criteria
- **Multi-region Support** — regional factor data from Kenneth French's data library
- **Caching** — Redis-backed caching for factor regression results

---

## Stack

| Component | Technology |
|-----------|------------|
| API | FastAPI |
| Database | TimescaleDB (PostgreSQL) |
| Cache | Redis |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Data | yfinance, Kenneth French Data Library, FRED, FMP, OpenFIGI |
| Dashboard | [finance-dashboard](link-to-dashboard-repo) |

---

## Project Structure
```
src/
├── api/                        # FastAPI application
│   ├── main.py                 # app setup, middleware, error handlers
│   ├── dependencies.py         # shared dependencies, auth
│   ├── routers/                # endpoint routers by domain
│   │   ├── assets.py
│   │   ├── factors.py
│   │   ├── portfolio.py
│   │   └── screening.py
│   └── schemas/                # Pydantic request/response models
├── data/
│   ├── database/               # SQLAlchemy models and engine
│   ├── repositories/           # database read/write functions
│   │   ├── assets.py
│   │   ├── prices.py
│   │   ├── returns.py
│   │   ├── factors.py
│   │   ├── macro.py
│   │   ├── enriched.py
│   │   └── regimes.py
│   └── config.py               # exchange maps, constants
├── integrations/               # external API/library clients
│   ├── base.py                 # shared HTTP client base class
│   ├── yf.py                   # yfinance
│   ├── fred.py                 # FRED macro data
│   ├── french.py               # Kenneth French data library
│   ├── fmp/                    # Financial Modeling Prep
│   │   ├── client.py
│   │   └── profile.py
│   └── openfigi/               # OpenFIGI identifier mapping
│       ├── client.py
│       └── figi.py
├── services/
│   ├── sync/                   # fetch + store pipelines
│   │   ├── yf.py
│   │   ├── french.py
│   │   ├── fred.py
│   │   └── main.py             # orchestrates all syncs + enrichment
│   ├── enrichment/             # asset enrichment pipelines
│   │   ├── isin.py
│   │   ├── figi.py
│   │   ├── region.py
│   │   └── main.py
│   └── transforms/             # pure data transformations
│       └── returns.py
├── models/
│   └── factor/                 # factor regression logic
│       ├── loader.py           # data alignment
│       ├── regression.py       # OLS regression
│       └── service.py          # orchestration + caching
├── config.py                   # environment variable helpers
└── logger.py                   # logging setup
```

---

## API Endpoints

### Assets
```
GET  /v1/assets/              # list all assets
GET  /v1/assets/{ticker}      # get single asset
```

### Factors
```
GET  /v1/factors/{ticker}     # factor regression for single asset
GET  /v1/factors/portfolio    # factor regression for portfolio
```

### Portfolio
```
GET  /v1/portfolio/exposure   # current factor exposure
GET  /v1/portfolio/gap        # gap vs target
GET  /v1/portfolio/diagnose   # rebalance or add asset recommendation
```

### Screening
```
POST /v1/screening/candidates # generate candidates from factor gap
GET  /v1/screening/universe   # list current universe
```

---

## Setup

### Requirements
- Python 3.12+
- Docker + Docker Compose
- uv

### Installation
```bash
git clone https://github.com/username/finance-api
cd finance-api
uv sync
```

### Configuration
Create a `.env` file based on `.env.example`:
```
DB_URL=postgresql://postgres:password@localhost:5433/finance
REDIS_URL=redis://localhost:6380
API_KEY=your-api-key-here
```

### Running with Docker
```bash
docker compose up --build
```

### Running locally
```bash
# start dependencies
docker compose up timescaledb redis -d

# run migrations
uv run alembic upgrade head

# start API
uv run fastapi dev src/api/main.py
```

### Syncing data
```bash
# full sync (prices, factors, macro) + enrichment (ISIN, FIGI, region)
uv run python -m src.services.sync.main
```

---

## Database Schema

| Table | Description |
|-------|-------------|
| `assets` | Static asset metadata, region, ISIN |
| `prices` | Daily OHLCV price data |
| `returns` | Computed daily and monthly returns |
| `factor_returns` | Fama-French factor returns by region and frequency |

---

## Authentication

All endpoints require an API key passed in the `X-API-Key` header:
```
X-API-Key: your-api-key-here
```

---

## Development

### Running migrations
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Project board
Tasks and roadmap are tracked on the [GitHub Projects board](link-to-project-board).
