"""Compute historical risk metrics for all portfolio snapshots and persist to MongoDB + Redis."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.operations import UpdateOne

from config.mongodb_config import get_database, get_mongo_client
from src.risk_engine.cache_manager import CacheManager
from src.risk_engine.performance_metrics import (
    calculate_beta_from_dataframes,
    calculate_rolling_volatility,
    calculate_sharpe_ratio,
)
from src.risk_engine.var_calculator import calculate_expected_shortfall, calculate_portfolio_var

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def fetch_portfolio_dates(db, portfolio_id: Optional[str] = None) -> List[Dict[str, object]]:
    """
    Fetch all unique (portfolio_id, date) combinations from portfolio_holdings.

    Args:
        db: MongoDB database instance
        portfolio_id: Filter by specific portfolio (optional, fetches all if None)

    Returns:
        List of dictionaries with portfolio_id and date fields
    """
    query = {} if portfolio_id is None else {"portfolio_id": portfolio_id}

    pipeline = [
        {"$match": query},
        {"$project": {"portfolio_id": 1, "date": 1, "_id": 0}},
        {"$sort": {"portfolio_id": 1, "date": 1}},
    ]

    snapshots = list(db.portfolio_holdings.aggregate(pipeline))
    logger.info(f"Found {len(snapshots)} portfolio snapshots to process")

    return snapshots


def fetch_returns_window(db, end_date: datetime, lookback_days: int = 50) -> pd.DataFrame:
    """
    Fetch price data and compute returns for a lookback window.

    Args:
        db: MongoDB database instance
        end_date: End date for the window (inclusive)
        lookback_days: Number of days to look back (default 50 for 20-day rolling calculations)

    Returns:
        DataFrame of daily returns indexed by date with tickers as columns
    """
    start_timestamp = end_date.timestamp() - (lookback_days * 86400)
    start_date = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)

    query = {"date": {"$gte": start_date, "$lte": end_date}}

    price_docs = list(db.prices.find(query).sort("date", ASCENDING))

    if not price_docs:
        logger.warning(f"No price data found between {start_date} and {end_date}")
        return pd.DataFrame()

    prices_list = []
    for doc in price_docs:
        prices_list.append(
            {
                "date": doc["date"],
                "ticker": doc["ticker"],
                "close": doc.get("close", np.nan),
            }
        )

    df = pd.DataFrame(prices_list)
    prices_pivot = df.pivot(index="date", columns="ticker", values="close")
    prices_pivot = prices_pivot.sort_index()

    returns = prices_pivot.pct_change().dropna(how="all")

    logger.debug(
        f"Fetched returns: {returns.shape[0]} days × {returns.shape[1]} tickers "
        f"(window: {start_date.date()} to {end_date.date()})"
    )

    return returns


def fetch_portfolio_weights(db, portfolio_id: str, date: datetime) -> pd.Series:
    """
    Fetch portfolio weights for a specific date.

    Args:
        db: MongoDB database instance
        portfolio_id: Portfolio identifier
        date: Snapshot date

    Returns:
        Series of weights indexed by ticker
    """
    snapshot = db.portfolio_holdings.find_one(
        {"portfolio_id": portfolio_id, "date": date}, {"assets": 1, "_id": 0}
    )

    if not snapshot or "assets" not in snapshot:
        raise ValueError(f"No holdings found for {portfolio_id} on {date.date()}")

    weights = {asset["ticker"]: asset["weight"] for asset in snapshot["assets"]}

    return pd.Series(weights)


def compute_metrics_for_snapshot(
    db,
    portfolio_id: str,
    snapshot_date: datetime,
    benchmark_ticker: str = "SPY",
    n_simulations: int = 1000,
    confidence_level: float = 0.95,
    window: int = 20,
) -> Optional[Dict[str, object]]:
    """
    Compute all risk metrics for a single portfolio snapshot.

    Args:
        db: MongoDB database instance
        portfolio_id: Portfolio identifier
        snapshot_date: Date of the portfolio snapshot
        benchmark_ticker: Benchmark for beta calculation (default SPY)
        n_simulations: Number of Monte Carlo simulations for VaR
        confidence_level: Confidence level for VaR and ES
        window: Rolling window size for Sharpe, Beta, Volatility

    Returns:
        Dictionary with all computed metrics, or None if computation fails
    """
    try:
        returns = fetch_returns_window(db, snapshot_date, lookback_days=window + 30)

        if returns.empty or len(returns) < window:
            logger.warning(
                f"Insufficient data for {portfolio_id} on {snapshot_date.date()}: "
                f"{len(returns)} days < {window} required"
            )
            return None

        weights = fetch_portfolio_weights(db, portfolio_id, snapshot_date)

        var_95 = calculate_portfolio_var(
            returns, weights, confidence_level=confidence_level, n_simulations=n_simulations
        )

        expected_shortfall = calculate_expected_shortfall(
            returns, weights, confidence_level=confidence_level, n_simulations=n_simulations
        )

        sharpe_ratio = calculate_sharpe_ratio(returns, weights, window=window)

        beta = calculate_beta_from_dataframes(
            returns, weights, benchmark_ticker=benchmark_ticker, window=window
        )

        volatility = calculate_rolling_volatility(returns, weights, window=window)

        if sharpe_ratio is None or beta is None or volatility is None:
            logger.warning(f"Some metrics unavailable for {portfolio_id} on {snapshot_date.date()}")
            return None

        metrics = {
            "portfolio_id": portfolio_id,
            "date": snapshot_date,
            "VaR_95": var_95,
            "expected_shortfall": expected_shortfall,
            "sharpe_ratio_20d": sharpe_ratio,
            "beta_vs_SPY_20d": beta,
            "portfolio_volatility_20d": volatility,
            "simulation_params": {
                "n_simulations": n_simulations,
                "confidence_level": confidence_level,
                "method": "historical_monte_carlo",
                "window": window,
            },
            "computed_at": datetime.now(timezone.utc),
        }

        logger.debug(
            f"Computed metrics for {portfolio_id} on {snapshot_date.date()}: "
            f"VaR={var_95:.6f}, ES={expected_shortfall:.6f}, Sharpe={sharpe_ratio:.4f}, "
            f"Beta={beta:.4f}, Vol={volatility:.6f}"
        )

        return metrics

    except Exception as e:
        logger.error(
            f"Failed to compute metrics for {portfolio_id} on {snapshot_date.date()}: {e}",
            exc_info=True,
        )
        return None


def ensure_risk_metrics_index(db) -> None:
    """Create index on risk_metrics collection if it doesn't exist."""
    db.risk_metrics.create_index(
        [("portfolio_id", ASCENDING), ("date", DESCENDING)],
        name="idx_risk_metrics_portfolio_date",
    )
    logger.info("Ensured risk_metrics index exists")


