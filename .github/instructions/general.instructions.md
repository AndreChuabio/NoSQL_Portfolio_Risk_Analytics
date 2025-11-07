---
applyTo: '**'
---

# NoSQL Portfolio Risk Analytics Dashboard - Agent Instructions

## Project Context
This is a **portfolio-level risk analytics system** using MongoDB and Redis to handle real-time and historical financial risk metrics. The goal is to demonstrate NoSQL advantages over traditional relational databases for portfolio management workflows.

**Key Constraint**: This is a 3-week project with specific milestones. Always reference the proposal timeline when planning work.

---

## Architecture Overview

### Dual-Database Pattern
- **MongoDB**: Persistent storage for historical data (prices, holdings, computed risk metrics)
- **Redis**: In-memory cache for latest metrics (current VaR, alerts) with TTL expiration

### Data Flow
1. Price data (OHLCV) ingested into MongoDB `prices` collection
2. Portfolio snapshots stored in `portfolio_holdings` collection
3. Risk engine computes VaR, Sharpe, Beta and stores in `risk_metrics` collection
4. Latest metrics pushed to Redis with 60-second TTL
5. Dashboard reads historical data from MongoDB, real-time from Redis

---

## Coding Standards

### Python Style
- **PEP8 compliance**: Use `black` formatter, max line length 100
- **Type hints**: Use for all function signatures
- **Docstrings**: Google-style docstrings for all functions/classes
- **Imports**: Group by stdlib, third-party, local (use `isort`)

### Vectorization First
- Prefer NumPy/Pandas vectorized operations over loops
- Use `pandas.DataFrame.apply()` only when vectorization is impossible
- For Monte Carlo simulations: Use `numpy.random` with batch operations

### Error Handling
- Always use explicit exception handling with logging
- Never fail silently - log warnings at minimum
- Validate data shapes before computations

### Example Pattern:
```python
import logging
from typing import Dict, List
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

def calculate_portfolio_var(
    returns: pd.DataFrame,
    weights: pd.Series,
    confidence_level: float = 0.95,
    n_simulations: int = 1000
) -> float:
    """
    Calculate portfolio Value-at-Risk using Monte Carlo simulation.
    
    Args:
        returns: DataFrame of historical returns (rows=dates, cols=tickers)
        weights: Series of portfolio weights indexed by ticker
        confidence_level: VaR confidence level (default 0.95 for 95% VaR)
        n_simulations: Number of Monte Carlo paths
        
    Returns:
        VaR as negative percentage (e.g., -0.0231 for -2.31% loss)
        
    Raises:
        ValueError: If weights don't sum to 1.0 or tickers mismatch
    """
    if not np.isclose(weights.sum(), 1.0, atol=1e-4):
        raise ValueError(f"Weights sum to {weights.sum()}, expected 1.0")
    
    try:
        # Vectorized simulation
        simulated_returns = np.random.choice(
            returns.values.flatten(), 
            size=(n_simulations, len(returns))
        )
        portfolio_returns = simulated_returns @ weights.values
        var = np.percentile(portfolio_returns, (1 - confidence_level) * 100)
        
        logger.info(f"VaR calculated: {var:.4f} ({n_simulations} simulations)")
        return var
        
    except Exception as e:
        logger.error(f"VaR calculation failed: {e}")
        raise
```

---

## Database Patterns

### MongoDB Best Practices

#### Collection Schema Design
```python
# portfolio_holdings collection
{
    "portfolio_id": "PORT_A",  # String identifier
    "date": ISODate("2025-10-27T00:00:00Z"),  # Use ISODate, not strings
    "assets": [
        {
            "ticker": "AAPL",
            "weight": 0.07,  # Decimal weight
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

#### Required Indexes
```python
# In setup scripts
db.portfolio_holdings.create_index([("portfolio_id", 1), ("date", -1)])
db.risk_metrics.create_index([("portfolio_id", 1), ("date", -1)])
db.prices.create_index([("ticker", 1), ("date", -1)])
```

#### Query Patterns
```python
# Correct: Use projections to limit data transfer
holdings = db.portfolio_holdings.find_one(
    {"portfolio_id": "PORT_A", "date": target_date},
    {"assets.ticker": 1, "assets.weight": 1, "_id": 0}
)

# Correct: Use aggregation for complex queries
pipeline = [
    {"$match": {"portfolio_id": "PORT_A"}},
    {"$sort": {"date": -1}},
    {"$limit": 20},
    {"$project": {"VaR_95": 1, "date": 1}}
]
metrics = list(db.risk_metrics.aggregate(pipeline))
```

### Redis Best Practices

#### Key Naming Convention
```
<metric_type>:<portfolio_id>[:<optional_qualifier>]

