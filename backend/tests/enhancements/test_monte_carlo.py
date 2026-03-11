"""
Tests for StrategyVault - Monte Carlo Simulation
Tests confidence intervals, p-values, and edge cases.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import numpy as np
from src.validation.monte_carlo import run_monte_carlo, MonteCarloResult


@pytest.fixture
def trending_returns():
    """Returns that show a clear trend (should be significant)."""
    np.random.seed(42)
    # Strong uptrend with noise
    return pd.Series(np.random.normal(0.003, 0.01, 252))


@pytest.fixture
def random_returns():
    """Purely random returns (should NOT be significant)."""
    np.random.seed(42)
    return pd.Series(np.random.normal(0.0, 0.02, 252))


class TestMonteCarloResult:
    def test_returns_correct_type(self, trending_returns):
        result = run_monte_carlo(trending_returns, num_simulations=100, seed=42)
        assert isinstance(result, MonteCarloResult)

    def test_num_simulations_stored(self, trending_returns):
        result = run_monte_carlo(trending_returns, num_simulations=200, seed=42)
        assert result.num_simulations == 200

    def test_confidence_intervals_ordered(self, trending_returns):
        result = run_monte_carlo(trending_returns, num_simulations=100, seed=42)
        assert result.return_ci_lower <= result.return_ci_upper
        assert result.sharpe_ci_lower <= result.sharpe_ci_upper

    def test_original_metrics_present(self, trending_returns):
        result = run_monte_carlo(trending_returns, num_simulations=100, seed=42)
        assert result.original_return != 0
        assert isinstance(result.original_sharpe, float)


class TestMonteCarloSignificance:
    def test_p_value_in_range(self, trending_returns):
        result = run_monte_carlo(trending_returns, num_simulations=100, seed=42)
        assert 0 <= result.p_value <= 1

    def test_is_significant_bool(self, trending_returns):
        result = run_monte_carlo(trending_returns, num_simulations=100, seed=42)
        assert isinstance(result.is_significant, bool)


class TestMonteCarloEdgeCases:
    def test_short_series(self):
        """Too-short returns should return non-significant result."""
        short = pd.Series([0.01, -0.01, 0.005])
        result = run_monte_carlo(short, num_simulations=100)
        assert result.num_simulations == 0
        assert result.is_significant is False

    def test_reproducible_with_seed(self, trending_returns):
        """Same seed should produce identical results."""
        r1 = run_monte_carlo(trending_returns, num_simulations=100, seed=42)
        r2 = run_monte_carlo(trending_returns, num_simulations=100, seed=42)
        assert r1.p_value == r2.p_value
        assert r1.return_ci_lower == r2.return_ci_lower

    def test_different_seeds_differ(self, trending_returns):
        """Different seeds should produce different results."""
        r1 = run_monte_carlo(trending_returns, num_simulations=100, seed=42)
        r2 = run_monte_carlo(trending_returns, num_simulations=100, seed=99)
        # Very unlikely to be exactly equal
        assert r1.return_ci_lower != r2.return_ci_lower
