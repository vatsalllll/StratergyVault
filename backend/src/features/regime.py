"""
StrategyVault - Regime Detection Module
Adapted from AgentQuant's regime detection system

Provides:
- Market regime classification based on VIX and momentum
- Regime-aware strategy recommendations
- Historical regime timeline analysis
"""

from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum

import pandas as pd
import numpy as np

from src.core.config import REGIME_THRESHOLDS, REGIME_LABELS


class MarketRegime(Enum):
    """Market regime classifications."""
    CRISIS_BEAR = "Crisis-Bear"
    HIGHVOL_UNCERTAIN = "HighVol-Uncertain"
    MIDVOL_BULL = "MidVol-Bull"
    MIDVOL_BEAR = "MidVol-Bear"
    MIDVOL_MEANREVERT = "MidVol-MeanRevert"
    LOWVOL_BULL = "LowVol-Bull"
    LOWVOL_MEANREVERT = "LowVol-MeanRevert"
    UNKNOWN = "Unknown"


@dataclass
class RegimeAnalysis:
    """Container for regime analysis results."""
    current_regime: MarketRegime
    vix_level: float
    momentum_63d: float
    volatility_21d: float
    regime_confidence: float
    strategy_recommendations: List[str]
    regime_history: Optional[pd.DataFrame] = None


def detect_regime(
    features_df: pd.DataFrame,
    vix_column: str = "vix_close",
    momentum_column: str = "momentum_63d"
) -> MarketRegime:
    """
    Detect market regime based on VIX and momentum indicators.
    
    Logic:
    - VIX > 30: High volatility environment
      - Momentum < -10%: Crisis-Bear
      - Else: HighVol-Uncertain
    - VIX 20-30: Mid volatility
      - Momentum > 5%: MidVol-Bull
      - Momentum < -5%: MidVol-Bear
      - Else: MidVol-MeanRevert
    - VIX < 20: Low volatility
      - Momentum > 5%: LowVol-Bull
      - Else: LowVol-MeanRevert
    
    Args:
        features_df: DataFrame with computed features
        vix_column: Column name for VIX data
        momentum_column: Column name for momentum data
        
    Returns:
        MarketRegime enum value
    """
    if features_df.empty:
        return MarketRegime.UNKNOWN
    
    latest = features_df.iloc[-1]
    
    # Get VIX and momentum values
    vix = latest.get(vix_column, 20)  # Default to 20 if not available
    momentum = latest.get(momentum_column, 0)
    
    # Handle NaN values
    if pd.isna(vix):
        vix = 20
    if pd.isna(momentum):
        momentum = 0
    
    # Classification logic
    if vix > REGIME_THRESHOLDS["vix_high"]:  # > 30
        if momentum < -0.10:
            return MarketRegime.CRISIS_BEAR
        else:
            return MarketRegime.HIGHVOL_UNCERTAIN
    
    elif vix > REGIME_THRESHOLDS["vix_mid"]:  # 20-30
        if momentum > REGIME_THRESHOLDS["momentum_bull"]:  # > 5%
            return MarketRegime.MIDVOL_BULL
        elif momentum < REGIME_THRESHOLDS["momentum_bear"]:  # < -5%
            return MarketRegime.MIDVOL_BEAR
        else:
            return MarketRegime.MIDVOL_MEANREVERT
    
    else:  # VIX < 20
        if momentum > REGIME_THRESHOLDS["momentum_bull"]:
            return MarketRegime.LOWVOL_BULL
        else:
            return MarketRegime.LOWVOL_MEANREVERT


def get_regime_recommendations(regime: MarketRegime) -> List[str]:
    """
    Get strategy type recommendations based on current regime.
    
    Args:
        regime: Current market regime
        
    Returns:
        List of recommended strategy types
    """
    recommendations = {
        MarketRegime.CRISIS_BEAR: [
            "Short-term mean reversion",
            "Volatility breakout",
            "Avoid trend following",
            "Consider reduced position sizes"
        ],
        MarketRegime.HIGHVOL_UNCERTAIN: [
            "Short-term momentum",
            "Volatility mean reversion",
            "Smaller position sizes",
            "Wider stop losses"
        ],
        MarketRegime.MIDVOL_BULL: [
            "Trend following",
            "Momentum strategies",
            "Breakout strategies",
            "Standard position sizes"
        ],
        MarketRegime.MIDVOL_BEAR: [
            "Short-term mean reversion",
            "Counter-trend strategies",
            "Reduced exposure",
            "Tighter stops"
        ],
        MarketRegime.MIDVOL_MEANREVERT: [
            "Mean reversion",
            "Range-bound strategies",
            "RSI oversold/overbought",
            "Bollinger band strategies"
        ],
        MarketRegime.LOWVOL_BULL: [
            "Long-term trend following",
            "Momentum strategies",
            "Larger position sizes possible",
            "Trailing stops"
        ],
        MarketRegime.LOWVOL_MEANREVERT: [
            "Mean reversion",
            "Range trading",
            "Carry strategies",
            "Standard sizing"
        ],
        MarketRegime.UNKNOWN: [
            "Use caution",
            "Reduce position sizes",
            "Wait for clarity"
        ]
    }
    
    return recommendations.get(regime, ["No specific recommendations"])