Examples:
VaR:PORT_A
Sharpe:PORT_B:20d
Alert:PORT_A:var_spike
```

#### Data Structure Pattern
```python
import redis
import json
from datetime import datetime

# Always include timestamp
data = {
    "current_VaR_95": -0.0231,
    "ts": datetime.utcnow().isoformat() + "Z"
}

# Set with TTL
r.setex(
    name=f"VaR:{portfolio_id}",
    time=60,  # 60-second expiration
    value=json.dumps(data)
)

# Read and validate freshness
cached = r.get(f"VaR:{portfolio_id}")
if cached:
    data = json.loads(cached)
    # Check if timestamp is recent enough
```

#### Alert Patterns
```python
# Set multiple alert flags atomically
pipe = r.pipeline()
pipe.hset(f"Alert:{portfolio_id}", "var_spike", "true")
pipe.hset(f"Alert:{portfolio_id}", "beta_limit_breach", "false")
pipe.expire(f"Alert:{portfolio_id}", 120)  # 2-minute expiration
pipe.execute()
```

---

## Data Generation Guidelines

### Price Data Requirements
- **Source**: Use `yfinance` for historical OHLCV data
- **Universe**: 20-30 tickers covering:
  - Tech: AAPL, MSFT, GOOGL, NVDA, META
  - Financials: JPM, BAC, GS
  - Energy: XOM, CVX, COP
  - Benchmarks: SPY, QQQ
- **Timeline**: Minimum 252 trading days (1 year)
- **Validation**: Check for missing data, handle stock splits

### Portfolio Construction
```python
# Generate realistic portfolios with constraints
portfolios = {
    "PORT_A_TechGrowth": {
        "sector_limits": {"Technology": (0.4, 0.6)},
        "position_size": (0.02, 0.10),
        "rebalance_frequency": "weekly"
    },
    "PORT_B_EnergyTilt": {
        "sector_limits": {"Energy": (0.25, 0.40)},
        "position_size": (0.03, 0.12),
        "rebalance_frequency": "monthly"
    }
}
```

### Risk Metric Computation
- **VaR**: Use 95% confidence, 1000 Monte Carlo simulations
- **Sharpe Ratio**: 20-day rolling window, annualize using sqrt(252)
- **Beta**: Rolling 20-day regression vs SPY
- **Expected Shortfall**: Average of worst 5% outcomes from VaR simulation

---

## File Organization

### Required Directory Structure
```
NoSQL_Project/
├── data/
│   ├── raw/              # CSV/Parquet price data
│   └── processed/        # Cleaned data ready for ingestion
├── src/
│   ├── ingestion/        # Data loading scripts
│   │   ├── fetch_prices.py
│   │   ├── generate_portfolios.py
│   │   └── load_mongodb.py
│   ├── risk_engine/      # Risk calculations
│   │   ├── var_calculator.py
│   │   ├── performance_metrics.py
│   │   └── cache_manager.py
│   ├── api/              # Flask/FastAPI endpoints
│   │   └── endpoints.py
│   └── dashboard/        # Streamlit UI
│       └── app.py
├── config/
│   ├── mongodb_config.py
│   ├── redis_config.py
│   └── portfolios.yaml
├── tests/
│   ├── test_risk_engine.py
│   └── test_ingestion.py
├── notebooks/            # Exploratory analysis
│   └── EDA_prices.ipynb
├── requirements.txt
└── README.md
```

---

## Testing Requirements

### Unit Tests
- Test risk calculations with known inputs/outputs
- Mock MongoDB/Redis connections for isolation
- Use `pytest` with fixtures for data setup

### Integration Tests
- Validate end-to-end data flow (ingest → compute → cache → query)
- Test MongoDB query performance with realistic data volumes
- Verify Redis TTL behavior

### Performance Benchmarks
```python
# Required benchmarks to capture
benchmarks = {
    "mongodb_historical_query": "Time to fetch 20-day VaR history",
    "redis_current_metric": "Time to fetch current VaR from cache",
    "risk_computation": "Time to compute VaR for 30-asset portfolio",
    "stress_test": "Query time with 1000-asset portfolio"
}
```

---

## Dashboard Requirements

### Must-Have Features
1. **Portfolio Selector**: Dropdown to choose portfolio
2. **Date Range Picker**: Select historical window
3. **Real-Time Status Card**: 
   - Current VaR (from Redis)
   - Current Sharpe (from Redis)
   - Alert indicators
4. **Historical Charts**:
   - VaR time series
   - Sharpe ratio over time
   - Portfolio volatility
5. **Sector Exposure Breakdown**: Pie or bar chart
6. **Alert Banner**: Display active warnings

### UI Best Practices
- Use `streamlit.cache_data` for MongoDB queries
- Poll Redis every 5 seconds for real-time updates
- Show data source (MongoDB vs Redis) with icon/badge
- Include latency metrics in footer

---

## Week-by-Week Execution Plan

### Week 1: Foundation
**Deliverables**:
- [ ] MongoDB and Redis running locally (Docker Compose preferred)
- [ ] Collections created with indexes
- [ ] Price data fetched and stored in `data/raw/`
- [ ] `ingest.py` script loads prices into MongoDB
- [ ] At least 1 portfolio snapshot per trading day in MongoDB

**Validation**: Query MongoDB for price count, verify index usage with `.explain()`

### Week 2: Risk Engine
**Deliverables**:
- [ ] VaR calculation function with unit tests
- [ ] Sharpe, Beta, ES calculations implemented
- [ ] Script to compute daily risk metrics for all portfolios
- [ ] Risk metrics stored in MongoDB `risk_metrics` collection
- [ ] Latest metrics pushed to Redis with TTL

**Validation**: Manually verify VaR calculation matches expected distribution, check Redis keys expire

### Week 3: Dashboard & Analysis
**Deliverables**:
- [ ] Streamlit dashboard with all required features
- [ ] Optional REST API with at least `/api/var/<portfolio_id>` endpoint
- [ ] Performance benchmarks documented (MongoDB vs Redis latency)
- [ ] Stress test with 1000-asset portfolio
- [ ] Screenshots for presentation
- [ ] Final report with tradeoff analysis

**Validation**: Dashboard loads in <2 seconds, Redis queries <10ms, MongoDB queries <100ms

---

## Common Pitfalls to Avoid

### Data Issues
- **Timezone Inconsistency**: Always use UTC, store as `datetime` not strings
- **Missing Data**: Handle weekends/holidays in time series
- **Weight Drift**: Ensure portfolio weights sum to 1.0 after rebalancing

### Database Issues
- **Missing Indexes**: Always create indexes before bulk inserts
- **Connection Leaks**: Use context managers for MongoDB connections
- **Redis Memory**: Monitor memory usage, set `maxmemory-policy allkeys-lru`

### Code Issues
- **Hardcoded Values**: Use config files for portfolio definitions, DB connections
- **Silent Failures**: Always log errors, never use bare `except:`
- **Blocking Operations**: Use async patterns for API if handling multiple requests

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| MongoDB historical query | <100ms | Fetch 20-day VaR history |
| Redis current metric | <10ms | Fetch latest VaR |
| VaR computation (30 assets) | <500ms | 1000 Monte Carlo simulations |
| Dashboard initial load | <2s | Full page render |
| Stress test (1000 assets) | Document actual | Measure and report |

---

## Logging Standards

### Required Log Levels
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Use consistently
logger.debug("Fetching prices for 30 tickers")  # Verbose details
logger.info("VaR calculation completed: -2.31%")  # Key milestones
logger.warning("Missing data for AAPL on 2025-10-15")  # Recoverable issues
logger.error("MongoDB connection failed", exc_info=True)  # Failures
```

