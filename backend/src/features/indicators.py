"""
StrategyVault - Feature Engineering Module
Adapted from AgentQuant's feature computation system

Provides:
- Technical indicator calculations (volatility, momentum, SMAs)
- Regime detection features (VIX integration)
- Robust column handling for MultiIndex DataFrames
"""

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _find_close_series(df: pd.DataFrame) -> pd.Series:
    """
    Robustly extract Close price series from DataFrame.
    Handles MultiIndex columns, flattened names, and case variations.
    
    Args:
        df: DataFrame with OHLCV data
        
    Returns:
        Series with close prices
        
    Raises:
        KeyError if Close column not found
    """
    cols = df.columns
    
    # Handle MultiIndex columns
    if isinstance(cols, pd.MultiIndex):
        for col in cols:
            if any('close' in str(x).lower() for x in col):
                return df[col].rename('Close')
        # Try flattening
        flat_df = df.copy()
        flat_df.columns = ['_'.join(map(str, col)).strip() for col in flat_df.columns]
        cols = flat_df.columns
        df = flat_df
    
    # Single-level columns
    if 'Close' in cols:
        return df['Close']
    
    # Case-insensitive search
    for col in cols:
        if str(col).lower() == 'close':
            return df[col].rename('Close')
    
    # Substring search
    for col in cols:
        if 'close' in str(col).lower():
            return df[col].rename('Close')
    
    raise KeyError(f"Could not find Close column. Available: {list(cols)[:10]}")


def compute_features(df: pd.DataFrame, include_vix: bool = True) -> pd.DataFrame:
    """
    Compute trading features from OHLCV data.
    
    Args:
        df: DataFrame with OHLCV data
        include_vix: Whether to expect VIX data in the DataFrame
        
    Returns:
        DataFrame with original data plus computed features:
        - volatility_21d: 21-day annualized volatility
        - volatility_63d: 63-day annualized volatility
        - momentum_21d: 21-day price momentum
        - momentum_63d: 63-day price momentum
        - momentum_252d: 252-day (1 year) price momentum
        - sma_21: 21-day simple moving average
        - sma_63: 63-day simple moving average
        - price_vs_sma63: Price relative to 63-day SMA
        - rsi_14: 14-period Relative Strength Index
        - macd: MACD line
        - macd_signal: MACD signal line
    """
    result = df.copy()
    
    # Flatten MultiIndex if present
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = ['_'.join(map(str, col)).strip() for col in result.columns]
    
    # Get close prices
    close = _find_close_series(result)
    
    # --- Volatility Features ---
    returns = close.pct_change()
    
    result['volatility_21d'] = returns.rolling(window=21).std() * np.sqrt(252)
    result['volatility_63d'] = returns.rolling(window=63).std() * np.sqrt(252)
    
    # --- Momentum Features ---
    result['momentum_21d'] = close.pct_change(periods=21)
    result['momentum_63d'] = close.pct_change(periods=63)
    result['momentum_252d'] = close.pct_change(periods=252)
    
    # --- Trend Features (SMAs) ---
    result['sma_21'] = close.rolling(window=21).mean()
    result['sma_63'] = close.rolling(window=63).mean()
    result['sma_200'] = close.rolling(window=200).mean()
    result['price_vs_sma63'] = (close / result['sma_63']) - 1
    
    # --- RSI (Relative Strength Index) ---
    result['rsi_14'] = compute_rsi(close, period=14)
    
    # --- MACD ---
    result['macd'], result['macd_signal'], result['macd_hist'] = compute_macd(close)
    
    # --- Bollinger Bands ---
    result['bb_upper'], result['bb_middle'], result['bb_lower'] = compute_bollinger_bands(close)
    
    # --- ATR (Average True Range) ---
    if 'High' in result.columns and 'Low' in result.columns:
        result['atr_14'] = compute_atr(result, period=14)
    
    return result


def compute_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def compute_macd(
    prices: pd.Series,
    fast: int = 12,
    slow: int = 26,
    signal: int = 9
) -> tuple:
    """Calculate MACD indicator."""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()
    
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def compute_bollinger_bands(
    prices: pd.Series,
    period: int = 20,
    std_dev: float = 2.0
) -> tuple:
    """Calculate Bollinger Bands."""
    middle = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    
    return upper, middle, lower


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high = df['High']
    low = df['Low']
    close = df['Close'].shift(1)
    
    tr1 = high - low
    tr2 = abs(high - close)
    tr3 = abs(low - close)
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def compute_features_for_multiple(
    data: Dict[str, pd.DataFrame]
) -> Dict[str, pd.DataFrame]:
    """
    Compute features for multiple assets.
    
    Args:
        data: Dictionary mapping symbol to OHLCV DataFrame
        
    Returns:
        Dictionary mapping symbol to DataFrame with features
    """
    result = {}
    
    for symbol, df in data.items():
        try:
            result[symbol] = compute_features(df)
        except Exception as e:
            logger.error(f"Error computing features for {symbol}: {e}")
    
    return result


if __name__ == "__main__":
    # Test feature computation
    from src.data.fetcher import fetch_ohlcv
    
    print("Testing feature computation...")
    
    # Fetch sample data
    btc = fetch_ohlcv("BTC-USD", period="6mo")
    
    if btc is not None:
        # Compute features
        features = compute_features(btc)
        
        print(f"\nFeatures computed: {len(features.columns)} columns")
        print("\nLast row with features:")
        print(features.iloc[-1])
        
        print("\nFeature columns:")
        for col in features.columns:
            print(f"  - {col}")
