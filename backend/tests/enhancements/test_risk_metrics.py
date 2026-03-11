"""
Tests for StrategyVault - Advanced Risk Metrics
Tests each risk metric against known values and edge cases.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import numpy as np
from src.features.risk_metrics import (
    calmar_ratio,
    value_at_risk,
    conditional_var,
    omega_ratio,
    profit_factor,
    information_ratio,
    ulcer_index,
    compute_all_risk_metrics,
)


@pytest.fixture
def positive_returns():
    """Returns series that is consistently positive."""
    np.random.seed(42)
    return pd.Series(np.random.uniform(0.001, 0.02, 252))


@pytest.fixture
def negative_returns():
    """Returns series that is consistently negative."""
    np.random.seed(42)
    return pd.Series(np.random.uniform(-0.02, -0.001, 252))


@pytest.fixture
def mixed_returns():
    """Returns series with both positive and negative returns."""
    np.random.seed(42)
    return pd.Series(np.random.normal(0.001, 0.02, 252))


@pytest.fixture
def empty_returns():
    """Empty returns series."""
    return pd.Series([], dtype=float)


class TestCalmarRatio:
    def test_positive_returns(self, positive_returns):
        result = calmar_ratio(positive_returns)
        assert result > 0

    def test_empty_returns(self, empty_returns):
        assert calmar_ratio(empty_returns) == 0.0


class TestValueAtRisk:
    def test_var_95(self, mixed_returns):
        var = value_at_risk(mixed_returns, 0.95)
        assert var < 0  # VaR should be negative (a loss)

    def test_var_99_more_extreme(self, mixed_returns):
        var_95 = value_at_risk(mixed_returns, 0.95)
        var_99 = value_at_risk(mixed_returns, 0.99)
        assert var_99 <= var_95  # 99% VaR should be more extreme

    def test_empty_returns(self, empty_returns):
        assert value_at_risk(empty_returns) == 0.0


class TestConditionalVaR:
    def test_cvar_worse_than_var(self, mixed_returns):
        var = value_at_risk(mixed_returns, 0.95)
        cvar = conditional_var(mixed_returns, 0.95)
        assert cvar <= var  # CVaR should be worse (more negative)

    def test_empty_returns(self, empty_returns):
        assert conditional_var(empty_returns) == 0.0


class TestOmegaRatio:
    def test_positive_returns_above_one(self, positive_returns):
        result = omega_ratio(positive_returns)
        assert result > 1  # All positive → Omega >> 1

    def test_negative_returns_below_one(self, negative_returns):
        result = omega_ratio(negative_returns)
        assert result < 1  # All negative → Omega < 1

    def test_empty_returns(self, empty_returns):
        assert omega_ratio(empty_returns) == 0.0


class TestProfitFactor:
    def test_profitable_strategy(self, positive_returns):
        result = profit_factor(positive_returns)
        assert result == float("inf")  # All positive

    def test_mixed_returns(self, mixed_returns):
        result = profit_factor(mixed_returns)
        assert result > 0

    def test_empty_returns(self, empty_returns):
        assert profit_factor(empty_returns) == 0.0


class TestInformationRatio:
    def test_no_benchmark(self, mixed_returns):
        result = information_ratio(mixed_returns)
        assert isinstance(result, float)

    def test_empty_returns(self, empty_returns):
        assert information_ratio(empty_returns) == 0.0


class TestUlcerIndex:
    def test_positive_returns_low_ulcer(self, positive_returns):
        result = ulcer_index(positive_returns)
        assert result >= 0  # Ulcer index is always non-negative

    def test_negative_returns_high_ulcer(self, negative_returns):
        neg_ui = ulcer_index(negative_returns)
        pos_ui = ulcer_index(pd.Series(np.random.uniform(0.001, 0.02, 252)))
        assert neg_ui > pos_ui  # Negative returns → more drawdown pain

    def test_empty_returns(self, empty_returns):
        assert ulcer_index(empty_returns) == 0.0


class TestComputeAllRiskMetrics:
    def test_returns_all_keys(self, mixed_returns):
        metrics = compute_all_risk_metrics(mixed_returns)
        expected_keys = {
            "calmar_ratio", "var_95", "var_99",
            "cvar_95", "cvar_99", "omega_ratio",
            "profit_factor", "information_ratio", "ulcer_index",
        }
        assert set(metrics.keys()) == expected_keys

    def test_all_values_are_float(self, mixed_returns):
        metrics = compute_all_risk_metrics(mixed_returns)
        for key, value in metrics.items():
            assert isinstance(value, float), f"{key} is not float: {type(value)}"