---

## Documentation Requirements

### Code Documentation
- Docstrings for all public functions
- Inline comments for complex logic (Monte Carlo sampling, weight calculations)
- Type hints for all function signatures

### Project Documentation
- `README.md` with setup instructions, architecture diagram
- API documentation if REST endpoints implemented
- Performance benchmark results in final report

---

## Environment Setup

### Required Dependencies
```txt
# Data & Computation
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.0

# Databases
pymongo>=4.0.0
redis>=4.5.0

# Dashboard
streamlit>=1.25.0

# Optional: API
flask>=2.3.0
# OR
fastapi>=0.100.0
uvicorn>=0.23.0

# Development
pytest>=7.4.0
black>=23.0.0
isort>=5.12.0
```

### Docker Compose (Recommended)
```yaml
version: '3.8'
services:
  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
      
  redis:
    image: redis:7.2-alpine
    ports:
      - "6379:6379"
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    
volumes:
  mongo_data:
```

---

## Final Deliverable Checklist

- [ ] MongoDB collections populated with 1+ year of data
- [ ] Redis cache functioning with TTL
- [ ] Risk metrics computed daily for all portfolios
- [ ] Dashboard deployed and functional
- [ ] Performance benchmarks documented
- [ ] Code follows PEP8 with type hints
- [ ] Unit tests for risk calculations
- [ ] README with setup instructions
- [ ] Final report with NoSQL tradeoff analysis
- [ ] Screenshots of dashboard features

---

## Questions to Ask Before Starting Work

1. **Scope Clarification**: Which week are we in? What is the immediate deliverable?
2. **Data Availability**: Do we have price data already, or should I fetch it?
3. **Infrastructure**: Are MongoDB and Redis already running, or should I set them up?
4. **Preferences**: Streamlit or Flask for dashboard? REST API required or optional?

Always confirm the current state before generating code to avoid redundant work.

