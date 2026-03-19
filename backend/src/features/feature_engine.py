"""
StrategyVault — Integrated Feature Engine
Ported from AgentQuant (src/features/engine.py) with StrategyVault-specific additions.

Computes:
 - Volatility (21d, 63d)
 - Momentum (21d, 63d, 252d)
 - Trend (SMA21, SMA63, price_vs_sma63)
 - RSI, Bollinger Band width, ATR
 - VIX integration (optional)
 - Market regime label (from regime module)
"""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _find_close(df: pd.DataFrame) -> pd.Series:
    """
    Robustly extract the 'Close' series from a DataFrame.
    Handles: single-level, MultiIndex, case-insensitive, substring match.
    Ported directly from AgentQuant/src/features/engine.py.
    """
    field = "Close"
    field_l = field.lower()

    def _to_series(candidate):
        s = df[candidate]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[:, 0]
        return s.rename(field)

    cols = df.columns
    if isinstance(cols, pd.MultiIndex):
        matches = [c for c in cols if any(str(x).lower() == field_l for x in c)]
        if matches:
            return _to_series(matches[0])
        for lvl in range(cols.nlevels):
            for col in cols:
                if str(col[lvl]).lower() == field_l:
                    return _to_series(col)
        substr = [c for c in cols if any(field_l in str(x).lower() for x in c)]
        if substr:
            return _to_series(substr[0])
    else:
        if field in cols:
            return _to_series(field)
        ci = [c for c in cols if str(c).lower() == field_l]
        if ci:
            return _to_series(ci[0])
        sub = [c for c in cols if field_l in str(c).lower()]
        if sub:
            return _to_series(sub[0])

    raise KeyError(f"Could not find 'Close' in columns: {list(cols[:10])}")


def compute_features(
    df: pd.DataFrame,
    include_vix: bool = False,
) -> pd.DataFrame:
    """
    Compute full feature set from an OHLCV DataFrame.

    Args:
        df: OHLCV DataFrame (index=datetime, columns include Open/High/Low/Close/Volume)
        include_vix: Whether to try fetching VIX and appending vix_close

    Returns:
        DataFrame with original OHLCV + feature columns, NaN rows dropped
    """
    # Flatten any MultiIndex columns
    result = df.copy()
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = ["_".join(map(str, c)).strip() for c in result.columns]

    close = _find_close(df)

    # ── Volatility ──────────────────────────────────────────────
    result["volatility_21d"] = close.pct_change().rolling(21).std() * np.sqrt(252)
    result["volatility_63d"] = close.pct_change().rolling(63).std() * np.sqrt(252)

    # ── Momentum ────────────────────────────────────────────────
    result["momentum_21d"] = close.pct_change(21)
    result["momentum_63d"] = close.pct_change(63)
    result["momentum_252d"] = close.pct_change(252)

    # ── Trend ───────────────────────────────────────────────────
    sma21 = close.rolling(21).mean()
    sma63 = close.rolling(63).mean()
    result["sma_21"] = sma21
    result["sma_63"] = sma63
    result["price_vs_sma63"] = close / sma63 - 1

    # ── RSI (14-period) ─────────────────────────────────────────
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    result["rsi_14"] = 100 - (100 / (1 + rs))

    # ── Bollinger Band Width ─────────────────────────────────────
    bb_std = close.rolling(20).std()
    bb_mid = close.rolling(20).mean()
    result["bb_width"] = (2 * bb_std) / bb_mid

    # ── ATR (14-period) ─────────────────────────────────────────
    try:
        high = df["High"] if "High" in df.columns else df.iloc[:, 1]
        low  = df["Low"]  if "Low"  in df.columns else df.iloc[:, 2]
        tr = pd.concat([
            high - low,
            (high - close.shift(1)).abs(),
            (low  - close.shift(1)).abs(),
        ], axis=1).max(axis=1)
        result["atr_14"] = tr.rolling(14).mean()
    except Exception:
        pass

    # ── VIX (optional) ─────────────────────────────────────────
    if include_vix:
        try:
            import yfinance as yf
            vix = yf.download("^VIX", period="5y", progress=False)["Close"]
            vix.name = "vix_close"
            result = result.join(vix, how="left")
            result["vix_close"] = result["vix_close"].ffill()
        except Exception as e:
            logger.warning("Could not fetch VIX: %s", e)

    return result.dropna()


def compute_features_for_strategy(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute a compact dict of the latest feature values for a DataFrame.
    Useful for feeding feature signals into the AI strategy generator.
    """
    features_df = compute_features(df)
    if features_df.empty:
        return {}

    latest = features_df.iloc[-1]
    return {
        "volatility_21d": round(float(latest.get("volatility_21d", 0)), 4),
        "volatility_63d": round(float(latest.get("volatility_63d", 0)), 4),
        "momentum_21d":   round(float(latest.get("momentum_21d",   0)), 4),
        "momentum_63d":   round(float(latest.get("momentum_63d",   0)), 4),
        "rsi_14":         round(float(latest.get("rsi_14",         50)), 2),
        "bb_width":       round(float(latest.get("bb_width",       0)), 4),
        "price_vs_sma63": round(float(latest.get("price_vs_sma63", 0)), 4),
    }
