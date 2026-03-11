"""
Tests for StrategyVault - Executor Code Sanitization
Tests that dangerous code patterns are blocked before execution.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.generation.executor import sanitize_code, execute_backtest


class TestSanitizeCode:
    """Test the code sanitization function."""

    def test_safe_strategy_code_passes(self):
        """Normal backtesting code should pass sanitization."""
        safe_code = '''
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy

class MyStrategy(Strategy):
    def init(self):
        self.sma = self.I(lambda x: pd.Series(x).rolling(20).mean(), self.data.Close)
    
    def next(self):
        if self.data.Close[-1] > self.sma[-1]:
            self.buy(size=0.95)
'''
        is_safe, msg = sanitize_code(safe_code)
        assert is_safe is True
        assert msg == ""

    def test_blocks_os_system(self):
        """os.system() calls must be blocked."""
        code = 'os.system("rm -rf /")'
        is_safe, msg = sanitize_code(code)
        assert is_safe is False
        assert "os.system" in msg

    def test_blocks_subprocess(self):
        """subprocess module must be blocked."""
        code = 'import subprocess\nsubprocess.run(["ls"])'
        is_safe, msg = sanitize_code(code)
        assert is_safe is False
        assert "subprocess" in msg

    def test_blocks_eval(self):
        """eval() calls must be blocked."""
        code = 'result = eval("__import__(\'os\').system(\'whoami\')")'
        is_safe, msg = sanitize_code(code)
        assert is_safe is False
        assert "eval" in msg

    def test_blocks_exec(self):
        """exec() calls must be blocked."""
        code = 'exec("print(42)")'
        is_safe, msg = sanitize_code(code)
        assert is_safe is False
        assert "exec" in msg

    def test_blocks_network_imports(self):
        """Network-related imports must be blocked."""
        for module in ["requests", "urllib", "httpx", "aiohttp", "socket"]:
            code = f"import {module}"
            is_safe, msg = sanitize_code(code)
            assert is_safe is False, f"{module} should be blocked"

    def test_blocks_file_deletion(self):
        """File deletion operations must be blocked."""
        dangerous_ops = [
            'os.remove("/etc/passwd")',
            'os.unlink("data.csv")',
            'import shutil',
            'os.rmdir("/tmp")',
        ]
        for code in dangerous_ops:
            is_safe, msg = sanitize_code(code)
            assert is_safe is False, f"Should block: {code}"

    def test_blocks_pickle(self):
        """Pickle (arbitrary code execution via deserialization) must be blocked."""
        code = "import pickle\npickle.loads(data)"
        is_safe, msg = sanitize_code(code)
        assert is_safe is False
        assert "pickle" in msg

    def test_blocks_dunder_import(self):
        """__import__() must be blocked."""
        code = '__import__("os").system("ls")'
        is_safe, msg = sanitize_code(code)
        assert is_safe is False
        assert "__import__" in msg

    def test_blocks_globals(self):
        """globals() call must be blocked."""
        code = 'g = globals()\ng["__builtins__"]["__import__"]("os")'
        is_safe, msg = sanitize_code(code)
        assert is_safe is False

    def test_blocks_setattr(self):
        """setattr() calls must be blocked."""
        code = 'setattr(obj, "dangerous", value)'
        is_safe, msg = sanitize_code(code)
        assert is_safe is False


class TestExecuteBacktestSanitization:
    """Test that execute_backtest rejects dangerous code."""

    def test_dangerous_code_returns_failed_result(self):
        """Backtest with dangerous code should return failed result."""
        dangerous_code = '''
import os
os.system("whoami")
'''
        result = execute_backtest(
            code=dangerous_code,
            data_path="/tmp/test.csv",
            strategy_name="DangerousStrat",
            timeout=10,
        )
        assert result.success is False
        assert "sanitization" in result.stderr.lower()
        assert result.return_pct is None

    def test_safe_code_not_blocked(self):
        """Safe backtest code should not be blocked by sanitizer."""
        safe_code = '''
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy

class SimpleMA(Strategy):
    def init(self):
        self.sma = self.I(lambda x: pd.Series(x).rolling(20).mean(), self.data.Close)
    def next(self):
        pass

data = pd.DataFrame({
    'Open': [1,2,3], 'High': [2,3,4], 'Low': [0,1,2],
    'Close': [1.5, 2.5, 3.5], 'Volume': [100, 200, 300]
})
'''
        is_safe, msg = sanitize_code(safe_code)
        assert is_safe is True
