"""Performance metrics: Sharpe ratio and Beta calculations."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def calculate_sharpe_ratio(
    returns: pd.DataFrame,
    weights: pd.Series,
    risk_free_rate: float = 0.0,
    window: int = 20,
    annualization_factor: float = np.sqrt(252),
) -> Optional[float]:
    """
    Calculate annualized Sharpe ratio for a portfolio using rolling window.

    Sharpe ratio measures risk-adjusted returns by dividing excess returns
    (above risk-free rate) by portfolio volatility.

    Args:
        returns: DataFrame of historical returns (rows=dates, cols=tickers)
        weights: Series of portfolio weights indexed by ticker
        risk_free_rate: Daily risk-free rate (default 0.0)
        window: Rolling window size in days (default 20)
        annualization_factor: Factor to annualize (default sqrt(252))

    Returns:
        Annualized Sharpe ratio (e.g., 1.45), or None if insufficient data

    Raises:
        ValueError: If inputs fail validation

    Example:
        >>> returns = pd.DataFrame({'AAPL': [0.01, -0.02, 0.015], 'MSFT': [0.005, -0.01, 0.02]})
        >>> weights = pd.Series({'AAPL': 0.6, 'MSFT': 0.4})
        >>> sharpe = calculate_sharpe_ratio(returns, weights, window=20)
    """
    if returns.empty:
        raise ValueError("Returns DataFrame is empty")

    if weights.empty:
        raise ValueError("Weights Series is empty")

    missing_tickers = set(weights.index) - set(returns.columns)
    if missing_tickers:
        raise ValueError(f"Weights contain tickers not in returns: {missing_tickers}")

    weight_sum = weights.sum()
    if not np.isclose(weight_sum, 1.0, atol=1e-4):
        raise ValueError(
            f"Portfolio weights sum to {weight_sum:.6f}, expected 1.0 (tolerance: 1e-4)"
        )

    if window < 2:
        raise ValueError(f"Window must be at least 2 days, got {window}")

    if len(returns) < window:
        logger.warning(
            f"Insufficient data for Sharpe calculation: {len(returns)} days < {window} window"
        )
        return None

    returns_filled = returns.ffill().fillna(0)
    aligned_returns = returns_filled[weights.index]

    portfolio_returns = aligned_returns @ weights.values

    rolling_mean = portfolio_returns.rolling(window=window).mean()
    rolling_std = portfolio_returns.rolling(window=window).std()

    latest_mean = rolling_mean.iloc[-1]
    latest_std = rolling_std.iloc[-1]

    if pd.isna(latest_mean) or pd.isna(latest_std):
        logger.warning("Rolling statistics contain NaN - insufficient data")
        return None

    if latest_std == 0:
        logger.warning("Zero volatility detected - cannot compute Sharpe ratio")
        return None

    excess_return = latest_mean - risk_free_rate
    sharpe_ratio = (excess_return / latest_std) * annualization_factor

    logger.info(
        f"Sharpe ratio calculated: {sharpe_ratio:.4f} "
        f"(window={window}d, mean={latest_mean:.6f}, std={latest_std:.6f})"
    )

    return float(sharpe_ratio)


def calculate_beta(
    portfolio_returns: pd.Series,
    benchmark_returns: pd.Series,
    window: int = 20,
) -> Optional[float]:
    """
    Calculate rolling beta of portfolio versus benchmark using linear regression.

    Beta measures systematic risk relative to the benchmark. Beta > 1 indicates
    higher volatility than benchmark, Beta < 1 indicates lower volatility.

    Args:
        portfolio_returns: Series of portfolio returns indexed by date
        benchmark_returns: Series of benchmark returns indexed by date
        window: Rolling window size in days (default 20)

    Returns:
        Beta coefficient (e.g., 1.12), or None if insufficient data

    Raises:
        ValueError: If inputs fail validation

    Example:
        >>> port_returns = pd.Series([0.01, -0.02, 0.015], index=pd.date_range('2025-01-01', periods=3))
        >>> bench_returns = pd.Series([0.008, -0.015, 0.012], index=pd.date_range('2025-01-01', periods=3))
        >>> beta = calculate_beta(port_returns, bench_returns, window=20)
    """
    if portfolio_returns.empty:
        raise ValueError("Portfolio returns Series is empty")

    if benchmark_returns.empty:
        raise ValueError("Benchmark returns Series is empty")

    if window < 2:
        raise ValueError(f"Window must be at least 2 days, got {window}")

    aligned_portfolio, aligned_benchmark = portfolio_returns.align(benchmark_returns, join="inner")

    if len(aligned_portfolio) < window:
        logger.warning(
            f"Insufficient data for beta calculation: {len(aligned_portfolio)} days < {window} window"
        )
        return None

    portfolio_filled = aligned_portfolio.ffill().fillna(0)
    benchmark_filled = aligned_benchmark.ffill().fillna(0)

    rolling_cov = portfolio_filled.rolling(window=window).cov(benchmark_filled)
    rolling_var = benchmark_filled.rolling(window=window).var()

    latest_cov = rolling_cov.iloc[-1]
    latest_var = rolling_var.iloc[-1]

    if pd.isna(latest_cov) or pd.isna(latest_var):
        logger.warning("Rolling covariance/variance contain NaN - insufficient data")
        return None

    if latest_var == 0:
        logger.warning("Zero benchmark variance - cannot compute beta")
        return None

    beta = latest_cov / latest_var

    logger.info(
        f"Beta calculated: {beta:.4f} (window={window}d, cov={latest_cov:.6f}, var={latest_var:.6f})"
    )

    return float(beta)


def calculate_beta_from_dataframes(
    returns: pd.DataFrame,
    weights: pd.Series,
    benchmark_ticker: str,
    window: int = 20,
) -> Optional[float]:
    """
    Calculate portfolio beta versus benchmark from returns DataFrame.

    Convenience function that constructs portfolio returns and extracts benchmark
    returns from the same DataFrame.

    Args:
        returns: DataFrame of historical returns (rows=dates, cols=tickers)
        weights: Series of portfolio weights indexed by ticker
        benchmark_ticker: Ticker symbol for benchmark (e.g., 'SPY')
        window: Rolling window size in days (default 20)

    Returns:
        Beta coefficient (e.g., 1.12), or None if insufficient data

    Raises:
        ValueError: If inputs fail validation or benchmark ticker not found

    Example:
        >>> returns = pd.DataFrame({
        ...     'AAPL': [0.01, -0.02, 0.015],
        ...     'MSFT': [0.005, -0.01, 0.02],
        ...     'SPY': [0.008, -0.015, 0.012]
        ... })
        >>> weights = pd.Series({'AAPL': 0.6, 'MSFT': 0.4})
        >>> beta = calculate_beta_from_dataframes(returns, weights, 'SPY', window=20)
    """
    if benchmark_ticker not in returns.columns:
        raise ValueError(f"Benchmark ticker '{benchmark_ticker}' not found in returns DataFrame")

    returns_filled = returns.ffill().fillna(0)

    portfolio_tickers = [ticker for ticker in weights.index if ticker != benchmark_ticker]

    if not portfolio_tickers:
        raise ValueError("No valid portfolio tickers after excluding benchmark")

    portfolio_weights = weights[portfolio_tickers]
    weight_sum = portfolio_weights.sum()

    if not np.isclose(weight_sum, 1.0, atol=1e-4):
        logger.warning(
            f"Portfolio weights (excluding benchmark) sum to {weight_sum:.6f}, normalizing to 1.0"
        )
        portfolio_weights = portfolio_weights / weight_sum

    aligned_returns = returns_filled[portfolio_weights.index]
    portfolio_returns = aligned_returns @ portfolio_weights.values

    benchmark_returns = returns_filled[benchmark_ticker]

    return calculate_beta(portfolio_returns, benchmark_returns, window=window)


def calculate_rolling_volatility(
    returns: pd.DataFrame, weights: pd.Series, window: int = 20
) -> Optional[float]:
    """
    Calculate rolling portfolio volatility.

    Args:
        returns: DataFrame of historical returns (rows=dates, cols=tickers)
        weights: Series of portfolio weights indexed by ticker
        window: Rolling window size in days (default 20)

    Returns:
        Annualized rolling volatility as decimal (e.g., 0.18 for 18%), or None if insufficient data

    Raises:
        ValueError: If inputs fail validation
    """
    if returns.empty:
        raise ValueError("Returns DataFrame is empty")

    if weights.empty:
        raise ValueError("Weights Series is empty")

    if window < 2:
        raise ValueError(f"Window must be at least 2 days, got {window}")

    if len(returns) < window:
        logger.warning(
            f"Insufficient data for volatility calculation: {len(returns)} days < {window} window"
        )
        return None

    returns_filled = returns.ffill().fillna(0)
    aligned_returns = returns_filled[weights.index]

    portfolio_returns = aligned_returns @ weights.values

    rolling_std = portfolio_returns.rolling(window=window).std()
    latest_std = rolling_std.iloc[-1]

    if pd.isna(latest_std):
        logger.warning("Rolling std contains NaN - insufficient data")
        return None

    annualized_vol = latest_std * np.sqrt(252)

    logger.info(f"Rolling volatility calculated: {annualized_vol:.6f} (window={window}d)")

    return float(annualized_vol)
