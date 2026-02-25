"""
Tests for StrategyVault - Walk-Forward Validation & Ablation
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.validation.walk_forward import (
    create_walk_forward_windows,
    calculate_performance_metrics,
    run_walk_forward_validation,
    detect_overfitting,
    generate_validation_report,
)
from src.validation.ablation import (
    calculate_component_contribution,
    run_ablation_study,
    generate_ablation_report,
)


# ─── Walk-Forward Tests ──────────────────────────────────────────

class TestCreateWindows:
    """Test walk-forward window generation."""

    def test_creates_windows(self):
        dates = pd.date_range('2020-01-01', periods=800, freq='D')
        df = pd.DataFrame(index=dates)
        windows = create_walk_forward_windows(df, train_months=6, test_months=3)
        assert len(windows) > 0

    def test_windows_non_overlapping_test(self):
        dates = pd.date_range('2020-01-01', periods=800, freq='D')
        df = pd.DataFrame(index=dates)
        windows = create_walk_forward_windows(df, train_months=6, test_months=3, step_months=3)
        for w in windows:
            assert w.test_start >= w.train_end
            assert w.test_end > w.test_start

    def test_windows_are_sequential(self):
        dates = pd.date_range('2020-01-01', periods=800, freq='D')
        df = pd.DataFrame(index=dates)
        windows = create_walk_forward_windows(df, train_months=6, test_months=3, step_months=3)
        for i in range(1, len(windows)):
            assert windows[i].train_start >= windows[i - 1].train_start

    def test_short_data_no_windows(self):
        dates = pd.date_range('2020-01-01', periods=30, freq='D')
        df = pd.DataFrame(index=dates)
        windows = create_walk_forward_windows(df, train_months=6, test_months=3)
        assert len(windows) == 0


class TestPerformanceMetrics:
    """Test performance metric calculations."""

    def test_positive_returns(self, sample_returns):
        metrics = calculate_performance_metrics(sample_returns)
        assert 'sharpe_ratio' in metrics
        assert 'total_return' in metrics
        assert 'max_drawdown' in metrics
        assert 'volatility' in metrics

    def test_zero_std_returns_zero_sharpe(self):
        flat = pd.Series([0.0] * 100)
        metrics = calculate_performance_metrics(flat)
        assert metrics['sharpe_ratio'] == 0.0

    def test_empty_returns(self):
        empty = pd.Series([], dtype=float)
        metrics = calculate_performance_metrics(empty)
        assert metrics['sharpe_ratio'] == 0.0
        assert metrics['total_return'] == 0.0

    def test_max_drawdown_negative(self, sample_returns):
        metrics = calculate_performance_metrics(sample_returns)
        assert metrics['max_drawdown'] <= 0  # Drawdown is negative or zero

    def test_volatility_positive(self, sample_returns):
        metrics = calculate_performance_metrics(sample_returns)
        assert metrics['volatility'] > 0


class TestWalkForwardValidation:
    """Test walk-forward validation logic."""

    def test_robust_strategy(self):
        """Strategy with similar in/out-of-sample performance is robust."""
        dates = pd.date_range('2020-01-01', periods=800, freq='D')
        df = pd.DataFrame(index=dates)
        windows = create_walk_forward_windows(df, train_months=6, test_months=3)

        n = len(windows)
        train_results = [{'sharpe_ratio': 1.5, 'total_return': 15.0}] * n
        test_results = [{'sharpe_ratio': 1.3, 'total_return': 12.0}] * n

        result = run_walk_forward_validation(windows, train_results, test_results)
        assert result.is_robust
        assert result.robustness_score > 0.5

    def test_overfit_strategy(self):
        """Strategy with huge in-sample vs out-of-sample gap is not robust."""
        dates = pd.date_range('2020-01-01', periods=800, freq='D')
        df = pd.DataFrame(index=dates)
        windows = create_walk_forward_windows(df, train_months=6, test_months=3)

        n = len(windows)
        train_results = [{'sharpe_ratio': 3.0, 'total_return': 50.0}] * n
        test_results = [{'sharpe_ratio': -0.5, 'total_return': -10.0}] * n

        result = run_walk_forward_validation(windows, train_results, test_results)
        assert not result.is_robust
        assert result.sharpe_degradation > 0.5

    def test_degradation_calculation(self):
        dates = pd.date_range('2020-01-01', periods=800, freq='D')
        df = pd.DataFrame(index=dates)
        windows = create_walk_forward_windows(df, train_months=6, test_months=3)

        n = len(windows)
        train_results = [{'sharpe_ratio': 2.0, 'total_return': 20.0}] * n
        test_results = [{'sharpe_ratio': 1.0, 'total_return': 10.0}] * n

        result = run_walk_forward_validation(windows, train_results, test_results)
        assert abs(result.sharpe_degradation - 0.5) < 0.01
        assert abs(result.return_degradation - 0.5) < 0.01


class TestOverfittingDetection:
    """Test overfitting heuristic."""

    def test_overfitting_detected(self):
        is_overfit, msg = detect_overfitting(in_sample_sharpe=3.0, out_of_sample_sharpe=0.5)
        assert is_overfit is True
        assert "overfit" in msg.lower()

    def test_robust_not_overfit(self):
        is_overfit, msg = detect_overfitting(in_sample_sharpe=1.5, out_of_sample_sharpe=1.3)
        assert is_overfit is False

    def test_negative_in_sample(self):
        is_overfit, msg = detect_overfitting(in_sample_sharpe=-0.5, out_of_sample_sharpe=-1.0)
        assert is_overfit is False


class TestValidationReport:
    """Test report generation."""

    def test_report_is_string(self):
        dates = pd.date_range('2020-01-01', periods=800, freq='D')
        df = pd.DataFrame(index=dates)
        windows = create_walk_forward_windows(df, train_months=6, test_months=3)

        n = len(windows)
        train_results = [{'sharpe_ratio': 1.5, 'total_return': 15.0}] * n
        test_results = [{'sharpe_ratio': 1.3, 'total_return': 12.0}] * n

        result = run_walk_forward_validation(windows, train_results, test_results)
        report = generate_validation_report(result)
        assert isinstance(report, str)
        assert "WALK-FORWARD" in report
        assert "Robustness Score" in report


# ─── Ablation Tests ──────────────────────────────────────────────

class TestAblation:
    """Test ablation study for component importance."""

    def test_contribution_calculation(self):
        # If baseline is 25% and ablated is 15%, the component contributes
        contribution = calculate_component_contribution(25.0, 15.0)
        assert contribution == 40.0  # (25-15)/25 * 100

    def test_contribution_zero_baseline(self):
        contribution = calculate_component_contribution(0.0, 5.0)
        assert contribution == 0.0

    def test_ablation_study(self):
        baseline = 25.0
        ablated = {
            "RSI Filter": 18.0,
            "Momentum": 12.0,
            "Volume Filter": 22.0,
            "Stop Loss": 15.0,
        }
        result = run_ablation_study(baseline, ablated)
        assert result.baseline_return == 25.0
        assert len(result.components) == 4
        # Most important = biggest contribution = Momentum (25-12=13 biggest gap)
        assert result.most_important == "Momentum"
        # Least important = smallest contribution = Volume Filter (25-22=3 smallest gap)
        assert result.least_important == "Volume Filter"

    def test_ablation_report_string(self):
        result = run_ablation_study(20.0, {"Component A": 10.0})
        report = generate_ablation_report(result)
        assert isinstance(report, str)
        assert "ABLATION" in report
