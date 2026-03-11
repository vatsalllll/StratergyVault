"""
StrategyVault - Advanced Risk Metrics
Provides quant-standard risk and performance metrics beyond basic Sharpe/Sortino.

Implements:
- Calmar Ratio
- Value at Risk (VaR) — parametric and historical
- Conditional VaR (CVaR / Expected Shortfall)
- Omega Ratio
- Profit Factor
- Information Ratio
- Ulcer Index
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional


def calmar_ratio(returns: pd.Series, periods_per_year: int = 252) -> float:
    """
    Calmar Ratio = Annualized Return / Max Drawdown.
    Higher is better (>3 is excellent).
    """
    if len(returns) == 0 or returns.std() == 0:
        return 0.0

    ann_return = (1 + returns.mean()) ** periods_per_year - 1
    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_dd = abs(drawdown.min())

    if max_dd == 0:
        return float("inf") if ann_return > 0 else 0.0

    return float(ann_return / max_dd)


def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Historical Value at Risk.
    Returns the loss threshold at the given confidence level.
    E.g., 95% VaR = 5th percentile of returns.
    Result is a negative number (representing loss).
    """
    if len(returns) == 0:
        return 0.0

    return float(np.percentile(returns, (1 - confidence) * 100))


def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Conditional Value at Risk (CVaR / Expected Shortfall).
    Average loss beyond the VaR threshold.
    More conservative than VaR — captures tail risk.
    """
    if len(returns) == 0:
        return 0.0

    var = value_at_risk(returns, confidence)
    tail_losses = returns[returns <= var]

    if len(tail_losses) == 0:
        return float(var)

    return float(tail_losses.mean())


def omega_ratio(returns: pd.Series, threshold: float = 0.0) -> float:
    """
    Omega Ratio = Probability-weighted gains / probability-weighted losses.
    An Omega > 1 means more upside than downside.
    """
    if len(returns) == 0:
        return 0.0

    gains = returns[returns > threshold] - threshold
    losses = threshold - returns[returns <= threshold]

    total_losses = losses.sum()
    if total_losses == 0:
        return float("inf") if gains.sum() > 0 else 0.0

    return float(gains.sum() / total_losses)


def profit_factor(returns: pd.Series) -> float:
    """
    Profit Factor = Sum of positive returns / |Sum of negative returns|.
    >1 means profitable. >2 is good. >3 is excellent.
    """
    if len(returns) == 0:
        return 0.0

    gross_profit = returns[returns > 0].sum()
    gross_loss = abs(returns[returns < 0].sum())

    if gross_loss == 0:
        return float("inf") if gross_profit > 0 else 0.0

    return float(gross_profit / gross_loss)


def information_ratio(
    returns: pd.Series,
    benchmark_returns: Optional[pd.Series] = None,
    periods_per_year: int = 252,
) -> float:
    """
    Information Ratio = (Portfolio Return - Benchmark Return) / Tracking Error.
    Measures risk-adjusted excess return vs a benchmark.
    If no benchmark, uses 0% (absolute return).
    """
    if len(returns) == 0:
        return 0.0

    if benchmark_returns is None:
        benchmark_returns = pd.Series(0, index=returns.index)

    # Align series
    active_return = returns - benchmark_returns
    tracking_error = active_return.std()

    if tracking_error == 0:
        return 0.0

    ann_active_return = active_return.mean() * periods_per_year
    ann_tracking_error = tracking_error * np.sqrt(periods_per_year)

    return float(ann_active_return / ann_tracking_error)


def ulcer_index(returns: pd.Series) -> float:
    """
    Ulcer Index — measures downside volatility (depth and duration of drawdowns).
    Lower is better. Named because it measures how much an investment
    would cause ulcers from drawdown pain.
    """
    if len(returns) == 0:
        return 0.0

    cumulative = (1 + returns).cumprod()
    running_max = cumulative.cummax()
    drawdown_pct = ((cumulative - running_max) / running_max) * 100

    return float(np.sqrt((drawdown_pct ** 2).mean()))


def compute_all_risk_metrics(
    returns: pd.Series,
    benchmark_returns: Optional[pd.Series] = None,
) -> Dict[str, float]:
    """
    Compute all advanced risk metrics at once.

    Args:
        returns: Daily returns series
        benchmark_returns: Optional benchmark returns for Information Ratio

    Returns:
        Dictionary with all risk metric values
    """
    return {
        "calmar_ratio": calmar_ratio(returns),
        "var_95": value_at_risk(returns, 0.95),
        "var_99": value_at_risk(returns, 0.99),
        "cvar_95": conditional_var(returns, 0.95),
        "cvar_99": conditional_var(returns, 0.99),
        "omega_ratio": omega_ratio(returns),
        "profit_factor": profit_factor(returns),
        "information_ratio": information_ratio(returns, benchmark_returns),
        "ulcer_index": ulcer_index(returns),
    }
