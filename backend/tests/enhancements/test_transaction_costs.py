"""
Tests for StrategyVault - Transaction Cost Modeling
Tests that commission and slippage are properly injected into backtest code.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.generation.executor import inject_transaction_costs


class TestTransactionCostConfig:
    """Test transaction cost configuration."""

    def test_commission_configured(self):
        from src.core.config import settings
        assert hasattr(settings, "BACKTEST_COMMISSION")
        assert settings.BACKTEST_COMMISSION > 0

    def test_slippage_configured(self):
        from src.core.config import settings
        assert hasattr(settings, "BACKTEST_SLIPPAGE")
        assert settings.BACKTEST_SLIPPAGE >= 0

    def test_total_cost_reasonable(self):
        """Total cost (commission + slippage) should be reasonable."""
        from src.core.config import settings
        total = settings.BACKTEST_COMMISSION + settings.BACKTEST_SLIPPAGE
        assert 0 < total < 0.05  # Less than 5% total cost


class TestInjectTransactionCosts:
    """Test the inject_transaction_costs function."""

    def test_replaces_commission_value(self):
        """Should replace commission=0.001 with config value."""
        code = 'bt = Backtest(data, Strategy, cash=100000, commission=0.001)'
        result = inject_transaction_costs(code)
        assert "commission=0.001" not in result or result != code
        # The value should be the sum from config
        from src.core.config import settings
        expected = settings.BACKTEST_COMMISSION + settings.BACKTEST_SLIPPAGE
        assert f"commission={expected}" in result

    def test_replaces_zero_commission(self):
        """Should replace commission=0 with config value."""
        code = 'bt = Backtest(data, Strategy, cash=100000, commission=0)'
        result = inject_transaction_costs(code)
        from src.core.config import settings
        expected = settings.BACKTEST_COMMISSION + settings.BACKTEST_SLIPPAGE
        assert f"commission={expected}" in result

    def test_handles_spaces_around_equals(self):
        """Should handle commission = 0.001 with spaces."""
        code = 'bt = Backtest(data, Strategy, cash=100000, commission = 0.002)'
        result = inject_transaction_costs(code)
        from src.core.config import settings
        expected = settings.BACKTEST_COMMISSION + settings.BACKTEST_SLIPPAGE
        assert f"commission={expected}" in result

    def test_preserves_rest_of_code(self):
        """Non-commission code should be preserved."""
        code = '''import pandas as pd
from backtesting import Backtest, Strategy

class MyStrat(Strategy):
    def init(self):
        pass

bt = Backtest(data, MyStrat, cash=100000, commission=0.001)
stats = bt.run()
print(stats)
'''
        result = inject_transaction_costs(code)
        assert "import pandas as pd" in result
        assert "class MyStrat(Strategy):" in result
        assert "stats = bt.run()" in result

    def test_no_commission_unchanged(self):
        """Code without commission= should pass through unchanged."""
        code = 'bt = Backtest(data, Strategy, cash=100000)'
        result = inject_transaction_costs(code)
        assert result == code
