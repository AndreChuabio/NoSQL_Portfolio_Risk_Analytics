# Portfolio Risk Analytics - Quick Start Guide

**Last Updated:** 2025-11-07  
**Status:** Phase 3 Complete - Production Ready

---

## Get Started in 3 Commands

```bash
# 1. Clone and setup
git clone https://github.com/AndreChuabio/NoSQL_Portfolio_Risk_Analytics.git
cd NoSQL_Portfolio_Risk_Analytics
pip install -r requirements.txt

# 2. Configure environment (get credentials from team)
source setup_env.sh

# 3. Launch dashboard
./run_dashboard.sh
```

**Dashboard opens at:** http://localhost:8501

---

## What You Get

### Real-Time Portfolio Risk Dashboard
- **3 Portfolios:** Tech-heavy, Energy-focused, Balanced
- **4 Risk Metrics:** VaR (95%), Expected Shortfall, Sharpe Ratio, Beta
- **Historical Trends:** Interactive charts with 2 years of data
- **Smart Alerts:** Color-coded warnings when thresholds breached
- **Dual Storage:** Redis cache (60s TTL) + MongoDB persistent storage

### Key Features
- Portfolio selector dropdown  
- Adjustable date range (7-365 days)  
- Real-time metric cards with data source indicators  
- 4 interactive Plotly charts (zoom, pan, tooltips)  
- Sector exposure pie chart  
- Alert system with configurable thresholds  
- Performance metrics footer (query latencies)  

---

## Project Structure

```
NoSQL_Project/
├── src/
│   ├── dashboard/          # Streamlit UI (Phase 3)
│   │   ├── app.py          # Main dashboard
│   │   ├── data_queries.py # MongoDB/Redis queries
│   │   └── alerts.py       # Alert logic
│   ├── risk_engine/        # Risk calculations (Phase 2)
│   │   ├── var_calculator.py
│   │   ├── performance_metrics.py
│   │   └── compute_historical_metrics.py
│   └── ingestion/          # Data loading (Phase 1)
│       ├── fetch_prices.py
│       └── load_mongodb.py
├── config/
│   ├── mongodb_config.py   # MongoDB Atlas connection
│   ├── redis_config.py     # Redis Cloud connection
│   └── portfolios.yaml     # Portfolio definitions
├── docs/
│   ├── TEAMMATE_SETUP.md   # Detailed setup for teammates
│   ├── status/
│   │   ├── phase3_status.md       # Phase 3 completion summary
│   │   └── phase3_benchmarks.md   # Performance metrics
│   └── screenshots/        # Dashboard screenshots
├── tests/
│   └── test_risk_engine.py # 28/28 tests passing
├── run_dashboard.sh        # One-click dashboard launch
└── requirements.txt        # Python dependencies
```

---

## Data Overview

### MongoDB Collections

| Collection | Documents | Description |
|------------|-----------|-------------|
| `prices` | 10,020 | OHLCV data for 20 tickers (2 years) |
| `portfolio_holdings` | 1,503 | Daily snapshots for 3 portfolios |
| `risk_metrics` | 1,443 | Computed VaR, Sharpe, Beta, ES |

### Redis Cache (60s TTL)

| Key Pattern | Example | Purpose |
|-------------|---------|---------|
| `VaR:<portfolio_id>` | `VaR:PORT_A_TechGrowth` | Latest VaR value |
| `Sharpe:<portfolio_id>` | `Sharpe:PORT_B_EnergyTilt` | Latest Sharpe ratio |
| `Beta:<portfolio_id>` | `Beta:PORT_C_BalancedCore` | Latest Beta vs SPY |

---

## Portfolios Available

### PORT_A_TechGrowth
- **Strategy:** Technology-heavy growth
- **Sector Allocation:** 40-60% Technology, 5-15% Energy
- **Characteristics:** High beta (1.27), aggressive
- **Rebalance:** Weekly

### PORT_B_EnergyTilt
- **Strategy:** Energy sector focus
- **Sector Allocation:** 25-40% Energy, 10-25% Technology
- **Characteristics:** Moderate beta (1.08), value-oriented
- **Rebalance:** Monthly

### PORT_C_BalancedCore
- **Strategy:** Diversified across sectors
- **Sector Allocation:** 20-35% Technology, 15-25% Financials, 10-20% Energy
- **Characteristics:** Balanced beta (1.10), Sharpe 0.26
- **Rebalance:** Monthly

---

## Risk Metrics Explained

### Value at Risk (VaR 95%)
- **What:** Maximum expected loss at 95% confidence level
- **Range:** -0.5% to -3% (negative = loss)
- **Alert:** Critical if < -2%
- **Use Case:** Daily loss limit setting

### Expected Shortfall (ES)
- **What:** Average loss beyond VaR threshold
- **Range:** Typically worse than VaR
- **Alert:** Informational
- **Use Case:** Tail risk assessment

### Sharpe Ratio (20-day)
- **What:** Risk-adjusted return measure
- **Range:** -1.0 to 5.0 (higher = better)
- **Alert:** Warning if negative >10 days
- **Use Case:** Performance comparison

