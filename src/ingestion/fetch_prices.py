"""Download OHLCV data for the project universe and persist it under data/raw."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"

TICKERS: tuple[str, ...] = (
    "AAPL",
    "MSFT",
    "GOOGL",
    "NVDA",
    "META",
    "AMZN",
    "NFLX",
    "JPM",
    "BAC",
    "GS",
    "XOM",
    "CVX",
    "COP",
    "SPY",
    "QQQ",
    "IWM",
    "XLK",
    "XLF",
    "XLE",
    "TSLA",
)


def _validate_dataframe(df: pd.DataFrame, tickers: Iterable[str]) -> None:
    """Validate the downloaded dataset to ensure data quality.

    Args:
        df: Combined OHLCV DataFrame.
        tickers: Iterable of tickers expected to be present.

    Raises:
        ValueError: If validation fails.
    """

    missing_tickers = set(tickers) - set(df.columns.get_level_values("Ticker"))
    if missing_tickers:
        raise ValueError(
            f"Missing tickers in dataset: {sorted(missing_tickers)}")

    if df.isna().any().any():
        raise ValueError("Detected missing values in the OHLCV dataset")


def fetch_prices(start_date: datetime, end_date: datetime | None = None) -> pd.DataFrame:
    """Fetch OHLCV data for the configured ticker universe.

    Args:
        start_date: Start date for the pull.
        end_date: Optional end date (defaults to today).

    Returns:
        Multi-index DataFrame with date index and columns grouped by ticker and field.
    """

    end = end_date or datetime.utcnow()
    logger.info("Fetching OHLCV data", extra={
                "start": start_date.isoformat(), "end": end.isoformat()})

    data = yf.download(list(TICKERS), start=start_date,
                       end=end, group_by="ticker", auto_adjust=False)
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = data.columns.set_names(["Ticker", "Field"])
        data = data.sort_index(axis=1)

    _validate_dataframe(data, TICKERS)
    return data.sort_index()


def persist_prices(data: pd.DataFrame) -> Path:
    """Persist the OHLCV dataset to the raw data directory as Parquet.

    Args:
        data: DataFrame produced by fetch_prices.

    Returns:
        Path to the saved Parquet file.
    """

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    date_suffix = datetime.utcnow().strftime("%Y%m%d")
    output_path = RAW_DATA_DIR / f"prices_{date_suffix}.parquet"
    data.to_parquet(output_path)
    logger.info("Saved OHLCV data", extra={"path": str(output_path)})
    return output_path


def fetch_and_store_prices(years_back: int = 2) -> Path:
    """Fetch OHLCV data for the defined universe and write it to disk.

    Args:
        years_back: Number of trailing years to pull.

    Returns:
        Path to the persisted Parquet file.
    """

    start_date = datetime.utcnow() - timedelta(days=365 * years_back)
    data = fetch_prices(start_date=start_date)
    return persist_prices(data)


def main() -> None:
    """Script entry point for standalone execution."""

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    output_file = fetch_and_store_prices(years_back=2)
    logger.info("Data ingest complete", extra={"output": str(output_file)})


if __name__ == "__main__":
    main()
