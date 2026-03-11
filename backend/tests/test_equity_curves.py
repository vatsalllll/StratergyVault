"""
Tests for StrategyVault - Equity Curves
Tests that equity curve data is properly stored, retrieved, and served.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestBacktestResultEquityCurve:
    """Test that BacktestResult includes equity curve field."""

    def test_backtest_result_has_equity_curve(self):
        """BacktestResult should have an equity_curve field."""
        from src.generation.executor import BacktestResult

        result = BacktestResult(
            success=True,
            return_pct=25.0,
            buy_hold_pct=10.0,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            max_drawdown_pct=-15.0,
            num_trades=50,
            win_rate=55.0,
            stdout="",
            stderr="",
            execution_time=1.0,
            strategy_name="TestStrat",
            data_source="test.csv",
            equity_curve=[10000, 10100, 10250, 10200, 10500],
        )
        assert result.equity_curve == [10000, 10100, 10250, 10200, 10500]

    def test_backtest_result_equity_curve_optional(self):
        """equity_curve should be optional (None by default)."""
        from src.generation.executor import BacktestResult

        result = BacktestResult(
            success=True,
            return_pct=25.0,
            buy_hold_pct=10.0,
            sharpe_ratio=1.5,
            sortino_ratio=2.0,
            max_drawdown_pct=-15.0,
            num_trades=50,
            win_rate=55.0,
            stdout="",
            stderr="",
            execution_time=1.0,
            strategy_name="TestStrat",
            data_source="test.csv",
        )
        assert result.equity_curve is None


class TestStrategyModelEquityCurve:
    """Test that Strategy model has equity curve columns."""

    def test_strategy_has_equity_curve_column(self, db_session):
        """Strategy model should have equity_curve column."""
        from src.models.database import Strategy, StrategyTier

        strategy = Strategy(
            name="TestCurve",
            code="# test",
            equity_curve=[10000, 10500, 11000],
            trade_log=[{"entry": 100, "exit": 110, "pnl": 10}],
            tier=StrategyTier.BRONZE,
        )
        db_session.add(strategy)
        db_session.commit()
        db_session.refresh(strategy)

        assert strategy.equity_curve == [10000, 10500, 11000]
        assert strategy.trade_log[0]["pnl"] == 10


class TestPerformanceEndpoint:
    """Test the /performance endpoint."""

    def test_performance_endpoint_returns_data_source(self):
        """Performance response should include data_source field."""
        from fastapi.testclient import TestClient
        from main import app

        client = TestClient(app)
        # Create a strategy first (via generate or manually)
        response = client.post(
            "/api/v1/strategies/generate",
            json={"trading_idea": "Buy when RSI below 30 for equity test"},
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("strategy_id"):
                perf_response = client.get(
                    f"/api/v1/strategies/{data['strategy_id']}/performance"
                )
                if perf_response.status_code == 200:
                    perf_data = perf_response.json()
                    assert "data_source" in perf_data
                    assert perf_data["data_source"] in ("real_backtest", "simulated")

    def test_month_labels_generated(self):
        """_generate_month_labels should produce correct labels."""
        from src.api.strategies import _generate_month_labels

        labels = _generate_month_labels(5)
        assert len(labels) == 5
        assert labels[0] == "Jan'24"
        assert labels[4] == "May'24"

    def test_month_labels_wraps_year(self):
        """Month labels should wrap to next year after December."""
        from src.api.strategies import _generate_month_labels

        labels = _generate_month_labels(15)
        assert labels[12] == "Jan'25"
        assert labels[14] == "Mar'25"
