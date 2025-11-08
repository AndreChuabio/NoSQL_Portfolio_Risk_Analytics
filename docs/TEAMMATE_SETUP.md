# Teammate Setup Guide - START HERE

**For:** NoSQL Portfolio Risk Analytics Project  
**Team:** Andre Chuabio + Aengus Martin Donaire  
**Infrastructure:** Cloud-based (MongoDB Atlas + Redis Cloud)  
**Current Status:** Phase 3 Complete - Dashboard Live

---

## Quick Setup (5 minutes)

### Step 1: Clone Repository

```bash
git clone https://github.com/AndreChuabio/NoSQL_Portfolio_Risk_Analytics.git
cd NoSQL_Portfolio_Risk_Analytics
```

### Step 2: Install Python Dependencies

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\activate  # Windows

# Install packages
pip install -r requirements.txt
```

**Key Dependencies:**
- `streamlit>=1.25.0` - Dashboard framework
- `plotly>=5.14.0` - Interactive charts
- `pymongo>=4.6.0` - MongoDB client
- `redis>=4.5.0` - Redis client
- `pandas>=2.0.0` - Data manipulation

### Step 3: Set Environment Variables

**Get credentials from Andre** (MongoDB URI, Redis host/port/password), then add them to your shell config:

**For macOS/Linux (zsh or bash):**

```bash
# Open your shell config file
nano ~/.zshrc  # or ~/.bashrc if using bash

# Add these lines at the end (replace with actual credentials from Andre):
export MONGODB_URI="mongodb+srv://ac233_db_user:password@clusterac1.od00ttk.mongodb.net/?retryWrites=true&w=majority"
export REDIS_HOST="redis-19109.c282.east-us-mz.azure.redns.redis-cloud.com"
export REDIS_PORT="19109"
export REDIS_PASSWORD="your_redis_password_here"

# Save and exit (Ctrl+O, Enter, Ctrl+X in nano)

# Load the credentials
source ~/.zshrc  # or source ~/.bashrc
```

**For Windows (PowerShell):**
```powershell
# Add to your PowerShell profile
$env:MONGODB_URI="mongodb+srv://..."
$env:REDIS_HOST="redis-xxxxx.redns.redis-cloud.com"
$env:REDIS_PORT="12345"
$env:REDIS_PASSWORD="your_password"
```

### Step 4: Verify Connections

```bash
# Test MongoDB connection
python -c "from config.mongodb_config import get_mongo_client; client = get_mongo_client(); print('MongoDB connected:', client.admin.command('ping'))"

