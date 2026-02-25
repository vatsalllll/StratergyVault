"""
StrategyVault - Data API Endpoints
Market data and regime analysis routes.
"""

from typing import List, Dict
from fastapi import APIRouter

from src.core.config import BACKTEST_ASSETS

router = APIRouter()


@router.get("/symbols")
async def list_symbols() -> List[Dict]:
    """List available symbols for backtesting."""
    return BACKTEST_ASSETS


@router.get("/regime")
async def get_current_regime():
    """
    Get current market regime analysis.
    Fetches live VIX + SPY data and classifies the regime.
    """
    try:
        from src.data.fetcher import fetch_ohlcv
        from src.features.indicators import compute_features
        from src.features.regime import analyze_regime
        import pandas as pd

        # Fetch SPY and VIX
        spy_data = fetch_ohlcv("SPY", period="6mo")
        vix_data = fetch_ohlcv("^VIX", period="6mo")

        if spy_data is None or spy_data.empty:
            return {"error": "Could not fetch market data", "regime": "Unknown"}

        features = compute_features(spy_data)

        if vix_data is not None and not vix_data.empty:
            if isinstance(vix_data.columns, pd.MultiIndex):
                vix_data.columns = vix_data.columns.get_level_values(0)
            features["vix_close"] = vix_data["Close"]
            features["vix_close"] = features["vix_close"].ffill()

        analysis = analyze_regime(features)

        return {
            "regime": analysis.current_regime.value,
            "vix_level": round(analysis.vix_level, 2),
            "momentum_63d": round(analysis.momentum_63d, 4),
            "volatility_21d": round(analysis.volatility_21d, 4),
            "confidence": round(analysis.regime_confidence, 2),
            "recommendations": analysis.strategy_recommendations,
        }
    except Exception as e:
        return {"error": str(e), "regime": "Unknown"}
