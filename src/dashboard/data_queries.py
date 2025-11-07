"""
Data query functions for the Streamlit dashboard.

Handles fetching metrics from Redis (cache) and MongoDB (persistent storage)
with proper fallback logic and performance instrumentation.
"""

from config.redis_config import get_redis_client
from config.mongodb_config import get_mongo_client, get_database
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import pandas as pd
import streamlit as st
from pymongo import DESCENDING

# Add project root to path for config imports
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)


logger = logging.getLogger(__name__)


@st.cache_resource
def get_db_connections() -> Tuple[object, object]:
    """
    Initialize MongoDB and Redis connections (cached for session).

    Returns:
        Tuple of (MongoDB database handle, Redis client)
    """
    mongo_client = get_mongo_client()
    db = get_database(mongo_client, "portfolio_risk")
    redis_client = get_redis_client()
    return db, redis_client


def fetch_latest_metrics_from_redis(
    portfolio_id: str, redis_client: object
) -> Tuple[Optional[Dict], float]:
    """
    Fetch latest metrics from Redis cache.

    Args:
        portfolio_id: Portfolio identifier (e.g., "PORT_A_TechGrowth")
        redis_client: Active Redis client

    Returns:
        Tuple of (metrics dict or None, query latency in ms)
    """
    start_time = time.time()

    try:
        # Try to fetch all metric types from Redis
        metrics = {}
        metric_types = ["VaR", "Sharpe", "Beta", "ES", "Volatility"]

        for metric_type in metric_types:
            key = f"{metric_type}:{portfolio_id}"
            cached_value = redis_client.get(key)

            if cached_value:
                data = json.loads(cached_value)
                metrics[metric_type.lower()] = data

        latency_ms = (time.time() - start_time) * 1000

        if metrics:
            logger.info(
                f"Redis cache hit for {portfolio_id}: {len(metrics)} metrics found")
            return metrics, latency_ms
        else:
            logger.info(f"Redis cache miss for {portfolio_id}")
            return None, latency_ms

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Redis query failed for {portfolio_id}: {e}")
        return None, latency_ms


def fetch_latest_metrics_from_mongodb(
    portfolio_id: str, db: object
) -> Tuple[Optional[Dict], float]:
    """
    Fetch latest metrics from MongoDB risk_metrics collection.

    Args:
        portfolio_id: Portfolio identifier
        db: MongoDB database handle

    Returns:
        Tuple of (metrics dict or None, query latency in ms)
    """
    start_time = time.time()

    try:
        # Query for the most recent metric document
        latest_metric = db.risk_metrics.find_one(
            {"portfolio_id": portfolio_id},
            sort=[("date", DESCENDING)]
        )

        latency_ms = (time.time() - start_time) * 1000

        if latest_metric:
            # Convert MongoDB document to standardized format
            metrics = {
                "var": {
                    "value": latest_metric.get("VaR_95"),
                    "ts": latest_metric.get("date").isoformat() + "Z" if latest_metric.get("date") else None
                },
                "sharpe": {
                    "value": latest_metric.get("sharpe_ratio_20d"),
                    "ts": latest_metric.get("date").isoformat() + "Z" if latest_metric.get("date") else None
                },
                "beta": {
                    "value": latest_metric.get("beta_vs_SPY_20d"),
                    "ts": latest_metric.get("date").isoformat() + "Z" if latest_metric.get("date") else None
                },
                "es": {
                    "value": latest_metric.get("expected_shortfall"),
                    "ts": latest_metric.get("date").isoformat() + "Z" if latest_metric.get("date") else None
                },
                "volatility": {
                    "value": latest_metric.get("portfolio_volatility_20d"),
                    "ts": latest_metric.get("date").isoformat() + "Z" if latest_metric.get("date") else None
                }
            }

            logger.info(
                f"MongoDB query successful for {portfolio_id} (latency: {latency_ms:.2f}ms)")
            return metrics, latency_ms
        else:
            logger.warning(f"No metrics found in MongoDB for {portfolio_id}")
            return None, latency_ms

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"MongoDB query failed for {portfolio_id}: {e}")
        return None, latency_ms


@st.cache_data(ttl=60)
def fetch_latest_metrics(portfolio_id: str) -> Tuple[Optional[Dict], str, Dict[str, float]]:
    """
    Fetch latest metrics with Redis-first fallback to MongoDB.

    Args:
        portfolio_id: Portfolio identifier

    Returns:
        Tuple of (metrics dict, data source string, latency dict)
    """
    db, redis_client = get_db_connections()
    latencies = {}

    # Try Redis first
    redis_metrics, redis_latency = fetch_latest_metrics_from_redis(
        portfolio_id, redis_client)
    latencies["redis"] = redis_latency

    if redis_metrics:
        return redis_metrics, "Redis (Real-time)", latencies

    # Fallback to MongoDB
    mongo_metrics, mongo_latency = fetch_latest_metrics_from_mongodb(
        portfolio_id, db)
    latencies["mongodb"] = mongo_latency

    if mongo_metrics:
        return mongo_metrics, "MongoDB (Historical)", latencies

    return None, "No Data", latencies


