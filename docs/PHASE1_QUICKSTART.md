# Phase 1 Quick Start Guide

**Status:** Complete ✓  
**Date:** November 7, 2025

This guide demonstrates how to reproduce the Phase 1 database setup from scratch.

---

## Prerequisites

Ensure you have installed:
- Python 3.9+
- MongoDB (local, Docker, or Atlas cluster access)
- Redis (local or Docker)

---

## Step 1: Environment Setup

```bash
# Clone repository
git clone https://github.com/AndreChuabio/NoSQL_Portfolio_Risk_Analytics.git
cd NoSQL_Portfolio_Risk_Analytics

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

---

## Step 2: Configure Database Connections

### MongoDB

Set your MongoDB connection string:

```bash
# For local MongoDB
export MONGODB_URI="mongodb://root:example@localhost:27017/?authSource=admin"

# OR for MongoDB Atlas
export MONGODB_URI="mongodb+srv://<username>:<password>@cluster.mongodb.net/"
```

### Redis

Start Redis (if not already running):

```bash
# Local installation
redis-server

# OR via Docker
docker run -d -p 6379:6379 redis:7.2-alpine
```

---

## Step 3: Fetch Price Data

Download 2 years of OHLCV data for 20 tickers:

```bash
python src/ingestion/fetch_prices.py
```

**Output:**
- Creates `data/raw/prices_YYYYMMDD.parquet`
- Downloads data for 20 tickers (AAPL, MSFT, GOOGL, NVDA, META, JPM, BAC, GS, XOM, CVX, COP, etc.)
- Approximately 500 trading days per ticker

---

## Step 4: Load Data into MongoDB

Populate MongoDB collections with prices and portfolio holdings:

```bash
python src/ingestion/load_mongodb.py
```

**Output:**
- Creates `portfolio_risk` database
- Populates `prices` collection with ~10,020 documents
- Populates `portfolio_holdings` collection with ~1,503 snapshots
- Creates indexes on `(ticker, date)` and `(portfolio_id, date)`

---

## Step 5: Verify Database Setup

### MongoDB Verification

```python
from pymongo import MongoClient
from config.mongodb_config import get_mongo_client, get_database

# Connect to MongoDB
client = get_mongo_client()
db = get_database(client)

# Check price count
price_count = db.prices.count_documents({})
print(f"Price documents: {price_count}")  # Expected: ~10,020

# Check portfolio holdings count
holdings_count = db.portfolio_holdings.count_documents({})
print(f"Portfolio holdings: {holdings_count}")  # Expected: ~1,503

# Verify indexes
print("Prices indexes:", list(db.prices.list_indexes()))
print("Holdings indexes:", list(db.portfolio_holdings.list_indexes()))
```

### Redis Verification

```bash
redis-cli ping
# Expected output: PONG
```

---

## Phase 1 Deliverables

### Database Collections

| Collection | Documents | Index | Purpose |
|------------|-----------|-------|---------|
| `prices` | 10,020 | `(ticker, date)` | Historical OHLCV data |
| `portfolio_holdings` | 1,503 | `(portfolio_id, date)` | Daily portfolio snapshots |

### Data Coverage

- **Tickers:** 20 (across Technology, Financials, Energy, Consumer, Benchmarks)
- **Date Range:** ~2 years (500+ trading days)
- **Portfolios:** 3 synthetic portfolios with daily rebalancing
- **File Format:** Parquet (efficient columnar storage)

### Code Artifacts

- `src/ingestion/fetch_prices.py` - Yahoo Finance data downloader
- `src/ingestion/load_mongodb.py` - MongoDB ingestion pipeline
- `config/mongodb_config.py` - Database connection utilities
- `config/portfolios.yaml` - Portfolio configuration definitions

---

## Expected Runtime

- **Price fetch:** 30-60 seconds (depends on network)
- **MongoDB load:** 10-20 seconds
- **Total setup time:** < 2 minutes

---

## Troubleshooting

### MongoDB Connection Failed

```bash
# Verify MongoDB is running
mongosh --eval "db.adminCommand('ping')"

# Check environment variable
echo $MONGODB_URI
```

### Missing Price Data

```bash
# Ensure data directory exists
ls -la data/raw/

# Re-run fetch if needed
python src/ingestion/fetch_prices.py
```

### Import Errors

```bash
# Ensure you're in the project root
pwd  # Should end in NoSQL_Portfolio_Risk_Analytics

# Verify virtual environment is activated
which python  # Should point to .venv/bin/python
```

---

## Next Steps (Phase 2)

Phase 1 provides the data foundation. Phase 2 will implement:
- VaR calculation engine
- Expected Shortfall computation
- Sharpe ratio and Beta metrics
- Redis caching layer
- Unit tests

Estimated timeline: 1 week
