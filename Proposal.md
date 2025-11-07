# NoSQL Portfolio Risk Analytics Dashboard

**Designing scalable data architecture for Portfolio-level Risk Analytics Dashboard using Redis and MongoDB to handle financial data**

**Authors:** Andre Chuabio, Aengus Martin Donaire  
**Date:** November 2025

---

## I. Problem Statement & Motivation

### The Challenge
A real portfolio is not just "one stock goes up or down." It contains hundreds of positions, each with:
- Individual volatility characteristics
- Complex correlations across names and sectors  
- Time-varying weights (PMs resize trades intraday)
- Risk measures that change minute-to-minute during volatile market conditions

### Traditional Database Limitations
Traditional relational databases struggle with portfolio risk analytics due to:

1. **Irregular Time Series**: Different assets update at different frequencies, forcing everything into fixed relational schemas leads to sparse, inefficient tables
2. **Multi-dimensional Analytics**: Risk metrics (Value-at-Risk, expected shortfall, sector exposure breakdowns, rolling Sharpe) are complex objects, not simple scalar columns
3. **Low-latency Requirements**: Portfolio managers need "What's my current VaR right now?" in under 100ms, not "Come back after a JOIN"

### NoSQL Solution Architecture
- **MongoDB (Document Store)**: Store complex per-portfolio snapshots in single objects containing weights, returns distributions, sector exposures, and factor betas
- **Redis (In-memory Cache)**: Expose latest "hot" metrics (e.g., "current VaR for Portfolio 12 at 10:31:00") for instant dashboard reads without disk access

### Target Use Cases
The dashboard/API will support:

- **Historical Analysis**: View current and historical Value-at-Risk (VaR) and Expected Shortfall (ES) by portfolio
- **Performance Metrics**: View rolling Sharpe ratio and Beta over chosen lookback windows (e.g., 20 trading days)
- **Risk Decomposition**: Drill into exposures (sector, region, asset class) and monitor concentration risk shifts  
- **Real-time Alerts**: Surface alerts such as "VaR just spiked >X% from its 10-day median" or "Beta to Tech sector >1.5"
## II. Target NoSQL Technologies

### MongoDB (Document Store)
**Purpose**: Stores full historical state including holdings, prices, and calculated risk metrics

**Key Features**:
- **Flexible Schema**: Record different fields for different instrument types:
  - Stocks: `ticker`, `sector`, `weight`, `daily_vol`
  - Bonds: `duration`, `credit_rating`  
  - Crypto: `liquidity_score`, `exchange`
- **Optimized Indexing**: Index by `(portfolio_id, date)` or `(ticker, date)` for fast time slice retrieval

### Redis (Key-Value In-Memory Cache)  
**Purpose**: Holds the most recent, frequently requested metrics for ultra-low latency access

**Key Patterns**:
```
Key: VaR:<portfolio_id>
Value: { "current_VaR": -2.31%, "timestamp": "2025-10-27T10:30:00Z" }

Alert:<portfolio_id> → { "var_spike": true, "beta_limit_breach": false, ... }
```

**Features**:
- **TTL (Time-to-Live)**: Ensures stale keys expire automatically
- **Ephemeral Alerts**: Real-time alert flags with automatic cleanup

### Dual-Database Architecture Rationale
**Why use both instead of just MongoDB?**

| Component | Role | Analogy |
|-----------|------|---------|
| **MongoDB** | Full book of record, audit trail, analytics history | The vault |
| **Redis** | Trading screen - instant answers without heavy computation | The dashboard |

This dual design mirrors actual quant infrastructure: **persistent store + hot cache**

---

## III. Dataset Design

We will build a comprehensive, self-contained dataset with three interconnected layers:

### A. Price History Data (Daily Time Series)

**Scope**:
- **Universe**: ~20-30 liquid US equities and ETFs
  - Large-cap tech, financials, energy sectors
  - Benchmark ETFs: SPY, QQQ
- **Timeline**: Minimum 1 year of daily OHLCV data
- **Storage**: Initial CSV/Parquet format, then MongoDB ingestion

**Derived Metrics**:
- Daily returns per asset
- Rolling volatility per asset  
- Benchmark index returns (for Beta calculations)
- Benchmark index returns (for Beta calculations)

### B. Portfolio Snapshots (Holdings Over Time)

**Model Portfolios**: 2-3 representative strategies
- "Tech Growth"
- "Energy Tilt" 
- "Balanced Core"

**Daily Snapshot Structure**:
```json
{
    "portfolio_id": "PORT_A",
    "date": "2025-10-27",
    "assets": [
        {
            "ticker": "AAPL",
            "weight": 0.07,
            "sector": "Technology", 
            "current_price": 238.50,
            "daily_vol": 0.022
        }
    ],
    "aggregate_metrics": {
        "gross_exposure": 1.25,
        "net_exposure_sector": {...}
    }
}
```

