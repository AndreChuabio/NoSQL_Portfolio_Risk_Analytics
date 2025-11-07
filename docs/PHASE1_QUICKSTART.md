# Phase 1 Quick Start Guide

**Status:** Complete ✓  
**Date:** November 7, 2025  
**Infrastructure:** Cloud-based (MongoDB Atlas + Redis Cloud)

This guide demonstrates how to reproduce the Phase 1 database setup from scratch using cloud databases.

---

## Prerequisites

- Python 3.9+
- MongoDB Atlas account (free tier: https://www.mongodb.com/cloud/atlas/register)
- Redis Cloud account (free tier: https://redis.com/try-free)

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

### MongoDB Atlas Setup

1. **Create MongoDB Atlas Cluster** (if not already done):
   - Go to https://cloud.mongodb.com
   - Create free M0 cluster (takes 3-5 minutes to provision)
   - Navigate to Database Access → Add Database User (create username/password)
   - Navigate to Network Access → Add IP Address → Allow Access from Anywhere (0.0.0.0/0)

2. **Get Connection String**:
   - Click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string (format: `mongodb+srv://...`)
   - Replace `<password>` with your database user password

3. **Set Environment Variable**:
   ```bash
   export MONGODB_URI="mongodb+srv://<username>:<password>@clusterac1.od00ttk.mongodb.net/?retryWrites=true&w=majority"
   ```

   **Tip**: Add to `~/.zshrc` to persist across terminal sessions:
   ```bash
   echo 'export MONGODB_URI="mongodb+srv://..."' >> ~/.zshrc
   source ~/.zshrc
   ```

### Redis Cloud Setup

1. **Create Redis Cloud Database**:
   - Go to https://redis.com/try-free
   - Sign up for free account (30MB free tier)
   - Create new subscription → Choose "Fixed" plan (free)
   - Create database → Note the **Public Endpoint** and **Default User Password**

2. **Set Environment Variables**:
   ```bash
   export REDIS_HOST="redis-12345.c123.us-east-1-1.ec2.redns.redis-cloud.com"
   export REDIS_PORT="12345"
   export REDIS_PASSWORD="your_redis_password"
   ```

   **Tip**: Add to `~/.zshrc`:
   ```bash
   echo 'export REDIS_HOST="redis-12345..."' >> ~/.zshrc
   echo 'export REDIS_PORT="12345"' >> ~/.zshrc
   echo 'export REDIS_PASSWORD="your_password"' >> ~/.zshrc
   source ~/.zshrc
   ```

**Note**: Phase 1 only requires MongoDB. Redis will be used in Phase 2 for caching risk metrics.

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

### Redis Verification (Optional - Phase 2)

**Phase 1 does not require Redis.** Verification will be needed when starting Phase 2.

To verify Redis Cloud connectivity once configured:

```bash
# Run Python verification script
PYTHONPATH=/Users/andrechuabio/NoSQL_Project python src/ingestion/verify_redis.py
```

Expected output:
```
✓ Redis PING successful
✓ String write/read successful
✓ TTL set successfully
✓ JSON cache successful
✓ Hash operations successful
✓ Cleanup successful
Redis Verification: ALL TESTS PASSED
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

### MongoDB Atlas Connection Failed

```bash
# Check environment variable is set
echo $MONGODB_URI

# Test connection with mongosh (if installed)
mongosh "$MONGODB_URI" --eval "db.adminCommand('ping')"

# Verify from Python
python -c "from config.mongodb_config import get_mongo_client; print('Connected:', get_mongo_client().admin.command('ping'))"
```

**Common issues:**
- Password contains special characters → URL-encode them (e.g., `@` becomes `%40`)
- IP not whitelisted → Add 0.0.0.0/0 in Atlas Network Access
- Wrong database user credentials → Check Database Access in Atlas

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
