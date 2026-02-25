"""Data module for StrategyVault."""

from .fetcher import fetch_ohlcv, fetch_multiple_assets, get_available_symbols

__all__ = [
    "fetch_ohlcv",
    "fetch_multiple_assets", 
    "get_available_symbols",
]
