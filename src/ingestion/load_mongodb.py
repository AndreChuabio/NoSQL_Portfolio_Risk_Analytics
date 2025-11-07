"""Load price history and synthetic portfolio holdings into MongoDB."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np
import pandas as pd
import yaml
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.operations import UpdateOne
from pymongo.errors import BulkWriteError

from config.mongodb_config import get_database, get_mongo_client
from src.ingestion.fetch_prices import TICKERS

logger = logging.getLogger(__name__)

SECTOR_MAP: Dict[str, str] = {
    "AAPL": "Technology",
    "MSFT": "Technology",
    "GOOGL": "Technology",
    "NVDA": "Technology",
    "META": "Technology",
    "AMZN": "Consumer Discretionary",
    "NFLX": "Communication Services",
    "JPM": "Financials",
    "BAC": "Financials",
    "GS": "Financials",
    "XOM": "Energy",
    "CVX": "Energy",
    "COP": "Energy",
    "SPY": "Benchmark",
    "QQQ": "Benchmark",
    "IWM": "Benchmark",
    "XLK": "Technology",
    "XLF": "Financials",
    "XLE": "Energy",
    "TSLA": "Consumer Discretionary",
}

BENCHMARK_TICKERS: tuple[str, ...] = ("SPY", "QQQ", "IWM")


@dataclass
class PortfolioConfig:
    """Configuration for building synthetic portfolio weights."""

    portfolio_id: str
    sector_limits: Dict[str, Dict[str, float]]
    position_size: Dict[str, float]
    rebalance_frequency: str


def load_prices(parquet_path: Path) -> pd.DataFrame:
    """Load OHLCV data from parquet."""

    data = pd.read_parquet(parquet_path)
    if not isinstance(data.columns, pd.MultiIndex):
        raise ValueError(
            "Expected a MultiIndex column structure for ticker and field")
    data.columns.names = ["Ticker", "Field"]
    data.index = pd.to_datetime(data.index, utc=True)
    return data.sort_index()


def generate_portfolio_configs(portfolio_yaml: Path) -> list[PortfolioConfig]:
    """Parse the portfolio configuration YAML file."""

    with portfolio_yaml.open("r", encoding="utf-8") as handle:
        raw_config = yaml.safe_load(handle)

    configs: list[PortfolioConfig] = []
    for portfolio_id, payload in raw_config.items():
        configs.append(
            PortfolioConfig(
                portfolio_id=portfolio_id,
                sector_limits=payload["sector_limits"],
                position_size=payload["position_size"],
                rebalance_frequency=payload["rebalance_frequency"],
            )
        )

    return configs


def _sample_sector_weights(config: PortfolioConfig, rng: np.random.Generator) -> Dict[str, float]:
    """Sample sector weights within configured bounds."""

    sector_weights: Dict[str, float] = {}
    for sector, bounds in config.sector_limits.items():
        min_w = float(bounds["min"])
        max_w = float(bounds["max"])
        sector_weights[sector] = rng.uniform(min_w, max_w)

    total = sum(sector_weights.values())
    residual = max(0.0, 1.0 - total)
    if residual > 0:
        sector_weights["Benchmark"] = sector_weights.get(
            "Benchmark", 0.0) + residual

    scaling = sum(sector_weights.values())
    if not np.isclose(scaling, 1.0, atol=1e-4):
        sector_weights = {sector: weight / scaling for sector,
                          weight in sector_weights.items()}

    return sector_weights


def _distribute_within_sector(
    sector_weights: Dict[str, float],
    tickers_by_sector: Dict[str, list[str]],
    position_bounds: Dict[str, float],
) -> Dict[str, float]:
    """Allocate sector weights across individual tickers."""

    ticker_weights: Dict[str, float] = {}
    min_pos = float(position_bounds["min"])
    max_pos = float(position_bounds["max"])

    for sector, weight in sector_weights.items():
        sector_tickers = tickers_by_sector.get(sector, [])
        if not sector_tickers:
            continue
        per_ticker = weight / len(sector_tickers)
        per_ticker = float(np.clip(per_ticker, min_pos, max_pos))
        for ticker in sector_tickers:
            ticker_weights[ticker] = per_ticker

    scaling = sum(ticker_weights.values())
    if scaling > 0:
        ticker_weights = {ticker: weight / scaling for ticker,
                          weight in ticker_weights.items()}

    return ticker_weights


def _build_ticker_sector_mapping() -> Dict[str, list[str]]:
    """Map sectors to the tickers available for allocation."""

    sector_map: Dict[str, list[str]] = {}
    for ticker, sector in SECTOR_MAP.items():
        sector_map.setdefault(sector, []).append(ticker)
    return sector_map


def _rebalance_frequency_days(freq: str) -> int:
    """Translate rebalance frequency keywords to day counts."""

    if freq.lower() == "weekly":
        return 5
    if freq.lower() == "monthly":
        return 21
    raise ValueError(f"Unsupported rebalance frequency: {freq}")


def build_portfolio_snapshots(
    prices: pd.DataFrame,
    configs: list[PortfolioConfig],
) -> list[Dict[str, object]]:
    """Generate synthetic portfolio snapshots based on price history."""

    close_prices = prices.xs("Close", axis=1, level="Field")
    returns = close_prices.pct_change().fillna(0.0)
    rolling_vol = (
        returns.rolling(window=20)
        .std()
        .bfill()
        .fillna(0.0)
    )

    tickers_by_sector = _build_ticker_sector_mapping()
    rng = np.random.default_rng(seed=42)

    snapshots: list[Dict[str, object]] = []
    for config in configs:
        rebalance_days = _rebalance_frequency_days(config.rebalance_frequency)
        current_weights: Dict[str, float] = {}
        days_until_rebalance = 0

        for as_of in close_prices.index:
            if days_until_rebalance <= 0 or not current_weights:
                sector_weights = _sample_sector_weights(config, rng)
                ticker_weights = _distribute_within_sector(
                    sector_weights, tickers_by_sector, config.position_size)
                current_weights = ticker_weights
                days_until_rebalance = rebalance_days
            days_until_rebalance -= 1

            asset_entries: list[Dict[str, object]] = []
            sector_exposure: Dict[str, float] = {}
            gross_exposure = 0.0

            for ticker, weight in current_weights.items():
                if ticker not in close_prices.columns:
                    continue
                price = float(close_prices.loc[as_of, ticker])
                vol = float(rolling_vol.loc[as_of, ticker])
                sector = SECTOR_MAP.get(ticker, "Other")
                asset_entries.append(
                    {
                        "ticker": ticker,
                        "weight": float(weight),
                        "sector": sector,
                        "price": price,
                        "daily_vol": vol,
                    }
                )
                sector_exposure[sector] = sector_exposure.get(
                    sector, 0.0) + float(weight)
                gross_exposure += float(weight)

            scaling = sum(item["weight"] for item in asset_entries)
            if scaling == 0:
                continue
            for item in asset_entries:
                item["weight"] = item["weight"] / scaling
            gross_exposure = sum(item["weight"] for item in asset_entries)
            sector_exposure = {
                sector: exp / gross_exposure for sector, exp in sector_exposure.items()}

            snapshot = {
                "portfolio_id": config.portfolio_id,
                "date": datetime.fromtimestamp(as_of.timestamp(), tz=timezone.utc),
                "assets": asset_entries,
                "gross_exposure": gross_exposure,
                "net_exposure_by_sector": sector_exposure,
            }
            snapshots.append(snapshot)

    return snapshots


def build_price_documents(prices: pd.DataFrame) -> List[Dict[str, object]]:
    """Convert the OHLCV DataFrame into MongoDB documents."""

    documents: list[Dict[str, object]] = []
    fields = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]

    for as_of, row in prices.iterrows():
        as_of_dt = datetime.fromtimestamp(
            pd.Timestamp(as_of).timestamp(), tz=timezone.utc)
        for ticker in TICKERS:
            ticker_slice = row.get(ticker)
            if ticker_slice is None:
                continue
            document = {
                "ticker": ticker,
                "date": as_of_dt,
                "source": "yfinance",
            }
            for field in fields:
                if field in ticker_slice:
                    document[field.lower().replace(" ", "_")] = float(
                        ticker_slice[field])
            documents.append(document)

    return documents


def upsert_documents(collection, documents: Iterable[Dict[str, object]], key_fields: tuple[str, ...]) -> None:
    """Perform bulk upserts for the provided documents."""

    requests: list[UpdateOne] = []
    for doc in documents:
        filter_query = {field: doc[field] for field in key_fields}
        requests.append(UpdateOne(filter_query, {"$set": doc}, upsert=True))

    if not requests:
        logger.warning("No documents to upsert")
        return

    try:
        collection.bulk_write(requests, ordered=False)
    except BulkWriteError as exc:
        logger.error("Bulk write failure", extra={"details": exc.details})
        raise


def ensure_indexes(db) -> None:
    """Create required indexes if they do not exist."""

    db.prices.create_index(
        [("ticker", ASCENDING), ("date", DESCENDING)], name="idx_prices_ticker_date")
    db.portfolio_holdings.create_index(
        [("portfolio_id", ASCENDING), ("date", DESCENDING)], name="idx_holdings_portfolio_date"
    )


def ingest(parquet_path: Path, portfolio_config_path: Path) -> None:
    """Ingest price history and portfolio holdings into MongoDB."""

    prices = load_prices(parquet_path)
    price_docs = build_price_documents(prices)
    configs = generate_portfolio_configs(portfolio_config_path)
    holdings_docs = build_portfolio_snapshots(prices, configs)

    logger.info(
        "Prepared documents",
        extra={
            "price_docs": len(price_docs),
            "holding_docs": len(holdings_docs),
        },
    )

    client: MongoClient = get_mongo_client()
    db = get_database(client)

    ensure_indexes(db)
    upsert_documents(db.prices, price_docs, key_fields=("ticker", "date"))
    upsert_documents(db.portfolio_holdings, holdings_docs,
                     key_fields=("portfolio_id", "date"))
    logger.info("Ingestion complete")


def main() -> None:
    """Execute the ingestion flow for the most recent raw dataset."""

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    data_dir = Path(__file__).resolve().parents[2] / "data" / "raw"
    parquet_files = sorted(data_dir.glob("prices_*.parquet"))
    if not parquet_files:
        raise FileNotFoundError("No parquet files found under data/raw")
    latest_file = parquet_files[-1]
    portfolio_config_path = Path(__file__).resolve(
    ).parents[2] / "config" / "portfolios.yaml"
    ingest(latest_file, portfolio_config_path)


if __name__ == "__main__":
    main()
