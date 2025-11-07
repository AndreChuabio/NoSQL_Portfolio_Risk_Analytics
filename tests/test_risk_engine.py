"""Unit tests for risk engine calculations."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.risk_engine.performance_metrics import (
    calculate_beta,
    calculate_beta_from_dataframes,
    calculate_rolling_volatility,
    calculate_sharpe_ratio,
)
from src.risk_engine.var_calculator import (
    calculate_expected_shortfall,
    calculate_portfolio_var,
    calculate_portfolio_volatility,
    validate_portfolio_inputs,
)


@pytest.fixture
def simple_returns():
    """Create deterministic returns for testing."""
    dates = pd.date_range("2025-01-01", periods=100, freq="D")
    returns = pd.DataFrame(
        {
            "AAPL": np.random.RandomState(42).normal(0.001, 0.02, 100),
            "MSFT": np.random.RandomState(43).normal(0.0008, 0.018, 100),
            "GOOGL": np.random.RandomState(44).normal(0.0012, 0.022, 100),
        },
        index=dates,
    )
    return returns


@pytest.fixture
def equal_weights():
    """Create equal weights for 3 assets."""
    return pd.Series({"AAPL": 1 / 3, "MSFT": 1 / 3, "GOOGL": 1 / 3})


@pytest.fixture
def benchmark_returns():
    """Create benchmark returns for beta testing."""
    dates = pd.date_range("2025-01-01", periods=100, freq="D")
    return pd.Series(
        np.random.RandomState(50).normal(0.0005, 0.015, 100),
        index=dates,
        name="SPY",
    )


class TestValidatePortfolioInputs:
    """Tests for portfolio input validation."""

    def test_valid_inputs(self, simple_returns, equal_weights):
        """Test that valid inputs pass validation."""
        validate_portfolio_inputs(simple_returns, equal_weights)

    def test_empty_returns(self, equal_weights):
        """Test that empty returns raise ValueError."""
        with pytest.raises(ValueError, match="Returns DataFrame is empty"):
            validate_portfolio_inputs(pd.DataFrame(), equal_weights)

    def test_empty_weights(self, simple_returns):
        """Test that empty weights raise ValueError."""
        with pytest.raises(ValueError, match="Weights Series is empty"):
            validate_portfolio_inputs(simple_returns, pd.Series(dtype=float))

    def test_weights_not_sum_to_one(self, simple_returns):
        """Test that weights not summing to 1.0 raise ValueError."""
        bad_weights = pd.Series({"AAPL": 0.5, "MSFT": 0.3, "GOOGL": 0.1})
        with pytest.raises(ValueError, match="weights sum to"):
            validate_portfolio_inputs(simple_returns, bad_weights)

    def test_negative_weights(self, simple_returns):
        """Test that negative weights raise ValueError."""
        bad_weights = pd.Series({"AAPL": 0.6, "MSFT": 0.6, "GOOGL": -0.2})
        with pytest.raises(ValueError, match="Negative weights detected"):
            validate_portfolio_inputs(simple_returns, bad_weights)

    def test_missing_tickers(self, simple_returns):
        """Test that weights with missing tickers raise ValueError."""
        bad_weights = pd.Series({"AAPL": 0.5, "NVDA": 0.5})
        with pytest.raises(ValueError, match="Weights contain tickers not in returns"):
            validate_portfolio_inputs(simple_returns, bad_weights)


class TestCalculatePortfolioVar:
    """Tests for VaR calculation."""

    def test_var_basic_calculation(self, simple_returns, equal_weights):
        """Test basic VaR calculation returns negative value."""
        var = calculate_portfolio_var(
            simple_returns, equal_weights, confidence_level=0.95, n_simulations=1000
        )
        assert isinstance(var, float)
        assert var < 0, "VaR should be negative (representing a loss)"

    def test_var_deterministic_seed(self, simple_returns, equal_weights):
        """Test that random seed produces reproducible results."""
        var1 = calculate_portfolio_var(
            simple_returns, equal_weights, confidence_level=0.95, random_seed=42
        )
        var2 = calculate_portfolio_var(
            simple_returns, equal_weights, confidence_level=0.95, random_seed=42
        )
        assert var1 == var2, "Same seed should produce identical VaR"

    def test_var_confidence_levels(self, simple_returns, equal_weights):
        """Test that higher confidence levels produce more conservative VaR."""
        var_95 = calculate_portfolio_var(
            simple_returns, equal_weights, confidence_level=0.95, random_seed=42
        )
        var_99 = calculate_portfolio_var(
            simple_returns, equal_weights, confidence_level=0.99, random_seed=42
        )
        assert var_99 < var_95, "99% VaR should be more conservative (more negative) than 95%"

    def test_var_invalid_confidence(self, simple_returns, equal_weights):
        """Test that invalid confidence levels raise ValueError."""
        with pytest.raises(ValueError, match="Confidence level must be between 0 and 1"):
            calculate_portfolio_var(simple_returns, equal_weights, confidence_level=1.5)

    def test_var_insufficient_simulations(self, simple_returns, equal_weights):
        """Test that too few simulations raise ValueError."""
        with pytest.raises(ValueError, match="Minimum 100 simulations required"):
            calculate_portfolio_var(simple_returns, equal_weights, n_simulations=50)

    def test_var_single_asset(self, simple_returns):
        """Test VaR calculation with single asset portfolio."""
        single_weight = pd.Series({"AAPL": 1.0})
        var = calculate_portfolio_var(
            simple_returns, single_weight, confidence_level=0.95, random_seed=42
        )
        assert isinstance(var, float)
        assert var < 0


class TestCalculateExpectedShortfall:
    """Tests for Expected Shortfall calculation."""

    def test_es_basic_calculation(self, simple_returns, equal_weights):
        """Test basic ES calculation returns negative value."""
        es = calculate_expected_shortfall(
            simple_returns, equal_weights, confidence_level=0.95, n_simulations=1000
        )
        assert isinstance(es, float)
        assert es < 0, "ES should be negative (representing a loss)"

    def test_es_more_conservative_than_var(self, simple_returns, equal_weights):
        """Test that ES is more conservative than VaR."""
        var = calculate_portfolio_var(
            simple_returns, equal_weights, confidence_level=0.95, random_seed=42
        )
        es = calculate_expected_shortfall(
            simple_returns, equal_weights, confidence_level=0.95, random_seed=42
        )
        assert es <= var, "Expected Shortfall should be more conservative than VaR"

    def test_es_deterministic_seed(self, simple_returns, equal_weights):
        """Test that random seed produces reproducible results."""
        es1 = calculate_expected_shortfall(
            simple_returns, equal_weights, confidence_level=0.95, random_seed=42
        )
        es2 = calculate_expected_shortfall(
            simple_returns, equal_weights, confidence_level=0.95, random_seed=42
        )
        assert es1 == es2, "Same seed should produce identical ES"


class TestCalculatePortfolioVolatility:
    """Tests for portfolio volatility calculation."""

    def test_volatility_basic_calculation(self, simple_returns, equal_weights):
        """Test basic volatility calculation returns positive value."""
        vol = calculate_portfolio_volatility(simple_returns, equal_weights)
        assert isinstance(vol, float)
        assert vol > 0, "Volatility should be positive"

    def test_volatility_zero_returns(self, equal_weights):
        """Test volatility with zero returns."""
        dates = pd.date_range("2025-01-01", periods=100, freq="D")
        zero_returns = pd.DataFrame(
            {"AAPL": np.zeros(100), "MSFT": np.zeros(100), "GOOGL": np.zeros(100)},
            index=dates,
        )
        vol = calculate_portfolio_volatility(zero_returns, equal_weights)
        assert vol == 0.0, "Volatility of zero returns should be zero"


class TestCalculateSharpeRatio:
    """Tests for Sharpe ratio calculation."""

    def test_sharpe_basic_calculation(self, simple_returns, equal_weights):
        """Test basic Sharpe ratio calculation."""
        sharpe = calculate_sharpe_ratio(simple_returns, equal_weights, window=20)
        assert isinstance(sharpe, float)

    def test_sharpe_insufficient_data(self, equal_weights):
        """Test Sharpe ratio with insufficient data returns None."""
        dates = pd.date_range("2025-01-01", periods=10, freq="D")
        short_returns = pd.DataFrame(
            {
                "AAPL": np.random.randn(10),
                "MSFT": np.random.randn(10),
                "GOOGL": np.random.randn(10),
            },
            index=dates,
        )
        sharpe = calculate_sharpe_ratio(short_returns, equal_weights, window=20)
        assert sharpe is None, "Should return None when insufficient data"

    def test_sharpe_positive_returns(self, equal_weights):
        """Test Sharpe ratio with consistently positive returns."""
        dates = pd.date_range("2025-01-01", periods=50, freq="D")
        positive_returns = pd.DataFrame(
            {
                "AAPL": np.random.RandomState(60).uniform(0.001, 0.01, 50),
                "MSFT": np.random.RandomState(61).uniform(0.001, 0.01, 50),
                "GOOGL": np.random.RandomState(62).uniform(0.001, 0.01, 50),
            },
            index=dates,
        )
        sharpe = calculate_sharpe_ratio(positive_returns, equal_weights, window=20)
        assert sharpe is not None
        assert sharpe > 0, "Sharpe ratio should be positive for positive returns"

    def test_sharpe_zero_volatility(self, equal_weights):
        """Test Sharpe ratio with zero volatility returns None."""
        dates = pd.date_range("2025-01-01", periods=50, freq="D")
        constant_returns = pd.DataFrame(
            {"AAPL": np.full(50, 0.01), "MSFT": np.full(50, 0.01), "GOOGL": np.full(50, 0.01)},
            index=dates,
        )
        sharpe = calculate_sharpe_ratio(constant_returns, equal_weights, window=20)
        assert sharpe is None, "Should return None when volatility is zero"


class TestCalculateBeta:
    """Tests for beta calculation."""

    def test_beta_basic_calculation(self, simple_returns, benchmark_returns, equal_weights):
        """Test basic beta calculation."""
        portfolio_returns = simple_returns @ equal_weights.values
        beta = calculate_beta(portfolio_returns, benchmark_returns, window=20)
        assert isinstance(beta, float)

    def test_beta_insufficient_data(self, benchmark_returns, equal_weights):
        """Test beta with insufficient data returns None."""
        dates = pd.date_range("2025-01-01", periods=10, freq="D")
        short_returns = pd.DataFrame(
            {
                "AAPL": np.random.randn(10),
                "MSFT": np.random.randn(10),
                "GOOGL": np.random.randn(10),
            },
            index=dates,
        )
        portfolio_returns = short_returns @ equal_weights.values
        beta = calculate_beta(portfolio_returns, benchmark_returns[:10], window=20)
        assert beta is None, "Should return None when insufficient data"

    def test_beta_perfect_correlation(self):
        """Test beta with perfect correlation to benchmark."""
        dates = pd.date_range("2025-01-01", periods=50, freq="D")
        benchmark = pd.Series(np.random.RandomState(70).randn(50), index=dates)
        portfolio = benchmark.copy()

        beta = calculate_beta(portfolio, benchmark, window=20)
        assert beta is not None
        assert abs(beta - 1.0) < 0.1, "Beta should be close to 1.0 for perfect correlation"


class TestCalculateBetaFromDataframes:
    """Tests for beta calculation from DataFrames."""

    def test_beta_from_dataframes(self, simple_returns, equal_weights):
        """Test beta calculation from DataFrame with benchmark column."""
        returns_with_bench = simple_returns.copy()
        returns_with_bench["SPY"] = np.random.RandomState(80).normal(
            0.0005, 0.015, len(simple_returns)
        )

        beta = calculate_beta_from_dataframes(returns_with_bench, equal_weights, "SPY", window=20)
        assert isinstance(beta, float) or beta is None

    def test_beta_missing_benchmark(self, simple_returns, equal_weights):
        """Test beta calculation with missing benchmark ticker."""
        with pytest.raises(ValueError, match="Benchmark ticker .* not found"):
            calculate_beta_from_dataframes(simple_returns, equal_weights, "QQQ", window=20)


class TestCalculateRollingVolatility:
    """Tests for rolling volatility calculation."""

    def test_rolling_volatility_basic(self, simple_returns, equal_weights):
        """Test basic rolling volatility calculation."""
        vol = calculate_rolling_volatility(simple_returns, equal_weights, window=20)
        assert isinstance(vol, float)
        assert vol > 0, "Volatility should be positive"

    def test_rolling_volatility_insufficient_data(self, equal_weights):
        """Test rolling volatility with insufficient data returns None."""
        dates = pd.date_range("2025-01-01", periods=10, freq="D")
        short_returns = pd.DataFrame(
            {
                "AAPL": np.random.randn(10),
                "MSFT": np.random.randn(10),
                "GOOGL": np.random.randn(10),
            },
            index=dates,
        )
        vol = calculate_rolling_volatility(short_returns, equal_weights, window=20)
        assert vol is None, "Should return None when insufficient data"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
