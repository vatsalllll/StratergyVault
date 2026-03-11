"""
Tests for StrategyVault - RBI Debug Loop
Tests package_check, debug_strategy, and iterative debug cycle.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestPackageCheck:
    """Test the package_check method from Moon Dev RBI Agent."""

    def test_removes_backtesting_lib_import(self):
        """package_check should remove backtesting.lib imports."""
        from src.generation.generator import StrategyGenerator, AIModel

        generator = StrategyGenerator(AIModel.GEMINI_FLASH)

        code = """from backtesting.lib import crossover
from backtesting import Backtest, Strategy

class MyStrat(Strategy):
    def init(self):
        pass
    def next(self):
        if crossover(self.data.Close, self.sma):
            self.buy()
"""
        fixed = generator.package_check(code)
        assert "from backtesting.lib" not in fixed
        # crossover function should still work (helper added)
        assert "def crossover" in fixed

    def test_keeps_valid_imports(self):
        """package_check should not touch valid imports."""
        from src.generation.generator import StrategyGenerator, AIModel

        generator = StrategyGenerator(AIModel.GEMINI_FLASH)

        code = """import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy
"""
        fixed = generator.package_check(code)
        assert "import pandas as pd" in fixed
        assert "import numpy as np" in fixed
        assert "from backtesting import Backtest, Strategy" in fixed

    def test_no_change_when_clean(self):
        """Clean code should pass through unchanged (except whitespace)."""
        from src.generation.generator import StrategyGenerator, AIModel

        generator = StrategyGenerator(AIModel.GEMINI_FLASH)

        code = """import pandas as pd
from backtesting import Backtest, Strategy

class Simple(Strategy):
    def init(self):
        pass
    def next(self):
        pass
"""
        fixed = generator.package_check(code)
        # Should be essentially the same
        assert "class Simple(Strategy):" in fixed


class TestDebugLoop:
    """Test debug loop configuration."""

    def test_max_debug_iterations_configured(self):
        """MAX_DEBUG_ITERATIONS should be set in config."""
        from src.core.config import settings

        assert hasattr(settings, "MAX_DEBUG_ITERATIONS")
        assert settings.MAX_DEBUG_ITERATIONS > 0
        assert settings.MAX_DEBUG_ITERATIONS <= 20  # Reasonable upper bound

    def test_debug_strategy_method_exists(self):
        """StrategyGenerator should have debug_strategy method."""
        from src.generation.generator import StrategyGenerator, AIModel

        generator = StrategyGenerator(AIModel.GEMINI_FLASH)
        assert hasattr(generator, "debug_strategy")
        assert callable(generator.debug_strategy)

    def test_optimize_strategy_method_exists(self):
        """StrategyGenerator should have optimize_strategy method."""
        from src.generation.generator import StrategyGenerator, AIModel

        generator = StrategyGenerator(AIModel.GEMINI_FLASH)
        assert hasattr(generator, "optimize_strategy")
        assert callable(generator.optimize_strategy)

    def test_pipeline_has_debug_loop(self):
        """Pipeline should reference debug iterations, not single-shot backtest."""
        import inspect
        from src.services.pipeline import run_pipeline

        source = inspect.getsource(run_pipeline)
        assert "debug_iteration" in source or "max_debug_attempts" in source
        assert "package_check" in source
