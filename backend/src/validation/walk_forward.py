"""
StrategyVault - Walk-Forward Validation Module
Adapted from AgentQuant's validation methodology

Provides:
- Walk-forward analysis (rolling train/test windows)
- Out-of-sample performance testing
- Overfitting detection
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


@dataclass
class WalkForwardWindow:
    """A single train/test window for walk-forward analysis."""
    train_start: datetime
    train_end: datetime
    test_start: datetime
    test_end: datetime
    train_sharpe: Optional[float] = None
    test_sharpe: Optional[float] = None
    train_return: Optional[float] = None
    test_return: Optional[float] = None


@dataclass
class WalkForwardResult:
    """Results from walk-forward validation."""
    windows: List[WalkForwardWindow]
    avg_train_sharpe: float
    avg_test_sharpe: float
    avg_train_return: float
    avg_test_return: float
    sharpe_degradation: float
    return_degradation: float
    is_robust: bool
    robustness_score: float


def create_walk_forward_windows(
    data: pd.DataFrame,
    train_months: int = 6,
    test_months: int = 3,
    step_months: int = 3
) -> List[WalkForwardWindow]:
    """
    Create walk-forward validation windows.
    
    Args:
        data: DataFrame with datetime index
        train_months: Training window size in months
        test_months: Test window size in months
        step_months: Step size between windows in months
        
    Returns:
        List of WalkForwardWindow objects
    """
    windows = []
    
    start_date = data.index.min()
    end_date = data.index.max()
    
    current_train_start = start_date
    
    while True:
        train_end = current_train_start + relativedelta(months=train_months)
        test_start = train_end
        test_end = test_start + relativedelta(months=test_months)
        
        # Check if we have enough data for this window
        if test_end > end_date:
            break
        
        windows.append(WalkForwardWindow(
            train_start=current_train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end
        ))
        
        # Move to next window
        current_train_start = current_train_start + relativedelta(months=step_months)
    
    return windows


def calculate_performance_metrics(returns: pd.Series) -> Dict[str, float]:
    """
    Calculate key performance metrics from returns.
    
    Args:
        returns: Series of daily returns
        
    Returns:
        Dictionary with performance metrics
    """
    if len(returns) == 0 or returns.std() == 0:
        return {
            'sharpe_ratio': 0.0,
            'total_return': 0.0,
            'max_drawdown': 0.0,
            'volatility': 0.0,
        }
    
    # Annualized Sharpe (assuming daily returns, 252 trading days)
    sharpe = (returns.mean() / returns.std()) * np.sqrt(252)
    
    # Total return
    total_return = (1 + returns).prod() - 1
    
    # Max drawdown
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Annualized volatility
    volatility = returns.std() * np.sqrt(252)
    
    return {
        'sharpe_ratio': sharpe,
        'total_return': total_return * 100,  # as percentage
        'max_drawdown': max_drawdown * 100,  # as percentage
        'volatility': volatility * 100,
    }


def run_walk_forward_validation(
    windows: List[WalkForwardWindow],
    train_results: List[Dict[str, float]],
    test_results: List[Dict[str, float]],
    min_robustness_score: float = 0.5
) -> WalkForwardResult:
    """
    Run walk-forward validation and calculate robustness metrics.
    
    Args:
        windows: List of walk-forward windows
        train_results: Performance metrics for each training window
        test_results: Performance metrics for each test window
        min_robustness_score: Minimum score to be considered robust
        
    Returns:
        WalkForwardResult with validation metrics
    """
    # Update windows with results
    for i, window in enumerate(windows):
        if i < len(train_results):
            window.train_sharpe = train_results[i].get('sharpe_ratio')
            window.train_return = train_results[i].get('total_return')
        if i < len(test_results):
            window.test_sharpe = test_results[i].get('sharpe_ratio')
            window.test_return = test_results[i].get('total_return')
    
    # Calculate averages
    train_sharpes = [w.train_sharpe for w in windows if w.train_sharpe is not None]
    test_sharpes = [w.test_sharpe for w in windows if w.test_sharpe is not None]
    train_returns = [w.train_return for w in windows if w.train_return is not None]
    test_returns = [w.test_return for w in windows if w.test_return is not None]
    
    avg_train_sharpe = np.mean(train_sharpes) if train_sharpes else 0
    avg_test_sharpe = np.mean(test_sharpes) if test_sharpes else 0
    avg_train_return = np.mean(train_returns) if train_returns else 0
    avg_test_return = np.mean(test_returns) if test_returns else 0
    
    # Calculate degradation
    if avg_train_sharpe != 0:
        sharpe_degradation = (avg_train_sharpe - avg_test_sharpe) / abs(avg_train_sharpe)
    else:
        sharpe_degradation = 1.0
    
    if avg_train_return != 0:
        return_degradation = (avg_train_return - avg_test_return) / abs(avg_train_return)
    else:
        return_degradation = 1.0
    
    # Calculate robustness score (0-1, higher is better)
    # Penalize high degradation, reward consistent out-of-sample performance
    degradation_penalty = (abs(sharpe_degradation) + abs(return_degradation)) / 2
    consistency_bonus = min(avg_test_sharpe / 2, 0.5) if avg_test_sharpe > 0 else 0
    
    robustness_score = max(0, min(1, 1 - degradation_penalty + consistency_bonus))
    
    return WalkForwardResult(
        windows=windows,
        avg_train_sharpe=avg_train_sharpe,
        avg_test_sharpe=avg_test_sharpe,
        avg_train_return=avg_train_return,
        avg_test_return=avg_test_return,
        sharpe_degradation=sharpe_degradation,
        return_degradation=return_degradation,
        is_robust=robustness_score >= min_robustness_score,
        robustness_score=robustness_score
    )


def detect_overfitting(
    in_sample_sharpe: float,
    out_of_sample_sharpe: float,
    threshold: float = 0.5
) -> Tuple[bool, str]:
    """
    Detect if a strategy is likely overfit.
    
    Args:
        in_sample_sharpe: In-sample (training) Sharpe ratio
        out_of_sample_sharpe: Out-of-sample (test) Sharpe ratio
        threshold: Degradation threshold for overfitting detection
        
    Returns:
        Tuple of (is_overfit, explanation)
    """
    if in_sample_sharpe <= 0:
        return False, "In-sample Sharpe is not positive, cannot assess overfitting"
    
    degradation = (in_sample_sharpe - out_of_sample_sharpe) / in_sample_sharpe
    
    if degradation > threshold:
        return True, f"High degradation ({degradation:.1%}): Strategy likely overfit to historical data"
    elif degradation > threshold / 2:
        return False, f"Moderate degradation ({degradation:.1%}): Some overfitting possible, monitor carefully"
    else:
        return False, f"Low degradation ({degradation:.1%}): Strategy appears robust"


def generate_validation_report(result: WalkForwardResult) -> str:
    """
    Generate a human-readable validation report.
    
    Args:
        result: WalkForwardResult from validation
        
    Returns:
        Formatted report string
    """
    report = []
    report.append("=" * 60)
    report.append("WALK-FORWARD VALIDATION REPORT")
    report.append("=" * 60)
    
    report.append(f"\nNumber of Windows: {len(result.windows)}")
    report.append(f"\nIn-Sample Performance:")
    report.append(f"  Average Sharpe Ratio: {result.avg_train_sharpe:.2f}")
    report.append(f"  Average Return: {result.avg_train_return:.2f}%")
    
    report.append(f"\nOut-of-Sample Performance:")
    report.append(f"  Average Sharpe Ratio: {result.avg_test_sharpe:.2f}")
    report.append(f"  Average Return: {result.avg_test_return:.2f}%")
    
    report.append(f"\nDegradation Metrics:")
    report.append(f"  Sharpe Degradation: {result.sharpe_degradation:.1%}")
    report.append(f"  Return Degradation: {result.return_degradation:.1%}")
    
    report.append(f"\nRobustness Assessment:")
    report.append(f"  Robustness Score: {result.robustness_score:.2f}/1.00")
    report.append(f"  Status: {'✅ ROBUST' if result.is_robust else '⚠️ NOT ROBUST'}")
    
    # Window details
    report.append(f"\nWindow Details:")
    for i, window in enumerate(result.windows):
        report.append(f"\n  Window {i+1}:")
        report.append(f"    Train: {window.train_start.strftime('%Y-%m-%d')} to {window.train_end.strftime('%Y-%m-%d')}")
        report.append(f"    Test: {window.test_start.strftime('%Y-%m-%d')} to {window.test_end.strftime('%Y-%m-%d')}")
        if window.train_sharpe is not None:
            report.append(f"    Train Sharpe: {window.train_sharpe:.2f}, Test Sharpe: {window.test_sharpe:.2f}")
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)


if __name__ == "__main__":
    # Test walk-forward validation
    print("Testing walk-forward validation...")
    
    # Create sample data
    dates = pd.date_range('2020-01-01', periods=500, freq='D')
    sample_data = pd.DataFrame(index=dates)
    
    # Create windows
    windows = create_walk_forward_windows(sample_data, train_months=6, test_months=3)
    print(f"Created {len(windows)} walk-forward windows")
    
    for i, w in enumerate(windows[:3]):
        print(f"\nWindow {i+1}:")
        print(f"  Train: {w.train_start.date()} to {w.train_end.date()}")
        print(f"  Test: {w.test_start.date()} to {w.test_end.date()}")
