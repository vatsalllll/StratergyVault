"""
StrategyVault Core Configuration
Combines best practices from AgentQuant and Moon Dev projects
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App Info
    APP_NAME: str = "StrategyVault"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./strategyvault.db"
    
    # AI Model APIs
    GOOGLE_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    DEEPSEEK_API_KEY: Optional[str] = None
    XAI_API_KEY: Optional[str] = None
    
    # Authentication
    JWT_SECRET_KEY: str = "change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # Stripe (for payments)
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    
    # Strategy Generation Settings (from Moon Dev RBI Agent)
    MAX_PARALLEL_BACKTESTS: int = 18
    TARGET_RETURN_PERCENT: float = 50.0
    MIN_SAVE_RETURN_PERCENT: float = 1.0
    MAX_DEBUG_ITERATIONS: int = 10
    
    # Validation Settings (from AgentQuant)
    WALK_FORWARD_WINDOW_MONTHS: int = 6
    MIN_SHARPE_RATIO: float = 0.5
    MAX_DRAWDOWN_PERCENT: float = 30.0
    
    # AI Consensus Settings (from Moon Dev Swarm)
    SWARM_MODELS: list = [
        "gemini-2.5-flash",
        "gpt-4o",
        "claude-sonnet-4-5",
        "deepseek-chat",
        "grok-4"
    ]
    CONSENSUS_THRESHOLD: float = 0.6  # 60% agreement = consensus
    
    # Quality Thresholds
    GOLD_SCORE_THRESHOLD: int = 85
    SILVER_SCORE_THRESHOLD: int = 70
    BRONZE_SCORE_THRESHOLD: int = 50
    
    model_config = ConfigDict(env_file=".env", case_sensitive=True)


# Global settings instance
settings = Settings()


# Asset configurations for backtesting (from Moon Dev)
BACKTEST_ASSETS = [
    # Crypto
    {"symbol": "BTC-USD", "name": "Bitcoin", "category": "crypto"},
    {"symbol": "ETH-USD", "name": "Ethereum", "category": "crypto"},
    {"symbol": "SOL-USD", "name": "Solana", "category": "crypto"},
    
    # Stocks
    {"symbol": "SPY", "name": "S&P 500 ETF", "category": "stocks"},
    {"symbol": "QQQ", "name": "Nasdaq 100 ETF", "category": "stocks"},
    {"symbol": "AAPL", "name": "Apple", "category": "stocks"},
    {"symbol": "MSFT", "name": "Microsoft", "category": "stocks"},
    {"symbol": "NVDA", "name": "NVIDIA", "category": "stocks"},
    {"symbol": "TSLA", "name": "Tesla", "category": "stocks"},
    {"symbol": "AMZN", "name": "Amazon", "category": "stocks"},
    
    # Indices
    {"symbol": "^VIX", "name": "VIX", "category": "indices"},
    {"symbol": "^GSPC", "name": "S&P 500", "category": "indices"},
]


# Regime definitions (from AgentQuant)
REGIME_THRESHOLDS = {
    "vix_high": 30,
    "vix_mid": 20,
    "momentum_bull": 0.05,
    "momentum_bear": -0.05,
}

REGIME_LABELS = [
    "Crisis-Bear",
    "HighVol-Uncertain",
    "MidVol-Bull",
    "MidVol-Bear",
    "MidVol-MeanRevert",
    "LowVol-Bull",
    "LowVol-MeanRevert",
]
