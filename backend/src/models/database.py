"""
StrategyVault - Database Models
SQLAlchemy models for strategies, users, and purchases
"""

from datetime import datetime
from typing import Optional, List
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, 
    Text, ForeignKey, JSON, Enum, create_engine
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker


class Base(DeclarativeBase):
    pass


class StrategyTier(PyEnum):
    """Strategy quality tiers based on StrategyScore."""
    GOLD = "gold"       # Score >= 85
    SILVER = "silver"   # Score >= 70
    BRONZE = "bronze"   # Score >= 50
    REJECTED = "rejected"  # Score < 50


class SubscriptionTier(PyEnum):
    """User subscription tiers."""
    FREE = "free"
    EXPLORER = "explorer"     # $29/mo - 3 strategies
    INVESTOR = "investor"     # $79/mo - 10 strategies
    PRO = "pro"               # $199/mo - unlimited
    ENTERPRISE = "enterprise" # $499/mo - custom


class Strategy(Base):
    """Trading strategy model."""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    
    # Strategy code
    code = Column(Text, nullable=False)
    
    # Performance metrics
    return_pct = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    max_drawdown_pct = Column(Float)
    win_rate = Column(Float)
    num_trades = Column(Integer)
    
    # Equity curve and trade log from backtest
    equity_curve = Column(JSON)   # List of equity values from backtest
    trade_log = Column(JSON)      # List of trade records
    
    # Advanced risk metrics
    calmar_ratio = Column(Float)
    var_95 = Column(Float)        # 95% Value at Risk
    cvar_95 = Column(Float)       # 95% Conditional VaR
    omega_ratio = Column(Float)
    profit_factor = Column(Float)
    
    # Validation metrics
    walk_forward_score = Column(Float)
    is_robust = Column(Boolean, default=False)
    ablation_report = Column(JSON)
    
    # AI Consensus metrics
    consensus_vote = Column(String(50))  # BUY, HOLD, SELL
    consensus_confidence = Column(Float)  # 0-1
    ai_summary = Column(Text)
    model_responses = Column(JSON)  # Store individual AI responses
    
    # Overall score and tier
    strategy_score = Column(Integer)  # 0-100
    tier = Column(Enum(StrategyTier, native_enum=False), default=StrategyTier.BRONZE)
    
    # Pricing
    credit_cost = Column(Integer, default=1)  # Credits needed to purchase
    
    # Regime recommendations
    best_regimes = Column(JSON)  # List of regimes where strategy works best
    avoid_regimes = Column(JSON)  # List of regimes to avoid
    
    # Assets tested
    assets_tested = Column(JSON)  # List of assets used in backtesting
    best_asset = Column(String(50))  # Best performing asset
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_published = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Generation metadata
    model_used = Column(String(100))  # AI model used for generation
    generation_prompt = Column(Text)  # Original trading idea
    
    # Relationships
    purchases = relationship("Purchase", back_populates="strategy")
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "return_pct": self.return_pct,
            "sharpe_ratio": self.sharpe_ratio,
            "max_drawdown_pct": self.max_drawdown_pct,
            "win_rate": self.win_rate,
            "num_trades": self.num_trades,
            "walk_forward_score": self.walk_forward_score,
            "is_robust": self.is_robust,
            "consensus_vote": self.consensus_vote,
            "consensus_confidence": self.consensus_confidence,
            "strategy_score": self.strategy_score,
            "tier": self.tier.value if self.tier else None,
            "credit_cost": self.credit_cost,
            "best_regimes": self.best_regimes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_featured": self.is_featured,
        }


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(255))
    
    # Subscription
    subscription_tier = Column(Enum(SubscriptionTier, native_enum=False), default=SubscriptionTier.FREE)
    subscription_start = Column(DateTime)
    subscription_end = Column(DateTime)
    
    # Credits
    credits_balance = Column(Integer, default=0)
    credits_used_this_month = Column(Integer, default=0)
    
    # Stripe
    stripe_customer_id = Column(String(255))
    stripe_subscription_id = Column(String(255))
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    purchases = relationship("Purchase", back_populates="user")
    
    @property
    def monthly_strategy_limit(self) -> int:
        """Get monthly strategy limit based on subscription."""
        limits = {
            SubscriptionTier.FREE: 0,
            SubscriptionTier.EXPLORER: 3,
            SubscriptionTier.INVESTOR: 10,
            SubscriptionTier.PRO: 999999,  # Unlimited
            SubscriptionTier.ENTERPRISE: 999999,
        }
        return limits.get(self.subscription_tier, 0)
    
    @property
    def can_purchase(self) -> bool:
        """Check if user can purchase more strategies this month."""
        if self.subscription_tier in [SubscriptionTier.PRO, SubscriptionTier.ENTERPRISE]:
            return True
        return self.credits_used_this_month < self.monthly_strategy_limit


class Purchase(Base):
    """Strategy purchase model."""
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    # Purchase details
    credits_spent = Column(Integer, default=1)
    purchase_price = Column(Float)  # If paid with money
    
    # Metadata
    purchased_at = Column(DateTime, default=datetime.utcnow)
    download_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="purchases")
    strategy = relationship("Strategy", back_populates="purchases")


class BacktestResult(Base):
    """Store individual backtest results for a strategy."""
    __tablename__ = "backtest_results"
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey("strategies.id"), nullable=False)
    
    # Asset tested
    asset_symbol = Column(String(50), nullable=False)
    timeframe = Column(String(20))
    
    # Results
    return_pct = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown_pct = Column(Float)
    num_trades = Column(Integer)
    
    # Metadata
    tested_at = Column(DateTime, default=datetime.utcnow)
    execution_time = Column(Float)  # Seconds


# Database setup functions
def get_engine(database_url: str):
    """Create database engine."""
    return create_engine(database_url)


def create_tables(engine):
    """Create all tables."""
    Base.metadata.create_all(engine)


def get_session(engine):
    """Create a database session."""
    Session = sessionmaker(bind=engine)
    return Session()


if __name__ == "__main__":
    # Test model creation
    print("Testing database models...")
    
    # Create in-memory SQLite for testing
    engine = create_engine("sqlite:///:memory:")
    create_tables(engine)
    
    session = get_session(engine)
    
    # Create test strategy
    strategy = Strategy(
        name="TestMomentum",
        description="Test momentum strategy",
        code="# Test code",
        return_pct=25.5,
        sharpe_ratio=1.5,
        strategy_score=85,
        tier=StrategyTier.GOLD
    )
    session.add(strategy)
    session.commit()
    
    print(f"Created strategy: {strategy.name} (ID: {strategy.id})")
    print(f"Tier: {strategy.tier.value}")
    
    session.close()
    print("✅ Database models test passed!")
