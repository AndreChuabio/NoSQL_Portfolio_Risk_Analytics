"""Value-at-Risk and Expected Shortfall calculations using Monte Carlo simulation."""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def validate_portfolio_inputs(
    returns: pd.DataFrame, weights: pd.Series, tolerance: float = 1e-4
) -> None:
    """
    Validate portfolio returns and weights for risk calculations.

    Args:
        returns: DataFrame of historical returns (rows=dates, cols=tickers)
        weights: Series of portfolio weights indexed by ticker
        tolerance: Acceptable deviation from weight sum of 1.0

    Raises:
        ValueError: If validation fails (shape mismatch, invalid weights, missing data)
    """
    if returns.empty:
        raise ValueError("Returns DataFrame is empty")

    if weights.empty:
        raise ValueError("Weights Series is empty")

    missing_tickers = set(weights.index) - set(returns.columns)
    if missing_tickers:
        raise ValueError(f"Weights contain tickers not in returns: {missing_tickers}")

    weight_sum = weights.sum()
    if not np.isclose(weight_sum, 1.0, atol=tolerance):
        raise ValueError(
            f"Portfolio weights sum to {weight_sum:.6f}, expected 1.0 (tolerance: {tolerance})"
        )

    if (weights < 0).any():
        raise ValueError("Negative weights detected - long-only portfolios required")

    if returns.isna().any().any():
        logger.warning("Returns contain NaN values - will forward fill missing data")


def calculate_portfolio_var(
    returns: pd.DataFrame,
    weights: pd.Series,
    confidence_level: float = 0.95,
    n_simulations: int = 1000,
    random_seed: Optional[int] = None,
) -> float:
    """
    Calculate portfolio Value-at-Risk using Monte Carlo simulation with historical sampling.

    VaR represents the maximum expected loss at a given confidence level. A 95% VaR of -2.31%
    means there is a 5% chance of losing more than 2.31% in a single period.

    Args:
        returns: DataFrame of historical returns (rows=dates, cols=tickers)
        weights: Series of portfolio weights indexed by ticker
        confidence_level: VaR confidence level (default 0.95 for 95% VaR)
        n_simulations: Number of Monte Carlo simulation paths (default 1000)
        random_seed: Random seed for reproducibility (optional)

    Returns:
        VaR as negative percentage (e.g., -0.0231 for -2.31% loss at 95% confidence)

    Raises:
        ValueError: If inputs fail validation

    Example:
        >>> returns = pd.DataFrame({'AAPL': [0.01, -0.02, 0.015], 'MSFT': [0.005, -0.01, 0.02]})
        >>> weights = pd.Series({'AAPL': 0.6, 'MSFT': 0.4})
        >>> var = calculate_portfolio_var(returns, weights, confidence_level=0.95)
        >>> print(f"95% VaR: {var:.4f}")
    """
    validate_portfolio_inputs(returns, weights)

    if not 0 < confidence_level < 1:
        raise ValueError(f"Confidence level must be between 0 and 1, got {confidence_level}")

    if n_simulations < 100:
        raise ValueError(f"Minimum 100 simulations required, got {n_simulations}")

    returns_filled = returns.ffill().fillna(0)
    aligned_returns = returns_filled[weights.index]

    rng = np.random.default_rng(random_seed)

    try:
        n_periods = len(aligned_returns)
        simulated_indices = rng.integers(0, n_periods, size=n_simulations)
        simulated_returns = aligned_returns.values[simulated_indices]

        portfolio_returns = simulated_returns @ weights.values

        percentile_rank = (1 - confidence_level) * 100
        var = np.percentile(portfolio_returns, percentile_rank)

        logger.info(
            f"VaR calculated: {var:.6f} "
            f"({n_simulations} simulations, {confidence_level:.0%} confidence)"
        )

        return float(var)

    except Exception as e:
        logger.error(f"VaR calculation failed: {e}", exc_info=True)
        raise


def calculate_expected_shortfall(
    returns: pd.DataFrame,
    weights: pd.Series,
    confidence_level: float = 0.95,
    n_simulations: int = 1000,
    random_seed: Optional[int] = None,
) -> float:
    """
    Calculate Expected Shortfall (Conditional VaR) using Monte Carlo simulation.

    Expected Shortfall represents the average loss in the worst (1 - confidence_level)
    scenarios. It is always more conservative than VaR at the same confidence level.

    Args:
        returns: DataFrame of historical returns (rows=dates, cols=tickers)
        weights: Series of portfolio weights indexed by ticker
        confidence_level: ES confidence level (default 0.95 for 95% ES)
        n_simulations: Number of Monte Carlo simulation paths (default 1000)
        random_seed: Random seed for reproducibility (optional)

    Returns:
        Expected Shortfall as negative percentage (e.g., -0.0312 for -3.12% average loss
        in worst 5% scenarios)

    Raises:
        ValueError: If inputs fail validation

    Example:
        >>> returns = pd.DataFrame({'AAPL': [0.01, -0.02, 0.015], 'MSFT': [0.005, -0.01, 0.02]})
        >>> weights = pd.Series({'AAPL': 0.6, 'MSFT': 0.4})
        >>> es = calculate_expected_shortfall(returns, weights, confidence_level=0.95)
        >>> print(f"95% ES: {es:.4f}")
    """
    validate_portfolio_inputs(returns, weights)

    if not 0 < confidence_level < 1:
        raise ValueError(f"Confidence level must be between 0 and 1, got {confidence_level}")

    if n_simulations < 100:
        raise ValueError(f"Minimum 100 simulations required, got {n_simulations}")

    returns_filled = returns.ffill().fillna(0)
    aligned_returns = returns_filled[weights.index]

    rng = np.random.default_rng(random_seed)

    try:
        n_periods = len(aligned_returns)
        simulated_indices = rng.integers(0, n_periods, size=n_simulations)
        simulated_returns = aligned_returns.values[simulated_indices]

        portfolio_returns = simulated_returns @ weights.values

        percentile_rank = (1 - confidence_level) * 100
        var_threshold = np.percentile(portfolio_returns, percentile_rank)

        worst_scenarios = portfolio_returns[portfolio_returns <= var_threshold]

        if len(worst_scenarios) == 0:
            logger.warning("No scenarios exceeded VaR threshold - returning VaR as ES")
            expected_shortfall = var_threshold
        else:
            expected_shortfall = np.mean(worst_scenarios)

        logger.info(
            f"Expected Shortfall calculated: {expected_shortfall:.6f} "
            f"(average of {len(worst_scenarios)} worst scenarios out of {n_simulations})"
        )

        return float(expected_shortfall)

    except Exception as e:
        logger.error(f"Expected Shortfall calculation failed: {e}", exc_info=True)
        raise


def calculate_portfolio_volatility(returns: pd.DataFrame, weights: pd.Series) -> float:
    """
    Calculate annualized portfolio volatility from historical returns.

    Args:
        returns: DataFrame of historical returns (rows=dates, cols=tickers)
        weights: Series of portfolio weights indexed by ticker

    Returns:
        Annualized portfolio volatility as decimal (e.g., 0.18 for 18% annualized vol)

    Raises:
        ValueError: If inputs fail validation
    """
    validate_portfolio_inputs(returns, weights)

    returns_filled = returns.ffill().fillna(0)
    aligned_returns = returns_filled[weights.index]

    portfolio_returns = aligned_returns @ weights.values

    daily_vol = portfolio_returns.std()
    annualized_vol = daily_vol * np.sqrt(252)

    logger.info(f"Portfolio volatility: {annualized_vol:.6f} (annualized)")

    return float(annualized_vol)
