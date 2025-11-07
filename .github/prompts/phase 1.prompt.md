---
mode: agent
---
Define the task to achieve, including specific requirements, constraints, and success criteria. 

Phase 1: Environment And Data Foundation
=======================================

Identity And Context
--------------------
- Address the user as Señor Clown. Recognize that they are a data scientist and aspiring quant trader.
- Re-read `/Users/andrechuabio/NoSQL_Project/.github/instructions/general.instructions.md` and `vscode-userdata:/Users/andrechuabio/Library/Application Support/Code/User/prompts/instructions.instructions.md` before starting.
- Confirm the current calendar week within the three week project timeline and document which week deliverables are in scope.

Objectives
----------
1. Ensure MongoDB and Redis services are running locally, preferably via Docker Compose.
2. Establish the required workspace structure under `NoSQL_Project/` as defined in the general instructions.
3. Ingest at least one year of OHLCV data for the required ticker universe and stage it under `data/raw/`.
4. Load cleaned price data and initial portfolio snapshots into MongoDB with required indexes.

Workflow Checklist
------------------
1. Validate infrastructure: verify Docker installation and version compatibility, create or update a `docker-compose.yml` based on the recommended template if not present, and start MongoDB and Redis containers while confirming connectivity.
2. Prepare workspace structure: create directories such as `data/raw`, `data/processed`, `src/ingestion`, `config`, `tests`, and `notebooks`, and add placeholder `__init__.py` files where modules will be created.
3. Acquire and validate market data: use Python scripts or notebooks to fetch OHLCV data via `yfinance` for the specified ticker list, validate coverage, handle missing values, and store CSV or Parquet outputs under `data/raw/`.
4. Seed MongoDB: design schemas for `prices` and `portfolio_holdings` collections, implement ingestion scripts in `src/ingestion/` to load price histories and daily portfolio snapshots, and create indexes on `(ticker, date)` for `prices` and `(portfolio_id, date)` for `portfolio_holdings`.

Quality Gates
-------------
- Containers respond to simple health queries (`mongo --eval "db.runCommand({ ping: 1 })"`, `redis-cli ping`).
- MongoDB collections contain the expected number of documents and pass sample validation queries.
- Portfolio weight vectors sum to 1.0 within tolerance and use UTC timestamps.
- Data directories contain only validated files with naming conventions documented.

Exit Criteria
-------------
- Infrastructure running with logs captured in `docs/runbooks/` or equivalent.
- MongoDB seeded with one year of price data per ticker and daily portfolio holdings.
- Redis reachable, even if no metrics cached yet.
- A brief status note recorded (location chosen by user) summarizing completion of Phase 1 checkpoints and any open risks.
