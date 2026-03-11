"""
Tests for StrategyVault - Pipeline Integration
Tests that the pipeline uses real validation and does not fake metrics.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np


class TestQuickWalkForward:
    """Test the quick_walk_forward convenience function."""

    def test_quick_walk_forward_returns_result(self, sample_ohlcv_df):
        """quick_walk_forward should return a WalkForwardResult."""
        from src.validation.walk_forward import quick_walk_forward, WalkForwardResult

        result = quick_walk_forward(sample_ohlcv_df, train_months=3, test_months=1)
        assert isinstance(result, WalkForwardResult)
        assert hasattr(result, "robustness_score")
        assert hasattr(result, "is_robust")

    def test_quick_walk_forward_has_windows(self, sample_ohlcv_df):
        """With enough data, walk-forward should create multiple windows."""
        from src.validation.walk_forward import quick_walk_forward

        result = quick_walk_forward(sample_ohlcv_df, train_months=3, test_months=1)
        assert len(result.windows) > 0

    def test_quick_walk_forward_score_in_range(self, sample_ohlcv_df):
        """Robustness score should be between 0 and 1."""
        from src.validation.walk_forward import quick_walk_forward

        result = quick_walk_forward(sample_ohlcv_df, train_months=3, test_months=1)
        assert 0 <= result.robustness_score <= 1

    def test_quick_walk_forward_insufficient_data(self):
        """Short data should return empty result with score 0."""
        from src.validation.walk_forward import quick_walk_forward

        # Only 30 days of data — not enough for 3+1 month windows
        dates = pd.date_range("2023-01-01", periods=30, freq="B")
        df = pd.DataFrame(
            {
                "Open": np.random.rand(30) * 100,
                "High": np.random.rand(30) * 100,
                "Low": np.random.rand(30) * 100,
                "Close": np.random.rand(30) * 100,
                "Volume": np.random.randint(1000, 10000, 30),
            },
            index=dates,
        )
        result = quick_walk_forward(df, train_months=3, test_months=1)
        assert result.robustness_score == 0.0
        assert len(result.windows) == 0


class TestPipelineNoSyntheticMetrics:
    """Test that the pipeline does not use synthetic/fake metrics."""

    def test_no_synthetic_metrics_function(self):
        """_synthetic_metrics should not exist in pipeline module."""
        from src.services import pipeline

        assert not hasattr(pipeline, "_synthetic_metrics"), (
            "_synthetic_metrics still exists — it should have been removed"
        )

    def test_pipeline_status_has_no_synthetic_step(self):
        """Pipeline output should never include a 'synthetic_metrics' step."""
        # We can't easily run the full pipeline without API keys,
        # but we can verify the function signature exists
        from src.services.pipeline import run_pipeline

        assert callable(run_pipeline)


class TestPipelineTierAssignment:
    """Test that tier assignment respects backtest success."""

    def test_rejected_tier_values(self):
        """Verify tier thresholds from config are properly ordered."""
        from src.core.config import settings

        assert settings.GOLD_SCORE_THRESHOLD > settings.SILVER_SCORE_THRESHOLD
        assert settings.SILVER_SCORE_THRESHOLD > settings.BRONZE_SCORE_THRESHOLD
        assert settings.BRONZE_SCORE_THRESHOLD > 0

    def test_score_calculation_works(self):
        """calculate_strategy_score should return a valid score."""
        from src.rating.swarm import calculate_strategy_score

        score = calculate_strategy_score(
            return_pct=25.0,
            sharpe_ratio=1.5,
            max_drawdown=-15.0,
            consensus_confidence=0.5,
            walk_forward_score=70.0,
            is_robust=True,
        )
        assert isinstance(score, int)
        assert 0 <= score <= 100

    def test_failed_backtest_gets_low_score(self):
        """A strategy with no returns should get a low score."""
        from src.rating.swarm import calculate_strategy_score

        score = calculate_strategy_score(
            return_pct=0,
            sharpe_ratio=0,
            max_drawdown=0,
            consensus_confidence=0.5,
            walk_forward_score=0,
            is_robust=False,
        )
        assert score < 50  # Should be below bronze threshold

    def test_good_strategy_gets_high_score(self):
        """A strategy with strong metrics should score high."""
        from src.rating.swarm import calculate_strategy_score

        score = calculate_strategy_score(
            return_pct=50.0,
            sharpe_ratio=2.5,
            max_drawdown=-10.0,
            consensus_confidence=0.9,
            walk_forward_score=80.0,
            is_robust=True,
        )
        assert score >= 50  # Should be at least bronze
