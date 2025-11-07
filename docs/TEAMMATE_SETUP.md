# Teammate Setup Guide

**For:** NoSQL Portfolio Risk Analytics Project  
**Team:** Andre + Groupmate  
**Infrastructure:** Cloud-based (no Docker required)

---

## Quick Setup (5 minutes)

### 1. Clone Repository

```bash
git clone https://github.com/AndreChuabio/NoSQL_Portfolio_Risk_Analytics.git
cd NoSQL_Portfolio_Risk_Analytics
```

### 2. Install Python Dependencies

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

### 3. Configure MongoDB Atlas Access

**Get connection string from Andre**, then set environment variable:

```bash
# Add to ~/.zshrc (macOS) or ~/.bashrc (Linux)
echo 'export MONGODB_URI="mongodb+srv://username:password@clusterac1.od00ttk.mongodb.net/?retryWrites=true&w=majority"' >> ~/.zshrc

# Reload shell config
source ~/.zshrc
```

**Windows:** Set via System Properties → Environment Variables

### 4. Verify Connection

```bash
# Test MongoDB
python -c "from config.mongodb_config import get_mongo_client; client = get_mongo_client(); print('MongoDB connected:', client.admin.command('ping'))"
```

Expected output:
```
MongoDB connected: {'ok': 1.0}
```

### 5. Check Data

```python
# Run in Python shell
from config.mongodb_config import get_mongo_client, get_database

client = get_mongo_client()
db = get_database(client)

print("Price documents:", db.prices.count_documents({}))  # Should be ~10,020
print("Portfolio snapshots:", db.portfolio_holdings.count_documents({}))  # Should be ~1,503
```

---

## Project Structure

```
NoSQL_Project/
├── data/
│   └── raw/              # Price data (already in MongoDB)
├── src/
│   ├── ingestion/        # Data loading scripts
│   ├── risk_engine/      # Phase 2: Risk calculations
│   ├── dashboard/        # Phase 3: Streamlit UI
│   └── api/              # Phase 3: Optional REST API
├── config/
│   ├── mongodb_config.py # Database connection
│   └── portfolios.yaml   # Portfolio definitions
└── docs/
    └── PHASE1_QUICKSTART.md  # Full setup guide
```

---

## Common Tasks

### Pull Latest Changes

```bash
git pull origin main
```

### Re-activate Virtual Environment

```bash
source .venv/bin/activate  # macOS/Linux
```

### Check MongoDB Collections

```python
from config.mongodb_config import get_mongo_client, get_database

client = get_mongo_client()
db = get_database(client)

# List all collections
print(db.list_collection_names())

# Sample price data
print(list(db.prices.find().limit(2)))

# Sample portfolio holdings
print(list(db.portfolio_holdings.find().limit(1)))
```

---

## Environment Variables Reference

| Variable | Value | Required For |
|----------|-------|--------------|
| `MONGODB_URI` | `mongodb+srv://...` | All phases (get from Andre) |
| `REDIS_HOST` | Redis Cloud endpoint | Phase 2+ (cache layer) |
| `REDIS_PORT` | Redis Cloud port | Phase 2+ |
| `REDIS_PASSWORD` | Redis Cloud password | Phase 2+ |

---

## Troubleshooting

### "No module named 'config'"

```bash
# Make sure you're in project root
pwd  # Should show .../NoSQL_Project

# Run with PYTHONPATH
PYTHONPATH=/path/to/NoSQL_Project python script.py
```

### "Connection to MongoDB timed out"

- Check if `MONGODB_URI` is set: `echo $MONGODB_URI`
- Verify internet connection
- Ask Andre to whitelist your IP in Atlas Network Access

### "Authentication failed"

- Double-check MongoDB URI has correct password
- URL-encode special characters in password (e.g., `@` → `%40`, `#` → `%23`)

---

## Phase 2 Preview

When starting Phase 2 (Risk Engine), we'll add:
- Redis Cloud for caching VaR metrics
- Risk calculation functions in `src/risk_engine/`
- Unit tests with `pytest`

**Redis setup will be coordinated together - not needed yet.**

---

## Need Help?

1. Check `docs/PHASE1_QUICKSTART.md` for detailed setup
2. Ask Andre for Atlas credentials or troubleshooting
3. Review `docs/status/phase1_status.md` for project status