@st.cache_data(ttl=60)
def fetch_historical_metrics(
    portfolio_id: str, days: int = 60
) -> Tuple[Optional[pd.DataFrame], float]:
    """
    Fetch historical risk metrics from MongoDB for time series charts.

    Args:
        portfolio_id: Portfolio identifier
        days: Number of days to look back

    Returns:
        Tuple of (DataFrame with metrics or None, query latency in ms)
    """
    start_time = time.time()
    db, _ = get_db_connections()

    try:
        # Calculate date threshold
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # Query MongoDB
        cursor = db.risk_metrics.find(
            {
                "portfolio_id": portfolio_id,
                "date": {"$gte": start_date, "$lte": end_date}
            },
            {
                "date": 1,
                "VaR_95": 1,
                "expected_shortfall": 1,
                "sharpe_ratio_20d": 1,
                "beta_vs_SPY_20d": 1,
                "portfolio_volatility_20d": 1,
                "_id": 0
            }
        ).sort("date", 1)

        # Convert to DataFrame
        data = list(cursor)
        latency_ms = (time.time() - start_time) * 1000

        if data:
            df = pd.DataFrame(data)

            # Rename columns if they exist
            rename_map = {
                "VaR_95": "VaR",
                "expected_shortfall": "ES",
                "sharpe_ratio_20d": "Sharpe",
                "beta_vs_SPY_20d": "Beta",
                "portfolio_volatility_20d": "Volatility"
            }

            # Only rename columns that actually exist in the DataFrame
            existing_renames = {k: v for k,
                                v in rename_map.items() if k in df.columns}
            df.rename(columns=existing_renames, inplace=True)

            # Log what columns we have
            logger.info(f"DataFrame columns: {df.columns.tolist()}")

            logger.info(
                f"Fetched {len(df)} historical metrics for {portfolio_id} "
                f"({days} days, latency: {latency_ms:.2f}ms)"
            )
            return df, latency_ms
        else:
            logger.warning(
                f"No historical data found for {portfolio_id} in last {days} days")
            return None, latency_ms

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Historical query failed for {portfolio_id}: {e}")
        return None, latency_ms


@st.cache_data(ttl=300)
def fetch_latest_portfolio_holdings(portfolio_id: str) -> Tuple[Optional[Dict], float]:
    """
    Fetch latest portfolio holdings for sector exposure breakdown.

    Args:
        portfolio_id: Portfolio identifier

    Returns:
        Tuple of (holdings dict with sector breakdown or None, query latency in ms)
    """
    start_time = time.time()
    db, _ = get_db_connections()

    try:
        # Query for most recent holdings snapshot
        latest_holdings = db.portfolio_holdings.find_one(
            {"portfolio_id": portfolio_id},
            sort=[("date", DESCENDING)]
        )

        latency_ms = (time.time() - start_time) * 1000

        if latest_holdings and "assets" in latest_holdings:
            # Aggregate by sector
            sector_weights = {}
            for asset in latest_holdings["assets"]:
                sector = asset.get("sector", "Unknown")
                weight = asset.get("weight", 0)
                sector_weights[sector] = sector_weights.get(sector, 0) + weight

            holdings_data = {
                "date": latest_holdings.get("date"),
                "sector_weights": sector_weights,
                "gross_exposure": latest_holdings.get("gross_exposure"),
                "num_assets": len(latest_holdings["assets"])
            }

            logger.info(
                f"Fetched holdings for {portfolio_id} (latency: {latency_ms:.2f}ms)")
            return holdings_data, latency_ms
        else:
            logger.warning(f"No holdings found for {portfolio_id}")
            return None, latency_ms

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        logger.error(f"Holdings query failed for {portfolio_id}: {e}")
        return None, latency_ms


@st.cache_data(ttl=60)
def get_available_portfolios() -> List[str]:
    """
    Get list of portfolios with data in MongoDB.

    Returns:
        List of portfolio IDs
    """
    db, _ = get_db_connections()

    try:
        # Get distinct portfolio IDs from risk_metrics collection
        portfolios = db.risk_metrics.distinct("portfolio_id")
        logger.info(f"Found {len(portfolios)} portfolios in database")
        return sorted(portfolios)
    except Exception as e:
        logger.error(f"Failed to fetch portfolio list: {e}")
        return []