def bulk_insert_metrics(db, metrics_list: List[Dict[str, object]]) -> int:
    """
    Bulk insert or update risk metrics in MongoDB.

    Args:
        db: MongoDB database instance
        metrics_list: List of metrics dictionaries to insert

    Returns:
        Number of documents upserted
    """
    if not metrics_list:
        logger.warning("No metrics to insert")
        return 0

    requests = []
    for metrics in metrics_list:
        filter_query = {
            "portfolio_id": metrics["portfolio_id"],
            "date": metrics["date"],
        }
        requests.append(UpdateOne(filter_query, {"$set": metrics}, upsert=True))

    try:
        result = db.risk_metrics.bulk_write(requests, ordered=False)
        upserted_count = result.upserted_count + result.modified_count
        logger.info(f"Bulk insert: {upserted_count} risk metrics upserted")
        return upserted_count

    except Exception as e:
        logger.error(f"Bulk insert failed: {e}", exc_info=True)
        return 0


def update_redis_cache_for_latest(
    cache_manager: CacheManager,
    db,
    portfolio_id: str,
) -> bool:
    """
    Update Redis cache with latest metrics for a portfolio.

    Args:
        cache_manager: CacheManager instance
        db: MongoDB database instance
        portfolio_id: Portfolio identifier

    Returns:
        True if cache updated successfully, False otherwise
    """
    try:
        latest_metrics = db.risk_metrics.find_one(
            {"portfolio_id": portfolio_id},
            sort=[("date", DESCENDING)],
        )

        if not latest_metrics:
            logger.warning(f"No metrics found for {portfolio_id} to cache")
            return False

        success = cache_manager.set_all_metrics(
            portfolio_id=portfolio_id,
            var_95=latest_metrics["VaR_95"],
            expected_shortfall=latest_metrics["expected_shortfall"],
            sharpe_ratio=latest_metrics["sharpe_ratio_20d"],
            beta=latest_metrics["beta_vs_SPY_20d"],
            volatility=latest_metrics["portfolio_volatility_20d"],
        )

        if success:
            logger.info(
                f"Updated Redis cache for {portfolio_id} with metrics from {latest_metrics['date'].date()}"
            )

        return success

    except Exception as e:
        logger.error(f"Failed to update Redis cache for {portfolio_id}: {e}", exc_info=True)
        return False


