"""
StrategyVault - Strategy API Endpoints
FastAPI routes for strategy management — wired to real database and pipeline.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.db import get_db
from src.models.database import Strategy, StrategyTier

# Create router
router = APIRouter()


# ── Pydantic models ───────────────────────────────────────────────

class StrategyCreate(BaseModel):
    """Request model for creating a strategy."""
    trading_idea: str
    name: Optional[str] = None
    asset: Optional[str] = "BTC-USD"


class StrategyResponse(BaseModel):
    """Response model for strategy data."""
    id: int
    name: str
    description: Optional[str]
    return_pct: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown_pct: Optional[float]
    consensus_vote: Optional[str]
    consensus_confidence: Optional[float]
    strategy_score: Optional[int]
    tier: Optional[str]
    credit_cost: int = 1
    is_featured: bool = False


class StrategyListResponse(BaseModel):
    """Response for strategy listing."""
    strategies: List[StrategyResponse]
    total: int
    page: int
    per_page: int


class GenerationStatus(BaseModel):
    """Status of strategy generation."""
    status: str  # pending, generating, validating, rating, complete, failed
    progress: int  # 0-100
    message: str
    strategy_id: Optional[int] = None
    strategy: Optional[dict] = None
    steps: Optional[list] = None


# ── Helper ────────────────────────────────────────────────────────

def _strategy_to_response(s: Strategy) -> dict:
    """Convert a Strategy ORM object to a response dict."""
    return {
        "id": s.id,
        "name": s.name,
        "description": s.description,
        "return_pct": s.return_pct,
        "sharpe_ratio": s.sharpe_ratio,
        "max_drawdown_pct": s.max_drawdown_pct,
        "consensus_vote": s.consensus_vote,
        "consensus_confidence": s.consensus_confidence,
        "strategy_score": s.strategy_score,
        "tier": s.tier.value if s.tier else None,
        "credit_cost": s.credit_cost or 1,
        "is_featured": s.is_featured or False,
    }


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/", response_model=StrategyListResponse)
async def list_strategies(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    tier: Optional[str] = None,
    min_score: Optional[int] = None,
    sort_by: str = "strategy_score",
    order: str = "desc",
    db: Session = Depends(get_db),
):
    """List available strategies with filtering and pagination."""
    query = db.query(Strategy).filter(Strategy.is_published == True)

    # Tier filter
    if tier:
        try:
            tier_enum = StrategyTier(tier.lower())
            query = query.filter(Strategy.tier == tier_enum)
        except ValueError:
            pass

    # Min score filter
    if min_score is not None:
        query = query.filter(Strategy.strategy_score >= min_score)

    # Total count
    total = query.count()

    # Sorting
    sort_column = getattr(Strategy, sort_by, Strategy.strategy_score)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    strategies = query.offset((page - 1) * per_page).limit(per_page).all()

    return StrategyListResponse(
        strategies=[_strategy_to_response(s) for s in strategies],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """Get details of a specific strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return _strategy_to_response(strategy)


@router.post("/generate", response_model=GenerationStatus)
async def generate_strategy(request: StrategyCreate, db: Session = Depends(get_db)):
    """
    Generate a new strategy from a trading idea.

    Runs the full pipeline:
    1. AI Strategy Generation (Gemini)
    2. Real market data fetch (yfinance)
    3. Backtesting
    4. Score Calculation & Tier Assignment
    5. Save to Database
    """
    from src.services.pipeline import run_pipeline

    try:
        result = run_pipeline(
            trading_idea=request.trading_idea,
            db=db,
            asset=request.asset or "BTC-USD",
        )

        if result["success"]:
            return GenerationStatus(
                status="complete",
                progress=100,
                message=f"Strategy '{result['strategy']['name']}' generated successfully!",
                strategy_id=result["strategy_id"],
                strategy=result.get("strategy"),
                steps=result.get("steps"),
            )
        else:
            return GenerationStatus(
                status="failed",
                progress=0,
                message=result.get("error", "Pipeline failed"),
                steps=result.get("steps"),
            )
    except Exception as e:
        return GenerationStatus(
            status="failed",
            progress=0,
            message=f"Error: {str(e)}",
        )


@router.get("/generate/{job_id}/status", response_model=GenerationStatus)
async def get_generation_status(job_id: str):
    """Get status of a strategy generation job."""
    raise HTTPException(status_code=404, detail="Job not found")


@router.get("/{strategy_id}/code")
async def get_strategy_code(strategy_id: int, db: Session = Depends(get_db)):
    """Get the strategy code."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "id": strategy.id,
        "name": strategy.name,
        "code": strategy.code,
        "model_used": strategy.model_used,
    }


@router.get("/{strategy_id}/validation-report")
async def get_validation_report(strategy_id: int, db: Session = Depends(get_db)):
    """Get the validation report for a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "id": strategy.id,
        "name": strategy.name,
        "walk_forward_score": strategy.walk_forward_score,
        "is_robust": strategy.is_robust,
        "ablation_report": strategy.ablation_report,
    }


