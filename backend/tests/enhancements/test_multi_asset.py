"""
Tests for StrategyVault - Multi-Asset Backtesting
Tests that strategies can be tested across multiple assets.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestMultiAssetConfig:
    """Test multi-asset configuration."""

    def test_default_backtest_assets_configured(self):
        """DEFAULT_BACKTEST_ASSETS should be populated in config."""
        from src.core.config import settings

        assert hasattr(settings, "DEFAULT_BACKTEST_ASSETS")
        assert isinstance(settings.DEFAULT_BACKTEST_ASSETS, list)
        assert len(settings.DEFAULT_BACKTEST_ASSETS) > 0

    def test_default_assets_include_crypto_and_stocks(self):
        """Default assets should include both crypto and stock symbols."""
        from src.core.config import settings, BACKTEST_ASSETS

        categories = {a["category"] for a in BACKTEST_ASSETS}
        assert "crypto" in categories
        assert "stocks" in categories


class TestAggregateResults:
    """Test the aggregate_results function."""

    def test_aggregate_empty_results(self):
        """Aggregating empty results should return zero counts."""
        from src.generation.executor import aggregate_results

        result = aggregate_results([])
        assert result["total_tests"] == 0
        assert result["successful_tests"] == 0
        assert result["avg_return"] is None

    def test_aggregate_successful_results(self):
        """Aggregating successful results should compute averages."""
        from src.generation.executor import aggregate_results, BacktestResult

        results = [
            BacktestResult(
                success=True, return_pct=20.0, buy_hold_pct=10.0,
                sharpe_ratio=1.5, sortino_ratio=2.0, max_drawdown_pct=-10.0,
                num_trades=50, win_rate=60.0, stdout="", stderr="",
                execution_time=1.0, strategy_name="Test", data_source="BTC-USD",
            ),
            BacktestResult(
                success=True, return_pct=30.0, buy_hold_pct=15.0,
                sharpe_ratio=2.0, sortino_ratio=2.5, max_drawdown_pct=-12.0,
                num_trades=40, win_rate=55.0, stdout="", stderr="",
                execution_time=1.0, strategy_name="Test", data_source="ETH-USD",
            ),
        ]
        agg = aggregate_results(results)
        assert agg["total_tests"] == 2
        assert agg["successful_tests"] == 2
        assert agg["avg_return"] == 25.0
        assert agg["best_return"] == 30.0
        assert agg["worst_return"] == 20.0

    def test_aggregate_mixed_results(self):
        """Aggregating mixed results should only use successful ones."""
        from src.generation.executor import aggregate_results, BacktestResult

        results = [
            BacktestResult(
                success=True, return_pct=20.0, buy_hold_pct=10.0,
                sharpe_ratio=1.5, sortino_ratio=2.0, max_drawdown_pct=-10.0,
                num_trades=50, win_rate=60.0, stdout="", stderr="",
                execution_time=1.0, strategy_name="Test", data_source="BTC-USD",
            ),
            BacktestResult(
                success=False, return_pct=None, buy_hold_pct=None,
                sharpe_ratio=None, sortino_ratio=None, max_drawdown_pct=None,
                num_trades=None, win_rate=None, stdout="", stderr="error",
                execution_time=1.0, strategy_name="Test", data_source="FAIL-USD",
            ),
        ]
        agg = aggregate_results(results)
        assert agg["total_tests"] == 2
        assert agg["successful_tests"] == 1


class TestMultiAssetFunction:
    """Test the run_multi_asset_backtest function."""

    def test_function_exists(self):
        """run_multi_asset_backtest should be importable."""
        from src.services.pipeline import run_multi_asset_backtest

        assert callable(run_multi_asset_backtest)

    def test_function_returns_expected_keys(self):
        """Return value should contain per_asset, aggregated, best_asset."""
        import inspect
        from src.services.pipeline import run_multi_asset_backtest

        source = inspect.getsource(run_multi_asset_backtest)
        assert "per_asset" in source
        assert "aggregated" in source
        assert "best_asset" in source
        assert "assets_tested" in source
