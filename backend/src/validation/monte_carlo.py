"""
StrategyVault - Monte Carlo Simulation
Validates strategy performance through statistical resampling.

Provides:
- Shuffle trade returns and re-simulate N times
- Generate confidence intervals for key metrics
- Determine if strategy performance is statistically significant
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class MonteCarloResult:
    """Results from Monte Carlo simulation."""
    num_simulations: int
    
    # Confidence intervals (5th and 95th percentile)
    return_ci_lower: float
    return_ci_upper: float
    sharpe_ci_lower: float
    sharpe_ci_upper: float
    max_dd_ci_lower: float
    max_dd_ci_upper: float
    
    # Original metrics
    original_return: float
    original_sharpe: float
    original_max_dd: float
    
    # P-value — probability that random shuffling produces equal or better results
    p_value: float
    is_significant: bool  # p_value < 0.05


def run_monte_carlo(
    returns: pd.Series,
    num_simulations: int = 1000,
    confidence: float = 0.90,
    seed: Optional[int] = None,
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation by shuffling daily returns.
    
    This tests whether the strategy's performance is due to the specific
    ordering of trades (genuine edge) or just random chance.
    
    Args:
        returns: Daily return series from the strategy
        num_simulations: Number of shuffle simulations (default 1000)
        confidence: Confidence interval level (default 90%)
        seed: Random seed for reproducibility
        
    Returns:
        MonteCarloResult with confidence intervals and significance test
    """
    if len(returns) < 10:
        return MonteCarloResult(
            num_simulations=0,
            return_ci_lower=0, return_ci_upper=0,
            sharpe_ci_lower=0, sharpe_ci_upper=0,
            max_dd_ci_lower=0, max_dd_ci_upper=0,
            original_return=0, original_sharpe=0, original_max_dd=0,
            p_value=1.0, is_significant=False,
        )

    rng = np.random.RandomState(seed)
    returns_arr = returns.values.copy()
    n = len(returns_arr)

    # Original metrics
    orig_total_return = float((1 + returns_arr).prod() - 1) * 100
    orig_sharpe = _sharpe(returns_arr)
    orig_max_dd = _max_drawdown(returns_arr)

    # Run simulations
    sim_returns = np.zeros(num_simulations)
    sim_sharpes = np.zeros(num_simulations)
    sim_max_dds = np.zeros(num_simulations)

    for i in range(num_simulations):
        shuffled = rng.permutation(returns_arr)
        sim_returns[i] = (np.prod(1 + shuffled) - 1) * 100
        sim_sharpes[i] = _sharpe(shuffled)
        sim_max_dds[i] = _max_drawdown(shuffled)

    # Confidence intervals
    lower_pct = (1 - confidence) / 2 * 100
    upper_pct = (1 + confidence) / 2 * 100

    # P-value: fraction of simulations that beat or match original Sharpe
    p_value = float(np.mean(sim_sharpes >= orig_sharpe))

    return MonteCarloResult(
        num_simulations=num_simulations,
        return_ci_lower=float(np.percentile(sim_returns, lower_pct)),
        return_ci_upper=float(np.percentile(sim_returns, upper_pct)),
        sharpe_ci_lower=float(np.percentile(sim_sharpes, lower_pct)),
        sharpe_ci_upper=float(np.percentile(sim_sharpes, upper_pct)),
        max_dd_ci_lower=float(np.percentile(sim_max_dds, lower_pct)),
        max_dd_ci_upper=float(np.percentile(sim_max_dds, upper_pct)),
        original_return=orig_total_return,
        original_sharpe=orig_sharpe,
        original_max_dd=orig_max_dd,
        p_value=p_value,
        is_significant=(p_value < 0.05),
    )


def _sharpe(returns: np.ndarray) -> float:
    """Annualized Sharpe ratio from daily returns."""
    if len(returns) == 0 or np.std(returns) == 0:
        return 0.0
    return float(np.mean(returns) / np.std(returns) * np.sqrt(252))


def _max_drawdown(returns: np.ndarray) -> float:
    """Max drawdown from daily returns (as negative percentage)."""
    if len(returns) == 0:
        return 0.0
    cumulative = np.cumprod(1 + returns)
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    return float(drawdown.min() * 100)
