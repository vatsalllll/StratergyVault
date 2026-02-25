"""
StrategyVault - Data Fetching Module
Adapted from AgentQuant's data ingestion system

Provides:
- Market data fetching via yfinance
- Data caching with Parquet format
- Multi-asset support (crypto, stocks, indices)
"""

import os
from pathlib import Path
from datetime import date, datetime
from typing import Dict, List, Optional, Union

import pandas as pd
import yfinance as yf

from src.core.config import settings, BACKTEST_ASSETS


def get_data_path() -> Path:
    """Creates and returns the data storage path."""
    path = Path("data_cache")
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch_ohlcv(
    symbol: str,
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None,
    period: str = "2y",
    interval: str = "1d",
    force_download: bool = False
) -> Optional[pd.DataFrame]:
    """
    Fetch OHLCV data for a single symbol.
    
    Args:
        symbol: Ticker symbol (e.g., 'BTC-USD', 'SPY')
        start_date: Start date (YYYY-MM-DD or date object)
        end_date: End date (YYYY-MM-DD or date object)
        period: Data period if dates not specified (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
        force_download: Force re-download even if cached
        
    Returns:
        DataFrame with OHLCV data or None if error
    """
    data_path = get_data_path()
    
    # Convert dates to strings
    if isinstance(start_date, date):
        start_date = start_date.strftime('%Y-%m-%d')
    if isinstance(end_date, date):
        end_date = end_date.strftime('%Y-%m-%d')
    
    # Create cache filename
    safe_symbol = symbol.replace('^', '').replace('-', '_')
    cache_file = data_path / f"{safe_symbol}_{interval}.parquet"
    csv_fallback = data_path / f"{safe_symbol}_{interval}.csv"
    
    # Check cache (Parquet first, then CSV)
    if not force_download:
        for cfile in [cache_file, csv_fallback]:
            if cfile.exists():
                try:
                    if str(cfile).endswith('.parquet'):
                        df = pd.read_parquet(cfile)
                    else:
                        df = pd.read_csv(cfile, index_col=0, parse_dates=True)
                    
                    # Flatten MultiIndex if needed
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    # Filter by date range if specified
                    if start_date or end_date:
                        if start_date:
                            df = df[df.index >= pd.to_datetime(start_date)]
                        if end_date:
                            df = df[df.index <= pd.to_datetime(end_date)]
                    
                    if not df.empty:
                        return df
                except Exception as e:
                    print(f"Error reading cache for {symbol}: {e}")
    
    # Download from yfinance
    try:
        print(f"Downloading {symbol}...")
        
        if start_date and end_date:
            data = yf.download(
                symbol, 
                start=start_date, 
                end=end_date,
                interval=interval,
                auto_adjust=True,
                progress=False
            )
        else:
            data = yf.download(
                symbol,
                period=period,
                interval=interval,
                auto_adjust=True,
                progress=False
            )
        
        if data.empty:
            print(f"Warning: No data found for {symbol}")
            return None
        
        # Flatten MultiIndex columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        
        # Save to cache — try Parquet first, fall back to CSV
        try:
            data.to_parquet(cache_file)
        except Exception:
            data.to_csv(csv_fallback)
        
        return data
        
    except Exception as e:
        print(f"Error downloading {symbol}: {e}")
        return None


def fetch_multiple_assets(
    symbols: Optional[List[str]] = None,
    **kwargs
) -> Dict[str, pd.DataFrame]:
    """
    Fetch OHLCV data for multiple symbols.
    
    Args:
        symbols: List of ticker symbols. If None, uses BACKTEST_ASSETS from config.
        **kwargs: Additional arguments passed to fetch_ohlcv
        
    Returns:
        Dictionary mapping symbol to DataFrame
    """
    if symbols is None:
        symbols = [asset["symbol"] for asset in BACKTEST_ASSETS]
    
    all_data = {}
    
    for symbol in symbols:
        try:
            data = fetch_ohlcv(symbol, **kwargs)
            if data is not None and not data.empty:
                all_data[symbol] = data
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    
    return all_data


def get_available_symbols() -> List[Dict]:
    """Get list of available symbols for backtesting."""
    return BACKTEST_ASSETS


def clear_cache():
    """Clear all cached data files."""
    data_path = get_data_path()
    for file in data_path.glob("*.parquet"):
        file.unlink()
    print("Cache cleared")


if __name__ == "__main__":
    # Test fetching
    print("Testing data fetching...")
    
    # Single asset
    btc = fetch_ohlcv("BTC-USD", period="1mo")
    if btc is not None:
        print(f"\nBTC-USD data shape: {btc.shape}")
        print(btc.tail())
    
    # Multiple assets
    data = fetch_multiple_assets(symbols=["BTC-USD", "ETH-USD", "SPY"], period="1mo")
    print(f"\nFetched {len(data)} assets")
    for symbol, df in data.items():
        print(f"  {symbol}: {len(df)} rows")