# Test Redis connection
python src/ingestion/verify_redis.py
```

Expected output:
```
MongoDB connected: {'ok': 1.0}
✓ Redis PING successful
✓ String write/read successful
...
Redis Verification: ALL TESTS PASSED
```

### Step 5: Launch the Dashboard

```bash
# Use the launch script (automatically loads credentials from ~/.zshrc)
./run_dashboard.sh
```

If you get a credential error, make sure you:
1. Added credentials to `~/.zshrc`
2. Ran `source ~/.zshrc`
3. Credentials are correct (no typos)

The dashboard will open at **http://localhost:8501**

---

## What You Have Access To

All 3 phases are complete:

**Phase 1 (Week 1) - Data Foundation:**
- 2 years of price data for 20 tickers (Technology, Energy, Financials, Healthcare, Consumer, Industrials)
- 3 synthetic portfolios with daily snapshots
- MongoDB collections: `prices`, `portfolio_holdings`

**Phase 2 (Week 2) - Risk Engine:**
- VaR, Expected Shortfall, Sharpe Ratio, Beta calculations implemented
- Historical risk metrics computed for all portfolio snapshots
- MongoDB collection: `risk_metrics` (1,443 documents)
- Redis cache integration with 60s TTL

**Phase 3 (Week 3) - Dashboard & Analytics:**
- Streamlit dashboard with real-time metrics
- Interactive Plotly charts (VaR, Sharpe, Beta, Volatility)
- Sector exposure visualization
- Alert system with configurable thresholds
- Performance benchmarks documented
- Redis cache configured (60-second TTL for latest metrics)
- Full test suite: 28/28 tests passing

---

## Dashboard Features (Phase 3 - COMPLETE)

### How to Use the Dashboard

1. **Launch**: Run `./run_dashboard.sh` or `PYTHONPATH=$PWD streamlit run src/dashboard/app.py`
2. **Access**: Open browser to http://localhost:8501
3. **Select Portfolio**: Use sidebar dropdown (PORT_A, PORT_B, or PORT_C)
4. **Adjust Time Range**: Slide the "Historical Window" slider (7-365 days)
5. **Monitor Alerts**: Red/orange banners appear when thresholds breached
6. **View Metrics**: Real-time cards show latest VaR, ES, Sharpe, Beta
7. **Analyze Trends**: Interactive charts allow zoom/pan for detailed analysis

### Dashboard Components

**Sidebar Controls:**
- Portfolio selector (3 options)
- Date range picker (7-365 days, default 60)
- Refresh data button
- Alert threshold reference

**Main View:**
- Alert banner (color-coded: red=critical, orange=warning, green=healthy)
- 4 metric cards (VaR, Expected Shortfall, Sharpe, Beta)
- Data source indicator (Redis or MongoDB)
- 4 historical trend charts (VaR, Sharpe, Beta, Volatility)
- Sector exposure pie chart
- Performance metrics footer (query latencies)

**Alert Thresholds:**
- VaR Critical: < -2.0%
- VaR Warning: < -1.5%
- Beta High: > 1.5
- Beta Warning: > 1.3
- Volatility High: > 30%
- Sharpe Negative: >10 consecutive days

### Dashboard Files

```
src/dashboard/
├── app.py              # Main Streamlit application (502 lines)
├── data_queries.py     # MongoDB/Redis query layer (333 lines)
└── alerts.py           # Alert threshold logic (221 lines)
```

---

## Project Structure

```
NoSQL_Project/
├── data/
│   └── raw/              # Price data (already in MongoDB)
├── src/
│   ├── ingestion/        # Data loading scripts (Phase 1 - DONE)
│   │   ├── fetch_prices.py
│   │   ├── load_mongodb.py
│   │   └── verify_redis.py
│   ├── risk_engine/      # Risk calculations (Phase 2 - DONE)
│   │   ├── var_calculator.py
│   │   ├── performance_metrics.py
│   │   ├── cache_manager.py
│   │   └── compute_historical_metrics.py
│   ├── dashboard/        # Phase 3: BUILD THIS (Streamlit UI)
│   └── api/              # Phase 3: Optional REST API
├── config/
│   ├── mongodb_config.py # Database connection helpers
│   ├── redis_config.py   # Redis connection helpers
│   └── portfolios.yaml   # Portfolio definitions
├── tests/
│   └── test_risk_engine.py  # Unit tests (all passing)
└── docs/
    ├── TEAMMATE_SETUP.md    # This file
    ├── ENV_SETUP_GUIDE.md   # Environment variable reference
    ├── PHASE1_QUICKSTART.md # Phase 1 historical context
    └── status/
        ├── phase1_status.md # Phase 1 completion summary
        └── phase2_status.md # Phase 2 completion summary
