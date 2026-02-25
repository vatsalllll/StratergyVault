"""
Tests for StrategyVault - Strategy Generation (Templates & Code Extraction)
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.generation.generator import (
    GeneratedStrategy,
    AIModel,
    generate_backtest_template,
    StrategyGenerator,
)
from src.generation.executor import (
    parse_backtest_output,
    aggregate_results,
    BacktestResult,
)


class TestBacktestTemplate:
    """Test template generation (no API keys required)."""

    def test_template_has_strategy_class(self):
        code = generate_backtest_template("MomentumAlpha")
        assert "class MomentumAlpha(Strategy):" in code

    def test_template_has_imports(self):
        code = generate_backtest_template("TestStrat")
        assert "import pandas" in code
        assert "from backtesting import" in code

    def test_template_has_init_and_next(self):
        code = generate_backtest_template("TestStrat")
        assert "def init(self):" in code
        assert "def next(self):" in code

    def test_template_has_data_loading(self):
        code = generate_backtest_template("TestStrat")
        assert "def load_data" in code

    def test_template_uses_self_I(self):
        code = generate_backtest_template("TestStrat")
        assert "self.I(" in code

    def test_template_different_names(self):
        code1 = generate_backtest_template("AlphaOne")
        code2 = generate_backtest_template("BetaTwo")
        assert "AlphaOne" in code1
        assert "BetaTwo" in code2
        assert "AlphaOne" not in code2


class TestCodeExtraction:
    """Test code extraction from AI responses (no API keys required)."""

    def test_extract_from_python_block(self):
        gen = StrategyGenerator.__new__(StrategyGenerator)
        text = '''Here is the code:
```python
import pandas as pd
print("hello")
```
Done!'''
        code = gen._extract_code(text)
        assert 'import pandas' in code
        assert 'print("hello")' in code

    def test_extract_from_generic_block(self):
        gen = StrategyGenerator.__new__(StrategyGenerator)
        text = '''```
import numpy as np
x = 1
```'''
        code = gen._extract_code(text)
        assert 'import numpy' in code

    def test_extract_when_no_blocks(self):
        gen = StrategyGenerator.__new__(StrategyGenerator)
        text = '''STRATEGY_NAME: TestStrat
import pandas as pd
from backtesting import Strategy
class X(Strategy):
    pass
'''
        code = gen._extract_code(text)
        assert 'import pandas' in code
        assert 'STRATEGY_NAME' not in code


class TestBacktestOutputParsing:
    """Test parsing of backtesting.py output."""

    def test_parse_full_output(self):
        stdout = """
Start                     2020-01-01 00:00:00
End                       2023-12-31 00:00:00
Duration                  1460 days 00:00:00
Exposure Time [%]                     78.5
Equity Final [$]                  135000.0
Equity Peak [$]                   142000.0
Return [%]                            35.0
Buy & Hold Return [%]                 50.2
Return (Ann.) [%]                     12.5
Volatility (Ann.) [%]                 18.3
Sharpe Ratio                           1.45
Sortino Ratio                          2.10
Calmar Ratio                           0.85
Max. Drawdown [%]                    -14.7
Avg. Drawdown [%]                     -3.2
# Trades                               42
Win Rate [%]                          58.3
Best Trade [%]                         8.2
Worst Trade [%]                       -4.1
Avg. Trade [%]                         0.83
Profit Factor                          1.85
        """
        stats = parse_backtest_output(stdout)
        assert stats['return_pct'] == 35.0
        assert stats['buy_hold_pct'] == 50.2
        assert stats['sharpe_ratio'] == 1.45
        assert stats['sortino_ratio'] == 2.10
        assert stats['max_drawdown_pct'] == -14.7
        assert stats['num_trades'] == 42
        assert stats['win_rate'] == 58.3

    def test_parse_empty_output(self):
        stats = parse_backtest_output("")
        assert stats['return_pct'] is None
        assert stats['sharpe_ratio'] is None

    def test_parse_partial_output(self):
        stdout = "Return [%]    25.0\n# Trades    10\n"
        stats = parse_backtest_output(stdout)
        assert stats['return_pct'] == 25.0
        assert stats['num_trades'] == 10
        assert stats['sharpe_ratio'] is None


class TestAggregateResults:
    """Test result aggregation from parallel backtests."""

    def test_aggregate_empty(self):
        result = aggregate_results([])
        assert result['total_tests'] == 0
        assert result['avg_return'] is None

    def test_aggregate_successful(self):
        results = [
            BacktestResult(True, 20.0, 15.0, 1.5, 2.0, -10.0, 30, 60.0, "", "", 5.0, "S1", "BTC"),
            BacktestResult(True, 30.0, 25.0, 1.8, 2.5, -8.0, 25, 65.0, "", "", 4.0, "S1", "ETH"),
        ]
        agg = aggregate_results(results)
        assert agg['total_tests'] == 2
        assert agg['successful_tests'] == 2
        assert agg['avg_return'] == 25.0
        assert agg['best_return'] == 30.0
        assert agg['worst_return'] == 20.0
        assert agg['positive_returns'] == 2

    def test_aggregate_mixed(self):
        results = [
            BacktestResult(True, 20.0, None, None, None, None, None, None, "", "", 5.0, "S1", "BTC"),
            BacktestResult(False, None, None, None, None, None, None, None, "", "Error", 1.0, "S1", "SPY"),
        ]
        agg = aggregate_results(results)
        assert agg['total_tests'] == 2
        assert agg['successful_tests'] == 1
        assert agg['avg_return'] == 20.0


class TestAIModelEnum:
    """Test AI model enum."""

    def test_model_values(self):
        assert AIModel.GEMINI_FLASH.value == "gemini-2.5-flash"
        assert AIModel.GPT4.value == "gpt-4o"
        assert AIModel.DEEPSEEK.value == "deepseek-chat"