def compute_all_historical_metrics(
    batch_size: int = 50,
    portfolio_id: Optional[str] = None,
    update_cache: bool = True,
) -> Dict[str, int]:
    """
    Compute risk metrics for all portfolio snapshots and persist to MongoDB + Redis.

    Args:
        batch_size: Number of snapshots to process before bulk insert (default 50)
        portfolio_id: Process only specific portfolio (optional, processes all if None)
        update_cache: Whether to update Redis cache with latest metrics (default True)

    Returns:
        Dictionary with statistics (total_processed, successful, failed, cached)
    """
    start_time = time.time()

    client: MongoClient = get_mongo_client()
    db = get_database(client)
    cache_manager = CacheManager() if update_cache else None

    if cache_manager and not cache_manager.health_check():
        logger.warning("Redis health check failed - caching disabled")
        cache_manager = None

    ensure_risk_metrics_index(db)

    snapshots = fetch_portfolio_dates(db, portfolio_id=portfolio_id)

    total_snapshots = len(snapshots)
    metrics_buffer = []
    successful = 0
    failed = 0
    processed_portfolios = set()

    logger.info(f"Starting historical backfill for {total_snapshots} snapshots")

    for idx, snapshot in enumerate(snapshots, start=1):
        portfolio_id_curr = snapshot["portfolio_id"]
        snapshot_date = snapshot["date"]

        metrics = compute_metrics_for_snapshot(db, portfolio_id_curr, snapshot_date)

        if metrics:
            metrics_buffer.append(metrics)
            successful += 1
            processed_portfolios.add(portfolio_id_curr)
        else:
            failed += 1

        if len(metrics_buffer) >= batch_size:
            bulk_insert_metrics(db, metrics_buffer)
            metrics_buffer = []

        if idx % 50 == 0:
            elapsed = time.time() - start_time
            rate = idx / elapsed
            eta_seconds = (total_snapshots - idx) / rate if rate > 0 else 0
            logger.info(
                f"Progress: {idx}/{total_snapshots} ({idx/total_snapshots*100:.1f}%) | "
                f"Success: {successful}, Failed: {failed} | "
                f"Rate: {rate:.2f} snapshots/sec | ETA: {eta_seconds/60:.1f} min"
            )

    if metrics_buffer:
        bulk_insert_metrics(db, metrics_buffer)

    cached_portfolios = 0
    if cache_manager:
        for portfolio_id_to_cache in processed_portfolios:
            if update_redis_cache_for_latest(cache_manager, db, portfolio_id_to_cache):
                cached_portfolios += 1

    elapsed_total = time.time() - start_time

    logger.info(
        f"Historical backfill completed in {elapsed_total:.2f}s | "
        f"Processed: {total_snapshots}, Success: {successful}, Failed: {failed}, "
        f"Cached: {cached_portfolios} portfolios"
    )

    return {
        "total_processed": total_snapshots,
        "successful": successful,
        "failed": failed,
        "cached_portfolios": cached_portfolios,
        "elapsed_seconds": elapsed_total,
    }


def main() -> None:
    """Execute historical backfill for all portfolios."""
    logger.info("=== Phase 2: Historical Risk Metrics Computation ===")

    stats = compute_all_historical_metrics(
        batch_size=50,
        portfolio_id=None,
        update_cache=True,
    )

    logger.info(f"Final statistics: {stats}")

    if stats["failed"] > 0:
        logger.warning(f"{stats['failed']} snapshots failed - review logs for details")


if __name__ == "__main__":
    main()