```

---

## Database Schema Reference

### Collection: `prices`
```python
{
    "ticker": "AAPL",
    "date": ISODate("2023-10-27T00:00:00Z"),
    "open": 238.50,
    "high": 240.12,
    "low": 237.80,
    "close": 239.65,
    "volume": 45123456,
    "daily_return": 0.0048  # (close - prev_close) / prev_close
}
```
**Index:** `(ticker, date)`

### Collection: `portfolio_holdings`
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
**Index:** `(portfolio_id, date)`

### Collection: `risk_metrics`
```python
{
    "portfolio_id": "PORT_A_TechGrowth",
    "date": ISODate("2023-12-07T00:00:00Z"),
    "VaR_95": -0.009325,  # Negative = potential loss
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
**Index:** `(portfolio_id, date)`

### Redis Cache Keys
```
VaR:<portfolio_id>              # Current VaR (60s TTL)
Sharpe:<portfolio_id>           # Current Sharpe Ratio
Beta:<portfolio_id>             # Current Beta
Alert:<portfolio_id>            # Alert flags (hash)
```

---

## Common Tasks

### Query MongoDB for Historical Data

```python
from config.mongodb_config import get_mongo_client, get_database
from datetime import datetime, timedelta

client = get_mongo_client()
db = get_database(client)

# Get last 20 days of VaR for a portfolio
end_date = datetime.utcnow()
start_date = end_date - timedelta(days=20)

metrics = list(db.risk_metrics.find(
    {
        "portfolio_id": "PORT_A_TechGrowth",
        "date": {"$gte": start_date, "$lte": end_date}
    },
    {"date": 1, "VaR_95": 1, "sharpe_ratio_20d": 1, "_id": 0}
).sort("date", 1))

# Convert to DataFrame for plotting
import pandas as pd
df = pd.DataFrame(metrics)
print(df)
```

### Query Redis for Latest Metrics

```python
from config.redis_config import get_redis_client
import json

r = get_redis_client()

# Get current VaR
var_data = r.get("VaR:PORT_A_TechGrowth")
if var_data:
    var_info = json.loads(var_data)
    print(f"Current VaR: {var_info['current_VaR_95']}")
    print(f"Timestamp: {var_info['ts']}")
else:
    print("Cache expired or empty - query MongoDB for latest")
```

### Re-populate Redis Cache

```python
# Run the compute script to refresh cache
# This will compute all metrics and push latest to Redis
python -m src.risk_engine.compute_historical_metrics
```
Note: This takes ~17 minutes to compute all 1,503 snapshots

---

## Phase 3 Dashboard Requirements

Build a Streamlit dashboard with these features:

### Must-Have Features
1. **Portfolio Selector**: Dropdown to choose from 3 portfolios
   - PORT_A_TechGrowth
   - PORT_B_EnergyTilt
   - PORT_C_BalancedCore

2. **Date Range Picker**: Select historical window for charts

3. **Real-Time Status Cards**: Display latest metrics
   - Current VaR (from Redis if available, else MongoDB)
   - Current Sharpe Ratio
   - Current Beta
   - Last updated timestamp

4. **Historical Charts** (using Plotly):
   - VaR time series
   - Sharpe ratio over time
   - Beta vs benchmark over time
   - Portfolio volatility trend

5. **Sector Exposure Breakdown**: Pie or bar chart showing current sector allocation

6. **Alert Banner**: Display warnings if:
   - VaR exceeds threshold (e.g., worse than -2%)
   - Beta exceeds limit (e.g., > 1.5)
   - Sharpe ratio negative for extended period

### Example Dashboard Code Structure

```python
# src/dashboard/app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from config.mongodb_config import get_mongo_client, get_database
from config.redis_config import get_redis_client
import json

st.set_page_config(page_title="Portfolio Risk Analytics", layout="wide")

# Sidebar
st.sidebar.title("Portfolio Selection")
portfolio_id = st.sidebar.selectbox(
    "Choose Portfolio",
    ["PORT_A_TechGrowth", "PORT_B_EnergyTilt", "PORT_C_BalancedCore"]
)

# Connect to databases
client = get_mongo_client()
db = get_database(client)
redis_client = get_redis_client()

# Fetch latest metrics (try Redis first, fallback to MongoDB)
var_key = f"VaR:{portfolio_id}"
cached = redis_client.get(var_key)

if cached:
    latest = json.loads(cached)
    st.info("Data from Redis Cache (real-time)")
else:
    # Query MongoDB for latest
    latest = db.risk_metrics.find_one(
        {"portfolio_id": portfolio_id},
        sort=[("date", -1)]
    )
    st.info("Data from MongoDB (cache expired)")

# Display metrics
col1, col2, col3, col4 = st.columns(4)
col1.metric("VaR (95%)", f"{latest['VaR_95']:.2%}")
col2.metric("Expected Shortfall", f"{latest['expected_shortfall']:.2%}")
col3.metric("Sharpe Ratio", f"{latest['sharpe_ratio_20d']:.2f}")
col4.metric("Beta vs SPY", f"{latest['beta_vs_SPY_20d']:.2f}")

# Historical chart
metrics_df = pd.DataFrame(list(db.risk_metrics.find(
    {"portfolio_id": portfolio_id},
    {"date": 1, "VaR_95": 1, "_id": 0}
).sort("date", 1)))

fig = px.line(metrics_df, x='date', y='VaR_95', title='VaR Over Time')
st.plotly_chart(fig, use_container_width=True)

# Add more charts and features...
```

---

## Running the Dashboard

```bash
# Activate virtual environment
source .venv/bin/activate

# Run Streamlit
streamlit run src/dashboard/app.py
```

Dashboard will open at `http://localhost:8501`

---

## Troubleshooting

### MongoDB Connection Failed

```bash
# Check environment variable is set
echo $MONGODB_URI

# Verify from Python
python -c "from config.mongodb_config import get_mongo_client; print('Connected:', get_mongo_client().admin.command('ping'))"
```

**Common issues:**
- Environment variable not set → Run `source setup_env.sh` or manually export
- Wrong credentials → Get updated connection string from Andre
- IP not whitelisted → Andre needs to add your IP in Atlas Network Access

### Redis Connection Failed

```bash
# Check environment variables
echo $REDIS_HOST
echo $REDIS_PORT
echo $REDIS_PASSWORD

# Test connection
python src/ingestion/verify_redis.py
```

### Import Errors

```bash
# Make sure you're in project root
pwd  # Should end in NoSQL_Portfolio_Risk_Analytics or NoSQL_Project

# Verify virtual environment is activated
which python  # Should point to .venv/bin/python

# If using module imports, set PYTHONPATH
export PYTHONPATH=/path/to/NoSQL_Project:$PYTHONPATH
```

### No Data in Risk Metrics Collection

```bash
# Re-run the compute script (takes ~17 minutes)
python -m src.risk_engine.compute_historical_metrics
```

---

## Environment Variables Reference

| Variable | Example Value | Required For | Get From |
|----------|--------------|--------------|----------|
| `MONGODB_URI` | `mongodb+srv://user:pass@cluster...` | All phases | Andre |
| `REDIS_HOST` | `redis-12345.c123...redis-cloud.com` | Phase 2+ | Andre |
| `REDIS_PORT` | `12345` | Phase 2+ | Andre |
| `REDIS_PASSWORD` | `aBcDe...` | Phase 2+ | Andre |

See `docs/ENV_SETUP_GUIDE.md` for detailed setup instructions.

---

## Performance Targets

Your dashboard should meet these benchmarks:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| MongoDB historical query | <100ms | Fetch 20-day VaR history |
| Redis current metric | <10ms | Fetch latest VaR from cache |
| Dashboard initial load | <2s | Full page render with charts |

---

## Need Help?

1. **Documentation:**
   - `docs/ENV_SETUP_GUIDE.md` - Environment setup reference
   - `docs/status/phase2_status.md` - What Andre completed in Phase 2
   - `docs/PHASE1_QUICKSTART.md` - Historical context for Phase 1

2. **Code Examples:**
   - `src/risk_engine/compute_historical_metrics.py` - See how to query MongoDB and write to Redis
   - `tests/test_risk_engine.py` - Examples of using risk calculation functions

3. **Ask Andre:**
   - Database credentials
   - Clarification on data schema
   - Help with MongoDB queries

---

## Git Workflow

```bash
# Pull latest changes before starting work
git pull origin main

# Create feature branch for dashboard
git checkout -b feature/dashboard

# Make changes, then commit
git add src/dashboard/
git commit -m "Add Streamlit dashboard with VaR time series chart"

# Push to GitHub
git push origin feature/dashboard

# Create Pull Request on GitHub for Andre to review
```

---

**Last Updated:** 2025-11-07 by Andre Chuabio  
**Current Project Status:** Phase 2 Complete, Ready for Phase 3 Dashboard Development
