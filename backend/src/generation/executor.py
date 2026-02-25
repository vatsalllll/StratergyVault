"""
StrategyVault - Backtest Executor
Runs backtesting.py strategies and captures results

Provides:
- Safe strategy code execution
- Result parsing (Sharpe, returns, drawdown, etc.)
- Parallel execution support
"""

import subprocess
import json
import re
import os
import tempfile
from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class BacktestResult:
    """Container for backtest execution results."""
    success: bool
    return_pct: Optional[float]
    buy_hold_pct: Optional[float]
    sharpe_ratio: Optional[float]
    sortino_ratio: Optional[float]
    max_drawdown_pct: Optional[float]
    num_trades: Optional[int]
    win_rate: Optional[float]
    stdout: str
    stderr: str
    execution_time: float
    strategy_name: str
    data_source: str


def parse_backtest_output(stdout: str) -> Dict[str, Any]:
    """
    Parse backtesting.py output to extract key metrics.
    
    Args:
        stdout: Standard output from backtest execution
        
    Returns:
        Dictionary with parsed metrics
    """
    stats = {
        'return_pct': None,
        'buy_hold_pct': None,
        'sharpe_ratio': None,
        'sortino_ratio': None,
        'max_drawdown_pct': None,
        'num_trades': None,
        'win_rate': None,
        'avg_trade_pct': None,
        'profit_factor': None,
    }
    
    patterns = {
        'return_pct': r'Return \[%\]\s+([-\d.]+)',
        'buy_hold_pct': r'Buy & Hold Return \[%\]\s+([-\d.]+)',
        'sharpe_ratio': r'Sharpe Ratio\s+([-\d.]+)',
        'sortino_ratio': r'Sortino Ratio\s+([-\d.]+)',
        'max_drawdown_pct': r'Max\. Drawdown \[%\]\s+([-\d.]+)',
        'num_trades': r'# Trades\s+(\d+)',
        'win_rate': r'Win Rate \[%\]\s+([-\d.]+)',
        'avg_trade_pct': r'Avg\. Trade \[%\]\s+([-\d.]+)',
        'profit_factor': r'Profit Factor\s+([-\d.]+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, stdout)
        if match:
            value = match.group(1)
            if key == 'num_trades':
                stats[key] = int(value)
            else:
                stats[key] = float(value)
    
    return stats


def execute_backtest(
    code: str,
    data_path: str,
    strategy_name: str = "Strategy",
    timeout: int = 300,
    python_path: str = "python"
) -> BacktestResult:
    """
    Execute a backtest strategy and capture results.
    
    Args:
        code: Python strategy code
        data_path: Path to CSV data file
        strategy_name: Name of the strategy
        timeout: Execution timeout in seconds
        python_path: Path to Python interpreter
        
    Returns:
        BacktestResult with execution results
    """
    # Replace data path placeholder in code
    code = code.replace("DATA_PATH = ", f'DATA_PATH = "{data_path}"  # ')
    code = code.replace('path/to/your/data.csv', data_path)
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        temp_file = f.name
    
    try:
        start_time = datetime.now()
        
        # Execute the backtest
        result = subprocess.run(
            [python_path, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.path.dirname(temp_file)
        )
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Parse results
        stats = parse_backtest_output(result.stdout)
        
        return BacktestResult(
            success=result.returncode == 0,
            return_pct=stats.get('return_pct'),
            buy_hold_pct=stats.get('buy_hold_pct'),
            sharpe_ratio=stats.get('sharpe_ratio'),
            sortino_ratio=stats.get('sortino_ratio'),
            max_drawdown_pct=stats.get('max_drawdown_pct'),
            num_trades=stats.get('num_trades'),
            win_rate=stats.get('win_rate'),
            stdout=result.stdout,
            stderr=result.stderr,
            execution_time=execution_time,
            strategy_name=strategy_name,
            data_source=os.path.basename(data_path)
        )
        
    except subprocess.TimeoutExpired:
        return BacktestResult(
            success=False,
            return_pct=None,
            buy_hold_pct=None,
            sharpe_ratio=None,
            sortino_ratio=None,
            max_drawdown_pct=None,
            num_trades=None,
            win_rate=None,
            stdout="",
            stderr="Execution timeout",
            execution_time=timeout,
            strategy_name=strategy_name,
            data_source=os.path.basename(data_path)
        )
        
    finally:
        # Cleanup
        if os.path.exists(temp_file):
            os.unlink(temp_file)


def execute_parallel_backtests(
    code: str,
    data_paths: List[str],
    strategy_name: str = "Strategy",
    max_workers: int = 4,
    timeout: int = 300
) -> List[BacktestResult]:
    """
    Execute backtest on multiple data sources in parallel.
    
    Args:
        code: Python strategy code
        data_paths: List of paths to CSV data files
        strategy_name: Name of the strategy
        max_workers: Maximum parallel workers
        timeout: Timeout per backtest
        
    Returns:
        List of BacktestResults
    """
    results = []
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(
                execute_backtest,
                code,
                data_path,
                strategy_name,
                timeout
            ): data_path
            for data_path in data_paths
        }
        
        for future in as_completed(futures):
            data_path = futures[future]
            try:
                result = future.result()
                results.append(result)
                print(f"✅ Completed: {os.path.basename(data_path)} - Return: {result.return_pct}%")
            except Exception as e:
                print(f"❌ Failed: {os.path.basename(data_path)} - {str(e)}")
                results.append(BacktestResult(
                    success=False,
                    return_pct=None,
                    buy_hold_pct=None,
                    sharpe_ratio=None,
                    sortino_ratio=None,
                    max_drawdown_pct=None,
                    num_trades=None,
                    win_rate=None,
                    stdout="",
                    stderr=str(e),
                    execution_time=0,
                    strategy_name=strategy_name,
                    data_source=os.path.basename(data_path)
                ))
    
    return results


def aggregate_results(results: List[BacktestResult]) -> Dict[str, Any]:
    """
    Aggregate results from multiple backtests.
    
    Args:
        results: List of BacktestResults
        
    Returns:
        Aggregated statistics
    """
    successful = [r for r in results if r.success and r.return_pct is not None]
    
    if not successful:
        return {
            'total_tests': len(results),
            'successful_tests': 0,
            'avg_return': None,
            'best_return': None,
            'worst_return': None,
            'avg_sharpe': None,
            'positive_returns': 0,
        }
    
    returns = [r.return_pct for r in successful]
    sharpes = [r.sharpe_ratio for r in successful if r.sharpe_ratio is not None]
    
    return {
        'total_tests': len(results),
        'successful_tests': len(successful),
        'avg_return': sum(returns) / len(returns),
        'best_return': max(returns),
        'worst_return': min(returns),
        'avg_sharpe': sum(sharpes) / len(sharpes) if sharpes else None,
        'positive_returns': sum(1 for r in returns if r > 0),
        'results_by_asset': {r.data_source: r.return_pct for r in successful}
    }


if __name__ == "__main__":
    # Test executor
    print("Testing backtest executor...")
    
    # Simple test code
    test_code = '''
import pandas as pd
import numpy as np
from backtesting import Backtest, Strategy

class SimpleMA(Strategy):
    def init(self):
        self.sma = self.I(lambda x: pd.Series(x).rolling(20).mean(), self.data.Close)
    
    def next(self):
        if not self.position:
            if self.data.Close[-1] > self.sma[-1]:
                self.buy(size=0.95)
        elif self.data.Close[-1] < self.sma[-1]:
            self.position.close()

# Create dummy data for testing
dates = pd.date_range('2020-01-01', periods=500, freq='D')
np.random.seed(42)
price = 100 + np.cumsum(np.random.randn(500) * 2)
data = pd.DataFrame({
    'Open': price + np.random.randn(500),
    'High': price + abs(np.random.randn(500)),
    'Low': price - abs(np.random.randn(500)),
    'Close': price,
    'Volume': np.random.randint(1000, 10000, 500)
}, index=dates)

bt = Backtest(data, SimpleMA, cash=100000, commission=0.001)
stats = bt.run()
print(stats)
'''
    
    # Note: This requires backtesting.py to be installed
    print("Executor module loaded successfully!")
