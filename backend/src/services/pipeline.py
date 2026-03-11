"""
StrategyVault - Strategy Generation Pipeline Service
Orchestrates: generate → fetch data → backtest → validate → score → save.

Key changes from initial version:
- Removed _synthetic_metrics() — no more fake performance numbers
- Integrated real walk-forward validation via quick_walk_forward()
- Failed backtests are marked as failed, not faked
"""

import os
import tempfile
import traceback
from typing import Optional, Dict, Any
from datetime import datetime

from sqlalchemy.orm import Session

from src.core.config import settings
from src.models.database import Strategy, StrategyTier
from src.data.fetcher import fetch_ohlcv
from src.rating.swarm import calculate_strategy_score


def run_pipeline(
    trading_idea: str,
    db: Session,
    asset: str = "BTC-USD",
) -> Dict[str, Any]:
    """
    Full strategy generation pipeline.

    Steps:
        1. Generate strategy code via AI (Gemini)
        2. Fetch real market data via yfinance
        3. Run backtest and parse metrics
        4. Run walk-forward validation on the data
        5. Calculate score and assign tier
        6. Save to database

    Args:
        trading_idea: Natural language description of the strategy
        db: Database session
        asset: Asset symbol to backtest on

    Returns:
        Dictionary with strategy data and pipeline status
    """
    status = {
        "steps": [],
        "success": False,
        "strategy_id": None,
        "error": None,
    }

    # ── Step 1: Generate strategy code via AI ──────────────────────
    strategy_name = "GeneratedStrategy"
    strategy_code = None

    try:
        from src.generation.generator import StrategyGenerator, AIModel

        generator = StrategyGenerator(AIModel.GEMINI_FLASH)
        result = generator.generate_strategy(trading_idea)
        strategy_name = result.name
        strategy_code = result.code
        status["steps"].append({"step": "generation", "status": "success", "name": strategy_name})
    except Exception as e:
        # Fall back to template if AI generation fails
        status["steps"].append({"step": "generation", "status": "fallback", "error": str(e)})
        from src.generation.generator import generate_backtest_template
        strategy_code = generate_backtest_template(strategy_name)

    # ── Step 2: Fetch real market data ─────────────────────────────
    data_path = None
    ohlcv_df = None
    try:
        ohlcv_df = fetch_ohlcv(asset, period="2y")
        if ohlcv_df is not None and not ohlcv_df.empty:
            # Save to temp CSV for backtest executor
            tmp = tempfile.NamedTemporaryFile(
                mode="w", suffix=".csv", delete=False, prefix="sv_data_"
            )
            # Prepare columns for backtesting.py
            export_df = ohlcv_df.copy()
            if hasattr(export_df.columns, "get_level_values"):
                try:
                    export_df.columns = export_df.columns.get_level_values(0)
                except Exception:
                    pass
            export_df.index.name = "datetime"
            export_df.to_csv(tmp.name)
            data_path = tmp.name
            status["steps"].append({"step": "data_fetch", "status": "success", "rows": len(ohlcv_df), "asset": asset})
        else:
            status["steps"].append({"step": "data_fetch", "status": "failed", "error": "No data returned"})
    except Exception as e:
        status["steps"].append({"step": "data_fetch", "status": "failed", "error": str(e)})

    # ── Step 3: RBI Debug Loop — backtest with iterative debugging ──
    return_pct = None
    sharpe_ratio = None
    max_drawdown_pct = None
    win_rate = None
    num_trades = None
    backtest_succeeded = False
    equity_curve_data = None

    if strategy_code and data_path:
        from src.generation.executor import execute_backtest

        # Package check first (fix backtesting.lib imports)
        try:
            from src.generation.generator import StrategyGenerator, AIModel
            generator = StrategyGenerator(AIModel.GEMINI_FLASH)
            strategy_code = generator.package_check(strategy_code)
            status["steps"].append({"step": "package_check", "status": "success"})
        except Exception:
            pass  # package_check is optional, proceed anyway

        max_debug_attempts = settings.MAX_DEBUG_ITERATIONS
        for attempt in range(max_debug_attempts + 1):
            try:
                bt_result = execute_backtest(
                    code=strategy_code,
                    data_path=data_path,
                    strategy_name=strategy_name,
                    timeout=120,
                )
                if bt_result.success and bt_result.return_pct is not None:
                    return_pct = bt_result.return_pct
                    sharpe_ratio = bt_result.sharpe_ratio
                    max_drawdown_pct = bt_result.max_drawdown_pct
                    win_rate = bt_result.win_rate
                    num_trades = bt_result.num_trades
                    equity_curve_data = bt_result.equity_curve
                    backtest_succeeded = True
                    status["steps"].append({
                        "step": "backtest",
                        "status": "success",
                        "return_pct": return_pct,
                        "sharpe_ratio": sharpe_ratio,
                        "attempt": attempt + 1,
                    })
                    break  # Success — exit the debug loop
                else:
                    # Backtest failed — try AI debug if we have attempts left
                    error_msg = bt_result.stderr[:500] if bt_result.stderr else "Unknown error"
                    if attempt < max_debug_attempts:
                        try:
                            strategy_code = generator.debug_strategy(strategy_code, error_msg)
                            strategy_code = generator.package_check(strategy_code)
                            status["steps"].append({
                                "step": "debug_iteration",
                                "status": "retrying",
                                "attempt": attempt + 1,
                                "error": error_msg[:100],
                            })
                        except Exception as debug_err:
                            status["steps"].append({
                                "step": "debug_iteration",
                                "status": "debug_failed",
                                "attempt": attempt + 1,
                                "error": str(debug_err)[:100],
                            })
                            break  # Can't debug, give up
                    else:
                        status["steps"].append({
                            "step": "backtest",
                            "status": "failed",
                            "error": error_msg[:200],
                            "attempts": attempt + 1,
                        })
            except Exception as e:
                if attempt >= max_debug_attempts:
                    status["steps"].append({
                        "step": "backtest",
                        "status": "error",
                        "error": str(e)[:200],
                        "attempts": attempt + 1,
                    })
                    break
    else:
        status["steps"].append({
            "step": "backtest",
            "status": "skipped",
            "error": "No code or data available",
        })

    # Clean up temp data file
    if data_path and os.path.exists(data_path):
        try:
            os.unlink(data_path)
        except Exception:
            pass

    # ── Step 4: Walk-forward validation ────────────────────────────
    walk_forward_score = 0.0
    is_robust = False

    if ohlcv_df is not None and not ohlcv_df.empty and len(ohlcv_df) > 180:
        try:
            from src.validation.walk_forward import quick_walk_forward

            wf_result = quick_walk_forward(
                ohlcv_df,
                train_months=settings.WALK_FORWARD_WINDOW_MONTHS,
                test_months=3,
            )
            walk_forward_score = float(wf_result.robustness_score * 100)  # 0-100 scale
            is_robust = bool(wf_result.is_robust)
            status["steps"].append({
                "step": "walk_forward",
                "status": "success",
                "score": round(walk_forward_score, 1),
                "windows": len(wf_result.windows),
                "is_robust": is_robust,
            })
        except Exception as e:
            status["steps"].append({
                "step": "walk_forward",
                "status": "failed",
                "error": str(e),
            })
    else:
        status["steps"].append({
            "step": "walk_forward",
            "status": "skipped",
            "error": "Insufficient data for walk-forward (need >180 days)",
        })

    # ── Step 5: Calculate score and tier ───────────────────────────
    # Use 0.5 default for consensus when swarm is not run
    consensus_confidence = 0.5

    score = calculate_strategy_score(
        return_pct=return_pct or 0,
        sharpe_ratio=sharpe_ratio or 0,
        max_drawdown=max_drawdown_pct or 0,
        consensus_confidence=consensus_confidence,
        walk_forward_score=walk_forward_score,
        is_robust=is_robust,
    )

    # Assign tier based on score AND backtest success
    if not backtest_succeeded:
        # Failed backtests cannot be Gold/Silver
        tier = StrategyTier.REJECTED
    elif score >= settings.GOLD_SCORE_THRESHOLD:
        tier = StrategyTier.GOLD
    elif score >= settings.SILVER_SCORE_THRESHOLD:
        tier = StrategyTier.SILVER
    elif score >= settings.BRONZE_SCORE_THRESHOLD:
        tier = StrategyTier.BRONZE
    else:
        tier = StrategyTier.REJECTED

    status["steps"].append({
        "step": "scoring",
        "status": "success",
        "score": score,
        "tier": tier.value,
        "backtest_succeeded": backtest_succeeded,
    })

    # ── Step 6: Save to database ──────────────────────────────────
    try:
        strategy = Strategy(
            name=strategy_name,
            description=trading_idea,
            code=strategy_code or "# Generation failed",
            return_pct=return_pct,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_drawdown_pct,
            win_rate=win_rate,
            num_trades=num_trades,
            walk_forward_score=walk_forward_score,
            is_robust=is_robust,
            consensus_vote="PENDING" if backtest_succeeded else "REJECTED",
            consensus_confidence=consensus_confidence,
            strategy_score=score,
            tier=tier,
            credit_cost=1,
            best_asset=asset,
            assets_tested=[asset],
            model_used="gemini-2.5-flash",
            generation_prompt=trading_idea,
            is_published=backtest_succeeded,  # Only publish if backtest succeeded
            is_featured=(score >= settings.GOLD_SCORE_THRESHOLD and backtest_succeeded),
        )
        db.add(strategy)
        db.commit()
        db.refresh(strategy)

        status["success"] = True
        status["strategy_id"] = strategy.id
        status["strategy"] = strategy.to_dict()
        status["steps"].append({"step": "save", "status": "success", "id": strategy.id})

    except Exception as e:
        db.rollback()
        status["steps"].append({"step": "save", "status": "failed", "error": str(e)})
        status["error"] = f"Failed to save: {str(e)}"

    return status
