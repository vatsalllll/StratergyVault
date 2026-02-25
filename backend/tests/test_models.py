"""
Tests for StrategyVault - Database Models
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.database import (
    Strategy, User, Purchase, BacktestResult,
    StrategyTier, SubscriptionTier,
    Base, create_tables, get_session,
)


class TestStrategyModel:
    """Test Strategy ORM model."""

    def test_create_strategy(self, db_session):
        s = Strategy(
            name="TestAlpha",
            description="A test strategy",
            code="# placeholder code",
            return_pct=25.5,
            sharpe_ratio=1.5,
            strategy_score=85,
            tier=StrategyTier.GOLD,
        )
        db_session.add(s)
        db_session.commit()

        fetched = db_session.query(Strategy).filter_by(name="TestAlpha").first()
        assert fetched is not None
        assert fetched.return_pct == 25.5
        assert fetched.tier == StrategyTier.GOLD

    def test_strategy_to_dict(self, db_session):
        s = Strategy(
            name="DictTest",
            code="pass",
            return_pct=10.0,
            strategy_score=70,
            tier=StrategyTier.SILVER,
        )
        db_session.add(s)
        db_session.commit()

        d = s.to_dict()
        assert d["name"] == "DictTest"
        assert d["tier"] == "silver"
        assert d["return_pct"] == 10.0
        assert "id" in d

    def test_strategy_defaults(self, db_session):
        s = Strategy(name="Defaults", code="pass")
        db_session.add(s)
        db_session.commit()

        assert s.credit_cost == 1
        assert s.is_published is False
        assert s.is_featured is False
        assert s.is_robust is False


class TestUserModel:
    """Test User ORM model."""

    def test_create_user(self, db_session):
        u = User(
            email="test@example.com",
            hashed_password="hashed_abc",
            name="Test User",
        )
        db_session.add(u)
        db_session.commit()

        fetched = db_session.query(User).filter_by(email="test@example.com").first()
        assert fetched is not None
        assert fetched.name == "Test User"
        assert fetched.subscription_tier == SubscriptionTier.FREE

    def test_monthly_limits(self, db_session):
        u = User(email="limit@test.com", hashed_password="x")
        u.subscription_tier = SubscriptionTier.EXPLORER
        db_session.add(u)
        db_session.commit()

        assert u.monthly_strategy_limit == 3

    def test_pro_unlimited(self, db_session):
        u = User(email="pro@test.com", hashed_password="x")
        u.subscription_tier = SubscriptionTier.PRO
        db_session.add(u)
        db_session.commit()

        assert u.monthly_strategy_limit >= 999999
        assert u.can_purchase is True

    def test_free_cannot_purchase(self, db_session):
        u = User(email="free@test.com", hashed_password="x")
        u.subscription_tier = SubscriptionTier.FREE
        db_session.add(u)
        db_session.commit()

        assert u.monthly_strategy_limit == 0
        assert u.can_purchase is False

    def test_explorer_purchase_limit(self, db_session):
        u = User(email="explorer@test.com", hashed_password="x")
        u.subscription_tier = SubscriptionTier.EXPLORER
        u.credits_used_this_month = 2
        db_session.add(u)
        db_session.commit()

        assert u.can_purchase is True  # 2 < 3
        u.credits_used_this_month = 3
        assert u.can_purchase is False  # 3 >= 3

    def test_unique_email(self, db_session):
        u1 = User(email="dup@test.com", hashed_password="x")
        db_session.add(u1)
        db_session.commit()

        u2 = User(email="dup@test.com", hashed_password="y")
        db_session.add(u2)
        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()


class TestPurchaseModel:
    """Test Purchase ORM model."""

    def test_create_purchase(self, db_session):
        user = User(email="buyer@test.com", hashed_password="x")
        strategy = Strategy(name="BuyMe", code="pass")
        db_session.add_all([user, strategy])
        db_session.commit()

        purchase = Purchase(
            user_id=user.id,
            strategy_id=strategy.id,
            credits_spent=1,
        )
        db_session.add(purchase)
        db_session.commit()

        assert purchase.id is not None
        assert purchase.download_count == 0

    def test_purchase_relationships(self, db_session):
        user = User(email="rel@test.com", hashed_password="x")
        strategy = Strategy(name="RelTest", code="pass")
        db_session.add_all([user, strategy])
        db_session.commit()

        purchase = Purchase(user_id=user.id, strategy_id=strategy.id)
        db_session.add(purchase)
        db_session.commit()

        assert purchase.user.email == "rel@test.com"
        assert purchase.strategy.name == "RelTest"
        assert len(user.purchases) == 1
        assert len(strategy.purchases) == 1


class TestBacktestResultModel:
    """Test BacktestResult ORM model."""

    def test_create_backtest_result(self, db_session):
        strategy = Strategy(name="BT", code="pass")
        db_session.add(strategy)
        db_session.commit()

        bt = BacktestResult(
            strategy_id=strategy.id,
            asset_symbol="BTC-USD",
            timeframe="1d",
            return_pct=15.0,
            sharpe_ratio=1.2,
            max_drawdown_pct=-8.0,
            num_trades=42,
            execution_time=3.5,
        )
        db_session.add(bt)
        db_session.commit()

        assert bt.id is not None
        assert bt.asset_symbol == "BTC-USD"


class TestTierEnums:
    """Test tier enum values."""

    def test_strategy_tiers(self):
        assert StrategyTier.GOLD.value == "gold"
        assert StrategyTier.SILVER.value == "silver"
        assert StrategyTier.BRONZE.value == "bronze"
        assert StrategyTier.REJECTED.value == "rejected"

    def test_subscription_tiers(self):
        assert SubscriptionTier.FREE.value == "free"
        assert SubscriptionTier.EXPLORER.value == "explorer"
        assert SubscriptionTier.PRO.value == "pro"
