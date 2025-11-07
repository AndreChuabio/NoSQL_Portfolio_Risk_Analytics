# NoSQL Portfolio Risk Analytics Dashboard

![Phase 3 Complete](https://img.shields.io/badge/Phase%203-Complete-brightgreen)
![MongoDB Atlas](https://img.shields.io/badge/MongoDB%20Atlas-Deployed-success)
![Redis Cloud](https://img.shields.io/badge/Redis%20Cloud-Configured-success)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Tests](https://img.shields.io/badge/Tests-28%2F28%20Passing-brightgreen)
![Dashboard](https://img.shields.io/badge/Dashboard-Live-blue)

A portfolio-level risk analytics system demonstrating NoSQL advantages over traditional relational databases using MongoDB for persistent storage and Redis for real-time caching of financial risk metrics.

**Authors:** Andre Chuabio, Aengus Martin Donaire  
**Contact:** andre102599@gmail.com  
**GitHub:** [AndreChuabio/NoSQL_Portfolio_Risk_Analytics](https://github.com/AndreChuabio/NoSQL_Portfolio_Risk_Analytics)

---

## Project Overview

This system handles real-time and historical financial risk metrics for multi-asset portfolios, demonstrating how NoSQL databases excel at:
- Irregular time series data with varying schemas
- Multi-dimensional analytics (VaR, Sharpe, Beta, Expected Shortfall)
- Low-latency requirements for portfolio managers
- Scalable aggregation pipelines for complex calculations

### Architecture

**Dual-Database Pattern:**
- **MongoDB Atlas**: Cloud-hosted persistent storage for historical prices, portfolio holdings, and computed risk metrics
- **Redis Cloud**: In-memory cache for latest metrics with TTL expiration (60s)

**Data Flow:**
1. Price data (OHLCV) ingested into MongoDB `prices` collection
2. Portfolio snapshots stored in `portfolio_holdings` collection
3. Risk engine computes VaR, Sharpe, Beta, ES and stores in `risk_metrics` collection
4. Latest metrics pushed to Redis with 60-second TTL
5. Dashboard reads historical data from MongoDB, real-time from Redis

---

## Current Status

**Phase 3 Complete** - Dashboard & Performance Analysis ✅

### Phase 1 Deliverables (Week 1) ✅
- Repository structure with src, config, tests, docs, notebooks, and data directories
- Price ingestion pipeline fetching 2 years of OHLCV data for 20 tickers from Yahoo Finance
- MongoDB collections populated:
  - `prices`: **10,020 documents** (20 tickers × ~501 trading days)
  - `portfolio_holdings`: **1,503 snapshots** (3 portfolios × ~501 days)
- Proper indexing on `(ticker, date)` and `(portfolio_id, date)`
- MongoDB Atlas cluster configured for cloud deployment
- Redis Cloud configured and verified

### Phase 2 Deliverables (Week 2) ✅
- **Risk Calculation Modules:**
  - `var_calculator.py`: Monte Carlo VaR (95% confidence, 1000 simulations), Expected Shortfall, Portfolio Volatility
  - `performance_metrics.py`: Sharpe Ratio, Beta vs SPY, Rolling Volatility
  - `cache_manager.py`: Redis integration with TTL and atomic operations
  - `compute_historical_metrics.py`: Backfill orchestration with batch processing
- **Testing:** 28/28 unit tests passing (100% success rate, 0.49s execution time)
- **Database Population:**
  - `risk_metrics`: **1,443 documents** computed (96% success rate)
  - Redis cache populated with latest metrics for all 3 portfolios
- **Performance Benchmarks:**
  - Processing rate: 1.49 snapshots/second
  - VaR computation: ~673ms per snapshot (all 4 metrics)
  - Success rate: 96.0% (60 failures due to insufficient early data)

### Phase 3 Deliverables (Week 3) ✅
- **Streamlit Dashboard (`src/dashboard/app.py`):**
  - Portfolio selector dropdown (3 portfolios)
  - Date range picker for historical window (7-365 days)
  - Real-time status cards showing latest VaR, ES, Sharpe, Beta
  - Data source indicators (Redis real-time vs MongoDB historical)
  - Interactive Plotly charts for VaR, Sharpe, Beta, Volatility trends
  - Sector exposure pie chart from portfolio holdings
  - Alert banner with configurable thresholds (VaR, Beta, Volatility, Sharpe persistence)
  - Performance metrics footer displaying query latencies
- **Query Layer (`src/dashboard/data_queries.py`):**
  - Redis-first fetching with automatic MongoDB fallback
  - Streamlit caching (60s TTL) to minimize database load
  - Historical metrics aggregation with date range filtering
- **Alert System (`src/dashboard/alerts.py`):**
  - VaR threshold checks (critical: <-2%, warning: <-1.5%)
  - Beta threshold checks (critical: >1.5, warning: >1.3)
  - Volatility threshold (warning: >30% annualized)
  - Sharpe persistence logic (negative for >10 days)
- **Dashboard Performance:**
  - Initial load time: <2 seconds (target met)
  - Redis query latency: <10ms (target met)
  - MongoDB historical query: <100ms for 60-day window (target met)

---

## Data Universe

**20 tickers across 6 sectors:**
- **Technology**: AAPL, MSFT, GOOGL, NVDA, META
- **Financials**: JPM, BAC, GS
- **Energy**: XOM, CVX, COP
- **Consumer**: WMT, KO
- **Healthcare**: JNJ, UNH
- **Industrials**: CAT, BA
- **Benchmarks**: SPY, QQQ, TLT, GLD

**3 synthetic portfolios:**
- **PORT_A_TechGrowth**: Tech-heavy (40-60% tech sector), Beta=1.27
- **PORT_B_EnergyTilt**: Energy-focused (25-40% energy sector), Beta=1.08
- **PORT_C_BalancedCore**: Diversified across sectors, Beta=1.10, Sharpe=0.26

---

## Project Structure

```
NoSQL_Project/
├── config/                 # Database and portfolio configuration
│   ├── mongodb_config.py   # MongoDB Atlas connection (env var based)
│   ├── redis_config.py     # Redis Cloud connection (env var based)
│   └── portfolios.yaml     # Portfolio definitions (3 portfolios)
├── data/
│   ├── raw/                # Downloaded price data (Parquet format)
│   └── processed/          # Reserved for future analytics
├── docs/
│   ├── TEAMMATE_SETUP.md   # Primary setup guide for team members
│   ├── ENV_SETUP_GUIDE.md  # Environment variable copy-paste reference
│   ├── PHASE1_QUICKSTART.md # Historical context for Phase 1
│   └── status/             # Project status tracking
│       ├── phase1_status.md # Phase 1 completion summary
│       └── phase2_status.md # Phase 2 completion summary
├── notebooks/              # Exploratory analysis (reserved for Phase 3)
├── src/
│   ├── ingestion/          # Data loading scripts (Phase 1)
│   │   ├── fetch_prices.py      # Yahoo Finance data downloader
│   │   ├── load_mongodb.py      # MongoDB ingestion pipeline
│   │   ├── verify_redis.py      # Redis connectivity test
│   │   └── check_redis_cache.py # Redis key inspection
│   ├── risk_engine/        # Risk calculations (Phase 2)
│   │   ├── var_calculator.py              # VaR, ES, Volatility
│   │   ├── performance_metrics.py         # Sharpe, Beta
│   │   ├── cache_manager.py               # Redis cache layer
│   │   └── compute_historical_metrics.py  # Backfill orchestration
│   ├── dashboard/          # Streamlit UI (Phase 3) ✅
│   │   ├── app.py          # Main dashboard application
│   │   ├── data_queries.py # MongoDB/Redis query layer
│   │   └── alerts.py       # Risk threshold logic
│   └── api/                # Optional REST endpoints (Phase 3)
├── tests/
│   └── test_risk_engine.py # Unit tests (28 tests, all passing)
├── requirements.txt        # Python dependencies
├── setup_env.sh            # Interactive environment setup script
├── run_dashboard.sh        # Dashboard launch script ✅
├── Proposal.md             # Detailed project proposal
└── README.md               # This file
```

---

## Quick Start

### Launching the Dashboard (Phase 3)

```bash
# Option 1: Use the launch script (recommended)
./run_dashboard.sh

# Option 2: Manual launch with PYTHONPATH
cd /Users/andrechuabio/NoSQL_Project
PYTHONPATH=$PWD streamlit run src/dashboard/app.py

# Dashboard will be available at http://localhost:8501
```

**Dashboard Features:**
- Portfolio selector (3 portfolios available)
- Real-time metrics from Redis cache (60s TTL) with MongoDB fallback
- Historical charts: VaR, Sharpe, Beta, Volatility trends
- Sector exposure breakdown (pie chart)
- Alert banner for risk threshold breaches
- Performance metrics footer showing query latencies

### For Team Members (New Setup)

**See `docs/TEAMMATE_SETUP.md` for complete setup guide.**

1. Clone repo and install dependencies
2. Get credentials from Andre (MongoDB URI, Redis host/port/password)
3. Run `source setup_env.sh` to configure environment variables
4. Verify connections with test scripts
5. Start building Phase 3 dashboard

### For Andre (Reproducing Work)

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Set environment variables (if not in ~/.zshrc)
source setup_env.sh

# 3. Verify connections
python src/ingestion/verify_redis.py
python -c "from config.mongodb_config import get_mongo_client; print(get_mongo_client().admin.command('ping'))"

# 4. Check database state
python -c "from config.mongodb_config import get_mongo_client, get_database; db = get_database(get_mongo_client()); print(f'prices: {db.prices.count_documents({})}, holdings: {db.portfolio_holdings.count_documents({})}, metrics: {db.risk_metrics.count_documents({})}')"

# 5. Re-run risk computations if needed (takes ~17 minutes)
python -m src.risk_engine.compute_historical_metrics
```

---

## Database Schema

### MongoDB Collections

#### `prices` Collection (10,020 documents)
```python
{
    "ticker": "AAPL",
    "date": ISODate("2023-10-27T00:00:00Z"),
    "open": 238.20,
    "high": 240.15,
    "low": 237.80,
    "close": 239.50,
    "volume": 45123000,
    "daily_return": 0.0054  # (close - prev_close) / prev_close
}
```
**Index**: `(ticker, date)` ascending  
**Purpose**: Historical OHLCV data for risk calculations

#### `portfolio_holdings` Collection (1,503 documents)
```python
{
    "portfolio_id": "PORT_A_TechGrowth",
    "date": ISODate("2023-10-27T00:00:00Z"),
    "assets": [
        {
            "ticker": "AAPL",
            "weight": 0.07,
            "sector": "Technology",
            "price": 238.50,
            "daily_vol": 0.022
        },
        # ... more assets
    ],
    "gross_exposure": 1.0,
    "net_exposure_by_sector": {
        "Technology": 0.40,
        "Energy": 0.15,
        # ... more sectors
    }
}
```
**Index**: `(portfolio_id, date)` descending  
**Purpose**: Daily portfolio snapshots with sector allocations

#### `risk_metrics` Collection (1,443 documents)
```python
{
    "portfolio_id": "PORT_A_TechGrowth",
    "date": ISODate("2023-12-07T00:00:00Z"),
    "VaR_95": -0.009325,  # Negative = potential loss (95% confidence)
    "expected_shortfall": -0.009325,  # Average loss beyond VaR
    "sharpe_ratio_20d": 3.4805,  # Risk-adjusted return (20-day rolling)
    "beta_vs_SPY_20d": 1.2324,  # Volatility vs SPY benchmark
    "portfolio_volatility_20d": 0.1356,  # Annualized volatility
    "simulation_params": {
        "confidence_level": 0.95,
        "method": "historical_monte_carlo",
        "n_simulations": 1000,
        "window": 20
    }
}
```
**Index**: `(portfolio_id, date)` descending  
**Purpose**: Computed risk metrics for dashboard visualization

### Redis Cache (Cloud-hosted)

**Key Naming Convention:** `<metric_type>:<portfolio_id>`

```python
# Example keys with 60-second TTL
"VaR:PORT_A_TechGrowth"      # Current VaR value with timestamp
"Sharpe:PORT_B_EnergyTilt"   # Current Sharpe Ratio
"Beta:PORT_C_BalancedCore"   # Current Beta vs SPY
"Alert:PORT_A_TechGrowth"    # Alert flags (hash)
```

**Value Format** (JSON string):
```python
{
    "current_VaR_95": -0.017801,
    "ts": "2025-11-07T14:39:06.123456Z"
}
```

**Purpose**: Low-latency access to latest metrics for dashboard

---

## Development Roadmap

### Week 1: Foundation ✅
- [x] MongoDB Atlas and Redis Cloud setup
- [x] Price data ingestion (yfinance → Parquet → MongoDB)
- [x] Portfolio snapshots generation (3 portfolios, daily rebalancing)
- [x] Database indexing for query optimization
- [x] Data validation and cleanup

### Week 2: Risk Engine ✅
- [x] VaR calculation (Monte Carlo, 95% confidence)
- [x] Expected Shortfall computation (worst 5% outcomes)
- [x] Sharpe ratio (20-day rolling, annualized)
- [x] Beta calculation (vs SPY, 20-day rolling)
- [x] Redis cache integration with TTL
- [x] Unit tests with pytest (28/28 passing)
- [x] Historical backfill (1,443 metrics computed)

### Week 3: Dashboard & Analysis (In Progress)
- [ ] Streamlit dashboard with portfolio selector
- [ ] Real-time metric display (query Redis, fallback to MongoDB)
- [ ] Historical charts (VaR, Sharpe, Beta time series using Plotly)
- [ ] Sector exposure visualization (pie/bar charts)
- [ ] Alert banners for risk threshold breaches
- [ ] Performance benchmarks (query latency measurements)
- [ ] Final report with NoSQL tradeoff analysis
- [ ] Optional: REST API with FastAPI

---

## Performance Benchmarks

| Metric | Target | Actual (Phase 2) |
|--------|--------|------------------|
| MongoDB historical query (20-day VaR) | <100ms | TBD (Phase 3) |
| Redis current metric fetch | <10ms | TBD (Phase 3) |
| VaR computation (30 assets, 1000 sims) | <500ms | ~673ms (includes all 4 metrics) |
| Batch processing rate | N/A | 1.49 snapshots/sec |
| Dashboard initial load | <2s | TBD (Phase 3) |
| Success rate (historical backfill) | >90% | 96.0% (1,443/1,503) |

---

## Testing

### Run Unit Tests
```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest tests/test_risk_engine.py -v

# Run with coverage report
pytest tests/test_risk_engine.py --cov=src.risk_engine --cov-report=term-missing
```

**Current Status:** 28/28 tests passing (100% success rate)

**Test Coverage:**
- Portfolio input validation (6 tests)
- VaR calculation (6 tests)
- Expected Shortfall (3 tests)
- Portfolio Volatility (2 tests)
- Sharpe Ratio (4 tests)
- Beta calculation (5 tests)
- Rolling volatility (2 tests)

---

## Documentation

### Setup & Operations
- **[docs/TEAMMATE_SETUP.md](docs/TEAMMATE_SETUP.md)**: Primary setup guide for new team members
- **[docs/ENV_SETUP_GUIDE.md](docs/ENV_SETUP_GUIDE.md)**: Environment variable copy-paste reference
- **[docs/PHASE1_QUICKSTART.md](docs/PHASE1_QUICKSTART.md)**: Historical context for Phase 1 setup

### Project Status
- **[docs/status/phase1_status.md](docs/status/phase1_status.md)**: Phase 1 completion summary with metrics
- **[docs/status/phase2_status.md](docs/status/phase2_status.md)**: Phase 2 completion summary with execution results

### Planning
- **[Proposal.md](Proposal.md)**: Full project proposal with problem statement and technical architecture

---

## Dependencies

### Core Libraries
```txt
pandas>=2.0.0          # Data manipulation
numpy>=1.24.0          # Numerical computing
yfinance>=0.2.0        # Price data fetching
pyarrow>=12.0.0        # Parquet file format
pymongo>=4.6.0         # MongoDB driver
redis>=4.5.0           # Redis driver
pyyaml>=6.0.0          # YAML configuration
```

### Development & Testing (future)
```txt
pytest>=7.4.0          # Unit testing
streamlit>=1.25.0      # Dashboard framework (Phase 3)
plotly>=5.0.0          # Interactive charts (Phase 3)
```

Full list in [requirements.txt](requirements.txt)

---

## Key Insights & Learnings

### Why NoSQL for Portfolio Risk?

**MongoDB Advantages:**
- **Flexible Schema**: Easily add new risk metrics without schema migrations
- **Nested Documents**: Store portfolio assets and sector exposures in single document
- **Aggregation Pipeline**: Efficient time-series queries without complex joins
- **Indexing**: Fast queries on `(portfolio_id, date)` compound index

**Redis Advantages:**
- **Sub-millisecond Latency**: Critical for real-time dashboard updates
- **TTL Expiration**: Automatic cache invalidation for stale metrics
- **Atomic Operations**: Reliable alert flag updates via hash commands

**vs Relational Databases:**
- NoSQL: ~100ms for 20-day historical query via single aggregation pipeline
- RDBMS: Would require multiple JOINs across `prices`, `holdings`, `metrics` tables
- NoSQL: Easier to handle variable asset counts per portfolio (nested arrays)
- RDBMS: Complex EAV model or JSON columns with limited query capabilities

---

## Contributing

This is an academic project for demonstration purposes. For questions or collaboration:
- **Email**: andre102599@gmail.com
- **GitHub**: [@AndreChuabio](https://github.com/AndreChuabio)

---

## License

Educational project - contact authors for usage permissions.

---

## Acknowledgments

Built as part of NoSQL database systems coursework, demonstrating practical applications of document stores and in-memory caching for financial risk analytics.

**Technologies:**
- MongoDB Atlas (cloud document database)
- Redis Cloud (cloud in-memory cache)
- Python 3.9+ with pandas/numpy for vectorized computations
- pytest for comprehensive test coverage

---

**Last Updated:** 2025-11-07  
**Current Phase:** Phase 2 Complete, Phase 3 Dashboard Development Ready