def analyze_regime(
    features_df: pd.DataFrame,
    include_history: bool = True
) -> RegimeAnalysis:
    """
    Perform comprehensive regime analysis.
    
    Args:
        features_df: DataFrame with computed features
        include_history: Whether to compute regime history
        
    Returns:
        RegimeAnalysis with current regime and recommendations
    """
    # Get current regime
    current_regime = detect_regime(features_df)
    
    # Get latest values
    latest = features_df.iloc[-1]
    vix_level = latest.get("vix_close", 20)
    momentum_63d = latest.get("momentum_63d", 0)
    volatility_21d = latest.get("volatility_21d", 0)
    
    # Calculate confidence (simple heuristic)
    # Higher confidence when indicators clearly point to regime
    if abs(momentum_63d) > 0.15:
        regime_confidence = 0.9
    elif abs(momentum_63d) > 0.08:
        regime_confidence = 0.75
    else:
        regime_confidence = 0.6
    
    # Get recommendations
    recommendations = get_regime_recommendations(current_regime)
    
    # Compute regime history if requested
    regime_history = None
    if include_history and len(features_df) > 1:
        regime_history = compute_regime_history(features_df)
    
    return RegimeAnalysis(
        current_regime=current_regime,
        vix_level=vix_level if not pd.isna(vix_level) else 20,
        momentum_63d=momentum_63d if not pd.isna(momentum_63d) else 0,
        volatility_21d=volatility_21d if not pd.isna(volatility_21d) else 0,
        regime_confidence=regime_confidence,
        strategy_recommendations=recommendations,
        regime_history=regime_history
    )


def compute_regime_history(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute regime for each point in time.
    
    Args:
        features_df: DataFrame with computed features
        
    Returns:
        DataFrame with date and regime columns
    """
    regimes = []
    
    for i in range(len(features_df)):
        row_df = features_df.iloc[:i+1]
        if len(row_df) > 0:
            regime = detect_regime(row_df)
            regimes.append({
                "date": features_df.index[i],
                "regime": regime.value
            })
    
    return pd.DataFrame(regimes)


def get_regime_summary() -> Dict[str, str]:
    """Get description of each regime type."""
    return {
        MarketRegime.CRISIS_BEAR.value: "High volatility with strong downward momentum. Crisis conditions.",
        MarketRegime.HIGHVOL_UNCERTAIN.value: "High volatility without clear direction. Uncertainty prevails.",
        MarketRegime.MIDVOL_BULL.value: "Moderate volatility with upward momentum. Healthy bull market.",
        MarketRegime.MIDVOL_BEAR.value: "Moderate volatility with downward momentum. Correction or bear.",
        MarketRegime.MIDVOL_MEANREVERT.value: "Moderate volatility, sideways market. Range-bound conditions.",
        MarketRegime.LOWVOL_BULL.value: "Low volatility with upward trend. Strong bull market.",
        MarketRegime.LOWVOL_MEANREVERT.value: "Low volatility, sideways market. Calm range-bound.",
    }


if __name__ == "__main__":
    # Test regime detection
    from src.data.fetcher import fetch_multiple_assets
    from src.features.indicators import compute_features
    
    print("Testing regime detection...")
    
    # Fetch SPY and VIX
    data = fetch_multiple_assets(symbols=["SPY", "^VIX"], period="6mo")
    
    if "SPY" in data:
        # Compute features
        features = compute_features(data["SPY"])
        
        # Add VIX if available
        if "^VIX" in data:
            vix_df = data["^VIX"]
            if isinstance(vix_df.columns, pd.MultiIndex):
                vix_df.columns = vix_df.columns.get_level_values(0)
            features["vix_close"] = vix_df["Close"]
            features["vix_close"] = features["vix_close"].ffill()
        
        # Analyze regime
        analysis = analyze_regime(features)
        
        print(f"\nCurrent Regime: {analysis.current_regime.value}")
        print(f"VIX Level: {analysis.vix_level:.2f}")
        print(f"63-day Momentum: {analysis.momentum_63d:.2%}")
        print(f"Confidence: {analysis.regime_confidence:.0%}")
        print(f"\nRecommendations:")
        for rec in analysis.strategy_recommendations:
            print(f"  - {rec}")
