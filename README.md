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

See full README content in repository.