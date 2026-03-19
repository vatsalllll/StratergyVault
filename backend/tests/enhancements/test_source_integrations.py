"""
Tests for StrategyVault — Feature Engine & Strategy Templates (from source repos)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import pandas as pd
import numpy as np
from src.features.feature_engine import compute_features, compute_features_for_strategy, _find_close
from src.features.strategy_templates import list_templates, get_template, STRATEGY_TEMPLATES


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_ohlcv():
    """300-bar OHLCV DataFrame for testing."""
    np.random.seed(42)
    n = 300
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    close = 100 + np.cumsum(np.random.randn(n) * 1.5)
    df = pd.DataFrame({
        "Open":   close + np.random.randn(n) * 0.3,
        "High":   close + abs(np.random.randn(n)) * 0.8,
        "Low":    close - abs(np.random.randn(n)) * 0.8,
        "Close":  close,
        "Volume": np.random.randint(1_000, 50_000, n).astype(float),
    }, index=idx)
    return df


@pytest.fixture
def multiindex_ohlcv(sample_ohlcv):
    """Same data but with a MultiIndex column (as yfinance can return)."""
    df = sample_ohlcv.copy()
    df.columns = pd.MultiIndex.from_tuples(
        [(c, "BTC-USD") for c in df.columns]
    )
    return df


# ── Feature Engine Tests ───────────────────────────────────────────────────────

class TestFindClose:
    def test_single_level(self, sample_ohlcv):
        s = _find_close(sample_ohlcv)
        assert s.name == "Close"
        assert len(s) == len(sample_ohlcv)

    def test_multiindex(self, multiindex_ohlcv):
        s = _find_close(multiindex_ohlcv)
        assert s.name == "Close"

    def test_raises_on_missing(self):
        bad = pd.DataFrame({"foo": [1, 2, 3], "bar": [4, 5, 6]})
        with pytest.raises(KeyError):
            _find_close(bad)


class TestComputeFeatures:
    def test_returns_dataframe(self, sample_ohlcv):
        out = compute_features(sample_ohlcv)
        assert isinstance(out, pd.DataFrame)
        assert not out.empty

    def test_has_expected_columns(self, sample_ohlcv):
        out = compute_features(sample_ohlcv)
        for col in ["volatility_21d", "volatility_63d", "momentum_21d",
                    "momentum_63d", "rsi_14", "bb_width", "sma_21", "sma_63"]:
            assert col in out.columns, f"Missing: {col}"

    def test_no_overflow(self, sample_ohlcv):
        out = compute_features(sample_ohlcv)
        assert not out.isin([float("inf"), float("-inf")]).any().any()

    def test_multiindex_input(self, multiindex_ohlcv):
        out = compute_features(multiindex_ohlcv)
        assert not out.empty

    def test_rsi_bounded(self, sample_ohlcv):
        out = compute_features(sample_ohlcv)
        assert (out["rsi_14"] >= 0).all()
        assert (out["rsi_14"] <= 100).all()


class TestComputeFeaturesForStrategy:
    def test_returns_dict(self, sample_ohlcv):
        d = compute_features_for_strategy(sample_ohlcv)
        assert isinstance(d, dict)

    def test_has_keys(self, sample_ohlcv):
        d = compute_features_for_strategy(sample_ohlcv)
        assert "rsi_14" in d
        assert "volatility_21d" in d

    def test_values_are_floats(self, sample_ohlcv):
        d = compute_features_for_strategy(sample_ohlcv)
        for k, v in d.items():
            assert isinstance(v, float), f"{k} is not float"


# ── Strategy Template Tests ────────────────────────────────────────────────────

class TestStrategyTemplates:
    def test_list_templates_returns_list(self):
        templates = list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0

    def test_each_template_has_required_keys(self):
        for t in list_templates():
            for key in ("id", "name", "description", "tags", "source"):
                assert key in t, f"Template missing key: {key}"

    def test_get_template_returns_code(self):
        t = get_template("bb_squeeze_adx")
        assert "code" in t
        assert "BBSqueezeADX" in t["code"]

    def test_template_code_is_valid_python(self):
        for name, t in STRATEGY_TEMPLATES.items():
            try:
                compile(t["code"], f"<template:{name}>", "exec")
            except SyntaxError as e:
                pytest.fail(f"Template '{name}' has syntax error: {e}")

    def test_get_nonexistent_template(self):
        t = get_template("nonexistent_strategy")
        assert t == {}

    def test_bb_squeeze_tags(self):
        t = get_template("bb_squeeze_adx")
        assert "volatility" in t["tags"]
        assert "trend-filter" in t["tags"]
