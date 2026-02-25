"""
StrategyVault - Shared test fixtures and configuration.
"""

import sys
import os
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add backend directory to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ─── Sample Data Fixtures ───────────────────────────────────────

@pytest.fixture
def sample_ohlcv_df():
    """Create a realistic OHLCV DataFrame for testing."""
    np.random.seed(42)
    n = 300
    dates = pd.date_range('2022-01-01', periods=n, freq='B')  # business days

    # Simulate a random walk price series
    price = 100 + np.cumsum(np.random.randn(n) * 1.5)
    price = np.maximum(price, 10)  # floor at 10

    df = pd.DataFrame({
        'Open': price + np.random.randn(n) * 0.5,
        'High': price + np.abs(np.random.randn(n)) * 1.2,
        'Low': price - np.abs(np.random.randn(n)) * 1.2,
        'Close': price,
        'Volume': np.random.randint(1_000_000, 10_000_000, n),
    }, index=dates)

    return df


@pytest.fixture
def sample_returns():
    """Create a sample returns Series for performance testing."""
    np.random.seed(42)
    n = 252  # one trading year
    dates = pd.date_range('2023-01-01', periods=n, freq='B')
    returns = pd.Series(np.random.randn(n) * 0.01 + 0.0003, index=dates)
    return returns


@pytest.fixture
def sample_features_df(sample_ohlcv_df):
    """Create a sample DataFrame with pre-computed features for regime tests."""
    df = sample_ohlcv_df.copy()
    close = df['Close']
    returns = close.pct_change()

    df['volatility_21d'] = returns.rolling(21).std() * np.sqrt(252)
    df['momentum_63d'] = close.pct_change(periods=63)
    df['vix_close'] = 18.0  # Low vol default
    return df.dropna()


# ─── Database Fixtures ───────────────────────────────────────────

@pytest.fixture
def db_engine():
    """Create an in-memory SQLite engine."""
    from sqlalchemy import create_engine
    engine = create_engine("sqlite:///:memory:")
    return engine


@pytest.fixture
def db_session(db_engine):
    """Create a database session with all tables."""
    from src.models.database import Base, get_session
    Base.metadata.create_all(db_engine)
    session = get_session(db_engine)
    yield session
    session.close()