### Beta vs SPY (20-day)
- **What:** Systematic risk relative to S&P 500
- **Range:** 0.5 to 2.0 (1.0 = market-neutral)
- **Alert:** Warning if > 1.3, Critical if > 1.5
- **Use Case:** Portfolio sensitivity analysis

---

## Performance Benchmarks

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Dashboard load time | <2s | ~1.5s | Pass |
| Redis query | <10ms | 5-8ms | Pass |
| MongoDB query | <100ms | 145-480ms | Cloud overhead |
| Chart rendering | <500ms | 100-150ms | Pass |

**Note:** MongoDB latency higher due to cloud hosting (Atlas M0 free tier). Local deployment would meet <100ms target.

---

## Common Commands

### Database Verification
```bash
# Check MongoDB connection
python -c "from config.mongodb_config import get_mongo_client; print(get_mongo_client().admin.command('ping'))"

# Check Redis connection
python src/ingestion/verify_redis.py

# View database contents
python -c "from config.mongodb_config import get_mongo_client, get_database; db = get_database(get_mongo_client()); print(f'Prices: {db.prices.count_documents({})}, Holdings: {db.portfolio_holdings.count_documents({})}, Metrics: {db.risk_metrics.count_documents({})}')"
```

### Re-compute Risk Metrics (if needed)
```bash
# Takes ~17 minutes to process all 1,503 snapshots
python -m src.risk_engine.compute_historical_metrics
```

### Run Tests
```bash
# All 28 tests should pass
python -m pytest tests/test_risk_engine.py -v
```

### Dashboard Operations
```bash
# Launch dashboard
./run_dashboard.sh

# Stop dashboard
pkill -f streamlit

# View dashboard logs
PYTHONPATH=$PWD streamlit run src/dashboard/app.py > dashboard.log 2>&1 &
tail -f dashboard.log
```

---

## Troubleshooting

### Dashboard won't start
```bash
# 1. Check environment variables
echo $MONGODB_URI
echo $REDIS_HOST

# 2. Verify database connections
python src/ingestion/verify_redis.py

# 3. Check Python path
which python
python --version  # Should be 3.9+

# 4. Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### "Module not found" errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=$PWD
streamlit run src/dashboard/app.py
```

### Redis cache always missing
```bash
# Normal behavior! 60s TTL means cache expires quickly
# To populate cache manually:
python -m src.risk_engine.compute_historical_metrics
# (This updates Redis with latest metrics)
```

### Charts not displaying data
```bash
# Check MongoDB field names match expectations
python -c "from config.mongodb_config import get_mongo_client, get_database; db = get_database(get_mongo_client()); doc = db.risk_metrics.find_one(); print(list(doc.keys()))"

# Should see: ['_id', 'date', 'portfolio_id', 'VaR_95', 'expected_shortfall', 'sharpe_ratio_20d', 'beta_vs_SPY_20d', 'portfolio_volatility_20d', 'computed_at', 'simulation_params']
```

---

## Documentation Reference

- **Setup Guide:** `docs/TEAMMATE_SETUP.md` (Start here for teammates)
- **Environment Setup:** `docs/ENV_SETUP_GUIDE.md` (Credential configuration)
- **Phase 3 Status:** `docs/status/phase3_status.md` (Completion summary)
- **Performance:** `docs/status/phase3_benchmarks.md` (Detailed metrics)
- **Phase 1 Context:** `docs/PHASE1_QUICKSTART.md` (Data foundation)
- **Phase 2 Status:** `docs/status/phase2_status.md` (Risk engine details)

---

## Next Steps

### For Presentation
1. Take screenshots of dashboard (different portfolios, date ranges, alerts)
2. Review `docs/status/phase3_benchmarks.md` for performance talking points
3. Prepare demo: Show VaR spike when tech stocks volatile
4. Explain NoSQL advantages: Nested data structures, flexible schema, aggregation pipelines

### For Production (Optional)
1. Upgrade MongoDB Atlas to M10+ tier (better performance, more connections)
2. Increase Redis TTL to 5-10 minutes (better cache hit rate)
3. Add user authentication (portfolio-level access control)
4. Implement REST API with FastAPI (programmatic access)
5. Set up Docker deployment (containerization)
6. Add monitoring (Prometheus + Grafana)

### For Further Development
1. Real-time WebSocket streaming (live metric updates)
2. Custom alert configuration (user-defined thresholds)
3. Export functionality (PDF reports, CSV downloads)
4. Historical replay (time-travel to any date)
5. Multi-portfolio comparison view
6. Machine learning predictions (future VaR forecasting)

---

## Team Contacts

**Andre Chuabio**
- Email: andre102599@gmail.com
- GitHub: https://github.com/AndreChuabio
- Role: Project lead, Phases 1-3

**Aengus Martin Donaire**
- Role: Teammate, Review & Testing

---

## Project Metadata

**Course:** Database Management Systems  
**Topic:** NoSQL Portfolio Risk Analytics  
**Timeline:** 3 weeks (Nov 2025)  
**Tech Stack:** Python, MongoDB Atlas, Redis Cloud, Streamlit, Plotly  
**Status:** Production Ready

**Repository:** https://github.com/AndreChuabio/NoSQL_Portfolio_Risk_Analytics

---

**Need help?** See `docs/TEAMMATE_SETUP.md` or contact Andre!
