"""
Tests for StrategyVault - Strategy Scoring & Consensus
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.rating.swarm import (
    ModelResponse,
    ConsensusResult,
    SwarmAgent,
    calculate_strategy_score,
)


class TestStrategyScore:
    """Test the strategy scoring algorithm."""

    def test_perfect_strategy(self):
        """A strategy with excellent metrics should score high."""
        score = calculate_strategy_score(
            return_pct=50.0,
            sharpe_ratio=2.0,
            max_drawdown=-10.0,
            consensus_confidence=1.0,
            walk_forward_score=100.0,
            is_robust=True
        )
        assert score >= 85  # Should be Gold tier

    def test_mediocre_strategy(self):
        """A mediocre strategy should score mid-range."""
        score = calculate_strategy_score(
            return_pct=10.0,
            sharpe_ratio=0.5,
            max_drawdown=-20.0,
            consensus_confidence=0.5,
            walk_forward_score=50.0,
            is_robust=False
        )
        assert 20 <= score <= 60

    def test_terrible_strategy(self):
        """A strategy with negative returns and high drawdown should score low."""
        score = calculate_strategy_score(
            return_pct=-10.0,
            sharpe_ratio=-0.5,
            max_drawdown=-45.0,
            consensus_confidence=0.0,
            walk_forward_score=10.0,
            is_robust=False
        )
        assert score < 30

    def test_score_bounded_0_100(self):
        """Score should always be in [0, 100]."""
        # Very high metrics
        high = calculate_strategy_score(100.0, 5.0, -5.0, 1.0, 100.0, True)
        assert 0 <= high <= 100

        # Very low metrics
        low = calculate_strategy_score(-50.0, -2.0, -80.0, 0.0, 0.0, False)
        assert 0 <= low <= 100

    def test_high_drawdown_penalty(self):
        """High drawdown should reduce score."""
        score_low_dd = calculate_strategy_score(30.0, 1.5, -10.0, 0.75, 80.0, True)
        score_high_dd = calculate_strategy_score(30.0, 1.5, -35.0, 0.75, 80.0, True)
        assert score_low_dd > score_high_dd

    def test_robustness_bonus(self):
        """Robustness flag should add points."""
        robust = calculate_strategy_score(20.0, 1.0, -15.0, 0.6, 60.0, True)
        not_robust = calculate_strategy_score(20.0, 1.0, -15.0, 0.6, 60.0, False)
        assert robust > not_robust
        assert robust - not_robust == 10  # 10-point bonus

    def test_consensus_contribution(self):
        """Higher consensus confidence should increase score."""
        high = calculate_strategy_score(20.0, 1.0, -15.0, 1.0, 60.0, True)
        low = calculate_strategy_score(20.0, 1.0, -15.0, 0.0, 60.0, True)
        assert high > low


class TestConsensusCalculation:
    """Test consensus from model responses."""

    def test_unanimous_buy(self):
        agent = SwarmAgent.__new__(SwarmAgent)
        agent.models = SwarmAgent.DEFAULT_MODELS
        agent.clients = {}

        responses = [
            ModelResponse("gemini", "model", "", "BUY", 0.9, "Good strategy", 1.0, True),
            ModelResponse("openai", "model", "", "BUY", 0.8, "Looks solid", 1.5, True),
            ModelResponse("anthropic", "model", "", "BUY", 0.85, "Strong", 1.2, True),
        ]

        result = agent._calculate_consensus(responses)
        assert result.consensus_vote == "BUY"
        assert result.consensus_confidence == 1.0
        assert result.successful_models == 3

    def test_split_vote(self):
        agent = SwarmAgent.__new__(SwarmAgent)
        agent.models = SwarmAgent.DEFAULT_MODELS
        agent.clients = {}

        responses = [
            ModelResponse("gemini", "model", "", "BUY", 0.9, "Good", 1.0, True),
            ModelResponse("openai", "model", "", "HOLD", 0.5, "Unsure", 1.5, True),
            ModelResponse("anthropic", "model", "", "SELL", 0.7, "Risky", 1.2, True),
        ]

        result = agent._calculate_consensus(responses)
        assert result.consensus_vote in ["BUY", "HOLD", "SELL"]
        assert result.total_models == 3

    def test_failed_models_excluded(self):
        agent = SwarmAgent.__new__(SwarmAgent)
        agent.models = SwarmAgent.DEFAULT_MODELS
        agent.clients = {}

        responses = [
            ModelResponse("gemini", "model", "", "BUY", 0.9, "Good", 1.0, True),
            ModelResponse("openai", "model", "", "HOLD", 0.0, "", 0, False, "API Error"),
        ]

        result = agent._calculate_consensus(responses)
        assert result.successful_models == 1
        assert result.consensus_vote == "BUY"

    def test_no_successful_models(self):
        agent = SwarmAgent.__new__(SwarmAgent)
        agent.models = SwarmAgent.DEFAULT_MODELS
        agent.clients = {}

        responses = [
            ModelResponse("gemini", "model", "", "HOLD", 0.0, "", 0, False, "Error"),
        ]

        result = agent._calculate_consensus(responses)
        assert result.consensus_vote == "HOLD"
        assert result.consensus_confidence == 0


class TestJsonParsing:
    """Test JSON response parsing from AI models."""

    def test_valid_json(self):
        agent = SwarmAgent.__new__(SwarmAgent)
        text = '{"vote": "BUY", "confidence": 0.85, "reasoning": "Looks good"}'
        result = agent._parse_json_response(text)
        assert result["vote"] == "BUY"

    def test_json_in_markdown(self):
        agent = SwarmAgent.__new__(SwarmAgent)
        text = 'Here is my analysis:\n{"vote": "SELL", "confidence": 0.3, "reasoning": "Bad"}\nThank you.'
        result = agent._parse_json_response(text)
        assert result["vote"] == "SELL"

    def test_invalid_json(self):
        agent = SwarmAgent.__new__(SwarmAgent)
        text = 'This is not JSON at all'
        result = agent._parse_json_response(text)
        assert result == {}
