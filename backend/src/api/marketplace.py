"""
StrategyVault - Marketplace API Endpoints
FastAPI routes for browsing strategies — wired to real database.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.models.database import Strategy, StrategyTier

# Create router
router = APIRouter()


class FeaturedStrategy(BaseModel):
    """Featured strategy card."""
    id: int
    name: str
    description: str
    return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: Optional[float] = None
    consensus_vote: Optional[str] = None
    consensus_confidence: float
    strategy_score: Optional[int] = None
    tier: str
    credit_cost: int
    is_featured: bool = False


class MarketplaceResponse(BaseModel):
    """Marketplace page response."""
    featured: List[FeaturedStrategy]
    gold_strategies: List[FeaturedStrategy]
    silver_strategies: List[FeaturedStrategy]
    bronze_strategies: List[FeaturedStrategy]
    total_strategies: int


def _to_featured(s: Strategy) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description or "",
        "return_pct": s.return_pct or 0,
        "sharpe_ratio": s.sharpe_ratio or 0,
        "max_drawdown_pct": s.max_drawdown_pct,
        "consensus_vote": s.consensus_vote,
        "consensus_confidence": s.consensus_confidence or 0,
        "strategy_score": s.strategy_score,
        "tier": s.tier.value if s.tier else "bronze",
        "credit_cost": s.credit_cost or 1,
        "is_featured": s.is_featured or False,
    }


@router.get("/", response_model=MarketplaceResponse)
async def get_marketplace(db: Session = Depends(get_db)):
    """Get marketplace homepage with featured and tiered strategies."""
    base = db.query(Strategy).filter(Strategy.is_published == True)

    featured = base.filter(Strategy.is_featured == True).order_by(Strategy.strategy_score.desc()).limit(4).all()
    gold = base.filter(Strategy.tier == StrategyTier.GOLD).order_by(Strategy.strategy_score.desc()).limit(10).all()
    silver = base.filter(Strategy.tier == StrategyTier.SILVER).order_by(Strategy.strategy_score.desc()).limit(10).all()
    bronze = base.filter(Strategy.tier == StrategyTier.BRONZE).order_by(Strategy.strategy_score.desc()).limit(10).all()
    total = base.count()

    return MarketplaceResponse(
        featured=[_to_featured(s) for s in featured],
        gold_strategies=[_to_featured(s) for s in gold],
        silver_strategies=[_to_featured(s) for s in silver],
        bronze_strategies=[_to_featured(s) for s in bronze],
        total_strategies=total,
    )


@router.get("/search")
async def search_strategies(
    query: Optional[str] = None,
    tier: Optional[str] = None,
    min_return: Optional[float] = None,
    max_drawdown: Optional[float] = None,
    regime: Optional[str] = None,
    page: int = 1,
    per_page: int = 20,
    db: Session = Depends(get_db),
):
    """Search strategies with filters."""
    q = db.query(Strategy).filter(Strategy.is_published == True)

    if query:
        q = q.filter(
            (Strategy.name.ilike(f"%{query}%")) | (Strategy.description.ilike(f"%{query}%"))
        )
    if tier:
        try:
            q = q.filter(Strategy.tier == StrategyTier(tier.lower()))
        except ValueError:
            pass
    if min_return is not None:
        q = q.filter(Strategy.return_pct >= min_return)
    if max_drawdown is not None:
        q = q.filter(Strategy.max_drawdown_pct >= max_drawdown)

    total = q.count()
    strategies = q.order_by(Strategy.strategy_score.desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        "strategies": [_to_featured(s) for s in strategies],
        "total": total,
    }


@router.post("/purchase/{strategy_id}")
async def purchase_strategy(strategy_id: int):
    """Purchase a strategy using credits."""
    raise HTTPException(status_code=401, detail="Authentication required")


@router.get("/my-strategies")
async def get_my_strategies():
    """Get user's purchased strategies."""
    raise HTTPException(status_code=401, detail="Authentication required")


@router.get("/download/{strategy_id}")
async def download_strategy(strategy_id: int):
    """Download strategy package (code + reports)."""
    raise HTTPException(status_code=401, detail="Purchase required")
