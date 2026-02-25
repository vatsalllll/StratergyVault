"""
Tests for StrategyVault - Core Configuration
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class TestSettings:
    """Test core settings and configuration."""

    def test_settings_load(self):
        """Settings singleton should load with defaults."""
        from src.core.config import settings
        assert settings.APP_NAME == "StrategyVault"
        assert settings.APP_VERSION == "1.0.0"

    def test_default_thresholds(self):
        """Quality thresholds should have sensible defaults."""
        from src.core.config import settings
        assert settings.GOLD_SCORE_THRESHOLD == 85
        assert settings.SILVER_SCORE_THRESHOLD == 70
        assert settings.BRONZE_SCORE_THRESHOLD == 50
        assert settings.GOLD_SCORE_THRESHOLD > settings.SILVER_SCORE_THRESHOLD > settings.BRONZE_SCORE_THRESHOLD

    def test_walk_forward_config(self):
        """Validation settings should be present."""
        from src.core.config import settings
        assert settings.WALK_FORWARD_WINDOW_MONTHS > 0
        assert settings.MIN_SHARPE_RATIO >= 0
        assert settings.MAX_DRAWDOWN_PERCENT > 0

    def test_backtest_assets_non_empty(self):
        """BACKTEST_ASSETS should have at least a few assets."""
        from src.core.config import BACKTEST_ASSETS
        assert len(BACKTEST_ASSETS) > 5
        # Every asset must have symbol, name, category
        for asset in BACKTEST_ASSETS:
            assert "symbol" in asset
            assert "name" in asset
            assert "category" in asset

    def test_asset_categories(self):
        """BACKTEST_ASSETS should include multiple categories."""
        from src.core.config import BACKTEST_ASSETS
        categories = {a["category"] for a in BACKTEST_ASSETS}
        assert "crypto" in categories
        assert "stocks" in categories

    def test_regime_thresholds(self):
        """REGIME_THRESHOLDS should have required keys."""
        from src.core.config import REGIME_THRESHOLDS
        assert "vix_high" in REGIME_THRESHOLDS
        assert "vix_mid" in REGIME_THRESHOLDS
        assert "momentum_bull" in REGIME_THRESHOLDS
        assert "momentum_bear" in REGIME_THRESHOLDS
        assert REGIME_THRESHOLDS["vix_high"] > REGIME_THRESHOLDS["vix_mid"]

    def test_regime_labels(self):
        """REGIME_LABELS should have all expected regimes."""
        from src.core.config import REGIME_LABELS
        assert len(REGIME_LABELS) >= 7
        assert "Crisis-Bear" in REGIME_LABELS
        assert "LowVol-Bull" in REGIME_LABELS

    def test_swarm_models_config(self):
        """SWARM_MODELS should list multiple AI models."""
        from src.core.config import settings
        assert len(settings.SWARM_MODELS) >= 3
        assert settings.CONSENSUS_THRESHOLD > 0
        assert settings.CONSENSUS_THRESHOLD <= 1.0