**Realism Features**:
- End-of-day portfolio snapshots (simulating PM's book at close)
- Intraday rebalancing events for added complexity

### C. Risk Analytics Output

**Computed Risk Metrics** per `(portfolio_id, date)`:

| Metric | Methodology |
|--------|-------------|
| **VaR (Value-at-Risk)** | Monte Carlo simulation: 1,000 random return paths from recent N days, reweighted by current portfolio, 5th percentile outcome |
| **Expected Shortfall (CVaR)** | Average of worst X% outcomes from VaR simulation |
| **Rolling Sharpe Ratio** | `mean(returns) / std(returns)` over trailing window |
| **Beta** | Regression of portfolio returns vs benchmark (SPY) over trailing window |
| **Volatility** | Annualized standard deviation of portfolio daily returns |
| **Sector Exposure** | Percentage capital allocation by sector |

**Storage**: All metrics stored as documents in `risk_metrics` collection

### Dataset Advantages for NoSQL
This structure is ideal for NoSQL because it combines:
- **Time series data** (prices, returns)
- **Cross-sectional data** (weights per ticker)  
- **Analytics outputs** (VaR, Sharpe, Beta)

This heterogeneous data mix showcases NoSQL's strength in handling flexible schemas without rigid relational constraints.
(C) Derived risk metrics / analytics output
For each (portfolio_id, date) we compute and store:
VaR (Value-at-Risk): We’ll run a Monte Carlo simulation using recent return distributions (for example: draw 1,000 random return paths from the last N days of asset returns, reweight by current portfolio weights, sort outcomes, take the 5th percentile).
Expected Shortfall (CVaR): Average of the worst X% outcomes in those simulations.
Rolling Sharpe ratio: mean(returns) / std(returns) over a trailing window.
Beta: Regression of portfolio returns against a benchmark (for example SPY) over a trailing window.
Volatility: Annualized standard deviation of portfolio daily returns.
Sector exposure breakdown: % of capital allocated to each sector.
All these become documents in a risk_metrics collection.
This dataset is realistic because:
It mixes time series data (prices, returns),
Cross-sectional data (weights per ticker),
And analytics outputs (VaR, Sharpe, Beta),
which is exactly what NoSQL is good at storing without rigid schemas.
IV. Model (Collection and Keys)
MongoDB Collections
portfolio_holdings
{
  "portfolio_id": "PORT_A",
  "date": "2025-10-27",
  "assets": [
    {
      "ticker": "AAPL",
      "weight": 0.07,
      "sector": "Technology",
      "price": 238.50,
      "daily_vol": 0.022
    },
    {
      "ticker": "XOM",
      "weight": 0.05,
      "sector": "Energy",
      "price": 124.10,
      "daily_vol": 0.018
    }
  ],
  "gross_exposure": 1.25,
  "net_exposure_by_sector": {
    "Technology": 0.40,
    "Energy": 0.15,
    "Financials": 0.10
  }
}
Index: { portfolio_id: 1, date: -1 }

risk_metrics
{
  "portfolio_id": "PORT_A",
  "date": "2025-10-27",
  "VaR_95": -0.0231,
  "ES_95": -0.0310,
  "Sharpe_20d": 1.45,
  "Beta_SPY_20d": 1.18,
  "vol_20d": 0.025,
  "returns_distribution": [-0.012, -0.009, ... , 0.010]
}
Index: { portfolio_id: 1, date: -1 }

prices
{
  "ticker": "AAPL",
  "date": "2025-10-27",
  "open": 237.7,
  "high": 240.2,
  "low": 236.9,
  "close": 238.5,
  "volume": 72000000
}
Index: { ticker: 1, date: -1 }
Redis Keys
VaR:PORT_A →
{"current_VaR_95": -0.0231, "ts": "2025-10-27T10:30:00Z"}
Sharpe:PORT_A →
{"Sharpe_20d": 1.45, "ts": "2025-10-27T10:30:00Z"}
Alert:PORT_A →
{"var_spike": true, "beta_limit_breach": false, "ts": "2025-10-27T10:30:00Z"}
TTL on these keys (for example 60 seconds) keeps them fresh.
V. Timeline
Week 1: Database & Data Setup
Spin up local MongoDB and Redis;
Create collections (prices, portfolio_holdings, risk_metrics); 
Define indexes and Redis key naming/TTL; build dataset (1–2 yrs daily OHLCV for ~20–30 tickers + benchmark + simulated portfolios); 
Write ingest.py to load prices and insert daily portfolio_holdings snapshots.
Week 2: Risk Engine & Cache Layer
Compute daily returns per portfolio; 
Run Monte Carlo VaR + Expected Shortfall; calculate rolling Sharpe, Beta vs benchmark, volatility, sector exposure; 
Write results into risk_metrics in MongoDB; 
Push latest metrics and alert flags (current VaR, Sharpe, etc.) into Redis keys with timestamps.
Week 3: Dashboard / API / Performance Write-up
Build Streamlit or Flask dashboard; historical charts (VaR, Sharpe, vol) pulled from MongoDB; real-time “current status” card pulled from Redis; 
Alert banner (e.g. VaR spike); optional REST endpoints (/api/var/<portfolio_id>); 
Measure MongoDB vs Redis latency, stress test with 1,000-asset portfolio, capture screenshots, finalize slides + report with tradeoff discussion (Redis = fast/ephemeral, MongoDB = persistent/flexible).
