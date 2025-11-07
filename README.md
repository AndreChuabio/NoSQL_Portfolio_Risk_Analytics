# NoSQL Portfolio Risk Analytics Dashboard

![Phase 1 Complete](https://img.shields.io/badge/Phase%201-Complete-brightgreen)
![MongoDB](https://img.shields.io/badge/MongoDB-Deployed-success)
![Redis](https://img.shields.io/badge/Redis-Configured-success)
![Python](https://img.shields.io/badge/Python-3.9%2B-blue)

A portfolio-level risk analytics system demonstrating NoSQL advantages over traditional relational databases using MongoDB for persistent storage and Redis for real-time caching of financial risk metrics.

**Authors:** Andre Chuabio, Aengus Martin Donaire  
**Contact:** andre102599@gmail.com  
**GitHub:** [AndreChuabio](https://github.com/AndreChuabio)

---

## Project Overview

This system handles real-time and historical financial risk metrics for multi-asset portfolios, demonstrating how NoSQL databases excel at:
- Irregular time series data
- Multi-dimensional analytics (VaR, Sharpe, Beta, Expected Shortfall)
- Low-latency requirements for portfolio managers

### Architecture

**Dual-Database Pattern:**
- **MongoDB**: Persistent storage for historical prices, portfolio holdings, and computed risk metrics
- **Redis**: In-memory cache for latest metrics with TTL expiration (60s)

**Data Flow:**
1. Price data (OHLCV) ingested into MongoDB `prices` collection
2. Portfolio snapshots stored in `portfolio_holdings` collection
3. Risk engine computes VaR, Sharpe, Beta and stores in `risk_metrics` collection
4. Latest metrics pushed to Redis with 60-second TTL
5. Dashboard reads historical data from MongoDB, real-time from Redis

---

## Current Status

**Phase 1 Complete** (Week 1 of 3) - Environment and Data Foundation

### Deliverables Completed
- Repository structure with src, config, tests, docs, notebooks, and data directories
- Price ingestion pipeline fetching 2 years of OHLCV data for 20 tickers from Yahoo Finance
- MongoDB collections populated with 10,020 price documents and 1,503 portfolio holdings snapshots
- Proper indexing on `(ticker, date)` and `(portfolio_id, date)`
- MongoDB Atlas cluster configured for cloud deployment
- Redis container running and accessible
- Full project documentation including proposal, runbooks, and status tracking

### Data Universe
20 tickers across sectors:
- **Technology**: AAPL, MSFT, GOOGL, NVDA, META
- **Financials**: JPM, BAC, GS
- **Energy**: XOM, CVX, COP
- **Consumer**: WMT, KO
- **Healthcare**: JNJ, UNH
- **Industrials**: CAT, BA
- **Benchmarks**: SPY, QQQ, TLT, GLD

---

## Project Structure

```
NoSQL_Project/
├── config/                 # Database and portfolio configuration
│   ├── mongodb_config.py   # MongoDB connection settings
│   ├── redis_config.py     # Redis connection settings
│   └── portfolios.yaml     # Portfolio definitions
├── data/
│   ├── raw/                # Downloaded price data (Parquet)
│   └── processed/          # Cleaned data ready for analytics
├── docs/
│   ├── runbooks/           # Operational guides
│   │   └── container_setup.md
│   └── status/             # Project status tracking
│       └── phase1_status.md
├── notebooks/              # Exploratory analysis
├── src/
│   ├── ingestion/          # Data loading scripts
│   │   ├── fetch_prices.py
│   │   └── load_mongodb.py
│   ├── risk_engine/        # Risk calculations (Week 2)
│   ├── api/                # REST endpoints (Week 3)
│   └── dashboard/          # Streamlit UI (Week 3)
├── tests/                  # Unit and integration tests
├── requirements.txt        # Python dependencies
├── Proposal.md            # Detailed project proposal
└── README.md              # This file
```

---

## Setup Instructions

### Prerequisites
- Python 3.9+
- MongoDB (Docker or Atlas cluster)
- Redis (Docker or local install)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/AndreChuabio/NoSQL_Project.git
   cd NoSQL_Project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure MongoDB connection**
   
   Set environment variable for MongoDB URI:
   ```bash
   export MONGODB_URI="mongodb://root:example@localhost:27017/"
   # OR for Atlas:
   export MONGODB_URI="mongodb+srv://<user>:<password>@cluster.mongodb.net/"
   ```

5. **Start Redis**
   ```bash
   redis-server
   # OR via Docker:
   docker run -d -p 6379:6379 redis:7.2-alpine
   ```

### Running the Data Pipeline

1. **Fetch price data**
   ```bash
   python src/ingestion/fetch_prices.py
   ```
   This downloads 2 years of OHLCV data and saves to `data/raw/prices_YYYYMMDD.parquet`

2. **Load data into MongoDB**
   ```bash
   python src/ingestion/load_mongodb.py
   ```
   This creates collections, indexes, and populates with price and portfolio data

---

## Technical Details

### MongoDB Collections

#### `prices` Collection
```python
{
    "ticker": "AAPL",
    "date": ISODate("2025-10-27T00:00:00Z"),
    "open": 238.20,
    "high": 240.15,
    "low": 237.80,
    "close": 239.50,
    "volume": 45123000,
    "returns": 0.0054
}
```
**Index**: `(ticker, date)` ascending

#### `portfolio_holdings` Collection
```python
{
    "portfolio_id": "PORT_A",
    "date": ISODate("2025-10-27T00:00:00Z"),
    "assets": [
        {
            "ticker": "AAPL",
            "weight": 0.07,
            "sector": "Technology",
            "price": 238.50,
            "daily_vol": 0.022
        }
    ],
    "gross_exposure": 1.25,
    "net_exposure_by_sector": {
        "Technology": 0.40,
        "Energy": 0.15
    }
}
```
**Index**: `(portfolio_id, date)` descending

### Redis Key Patterns

```
VaR:<portfolio_id>          # Current 95% VaR
Sharpe:<portfolio_id>       # 20-day Sharpe ratio
Alert:<portfolio_id>        # Active alerts
```
All keys have 60-second TTL.

---

## Development Roadmap

### Week 1: Foundation ✓
- [x] MongoDB and Redis setup
- [x] Price data ingestion
- [x] Portfolio snapshots generation
- [x] Database indexing
- [x] Data validation

### Week 2: Risk Engine (In Progress)
- [ ] VaR calculation (Monte Carlo, 95% confidence)
- [ ] Expected Shortfall computation
- [ ] Sharpe ratio (20-day rolling)
- [ ] Beta calculation (vs SPY)
- [ ] Redis cache integration
- [ ] Unit tests with pytest

### Week 3: Dashboard & Analysis
- [ ] Streamlit dashboard
- [ ] Real-time metric display
- [ ] Historical charts
- [ ] Sector exposure visualization
- [ ] Performance benchmarks
- [ ] Final report

---

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| MongoDB historical query | <100ms | TBD |
| Redis current metric | <10ms | TBD |
| VaR computation (30 assets) | <500ms | TBD |
| Dashboard initial load | <2s | TBD |

---

## Testing

Run unit tests:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest --cov=src tests/
```

---

## Documentation

- **[Proposal.md](Proposal.md)**: Full project proposal with problem statement and technical architecture
- **[docs/status/phase1_status.md](docs/status/phase1_status.md)**: Phase 1 completion summary with metrics
- **[docs/PHASE1_QUICKSTART.md](docs/PHASE1_QUICKSTART.md)**: Step-by-step guide to reproduce Phase 1 setup
- **[docs/runbooks/container_setup.md](docs/runbooks/container_setup.md)**: Docker setup guide (optional)

---

## Dependencies

Key libraries:
- **Data Processing**: pandas, numpy, yfinance, pyarrow
- **Databases**: pymongo, redis
- **Configuration**: pyyaml

Full list in [requirements.txt](requirements.txt)

---

## Contributing

This is an academic project for demonstration purposes. For questions or collaboration:
- Email: andre102599@gmail.com
- GitHub: [@AndreChuabio](https://github.com/AndreChuabio)

---

## License

Educational project - contact authors for usage permissions.

---

## Acknowledgments

Built as part of NoSQL database systems coursework, demonstrating practical applications of document stores and in-memory caching for financial risk analytics.
