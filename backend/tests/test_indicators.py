"""
Tests for StrategyVault - Feature Engineering (Indicators)
"""

import pytest
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.features.indicators import (
    _find_close_series,
    compute_features,
    compute_rsi,
    compute_macd,
    compute_bollinger_bands,
    compute_atr,
    compute_features_for_multiple,
)


class TestFindCloseSeries:
    """Test robust close-price extraction."""

    def test_standard_close_column(self, sample_ohlcv_df):
        close = _find_close_series(sample_ohlcv_df)
        assert close.name == 'Close'
        assert len(close) == len(sample_ohlcv_df)

    def test_lowercase_close(self):
        df = pd.DataFrame({'open': [1], 'high': [2], 'low': [0.5], 'close': [1.5]})
        close = _find_close_series(df)
        assert close.iloc[0] == 1.5

    def test_missing_close_raises(self):
        df = pd.DataFrame({'Open': [1], 'High': [2], 'Low': [0.5], 'Volume': [100]})
        with pytest.raises(KeyError):
            _find_close_series(df)


class TestComputeRSI:
    """Test RSI calculation."""

    def test_rsi_range(self, sample_ohlcv_df):
        close = sample_ohlcv_df['Close']
        rsi = compute_rsi(close, period=14)
        valid = rsi.dropna()
        assert (valid >= 0).all() and (valid <= 100).all()

    def test_rsi_length(self, sample_ohlcv_df):
        close = sample_ohlcv_df['Close']
        rsi = compute_rsi(close, period=14)
        assert len(rsi) == len(close)

    def test_rsi_custom_period(self, sample_ohlcv_df):
        close = sample_ohlcv_df['Close']
        rsi_7 = compute_rsi(close, period=7)
        rsi_21 = compute_rsi(close, period=21)
        # Both should be valid
        assert rsi_7.dropna().shape[0] > 0
        assert rsi_21.dropna().shape[0] > 0


class TestComputeMACD:
    """Test MACD calculation."""

    def test_macd_returns_tuple(self, sample_ohlcv_df):
        close = sample_ohlcv_df['Close']
        result = compute_macd(close)
        assert len(result) == 3  # macd_line, signal_line, histogram

    def test_macd_histogram_is_difference(self, sample_ohlcv_df):
        close = sample_ohlcv_df['Close']
        macd_line, signal_line, histogram = compute_macd(close)
        np.testing.assert_array_almost_equal(
            histogram.dropna().values,
            (macd_line - signal_line).dropna().values,
            decimal=10
        )


class TestComputeBollingerBands:
    """Test Bollinger Bands calculation."""

    def test_bollinger_upper_greater_lower(self, sample_ohlcv_df):
        close = sample_ohlcv_df['Close']
        upper, middle, lower = compute_bollinger_bands(close)
        valid_mask = upper.notna() & lower.notna()
        assert (upper[valid_mask] >= lower[valid_mask]).all()

    def test_bollinger_middle_is_sma(self, sample_ohlcv_df):
        close = sample_ohlcv_df['Close']
        upper, middle, lower = compute_bollinger_bands(close, period=20)
        expected_sma = close.rolling(20).mean()
        np.testing.assert_array_almost_equal(
            middle.dropna().values,
            expected_sma.dropna().values,
            decimal=10
        )


class TestComputeATR:
    """Test ATR calculation."""

    def test_atr_positive(self, sample_ohlcv_df):
        atr = compute_atr(sample_ohlcv_df, period=14)
        valid = atr.dropna()
        assert (valid >= 0).all()

    def test_atr_length(self, sample_ohlcv_df):
        atr = compute_atr(sample_ohlcv_df, period=14)
        assert len(atr) == len(sample_ohlcv_df)


class TestComputeFeatures:
    """Test full feature computation pipeline."""

    def test_features_adds_columns(self, sample_ohlcv_df):
        result = compute_features(sample_ohlcv_df)
        expected_cols = [
            'volatility_21d', 'volatility_63d',
            'momentum_21d', 'momentum_63d',
            'sma_21', 'sma_63', 'sma_200',
            'rsi_14', 'macd', 'macd_signal',
            'bb_upper', 'bb_middle', 'bb_lower',
        ]
        for col in expected_cols:
            assert col in result.columns, f"Missing column: {col}"

    def test_features_preserves_original(self, sample_ohlcv_df):
        result = compute_features(sample_ohlcv_df)
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            assert col in result.columns

    def test_features_has_atr_when_high_low_present(self, sample_ohlcv_df):
        result = compute_features(sample_ohlcv_df)
        assert 'atr_14' in result.columns

    def test_features_index_preserved(self, sample_ohlcv_df):
        result = compute_features(sample_ohlcv_df)
        assert result.index.equals(sample_ohlcv_df.index)

    def test_features_no_infinite_values(self, sample_ohlcv_df):
        result = compute_features(sample_ohlcv_df)
        numeric = result.select_dtypes(include=[np.number])
        assert not np.isinf(numeric.values).any()


class TestComputeFeaturesForMultiple:
    """Test multi-asset feature computation."""

    def test_multiple_assets(self, sample_ohlcv_df):
        data = {"BTC-USD": sample_ohlcv_df, "ETH-USD": sample_ohlcv_df.copy()}
        result = compute_features_for_multiple(data)
        assert "BTC-USD" in result
        assert "ETH-USD" in result
        assert 'rsi_14' in result["BTC-USD"].columns
