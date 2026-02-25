"""
Tests for StrategyVault - Regime Detection
"""

import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.features.regime import (
    MarketRegime,
    detect_regime,
    get_regime_recommendations,
    analyze_regime,
    get_regime_summary,
)


class TestDetectRegime:
    """Test regime classification logic."""

    def _make_features(self, vix=18, momentum=0.06):
        """Helper to build a single-row features DF."""
        return pd.DataFrame({
            'vix_close': [vix],
            'momentum_63d': [momentum],
            'volatility_21d': [0.15],
        })

    def test_crisis_bear(self):
        df = self._make_features(vix=35, momentum=-0.15)
        assert detect_regime(df) == MarketRegime.CRISIS_BEAR

    def test_highvol_uncertain(self):
        df = self._make_features(vix=35, momentum=0.0)
        assert detect_regime(df) == MarketRegime.HIGHVOL_UNCERTAIN

    def test_midvol_bull(self):
        df = self._make_features(vix=25, momentum=0.10)
        assert detect_regime(df) == MarketRegime.MIDVOL_BULL

    def test_midvol_bear(self):
        df = self._make_features(vix=25, momentum=-0.10)
        assert detect_regime(df) == MarketRegime.MIDVOL_BEAR

    def test_midvol_mean_revert(self):
        df = self._make_features(vix=25, momentum=0.0)
        assert detect_regime(df) == MarketRegime.MIDVOL_MEANREVERT

    def test_lowvol_bull(self):
        df = self._make_features(vix=15, momentum=0.10)
        assert detect_regime(df) == MarketRegime.LOWVOL_BULL

    def test_lowvol_mean_revert(self):
        df = self._make_features(vix=15, momentum=0.0)
        assert detect_regime(df) == MarketRegime.LOWVOL_MEANREVERT

    def test_empty_df_returns_unknown(self):
        df = pd.DataFrame()
        assert detect_regime(df) == MarketRegime.UNKNOWN

    def test_nan_defaults(self):
        """NaN values should fall back to defaults (VIX=20, momentum=0)."""
        df = pd.DataFrame({
            'vix_close': [float('nan')],
            'momentum_63d': [float('nan')],
        })
        regime = detect_regime(df)
        # NaN -> VIX=20 (at boundary, not > 20), momentum=0 -> LowVol-MeanRevert
        assert regime == MarketRegime.LOWVOL_MEANREVERT

    def test_missing_vix_column_defaults(self):
        """When VIX column doesn't exist, should default to 20."""
        df = pd.DataFrame({'momentum_63d': [0.10]})
        regime = detect_regime(df)
        # VIX default 20 => mid threshold, momentum > 5% => MidVol-Bull
        # But since VIX is exactly at threshold (20), it falls to else (< 20 => LowVol)
        # Actually vix > 20 is the elif, vix == 20 goes to else => LowVol
        assert regime == MarketRegime.LOWVOL_BULL


class TestRegimeRecommendations:
    """Test regime-based recommendations."""

    def test_all_regimes_have_recommendations(self):
        for regime in MarketRegime:
            recs = get_regime_recommendations(regime)
            assert isinstance(recs, list)
            assert len(recs) > 0

    def test_crisis_recommends_caution(self):
        recs = get_regime_recommendations(MarketRegime.CRISIS_BEAR)
        combined = " ".join(recs).lower()
        assert "reversion" in combined or "reduced" in combined


class TestAnalyzeRegime:
    """Test full regime analysis."""

    def test_analysis_returns_dataclass(self, sample_features_df):
        analysis = analyze_regime(sample_features_df, include_history=False)
        assert hasattr(analysis, 'current_regime')
        assert hasattr(analysis, 'regime_confidence')
        assert hasattr(analysis, 'strategy_recommendations')
        assert isinstance(analysis.strategy_recommendations, list)

    def test_confidence_range(self, sample_features_df):
        analysis = analyze_regime(sample_features_df, include_history=False)
        assert 0 <= analysis.regime_confidence <= 1

    def test_analysis_with_history(self, sample_features_df):
        # Limit rows for speed
        small_df = sample_features_df.head(30)
        analysis = analyze_regime(small_df, include_history=True)
        assert analysis.regime_history is not None
        assert len(analysis.regime_history) == len(small_df)


class TestRegimeSummary:
    """Test regime descriptions."""

    def test_summary_has_all_regimes(self):
        summary = get_regime_summary()
        assert len(summary) >= 7
        for key in summary:
            assert isinstance(summary[key], str)
            assert len(summary[key]) > 10