@router.get("/{strategy_id}/ai-consensus")
async def get_ai_consensus(strategy_id: int, db: Session = Depends(get_db)):
    """Get the AI consensus report for a strategy."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "id": strategy.id,
        "name": strategy.name,
        "consensus_vote": strategy.consensus_vote,
        "consensus_confidence": strategy.consensus_confidence,
        "ai_summary": strategy.ai_summary,
        "model_responses": strategy.model_responses,
    }


@router.get("/{strategy_id}/performance")
async def get_strategy_performance(strategy_id: int, db: Session = Depends(get_db)):
    """
    Get performance chart data for a strategy — equity curve, monthly returns,
    and drawdown series. Does NOT reveal strategy code.
    
    Returns real equity curve data if available from backtest,
    otherwise generates a simulated curve from stored metrics.
    """
    import numpy as np

    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    # ── Try real equity curve first ────────────────────────────────
    if strategy.equity_curve and len(strategy.equity_curve) > 10:
        equity = strategy.equity_curve
        equity_arr = np.array(equity)
        
        # Calculate drawdown from real equity
        running_max = np.maximum.accumulate(equity_arr)
        drawdown_series = ((equity_arr - running_max) / running_max * 100).tolist()
        
        # Calculate daily returns for monthly aggregation
        daily_returns = np.diff(equity_arr) / equity_arr[:-1]
        
        # Monthly returns (group every 21 days)
        monthly_returns = []
        for i in range(0, len(daily_returns), 21):
            chunk = daily_returns[i:i + 21]
            monthly_ret = float(np.prod(1 + chunk) - 1) * 100
            monthly_returns.append(round(monthly_ret, 2))
        
        # Generate month labels
        month_labels = _generate_month_labels(len(monthly_returns))
        
        # Sample for payload size
        step = max(1, len(equity) // 200)
        sampled_equity = [round(equity[i], 2) for i in range(0, len(equity), step)]
        sampled_dd = [round(drawdown_series[i], 2) for i in range(0, len(drawdown_series), step)]
        
        data_source = "real_backtest"
    else:
        # ── Fallback: simulated curve from stored metrics ──────────
        import hashlib
        
        seed_str = f"{strategy.id}-{strategy.name}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16) % (2**31)
        rng = np.random.RandomState(seed)

        total_return = (strategy.return_pct or 15) / 100
        sharpe = strategy.sharpe_ratio or 1.0
        max_dd = abs(strategy.max_drawdown_pct or 15) / 100
        n_days = 504

        daily_mean = total_return / n_days
        daily_vol = (daily_mean * np.sqrt(252) / max(sharpe, 0.3))
        daily_returns = rng.normal(daily_mean, daily_vol, n_days)

        dd_start = n_days // 3
        dd_length = 30
        daily_returns[dd_start:dd_start + dd_length] -= max_dd / dd_length * 1.5

        equity = [10000.0]
        for r in daily_returns:
            equity.append(equity[-1] * (1 + r))
        equity = equity[1:]

        running_max = np.maximum.accumulate(equity)
        drawdown_series = ((np.array(equity) - running_max) / running_max * 100).tolist()

        monthly_returns = []
        for i in range(0, n_days, 21):
            chunk = daily_returns[i:i + 21]
            monthly_ret = float(np.prod(1 + chunk) - 1) * 100
            monthly_returns.append(round(monthly_ret, 2))

        month_labels = _generate_month_labels(len(monthly_returns))

        sampled_equity = [round(equity[i], 2) for i in range(0, len(equity), 5)]
        sampled_dd = [round(drawdown_series[i], 2) for i in range(0, len(drawdown_series), 5)]
        
        data_source = "simulated"

    return {
        "id": strategy.id,
        "name": strategy.name,
        "data_source": data_source,
        "equity_curve": sampled_equity,
        "drawdown_series": sampled_dd,
        "monthly_returns": monthly_returns,
        "month_labels": month_labels,
        "summary": {
            "total_return_pct": strategy.return_pct,
            "sharpe_ratio": strategy.sharpe_ratio,
            "max_drawdown_pct": strategy.max_drawdown_pct,
            "win_rate": strategy.win_rate,
            "num_trades": strategy.num_trades,
            "walk_forward_score": strategy.walk_forward_score,
            "is_robust": strategy.is_robust,
            "consensus_vote": strategy.consensus_vote,
            "consensus_confidence": strategy.consensus_confidence,
            "strategy_score": strategy.strategy_score,
            "tier": strategy.tier.value if strategy.tier else None,
        },
    }


def _generate_month_labels(count: int) -> list:
    """Generate month labels for chart display."""
    labels = []
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    year = 24
    for i in range(count):
        m = i % 12
        y = year + i // 12
        labels.append(f"{months[m]}'{y}")
    return labels


@router.get("/{strategy_id}/detail")
async def get_strategy_detail(strategy_id: int, db: Session = Depends(get_db)):
    """Get full strategy details for the detail page (no code)."""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return {
        "id": strategy.id,
        "name": strategy.name,
        "description": strategy.description,
        "return_pct": strategy.return_pct,
        "sharpe_ratio": strategy.sharpe_ratio,
        "sortino_ratio": strategy.sortino_ratio,
        "max_drawdown_pct": strategy.max_drawdown_pct,
        "win_rate": strategy.win_rate,
        "num_trades": strategy.num_trades,
        "walk_forward_score": strategy.walk_forward_score,
        "is_robust": strategy.is_robust,
        "consensus_vote": strategy.consensus_vote,
        "consensus_confidence": strategy.consensus_confidence,
        "ai_summary": strategy.ai_summary,
        "strategy_score": strategy.strategy_score,
        "tier": strategy.tier.value if strategy.tier else None,
        "best_asset": strategy.best_asset,
        "assets_tested": strategy.assets_tested,
        "best_regimes": strategy.best_regimes,
        "model_used": strategy.model_used,
        "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
        "is_featured": strategy.is_featured,
        "credit_cost": strategy.credit_cost or 1,
    }

